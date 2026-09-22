from __future__ import annotations

from dataclasses import asdict, dataclass
import os
from pathlib import Path
import subprocess
from typing import Any, Mapping


@dataclass(frozen=True)
class PreflightResult:
    repository_path: str
    repository_name: str
    branch: str
    upstream: str
    sha_before: str
    fetched_upstream_sha: str
    sha_after: str
    ahead_count: int
    behind_count: int
    fast_forwarded: bool
    status: str  # "PASS" | "FAIL"
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


GIT_REDIRECTION_VARS = (
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_INDEX_FILE",
    "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_COMMON_DIR",
    "GIT_NAMESPACE",
)


def _build_git_env(override: Mapping[str, str] | None = None) -> dict[str, str]:
    env = os.environ.copy()
    if override:
        env.update(override)
    for var in GIT_REDIRECTION_VARS:
        env.pop(var, None)
    env["GIT_TERMINAL_PROMPT"] = "0"
    env["NO_COLOR"] = "1"
    return env


def _run_git(
    cwd: Path,
    args: list[str],
    *,
    env: Mapping[str, str] | None = None,
    timeout: int = 60,
) -> subprocess.CompletedProcess[str]:
    merged_env = _build_git_env(env)

    cmd = [
        "git",
        "-c",
        "core.hooksPath=/dev/null",
        "-c",
        "core.fsmonitor=false",
        *args,
    ]
    try:
        return subprocess.run(
            cmd,
            cwd=cwd,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=merged_env,
        )
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(
            args=cmd,
            returncode=124,
            stdout="",
            stderr=f"command timed out after {timeout} seconds: {' '.join(cmd)}",
        )
    except OSError as exc:
        return subprocess.CompletedProcess(
            args=cmd,
            returncode=127,
            stdout="",
            stderr=f"process execution error: {exc}",
        )


def _check_cleanliness(
    cwd: Path,
    env: Mapping[str, str] | None,
    timeout: int,
) -> tuple[bool, str | None, str]:
    """Check if repository working tree is clean.

    Returns (is_clean, error_message_if_status_failed, dirty_output).
    """
    status_proc = _run_git(
        cwd,
        ["status", "--porcelain=v1", "--untracked-files=all"],
        env=env,
        timeout=timeout,
    )
    if status_proc.returncode != 0:
        return False, status_proc.stderr.strip() or "git status failed", ""
    output = status_proc.stdout.strip()
    return (not output), None, output


def refresh_preflight(
    repo_path: str | Path,
    *,
    expected_upstream: str | None = None,
    timeout: int = 60,
    git_env: Mapping[str, str] | None = None,
) -> PreflightResult:
    """Perform a safe, fail-closed preflight and fast-forward refresh on a Git repository.

    Designed to run strictly on the trusted WSL host before executor tasks begin.
    """
    target = Path(repo_path).resolve()
    repo_name = target.name or str(target)

    def fail(
        reason: str,
        branch: str = "",
        upstream: str = "",
        sha_before: str = "",
        fetched_upstream_sha: str = "",
        sha_after: str = "",
        ahead_count: int = 0,
        behind_count: int = 0,
        fast_forwarded: bool = False,
    ) -> PreflightResult:
        return PreflightResult(
            repository_path=str(target),
            repository_name=repo_name,
            branch=branch,
            upstream=upstream,
            sha_before=sha_before,
            fetched_upstream_sha=fetched_upstream_sha,
            sha_after=sha_after or sha_before,
            ahead_count=ahead_count,
            behind_count=behind_count,
            fast_forwarded=fast_forwarded,
            status="FAIL",
            reason=reason,
        )

    if not target.exists() or not target.is_dir():
        return fail(f"target path '{target}' is not an accessible directory")

    # 1. Verify target is a git repository
    is_git_proc = _run_git(target, ["rev-parse", "--is-inside-work-tree"], env=git_env, timeout=timeout)
    if is_git_proc.returncode == 124:
        return fail(is_git_proc.stderr.strip() or "git command timed out")
    if is_git_proc.returncode != 0 or is_git_proc.stdout.strip() != "true":
        return fail(f"target path '{target}' is not a valid Git working tree")

    # Verify target is the repository root, not a nested subdirectory
    toplevel_proc = _run_git(target, ["rev-parse", "--show-toplevel"], env=git_env, timeout=timeout)
    if toplevel_proc.returncode == 124:
        return fail(toplevel_proc.stderr.strip() or "git command timed out")
    if toplevel_proc.returncode != 0:
        return fail(f"failed to determine repository top-level: {toplevel_proc.stderr.strip()}")
    toplevel_path = Path(toplevel_proc.stdout.strip()).resolve()
    if target != toplevel_path:
        return fail(f"target path '{target}' is a subdirectory of '{toplevel_path}', not the repository root")

    # 2. Reject dirty working tree before fetch
    is_clean, status_err, _ = _check_cleanliness(target, git_env, timeout)
    if status_err:
        return fail(f"failed to check working tree status: {status_err}")
    if not is_clean:
        return fail("source repository contains tracked, staged, or untracked changes before fetch")

    # 3 & 4. Determine current branch and reject detached HEAD
    branch_proc = _run_git(target, ["branch", "--show-current"], env=git_env, timeout=timeout)
    if branch_proc.returncode != 0:
        return fail(f"failed to determine current branch: {branch_proc.stderr.strip()}")
    branch = branch_proc.stdout.strip()
    if not branch:
        return fail("detached HEAD is not supported; a named branch is required")

    # Get local SHA before fetch
    sha_proc = _run_git(target, ["rev-parse", "HEAD"], env=git_env, timeout=timeout)
    if sha_proc.returncode != 0:
        return fail(f"failed to resolve HEAD commit: {sha_proc.stderr.strip()}", branch=branch)
    sha_before = sha_proc.stdout.strip()

    # 5. Determine configured upstream and reject if missing or unexpected
    upstream_name_proc = _run_git(
        target,
        ["for-each-ref", "--format=%(upstream:short)", f"refs/heads/{branch}"],
        env=git_env,
        timeout=timeout,
    )
    upstream = upstream_name_proc.stdout.strip() if upstream_name_proc.returncode == 0 else ""
    if not upstream:
        return fail(
            f"branch '{branch}' has no configured upstream tracking branch",
            branch=branch,
            sha_before=sha_before,
        )

    required_upstream = expected_upstream if expected_upstream is not None else f"origin/{branch}"
    if upstream != required_upstream:
        return fail(
            f"branch '{branch}' has configured upstream '{upstream}', which does not match expected upstream '{required_upstream}'",
            branch=branch,
            upstream=upstream,
            sha_before=sha_before,
        )

    remote_proc = _run_git(target, ["config", f"branch.{branch}.remote"], env=git_env, timeout=timeout)
    remote = remote_proc.stdout.strip() if remote_proc.returncode == 0 else ""
    if not remote:
        return fail(
            f"unable to determine remote for upstream tracking branch '{upstream}'",
            branch=branch,
            upstream=upstream,
            sha_before=sha_before,
        )

    # 6. Fetch the configured remote from the trusted host with prune
    fetch_proc = _run_git(target, ["fetch", "--prune", remote], env=git_env, timeout=timeout)
    if fetch_proc.returncode != 0:
        err_msg = fetch_proc.stderr.strip() or fetch_proc.stdout.strip() or "git fetch failed"
        return fail(
            f"fetch failed for remote '{remote}': {err_msg}",
            branch=branch,
            upstream=upstream,
            sha_before=sha_before,
        )

    # 7. Re-check cleanliness after fetch
    is_clean_after, status_err_after, _ = _check_cleanliness(target, git_env, timeout)
    if status_err_after:
        return fail(
            f"failed to check working tree status after fetch: {status_err_after}",
            branch=branch,
            upstream=upstream,
            sha_before=sha_before,
        )
    if not is_clean_after:
        return fail(
            "source repository became dirty after fetch",
            branch=branch,
            upstream=upstream,
            sha_before=sha_before,
        )

    # 8. Calculate ahead/behind state after fetch
    upstream_sha_proc = _run_git(target, ["rev-parse", upstream], env=git_env, timeout=timeout)
    if upstream_sha_proc.returncode != 0:
        return fail(
            f"failed to resolve upstream ref '@{{upstream}}': {upstream_sha_proc.stderr.strip()}",
            branch=branch,
            upstream=upstream,
            sha_before=sha_before,
        )
    fetched_upstream_sha = upstream_sha_proc.stdout.strip()

    rev_list_proc = _run_git(
        target,
        ["rev-list", "--left-right", "--count", f"HEAD...{fetched_upstream_sha}"],
        env=git_env,
        timeout=timeout,
    )
    if rev_list_proc.returncode != 0:
        return fail(
            f"failed to compute ahead/behind counts: {rev_list_proc.stderr.strip()}",
            branch=branch,
            upstream=upstream,
            sha_before=sha_before,
            fetched_upstream_sha=fetched_upstream_sha,
        )

    counts = rev_list_proc.stdout.strip().split()
    ahead_count = int(counts[0]) if len(counts) > 0 else 0
    behind_count = int(counts[1]) if len(counts) > 1 else 0

    # 9. Clean and already current
    if ahead_count == 0 and behind_count == 0:
        return PreflightResult(
            repository_path=str(target),
            repository_name=repo_name,
            branch=branch,
            upstream=upstream,
            sha_before=sha_before,
            fetched_upstream_sha=fetched_upstream_sha,
            sha_after=sha_before,
            ahead_count=0,
            behind_count=0,
            fast_forwarded=False,
            status="PASS",
            reason="source repository is clean and up to date with upstream",
        )

    # 10. Strictly behind -> fast-forward only
    if ahead_count == 0 and behind_count > 0:
        ff_proc = _run_git(target, ["merge", "--ff-only", fetched_upstream_sha], env=git_env, timeout=timeout)
        if ff_proc.returncode != 0:
            err_msg = ff_proc.stderr.strip() or ff_proc.stdout.strip()
            return fail(
                f"fast-forward merge failed: {err_msg}",
                branch=branch,
                upstream=upstream,
                sha_before=sha_before,
                fetched_upstream_sha=fetched_upstream_sha,
                ahead_count=ahead_count,
                behind_count=behind_count,
            )

        sha_after_proc = _run_git(target, ["rev-parse", "HEAD"], env=git_env, timeout=timeout)
        sha_after = sha_after_proc.stdout.strip() if sha_after_proc.returncode == 0 else ""
        if sha_after != fetched_upstream_sha:
            return fail(
                f"fast-forward did not advance HEAD to fetched upstream SHA {fetched_upstream_sha}",
                branch=branch,
                upstream=upstream,
                sha_before=sha_before,
                fetched_upstream_sha=fetched_upstream_sha,
                sha_after=sha_after,
                ahead_count=ahead_count,
                behind_count=behind_count,
            )

        # Verify cleanliness after merge
        is_clean_final, status_err_final, _ = _check_cleanliness(target, git_env, timeout)
        if status_err_final:
            return fail(
                f"failed to check working tree status after fast-forward: {status_err_final}",
                branch=branch,
                upstream=upstream,
                sha_before=sha_before,
                fetched_upstream_sha=fetched_upstream_sha,
                sha_after=sha_after,
                ahead_count=ahead_count,
                behind_count=behind_count,
            )
        if not is_clean_final:
            return fail(
                "working tree became dirty after fast-forward update",
                branch=branch,
                upstream=upstream,
                sha_before=sha_before,
                fetched_upstream_sha=fetched_upstream_sha,
                sha_after=sha_after,
                ahead_count=ahead_count,
                behind_count=behind_count,
            )

        commits_noun = "commit" if behind_count == 1 else "commits"
        return PreflightResult(
            repository_path=str(target),
            repository_name=repo_name,
            branch=branch,
            upstream=upstream,
            sha_before=sha_before,
            fetched_upstream_sha=fetched_upstream_sha,
            sha_after=sha_after,
            ahead_count=0,
            behind_count=behind_count,
            fast_forwarded=True,
            status="PASS",
            reason=f"fast-forwarded {behind_count} {commits_noun} from {upstream}",
        )

    # 11. Diverged (ahead > 0 and behind > 0)
    if ahead_count > 0 and behind_count > 0:
        return fail(
            f"branch '{branch}' diverged from upstream '{upstream}' ({ahead_count} ahead, {behind_count} behind)",
            branch=branch,
            upstream=upstream,
            sha_before=sha_before,
            fetched_upstream_sha=fetched_upstream_sha,
            ahead_count=ahead_count,
            behind_count=behind_count,
        )

    # 12. Local ahead only (ahead > 0 and behind == 0)
    commits_noun = "commit" if ahead_count == 1 else "commits"
    return fail(
        f"branch '{branch}' is ahead of upstream '{upstream}' by {ahead_count} {commits_noun}; refusing to push or rewrite",
        branch=branch,
        upstream=upstream,
        sha_before=sha_before,
        fetched_upstream_sha=fetched_upstream_sha,
        ahead_count=ahead_count,
        behind_count=0,
    )
