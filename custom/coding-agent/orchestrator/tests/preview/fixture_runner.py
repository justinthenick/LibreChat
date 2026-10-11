"""Trusted, test-only ProcessWorker callable. Never contacts a provider."""
from __future__ import annotations

from dataclasses import dataclass
import time

from coding_orchestrator.evidence import EvidenceCollector


def fixture_evidence():
    return {
        "repository_alias": "fixture", "task": None, "checks": [],
        "final_diff": None, "final_status": None,
        "observed_checks_status": "not_run", "evidence_complete": False,
        "action_count": 0, "pending_count": 0, "errors": [],
    }


def collected_evidence(context):
    """Feed matched synthetic events to the real collector; execute no tools."""
    collector = EvidenceCollector(context.repository_alias)
    task_id = "http-fixture-1234abcd"
    branch = "agent/" + task_id
    events = [
        ("create_task", {"repository": context.repository_alias, "task_name": "HTTP fixture",
                         "task_mode": context.task_mode},
         {"task_id": task_id, "branch": branch, "task_branch": branch,
          "task_mode": context.task_mode, "source_repository": context.repository_alias,
          "source_ref": "HEAD", "source_branch": "main", "source_commit": "a" * 40,
          "source_status": "", "path": "/synthetic/private-task-path"}),
        ("run_check", {"task_id": task_id, "command": "synthetic-check"},
         {"command": "synthetic-check", "exit_code": 0, "truncated": False,
          "stdout": "synthetic-raw-stdout\n", "stderr": "synthetic-raw-stderr\n"}),
        ("git_diff", {"task_id": task_id},
         "diff --git a/example.py b/example.py\n+fixture\n"),
        ("task_status", {"task_id": task_id},
         {"task_id": task_id, "branch": branch, "status": " M example.py\n"}),
    ]
    for index, (tool, arguments, result) in enumerate(events, 1):
        identity = (f"action-{index}", f"call-{index}", tool)
        collector.record_action(*identity, arguments)
        collector.record_observation(*identity, is_error=False, result=result)
    return collector.snapshot()


def run(context, control):
    control.emit_progress({"evidence": fixture_evidence()})
    if context.prompt == "wait":
        while True:
            control._check()
            time.sleep(.01)
    if context.prompt not in {"finish", "finish-evidence"}:
        raise ValueError("Unknown synthetic fixture command")
    return {"execution_status": "finished", "final_response": "Synthetic fixture finished.",
            "evidence": collected_evidence(context) if context.prompt == "finish-evidence" else fixture_evidence()}


@dataclass(frozen=True)
class BoundRunner:
    runner: object
    claim: object

    def __call__(self, context, control):
        identity = self.claim.identity
        if (identity.execution_id != context.execution_id or identity.job_id != context.job_id
                or identity.repository_alias != context.repository_alias
                or identity.task_mode != context.task_mode or identity.user_id != "owner"
                or identity.tenant_id != "tenant"):
            raise ValueError("synthetic dispatch identity mismatch")
        return self.runner(context, control)
