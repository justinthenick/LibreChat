#!/usr/bin/env python3
"""Safely inspect and edit the managed Synology LibreChat .env settings.

Python 3.8+ standard library only. The tool intentionally does not provide a
raw .env editor. It enforces deploy/synology/admin-settings.schema.json,
redacts secrets, preserves unmanaged lines/comments, rejects duplicate managed
keys, and creates a local chmod-600 backup before every write.
"""

import argparse
import datetime as dt
import getpass
import ipaddress
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parent
DEFAULT_ENV = ROOT / ".env"
DEFAULT_SCHEMA = ROOT / "admin-settings.schema.json"
ENV_LINE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)=(.*)$")
SAFE_UNQUOTED = re.compile(r"^[A-Za-z0-9_./:@+\-]*$")
HOST_LABEL = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?$")


class SettingsError(RuntimeError):
    pass


def load_schema(path):
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise SettingsError("Cannot read settings schema {}: {}".format(path, exc))
    if not isinstance(data, dict) or not isinstance(data.get("settings"), list):
        raise SettingsError("Invalid settings schema: expected a settings array")
    settings = {}
    for item in data["settings"]:
        if not isinstance(item, dict) or not item.get("key"):
            raise SettingsError("Invalid settings schema entry")
        key = str(item["key"])
        if key in settings:
            raise SettingsError("Duplicate key in settings schema: {}".format(key))
        settings[key] = item
    return data, settings


def parse_dotenv_value(raw):
    value = raw.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        quote = value[0]
        inner = value[1:-1]
        if quote == '"':
            inner = inner.replace("\\n", "\n").replace("\\r", "\r")
            inner = inner.replace('\\"', '"').replace("\\\\", "\\")
        return inner
    return value


def encode_dotenv_value(value):
    value = str(value)
    if "\n" in value or "\r" in value:
        value = value.replace("\\", "\\\\").replace('"', '\\"')
        value = value.replace("\r", "\\r").replace("\n", "\\n")
        return '"{}"'.format(value)
    if SAFE_UNQUOTED.fullmatch(value):
        return value
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return '"{}"'.format(escaped)


def read_env(path, managed_keys):
    if not path.exists():
        raise SettingsError(
            "Private environment file not found at {}. Create it from .env.example first.".format(path)
        )
    lines = path.read_text(encoding="utf-8").splitlines(True)
    values = {}
    positions = {}
    duplicates = []
    for index, line in enumerate(lines):
        stripped = line.rstrip("\r\n")
        match = ENV_LINE.match(stripped)
        if not match:
            continue
        key, raw = match.groups()
        if key in positions:
            if key in managed_keys:
                duplicates.append(key)
            continue
        positions[key] = index
        values[key] = parse_dotenv_value(raw)
    if duplicates:
        raise SettingsError(
            "Duplicate managed .env key(s) found: {}. Resolve duplicates manually before using this tool.".format(
                ", ".join(sorted(set(duplicates)))
            )
        )
    return lines, values, positions


def validate_host(value):
    if not value or any(ch.isspace() for ch in value) or "/" in value or "://" in value:
        raise SettingsError("Host must be a hostname or IP address without scheme, path, or whitespace")
    candidate = value
    if candidate.startswith("[") and candidate.endswith("]"):
        candidate = candidate[1:-1]
    try:
        ipaddress.ip_address(candidate)
        return value
    except ValueError:
        pass
    if len(candidate) > 253:
        raise SettingsError("Hostname is too long")
    labels = candidate.rstrip(".").split(".")
    if not labels or any(not HOST_LABEL.fullmatch(label) for label in labels):
        raise SettingsError("Invalid hostname")
    return value


def validate_url(value, spec):
    rules = spec.get("validation") or {}
    if value == "" and rules.get("allow_empty"):
        return value
    parsed = urlparse(value)
    allowed = rules.get("schemes") or ["http", "https"]
    if parsed.scheme not in allowed or not parsed.netloc:
        raise SettingsError("URL must use {} and include a host".format("/".join(allowed)))
    if parsed.username or parsed.password:
        raise SettingsError("Credentials must not be embedded in the URL")
    return value


def validate_value(spec, value):
    value = str(value).strip()
    control = spec.get("control")
    rules = spec.get("validation") or {}
    kind = rules.get("type")

    if control == "boolean":
        lowered = value.lower()
        if lowered not in ("true", "false"):
            raise SettingsError("{} must be true or false".format(spec["key"]))
        return lowered

    if control == "select":
        options = [str(v) for v in spec.get("options") or []]
        if value not in options:
            raise SettingsError("{} must be one of: {}".format(spec["key"], ", ".join(options)))
        return value

    if kind == "integer" or control == "number":
        try:
            number = int(value)
        except ValueError:
            raise SettingsError("{} must be an integer".format(spec["key"]))
        if "minimum" in rules and number < int(rules["minimum"]):
            raise SettingsError("{} must be at least {}".format(spec["key"], rules["minimum"]))
        if "maximum" in rules and number > int(rules["maximum"]):
            raise SettingsError("{} must be at most {}".format(spec["key"], rules["maximum"]))
        return str(number)

    if kind == "host":
        return validate_host(value)

    if kind == "url":
        return validate_url(value, spec)

    if "\n" in value or "\r" in value:
        raise SettingsError("{} cannot contain a newline".format(spec["key"]))
    return value


def derive_values(values):
    scheme = values.get("LIBRECHAT_SCHEME", "http")
    host = values.get("NAS_HOST", "")
    port = values.get("LIBRECHAT_PORT", "3200")
    base = "{}://{}:{}".format(scheme, host, port) if host else ""
    return {"DOMAIN_CLIENT": base, "DOMAIN_SERVER": base}


def backup_env(path):
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = path.with_name("{}.backup-{}".format(path.name, stamp))
    counter = 1
    while backup.exists():
        backup = path.with_name("{}.backup-{}-{}".format(path.name, stamp, counter))
        counter += 1
    shutil.copy2(str(path), str(backup))
    os.chmod(str(backup), 0o600)
    return backup


def atomic_write(path, lines):
    original_mode = path.stat().st_mode & 0o777 if path.exists() else 0o600
    fd, temp_name = tempfile.mkstemp(prefix=".env.tmp-", dir=str(path.parent), text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.writelines(lines)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temp_name, original_mode or 0o600)
        os.replace(temp_name, str(path))
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def replace_key(lines, positions, key, value):
    rendered = "{}={}\n".format(key, encode_dotenv_value(value))
    if key in positions:
        old = lines[positions[key]]
        newline = "\r\n" if old.endswith("\r\n") else "\n"
        lines[positions[key]] = rendered.rstrip("\n") + newline
    else:
        if lines and not lines[-1].endswith(("\n", "\r\n")):
            lines[-1] = lines[-1] + "\n"
        if lines and lines[-1].strip():
            lines.append("\n")
        lines.append(rendered)
    return lines


def confirm(message, assume_yes=False):
    if assume_yes:
        return True
    answer = input("{} [y/N]: ".format(message)).strip().lower()
    return answer in ("y", "yes")


def configured(value):
    return bool(str(value or "").strip())


def display_value(spec, values, derived):
    cls = spec.get("class")
    key = spec["key"]
    if cls in ("replace_only_secret", "locked_secret"):
        return "CONFIGURED" if configured(values.get(key)) else "NOT CONFIGURED"
    if cls == "derived":
        return derived.get(key, "")
    return values.get(key, "<missing>")


def command_show(schema, settings, env_path):
    _, values, _ = read_env(env_path, set(settings))
    derived = derive_values(values)
    group_labels = {g.get("id"): g.get("label", g.get("id")) for g in schema.get("groups") or []}
    current_group = object()
    for item in schema["settings"]:
        if item.get("class") == "internal":
            continue
        group = item.get("group")
        if group != current_group:
            current_group = group
            print("\n[{}]".format(group_labels.get(group, group or "Settings")))
        key = item["key"]
        value = display_value(item, values, derived)
        print("{:<32} {:<18} {}".format(key, item.get("class", ""), value))
    print("")
    return 0


def command_validate(schema, settings, env_path):
    _, values, _ = read_env(env_path, set(settings))
    errors = []
    for item in schema["settings"]:
        if item.get("class") != "editable":
            continue
        key = item["key"]
        if key not in values:
            errors.append("{} is missing".format(key))
            continue
        try:
            validate_value(item, values[key])
        except SettingsError as exc:
            errors.append(str(exc))

    # Helpful cross-setting checks. These are warnings, not invented hard gates.
    warnings = []
    if values.get("LIBRECHAT_SCHEME") == "https" and values.get("SESSION_COOKIE_SECURE", "").lower() != "true":
        warnings.append("LIBRECHAT_SCHEME=https but SESSION_COOKIE_SECURE is not true")
    if values.get("LIBRECHAT_SCHEME") == "http" and values.get("SESSION_COOKIE_SECURE", "").lower() == "true":
        warnings.append("SESSION_COOKIE_SECURE=true while LIBRECHAT_SCHEME=http may prevent browser sessions on plain HTTP")

    if errors:
        print("Validation FAILED:")
        for error in errors:
            print("  - {}".format(error))
        return 2
    print("Managed .env validation OK")
    for warning in warnings:
        print("WARNING: {}".format(warning))
    derived = derive_values(values)
    if derived["DOMAIN_CLIENT"]:
        print("Derived DOMAIN_CLIENT/SERVER: {}".format(derived["DOMAIN_CLIENT"]))
    return 0


def command_set(settings, env_path, key, value, assume_yes):
    spec = settings.get(key)
    if not spec:
        raise SettingsError("{} is not in the managed settings allowlist".format(key))
    if spec.get("class") != "editable":
        raise SettingsError("{} is {} and cannot be changed with 'set'".format(key, spec.get("class")))
    normalized = validate_value(spec, value)
    lines, values, positions = read_env(env_path, set(settings))
    old = values.get(key, "<missing>")
    print("{}: {} -> {}".format(key, old, normalized))
    print("Restart impact: {}".format(spec.get("restart", "unknown")))
    if not confirm("Write this change to {}?".format(env_path), assume_yes):
        print("No change made")
        return 1
    backup = backup_env(env_path)
    replace_key(lines, positions, key, normalized)
    atomic_write(env_path, lines)
    print("Updated {}".format(env_path))
    print("Backup: {}".format(backup))
    if spec.get("restart") == "recreate":
        print("Runtime note: recreate the LibreChat api service after compose validation for this change to take effect.")
    return 0


def read_secret_from_stdin():
    value = sys.stdin.read()
    if value.endswith("\n"):
        value = value[:-1]
    if value.endswith("\r"):
        value = value[:-1]
    return value


def command_set_secret(settings, env_path, key, assume_yes, from_stdin, clear):
    spec = settings.get(key)
    if not spec:
        raise SettingsError("{} is not in the managed settings allowlist".format(key))
    if spec.get("class") != "replace_only_secret":
        raise SettingsError("{} is {} and cannot be changed with 'set-secret'".format(key, spec.get("class")))
    lines, values, positions = read_env(env_path, set(settings))
    old_state = "CONFIGURED" if configured(values.get(key)) else "NOT CONFIGURED"
    if clear:
        secret = ""
    elif from_stdin:
        secret = read_secret_from_stdin()
    else:
        secret = getpass.getpass("New value for {} (input hidden): ".format(key))
    if "\n" in secret or "\r" in secret:
        raise SettingsError("Secret value cannot contain a newline")
    if not clear and secret == "":
        raise SettingsError("Empty secret rejected. Use --clear to remove a configured secret intentionally.")
    new_state = "CONFIGURED" if configured(secret) else "NOT CONFIGURED"
    print("{}: {} -> {} (value redacted)".format(key, old_state, new_state))
    print("Restart impact: {}".format(spec.get("restart", "unknown")))
    if not confirm("Write this secret change to {}?".format(env_path), assume_yes):
        print("No change made")
        return 1
    backup = backup_env(env_path)
    replace_key(lines, positions, key, secret)
    atomic_write(env_path, lines)
    print("Updated {} (secret not displayed)".format(env_path))
    print("Backup: {}".format(backup))
    if spec.get("restart") == "recreate":
        print("Runtime note: recreate the LibreChat api service after compose validation for this change to take effect.")
    return 0


def compose_command(env_path, args):
    deploy_dir = env_path.resolve().parent
    base = deploy_dir / "docker-compose.yml"
    overlay = deploy_dir / "docker-compose.cloudflare.yml"
    _, values, _ = read_env(env_path, set())
    cmd = ["docker-compose", "-f", str(base)]
    if configured(values.get("CLOUDFLARE_TUNNEL_TOKEN")) and overlay.exists():
        cmd.extend(["-f", str(overlay)])
    cmd.extend(args)
    return cmd


def command_compose_check(env_path):
    cmd = compose_command(env_path, ["config"])
    try:
        proc = subprocess.run(cmd, cwd=str(env_path.parent), stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    except FileNotFoundError:
        raise SettingsError("docker-compose was not found. Run this command on the Synology host where standalone Compose is installed.")
    if proc.returncode != 0:
        message = (proc.stderr or "Compose validation failed").strip()
        raise SettingsError(message)
    print("Compose config OK")
    return 0


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Manage allowlisted LibreChat Synology .env settings safely.")
    parser.add_argument("--env-file", type=Path, default=DEFAULT_ENV)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("show", help="Show managed values with secrets redacted")
    sub.add_parser("validate", help="Validate current managed values")
    sub.add_parser("compose-check", help="Run docker-compose config against the current environment")

    p_set = sub.add_parser("set", help="Change one allowlisted non-secret setting")
    p_set.add_argument("key")
    p_set.add_argument("value")
    p_set.add_argument("--yes", action="store_true", help="Skip confirmation prompt")

    p_secret = sub.add_parser("set-secret", help="Replace one allowlisted secret without displaying it")
    p_secret.add_argument("key")
    p_secret.add_argument("--stdin", action="store_true", help="Read replacement secret from stdin")
    p_secret.add_argument("--clear", action="store_true", help="Intentionally clear the secret")
    p_secret.add_argument("--yes", action="store_true", help="Skip confirmation prompt")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    env_path = args.env_file.resolve()
    schema_path = args.schema.resolve()
    schema, settings = load_schema(schema_path)

    if args.command == "show":
        return command_show(schema, settings, env_path)
    if args.command == "validate":
        return command_validate(schema, settings, env_path)
    if args.command == "compose-check":
        return command_compose_check(env_path)
    if args.command == "set":
        return command_set(settings, env_path, args.key, args.value, args.yes)
    if args.command == "set-secret":
        if args.stdin and args.clear:
            raise SettingsError("Use either --stdin or --clear, not both")
        return command_set_secret(settings, env_path, args.key, args.yes, args.stdin, args.clear)
    raise SettingsError("Unknown command")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SettingsError as exc:
        print("ERROR: {}".format(exc), file=sys.stderr)
        raise SystemExit(2)
