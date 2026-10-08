from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING

from .backend import BackendContractError

if TYPE_CHECKING:
    from openhands.sdk import LLM


@dataclass(frozen=True)
class OpenHandsProviderConfig:
    """Explicit provider selection; credentials remain owned by the SDK."""

    mode: str
    model: str

    def __post_init__(self) -> None:
        if self.mode != "chatgpt_subscription":
            raise ValueError(
                "CODING_OPENHANDS_PROVIDER must be chatgpt_subscription; "
                "direct/API providers are not implemented"
            )
        if (
            not isinstance(self.model, str)
            or not self.model
            or self.model != self.model.strip()
            or any(character.isspace() for character in self.model)
            or "/" in self.model
        ):
            raise ValueError(
                "CODING_OPENHANDS_MODEL must be an explicit bare model ID"
            )

    @classmethod
    def from_environment(
        cls,
        environment: Mapping[str, str] | None = None,
    ) -> OpenHandsProviderConfig:
        environment = os.environ if environment is None else environment
        for name in ("CODING_OPENHANDS_PROVIDER", "CODING_OPENHANDS_MODEL"):
            if not environment.get(name, "").strip():
                raise ValueError(f"{name} is required")
        for name in ("CODING_OPENHANDS_API_KEY", "CODING_OPENHANDS_BASE_URL"):
            if environment.get(name, "").strip():
                raise ValueError(
                    f"{name} is not supported by the subscription provider"
                )
        return cls(
            mode=environment["CODING_OPENHANDS_PROVIDER"],
            model=environment["CODING_OPENHANDS_MODEL"],
        )

    def _validate_subscription_model(self) -> None:
        from openhands.sdk.llm.auth import OPENAI_CODEX_MODELS

        if self.model not in OPENAI_CODEX_MODELS:
            raise BackendContractError(
                "Configured model is not supported by the installed "
                "OpenHands subscription adapter; no fallback was attempted"
            )

    def _verify_llm(self, llm: LLM) -> LLM:
        if (
            not llm.is_subscription
            or llm.auth_type != "subscription"
            or llm.subscription_vendor != "openai"
            or llm.model != f"openai/{self.model}"
        ):
            raise BackendContractError(
                "OpenHands provider/model contract mismatch"
            )
        return llm

    def build_llm(self) -> LLM:
        """Load/refresh cached OAuth credentials without interactive login."""
        self._validate_subscription_model()
        from openhands.sdk.llm.auth import OpenAISubscriptionAuth

        try:
            auth = OpenAISubscriptionAuth()
            credentials = auth.refresh_if_needed_sync()
            if credentials is None:
                raise BackendContractError(
                    "ChatGPT subscription login is required; run "
                    "coding-agent-backend login openhands explicitly"
                )
            llm = auth.create_llm(
                model=self.model,
                credentials=credentials,
                usage_id="coding-orchestrator",
            )
        except BackendContractError:
            raise
        except Exception:
            # Provider exceptions can contain credentials or response bodies.
            raise BackendContractError(
                "ChatGPT subscription initialization failed; check cached "
                "credentials or run coding-agent-backend login openhands"
            ) from None
        return self._verify_llm(llm)

    def login(self) -> None:
        """Explicit operator-only device login; never called by an agent run."""
        self._validate_subscription_model()
        from openhands.sdk import LLM

        try:
            llm = LLM.subscription_login(
                vendor="openai",
                model=self.model,
                auth_method="device_code",
                open_browser=False,
                force_login=True,
            )
        except Exception:
            raise BackendContractError(
                "ChatGPT subscription login failed"
            ) from None
        self._verify_llm(llm)
