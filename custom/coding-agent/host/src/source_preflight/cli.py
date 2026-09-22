from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .preflight import PreflightResult, refresh_preflight


def _format_human(result: PreflightResult) -> str:
    lines = [
        f"Repository:       {result.repository_name} ({result.repository_path})",
        f"Branch:           {result.branch or '<none>'}",
        f"Upstream:         {result.upstream or '<none>'}",
        f"SHA Before:       {result.sha_before or '<none>'}",
        f"Fetched Upstream: {result.fetched_upstream_sha or '<none>'}",
        f"SHA After:        {result.sha_after or '<none>'}",
        f"Ahead:            {result.ahead_count}",
        f"Behind:           {result.behind_count}",
        f"Fast-Forwarded:   {'yes' if result.fast_forwarded else 'no'}",
        f"Status:           {result.status}",
        f"Reason:           {result.reason}",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="coding-agent-source-preflight",
        description="Fail-closed source repository refresh and preflight layer for trusted WSL host",
    )
    parser.add_argument(
        "repository",
        type=str,
        help="Path to the approved target Git repository",
    )
    parser.add_argument(
        "--expected-upstream",
        type=str,
        default=None,
        help="Expected upstream tracking branch (defaults to origin/<current-branch>)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output result as structured JSON",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="Git command timeout in seconds (default: 60)",
    )

    args = parser.parse_args(argv)
    repo_path = Path(args.repository).expanduser().resolve()

    result = refresh_preflight(
        repo_path,
        expected_upstream=args.expected_upstream,
        timeout=args.timeout,
    )

    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print(_format_human(result))

    return 0 if result.status == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
