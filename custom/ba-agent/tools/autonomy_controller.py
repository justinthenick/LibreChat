#!/usr/bin/env python3
"""Deterministic autonomy controller for the BA/Skill benchmark lab.

This controller deliberately handles only operational transitions that can be
made without semantic judgement. It may enqueue one fresh same-model retry for
provider/quota/network failures, then enqueue a cross-model fallback when the
source job explicitly opts in via `auto_fallback` and provides
`fallback_models`. Same-model retries preserve failed artifacts and use fresh
job IDs, so experiments remain auditable.

When an execution retry/fallback changes the deterministic result filenames,
the controller also clones any waiting semantic job that references those
filenames and rewrites it to follow the new execution lineage. This removes the
manual execution-to-assessment relinking delay while preserving the original
semantic job and evidence in history.

It never edits Skills, scores semantic quality, promotes releases, or deploys
production. Python 3.8+ standard library only.
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
DEFAULT_SEMANTIC_JOBS_PATH = "custom/ba-agent/automation/semantic-jobs.json"
DEFAULT_SAME_MODEL_RETRIES = 1


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
        "User-Agent": "ba-agent-autonomy-controller/1.2",
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


def int_value(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return int(default)


def same_model_retry_limit(job):
    limit = int_value(job.get("same_model_retries", DEFAULT_SAME_MODEL_RETRIES), DEFAULT_SAME_MODEL_RETRIES)
    return max(0, min(limit, 3))


def same_model_retry_count(job):
    return max(0, int_value(job.get("same_model_retry_count", 0), 0))


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


def unique_id(base, suffix, existing_ids):
    candidate = base + "-" + suffix
    counter = 2
    while candidate in existing_ids:
        candidate = base + "-{}-{}".format(suffix, counter)
        counter += 1
    return candidate


def clone_for_same_model_retry(job, existing_ids):
    clone = dict(job)
    base = str(job.get("id") or "job")
    next_count = same_model_retry_count(job) + 1
    clone["id"] = unique_id(base, "retry-same-model-{}".format(next_count), existing_ids)
    clone["enabled"] = True
    clone["same_model_retry_count"] = next_count
    clone["autonomy_parent"] = base
    clone["autonomy_reason"] = "operational_same_model_retry"
    return clone


def clone_for_model(job, new_model, existing_ids):
    clone = dict(job)
    clone["model"] = new_model
    base = str(job.get("id") or "job")
    suffix = "auto-{}".format(slug(new_model))
    clone["id"] = unique_id(base, suffix, existing_ids)
    clone["enabled"] = True
    clone["same_model_retry_count"] = 0
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


def lineage_rewrite(old_job, new_job):
    return {
        "old_id": str(old_job.get("id") or ""),
        "new_id": str(new_job.get("id") or ""),
        "old_model": str(old_job.get("model") or ""),
        "new_model": str(new_job.get("model") or ""),
        "reason": str(new_job.get("autonomy_reason") or "operational_lineage"),
    }


def rewrite_result_path(value, rewrites):
    if not isinstance(value, str) or not value:
        return value, False
    updated = value
    changed = False
    for item in rewrites:
        old_prefix = "{}-{}".format(item["old_id"], slug(item["old_model"]))
        new_prefix = "{}-{}".format(item["new_id"], slug(item["new_model"]))
        if old_prefix and old_prefix in updated:
            updated = updated.replace(old_prefix, new_prefix)
            changed = True
    return updated, changed


def clone_semantic_followups(queue, rewrites):
    jobs = queue.get("jobs") or []
    if not isinstance(jobs, list):
        raise ControllerError("semantic-jobs.json must contain a jobs array")
    existing_ids = {str(job.get("id")) for job in jobs if isinstance(job, dict) and job.get("id")}
    additions = []
    for job in list(jobs):
        if not isinstance(job, dict) or not job.get("id") or not bool(job.get("enabled", True)):
            continue
        clone = dict(job)
        changed = False
        for field in ("baseline_result", "skill_result", "skill_metadata"):
            rewritten, field_changed = rewrite_result_path(clone.get(field), rewrites)
            if field_changed:
                clone[field] = rewritten
                changed = True
        if not changed:
            continue

        affected = []
        for item in rewrites:
            old_prefix = "{}-{}".format(item["old_id"], slug(item["old_model"]))
            for field in ("baseline_result", "skill_result", "skill_metadata"):
                original = str(job.get(field) or "")
                if old_prefix and old_prefix in original:
                    affected.append(item)
                    break
        new_models = {item["new_model"] for item in affected if item.get("new_model")}
        if len(new_models) == 1:
            new_model = next(iter(new_models))
            clone["generation_model"] = new_model
            if clone.get("rerun_model") is not None:
                clone["rerun_model"] = new_model
            if clone.get("generation_fallback_models") is not None:
                clone["generation_fallback_models"] = [new_model]

        base = str(job.get("id") or "semantic")
        model_tag = slug(next(iter(new_models))) if len(new_models) == 1 else "lineage"
        clone["id"] = unique_id(base, "auto-follow-{}".format(model_tag), existing_ids)
        existing_ids.add(clone["id"])
        clone["enabled"] = True
        clone["autonomy_parent"] = base
        clone["autonomy_reason"] = "execution_operational_lineage_follow"
        additions.append(clone)
    return additions


def publish_semantic_followups(repo, branch, semantic_path, token, rewrites):
    if not rewrites:
        return 0, None
    queue, sha = github_get_json_file(repo, branch, semantic_path, token)
    additions = clone_semantic_followups(queue, rewrites)
    if not additions:
        return 0, None
    queue["jobs"].extend(additions)
    commit = github_put_json_file(
        repo, branch, semantic_path, queue, sha, token,
        "automation: follow execution retry lineage in semantic queue",
    )
    return len(additions), commit


def main():
    parser = argparse.ArgumentParser(description="Advance deterministic BA lab operational state.")
    parser.add_argument("--repo", default=DEFAULT_REPO)
    parser.add_argument("--branch", default=DEFAULT_BRANCH)
    parser.add_argument("--root", default=DEFAULT_ROOT)
    parser.add_argument("--jobs-path", default=DEFAULT_JOBS_PATH)
    parser.add_argument("--semantic-jobs-path", default=DEFAULT_SEMANTIC_JOBS_PATH)
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
    rewrites = []

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

        retry_limit = same_model_retry_limit(job)
        retry_count = same_model_retry_count(job)
        if retry_count < retry_limit:
            members = choose_group(jobs, job)
            created = []
            for member in members:
                member_id = str(member.get("id") or "")
                if handled.get(member_id):
                    continue
                clone = clone_for_same_model_retry(member, existing_ids)
                existing_ids.add(clone["id"])
                additions.append(clone)
                rewrites.append(lineage_rewrite(member, clone))
                created.append(clone["id"])
                handled[member_id] = {
                    "at": dt.datetime.now(dt.timezone.utc).isoformat(),
                    "action": "same_model_retry_queued",
                    "reason": failure,
                    "model": str(member.get("model") or ""),
                    "job_id": clone["id"],
                    "retry_count": clone["same_model_retry_count"],
                }
            if created:
                print("[controller] {} -> {} same-model retry after {}".format(job_id, ", ".join(created), failure))
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
            rewrites.append(lineage_rewrite(member, clone))
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
            "automation: queue operational retry/fallback jobs",
        )
        print("[controller] queued {} operational job(s); commit={}".format(len(additions), commit or "unknown"))
        try:
            semantic_count, semantic_commit = publish_semantic_followups(
                args.repo, args.branch, args.semantic_jobs_path, token, rewrites,
            )
            if semantic_count:
                print("[controller] queued {} semantic lineage follow-up(s); commit={}".format(
                    semantic_count, semantic_commit or "unknown"
                ))
        except ControllerError as exc:
            print("[controller] WARNING semantic lineage follow-up failed: {}".format(exc))
    else:
        print("[controller] no deterministic transition required")

    state["schema"] = 3
    state["last_checked_at"] = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    write_json(controller_state_path, state)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ControllerError as exc:
        print("ERROR: {}".format(exc))
        raise SystemExit(2)
