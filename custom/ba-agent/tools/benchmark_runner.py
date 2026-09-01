#!/usr/bin/env python3
"""Run BA benchmarks directly against the Gemini API.

The runner deliberately keeps evaluator-only gold standards/rubrics out of model
context. It can run a baseline, a skill-assisted case, or both, and saves raw
outputs plus reproducibility metadata under the benchmark's results directory.

Python standard library only; suitable for a small Synology/NAS environment.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from typing import Any
import urllib.error
import urllib.parse
import urllib.request


DEFAULT_API_BASE = "https://generativelanguage.googleapis.com/v1beta"
KEY_ENV_CANDIDATES = ("GEMINI_API_KEY", "GOOGLE_KEY", "GOOGLE_API_KEY")


class RunnerError(RuntimeError):
    pass


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def iso_z(value: dt.datetime) -> str:
    return value.astimezone(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def slug(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9._-]+", "-", value)
    return value.strip("-") or "run"


def load_dotenv(path: Path) -> dict[str, str]:
    """Parse simple KEY=VALUE .env files without shell execution."""
    result: dict[str, str] = {}
    if not path.exists():
        raise RunnerError(f"Environment file not found: {path}")

    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            continue
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        result[key] = value
    return result


def resolve_api_key(env_file: Path | None) -> tuple[str, str]:
    merged = dict(os.environ)
    if env_file is not None:
        # Real environment wins over the file if both are set.
        from_file = load_dotenv(env_file)
        from_file.update(merged)
        merged = from_file

    for name in KEY_ENV_CANDIDATES:
        value = merged.get(name, "").strip()
        if value:
            return value, name
    names = ", ".join(KEY_ENV_CANDIDATES)
    raise RunnerError(f"No Gemini API key found. Set one of: {names}, or use --env-file.")


def strip_skill_frontmatter(text: str) -> str:
    if not text.startswith("---\n"):
        return text
    lines = text.splitlines()
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            return "\n".join(lines[idx + 1 :]).lstrip() + "\n"
    return text


def skill_version(text: str) -> str | None:
    match = re.search(r"^Version:\s*\*\*([^*]+)\*\*", text, flags=re.MULTILINE)
    return match.group(1).strip() if match else None


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RunnerError(f"Cannot read JSON config {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise RunnerError(f"Benchmark config must be a JSON object: {path}")
    return value


def resolve_path(base: Path, configured: str | None, fallback: str | None = None) -> Path | None:
    value = configured or fallback
    if not value:
        return None
    path = Path(value)
    if not path.is_absolute():
        path = (base / path).resolve()
    return path


def gemini_generate(
    *,
    api_key: str,
    api_base: str,
    model: str,
    user_prompt: str,
    system_instruction: str | None,
    temperature: float,
    max_output_tokens: int,
    timeout: int,
) -> dict[str, Any]:
    encoded_model = urllib.parse.quote(model, safe="._-")
    endpoint = f"{api_base.rstrip('/')}/models/{encoded_model}:generateContent"

    payload: dict[str, Any] = {
        "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_output_tokens,
        },
    }
    if system_instruction:
        payload["system_instruction"] = {"parts": [{"text": system_instruction}]}

    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        endpoint,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": api_key,
            "User-Agent": "ba-agent-benchmark-runner/1.0",
        },
    )

    started = utc_now()
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
            status_code = response.status
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        classification = "quota_blocked" if exc.code == 429 else "provider_busy" if exc.code == 503 else "provider_error"
        return {
            "status": classification,
            "http_status": exc.code,
            "started_at": iso_z(started),
            "ended_at": iso_z(utc_now()),
            "error": safe_provider_error(error_body, exc.code),
            "text": "",
            "usage": None,
            "finish_reason": None,
        }
    except urllib.error.URLError as exc:
        return {
            "status": "network_error",
            "http_status": None,
            "started_at": iso_z(started),
            "ended_at": iso_z(utc_now()),
            "error": str(exc.reason),
            "text": "",
            "usage": None,
            "finish_reason": None,
        }

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {
            "status": "provider_error",
            "http_status": status_code,
            "started_at": iso_z(started),
            "ended_at": iso_z(utc_now()),
            "error": "Provider returned non-JSON response",
            "text": "",
            "usage": None,
            "finish_reason": None,
        }

    candidates = data.get("candidates") or []
    if not candidates:
        prompt_feedback = data.get("promptFeedback") or data.get("prompt_feedback")
        return {
            "status": "no_candidate",
            "http_status": status_code,
            "started_at": iso_z(started),
            "ended_at": iso_z(utc_now()),
            "error": json.dumps(prompt_feedback, ensure_ascii=False) if prompt_feedback else "No candidate returned",
            "text": "",
            "usage": data.get("usageMetadata") or data.get("usage_metadata"),
            "finish_reason": None,
        }

    first = candidates[0]
    parts = ((first.get("content") or {}).get("parts") or [])
    texts = [part.get("text", "") for part in parts if isinstance(part, dict) and part.get("text")]
    output_text = "\n".join(texts).strip()
    finish_reason = first.get("finishReason") or first.get("finish_reason")

    return {
        "status": "success" if output_text else "empty_output",
        "http_status": status_code,
        "started_at": iso_z(started),
        "ended_at": iso_z(utc_now()),
        "error": None if output_text else "Candidate contained no text output",
        "text": output_text,
        "usage": data.get("usageMetadata") or data.get("usage_metadata"),
        "finish_reason": finish_reason,
    }


def safe_provider_error(raw: str, code: int) -> str:
    """Keep useful provider diagnostics without storing request headers or API keys."""
    try:
        parsed = json.loads(raw)
        error = parsed.get("error") if isinstance(parsed, dict) else None
        if isinstance(error, dict):
            message = str(error.get("message") or f"HTTP {code}")
            status = error.get("status")
            details = error.get("details")
            compact: dict[str, Any] = {"message": message}
            if status:
                compact["status"] = status
            if details:
                compact["details"] = details
            return json.dumps(compact, ensure_ascii=False)
    except json.JSONDecodeError:
        pass
    return f"HTTP {code}: provider request failed"


def render_result_markdown(meta: dict[str, Any], output_text: str) -> str:
    lines = [
        "# BA Benchmark Raw Result",
        "",
        "> Raw model output. Not an evaluator score.",
        "",
        "## Run metadata",
        "",
        f"- Benchmark: `{meta['benchmark']}`",
        f"- Mode: `{meta['mode']}`",
        f"- Provider: `gemini`",
        f"- Model: `{meta['model']}`",
        f"- Status: `{meta['status']}`",
        f"- Started: `{meta['started_at']}`",
        f"- Ended: `{meta['ended_at']}`",
        f"- Temperature: `{meta['temperature']}`",
        f"- Max output tokens: `{meta['max_output_tokens']}`",
        f"- Input SHA-256: `{meta['input_sha256']}`",
        f"- Prompt SHA-256: `{meta['prompt_sha256']}`",
    ]
    if meta.get("skill_path"):
        lines.append(f"- Skill: `{meta['skill_path']}`")
        lines.append(f"- Skill version: `{meta.get('skill_version') or 'unknown'}`")
        lines.append(f"- Skill SHA-256: `{meta.get('skill_sha256')}`")
    if meta.get("finish_reason"):
        lines.append(f"- Finish reason: `{meta['finish_reason']}`")
    if meta.get("usage"):
        lines.append(f"- Usage metadata: `{json.dumps(meta['usage'], ensure_ascii=False, sort_keys=True)}`")
    if meta.get("error"):
        lines.extend(["", "## Provider status", "", f"`{meta['error']}`"])
    lines.extend(["", "---", "", "## Model output", "", output_text or "_No model output._", ""])
    return "\n".join(lines)


def find_repo_root(start: Path) -> Path | None:
    current = start.resolve()
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists():
            return candidate
    return None


def git_publish(repo_root: Path, files: list[Path], commit_message: str, push: bool) -> dict[str, Any]:
    rels = [str(path.resolve().relative_to(repo_root.resolve())) for path in files]
    result: dict[str, Any] = {"commit": None, "push": None}

    subprocess.run(["git", "-C", str(repo_root), "add", "--", *rels], check=True)
    commit = subprocess.run(
        ["git", "-C", str(repo_root), "commit", "-m", commit_message],
        text=True,
        capture_output=True,
    )
    if commit.returncode != 0:
        combined = (commit.stdout + "\n" + commit.stderr).strip()
        if "nothing to commit" not in combined.lower():
            raise RunnerError(f"git commit failed: {combined}")
        result["commit"] = "nothing_to_commit"
    else:
        sha = subprocess.check_output(["git", "-C", str(repo_root), "rev-parse", "HEAD"], text=True).strip()
        result["commit"] = sha

    if push:
        pushed = subprocess.run(["git", "-C", str(repo_root), "push", "origin", "HEAD"], text=True, capture_output=True)
        result["push"] = "success" if pushed.returncode == 0 else (pushed.stdout + "\n" + pushed.stderr).strip()
    return result


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a BA benchmark against Gemini without exposing evaluator files.")
    parser.add_argument("benchmark", type=Path, help="Benchmark directory containing benchmark.json/input/prompt.")
    parser.add_argument("--model", required=True, help="Exact Gemini model ID. No automatic fallback is performed.")
    parser.add_argument("--mode", choices=("baseline", "skill", "both"), default="both")
    parser.add_argument("--skill", type=Path, help="Override skill file configured in benchmark.json.")
    parser.add_argument("--input", type=Path, help="Override input file configured in benchmark.json.")
    parser.add_argument("--prompt", type=Path, help="Override prompt file configured in benchmark.json.")
    parser.add_argument("--env-file", type=Path, help="Optional .env containing GEMINI_API_KEY, GOOGLE_KEY or GOOGLE_API_KEY.")
    parser.add_argument("--api-base", default=DEFAULT_API_BASE)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--max-output-tokens", type=int, default=8192)
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--repeat", type=int, default=1, help="Runs per requested mode; default 1.")
    parser.add_argument("--run-id", help="Optional run ID prefix. Default is UTC timestamp.")
    parser.add_argument("--git-commit", action="store_true", help="Commit generated result files to the current git repository.")
    parser.add_argument("--git-push", action="store_true", help="Push the result commit to origin HEAD. Implies --git-commit.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    benchmark_dir = args.benchmark.resolve()
    config_path = benchmark_dir / "benchmark.json"
    config = read_json(config_path) if config_path.exists() else {}

    input_path = args.input.resolve() if args.input else resolve_path(benchmark_dir, config.get("input"), "input.md")
    prompt_path = args.prompt.resolve() if args.prompt else resolve_path(benchmark_dir, config.get("prompt"), "prompt.md")
    skill_path = args.skill.resolve() if args.skill else resolve_path(benchmark_dir, config.get("skill"))

    if input_path is None or not input_path.exists():
        raise RunnerError(f"Benchmark input not found: {input_path}")
    if prompt_path is None or not prompt_path.exists():
        raise RunnerError(f"Benchmark prompt not found: {prompt_path}. Add prompt.md or pass --prompt.")
    if args.mode in ("skill", "both") and (skill_path is None or not skill_path.exists()):
        raise RunnerError("Skill mode requested but no valid skill file is configured. Use --skill or benchmark.json.")
    if args.repeat < 1:
        raise RunnerError("--repeat must be at least 1")
    if not (0.0 <= args.temperature <= 2.0):
        raise RunnerError("--temperature must be between 0.0 and 2.0")

    api_key, key_source = resolve_api_key(args.env_file.resolve() if args.env_file else None)
    input_text = input_path.read_text(encoding="utf-8")
    instruction_text = prompt_path.read_text(encoding="utf-8").strip()
    user_prompt = f"{instruction_text}\n\n---\n\n# Supplied benchmark material\n\n{input_text.strip()}\n"

    raw_skill_text = skill_path.read_text(encoding="utf-8") if skill_path else None
    injected_skill_text = strip_skill_frontmatter(raw_skill_text) if raw_skill_text else None
    version = skill_version(raw_skill_text or "")

    benchmark_name = str(config.get("name") or benchmark_dir.name)
    results_dir = benchmark_dir / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    base_run_id = args.run_id or utc_now().strftime("%Y%m%dT%H%M%SZ")
    requested_modes = [args.mode] if args.mode != "both" else ["baseline", "skill"]
    generated_files: list[Path] = []
    manifest_runs: list[dict[str, Any]] = []

    print(f"Benchmark : {benchmark_name}")
    print(f"Model     : {args.model}")
    print(f"Modes     : {', '.join(requested_modes)}")
    print(f"Repeat    : {args.repeat}")
    print(f"API key   : loaded from {key_source} (value not displayed)")
    print(f"Results   : {results_dir}")

    stop_for_quota = False
    for repetition in range(1, args.repeat + 1):
        for mode in requested_modes:
            if stop_for_quota:
                break
            system_instruction = injected_skill_text if mode == "skill" else None
            label = f"{base_run_id}-{slug(args.model)}-{mode}"
            if args.repeat > 1:
                label += f"-r{repetition}"
            if mode == "skill" and version:
                label += f"-v{slug(version)}"

            print(f"\nRunning {mode} ({repetition}/{args.repeat}) ...", flush=True)
            result = gemini_generate(
                api_key=api_key,
                api_base=args.api_base,
                model=args.model,
                user_prompt=user_prompt,
                system_instruction=system_instruction,
                temperature=args.temperature,
                max_output_tokens=args.max_output_tokens,
                timeout=args.timeout,
            )

            meta: dict[str, Any] = {
                "benchmark": benchmark_name,
                "benchmark_dir": str(benchmark_dir),
                "mode": mode,
                "repetition": repetition,
                "provider": "gemini",
                "model": args.model,
                "status": result["status"],
                "http_status": result.get("http_status"),
                "started_at": result["started_at"],
                "ended_at": result["ended_at"],
                "temperature": args.temperature,
                "max_output_tokens": args.max_output_tokens,
                "input_path": str(input_path),
                "input_sha256": sha256_text(input_text),
                "prompt_path": str(prompt_path),
                "prompt_sha256": sha256_text(instruction_text),
                "skill_path": str(skill_path) if mode == "skill" and skill_path else None,
                "skill_version": version if mode == "skill" else None,
                "skill_sha256": sha256_text(raw_skill_text) if mode == "skill" and raw_skill_text else None,
                "finish_reason": result.get("finish_reason"),
                "usage": result.get("usage"),
                "error": result.get("error"),
            }

            md_path = results_dir / f"{label}.md"
            meta_path = results_dir / f"{label}.json"
            md_path.write_text(render_result_markdown(meta, result.get("text", "")), encoding="utf-8")
            meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
            generated_files.extend([md_path, meta_path])
            manifest_runs.append({**meta, "output_markdown": str(md_path), "metadata_json": str(meta_path)})
            print(f"Status    : {result['status']}")
            print(f"Saved     : {md_path.name}")

            # Never silently switch model/retry on quota exhaustion. This preserves experimental validity.
            if result["status"] == "quota_blocked":
                print("Quota blocked. Stopping remaining runs; no model fallback or retry performed.")
                stop_for_quota = True
        if stop_for_quota:
            break

    manifest = {
        "schema": 1,
        "benchmark": benchmark_name,
        "run_id": base_run_id,
        "created_at": iso_z(utc_now()),
        "provider": "gemini",
        "model": args.model,
        "temperature": args.temperature,
        "max_output_tokens": args.max_output_tokens,
        "mode_requested": args.mode,
        "repeat_requested": args.repeat,
        "quota_stopped": stop_for_quota,
        "runs": manifest_runs,
    }
    manifest_path = results_dir / f"{base_run_id}-{slug(args.model)}-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    generated_files.append(manifest_path)

    if args.git_push:
        args.git_commit = True
    if args.git_commit:
        repo_root = find_repo_root(benchmark_dir)
        if repo_root is None:
            raise RunnerError("--git-commit requested but no .git repository was found above the benchmark directory")
        publish = git_publish(
            repo_root,
            generated_files,
            commit_message=f"BA benchmark: {benchmark_name} on {args.model} ({base_run_id})",
            push=args.git_push,
        )
        print(f"Git commit: {publish['commit']}")
        if args.git_push:
            print(f"Git push  : {publish['push']}")

    print(f"\nManifest  : {manifest_path}")
    return 2 if stop_for_quota else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RunnerError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
