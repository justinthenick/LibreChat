#!/usr/bin/env python3
"""Run a persisted multi-stage BA specialist-agent pipeline against Gemini.

Python 3.8+ standard-library-only. The runner refreshes model-visible pipeline
inputs/agent instructions from GitHub, calls Gemini once per stage, persists
stage outputs and hashes, and optionally publishes results back to GitHub.
Evaluator-only gold standards/rubrics are never loaded.
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


class PipelineError(RuntimeError):
    pass


def utc_now():
    return dt.datetime.now(dt.timezone.utc)


def iso_z(value):
    return value.astimezone(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def slug(value):
    value = re.sub(r"[^a-z0-9._-]+", "-", value.strip().lower())
    return value.strip("-") or "run"


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_dotenv(path):
    result = {}
    if not path.exists():
        raise PipelineError("Environment file not found: {}".format(path))
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        if key:
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
            return value
    raise PipelineError("No Gemini API key found. Set one of: {}".format(", ".join(KEY_ENV_CANDIDATES)))


def resolve_github_token(env, token_env):
    value = env.get(token_env, "").strip()
    if value:
        return value
    raise PipelineError("GitHub publishing requested but {} is not set".format(token_env))


def strip_frontmatter(text):
    if not text.startswith("---\n"):
        return text
    lines = text.splitlines()
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            return "\n".join(lines[idx + 1 :]).lstrip() + "\n"
    return text


def document_version(text):
    match = re.search(r"^Version:\s*\*\*([^*]+)\*\*", text, flags=re.MULTILINE)
    return match.group(1).strip() if match else None


def find_lab_root(path):
    current = path.resolve()
    for candidate in [current] + list(current.parents):
        if (candidate / "custom" / "ba-agent").exists():
            return candidate
    return None


def github_request(url, token=None, method="GET", payload=None):
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "ba-agent-pipeline-runner/1.0",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = "Bearer {}".format(token)
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            raw = response.read().decode("utf-8")
            return response.status, json.loads(raw) if raw else None
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise PipelineError("GitHub HTTP {}: {}".format(exc.code, body[:500]))
    except urllib.error.URLError as exc:
        raise PipelineError("GitHub network error: {}".format(exc.reason))


def github_fetch_text(repo, branch, repo_path):
    encoded_path = urllib.parse.quote(repo_path.strip("/"), safe="/")
    ref = urllib.parse.quote(branch, safe="")
    url = "https://api.github.com/repos/{}/contents/{}?ref={}".format(repo, encoded_path, ref)
    _, data = github_request(url)
    if not isinstance(data, dict) or data.get("encoding") != "base64":
        raise PipelineError("Unexpected GitHub content response for {}".format(repo_path))
    return base64.b64decode(data.get("content", "")).decode("utf-8")


def github_put_text(repo, branch, repo_path, text, token, message):
    encoded_path = urllib.parse.quote(repo_path.strip("/"), safe="/")
    ref = urllib.parse.quote(branch, safe="")
    get_url = "https://api.github.com/repos/{}/contents/{}?ref={}".format(repo, encoded_path, ref)
    sha = None
    try:
        _, existing = github_request(get_url, token=token)
        if isinstance(existing, dict):
            sha = existing.get("sha")
    except PipelineError as exc:
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
    _, result = github_request(put_url, token=token, method="PUT", payload=payload)
    commit = result.get("commit") if isinstance(result, dict) else None
    return commit.get("sha") if isinstance(commit, dict) else None


def safe_provider_error(raw, code):
    try:
        parsed = json.loads(raw)
        error = parsed.get("error") if isinstance(parsed, dict) else None
        if isinstance(error, dict):
            return json.dumps({
                "message": str(error.get("message") or "HTTP {}".format(code)),
                "status": error.get("status"),
            }, ensure_ascii=False)
    except ValueError:
        pass
    return "HTTP {}: provider request failed".format(code)


def gemini_generate(api_key, api_base, model, user_prompt, system_instruction, temperature, max_output_tokens, timeout):
    encoded_model = urllib.parse.quote(model, safe="._-")
    endpoint = "{}/models/{}:generateContent".format(api_base.rstrip("/"), encoded_model)
    payload = {
        "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
        "generationConfig": {"temperature": temperature, "maxOutputTokens": max_output_tokens},
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
            "User-Agent": "ba-agent-pipeline-runner/1.0",
        },
    )
    started = utc_now()
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
            status_code = response.status
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        classification = "quota_blocked" if exc.code == 429 else "provider_busy" if exc.code == 503 else "provider_error"
        return {
            "status": classification, "http_status": exc.code,
            "started_at": iso_z(started), "ended_at": iso_z(utc_now()),
            "error": safe_provider_error(body, exc.code), "text": "", "usage": None, "finish_reason": None,
        }
    except urllib.error.URLError as exc:
        return {
            "status": "network_error", "http_status": None,
            "started_at": iso_z(started), "ended_at": iso_z(utc_now()),
            "error": str(exc.reason), "text": "", "usage": None, "finish_reason": None,
        }
    try:
        data = json.loads(raw)
    except ValueError:
        return {
            "status": "provider_error", "http_status": status_code,
            "started_at": iso_z(started), "ended_at": iso_z(utc_now()),
            "error": "Provider returned non-JSON response", "text": "", "usage": None, "finish_reason": None,
        }
    candidates = data.get("candidates") or []
    if not candidates:
        return {
            "status": "no_candidate", "http_status": status_code,
            "started_at": iso_z(started), "ended_at": iso_z(utc_now()),
            "error": "No candidate returned", "text": "",
            "usage": data.get("usageMetadata") or data.get("usage_metadata"), "finish_reason": None,
        }
    first = candidates[0]
    parts = ((first.get("content") or {}).get("parts") or [])
    texts = [part.get("text", "") for part in parts if isinstance(part, dict) and part.get("text")]
    output_text = "\n".join(texts).strip()
    return {
        "status": "success" if output_text else "empty_output",
        "http_status": status_code,
        "started_at": iso_z(started), "ended_at": iso_z(utc_now()),
        "error": None if output_text else "Candidate contained no text output",
        "text": output_text,
        "usage": data.get("usageMetadata") or data.get("usage_metadata"),
        "finish_reason": first.get("finishReason") or first.get("finish_reason"),
    }


def refresh_pipeline(benchmark_dir, config_name, repo, branch):
    root = find_lab_root(benchmark_dir)
    if root is None:
        raise PipelineError("Cannot infer BA lab root")
    benchmark_rel = benchmark_dir.resolve().relative_to(root.resolve()).as_posix()
    config_rel = benchmark_rel + "/" + config_name
    config_text = github_fetch_text(repo, branch, config_rel)
    config_path = benchmark_dir / config_name
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(config_text, encoding="utf-8")
    config = json.loads(config_text)

    input_name = str(config.get("input") or "input.md")
    prompt_name = str(config.get("prompt") or "pipeline-prompt.md")
    for name in (input_name, prompt_name):
        rel = benchmark_rel + "/" + name
        path = benchmark_dir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(github_fetch_text(repo, branch, rel), encoding="utf-8")

    for stage in config.get("stages") or []:
        agent_path = (benchmark_dir / str(stage.get("agent") or "")).resolve()
        try:
            agent_rel = agent_path.relative_to(root.resolve()).as_posix()
        except ValueError:
            raise PipelineError("Agent path resolves outside BA lab root")
        agent_path.parent.mkdir(parents=True, exist_ok=True)
        agent_path.write_text(github_fetch_text(repo, branch, agent_rel), encoding="utf-8")
    return config


def usage_number(usage, key):
    if not isinstance(usage, dict):
        return 0
    value = usage.get(key)
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def parse_args(argv):
    parser = argparse.ArgumentParser(description="Run a multi-call BA specialist-agent pipeline against Gemini.")
    parser.add_argument("benchmark", type=Path)
    parser.add_argument("--pipeline-config", default="pipeline-specialists.json")
    parser.add_argument("--model", required=True)
    parser.add_argument("--env-file", type=Path)
    parser.add_argument("--api-base", default=DEFAULT_API_BASE)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--max-output-tokens", type=int, default=8192)
    parser.add_argument("--timeout", type=int, default=180)
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
    benchmark_dir.mkdir(parents=True, exist_ok=True)

    if args.refresh_from_github:
        config = refresh_pipeline(benchmark_dir, args.pipeline_config, args.github_repo, args.github_branch)
    else:
        config = json.loads((benchmark_dir / args.pipeline_config).read_text(encoding="utf-8"))

    env = merged_environment(args.env_file)
    api_key = resolve_api_key(env)
    github_token = resolve_github_token(env, args.github_token_env) if args.publish_github else None

    input_name = str(config.get("input") or "input.md")
    prompt_name = str(config.get("prompt") or "pipeline-prompt.md")
    source_text = (benchmark_dir / input_name).read_text(encoding="utf-8")
    common_prompt = (benchmark_dir / prompt_name).read_text(encoding="utf-8")
    stages = config.get("stages") or []
    if not stages:
        raise PipelineError("Pipeline has no stages")

    run_id = slug(args.run_id or ("pipeline-" + utc_now().strftime("%Y%m%dT%H%M%SZ")))
    model_slug = slug(args.model)
    results_dir = benchmark_dir / str(config.get("results_dir") or "results")
    results_dir.mkdir(parents=True, exist_ok=True)
    root = find_lab_root(benchmark_dir)
    if root is None:
        raise PipelineError("Cannot infer BA lab root")
    results_rel = results_dir.resolve().relative_to(root.resolve()).as_posix()

    previous = None
    stage_records = []
    files_to_publish = []
    total_prompt = total_candidate = total_thoughts = total_tokens = 0

    for index, stage in enumerate(stages, start=1):
        stage_id = slug(str(stage.get("id") or "stage-{}".format(index)))
        stage_name = str(stage.get("name") or stage_id)
        instruction = str(stage.get("instruction") or "").strip()
        agent_path = (benchmark_dir / str(stage.get("agent") or "")).resolve()
        agent_text = agent_path.read_text(encoding="utf-8")
        system_instruction = strip_frontmatter(agent_text)

        if index == 1:
            stage_input = common_prompt.rstrip() + "\n\n" + instruction + "\n\n# Original source packet\n\n" + source_text
        else:
            stage_input = common_prompt.rstrip() + "\n\n" + instruction + "\n\n# Upstream handoff artifact\n\n" + (previous or "")

        result = gemini_generate(
            api_key, args.api_base, args.model, stage_input, system_instruction,
            args.temperature, args.max_output_tokens, args.timeout,
        )
        usage = result.get("usage") or {}
        total_prompt += usage_number(usage, "promptTokenCount")
        total_candidate += usage_number(usage, "candidatesTokenCount")
        total_thoughts += usage_number(usage, "thoughtsTokenCount")
        total_tokens += usage_number(usage, "totalTokenCount")

        meta = {
            "pipeline": str(config.get("name") or args.pipeline_config),
            "run_id": run_id,
            "stage_index": index,
            "stage_id": stage_id,
            "stage_name": stage_name,
            "model": args.model,
            "status": result.get("status"),
            "started_at": result.get("started_at"),
            "ended_at": result.get("ended_at"),
            "temperature": args.temperature,
            "max_output_tokens": args.max_output_tokens,
            "stage_input_sha256": sha256_text(stage_input),
            "upstream_output_sha256": sha256_text(previous) if previous is not None else None,
            "agent_path": agent_path.relative_to(root.resolve()).as_posix(),
            "agent_version": document_version(agent_text),
            "agent_sha256": sha256_text(agent_text),
            "finish_reason": result.get("finish_reason"),
            "usage": usage,
            "error": result.get("error"),
        }
        stem = "{}-{}-pipeline-01-stage-{:02d}-{}".format(run_id, model_slug, index, stage_id)
        md_path = results_dir / (stem + ".md")
        json_path = results_dir / (stem + ".json")
        md_text = "# BA Specialist Pipeline Stage\n\n## Metadata\n\n```json\n{}\n```\n\n---\n\n## Stage output\n\n{}\n".format(
            json.dumps(meta, indent=2, sort_keys=True), result.get("text") or "_No model output._"
        )
        json_text = json.dumps(meta, indent=2, sort_keys=True) + "\n"
        md_path.write_text(md_text, encoding="utf-8")
        json_path.write_text(json_text, encoding="utf-8")
        files_to_publish.extend([(md_path, md_text), (json_path, json_text)])
        stage_records.append({
            "stage_id": stage_id,
            "stage_name": stage_name,
            "status": result.get("status"),
            "markdown": md_path.name,
            "metadata": json_path.name,
            "output_sha256": sha256_text(result.get("text") or ""),
            "usage": usage,
        })
        print("[pipeline] stage {} {} -> {}".format(index, stage_id, result.get("status")))
        if result.get("status") != "success":
            previous = result.get("text") or ""
            break
        previous = result.get("text") or ""

    overall_status = "success" if len(stage_records) == len(stages) and all(s["status"] == "success" for s in stage_records) else "incomplete"
    combined_stem = "{}-{}-pipeline-01".format(run_id, model_slug)
    combined_path = results_dir / (combined_stem + ".md")
    combined_meta_path = results_dir / (combined_stem + ".json")
    manifest_path = results_dir / ("{}-{}-pipeline-manifest.json".format(run_id, model_slug))

    combined_lines = [
        "# BA Specialist Pipeline Result", "",
        "- Pipeline: `{}`".format(config.get("name") or args.pipeline_config),
        "- Model: `{}`".format(args.model),
        "- Status: `{}`".format(overall_status),
        "- Run ID: `{}`".format(run_id),
        "- Total prompt tokens: `{}`".format(total_prompt),
        "- Total candidate tokens: `{}`".format(total_candidate),
        "- Total thought tokens: `{}`".format(total_thoughts),
        "- Total tokens: `{}`".format(total_tokens), "",
    ]
    for record in stage_records:
        stage_md = (results_dir / record["markdown"]).read_text(encoding="utf-8")
        marker = "## Stage output\n\n"
        output = stage_md.split(marker, 1)[1] if marker in stage_md else stage_md
        combined_lines.extend(["---", "", "## {} — {}".format(record["stage_id"], record["stage_name"]), "", output.strip(), ""])
    combined_text = "\n".join(combined_lines)
    combined_meta = {
        "schema": 1,
        "pipeline": config.get("name") or args.pipeline_config,
        "run_id": run_id,
        "model": args.model,
        "status": overall_status,
        "temperature": args.temperature,
        "input_sha256": sha256_text(source_text),
        "prompt_sha256": sha256_text(common_prompt),
        "stages": stage_records,
        "total_usage": {
            "promptTokenCount": total_prompt,
            "candidatesTokenCount": total_candidate,
            "thoughtsTokenCount": total_thoughts,
            "totalTokenCount": total_tokens,
        },
    }
    combined_meta_text = json.dumps(combined_meta, indent=2, sort_keys=True) + "\n"
    manifest_text = json.dumps({
        "schema": 1,
        "run_id": run_id,
        "status": overall_status,
        "combined_markdown": combined_path.name,
        "combined_metadata": combined_meta_path.name,
        "stages": stage_records,
    }, indent=2, sort_keys=True) + "\n"
    combined_path.write_text(combined_text, encoding="utf-8")
    combined_meta_path.write_text(combined_meta_text, encoding="utf-8")
    manifest_path.write_text(manifest_text, encoding="utf-8")
    files_to_publish.extend([(combined_path, combined_text), (combined_meta_path, combined_meta_text), (manifest_path, manifest_text)])

    if args.publish_github:
        last_commit = None
        for path, text in files_to_publish:
            repo_path = results_rel + "/" + path.name
            last_commit = github_put_text(
                args.github_repo, args.github_branch, repo_path, text, github_token,
                "pipeline: publish {}".format(path.name),
            )
        print("Published {} pipeline files to {}@{}.".format(len(files_to_publish), args.github_repo, args.github_branch))
        if last_commit:
            print("Last GitHub commit: {}".format(last_commit))

    print("[pipeline] {} -> {}".format(run_id, overall_status))
    print("[pipeline] combined result: {}".format(combined_path))
    return 0 if overall_status == "success" else 3


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except PipelineError as exc:
        print("ERROR: {}".format(exc))
        raise SystemExit(2)
