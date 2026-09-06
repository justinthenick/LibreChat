#!/usr/bin/env python3
"""Apply bounded evidence-backed Skill revisions queued by semantic_evaluator.py."""

import argparse
import json
from pathlib import Path
import re

from lab_common import (
    API_BASE, BRANCH, ENV_FILE, GITHUB_TOKEN_ENV, OPERATIONAL_FAILURES, REPO, ROOT,
    LabError, gemini, get_json, get_text, load_env, now_z, put_json, put_text,
    read_local_json, repo_relative, resolve_api_key, sha256_text, slug, write_local_json,
)

REVISION_QUEUE = "custom/ba-agent/automation/semantic-revision-jobs.json"
SEMANTIC_QUEUE = "custom/ba-agent/automation/semantic-jobs.json"
EXECUTION_QUEUE = "custom/ba-agent/automation/jobs.json"

SYSTEM = """You are revising one reusable Skill under a controlled benchmark process.
Use only the supplied current Skill, machine evaluation, evaluator evidence, input packet,
gold standard, scoring rubric and raw Skill output. Make the smallest reusable correction
that fixes the listed evidence-backed defects. Do not optimize to benchmark-specific names,
values or wording. Do not invent authority, approval, ownership or evidence. Preserve the
Skill's YAML frontmatter name and public purpose. Return the complete revised SKILL.md only,
with no markdown fences. Do not change the Version line; the controller bumps it."""


def skill_name(text):
    match = re.search(r"(?m)^name:\s*([^\s#]+)\s*$", text)
    return match.group(1).strip() if match else None


def version_tuple(text):
    match = re.search(r"(?m)^Version:\s*\*\*(\d+)\.(\d+)\.(\d+)\*\*\s*$", text)
    return tuple(int(x) for x in match.groups()) if match else None


def validate_and_bump(current, candidate):
    if not candidate.startswith("---\n"):
        raise LabError("Revision lost YAML frontmatter")
    if skill_name(candidate) != skill_name(current) or not skill_name(current):
        raise LabError("Revision changed or lost Skill name")
    current_version = version_tuple(current)
    if not current_version:
        raise LabError("Current Skill Version line is unsupported")
    if len(candidate) < 500:
        raise LabError("Revision is implausibly short")
    current_line = "Version: **{}.{}.{}**".format(*current_version)
    candidate, count = re.subn(
        r"(?m)^Version:\s*\*\*\d+\.\d+\.\d+\*\*\s*$",
        current_line,
        candidate,
        count=1,
    )
    if count != 1:
        raise LabError("Revision lost Version line")
    new_version = (current_version[0], current_version[1], current_version[2] + 1)
    new_line = "Version: **{}.{}.{}**".format(*new_version)
    candidate = candidate.replace(current_line, new_line, 1)
    return candidate.rstrip() + "\n", "{}.{}.{}".format(*new_version)


def next_model(job):
    chain = [str(x).strip() for x in (job.get("fallback_models") or []) if str(x).strip()]
    current = str(job.get("revision_model") or "").strip()
    if current in chain:
        idx = chain.index(current) + 1
        return chain[idx] if idx < len(chain) else None
    return chain[0] if chain else None


def append_unique(repo, branch, token, path, item, message):
    queue, sha = get_json(repo, branch, path, token)
    jobs = queue.get("jobs") or []
    if not isinstance(jobs, list):
        raise LabError("{} jobs is malformed".format(path))
    ids = {str(x.get("id")) for x in jobs if isinstance(x, dict)}
    if str(item.get("id")) not in ids:
        jobs.append(item)
        queue["jobs"] = jobs
        put_json(repo, branch, path, queue, token, message, sha=sha)


def queue_fallback(args, token, job, model):
    clone = dict(job)
    clone["id"] = "{}-auto-{}".format(job["id"], slug(model))
    clone["revision_model"] = model
    clone["autonomy_parent"] = job["id"]
    clone["autonomy_reason"] = "semantic_revision_operational_fallback"
    append_unique(args.repo, args.branch, token, args.revision_jobs, clone, "automation: queue semantic revision fallback")
    return clone["id"]


def queue_execution_rerun(args, token, job, version):
    model = str(job.get("rerun_model") or "").strip()
    if not model:
        raise LabError("Automatic revision requires rerun_model")
    prefix = str(job.get("rerun_id_prefix") or "semantic-rerun")
    run_id = "{}-v{}".format(prefix, version.replace(".", ""))
    queue, sha = get_json(args.repo, args.branch, EXECUTION_QUEUE, token)
    jobs = queue.get("jobs") or []
    ids = {str(x.get("id")) for x in jobs if isinstance(x, dict)}
    base = run_id
    counter = 2
    while run_id in ids:
        run_id = "{}-{}".format(base, counter)
        counter += 1
    rerun = {
        "id": run_id,
        "enabled": True,
        "benchmark": job["benchmark"],
        "model": model,
        "mode": "skill",
        "repeat": 1,
        "temperature": 0.0,
        "auto_fallback": True,
        "fallback_models": job.get("generation_fallback_models") or [model],
        "autonomy_reason": "semantic_revision_rerun",
    }
    jobs.append(rerun)
    queue["jobs"] = jobs
    put_json(args.repo, args.branch, EXECUTION_QUEUE, queue, token, "automation: queue revised Skill rerun", sha=sha)
    return rerun


def queue_followup_evaluation(args, token, job, rerun, new_version):
    policy = job.get("semantic_policy") or {}
    model = str((job.get("fallback_models") or [job.get("revision_model")])[0])
    model_slug = slug(rerun["model"])
    follow = {
        "id": "{}-eval-v{}".format(job["id"], new_version.replace(".", "")),
        "enabled": True,
        "benchmark": job["benchmark"],
        "baseline_result": job["baseline_result"],
        "skill_result": "results/{}-{}-skill-01.md".format(rerun["id"], model_slug),
        "skill_metadata": "results/{}-{}-skill-01.json".format(rerun["id"], model_slug),
        "generation_model": rerun["model"],
        "evaluator_model": model,
        "fallback_models": job.get("fallback_models") or [model],
        "revision_model": model,
        "revision_fallback_models": job.get("fallback_models") or [model],
        "rerun_model": rerun["model"],
        "generation_fallback_models": job.get("generation_fallback_models") or [rerun["model"]],
        "rerun_id_prefix": job.get("rerun_id_prefix"),
        "min_score": int(policy.get("min_score", 90)),
        "max_baseline_gap": int(policy.get("max_baseline_gap", 10)),
        "zero_critical_required": bool(policy.get("zero_critical_required", True)),
        "allow_auto_revision": True,
        "max_revisions": int(job.get("max_revisions", 1)),
        "revision_count": int(job.get("revision_count", 0)) + 1,
        "autonomy_parent": job["id"],
        "autonomy_reason": "evaluate_semantic_revision",
    }
    append_unique(args.repo, args.branch, token, SEMANTIC_QUEUE, follow, "automation: queue revised Skill evaluation")
    return follow


def process(args, token, api_key, job):
    if int(job.get("revision_count", 0)) >= int(job.get("max_revisions", 1)):
        return {"status": "revision_limit_reached"}
    benchmark = str(job.get("benchmark") or "").strip().rstrip("/")
    if not benchmark.startswith("custom/ba-agent/benchmarks/"):
        raise LabError("Revision benchmark path is not allowed")
    config, _ = get_json(args.repo, args.branch, benchmark + "/benchmark.json", token)
    skill_path = repo_relative(benchmark, config.get("skill"))
    if not skill_path.startswith("custom/ba-agent/skills/") or not skill_path.endswith("/SKILL.md"):
        raise LabError("Automatic revisions are restricted to custom/ba-agent/skills/*/SKILL.md")
    current_skill, skill_sha = get_text(args.repo, args.branch, skill_path, token)
    if job.get("skill_metadata"):
        meta, _ = get_json(args.repo, args.branch, benchmark + "/" + str(job["skill_metadata"]), token, missing_ok=True)
        if meta is None:
            return {"status": "waiting"}
        expected = str(meta.get("skill_sha256") or "")
        if expected and expected != sha256_text(current_skill):
            return {"status": "stale_skill", "expected": expected, "current": sha256_text(current_skill)}
    evaluation, _ = get_json(args.repo, args.branch, benchmark + "/" + str(job["evaluation_artifact"]), token, missing_ok=True)
    if evaluation is None:
        return {"status": "waiting"}
    input_text, _ = get_text(args.repo, args.branch, benchmark + "/" + str(config.get("input") or "input.md"), token)
    gold, _ = get_text(args.repo, args.branch, benchmark + "/gold-standard.md", token)
    rubric, _ = get_text(args.repo, args.branch, benchmark + "/scoring-rubric.md", token)
    skill_raw, _ = get_text(args.repo, args.branch, benchmark + "/" + str(job["skill_result"]), token, missing_ok=True)
    if skill_raw is None:
        return {"status": "waiting"}
    prompt = "\n\n".join([
        "# Current Skill\n" + current_skill,
        "# Machine evaluation\n" + json.dumps(evaluation, indent=2, ensure_ascii=False),
        "# Input packet\n" + input_text,
        "# Gold standard\n" + gold,
        "# Scoring rubric\n" + rubric,
        "# Raw Skill output\n" + skill_raw,
        "# Required action\nReturn the complete revised SKILL.md with only reusable evidence-backed corrections.",
    ])
    model = str(job.get("revision_model") or "").strip()
    if not model:
        raise LabError("Revision job requires revision_model")
    result = gemini(api_key, model, prompt, SYSTEM, max_tokens=12000, timeout=args.timeout, api_base=args.api_base)
    if result["status"] != "success":
        return {"status": result["status"], "error": result.get("error")}
    candidate = result["text"].strip()
    if candidate.startswith("```"):
        candidate = re.sub(r"^```(?:markdown)?\s*", "", candidate, flags=re.I)
        candidate = re.sub(r"\s*```$", "", candidate)
    revised, new_version = validate_and_bump(current_skill, candidate)
    commit = put_text(
        args.repo, args.branch, skill_path, revised, token,
        "skill: apply evidence-backed semantic correction v{}".format(new_version),
        sha=skill_sha,
    )
    rerun = queue_execution_rerun(args, token, job, new_version)
    follow = queue_followup_evaluation(args, token, job, rerun, new_version)
    return {
        "status": "revised_and_queued",
        "new_version": new_version,
        "skill_path": skill_path,
        "skill_commit": commit,
        "rerun_job": rerun["id"],
        "followup_semantic_job": follow["id"],
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--repo", default=REPO)
    p.add_argument("--branch", default=BRANCH)
    p.add_argument("--root", default=ROOT)
    p.add_argument("--env-file", default=ENV_FILE)
    p.add_argument("--github-token-env", default=GITHUB_TOKEN_ENV)
    p.add_argument("--revision-jobs", default=REVISION_QUEUE)
    p.add_argument("--api-base", default=API_BASE)
    p.add_argument("--timeout", type=int, default=180)
    args = p.parse_args()
    env = load_env(args.env_file)
    token = env.get(args.github_token_env, "").strip()
    if not token:
        raise LabError("{} is required".format(args.github_token_env))
    api_key = resolve_api_key(env)
    queue, _ = get_json(args.repo, args.branch, args.revision_jobs, token)
    jobs = queue.get("jobs") or []
    state_path = Path(args.root) / "custom/ba-agent/automation/semantic-reviser-state.json"
    state = read_local_json(state_path, {"schema": 1, "jobs": {}})
    records = state.setdefault("jobs", {})
    acted = False
    for job in jobs:
        if not isinstance(job, dict) or not job.get("id") or not bool(job.get("enabled", True)):
            continue
        job_id = str(job["id"])
        prior = records.get(job_id)
        if isinstance(prior, dict) and prior.get("terminal"):
            continue
        try:
            outcome = process(args, token, api_key, job)
        except Exception as exc:
            outcome = {"status": "error", "error": str(exc)}
        status = str(outcome.get("status") or "error")
        print("[semantic-reviser] {} -> {}".format(job_id, status))
        if status == "waiting":
            continue
        if status in OPERATIONAL_FAILURES:
            fallback = next_model(job)
            if fallback:
                outcome["fallback_job"] = queue_fallback(args, token, job, fallback)
            records[job_id] = {"at": now_z(), "status": status, "terminal": True, "outcome": outcome}
        else:
            records[job_id] = {"at": now_z(), "status": status, "terminal": status != "waiting", "outcome": outcome}
        acted = True
        break
    state["last_checked_at"] = now_z()
    write_local_json(state_path, state)
    if not acted:
        print("[semantic-reviser] no semantic transition required")
    return 2 if acted and status not in ("revised_and_queued", "revision_limit_reached") else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except LabError as exc:
        print("ERROR: {}".format(exc))
        raise SystemExit(2)
