"""Dormant translation of SDK tool arguments into the closed workspace contract.

The embedding host supplies the authenticated persisted claim and stable SDK
call identity. Neither may be extracted from model-controlled tool arguments.
No listener, credential discovery or profile registration is performed here.
"""
from .dispatch import FencedWorkspace
from .executions import ExecutionConflict


class SDKWorkspace:
    def __init__(self, workspace: FencedWorkspace):
        self.workspace = workspace
        self.commands = {command: alias for alias, command in workspace.checks.items()}
        if len(self.commands) != len(workspace.checks):
            raise ValueError("check commands must have unique aliases")

    def dispatch(self, claim, action_id, operation, arguments):
        self.workspace._authorized(claim)
        if type(arguments) is not dict:
            raise ValueError("SDK arguments must be an object")
        arguments = dict(arguments)
        if operation == "create_task":
            if (set(arguments) - {"repository", "task_name", "task_mode", "base_ref"}
                    or arguments.get("repository") != claim.identity.repository_alias
                    or arguments.get("task_mode") != "read_only"
                    or type(arguments.get("task_name")) is not str
                    or not arguments["task_name"] or len(arguments["task_name"]) > 128
                    or arguments.get("base_ref", "HEAD") != "HEAD"):
                raise ExecutionConflict("SDK repository scope mismatch")
            arguments = {}
        else:
            task = self.workspace.ledger.task_for(claim)
            if task is None or arguments.pop("task_id", None) != task:
                raise ExecutionConflict("SDK task ownership mismatch")
            if operation == "run_check":
                if set(arguments) != {"command"} or type(arguments["command"]) is not str:
                    raise ValueError("fixed SDK check required")
                alias = self.commands.get(arguments["command"])
                if alias is None:
                    raise ExecutionConflict("SDK check is not configured")
                arguments = {"check": alias}
        return self.workspace.dispatch(claim, action_id, operation, arguments)
