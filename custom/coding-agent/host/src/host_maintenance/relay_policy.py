from __future__ import annotations

import re
import hmac
from pathlib import Path

from host_maintenance.acp_sandbox import ACP_NETWORK, ACP_RELAY_CONTAINER


def validate_relay(info: dict, image: str, socket_directory: Path, signing_key: bytes) -> None:
    """Reject runtime drift before authorizing a contained provider session."""
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", image):
        raise RuntimeError("ACP relay image must be pinned")
    host = info.get("HostConfig", {})
    config = info.get("Config", {})
    if (info.get("Name") != "/" + ACP_RELAY_CONTAINER
            or info.get("Image") != image
            or info.get("State", {}).get("Running") is not True):
        raise RuntimeError("ACP relay identity or image mismatch")
    if (config.get("User") != "10001:10001"
            or config.get("Entrypoint") != ["python3", "/app/relay.py"]
            or config.get("Cmd") not in (None, [])
            or host.get("ReadonlyRootfs") is not True
            or host.get("Privileged") is not False
            or set(host.get("CapDrop") or []) != {"ALL"}
            or host.get("CapAdd") or host.get("Devices")
            or host.get("PidMode") not in (None, "")
            or host.get("IpcMode") not in (None, "private")
            or not any(v in {"no-new-privileges", "no-new-privileges:true", "no-new-privileges=true"}
                       for v in host.get("SecurityOpt", []))):
        raise RuntimeError("ACP relay process isolation mismatch")
    if (host.get("NetworkMode") != ACP_NETWORK
            or set(info.get("NetworkSettings", {}).get("Networks", {})) != {ACP_NETWORK}
            or host.get("PortBindings") or host.get("PublishAllPorts")
            or host.get("ExtraHosts") or host.get("Links")):
        raise RuntimeError("ACP relay network policy mismatch")
    mounts = info.get("Mounts", [])
    if (len(mounts) != 1
            or mounts[0].get("Type") != "bind"
            or mounts[0].get("Source") != str(socket_directory)
            or mounts[0].get("Destination") != "/run/codex-adapter"
            or mounts[0].get("RW") is not False
            or mounts[0].get("Propagation") != "rprivate"):
        raise RuntimeError("ACP relay socket-directory bind mismatch")
    if (host.get("PidsLimit") != 64 or host.get("Memory") != 128 * 1024 * 1024
            or host.get("MemorySwap") != 128 * 1024 * 1024
            or host.get("NanoCpus") != 500_000_000):
        raise RuntimeError("ACP relay resource policy mismatch")
    entries = [value.split("=", 1) for value in config.get("Env", []) if "=" in value]
    environment = dict(entries)
    if len(environment) != len(entries):
        raise RuntimeError("ACP relay environment policy mismatch")
    actual_key = environment.get("RELAY_SIGNING_KEY", "")
    if (len(signing_key) != 32 or not re.fullmatch(r"[0-9a-f]{64}", actual_key)
            or not hmac.compare_digest(actual_key, signing_key.hex())):
        raise RuntimeError("ACP relay signing key mismatch")
    if (environment.get("CODEX_ADAPTER_SOCKET") != "/run/codex-adapter/codex.sock"
            or environment.get("ALLOWED_MODEL") != "coding-agent-text"
            or any(key in environment for key in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY"))):
        raise RuntimeError("ACP relay environment policy mismatch")
