"""Versioned private storage protocol. Digests are consistency checks, not authentication."""
import base64
import hashlib
import json
import re

from integration import IntegrationMapping, _uuid
from job_store import IdempotencyConflict, JobNotFound, StoreBusy

MAX_SAFE = (1 << 53) - 1
MAPPING_FIELDS = set(IntegrationMapping.__dataclass_fields__)
COMMON = {'version', 'backend', 'namespace', 'kind'}
MUTATION = {'mapping', 'operation_id', 'owner_epoch', 'expected_version'}
FIELDS = {
    'snapshot': set(), 'query': {'mapping', 'operation_id'},
    'admit': MUTATION, 'cancel': MUTATION,
    'observe': MUTATION | {'evidence_id', 'producer', 'producer_epoch', 'sequence',
                           'prior_binding_head', 'data'},
    'finish': {'mapping', 'owner_epoch', 'expected_version', 'verification_receipt_id'},
}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode('ascii')).hexdigest()


def exact(value, fields):
    if type(value) is not dict or set(value) != fields:
        raise ValueError('Invalid protocol fields')


def counter(value, positive=False):
    if type(value) is not int or not int(positive) <= value <= MAX_SAFE:
        raise ValueError('Invalid protocol counter')


def validate(payload):
    if type(payload) is not dict or type(payload.get('kind')) is not str:
        raise ValueError('Invalid protocol kind')
    kind = payload['kind']
    if kind not in FIELDS:
        raise ValueError('Unknown protocol kind')
    exact(payload, COMMON | FIELDS[kind])
    if type(payload['version']) is not int or payload['version'] != 1 or payload['backend'] != 'supervisor':
        raise ValueError('Unsupported protocol')
    _uuid(payload['namespace'])
    for name in ('operation_id', 'verification_receipt_id', 'evidence_id', 'producer_epoch'):
        if name in payload:
            _uuid(payload[name])
    for name in ('owner_epoch', 'expected_version', 'sequence'):
        if name in payload:
            counter(payload[name], positive=name != 'expected_version')
    if 'mapping' in payload:
        exact(payload['mapping'], MAPPING_FIELDS)
        for name, value in payload['mapping'].items():
            if name == 'logical_generation':
                counter(value, positive=True)
            elif type(value) is not str or not value.isascii() or any(not 32 <= ord(c) <= 126 for c in value):
                raise ValueError('Mapping must use printable ASCII')
        IntegrationMapping(**payload['mapping'])
    if kind == 'observe':
        if payload['producer'] not in ('guest', 'host'):
            raise ValueError('Unsupported producer')
        if type(payload['prior_binding_head']) is not str or not re.fullmatch('[0-9a-f]{64}', payload['prior_binding_head']):
            raise ValueError('Invalid binding digest')
        data = payload['data']
        if type(data) is not str or not 0 < len(data) <= 87384:
            raise ValueError('Invalid encoded observation')
        raw = base64.b64decode(data, validate=True)
        if not 0 < len(raw) <= 65536 or base64.b64encode(raw).decode('ascii') != data:
            raise ValueError('Noncanonical observation')
    return payload


def dispatch(store, command):
    exact(command, {'sequence', 'operation', 'payload', 'payloadDigest'})
    if command['operation'] != 'integration_v1' or store.integration is None:
        raise ValueError('Wrong journal mode')
    counter(command['sequence'], positive=True)
    payload = validate(command['payload'])
    if payload['namespace'] != store.integration.namespace or command['payloadDigest'] != digest(payload):
        raise ValueError('Protocol binding mismatch')
    kind = payload['kind']
    mapping = IntegrationMapping(**payload['mapping']) if 'mapping' in payload else None
    try:
        if kind == 'snapshot':
            result = {'status': 'snapshot', 'snapshot': store.integration.snapshot()}
        elif kind == 'query':
            receipt = store.integration.query_operation(payload['operation_id'])
            if receipt is None:
                result = {'status': 'not_found'}
            else:
                with store._transaction() as database:
                    store.integration._binding(database, mapping)
                    if receipt['review_id'] != mapping.review_id:
                        raise JobNotFound('Receipt target mismatch')
                result = {'status': 'found', 'receipt': receipt}
        elif kind == 'finish':
            with store._transaction() as database:
                meta = store.integration._fence(database, payload['owner_epoch'], payload['expected_version'])
                store.integration._version(meta, payload['expected_version'])
                store.integration._binding(database, mapping)
            result = {'status': 'verification_unavailable'}
        else:
            arguments = dict(owner_epoch=payload['owner_epoch'], expected_version=payload['expected_version'])
            if kind == 'observe':
                arguments.update({key: payload[key] for key in
                    ('evidence_id', 'producer', 'producer_epoch', 'sequence', 'prior_binding_head')})
                arguments['data'] = base64.b64decode(payload['data'], validate=True)
            method = getattr(store.integration, 'request_cancel' if kind == 'cancel' else kind)
            receipt = method(mapping, payload['operation_id'], **arguments)
            result = {'status': 'recorded', 'receipt': receipt}
    except StoreBusy:
        result = {'status': 'rejected', 'code': 'busy'}
    except JobNotFound:
        result = {'status': 'rejected', 'code': 'forbidden'}
    except IdempotencyConflict:
        result = {'status': 'rejected', 'code': 'conflict'}
    return {'integration': dict(version=1, backend='supervisor', namespace=payload['namespace'],
        kind=kind, requestDigest=command['payloadDigest'], resultDigest=digest(result), result=result)}
