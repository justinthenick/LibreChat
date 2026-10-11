"""Bounded evidence from paired executor events; agent prose is never evidence."""
from __future__ import annotations

import hashlib
import json
import re
from threading import RLock


_TOOLS = frozenset({"list_repositories", "create_task", "task_status", "list_files",
                    "read_file", "search_text", "apply_patch", "run_check", "git_diff", "finish"})
_KEYS = {
    "list_repositories": set(), "create_task": {"repository", "task_name", "base_ref", "task_mode"},
    "task_status": {"task_id"}, "git_diff": {"task_id"},
    "list_files": {"task_id", "path", "max_results"},
    "read_file": {"task_id", "path", "start_line", "end_line"},
    "search_text": {"task_id", "query", "path", "glob", "max_results"},
    "apply_patch": {"task_id", "patch"},
    "run_check": {"task_id", "command", "timeout_seconds"}, "finish": {"message"},
}
_ID = re.compile(r"[A-Za-z0-9_.:-]{1,128}\Z")
_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}\Z")
_REF = re.compile(r"[A-Za-z0-9][A-Za-z0-9._/@{}^~-]{0,199}\Z")


class EvidenceError(ValueError):
    """The message is a fixed code, never an event or executor payload."""


class EvidenceCollector:
    def __init__(self, repository_alias: str, max_actions: int = 32):
        self._errors: set[str] = set()
        self._lock = RLock()
        self._require(type(repository_alias) is str and bool(_NAME.fullmatch(repository_alias)),
                      "invalid_repository")
        self._require(type(max_actions) is int and 1 <= max_actions <= 32, "invalid_action_limit")
        self.repository_alias, self.max_actions = repository_alias, max_actions
        self._actions: dict[str, dict] = {}
        self._calls: set[str] = set()
        self._pending: set[str] = set()
        self._task: dict | None = None
        self._checks: list[dict] = []
        self._diff: dict | None = None
        self._status: dict | None = None
        self._sequence = self._last_mutation = 0
        self._created = False
        self._check_error = False

    def _require(self, condition: bool, code: str) -> None:
        if not condition:
            self._errors.add(code)
            raise EvidenceError(code) from None

    def _text(self, value: object, limit: int, *, empty: bool = True) -> str:
        self._require(type(value) is str, "malformed_payload")
        try:
            size = len(value.encode("utf-8"))
        except UnicodeError:
            self._require(False, "malformed_payload")
        self._require(size <= limit, "payload_too_large")
        self._require(empty or bool(value), "malformed_payload")
        return value

    def _json(self, value: object, limit: int = 524288) -> str:
        try:
            encoded = json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
        except (TypeError, ValueError, RecursionError, OverflowError):
            self._require(False, "malformed_payload")
        self._text(encoded, limit)
        return encoded

    def record_action(self, action_id: str, tool_call_id: str, tool_name: str, arguments: dict) -> None:
        with self._lock:
            self._require(type(tool_name) is str and tool_name in _TOOLS, "unexpected_tool")
            self._require(all(type(v) is str and _ID.fullmatch(v) for v in (action_id, tool_call_id)),
                          "invalid_identity")
            self._require(action_id not in self._actions and tool_call_id not in self._calls,
                          "duplicate_action")
            self._require(len(self._actions) < self.max_actions, "action_limit")
            self._json(arguments)
            self._require(type(arguments) is dict and set(arguments) <= _KEYS[tool_name], "malformed_arguments")
            retained = {}
            if tool_name == "create_task":
                self._require(not self._created and arguments.get("repository") == self.repository_alias,
                              "task_identity_mismatch")
                self._text(arguments.get("task_name"), 200, empty=False)
                ref = self._text(arguments.get("base_ref", "HEAD"), 200, empty=False)
                self._require(bool(_REF.fullmatch(ref)), "malformed_arguments")
                mode = arguments.get("task_mode", "modification")
                self._require(mode in ("modification", "read_only"), "malformed_arguments")
                retained = {"source_ref": ref, "task_mode": mode}
            elif tool_name not in {"finish", "list_repositories"}:
                self._require(self._task is not None and arguments.get("task_id") == self._task["task_id"],
                              "task_identity_mismatch")
            if tool_name == "run_check":
                command = self._text(arguments.get("command"), 512, empty=False)
                self._require(command.isprintable(), "malformed_arguments")
                retained["command"] = command
            if tool_name == "apply_patch":
                self._text(arguments.get("patch"), 262144, empty=False)
            if tool_name == "finish":
                self._text(arguments.get("message"), 16384)
            for key in ("path", "query", "glob"):
                if key in arguments or (tool_name == "read_file" and key == "path") or (tool_name == "search_text" and key == "query"):
                    self._text(arguments.get(key), 1024, empty=key != "query" and tool_name != "read_file")
            for key in ("start_line", "end_line", "max_results", "timeout_seconds"):
                if key in arguments and not (key == "timeout_seconds" and arguments[key] is None):
                    self._require(type(arguments[key]) is int and 1 <= arguments[key] <= 1_000_000,
                                  "malformed_arguments")
            if tool_name == "read_file":
                self._require(arguments.get("start_line", 1) <= arguments.get("end_line", 400), "malformed_arguments")
            self._sequence += 1
            self._actions[action_id] = {"action_id": action_id, "tool_call_id": tool_call_id,
                                        "tool_name": tool_name, "started": self._sequence, **retained}
            self._calls.add(tool_call_id)
            self._pending.add(action_id)
            if tool_name in {"create_task", "apply_patch"}:
                self._last_mutation = self._sequence
            self._created |= tool_name == "create_task"

    def _task_metadata(self, result: dict, action: dict) -> dict:
        task_id = self._text(result.get("task_id"), 80, empty=False)
        self._require(bool(_NAME.fullmatch(task_id)) and ".." not in task_id, "invalid_task_metadata")
        branch = "agent/" + task_id
        self._require(result.get("branch") == branch and result.get("task_branch") == branch,
                      "invalid_task_metadata")
        self._require(result.get("source_repository") == self.repository_alias and
                      result.get("source_status") == "", "invalid_task_metadata")
        commit = self._text(result.get("source_commit"), 40)
        self._require(bool(re.fullmatch(r"[0-9a-fA-F]{40}", commit)), "invalid_task_metadata")
        source_branch = self._text(result.get("source_branch"), 200)
        self._require(not source_branch or bool(_REF.fullmatch(source_branch)), "invalid_task_metadata")
        self._require(result.get("source_ref") == action["source_ref"] and
                      result.get("task_mode") == action["task_mode"], "invalid_task_metadata")
        return {key: result[key] for key in ("task_id", "branch", "task_branch", "task_mode",
                "source_repository", "source_ref", "source_branch", "source_commit", "source_status")}

    def _task_status(self, result: dict) -> dict:
        self._require(self._task is not None and result.get("task_id") == self._task["task_id"] and
                      result.get("branch") == self._task["branch"], "task_identity_mismatch")
        status = self._text(result.get("status"), 4096)
        self._json(status, 8192)
        return {"task_id": self._task["task_id"], "branch": self._task["branch"], "status": status}

    def record_observation(self, action_id: str, tool_call_id: str, tool_name: str, *,
                           is_error: bool, result: object) -> None:
        with self._lock:
            self._require(type(action_id) is str and action_id in self._actions, "unmatched_observation")
            action = self._actions[action_id]
            self._require(action_id in self._pending, "duplicate_observation")
            self._require(action["tool_call_id"] == tool_call_id and action["tool_name"] == tool_name,
                          "observation_mismatch")
            self._require(type(is_error) is bool, "malformed_payload")
            self._json(result)
            self._sequence += 1
            if tool_name in {"create_task", "apply_patch"}:
                self._last_mutation = self._sequence
            if is_error:
                self._pending.remove(action_id)
                self._errors.add("tool_error")
                self._check_error |= tool_name == "run_check"
                return
            if type(result) is dict and set(result) == {"result"}:
                result = result["result"]
            proof = {key: action[key] for key in ("action_id", "tool_call_id", "started")}
            proof["completed"] = self._sequence
            if tool_name in {"create_task", "task_status", "apply_patch", "run_check"}:
                self._require(type(result) is dict, "malformed_payload")
            if tool_name == "create_task":
                self._task = self._task_metadata(result, action)
            elif tool_name in {"task_status", "apply_patch"}:
                status = self._task_status(result)
                if tool_name == "task_status":
                    self._status = {**status, **proof}
            elif tool_name == "run_check":
                self._require(result.get("command") == action["command"] and
                              type(result.get("exit_code")) is int and
                              -255 <= result["exit_code"] <= 255 and
                              type(result.get("truncated")) is bool, "invalid_check")
                hashes = {name + "_sha256": hashlib.sha256(self._text(result.get(name), 65536).encode()).hexdigest()
                          for name in ("stdout", "stderr")}
                self._checks.append({"command": action["command"], "exit_code": result["exit_code"],
                                     "truncated": result["truncated"], **hashes, **proof})
            elif tool_name == "git_diff":
                diff = self._text(result, 65536)
                self._json(diff, 65540)
                self._diff = {"text": diff, "sha256": hashlib.sha256(diff.encode()).hexdigest(), **proof}
            elif tool_name in {"read_file", "search_text"}:
                self._text(result, 262144)
            elif tool_name in {"list_files", "list_repositories"}:
                self._require(type(result) is list and all(type(item) is str for item in result), "malformed_payload")
            self._pending.remove(action_id)

    def snapshot(self) -> dict:
        """Return detached observed evidence, without claiming overall task success."""
        with self._lock:
            latest = {check["command"]: check for check in sorted(self._checks, key=lambda c: c["started"])}
            pending_checks = any(self._actions[key]["tool_name"] == "run_check" for key in self._pending)
            current = [check for check in latest.values() if check["started"] > self._last_mutation]
            if any(check["exit_code"] != 0 for check in current):
                checks_status = "failed"
            elif self._check_error or pending_checks or len(current) != len(latest) or any(c["truncated"] for c in current):
                checks_status = "incomplete"
            else:
                checks_status = "passed" if current else "not_run"
            complete = bool(self._task and self._diff and self._status and not self._pending and not self._errors
                            and self._diff["started"] > self._last_mutation
                            and self._status["started"] > self._last_mutation)
            value = {"repository_alias": self.repository_alias, "task": self._task, "checks": self._checks,
                     "final_diff": self._diff, "final_status": self._status,
                     "observed_checks_status": checks_status, "evidence_complete": complete,
                     "action_count": len(self._actions), "pending_count": len(self._pending),
                     "errors": sorted(self._errors)}
            return json.loads(self._json(value, 131072))

    def on_event(self, event: object) -> None:
        """Adapt real pinned SDK events; importing this module needs no SDK."""
        from openhands.sdk.event import ActionEvent, ObservationEvent
        from openhands.sdk.llm import TextContent
        from openhands.sdk.mcp.definition import MCPToolAction, MCPToolObservation
        from openhands.sdk.tool.builtins.finish import FinishAction, FinishObservation

        with self._lock:
            if isinstance(event, ActionEvent):
                self._require(event.tool_call.id == event.tool_call_id and event.tool_call.name == event.tool_name,
                              "action_mismatch")
                if event.tool_name == "finish":
                    self._require(isinstance(event.action, FinishAction), "malformed_action")
                    arguments = {"message": event.action.message}
                else:
                    self._require(isinstance(event.action, MCPToolAction), "malformed_action")
                    arguments = event.action.data
                self.record_action(event.id, event.tool_call_id, event.tool_name, arguments)
            elif isinstance(event, ObservationEvent):
                observation = event.observation
                if event.tool_name == "finish":
                    self._require(isinstance(observation, FinishObservation), "malformed_observation")
                    self._require(all(isinstance(c, TextContent) for c in observation.content), "malformed_observation")
                    self._json([c.text for c in observation.content], 32768)
                    result = None
                else:
                    self._require(isinstance(observation, MCPToolObservation), "malformed_observation")
                    self._require(observation.tool_name == event.tool_name, "observation_mismatch")
                    content = observation.content
                    self._require(1 <= len(content) <= 1001 and all(isinstance(c, TextContent) for c in content),
                                  "malformed_observation")
                    self._require(content[0].text == f"[Tool '{event.tool_name}' executed.]", "malformed_observation")
                    texts = [c.text for c in content[1:]]
                    self._json(texts)
                    if len(texts) == 1:
                        try:
                            result = json.loads(texts[0], object_pairs_hook=self._unique_object)
                        except EvidenceError:
                            raise
                        except (ValueError, RecursionError):
                            self._require(event.tool_name in {"read_file", "search_text", "git_diff", "list_files",
                                                            "list_repositories"} or observation.is_error, "malformed_payload")
                            result = texts[0]
                        if event.tool_name in {"list_files", "list_repositories"} and type(result) not in {dict, list}:
                            result = [result if type(result) is str else texts[0]]
                    else:
                        result = texts
                self.record_observation(event.action_id, event.tool_call_id, event.tool_name,
                                        is_error=observation.is_error, result=result)

    def _unique_object(self, pairs: list[tuple[str, object]]) -> dict:
        self._require(len({key for key, _ in pairs}) == len(pairs), "malformed_payload")
        return dict(pairs)
