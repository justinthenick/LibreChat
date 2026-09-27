"""Fixed executor-side operations. No shell or caller-supplied commands."""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import re
import signal
import tempfile
from pathlib import Path

from coding_executor.bounded import run, run_bytes, run_stdout_bytes
from coding_executor.coordination import maintenance_lock
from coding_executor.task_maintenance import SAFE_NAME
from coding_executor.workspaces import WorkspaceManager


INDEX_SCAN_LIMIT = 8 * 1024 * 1024
PROMOTION_PATCH_LIMIT = 8 * 1024 * 1024


def git(path: Path, *args: str, limit: int = 65536) -> str:
    return run(["git", "--no-optional-locks", "-c", "core.hooksPath=/dev/null", "-c", "core.fsmonitor=false",
                "-c", "credential.helper=", "-c", "protocol.allow=never",
                "-c", "protocol.https.allow=always", "-c", "submodule.recurse=false",
                *args], cwd=path, limit=limit)


def git_path_records(path: Path, *args: str, limit: int = 65536) -> list[str]:
    """Return NUL-delimited Git paths using reversible filesystem decoding."""
    output = run_stdout_bytes(
        ["git", "--no-optional-locks", "-c", "core.hooksPath=/dev/null", "-c", "core.fsmonitor=false",
         "-c", "credential.helper=", "-c", "protocol.allow=never",
         "-c", "protocol.https.allow=always", "-c", "submodule.recurse=false",
         *args],
        cwd=path,
        limit=limit,
    )
    return [os.fsdecode(record) for record in output.split(b"\0") if record]


def promotion_patch_bytes(task: Path, untracked: list[str]) -> bytes:
    """Render the exact byte sequence documented for human promotion."""
    prefix = [
        "git",
        "--no-optional-locks",
        "-c",
        "core.hooksPath=/dev/null",
        "-c",
        "core.fsmonitor=false",
        "-c",
        "credential.helper=",
        "-c",
        "protocol.allow=never",
        "-c",
        "protocol.https.allow=always",
        "-c",
        "submodule.recurse=false",
    ]
    sections = [
        run_stdout_bytes(
            [*prefix, "diff", "--binary", "--no-ext-diff", "--no-textconv", "--"],
            cwd=task,
            limit=PROMOTION_PATCH_LIMIT,
        )
    ]
    size = len(sections[0])

    for relative in untracked:
        remaining = PROMOTION_PATCH_LIMIT - size
        if remaining <= 0:
            raise ValueError(
                f"complete promotion patch exceeds {PROMOTION_PATCH_LIMIT} byte output limit; split the task"
            )
        section = run_stdout_bytes(
            [
                *prefix,
                "diff",
                "--no-index",
                "--binary",
                "--no-ext-diff",
                "--no-textconv",
                "--",
                "/dev/null",
                relative,
            ],
            cwd=task,
            limit=remaining,
            accepted_returncodes=(1,),
        )
        if not section:
            raise ValueError(f"untracked file cannot be represented as a patch: {relative}")
        sections.append(section)
        size += len(section)

    patch = b"".join(sections)
    if not patch:
        raise ValueError("promotion candidate patch is empty")
    return patch



def promotion_paths(task: Path) -> tuple[list[str], list[str]]:
    """Enumerate and validate all paths represented by a promotion candidate."""
    untracked, ordered_paths = promotion_paths(task)

    common = source / ".git"
    objects = common / "objects"
    if common.is_symlink() or objects.is_symlink() or not objects.is_dir():
        raise ValueError("source object store is not a local canonical directory")

    promotion_patch = promotion_patch_bytes(task, untracked)
    patch_sha256 = hashlib.sha256(promotion_patch).hexdigest()

    def build_candidate_tree() -> str:
        with tempfile.TemporaryDirectory(prefix="coding-promotion-") as temporary:
            root = Path(temporary)
            object_dir = root / "objects"
            object_dir.mkdir()
            index_file = root / "index"
            environment = {
                "GIT_INDEX_FILE": str(index_file),
                "GIT_OBJECT_DIRECTORY": str(object_dir),
                "GIT_ALTERNATE_OBJECT_DIRECTORIES": str(objects),
            }

            command_prefix = [
                "git",
                "--no-optional-locks",
                "-c",
                "core.hooksPath=/dev/null",
                "-c",
                "core.fsmonitor=false",
                "-c",
                "credential.helper=",
                "-c",
                "protocol.allow=never",
                "-c",
                "submodule.recurse=false",
            ]

            def candidate_git(*args: str, limit: int = 65536) -> str:
                return run(
                    [*command_prefix, *args],
                    cwd=task,
                    limit=limit,
                    env_override=environment,
                )

            candidate_git("read-tree", "HEAD")
            candidate_git("add", "--all", "--", ".")
            return candidate_git("write-tree").strip()

    candidate_tree = build_candidate_tree()
    if not re.fullmatch(r"[0-9a-f]{40,64}", candidate_tree):
        raise RuntimeError("candidate tree was not a valid Git object ID")

    if git(source, "rev-parse", "HEAD").strip() != source_head:
        raise RuntimeError("source HEAD changed during promotion preview")
    if git(source, "branch", "--show-current").strip() != source_branch:
        raise RuntimeError("source branch changed during promotion preview")
    if git(source, "status", "--porcelain=v1", "--untracked-files=all"):
        raise RuntimeError("source repository changed during promotion preview")
    if _hidden_index_flags(source):
        raise RuntimeError("source hidden-index state changed during promotion preview")

    verification_untracked, verification_paths = promotion_paths(task)
    if verification_untracked != untracked or verification_paths != ordered_paths:
        raise RuntimeError("task paths changed during promotion preview")
    verification_patch = promotion_patch_bytes(task, verification_untracked)
    verification_sha256 = hashlib.sha256(verification_patch).hexdigest()
    verification_tree = build_candidate_tree()
    if verification_tree != candidate_tree or verification_sha256 != patch_sha256:
        raise RuntimeError("task changed during promotion preview")

    evidence = {
        "task_id": task_id,
        "repository": snapshot["repository"],
        "task_branch": snapshot["branch"],
        "source_branch": source_branch,
        "source_head": source_head,
        "candidate_tree": candidate_tree,
        "patch_sha256": patch_sha256,
        "changed_paths": ordered_paths,
    }
    candidate_hash = hashlib.sha256(
        json.dumps(evidence, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {
        **evidence,
        "candidate_hash": candidate_hash,
        "change_count": len(ordered_paths),
        "source_mutated": False,
        "candidate_storage": "temporary_index_and_object_store",
    }


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
    parser.add_argument("operation", choices=["health", "status", "fresh-status", "refresh", "inventory", "preview", "promotion-candidate", "remove"])
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
            elif args.operation == "promotion-candidate":
                result = promotion_candidate(repositories, tasks, args.task)
                result["exclusive_gate_verified"] = True
            else:
                result = remove_task(repositories, tasks, args.task, args.fingerprint)
    print(json.dumps(result))


if __name__ == "__main__":
    main()
