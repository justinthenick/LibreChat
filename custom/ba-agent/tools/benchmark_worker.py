#!/usr/bin/env python3
"""Poll a GitHub-controlled BA benchmark job queue and run new jobs on the NAS.

Python 3.8+ standard library only. The worker never stores API keys; it passes the
configured private .env path to the selected runner. Each unique job ID is
attempted once and recorded locally. To retry, publish a new job ID.
"""

import argparse
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


def fetch_json(repo, branch, repo_path):
    encoded_path = urllib.parse.quote(repo_path.strip("/"), safe="/")
    ref = urllib.parse.quote(branch, safe="")
    url = "https://api.github.com/repos/{}/contents/{}?ref={}".format(repo, encoded_path, ref)
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github.raw+json",
            "User-Agent": "ba-agent-benchmark-worker/1.1",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise WorkerError("GitHub HTTP {} for {}: {}".format(exc.code, repo_path, body[:500]))
    except urllib.error.URLError as exc:
        raise WorkerError("GitHub network error for {}: {}".format(repo_path, exc.reason))
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise WorkerError("Invalid JSON in {}: {}".format(repo_path, exc))
    if not isinstance(value, dict):
        raise WorkerError("Expected JSON object in {}".format(repo_path))
    return value


def load_state(path):
    if not path.exists():
        return {"schema": 1, "jobs": {}}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"schema": 1, "jobs": {}}
    if not isinstance(value, dict) or not isinstance(value.get("jobs"), dict):
        return {"schema": 1, "jobs": {}}
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
    }
    if runner == "benchmark":
        mode = str(job.get("mode") or "skill").strip()
        if mode not in ("baseline", "skill", "both"):
            raise WorkerError("Job {} has invalid mode {}".format(job_id, mode))
        normalized["mode"] = mode
    else:
        normalized["pipeline_config"] = str(job.get("pipeline_config") or "pipeline-specialists.json").strip()
    return normalized


def run_job(root, env_file, token_env, repo, branch, job):
    benchmark = root / job["benchmark"]
    benchmark.mkdir(parents=True, exist_ok=True)

    if job["runner"] == "pipeline":
        runner = root / "custom/ba-agent/tools/agent_pipeline_runner.py"
        if not runner.exists():
            raise WorkerError("Pipeline runner not found: {}".format(runner))
        cmd = [
            sys.executable,
            str(runner),
            str(benchmark),
            "--pipeline-config", job["pipeline_config"],
            "--model", job["model"],
            "--temperature", str(job["temperature"]),
            "--run-id", job["id"],
            "--env-file", str(env_file),
            "--refresh-from-github",
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
            sys.executable,
            str(runner),
            str(benchmark),
            "--model", job["model"],
            "--mode", job["mode"],
            "--repeat", str(job["repeat"]),
            "--temperature", str(job["temperature"]),
            "--run-id", job["id"],
            "--env-file", str(env_file),
            "--refresh-from-github",
            "--publish-github",
            "--github-token-env", token_env,
            "--github-repo", repo,
            "--github-branch", branch,
        ]
        label = "{}".format(job["mode"])

    print("[worker] starting {}: {} {} {}".format(job["id"], job["model"], label, job["benchmark"]))
    proc = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output = proc.stdout or ""
    if output:
        print(output.rstrip())
    print("[worker] finished {} rc={}".format(job["id"], proc.returncode))
    return proc.returncode, output


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

    print("[worker] repo={} branch={} jobs={}".format(args.repo, args.branch, args.jobs_path))
    print("[worker] root={} env={}".format(root, env_file))
    print("[worker] state={}".format(state_file))

    while True:
        try:
            queue = fetch_json(args.repo, args.branch, args.jobs_path)
            jobs = queue.get("jobs") or []
            if not isinstance(jobs, list):
                raise WorkerError("jobs.json must contain a jobs array")

            state = load_state(state_file)
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
                }
                if job["runner"] == "benchmark":
                    record["mode"] = job["mode"]
                else:
                    record["pipeline_config"] = job["pipeline_config"]
                try:
                    rc, output = run_job(root, env_file, args.github_token_env, args.repo, args.branch, job)
                    record["return_code"] = rc
                    record["status"] = "completed" if rc == 0 else "failed"
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
