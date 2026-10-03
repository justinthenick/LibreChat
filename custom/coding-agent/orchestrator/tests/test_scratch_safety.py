from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from coding_orchestrator.openhands_backend import (
    _validate_run_workspace,
    _validate_scratch_root,
)


class ScratchSafetyTests(unittest.TestCase):
    def test_invalid_nested_path_is_rejected_without_creating_ancestors(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory) / "repo"
            repo.mkdir()
            (repo / ".git").mkdir()
            with self.assertRaisesRegex(ValueError, "Git repository"):
                _validate_scratch_root(repo / "new" / "nested" / "scratch")
            self.assertFalse((repo / "new").exists())

    def test_symlink_ancestor_into_repository_is_rejected_before_creation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            repo = base / "repo"
            repo.mkdir()
            (repo / ".git").write_text("gitdir: elsewhere\n")
            link = base / "link"
            link.symlink_to(repo, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "Git repository"):
                _validate_scratch_root(link / "new" / "scratch")
            self.assertFalse((repo / "new").exists())

    def test_real_bare_repository_and_descendants_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory) / "bare.git"
            subprocess.run(
                ["git", "init", "--bare", "--quiet", str(repo)], check=True,
            )
            before = sorted(str(path.relative_to(repo)) for path in repo.rglob("*"))
            for scratch in (repo, repo / "new" / "nested"):
                with self.subTest(scratch=scratch):
                    with self.assertRaisesRegex(ValueError, "Git repository"):
                        _validate_scratch_root(scratch)
            after = sorted(str(path.relative_to(repo)) for path in repo.rglob("*"))
            self.assertEqual(after, before)

    def test_workspace_revalidates_bare_repository_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            workspace = root / "run"
            workspace.mkdir()
            subprocess.run(
                ["git", "init", "--bare", "--quiet", str(root)], check=True,
            )
            with self.assertRaisesRegex(ValueError, "Git repository"):
                _validate_run_workspace(workspace, root)


if __name__ == "__main__":
    unittest.main()
