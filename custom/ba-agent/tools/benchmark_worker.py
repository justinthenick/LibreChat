#!/usr/bin/env python3
"""Poll a GitHub-controlled BA benchmark job queue and run new jobs on the NAS.

Python 3.8+ standard library only. GitHub reads are authenticated with the
configured token when available. Model-visible benchmark/pipeline inputs are
refreshed by this worker before execution, so the runners can execute from the
local cache without making anonymous GitHub reads.

Each unique job ID is attempted once and recorded locally.
"""

import argparse
import base64
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

DEFAULT_REPO = "justinthenick/LibreChat"
DEFAULT_BRANCH = "feature/ba-agent-v0.1"
DEFAULT_ROOT = "/volume1/docker/librechat-ba-lab"
DEFAULT_JOBS_PATH = "custom/ba-agent/automation/jobs.json"
DEFAULT_ENV_FILE = "/volume1/docker/librechat/deploy/synology/.env"
DEFAULT_TOKEN_ENV = "GITHUB_TELEMETRY_TOKEN"


class WorkerError(RuntimeError):
    pass


def load_dotenv(path):
    values = {}
    if not path.exists():
        raise WorkerError("Environment file not found: {}".format(path))
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        if key:
            values[key] = value
    return values


def merged_environment(env_file):
    values = load_dotenv(env_file)
    values.update(os.environ)
    return values


def github_request(url, token=None, accept="application/vnd.github+json"):
    headers = {
        "Accept": accept,
        "User-Agent": "ba-agent-benchmark-worker/2.0",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = "Bearer {}".format(token)
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise WorkerError("GitHub HTTP {}: {}".format(exc.code, body[:500]))
    except urllib.error.URLError as exc:
        raise WorkerError("GitHub network error: {}".format(exc.reason))


def contents_url(repo, branch, repo_path):
    encoded_path = urllib.parse.quote(repo_path.strip("/"), safe="/")
    ref = urllib.parse.quote(branch, safe="")
    return "https://api.github.com/repos/{}/contents/{}?ref={}".format(repo, encoded_path, ref)


def fetch_json(repo, branch, repo_path, token=None):
    raw = github_request(
        contents_url(repo, branch, repo_path),
        token=token,
        accept="application/vnd.github.raw+json",
    )
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise WorkerError("Invalid JSON in {}: {}".format(repo_path, exc))
    if not isinstance(value, dict):
        raise WorkerError("Expected JSON object in {}".format(repo_path))
    return value


def fetch_text(repo, branch, repo_path, token=None):
    raw = github_request(contents_url(repo, branch, repo_path), token=token)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise WorkerError("Invalid GitHub content response for {}: {}".format(repo_path, exc))
    if not isinstance(data, dict) or data.get("type") != "file" or data.get("encoding") != "base64":
        raise WorkerError("GitHub path is not a text file: {}".format(repo_path))
    try:
        return base64.b64decode(data.get("content", "")).decode("utf-8")
    except Exception as exc:
        raise WorkerError("Cannot decode {}: {}".format(repo_path, exc))


def write_repo_file(root, repo_path, text):
    path = root / repo_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def load_state(path):
    if not path.exists():
        return {"schema": 2, "jobs": {}}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"schema": 2, "jobs": {}}
    if not isinstance(value, dict) or not isinstance(value.get("jobs"), dict):
        return {"schema": 2, "jobs": {}}
    return value


def save_state(path, state):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temp.replace(path)


def validate_job(job):
    if not isinstance(job, dict):
        raise WorkerError("Job entry must be a JSON object")
    job_id = str(job.get("id") or "").strip()
    if not job_id:
        raise WorkerError("Job is missing id")
    benchmark = str(job.get("benchmark") or "").strip()
    if not benchmark.startswith("custom/ba-agent/benchmarks/"):
        raise WorkerError("Job {} has invalid benchmark path".format(job_id))
    model = str(job.get("model") or "").strip()
    if not model:
        raise WorkerError("Job {} is missing model".format(job_id))
    runner = str(job.get("runner") or "benchmark").strip().lower()
    if runner not in ("benchmark", "pipeline"):
        raise WorkerError("Job {} has invalid runner {}".format(job_id, runner))
    repeat = int(job.get("repeat") or 1)
    if repeat < 1 or repeat > 5:
        raise WorkerError("Job {} repeat must be 1..5".format(job_id))
    temperature = float(job.get("temperature", 0.0))
    if temperature < 0.0 or temperature > 2.0:
        raise WorkerError("Job {} temperature must be 0..2".format(job_id))

    normalized = {
        "id": job_id,
        "benchmark": benchmark,
        "model": model,
        "runner": runner,
        "repeat": repeat,
        "temperature": temperature,
        "enabled": bool(job.get("enabled", True)),
        "auto_fallback": bool(job.get("auto_fallback", False)),
        "comparison_group": str(job.get("comparison_group") or "").strip() or None,
        "fallback_models": [str(x).strip() for x in (job.get("fallback_models") or []) if str(x).strip()],
    }
    if runner == "benchmark":
        mode = str(job.get("mode") or "skill").strip()
        if mode not in ("baseline", "skill", "both"):
            raise WorkerError("Job {} has invalid mode {}".format(job_id, mode))
        normalized["mode"] = mode
    else:
        normalized["pipeline_config"] = str(job.get("pipeline_config") or "pipeline-specialists.json").strip()
    return normalized


def refresh_benchmark_inputs(root, repo, branch, job, token):
    benchmark_rel = job["benchmark"].rstrip("/")
    config_rel = benchmark_rel + "/benchmark.json"
    config_text = fetch_text(repo, branch, config_rel, token=token)
    write_repo_file(root, config_rel, config_text)
    try:
        config = json.loads(config_text)
    except ValueError as exc:
        raise WorkerError("Invalid benchmark config {}: {}".format(config_rel, exc))

    for name in (str(config.get("input") or "input.md"), str(config.get("prompt") or "prompt.md")):
        rel = benchmark_rel + "/" + name
        write_repo_file(root, rel, fetch_text(repo, branch, rel, token=token))

    skill_config = config.get("skill")
    if skill_config:
        benchmark_dir = root / benchmark_rel
        skill_path = (benchmark_dir / str(skill_config)).resolve()
        try:
            skill_rel = skill_path.relative_to(root.resolve()).as_posix()
        except ValueError:
            raise WorkerError("Configured skill resolves outside lab root: {}".format(skill_path))
        write_repo_file(root, skill_rel, fetch_text(repo, branch, skill_rel, token=token))


def refresh_pipeline_inputs(root, repo, branch, job, token):
    benchmark_rel = job["benchmark"].rstrip("/")
    config_name = job["pipeline_config"]
    config_rel = benchmark_rel + "/" + config_name
    config_text = fetch_text(repo, branch, config_rel, token=token)
    write_repo_file(root, config_rel, config_text)
    try:
        config = json.loads(config_text)
    except ValueError as exc:
        raise WorkerError("Invalid pipeline config {}: {}".format(config_rel, exc))

    for name in (str(config.get("input") or "input.md"), str(config.get("prompt") or "pipeline-prompt.md")):
        rel = benchmark_rel + "/" + name
        write_repo_file(root, rel, fetch_text(repo, branch, rel, token=token))

    benchmark_dir = root / benchmark_rel
    for stage in config.get("stages") or []:
        agent_path = (benchmark_dir / str(stage.get("agent") or "")).resolve()
        try:
            agent_rel = agent_path.relative_to(root.resolve()).as_posix()
        except ValueError:
            raise WorkerError("Pipeline agent resolves outside lab root: {}".format(agent_path))
        write_repo_file(root, agent_rel, fetch_text(repo, branch, agent_rel, token=token))


def refresh_job_inputs(root, repo, branch, job, token):
    if not token:
        raise WorkerError("Authenticated GitHub token is required for autonomous refresh")
    if job["runner"] == "pipeline":
        refresh_pipeline_inputs(root, repo, branch, job, token)
    else:
        refresh_benchmark_inputs(root, repo, branch, job, token)


def run_job(root, env_file, token_env, repo, branch, job):
    benchmark = root / job["benchmark"]
    benchmark.mkdir(parents=True, exist_ok=True)

    if job["runner"] == "pipeline":
        runner = root / "custom/ba-agent/tools/agent_pipeline_runner.py"
        if not runner.exists():
            raise WorkerError("Pipeline runner not found: {}".format(runner))
        cmd = [
            sys.executable, str(runner), str(benchmark),
            "--pipeline-config", job["pipeline_config"],
            "--model", job["model"],
            "--temperature", str(job["temperature"]),
            "--run-id", job["id"],
            "--env-file", str(env_file),
            "--publish-github",
            "--github-token-env", token_env,
            "--github-repo", repo,
            "--github-branch", branch,
        ]
        label = "pipeline {}".format(job["pipeline_config"])
    else:
        runner = root / "custom/ba-agent/tools/benchmark_runner.py"
        if not runner.exists():
            raise WorkerError("Runner not found: {}".format(runner))
        cmd = [
            sys.executable, str(runner), str(benchmark),
            "--model", job["model"],
            "--mode", job["mode"],
            "--repeat", str(job["repeat"]),
            "--temperature", str(job["temperature"]),
            "--run-id", job["id"],
            "--env-file", str(env_file),
            "--publish-github",
            "--github-token-env", token_env,
            "--github-repo", repo,
            "--github-branch", branch,
        ]
        label = job["mode"]

    print("[worker] starting {}: {} {} {}".format(job["id"], job["model"], label, job["benchmark"]))
    proc = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output = proc.stdout or ""
    if output:
        print(output.rstrip())
    print("[worker] finished {} rc={}".format(job["id"], proc.returncode))
    return proc.returncode, output


def classify_operational_status(output):
    text = (output or "").lower()
    if "quota_blocked" in text:
        return "quota_blocked"
    if "provider_busy" in text:
        return "provider_busy"
    if "network_error" in text:
        return "network_error"
    return None


def main():
    parser = argparse.ArgumentParser(description="Poll GitHub for BA benchmark jobs and execute each job ID once.")
    parser.add_argument("--repo", default=DEFAULT_REPO)
    parser.add_argument("--branch", default=DEFAULT_BRANCH)
    parser.add_argument("--root", default=DEFAULT_ROOT)
    parser.add_argument("--jobs-path", default=DEFAULT_JOBS_PATH)
    parser.add_argument("--env-file", default=DEFAULT_ENV_FILE)
    parser.add_argument("--github-token-env", default=DEFAULT_TOKEN_ENV)
    parser.add_argument("--state-file")
    parser.add_argument("--interval", type=int, default=300)
    parser.add_argument("--once", action="store_true", help="Poll once and exit instead of looping.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    env_file = Path(args.env_file).resolve()
    state_file = Path(args.state_file).resolve() if args.state_file else root / "custom/ba-agent/automation/worker-state.json"

    if not env_file.exists():
        raise WorkerError("Environment file not found: {}".format(env_file))
    if args.interval < 60 and not args.once:
        raise WorkerError("Loop interval must be at least 60 seconds")

    env = merged_environment(env_file)
    token = env.get(args.github_token_env, "").strip() or None
    if not token:
        raise WorkerError("{} is required for autonomous GitHub reads".format(args.github_token_env))

    print("[worker] repo={} branch={} jobs={}".format(args.repo, args.branch, args.jobs_path))
    print("[worker] root={} env={}".format(root, env_file))
    print("[worker] state={}".format(state_file))
    print("[worker] authenticated GitHub reads enabled")

    while True:
        try:
            queue = fetch_json(args.repo, args.branch, args.jobs_path, token=token)
            jobs = queue.get("jobs") or []
            if not isinstance(jobs, list):
                raise WorkerError("jobs.json must contain a jobs array")

            state = load_state(state_file)
            state["schema"] = 2
            known = state["jobs"]
            pending = []
            for raw_job in jobs:
                job = validate_job(raw_job)
                if job["enabled"] and job["id"] not in known:
                    pending.append(job)

            print("[worker] {} new job(s)".format(len(pending)) if pending else "[worker] no new jobs")

            for job in pending:
                record = {
                    "model": job["model"],
                    "runner": job["runner"],
                    "benchmark": job["benchmark"],
                    "attempted_at_epoch": int(time.time()),
                    "comparison_group": job.get("comparison_group"),
                    "auto_fallback": job.get("auto_fallback", False),
                    "fallback_models": job.get("fallback_models") or [],
                }
                if job["runner"] == "benchmark":
                    record["mode"] = job["mode"]
                else:
                    record["pipeline_config"] = job["pipeline_config"]
                try:
                    refresh_job_inputs(root, args.repo, args.branch, job, token)
                    record["source_refresh"] = "authenticated"
                    rc, output = run_job(root, env_file, args.github_token_env, args.repo, args.branch, job)
                    record["return_code"] = rc
                    record["status"] = "completed" if rc == 0 else "failed"
                    record["operational_status"] = classify_operational_status(output)
                    record["output_tail"] = output[-4000:]
                except Exception as exc:
                    record["return_code"] = None
                    record["status"] = "failed"
                    record["error"] = str(exc)
                    print("[worker] job {} failed: {}".format(job["id"], exc))
                known[job["id"]] = record
                save_state(state_file, state)

        except Exception as exc:
            print("[worker] poll error: {}".format(exc))

        if args.once:
            break
        time.sleep(args.interval)

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except WorkerError as exc:
        print("ERROR: {}".format(exc))
        raise SystemExit(2)
