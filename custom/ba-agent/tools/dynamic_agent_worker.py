#!/usr/bin/env python3
"""Run dynamically routed Agent -> Skill execution jobs on the NAS.

The Agent performs routing only. The runner validates the selected Skill names
against an allowlist, then actually invokes those Skill instructions in the
returned order. Evaluator-only gold/rubric files are never loaded here.

Each dynamic job ID is attempted once and recorded in a local state file.
"""

import argparse
import json
from pathlib import Path
import sys

from lab_common import (
    API_BASE,
    BRANCH,
    ENV_FILE,
    GITHUB_TOKEN_ENV,
    OPERATIONAL_FAILURES,
    REPO,
    ROOT,
    LabError,
    gemini,
    get_json,
    get_text,
    load_env,
    now_z,
    parse_json_object,
    put_json,
    put_text,
    read_local_json,
    repo_relative,
    resolve_api_key,
    sha256_text,
    slug,
    write_local_json,
)

DYNAMIC_QUEUE = "custom/ba-agent/automation/dynamic-jobs.json"
STATE_REL = "custom/ba-agent/automation/dynamic-worker-state.json"

ROUTE_CONTRACT = """Return JSON only, with exactly this top-level shape:
{
  "objective": "...",
  "selected_skills": ["exact-skill-name", "..."],
  "not_selected": [{"skill": "exact-skill-name", "reason": "..."}],
  "stop_rules": ["..."],
  "expected_final_artifact": "..."
}
Rules:
- selected_skills must contain only exact names from the supplied allowed catalog.
- preserve dependency order and choose the minimum sufficient route.
- do not execute the Skills in the routing response.
- do not invent owners, approvals, architecture, policy, or certainty.
"""

EXECUTION_INSTRUCTION = """You are being invoked as one dynamically selected Skill in a controlled Agent benchmark.
Execute only the capability in your Skill instruction. Preserve source-backed state, authority,
traceability, and uncertainty. Do not claim another Skill ran unless its supplied handoff proves it.
Use the original source packet only to preserve evidence context; treat the upstream handoff as the
authoritative output of preceding selected Skills. Produce a complete handoff artifact for the next
selected Skill or final user outcome.
"""


def strip_frontmatter(text):
    if not text.startswith("---\n"):
        return text
    lines = text.splitlines()
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            return "\n".join(lines[idx + 1 :]).lstrip() + "\n"
    return text


def usage_int(usage, key):
    if not isinstance(usage, dict):
        return 0
    try:
        return int(usage.get(key) or 0)
    except (TypeError, ValueError):
        return 0


def load_job_queue(args, token):
    queue, _ = get_json(args.repo, args.branch, args.dynamic_jobs, token)
    if not bool(queue.get("enabled", True)):
        return []
    jobs = queue.get("jobs") or []
    if not isinstance(jobs, list):
        raise LabError("dynamic-jobs.json jobs must be an array")
    return jobs


def normalize_job(raw):
    if not isinstance(raw, dict):
        raise LabError("Dynamic job must be a JSON object")
    job_id = str(raw.get("id") or "").strip()
    benchmark = str(raw.get("benchmark") or "").strip().rstrip("/")
    model = str(raw.get("model") or "").strip()
    config = str(raw.get("dynamic_config") or "dynamic-a001.json").strip()
    if not job_id:
        raise LabError("Dynamic job missing id")
    if not benchmark.startswith("custom/ba-agent/benchmarks/"):
        raise LabError("Dynamic job {} has invalid benchmark".format(job_id))
    if not model:
        raise LabError("Dynamic job {} missing model".format(job_id))
    if "/" in config or config.startswith("."):
        raise LabError("Dynamic job {} has invalid dynamic_config".format(job_id))
    return {
        "id": job_id,
        "enabled": bool(raw.get("enabled", True)),
        "benchmark": benchmark,
        "model": model,
        "dynamic_config": config,
    }


def load_dynamic_inputs(args, token, job):
    benchmark = job["benchmark"]
    config_path = benchmark + "/" + job["dynamic_config"]
    config, _ = get_json(args.repo, args.branch, config_path, token)

    input_name = str(config.get("input") or "input.md").strip()
    prompt_name = str(config.get("prompt") or "prompt.md").strip()
    input_text, _ = get_text(args.repo, args.branch, benchmark + "/" + input_name, token)
    prompt_text, _ = get_text(args.repo, args.branch, benchmark + "/" + prompt_name, token)

    agent_rel = repo_relative(benchmark, config.get("agent"))
    agent_text, _ = get_text(args.repo, args.branch, agent_rel, token)

    skill_entries = config.get("allowed_skills") or []
    if not isinstance(skill_entries, list) or not skill_entries:
        raise LabError("Dynamic config requires allowed_skills")

    allowed = {}
    ordered_names = []
    for entry in skill_entries:
        if not isinstance(entry, dict):
            raise LabError("allowed_skills entry must be an object")
        name = str(entry.get("name") or "").strip()
        configured_path = str(entry.get("path") or "").strip()
        if not name or not configured_path:
            raise LabError("allowed_skills entry missing name/path")
        if name in allowed:
            raise LabError("Duplicate allowed Skill {}".format(name))
        rel = repo_relative(benchmark, configured_path)
        text, _ = get_text(args.repo, args.branch, rel, token)
        allowed[name] = {"path": rel, "text": text, "sha256": sha256_text(text)}
        ordered_names.append(name)

    max_steps = int(config.get("max_steps") or len(ordered_names))
    if max_steps < 1 or max_steps > len(ordered_names):
        raise LabError("Dynamic config max_steps out of range")

    return {
        "config": config,
        "input_text": input_text,
        "prompt_text": prompt_text,
        "agent_path": agent_rel,
        "agent_text": agent_text,
        "allowed": allowed,
        "ordered_names": ordered_names,
        "max_steps": max_steps,
    }


def validate_route(route, inputs):
    selected = route.get("selected_skills")
    if not isinstance(selected, list):
        raise LabError("Route selected_skills must be an array")
    names = []
    for value in selected:
        name = str(value).strip()
        if name not in inputs["allowed"]:
            raise LabError("Route selected disallowed Skill {}".format(name))
        if name in names:
            raise LabError("Route selected duplicate Skill {}".format(name))
        names.append(name)
    if not names:
        raise LabError("Route selected no Skills for an execution benchmark")
    if len(names) > inputs["max_steps"]:
        raise LabError("Route exceeds max_steps")
    route["selected_skills"] = names

    if not isinstance(route.get("not_selected"), list):
        route["not_selected"] = []
    if not isinstance(route.get("stop_rules"), list):
        route["stop_rules"] = []
    route["objective"] = str(route.get("objective") or "").strip()
    route["expected_final_artifact"] = str(route.get("expected_final_artifact") or "").strip()
    downstream = {"decompose-requirements", "elaborate-acceptance-criteria", "derive-test-cases", "assess-change-impact"}
    if inputs["config"].get("require_active_delta_scope") and downstream.intersection(names):
        active_delta_scope(route, required=True)
    return route


def active_delta_scope(route, required=False):
    rules = [r.strip() for r in route.get("stop_rules", [])
             if isinstance(r, str) and r.strip().startswith("ACTIVE_DELTA_SCOPE:")]
    if not rules and not required:
        return ""
    if len(rules) != 1 or not rules[0].split(":", 1)[1].strip():
        raise LabError("Selective downstream execution requires exactly one nonempty ACTIVE_DELTA_SCOPE")
    return rules[0]


def invocation_system(skill_text, route):
    instruction = strip_frontmatter(skill_text)
    scope = active_delta_scope(route)
    if not scope:
        return instruction
    return instruction + "\n\n# Binding invocation scope\n" + scope + "\n" + (
        "This scope limits artifact creation for this invocation. General coverage or completeness "
        "instructions apply only within this active delta. Read other baseline items as context; "
        "leave their existing downstream artifacts unchanged by reference. Do not create or restate "
        "acceptance criteria, tests or other downstream artifacts for unaffected items. "
        "Reconciliation may classify all source items without regenerating their downstream artifacts.\n"
    )


def render_final(job, route, stage_records, status, operational_status, totals):
    lines = [
        "# Dynamic Agent Invocation Result",
        "",
        "- Agent: `ba-change-delivery-orchestrator`",
        "- Run ID: `{}`".format(job["id"]),
        "- Model: `{}`".format(job["model"]),
        "- Status: `{}`".format(status),
        "- Operational status: `{}`".format(operational_status or "none"),
        "- Selected Skills: `{}`".format(" -> ".join(route.get("selected_skills") or [])),
        "- Total prompt tokens: `{}`".format(totals["prompt"]),
        "- Total candidate tokens: `{}`".format(totals["candidate"]),
        "- Total thought tokens: `{}`".format(totals["thoughts"]),
        "- Total tokens: `{}`".format(totals["total"]),
        "",
        "## Agent routing decision",
        "",
        "```json",
        json.dumps(route, indent=2, ensure_ascii=False),
        "```",
        "",
    ]
    for record in stage_records:
        lines.extend([
            "---",
            "",
            "## {} — {}".format(record["index"], record["skill"]),
            "",
            "- Status: `{}`".format(record["status"]),
            "- Skill SHA-256: `{}`".format(record["skill_sha256"]),
            "",
            record.get("text") or "_No model output._",
            "",
        ])
    return "\n".join(lines).rstrip() + "\n"


def publish_result(args, token, job, inputs, route, stage_records, route_result, status, operational_status, totals):
    results_dir = str(inputs["config"].get("results_dir") or "results").strip("/")
    model_slug = slug(job["model"])
    stem = "{}-{}-dynamic-01".format(slug(job["id"]), model_slug)
    md_rel = "{}/{}/{}.md".format(job["benchmark"], results_dir, stem)
    json_rel = "{}/{}/{}-manifest.json".format(job["benchmark"], results_dir, stem)

    md_text = render_final(job, route, stage_records, status, operational_status, totals)
    manifest = {
        "schema": 1,
        "run_id": job["id"],
        "benchmark": job["benchmark"],
        "model": job["model"],
        "mode": "dynamic",
        "input_sha256": sha256_text(inputs["input_text"]),
        "prompt_sha256": sha256_text(inputs["prompt_text"]),
        "result_sha256": sha256_text(md_text),
        "status": status,
        "operational_status": operational_status,
        "created_at": now_z(),
        "agent_path": inputs["agent_path"],
        "agent_sha256": sha256_text(inputs["agent_text"]),
        "route": route,
        "route_status": route_result.get("status"),
        "route_usage": route_result.get("usage"),
        "stages": [
            {
                "index": r["index"],
                "skill": r["skill"],
                "skill_path": r["skill_path"],
                "skill_sha256": r["skill_sha256"],
                "status": r["status"],
                "usage": r.get("usage"),
                "output_sha256": sha256_text(r.get("text") or ""),
                "error": r.get("error"),
            }
            for r in stage_records
        ],
        "usage_totals": totals,
        "result_markdown": md_rel.rsplit("/", 1)[-1],
    }

    _, md_sha = get_text(args.repo, args.branch, md_rel, token, missing_ok=True)
    _, json_sha = get_text(args.repo, args.branch, json_rel, token, missing_ok=True)
    put_text(
        args.repo, args.branch, md_rel, md_text, token,
        "Publish dynamic Agent result {}".format(job["id"]), sha=md_sha
    )
    put_json(
        args.repo, args.branch, json_rel, manifest, token,
        "Publish dynamic Agent manifest {}".format(job["id"]), sha=json_sha
    )
    return {
        "markdown": md_rel,
        "manifest": json_rel,
        "status": status,
        "operational_status": operational_status,
    }


def process_job(args, token, api_key, job):
    inputs = load_dynamic_inputs(args, token, job)

    catalog = "\n".join("- `{}`".format(name) for name in inputs["ordered_names"])
    route_prompt = "\n\n".join([
        inputs["prompt_text"],
        "# Allowed Skill catalog\n" + catalog,
        "# Original source packet\n" + inputs["input_text"],
        "# Machine-readable routing contract\n" + ROUTE_CONTRACT,
    ])
    route_result = gemini(
        api_key,
        job["model"],
        route_prompt,
        strip_frontmatter(inputs["agent_text"]),
        timeout=args.timeout,
        api_base=args.api_base,
    )

    totals = {
        "prompt": usage_int(route_result.get("usage"), "promptTokenCount"),
        "candidate": usage_int(route_result.get("usage"), "candidatesTokenCount"),
        "thoughts": usage_int(route_result.get("usage"), "thoughtsTokenCount"),
        "total": usage_int(route_result.get("usage"), "totalTokenCount"),
    }

    if route_result.get("status") != "success":
        route = {
            "objective": "",
            "selected_skills": [],
            "not_selected": [],
            "stop_rules": [],
            "expected_final_artifact": "",
        }
        status = "operational_failure" if route_result.get("status") in OPERATIONAL_FAILURES else "failed"
        return publish_result(
            args, token, job, inputs, route, [], route_result,
            status, route_result.get("status"), totals
        )

    route = validate_route(parse_json_object(route_result.get("text") or ""), inputs)
    previous = None
    stage_records = []
    operational_status = None
    overall = "success"

    for index, name in enumerate(route["selected_skills"], 1):
        skill = inputs["allowed"][name]
        stage_prompt_parts = [
            EXECUTION_INSTRUCTION,
            "# Dynamic route\n" + json.dumps(route, indent=2, ensure_ascii=False),
            "# Original source packet\n" + inputs["input_text"],
        ]
        if previous is not None:
            stage_prompt_parts.append("# Upstream handoff artifact\n" + previous)
        else:
            stage_prompt_parts.append("# Upstream handoff artifact\n_No upstream Skill; this is the first selected capability._")
        stage_prompt_parts.append(
            "# Current invocation\nExecute the selected Skill `{}` now. Return only the resulting handoff artifact.".format(name)
        )
        result = gemini(
            api_key,
            job["model"],
            "\n\n".join(stage_prompt_parts),
            invocation_system(skill["text"], route),
            timeout=args.timeout,
            api_base=args.api_base,
        )
        usage = result.get("usage") or {}
        totals["prompt"] += usage_int(usage, "promptTokenCount")
        totals["candidate"] += usage_int(usage, "candidatesTokenCount")
        totals["thoughts"] += usage_int(usage, "thoughtsTokenCount")
        totals["total"] += usage_int(usage, "totalTokenCount")
        record = {
            "index": index,
            "skill": name,
            "skill_path": skill["path"],
            "skill_sha256": skill["sha256"],
            "status": result.get("status"),
            "usage": usage,
            "error": result.get("error"),
            "text": result.get("text") or "",
        }
        stage_records.append(record)
        print("[dynamic-worker] {} stage {}/{} {} -> {}".format(
            job["id"], index, len(route["selected_skills"]), name, result.get("status")
        ))
        if result.get("status") != "success":
            overall = "operational_failure" if result.get("status") in OPERATIONAL_FAILURES else "failed"
            operational_status = result.get("status") if result.get("status") in OPERATIONAL_FAILURES else None
            break
        previous = result.get("text") or ""

    return publish_result(
        args, token, job, inputs, route, stage_records, route_result,
        overall, operational_status, totals
    )


def parse_args(argv):
    parser = argparse.ArgumentParser(description="Execute dynamically routed Agent -> Skill jobs.")
    parser.add_argument("--repo", default=REPO)
    parser.add_argument("--branch", default=BRANCH)
    parser.add_argument("--root", default=ROOT)
    parser.add_argument("--env-file", default=ENV_FILE)
    parser.add_argument("--github-token-env", default=GITHUB_TOKEN_ENV)
    parser.add_argument("--dynamic-jobs", default=DYNAMIC_QUEUE)
    parser.add_argument("--state-file")
    parser.add_argument("--api-base", default=API_BASE)
    parser.add_argument("--timeout", type=int, default=180)
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv or sys.argv[1:])
    env = load_env(args.env_file)
    token = str(env.get(args.github_token_env) or "").strip()
    if not token:
        raise LabError("{} is required".format(args.github_token_env))
    api_key = resolve_api_key(env)

    state_path = Path(args.state_file) if args.state_file else Path(args.root) / STATE_REL
    state = read_local_json(state_path, {"schema": 1, "jobs": {}})
    jobs_state = state.get("jobs")
    if not isinstance(jobs_state, dict):
        jobs_state = {}
        state["jobs"] = jobs_state

    pending = []
    for raw in load_job_queue(args, token):
        job = normalize_job(raw)
        if job["enabled"] and job["id"] not in jobs_state:
            pending.append(job)

    if not pending:
        print("[dynamic-worker] no new jobs")
        return 0

    print("[dynamic-worker] {} new job(s)".format(len(pending)))
    for job in pending:
        print("[dynamic-worker] starting {} model={}".format(job["id"], job["model"]))
        record = {
            "attempted_at": now_z(),
            "model": job["model"],
            "benchmark": job["benchmark"],
            "dynamic_config": job["dynamic_config"],
        }
        try:
            result = process_job(args, token, api_key, job)
            record.update(result)
            print("[dynamic-worker] finished {} status={} operational={}".format(
                job["id"], result.get("status"), result.get("operational_status")
            ))
        except Exception as exc:
            record.update({"status": "worker_error", "error": str(exc)[:1000]})
            print("[dynamic-worker] {} worker_error: {}".format(job["id"], exc))
        jobs_state[job["id"]] = record
        write_local_json(state_path, state)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except LabError as exc:
        print("ERROR: {}".format(exc))
        raise SystemExit(2)
