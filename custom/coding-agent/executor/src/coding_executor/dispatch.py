"""Dormant claim-bound workspace dispatch. No server registration or credential discovery."""
from dataclasses import asdict
import hashlib
import json

from .coordination import maintenance_lock
from .executions import Claim, ExecutionConflict, ExecutionService
from .workspaces import WorkspaceManager


class FencedWorkspace:
    """Trusted host supplies authenticated claims and grants; frames cannot grant access.

    One existing ledger owns attempts, action receipts and task binding. This adapter
    adds no attempt registry. The supervisor must independently establish exact
    quiescence; workspace return, caller timeout and process exit are not stop proof.
    """

    def __init__(self, ledger: ExecutionService, manager: WorkspaceManager, *, authorize,
                 checks=None, enabled=False):
        if type(enabled) is not bool or not callable(authorize):
            raise ValueError("explicit dispatch policy required")
        self.ledger, self.manager, self.authorize = ledger, manager, authorize
        self.enabled = enabled
        self.checks = dict(checks or {})
        if any(type(k) is not str or type(v) is not str for k, v in self.checks.items()):
            raise ValueError("fixed check aliases required")

    def _authorized(self, claim):
        if (not self.enabled or type(claim) is not Claim or claim.identity.task_mode != "read_only"
                or self.authorize(claim.identity) is not True):
            raise ExecutionConflict("workspace dispatch disabled or unauthorized")

    def admit(self, claim, *, max_requests, timeout_seconds, deadline_monotonic=None):
        self._authorized(claim)
        self.ledger.configure_dispatch(claim, max_requests=max_requests, timeout_seconds=timeout_seconds,
                                       deadline_monotonic=deadline_monotonic)

    def dispatch(self, claim, action_id, operation, arguments):
        self._authorized(claim)
        shapes = {
            "create_task": {}, "task_status": {}, "git_diff": {},
            "list_files": {"path": str, "max_results": int},
            "read_file": {"path": str, "start_line": int, "end_line": int},
            "search_text": {"query": str, "path": str, "glob": str, "max_results": int},
            "run_check": {"check": str},
        }
        if (type(operation) is not str or operation not in shapes or type(arguments) is not dict
                or set(arguments) - set(shapes[operation])
                or any(type(value) is not shapes[operation][key] for key, value in arguments.items())
                or operation == "read_file" and "path" not in arguments
                or operation == "search_text" and "query" not in arguments
                or operation == "run_check" and arguments.get("check") not in self.checks):
            raise ValueError("invalid closed workspace request")
        encoded = json.dumps([operation, arguments], sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
        if len(encoded) > 49152:
            raise ValueError("workspace request exceeds bound")
        # Snapshot request data before starting the owned action thread.
        operation, arguments = json.loads(encoded)

        def execute(remaining):
            with maintenance_lock(self.manager.task_root):
                task = self.ledger.task_for(claim)
                if operation == "create_task":
                    if task is not None:
                        raise ExecutionConflict("claim already has a task")
                    result = self.manager.create_task(claim.identity.repository_alias,
                        "preview-" + claim.attempt_id[:40], task_mode="read_only")
                    self.ledger.bind_task(claim, result["task_id"])
                    return result
                if task is None:
                    raise ExecutionConflict("claim has no task")
                if operation == "run_check":
                    return asdict(self.manager.run_check(task, self.checks[arguments["check"]],
                                                        timeout_seconds=remaining))
                method = "diff" if operation == "git_diff" else operation
                return getattr(self.manager, method)(task, **arguments)

        return self.ledger.dispatch(claim, action_id, hashlib.sha256(encoded).hexdigest(), execute)
