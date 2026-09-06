#!/usr/bin/env python3
"""One-time local bootstrap for Synology RAG/pgvector credentials.

Generates a private PostgreSQL password if RAG_DB_PASSWORD is not already set.
The value is written only to deploy/synology/.env, is never printed, and an
existing configured password is preserved so re-running this command is safe.
"""

import importlib.util
import os
from pathlib import Path
import secrets

ROOT = Path(__file__).resolve().parent
ENV = ROOT / ".env"
SCHEMA = ROOT / "admin-settings.schema.json"

SPEC = importlib.util.spec_from_file_location("manage_env", ROOT / "manage-env.py")
manage_env = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(manage_env)


def main():
    _, settings = manage_env.load_schema(SCHEMA)
    lines, values, positions = manage_env.read_env(ENV, set(settings))

    if values.get("RAG_DB_PASSWORD", "").strip():
        print("Synology RAG bootstrap already complete; existing database password preserved")
        return 0

    password = secrets.token_urlsafe(36)
    backup = manage_env.backup_env(ENV)
    manage_env.replace_key(lines, positions, "RAG_DB_PASSWORD", password)
    manage_env.atomic_write(ENV, lines)
    os.chmod(str(ENV), 0o600)

    print("Synology RAG bootstrap complete")
    print("RAG database password generated locally and stored in the private .env")
    print("Value was NOT printed")
    print("Private .env backup: {}".format(backup))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
