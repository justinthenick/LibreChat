#!/usr/bin/env python3
"""Render the Synology LibreChat runtime YAML without a YAML dependency.

The block between the two MANAGED OPENROUTER MODELS markers is replaced.
The non-secret coding-executor host and port are also materialized because
LibreChat validates MCP private-address exemptions before normal environment
interpolation. Secret placeholders remain untouched.

Production containers read values from their process environment (populated by
Docker Compose env_file). --env-file remains available for tests and host-side
tooling, but the private host .env never needs to be bind-mounted into LibreChat.
"""

import argparse
import os
from pathlib import Path
import re
import tempfile

BEGIN = "      # BEGIN MANAGED OPENROUTER MODELS"
END = "      # END MANAGED OPENROUTER MODELS"
MODEL_ID = re.compile(r"^[A-Za-z0-9._:/+\-]+$")
ENV_LINE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)=(.*)$")
EXECUTOR_HOST = re.compile(r"^[A-Za-z0-9.-]+$")


def parse_env(path):
    values = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        m = ENV_LINE.match(raw_line)
        if not m:
            continue
        key, raw = m.groups()
        value = raw.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
            if raw.strip().startswith('"'):
                value = value.replace("\\n", "\n").replace("\\r", "\r")
                value = value.replace('\\"', '"').replace("\\\\", "\\")
        values[key] = value
    return values


def load_values(env_file=None):
    if env_file is not None:
        return parse_env(env_file)
    return dict(os.environ)


def parse_models(value):
    result = []
    seen = set()
    for item in re.split(r"[,\n\r]+", value or ""):
        model = item.strip()
        if not model:
            continue
        if not MODEL_ID.fullmatch(model):
            raise ValueError("Invalid model id in ALLOWED_MODELS: {!r}".format(model))
        if model not in seen:
            seen.add(model)
            result.append(model)
    return result


def render(template_text, values):
    allowed = parse_models(values.get("ALLOWED_MODELS", ""))
    enabled = bool(allowed)

    start = template_text.find(BEGIN)
    end = template_text.find(END)
    if start < 0 or end < 0 or end <= start:
        raise ValueError("Managed OpenRouter model markers are missing or out of order")
    end += len(END)

    if enabled:
        lines = [BEGIN, "      models:", "        default:"]
        for model in allowed:
            escaped = model.replace("'", "''")
            lines.append("          - '{}'".format(escaped))
        lines += ["        fetch: false", END]
    else:
        lines = [
            BEGIN,
            "      models:",
            "        default:",
            "          - 'deepseek/deepseek-v3.2'",
            "        fetch: true",
            END,
        ]

    rendered = template_text[:start] + "\n".join(lines) + template_text[end:]

    host = values.get("CODING_EXECUTOR_HOST", "localhost").strip()
    port_text = values.get("CODING_EXECUTOR_PORT", "8765").strip()
    if not host or not EXECUTOR_HOST.fullmatch(host):
        raise ValueError("Invalid CODING_EXECUTOR_HOST")
    try:
        port = int(port_text)
    except ValueError:
        raise ValueError("Invalid CODING_EXECUTOR_PORT")
    if port < 1 or port > 65535:
        raise ValueError("Invalid CODING_EXECUTOR_PORT")

    return (
        rendered.replace("${CODING_EXECUTOR_HOST}", host)
        .replace("${CODING_EXECUTOR_PORT}", str(port))
    )


def atomic_write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=path.name + ".tmp-", dir=str(path.parent), text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temp_name, 0o644)
        os.replace(temp_name, str(path))
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def main():
    parser = argparse.ArgumentParser()
    root = Path(__file__).resolve().parent
    parser.add_argument(
        "--env-file",
        type=Path,
        default=None,
        help="Optional dotenv source. If omitted, read the current process environment.",
    )
    parser.add_argument("--template", type=Path, default=root / "librechat.yaml")
    parser.add_argument("--output", type=Path, default=root / "librechat.runtime.yaml")
    args = parser.parse_args()

    values = load_values(args.env_file)
    models = parse_models(values.get("ALLOWED_MODELS", ""))
    rendered = render(args.template.read_text(encoding="utf-8"), values)
    atomic_write(args.output, rendered)
    print("Rendered {} (model pre-filter: {}; allowed models: {})".format(
        args.output, "enabled" if models else "disabled", len(models) if models else "provider fetch"
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
