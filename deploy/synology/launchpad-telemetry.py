#!/usr/bin/env python3
"""Emit a sanitised LibreChat launchpad snapshot for GitHub telemetry.

This script is read-only. It reports only:
- production checkout branch/commit/cleanliness
- managed Skill Sync status/counts
- managed GitHub skill names/versions
- LibreChat-container -> coding-executor health
- LibreChat-container -> coding-maintenance connectivity

It never emits credential values, executor/maintenance hostnames/IPs, raw logs,
or arbitrary MongoDB documents.
"""

import json
import re
import subprocess
import sys

REPO_DIR = "/volume1/docker/librechat"


def run(cmd, timeout=30):
    proc = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=timeout,
        check=False,
    )
    return proc.returncode, (proc.stdout or "").strip(), (proc.stderr or "").strip()


def safe_error(code, fallback):
    text = str(fallback or "")
    text = re.sub(r"(?:github_pat_|ghp_|gho_|ghu_|ghs_|ghr_)[0-9A-Za-z_]{20,}", "[REDACTED]", text)
    text = re.sub(r"AIza[0-9A-Za-z_-]{20,}", "[REDACTED]", text)
    text = re.sub(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", "[REDACTED_ADDRESS]", text)
    text = re.sub(r"(?i)(token|secret|password|key)=[^\s]+", r"\1=[REDACTED]", text)
    return {"ok": False, "error_code": code, "detail": text[:240] if text else code}


def git_value(args):
    cmd = [
        "docker", "run", "--rm", "--user", "1026:100",
        "-v", REPO_DIR + ":/repo", "alpine/git:latest", "-C", "/repo",
    ] + args
    rc, out, err = run(cmd, timeout=45)
    if rc != 0:
        raise RuntimeError(err or out or "git command failed")
    return out


def mongo_json(script):
    commands = [
        ["docker", "exec", "librechat-mongodb", "mongosh", "LibreChat", "--quiet", "--eval", script],
        ["docker", "exec", "librechat-mongodb", "mongo", "LibreChat", "--quiet", "--eval", script],
    ]
    errors = []
    for cmd in commands:
        rc, out, err = run(cmd)
        if rc != 0:
            errors.append(err or out or "mongo shell failed")
            continue
        line = out.splitlines()[-1] if out else ""
        try:
            return json.loads(line) if line else None
        except Exception as exc:
            errors.append("non-json mongo output: {}".format(exc))
    raise RuntimeError(" | ".join(errors))


def checkout_snapshot():
    """Read branch/commit directly from .git without starting another Git container.

    Synology can take tens of seconds to start the alpine/git bind-mounted probe.
    Deployment correctness is already enforced by autodeploy.sh, so telemetry
    reports the exact checked-out ref cheaply and leaves worktree cleanliness as
    an explicit/manual diagnostic rather than turning a timeout into a false
    launchpad failure.
    """
    try:
        git_dir = REPO_DIR + "/.git"
        with open(git_dir + "/HEAD", "r", encoding="utf-8") as handle:
            head = handle.read().strip()

        branch = None
        commit = None
        if head.startswith("ref: "):
            ref = head[5:].strip()
            prefix = "refs/heads/"
            branch = ref[len(prefix):] if ref.startswith(prefix) else ref
            ref_path = git_dir + "/" + ref
            try:
                with open(ref_path, "r", encoding="utf-8") as handle:
                    commit = handle.read().strip()
            except FileNotFoundError:
                with open(git_dir + "/packed-refs", "r", encoding="utf-8") as handle:
                    for raw in handle:
                        line = raw.strip()
                        if not line or line.startswith("#") or line.startswith("^"):
                            continue
                        sha, name = line.split(" ", 1)
                        if name == ref:
                            commit = sha
                            break
        else:
            commit = head

        if not commit:
            raise RuntimeError("could not resolve HEAD commit")

        return {
            "ok": True,
            "branch": branch,
            "commit": commit,
            "cleanliness": "not_polled",
        }
    except Exception as exc:
        return safe_error("checkout_probe_failed", exc)


def skill_sync_snapshot():
    script = (
        "var d=db.skillsyncstatuses.findOne("
        "{provider:'github',sourceId:'managed-skills'},"
        "{_id:0,provider:1,sourceId:1,status:1,ref:1,lastSuccessAt:1,"
        "errorCode:1,syncedSkillCount:1,syncedFileCount:1,"
        "deletedSkillCount:1,deletedFileCount:1,skippedSkillCount:1,skippedFileCount:1});"
        "print(d?JSON.stringify(d):'null');"
    )
    try:
        doc = mongo_json(script)
        if doc is None:
            return {"ok": False, "found": False, "error_code": "skill_sync_not_found"}
        allowed = {
            "provider", "sourceId", "status", "ref", "lastSuccessAt", "errorCode",
            "syncedSkillCount", "syncedFileCount", "deletedSkillCount",
            "deletedFileCount", "skippedSkillCount", "skippedFileCount",
        }
        clean = {k: doc.get(k) for k in allowed if k in doc}
        clean.update({"ok": True, "found": True})
        return clean
    except Exception as exc:
        return safe_error("skill_sync_probe_failed", exc)


def managed_skills_snapshot():
    script = (
        "var rows=db.skills.find({source:'github','sourceMetadata.sourceId':'managed-skills'},"
        "{_id:0,name:1,version:1,'sourceMetadata.ref':1,'sourceMetadata.commitSha':1})"
        ".sort({name:1}).toArray(); print(JSON.stringify(rows));"
    )
    try:
        rows = mongo_json(script) or []
        skills = []
        for row in rows:
            skills.append({
                "name": row.get("name"),
                "version": row.get("version"),
                "ref": (row.get("sourceMetadata") or {}).get("ref"),
                "commit": (row.get("sourceMetadata") or {}).get("commitSha"),
            })
        return {
            "ok": True,
            "count": len(skills),
            "names": [item.get("name") for item in skills],
            "skills": skills,
        }
    except Exception as exc:
        return safe_error("managed_skill_probe_failed", exc)


def executor_snapshot():
    js = r"""
const host = process.env.CODING_EXECUTOR_HOST || "";
const port = process.env.CODING_EXECUTOR_PORT || "";
const token = process.env.CODING_EXECUTOR_TOKEN || "";
if (!host || !port) {
  console.log(JSON.stringify({
    endpoint_configured:false,
    token_configured:Boolean(token),
    reachable:false
  }));
  process.exit(0);
}
fetch("http://" + host + ":" + port + "/health")
  .then(async (response) => {
    const raw = await response.text();
    let body = {};
    try { body = JSON.parse(raw); } catch (_) {}
    console.log(JSON.stringify({
      endpoint_configured:true,
      token_configured:Boolean(token),
      reachable:true,
      http_status:response.status,
      ok:response.ok,
      service_status:typeof body.status === "string" ? body.status : null,
      version:typeof body.version === "string" ? body.version : null
    }));
  })
  .catch(() => {
    console.log(JSON.stringify({
      endpoint_configured:true,
      token_configured:Boolean(token),
      reachable:false,
      ok:false,
      error_code:"executor_unreachable"
    }));
  });
"""
    rc, out, err = run(["docker", "exec", "librechat", "node", "-e", js], timeout=20)
    if rc != 0:
        return safe_error("executor_probe_failed", err or out)
    try:
        return json.loads(out.splitlines()[-1]) if out else {"ok": False, "error_code": "executor_empty_response"}
    except Exception as exc:
        return safe_error("executor_non_json_response", exc)


def maintenance_snapshot():
    js = r"""
const net = require("net");
const host = process.env.CODING_MAINTENANCE_HOST || "";
const portRaw = process.env.CODING_MAINTENANCE_PORT || "";
const token = process.env.CODING_MAINTENANCE_TOKEN || "";
const validPort = /^[0-9]+$/.test(portRaw);
const port = validPort ? Number(portRaw) : 0;

if (!host || !validPort || port <= 0 || port > 65535) {
  console.log(JSON.stringify({
    endpoint_configured:false,
    token_configured:Boolean(token),
    reachable:false
  }));
  process.exit(0);
}

const socket = net.createConnection({host, port});
let settled = false;

function finish(reachable, ok, errorCode) {
  if (settled) return;
  settled = true;
  socket.destroy();
  const result = {
    endpoint_configured:true,
    token_configured:Boolean(token),
    reachable
  };
  if (ok !== undefined) result.ok = ok;
  if (errorCode) result.error_code = errorCode;
  console.log(JSON.stringify(result));
}

socket.setTimeout(5000);
socket.once("connect", () => finish(true, true));
socket.once("timeout", () => finish(false, false, "maintenance_unreachable"));
socket.once("error", () => finish(false, false, "maintenance_unreachable"));
"""
    rc, out, _err = run(["docker", "exec", "librechat", "node", "-e", js], timeout=20)
    if rc != 0:
        return {"ok": False, "error_code": "maintenance_probe_failed"}
    if not out:
        return {"ok": False, "error_code": "maintenance_empty_response"}
    try:
        raw = json.loads(out.splitlines()[-1])
    except Exception:
        return {"ok": False, "error_code": "maintenance_non_json_response"}

    required = ("endpoint_configured", "token_configured", "reachable")
    if not isinstance(raw, dict) or any(type(raw.get(key)) is not bool for key in required):
        return {"ok": False, "error_code": "maintenance_invalid_response"}

    result = {key: raw[key] for key in required}
    if "ok" in raw:
        if type(raw["ok"]) is not bool:
            return {"ok": False, "error_code": "maintenance_invalid_response"}
        result["ok"] = raw["ok"]
    if "error_code" in raw:
        if raw["error_code"] != "maintenance_unreachable":
            return {"ok": False, "error_code": "maintenance_invalid_response"}
        result["error_code"] = raw["error_code"]
    return result


def main():
    result = {
        "schema": 1,
        "checkout": checkout_snapshot(),
        "skill_sync": skill_sync_snapshot(),
        "managed_skills": managed_skills_snapshot(),
        "coding_executor": executor_snapshot(),
        "coding_maintenance": maintenance_snapshot(),
    }
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
