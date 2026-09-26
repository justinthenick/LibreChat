from __future__ import annotations

import importlib.util
import os
import sys
import unittest
from pathlib import Path


def _load_bounded_module():
    current_dir = Path(__file__).resolve().parent
    bounded_path = (current_dir / ".." / "src" / "coding_executor" / "bounded.py").resolve()
    spec = importlib.util.spec_from_file_location("coding_executor.bounded", str(bounded_path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load spec for {bounded_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, bounded_path


bounded, BOUNDED_SOURCE_PATH = _load_bounded_module()


class TestBoundedExecution(unittest.TestCase):
    def test_loaded_module_path_is_task_source(self):
        self.assertTrue(hasattr(bounded, "__file__"))
        loaded_file = Path(bounded.__file__).resolve()
        self.assertEqual(loaded_file, BOUNDED_SOURCE_PATH)
        self.assertTrue(str(loaded_file).endswith("src/coding_executor/bounded.py"))

    def test_allowed_git_index_file_override_reaches_child(self):
        override_val = "/tmp/test_git_index_123"
        out = bounded.run(
            [sys.executable, "-c", "import os; print(os.environ.get('GIT_INDEX_FILE', ''))"],
            env_override={"GIT_INDEX_FILE": override_val},
        )
        self.assertEqual(out.strip(), override_val)

    def test_all_three_git_override_keys_accepted(self):
        overrides = {
            "GIT_INDEX_FILE": "/tmp/test_index",
            "GIT_OBJECT_DIRECTORY": "/tmp/test_obj",
            "GIT_ALTERNATE_OBJECT_DIRECTORIES": "/tmp/test_alt1:/tmp/test_alt2",
        }
        cmd = (
            "import os; print(';'.join([os.environ.get(k, '') for k in ("
            "'GIT_INDEX_FILE', 'GIT_OBJECT_DIRECTORY', 'GIT_ALTERNATE_OBJECT_DIRECTORIES'"
            ")]))"
        )
        out = bounded.run([sys.executable, "-c", cmd], env_override=overrides)
        expected = f"{overrides['GIT_INDEX_FILE']};{overrides['GIT_OBJECT_DIRECTORY']};{overrides['GIT_ALTERNATE_OBJECT_DIRECTORIES']}"
        self.assertEqual(out.strip(), expected)

    def test_arbitrary_key_rejected(self):
        with self.assertRaises(ValueError):
            bounded.run(
                [sys.executable, "-c", "print(1)"],
                env_override={"SECRET_TOKEN": "disallowed"},
            )

    def test_git_key_outside_allowlist_rejected(self):
        disallowed_git_keys = ["GIT_DIR", "GIT_WORK_TREE", "GIT_CONFIG", "GIT_AUTHOR_NAME"]
        for key in disallowed_git_keys:
            with self.subTest(key=key):
                with self.assertRaises(ValueError):
                    bounded.run(
                        [sys.executable, "-c", "print(1)"],
                        env_override={key: "/tmp/val"},
                    )

    def test_non_string_key_rejected(self):
        for invalid_key in (123, None, ("GIT_INDEX_FILE",), 3.14):
            with self.subTest(invalid_key=invalid_key):
                with self.assertRaises(TypeError):
                    bounded.run(
                        [sys.executable, "-c", "print(1)"],
                        env_override={invalid_key: "val"},
                    )

    def test_unrelated_host_secrets_absent_from_child(self):
        secret_var = "TEST_BOUNDED_SECRET_987654"
        secret_val = "sensitive_value_not_for_child"
        os.environ[secret_var] = secret_val
        try:
            out = bounded.run(
                [sys.executable, "-c", f"import os; print(os.environ.get({secret_var!r}, 'NOT_FOUND'))"]
            )
            self.assertEqual(out.strip(), "NOT_FOUND")
        finally:
            os.environ.pop(secret_var, None)

    def test_python_dont_write_bytecode_is_one(self):
        out = bounded.run(
            [sys.executable, "-c", "import os; print(os.environ.get('PYTHONDONTWRITEBYTECODE', ''))"]
        )
        self.assertEqual(out.strip(), "1")

    def test_run_without_overrides_retains_normal_behaviour(self):
        out = bounded.run([sys.executable, "-c", "print('bounded-ok')"])
        self.assertEqual(out.strip(), "bounded-ok")

    def test_output_limit_behaviour_unchanged(self):
        with self.assertRaises(RuntimeError) as cm:
            bounded.run(
                [sys.executable, "-c", "import sys; sys.stdout.write('A' * 200); sys.stdout.flush()"],
                limit=50,
            )
        self.assertIn("maintenance output limit exceeded", str(cm.exception))

    def test_timeout_behaviour_unchanged(self):
        with self.assertRaises(RuntimeError) as cm:
            bounded.run(
                [sys.executable, "-c", "import time; time.sleep(5)"],
                timeout=1,
            )
        self.assertIn("maintenance command timed out", str(cm.exception))

    def test_nonzero_child_failure_behaviour_unchanged(self):
        with self.assertRaises(RuntimeError) as cm:
            bounded.run([sys.executable, "-c", "import sys; sys.exit(2)"])
        self.assertIn("maintenance command failed", str(cm.exception))
