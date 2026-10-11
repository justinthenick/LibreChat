import { createHash } from 'node:crypto';
import type { Connection, mongo } from 'mongoose';

export interface CaptureIdentity {
  tenantId: string | null;
  ownerId: string;
}

export interface CaptureSource {
  _id: string;
  tenantId: string | null;
  generation: number;
  digest: string;
  upstreamRevision: string;
}

export interface CaptureDraft extends CaptureIdentity {
  _id: string;
  name: string;
  sourceId: string;
  sourceGeneration: number;
  sourceDigest: string;
  attempt: number;
  revision: number;
  status: 'initializing' | 'failed' | 'ready';
  digest: string | null;
}

export interface CapturePayload {
  digest: string;
  json: string;
}

type Reservation = Pick<
  CaptureDraft,
  '_id' | 'name' | 'sourceId' | 'sourceGeneration' | 'sourceDigest'
>;
type Transition = 'complete' | 'fail' | 'recover' | 'edit';

function sourceCopy(input: CaptureSource): CaptureSource {
  return {
    _id: input._id,
    tenantId: input.tenantId,
    generation: input.generation,
    digest: input.digest,
    upstreamRevision: input.upstreamRevision,
  };
}

function reservationCopy(input: Reservation): Reservation {
  return {
    _id: input._id,
    name: input.name,
    sourceId: input.sourceId,
    sourceGeneration: input.sourceGeneration,
    sourceDigest: input.sourceDigest,
  };
}

function draftCopy(input: CaptureDraft): CaptureDraft {
  return {
    ...reservationCopy(input),
    tenantId: input.tenantId,
    ownerId: input.ownerId,
    attempt: input.attempt,
    revision: input.revision,
    status: input.status,
    digest: input.digest,
  };
}

function payloadFields(input: CapturePayload): CapturePayload {
  return { digest: input.digest, json: input.json };
}

interface Receipt {
  _id: string;
  requestDigest: string;
  result: CaptureSource | CaptureDraft;
}

export interface CapturePersistence {
  commitSource: (
    operationId: string,
    actor: CaptureIdentity,
    source: CaptureSource,
    payload: CapturePayload,
  ) => Promise<CaptureSource>;
  reserve: (
    operationId: string,
    actor: CaptureIdentity,
    draft: Reservation,
  ) => Promise<CaptureDraft>;
  transition: (
    operationId: string,
    actor: CaptureIdentity,
    expected: CaptureDraft,
    action: Transition,
    payload?: CapturePayload,
  ) => Promise<CaptureDraft>;
  readSource: (id: string, tenantId: string | null) => Promise<CaptureSource | null>;
  readGeneration: (
    id: string,
    tenantId: string | null,
    generation: number,
  ) => Promise<CaptureSource | null>;
  readDraft: (id: string, actor: CaptureIdentity) => Promise<CaptureDraft | null>;
  readPayload: (digest: string) => Promise<string>;
  resolve: (operationId: string, requestDigest: string) => Promise<Receipt | null>;
}

const HASH = /^[a-f0-9]{64}$/;
const ID = /^[a-f0-9]{24}$/;

function reject(reason: string): never {
  throw new Error(`skill_capture_${reason}`);
}

export function captureDigest(value: string): string {
  return createHash('sha256').update(value).digest('hex');
}

type JsonValue = null | boolean | number | string | JsonValue[] | { [key: string]: JsonValue };

function canonicalJson(value: JsonValue): string {
  if (value === null || typeof value !== 'object') return JSON.stringify(value);
  if (Array.isArray(value)) return `[${value.map(canonicalJson).join(',')}]`;
  return `{${Object.keys(value)
    .sort()
    .map((key) => `${JSON.stringify(key)}:${canonicalJson(value[key])}`)
    .join(',')}}`;
}

/** Uses the same field projection/defaults as writes, including structurally richer inputs. */
export function captureRequestDigest(
  operation: 'source',
  actor: CaptureIdentity,
  source: CaptureSource,
  payload: CapturePayload,
): string;
export function captureRequestDigest(
  operation: 'reserve',
  actor: CaptureIdentity,
  request: Reservation,
): string;
export function captureRequestDigest(
  operation: Transition,
  actor: CaptureIdentity,
  draft: CaptureDraft,
  payload?: CapturePayload | null,
): string;
export function captureRequestDigest(
  operation: 'source' | 'reserve' | Transition,
  actor: CaptureIdentity,
  input: CaptureSource | CaptureDraft | Reservation,
  payload?: CapturePayload | null,
): string {
  const who = identity(actor);
  let fields: Array<CaptureSource | CaptureDraft | Reservation | CapturePayload | null>;
  if (operation === 'source') {
    if (!payload) reject('payload');
    fields = [sourceCopy(input as CaptureSource), payloadFields(payload)];
  } else if (operation === 'reserve') fields = [reservationCopy(input as Reservation)];
  else {
    if (!['complete', 'fail', 'recover', 'edit'].includes(operation)) reject('operation');
    fields = [draftCopy(input as CaptureDraft), payload ? payloadFields(payload) : null];
  }
  const tuple = JSON.parse(
    JSON.stringify([operation, who.tenantId, who.ownerId, ...fields]),
  ) as JsonValue;
  return captureDigest(canonicalJson(tuple));
}

function next(value: number): number {
  if (!Number.isSafeInteger(value) || value < 0 || value >= Number.MAX_SAFE_INTEGER)
    reject('counter');
  return value + 1;
}

function identity(actor: CaptureIdentity): CaptureIdentity {
  if (
    typeof actor.ownerId !== 'string' ||
    !actor.ownerId ||
    actor.ownerId.length > 256 ||
    (actor.tenantId !== null &&
      (typeof actor.tenantId !== 'string' || !actor.tenantId || actor.tenantId.length > 256))
  )
    reject('identity');
  return { tenantId: actor.tenantId, ownerId: actor.ownerId };
}

function payloadCopy(payload: CapturePayload): CapturePayload {
  if (
    typeof payload.json !== 'string' ||
    Buffer.byteLength(payload.json) > 8 * 1024 * 1024 ||
    !HASH.test(payload.digest) ||
    captureDigest(payload.json) !== payload.digest
  )
    reject('payload');
  JSON.parse(payload.json);
  return payloadFields(payload);
}

/** No live factory exists until all authorization writers participate in a commit-time fence. */
export function activateSkillCapturePersistence(): never {
  return reject('authorization_unavailable');
}

/** Storage proof only: opaque, previously validated bundle JSON; no application authorization. */
export async function createIsolatedCapturePersistence(
  connection: Connection,
): Promise<CapturePersistence> {
  const db = connection.db;
  if (!db || !/^test_skill_capture_[a-z0-9_]+$/.test(db.databaseName)) reject('isolation_required');
  const hello = await db.admin().command({ hello: 1 });
  if (!hello.setName || hello.logicalSessionTimeoutMinutes == null)
    reject('transactions_unavailable');
  const sources = db.collection<CaptureSource>('capture_sources');
  const drafts = db.collection<CaptureDraft>('capture_drafts');
  const blobs = db.collection<{ _id: string; json: string }>('capture_blobs');
  const generations = db.collection<CaptureSource & { sourceId: string }>('capture_generations');
  const receipts = db.collection<Receipt>('capture_receipts');
  await sources.createIndex({ tenantId: 1 });
  await drafts.createIndex({ tenantId: 1, ownerId: 1, name: 1 }, { unique: true });
  await blobs.createIndex({ _id: 1 });
  await generations.createIndex({ sourceId: 1, generation: 1 }, { unique: true });
  await receipts.createIndex({ _id: 1 });

  async function persistPayload(
    payload: CapturePayload,
    session: mongo.ClientSession,
  ): Promise<void> {
    const existing = await blobs.findOne({ _id: payload.digest }, { session });
    if (existing) {
      if (existing.json !== payload.json) reject('payload_corrupt');
      return;
    }
    await blobs.insertOne({ _id: payload.digest, json: payload.json }, { session });
  }

  async function transact<T extends CaptureSource | CaptureDraft>(
    operationId: string,
    requestDigest: string,
    write: (session: mongo.ClientSession) => Promise<T>,
  ): Promise<T> {
    if (typeof operationId !== 'string' || !/^[a-zA-Z0-9_-]{1,128}$/.test(operationId))
      reject('operation_id');
    const session = await connection.startSession();
    try {
      session.startTransaction({
        readConcern: { level: 'snapshot' },
        writeConcern: { w: 'majority', j: true },
        readPreference: 'primary',
      });
      if (await receipts.findOne({ _id: operationId }, { session })) reject('operation_exists');
      const result = await write(session);
      await receipts.insertOne({ _id: operationId, requestDigest, result }, { session });
      await session.commitTransaction();
      return result;
    } catch (error) {
      if (session.inTransaction()) await session.abortTransaction().catch(() => undefined);
      throw error;
    } finally {
      await session.endSession();
    }
  }

  async function commitSource(
    operationId: string,
    inputActor: CaptureIdentity,
    input: CaptureSource,
    inputPayload: CapturePayload,
  ): Promise<CaptureSource> {
    const actor = identity(inputActor);
    const source = sourceCopy(input);
    const payload = payloadCopy(inputPayload);
    if (
      typeof source._id !== 'string' ||
      !ID.test(source._id) ||
      source.tenantId !== actor.tenantId ||
      source.digest !== payload.digest ||
      typeof source.upstreamRevision !== 'string' ||
      !/^(?:[a-f0-9]{40}|[a-f0-9]{64})$/.test(source.upstreamRevision)
    )
      reject('source');
    const result = { ...source, generation: next(source.generation) };
    const requestDigest = captureRequestDigest('source', actor, source, payload);
    return transact(operationId, requestDigest, async (session) => {
      await persistPayload(payload, session);
      if (source.generation === 0) await sources.insertOne(result, { session });
      else {
        const changed = await sources.replaceOne(
          { _id: source._id, tenantId: actor.tenantId, generation: source.generation },
          result,
          { session },
        );
        if (changed.modifiedCount !== 1) reject('conflict');
      }
      await generations.insertOne(
        { ...result, sourceId: source._id, _id: `${source._id}:${result.generation}` },
        { session },
      );
      return result;
    });
  }

  async function reserve(
    operationId: string,
    inputActor: CaptureIdentity,
    input: Reservation,
  ): Promise<CaptureDraft> {
    const actor = identity(inputActor);
    const request = reservationCopy(input);
    if (
      typeof request._id !== 'string' ||
      typeof request.sourceId !== 'string' ||
      typeof request.name !== 'string' ||
      typeof request.sourceDigest !== 'string' ||
      !ID.test(request._id) ||
      !ID.test(request.sourceId) ||
      request._id === request.sourceId ||
      !/^[a-z0-9][a-z0-9-]{0,63}$/.test(request.name) ||
      !HASH.test(request.sourceDigest) ||
      request.sourceGeneration < 1
    )
      reject('draft');
    next(request.sourceGeneration);
    return transact(
      operationId,
      captureRequestDigest('reserve', actor, request),
      async (session) => {
        const source = await generations.findOne(
          {
            sourceId: request.sourceId,
            tenantId: actor.tenantId,
            generation: request.sourceGeneration,
            digest: request.sourceDigest,
          },
          { session },
        );
        if (!source) reject('source_missing');
        const existing = await drafts.findOne({ _id: request._id }, { session });
        if (existing) {
          if (
            existing.tenantId !== actor.tenantId ||
            existing.ownerId !== actor.ownerId ||
            existing.name !== request.name ||
            existing.sourceId !== request.sourceId ||
            existing.status !== 'ready'
          )
            reject('conflict');
          return existing;
        }
        const result: CaptureDraft = {
          ...request,
          ...actor,
          attempt: 1,
          revision: 1,
          status: 'initializing',
          digest: null,
        };
        await drafts.insertOne(result, { session });
        return result;
      },
    );
  }

  async function transition(
    operationId: string,
    inputActor: CaptureIdentity,
    input: CaptureDraft,
    action: Transition,
    inputPayload?: CapturePayload,
  ): Promise<CaptureDraft> {
    const actor = identity(inputActor);
    const expected = draftCopy(input);
    const payload = inputPayload ? payloadCopy(inputPayload) : null;
    if (
      expected.tenantId !== actor.tenantId ||
      expected.ownerId !== actor.ownerId ||
      !['complete', 'fail', 'recover', 'edit'].includes(action)
    )
      reject('identity');
    if (
      typeof expected._id !== 'string' ||
      !ID.test(expected._id) ||
      typeof expected.sourceId !== 'string' ||
      !ID.test(expected.sourceId) ||
      typeof expected.name !== 'string' ||
      !/^[a-z0-9][a-z0-9-]{0,63}$/.test(expected.name) ||
      typeof expected.sourceDigest !== 'string' ||
      !HASH.test(expected.sourceDigest) ||
      !['initializing', 'failed', 'ready'].includes(expected.status) ||
      (expected.status === 'ready'
        ? typeof expected.digest !== 'string' || !HASH.test(expected.digest)
        : expected.digest !== null) ||
      expected.attempt < 1 ||
      expected.revision < 1 ||
      expected.sourceGeneration < 1
    )
      reject('draft');
    next(expected.attempt);
    next(expected.sourceGeneration);
    const result = { ...expected, revision: next(expected.revision) };
    if (action === 'edit') {
      if (expected.status !== 'ready' || !payload) reject('state');
      result.digest = payload.digest;
    } else if (action === 'recover') {
      if (expected.status === 'ready' || payload) reject('state');
      result.attempt = next(expected.attempt);
      result.status = 'initializing';
    } else {
      if (expected.status !== 'initializing' || (action === 'complete') !== (payload !== null))
        reject('state');
      result.status = action === 'complete' ? 'ready' : 'failed';
      result.digest = payload?.digest ?? null;
    }
    return transact(
      operationId,
      captureRequestDigest(action, actor, expected, payload),
      async (session) => {
        if (payload) await persistPayload(payload, session);
        const changed = await drafts.replaceOne(expected, result, { session });
        if (changed.modifiedCount !== 1) reject('conflict');
        return result;
      },
    );
  }

  return {
    commitSource,
    reserve,
    transition,
    readSource: (id, tenantId) =>
      sources.findOne(
        { _id: id, tenantId },
        { readPreference: 'primary', readConcern: { level: 'majority' } },
      ),
    readGeneration: async (id, tenantId, generation) => {
      const record = await generations.findOne(
        { sourceId: id, tenantId, generation },
        { readPreference: 'primary', readConcern: { level: 'majority' } },
      );
      return record ? sourceCopy({ ...record, _id: record.sourceId }) : null;
    },
    readDraft: (id, actor) =>
      drafts.findOne(
        { _id: id, ...identity(actor) },
        { readPreference: 'primary', readConcern: { level: 'majority' } },
      ),
    readPayload: async (digest) => {
      if (!HASH.test(digest)) reject('payload');
      const blob = await blobs.findOne(
        { _id: digest },
        { readPreference: 'primary', readConcern: { level: 'majority' } },
      );
      if (!blob || captureDigest(blob.json) !== digest) reject('payload_corrupt');
      return blob.json;
    },
    resolve: async (operationId, requestDigest) => {
      if (!HASH.test(requestDigest)) reject('receipt');
      const receipt = await receipts.findOne(
        { _id: operationId },
        { readPreference: 'primary', readConcern: { level: 'majority' } },
      );
      if (receipt && receipt.requestDigest !== requestDigest) reject('receipt_mismatch');
      return receipt;
    },
  };
}
