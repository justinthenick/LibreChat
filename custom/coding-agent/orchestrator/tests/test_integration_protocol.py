"""Actual private helper and disposable records; no provider or Supervisor execution."""
from pathlib import Path
import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from uuid import uuid4
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src' / 'coding_orchestrator'))
from integration_protocol import canonical, digest
from job_store import JobStore, StoreError
from review_journal import dispatch


class IntegrationProtocolTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix='integration-protocol-')
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / 'private' / 'jobs.sqlite'
        self.namespace = str(uuid4())
        self.mapping = dict(review_id=str(uuid4()), attempt_id=str(uuid4()), logical_generation=1,
            user_id='fixture', tenant_id='', repository_alias='fixture', base='a'*40, head='b'*40,
            profile_id='fixture', model='fixture')
        self.sequence = 0
        self.child = self.open()

    def open(self, namespace=True):
        helper = Path(__file__).resolve().parents[1] / 'src' / 'coding_orchestrator' / 'review_journal.py'
        child = subprocess.Popen([sys.executable, '-B', '-S', '-s', str(helper), str(self.path)] +
            (['--integration-v1', self.namespace] if namespace else []),
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        def cleanup():
            if child.poll() is None:
                child.kill()
            child.communicate(timeout=10)
        self.addCleanup(cleanup)
        greeting = child.stdout.readline()
        self.assertTrue(greeting, child.stderr.read() if child.poll() is not None else '')
        self.assertEqual(json.loads(greeting), dict(ready=True, version=1, backend='supervisor', namespace=self.namespace))
        return child

    def payload(self, kind, **fields):
        return dict(version=1, backend='supervisor', namespace=self.namespace, kind=kind, **fields)

    def wire(self, payload):
        self.sequence += 1
        return dict(sequence=self.sequence, operation='integration_v1', payload=payload, payloadDigest=digest(payload))

    def send(self, payload):
        command = self.wire(payload)
        self.child.stdin.write(canonical(command) + '\n')
        self.child.stdin.flush()
        line = self.child.stdout.readline()
        self.assertTrue(line)
        response = json.loads(line)
        self.assertEqual(line, canonical(response) + '\n')
        self.assertEqual(response['sequence'], self.sequence)
        reply = response['integration']
        self.assertEqual(reply['requestDigest'], digest(payload))
        self.assertEqual(reply['resultDigest'], digest(reply['result']))
        return reply['result']

    def admit(self):
        operation_id = str(uuid4())
        receipt = self.send(self.payload('admit', mapping=self.mapping, operation_id=operation_id,
            owner_epoch=1, expected_version=0))
        self.assertEqual(receipt['status'], 'recorded')
        return operation_id, receipt['receipt']

    def fence(self, raw):
        self.child.stdin.write(raw + '\n')
        self.child.stdin.flush()
        self.assertEqual(self.child.wait(timeout=10), 1)
        self.assertEqual(self.child.stdout.read(), '')
        with sqlite3.connect(self.path) as database:
            self.assertEqual(database.execute('SELECT count(*) FROM jobs').fetchone()[0], 0)

    def test_snapshot_admit_query_and_finish_never_release(self):
        self.assertEqual(self.send(self.payload('snapshot'))['snapshot']['owner_epoch'], 1)
        operation, receipt = self.admit()
        found = self.send(self.payload('query', mapping=self.mapping, operation_id=operation))
        self.assertEqual(found, dict(status='found', receipt=receipt))
        result = self.send(self.payload('finish', mapping=self.mapping, owner_epoch=1,
            expected_version=1, verification_receipt_id=str(uuid4())))
        self.assertEqual(result, {'status': 'verification_unavailable'})
        self.assertEqual(self.send(self.payload('snapshot'))['snapshot']['version'], 1)
        with sqlite3.connect(self.path) as database:
            self.assertEqual(database.execute('SELECT state FROM jobs').fetchone()[0], 'queued')
            self.assertIsNone(database.execute('SELECT resolved_at FROM reservations').fetchone()[0])

    def test_cancel_alias_and_unverified_success_bytes(self):
        self.admit()
        for version in (1, 2):
            result = self.send(self.payload('cancel', mapping=self.mapping, operation_id=str(uuid4()),
                owner_epoch=1, expected_version=version))
            self.assertFalse(result['receipt']['stop_confirmed'])
        with sqlite3.connect(self.path) as database:
            binding = database.execute('SELECT binding_head FROM integration_mappings').fetchone()[0]
        import base64
        result = self.send(self.payload('observe', mapping=self.mapping, operation_id=str(uuid4()),
            owner_epoch=1, expected_version=3, evidence_id=str(uuid4()), producer='guest',
            producer_epoch=str(uuid4()), sequence=1, prior_binding_head=binding,
            data=base64.b64encode(b'{"success":true,"stopped":true}').decode()))
        self.assertEqual(result['receipt']['kind'], 'unverified_observation_recorded')
        self.assertFalse(result['receipt']['stop_confirmed'])

    def test_reopen_queries_original_operation_without_reapplication(self):
        operation, receipt = self.admit()
        # Discard the original response; simulate loss of the owning service/helper.
        self.child.kill()
        self.child.wait(timeout=10)
        self.sequence = 0
        self.child = self.open()
        current = self.send(self.payload('snapshot'))['snapshot']
        self.assertEqual((current['owner_epoch'], current['version'], current['recovery']), (2, 2, 1))
        self.assertEqual(self.send(self.payload('query', mapping=self.mapping, operation_id=operation)),
                         dict(status='found', receipt=receipt))
        self.assertEqual(self.send(self.payload('query', mapping=self.mapping, operation_id=str(uuid4()))),
                         {'status': 'not_found'})

    def test_query_cannot_switch_mapping(self):
        operation, _ = self.admit()
        result = self.send(self.payload('query', mapping=self.mapping | {'logical_generation': 2}, operation_id=operation))
        self.assertEqual(result, {'status': 'rejected', 'code': 'forbidden'})

    def test_unknown_kind_fences(self):
        self.fence(canonical(self.wire(self.payload('resolve'))))

    def test_unknown_field_fences(self):
        self.fence(canonical(self.wire(self.payload('snapshot', success=True))))

    def test_digest_mismatch_fences(self):
        self.fence(canonical(self.wire(self.payload('snapshot')) | {'payloadDigest': '0'*64}))

    def test_duplicate_key_fences(self):
        raw = canonical(self.wire(self.payload('snapshot')))
        self.fence(raw.replace('"version":1', '"version":1,"version":1'))

    def test_unsafe_version_fences(self):
        self.fence(canonical(self.wire(self.payload('admit', mapping=self.mapping,
            operation_id=str(uuid4()), owner_epoch=1, expected_version=1 << 53))))

    def test_noncanonical_uuid_fences(self):
        self.fence(canonical(self.wire(self.payload('query', mapping=self.mapping,
            operation_id='AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA'))))

    def test_noncanonical_base64_fences(self):
        self.fence(canonical(self.wire(self.payload('observe', mapping=self.mapping,
            operation_id=str(uuid4()), owner_epoch=1, expected_version=0, evidence_id=str(uuid4()),
            producer='guest', producer_epoch=str(uuid4()), sequence=1, prior_binding_head='a'*64, data='Zh=='))))

    def test_sequence_replay_fences(self):
        self.send(self.payload('snapshot'))
        self.sequence = 0
        self.fence(canonical(self.wire(self.payload('snapshot'))))

    def test_legacy_success_cannot_mutate_integrated_store(self):
        self.fence(canonical(dict(sequence=1, operation='finish', id=self.mapping['review_id'],
            principal=dict(userId='fixture'), result=dict(success=True, stopped=True))))

    def test_legacy_mode_rejects_integration_before_maintenance(self):
        with JobStore(Path(self.directory.name) / 'legacy' / 'jobs.sqlite') as legacy:
            with patch.object(legacy, 'discard_terminal_results', wraps=legacy.discard_terminal_results) as expire:
                with self.assertRaises(StoreError):
                    dispatch(legacy, self.wire(self.payload('snapshot')))
                expire.assert_not_called()
            self.assertEqual(legacy._connection.execute('SELECT count(*) FROM jobs').fetchone()[0], 0)

    def test_oversized_frame_fences(self):
        self.fence(' ' * 132097)

    def test_shared_ascii_escape_vector(self):
        self.assertEqual(canonical({'tenant': '', 'text': 'quote" slash\\'}),
                         '{"tenant":"","text":"quote\\" slash\\\\"}')
        self.assertEqual(digest({'tenant': '', 'text': 'quote" slash\\'}),
                         'e02a7b89943384c33b0e84d815acc23566f3b232d5bdf6556c78490972dd8440')


if __name__ == '__main__':
    unittest.main()
