#!/usr/bin/env python3
"""Minimal stdio MCP bridge for the Synology read-only infrastructure worker."""

import json
import os
import socket
import sys


SOCKET_PATH = os.environ.get(
    "NAS_INFRA_READONLY_SOCKET",
    "/run/nas-infra-readonly/worker.sock",
)
MAX_RESPONSE = 512 * 1024

TOOLS = [
    {
        "name": "get_host_summary",
        "description": "Return a sanitized NAS host summary: hostname, kernel, architecture, and uptime.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "get_memory_status",
        "description": "Return host RAM and swap totals/usage from /proc/meminfo.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "get_disk_status",
        "description": "Return capacity and usage for the fixed Synology /volume1 filesystem.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "get_docker_version",
        "description": "Return sanitized Docker Engine server version information.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "list_containers",
        "description": "List only reviewed LibreChat-related containers and sanitized runtime state.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "inspect_container",
        "description": "Inspect one reviewed LibreChat service without exposing environment variables, labels, commands, or host mount source paths.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "service": {
                    "type": "string",
                    "enum": ["api", "mongodb", "rag_api", "vectordb", "cloudflared", "admin_settings"],
                }
            },
            "required": ["service"],
            "additionalProperties": False,
        },
    },
    {
        "name": "list_docker_networks",
        "description": "List Docker network names, drivers, scopes, and short IDs without inspection details.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "list_docker_volumes",
        "description": "List only LibreChat-related Docker volume names and drivers; host mount paths are not exposed.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "get_service_health",
        "description": "Return sanitized health/running state for reviewed LibreChat services.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "get_dsm_version",
        "description": "Return a sanitized subset of Synology DSM version metadata.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "get_deployment_state",
        "description": "Return the checked-out deployment branch/head and recorded last-success commit, without arbitrary repository access.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
]

TOOL_NAMES = {tool["name"] for tool in TOOLS}


def worker_call(action, params):
    request = (json.dumps({"action": action, "params": params}, separators=(",", ":")) + "\n").encode("utf-8")
    chunks = []
    total = 0
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
        client.settimeout(10)
        client.connect(SOCKET_PATH)
        client.sendall(request)
        while True:
            chunk = client.recv(65536)
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
            if total > MAX_RESPONSE:
                raise RuntimeError("read-only infrastructure response exceeded safety limit")
            if b"\n" in chunk:
                break
    raw = b"".join(chunks).split(b"\n", 1)[0]
    result = json.loads(raw.decode("utf-8"))
    if not result.get("ok"):
        raise RuntimeError(result.get("error") or "read-only infrastructure inspection failed")
    return result.get("result")


def emit(payload):
    sys.stdout.write(json.dumps(payload, separators=(",", ":")) + "\n")
    sys.stdout.flush()


def error_response(request_id, code, message):
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


def handle(request):
    method = request.get("method")
    request_id = request.get("id")
    params = request.get("params") or {}

    if method == "initialize":
        requested = params.get("protocolVersion") or "2024-11-05"
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": requested,
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": "nas-infra-readonly", "version": "1.0.0"},
            },
        }
    if method == "ping":
        return {"jsonrpc": "2.0", "id": request_id, "result": {}}
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": request_id, "result": {"tools": TOOLS}}
    if method == "tools/call":
        name = str(params.get("name") or "")
        arguments = params.get("arguments") or {}
        if name not in TOOL_NAMES:
            return error_response(request_id, -32602, "Unknown read-only infrastructure tool")
        if not isinstance(arguments, dict):
            return error_response(request_id, -32602, "Tool arguments must be an object")
        try:
            result = worker_call(name, arguments)
        except Exception:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [{"type": "text", "text": "Inspection failed: read-only infrastructure worker unavailable or rejected the request"}],
                    "isError": True,
                },
            }
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "content": [{"type": "text", "text": json.dumps(result, indent=2, sort_keys=True)}],
                "isError": False,
            },
        }
    if method and method.startswith("notifications/"):
        return None
    if request_id is None:
        return None
    return error_response(request_id, -32601, "Method not found")


def main():
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            request = json.loads(line)
            if not isinstance(request, dict):
                raise ValueError("request must be an object")
            response = handle(request)
        except Exception:
            response = error_response(None, -32700, "Parse error")
        if response is not None:
            emit(response)


if __name__ == "__main__":
    main()
