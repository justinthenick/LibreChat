import path from 'node:path';
import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import type { OfflineContext, OfflineEnvelope, OfflineVerdict } from './verify';
import fixtures from './fixtures/signed-profile.json';
import { verifyOfflineBundle } from './verify';

function hash(bytes: Uint8Array): string {
  return createHash('sha256').update(bytes).digest('hex');
}

function load(index: number): { context: OfflineContext; envelopes: OfflineEnvelope[] } {
  const fixture = fixtures.bundles[index];
  return {
    context: structuredClone(fixture.expectedContext) as OfflineContext,
    envelopes: fixture.records.map((record) => ({
      frame: Buffer.from(record.frameHex, 'hex'),
      signature: Buffer.from(record.signatureHex, 'hex'),
      artifacts: record.artifacts.map((artifact) => Buffer.from(artifact.bytesHex, 'hex')),
    })),
  };
}

function noAuthority(result: OfflineVerdict): void {
  expect(result).toMatchObject({
    syntheticOnly: true,
    liveAuthority: false,
    stopConfirmed: false,
    reservationReleased: false,
    quarantineClearance: false,
  });
}

function reject(envelopes: OfflineEnvelope[], context: OfflineContext): OfflineVerdict {
  const result = verifyOfflineBundle(envelopes, context);
  noAuthority(result);
  expect(result.status).toBe('INVALID');
  return result;
}

describe('independently produced signed synthetic profile fixtures', () => {
  it('pins exact public bytes, provenance and hashes without running a signer', () => {
    const bytes = readFileSync(path.join(__dirname, 'fixtures/signed-profile.json'));
    expect(hash(bytes)).toBe('855860970e67db44582ba342f552c48554932437a1ffe0e95f184ed15590dd6e');
    expect(fixtures.specSha256).toBe(
      '96c7e775625b04565f1009227c90ffc62078d90f75922c55e77423520e093cf8',
    );
    expect(fixtures.provenance.primitiveLibraryDiversityClaimed).toBe(false);
    expect(fixtures.bundles).toHaveLength(2);
    for (const bundle of fixtures.bundles) {
      for (const record of bundle.records) {
        expect(hash(Buffer.from(record.frameHex, 'hex'))).toBe(record.frameSha256);
        expect(hash(Buffer.from(record.signatureHex, 'hex'))).toBe(record.signatureSha256);
        for (const artifact of record.artifacts) {
          expect(hash(Buffer.from(artifact.bytesHex, 'hex'))).toBe(artifact.sha256);
        }
      }
    }
  });

  it.each([0, 1])('verifies fixed complete bundle %i with no live authority', (index) => {
    const { context, envelopes } = load(index);
    const result = verifyOfflineBundle(envelopes, context);
    const expected = fixtures.bundles[index].expectedResult;
    noAuthority(result);
    expect(result).toMatchObject({
      status: expected.status,
      signatureValid: expected.signatureValidity,
      bindingValid: expected.bindingValidity,
      bundleComplete: expected.bundleCompleteness,
      reasons: [],
    });
  });

  it.each([
    'reviewId',
    'attemptId',
    'runtimeEpoch',
    'reservationId',
    'mappingDigest',
    'priorBindingHead',
    'challenge',
    'sourceDigest',
    'binaryDigest',
    'configDigest',
    'generation',
    'ownerEpoch',
  ])('keeps real signatures distinct from wrong expected binding %s', (field) => {
    const { context, envelopes } = load(0);
    const original = context[field as keyof OfflineContext];
    let value: string | number = 'a'.repeat(64);
    if (typeof original === 'number') value = 2;
    else if (typeof original === 'string' && original.length === 36) {
      value = 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa';
    }
    const result = reject(envelopes, { ...context, [field]: value });
    expect(result.signatureValid).toBe(true);
    expect(result.bindingValid).toBe(false);
    expect(result.reasons).toContain('binding');
  });

  it('rejects a changed signed challenge without regenerating its signature', () => {
    const { context, envelopes } = load(0);
    const bytes = Buffer.from(envelopes[0].frame);
    const position = bytes.indexOf(Buffer.from(context.challenge, 'ascii'));
    expect(position).toBeGreaterThan(0);
    bytes[position] = bytes[position] === 97 ? 98 : 97;
    envelopes[0] = { ...envelopes[0], frame: bytes };
    const result = reject(envelopes, context);
    expect(result.signatureValid).toBe(false);
    expect(result.bindingValid).toBe(false);
    expect(result.reasons).toEqual(expect.arrayContaining(['signature', 'binding']));
  });

  it('rejects a damaged detached signature', () => {
    const { context, envelopes } = load(0);
    const signature = Buffer.from(envelopes[0].signature);
    signature[0] ^= 1;
    envelopes[0] = { ...envelopes[0], signature };
    const result = reject(envelopes, context);
    expect(result).toMatchObject({
      signatureValid: false,
      bindingValid: true,
      bundleComplete: true,
    });
  });

  it('rejects the wrong allowed fixture key without enrolling another key', () => {
    const { context, envelopes } = load(0);
    const producers = context.producers.map((producer, index) => ({
      ...producer,
      publicKeyHex: context.producers[1 - index].publicKeyHex,
    }));
    const result = reject(envelopes, { ...context, producers });
    expect(result).toMatchObject({
      signatureValid: false,
      bindingValid: true,
      bundleComplete: true,
    });
  });

  it.each(['role', 'keyId', 'producerEpoch', 'clockDomain'])(
    'rejects expected producer binding %s while preserving signature evidence',
    (field) => {
      const { context, envelopes } = load(0);
      const producers = context.producers.map((producer, index) => {
        let value = 'other-fixture';
        if (field === 'role') value = index === 0 ? 'host' : 'guest';
        if (field === 'keyId') value = `other-fixture-${index}`;
        if (field === 'producerEpoch') value = 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa';
        return { ...producer, [field]: value };
      });
      const result = reject(envelopes, { ...context, producers });
      expect(result.signatureValid).toBe(true);
      expect(result.bindingValid).toBe(false);
      expect(result.reasons).toContain('binding');
    },
  );

  it('detects changed raw bytes despite valid signatures over artifact references', () => {
    const { context, envelopes } = load(0);
    const bytes = Buffer.from(envelopes[0].artifacts[0]);
    bytes[0] ^= 1;
    envelopes[0] = { ...envelopes[0], artifacts: [bytes] };
    const result = reject(envelopes, context);
    expect(result).toMatchObject({
      signatureValid: true,
      bindingValid: true,
      bundleComplete: false,
    });
    expect(result.reasons).toContain('artifact_binding');
  });

  it.each(['drop-end', 'reorder', 'replay', 'omit-producer'])(
    'rejects incomplete signed sequences: %s',
    (change) => {
      const { context, envelopes } = load(1);
      let changed = envelopes;
      if (change === 'drop-end') changed = envelopes.filter((_, index) => index !== 1);
      if (change === 'reorder') changed = [envelopes[1], envelopes[0], ...envelopes.slice(2)];
      if (change === 'replay') changed = [...envelopes, envelopes[0]];
      if (change === 'omit-producer') changed = envelopes.slice(0, 2);
      const result = reject(changed, context);
      expect(result.signatureValid).toBe(true);
      expect(result.bundleComplete).toBe(false);
    },
  );

  it('rejects trailing bytes instead of verifying a prefix', () => {
    const { context, envelopes } = load(0);
    envelopes[0] = {
      ...envelopes[0],
      frame: Buffer.concat([envelopes[0].frame, Buffer.from('x')]),
    };
    expect(reject(envelopes, context).reasons).toContain('frame_or_schema');
  });
});
