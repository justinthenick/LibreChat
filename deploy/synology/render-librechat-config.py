#!/usr/bin/env python3
"""Render the Synology LibreChat runtime YAML without a YAML dependency.

Only the block between the two MANAGED OPENROUTER MODELS markers is replaced.
The source librechat.yaml remains valid and reviewable. The generated runtime
copy is local deployment state and must not be committed.
"""

import argparse
from pathlib import Path
import re
import tempfile
import os

BEGIN = "      # BEGIN MANAGED OPENROUTER MODELS"
END = "      # END MANAGED OPENROUTER MODELS"
MODEL_ID = re.compile(r"^[A-Za-z0-9._:/+\-]+$")
ENV_LINE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)=(.*)$")


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


def bool_value(raw):
    return str(raw or "").strip().lower() in ("1", "true", "yes", "on")


def render(template_text, values):
    allowed = parse_models(values.get("ALLOWED_MODELS", ""))
    explicit_flag = values.get("MODEL_PREFILTER_ENABLED")
    # Backwards compatibility with the earlier Synology pre-filter: if the new
    # flag has never been written, an existing ALLOWED_MODELS list remains active.
    enabled = bool_value(explicit_flag) if explicit_flag is not None else bool(allowed)
    if enabled and not allowed:
        raise ValueError("MODEL_PREFILTER_ENABLED=true requires at least one ALLOWED_MODELS entry")

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

    return template_text[:start] + "\n".join(lines) + template_text[end:]


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
    parser.add_argument("--env-file", type=Path, default=root / ".env")
    parser.add_argument("--template", type=Path, default=root / "librechat.yaml")
    parser.add_argument("--output", type=Path, default=root / "librechat.runtime.yaml")
    args = parser.parse_args()

    values = parse_env(args.env_file)
    rendered = render(args.template.read_text(encoding="utf-8"), values)
    atomic_write(args.output, rendered)
    models = parse_models(values.get("ALLOWED_MODELS", ""))
    explicit_flag = values.get("MODEL_PREFILTER_ENABLED")
    enabled = bool_value(explicit_flag) if explicit_flag is not None else bool(models)
    print("Rendered {} (model pre-filter: {}; allowed models: {})".format(
        args.output, "enabled" if enabled else "disabled", len(models) if enabled else "provider fetch"
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
