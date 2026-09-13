#!/usr/bin/env python3
"""Generate a sanitised, read-only runtime evidence snapshot for architecture agents.

The collector runs on the Synology host from a reviewed systemd timer. It has
privileged local visibility, but it emits only an allowlisted JSON projection.
No environment values, Docker socket, raw logs, host bind sources, container IPs,
or arbitrary command interface are exposed to LibreChat.
"""

import argparse
import datetime as dt
import json
import os
import platform
import subprocess
import tempfile
from typing import Any, Dict, Iterable, List, Optional, Tuple

SCHEMA_VERSION = 1
DEFAULT_OUTPUT_DIR = "/volume1/docker/librechat/runtime-evidence"
DEFAULT_STATE_FILE = "/volume1/docker/librechat-deploy.last-success"

CONTAINERS = {
    "api": "librechat",
    "mongodb": "librechat-mongodb",
    "rag_api": "librechat-rag-api",
    "vectordb": "librechat-vectordb",
    "cloudflared": "librechat-cloudflared",
    "admin_settings": "librechat-admin-settings",
}

DSM_KEYS = ("productversion", "buildnumber", "smallfixnumber", "buildphase")
MEMINFO_KEYS = ("MemTotal", "MemAvailable", "SwapTotal", "SwapFree")
FORBIDDEN_KEYS = {
    "env",
    "environment",
    "token",
    "secret",
    "password",
    "credential",
    "credentials",
    "source",
    "mountpoint",
    "ip",
    "ipaddress",
    "ip_address",
    "mac",
    "macaddress",
    "mac_address",
}


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")


def run(command: List[str], timeout: int = 10) -> Tuple[int, str]:
    try:
        proc = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=timeout,
            check=False,
        )
        return proc.returncode, proc.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        return 127, ""


def read_text(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as handle:
            return handle.read().strip()
    except OSError:
        return ""


def dsm_version() -> Dict[str, str]:
    values: Dict[str, str] = {}
    for path in ("/etc.defaults/VERSION", "/etc/VERSION"):
        text = read_text(path)
        if not text:
            continue
        for raw_line in text.splitlines():
            if "=" not in raw_line:
                continue
            key, value = raw_line.split("=", 1)
            key = key.strip()
            if key not in DSM_KEYS or key in values:
                continue
            values[key] = value.strip().strip('"').strip("'")
        if values:
            break
    return values


def meminfo() -> Dict[str, int]:
    result: Dict[str, int] = {}
    text = read_text("/proc/meminfo")
    for raw_line in text.splitlines():
        if ":" not in raw_line:
            continue
        key, value = raw_line.split(":", 1)
        if key not in MEMINFO_KEYS:
            continue
        parts = value.strip().split()
        if not parts:
            continue
        try:
            result[key.lower() + "_kb"] = int(parts[0])
        except ValueError:
            continue
    if "swaptotal_kb" in result and "swapfree_kb" in result:
        result["swapused_kb"] = max(0, result["swaptotal_kb"] - result["swapfree_kb"])
    return result


def disk_status(path: str = "/volume1") -> Dict[str, Any]:
    try:
        stat = os.statvfs(path)
        total = stat.f_blocks * stat.f_frsize
        free = stat.f_bfree * stat.f_frsize
        available = stat.f_bavail * stat.f_frsize
        used = max(0, total - free)
        percent = round((used / total) * 100.0, 1) if total else None
        return {
            "path": path,
            "total_bytes": total,
            "used_bytes": used,
            "available_bytes": available,
            "used_percent": percent,
        }
    except OSError:
        return {"path": path, "status": "unavailable"}


def host_summary() -> Dict[str, Any]:
    rc, docker_version = run(["docker", "version", "--format", "{{.Server.Version}}"])
    try:
        load = [round(value, 2) for value in os.getloadavg()]
    except OSError:
        load = []
    uptime = read_text("/proc/uptime").split()
    uptime_seconds: Optional[int] = None
    if uptime:
        try:
            uptime_seconds = int(float(uptime[0]))
        except ValueError:
            pass
    return {
        "architecture": platform.machine(),
        "kernel_release": platform.release(),
        "cpu_count": os.cpu_count(),
        "load_average_1m_5m_15m": load,
        "uptime_seconds": uptime_seconds,
        "dsm": dsm_version(),
        "memory": meminfo(),
        "volume1": disk_status(),
        "docker_server_version": docker_version if rc == 0 and docker_version else "unavailable",
    }


def safe_mounts(mounts: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    safe: List[Dict[str, Any]] = []
    for mount in mounts:
        mount_type = str(mount.get("Type") or "unknown")
        item: Dict[str, Any] = {
            "type": mount_type,
            "destination": str(mount.get("Destination") or ""),
            "read_only": not bool(mount.get("RW", False)),
        }
        if mount_type == "volume":
            item["name"] = str(mount.get("Name") or "")
        safe.append(item)
    return safe


def inspect_container(service: str, name: str) -> Dict[str, Any]:
    rc, output = run(["docker", "inspect", name])
    if rc != 0 or not output:
        return {"service": service, "container": name, "present": False}
    try:
        payload = json.loads(output)[0]
    except (ValueError, IndexError, TypeError):
        return {"service": service, "container": name, "present": True, "inspection": "unavailable"}

    state = payload.get("State") or {}
    config = payload.get("Config") or {}
    network_settings = payload.get("NetworkSettings") or {}
    networks = network_settings.get("Networks") or {}
    health = state.get("Health") or {}
    return {
        "service": service,
        "container": name,
        "present": True,
        "image": str(config.get("Image") or ""),
        "status": str(state.get("Status") or "unknown"),
        "running": bool(state.get("Running", False)),
        "exit_code": state.get("ExitCode"),
        "restart_count": payload.get("RestartCount"),
        "health": str(health.get("Status") or "not_defined"),
        "started_at": str(state.get("StartedAt") or ""),
        "finished_at": str(state.get("FinishedAt") or ""),
        "network_names": sorted(str(key) for key in networks.keys()),
        "mounts": safe_mounts(payload.get("Mounts") or []),
    }


def inspect_network(name: str) -> Dict[str, Any]:
    rc, output = run(["docker", "network", "inspect", name])
    if rc != 0 or not output:
        return {"name": name, "present": False}
    try:
        payload = json.loads(output)[0]
    except (ValueError, IndexError, TypeError):
        return {"name": name, "present": True, "inspection": "unavailable"}
    return {
        "name": name,
        "present": True,
        "driver": str(payload.get("Driver") or ""),
        "scope": str(payload.get("Scope") or ""),
        "internal": bool(payload.get("Internal", False)),
        "attachable": bool(payload.get("Attachable", False)),
        "container_count": len(payload.get("Containers") or {}),
    }


def inspect_volume(name: str) -> Dict[str, Any]:
    rc, output = run(["docker", "volume", "inspect", name])
    if rc != 0 or not output:
        return {"name": name, "present": False}
    try:
        payload = json.loads(output)[0]
    except (ValueError, IndexError, TypeError):
        return {"name": name, "present": True, "inspection": "unavailable"}
    return {
        "name": name,
        "present": True,
        "driver": str(payload.get("Driver") or ""),
        "scope": str(payload.get("Scope") or ""),
    }


def api_http_health() -> str:
    script = (
        'const http=require("http");'
        'const req=http.get("http://127.0.0.1:3080/api/config",res=>'
        'process.exit(res.statusCode>=200&&res.statusCode<500?0:1));'
        'req.setTimeout(5000,()=>{req.destroy();process.exit(1)});'
        'req.on("error",()=>process.exit(1));'
    )
    rc, _ = run(["docker", "exec", "librechat", "node", "-e", script], timeout=7)
    return "pass" if rc == 0 else "fail"


def cloudflare_health(containers: Dict[str, Dict[str, Any]]) -> str:
    item = containers.get("cloudflared") or {}
    if not item.get("present"):
        return "disabled"
    if not item.get("running"):
        return "fail"
    rc, output = run(["docker", "logs", "--tail=200", "librechat-cloudflared"], timeout=7)
    if rc == 0 and "Registered tunnel connection" in output:
        return "connected"
    return "running_unregistered"


def admin_worker_health() -> str:
    rc, output = run(["systemctl", "is-active", "librechat-admin-settings-worker.service"], timeout=5)
    if rc == 0 and output == "active":
        return "active"
    if output in ("inactive", "failed", "activating", "deactivating"):
        return output
    return "not_configured_or_unavailable"


def service_health(containers: Dict[str, Dict[str, Any]]) -> Dict[str, str]:
    def docker_health(service: str) -> str:
        item = containers.get(service) or {}
        if not item.get("present"):
            return "absent"
        if not item.get("running"):
            return "not_running"
        status = str(item.get("health") or "not_defined")
        return "running" if status == "not_defined" else status

    return {
        "librechat_http": api_http_health(),
        "mongodb": docker_health("mongodb"),
        "rag_api": docker_health("rag_api"),
        "vectordb": docker_health("vectordb"),
        "cloudflare_tunnel": cloudflare_health(containers),
        "admin_settings_container": docker_health("admin_settings"),
        "admin_settings_worker": admin_worker_health(),
    }


def collect_runtime(branch: str, commit: str, stage: str, state_file: str) -> Dict[str, Any]:
    last_success = read_text(state_file)
    effective_commit = commit or last_success or "unknown"
    containers = {
        service: inspect_container(service, name) for service, name in CONTAINERS.items()
    }

    network_names = sorted(
        {
            network
            for item in containers.values()
            for network in (item.get("network_names") or [])
            if network
        }
    )
    volume_names = sorted(
        {
            str(mount.get("name"))
            for item in containers.values()
            for mount in (item.get("mounts") or [])
            if mount.get("type") == "volume" and mount.get("name")
        }
    )

    snapshot: Dict[str, Any] = {
        "schema": SCHEMA_VERSION,
        "generated_at": now_iso(),
        "evidence_type": "sanitised_runtime_snapshot",
        "deployment": {
            "branch": branch,
            "commit": effective_commit,
            "collector_stage": stage,
            "last_success_commit": last_success,
        },
        "host": host_summary(),
        "containers": containers,
        "networks": [inspect_network(name) for name in network_names],
        "volumes": [inspect_volume(name) for name in volume_names],
        "service_health": service_health(containers),
        "safety": {
            "environment_values_exposed": False,
            "raw_logs_exposed": False,
            "container_addresses_exposed": False,
            "host_bind_sources_exposed": False,
            "docker_socket_exposed_to_agent": False,
            "generic_command_execution_exposed_to_agent": False,
        },
    }
    assert_snapshot_safe(snapshot)
    return snapshot


def assert_snapshot_safe(value: Any, path: str = "root") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = str(key).lower()
            if normalized in FORBIDDEN_KEYS:
                raise RuntimeError("refusing to emit forbidden key at {}.{}".format(path, key))
            assert_snapshot_safe(child, "{}.{}".format(path, key))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            assert_snapshot_safe(child, "{}[{}]".format(path, index))


def write_snapshot(output_dir: str, snapshot: Dict[str, Any]) -> str:
    os.makedirs(output_dir, exist_ok=True)
    target = os.path.join(output_dir, "latest.json")
    fd, temp_path = tempfile.mkstemp(prefix=".latest.", suffix=".json", dir=output_dir)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(snapshot, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temp_path, 0o640)
        try:
            os.chown(temp_path, 0, 100)
        except PermissionError:
            pass
        os.replace(temp_path, target)
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)
    return target


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--state-file", default=DEFAULT_STATE_FILE)
    parser.add_argument("--branch", default="server/synology")
    parser.add_argument("--commit", default="")
    parser.add_argument("--stage", default="timer")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    snapshot = collect_runtime(args.branch, args.commit, args.stage, args.state_file)
    write_snapshot(args.output_dir, snapshot)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
