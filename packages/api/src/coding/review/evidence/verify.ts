import { z } from 'zod';
import { createHash, createPublicKey, verify } from 'node:crypto';

type Json = boolean | number | string | Json[] | { [key: string]: Json };
type Role = 'guest' | 'host';
type Binding = {
  profile: 'S4-OFFLINE-1';
  policyVersion: 1;
  reviewId: string;
  attemptId: string;
  generation: number;
  ownerEpoch: number;
  runtimeEpoch: string;
  reservationId: string;
  mappingDigest: string;
  priorBindingHead: string;
  challenge: string;
  sourceDigest: string;
  binaryDigest: string;
  configDigest: string;
};
type Producer = {
  keyId: string;
  producerId: string;
  role: Role;
  producerEpoch: string;
  clockDomain: string;
  publicKeyHex: string;
};
export type OfflineContext = Binding & { producers: readonly Producer[] };
export interface OfflineEnvelope {
  frame: Uint8Array;
  signature: Uint8Array;
  artifacts: readonly Uint8Array[];
}
export interface OfflineVerdict {
  status: 'OFFLINE_PROFILE_VALID' | 'INVALID';
  syntheticOnly: true;
  signatureValid: boolean;
  bindingValid: boolean;
  bundleComplete: boolean;
  reasons: string[];
  liveAuthority: false;
  stopConfirmed: false;
  reservationReleased: false;
  quarantineClearance: false;
}

const domain = Buffer.from('LibreChat/Supervisor/observation/S4-OFFLINE-1\0', 'ascii');
const payloadLimit = 16384;
const frameLimit = domain.length + 4 + payloadLimit;
const publicFixtures = [
  'd75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a',
  '3d4017c3e843895a92b70aa74d1b7ebc9c982ccf2ec4968cc0cd55f12af4660c',
];
const text = z
  .string()
  .min(1)
  .max(256)
  .regex(/^[\x21-\x7e](?:[\x20-\x7e]*[\x21-\x7e])?(?![\s\S])/);
const uuid = z.string().regex(/^[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}(?![\s\S])/);
const digest = z.string().regex(/^[0-9a-f]{64}(?![\s\S])/);
const counter = z.number().int().min(0).max(Number.MAX_SAFE_INTEGER);
const positive = counter.min(1);
const binding = {
  profile: z.literal('S4-OFFLINE-1'),
  policyVersion: z.literal(1),
  reviewId: uuid,
  attemptId: uuid,
  generation: positive,
  ownerEpoch: positive,
  runtimeEpoch: uuid,
  reservationId: uuid,
  mappingDigest: digest,
  priorBindingHead: digest,
  challenge: digest,
  sourceDigest: digest,
  binaryDigest: digest,
  configDigest: digest,
};
const producer = {
  keyId: text,
  producerId: text,
  role: z.enum(['guest', 'host']),
  producerEpoch: uuid,
  clockDomain: text,
};
const contextSchema = z
  .object({
    ...binding,
    producers: z.array(z.object({ ...producer, publicKeyHex: digest }).strict()).length(2),
  })
  .strict();
const payloadSchema = z
  .object({
    ...binding,
    ...producer,
    observationKind: z.literal('fixture_observation'),
    sequence: positive,
    previousRecordDigest: digest,
    start: z.boolean(),
    end: z.boolean(),
    intervalStart: counter,
    intervalEnd: counter,
    limitationCodes: z.tuple([z.literal('NO_RUNTIME_OBSERVATION'), z.literal('SYNTHETIC_ONLY')]),
    artifacts: z
      .array(
        z
          .object({ name: text, bytes: z.number().int().min(1).max(65536), sha256: digest })
          .strict(),
      )
      .min(1)
      .max(4),
  })
  .strict();
type Payload = z.infer<typeof payloadSchema>;

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

function hash(bytes: Uint8Array): string {
  return createHash('sha256').update(bytes).digest('hex');
}

function verdict(
  signatureValid: boolean,
  bindingValid: boolean,
  bundleComplete: boolean,
  reasons: string[],
): OfflineVerdict {
  return {
    status: signatureValid && bindingValid && bundleComplete ? 'OFFLINE_PROFILE_VALID' : 'INVALID',
    syntheticOnly: true,
    signatureValid,
    bindingValid,
    bundleComplete,
    reasons,
    liveAuthority: false,
    stopConfirmed: false,
    reservationReleased: false,
    quarantineClearance: false,
  };
}

/** Primitive mechanics only: caller-supplied public bytes never establish producer trust. */
export function verifyPublicFixture(
  message: Uint8Array,
  publicKey: Uint8Array,
  signature: Uint8Array,
): boolean {
  if (
    !(message instanceof Uint8Array) ||
    !(publicKey instanceof Uint8Array) ||
    !(signature instanceof Uint8Array)
  ) {
    return false;
  }
  if (
    message.byteLength > frameLimit ||
    publicKey.byteLength !== 32 ||
    signature.byteLength !== 64
  ) {
    return false;
  }
  try {
    const key = createPublicKey({
      key: Buffer.concat([Buffer.from('302a300506032b6570032100', 'hex'), publicKey]),
      format: 'der',
      type: 'spki',
    });
    return verify(null, message, key, signature);
  } catch {
    return false;
  }
}

function parseFrame(frame: Uint8Array): Payload | undefined {
  const bytes = Buffer.from(frame);
  if (bytes.length < domain.length + 4 || bytes.length > frameLimit) return;
  if (!bytes.subarray(0, domain.length).equals(domain)) return;
  const size = bytes.readUInt32BE(domain.length);
  if (size > payloadLimit || bytes.length !== domain.length + 4 + size) return;
  const raw = bytes.subarray(domain.length + 4);
  if (raw.some((byte) => byte > 127)) return;
  try {
    const parsed = payloadSchema.safeParse(JSON.parse(raw.toString('ascii')));
    if (!parsed.success || canonical(parsed.data) !== raw.toString('ascii')) return;
    if (parsed.data.intervalEnd < parsed.data.intervalStart) return;
    const names = new Set(parsed.data.artifacts.map((artifact) => artifact.name));
    if (names.size !== parsed.data.artifacts.length) return;
    return parsed.data;
  } catch {
    return;
  }
}

/** First-bundle fixture checking only; no durable replay decision, receipt or live authority. */
export function verifyOfflineBundle(
  envelopes: readonly OfflineEnvelope[],
  expected: OfflineContext,
): OfflineVerdict {
  const context = contextSchema.safeParse(expected);
  if (
    !context.success ||
    !Array.isArray(envelopes) ||
    envelopes.length < 2 ||
    envelopes.length > 16
  ) {
    return verdict(false, false, false, ['context_or_bundle_limit']);
  }
  const producers = context.data.producers;
  if (
    new Set(producers.map((item) => item.producerId)).size !== 2 ||
    new Set(producers.map((item) => item.keyId)).size !== 2 ||
    new Set(producers.map((item) => item.role)).size !== 2 ||
    new Set(producers.map((item) => item.publicKeyHex)).size !== 2 ||
    producers.some((item) => !publicFixtures.includes(item.publicKeyHex))
  ) {
    return verdict(false, false, false, ['fixture_producers']);
  }
  let aggregate = 0;
  const payloads: Payload[] = [];
  const snapshots: OfflineEnvelope[] = [];
  for (const envelope of envelopes) {
    if (
      !envelope ||
      !(envelope.frame instanceof Uint8Array) ||
      !(envelope.signature instanceof Uint8Array) ||
      !Array.isArray(envelope.artifacts) ||
      envelope.artifacts.length < 1 ||
      envelope.artifacts.length > 4 ||
      envelope.frame.byteLength > frameLimit ||
      envelope.signature.byteLength !== 64
    ) {
      return verdict(false, false, false, ['envelope_limit']);
    }
    for (const artifact of envelope.artifacts) {
      if (
        !(artifact instanceof Uint8Array) ||
        artifact.byteLength < 1 ||
        artifact.byteLength > 65536
      ) {
        return verdict(false, false, false, ['artifact_limit']);
      }
      aggregate += artifact.byteLength;
      if (aggregate > 1048576) return verdict(false, false, false, ['aggregate_limit']);
    }
    const snapshot = {
      frame: Buffer.from(envelope.frame),
      signature: Buffer.from(envelope.signature),
      artifacts: envelope.artifacts.map((bytes: Uint8Array) => Buffer.from(bytes)),
    };
    const payload = parseFrame(snapshot.frame);
    if (!payload) return verdict(false, false, false, ['frame_or_schema']);
    payloads.push(payload);
    snapshots.push(snapshot);
  }
  let signatures = true;
  let bindings = true;
  let complete = true;
  const reasons = new Set<string>();
  const cursors = new Map<string, { sequence: number; digest: string; ended: boolean }>();
  for (let index = 0; index < snapshots.length; index++) {
    const envelope = snapshots[index];
    const payload = payloads[index];
    const expectedProducer = producers.find((item) => item.producerId === payload.producerId);
    if (!expectedProducer) {
      signatures = false;
      bindings = false;
      complete = false;
      reasons.add('unknown_producer');
      continue;
    }
    const identityMatches = Object.keys(binding).every(
      (key) => payload[key as keyof Binding] === context.data[key as keyof Binding],
    );
    const producerMatches = Object.keys(producer).every(
      (key) =>
        payload[key as keyof typeof producer] === expectedProducer[key as keyof typeof producer],
    );
    if (!identityMatches || !producerMatches) {
      bindings = false;
      reasons.add('binding');
    }
    const publicKey = Buffer.from(expectedProducer.publicKeyHex, 'hex');
    if (!verifyPublicFixture(envelope.frame, publicKey, envelope.signature)) {
      signatures = false;
      reasons.add('signature');
    }
    const prior = cursors.get(payload.producerId);
    if (
      payload.sequence !== (prior?.sequence ?? 0) + 1 ||
      payload.previousRecordDigest !== (prior?.digest ?? '0'.repeat(64)) ||
      payload.start !== !prior ||
      prior?.ended
    ) {
      complete = false;
      reasons.add('sequence_or_boundary');
    }
    cursors.set(payload.producerId, {
      sequence: payload.sequence,
      digest: hash(envelope.frame),
      ended: payload.end,
    });
    if (
      payload.artifacts.length !== envelope.artifacts.length ||
      payload.artifacts.some((artifact, position) => {
        const bytes = envelope.artifacts[position];
        return !bytes || artifact.bytes !== bytes.byteLength || artifact.sha256 !== hash(bytes);
      })
    ) {
      complete = false;
      reasons.add('artifact_binding');
    }
  }
  if (producers.some((item) => !cursors.get(item.producerId)?.ended)) {
    complete = false;
    reasons.add('missing_end_or_producer');
  }
  return verdict(signatures, bindings, complete, [...reasons].sort());
}
