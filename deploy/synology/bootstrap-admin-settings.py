#!/usr/bin/env python3
"""One-time local bootstrap for Synology deployment administration.

Generates the custom Synology Deployment Settings recovery credential without
printing it, ensures the official LibreChat Admin Panel has an independent
session secret, and writes a chmod-600 local bootstrap token file for the
administrator to retrieve once over SSH.

The two admin surfaces have deliberately separate responsibilities:
- LibreChat Admin Panel: application users/roles/grants/configuration overrides.
- Synology Deployment Settings: host-side .env/deployment changes and rollback.
"""

import importlib.util
import os
from pathlib import Path
import secrets

ROOT = Path(__file__).resolve().parent
ENV = ROOT / ".env"
SCHEMA = ROOT / "admin-settings.schema.json"
TOKEN_FILE = Path("/volume1/docker/librechat/admin-settings-bootstrap-token.txt")

SPEC = importlib.util.spec_from_file_location("manage_env", ROOT / "manage-env.py")
manage_env = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(manage_env)


def replace_many(lines, positions, updates):
    out = list(lines)
    pos = dict(positions)
    for key, value in updates.items():
        manage_env.replace_key(out, pos, key, value)
        if key not in pos:
            for idx in range(len(out) - 1, -1, -1):
                if out[idx].startswith(key + "="):
                    pos[key] = idx
                    break
    return out


def validate_port(raw, key):
    try:
        port = int(str(raw))
    except ValueError:
        raise SystemExit("{} must be an integer".format(key))
    if port < 1 or port > 65535:
        raise SystemExit("{} must be between 1 and 65535".format(key))
    return str(port)


def ensure_official_session_secret(env):
    key = "ADMIN_PANEL_SESSION_SECRET"
    lines, values, positions = manage_env.read_env(env, {key})
    if values.get(key):
        return False
    manage_env.replace_key(lines, positions, key, secrets.token_urlsafe(48))
    manage_env.backup_env(env)
    manage_env.atomic_write(env, lines)
    return True


def main():
    schema, settings = manage_env.load_schema(SCHEMA)
    lines, values, positions = manage_env.read_env(ENV, set(settings))

    deployment_port = values.get("ADMIN_SETTINGS_PORT") or "3210"
    deployment_port = manage_env.validate_value(settings["ADMIN_SETTINGS_PORT"], deployment_port)
    # Use a deployment-specific host port so the upstream panel does not compete
    # with common NAS services that already use port 3000. The container still
    # listens on its upstream-standard internal port 3000.
    official_port = validate_port(values.get("ADMIN_PANEL_PORT") or "3220", "ADMIN_PANEL_PORT")

    host = values.get("NAS_HOST") or ""
    if not host:
        raise SystemExit("NAS_HOST must be configured before bootstrapping administration")
    manage_env.validate_host(host)

    recovery_token = values.get("ADMIN_SETTINGS_ACCESS_TOKEN", "") or secrets.token_urlsafe(36)
    official_session_secret = values.get("ADMIN_PANEL_SESSION_SECRET", "") or secrets.token_urlsafe(48)

    # Older deployments used ADMIN_PANEL_URL for the custom Synology settings UI.
    # Migrate that known local value to the upstream LibreChat Admin Panel URL;
    # preserve any other value because it may already be a deliberate external URL.
    current_panel_url = values.get("ADMIN_PANEL_URL", "")
    legacy_panel_urls = {
        "http://{}:{}".format(host, deployment_port),
        "https://{}:{}".format(host, deployment_port),
    }
    if not current_panel_url or current_panel_url in legacy_panel_urls:
        official_panel_url = "http://{}:{}".format(host, official_port)
    else:
        official_panel_url = current_panel_url
    official_panel_url = manage_env.validate_value(settings["ADMIN_PANEL_URL"], official_panel_url)

    deployment_settings_url = "http://{}:{}".format(host, deployment_port)

    updates = {
        "ADMIN_SETTINGS_PORT": deployment_port,
        "ADMIN_SETTINGS_ACCESS_TOKEN": recovery_token,
        "ADMIN_PANEL_PORT": official_port,
        "ADMIN_PANEL_SESSION_SECRET": official_session_secret,
        "ADMIN_PANEL_URL": official_panel_url,
    }
    backup = manage_env.backup_env(ENV)
    manage_env.atomic_write(ENV, replace_many(lines, positions, updates))

    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_FILE.write_text(recovery_token + "\n", encoding="utf-8")
    os.chmod(str(TOKEN_FILE), 0o600)

    print("Synology administration bootstrap complete")
    print("LibreChat Admin Panel URL: {}".format(official_panel_url))
    print("Synology Deployment Settings URL: {}".format(deployment_settings_url))
    print("Private .env backup: {}".format(backup))
    print("Deployment-settings recovery token was NOT printed. Retrieve it locally once with:")
    print("  sudo cat {}".format(TOKEN_FILE))
    print("After confirming login, remove the bootstrap copy with:")
    print("  sudo rm -f {}".format(TOKEN_FILE))
    return 0


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ensure-session-secret", action="store_true",
                        help="Only create a missing official panel secret; preserve other settings")
    parser.add_argument("--env-file", type=Path, default=ENV)
    args = parser.parse_args()
    if args.ensure_session_secret:
        ensure_official_session_secret(args.env_file)
    else:
        ENV = args.env_file
        raise SystemExit(main())
