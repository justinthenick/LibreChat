#!/usr/bin/env python3
"""Privileged apply worker for Synology Admin Settings.

The browser-facing panel never receives the private .env file and never gets
Docker access. It talks to this host-side worker over a Unix-domain socket.
The worker validates every requested key against admin-settings.schema.json,
backs up and atomically updates .env, validates Compose, recreates only affected
services, health-checks them, and rolls the previous .env back on failure.
"""

import argparse
import datetime as dt
import importlib.util
import json
import os
from pathlib import Path
import socket
import socketserver
import subprocess
import threading
import time
import urllib.request


ROOT = Path(__file__).resolve().parent
DEFAULT_ENV = ROOT / ".env"
DEFAULT_SCHEMA = ROOT / "admin-settings.schema.json"
DEFAULT_STATE = Path("/volume1/docker/librechat/admin-settings-state")
MAX_REQUEST = 128 * 1024

SPEC = importlib.util.spec_from_file_location("manage_env", ROOT / "manage-env.py")
manage_env = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(manage_env)


class WorkerError(RuntimeError):
    pass


def utc_now():
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def audit(state_dir, action, keys, outcome, detail=None):
    state_dir.mkdir(parents=True, exist_ok=True)
    entry = {
        "time": utc_now(),
        "action": action,
        "keys": sorted(set(keys or [])),
        "outcome": outcome,
    }
    if detail:
        entry["detail"] = str(detail)[:500]
    path = state_dir / "audit.log"
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")
    try:
        os.chmod(str(path), 0o640)
    except OSError:
        pass


def load_context(env_path, schema_path):
    schema, settings = manage_env.load_schema(schema_path)
    lines, values, positions = manage_env.read_env(env_path, set(settings))
    return schema, settings, lines, values, positions


def sanitize_state(schema, settings, values):
    derived = manage_env.derive_values(values)
    groups = schema.get("groups") or []
    items = []
    for item in schema.get("settings") or []:
        if item.get("ui_hidden") or item.get("class") == "internal":
            continue
        key = item["key"]
        cls = item.get("class")
        row = {
            "key": key,
            "label": item.get("label", key),
            "group": item.get("group"),
            "class": cls,
            "control": item.get("control"),
            "options": item.get("options") or [],
            "restart": item.get("restart", "none"),
            "description": item.get("description"),
            "warning": item.get("warning"),
        }
        if cls == "replace_only_secret":
            row["configured"] = manage_env.configured(values.get(key))
        elif cls == "derived":
            row["value"] = derived.get(key, "")
        else:
            row["value"] = values.get(key, "")
        items.append(row)
    return {
        "schema": schema.get("schema"),
        "title": schema.get("title"),
        "groups": groups,
        "settings": items,
        "derived": derived,
    }


def validation_warnings(values):
    warnings = []
    if values.get("LIBRECHAT_SCHEME") == "https" and values.get("SESSION_COOKIE_SECURE", "").lower() != "true":
        warnings.append("LIBRECHAT_SCHEME=https but SESSION_COOKIE_SECURE is not true")
    if values.get("LIBRECHAT_SCHEME") == "http" and values.get("SESSION_COOKIE_SECURE", "").lower() == "true":
        warnings.append("SESSION_COOKIE_SECURE=true while LIBRECHAT_SCHEME=http may prevent browser sessions on plain HTTP")
    return warnings


def build_plan(schema, settings, values, payload):
    updates = payload.get("updates") or {}
    secrets = payload.get("secrets") or {}
    if not isinstance(updates, dict) or not isinstance(secrets, dict):
        raise WorkerError("updates and secrets must be JSON objects")
    if len(updates) + len(secrets) > 40:
        raise WorkerError("Too many settings in one request")

    normalized = {}
    secret_keys = set()
    changed_keys = []
    services = set()
    impacts = set()

    for key, raw in updates.items():
        spec = settings.get(str(key))
        if not spec or spec.get("class") != "editable" or spec.get("ui_hidden"):
            raise WorkerError("{} is not editable from the web panel".format(key))
        value = manage_env.validate_value(spec, raw)
        if values.get(key, "") == value:
            continue
        normalized[key] = value
        changed_keys.append(key)
        impacts.add(spec.get("restart", "none"))
        services.update(spec.get("services") or [])

    for key, raw in secrets.items():
        spec = settings.get(str(key))
        if not spec or spec.get("class") != "replace_only_secret" or spec.get("ui_hidden"):
            raise WorkerError("{} is not replaceable from the web panel".format(key))
        value = str(raw)
        if not value:
            raise WorkerError("Empty replacement rejected for {}. Use the host CLI for an intentional clear.".format(key))
        if "\n" in value or "\r" in value:
            raise WorkerError("Secret values cannot contain newlines")
        normalized[key] = value
        secret_keys.add(key)
        changed_keys.append(key)
        impacts.add(spec.get("restart", "none"))
        services.update(spec.get("services") or [])

    proposed = dict(values)
    proposed.update(normalized)
    derived = manage_env.derive_values(proposed)
    preview = []
    for key in changed_keys:
        spec = settings[key]
        if key in secret_keys:
            preview.append({
                "key": key,
                "label": spec.get("label", key),
                "from": "CONFIGURED" if manage_env.configured(values.get(key)) else "NOT CONFIGURED",
                "to": "CONFIGURED",
                "secret": True,
            })
        else:
            preview.append({
                "key": key,
                "label": spec.get("label", key),
                "from": values.get(key, "<missing>"),
                "to": normalized[key],
                "secret": False,
            })

    return {
        "normalized": normalized,
        "secret_keys": secret_keys,
        "changed_keys": changed_keys,
        "services": sorted(services),
        "restart_required": "recreate" in impacts,
        "preview": preview,
        "warnings": validation_warnings(proposed),
        "derived": derived,
    }


def replace_many(lines, positions, normalized):
    out = list(lines)
    pos = dict(positions)
    for key, value in normalized.items():
        manage_env.replace_key(out, pos, key, value)
        if key not in pos:
            for idx in range(len(out) - 1, -1, -1):
                if out[idx].startswith(key + "="):
                    pos[key] = idx
                    break
    return out


def compose_cmd(env_path, values, args):
    cmd = ["docker-compose", "-f", str(ROOT / "docker-compose.yml")]
    if manage_env.configured(values.get("CLOUDFLARE_TUNNEL_TOKEN")) and (ROOT / "docker-compose.cloudflare.yml").exists():
        cmd.extend(["-f", str(ROOT / "docker-compose.cloudflare.yml")])
    if manage_env.configured(values.get("ADMIN_SETTINGS_ACCESS_TOKEN")) and (ROOT / "docker-compose.admin.yml").exists():
        cmd.extend(["-f", str(ROOT / "docker-compose.admin.yml")])
    cmd.extend(args)
    return cmd


def run(cmd, timeout=180):
    try:
        return subprocess.run(cmd, cwd=str(ROOT), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=timeout)
    except FileNotFoundError as exc:
        raise WorkerError("Required command not found: {}".format(cmd[0])) from exc
    except subprocess.TimeoutExpired as exc:
        raise WorkerError("Command timed out: {}".format(cmd[0])) from exc


def compose_validate(env_path, values):
    proc = run(compose_cmd(env_path, values, ["config"]), timeout=60)
    if proc.returncode != 0:
        raise WorkerError((proc.stderr or "docker-compose config failed").strip()[:1000])


def recreate_services(env_path, values, services):
    services = [s for s in services if s]
    if not services:
        return
    proc = run(compose_cmd(env_path, values, ["up", "-d", "--no-deps", "--force-recreate"] + services), timeout=240)
    if proc.returncode != 0:
        raise WorkerError((proc.stderr or proc.stdout or "service recreate failed").strip()[:1000])


def health_api():
    command = [
        "docker", "exec", "librechat", "node", "-e",
        'const http=require("http");const r=http.get("http://127.0.0.1:3080/api/config",x=>process.exit(x.statusCode>=200&&x.statusCode<500?0:1));r.setTimeout(5000,()=>{r.destroy();process.exit(1)});r.on("error",()=>process.exit(1));'
    ]
    return run(command, timeout=10).returncode == 0


def health_admin(port):
    try:
        with urllib.request.urlopen("http://127.0.0.1:{}/health".format(port), timeout=5) as response:
            return 200 <= response.status < 300
    except Exception:
        return False


def health_cloudflare():
    inspect = run(["docker", "inspect", "-f", "{{.State.Running}}", "librechat-cloudflared"], timeout=10)
    if inspect.returncode != 0 or inspect.stdout.strip() != "true":
        return False
    logs = run(["docker", "logs", "--tail=200", "librechat-cloudflared"], timeout=10)
    return "Registered tunnel connection" in (logs.stdout + logs.stderr)


def wait_health(services, values, timeout=75):
    deadline = time.time() + timeout
    pending = set(services)
    while time.time() < deadline:
        failed = set()
        for service in pending:
            if service == "api" and not health_api():
                failed.add(service)
            elif service == "admin-settings" and not health_admin(values.get("ADMIN_SETTINGS_PORT", "3210")):
                failed.add(service)
            elif service == "cloudflared" and not health_cloudflare():
                failed.add(service)
        if not failed:
            return True
        pending = failed
        time.sleep(5)
    return False


def restore_backup(backup, env_path):
    data = backup.read_bytes()
    temp = env_path.with_name(".env.rollback-{}".format(os.getpid()))
    temp.write_bytes(data)
    os.chmod(str(temp), 0o600)
    os.replace(str(temp), str(env_path))


class WorkerCore:
    def __init__(self, env_path, schema_path, state_dir):
        self.env_path = env_path
        self.schema_path = schema_path
        self.state_dir = state_dir
        self.lock = threading.Lock()

    def state(self):
        schema, settings, _, values, _ = load_context(self.env_path, self.schema_path)
        result = sanitize_state(schema, settings, values)
        result["warnings"] = validation_warnings(values)
        result["worker_time"] = utc_now()
        return result

    def preview(self, payload):
        schema, settings, _, values, _ = load_context(self.env_path, self.schema_path)
        plan = build_plan(schema, settings, values, payload)
        return {
            "changes": plan["preview"],
            "services": plan["services"],
            "restart_required": plan["restart_required"],
            "warnings": plan["warnings"],
            "derived": plan["derived"],
        }

    def apply(self, payload):
        with self.lock:
            schema, settings, lines, values, positions = load_context(self.env_path, self.schema_path)
            plan = build_plan(schema, settings, values, payload)
            keys = plan["changed_keys"]
            if not keys:
                return {"ok": True, "changed": [], "message": "No changes required", "state": self.state()}

            backup = manage_env.backup_env(self.env_path)
            try:
                new_lines = replace_many(lines, positions, plan["normalized"])
                manage_env.atomic_write(self.env_path, new_lines)
                _, new_values, _ = manage_env.read_env(self.env_path, set(settings))
                compose_validate(self.env_path, new_values)
                if plan["services"]:
                    recreate_services(self.env_path, new_values, plan["services"])
                    if not wait_health(plan["services"], new_values):
                        raise WorkerError("Health check failed after applying settings")
                audit(self.state_dir, "apply", keys, "success")
                return {
                    "ok": True,
                    "changed": keys,
                    "services": plan["services"],
                    "warnings": plan["warnings"],
                    "backup": backup.name,
                    "message": "Settings applied and health checks passed",
                    "state": self.state(),
                }
            except Exception as exc:
                try:
                    restore_backup(backup, self.env_path)
                    _, old_values, _ = manage_env.read_env(self.env_path, set(settings))
                    compose_validate(self.env_path, old_values)
                    if plan["services"]:
                        recreate_services(self.env_path, old_values, plan["services"])
                        wait_health(plan["services"], old_values, timeout=75)
                    audit(self.state_dir, "apply", keys, "rolled_back", str(exc))
                except Exception as rollback_exc:
                    audit(self.state_dir, "apply", keys, "rollback_failed", "{}; rollback: {}".format(exc, rollback_exc))
                    raise WorkerError("Apply failed and rollback also failed: {}; rollback: {}".format(exc, rollback_exc))
                raise WorkerError("Apply failed; previous .env restored: {}".format(exc))

    def handle(self, request):
        action = request.get("action") if isinstance(request, dict) else None
        if action == "state":
            return {"ok": True, "state": self.state()}
        if action == "preview":
            return {"ok": True, "preview": self.preview(request)}
        if action == "apply":
            return self.apply(request)
        if action == "ping":
            return {"ok": True, "time": utc_now()}
        raise WorkerError("Unsupported worker action")


class Handler(socketserver.StreamRequestHandler):
    def handle(self):
        raw = self.rfile.readline(MAX_REQUEST + 1)
        if len(raw) > MAX_REQUEST:
            response = {"ok": False, "error": "Request too large"}
        else:
            try:
                request = json.loads(raw.decode("utf-8"))
                response = self.server.core.handle(request)
            except Exception as exc:
                response = {"ok": False, "error": str(exc)}
        self.wfile.write((json.dumps(response, ensure_ascii=False) + "\n").encode("utf-8"))


class UnixServer(socketserver.ThreadingMixIn, socketserver.UnixStreamServer):
    daemon_threads = True


def serve(core, socket_path, socket_group):
    socket_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(str(socket_path.parent), 0o770)
        if socket_group is not None:
            os.chown(str(socket_path.parent), 0, socket_group)
    except OSError:
        pass
    if socket_path.exists() or socket_path.is_socket():
        socket_path.unlink()
    server = UnixServer(str(socket_path), Handler)
    server.core = core
    try:
        os.chmod(str(socket_path), 0o660)
        if socket_group is not None:
            os.chown(str(socket_path), 0, socket_group)
        audit(core.state_dir, "worker", [], "started")
        server.serve_forever(poll_interval=0.5)
    finally:
        server.server_close()
        if socket_path.exists():
            socket_path.unlink()


def parse_args():
    parser = argparse.ArgumentParser(description="Privileged apply worker for Synology Admin Settings")
    parser.add_argument("--env-file", type=Path, default=DEFAULT_ENV)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--state-dir", type=Path, default=DEFAULT_STATE)
    parser.add_argument("--socket", type=Path)
    parser.add_argument("--socket-group", type=int, default=100)
    parser.add_argument("command", choices=("serve", "state", "ping"))
    return parser.parse_args()


def main():
    args = parse_args()
    state_dir = args.state_dir.resolve()
    socket_path = args.socket.resolve() if args.socket else state_dir / "worker.sock"
    core = WorkerCore(args.env_file.resolve(), args.schema.resolve(), state_dir)
    if args.command == "serve":
        serve(core, socket_path, args.socket_group)
        return 0
    if args.command == "state":
        print(json.dumps(core.state(), indent=2, ensure_ascii=False))
        return 0
    if args.command == "ping":
        print(utc_now())
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
