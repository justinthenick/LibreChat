"""Read-only pull-request review evidence."""

from __future__ import annotations

import os
import re
import selectors
import subprocess
import time
from pathlib import Path

COMMIT_SHA = re.compile(r"[0-9a-f]{40}\Z")


class ReviewError(ValueError):
    """Review inputs or evidence failed validation."""


def git_read(repo: Path, *arguments: str) -> bytes:
    """Execute a bounded, non-interactive Git read."""
    allowed = (
        len(arguments) == 3
        and (
            (arguments[:2] == ("cat-file", "-t")
             and COMMIT_SHA.fullmatch(arguments[2]))
            or
            (arguments[0] == "merge-base"
             and all(COMMIT_SHA.fullmatch(x) for x in arguments[1:]))
        )
    )
    if not allowed:
        allowed = (
            len(arguments) == 9
            and arguments[:6] == (
                "diff", "--no-ext-diff", "--no-textconv",
                "--no-color", "--no-renames", "--unified=0"
            )
            and all(COMMIT_SHA.fullmatch(s) for s in arguments[6:8])
            and arguments[8] == "--"
        )
    if not allowed:
        raise ReviewError("Git operation is not permitted")
    try:
        with subprocess.Popen(
            ["git", "-c", "protocol.allow=never", "-c", "core.fsmonitor=false",
             "-C", str(repo), *arguments],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            env={
                "PATH": os.defpath,
                "LC_ALL": "C",
                "GIT_CONFIG_NOSYSTEM": "1",
                "GIT_CONFIG_GLOBAL": os.devnull,
                "GIT_OPTIONAL_LOCKS": "0",
                "GIT_NO_REPLACE_OBJECTS": "1",
                "GIT_TERMINAL_PROMPT": "0",
            },
        ) as process:
            try:
                output = bytearray()
                deadline = time.monotonic() + 30
                with selectors.DefaultSelector() as selector:
                    selector.register(process.stdout, selectors.EVENT_READ)
                    while True:
                        remaining = deadline - time.monotonic()
                        if remaining <= 0 or not selector.select(remaining):
                            raise ReviewError("Git evidence collection timed out")
                        chunk = os.read(process.stdout.fileno(), 8192)
                        if not chunk:
                            break
                        output.extend(chunk)
                        if len(output) > 256_000:
                            raise ReviewError("Git evidence exceeds size limit")
                if process.wait(timeout=max(0.001, deadline - time.monotonic())):
                    raise ReviewError("Git evidence collection failed")
                return bytes(output)
            finally:
                if process.poll() is None:
                    process.kill()
                process.wait()

    except (subprocess.SubprocessError, OSError) as exc:
        raise ReviewError("Git evidence collection failed") from exc


def validate_commits(repo: Path, base: str, head: str) -> None:
    """Require explicit commits in a linear base-to-head relationship."""
    for revision in (base, head):
        if not COMMIT_SHA.fullmatch(revision):
            raise ReviewError("Full commit SHA required")
        if git_read(repo, "cat-file", "-t", revision).strip() != b"commit":
            raise ReviewError("Revision is not a commit")

    ancestor = git_read(repo, "merge-base", base, head).decode().strip()
    if ancestor != base:
        raise ReviewError("Base is not an ancestor of head")


def collect_diff(repo: Path, base: str, head: str) -> str:
    """Collect UTF-8 diff evidence from two validated commits."""
    validate_commits(repo, base, head)
    raw = git_read(
        repo, "diff", "--no-ext-diff", "--no-textconv",
        "--no-color", "--no-renames", "--unified=0",
        base, head, "--",
    )
    if len(raw) > 256_000:
        raise ReviewError("Diff exceeds review size limit")
    if b"\0" in raw or b"Binary files " in raw:
        raise ReviewError("Unsupported binary diff")
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ReviewError("Non-UTF-8 diff unsupported") from exc


def extract_added_lines(diff: str) -> list[dict[str, object]]:
    """Extract new-side line evidence, rejecting unsupported paths."""
    if not diff.endswith("\n") or "\0" in diff:
        raise ReviewError("Invalid diff framing")
    _validate_hunks(diff)
    if not diff.startswith("diff --git "):
        raise ReviewError("Invalid diff header")

    rows: list[dict[str, object]] = []
    expected = None
    path = None
    number = None

    for line in diff.split("\n")[:-1]:
        if line.startswith("diff --git "):
            match = re.fullmatch(
                r"diff --git a/([A-Za-z0-9._/-]+) "
                r"b/([A-Za-z0-9._/-]+)", line
            )
            if not match or any(
                part in {"", ".", ".."} for part in match.group(2).split("/")
            ):
                raise ReviewError("Unsupported diff filename")
            expected = match.group(2)
            path = None
            number = None
            continue

        if line.startswith("@@ "):
            match = re.match(
                r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@(?: .*)?$",
                line,
            )
            if not match:
                raise ReviewError("Malformed diff hunk")
            number = int(match.group(1))
            continue

        if number is not None:
            if line.startswith("+"):
                if path is None:
                    raise ReviewError("Added line has no target file")
                rows.append({
                    "path": path,
                    "line": number,
                    "text": line[1:],
                })
                number += 1
            elif line.startswith(" "):
                number += 1
            elif line.startswith("-") or line.startswith("\\"):
                pass
            else:
                raise ReviewError("Malformed hunk body")
            continue

        if line.startswith("+++ "):
            if line == "+++ /dev/null":
                path = None
            elif line == "+++ b/" + str(expected):
                path = expected
            else:
                raise ReviewError("Unsupported target path")

    return rows



def _validate_hunks(diff: str) -> None:
    """Reject inconsistent diff paths and hunk line counts."""
    old_left = new_left = None
    seen_file = False
    seen_hunk = False
    expected = None
    old_header = new_header = False
    old_null = False

    for line in diff.split("\n")[:-1]:
        if line.startswith("diff --git "):
            if seen_file and not seen_hunk:
                raise ReviewError("Diff section has no hunk")
            if old_left is not None and (old_left or new_left):
                raise ReviewError("Incomplete diff hunk")
            match = re.fullmatch(
                r"diff --git a/(.+) b/(.+)", line
            )
            if not match or match.group(1) != match.group(2):
                raise ReviewError("Mismatched diff paths")
            seen_file = True
            seen_hunk = False
            expected = match.group(2)
            old_header = new_header = False
            old_null = False
            old_left = new_left = None

        elif line.startswith("--- ") and old_left is None:
            if (not seen_file or seen_hunk or old_header
                    or line not in ("--- a/" + expected, "--- /dev/null")):
                raise ReviewError("Invalid old-file header")
            old_header = True
            old_null = line == "--- /dev/null"

        elif line.startswith("+++ ") and new_left is None:
            if (not old_header or new_header or seen_hunk
                    or line not in ("+++ b/" + expected, "+++ /dev/null")
                    or (old_null and line == "+++ /dev/null")):
                raise ReviewError("Invalid new-file header")
            new_header = True

        elif line.startswith("@@ "):
            if not (old_header and new_header):
                raise ReviewError("Missing diff file headers")

            if not seen_file:
                raise ReviewError("Hunk without file")
            if old_left is not None and (old_left or new_left):
                raise ReviewError("Incomplete diff hunk")
            match = re.match(
                r"^@@ -\d+(?:,(\d+))? "
                r"\+\d+(?:,(\d+))? @@(?: .*)?$",
                line,
            )
            if not match:
                raise ReviewError("Malformed hunk header")
            old_left = int(match.group(1) or 1)
            new_left = int(match.group(2) or 1)
            seen_hunk = True

        elif old_left is not None:
            if line.startswith("+"):
                new_left -= 1
            elif line.startswith("-"):
                old_left -= 1
            elif line.startswith(" "):
                old_left -= 1
                new_left -= 1
            elif line.startswith(chr(92) + " No newline at end of file"):
                continue
            else:
                raise ReviewError("Malformed hunk body")

            if old_left < 0 or new_left < 0:
                raise ReviewError("Hunk exceeds declared size")

        elif seen_file:
            accepted = (
                re.fullmatch(
                    r"index [0-9a-f]{7,64}[.][.]"
                    r"[0-9a-f]{7,64}(?: [0-7]{6})?",
                    line,
                )
                or re.fullmatch(
                    r"(?:new file mode|deleted file mode|"
                    r"old mode|new mode) [0-7]{6}",
                    line,
                )
            )
            if not accepted:
                raise ReviewError("Unrecognized diff metadata")
        else:
            raise ReviewError("Unexpected diff preamble")

    if seen_file and not seen_hunk:
        raise ReviewError("Diff section has no hunk")
    if old_left is not None and (old_left or new_left):
        raise ReviewError("Incomplete diff hunk")




def validate_findings(
    changed_lines: list[dict[str, object]],
    report: dict,
) -> dict:
    """Require every finding to reference exact changed-line evidence."""
    if not isinstance(report, dict) or set(report) != {"findings"}:
        raise ReviewError("Invalid report schema")

    findings = report["findings"]
    if not isinstance(findings, list) or len(findings) > 100:
        raise ReviewError("Invalid finding count")

    if not isinstance(changed_lines, list):
        raise ReviewError("Invalid evidence collection")

    if len(changed_lines) > 10000:
        raise ReviewError("Evidence collection too large")

    for row in changed_lines:
        if not isinstance(row, dict):
            raise ReviewError("Invalid evidence row")
        if set(row) != {"path", "line", "text"}:
            raise ReviewError("Invalid evidence fields")
        if not isinstance(row["path"], str) or not row["path"]:
            raise ReviewError("Invalid evidence path")
        if type(row["line"]) is not int or row["line"] < 1:
            raise ReviewError("Invalid evidence line")
        if not isinstance(row["text"], str):
            raise ReviewError("Invalid evidence text")
        if len(row["text"]) > 10000:
            raise ReviewError("Evidence text too large")

    allowed = {
        (row["path"], row["line"], row["text"])
        for row in changed_lines
        if isinstance(row.get("text"), str) and row["text"].strip()
    }

    fields = {
        "severity", "path", "line",
        "title", "evidence", "recommendation",
    }

    for finding in findings:
        if not isinstance(finding, dict) or set(finding) != fields:
            raise ReviewError("Invalid finding fields")

        if finding["severity"] not in ("blocker", "major", "minor"):
            raise ReviewError("Invalid finding severity")

        if type(finding["line"]) is not int:
            raise ReviewError("Invalid finding line")

        for key in ("path", "title", "evidence", "recommendation"):
            value = finding[key]
            if not isinstance(value, str) or not value.strip():
                raise ReviewError("Missing finding content")
            try:
                value.encode("utf-8")
            except UnicodeEncodeError:
                raise ReviewError("Finding contains invalid Unicode") from None
            if any(ord(char) < 32 and char not in "\t" for char in value):
                raise ReviewError("Finding contains control characters")
            if len(value) > 2000:
                raise ReviewError("Finding field exceeds size limit")

        anchor = (
            finding["path"],
            finding["line"],
            finding["evidence"],
        )
        if anchor not in allowed:
            raise ReviewError("Finding lacks exact source evidence")

    return {
        "status": "human_review_required",
        "finding_count": len(findings),
        "findings": findings,
    }
