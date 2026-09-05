#!/usr/bin/env python3
"""Deterministic autonomy controller for the BA/Skill benchmark lab.

This controller deliberately handles only operational transitions that can be
made without semantic judgement. It may enqueue fresh fallback jobs after
provider/quota/network failures when the source job explicitly opts in via
`auto_fallback` and provides `fallback_models`. It never edits Skills, scores
semantic quality, promotes releases, or deploys production.

Python 3.8+ standard library only.
"""

import argparse
import base64
import datetime as dt
import json
import os
from pathlib import Path
import re
import urllib.error
import urllib.parse
import urllib.request

DEFAULT_REPO = "justinthenick/LibreChat"
DEFAULT_BRANCH = "feature/ba-agent-v0.1"
DEFAULT_ROOT = "/volume1/docker/librechat-ba-lab"
DEFAULT_ENV_FILE = "/volume1/docker/librechat/deploy/synology/.env"
DEFAULT_TOKEN_ENV = "GITHUB_TELEMETRY_TOKEN"
DEFAULT_JOBS_PATH = "custom/ba-agent/automation/jobs.json"


class ControllerError(RuntimeError):
    pass


def load_dotenv(path):
    values = {}
    if not path.exists():
        raise ControllerError("Environment file not found: {}".format(path))
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


def github_request(url, token, method="GET", payload=None):
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "ba-agent-autonomy-controller/1.0",
        "X-GitHub-Api-Version": "2022-11-28",
        "Authorization": "Bearer {}".format(token),
    }
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            raw = response.read().decode("utf-8")
            return response.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise ControllerError("GitHub HTTP {}: {}".format(exc.code, body[:500]))
    except urllib.error.URLError as exc:
        raise ControllerError("GitHub network error: {}".format(exc.reason))


def contents_url(repo, branch, repo_path):
    encoded = urllib.parse.quote(repo_path.strip("/"), safe="/")
    ref = urllib.parse.quote(branch, safe="")
    return "https://api.github.com/repos/{}/contents/{}?ref={}".format(repo, encoded, ref)


def github_get_json_file(repo, branch, repo_path, token):
    _, data = github_request(contents_url(repo, branch, repo_path), token)
    if not isinstance(data, dict) or data.get("type") != "file" or data.get("encoding") != "base64":
        raise ControllerError("GitHub path is not a JSON file: {}".format(repo_path))
    try:
        text = base64.b64decode(data.get("content", "")).decode("utf-8")
        value = json.loads(text)
    except Exception as exc:
        raise ControllerError("Invalid JSON in {}: {}".format(repo_path, exc))
    if not isinstance(value, dict):
        raise ControllerError("Expected JSON object in {}".format(repo_path))
    return value, data.get("sha")


def github_put_json_file(repo, branch, repo_path, value, sha, token, message):
    encoded = urllib.parse.quote(repo_path.strip("/"), safe="/")
    url = "https://api.github.com/repos/{}/contents/{}".format(repo, encoded)
    text = json.dumps(value, indent=2, ensure_ascii=False) + "\n"
    payload = {
        "message": message,
        "content": base64.b64encode(text.encode("utf-8")).decode("ascii"),
        "branch": branch,
        "sha": sha,
    }
    _, result = github_request(url, token, method="PUT", payload=payload)
    commit = result.get("commit") if isinstance(result, dict) else None
    return commit.get("sha") if isinstance(commit, dict) else None


def read_json(path, default):
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else default
    except Exception:
        return default


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temp.replace(path)


def slug(value):
    value = re.sub(r"[^a-z0-9]+", "-", str(value).lower()).strip("-")
    return value or "model"


def next_fallback_model(job):
    chain = [str(x).strip() for x in (job.get("fallback_models") or []) if str(x).strip()]
    current = str(job.get("model") or "").strip()
    if not chain:
        return None
    if current in chain:
        index = chain.index(current) + 1
        return chain[index] if index < len(chain) else None
    return chain[0]


def operational_failure(record):
    status = str(record.get("operational_status") or "").strip().lower()
    return status if status in ("provider_busy", "quota_blocked", "network_error") else None


def clone_for_model(job, new_model, existing_ids):
    clone = dict(job)
    clone["model"] = new_model
    base = str(job.get("id") or "job")
    suffix = "auto-{}".format(slug(new_model))
    candidate = base + "-" + suffix
    counter = 2
    while candidate in existing_ids:
        candidate = base + "-{}-{}".format(suffix, counter)
        counter += 1
    clone["id"] = candidate
    clone["enabled"] = True
    clone["autonomy_parent"] = base
    clone["autonomy_reason"] = "operational_fallback"
    return clone


def choose_group(queue_jobs, trigger_job):
    group = str(trigger_job.get("comparison_group") or "").strip()
    if not group:
        return [trigger_job]
    model = str(trigger_job.get("model") or "")
    members = [
        job for job in queue_jobs
        if isinstance(job, dict)
        and str(job.get("comparison_group") or "").strip() == group
        and str(job.get("model") or "") == model
        and bool(job.get("enabled", True))
    ]
    return members or [trigger_job]


def main():
    parser = argparse.ArgumentParser(description="Advance deterministic BA lab operational state.")
    parser.add_argument("--repo", default=DEFAULT_REPO)
    parser.add_argument("--branch", default=DEFAULT_BRANCH)
    parser.add_argument("--root", default=DEFAULT_ROOT)
    parser.add_argument("--jobs-path", default=DEFAULT_JOBS_PATH)
    parser.add_argument("--env-file", default=DEFAULT_ENV_FILE)
    parser.add_argument("--github-token-env", default=DEFAULT_TOKEN_ENV)
    parser.add_argument("--worker-state")
    parser.add_argument("--controller-state")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    env_file = Path(args.env_file).resolve()
    worker_state_path = Path(args.worker_state).resolve() if args.worker_state else root / "custom/ba-agent/automation/worker-state.json"
    controller_state_path = Path(args.controller_state).resolve() if args.controller_state else root / "custom/ba-agent/automation/controller-state.json"

    env = merged_environment(env_file)
    token = env.get(args.github_token_env, "").strip()
    if not token:
        raise ControllerError("{} is required".format(args.github_token_env))

    queue, queue_sha = github_get_json_file(args.repo, args.branch, args.jobs_path, token)
    jobs = queue.get("jobs") or []
    if not isinstance(jobs, list):
        raise ControllerError("jobs.json must contain a jobs array")
    worker_state = read_json(worker_state_path, {"jobs": {}})
    records = worker_state.get("jobs") if isinstance(worker_state.get("jobs"), dict) else {}
    state = read_json(controller_state_path, {"schema": 1, "handled": {}})
    handled = state.setdefault("handled", {})

    by_id = {str(job.get("id")): job for job in jobs if isinstance(job, dict) and job.get("id")}
    existing_ids = set(by_id)
    additions = []

    for job_id, job in list(by_id.items()):
        if not bool(job.get("auto_fallback", False)):
            continue
        record = records.get(job_id)
        if not isinstance(record, dict):
            continue
        failure = operational_failure(record)
        if not failure:
            continue
        if handled.get(job_id):
            continue
        new_model = next_fallback_model(job)
        if not new_model:
            handled[job_id] = {
                "at": dt.datetime.now(dt.timezone.utc).isoformat(),
                "action": "exhausted",
                "reason": failure,
            }
            print("[controller] {} operationally failed; fallback chain exhausted".format(job_id))
            continue

        members = choose_group(jobs, job)
        created = []
        for member in members:
            member_id = str(member.get("id") or "")
            if handled.get(member_id):
                continue
            clone = clone_for_model(member, new_model, existing_ids)
            existing_ids.add(clone["id"])
            additions.append(clone)
            created.append(clone["id"])
            handled[member_id] = {
                "at": dt.datetime.now(dt.timezone.utc).isoformat(),
                "action": "fallback_queued",
                "reason": failure,
                "model": new_model,
                "job_id": clone["id"],
            }
        if created:
            print("[controller] {} -> {} on {}".format(job_id, ", ".join(created), new_model))

    if additions:
        queue["jobs"].extend(additions)
        commit = github_put_json_file(
            args.repo, args.branch, args.jobs_path, queue, queue_sha, token,
            "automation: queue operational fallback jobs",
        )
        print("[controller] queued {} fallback job(s); commit={}".format(len(additions), commit or "unknown"))
    else:
        print("[controller] no deterministic transition required")

    state["schema"] = 1
    state["last_checked_at"] = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    write_json(controller_state_path, state)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ControllerError as exc:
        print("ERROR: {}".format(exc))
        raise SystemExit(2)
