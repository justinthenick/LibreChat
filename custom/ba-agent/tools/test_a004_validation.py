"""Regression checks for selective invocation and trustworthy A/B scoring."""
import copy
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import dynamic_agent_worker as dynamic
import semantic_evaluator as evaluator
import semantic_reviser as reviser
from lab_common import LabError, sha256_text


class ValidationTests(unittest.TestCase):
    def setUp(self):
        self.job = {"generation_model": "test-model", "baseline_mode": "pipeline", "skill_mode": "dynamic"}
        common = {"status": "success", "model": "test-model", "input_sha256": sha256_text("source"),
                  "stages": [{"status": "success"}]}
        self.meta = {"baseline": dict(common, pipeline="fixed"),
                     "skill": dict(common, mode="dynamic", route_status="success")}

    def validate(self, meta=None):
        evaluator.validate_pair(meta or self.meta, self.job, "source", "baseline", "candidate")

    def test_valid_fixed_control_and_dynamic_pair(self):
        self.validate()

    def test_reject_failed_mismatched_or_unverifiable_runs(self):
        cases = [("status", "failed"), ("model", "other"), ("input_sha256", None),
                 ("input_sha256", sha256_text("changed")), ("mode", "wrong"),
                 ("stages", []), ("stages", [{"status": "failed"}]),
                 ("result_sha256", sha256_text("different artifact"))]
        for side in ("baseline", "skill"):
            for field, value in cases:
                with self.subTest(side=side, field=field, value=value):
                    meta = copy.deepcopy(self.meta)
                    meta[side][field] = value
                    with self.assertRaises(LabError):
                        self.validate(meta)

    def test_missing_model_and_failed_route_rejected(self):
        with self.assertRaises(LabError):
            evaluator.validate_pair(self.meta, {}, "source", "baseline", "candidate")
        self.meta["skill"]["route_status"] = "failed"
        with self.assertRaises(LabError):
            self.validate()

    def test_scope_required_for_downstream_route(self):
        inputs = {"config": {"require_active_delta_scope": True},
                  "allowed": {"derive-test-cases": {}}, "max_steps": 1}
        for rules in ([], ["ACTIVE_DELTA_SCOPE: "], ["ACTIVE_DELTA_SCOPE: R2"] * 2):
            with self.subTest(rules=rules), self.assertRaises(LabError):
                dynamic.validate_route({"selected_skills": ["derive-test-cases"], "stop_rules": rules}, inputs)
        route = dynamic.validate_route({"selected_skills": ["derive-test-cases"],
                                        "stop_rules": ["ACTIVE_DELTA_SCOPE: R2 only"]}, inputs)
        system = dynamic.invocation_system("---\nname: test\n---\nCover requirements.", route)
        self.assertIn("ACTIVE_DELTA_SCOPE: R2 only", system)
        self.assertIn("unchanged by reference", system)
        self.assertNotIn("name: test", system)

    def test_unscoped_agents_preserve_existing_instruction(self):
        self.assertEqual(dynamic.invocation_system("instruction", {"stop_rules": []}), "instruction")

    def test_terminal_processing_errors_reach_scheduler(self):
        for module in (evaluator, reviser):
            with self.subTest(module=module.__name__), tempfile.TemporaryDirectory() as root:
                args = SimpleNamespace(repo="repo", branch="lab", root=root, env_file="unused",
                                       github_token_env="TOKEN", semantic_jobs="q", revision_jobs="q")
                with patch.object(module.argparse.ArgumentParser, "parse_args", return_value=args), \
                     patch.object(module, "load_env", return_value={"TOKEN": "test"}), \
                     patch.object(module, "resolve_api_key", return_value="test"), \
                     patch.object(module, "get_json", return_value=({"jobs": [{"id": "job"}]}, "sha")), \
                     patch.object(module, "process", side_effect=LabError("external write failed")):
                    self.assertEqual(module.main(), 2)
                self.assertTrue(list(Path(root).rglob("*-state.json")))


if __name__ == "__main__":
    unittest.main()
