"""Fixed executor-side operations. No shell or caller-supplied commands."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import signal
from pathlib import Path

from coding_executor.bounded import run
from coding_executor.coordination import maintenance_lock
from coding_executor.task_maintenance import SAFE_NAME
from coding_executor.workspaces import WorkspaceManager


def git(path: Path, *args: str) -> str:
    return run(["git", "-c", "core.hooksPath=/dev/null", "-c", "core.fsmonitor=false",
                "-c", "credential.helper=", "-c", "protocol.allow=never",
                "-c", "protocol.https.allow=always", "-c", "submodule.recurse=false",
                *args], cwd=path)


def child(root: Path, name: str) -> Path:
    if not SAFE_NAME.fullmatch(name):
        raise ValueError("invalid identifier")
    candidate = root / name
    if candidate.is_symlink() or candidate.resolve().parent != root or not candidate.is_dir():
        raise ValueError("invalid directory")
    return candidate


def repository_status(repositories: Path, name: str, branch: str) -> dict[str, object]:
    source = child(repositories, name)
    if (source / ".git").is_symlink() or not (source / ".git").is_dir():
        raise ValueError("source must have a local Git directory")
    if Path(git(source, "rev-parse", "--show-toplevel").strip()).resolve() != source:
        raise ValueError("source is not a repository root")
    actual = git(source, "branch", "--show-current").strip()
    head = git(source, "rev-parse", "HEAD").strip()
    dirty = bool(git(source, "status", "--porcelain=v1", "--untracked-files=all"))
    upstream = git(source, "for-each-ref", "--format=%(upstream:short)", f"refs/heads/{branch}").strip()
    return {"repository": name, "branch": actual, "head": head, "dirty": dirty,
            "expected_branch": branch, "upstream": upstream, "freshness": "not_fetched"}


def refresh(repositories: Path, name: str, branch: str, url: str) -> dict[str, object]:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_./-]{0,150}", branch) or ".." in branch:
        raise ValueError("invalid configured branch")
    if not re.fullmatch(r"https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\.git", url):
        raise ValueError("only configured GitHub HTTPS sources are supported")
    before = repository_status(repositories, name, branch)
    if before["dirty"] or before["branch"] != branch or before["upstream"] != f"origin/{branch}":
        raise ValueError("source must be clean, on its approved branch and expected upstream")
    source = child(repositories, name)
    if git(source, "ls-remote", "--get-url", url).strip() != url:
        raise ValueError("repository URL rewrites are not allowed")
    git(source, "fetch", "--no-tags", "--no-recurse-submodules", url, f"refs/heads/{branch}")
    target = git(source, "rev-parse", "FETCH_HEAD^{commit}").strip()
    after_fetch = repository_status(repositories, name, branch)
    if before != after_fetch:
        raise ValueError("source changed during fetch")
    ahead, behind = map(int, git(source, "rev-list", "--left-right", "--count", f"HEAD...{target}").split())
    if ahead:
        raise ValueError("source is ahead or diverged; refusing update")
    if behind:
        git(source, "merge", "--ff-only", "--no-edit", "--no-overwrite-ignore", target)
    # Update only this approved tracking ref; never push or prune other refs.
    git(source, "update-ref", f"refs/remotes/origin/{branch}", target)
    result = repository_status(repositories, name, branch)
    if result["dirty"] or result["head"] != target:
        raise RuntimeError("post-refresh verification failed")
    return {**result, "freshness": "fetched", "previous_head": before["head"], "fast_forwarded": bool(behind)}


def task_snapshot(repositories: Path, tasks: Path, task_id: str) -> dict[str, object]:
    task = child(tasks, task_id)
    if not (task / ".git").is_file() or (task / ".git").is_symlink():
        raise ValueError("task must be a linked worktree")
    common = Path(git(task, "rev-parse", "--path-format=absolute", "--git-common-dir").strip())
    source = child(repositories, common.parent.name)
    if common != source / ".git" or common.is_symlink():
        raise ValueError("task repository is not approved")
    if Path(git(task, "rev-parse", "--show-toplevel").strip()).resolve() != task:
        raise ValueError("task is not a worktree root")
    registrations = git(source, "worktree", "list", "--porcelain", "-z").split("\0\0")
    entry = next((entry for entry in registrations if entry.split("\0")[0] == f"worktree {task}"), None)
    if entry is None or any(field.startswith(("locked", "prunable")) for field in entry.split("\0")):
        raise ValueError("task is unregistered, locked or prunable")
    branch = git(task, "branch", "--show-current").strip()
    if branch != f"agent/{task_id}":
        raise ValueError("only matching agent task branches are eligible")
    dirty = bool(git(task, "status", "--porcelain=v1", "--untracked-files=all", "--ignored"))
    info = task.stat()
    identity = {"task_id": task_id, "repository": source.name, "branch": branch,
                "head": git(task, "rev-parse", "HEAD").strip(), "dirty": dirty,
                "device": info.st_dev, "inode": info.st_ino}
    fingerprint = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
    return {**identity, "fingerprint": fingerprint}


def remove_task(repositories: Path, tasks: Path, task_id: str, expected: str) -> dict[str, object]:
    snapshot = task_snapshot(repositories, tasks, task_id)
    if snapshot["dirty"] or snapshot["fingerprint"] != expected:
        raise ValueError("task changed or is not completely clean; preview again")
    source = child(repositories, str(snapshot["repository"]))
    git(source, "worktree", "remove", str(child(tasks, task_id)))
    return {"removed": True, "task_id": task_id, "branch_retained": snapshot["branch"]}


def inventory(repositories: Path, tasks: Path) -> dict[str, object]:
    entries = sorted(path.name for path in tasks.iterdir() if not path.name.startswith("."))
    if len(entries) > 200:
        raise ValueError("too many tasks; operator inventory required")
    result = []
    for name in entries:
        try:
            result.append(task_snapshot(repositories, tasks, name))
        except (ValueError, RuntimeError, OSError):
            result.append({"task_id": name, "eligible": False, "reason": "manual_review_required"})
    return {"tasks": result, "stale_registrations": "use operator inventory; never automatically pruned"}


def main() -> None:
    def deadline_expired(_signum, _frame):
        raise RuntimeError("maintenance operation deadline exceeded")
    signal.signal(signal.SIGALRM, deadline_expired)
    signal.alarm(120)
    parser = argparse.ArgumentParser()
    parser.add_argument("operation", choices=["status", "refresh", "inventory", "preview", "remove"])
    parser.add_argument("--repository", default="")
    parser.add_argument("--branch", default="")
    parser.add_argument("--url", default="")
    parser.add_argument("--task", default="")
    parser.add_argument("--fingerprint", default="")
    args = parser.parse_args()
    repositories = Path(os.environ["CODING_REPOSITORY_ROOT"]).resolve(strict=True)
    tasks = Path(os.environ["CODING_TASK_ROOT"]).resolve(strict=True)
    with maintenance_lock(tasks, exclusive=True):
        with WorkspaceManager(repositories, tasks)._source_sync_lock():
            if args.operation == "status":
                result = repository_status(repositories, args.repository, args.branch)
            elif args.operation == "refresh":
                result = refresh(repositories, args.repository, args.branch, args.url)
            elif args.operation == "inventory":
                result = inventory(repositories, tasks)
            elif args.operation == "preview":
                result = task_snapshot(repositories, tasks, args.task)
            else:
                result = remove_task(repositories, tasks, args.task, args.fingerprint)
    print(json.dumps(result))


if __name__ == "__main__":
    main()
