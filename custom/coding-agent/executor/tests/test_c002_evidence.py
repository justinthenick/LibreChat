import json
import re
import unittest
from pathlib import Path


CODING_AGENT_ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_PATH = (
    CODING_AGENT_ROOT
    / "benchmarks"
    / "C002-real-extension-regression"
    / "activation-evidence.json"
)

EXPECTED_TOP_LEVEL_KEYS = {
    "schema_version",
    "benchmark",
    "run_date",
    "source_profile",
    "generation_model",
    "executor_version",
    "results",
    "final_score",
    "critical_penalties",
    "defects",
    "gate_passed",
    "limitation",
    "privacy_note",
}

EXPECTED_RESULT_KEYS = {
    "approved_source_baseline_verified",
    "repository_discovered",
    "exactly_one_task_created",
    "repository_instructions_read",
    "initial_test_exit_code",
    "initial_failures",
    "changed_files",
    "ground_truth_corrections_matched",
    "post_change_test_exit_code",
    "post_change_validation",
    "task_status",
    "git_diff_check_passed",
    "source_and_task_base_match",
    "source_repository_unchanged",
    "committed",
    "pushed",
}

TRUE_CONTROLS = {
    "approved_source_baseline_verified",
    "repository_discovered",
    "exactly_one_task_created",
    "repository_instructions_read",
    "ground_truth_corrections_matched",
    "git_diff_check_passed",
    "source_and_task_base_match",
    "source_repository_unchanged",
}

FALSE_CONTROLS = {"committed", "pushed"}

FORBIDDEN_KEYS = {
    "source_repository",
    "source_commit",
    "approved_source_commit",
    "seeded_source_commit",
    "task_id",
    "conversation_id",
    "user_id",
    "username",
    "local_path",
    "absolute_path",
}

FORBIDDEN_TEXT_PATTERNS = {
    "commit-like hexadecimal identifier": re.compile(r"(?<![0-9a-f])[0-9a-f]{40,64}(?![0-9a-f])", re.IGNORECASE),
    "GitHub repository locator": re.compile(r"(?:https?://)?github\.com/", re.IGNORECASE),
    "Unix host path": re.compile(r"(?:^|[\s\"'])/(?:home|Users|volume\d+|mnt)/", re.IGNORECASE),
    "Windows host path": re.compile(r"\b[A-Z]:\\", re.IGNORECASE),
    "email address": re.compile(r"\b[^\s@]+@[^\s@]+\.[^\s@]+\b"),
}


class C002EvidenceContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evidence = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
        cls.serialized = json.dumps(cls.evidence, sort_keys=True)

    def test_schema_is_closed_and_expected(self):
        self.assertEqual(set(self.evidence), EXPECTED_TOP_LEVEL_KEYS)
        self.assertEqual(set(self.evidence["results"]), EXPECTED_RESULT_KEYS)
        self.assertTrue(FORBIDDEN_KEYS.isdisjoint(self.evidence))
        self.assertTrue(FORBIDDEN_KEYS.isdisjoint(self.evidence["results"]))

    def test_benchmark_outcome_meets_gate(self):
        self.assertEqual(self.evidence["schema_version"], 1)
        self.assertEqual(self.evidence["benchmark"], "C002")
        self.assertEqual(self.evidence["final_score"], 100)
        self.assertEqual(self.evidence["critical_penalties"], 0)
        self.assertEqual(self.evidence["defects"], 0)
        self.assertIs(self.evidence["gate_passed"], True)

    def test_execution_and_isolation_controls(self):
        results = self.evidence["results"]
        for control in TRUE_CONTROLS:
            with self.subTest(control=control):
                self.assertIs(results[control], True)
        for control in FALSE_CONTROLS:
            with self.subTest(control=control):
                self.assertIs(results[control], False)

        self.assertEqual(results["initial_test_exit_code"], 1)
        self.assertEqual(results["post_change_test_exit_code"], 0)
        self.assertEqual(set(results["changed_files"]), {"package.json", "popup.html"})
        self.assertEqual(
            results["post_change_validation"],
            "Extension validation passed (8 referenced files checked, 15 popup IDs checked).",
        )

    def test_private_identifiers_are_absent(self):
        for label, pattern in FORBIDDEN_TEXT_PATTERNS.items():
            with self.subTest(pattern=label):
                self.assertIsNone(pattern.search(self.serialized), label)

        self.assertIn("intentionally omitted", self.evidence["privacy_note"])


if __name__ == "__main__":
    unittest.main()
