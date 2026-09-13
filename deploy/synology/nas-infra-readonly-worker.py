#!/usr/bin/env python3
"""Read-only Synology infrastructure inspection worker.

This host-side worker exposes a deliberately narrow JSON-lines protocol over a
Unix-domain socket. It has no generic shell, arbitrary file-read, Docker exec,
container lifecycle, or environment access actions. Every host/Docker query is
fixed and sanitized before it crosses the socket boundary.
"""

import argparse
import json
import os
from pathlib import Path
import platform
import shutil
import socket
import socketserver
import subprocess
import urllib.request


MAX_REQUEST = 64 * 1024
MAX_RESPONSE = 512 * 1024
DEFAULT_SOCKET = "/volume1/docker/librechat/nas-infra-readonly-state/worker.sock"
DEPLOY_STATE_FILE = Path("/volume1/docker/librechat-deploy.last-success")
REPO_DIR = Path("/volume1/docker/librechat")
VOLUME1 = Path("/volume1")
DSM_VERSION = Path("/etc/VERSION")

ALLOWED_CONTAINERS = {
    "api": "librechat",
    "mongodb": "librechat-mongodb",
    "rag_api": "librechat-rag-api",
    "vectordb": "librechat-vectordb",
    "cloudflared": "librechat-cloudflared",
    "admin_settings": "librechat-admin-settings",
}

ACTIONS = {
    "ping",
    "get_host_summary",
    "get_memory_status",
    "get_disk_status",
    "get_docker_version",
    "list_containers",
    "inspect_container",
    "list_docker_networks",
    "list_docker_volumes",
    "get_service_health",
    "get_dsm_version",
    "get_deployment_state",
}


class WorkerError(RuntimeError):
    pass


def run_fixed(command, timeout=10):
    """Run a fixed argv list and return stdout, never exposing stderr."""
    try:
        proc = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError as exc:
        raise WorkerError("Required host command is unavailable") from exc
    except subprocess.TimeoutExpired as exc:
        raise WorkerError("Host inspection command timed out") from exc
    if proc.returncode != 0:
        raise WorkerError("Host inspection command failed")
    return proc.stdout


def docker_inspect(name):
    raw = run_fixed(["docker", "inspect", name], timeout=10)
    try:
        items = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise WorkerError("Docker returned invalid inspection data") from exc
    if not items:
        raise WorkerError("Container is not present")
    return items[0]


def safe_container_snapshot(service, name):
    item = docker_inspect(name)
    state = item.get("State") or {}
    config = item.get("Config") or {}
    network_settings = item.get("NetworkSettings") or {}
    networks = network_settings.get("Networks") or {}
    health = state.get("Health") or {}
    mounts = []
    for mount in item.get("Mounts") or []:
        mounts.append(
            {
                "type": mount.get("Type"),
                "destination": mount.get("Destination"),
                "mode": mount.get("Mode"),
                "rw": bool(mount.get("RW")),
            }
        )
    ports = {}
    for key, bindings in (network_settings.get("Ports") or {}).items():
        safe_bindings = []
        for binding in bindings or []:
            safe_bindings.append(
                {
                    "host_ip": binding.get("HostIp"),
                    "host_port": binding.get("HostPort"),
                }
            )
        ports[key] = safe_bindings
    return {
        "service": service,
        "container": name,
        "id": str(item.get("Id") or "")[:12],
        "image": config.get("Image"),
        "state": {
            "status": state.get("Status"),
            "running": bool(state.get("Running")),
            "restarting": bool(state.get("Restarting")),
            "exit_code": state.get("ExitCode"),
            "started_at": state.get("StartedAt"),
            "finished_at": state.get("FinishedAt"),
            "health": health.get("Status") or "none",
        },
        "restart_count": item.get("RestartCount"),
        "networks": sorted(networks.keys()),
        "ports": ports,
        "mounts": mounts,
    }


def get_host_summary():
    uname = platform.uname()
    try:
        uptime_seconds = int(float(Path("/proc/uptime").read_text(encoding="utf-8").split()[0]))
    except (OSError, ValueError, IndexError):
        uptime_seconds = None
    return {
        "hostname": socket.gethostname(),
        "system": uname.system,
        "kernel": uname.release,
        "machine": uname.machine,
        "uptime_seconds": uptime_seconds,
    }


def get_memory_status():
    values = {}
    try:
        for line in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
            if ":" not in line:
                continue
            key, rest = line.split(":", 1)
            parts = rest.strip().split()
            if not parts:
                continue
            try:
                value = int(parts[0])
            except ValueError:
                continue
            values[key] = value * 1024
    except OSError as exc:
        raise WorkerError("Could not read host memory status") from exc

    total = values.get("MemTotal")
    available = values.get("MemAvailable")
    swap_total = values.get("SwapTotal")
    swap_free = values.get("SwapFree")
    return {
        "memory_total_bytes": total,
        "memory_available_bytes": available,
        "memory_used_bytes": (total - available) if total is not None and available is not None else None,
        "swap_total_bytes": swap_total,
        "swap_free_bytes": swap_free,
        "swap_used_bytes": (swap_total - swap_free)
        if swap_total is not None and swap_free is not None
        else None,
    }


def get_disk_status():
    try:
        usage = shutil.disk_usage(str(VOLUME1))
    except OSError as exc:
        raise WorkerError("Could not read /volume1 capacity") from exc
    used_percent = round((usage.used / usage.total) * 100, 1) if usage.total else None
    return {
        "path": str(VOLUME1),
        "total_bytes": usage.total,
        "used_bytes": usage.used,
        "free_bytes": usage.free,
        "used_percent": used_percent,
    }


def get_docker_version():
    template = "{{.Server.Version}}\t{{.Server.APIVersion}}\t{{.Server.Os}}\t{{.Server.Arch}}\t{{.Server.KernelVersion}}"
    line = run_fixed(["docker", "version", "--format", template], timeout=10).strip()
    parts = line.split("\t")
    while len(parts) < 5:
        parts.append("")
    return {
        "server_version": parts[0],
        "api_version": parts[1],
        "os": parts[2],
        "arch": parts[3],
        "kernel_version": parts[4],
    }


def list_containers():
    rows = []
    for service, name in ALLOWED_CONTAINERS.items():
        try:
            snapshot = safe_container_snapshot(service, name)
        except WorkerError:
            rows.append({"service": service, "container": name, "present": False})
            continue
        rows.append(
            {
                "service": service,
                "container": name,
                "present": True,
                "image": snapshot.get("image"),
                "status": snapshot["state"]["status"],
                "running": snapshot["state"]["running"],
                "health": snapshot["state"]["health"],
                "restart_count": snapshot.get("restart_count"),
            }
        )
    return rows


def inspect_container(params):
    service = str((params or {}).get("service") or "")
    name = ALLOWED_CONTAINERS.get(service)
    if not name:
        raise WorkerError("Unknown service; inspection is limited to the reviewed LibreChat service allowlist")
    return safe_container_snapshot(service, name)


def list_docker_networks():
    output = run_fixed(
        ["docker", "network", "ls", "--format", "{{.ID}}\t{{.Name}}\t{{.Driver}}\t{{.Scope}}"],
        timeout=10,
    )
    rows = []
    for line in output.splitlines():
        parts = line.split("\t")
        if len(parts) != 4:
            continue
        rows.append(
            {
                "id": parts[0][:12],
                "name": parts[1],
                "driver": parts[2],
                "scope": parts[3],
            }
        )
    return rows


def list_docker_volumes():
    output = run_fixed(
        ["docker", "volume", "ls", "--format", "{{.Name}}\t{{.Driver}}"],
        timeout=10,
    )
    rows = []
    for line in output.splitlines():
        parts = line.split("\t")
        if len(parts) != 2:
            continue
        name, driver = parts
        if name.startswith("librechat") or name in {
            "mongo-data",
            "rag-pgdata",
            "librechat-data",
            "librechat-images",
            "librechat-uploads",
            "librechat-logs",
        }:
            rows.append({"name": name, "driver": driver})
    return rows


def _api_http_health(snapshot):
    bindings = (snapshot.get("ports") or {}).get("3080/tcp") or []
    host_port = None
    for binding in bindings:
        if binding.get("host_port"):
            host_port = binding["host_port"]
            break
    if not host_port:
        return "not_published"
    try:
        request = urllib.request.Request("http://127.0.0.1:{}/api/config".format(host_port), method="GET")
        with urllib.request.urlopen(request, timeout=5) as response:
            code = int(response.status)
        return "pass" if 200 <= code < 500 else "fail"
    except Exception:
        return "fail"


def get_service_health():
    services = []
    for service, name in ALLOWED_CONTAINERS.items():
        try:
            snapshot = safe_container_snapshot(service, name)
        except WorkerError:
            services.append({"service": service, "container": name, "present": False, "health": "absent"})
            continue
        health = snapshot["state"]["health"]
        if service == "api":
            health = _api_http_health(snapshot) if snapshot["state"]["running"] else "fail"
        elif health == "none":
            health = "running" if snapshot["state"]["running"] else "stopped"
        services.append(
            {
                "service": service,
                "container": name,
                "present": True,
                "state": snapshot["state"]["status"],
                "health": health,
                "restart_count": snapshot.get("restart_count"),
            }
        )
    return services


def get_dsm_version():
    if not DSM_VERSION.exists():
        return {"present": False}
    allowed = {
        "majorversion",
        "minorversion",
        "productversion",
        "buildnumber",
        "smallfixnumber",
        "buildphase",
    }
    values = {}
    try:
        for line in DSM_VERSION.read_text(encoding="utf-8", errors="replace").splitlines():
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            if key not in allowed:
                continue
            values[key] = value.strip().strip('"')
    except OSError as exc:
        raise WorkerError("Could not read DSM version metadata") from exc
    values["present"] = True
    return values


def _read_repo_head():
    head = REPO_DIR / ".git" / "HEAD"
    try:
        raw = head.read_text(encoding="utf-8").strip()
    except OSError:
        return {"branch": None, "commit": None}
    if raw.startswith("ref: "):
        ref = raw[5:].strip()
        branch = ref[len("refs/heads/") :] if ref.startswith("refs/heads/") else ref
        ref_file = REPO_DIR / ".git" / ref
        try:
            commit = ref_file.read_text(encoding="utf-8").strip()
        except OSError:
            commit = None
            packed = REPO_DIR / ".git" / "packed-refs"
            try:
                for line in packed.read_text(encoding="utf-8").splitlines():
                    if line.startswith("#") or line.startswith("^") or " " not in line:
                        continue
                    sha, candidate = line.split(" ", 1)
                    if candidate.strip() == ref:
                        commit = sha
                        break
            except OSError:
                pass
        return {"branch": branch, "commit": commit}
    return {"branch": None, "commit": raw or None}


def get_deployment_state():
    repo = _read_repo_head()
    try:
        deployed = DEPLOY_STATE_FILE.read_text(encoding="utf-8").splitlines()[0].strip()
    except (OSError, IndexError):
        deployed = None
    return {
        "repository_branch": repo.get("branch"),
        "repository_head_commit": repo.get("commit"),
        "recorded_success_commit": deployed,
        "recorded_success_matches_head": bool(deployed and repo.get("commit") and deployed == repo.get("commit")),
    }


def dispatch(action, params=None):
    if action not in ACTIONS:
        raise WorkerError("Unsupported read-only action")
    if action == "ping":
        return {"status": "ok", "version": "1.0.0"}
    if action == "get_host_summary":
        return get_host_summary()
    if action == "get_memory_status":
        return get_memory_status()
    if action == "get_disk_status":
        return get_disk_status()
    if action == "get_docker_version":
        return get_docker_version()
    if action == "list_containers":
        return list_containers()
    if action == "inspect_container":
        return inspect_container(params or {})
    if action == "list_docker_networks":
        return list_docker_networks()
    if action == "list_docker_volumes":
        return list_docker_volumes()
    if action == "get_service_health":
        return get_service_health()
    if action == "get_dsm_version":
        return get_dsm_version()
    if action == "get_deployment_state":
        return get_deployment_state()
    raise WorkerError("Unsupported read-only action")


class RequestHandler(socketserver.StreamRequestHandler):
    def handle(self):
        raw = self.rfile.readline(MAX_REQUEST + 1)
        if len(raw) > MAX_REQUEST:
            self._write({"ok": False, "error": "request_too_large"})
            return
        try:
            request = json.loads(raw.decode("utf-8"))
            if not isinstance(request, dict):
                raise WorkerError("Request must be a JSON object")
            action = request.get("action")
            params = request.get("params") or {}
            if not isinstance(params, dict):
                raise WorkerError("params must be a JSON object")
            result = dispatch(action, params)
            self._write({"ok": True, "result": result})
        except WorkerError as exc:
            self._write({"ok": False, "error": str(exc)})
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._write({"ok": False, "error": "invalid_json"})
        except Exception:
            self._write({"ok": False, "error": "inspection_failed"})

    def _write(self, payload):
        encoded = (json.dumps(payload, separators=(",", ":"), sort_keys=True) + "\n").encode("utf-8")
        if len(encoded) > MAX_RESPONSE:
            encoded = b'{"ok":false,"error":"response_too_large"}\n'
        self.wfile.write(encoded)
        self.wfile.flush()


class UnixServer(socketserver.ThreadingMixIn, socketserver.UnixStreamServer):
    daemon_threads = True
    allow_reuse_address = True


def serve(socket_path, socket_group):
    path = Path(socket_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(str(path.parent), 0o770)
    except OSError:
        pass
    if path.exists() or path.is_socket():
        path.unlink()
    server = UnixServer(str(path), RequestHandler)
    try:
        os.chmod(str(path), 0o660)
        if socket_group is not None:
            os.chown(str(path), 0, int(socket_group))
        server.serve_forever(poll_interval=0.5)
    finally:
        server.server_close()
        try:
            path.unlink()
        except OSError:
            pass


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--socket", default=DEFAULT_SOCKET)
    parser.add_argument("--socket-group", type=int, default=100)
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("serve")
    query = sub.add_parser("query")
    query.add_argument("action", choices=sorted(ACTIONS - {"ping"}))
    args = parser.parse_args()

    if args.command == "serve":
        serve(args.socket, args.socket_group)
        return 0
    if args.command == "query":
        print(json.dumps(dispatch(args.action, {}), indent=2, sort_keys=True))
        return 0
    parser.error("command is required")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
