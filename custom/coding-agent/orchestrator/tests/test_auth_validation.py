"""Synthetic RSA fixtures; no credential lifecycle or network access."""
import base64
import io
import json
import pickle
import threading
import time
import unittest
from unittest.mock import patch

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from coding_orchestrator.auth_validation import AUTH_CLAIM, ISSUER, validate_identity
from coding_orchestrator.backend import BackendContractError
from coding_orchestrator.job_worker import WorkerControl, WorkerCancelled, WorkerDeadline
from test_bounded_llm import Counter


def b64(value):
    return base64.urlsafe_b64encode(value).rstrip(b'=').decode()


class AuthValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        numbers = cls.key.public_key().public_numbers()
        cls.public = {'kty': 'RSA', 'kid': 'synthetic-key', 'use': 'sig', 'alg': 'RS256',
                      'n': b64(numbers.n.to_bytes(256, 'big')), 'e': 'AQAB'}

    def setUp(self):
        self.counter = Counter()
        self.cancelled = threading.Event()
        self.control = WorkerControl(self.counter, self.cancelled, threading.Event(),
                                     time.monotonic() + 60, 3, io.BytesIO())
        self.now = 1000000
        clock = patch('coding_orchestrator.auth_validation.time.time', lambda: self.now)
        clock.start()
        self.addCleanup(clock.stop)
        self.guards = []
        for target in ('socket.getaddrinfo', 'socket.create_connection',
                       'httpx.Client.send', 'httpx.AsyncClient.send'):
            guard = patch(target, side_effect=AssertionError('Offline validation only'))
            self.guards.append(guard.start())
            self.addCleanup(guard.stop)
        from openhands.sdk.llm.auth import CredentialStore, OpenAISubscriptionAuth
        for owner, name in ((CredentialStore, 'get'), (CredentialStore, 'save'),
                            (OpenAISubscriptionAuth, 'refresh_if_needed_sync')):
            guard = patch.object(owner, name, side_effect=AssertionError('No credential lifecycle'))
            self.guards.append(guard.start())
            self.addCleanup(guard.stop)

    def tearDown(self):
        self.assertEqual(self.counter.value, 0)
        for guard in self.guards:
            guard.assert_not_called()

    def claims(self, **changes):
        return {'iss': ISSUER, 'sub': 'synthetic-subject', 'aud': 'synthetic-audience',
                'iat': self.now - 10, 'exp': self.now + 60,
                AUTH_CLAIM: {'chatgpt_account_id': 'synthetic-account'}, **changes}

    def token(self, claims=None, header=None, raw_claims=None, raw_header=None):
        header = header or {'alg': 'RS256', 'kid': 'synthetic-key', 'typ': 'JWT'}
        content = b64(raw_header if raw_header is not None else json.dumps(header).encode()) + '.'
        content += b64(raw_claims if raw_claims is not None else json.dumps(self.claims() if claims is None else claims).encode())
        return content + '.' + b64(self.key.sign(content.encode(), padding.PKCS1v15(), hashes.SHA256()))

    def validate(self, token=None, keys=None, **options):
        return validate_identity(self.control, self.token() if token is None else token,
            json.dumps({'keys': [self.public]}).encode() if keys is None else keys,
            expected_subject='synthetic-subject', expected_account_id='synthetic-account',
            expected_audience='synthetic-audience', **({'enabled': True} | options))

    def test_valid_signature_identity_and_minimal_nonserializable_result(self):
        result = self.validate()
        self.assertEqual((result.subject, result.account_id, result.expires_at),
                         ('synthetic-subject', 'synthetic-account', self.now + 60))
        self.assertNotIn('synthetic', repr(result))
        with self.assertRaises(TypeError):
            pickle.dumps(result)
        self.assertFalse(hasattr(result, 'access_token'))

    def test_disabled_path_never_calls_signature_implementation(self):
        with patch('joserfc.jwt.decode', side_effect=AssertionError('Disabled')) as decode:
            with self.assertRaises(BackendContractError):
                self.validate(enabled=False)
        decode.assert_not_called()

    def test_tampered_signature_and_payload_rejected(self):
        token = self.token()
        header, payload, signature = token.split('.')
        for bad in (header + '.' + payload + '.' + ('A' if signature[0] != 'A' else 'B') + signature[1:],
                    header + '.' + b64(json.dumps(self.claims(sub='attacker')).encode()) + '.' + signature):
            with self.assertRaises(BackendContractError):
                self.validate(bad)

    def test_required_identity_and_time_claims(self):
        cases = [{'iss': 'https://invalid.test'}, {'iss': [ISSUER]}, {'sub': 'other'}, {'sub': 1},
                 {'aud': 'other'}, {'aud': ['other']}, {'aud': ['synthetic-audience', 'synthetic-audience']},
                 {AUTH_CLAIM: {'chatgpt_account_id': 'other'}}, {AUTH_CLAIM: []},
                 {'exp': self.now}, {'exp': self.now - 1}, {'iat': self.now + 1},
                 {'nbf': self.now + 1}, {'exp': True}, {'exp': float(self.now + 60)},
                 {'iat': None}, {'nbf': False}, {'exp': 2**53}, {'iat': self.now + 60}]
        for changes in cases:
            with self.subTest(changes=changes), self.assertRaises(BackendContractError):
                self.validate(self.token(self.claims(**changes)))
        for missing in ('iss', 'sub', 'aud', 'exp', 'iat', AUTH_CLAIM):
            claims = self.claims()
            del claims[missing]
            with self.subTest(missing=missing), self.assertRaises(BackendContractError):
                self.validate(self.token(claims))

    def test_audience_membership_and_not_before_boundary(self):
        self.validate(self.token(self.claims(aud=['other', 'synthetic-audience'], nbf=self.now)))

    def test_default_is_disabled_and_expected_bindings_are_required(self):
        args = {'expected_subject': 'synthetic-subject',
                'expected_account_id': 'synthetic-account',
                'expected_audience': 'synthetic-audience'}
        keys = json.dumps({'keys': [self.public]}).encode()
        with self.assertRaises(BackendContractError):
            validate_identity(self.control, self.token(), keys, **args)
        for name in args:
            for value in ('', None, [], 'white space', 'x' * 257):
                with self.subTest(name=name, value=value), self.assertRaises(BackendContractError):
                    validate_identity(self.control, self.token(), keys, enabled=True,
                                      **{**args, name: value})

    def test_different_public_key_with_same_id_cannot_verify(self):
        other = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        key = {**self.public, 'n': b64(other.public_key().public_numbers().n.to_bytes(256, 'big'))}
        with self.assertRaises(BackendContractError):
            self.validate(keys=json.dumps({'keys': [key]}).encode())

    def test_rechecks_expiry_and_control_after_real_signature_verification(self):
        from joserfc import jwt
        decode = jwt.decode
        for outcome in ('expiry', 'cancel', 'deadline'):
            token = self.token()

            def verified(*args, **kwargs):
                result = decode(*args, **kwargs)
                if outcome == 'expiry':
                    self.now += 60
                elif outcome == 'cancel':
                    self.cancelled.set()
                else:
                    self.control._deadline = time.monotonic() - 1
                return result

            category = {'expiry': BackendContractError, 'cancel': WorkerCancelled,
                        'deadline': WorkerDeadline}[outcome]
            with self.subTest(outcome=outcome), patch.object(jwt, 'decode', verified):
                with self.assertRaises(category):
                    self.validate(token)
            self.cancelled.clear()
            self.control._deadline = time.monotonic() + 60

    def test_bounded_strict_json_for_tokens_and_keys(self):
        claims = json.dumps(self.claims()).encode()
        raw_cases = [b'{"extra":1e999,' + claims[1:], b'{"extra":NaN,' + claims[1:],
                     b'{"extra":' + b'[' * 9 + b'0' + b']' * 9 + b',' + claims[1:],
                     b'{"extra":[' + b'0,' * 1024 + b'0],' + claims[1:]]
        for raw in raw_cases:
            with self.subTest(size=len(raw)), self.assertRaises(BackendContractError):
                self.validate(self.token(raw_claims=raw))
        keys = json.dumps({'keys': [self.public]}).encode()
        for raw in (b'', b'[]', b'null', b'\xff', b'{' , b' ' * (64 * 1024 + 1),
                    b'{"keys":[],' + keys[1:], b'{"extra":1e999,' + keys[1:]):
            with self.subTest(size=len(raw)), self.assertRaises(BackendContractError):
                self.validate(keys=raw)

    def test_failed_verification_preserves_concurrent_control_and_sanitizes_error(self):
        for category in (WorkerCancelled, WorkerDeadline):
            def failed(*args, **kwargs):
                if category is WorkerCancelled:
                    self.cancelled.set()
                else:
                    self.control._deadline = time.monotonic() - 1
                raise ValueError('verification-retention-canary')

            with patch('joserfc.jwt.decode', failed):
                try:
                    self.validate()
                except category as error:
                    self.assertIsNone(error.__context__)
                    self.assertIsNone(error.__cause__)
                    trace = error.__traceback__
                    while trace:
                        if trace.tb_frame.f_globals.get('__name__') == 'coding_orchestrator.auth_validation':
                            self.assertIn(trace.tb_frame.f_code.co_name, ('validate_identity', '_fail'))
                            for name, value in trace.tb_frame.f_locals.items():
                                self.assertIs(value, category if name in ('failure', 'category') else None)
                        trace = trace.tb_next
                else:
                    self.fail('Expected native worker condition')
            self.cancelled.clear()
            self.control._deadline = time.monotonic() + 60

    def test_header_profile_and_remote_key_hints_rejected(self):
        for change in ({'alg': 'none'}, {'alg': 'HS256'}, {'typ': 'JWE'}, {'kid': 'unknown'},
                       {'jku': 'https://invalid.test'}, {'x5u': 'https://invalid.test'},
                       {'jwk': self.public}, {'crit': ['custom']}):
            header = {'alg': 'RS256', 'kid': 'synthetic-key', 'typ': 'JWT', **change}
            with self.subTest(change=change), self.assertRaises(BackendContractError):
                self.validate(self.token(header=header))

    def test_malformed_compact_and_duplicate_json(self):
        claims = json.dumps(self.claims()).encode()
        cases = ['', 'a.b.c', self.token() + '=', 'a.b.c.d', 'x' * (16 * 1024 + 1),
                 self.token(raw_header=b'{"alg":"none","alg":"RS256","kid":"synthetic-key"}'),
                 self.token(raw_claims=b'{"exp":1,' + claims[1:]),
                 self.token(raw_claims=b'[]')]
        for token in cases:
            with self.subTest(token_length=len(token)), self.assertRaises(BackendContractError):
                self.validate(token)

    def test_key_set_profile_and_ambiguity(self):
        cases = [[], [self.public, self.public], [self.public] * 17]
        for change in ({'kty': 'oct'}, {'d': 'private'}, {'e': 'Aw'}, {'n': 'AQAB'},
                       {'n': b64(b'\xff' * 513)}, {'n': '='}, {'alg': 'RS512'},
                       {'use': 'enc'}, {'key_ops': ['sign']}, {'kid': 'unknown'}):
            cases.append([{**self.public, **change}])
        for keys in cases:
            with self.subTest(keys_count=len(keys)), self.assertRaises(BackendContractError):
                self.validate(keys=json.dumps({'keys': keys}).encode())

    def test_cancel_and_deadline_stay_typed_without_provider_accounting(self):
        for category in (WorkerCancelled, WorkerDeadline):
            if category is WorkerCancelled:
                self.cancelled.set()
            else:
                self.control._deadline = time.monotonic() - 1
            with self.assertRaises(category):
                self.validate()
            self.cancelled.clear()
            self.control._deadline = time.monotonic() + 60

    def test_live_failure_traceback_has_no_sensitive_validation_frames(self):
        try:
            self.validate(self.token(self.claims(sub='retention-canary')))
        except BackendContractError as error:
            self.assertIsNone(error.__context__)
            self.assertIsNone(error.__cause__)
            self.assertNotIn('retention-canary', str(error))
            trace = error.__traceback__
            while trace:
                frame = trace.tb_frame
                if frame.f_globals.get('__name__') == 'coding_orchestrator.auth_validation':
                    self.assertIn(frame.f_code.co_name, ('validate_identity', '_fail'))
                    for name, value in frame.f_locals.items():
                        if name in ('failure', 'category'):
                            self.assertIs(value, BackendContractError)
                        else:
                            self.assertIsNone(value)
                trace = trace.tb_next
        else:
            self.fail('Expected identity rejection')


if __name__ == '__main__':
    unittest.main()
