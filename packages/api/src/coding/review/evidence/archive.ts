import path from 'node:path';
import { createHash } from 'node:crypto';
import { closeSync, openSync, readSync } from 'node:fs';
import type catalog from './fixtures/signed-profile.json';
import type { OfflineContext } from './verify';
import { verifyOfflineBundle } from './verify';
import { protocolJson } from '../protocol';

const catalogSha = '855860970e67db44582ba342f552c48554932437a1ffe0e95f184ed15590dd6e';
const archiveClass = 'S6_FIXED_SYNTHETIC_ARCHIVE';
const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;

function hash(bytes: Uint8Array): string {
  return createHash('sha256').update(bytes).digest('hex');
}

function identifier(value: string): void {
  if (typeof value !== 'string' || value.length !== 36 || !uuid.test(value)) {
    throw new Error('Invalid fixture identity');
  }
}

/** Fixed public catalog only. No signer, trust input, normal journal routing or live receipt. */
export function fixtureArchiveRequest(
  namespace: string,
  operationId: string,
  ownerEpoch: number,
  expectedVersion: number,
  bundleIndex: number,
): string {
  identifier(namespace);
  identifier(operationId);
  if (
    !Number.isSafeInteger(ownerEpoch) ||
    ownerEpoch < 1 ||
    !Number.isSafeInteger(expectedVersion) ||
    expectedVersion < 0 ||
    !Number.isInteger(bundleIndex) ||
    bundleIndex < 0 ||
    bundleIndex > 1
  ) {
    throw new Error('Invalid fixture fence');
  }
  const descriptor = openSync(path.join(__dirname, 'fixtures/signed-profile.json'), 'r');
  const buffer = Buffer.alloc(131073);
  let length = 0;
  try {
    while (length < buffer.length) {
      const count = readSync(descriptor, buffer, length, buffer.length - length, null);
      if (count === 0) break;
      length += count;
    }
  } finally {
    closeSync(descriptor);
  }
  const raw = buffer.subarray(0, length);
  if (raw.length > 131072 || hash(raw) !== catalogSha) throw new Error('Catalog mismatch');
  const snapshot = JSON.parse(raw.toString('ascii')) as typeof catalog;
  const bundle = snapshot.bundles[bundleIndex];
  const context = Buffer.from(protocolJson(bundle.expectedContext), 'ascii');
  const envelopes = bundle.records.map((record) => ({
    frame: Buffer.from(record.frameHex, 'hex'),
    signature: Buffer.from(record.signatureHex, 'hex'),
    artifacts: record.artifacts.map((artifact) => Buffer.from(artifact.bytesHex, 'hex')),
  }));
  const verdict = verifyOfflineBundle(envelopes, bundle.expectedContext as OfflineContext);
  if (
    verdict.status !== 'OFFLINE_PROFILE_VALID' ||
    !verdict.signatureValid ||
    !verdict.bindingValid ||
    !verdict.bundleComplete ||
    !verdict.syntheticOnly ||
    verdict.liveAuthority ||
    verdict.stopConfirmed ||
    verdict.reservationReleased ||
    verdict.quarantineClearance
  ) {
    throw new Error('Invalid synthetic bundle');
  }
  const manifest = {
    version: 1,
    class: archiveClass,
    catalog_sha256: catalogSha,
    bundle_index: bundleIndex,
    context_sha256: hash(context),
    context_bytes: context.length,
    records: envelopes.map(({ frame, signature, artifacts }) => ({
      frame_sha256: hash(frame),
      frame_bytes: frame.length,
      signature_sha256: hash(signature),
      signature_bytes: signature.length,
      artifacts: artifacts.map((bytes) => ({ sha256: hash(bytes), bytes: bytes.length })),
    })),
  };
  const bytes = Buffer.from(protocolJson(manifest), 'ascii');
  if (context.length > 8192 || bytes.length > 16384) throw new Error('Archive limit');
  const digest = hash(
    Buffer.concat([
      Buffer.from('LibreChat/Supervisor/S6-fixed-fixture-bundle/1\0', 'ascii'),
      bytes,
    ]),
  );
  return protocolJson({
    version: 1,
    kind: 'fixture_bundle_append',
    namespace,
    operation_id: operationId,
    owner_epoch: ownerEpoch,
    expected_version: expectedVersion,
    catalog_sha256: catalogSha,
    bundle_index: bundleIndex,
    bundle_digest: digest,
  });
}

export type SyntheticArchiveReceipt = {
  version: 1;
  kind: 'synthetic_bundle_archived';
  class: 'S6_FIXED_SYNTHETIC_ARCHIVE';
  namespace: string;
  operation_id: string;
  bundle_digest: string;
  catalog_sha256: string;
  bundle_index: number;
  committed_version: number;
  accepted_owner_epoch: number;
  synthetic_only: true;
  live_authority: false;
  stop_confirmed: false;
  reservation_released: false;
  quarantine_clearance: false;
  result_publication_authority: false;
};

/** Parse a historical archive receipt against its original request, never current authority. */
export function parseFixtureReceipt(raw: string, request: string): SyntheticArchiveReceipt {
  if (Buffer.byteLength(raw) > 4096 || Buffer.byteLength(request) > 2048) {
    throw new Error('Receipt limit');
  }
  const value = JSON.parse(raw) as SyntheticArchiveReceipt;
  const original = JSON.parse(request) as {
    namespace: string;
    operation_id: string;
    owner_epoch: number;
    expected_version: number;
    bundle_index: number;
    bundle_digest: string;
  };
  if (
    request !==
    fixtureArchiveRequest(
      original.namespace,
      original.operation_id,
      original.owner_epoch,
      original.expected_version,
      original.bundle_index,
    )
  ) {
    throw new Error('Invalid original fixture request');
  }
  const expected = {
    version: 1,
    kind: 'synthetic_bundle_archived',
    class: archiveClass,
    namespace: original.namespace,
    operation_id: original.operation_id,
    bundle_digest: original.bundle_digest,
    catalog_sha256: catalogSha,
    bundle_index: original.bundle_index,
    committed_version: value.committed_version,
    accepted_owner_epoch: value.accepted_owner_epoch,
    synthetic_only: true,
    live_authority: false,
    stop_confirmed: false,
    reservation_released: false,
    quarantine_clearance: false,
    result_publication_authority: false,
  };
  if (
    protocolJson(value) !== raw ||
    protocolJson(expected) !== raw ||
    !Number.isSafeInteger(value.committed_version) ||
    value.committed_version < 1 ||
    !Number.isSafeInteger(value.accepted_owner_epoch) ||
    value.accepted_owner_epoch < 1
  ) {
    throw new Error('Invalid synthetic receipt');
  }
  return value;
}
