#!/usr/bin/env python3
"""Shared standard-library helpers for NAS-side semantic lab workers."""

import base64
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import urllib.error
import urllib.parse
import urllib.request

API_BASE = "https://generativelanguage.googleapis.com/v1beta"
REPO = "justinthenick/LibreChat"
BRANCH = "feature/ba-agent-v0.1"
ROOT = "/volume1/docker/librechat-ba-lab"
ENV_FILE = "/volume1/docker/librechat/deploy/synology/.env"
GITHUB_TOKEN_ENV = "GITHUB_TELEMETRY_TOKEN"
KEY_ENV_CANDIDATES = ("GEMINI_API_KEY", "GOOGLE_KEY", "GOOGLE_API_KEY")
OPERATIONAL_FAILURES = ("provider_busy", "quota_blocked", "network_error")


class LabError(RuntimeError):
    pass


def now_z():
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def slug(value):
    return re.sub(r"[^a-z0-9]+", "-", str(value).lower()).strip("-") or "item"


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_env(path):
    values = {}
    p = Path(path)
    if not p.exists():
        raise LabError("Environment file not found: {}".format(p))
    for raw in p.read_text(encoding="utf-8", errors="replace").splitlines():
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
    values.update(os.environ)
    return values


def resolve_api_key(env):
    for name in KEY_ENV_CANDIDATES:
        value = env.get(name, "").strip()
        if value:
            return value
    raise LabError("No Gemini API key found")


def github_request(url, token, method="GET", payload=None, timeout=60):
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "ba-agent-semantic-lab/1.0",
        "X-GitHub-Api-Version": "2022-11-28",
        "Authorization": "Bearer {}".format(token),
    }
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
            return response.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise LabError("GitHub HTTP {}: {}".format(exc.code, body[:500]))
    except urllib.error.URLError as exc:
        raise LabError("GitHub network error: {}".format(exc.reason))


def contents_url(repo, branch, path):
    return "https://api.github.com/repos/{}/contents/{}?ref={}".format(
        repo,
        urllib.parse.quote(path.strip("/"), safe="/"),
        urllib.parse.quote(branch, safe=""),
    )


def get_text(repo, branch, path, token, missing_ok=False):
    try:
        _, data = github_request(contents_url(repo, branch, path), token)
    except LabError as exc:
        if missing_ok and "GitHub HTTP 404" in str(exc):
            return None, None
        raise
    if not isinstance(data, dict) or data.get("type") != "file" or data.get("encoding") != "base64":
        raise LabError("GitHub path is not a text file: {}".format(path))
    return base64.b64decode(data.get("content", "")).decode("utf-8"), data.get("sha")


def get_json(repo, branch, path, token, missing_ok=False):
    text, sha = get_text(repo, branch, path, token, missing_ok=missing_ok)
    if text is None:
        return None, None
    try:
        value = json.loads(text)
    except ValueError as exc:
        raise LabError("Invalid JSON in {}: {}".format(path, exc))
    if not isinstance(value, dict):
        raise LabError("Expected JSON object in {}".format(path))
    return value, sha


def put_text(repo, branch, path, text, token, message, sha=None):
    url = "https://api.github.com/repos/{}/contents/{}".format(repo, urllib.parse.quote(path.strip("/"), safe="/"))
    payload = {
        "message": message,
        "content": base64.b64encode(text.encode("utf-8")).decode("ascii"),
        "branch": branch,
    }
    if sha:
        payload["sha"] = sha
    _, result = github_request(url, token, method="PUT", payload=payload)
    commit = result.get("commit") if isinstance(result, dict) else None
    return commit.get("sha") if isinstance(commit, dict) else None


def put_json(repo, branch, path, value, token, message, sha=None):
    return put_text(repo, branch, path, json.dumps(value, indent=2, ensure_ascii=False) + "\n", token, message, sha=sha)


def read_local_json(path, default):
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else default
    except Exception:
        return default


def write_local_json(path, value):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(p)


def provider_error(raw, code):
    try:
        parsed = json.loads(raw)
        err = parsed.get("error") if isinstance(parsed, dict) else None
        if isinstance(err, dict):
            return str(err.get("message") or "HTTP {}".format(code))[:1000]
    except ValueError:
        pass
    return "HTTP {} provider request failed".format(code)


def gemini(api_key, model, prompt, system_instruction, max_tokens=8192, timeout=180, api_base=API_BASE):
    endpoint = "{}/models/{}:generateContent".format(api_base.rstrip("/"), urllib.parse.quote(model, safe="._-"))
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.0, "maxOutputTokens": int(max_tokens)},
        "system_instruction": {"parts": [{"text": system_instruction}]},
    }
    req = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/json", "x-goog-api-key": api_key, "User-Agent": "ba-agent-semantic-lab/1.0"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        status = "quota_blocked" if exc.code == 429 else "provider_busy" if exc.code == 503 else "provider_error"
        return {"status": status, "error": provider_error(raw, exc.code), "text": "", "usage": None}
    except urllib.error.URLError as exc:
        return {"status": "network_error", "error": str(exc.reason), "text": "", "usage": None}
    candidates = data.get("candidates") or []
    if not candidates:
        return {"status": "no_candidate", "error": "No candidate returned", "text": "", "usage": data.get("usageMetadata")}
    parts = ((candidates[0].get("content") or {}).get("parts") or [])
    text = "\n".join(p.get("text", "") for p in parts if isinstance(p, dict) and p.get("text")).strip()
    return {"status": "success" if text else "empty_output", "error": None if text else "Empty output", "text": text, "usage": data.get("usageMetadata")}


def parse_json_object(text):
    candidate = text.strip()
    candidate = re.sub(r"^```(?:json)?\s*", "", candidate, flags=re.I)
    candidate = re.sub(r"\s*```$", "", candidate)
    try:
        value = json.loads(candidate)
    except ValueError:
        start, end = candidate.find("{"), candidate.rfind("}")
        if start < 0 or end <= start:
            raise LabError("Model did not return a JSON object")
        value = json.loads(candidate[start:end + 1])
    if not isinstance(value, dict):
        raise LabError("Model response was not a JSON object")
    return value


def repo_relative(base_path, configured):
    parts = base_path.strip("/").split("/")
    for part in str(configured).replace("\\", "/").split("/"):
        if part in ("", "."):
            continue
        if part == "..":
            if not parts:
                raise LabError("Relative path escapes repository")
            parts.pop()
        else:
            parts.append(part)
    return "/".join(parts)
