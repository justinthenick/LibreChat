#!/usr/bin/env python3
"""Install/refresh the Synology runtime-evidence systemd service and timer."""

import json
import os
import pathlib
import subprocess
import sys
import tempfile

DEPLOY_DIR = pathlib.Path("/volume1/docker/librechat/deploy/synology")
COLLECTOR = DEPLOY_DIR / "runtime-evidence.py"
OUTPUT_DIR = pathlib.Path("/volume1/docker/librechat/runtime-evidence")
SERVICE_PATH = pathlib.Path("/etc/systemd/system/librechat-runtime-evidence.service")
TIMER_PATH = pathlib.Path("/etc/systemd/system/librechat-runtime-evidence.timer")

SERVICE_TEXT = """[Unit]
Description=LibreChat Synology sanitised runtime evidence collector
After=docker.service
Wants=docker.service

[Service]
Type=oneshot
User=root
Group=root
WorkingDirectory=/volume1/docker/librechat/deploy/synology
ExecStart=/usr/bin/python3 /volume1/docker/librechat/deploy/synology/runtime-evidence.py --output-dir /volume1/docker/librechat/runtime-evidence --branch server/synology --stage timer
"""

TIMER_TEXT = """[Unit]
Description=Refresh LibreChat Synology sanitised runtime evidence

[Timer]
OnBootSec=90s
OnUnitActiveSec=300s
AccuracySec=30s
Persistent=true
Unit=librechat-runtime-evidence.service

[Install]
WantedBy=timers.target
"""


def run(*args: str) -> None:
    subprocess.run(args, check=True)


def write_if_changed(path: pathlib.Path, text: str) -> bool:
    if path.exists() and path.read_text(encoding="utf-8") == text:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temp_name, 0o644)
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)
    return True


def validate_snapshot() -> None:
    snapshot_path = OUTPUT_DIR / "latest.json"
    if not snapshot_path.is_file():
        raise RuntimeError("runtime evidence snapshot was not created")
    with snapshot_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if payload.get("evidence_type") != "sanitised_runtime_snapshot":
        raise RuntimeError("runtime evidence snapshot has unexpected evidence_type")
    if not payload.get("generated_at"):
        raise RuntimeError("runtime evidence snapshot has no generated_at timestamp")


def main() -> int:
    if os.geteuid() != 0:
        print("ERROR: run with sudo/root", file=sys.stderr)
        return 2
    if not COLLECTOR.is_file():
        print("ERROR: runtime-evidence.py is missing from the deployed Synology checkout", file=sys.stderr)
        return 2

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    os.chown(str(OUTPUT_DIR), 0, 100)
    os.chmod(str(OUTPUT_DIR), 0o750)

    changed = write_if_changed(SERVICE_PATH, SERVICE_TEXT)
    changed = write_if_changed(TIMER_PATH, TIMER_TEXT) or changed
    if changed:
        run("systemctl", "daemon-reload")

    run("systemctl", "enable", "librechat-runtime-evidence.timer")
    run("systemctl", "restart", "librechat-runtime-evidence.timer")
    run("systemctl", "start", "librechat-runtime-evidence.service")
    validate_snapshot()

    print("Runtime evidence collector installed and snapshot generated.")
    print("Timer: librechat-runtime-evidence.timer (300 second refresh interval)")
    print("Snapshot: /volume1/docker/librechat/runtime-evidence/latest.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
