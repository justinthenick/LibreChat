from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from .backend import (
    BackendContractError,
    BackendRunRequest,
)
from .openhands_backend import (
    OpenHandsBackend,
)

from .provider import OpenHandsProviderConfig


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


def _provider_command(args: argparse.Namespace) -> int:
    try:
        provider = OpenHandsProviderConfig.from_environment()
        if args.command == "login":
            provider.login()
            result = {"provider": provider.mode, "model": provider.model}
        else:
            prompt = (
                sys.stdin.read()
                if args.prompt_file == "-"
                else Path(args.prompt_file).read_text(encoding="utf-8")
            )
            if not prompt.strip():
                raise ValueError("agent prompt must not be empty")
            backend = OpenHandsBackend(
                **_backend_kwargs(),
                provider=provider,
                scratch_root=_required_environment("CODING_OPENHANDS_SCRATCH_ROOT"),
            )
            try:
                run = backend.run(BackendRunRequest(
                    prompt=prompt,
                    max_iterations=args.max_iterations,
                ))
            except BackendContractError:
                raise
            except Exception:
                raise BackendContractError(
                    "OpenHands run failed; check provider credentials and "
                    "executor connectivity; no fallback was attempted"
                ) from None
            result = {
                "provider": provider.mode,
                "model": provider.model,
                **run.as_dict(),
            }
    except (BackendContractError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 1
    except Exception:
        print(
            "OpenHands provider command failed; check input, credentials, "
            "executor connectivity, and installed SDK",
            file=sys.stderr,
        )
        return 1
    print(json.dumps({"ok": True, **result}, indent=2, sort_keys=True))
    return 0


def _iterations(value: str) -> int:
    try:
        count = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("max-iterations must be an integer") from None
    if not 1 <= count <= 100:
        raise argparse.ArgumentTypeError("max-iterations must be between 1 and 100")
    return count


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

    login = commands.add_parser("login")
    login.add_argument("backend", choices=["openhands"])
    run = commands.add_parser("run")
    run.add_argument("backend", choices=["openhands"])
    run.add_argument(
        "--prompt-file", required=True,
        help="UTF-8 prompt file, or - to read standard input",
    )
    run.add_argument("--max-iterations", type=_iterations, default=12)

    return parser


def main() -> int:
    args = build_parser().parse_args()

    if args.command in {"login", "run"}:
        return _provider_command(args)

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
