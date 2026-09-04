#!/usr/bin/env python3
"""Run one-shot, GitHub-triggered NAS diagnostics using a constrained recipe engine.

Python 3.8+ standard library only. The repository can request a diagnostic by
updating diagnostic-request.json with a new request_id. The worker executes only
allowlisted read-only check types; it never executes shell commands supplied by
GitHub and never publishes secret values.
"""

import argparse
import base64
import datetime as dt
import json
import os
from pathlib import Path
import re
import socket
import sys
import urllib.error
import urllib.parse
import urllib.request

DEFAULT_REPO = "justinthenick/LibreChat"
DEFAULT_BRANCH = "feature/ba-agent-v0.1"
DEFAULT_ROOT = "/volume1/docker/librechat-ba-lab"
DEFAULT_ENV_FILE = "/volume1/docker/librechat/deploy/synology/.env"
DEFAULT_TOKEN_ENV = "GITHUB_TELEMETRY_TOKEN"
DEFAULT_REQUEST_PATH = "custom/ba-agent/automation/diagnostic-request.json"
DEFAULT_RESULTS_PREFIX = "custom/ba-agent/automation/diagnostic-results"
SAFE_ENV_NAMES = {
    "GEMINI_API_KEY",
    "GOOGLE_KEY",
    "GOOGLE_API_KEY",
    "GITHUB_TELEMETRY_TOKEN",
    "GITHUB_BA_BENCHMARK_TOKEN",
}
MAX_CHECKS = 20
MAX_TAIL_LINES = 200
MAX_TEXT = 20000


class DiagnosticError(RuntimeError):
    pass


def iso_now():
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_dotenv(path):
    values = {}
    if not path.exists():
        return values
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        values[key] = value
    return values


def merged_environment(env_file):
    values = load_dotenv(env_file)
    values.update(os.environ)
    return values


def sanitize_text(value):
    text = str(value)
    text = re.sub(r"AIza[0-9A-Za-z_-]{20,}", "[REDACTED_GOOGLE_KEY]", text)
    text = re.sub(r"(?:github_pat_|ghp_|gho_|ghu_|ghs_|ghr_)[0-9A-Za-z_]{20,}", "[REDACTED_GITHUB_TOKEN]", text)
    text = re.sub(
        r"(?im)^([A-Z0-9_]*(?:KEY|TOKEN|SECRET|PASSWORD)[A-Z0-9_]*\s*=\s*).+$",
        r"\1[REDACTED]",
        text,
    )
    if len(text) > MAX_TEXT:
        text = text[-MAX_TEXT:]
        text = "[TRUNCATED]\n" + text
    return text


def github_request(url, method="GET", token=None, payload=None, timeout=60):
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "ba-agent-diagnostic-worker/1.0",
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
        raise DiagnosticError("GitHub HTTP {}: {}".format(exc.code, sanitize_text(raw[:1000])))
    except urllib.error.URLError as exc:
        raise DiagnosticError("GitHub network error: {}".format(exc.reason))


def github_fetch_json(repo, branch, repo_path):
    encoded = urllib.parse.quote(repo_path.strip("/"), safe="/")
    ref = urllib.parse.quote(branch, safe="")
    url = "https://api.github.com/repos/{}/contents/{}?ref={}".format(repo, encoded, ref)
    _, data = github_request(url)
    if not isinstance(data, dict) or data.get("type") != "file" or data.get("encoding") != "base64":
        raise DiagnosticError("GitHub path is not a JSON file: {}".format(repo_path))
    try:
        text = base64.b64decode(data.get("content", "")).decode("utf-8")
        value = json.loads(text)
    except Exception as exc:
        raise DiagnosticError("Invalid JSON in {}: {}".format(repo_path, exc))
    if not isinstance(value, dict):
        raise DiagnosticError("Expected JSON object in {}".format(repo_path))
    return value


def github_put_text(repo, branch, repo_path, text, token, message):
    encoded = urllib.parse.quote(repo_path.strip("/"), safe="/")
    ref = urllib.parse.quote(branch, safe="")
    get_url = "https://api.github.com/repos/{}/contents/{}?ref={}".format(repo, encoded, ref)
    sha = None
    try:
        _, existing = github_request(get_url, token=token)
        if isinstance(existing, dict):
            sha = existing.get("sha")
    except DiagnosticError as exc:
        if "HTTP 404" not in str(exc):
            raise
    put_url = "https://api.github.com/repos/{}/contents/{}".format(repo, encoded)
    payload = {
        "message": message,
        "content": base64.b64encode(text.encode("utf-8")).decode("ascii"),
        "branch": branch,
    }
    if sha:
        payload["sha"] = sha
    _, result = github_request(put_url, method="PUT", token=token, payload=payload)
    commit = result.get("commit") if isinstance(result, dict) else None
    return commit.get("sha") if isinstance(commit, dict) else None


def read_json_file(path, default):
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else default
    except Exception:
        return default


def save_json_file(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temp.replace(path)


def is_allowed_path(path, root, env_file):
    resolved = path.resolve()
    allowed_roots = [
        (root / "custom/ba-agent").resolve(),
        Path("/tmp").resolve(),
    ]
    if resolved == env_file.resolve():
        return True
    for allowed in allowed_roots:
        try:
            resolved.relative_to(allowed)
            return True
        except ValueError:
            pass
    return False


def checked_path(raw, root, env_file):
    path = Path(str(raw or ""))
    if not path.is_absolute():
        path = (root / path).resolve()
    else:
        path = path.resolve()
    if not is_allowed_path(path, root, env_file):
        raise DiagnosticError("Path outside diagnostic allowlist: {}".format(path))
    return path


def process_matches(fragment):
    fragment = str(fragment or "").strip()
    if not re.fullmatch(r"[A-Za-z0-9_.-]{1,80}", fragment):
        raise DiagnosticError("Invalid process fragment")
    matches = []
    proc = Path("/proc")
    if not proc.exists():
        return matches
    for entry in proc.iterdir():
        if not entry.name.isdigit():
            continue
        try:
            cmdline = (entry / "cmdline").read_bytes().replace(b"\x00", b" ").decode("utf-8", errors="replace")
        except Exception:
            continue
        if fragment in cmdline and "diagnostic_worker.py" not in cmdline:
            matches.append({"pid": int(entry.name), "cmdline": sanitize_text(cmdline[:500])})
    return matches[:20]


def tail_text(path, lines):
    lines = max(1, min(int(lines), MAX_TAIL_LINES))
    try:
        content = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception as exc:
        raise DiagnosticError("Cannot read {}: {}".format(path, exc))
    return sanitize_text("\n".join(content[-lines:]))


def check_path_exists(check, root, env_file, repo, branch):
    path = checked_path(check.get("path"), root, env_file)
    result = {"path": str(path), "exists": path.exists()}
    if path.exists():
        try:
            stat = path.stat()
            result.update({"is_file": path.is_file(), "is_dir": path.is_dir(), "size": stat.st_size, "mtime_epoch": int(stat.st_mtime)})
        except Exception:
            pass
    return result


def check_tail(check, root, env_file, repo, branch):
    path = checked_path(check.get("path"), root, env_file)
    if path.resolve() == env_file.resolve():
        raise DiagnosticError("Reading .env content is forbidden")
    return {"path": str(path), "lines": min(int(check.get("lines", 100)), MAX_TAIL_LINES), "text": tail_text(path, check.get("lines", 100))}


def check_python_info(check, root, env_file, repo, branch):
    return {"executable": sys.executable, "version": sys.version.split()[0]}


def check_lock_status(check, root, env_file, repo, branch):
    path = checked_path(check.get("path"), root, env_file)
    fragment = check.get("process_contains") or "benchmark_worker.py"
    return {"lock_path": str(path), "lock_exists": path.exists(), "matching_processes": process_matches(fragment)}


def check_worker_state(check, root, env_file, repo, branch):
    path = checked_path(check.get("path"), root, env_file)
    value = read_json_file(path, {"jobs": {}})
    jobs = value.get("jobs") if isinstance(value.get("jobs"), dict) else {}
    requested = [str(x) for x in (check.get("job_ids") or [])][:50]
    selected = {}
    for job_id in requested:
        record = jobs.get(job_id)
        if isinstance(record, dict):
            clean = dict(record)
            if "output_tail" in clean:
                clean["output_tail"] = sanitize_text(clean["output_tail"])
            if "error" in clean:
                clean["error"] = sanitize_text(clean["error"])
            selected[job_id] = clean
        else:
            selected[job_id] = None
    return {"path": str(path), "known_job_count": len(jobs), "jobs": selected}


def check_queue_compare(check, root, env_file, repo, branch):
    state_path = checked_path(check.get("state_path"), root, env_file)
    jobs_path = str(check.get("jobs_path") or "custom/ba-agent/automation/jobs.json")
    queue = github_fetch_json(repo, branch, jobs_path)
    state = read_json_file(state_path, {"jobs": {}})
    known = state.get("jobs") if isinstance(state.get("jobs"), dict) else {}
    remote = queue.get("jobs") if isinstance(queue.get("jobs"), list) else []
    enabled = [j for j in remote if isinstance(j, dict) and j.get("enabled", True)]
    pending = [str(j.get("id")) for j in enabled if j.get("id") and str(j.get("id")) not in known]
    requested = [str(x) for x in (check.get("job_ids") or [])][:50]
    target = {}
    remote_ids = {str(j.get("id")) for j in enabled if j.get("id")}
    for job_id in requested:
        target[job_id] = {"remote_enabled": job_id in remote_ids, "known_locally": job_id in known, "pending": job_id in pending}
    return {"enabled_remote_jobs": len(enabled), "known_local_jobs": len(known), "pending_job_count": len(pending), "pending_job_ids": pending[:100], "targets": target}


def check_disk_usage(check, root, env_file, repo, branch):
    path = checked_path(check.get("path"), root, env_file)
    stat = os.statvfs(str(path))
    total = stat.f_blocks * stat.f_frsize
    free = stat.f_bavail * stat.f_frsize
    used = total - free
    return {"path": str(path), "total_bytes": total, "used_bytes": used, "free_bytes": free, "used_percent": round((used / total * 100.0) if total else 0.0, 2)}


def check_env_presence(check, root, env_file, repo, branch):
    path = checked_path(check.get("path") or str(env_file), root, env_file)
    if path.resolve() != env_file.resolve():
        raise DiagnosticError("env_presence may inspect only the configured .env path")
    names = [str(x) for x in (check.get("names") or [])]
    if any(name not in SAFE_ENV_NAMES for name in names):
        raise DiagnosticError("env_presence requested a non-allowlisted variable name")
    values = load_dotenv(path)
    return {"path": str(path), "present": {name: bool(values.get(name, "").strip()) for name in names}}


CHECKS = {
    "path_exists": check_path_exists,
    "tail": check_tail,
    "python_info": check_python_info,
    "lock_status": check_lock_status,
    "worker_state": check_worker_state,
    "queue_compare": check_queue_compare,
    "disk_usage": check_disk_usage,
    "env_presence": check_env_presence,
}


def execute_recipe(recipe, root, env_file, repo, branch):
    checks = recipe.get("checks")
    if not isinstance(checks, list):
        raise DiagnosticError("Diagnostic recipe must contain a checks array")
    if len(checks) > MAX_CHECKS:
        raise DiagnosticError("Diagnostic recipe exceeds {} checks".format(MAX_CHECKS))
    results = []
    for index, check in enumerate(checks, 1):
        if not isinstance(check, dict):
            results.append({"index": index, "status": "error", "error": "check must be an object"})
            continue
        check_type = str(check.get("type") or "").strip()
        label = str(check.get("label") or check_type or "check-{}".format(index))[:120]
        handler = CHECKS.get(check_type)
        if handler is None:
            results.append({"index": index, "label": label, "type": check_type, "status": "error", "error": "unsupported check type"})
            continue
        try:
            data = handler(check, root, env_file, repo, branch)
            results.append({"index": index, "label": label, "type": check_type, "status": "ok", "data": data})
        except Exception as exc:
            results.append({"index": index, "label": label, "type": check_type, "status": "error", "error": sanitize_text(exc)})
    overall = "ok" if all(item.get("status") == "ok" for item in results) else "partial"
    return overall, results


def main():
    parser = argparse.ArgumentParser(description="Run one GitHub-triggered constrained NAS diagnostic request.")
    parser.add_argument("--repo", default=DEFAULT_REPO)
    parser.add_argument("--branch", default=DEFAULT_BRANCH)
    parser.add_argument("--root", default=DEFAULT_ROOT)
    parser.add_argument("--env-file", default=DEFAULT_ENV_FILE)
    parser.add_argument("--github-token-env", default=DEFAULT_TOKEN_ENV)
    parser.add_argument("--request-path", default=DEFAULT_REQUEST_PATH)
    parser.add_argument("--results-prefix", default=DEFAULT_RESULTS_PREFIX)
    parser.add_argument("--state-file")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    env_file = Path(args.env_file).resolve()
    state_file = Path(args.state_file).resolve() if args.state_file else root / "custom/ba-agent/automation/diagnostic-state.json"
    local_dir = root / "custom/ba-agent/automation/diagnostic-local"
    local_dir.mkdir(parents=True, exist_ok=True)

    request = github_fetch_json(args.repo, args.branch, args.request_path)
    if not bool(request.get("enabled", False)):
        print("[diagnostic] no enabled request")
        return 0

    request_id = str(request.get("request_id") or "").strip()
    if not re.fullmatch(r"[A-Za-z0-9._-]{1,100}", request_id):
        raise DiagnosticError("Invalid diagnostic request_id")
    recipe_path = str(request.get("recipe") or "").strip()
    if not recipe_path.startswith("custom/ba-agent/diagnostics/") or not recipe_path.endswith(".json"):
        raise DiagnosticError("Diagnostic recipe path must be under custom/ba-agent/diagnostics/ and end in .json")

    state = read_json_file(state_file, {"schema": 1, "requests": {}})
    requests = state.get("requests")
    if not isinstance(requests, dict):
        requests = {}
        state["requests"] = requests

    previous = requests.get(request_id)
    local_path = local_dir / (request_id + ".json")
    env = merged_environment(env_file)
    token = str(env.get(args.github_token_env) or "").strip()

    if isinstance(previous, dict) and previous.get("published"):
        print("[diagnostic] request {} already published".format(request_id))
        return 0

    if isinstance(previous, dict) and local_path.exists():
        result_text = local_path.read_text(encoding="utf-8")
        result_path = str(previous.get("result_path") or "{}/{}.json".format(args.results_prefix.rstrip("/"), request_id))
        if not token:
            print("[diagnostic] request {} cached locally but {} is unavailable for publish".format(request_id, args.github_token_env))
            return 1
        commit = github_put_text(args.repo, args.branch, result_path, result_text, token, "Publish NAS diagnostic {}".format(request_id))
        previous["published"] = True
        previous["publish_commit"] = commit
        previous["published_at"] = iso_now()
        save_json_file(state_file, state)
        print("[diagnostic] published cached request {} -> {}".format(request_id, result_path))
        return 0

    recipe = github_fetch_json(args.repo, args.branch, recipe_path)
    started = iso_now()
    overall, check_results = execute_recipe(recipe, root, env_file, args.repo, args.branch)
    ended = iso_now()
    result = {
        "schema": 1,
        "request_id": request_id,
        "recipe": recipe_path,
        "recipe_name": str(recipe.get("name") or recipe_path),
        "hostname": socket.gethostname(),
        "started_at": started,
        "ended_at": ended,
        "overall": overall,
        "checks": check_results,
    }
    result_text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    local_path.write_text(result_text, encoding="utf-8")
    result_path = "{}/{}.json".format(args.results_prefix.rstrip("/"), request_id)
    record = {
        "recipe": recipe_path,
        "result_path": result_path,
        "attempted_at": ended,
        "published": False,
    }
    requests[request_id] = record
    save_json_file(state_file, state)

    if not token:
        print("[diagnostic] completed {} locally; {} unavailable for publish".format(request_id, args.github_token_env))
        return 1

    commit = github_put_text(args.repo, args.branch, result_path, result_text, token, "Publish NAS diagnostic {}".format(request_id))
    record["published"] = True
    record["publish_commit"] = commit
    record["published_at"] = iso_now()
    save_json_file(state_file, state)
    print("[diagnostic] completed {} overall={} and published {}".format(request_id, overall, result_path))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except DiagnosticError as exc:
        print("ERROR: {}".format(sanitize_text(exc)))
        raise SystemExit(2)
