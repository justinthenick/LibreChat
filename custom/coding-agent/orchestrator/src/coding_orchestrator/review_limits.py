"""Review-only input and output acceptance budgets."""

import json

from .pr_review import ReviewError

MAX_DIFF_BYTES = 20_000
MAX_RESPONSE_BYTES = 64_000
MAX_JSON_DEPTH = 8


def validate_input(diff: str) -> None:
    if len(diff.encode("utf-8")) > MAX_DIFF_BYTES:
        raise ReviewError("Review input budget exceeded")


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ReviewError("Duplicate review JSON field")
        result[key] = value
    return result


def _reject_constant(value):
    raise ReviewError("Non-finite review JSON number")


def parse_report(answer: str) -> dict:
    if not isinstance(answer, str):
        raise ReviewError("Review response must be text")
    try:
        size = len(answer.encode("utf-8"))
    except UnicodeEncodeError:
        raise ReviewError("Review response contains invalid Unicode") from None
    if size > MAX_RESPONSE_BYTES:
        raise ReviewError("Review response exceeds size limit")

    depth = 0
    quoted = escaped = False
    for character in answer:
        if quoted:
            if escaped:
                escaped = False
            elif character == chr(92):
                escaped = True
            elif character == '"':
                quoted = False
        elif character == '"':
            quoted = True
        elif character in "[{":
            depth += 1
            if depth > MAX_JSON_DEPTH:
                raise ReviewError("Review JSON nesting exceeds limit")
        elif character in "]}":
            depth -= 1
    try:
        return json.loads(
            answer, object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
    except (ValueError, RecursionError):
        raise ReviewError("Review response is not valid JSON") from None
