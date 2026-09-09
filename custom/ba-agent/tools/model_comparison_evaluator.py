#!/usr/bin/env python3
"""Evaluate two successful model outputs against one benchmark gold/rubric.

Unlike semantic_evaluator.py, this evaluator intentionally permits different
model IDs while requiring identical input, prompt and Skill hashes. Results are
published to the benchmark results folder and each queue job is one-shot.
"""

import argparse
import json
from pathlib import Path

from lab_common import (
    API_BASE, BRANCH, ENV_FILE, GITHUB_TOKEN_ENV, REPO, ROOT,
    LabError, gemini, get_json, get_text, load_env, now_z, parse_json_object,
    put_json, put_text, read_local_json, repo_relative, resolve_api_key,
    sha256_text, write_local_json,
)

QUEUE = "custom/ba-agent/automation/model-comparison-jobs.json"
STATE_REL = "custom/ba-agent/automation/model-comparison-evaluator-state.json"

SYSTEM = """You are the evaluator-only judge for a controlled cross-model BA benchmark.
Use only the supplied input, evaluator-only gold standard, scoring rubric and the two raw outputs.
Score each output independently against the rubric. Apply every automatic-fail condition literally.
Do not reward verbosity or style beyond the rubric. Do not infer missing evidence. The two model IDs
are labels, not quality priors. Apply the benchmark's model-comparison decision rule exactly.
Return JSON only, with no markdown fences or prose outside JSON."""

SCHEMA = """Return exactly this shape:
{
  "left": {
    "model": "...",
    "score": 0,
    "automatic_fail": false,
    "criteria": [{"criterion": "...", "score": 0, "max": 0, "rationale": "..."}],
    "violations": ["..."],
    "summary": "..."
  },
  "right": {
    "model": "...",
    "score": 0,
    "automatic_fail": false,
    "criteria": [],
    "violations": [],
    "summary": "..."
  },
  "preferred_model": "model-id-or-none",
  "decision_rule_met": false,
  "rationale": "..."
}
Scores must be integers 0..100. automatic_fail must reflect only the rubric's automatic-fail rules.
preferred_model must be `none` unless the supplied model-comparison decision rule is satisfied."""


def validate_meta(label, meta, raw, input_hash):
    if not isinstance(meta, dict):
        raise LabError("{} metadata missing".format(label))
    if meta.get("status") != "success":
        raise LabError("{} generation did not succeed".format(label))
    if meta.get("mode") != "skill":
        raise LabError("{} is not a Skill-mode generation".format(label))
    if meta.get("input_sha256") != input_hash:
        raise LabError("{} input hash mismatch".format(label))
    if meta.get("finish_reason") == "MAX_TOKENS":
        raise LabError("{} generation was truncated".format(label))
    if meta.get("result_sha256") and meta.get("result_sha256") != sha256_text(raw):
        raise LabError("{} raw result hash mismatch".format(label))


def normalize_side(value, expected_model):
    if not isinstance(value, dict):
        raise LabError("Evaluator side missing")
    try:
        score = int(value.get("score", 0))
    except Exception:
        score = 0
    score = max(0, min(100, score))
    criteria = value.get("criteria") if isinstance(value.get("criteria"), list) else []
    violations = [str(x).strip() for x in (value.get("violations") or []) if str(x).strip()]
    return {
        "model": expected_model,
        "score": score,
        "automatic_fail": bool(value.get("automatic_fail", False)),
        "criteria": criteria,
        "violations": violations,
        "summary": str(value.get("summary") or "").strip(),
    }


def render(record):
    ev = record["evaluation"]
    lines = [
        "# Cross-Model Semantic Evaluation",
        "",
        "- Job: `{}`".format(record["job_id"]),
        "- Evaluator: `{}`".format(record["evaluator_model"]),
        "- Left: `{}` — **{}/100**{}".format(ev["left"]["model"], ev["left"]["score"], " AUTO-FAIL" if ev["left"]["automatic_fail"] else ""),
        "- Right: `{}` — **{}/100**{}".format(ev["right"]["model"], ev["right"]["score"], " AUTO-FAIL" if ev["right"]["automatic_fail"] else ""),
        "- Preferred model: `{}`".format(ev["preferred_model"]),
        "- Decision rule met: `{}`".format(str(ev["decision_rule_met"]).lower()),
        "",
        "## Rationale",
        "",
        ev["rationale"] or "No rationale supplied.",
    ]
    for side_name in ("left", "right"):
        side = ev[side_name]
        lines.extend(["", "## {} — {}".format(side_name.title(), side["model"]), ""])
        for item in side["criteria"]:
            if isinstance(item, dict):
                lines.append("- **{}:** {}/{} — {}".format(
                    item.get("criterion", "criterion"), item.get("score", 0), item.get("max", 0), item.get("rationale", "")
                ))
        if side["violations"]:
            lines.extend(["", "Violations:"])
            lines.extend("- {}".format(x) for x in side["violations"])
        if side["summary"]:
            lines.extend(["", side["summary"]])
    return "\n".join(lines) + "\n"


def process(args, token, api_key, job):
    benchmark = str(job.get("benchmark") or "").strip().rstrip("/")
    if not benchmark.startswith("custom/ba-agent/benchmarks/"):
        raise LabError("Invalid benchmark path")
    config, _ = get_json(args.repo, args.branch, benchmark + "/benchmark.json", token)
    input_text, _ = get_text(args.repo, args.branch, benchmark + "/" + str(config.get("input") or "input.md"), token)
    gold, _ = get_text(args.repo, args.branch, benchmark + "/gold-standard.md", token)
    rubric, _ = get_text(args.repo, args.branch, benchmark + "/scoring-rubric.md", token)

    left_raw, _ = get_text(args.repo, args.branch, benchmark + "/" + str(job["left_result"]), token, missing_ok=True)
    right_raw, _ = get_text(args.repo, args.branch, benchmark + "/" + str(job["right_result"]), token, missing_ok=True)
    if left_raw is None or right_raw is None:
        return {"status": "waiting"}

    left_meta, _ = get_json(args.repo, args.branch, benchmark + "/" + str(job["left_metadata"]), token, missing_ok=True)
    right_meta, _ = get_json(args.repo, args.branch, benchmark + "/" + str(job["right_metadata"]), token, missing_ok=True)
    if left_meta is None or right_meta is None:
        return {"status": "waiting"}

    input_hash = sha256_text(input_text)
    validate_meta("left", left_meta, left_raw, input_hash)
    validate_meta("right", right_meta, right_raw, input_hash)
    if left_meta.get("prompt_sha256") != right_meta.get("prompt_sha256"):
        raise LabError("Prompt hashes differ")
    if left_meta.get("skill_sha256") != right_meta.get("skill_sha256"):
        raise LabError("Skill hashes differ")

    skill_path = repo_relative(benchmark, config.get("skill"))
    current_skill, _ = get_text(args.repo, args.branch, skill_path, token)
    if not left_meta.get("skill_sha256") or left_meta.get("skill_sha256") != sha256_text(current_skill):
        raise LabError("Generation Skill differs from current benchmark Skill")

    prompt = "\n\n".join([
        "# Required JSON contract\n" + SCHEMA,
        "# Benchmark input\n" + input_text,
        "# Evaluator-only gold standard\n" + gold,
        "# Evaluator-only scoring rubric\n" + rubric,
        "# Left model\n" + str(left_meta.get("model")) + "\n\n" + left_raw,
        "# Right model\n" + str(right_meta.get("model")) + "\n\n" + right_raw,
    ])
    evaluator_model = str(job.get("evaluator_model") or "").strip()
    if not evaluator_model:
        raise LabError("evaluator_model is required")
    result = gemini(api_key, evaluator_model, prompt, SYSTEM, max_tokens=int(job.get("max_output_tokens") or 8192), timeout=args.timeout, api_base=args.api_base)
    if result["status"] != "success":
        return {"status": result["status"], "error": result.get("error")}

    raw_ev = parse_json_object(result["text"])
    left = normalize_side(raw_ev.get("left"), str(left_meta.get("model")))
    right = normalize_side(raw_ev.get("right"), str(right_meta.get("model")))
    preferred = str(raw_ev.get("preferred_model") or "none").strip()
    if preferred not in (left["model"], right["model"], "none"):
        preferred = "none"
    decision_rule_met = bool(raw_ev.get("decision_rule_met", False))
    if preferred == "none":
        decision_rule_met = False

    evaluation = {
        "left": left,
        "right": right,
        "preferred_model": preferred,
        "decision_rule_met": decision_rule_met,
        "rationale": str(raw_ev.get("rationale") or "").strip(),
    }
    record = {
        "schema": 1,
        "job_id": str(job["id"]),
        "benchmark": str(config.get("name") or benchmark.rsplit("/", 1)[-1]),
        "benchmark_path": benchmark,
        "evaluated_at": now_z(),
        "evaluator_model": evaluator_model,
        "left_result": job["left_result"],
        "right_result": job["right_result"],
        "left_metadata": left_meta,
        "right_metadata": right_meta,
        "skill_path": skill_path,
        "skill_sha256": sha256_text(current_skill),
        "evaluation": evaluation,
        "usage": result.get("usage"),
    }
    base = benchmark + "/results/" + str(job["id"]) + "-model-comparison"
    put_json(args.repo, args.branch, base + ".json", record, token, "evaluation: publish cross-model score")
    put_text(args.repo, args.branch, base + ".md", render(record), token, "evaluation: publish cross-model summary")
    return {"status": "completed", "record": record}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--repo", default=REPO)
    p.add_argument("--branch", default=BRANCH)
    p.add_argument("--root", default=ROOT)
    p.add_argument("--env-file", default=ENV_FILE)
    p.add_argument("--github-token-env", default=GITHUB_TOKEN_ENV)
    p.add_argument("--jobs", default=QUEUE)
    p.add_argument("--api-base", default=API_BASE)
    p.add_argument("--timeout", type=int, default=240)
    args = p.parse_args()

    env = load_env(args.env_file)
    token = env.get(args.github_token_env, "").strip()
    if not token:
        raise LabError("{} is required".format(args.github_token_env))
    api_key = resolve_api_key(env)
    queue, _ = get_json(args.repo, args.branch, args.jobs, token)
    jobs = queue.get("jobs") or []
    state_path = Path(args.root) / STATE_REL
    state = read_local_json(state_path, {"schema": 1, "jobs": {}})
    records = state.setdefault("jobs", {})
    acted = False

    for job in jobs:
        if not isinstance(job, dict) or not job.get("id") or not bool(job.get("enabled", True)):
            continue
        job_id = str(job["id"])
        if isinstance(records.get(job_id), dict) and records[job_id].get("terminal"):
            continue
        try:
            outcome = process(args, token, api_key, job)
        except Exception as exc:
            outcome = {"status": "error", "error": str(exc)}
        status = str(outcome.get("status") or "error")
        print("[model-comparison] {} -> {}".format(job_id, status))
        if status == "waiting":
            continue
        terminal = status == "completed" or status == "error"
        records[job_id] = {
            "status": status,
            "terminal": terminal,
            "updated_at": now_z(),
            "error": outcome.get("error"),
        }
        write_local_json(state_path, state)
        acted = True

    if not acted:
        print("[model-comparison] no comparison transition required")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except LabError as exc:
        print("ERROR: {}".format(exc))
        raise SystemExit(2)
