#!/usr/bin/env python3
"""Render the Synology LibreChat runtime YAML without a YAML dependency.

Only the block between the two MANAGED OPENROUTER MODELS markers is replaced.
A non-empty ALLOWED_MODELS value enables the pre-filter; clearing it restores
provider catalogue fetch. This preserves the earlier Synology pre-filter
contract without maintaining a second boolean that can disagree with the list.
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
    models = parse_models(values.get("ALLOWED_MODELS", ""))
    rendered = render(args.template.read_text(encoding="utf-8"), values)
    atomic_write(args.output, rendered)
    print("Rendered {} (model pre-filter: {}; allowed models: {})".format(
        args.output, "enabled" if models else "disabled", len(models) if models else "provider fetch"
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
