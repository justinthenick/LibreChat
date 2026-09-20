from __future__ import annotations

import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVER = ROOT / "src/coding_executor/server.py"
WORKSPACES = ROOT / "src/coding_executor/workspaces.py"


def return_annotation(path: Path, function_name: str) -> str:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    matches = [
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == function_name
    ]
    if len(matches) != 1:
        raise AssertionError(
            f"{path.name}:{function_name} expected one function, found {len(matches)}"
        )
    return ast.unparse(matches[0].returns)


class ServerContractTest(unittest.TestCase):
    def test_structured_task_status_return_contracts(self) -> None:
        self.assertEqual(
            return_annotation(SERVER, "task_status"),
            "dict[str, object]",
        )
        self.assertEqual(
            return_annotation(SERVER, "apply_patch"),
            "dict[str, object]",
        )
        self.assertEqual(
            return_annotation(WORKSPACES, "task_status"),
            "dict[str, object]",
        )
        self.assertEqual(
            return_annotation(WORKSPACES, "apply_patch"),
            "dict[str, object]",
        )


if __name__ == "__main__":
    unittest.main()
