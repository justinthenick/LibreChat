from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path


SAFE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$")


def _child_environment() -> dict[str, str]:
    return {
        "PATH": "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
        "HOME": "/tmp/coding-agent-home",
        "CI": "true",
        "NO_COLOR": "1",
        "LANG": "C.UTF-8",
    }


def _git(cwd: Path, *args: str) -> str:
    result = subprocess.run(
        [
            "git",
            "-c",
            "core.hooksPath=/dev/null",
            "-c",
            "core.fsmonitor=false",
            *args,
        ],
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
        env=_child_environment(),
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "git command failed")
    return result.stdout


def _repositories(repository_root: Path) -> list[Path]:
    return sorted(
        (
            path
            for path in repository_root.iterdir()
            if path.is_dir() and not path.is_symlink() and (path / ".git").exists()
        ),
        key=lambda path: path.name,
    )


def _registered_worktrees(repository: Path) -> list[Path]:
    output = _git(repository, "worktree", "list", "--porcelain", "-z")
    return [
        Path(field.removeprefix("worktree ")).resolve()
        for field in output.split("\0")
        if field.startswith("worktree ")
    ]


def _task_path(task_root: Path, task_id: str) -> Path:
    if not SAFE_NAME.fullmatch(task_id):
        raise ValueError("invalid task id")
    candidate = task_root / task_id
    if candidate.is_symlink():
        raise ValueError("task path must not be a symbolic link")
    path = candidate.resolve()
    if path.parent != task_root or not path.is_dir():
        raise ValueError("task does not exist")
    return path


def inventory(repository_root: Path, task_root: Path) -> dict[str, object]:
    repository_root = repository_root.resolve()
    task_root = task_root.resolve()
    tasks: list[dict[str, str]] = []
    stale: list[dict[str, str]] = []

    for candidate in sorted(task_root.iterdir(), key=lambda path: path.name):
        if not SAFE_NAME.fullmatch(candidate.name):
            continue
        if candidate.is_symlink() or not candidate.is_dir():
            tasks.append({"task_id": candidate.name, "state": "invalid", "branch": "", "status": ""})
            continue
        try:
            branch = _git(candidate, "branch", "--show-current").strip()
            status = _git(candidate, "status", "--short", "--untracked-files=all")
            ignored = _git(
                candidate,
                "ls-files",
                "--others",
                "--ignored",
                "--exclude-standard",
                "-z",
                "--",
            )
            state = "clean" if not status and not ignored else "dirty"
            tasks.append(
                {
                    "task_id": candidate.name,
                    "state": state,
                    "branch": branch,
                    "status": status,
                }
            )
        except RuntimeError:
            tasks.append({"task_id": candidate.name, "state": "broken", "branch": "", "status": ""})

    for repository in _repositories(repository_root):
        try:
            worktrees = _registered_worktrees(repository)
        except RuntimeError:
            continue
        for worktree in worktrees:
            if worktree.parent == task_root and not worktree.exists():
                stale.append({"repository": repository.name, "task_id": worktree.name})

    return {"tasks": tasks, "stale_registrations": stale}


def remove_clean_task(repository_root: Path, task_root: Path, task_id: str) -> dict[str, object]:
    repository_root = repository_root.resolve()
    task_root = task_root.resolve()
    task = _task_path(task_root, task_id)

    status = _git(task, "status", "--porcelain=v1", "--untracked-files=all")
    if status:
        raise ValueError("task has tracked or untracked changes")

    ignored = _git(
        task,
        "ls-files",
        "--others",
        "--ignored",
        "--exclude-standard",
        "-z",
        "--",
    )
    if ignored:
        raise ValueError("task contains ignored files")

    branch = _git(task, "branch", "--show-current").strip()
    common_dir = Path(
        _git(task, "rev-parse", "--path-format=absolute", "--git-common-dir").strip()
    ).resolve()
    repository = common_dir.parent
    if (
        common_dir.name != ".git"
        or repository.parent != repository_root
        or repository.is_symlink()
        or not (repository / ".git").exists()
    ):
        raise ValueError("task is not attached to an approved repository")

    registered = _registered_worktrees(repository)
    if task not in registered:
        raise ValueError("task is not registered as a repository worktree")

    _git(repository, "worktree", "remove", str(task))
    if task.exists():
        raise RuntimeError("Git reported success but the task directory still exists")

    return {
        "removed": True,
        "task_id": task_id,
        "repository": repository.name,
        "branch_retained": branch,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inventory executor tasks or remove one completely clean task worktree."
    )
    parser.add_argument(
        "--repository-root",
        default=os.environ.get("CODING_REPOSITORY_ROOT"),
    )
    parser.add_argument(
        "--task-root",
        default=os.environ.get("CODING_TASK_ROOT"),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("inventory")

    remove = subparsers.add_parser("remove-clean")
    remove.add_argument("task_id")
    remove.add_argument("--yes", action="store_true")
    return parser


def main() -> int:
    parser = _parser()
    args = parser.parse_args()
    if not args.repository_root or not args.task_root:
        parser.error(
            "repository and task roots must be supplied by arguments or executor environment"
        )

    try:
        if args.command == "inventory":
            result = inventory(Path(args.repository_root), Path(args.task_root))
        else:
            if not args.yes:
                raise ValueError("remove-clean requires --yes")
            result = remove_clean_task(
                Path(args.repository_root),
                Path(args.task_root),
                args.task_id,
            )
    except (OSError, RuntimeError, ValueError) as error:
        print(json.dumps({"ok": False, "error": str(error)}), file=sys.stderr)
        return 1

    print(json.dumps({"ok": True, **result}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
