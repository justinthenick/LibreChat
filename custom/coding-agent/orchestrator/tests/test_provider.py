from __future__ import annotations

import base64
import json
import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from openhands.sdk import LLM
from openhands.sdk.llm.auth import CredentialStore, OAuthCredentials, OpenAISubscriptionAuth

from coding_orchestrator import (
    BackendContractError,
    OpenHandsBackend,
    OpenHandsProviderConfig,
)


class ProviderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.environment = patch.dict(
            os.environ, {"OH_PERSISTENCE_DIR": self.directory.name},
        )
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.config = OpenHandsProviderConfig("chatgpt_subscription", "gpt-5.6-sol")

    def save_credentials(self, *, expired: bool = False) -> CredentialStore:
        payload = base64.urlsafe_b64encode(json.dumps({
            "https://api.openai.com/auth": {"chatgpt_account_id": "test-account"},
        }).encode()).decode().rstrip("=")
        store = CredentialStore(Path(self.directory.name) / "auth")
        store.save(OAuthCredentials(
            vendor="openai",
            access_token=f"test.{payload}.signature",
            refresh_token="test-refresh-secret",
            expires_at=int(time.time() * 1000) + (-1000 if expired else 3600000),
        ))
        return store

    def test_configuration_requires_both_explicit_fields(self) -> None:
        for environment in (
            {},
            {"CODING_OPENHANDS_PROVIDER": "chatgpt_subscription"},
            {"CODING_OPENHANDS_MODEL": "gpt-5.6-sol"},
            {"OPENAI_MODEL": "gpt-5.6-sol", "OPENAI_API_KEY": "must-not-use"},
        ):
            with self.subTest(environment=environment), self.assertRaises(ValueError):
                OpenHandsProviderConfig.from_environment(environment)

    def test_configuration_rejects_unsupported_modes_and_ambiguous_models(self) -> None:
        for mode in ("", "api", "direct", "auto", "ChatGPT", "chatgpt_subscription "):
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                OpenHandsProviderConfig(mode, "gpt-5.6-sol")
        for model in ("", " ", "gpt-5.6-sol ", "openai/gpt-5.6-sol", "gpt\n5"):
            with self.subTest(model=model), self.assertRaises(ValueError):
                OpenHandsProviderConfig("chatgpt_subscription", model)

    def test_explicit_api_settings_are_rejected(self) -> None:
        environment = {
            "CODING_OPENHANDS_PROVIDER": "chatgpt_subscription",
            "CODING_OPENHANDS_MODEL": "gpt-5.6-sol",
        }
        self.assertEqual(OpenHandsProviderConfig.from_environment(environment), self.config)
        for name in ("CODING_OPENHANDS_API_KEY", "CODING_OPENHANDS_BASE_URL"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                OpenHandsProviderConfig.from_environment({**environment, name: "secret"})

    def test_unknown_model_fails_before_credentials_or_login(self) -> None:
        config = OpenHandsProviderConfig("chatgpt_subscription", "not-a-model")
        with patch.object(OpenAISubscriptionAuth, "refresh_if_needed_sync") as refresh:
            with patch.object(LLM, "subscription_login") as login:
                for operation in (config.build_llm, config.login):
                    with self.assertRaisesRegex(BackendContractError, "no fallback"):
                        operation()
                refresh.assert_not_called()
                login.assert_not_called()

    def test_missing_credentials_never_login_or_use_api_environment(self) -> None:
        with patch.dict(os.environ, {"OPENAI_API_KEY": "do-not-use"}):
            with patch.object(LLM, "subscription_login") as login:
                with self.assertRaisesRegex(BackendContractError, "login is required"):
                    self.config.build_llm()
                login.assert_not_called()

    def test_cached_credentials_create_exact_subscription_repeatedly(self) -> None:
        self.save_credentials()
        with patch.dict(os.environ, {
            "OPENAI_API_KEY": "do-not-use",
            "OPENAI_BASE_URL": "https://invalid.example.test",
        }):
            first = self.config.build_llm()
            second = self.config.build_llm()
        self.assertIsNot(first, second)
        for llm in (first, second):
            self.assertEqual(llm.model, "openai/gpt-5.6-sol")
            self.assertTrue(llm.is_subscription)
            self.assertEqual(llm.auth_type, "subscription")
            self.assertEqual(llm.subscription_vendor, "openai")
            self.assertNotIn("invalid.example.test", llm.base_url)
            self.assertIsNone(llm.api_key)

    def test_expired_credentials_refresh_through_sdk(self) -> None:
        store = self.save_credentials(expired=True)
        with patch(
            "openhands.sdk.llm.auth.openai._refresh_access_token_sync",
            return_value={
                "access_token": store.get("openai").access_token,
                "refresh_token": "renewed-refresh",
                "expires_in": 3600,
            },
        ) as refresh:
            llm = self.config.build_llm()
        refresh.assert_called_once_with("test-refresh-secret")
        self.assertFalse(store.get("openai").is_expired())
        self.assertTrue(llm.is_subscription)

    def test_refresh_failure_is_sanitized_and_never_logs_in(self) -> None:
        self.save_credentials(expired=True)
        with patch(
            "openhands.sdk.llm.auth.openai._refresh_access_token_sync",
            side_effect=RuntimeError("private-token-response"),
        ), patch.object(LLM, "subscription_login") as login:
            with self.assertRaises(BackendContractError) as error:
                self.config.build_llm()
            self.assertNotIn("private-token", str(error.exception))
            login.assert_not_called()

    def test_returned_model_or_auth_mismatch_fails_closed(self) -> None:
        self.save_credentials()
        for field, value in (
            ("model", "openai/gpt-5.5"),
            ("is_subscription", False),
            ("auth_type", "api_key"),
            ("subscription_vendor", None),
        ):
            llm = self.config.build_llm()
            setattr(llm, field, value)
            with self.subTest(field=field), patch.object(
                OpenAISubscriptionAuth, "create_llm", return_value=llm,
            ), self.assertRaisesRegex(BackendContractError, "contract mismatch"):
                self.config.build_llm()

    def test_explicit_login_has_fixed_vendor_model_and_device_flow(self) -> None:
        self.save_credentials()
        llm = self.config.build_llm()
        with patch.object(LLM, "subscription_login", return_value=llm) as login:
            self.config.login()
        login.assert_called_once_with(
            vendor="openai", model="gpt-5.6-sol", auth_method="device_code",
            open_browser=False, force_login=True,
        )

    def test_login_failure_is_sanitized(self) -> None:
        with patch.object(LLM, "subscription_login", side_effect=RuntimeError("secret")):
            with self.assertRaisesRegex(BackendContractError, "^ChatGPT subscription login failed$"):
                self.config.login()

    def test_provider_and_injected_llm_are_mutually_exclusive(self) -> None:
        with self.assertRaisesRegex(ValueError, "not both"):
            OpenHandsBackend(
                "http://127.0.0.1:8765/mcp", "test-token",
                provider=self.config, llm=object(),
            )

    def test_backend_reloads_provider_and_preserves_boundary(self) -> None:
        self.save_credentials()
        backend = OpenHandsBackend(
            "http://127.0.0.1:8765/mcp", "test-token", provider=self.config,
        )
        first = backend._build_agent()
        self.assertEqual(first.llm.model, "openai/gpt-5.6-sol")
        self.assertEqual(first.tools, [])
        self.assertEqual(first.include_default_tools, ["FinishTool"])
        self.assertEqual(set(first.mcp_config), {"coding_executor"})
        CredentialStore(Path(self.directory.name) / "auth").delete("openai")
        with self.assertRaisesRegex(BackendContractError, "login is required"):
            backend._build_agent()


if __name__ == "__main__":
    unittest.main()
