from enum import Enum


class PolicyReason(Enum):
    REPOSITORY = (
        "maintenance_repository_not_allowed: This repository is not allowlisted for maintenance. "
        "Executor repository discovery does not grant maintenance access. "
        "Stop and report this permission blocker; do not create a task or substitute another tool to inspect it."
    )
    DISABLED = (
        "maintenance_operation_disabled: This operation is disabled by operator policy. "
        "Stop and report this permission blocker; do not retry through another tool."
    )


class PolicyRefusal(ValueError):
    def __init__(self, reason: PolicyReason):
        self.reason = PolicyReason(reason)
        super().__init__(self.reason.value)
