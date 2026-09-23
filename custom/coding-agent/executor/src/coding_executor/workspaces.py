from __future__ import annotations

import fcntl
import json
import os
import re
import shlex
import signal
import stat
import subprocess
import threading
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path, PurePosixPath


SAFE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$")
SAFE_REF = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/@{}^-]{0,199}$")
PATCH_LIMIT_BYTES = 262_144
READ_LIMIT_BYTES = 262_144
MODIFICATION_EXPLORATION_SOFT_LIMIT = 12
MODIFICATION_EXPLORATION_HARD_LIMIT = 16
READ_ONLY_EXPLORATION_SOFT_LIMIT = 24
READ_ONLY_EXPLORATION_HARD_LIMIT = 32

ALLOWED_COMMANDS: tuple[tuple[str, ...], ...] = (
    ("git", "diff", "--check"),
    ("python", "-m", "unittest"),
    ("python3", "-m", "unittest"),
    ("python", "-m", "pytest"),
    ("python3", "-m", "pytest"),
    ("pytest",),
    ("npm", "test"),
    ("npm", "run", "test"),
    ("npm", "run", "lint"),
    ("npm", "run", "build"),
    ("pnpm", "test"),
    ("pnpm", "lint"),
    ("pnpm", "build"),
    ("yarn", "test"),
    ("yarn", "lint"),
    ("yarn", "build"),
    ("go", "test"),
    ("cargo", "test"),
    ("cargo", "check"),
    ("cargo", "clippy"),
    ("dotnet", "test"),
)


@dataclass(frozen=True)
class CommandResult:
    command: str
    exit_code: int
    stdout: str
    stderr: str
    truncated: bool


class WorkspaceManager:
    def __init__(
        self,
        repository_root: Path,
        task_root: Path,
        command_timeout_seconds: int = 300,
        max_output_bytes: int = 65_536,
    ) -> None:
        self.repository_root = repository_root.resolve()
        self.task_root = task_root.resolve()
        self.command_timeout_seconds = command_timeout_seconds
        self.max_output_bytes = max_output_bytes
        self._task_modes: dict[str, str] = {}
        self._exploration_calls: dict[str, int] = {}
        self._budget_lock = threading.Lock()

    def list_repositories(self) -> list[str]:
        return sorted(
            path.name
            for path in self.repository_root.iterdir()
            if path.is_dir() and not path.is_symlink() and (path / ".git").exists()
        )

    def create_task(
        self,
        repository: str,
        task_name: str,
        base_ref: str = "HEAD",
        task_mode: str = "modification",
    ) -> dict[str, str]:
        if task_mode not in {"modification", "read_only"}:
            raise ValueError("task_mode must be modification or read_only")
        source = self._repository(repository)
        if not SAFE_REF.fullmatch(base_ref):
            raise ValueError("invalid base ref")
        slug = self._slug(task_name)
        task_id = f"{slug}-{uuid.uuid4().hex[:8]}"
        destination = self.task_root / task_id
        branch = f"agent/{task_id}"

        with self._source_sync_lock():
            self._ensure_source_fresh(source, base_ref)
            source_commit = self._git(source, "rev-parse", "--verify", f"{base_ref}^{{commit}}").stdout.strip()
            source_branch = self._git(source, "branch", "--show-current").stdout.strip()
            self._git(
                source,
                "-c",
                "core.hooksPath=/dev/null",
                "worktree",
                "add",
                "-b",
                branch,
                str(destination),
                base_ref,
            )
            source_status = self._git(source, "status", "--short").stdout
        with self._budget_lock:
            self._task_modes[task_id] = task_mode
            self._exploration_calls[task_id] = 0
            self._save_state(task_id)
        return {
            "task_id": task_id,
            "branch": branch,
            "task_branch": branch,
            "path": str(destination),
            "task_mode": task_mode,
            "source_repository": repository,
            "source_ref": base_ref,
            "source_branch": source_branch,
            "source_commit": source_commit,
            "source_status": source_status,
        }

    @contextmanager
    def _source_sync_lock(self):
        lock_path = self.task_root / ".source-sync.lock"
        if lock_path.is_symlink():
            raise RuntimeError("source sync lock path must not be a symbolic link")
        with lock_path.open("a+", encoding="utf-8") as lock_file:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)

    def task_status(self, task_id: str) -> dict[str, object]:
        task = self._task(task_id)
        return {
            "task_id": task_id,
            "branch": self._git(task, "branch", "--show-current").stdout.strip(),
            "status": self._git(task, "status", "--short").stdout,
            "exploration_budget": self._budget_status(task_id),
        }

    def list_files(self, task_id: str, path: str = "", max_results: int = 300) -> list[str]:
        task = self._task(task_id)
        warning = self._consume_exploration(task_id)
        target = self._path(task, path, must_exist=True)
        if not target.is_dir():
            raise ValueError("path must identify a directory")
        maximum = min(max(max_results, 1), 1000)
        result = subprocess.run(
            ["rg", "--files", "--hidden", "-g", "!.git", "."],
            cwd=target,
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
            env=self._child_environment(),
        )
        if result.returncode not in {0, 1}:
            raise RuntimeError(result.stderr.strip() or "rg --files failed")
        prefix = target.relative_to(task)
        files = [str(prefix / line.removeprefix("./")) for line in result.stdout.splitlines()[:maximum]]
        if warning:
            files.append(warning)
        return files

    def read_file(self, task_id: str, path: str, start_line: int = 1, end_line: int = 400) -> str:
        task = self._task(task_id)
        warning = self._consume_exploration(task_id)
        target = self._path(task, path, must_exist=True)
        if not target.is_file() or target.is_symlink():
            raise ValueError("path must identify a regular file")
        if target.stat().st_size > READ_LIMIT_BYTES:
            raise ValueError(f"file exceeds {READ_LIMIT_BYTES} byte read limit")
        if start_line < 1 or end_line < start_line or end_line - start_line > 1000:
            raise ValueError("invalid line range")
        lines = target.read_text(encoding="utf-8").splitlines()
        selected = lines[start_line - 1 : end_line]
        output = "\n".join(f"{number}: {line}" for number, line in enumerate(selected, start_line))
        if warning:
            output = f"{output}\n\n{warning}" if output else warning
        return output

    def search_text(
        self,
        task_id: str,
        query: str,
        path: str = "",
        glob: str = "",
        max_results: int = 100,
    ) -> str:
        if not query or len(query) > 500:
            raise ValueError("query must contain between 1 and 500 characters")
        task = self._task(task_id)
        warning = self._consume_exploration(task_id)
        target = self._path(task, path, must_exist=True)
        args = ["rg", "--line-number", "--color", "never", "--max-count", str(min(max_results, 500))]
        if glob:
            if len(glob) > 200:
                raise ValueError("glob is too long")
            args.extend(["--glob", glob])
        args.extend(["--", query, str(target)])
        result = subprocess.run(
            args,
            cwd=task,
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
            env=self._child_environment(),
        )
        if result.returncode not in {0, 1}:
            raise RuntimeError(result.stderr.strip() or "rg failed")
        output = self._bounded(result.stdout)[0]
        if warning:
            output = f"{output}\n\n{warning}" if output else warning
        return output

    def apply_patch(self, task_id: str, patch: str) -> dict[str, object]:
        task = self._task(task_id)
        if self._task_mode(task_id) == "read_only":
            raise RuntimeError(
                "read_only_task: apply_patch is disabled for tasks created with task_mode=read_only"
            )
        encoded = patch.encode("utf-8")
        if not encoded or len(encoded) > PATCH_LIMIT_BYTES:
            raise ValueError(f"patch must contain between 1 and {PATCH_LIMIT_BYTES} bytes")
        self._validate_patch_paths(task, patch)
        self._git_input(task, patch, "apply", "--check", "--recount", "--whitespace=error-all")
        self._git_input(task, patch, "apply", "--recount", "--whitespace=nowarn")
        return self.task_status(task_id)

    def run_check(self, task_id: str, command: str, timeout_seconds: int | None = None) -> CommandResult:
        task = self._task(task_id)
        args = shlex.split(command, posix=True)
        if not args or not any(tuple(args[: len(prefix)]) == prefix for prefix in ALLOWED_COMMANDS):
            allowed = ", ".join(" ".join(prefix) for prefix in ALLOWED_COMMANDS)
            return CommandResult(
                command=command,
                exit_code=126,
                stdout="",
                stderr=f"command_not_allowed: allowed prefixes: {allowed}",
                truncated=False,
            )
        timeout = min(timeout_seconds or self.command_timeout_seconds, self.command_timeout_seconds)
        with subprocess.Popen(args, cwd=task, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              text=True, env=self._child_environment(), start_new_session=True) as process:
            try:
                raw_stdout, raw_stderr = process.communicate(timeout=timeout)
            except subprocess.TimeoutExpired as error:
                raise RuntimeError(f"command exceeded {timeout} second timeout") from error
            finally:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait()
        stdout, stdout_cut = self._bounded(raw_stdout)
        stderr, stderr_cut = self._bounded(raw_stderr)
        return CommandResult(command=command, exit_code=process.returncode, stdout=stdout, stderr=stderr, truncated=stdout_cut or stderr_cut)

    def diff(self, task_id: str) -> str:
        task = self._task(task_id)
        sections = [self._git(task, "diff", "--no-ext-diff", "--no-textconv", "--binary", "--").stdout]
        untracked = self._git(
            task,
            "ls-files",
            "--others",
            "--exclude-standard",
            "-z",
            "--",
        ).stdout

        for relative in filter(None, untracked.split("\0")):
            target = self._path(task, relative, must_exist=True)
            if not target.is_file() or target.is_symlink():
                raise ValueError(f"untracked path is not a regular file: {relative}")
            result = subprocess.run(
                [
                    "git",
                    "-c",
                    "core.hooksPath=/dev/null",
                    "diff",
                    "--no-index",
                    "--no-ext-diff",
                    "--no-textconv",
                    "--binary",
                    "--",
                    "/dev/null",
                    relative,
                ],
                cwd=task,
                check=False,
                capture_output=True,
                text=True,
                timeout=60,
                env=self._child_environment(),
            )
            if result.returncode not in {0, 1}:
                raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "git diff failed")
            if not result.stdout:
                raise ValueError(f"untracked file cannot be represented as a patch: {relative}")
            sections.append(result.stdout)

        complete = "".join(sections)
        if len(complete.encode("utf-8")) > self.max_output_bytes:
            raise ValueError(
                f"complete diff exceeds {self.max_output_bytes} byte output limit; split the task"
            )
        return complete

    @staticmethod
    def _budget_limits(task_mode: str) -> tuple[int, int]:
        if task_mode == "read_only":
            return READ_ONLY_EXPLORATION_SOFT_LIMIT, READ_ONLY_EXPLORATION_HARD_LIMIT
        return MODIFICATION_EXPLORATION_SOFT_LIMIT, MODIFICATION_EXPLORATION_HARD_LIMIT

    def _save_state(self, task_id: str) -> None:
        target = self.task_root / f".state-{task_id}.json"
        temporary = self.task_root / f".state-{uuid.uuid4().hex}.tmp"
        payload = json.dumps({"mode": self._task_modes[task_id], "calls": self._exploration_calls[task_id]})
        descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(descriptor, "w") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)

    def _load_state(self, task_id: str) -> None:
        if task_id in self._task_modes:
            return
        if not SAFE_NAME.fullmatch(task_id):
            raise ValueError("invalid task id")
        target = self.task_root / f".state-{task_id}.json"
        mode, calls = "read_only", READ_ONLY_EXPLORATION_HARD_LIMIT
        try:
            descriptor = os.open(target, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
            with os.fdopen(descriptor) as stream:
                info = os.fstat(stream.fileno())
                if not stat.S_ISREG(info.st_mode) or info.st_size > 4096 or info.st_nlink != 1:
                    raise ValueError("invalid persisted task state file")
                state = json.loads(stream.read(4096))
            if state["mode"] not in {"read_only", "modification"} or type(state["calls"]) is not int or state["calls"] < 0:
                raise ValueError("invalid persisted task state")
            mode, calls = state["mode"], state["calls"]
        except (OSError, ValueError, KeyError, TypeError):
            pass
        self._task_modes[task_id], self._exploration_calls[task_id] = mode, calls

    def _task_mode(self, task_id: str) -> str:
        with self._budget_lock:
            self._load_state(task_id)
            return self._task_modes.get(task_id, "modification")

    def _budget_status(self, task_id: str) -> dict[str, object]:
        with self._budget_lock:
            self._load_state(task_id)
            mode = self._task_modes.get(task_id, "modification")
            count = self._exploration_calls.get(task_id, 0)
            soft_limit, hard_limit = self._budget_limits(mode)
            return {
                "task_mode": mode,
                "exploration_calls": count,
                "exploration_soft_limit": soft_limit,
                "exploration_hard_limit": hard_limit,
                "exploration_remaining": max(hard_limit - count, 0),
                "exploration_exhausted": count >= hard_limit,
            }

    def _consume_exploration(self, task_id: str) -> str:
        with self._budget_lock:
            self._load_state(task_id)
            mode = self._task_modes.get(task_id, "modification")
            count = self._exploration_calls.get(task_id, 0)
            soft_limit, hard_limit = self._budget_limits(mode)

            if count >= hard_limit:
                if mode == "read_only":
                    next_steps = (
                        "Further list_files/read_file/search_text calls are blocked. "
                        "Do not create another task. Proceed with run_check, task_status, "
                        "git_diff, or provide the best evidence-backed final response. "
                        "apply_patch remains disabled for this read-only task."
                    )
                else:
                    next_steps = (
                        "Further list_files/read_file/search_text calls are blocked. "
                        "Do not create another task. Proceed with apply_patch, run_check, "
                        "task_status, git_diff, or provide the best evidence-backed final response."
                    )
                raise RuntimeError(
                    f"exploration_budget_exhausted: task {task_id} used "
                    f"{count}/{hard_limit} exploratory calls for task_mode={mode}. {next_steps}"
                )

            count += 1
            self._exploration_calls[task_id] = count
            self._save_state(task_id)

            if count < soft_limit:
                return ""

            remaining = hard_limit - count
            if mode == "read_only":
                action = (
                    "Stop broad exploration and prepare the final evidence-backed response; "
                    "apply_patch is disabled for this task."
                )
            else:
                action = (
                    "Decide now whether evidence is sufficient. If a fix is justified, "
                    "move to apply_patch and preserve budget for checks, task_status, git_diff, "
                    "and the final response."
                )

            return (
                "[executor_budget_warning] "
                f"task_mode={mode}; exploration_calls={count}; "
                f"soft_limit={soft_limit}; hard_limit={hard_limit}; "
                f"remaining={remaining}. {action}"
            )

    def _ensure_source_fresh(self, source: Path, base_ref: str = "HEAD") -> None:
        """Validate that the source repository is clean and not behind upstream.

        If the source repository has tracked, staged, or untracked changes, task creation
        is rejected to prevent dirty state from leaking or being overwritten.
        If the source ref has a configured upstream tracking branch and is behind it,
        task creation is rejected to prevent working against stale commits.
        If the source ref has no configured upstream tracking branch (e.g., local-only
        branch, detached HEAD, or unannotated tag), upstream freshness cannot be evaluated;
        the freshness gate permits task creation as long as the source repository is clean.
        """
        status_result = self._git(source, "status", "--porcelain")
        if status_result.stdout.strip():
            raise ValueError(
                f"source repository {source.name} is not clean (contains tracked, staged, or untracked changes); "
                "refresh or clean the source repository before creating tasks"
            )

        upstream_ref = f"{base_ref}@{{upstream}}"
        upstream_check = subprocess.run(
            ["git", "-c", "core.hooksPath=/dev/null", "rev-parse", "--verify", "--quiet", upstream_ref],
            cwd=source,
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
            env=self._child_environment(),
        )
        if upstream_check.returncode == 0:
            rev_list = self._git(source, "rev-list", "--count", f"{base_ref}..{upstream_ref}")
            behind_count = int(rev_list.stdout.strip() or "0")
            if behind_count > 0:
                commits_text = "commit" if behind_count == 1 else "commits"
                raise ValueError(
                    f"source repository {source.name} is behind its configured upstream "
                    f"({behind_count} {commits_text} behind); "
                    "refresh the source repository before creating tasks"
                )

    def _repository(self, name: str) -> Path:
        if not SAFE_NAME.fullmatch(name):
            raise ValueError("invalid repository name")
        candidate = self.repository_root / name
        if candidate.is_symlink():
            raise ValueError("repository is not available")
        path = candidate.resolve()
        if path.parent != self.repository_root or not (path / ".git").exists():
            raise ValueError("repository is not available")
        return path

    def _task(self, task_id: str) -> Path:
        if not SAFE_NAME.fullmatch(task_id):
            raise ValueError("invalid task id")
        candidate = self.task_root / task_id
        if candidate.is_symlink():
            raise ValueError("task does not exist")
        path = candidate.resolve()
        if path.parent != self.task_root or not path.is_dir():
            raise ValueError("task does not exist")
        return path

    @staticmethod
    def _slug(value: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")[:48]
        if not slug:
            raise ValueError("task name must contain a letter or number")
        return slug

    @staticmethod
    def _path(task: Path, relative: str, must_exist: bool) -> Path:
        candidate = PurePosixPath(relative or ".")
        if candidate.is_absolute() or ".." in candidate.parts:
            raise ValueError("path must be relative and remain inside the task")
        target = (task / Path(*candidate.parts)).resolve(strict=must_exist)
        if target != task and task not in target.parents:
            raise ValueError("path escaped the task workspace")
        return target

    @classmethod
    def _validate_patch_paths(cls, task: Path, patch: str) -> None:
        if "new file mode 120000" in patch or "old mode 120000" in patch:
            raise ValueError("symbolic-link patches are not allowed")
        headers = [line[4:] for line in patch.splitlines() if line.startswith(("--- ", "+++ "))]
        if not headers:
            raise ValueError("patch contains no file headers")
        for header in headers:
            raw = header.split("\t", 1)[0]
            if raw == "/dev/null":
                continue
            path = PurePosixPath(raw[2:] if raw.startswith(("a/", "b/")) else raw)
            if path.is_absolute() or ".." in path.parts or not path.parts:
                raise ValueError(f"unsafe patch path: {raw}")
            if path.parts[0] == ".git":
                raise ValueError("patches may not modify Git control files")
            target = cls._path(task, str(path), must_exist=False)
            if target.exists() and target.is_symlink():
                raise ValueError(f"patches may not modify symbolic links: {raw}")

    def _git(self, cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            ["git", "-c", "core.hooksPath=/dev/null", *args],
            cwd=cwd,
            check=False,
            capture_output=True,
            text=True,
            timeout=60,
            env=self._child_environment(),
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "git command failed")
        return result

    def _git_input(self, cwd: Path, value: str, *args: str) -> None:
        result = subprocess.run(
            ["git", "-c", "core.hooksPath=/dev/null", *args],
            cwd=cwd,
            input=value,
            check=False,
            capture_output=True,
            text=True,
            timeout=60,
            env=self._child_environment(),
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "git command failed")

    def _bounded(self, value: str) -> tuple[str, bool]:
        encoded = value.encode("utf-8")
        if len(encoded) <= self.max_output_bytes:
            return value, False
        return encoded[: self.max_output_bytes].decode("utf-8", errors="ignore") + "\n[output truncated]", True

    @staticmethod
    def _child_environment() -> dict[str, str]:
        return {
            "PATH": "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
            "HOME": "/tmp/coding-agent-home",
            "CI": "true",
            "NO_COLOR": "1",
            "LANG": "C.UTF-8",
        }
