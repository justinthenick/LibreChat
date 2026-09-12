from __future__ import annotations

import secrets
import time
from dataclasses import asdict

import uvicorn
from pydantic import AnyHttpUrl
from starlette.responses import JSONResponse

from mcp.server import MCPServer
from mcp.server.auth.provider import AccessToken, TokenVerifier
from mcp.server.auth.settings import AuthSettings
from mcp.server.transport_security import TransportSecuritySettings

from coding_executor.config import Settings
from coding_executor.workspaces import WorkspaceManager


class StaticTokenVerifier(TokenVerifier):
    def __init__(self, expected_token: str, resource: str) -> None:
        self.expected_token = expected_token
        self.resource = resource

    async def verify_token(self, token: str) -> AccessToken | None:
        if not secrets.compare_digest(token, self.expected_token):
            return None
        return AccessToken(
            token=token,
            client_id="librechat",
            scopes=["coding:execute"],
            expires_at=int(time.time()) + 300,
            resource=self.resource,
            subject="librechat-coding-agent",
        )


def build_server(settings: Settings) -> MCPServer:
    manager = WorkspaceManager(
        settings.repository_root,
        settings.task_root,
        settings.command_timeout_seconds,
        settings.max_output_bytes,
    )
    server = MCPServer(
        "librechat-coding-executor",
        instructions=(
            "Work only in isolated task worktrees. Inspect before editing, make the smallest justified patch, "
            "run relevant allowlisted checks, and finish with status plus diff. This server cannot commit or push."
        ),
        token_verifier=StaticTokenVerifier(settings.bearer_token, settings.public_url),
        auth=AuthSettings(
            issuer_url=AnyHttpUrl(settings.issuer_url),
            resource_server_url=AnyHttpUrl(settings.public_url),
            required_scopes=["coding:execute"],
            validate_token_resource=True,
        ),
    )

    @server.custom_route("/health", methods=["GET"])
    async def health(_request: object) -> JSONResponse:
        return JSONResponse({"status": "ok", "version": "0.1.0"})

    @server.tool(description="List Git repositories explicitly mounted into the executor.")
    def list_repositories() -> list[str]:
        return manager.list_repositories()

    @server.tool(description="Create an isolated Git worktree and branch for one coding task.")
    def create_task(repository: str, task_name: str, base_ref: str = "HEAD") -> dict[str, str]:
        return manager.create_task(repository, task_name, base_ref)

    @server.tool(description="Show the branch and concise Git status for a task worktree.")
    def task_status(task_id: str) -> dict[str, str]:
        return manager.task_status(task_id)

    @server.tool(description="List files under a task-relative directory. Paths never escape the task worktree.")
    def list_files(task_id: str, path: str = "", max_results: int = 300) -> list[str]:
        return manager.list_files(task_id, path, max_results)

    @server.tool(description="Read a bounded line range from a regular UTF-8 file in a task worktree.")
    def read_file(task_id: str, path: str, start_line: int = 1, end_line: int = 400) -> str:
        return manager.read_file(task_id, path, start_line, end_line)

    @server.tool(description="Search task files with ripgrep using a literal query or regex.")
    def search_text(task_id: str, query: str, path: str = "", glob: str = "", max_results: int = 100) -> str:
        return manager.search_text(task_id, query, path, glob, max_results)

    @server.tool(description="Check and apply one unified diff inside a task worktree; traversal and symlink patches are rejected.")
    def apply_patch(task_id: str, patch: str) -> dict[str, str]:
        return manager.apply_patch(task_id, patch)

    @server.tool(description="Run a bounded test, lint, build, or git diff check from the executor allowlist.")
    def run_check(task_id: str, command: str, timeout_seconds: int | None = None) -> dict[str, object]:
        return asdict(manager.run_check(task_id, command, timeout_seconds))

    @server.tool(description="Return the bounded uncommitted Git diff for final human review.")
    def git_diff(task_id: str) -> str:
        return manager.diff(task_id)

    return server


def main() -> None:
    settings = Settings.from_environment()
    server = build_server(settings)
    security = TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=list(settings.allowed_hosts),
        allowed_origins=[],
    )
    app = server.streamable_http_app(
        host="0.0.0.0",
        stateless_http=True,
        json_response=True,
        transport_security=security,
    )
    uvicorn.run(app, host="0.0.0.0", port=settings.port, log_level="info")


if __name__ == "__main__":
    main()
