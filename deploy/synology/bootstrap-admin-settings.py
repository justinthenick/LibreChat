#!/usr/bin/env python3
"""One-time local bootstrap for the Synology Admin Settings panel.

Generates an independent access token without printing it, stores it in the
private .env, fills the panel port/URL when absent, and writes a chmod-600 local
bootstrap token file for the administrator to retrieve once over SSH.
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


def main():
    schema, settings = manage_env.load_schema(SCHEMA)
    lines, values, positions = manage_env.read_env(ENV, set(settings))
    port = values.get("ADMIN_SETTINGS_PORT") or "3210"
    port = manage_env.validate_value(settings["ADMIN_SETTINGS_PORT"], port)
    host = values.get("NAS_HOST") or ""
    if not host:
        raise SystemExit("NAS_HOST must be configured before bootstrapping the admin panel")
    manage_env.validate_host(host)

    existing = values.get("ADMIN_SETTINGS_ACCESS_TOKEN", "")
    token = existing or secrets.token_urlsafe(36)
    panel_url = values.get("ADMIN_PANEL_URL", "") or "http://{}:{}".format(host, port)
    panel_url = manage_env.validate_value(settings["ADMIN_PANEL_URL"], panel_url)

    updates = {
        "ADMIN_SETTINGS_PORT": port,
        "ADMIN_PANEL_URL": panel_url,
        "ADMIN_SETTINGS_ACCESS_TOKEN": token,
    }
    backup = manage_env.backup_env(ENV)
    manage_env.atomic_write(ENV, replace_many(lines, positions, updates))

    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_FILE.write_text(token + "\n", encoding="utf-8")
    os.chmod(str(TOKEN_FILE), 0o600)

    print("Synology Admin Settings bootstrap complete")
    print("Panel URL: {}".format(panel_url))
    print("Private .env backup: {}".format(backup))
    print("Access token was NOT printed. Retrieve it locally once with:")
    print("  sudo cat {}".format(TOKEN_FILE))
    print("After confirming login, remove the bootstrap copy with:")
    print("  sudo rm -f {}".format(TOKEN_FILE))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
