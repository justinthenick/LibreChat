from __future__ import annotations

import argparse
import json
import os
import sys

from .backend import (
    BackendContractError,
    BackendRunRequest,
)
from .openhands_backend import (
    OpenHandsBackend,
)


def _required_environment(
    name: str,
) -> str:
    value = os.environ.get(
        name,
        "",
    ).strip()

    if not value:
        raise ValueError(
            f"{name} is required"
        )

    return value


def _backend_kwargs() -> dict[str, str]:
    return {
        "endpoint": _required_environment(
            "CODING_OPENHANDS_EXECUTOR_URL"
        ),
        "token": _required_environment(
            "CODING_EXECUTOR_TOKEN"
        ),
    }


def _probe_openhands() -> int:
    try:
        result = OpenHandsBackend(
            **_backend_kwargs(),
        ).probe()
    except (
        BackendContractError,
        ValueError,
    ) as error:
        print(
            str(error),
            file=sys.stderr,
        )
        return 1

    print(
        json.dumps(
            {
                "ok": True,
                **result.as_dict(),
            },
            indent=2,
            sort_keys=True,
        )
    )

    return 0


def _smoke_openhands() -> int:
    try:
        scratch_root = _required_environment(
            "CODING_OPENHANDS_SCRATCH_ROOT"
        )

        from openhands.sdk.llm import (
            Message,
            MessageToolCall,
            TextContent,
        )
        from openhands.sdk.testing import (
            TestLLM,
        )

        llm = TestLLM.from_messages(
            [
                Message(
                    role="assistant",
                    content=[
                        TextContent(text="")
                    ],
                    tool_calls=[
                        MessageToolCall(
                            id="call-list-repositories",
                            name="list_repositories",
                            arguments="{}",
                            origin="completion",
                        )
                    ],
                ),
                Message(
                    role="assistant",
                    content=[
                        TextContent(text="")
                    ],
                    tool_calls=[
                        MessageToolCall(
                            id="call-finish",
                            name="finish",
                            arguments=json.dumps(
                                {
                                    "message": (
                                        "OpenHands restricted "
                                        "executor smoke complete."
                                    )
                                }
                            ),
                            origin="completion",
                        )
                    ],
                ),
            ],
            model="test-model",
            usage_id="openhands-smoke",
        )

        backend = OpenHandsBackend(
            **_backend_kwargs(),
            llm=llm,
            scratch_root=scratch_root,
        )

        result = backend.run(
            BackendRunRequest(
                prompt=(
                    "Perform a read-only executor "
                    "connectivity smoke test. "
                    "List the approved repositories, "
                    "then finish."
                ),
                max_iterations=4,
            )
        )
    except (
        BackendContractError,
        ValueError,
    ) as error:
        print(
            str(error),
            file=sys.stderr,
        )
        return 1

    print(
        json.dumps(
            {
                "ok": True,
                **result.as_dict(),
            },
            indent=2,
            sort_keys=True,
        )
    )

    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="coding-agent-backend",
    )

    commands = parser.add_subparsers(
        dest="command",
        required=True,
    )

    for command in (
        "probe",
        "smoke",
    ):
        subparser = commands.add_parser(
            command,
        )
        subparser.add_argument(
            "backend",
            choices=["openhands"],
        )

    return parser


def main() -> int:
    args = build_parser().parse_args()

    if (
        args.command == "probe"
        and args.backend == "openhands"
    ):
        return _probe_openhands()

    if (
        args.command == "smoke"
        and args.backend == "openhands"
    ):
        return _smoke_openhands()

    raise AssertionError(
        "unreachable backend command"
    )


if __name__ == "__main__":
    raise SystemExit(main())
