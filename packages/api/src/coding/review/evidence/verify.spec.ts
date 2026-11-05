import { createHash } from 'node:crypto';
import type { OfflineContext, OfflineEnvelope } from './verify';
import { verifyOfflineBundle, verifyPublicFixture } from './verify';

/** Public-only https://www.rfc-editor.org/rfc/rfc8032#section-7.1 tests 1/2. */
const vectors = [
  {
    key: 'd75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a',
    message: '',
    signature:
      'e5564300c360ac729086e2cc806e828a84877f1eb8e5d974d873e06522490155' +
      '5fb8821590a33bacc61e39701cf9b46bd25bf5f0595bbe24655141438e7a100b',
  },
  {
    key: '3d4017c3e843895a92b70aa74d1b7ebc9c982ccf2ec4968cc0cd55f12af4660c',
    message: '72',
    signature:
      '92a009a9f0d4cab8720e820b5f642540a2b27b5416503f8fb3762223ebdb69da' +
      '085ac1e43e15996e458f3613d0f11d8c387b2eaeb4302aeeb00d291612bb0c00',
  },
];
const uuid = '550e8400-e29b-41d4-a716-446655440000';
const binding = {
  profile: 'S4-OFFLINE-1' as const,
  policyVersion: 1 as const,
  reviewId: uuid,
  attemptId: uuid,
  generation: 1,
  ownerEpoch: 1,
  runtimeEpoch: uuid,
  reservationId: uuid,
  mappingDigest: '1'.repeat(64),
  priorBindingHead: '2'.repeat(64),
  challenge: '3'.repeat(64),
  sourceDigest: '4'.repeat(64),
  binaryDigest: '5'.repeat(64),
  configDigest: '6'.repeat(64),
};
const context: OfflineContext = {
  ...binding,
  producers: [
    {
      keyId: 'public-vector-1',
      producerId: 'fixture-guest',
      role: 'guest',
      producerEpoch: uuid,
      clockDomain: 'guest-fixture-ticks',
      publicKeyHex: vectors[0].key,
    },
    {
      keyId: 'public-vector-2',
      producerId: 'fixture-host',
      role: 'host',
      producerEpoch: uuid,
      clockDomain: 'host-fixture-ticks',
      publicKeyHex: vectors[1].key,
    },
  ],
};
type Json = boolean | number | string | Json[] | { [key: string]: Json };
function canonical(value: Json): string {
  if (Array.isArray(value)) return `[${value.map(canonical).join(',')}]`;
  if (typeof value === 'object') {
    return `{${Object.keys(value)
      .sort()
      .map((key) => `${JSON.stringify(key)}:${canonical(value[key])}`)
      .join(',')}}`;
  }
  return JSON.stringify(value);
}
function frame(raw: string): Buffer {
  const bytes = Buffer.from(raw, 'utf8');
  const length = Buffer.alloc(4);
  length.writeUInt32BE(bytes.length);
  return Buffer.concat([
    Buffer.from('LibreChat/Supervisor/observation/S4-OFFLINE-1\0', 'ascii'),
    length,
    bytes,
  ]);
}
function payload(index: number, changes: { [key: string]: Json } = {}): Json {
  const producer = context.producers[index];
  const bytes = Buffer.from('fabricated artifact');
  return {
    ...binding,
    keyId: producer.keyId,
    producerId: producer.producerId,
    role: producer.role,
    producerEpoch: producer.producerEpoch,
    clockDomain: producer.clockDomain,
    observationKind: 'fixture_observation',
    sequence: 1,
    previousRecordDigest: '0'.repeat(64),
    start: true,
    end: true,
    intervalStart: 0,
    intervalEnd: 1,
    limitationCodes: ['NO_RUNTIME_OBSERVATION', 'SYNTHETIC_ONLY'],
    artifacts: [
      {
        name: 'fixture',
        bytes: bytes.length,
        sha256: createHash('sha256').update(bytes).digest('hex'),
      },
    ],
    ...changes,
  };
}
function envelope(index: number, changes: { [key: string]: Json } = {}): OfflineEnvelope {
  return {
    frame: frame(canonical(payload(index, changes))),
    signature: Buffer.alloc(64),
    artifacts: [Buffer.from('fabricated artifact')],
  };
}
function check(first: OfflineEnvelope, second = envelope(1), expected = context) {
  const result = verifyOfflineBundle([first, second], expected);
  expect(result).toMatchObject({
    status: 'INVALID',
    syntheticOnly: true,
    signatureValid: false,
    liveAuthority: false,
    stopConfirmed: false,
    reservationReleased: false,
    quarantineClearance: false,
  });
  return result;
}

describe('real primitive verification of independent public RFC8032 vectors', () => {
  it.each(vectors)('verifies published message $message', ({ key, message, signature }) => {
    expect(
      verifyPublicFixture(
        Buffer.from(message, 'hex'),
        Buffer.from(key, 'hex'),
        Buffer.from(signature, 'hex'),
      ),
    ).toBe(true);
  });
  it('records the actual primitive runtime without claiming acceptance-set coverage', () => {
    console.info(
      `S4 fixture runtime Node=${process.versions.node} OpenSSL=${process.versions.openssl}`,
    );
  });
  it.each(['message', 'signature', 'key', 'short-signature', 'short-key', 'oversize'])(
    'rejects locally mutated primitive input: %s',
    (kind) => {
      let message = Buffer.from(vectors[1].message, 'hex');
      let key = Buffer.from(vectors[1].key, 'hex');
      let signature = Buffer.from(vectors[1].signature, 'hex');
      if (kind === 'message') message[0] ^= 1;
      if (kind === 'signature') signature[0] ^= 1;
      if (kind === 'key') key[0] ^= 1;
      if (kind === 'short-signature') signature = signature.subarray(1);
      if (kind === 'short-key') key = key.subarray(1);
      if (kind === 'oversize') message = Buffer.alloc(17000);
      expect(verifyPublicFixture(message, key, signature)).toBe(false);
    },
  );
});

describe('fabricated unsigned profile controls, never authenticated acceptance', () => {
  it('separates structural completeness from failed actual signatures', () => {
    expect(check(envelope(0))).toMatchObject({
      bindingValid: true,
      bundleComplete: true,
      reasons: ['signature'],
    });
  });
  it('cannot reuse a valid RFC signature as a profile signature', () => {
    const first = { ...envelope(0), signature: Buffer.from(vectors[0].signature, 'hex') };
    expect(check(first).reasons).toContain('signature');
  });
  it.each([
    'reviewId',
    'attemptId',
    'runtimeEpoch',
    'reservationId',
    'generation',
    'ownerEpoch',
    'mappingDigest',
    'priorBindingHead',
    'challenge',
    'sourceDigest',
    'binaryDigest',
    'configDigest',
  ])('rejects a different valid expected binding %s', (field) => {
    const original = binding[field as keyof typeof binding];
    let value: string | number = 'a'.repeat(64);
    if (typeof original === 'number') value = 2;
    else if (original.length === 36) value = '550e8400-e29b-41d4-a716-446655440001';
    const altered = { ...context, [field]: value };
    expect(check(envelope(0), envelope(1), altered).reasons).toContain('binding');
  });
  it.each([
    ['role', 'host'],
    ['keyId', 'other-key'],
    ['producerEpoch', '550e8400-e29b-41d4-a716-446655440001'],
    ['clockDomain', 'other-clock'],
    ['producerId', 'unknown'],
  ])('rejects producer binding %s', (field, value) => {
    expect(check(envelope(0, { [field]: value })).bindingValid).toBe(false);
  });
  it.each([
    ['sequence', 2],
    ['previousRecordDigest', 'a'.repeat(64)],
    ['start', false],
    ['end', false],
  ] as const)('rejects incomplete first-bundle boundary %s', (field, value) => {
    expect(check(envelope(0, { [field]: value })).bundleComplete).toBe(false);
  });
  it.each([
    ['extra', true],
    ['sequence', 1.5],
    ['ownerEpoch', Number.MAX_SAFE_INTEGER + 1],
    ['profile', 'live'],
    ['policyVersion', 2],
    ['observationKind', 'termination'],
    ['intervalEnd', -1],
    ['intervalStart', 2],
    ['keyId', 'x'.repeat(257)],
    ['keyId', 'trailing\n'],
    ['reviewId', uuid.toUpperCase()],
    ['limitationCodes', ['SYNTHETIC_ONLY']],
    ['artifacts', []],
    ['extra', [[[[true]]]]],
  ] as const)('rejects schema violation %s', (field, value) => {
    expect(check(envelope(0, { [field]: value as Json })).reasons).toContain('frame_or_schema');
  });
  it.each([
    'domain',
    'short',
    'long',
    'trailing',
    'whitespace',
    'duplicate',
    'non-ascii',
    'oversize',
  ])('rejects noncanonical frame: %s', (kind) => {
    let bytes = Buffer.from(envelope(0).frame);
    const raw = canonical(payload(0));
    if (kind === 'domain') bytes[0] ^= 1;
    const offset = Buffer.byteLength('LibreChat/Supervisor/observation/S4-OFFLINE-1\0');
    if (kind === 'short') bytes.writeUInt32BE(bytes.readUInt32BE(offset) - 1, offset);
    if (kind === 'long') bytes.writeUInt32BE(bytes.readUInt32BE(offset) + 1, offset);
    if (kind === 'trailing') bytes = Buffer.concat([bytes, Buffer.from('x')]);
    if (kind === 'whitespace') bytes = frame(` ${raw}`);
    if (kind === 'duplicate') bytes = frame(raw.replace('{', '{"sequence":1,'));
    if (kind === 'non-ascii') bytes = frame(raw.replace('fixture_observation', 'fixtur�'));
    if (kind === 'oversize') bytes = frame('x'.repeat(16385));
    expect(check({ ...envelope(0), frame: bytes }).bundleComplete).toBe(false);
  });
  it.each(['missing', 'changed', 'empty', 'oversize', 'extra'])(
    'rejects artifact mismatch or bound: %s',
    (kind) => {
      let artifacts = [Buffer.from('fabricated artifact')];
      if (kind === 'missing') artifacts = [];
      if (kind === 'changed') artifacts[0][0] ^= 1;
      if (kind === 'empty') artifacts = [Buffer.alloc(0)];
      if (kind === 'oversize') artifacts = [Buffer.alloc(65537)];
      if (kind === 'extra') artifacts = Array.from({ length: 5 }, () => Buffer.from('a'));
      expect(check({ ...envelope(0), artifacts }).bundleComplete).toBe(false);
    },
  );
  it('rejects aggregate excess before signature checks', () => {
    const item = {
      ...envelope(0),
      artifacts: Array.from({ length: 4 }, () => Buffer.alloc(65536)),
    };
    const result = verifyOfflineBundle(Array.from({ length: 5 }, () => item), context);
    expect(result.reasons).toEqual(['aggregate_limit']);
  });
  it('requires exactly both configured producers and bounds bundle count', () => {
    expect(check(envelope(0), envelope(0)).bundleComplete).toBe(false);
    expect(verifyOfflineBundle([], context).bundleComplete).toBe(false);
    const result = verifyOfflineBundle(Array.from({ length: 17 }, () => envelope(0)), context);
    expect(result.reasons).toEqual(['context_or_bundle_limit']);
  });
  it('refuses arbitrary key enrollment even from the context', () => {
    const producers = context.producers.map((item) => ({ ...item, publicKeyHex: '0'.repeat(64) }));
    const result = check(envelope(0), envelope(1), { ...context, producers });
    expect(result.reasons).toEqual(['fixture_producers']);
  });
  it('checks per-producer continuity while keeping priorBindingHead fixed', () => {
    const first = envelope(0, { end: false });
    const next = envelope(0, {
      sequence: 2,
      start: false,
      previousRecordDigest: createHash('sha256').update(first.frame).digest('hex'),
    });
    expect(verifyOfflineBundle([first, envelope(1), next], context)).toMatchObject({
      status: 'INVALID',
      signatureValid: false,
      bindingValid: true,
      bundleComplete: true,
    });
    const afterEnd = verifyOfflineBundle([envelope(0), envelope(1), next], context);
    expect(afterEnd.bundleComplete).toBe(false);
  });
  it('accepts exact artifact and aggregate caps structurally without authenticating them', () => {
    const artifact = Buffer.alloc(65536, 7);
    const artifacts = Array.from({ length: 4 }, () => artifact);
    const references = artifacts.map((bytes, index) => ({
      name: `fixture-${index}`,
      bytes: bytes.length,
      sha256: createHash('sha256').update(bytes).digest('hex'),
    }));
    const frames: OfflineEnvelope[] = [];
    for (let producer = 0; producer < 2; producer++) {
      const first = envelope(producer, { artifacts: references, end: false });
      frames.push({ ...first, artifacts });
      const second = envelope(producer, {
        artifacts: references,
        sequence: 2,
        start: false,
        previousRecordDigest: createHash('sha256').update(first.frame).digest('hex'),
      });
      frames.push({ ...second, artifacts });
    }
    expect(verifyOfflineBundle(frames, context)).toMatchObject({
      status: 'INVALID',
      signatureValid: false,
      bindingValid: true,
      bundleComplete: true,
    });
  });
});
