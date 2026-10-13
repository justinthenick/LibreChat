"""Dormant offline verification against explicitly supplied, trusted public keys.

No credential discovery, transport, SDK hooks, persistence or authorization grant.
The caller must establish key provenance and expected identity independently.
"""
import base64
import json
import math
import re
import time
from dataclasses import dataclass, field

from .auth_exchange import MAX_REPLY, TOKEN_URL
from .backend import BackendContractError
from .job_worker import WorkerCancelled, WorkerDeadline, WorkerLimit

ISSUER = TOKEN_URL.removesuffix('/oauth/token')
AUTH_CLAIM = 'https://api.openai.com/auth'
MAX_TOKEN = 16 * 1024


@dataclass(frozen=True)
class ValidatedIdentity:
    """Signature/claims result for supplied keys, not proof of owner authorization."""

    subject: str = field(repr=False)
    account_id: str = field(repr=False)
    expires_at: int

    def __reduce__(self):
        raise TypeError('Auth identity must remain inside the worker')


def _fail(category):
    if category in (WorkerCancelled, WorkerDeadline, WorkerLimit):
        raise category() from None
    raise BackendContractError('Auth identity unavailable or invalid') from None


def validate_identity(control, access_token, jwks, *, expected_subject,
                      expected_account_id, expected_audience, enabled=False):
    """Validate offline inside a worker; policy inputs must come from trusted code."""
    identity, failure = _validate(control, access_token, jwks, expected_subject,
                                   expected_account_id, expected_audience, enabled)
    control = access_token = jwks = expected_subject = expected_account_id = expected_audience = enabled = None
    if failure is not None:
        _fail(failure)
    return identity


def _text(value, maximum=256):
    if type(value) is not str or not 1 <= len(value) <= maximum or any(not 33 <= ord(c) <= 126 for c in value):
        raise ValueError('Invalid bounded text')
    return value


def _segment(value):
    if type(value) is not str or not re.fullmatch(r'[A-Za-z0-9_-]+', value):
        raise ValueError('Invalid base64url')
    decoded = base64.urlsafe_b64decode(value + '=' * (-len(value) % 4))
    if base64.urlsafe_b64encode(decoded).rstrip(b'=').decode() != value:
        raise ValueError('Noncanonical base64url')
    return decoded


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate JSON field')
        result[key] = value
    return result


def _constant(value):
    raise ValueError('Nonfinite JSON value')


def _json(raw):
    value = json.loads(raw.decode('utf-8'), object_pairs_hook=_pairs, parse_constant=_constant)
    pending = [(value, 0)]
    count = 0
    while pending:
        item, depth = pending.pop()
        count += 1
        if depth > 8 or count > 1024:
            raise ValueError('JSON structure limit')
        if type(item) is float and not math.isfinite(item):
            raise ValueError('Nonfinite JSON value')
        children = item.values() if type(item) is dict else item if type(item) is list else ()
        pending.extend((child, depth + 1) for child in children)
    if type(value) is not dict:
        raise ValueError('JSON object required')
    return value


def _key(jwks, kid):
    keys = _json(jwks).get('keys')
    if type(keys) is not list or not 1 <= len(keys) <= 16:
        raise ValueError('Invalid key set')
    selected = None
    seen = set()
    for key in keys:
        if type(key) is not dict or set(key) - {'kty', 'kid', 'n', 'e', 'alg', 'use', 'key_ops'}:
            raise ValueError('Public RSA key required')
        key_id = _text(key.get('kid'), 128)
        if key_id in seen:
            raise ValueError('Ambiguous key ID')
        seen.add(key_id)
        if (key.get('kty') != 'RSA' or key.get('alg', 'RS256') != 'RS256'
                or key.get('use', 'sig') != 'sig' or key.get('key_ops', ['verify']) != ['verify']):
            raise ValueError('Signing key required')
        modulus = _segment(key.get('n'))
        if (not 256 <= len(modulus) <= 512 or modulus[0] == 0
                or not 2048 <= int.from_bytes(modulus, 'big').bit_length() <= 4096
                or not modulus[-1] & 1 or key.get('e') != 'AQAB'):
            raise ValueError('Bounded RSA parameters required')
        if key_id == kid:
            selected = key
    if selected is None:
        raise ValueError('Unknown signing key')
    return selected


def _validate(control, access_token, jwks, subject, account, audience, enabled):
    try:
        if enabled is not True:
            raise ValueError('Validation disabled')
        control.remaining_seconds()
        _text(subject)
        _text(account)
        _text(audience)
        _text(access_token, MAX_TOKEN)
        if type(jwks) is not bytes or not 1 <= len(jwks) <= MAX_REPLY:
            raise ValueError('Invalid bounded key set')
        parts = access_token.split('.')
        if len(parts) != 3:
            raise ValueError('Compact signed JWT required')
        header, claims = _json(_segment(parts[0])), _json(_segment(parts[1]))
        signature = _segment(parts[2])
        if (set(header) - {'alg', 'kid', 'typ'} or header.get('alg') != 'RS256'
                or header.get('typ', 'JWT') != 'JWT' or not 256 <= len(signature) <= 512):
            raise ValueError('Unsupported token header')
        kid = _text(header.get('kid'), 128)
        public_key = _key(jwks, kid)
        from joserfc import jwk, jwt

        # Reuse the SDK's JOSE implementation, without its network/logging helper.
        decoded = jwt.decode(access_token, jwk.RSAKey.import_key(public_key), algorithms=['RS256'])
        if decoded.claims != claims:
            raise ValueError('Inconsistent claims decoding')
        for name in ('exp', 'iat', 'nbf'):
            value = claims.get(name)
            if name == 'nbf' and name not in claims:
                continue
            if type(value) is not int or not 0 <= value < 2**53:
                raise ValueError('Integral bounded timestamp required')
        if claims['iat'] >= claims['exp'] or claims.get('nbf', 0) >= claims['exp']:
            raise ValueError('Inconsistent token lifetime')
        audiences = claims.get('aud')
        if type(audiences) is str:
            audiences = [audiences]
        if type(audiences) is not list or not 1 <= len(audiences) <= 8:
            raise ValueError('Bounded audience required')
        for item in audiences:
            _text(item)
        if len(set(audiences)) != len(audiences):
            raise ValueError('Duplicate audience')
        now = int(time.time())
        jwt.JWTClaimsRegistry(now=now, leeway=0,
            iss={'essential': True, 'value': ISSUER},
            sub={'essential': True, 'value': subject},
            aud={'essential': True, 'value': audience},
            exp={'essential': True}, iat={'essential': True}).validate(claims)
        auth = claims.get(AUTH_CLAIM)
        if type(auth) is not dict or _text(auth.get('chatgpt_account_id')) != account:
            raise ValueError('Account binding mismatch')
        control.remaining_seconds()
        # Enforce exp equality rejection and recheck after signature work.
        if claims['exp'] <= max(now, int(time.time())):
            raise ValueError('Expired identity')
        return ValidatedIdentity(subject, account, claims['exp']), None
    except Exception as error:
        category = type(error) if type(error) in (WorkerCancelled, WorkerDeadline, WorkerLimit) else BackendContractError
        if category is BackendContractError and enabled is True:
            try:
                control.remaining_seconds()
            except (WorkerCancelled, WorkerDeadline, WorkerLimit) as stopped:
                category = type(stopped)
            except Exception:
                pass
        return None, category
