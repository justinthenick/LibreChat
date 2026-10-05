import importlib.util
import os
from pathlib import Path
import stat
import tempfile
import subprocess
import sys
from unittest.mock import patch
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("secure_worker", HERE / "admin-settings-worker.py")
worker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(worker)


class RecoveryStorageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.directory = self.root / "private-recovery"
        self.marker = self.directory / "recovery-required.json"
        self.victim = self.root / "victim"
        self.victim.write_text("must remain intact")
        self.victim.chmod(0o644)

    def assert_victim_intact(self):
        self.assertEqual(self.victim.read_text(), "must remain intact")
        self.assertEqual(stat.S_IMODE(self.victim.stat().st_mode), 0o644)

    def test_preplanted_temporary_symlink_cannot_truncate_or_chmod_target(self):
        self.directory.mkdir(mode=0o700)
        (self.directory / "recovery-required.json.tmp").symlink_to(self.victim)
        worker.write_recovery(self.marker, {"stage": "test"})
        self.assert_victim_intact()

    def test_recovery_directory_is_private_not_panel_state(self):
        worker.write_recovery(self.marker, {"stage": "test"})
        self.assertEqual(stat.S_IMODE(self.directory.stat().st_mode), 0o700)
        self.assertEqual(stat.S_IMODE(self.marker.stat().st_mode), 0o600)
        core = worker.WorkerCore(self.root / ".env", HERE / "admin-settings.schema.json", self.root / "panel-state")
        self.assertEqual(core.recovery_dir, Path("/var/lib/librechat-admin-settings"))

    def test_group_writable_directory_is_rejected_without_chmod(self):
        self.directory.mkdir(mode=0o770)
        self.directory.chmod(0o770)
        with self.assertRaises(worker.WorkerError):
            worker.write_recovery(self.marker, {})
        self.assertEqual(stat.S_IMODE(self.directory.stat().st_mode), 0o770)
        self.assertFalse(self.marker.exists())

    def test_directory_symlink_is_rejected(self):
        target = self.root / "panel-state"
        target.mkdir(mode=0o700)
        self.directory.symlink_to(target, target_is_directory=True)
        with self.assertRaises(worker.WorkerError):
            worker.write_recovery(self.marker, {})
        self.assertFalse((target / self.marker.name).exists())

    def test_symlink_in_ancestor_is_rejected(self):
        target = self.root / "actual"
        target.mkdir(mode=0o700)
        alias = self.root / "alias"
        alias.symlink_to(target, target_is_directory=True)
        with self.assertRaises(worker.WorkerError):
            worker.write_recovery(alias / "private" / self.marker.name, {})
        self.assertFalse((target / "private").exists())

    def test_symlink_or_hardlink_marker_is_rejected_without_touching_target(self):
        self.directory.mkdir(mode=0o700)
        for link in (lambda: self.marker.symlink_to(self.victim), lambda: os.link(self.victim, self.marker)):
            link()
            try:
                with self.assertRaises(worker.WorkerError):
                    worker.write_recovery(self.marker, {})
                self.assert_victim_intact()
            finally:
                self.marker.unlink()

    def test_presence_check_rejects_dangling_link_and_delete_does_not_follow_it(self):
        self.directory.mkdir(mode=0o700)
        self.marker.symlink_to(self.root / "missing")
        with self.assertRaises(worker.WorkerError):
            worker.recovery_pending(self.directory)
        with self.assertRaises(worker.WorkerError):
            worker.clear_recovery(self.marker)
        self.assertTrue(self.marker.is_symlink())

    def test_shared_group_cannot_unlink_hold_through_socket_directory(self):
        state = self.root / "panel-state"
        state.mkdir(mode=0o770)
        worker.write_recovery(self.marker, {})
        self.assertFalse((state / self.marker.name).exists())
        self.assertEqual(self.directory.stat().st_mode & 0o077, 0)
        self.assertTrue(worker.recovery_pending(self.directory))
        worker.clear_recovery(self.marker)
        self.assertFalse(worker.recovery_pending(self.directory))

    def test_wrong_owner_is_rejected_without_mutating_storage(self):
        self.directory.mkdir(mode=0o700)
        with patch.object(worker.os, "geteuid", return_value=os.geteuid() + 1):
            with self.assertRaises(worker.WorkerError):
                worker.write_recovery(self.marker, {})
        self.assertFalse(self.marker.exists())

    def test_read_only_cli_fails_closed_without_reading_env_or_creating_state(self):
        command = [sys.executable, str(HERE / "admin-settings-worker.py"),
                   "--env-file", str(self.root / "no-env"), "--schema", str(self.root / "no-schema"),
                   "--recovery-dir", str(self.directory), "recovery-status"]
        self.assertEqual(subprocess.run(command, capture_output=True).returncode, 0)
        self.assertFalse(self.directory.exists())
        self.directory.mkdir(mode=0o700)
        self.marker.symlink_to(self.root / "missing")
        self.assertEqual(subprocess.run(command, capture_output=True).returncode, 2)
        self.assertTrue(self.marker.is_symlink())

    def test_state_exposes_only_hold_boolean_and_fails_closed_for_unsafe_storage(self):
        env = self.root / ".env"
        env.write_text("SEARCH=false\n")
        core = worker.WorkerCore(env, HERE / "admin-settings.schema.json", self.root / "panel", self.directory)
        self.assertFalse(core.state()["recovery_required"])
        worker.write_recovery(self.marker, {"private": "must-not-reach-browser"})
        state = core.state()
        self.assertTrue(state["recovery_required"])
        self.assertNotIn("must-not-reach-browser", str(state))
        self.directory.chmod(0o770)
        self.assertTrue(core.state()["recovery_required"])


if __name__ == "__main__":
    unittest.main()
