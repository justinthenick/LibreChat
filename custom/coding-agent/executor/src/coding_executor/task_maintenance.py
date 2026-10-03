from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Callable


SAFE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$")

LIBRECHAT_GENERATED_ROOTS = (
    "node_modules",
    "api/node_modules",
    "client/node_modules",
    "packages/api/node_modules",
    "packages/data-provider/node_modules",
    "packages/data-schemas/node_modules",
    "packages/client/node_modules",
    "packages/api/dist",
    "packages/data-provider/dist",
    "packages/data-schemas/dist",
    "packages/client/dist",
    ".turbo",
)

LIBRECHAT_WORKSPACE_LINKS = {
    "node_modules/@librechat/api": ("packages/api", "dist/index.cjs"),
    "node_modules/librechat-data-provider": (
        "packages/data-provider",
        "dist/index.js",
    ),
    "node_modules/@librechat/data-schemas": (
        "packages/data-schemas",
        "dist/index.cjs",
    ),
    "node_modules/@librechat/client": (
        "packages/client",
        "dist/index.cjs",
    ),
}

DEPENDENCY_COMMAND_TIMEOUT_SECONDS = 1800
TaskRunner = Callable[[Path, list[str], int], None]


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


def _task_attachment(
    repository_root: Path,
    task_root: Path,
    task_id: str,
) -> tuple[Path, Path, str]:
    repository_root = repository_root.resolve()
    task_root = task_root.resolve()
    task = _task_path(task_root, task_id)

    common_dir = Path(
        _git(
            task,
            "rev-parse",
            "--path-format=absolute",
            "--git-common-dir",
        ).strip()
    ).resolve()
    repository = common_dir.parent

    if (
        common_dir.name != ".git"
        or repository.parent != repository_root
        or repository.is_symlink()
        or not (repository / ".git").exists()
    ):
        raise ValueError("task is not attached to an approved repository")

    if task not in _registered_worktrees(repository):
        raise ValueError("task is not registered as a repository worktree")

    branch = _git(task, "branch", "--show-current").strip()
    if branch != f"agent/{task_id}":
        raise ValueError("task branch does not match task identity")

    return task, repository, branch


def _require_librechat_repository(repository: Path) -> None:
    if repository.name != "LibreChat":
        raise ValueError(
            "dependency provisioning is restricted to the LibreChat repository"
        )


def _ignored_paths(task: Path) -> list[str]:
    return sorted(
        filter(
            None,
            _git(
                task,
                "ls-files",
                "--others",
                "--ignored",
                "--exclude-standard",
                "-z",
                "--",
            ).split("\0"),
        )
    )


def _untracked_paths(task: Path) -> list[str]:
    return sorted(
        filter(
            None,
            _git(
                task,
                "ls-files",
                "--others",
                "--exclude-standard",
                "-z",
                "--",
            ).split("\0"),
        )
    )


def _is_generated_path(relative: str) -> bool:
    return any(
        relative == root or relative.startswith(root + "/")
        for root in LIBRECHAT_GENERATED_ROOTS
    )


def _validate_librechat_workspace(task: Path) -> None:
    package_path = task / "package.json"
    lock_path = task / "package-lock.json"

    if package_path.is_symlink() or not package_path.is_file():
        raise ValueError("task package.json must be a regular file")
    if lock_path.is_symlink() or not lock_path.is_file():
        raise ValueError("task package-lock.json must be a regular file")

    package = json.loads(package_path.read_text(encoding="utf-8"))

    if package.get("name") != "LibreChat":
        raise ValueError("unexpected LibreChat package identity")
    if package.get("workspaces") != ["api", "client", "packages/*"]:
        raise ValueError("unexpected LibreChat workspace layout")

    package_manager = package.get("packageManager")
    if not isinstance(package_manager, str) or not re.fullmatch(
        r"npm@\d+\.\d+\.\d+",
        package_manager,
    ):
        raise ValueError("LibreChat must declare a pinned npm package manager")


def _run_operator_command(
    cwd: Path,
    argv: list[str],
    timeout: int,
) -> None:
    result = subprocess.run(
        argv,
        cwd=cwd,
        check=False,
        stdin=subprocess.DEVNULL,
        stdout=sys.stderr,
        stderr=sys.stderr,
        timeout=timeout,
        env=_child_environment(),
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"{argv[0]} command failed with exit code {result.returncode}"
        )


def _verify_provisioned_dependencies(task: Path) -> None:
    for relative, (workspace, entrypoint) in LIBRECHAT_WORKSPACE_LINKS.items():
        link = task / relative
        expected = (task / workspace).resolve(strict=True)

        if not link.is_symlink():
            raise RuntimeError(
                f"workspace dependency is not a symbolic link: {relative}"
            )
        if link.resolve(strict=True) != expected:
            raise RuntimeError(
                f"workspace dependency escapes task-local package: {relative}"
            )

        runtime_entrypoint = expected / entrypoint
        if runtime_entrypoint.is_symlink() or not runtime_entrypoint.is_file():
            raise RuntimeError(
                f"workspace runtime entrypoint is missing: "
                f"{workspace}/{entrypoint}"
            )

    unexpected = [
        value
        for value in _ignored_paths(task)
        if not _is_generated_path(value)
    ]
    if unexpected:
        raise RuntimeError(
            "dependency provisioning created ignored paths outside "
            f"the allowlist: {json.dumps(unexpected[:20])}"
        )


def provision_task_dependencies(
    repository_root: Path,
    task_root: Path,
    task_id: str,
    runner: TaskRunner = _run_operator_command,
) -> dict[str, object]:
    repository_root = repository_root.resolve()
    task_root = task_root.resolve()
    task, repository, branch = _task_attachment(
        repository_root,
        task_root,
        task_id,
    )

    _require_librechat_repository(repository)
    _validate_librechat_workspace(task)

    if _git(task, "status", "--porcelain=v1", "--untracked-files=all"):
        raise ValueError(
            "task must have no tracked or untracked changes before provisioning"
        )
    if _ignored_paths(task):
        raise ValueError(
            "task must contain no ignored files before provisioning"
        )

    cache = task_root / ".npm-cache"
    if cache.is_symlink():
        raise ValueError("shared npm cache must not be a symbolic link")
    if cache.exists() and not cache.is_dir():
        raise ValueError("shared npm cache must be a directory")

    cache.mkdir(mode=0o700, exist_ok=True)
    cache.chmod(0o700)
    cache = cache.resolve()

    if cache.parent != task_root:
        raise ValueError("shared npm cache escapes task root")

    runner(
        task,
        [
            "npm",
            "ci",
            "--ignore-scripts",
            "--no-audit",
            "--no-fund",
            "--cache",
            str(cache),
        ],
        DEPENDENCY_COMMAND_TIMEOUT_SECONDS,
    )
    runner(
        task,
        ["npm", "run", "build:packages"],
        DEPENDENCY_COMMAND_TIMEOUT_SECONDS,
    )

    status = _git(
        task,
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
    )
    if status:
        raise RuntimeError(
            "dependency provisioning modified tracked or "
            "non-ignored untracked task content"
        )

    _verify_provisioned_dependencies(task)

    return {
        "provisioned": True,
        "task_id": task_id,
        "repository": repository.name,
        "branch": branch,
        "cache": str(cache),
        "generated_roots": list(LIBRECHAT_GENERATED_ROOTS),
    }


def deprovision_task_dependencies(
    repository_root: Path,
    task_root: Path,
    task_id: str,
) -> dict[str, object]:
    repository_root = repository_root.resolve()
    task_root = task_root.resolve()
    task, repository, branch = _task_attachment(
        repository_root,
        task_root,
        task_id,
    )

    _require_librechat_repository(repository)

    ignored = _ignored_paths(task)
    if not ignored:
        return {
            "deprovisioned": False,
            "task_id": task_id,
            "repository": repository.name,
            "branch": branch,
            "status": _git(
                task,
                "status",
                "--short",
                "--untracked-files=all",
            ),
        }

    unexpected = [
        value for value in ignored if not _is_generated_path(value)
    ]
    if unexpected:
        raise ValueError(
            "task contains ignored files outside the dependency allowlist: "
            f"{json.dumps(unexpected[:20])}"
        )

    protected_untracked = [
        value
        for value in _untracked_paths(task)
        if _is_generated_path(value)
    ]
    if protected_untracked:
        raise ValueError(
            "generated roots contain non-ignored untracked files: "
            f"{json.dumps(protected_untracked[:20])}"
        )

    for relative in LIBRECHAT_GENERATED_ROOTS:
        if _git(task, "ls-files", "--", relative):
            raise ValueError(
                "refusing to remove generated root containing tracked files: "
                + relative
            )

    for relative in sorted(
        LIBRECHAT_GENERATED_ROOTS,
        key=lambda value: value.count("/"),
        reverse=True,
    ):
        target = task / relative
        if target.is_symlink() or target.is_file():
            target.unlink()
        elif target.is_dir():
            shutil.rmtree(target)

    remaining = _ignored_paths(task)
    if remaining:
        raise RuntimeError(
            "ignored files remain after dependency deprovisioning: "
            f"{json.dumps(remaining[:20])}"
        )

    return {
        "deprovisioned": True,
        "task_id": task_id,
        "repository": repository.name,
        "branch": branch,
        "status": _git(
            task,
            "status",
            "--short",
            "--untracked-files=all",
        ),
    }


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


def remove_clean_task(
    repository_root: Path,
    task_root: Path,
    task_id: str,
) -> dict[str, object]:
    repository_root = repository_root.resolve()
    task_root = task_root.resolve()
    task, repository, branch = _task_attachment(
        repository_root,
        task_root,
        task_id,
    )

    status = _git(task, "status", "--porcelain=v1", "--untracked-files=all")
    if status:
        raise ValueError("task has tracked or untracked changes")
    if _ignored_paths(task):
        raise ValueError("task contains ignored files")

    _git(repository, "worktree", "remove", str(task))
    if task.exists():
        raise RuntimeError(
            "Git reported success but the task directory still exists"
        )

    return {
        "removed": True,
        "task_id": task_id,
        "repository": repository.name,
        "branch_retained": branch,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inventory tasks, manage task-local dependencies, or remove a clean task."
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

    provision = subparsers.add_parser("provision")
    provision.add_argument("task_id")
    provision.add_argument("--yes", action="store_true")

    deprovision = subparsers.add_parser("deprovision")
    deprovision.add_argument("task_id")
    deprovision.add_argument("--yes", action="store_true")

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

    repository_root = Path(args.repository_root)
    task_root = Path(args.task_root)

    try:
        if args.command == "inventory":
            result = inventory(repository_root, task_root)
        elif args.command == "provision":
            if not args.yes:
                raise ValueError("provision requires --yes")
            result = provision_task_dependencies(
                repository_root,
                task_root,
                args.task_id,
            )
        elif args.command == "deprovision":
            if not args.yes:
                raise ValueError("deprovision requires --yes")
            result = deprovision_task_dependencies(
                repository_root,
                task_root,
                args.task_id,
            )
        else:
            if not args.yes:
                raise ValueError("remove-clean requires --yes")
            result = remove_clean_task(
                repository_root,
                task_root,
                args.task_id,
            )
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as error:
        print(json.dumps({"ok": False, "error": str(error)}), file=sys.stderr)
        return 1

    print(json.dumps({"ok": True, **result}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
