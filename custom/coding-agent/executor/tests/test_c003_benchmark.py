import json
import re
import unittest
from pathlib import Path


CODING_AGENT_ROOT = Path(__file__).resolve().parents[2]
C003_ROOT = CODING_AGENT_ROOT / "benchmarks" / "C003-new-file-module-extraction"


class C003BenchmarkContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.benchmark = json.loads(
            (C003_ROOT / "benchmark.json").read_text(encoding="utf-8")
        )
        cls.task_prompt = (C003_ROOT / "task-prompt.md").read_text(encoding="utf-8")
        cls.gold = (C003_ROOT / "gold-standard.md").read_text(encoding="utf-8")
        cls.scorecard = (C003_ROOT / "scorecard.md").read_text(encoding="utf-8")
        cls.operator = (C003_ROOT / "OPERATOR.md").read_text(encoding="utf-8")
        cls.all_materials = "\n".join(
            [
                json.dumps(cls.benchmark, sort_keys=True),
                cls.task_prompt,
                cls.gold,
                cls.scorecard,
                cls.operator,
            ]
        )

    def test_benchmark_contract_is_closed_and_sanitized(self):
        self.assertEqual(
            set(self.benchmark),
            {
                "schema_version",
                "id",
                "name",
                "agent",
                "type",
                "repository_alias",
                "source_profile",
                "pass_threshold",
                "critical_penalties_allowed",
                "required_existing_file_changes",
                "required_new_files",
                "source_identifiers",
            },
        )
        self.assertEqual(self.benchmark["schema_version"], 1)
        self.assertEqual(self.benchmark["id"], "C003")
        self.assertEqual(self.benchmark["pass_threshold"], 90)
        self.assertEqual(self.benchmark["critical_penalties_allowed"], 0)
        self.assertNotIn("source_repository", self.benchmark)
        self.assertNotIn("source_commit", self.benchmark)
        self.assertNotRegex(self.all_materials, r"(?<![0-9a-f])[0-9a-f]{40,64}(?![0-9a-f])")
        self.assertNotRegex(self.all_materials, r"(?:https?://)?github\.com/")
        self.assertNotRegex(self.all_materials, r"\b[^\s@]+@[^\s@]+\.[^\s@]+\b")

    def test_required_file_boundary(self):
        self.assertEqual(
            set(self.benchmark["required_existing_file_changes"]),
            {"package.json", "popup.html", "popup.js"},
        )
        self.assertEqual(
            set(self.benchmark["required_new_files"]),
            {"synology-host.js", "tests/synology-host.test.mjs"},
        )
        for path in (
            *self.benchmark["required_existing_file_changes"],
            *self.benchmark["required_new_files"],
        ):
            with self.subTest(path=path):
                self.assertIn(path, self.task_prompt)
                self.assertIn(path, self.gold)

    def test_task_prompt_preserves_executor_boundary(self):
        for requirement in (
            "Create exactly one isolated task",
            "Run the existing test command before making changes",
            "complete `git_diff`",
            "Do not commit, push, merge or modify the source repository",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, self.task_prompt)

    def test_gold_standard_covers_new_file_and_validation_behavior(self):
        for requirement in (
            "malformed input",
            "non-HTTP(S) protocols",
            "embedded usernames or passwords",
            "non-root paths",
            "query strings",
            "fragments",
            "untruncated",
            "uncommitted and unpushed",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, self.gold)

    def test_scorecard_totals_one_hundred(self):
        points = [
            int(match.group(1))
            for match in re.finditer(r"^\|[^|]+\|\s*(\d+)\s*\|$", self.scorecard, re.MULTILINE)
        ]
        self.assertEqual(sum(points), 100)
        self.assertIn("Critical penalties allowed: **0**", self.scorecard)
        self.assertIn("required new files omitted", self.scorecard)

    def test_operator_procedure_keeps_private_baseline_local(self):
        self.assertIn("<approved-private-source-url>", self.operator)
        self.assertIn("Do not publish the source URL or commit", self.operator)
        self.assertIn("Do not promote the benchmark task", self.operator)


if __name__ == "__main__":
    unittest.main()
