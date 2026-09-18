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
import signal
import socket
import subprocess
import sys
import time
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
GITHUB_READ_TOKEN = None

# Additional fixed, read-only production diagnostics. These are intentionally
# exact files rather than directory roots so a GitHub recipe cannot browse the
# deployment tree or private .env.
SAFE_PRODUCTION_FILES = {
    Path("/volume1/docker/librechat-deploy.log"),
    Path("/volume1/docker/librechat-deploy-events.log"),
    Path("/volume1/docker/librechat-deploy.last-success"),
    Path("/volume1/docker/librechat/deploy/synology/librechat.yaml"),
}


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


def github_fetch_text(repo, branch, repo_path):
    encoded = urllib.parse.quote(repo_path.strip("/"), safe="/")
    ref = urllib.parse.quote(branch, safe="")
    url = "https://api.github.com/repos/{}/contents/{}?ref={}".format(repo, encoded, ref)
    _, data = github_request(url, token=GITHUB_READ_TOKEN)
    if not isinstance(data, dict) or data.get("type") != "file" or data.get("encoding") != "base64":
        raise DiagnosticError("GitHub path is not a file: {}".format(repo_path))
    try:
        return base64.b64decode(data.get("content", "")).decode("utf-8")
    except Exception as exc:
        raise DiagnosticError("Invalid text file {}: {}".format(repo_path, exc))


def github_fetch_json(repo, branch, repo_path):
    text = github_fetch_text(repo, branch, repo_path)
    try:
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
    if resolved in {p.resolve() for p in SAFE_PRODUCTION_FILES}:
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


def check_skill_sync_status(check, root, env_file, repo, branch):
    """Read only the managed-skills SkillSyncStatus document from local MongoDB."""
    source_id = str(check.get("source_id") or "managed-skills").strip()
    if source_id != "managed-skills":
        raise DiagnosticError("skill_sync_status supports only source_id managed-skills")

    projection = {
        "_id": 0,
        "provider": 1,
        "sourceId": 1,
        "status": 1,
        "credentialKey": 1,
        "owner": 1,
        "repo": 1,
        "ref": 1,
        "paths": 1,
        "startedAt": 1,
        "finishedAt": 1,
        "lastSuccessAt": 1,
        "lastFailureAt": 1,
        "errorCode": 1,
        "errorMessage": 1,
        "syncedSkillCount": 1,
        "syncedFileCount": 1,
        "deletedSkillCount": 1,
        "deletedFileCount": 1,
        "skippedSkillCount": 1,
        "skippedFileCount": 1,
        "updatedAt": 1,
    }
    script = (
        "var d=db.skillsyncstatuses.findOne("
        + json.dumps({"provider": "github", "sourceId": source_id})
        + ","
        + json.dumps(projection)
        + "); print(d ? JSON.stringify(d) : 'null');"
    )
    try:
        proc = subprocess.run(
            ["docker", "exec", "librechat-mongodb", "mongo", "LibreChat", "--quiet", "--eval", script],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=20,
            check=False,
        )
    except Exception as exc:
        raise DiagnosticError("Skill sync status query failed to start: {}".format(exc))
    if proc.returncode != 0:
        raise DiagnosticError(
            "Skill sync status query failed rc={}: {}".format(
                proc.returncode, sanitize_text(proc.stderr or proc.stdout)
            )
        )
    output = (proc.stdout or "").strip()
    if not output:
        return {"source_id": source_id, "document": None}
    try:
        value = json.loads(output.splitlines()[-1])
    except Exception:
        raise DiagnosticError("Skill sync status returned non-JSON output: {}".format(sanitize_text(output)))
    return {"source_id": source_id, "document": value}


def check_clear_failed_autodeploy(check, root, env_file, repo, branch):
    """Clear only a failed git_update autodeploy stuck in telemetry publication."""
    event_log = Path("/volume1/docker/librechat-deploy-events.log")
    lock_dir = Path("/tmp/librechat-autodeploy.lock")
    try:
        events = event_log.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        raise DiagnosticError("Cannot read deployment event log: {}".format(exc))

    recent = "\n".join(events.splitlines()[-20:])
    if "ERROR: Git fast-forward update failed" not in recent:
        raise DiagnosticError("Refusing cleanup: no recent git_update failure is recorded")

    try:
        with urllib.request.urlopen("http://127.0.0.1:3200/api/config", timeout=5) as response:
            if response.status < 200 or response.status >= 500:
                raise DiagnosticError("Refusing cleanup: LibreChat HTTP health is not acceptable")
    except DiagnosticError:
        raise
    except Exception as exc:
        raise DiagnosticError("Refusing cleanup: LibreChat HTTP health check failed: {}".format(exc))

    proc_rows = []
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        try:
            cmdline = (entry / "cmdline").read_bytes().replace(b"\x00", b" ").decode(
                "utf-8", errors="replace"
            ).strip()
        except Exception:
            continue
        if not cmdline:
            continue
        pid = int(entry.name)
        kind = None
        if cmdline == "sh /volume1/docker/librechat/deploy/synology/autodeploy.sh":
            kind = "autodeploy"
        elif ("publish-telemetry.sh failure git_update" in cmdline
              and "/volume1/docker/librechat/deploy/synology/" in cmdline):
            kind = "telemetry"
        elif ("docker run --rm" in cmdline and "curlimages/curl:8.10.1" in cmdline
              and "telemetry/history/" in cmdline and "-failure.json" in cmdline):
            kind = "telemetry-docker"
        if kind:
            proc_rows.append({"pid": pid, "kind": kind, "cmdline": sanitize_text(cmdline[:700])})

    auto = [row for row in proc_rows if row["kind"] == "autodeploy"]
    telem = [row for row in proc_rows if row["kind"] in {"telemetry", "telemetry-docker"}]
    if len(auto) != 1 or not telem:
        raise DiagnosticError(
            "Refusing cleanup: expected one failed autodeploy and active telemetry child"
        )

    ordered = sorted(telem, key=lambda row: 0 if row["kind"] == "telemetry-docker" else 1) + auto
    terminated = []
    for row in ordered:
        try:
            os.kill(row["pid"], signal.SIGTERM)
            terminated.append({"pid": row["pid"], "kind": row["kind"], "signal": "TERM"})
        except ProcessLookupError:
            pass

    time.sleep(3)

    for row in ordered:
        proc_path = Path("/proc") / str(row["pid"])
        if proc_path.exists():
            try:
                os.kill(row["pid"], signal.SIGKILL)
                terminated.append({"pid": row["pid"], "kind": row["kind"], "signal": "KILL"})
            except ProcessLookupError:
                pass

    time.sleep(1)
    remaining_auto = process_matches("autodeploy.sh")
    if remaining_auto:
        raise DiagnosticError(
            "Failed autodeploy process remains after bounded termination: {}".format(
                sanitize_text(remaining_auto)
            )
        )

    if lock_dir.exists():
        try:
            for child in lock_dir.iterdir():
                if child.is_file() or child.is_symlink():
                    child.unlink()
            lock_dir.rmdir()
        except Exception as exc:
            raise DiagnosticError("Failed to remove stale autodeploy lock: {}".format(exc))

    return {
        "cleared": True,
        "terminated": terminated,
        "lock_exists_after": lock_dir.exists(),
        "http_health": "pass",
    }


def check_restore_librechat_yaml_from_last_success(check, root, env_file, repo, branch):
    """Restore one tracked config file from the last successful deployment SHA."""
    deploy_lock = Path("/tmp/librechat-autodeploy.lock")
    if deploy_lock.exists():
        raise DiagnosticError("Refusing config restore while autodeploy lock exists")

    state_file = Path("/volume1/docker/librechat-deploy.last-success")
    target = Path("/volume1/docker/librechat/deploy/synology/librechat.yaml")
    tracked = "deploy/synology/librechat.yaml"

    try:
        last_success = state_file.read_text(encoding="utf-8").strip()
    except Exception as exc:
        raise DiagnosticError("Cannot read last successful deployment SHA: {}".format(exc))
    if not re.fullmatch(r"[0-9a-f]{40}", last_success):
        raise DiagnosticError("Invalid last successful deployment SHA")

    restored = github_fetch_text(repo, last_success, tracked)
    try:
        before = target.read_text(encoding="utf-8", errors="replace")
    except Exception:
        before = None

    temp = target.with_name(target.name + ".diag-restore.tmp")
    temp.write_text(restored, encoding="utf-8")
    temp.replace(target)

    return {
        "path": str(target),
        "restored_from": last_success,
        "changed": before != restored,
        "bytes": len(restored.encode("utf-8")),
    }


def check_repair_skill_sync_checkout(check, root, env_file, repo, branch):
    """Restore only deploy/synology/librechat.yaml in the live checkout.

    This is intentionally not a generic git/shell primitive. It operates on one
    fixed repository path and one fixed tracked file so GitHub-triggered
    diagnostics can recover the known post-promotion local-config conflict.
    """
    repo_dir = Path("/volume1/docker/librechat")
    tracked = "deploy/synology/librechat.yaml"

    def git_run(args, timeout=180):
        cmd = [
            "docker", "run", "--rm", "--user", "1026:100",
            "-v", "{}:/repo".format(repo_dir),
            "alpine/git:latest", "-C", "/repo"
        ] + list(args)
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
            check=False,
        )
        if proc.returncode != 0:
            raise DiagnosticError(
                "Bounded git operation failed rc={}: {}".format(
                    proc.returncode, sanitize_text(proc.stderr or proc.stdout)
                )
            )
        return (proc.stdout or "").strip()

    current_branch = git_run(["rev-parse", "--abbrev-ref", "HEAD"])
    if current_branch != "server/synology":
        raise DiagnosticError(
            "Refusing checkout repair: live repository branch is {}".format(current_branch)
        )

    before = git_run(["status", "--porcelain", "--", tracked])
    if not before:
        return {
            "branch": current_branch,
            "path": tracked,
            "changed": False,
            "before": "",
            "after": "",
        }

    lines = [line for line in before.splitlines() if line.strip()]
    if any(not line.endswith(tracked) for line in lines):
        raise DiagnosticError("Refusing checkout repair: unexpected path in scoped status")

    git_run(["checkout", "--", tracked])
    after = git_run(["status", "--porcelain", "--", tracked])
    if after:
        raise DiagnosticError(
            "Scoped checkout repair did not clean {}: {}".format(tracked, sanitize_text(after))
        )

    return {
        "branch": current_branch,
        "path": tracked,
        "changed": True,
        "before": sanitize_text(before),
        "after": after,
    }


def check_skill_inventory(check, root, env_file, repo, branch):
    script = (
        "var rows=db.skills.find({},"
        + json.dumps({
            "_id": 1,
            "name": 1,
            "description": 1,
            "source": 1,
            "sourceMetadata": 1,
            "version": 1,
            "tenantId": 1,
            "author": 1,
            "createdAt": 1,
            "updatedAt": 1,
        })
        + ").sort({name:1}).toArray(); print(JSON.stringify(rows));"
    )
    commands = [
        ["docker", "exec", "librechat-mongodb", "mongosh", "LibreChat", "--quiet", "--eval", script],
        ["docker", "exec", "librechat-mongodb", "mongo", "LibreChat", "--quiet", "--eval", script],
    ]
    errors = []
    for cmd in commands:
        try:
            proc = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=30,
                check=False,
            )
        except Exception as exc:
            errors.append(str(exc))
            continue
        if proc.returncode != 0:
            errors.append(sanitize_text(proc.stderr or proc.stdout))
            continue
        output = (proc.stdout or "").strip()
        try:
            rows = json.loads(output.splitlines()[-1]) if output else []
        except Exception:
            raise DiagnosticError("Skill inventory returned non-JSON output: {}".format(sanitize_text(output)))
        return {"count": len(rows), "skills": rows}
    raise DiagnosticError("Skill inventory query failed: {}".format(" | ".join(errors)))


def check_inline_skill_export(check, root, env_file, repo, branch):
    names = check.get("names") or []
    if not isinstance(names, list) or not names or len(names) > 20:
        raise DiagnosticError("inline skill export requires 1-20 names")
    cleaned = []
    for name in names:
        value = str(name or "").strip()
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,63}", value):
            raise DiagnosticError("Invalid skill name")
        cleaned.append(value)
    script = (
        "var rows=db.skills.find({source:'inline',name:{$in:"
        + json.dumps(cleaned)
        + "}},"
        + json.dumps({
            "_id": 0,
            "name": 1,
            "displayTitle": 1,
            "description": 1,
            "body": 1,
            "frontmatter": 1,
            "disableModelInvocation": 1,
            "userInvocable": 1,
            "allowedTools": 1,
            "category": 1,
            "alwaysApply": 1,
            "version": 1,
            "fileCount": 1,
            "createdAt": 1,
            "updatedAt": 1,
        })
        + ").sort({name:1}).toArray(); print(JSON.stringify(rows));"
    )
    commands = [
        ["docker", "exec", "librechat-mongodb", "mongosh", "LibreChat", "--quiet", "--eval", script],
        ["docker", "exec", "librechat-mongodb", "mongo", "LibreChat", "--quiet", "--eval", script],
    ]
    errors = []
    for cmd in commands:
        try:
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=30, check=False)
        except Exception as exc:
            errors.append(str(exc))
            continue
        if proc.returncode != 0:
            errors.append(sanitize_text(proc.stderr or proc.stdout))
            continue
        output = (proc.stdout or "").strip()
        try:
            rows = json.loads(output.splitlines()[-1]) if output else []
        except Exception:
            raise DiagnosticError("Inline skill export returned non-JSON output: {}".format(sanitize_text(output)))
        return {"count": len(rows), "skills": rows}
    raise DiagnosticError("Inline skill export query failed: {}".format(" | ".join(errors)))


def check_inline_skill_files(check, root, env_file, repo, branch):
    names = check.get("names") or []
    if not isinstance(names, list) or not names or len(names) > 20:
        raise DiagnosticError("inline skill file export requires 1-20 names")
    cleaned = []
    for name in names:
        value = str(name or "").strip()
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,63}", value):
            raise DiagnosticError("Invalid skill name")
        cleaned.append(value)
    script = (
        "var skills=db.skills.find({source:'inline',name:{$in:"
        + json.dumps(cleaned)
        + "}},{_id:1,name:1}).toArray();"
        "var map={}; skills.forEach(function(s){map[String(s._id)]=s.name;});"
        "var ids=skills.map(function(s){return s._id;});"
        "var rows=db.skillfiles.find({skillId:{$in:ids}},"
        + json.dumps({
            "_id": 0,
            "skillId": 1,
            "relativePath": 1,
            "file_id": 1,
            "filename": 1,
            "filepath": 1,
            "storageKey": 1,
            "storageRegion": 1,
            "source": 1,
            "mimeType": 1,
            "bytes": 1,
            "category": 1,
            "isExecutable": 1,
            "content": 1,
            "isBinary": 1,
            "createdAt": 1,
            "updatedAt": 1
        })
        + ").sort({skillId:1,relativePath:1}).toArray();"
        "rows=rows.map(function(r){r.skillName=map[String(r.skillId)]||null; delete r.skillId; return r;});"
        "print(JSON.stringify(rows));"
    )
    commands = [
        ["docker", "exec", "librechat-mongodb", "mongosh", "LibreChat", "--quiet", "--eval", script],
        ["docker", "exec", "librechat-mongodb", "mongo", "LibreChat", "--quiet", "--eval", script],
    ]
    errors = []
    for cmd in commands:
        try:
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=30, check=False)
        except Exception as exc:
            errors.append(str(exc))
            continue
        if proc.returncode != 0:
            errors.append(sanitize_text(proc.stderr or proc.stdout))
            continue
        output = (proc.stdout or "").strip()
        try:
            rows = json.loads(output.splitlines()[-1]) if output else []
        except Exception:
            raise DiagnosticError("Inline skill files query returned non-JSON output: {}".format(sanitize_text(output)))
        return {"count": len(rows), "files": rows}
    raise DiagnosticError("Inline skill files query failed: {}".format(" | ".join(errors)))


def check_inline_skill_file_content(check, root, env_file, repo, branch):
    requests = check.get("files") or []
    if not isinstance(requests, list) or not requests or len(requests) > 20:
        raise DiagnosticError("inline skill file content requires 1-20 files")
    cleaned = []
    for item in requests:
        if not isinstance(item, dict):
            raise DiagnosticError("file request must be an object")
        name = str(item.get("skill") or "").strip()
        rel = str(item.get("path") or "").strip()
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,63}", name):
            raise DiagnosticError("Invalid skill name")
        if not rel or rel.startswith("/") or ".." in rel.split("/") or not re.fullmatch(r"[A-Za-z0-9._/-]+", rel):
            raise DiagnosticError("Invalid relative path")
        cleaned.append({"skill": name, "path": rel})
    script = (
        "var reqs=" + json.dumps(cleaned) + "; var out=[];"
        "reqs.forEach(function(q){"
        "var s=db.skills.findOne({source:'inline',name:q.skill},{_id:1,name:1});"
        "if(!s){out.push({skill:q.skill,path:q.path,error:'skill not found'});return;}"
        "var f=db.skillfiles.findOne({skillId:s._id,relativePath:q.path},"
        "{_id:0,relativePath:1,filename:1,filepath:1,mimeType:1,bytes:1,content:1,isBinary:1});"
        "if(!f){out.push({skill:q.skill,path:q.path,error:'file not found'});return;}"
        "f.skill=q.skill; out.push(f);"
        "}); print(JSON.stringify(out));"
    )
    commands = [
        ["docker", "exec", "librechat-mongodb", "mongosh", "LibreChat", "--quiet", "--eval", script],
        ["docker", "exec", "librechat-mongodb", "mongo", "LibreChat", "--quiet", "--eval", script],
    ]
    rows = None
    errors = []
    for cmd in commands:
        try:
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=30, check=False)
        except Exception as exc:
            errors.append(str(exc)); continue
        if proc.returncode != 0:
            errors.append(sanitize_text(proc.stderr or proc.stdout)); continue
        output = (proc.stdout or "").strip()
        try:
            rows = json.loads(output.splitlines()[-1]) if output else []
        except Exception:
            raise DiagnosticError("Inline skill file metadata returned non-JSON output")
        break
    if rows is None:
        raise DiagnosticError("Inline skill file metadata query failed: {}".format(" | ".join(errors)))
    results = []
    for row in rows:
        if row.get("error"):
            results.append(row); continue
        if row.get("isBinary") is True:
            results.append({"skill": row.get("skill"), "path": row.get("relativePath"), "error": "binary file"}); continue
        size = int(row.get("bytes") or 0)
        if size > 200000:
            results.append({"skill": row.get("skill"), "path": row.get("relativePath"), "error": "file too large"}); continue
        content = row.get("content")
        if not isinstance(content, str):
            filepath = str(row.get("filepath") or "")
            if not filepath.startswith("/uploads/") or ".." in filepath.split("/"):
                results.append({"skill": row.get("skill"), "path": row.get("relativePath"), "error": "unsafe filepath"}); continue
            candidates = [filepath, "/app" + filepath]
            proc = None
            last_error = ""
            for candidate in candidates:
                proc = subprocess.run(
                    ["docker", "exec", "librechat", "cat", candidate],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20, check=False
                )
                if proc.returncode == 0:
                    break
                last_error = sanitize_text(proc.stderr.decode("utf-8","replace"))
            if proc is None or proc.returncode != 0:
                results.append({"skill": row.get("skill"), "path": row.get("relativePath"), "error": last_error}); continue
            try:
                content = proc.stdout.decode("utf-8")
            except Exception:
                results.append({"skill": row.get("skill"), "path": row.get("relativePath"), "error": "not utf-8"}); continue
        results.append({
            "skill": row.get("skill"),
            "path": row.get("relativePath"),
            "filename": row.get("filename"),
            "mimeType": row.get("mimeType"),
            "bytes": size,
            "content": content,
        })
    return {"count": len(results), "files": results}


def check_skill_reference_audit(check, root, env_file, repo, branch):
    names = check.get("names") or []
    if not isinstance(names, list) or not names or len(names) > 20:
        raise DiagnosticError("skill reference audit requires 1-20 names")
    cleaned = []
    for name in names:
        value = str(name or "").strip()
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,63}", value):
            raise DiagnosticError("Invalid skill name")
        cleaned.append(value)
    script = (
        "var skills=db.skills.find({name:{$in:" + json.dumps(cleaned) + "}},"
        "{_id:1,name:1,source:1,sourceMetadata:1}).toArray();"
        "var ids=skills.map(function(s){return String(s._id);});"
        "var agents=db.agents.find({skills:{$in:ids}},"
        "{_id:1,name:1,skills:1,skills_enabled:1}).toArray();"
        "print(JSON.stringify({skills:skills,agents:agents}));"
    )
    commands = [
        ["docker", "exec", "librechat-mongodb", "mongosh", "LibreChat", "--quiet", "--eval", script],
        ["docker", "exec", "librechat-mongodb", "mongo", "LibreChat", "--quiet", "--eval", script],
    ]
    errors = []
    for cmd in commands:
        try:
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=30, check=False)
        except Exception as exc:
            errors.append(str(exc)); continue
        if proc.returncode != 0:
            errors.append(sanitize_text(proc.stderr or proc.stdout)); continue
        output=(proc.stdout or "").strip()
        try:
            value=json.loads(output.splitlines()[-1]) if output else {"skills":[],"agents":[]}
        except Exception:
            raise DiagnosticError("Skill reference audit returned non-JSON output")
        return value
    raise DiagnosticError("Skill reference audit failed: {}".format(" | ".join(errors)))


def check_finalize_inline_skill_cleanup(check, root, env_file, repo, branch):
    approved = {
        "analyze-requirements",
        "decompose-requirements",
        "frontend-design",
        "improve-codebase-architecture",
        "technical-writer",
    }
    names = check.get("names") or []
    cleaned = [str(x or "").strip() for x in names]
    if set(cleaned) != approved or len(cleaned) != len(approved):
        raise DiagnosticError("Cleanup scope must exactly match the audited five-skill baseline")
    expected_commit = str(check.get("expected_commit") or "").strip()
    if expected_commit != "c521ee2eb4b34abadf7d81a2fec1e1a6acee0c51":
        raise DiagnosticError("Unexpected baseline commit")
    script = (
        "var names=" + json.dumps(cleaned) + ";"
        "var skills=db.skills.find({name:{$in:names}},"
        "{_id:1,name:1,source:1,description:1,sourceMetadata:1}).toArray();"
        "var oldIds=skills.filter(function(s){return s.source==='inline';}).map(function(s){return String(s._id);});"
        "var agents=db.agents.find({skills:{$in:oldIds}},{_id:1,name:1,skills:1}).toArray();"
        "print(JSON.stringify({skills:skills,agents:agents}));"
    )
    commands = [
        ["docker", "exec", "librechat-mongodb", "mongosh", "LibreChat", "--quiet", "--eval", script],
        ["docker", "exec", "librechat-mongodb", "mongo", "LibreChat", "--quiet", "--eval", script],
    ]
    snapshot = None
    errors = []
    for cmd in commands:
        try:
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=30, check=False)
        except Exception as exc:
            errors.append(str(exc)); continue
        if proc.returncode != 0:
            errors.append(sanitize_text(proc.stderr or proc.stdout)); continue
        output=(proc.stdout or "").strip()
        try:
            snapshot=json.loads(output.splitlines()[-1])
        except Exception:
            raise DiagnosticError("Cleanup preflight returned non-JSON output")
        break
    if snapshot is None:
        raise DiagnosticError("Cleanup preflight failed: {}".format(" | ".join(errors)))
    if snapshot.get("agents"):
        raise DiagnosticError("Inline skill ids are still referenced by agents")
    rows = snapshot.get("skills") or []
    inline_by = {}
    github_by = {}
    for row in rows:
        name = row.get("name")
        if row.get("source") == "inline":
            inline_by.setdefault(name, []).append(row)
        elif row.get("source") == "github":
            meta = row.get("sourceMetadata") or {}
            if meta.get("sourceId") == "managed-skills" and meta.get("commitSha") == expected_commit:
                github_by.setdefault(name, []).append(row)
    for name in sorted(approved):
        if len(inline_by.get(name, [])) != 1:
            raise DiagnosticError("Expected exactly one inline row for {}".format(name))
        if len(github_by.get(name, [])) != 1:
            raise DiagnosticError("Expected exactly one audited GitHub row for {}".format(name))
        if inline_by[name][0].get("description") != github_by[name][0].get("description"):
            raise DiagnosticError("Description mismatch for {}".format(name))
    ids = [inline_by[name][0]["_id"]["$oid"] for name in sorted(approved)]
    node_script = r"""
const path = require("path");
require("module-alias")({ base: path.resolve("/app/api") });
const connect = require("/app/config/connect");
(async () => {
  await connect();
  require("~/db/models");
  const db = require("~/models");
  const ids = JSON.parse(process.env.SKILL_IDS_JSON || "[]");
  const results = [];
  for (const id of ids) {
    results.push({ id, ...(await db.deleteSkill(id)) });
  }
  console.log(JSON.stringify(results));
  await require("mongoose").disconnect();
})().catch((err) => { console.error(err); process.exit(1); });
"""
    env = dict(os.environ)
    env["SKILL_IDS_JSON"] = json.dumps(ids)
    proc = subprocess.run(
        ["docker", "exec", "-e", "SKILL_IDS_JSON=" + json.dumps(ids), "librechat", "node", "-e", node_script],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=60, check=False
    )
    if proc.returncode != 0:
        raise DiagnosticError("Cleanup delete failed rc={}: {}".format(proc.returncode, sanitize_text(proc.stderr or proc.stdout)))
    output = (proc.stdout or "").strip()
    result_line = output.splitlines()[-1] if output else "[]"
    try:
        results = json.loads(result_line)
    except Exception:
        raise DiagnosticError("Cleanup delete returned non-JSON output: {}".format(sanitize_text(output)))
    if len(results) != len(ids) or not all(item.get("deleted") is True for item in results):
        raise DiagnosticError("One or more inline skill deletions did not complete")
    return {"deleted": len(results), "ids": ids, "results": results}


CHECKS = {
    "path_exists": check_path_exists,
    "tail": check_tail,
    "python_info": check_python_info,
    "lock_status": check_lock_status,
    "worker_state": check_worker_state,
    "queue_compare": check_queue_compare,
    "disk_usage": check_disk_usage,
    "env_presence": check_env_presence,
    "skill_sync_status": check_skill_sync_status,
    "skill_inventory": check_skill_inventory,
    "inline_skill_export": check_inline_skill_export,
    "inline_skill_files": check_inline_skill_files,
    "inline_skill_file_content": check_inline_skill_file_content,
    "skill_reference_audit": check_skill_reference_audit,
    "finalize_inline_skill_cleanup": check_finalize_inline_skill_cleanup,
    "repair_skill_sync_checkout": check_repair_skill_sync_checkout,
    "restore_librechat_yaml_from_last_success": check_restore_librechat_yaml_from_last_success,
    "clear_failed_autodeploy": check_clear_failed_autodeploy,
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
    global GITHUB_READ_TOKEN

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

    env = merged_environment(env_file)
    token = str(env.get(args.github_token_env) or "").strip()
    GITHUB_READ_TOKEN = token or None

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
