#!/usr/bin/env python3
"""Evaluate completed benchmark pairs against evaluator-only gold/rubric files."""

import argparse
import json
from pathlib import Path

from lab_common import (
    API_BASE, BRANCH, ENV_FILE, GITHUB_TOKEN_ENV, OPERATIONAL_FAILURES, REPO, ROOT,
    LabError, gemini, get_json, get_text, load_env, now_z, parse_json_object,
    put_json, put_text, read_local_json, repo_relative, resolve_api_key, sha256_text,
    slug, write_local_json,
)

SEMANTIC_QUEUE = "custom/ba-agent/automation/semantic-jobs.json"
REVISION_QUEUE = "custom/ba-agent/automation/semantic-revision-jobs.json"
EXECUTION_QUEUE = "custom/ba-agent/automation/jobs.json"

SYSTEM = """You are the evaluator-only judge for a controlled Skill benchmark.
Use only the supplied input packet, gold standard, scoring rubric and raw outputs.
Do not rewrite outputs. Do not reward style beyond the rubric. Do not infer facts,
authority, approval, ownership or source strength not established by the evidence.
Apply every rubric criterion and critical penalty exactly. Score baseline and Skill
independently. Return JSON only, with no markdown fences or prose outside JSON."""

SCHEMA = """Return exactly this shape:
{
  "baseline": {
    "raw_score": 0,
    "critical_penalties": [{"points": 20, "reason": "...", "evidence": "..."}],
    "criteria": [{"criterion": "A", "score": 0, "max": 0, "rationale": "..."}],
    "summary": "..."
  },
  "skill": {
    "raw_score": 0,
    "critical_penalties": [],
    "criteria": [],
    "summary": "..."
  },
  "defects": [
    {"severity": "critical|major|minor", "criterion": "...", "evidence": "...", "correction": "..."}
  ],
  "summary": "..."
}
Do not supply final_score; the controller computes it from raw_score minus listed penalty points.
Only list Skill defects directly supported by the Skill output versus the supplied evidence and rubric.
"""


def penalties(value):
    out = []
    for item in value if isinstance(value, list) else []:
        if not isinstance(item, dict):
            continue
        try:
            points = abs(int(item.get("points", 0)))
        except Exception:
            points = 0
        out.append({
            "points": points,
            "reason": str(item.get("reason") or "").strip(),
            "evidence": str(item.get("evidence") or "").strip(),
        })
    return out


def side(value, label):
    if not isinstance(value, dict):
        raise LabError("Evaluator response missing {} object".format(label))
    try:
        raw = int(value.get("raw_score"))
    except Exception:
        raise LabError("Evaluator {} raw_score must be an integer".format(label))
    if raw < 0 or raw > 100:
        raise LabError("Evaluator {} raw_score out of range".format(label))
    p = penalties(value.get("critical_penalties"))
    return {
        "raw_score": raw,
        "critical_penalties": p,
        "final_score": max(0, raw - sum(x["points"] for x in p)),
        "criteria": value.get("criteria") if isinstance(value.get("criteria"), list) else [],
        "summary": str(value.get("summary") or "").strip(),
    }


def normalize(value):
    defects = []
    for item in value.get("defects") if isinstance(value.get("defects"), list) else []:
        if isinstance(item, dict):
            defects.append({
                "severity": str(item.get("severity") or "minor").strip().lower(),
                "criterion": str(item.get("criterion") or "").strip(),
                "evidence": str(item.get("evidence") or "").strip(),
                "correction": str(item.get("correction") or "").strip(),
            })
    return {
        "baseline": side(value.get("baseline"), "baseline"),
        "skill": side(value.get("skill"), "skill"),
        "defects": defects,
        "summary": str(value.get("summary") or "").strip(),
    }


def gate(evaluation, job):
    skill = evaluation["skill"]["final_score"]
    baseline = evaluation["baseline"]["final_score"]
    minimum = int(job.get("min_score", 90))
    max_gap = int(job.get("max_baseline_gap", 10))
    zero_critical = bool(job.get("zero_critical_required", True))
    reasons = []
    if skill < minimum:
        reasons.append("skill_final_score {} < {}".format(skill, minimum))
    if baseline - skill > max_gap:
        reasons.append("baseline_gap {} > {}".format(baseline - skill, max_gap))
    if zero_critical and evaluation["skill"]["critical_penalties"]:
        reasons.append("critical_penalty_present")
    return {
        "passed": not reasons,
        "min_score": minimum,
        "max_baseline_gap": max_gap,
        "zero_critical_required": zero_critical,
        "reasons": reasons,
    }


def render(record):
    ev, g = record["evaluation"], record["gate"]
    lines = [
        "# Semantic Benchmark Evaluation", "",
        "> Evaluator-only artifact. Raw benchmark outputs remain unchanged.", "",
        "- Semantic job: `{}`".format(record["job_id"]),
        "- Benchmark: `{}`".format(record["benchmark"]),
        "- Evaluator model: `{}`".format(record["evaluator_model"]),
        "- Baseline final score: **{}/100**".format(ev["baseline"]["final_score"]),
        "- Skill final score: **{}/100**".format(ev["skill"]["final_score"]),
        "- Gate: **{}**".format("PASS" if g["passed"] else "REVISION REQUIRED"), "",
        "## Summary", "", ev["summary"] or "_No evaluator summary supplied._", "",
    ]
    if ev["defects"]:
        lines.extend(["## Skill defects", ""])
        for i, defect in enumerate(ev["defects"], 1):
            lines.append("{}. **{} / {}** — {} Correction: {}".format(
                i, defect["severity"], defect["criterion"] or "unmapped",
                defect["evidence"] or "No evidence text supplied.",
                defect["correction"] or "No correction supplied.",
            ))
    return "\n".join(lines) + "\n"


def next_model(job):
    chain = [str(x).strip() for x in (job.get("fallback_models") or []) if str(x).strip()]
    current = str(job.get("evaluator_model") or "").strip()
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
    clone["evaluator_model"] = model
    clone["autonomy_parent"] = job["id"]
    clone["autonomy_reason"] = "semantic_evaluator_operational_fallback"
    append_unique(args.repo, args.branch, token, args.semantic_jobs, clone, "automation: queue semantic evaluator fallback")
    return clone["id"]


def queue_revision(args, token, job, record):
    revision_id = "{}-revision-{}".format(job["id"], len(record["evaluation"]["defects"]))
    revision = {
        "id": revision_id,
        "enabled": True,
        "benchmark": job["benchmark"],
        "baseline_result": job["baseline_result"],
        "skill_result": job["skill_result"],
        "skill_metadata": job.get("skill_metadata"),
        "evaluation_artifact": "results/{}-semantic-evaluation.json".format(job["id"]),
        "revision_model": job.get("revision_model") or job.get("evaluator_model"),
        "fallback_models": job.get("revision_fallback_models") or job.get("fallback_models") or [],
        "rerun_model": job.get("rerun_model") or job.get("generation_model"),
        "generation_fallback_models": job.get("generation_fallback_models") or [],
        "rerun_id_prefix": job.get("rerun_id_prefix") or "{}-semantic-rerun".format(slug(job["benchmark"].rsplit("/", 1)[-1])),
        "max_revisions": int(job.get("max_revisions", 1)),
        "revision_count": int(job.get("revision_count", 0)),
        "semantic_policy": {
            "min_score": int(job.get("min_score", 90)),
            "max_baseline_gap": int(job.get("max_baseline_gap", 10)),
            "zero_critical_required": bool(job.get("zero_critical_required", True)),
        },
    }
    append_unique(args.repo, args.branch, token, REVISION_QUEUE, revision, "automation: queue evidence-backed Skill revision")
    return revision_id


def queue_on_pass(args, token, job):
    for item in job.get("on_pass_jobs") or []:
        if isinstance(item, dict) and item.get("id"):
            append_unique(args.repo, args.branch, token, EXECUTION_QUEUE, item, "automation: queue post-evaluation progression job")


def process(args, token, api_key, job):
    benchmark = str(job.get("benchmark") or "").strip().rstrip("/")
    if not benchmark.startswith("custom/ba-agent/benchmarks/"):
        raise LabError("Semantic job benchmark path is not allowed")
    config, _ = get_json(args.repo, args.branch, benchmark + "/benchmark.json", token)
    name = str(config.get("name") or benchmark.rsplit("/", 1)[-1])
    input_text, _ = get_text(args.repo, args.branch, benchmark + "/" + str(config.get("input") or "input.md"), token)
    gold, _ = get_text(args.repo, args.branch, benchmark + "/gold-standard.md", token)
    rubric, _ = get_text(args.repo, args.branch, benchmark + "/scoring-rubric.md", token)
    baseline, _ = get_text(args.repo, args.branch, benchmark + "/" + str(job["baseline_result"]), token, missing_ok=True)
    skill_raw, _ = get_text(args.repo, args.branch, benchmark + "/" + str(job["skill_result"]), token, missing_ok=True)
    if baseline is None or skill_raw is None:
        return {"status": "waiting"}
    if job.get("skill_metadata"):
        meta, _ = get_json(args.repo, args.branch, benchmark + "/" + str(job["skill_metadata"]), token, missing_ok=True)
        if meta is None or meta.get("status") != "success":
            return {"status": "waiting"}
    skill_path = repo_relative(benchmark, config.get("skill"))
    current_skill, _ = get_text(args.repo, args.branch, skill_path, token)
    if job.get("skill_metadata"):
        expected = str(meta.get("skill_sha256") or "")
        if expected and expected != sha256_text(current_skill):
            return {"status": "stale_skill", "expected": expected, "current": sha256_text(current_skill)}
    prompt = "\n\n".join([
        "# Required JSON contract\n" + SCHEMA,
        "# Benchmark\n" + name,
        "# Input packet\n" + input_text,
        "# Evaluator-only gold standard\n" + gold,
        "# Evaluator-only scoring rubric\n" + rubric,
        "# Baseline raw output\n" + baseline,
        "# Skill raw output\n" + skill_raw,
    ])
    model = str(job.get("evaluator_model") or "").strip()
    if not model:
        raise LabError("Semantic job requires evaluator_model")
    result = gemini(api_key, model, prompt, SYSTEM, timeout=args.timeout, api_base=args.api_base)
    if result["status"] != "success":
        return {"status": result["status"], "error": result.get("error")}
    evaluation = normalize(parse_json_object(result["text"]))
    g = gate(evaluation, job)
    record = {
        "schema": 1,
        "job_id": job["id"],
        "benchmark": name,
        "benchmark_path": benchmark,
        "evaluator_model": model,
        "evaluated_at": now_z(),
        "baseline_result": job["baseline_result"],
        "skill_result": job["skill_result"],
        "skill_path": skill_path,
        "skill_sha256": sha256_text(current_skill),
        "evaluation": evaluation,
        "gate": g,
        "usage": result.get("usage"),
    }
    base = benchmark + "/results/" + str(job["id"]) + "-semantic-evaluation"
    put_json(args.repo, args.branch, base + ".json", record, token, "evaluation: publish semantic score")
    put_text(args.repo, args.branch, base + ".md", render(record), token, "evaluation: publish semantic summary")
    if g["passed"]:
        queue_on_pass(args, token, job)
        return {"status": "passed", "record": record}
    if bool(job.get("allow_auto_revision", False)):
        revision_id = queue_revision(args, token, job, record)
        return {"status": "revision_queued", "revision_id": revision_id, "record": record}
    return {"status": "revision_required", "record": record}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--repo", default=REPO)
    p.add_argument("--branch", default=BRANCH)
    p.add_argument("--root", default=ROOT)
    p.add_argument("--env-file", default=ENV_FILE)
    p.add_argument("--github-token-env", default=GITHUB_TOKEN_ENV)
    p.add_argument("--semantic-jobs", default=SEMANTIC_QUEUE)
    p.add_argument("--api-base", default=API_BASE)
    p.add_argument("--timeout", type=int, default=180)
    args = p.parse_args()
    env = load_env(args.env_file)
    token = env.get(args.github_token_env, "").strip()
    if not token:
        raise LabError("{} is required".format(args.github_token_env))
    api_key = resolve_api_key(env)
    queue, _ = get_json(args.repo, args.branch, args.semantic_jobs, token)
    jobs = queue.get("jobs") or []
    state_path = Path(args.root) / "custom/ba-agent/automation/semantic-evaluator-state.json"
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
        print("[semantic-evaluator] {} -> {}".format(job_id, status))
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
        print("[semantic-evaluator] no semantic transition required")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except LabError as exc:
        print("ERROR: {}".format(exc))
        raise SystemExit(2)
