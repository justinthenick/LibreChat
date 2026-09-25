"""Fixed executor-side operations. No shell or caller-supplied commands."""
from __future__ import annotations

import argparse
import datetime
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


INDEX_SCAN_LIMIT = 8 * 1024 * 1024


def git(path: Path, *args: str, limit: int = 65536) -> str:
    return run(["git", "--no-optional-locks", "-c", "core.hooksPath=/dev/null", "-c", "core.fsmonitor=false",
                "-c", "credential.helper=", "-c", "protocol.allow=never",
                "-c", "protocol.https.allow=always", "-c", "submodule.recurse=false",
                *args], cwd=path, limit=limit)


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
    ahead = behind = None
    upstream_sha = None
    if upstream:
        try:
            ahead, behind = map(int, git(source, "rev-list", "--left-right", "--count",
                                         f"HEAD...refs/remotes/{upstream}").split())
            upstream_sha = git(source, "rev-parse", f"refs/remotes/{upstream}^{{commit}}").strip()
        except RuntimeError:
            pass
    return {"repository": name, "branch": actual, "head": head, "dirty": dirty,
            "expected_branch": branch, "upstream": upstream, "freshness": "not_fetched",
            "ahead": ahead, "behind": behind,
            "upstream_sha": upstream_sha,
            "diverged": bool(ahead and behind) if ahead is not None else None,
            "comparison_basis": "cached_upstream" if ahead is not None else "unavailable"}


def fresh_repository_status(repositories: Path, name: str, branch: str, url: str) -> dict[str, object]:
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    refused = {"ok": False, "repository": name, "freshness": "unavailable",
               "comparison_basis": "unavailable", "fetch_started_at": started, "fetched_at": None}
    if (not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_./-]{0,150}", branch) or ".." in branch
            or not re.fullmatch(r"https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\.git", url)):
        return {**refused, "fetch_result": "invalid_policy"}
    try:
        source = child(repositories, name)
        git(source, "check-ref-format", "refs/heads/" + branch)
        before = repository_status(repositories, name, branch)
        if before["dirty"] or before["branch"] != branch or before["upstream"] != f"origin/{branch}":
            return {**refused, "fetch_result": "refused_source_state"}
        origins = git(source, "config", "--get-all", "remote.origin.url").splitlines()
        if origins != [url] or git(source, "ls-remote", "--get-url", url).strip() != url:
            return {**refused, "fetch_result": "refused_remote_identity"}
    except (ValueError, RuntimeError, OSError):
        return {**refused, "fetch_result": "refused_ambiguous_source"}
    ref = f"refs/coding-maintenance/status/{branch}"
    try:
        git(source, "-c", "http.followRedirects=false", "-c", "http.sslVerify=true",
            "fetch", "--no-tags", "--no-prune", "--no-recurse-submodules", "--no-auto-maintenance",
            "--no-write-fetch-head", "--refmap=", url, f"+refs/heads/{branch}:{ref}")
        target = git(source, "rev-parse", ref + "^{commit}").strip()
        if repository_status(repositories, name, branch) != before:
            return {**refused, "fetch_result": "refused_source_changed"}
        ahead, behind = map(int, git(source, "rev-list", "--left-right", "--count", f"HEAD...{target}").split())
    except (ValueError, RuntimeError, OSError):
        return {**refused, "fetch_result": "fetch_or_comparison_failed"}
    return {**before, "ok": True, "freshness": "fetched", "comparison_basis": "fresh_remote_ref",
            "upstream_sha": target, "ahead": ahead, "behind": behind, "diverged": bool(ahead and behind),
            "fetch_started_at": started, "fetched_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "fetch_result": "success", "comparison_ref": ref, "working_tree_modified": False}


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
    admin = Path(git(task, "rev-parse", "--absolute-git-dir").strip())
    if (any(admin.glob("*.lock")) or any(common.glob("*.lock")) or (common / "index.lock").exists()
            or (common / "HEAD.lock").exists() or (common / "refs/heads" / (branch + ".lock")).exists()):
        raise ValueError("worktree has an active Git lock")
    if any((admin / marker).exists() for marker in
           ("MERGE_HEAD", "CHERRY_PICK_HEAD", "REVERT_HEAD", "rebase-apply", "rebase-merge", "sequencer", "BISECT_LOG")):
        raise ValueError("worktree has an unfinished Git operation")
    records = git(task, "status", "--porcelain=v1", "-z", "--untracked-files=all", "--ignored").split("\0")
    statuses = []
    index = 0
    while index < len(records):
        if records[index]:
            code = records[index][:2]
            statuses.append(code)
            if "R" in code or "C" in code:
                index += 1
        index += 1
    # Hidden-index detection must inspect every tracked path. Large approved repositories
    # can exceed the generic 64 KiB command-output cap, so use a larger but still bounded
    # cap for this fixed, read-only index scan.
    index_records = [record for record in git(
        task, "ls-files", "-v", "-z", "--", limit=INDEX_SCAN_LIMIT
    ).split("\0") if record]
    hidden_index_flags = [record[0] for record in index_records
                          if record[0] == "S" or record[0].islower()]
    dirty = bool(statuses or hidden_index_flags)
    checks = {"tracked_clean": all(code in ("??", "!!") for code in statuses),
              "index_clean": all(code[0] in (" ", "?", "!") for code in statuses),
              "no_untracked": "??" not in statuses, "no_ignored": "!!" not in statuses,
              "no_hidden_index_flags": not hidden_index_flags,
              "expected_identity": True, "registered_nonbroken": True, "no_git_locks": True,
              "no_git_operation": True}
    info = task.stat()
    identity = {"task_id": task_id, "repository": source.name, "branch": branch,
                "head": git(task, "rev-parse", "HEAD").strip(), "dirty": dirty,
                "device": info.st_dev, "inode": info.st_ino}
    fingerprint = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
    return {**identity, "fingerprint": fingerprint, "stale": False,
            "state": "dirty" if dirty else "clean", "checks": checks,
            "cleanup_eligible": False, "eligibility_basis": "requires_operator_retirement_and_preview"}


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
    stale = []
    sources = sorted(path for path in repositories.iterdir() if not path.name.startswith("."))
    if len(sources) > 200:
        raise ValueError("too many repositories; operator inventory required")
    for source in sources:
        if source.is_symlink() or not (source / ".git").is_dir() or (source / ".git").is_symlink():
            continue
        for entry in git(source, "worktree", "list", "--porcelain", "-z").split("\0\0"):
            fields = entry.split("\0")
            if not fields[0].startswith("worktree "):
                continue
            path = Path(fields[0][9:])
            if path.parent != tasks:
                continue
            if any(field.startswith("prunable") for field in fields) or not path.exists():
                stale.append({"repository": source.name, "task_id": path.name, "stale": True,
                              "state": "stale", "eligible": False, "reason": "manual_review_required"})
    return {"tasks": result, "stale_registrations": stale, "automatically_pruned": False}


def main() -> None:
    def deadline_expired(_signum, _frame):
        raise RuntimeError("maintenance operation deadline exceeded")
    signal.signal(signal.SIGALRM, deadline_expired)
    signal.alarm(120)
    parser = argparse.ArgumentParser()
    parser.add_argument("operation", choices=["health", "status", "fresh-status", "refresh", "inventory", "preview", "remove"])
    parser.add_argument("--repository", default="")
    parser.add_argument("--branch", default="")
    parser.add_argument("--url", default="")
    parser.add_argument("--task", default="")
    parser.add_argument("--fingerprint", default="")
    args = parser.parse_args()
    if args.operation == "health":
        from coding_executor import __version__
        print(json.dumps({"version": __version__}))
        return
    repositories = Path(os.environ["CODING_REPOSITORY_ROOT"]).resolve(strict=True)
    tasks = Path(os.environ["CODING_TASK_ROOT"]).resolve(strict=True)
    with maintenance_lock(tasks, exclusive=True):
        with WorkspaceManager(repositories, tasks)._source_sync_lock():
            if args.operation == "status":
                result = repository_status(repositories, args.repository, args.branch)
            elif args.operation == "fresh-status":
                result = fresh_repository_status(repositories, args.repository, args.branch, args.url)
            elif args.operation == "refresh":
                result = refresh(repositories, args.repository, args.branch, args.url)
            elif args.operation == "inventory":
                result = inventory(repositories, tasks)
            elif args.operation == "preview":
                result = task_snapshot(repositories, tasks, args.task)
                result["exclusive_gate_verified"] = True
            else:
                result = remove_task(repositories, tasks, args.task, args.fingerprint)
    print(json.dumps(result))


if __name__ == "__main__":
    main()
