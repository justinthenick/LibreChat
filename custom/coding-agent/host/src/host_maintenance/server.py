from __future__ import annotations

import json
import logging
import os
import secrets
import time
from functools import wraps
from pathlib import Path

import uvicorn
from mcp.server import MCPServer
from mcp.server.auth.provider import AccessToken, TokenVerifier
from mcp.server.auth.settings import AuthSettings
from mcp.server.transport_security import TransportSecuritySettings
from pydantic import AnyHttpUrl

from host_maintenance.broker import Broker


class MaintenanceTokenVerifier(TokenVerifier):
    def __init__(self, token: str, resource: str):
        if len(token) < 32:
            raise ValueError("maintenance token must contain at least 32 characters")
        self.token, self.resource = token, resource

    async def verify_token(self, token: str) -> AccessToken | None:
        if not secrets.compare_digest(token, self.token):
            return None
        return AccessToken(token=token, client_id="librechat-maintenance", scopes=["coding:maintain"],
                           expires_at=int(time.time()) + 300, resource=self.resource,
                           subject="librechat-host-maintenance")


def audited(function):
    @wraps(function)
    def invoke(*args, **kwargs):
        request_id = secrets.token_hex(8)
        logger = logging.getLogger("coding-maintenance.audit")
        logger.info("request=%s operation=%s result=started", request_id, function.__name__)
        try:
            result = function(*args, **kwargs)
        except Exception:
            logger.warning("request=%s operation=%s result=failed", request_id, function.__name__)
            raise
        logger.info("request=%s operation=%s result=completed", request_id, function.__name__)
        return result
    return invoke


def build_server(broker: Broker, token: str, url: str) -> MCPServer:
    server = MCPServer("librechat-host-maintenance", token_verifier=MaintenanceTokenVerifier(token, url),
                       auth=AuthSettings(issuer_url=AnyHttpUrl("https://librechat.local"),
                                         resource_server_url=AnyHttpUrl(url),
                                         required_scopes=["coding:maintain"], validate_token_resource=True),
                       instructions="Use only allowlisted maintenance operations. Preview before cleanup/restart. Tickets expire after 60 seconds and are not human approval. Never infer a task is retired because it is clean. No shell, deployment, force cleanup, branch deletion or push is available.")

    @server.tool(description="Inspect only the configured executor container, image and health.")
    @audited
    def executor_health() -> dict:
        return broker.health()

    @server.tool(description="Inspect an allowlisted source. Does not fetch; freshness remains unknown until refresh.")
    @audited
    def repository_status(repository: str) -> dict:
        return broker.repository_status(repository)

    @server.tool(description="Fetch only the approved remote branch into a dedicated status ref and compare it with source HEAD. Never changes source files, index or branch. Check ok/fetch_result: dirty, detached, wrong-upstream and failed fetches return no fresh comparison.")
    @audited
    def fresh_repository_status(repository: str) -> dict:
        return broker.fresh_repository_status(repository)

    @server.tool(description="Fetch the configured GitHub source inside the executor and fast-forward only. Requires operator enablement; dirty/ahead/diverged sources are refused.")
    @audited
    def refresh_repository(repository: str) -> dict:
        return broker.refresh_repository(repository)

    @server.tool(description="Inventory worktrees without deleting or pruning. Clean does not mean retired.")
    @audited
    def task_inventory() -> dict:
        return broker.task_inventory()

    @server.tool(description="Preview one operator-retired, completely clean agent worktree; get a single-use ticket.")
    @audited
    def preview_cleanup(task_id: str) -> dict:
        return broker.preview_cleanup(task_id)

    @server.tool(description="Recheck and remove only the eligible, operator-retired worktree bound to a single-use ticket. confirm_task_id must match the preview exactly. Retains branch. Disabled without operator policy.")
    @audited
    def cleanup_task(ticket: str, confirm_task_id: str) -> dict:
        return broker.cleanup_task(ticket, confirm_task_id)

    @server.tool(description="Get bounded, privacy-filtered executor lifecycle/error events; no raw log text.")
    @audited
    def executor_logs() -> dict:
        return broker.logs()

    @server.tool(description="Preview the configured executor identity before a controlled restart.")
    @audited
    def preview_restart() -> dict:
        return broker.preview_restart()

    @server.tool(description="Restart only the unchanged previewed container, refuse active operations, enforce cooldown and verify health. No rebuild or deployment.")
    @audited
    def restart_executor(ticket: str) -> dict:
        return broker.restart_executor(ticket)

    return server


def main() -> None:
    config_path = Path(os.environ["CODING_MAINTENANCE_CONFIG"])
    config = json.loads(config_path.read_text())
    broker = Broker(config)
    if any(root == config_path.resolve() or root in config_path.resolve().parents
           for root in (broker.tasks, broker.repositories)):
        raise ValueError("maintenance policy must live outside executor mounts")
    token = os.environ["CODING_MAINTENANCE_TOKEN"]
    if token == os.environ.get("CODING_EXECUTOR_TOKEN"):
        raise ValueError("maintenance requires a separate token")
    url = os.environ["CODING_MAINTENANCE_PUBLIC_URL"]
    server = build_server(broker, token, url)
    hosts = os.environ["CODING_MAINTENANCE_ALLOWED_HOSTS"].split(",")
    if not all(hosts) or any("*" in host for host in hosts):
        raise ValueError("explicit allowed hosts required")
    app = server.streamable_http_app(stateless_http=True, json_response=True,
                                    transport_security=TransportSecuritySettings(
                                        enable_dns_rebinding_protection=True, allowed_hosts=hosts, allowed_origins=[]))
    logging.basicConfig(level=logging.INFO)
    uvicorn.run(app, host=os.environ.get("CODING_MAINTENANCE_BIND", "127.0.0.1"),
                port=int(os.environ.get("CODING_MAINTENANCE_PORT", "8766")))


if __name__ == "__main__":
    main()
