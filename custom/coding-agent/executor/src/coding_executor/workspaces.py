from __future__ import annotations

import re
import shlex
import subprocess
import uuid
from dataclasses import dataclass
from pathlib import Path, PurePosixPath


SAFE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$")
SAFE_REF = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/@{}^-]{0,199}$")
PATCH_LIMIT_BYTES = 262_144
READ_LIMIT_BYTES = 262_144

ALLOWED_COMMANDS: tuple[tuple[str, ...], ...] = (
    ("git", "diff", "--check"),
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

    def list_repositories(self) -> list[str]:
        return sorted(
            path.name
            for path in self.repository_root.iterdir()
            if path.is_dir() and not path.is_symlink() and (path / ".git").exists()
        )

    def create_task(self, repository: str, task_name: str, base_ref: str = "HEAD") -> dict[str, str]:
        source = self._repository(repository)
        if not SAFE_REF.fullmatch(base_ref):
            raise ValueError("invalid base ref")
        slug = self._slug(task_name)
        task_id = f"{slug}-{uuid.uuid4().hex[:8]}"
        destination = self.task_root / task_id
        branch = f"agent/{task_id}"
        self._git(source, "rev-parse", "--verify", f"{base_ref}^{{commit}}")
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
        return {"task_id": task_id, "branch": branch, "path": str(destination)}

    def task_status(self, task_id: str) -> dict[str, str]:
        task = self._task(task_id)
        return {
            "task_id": task_id,
            "branch": self._git(task, "branch", "--show-current").stdout.strip(),
            "status": self._git(task, "status", "--short").stdout,
        }

    def list_files(self, task_id: str, path: str = "", max_results: int = 300) -> list[str]:
        task = self._task(task_id)
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
        return [str(prefix / line.removeprefix("./")) for line in result.stdout.splitlines()[:maximum]]

    def read_file(self, task_id: str, path: str, start_line: int = 1, end_line: int = 400) -> str:
        task = self._task(task_id)
        target = self._path(task, path, must_exist=True)
        if not target.is_file() or target.is_symlink():
            raise ValueError("path must identify a regular file")
        if target.stat().st_size > READ_LIMIT_BYTES:
            raise ValueError(f"file exceeds {READ_LIMIT_BYTES} byte read limit")
        if start_line < 1 or end_line < start_line or end_line - start_line > 1000:
            raise ValueError("invalid line range")
        lines = target.read_text(encoding="utf-8").splitlines()
        selected = lines[start_line - 1 : end_line]
        return "\n".join(f"{number}: {line}" for number, line in enumerate(selected, start_line))

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
        return self._bounded(result.stdout)[0]

    def apply_patch(self, task_id: str, patch: str) -> dict[str, str]:
        task = self._task(task_id)
        encoded = patch.encode("utf-8")
        if not encoded or len(encoded) > PATCH_LIMIT_BYTES:
            raise ValueError(f"patch must contain between 1 and {PATCH_LIMIT_BYTES} bytes")
        self._validate_patch_paths(task, patch)
        self._git_input(task, patch, "apply", "--check", "--whitespace=error-all")
        self._git_input(task, patch, "apply", "--whitespace=nowarn")
        return self.task_status(task_id)

    def run_check(self, task_id: str, command: str, timeout_seconds: int | None = None) -> CommandResult:
        task = self._task(task_id)
        args = shlex.split(command, posix=True)
        if not args or not any(tuple(args[: len(prefix)]) == prefix for prefix in ALLOWED_COMMANDS):
            allowed = ", ".join(" ".join(prefix) for prefix in ALLOWED_COMMANDS)
            raise ValueError(f"command is not allowlisted; allowed prefixes: {allowed}")
        timeout = min(timeout_seconds or self.command_timeout_seconds, self.command_timeout_seconds)
        try:
            result = subprocess.run(
                args,
                cwd=task,
                check=False,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=self._child_environment(),
            )
        except subprocess.TimeoutExpired as error:
            raise RuntimeError(f"command exceeded {timeout} second timeout") from error
        stdout, stdout_cut = self._bounded(result.stdout)
        stderr, stderr_cut = self._bounded(result.stderr)
        return CommandResult(command=command, exit_code=result.returncode, stdout=stdout, stderr=stderr, truncated=stdout_cut or stderr_cut)

    def diff(self, task_id: str) -> str:
        task = self._task(task_id)
        result = self._git(task, "diff", "--no-ext-diff", "--binary")
        return self._bounded(result.stdout)[0]

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
