import os
import unittest
from unittest.mock import patch

from coding_orchestrator.review_cli import _DIAGNOSTIC_STAGES, _worker_stage


class ReviewDiagnosticTests(unittest.TestCase):
    def test_disabled_by_default_and_requires_exact_fd(self):
        for setting in [None, '', '4', '03', 'CANARY']:
            env = {} if setting is None else {'CODING_REVIEW_STAGE_FD': setting}
            with patch.dict(os.environ, env, clear=True), patch('os.write') as write:
                _worker_stage('provider_ready')
                write.assert_not_called()

    def test_only_fixed_ascii_labels_reach_fd3(self):
        with patch.dict(os.environ, {'CODING_REVIEW_STAGE_FD': '3'}, clear=True), patch('os.write') as write:
            for stage in sorted(_DIAGNOSTIC_STAGES):
                _worker_stage(stage)
            self.assertEqual(write.call_count, 5)
            for call in write.call_args_list:
                self.assertEqual(call.args[0], 3)
                self.assertIn(call.args[1].decode('ascii').strip(), _DIAGNOSTIC_STAGES)

    def test_unknown_or_injected_stage_is_never_written(self):
        with patch.dict(os.environ, {'CODING_REVIEW_STAGE_FD': '3'}, clear=True), patch('os.write') as write:
            for stage in ['CANARY', 'provider_ready\\nCANARY', '', 'x' * 10000]:
                _worker_stage(stage)
            write.assert_not_called()

    def test_broken_or_missing_pipe_does_not_fail_execution(self):
        with patch.dict(os.environ, {'CODING_REVIEW_STAGE_FD': '3'}, clear=True):
            for error in [BrokenPipeError('CANARY'), OSError('CANARY')]:
                with patch('os.write', side_effect=error):
                    _worker_stage('provider_ready')
