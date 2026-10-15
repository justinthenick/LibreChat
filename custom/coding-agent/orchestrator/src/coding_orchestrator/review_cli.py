"""Operator-only, non-publishing PR review command."""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import sys
from pathlib import Path

from .backend import BackendContractError
from .pr_review import ReviewError, collect_diff, extract_added_lines, validate_findings
from .review_limits import validate_input

# Private supervisor-only diagnostic pipe; never echo exception messages,
# user-controlled source, provider errors, or credentials to this channel.
_DIAGNOSTIC_STAGES = frozenset({
    "evidence_validated", "provider_ready", "conversation_started",
    "conversation_finished", "result_validated",
})


def _worker_stage(stage: str) -> None:
    # Diagnostics are observational: failures must not change review outcomes.
    try:
        if os.environ.get("CODING_REVIEW_STAGE_FD") != "3":
            return
        if stage not in _DIAGNOSTIC_STAGES:
            return
        os.write(3, (stage + "\n").encode("ascii"))
    except Exception:
        pass


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="coding-agent-pr-review")
    parser.add_argument("mode", choices=("preview", "review"))
    parser.add_argument("--repo", required=True)
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", required=True)
    args = parser.parse_args(argv)

    try:
        repo = Path(args.repo)

        # Validate evidence before any provider initialization.
        diff = collect_diff(repo, args.base, args.head)
        validate_input(diff)
        lines = extract_added_lines(diff)
        validate_findings(lines, {"findings": []})
        _worker_stage("evidence_validated")

        # Include deletion-only files, not just files with additions.
        changed_files = []
        for line in diff.split("\n"):
            if line.startswith("diff --git "):
                parts = line.partition(" b/")
                if not parts[1] or not parts[0].startswith("diff --git a/"):
                    raise ReviewError("Invalid changed-file header")
                old_path = parts[0][13:]
                if not old_path or old_path != parts[2]:
                    raise ReviewError("Mismatched changed-file paths")
                changed_files.append(old_path)

        if args.mode == "preview":
            result = {
                "status": "not_reviewed",
                "diff_bytes": len(diff.encode("utf-8")),
                "added_lines": len(lines),
                "changed_files": sorted(set(changed_files)),
            }
        else:
            with contextlib.redirect_stdout(sys.stderr):
                from .provider import OpenHandsProviderConfig
                from .review_backend import ReviewBackend

                scratch = os.environ.get(
                    "CODING_OPENHANDS_SCRATCH_ROOT", ""
                ).strip()
                if not scratch:
                    raise ValueError(
                        "CODING_OPENHANDS_SCRATCH_ROOT is required"
                    )

                provider = OpenHandsProviderConfig.from_environment()
                llm = provider.build_llm()
                _worker_stage("provider_ready")
                backend = ReviewBackend(
                    llm=llm,
                    scratch_root=scratch,
                    on_stage=_worker_stage,
                )
                result = backend.run(repo, args.base, args.head)
                result = {
                    "provider": provider.mode,
                    "model": provider.model,
                    **result,
                }

    except (ReviewError, BackendContractError) as exc:
        print(f"Review rejected: {exc}", file=sys.stderr)
        return 1
    except Exception:
        print(
            "Review failed; check repository, SDK and provider configuration",
            file=sys.stderr,
        )
        return 1

    print(json.dumps({
        "ok": True,
        "mode": args.mode,
        "base": args.base,
        "head": args.head,
        **result,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
