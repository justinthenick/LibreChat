#!/usr/bin/env python3
"""Run BA benchmarks directly against the Gemini API.

Python 3.8+ standard-library-only runner for Synology/NAS environments.
It can refresh benchmark-visible inputs/skills from GitHub, run baseline/skill
cases, save reproducibility metadata, and publish raw results back to GitHub
without requiring a local git executable.

Evaluator-only gold standards/rubrics are never loaded or sent to the model.
"""

import argparse
import base64
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

DEFAULT_API_BASE = "https://generativelanguage.googleapis.com/v1beta"
DEFAULT_GITHUB_REPO = "justinthenick/LibreChat"
DEFAULT_GITHUB_BRANCH = "feature/ba-agent-v0.1"
KEY_ENV_CANDIDATES = ("GEMINI_API_KEY", "GOOGLE_KEY", "GOOGLE_API_KEY")
GITHUB_TOKEN_DEFAULT_ENV = "GITHUB_BA_BENCHMARK_TOKEN"


class RunnerError(RuntimeError):
    pass


def utc_now():
    return dt.datetime.now(dt.timezone.utc)


def iso_z(value):
    return value.astimezone(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def slug(value):
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9._-]+", "-", value)
    return value.strip("-") or "run"


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_dotenv(path):
    result = {}
    if not path.exists():
        raise RunnerError("Environment file not found: {}".format(path))
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


def merged_environment(env_file):
    merged = {}
    if env_file is not None:
        merged.update(load_dotenv(env_file))
    merged.update(os.environ)
    return merged


def resolve_api_key(env):
    for name in KEY_ENV_CANDIDATES:
        value = env.get(name, "").strip()
        if value:
            return value, name
    raise RunnerError("No Gemini API key found. Set one of: {}".format(", ".join(KEY_ENV_CANDIDATES)))


def resolve_github_token(env, token_env):
    value = env.get(token_env, "").strip()
    if value:
        return value
    raise RunnerError(
        "GitHub publishing requested but {} is not set. Add a fine-grained token with Contents: Read and write for the repo.".format(
            token_env
        )
    )


def strip_skill_frontmatter(text):
    if not text.startswith("---\n"):
        return text
    lines = text.splitlines()
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            return "\n".join(lines[idx + 1 :]).lstrip() + "\n"
    return text


def skill_version(text):
    match = re.search(r"^Version:\s*\*\*([^*]+)\*\*", text, flags=re.MULTILINE)
    return match.group(1).strip() if match else None


def read_json(path):
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise RunnerError("Cannot read JSON config {}: {}".format(path, exc))
    if not isinstance(value, dict):
        raise RunnerError("Benchmark config must be a JSON object: {}".format(path))
    return value


def resolve_path(base, configured, fallback=None):
    value = configured or fallback
    if not value:
        return None
    path = Path(value)
    if not path.is_absolute():
        path = (base / path).resolve()
    return path


def find_lab_root(start):
    current = start.resolve()
    for candidate in [current] + list(current.parents):
        if (candidate / "custom" / "ba-agent").exists():
            return candidate
    return None


def github_api_request(url, method="GET", token=None, payload=None, timeout=60):
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "ba-agent-benchmark-runner/2.0",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = "Bearer {}".format(token)
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
            return response.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            body = json.loads(raw)
        except ValueError:
            body = {"message": raw[:1000]}
        raise RunnerError("GitHub API HTTP {}: {}".format(exc.code, body.get("message", "request failed")))
    except urllib.error.URLError as exc:
        raise RunnerError("GitHub API network error: {}".format(exc.reason))


def github_fetch_text(repo, branch, repo_path):
    encoded_path = urllib.parse.quote(repo_path.strip("/"), safe="/")
    ref = urllib.parse.quote(branch, safe="")
    url = "https://api.github.com/repos/{}/contents/{}?ref={}".format(repo, encoded_path, ref)
    _, data = github_api_request(url)
    if not isinstance(data, dict) or data.get("type") != "file":
        raise RunnerError("GitHub path is not a file: {}".format(repo_path))
    content = data.get("content", "")
    if data.get("encoding") != "base64":
        raise RunnerError("Unsupported GitHub content encoding for {}".format(repo_path))
    return base64.b64decode(content).decode("utf-8")


def github_put_text(repo, branch, repo_path, text, token, message):
    encoded_path = urllib.parse.quote(repo_path.strip("/"), safe="/")
    ref = urllib.parse.quote(branch, safe="")
    get_url = "https://api.github.com/repos/{}/contents/{}?ref={}".format(repo, encoded_path, ref)
    sha = None
    try:
        _, existing = github_api_request(get_url, token=token)
        if isinstance(existing, dict):
            sha = existing.get("sha")
    except RunnerError as exc:
        if "HTTP 404" not in str(exc):
            raise

    put_url = "https://api.github.com/repos/{}/contents/{}".format(repo, encoded_path)
    payload = {
        "message": message,
        "content": base64.b64encode(text.encode("utf-8")).decode("ascii"),
        "branch": branch,
    }
    if sha:
        payload["sha"] = sha
    _, result = github_api_request(put_url, method="PUT", token=token, payload=payload)
    commit = result.get("commit") if isinstance(result, dict) else None
    return commit.get("sha") if isinstance(commit, dict) else None


def refresh_from_github(benchmark_dir, repo, branch):
    root = find_lab_root(benchmark_dir)
    if root is None:
        raise RunnerError(
            "Cannot infer lab root. Expected benchmark under <root>/custom/ba-agent/. Use the NAS bootstrap once to create the lab tree."
        )

    benchmark_rel = benchmark_dir.resolve().relative_to(root.resolve()).as_posix()
    config_rel = benchmark_rel + "/benchmark.json"
    config_text = github_fetch_text(repo, branch, config_rel)
    config_path = benchmark_dir / "benchmark.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(config_text, encoding="utf-8")
    config = json.loads(config_text)

    input_rel = benchmark_rel + "/" + str(config.get("input") or "input.md")
    prompt_rel = benchmark_rel + "/" + str(config.get("prompt") or "prompt.md")
    input_path = benchmark_dir / str(config.get("input") or "input.md")
    prompt_path = benchmark_dir / str(config.get("prompt") or "prompt.md")

    input_path.parent.mkdir(parents=True, exist_ok=True)
    prompt_path.parent.mkdir(parents=True, exist_ok=True)
    input_path.write_text(github_fetch_text(repo, branch, input_rel), encoding="utf-8")
    prompt_path.write_text(github_fetch_text(repo, branch, prompt_rel), encoding="utf-8")

    skill_config = config.get("skill")
    if skill_config:
        skill_path = (benchmark_dir / str(skill_config)).resolve()
        skill_rel = skill_path.relative_to(root.resolve()).as_posix()
        skill_path.parent.mkdir(parents=True, exist_ok=True)
        skill_path.write_text(github_fetch_text(repo, branch, skill_rel), encoding="utf-8")

    return config


def safe_provider_error(raw, code):
    try:
        parsed = json.loads(raw)
        error = parsed.get("error") if isinstance(parsed, dict) else None
        if isinstance(error, dict):
            compact = {"message": str(error.get("message") or "HTTP {}".format(code))}
            if error.get("status"):
                compact["status"] = error["status"]
            if error.get("details"):
                compact["details"] = error["details"]
            return json.dumps(compact, ensure_ascii=False)
    except ValueError:
        pass
    return "HTTP {}: provider request failed".format(code)


def gemini_generate(api_key, api_base, model, user_prompt, system_instruction, temperature, max_output_tokens, timeout):
    encoded_model = urllib.parse.quote(model, safe="._-")
    endpoint = "{}/models/{}:generateContent".format(api_base.rstrip("/"), encoded_model)
    payload = {
        "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_output_tokens,
        },
    }
    if system_instruction:
        payload["system_instruction"] = {"parts": [{"text": system_instruction}]}

    request = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": api_key,
            "User-Agent": "ba-agent-benchmark-runner/2.0",
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
    except ValueError:
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
        feedback = data.get("promptFeedback") or data.get("prompt_feedback")
        return {
            "status": "no_candidate",
            "http_status": status_code,
            "started_at": iso_z(started),
            "ended_at": iso_z(utc_now()),
            "error": json.dumps(feedback, ensure_ascii=False) if feedback else "No candidate returned",
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


def render_result_markdown(meta, output_text):
    lines = [
        "# BA Benchmark Raw Result",
        "",
        "> Raw model output. Not an evaluator score.",
        "",
        "## Run metadata",
        "",
        "- Benchmark: `{}`".format(meta["benchmark"]),
        "- Mode: `{}`".format(meta["mode"]),
        "- Provider: `gemini`",
        "- Model: `{}`".format(meta["model"]),
        "- Status: `{}`".format(meta["status"]),
        "- Started: `{}`".format(meta["started_at"]),
        "- Ended: `{}`".format(meta["ended_at"]),
        "- Temperature: `{}`".format(meta["temperature"]),
        "- Max output tokens: `{}`".format(meta["max_output_tokens"]),
        "- Input SHA-256: `{}`".format(meta["input_sha256"]),
        "- Prompt SHA-256: `{}`".format(meta["prompt_sha256"]),
    ]
    if meta.get("skill_path"):
        lines.append("- Skill: `{}`".format(meta["skill_path"]))
        lines.append("- Skill version: `{}`".format(meta.get("skill_version") or "unknown"))
        lines.append("- Skill SHA-256: `{}`".format(meta.get("skill_sha256")))
    if meta.get("finish_reason"):
        lines.append("- Finish reason: `{}`".format(meta["finish_reason"]))
    if meta.get("usage"):
        lines.append("- Usage metadata: `{}`".format(json.dumps(meta["usage"], ensure_ascii=False, sort_keys=True)))
    if meta.get("error"):
        lines.extend(["", "## Provider status", "", "`{}`".format(meta["error"])])
    lines.extend(["", "---", "", "## Model output", "", output_text or "_No model output._", ""])
    return "\n".join(lines)


def parse_args(argv):
    parser = argparse.ArgumentParser(description="Run a BA benchmark against Gemini without exposing evaluator files.")
    parser.add_argument("benchmark", type=Path)
    parser.add_argument("--model", required=True)
    parser.add_argument("--mode", choices=("baseline", "skill", "both"), default="both")
    parser.add_argument("--skill", type=Path)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--prompt", type=Path)
    parser.add_argument("--env-file", type=Path)
    parser.add_argument("--api-base", default=DEFAULT_API_BASE)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--max-output-tokens", type=int, default=8192)
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--repeat", type=int, default=1)
    parser.add_argument("--run-id")
    parser.add_argument("--refresh-from-github", action="store_true")
    parser.add_argument("--github-repo", default=DEFAULT_GITHUB_REPO)
    parser.add_argument("--github-branch", default=DEFAULT_GITHUB_BRANCH)
    parser.add_argument("--publish-github", action="store_true")
    parser.add_argument("--github-token-env", default=GITHUB_TOKEN_DEFAULT_ENV)
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv or sys.argv[1:])
    benchmark_dir = args.benchmark.resolve()

    if args.refresh_from_github:
        refresh_from_github(benchmark_dir, args.github_repo, args.github_branch)

    config_path = benchmark_dir / "benchmark.json"
    config = read_json(config_path) if config_path.exists() else {}

    input_path = args.input.resolve() if args.input else resolve_path(benchmark_dir, config.get("input"), "input.md")
    prompt_path = args.prompt.resolve() if args.prompt else resolve_path(benchmark_dir, config.get("prompt"), "prompt.md")
    skill_path = args.skill.resolve() if args.skill else resolve_path(benchmark_dir, config.get("skill"))

    if input_path is None or not input_path.exists():
        raise RunnerError("Benchmark input not found: {}".format(input_path))
    if prompt_path is None or not prompt_path.exists():
        raise RunnerError("Benchmark prompt not found: {}".format(prompt_path))
    if args.mode in ("skill", "both") and (skill_path is None or not skill_path.exists()):
        raise RunnerError("Skill mode requested but no valid skill file is configured.")
    if args.repeat < 1:
        raise RunnerError("--repeat must be at least 1")
    if not (0.0 <= args.temperature <= 2.0):
        raise RunnerError("--temperature must be between 0.0 and 2.0")

    env_file = args.env_file.resolve() if args.env_file else None
    env = merged_environment(env_file)
    api_key, key_source = resolve_api_key(env)
    github_token = resolve_github_token(env, args.github_token_env) if args.publish_github else None

    input_text = input_path.read_text(encoding="utf-8")
    instruction_text = prompt_path.read_text(encoding="utf-8").strip()
    user_prompt = instruction_text + "\n\n---\n\n" + input_text

    skill_text = None
    skill_body = None
    skill_ver = None
    if skill_path is not None and skill_path.exists():
        skill_text = skill_path.read_text(encoding="utf-8")
        skill_body = strip_skill_frontmatter(skill_text).strip()
        skill_ver = skill_version(skill_text)

    results_dir = benchmark_dir / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    run_prefix = args.run_id or utc_now().strftime("%Y%m%dT%H%M%SZ")
    benchmark_name = str(config.get("name") or benchmark_dir.name)
    modes = ["baseline", "skill"] if args.mode == "both" else [args.mode]
    written = []
    manifest_runs = []
    stop_remaining = False

    for mode in modes:
        for iteration in range(1, args.repeat + 1):
            if stop_remaining:
                break
            system_instruction = skill_body if mode == "skill" else None
            result = gemini_generate(
                api_key,
                args.api_base,
                args.model,
                user_prompt,
                system_instruction,
                args.temperature,
                args.max_output_tokens,
                args.timeout,
            )
            suffix = "{}-{}-{}-{:02d}".format(run_prefix, slug(args.model), mode, iteration)
            md_path = results_dir / (suffix + ".md")
            json_path = results_dir / (suffix + ".json")

            meta = {
                "schema": 2,
                "benchmark": benchmark_name,
                "benchmark_dir": benchmark_dir.name,
                "mode": mode,
                "iteration": iteration,
                "provider": "gemini",
                "model": args.model,
                "status": result["status"],
                "http_status": result.get("http_status"),
                "started_at": result["started_at"],
                "ended_at": result["ended_at"],
                "temperature": args.temperature,
                "max_output_tokens": args.max_output_tokens,
                "input_sha256": sha256_text(input_text),
                "prompt_sha256": sha256_text(instruction_text),
                "skill_path": str(skill_path) if mode == "skill" and skill_path else None,
                "skill_version": skill_ver if mode == "skill" else None,
                "skill_sha256": sha256_text(skill_text) if mode == "skill" and skill_text else None,
                "finish_reason": result.get("finish_reason"),
                "usage": result.get("usage"),
                "error": result.get("error"),
                "api_key_source": key_source,
                "runner_python": sys.version.split()[0],
                "github_source": {
                    "repo": args.github_repo,
                    "branch": args.github_branch,
                    "refreshed": bool(args.refresh_from_github),
                },
            }

            md_path.write_text(render_result_markdown(meta, result.get("text", "")), encoding="utf-8")
            json_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
            written.extend([md_path, json_path])
            manifest_runs.append({"markdown": md_path.name, "metadata": json_path.name, "status": result["status"]})

            print("[{}] {} {} -> {}".format(result["status"], mode, iteration, md_path))
            if result["status"] == "quota_blocked":
                print("Quota blocked; stopping remaining calls to avoid contaminating the experiment.")
                stop_remaining = True
                break

    manifest = {
        "schema": 2,
        "created_at": iso_z(utc_now()),
        "benchmark": benchmark_name,
        "model": args.model,
        "mode": args.mode,
        "repeat": args.repeat,
        "runs": manifest_runs,
    }
    manifest_path = results_dir / (run_prefix + "-" + slug(args.model) + "-manifest.json")
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    written.append(manifest_path)

    if args.publish_github:
        root = find_lab_root(benchmark_dir)
        if root is None:
            raise RunnerError("Cannot infer lab root for GitHub publishing.")
        commit_shas = []
        for path in written:
            rel = path.resolve().relative_to(root.resolve()).as_posix()
            text = path.read_text(encoding="utf-8")
            sha = github_put_text(
                args.github_repo,
                args.github_branch,
                rel,
                text,
                github_token,
                "benchmark: publish {}".format(path.name),
            )
            commit_shas.append(sha)
        print("Published {} result files to {}@{}.".format(len(written), args.github_repo, args.github_branch))
        if commit_shas:
            print("Last GitHub commit: {}".format(commit_shas[-1]))

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except RunnerError as exc:
        print("ERROR: {}".format(exc), file=sys.stderr)
        sys.exit(2)
