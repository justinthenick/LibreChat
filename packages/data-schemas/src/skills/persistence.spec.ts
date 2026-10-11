import mongoose from 'mongoose';
import { MongoMemoryReplSet, MongoMemoryServer } from 'mongodb-memory-server';
import type { Connection } from 'mongoose';
import type {
  CaptureDraft,
  CaptureIdentity,
  CapturePayload,
  CapturePersistence,
  CaptureSource,
} from './persistence';
import {
  activateSkillCapturePersistence,
  captureDigest,
  captureRequestDigest,
  createIsolatedCapturePersistence,
} from './persistence';

const actor: CaptureIdentity = { tenantId: 'tenant-a', ownerId: 'owner-a' };
const sourceId = 'a'.repeat(24);
const draftId = 'b'.repeat(24);
const upstreamRevision = 'c'.repeat(40);
let server: MongoMemoryReplSet;
let connection: Connection;
let store: CapturePersistence;

function payload(body = 'original'): CapturePayload {
  const json = JSON.stringify({
    definition: { body },
    files: [{ path: 'data.txt', base64: Buffer.from(body).toString('base64') }],
  });
  return { json, digest: captureDigest(json) };
}

function candidate(generation = 0, content = payload()): CaptureSource {
  return {
    _id: sourceId,
    tenantId: actor.tenantId,
    generation,
    digest: content.digest,
    upstreamRevision,
  };
}

function request(source: CaptureSource, id = draftId) {
  return {
    _id: id,
    name: 'example-draft',
    sourceId: source._id,
    sourceGeneration: source.generation,
    sourceDigest: source.digest,
  };
}

async function initialize(): Promise<CaptureDraft> {
  const source = await store.commitSource('source', actor, candidate(), payload());
  return store.reserve('reserve', actor, request(source));
}

beforeAll(async () => {
  server = await MongoMemoryReplSet.create({ replSet: { count: 1, storageEngine: 'wiredTiger' } });
  connection = await mongoose
    .createConnection(server.getUri(), { dbName: 'test_skill_capture_persistence' })
    .asPromise();
  store = await createIsolatedCapturePersistence(connection);
}, 60000);

beforeEach(async () => {
  for (const collection of Object.values(connection.collections)) await collection.deleteMany({});
  for (const name of [
    'capture_sources',
    'capture_drafts',
    'capture_blobs',
    'capture_generations',
    'capture_receipts',
    'test_authority',
    'test_results',
  ])
    await connection.db!.collection(name).deleteMany({});
});

afterAll(async () => {
  await connection?.close();
  await server?.stop();
});

test('activation always fails closed, even with a transaction-capable database available', () => {
  expect(activateSkillCapturePersistence).toThrow('skill_capture_authorization_unavailable');
});

test('rejects an actual database outside the isolated namespace before creating collections', async () => {
  const other = await mongoose
    .createConnection(server.getUri(), { dbName: 'not_a_capture_test' })
    .asPromise();
  try {
    await expect(createIsolatedCapturePersistence(other)).rejects.toThrow(
      'skill_capture_isolation_required',
    );
    expect(await other.db!.listCollections().toArray()).toHaveLength(0);
  } finally {
    await other.close();
  }
});

test('standalone MongoDB fails closed without changing its mode', async () => {
  const standalone = await MongoMemoryServer.create();
  const other = await mongoose
    .createConnection(standalone.getUri(), { dbName: 'test_skill_capture_standalone' })
    .asPromise();
  try {
    await expect(createIsolatedCapturePersistence(other)).rejects.toThrow(
      'skill_capture_transactions_unavailable',
    );
    expect(await other.db!.listCollections().toArray()).toHaveLength(0);
  } finally {
    await other.close();
    await standalone.stop();
  }
}, 60000);

test('commits durable immutable bytes, source pointer, generation and receipt together', async () => {
  const content = payload();
  const source = candidate();
  const committed = await store.commitSource('commit', actor, source, content);
  expect(committed.generation).toBe(1);
  expect(await store.readPayload(content.digest)).toBe(content.json);
  expect(await store.readSource(sourceId, actor.tenantId)).toEqual(committed);
  expect(
    (await store.resolve('commit', captureRequestDigest('source', actor, source, content)))?.result,
  ).toEqual(committed);
});

test('concurrent source generation CAS selects exactly one winner', async () => {
  await store.commitSource('initial', actor, candidate(), payload());
  const outcomes = await Promise.allSettled(
    ['first', 'second'].map((body) =>
      store.commitSource(body, actor, candidate(1, payload(body)), payload(body)),
    ),
  );
  expect(outcomes.filter((r) => r.status === 'fulfilled')).toHaveLength(1);
  expect(outcomes.filter((r) => r.status === 'rejected')).toHaveLength(1);
  expect((await store.readSource(sourceId, actor.tenantId))?.generation).toBe(2);
  expect(await connection.db!.collection('capture_generations').countDocuments()).toBe(2);
  expect(await connection.db!.collection('capture_blobs').countDocuments()).toBe(2);
});

test('stale writes roll back staged bytes and cannot certify a partial commit', async () => {
  await store.commitSource('initial', actor, candidate(), payload());
  const content = payload('must-rollback');
  await expect(store.commitSource('stale', actor, candidate(3, content), content)).rejects.toThrow(
    'skill_capture_conflict',
  );
  expect(
    await connection
      .db!.collection<{ _id: string; json: string }>('capture_blobs')
      .countDocuments({ _id: content.digest }),
  ).toBe(0);
  expect(
    await store.resolve(
      'stale',
      captureRequestDigest('source', actor, candidate(3, content), content),
    ),
  ).toBeNull();
  expect((await store.readSource(sourceId, actor.tenantId))?.generation).toBe(1);
});

test.each(['truncated', 'digest'])('rejects %s payload corruption before staging', async (kind) => {
  const content = payload();
  if (kind === 'truncated') content.json = content.json.slice(0, -1);
  else content.digest = '0'.repeat(64);
  await expect(store.commitSource('bad', actor, candidate(), content)).rejects.toThrow(
    'skill_capture_payload',
  );
  expect(await connection.db!.collection('capture_blobs').countDocuments()).toBe(0);
});

test('stored payload corruption is detected and never overwritten on reuse', async () => {
  const content = payload();
  await store.commitSource('first', actor, candidate(), content);
  await connection
    .db!.collection<{ _id: string; json: string }>('capture_blobs')
    .updateOne({ _id: content.digest }, { $set: { json: '{}' } });
  await expect(store.readPayload(content.digest)).rejects.toThrow('skill_capture_payload_corrupt');
  await expect(store.commitSource('second', actor, candidate(1), content)).rejects.toThrow(
    'skill_capture_payload_corrupt',
  );
  expect((await store.readSource(sourceId, actor.tenantId))?.generation).toBe(1);
});

test('a draft pins one retained immutable generation despite later source advancement', async () => {
  const first = await store.commitSource('first', actor, candidate(), payload());
  const secondPayload = payload('new');
  await store.commitSource('second', actor, candidate(1, secondPayload), secondPayload);
  const draft = await store.reserve('reserve', actor, request(first));
  expect(draft.sourceGeneration).toBe(1);
  expect(await store.readPayload(draft.sourceDigest)).toBe(payload().json);
  await expect(
    store.reserve('mixed', actor, {
      ...request(first, 'd'.repeat(24)),
      sourceDigest: secondPayload.digest,
    }),
  ).rejects.toThrow('skill_capture_source_missing');
});

test.each(['id', 'name'])('concurrent reservation enforces unique %s in MongoDB', async (key) => {
  const source = await store.commitSource('source', actor, candidate(), payload());
  const first = request(source);
  const second = key === 'id' ? { ...first, name: 'other' } : { ...first, _id: 'd'.repeat(24) };
  const outcomes = await Promise.allSettled([
    store.reserve('one', actor, first),
    store.reserve('two', actor, second),
  ]);
  expect(outcomes.filter((r) => r.status === 'fulfilled')).toHaveLength(1);
  expect(await connection.db!.collection('capture_drafts').countDocuments()).toBe(1);
});

test('scope filters reject cross-tenant source pins and cross-owner draft transitions', async () => {
  const draft = await initialize();
  await expect(
    store.reserve(
      'cross-tenant',
      { ...actor, tenantId: 'tenant-b' },
      request({ ...candidate(), generation: 1 }, 'e'.repeat(24)),
    ),
  ).rejects.toThrow('skill_capture_source_missing');
  await expect(
    store.transition('cross-owner', { ...actor, ownerId: 'owner-b' }, draft, 'fail'),
  ).rejects.toThrow('skill_capture_identity');
  expect(await store.readDraft(draftId, { ...actor, ownerId: 'owner-b' })).toBeNull();
});

test('pending and failed reservations cannot be reused as ready drafts', async () => {
  const draft = await initialize();
  const source = (await store.readSource(sourceId, actor.tenantId))!;
  await expect(store.reserve('pending-reuse', actor, request(source))).rejects.toThrow(
    'skill_capture_conflict',
  );
  await store.transition('fail', actor, draft, 'fail');
  await expect(store.reserve('failed-reuse', actor, request(source))).rejects.toThrow(
    'skill_capture_conflict',
  );
});

test('recovery fences stale completion, failure and recovery proposals', async () => {
  const original = await initialize();
  const recovered = await store.transition('recover', actor, original, 'recover');
  expect(recovered.attempt).toBe(2);
  for (const action of ['complete', 'fail', 'recover'] as const) {
    await expect(
      store.transition(
        `stale-${action}`,
        actor,
        original,
        action,
        action === 'complete' ? payload('stale-copy') : undefined,
      ),
    ).rejects.toThrow('skill_capture_conflict');
  }
  expect(await store.readDraft(draftId, actor)).toEqual(recovered);
  expect(await connection.db!.collection('capture_blobs').countDocuments()).toBe(1);
});

test('concurrent completion selects one committed snapshot and one receipt', async () => {
  const draft = await initialize();
  const outcomes = await Promise.allSettled(
    ['one', 'two'].map((body) =>
      store.transition(`complete-${body}`, actor, draft, 'complete', payload(body)),
    ),
  );
  expect(outcomes.filter((r) => r.status === 'fulfilled')).toHaveLength(1);
  expect((await store.readDraft(draftId, actor))?.status).toBe('ready');
  expect(await connection.db!.collection('capture_receipts').countDocuments()).toBe(3);
});

test('ready edits and original base survive new sync and repeated reservation', async () => {
  const draft = await initialize();
  const ready = await store.transition('complete', actor, draft, 'complete', payload());
  const edited = await store.transition('edit', actor, ready, 'edit', payload('user edits'));
  const source = await store.commitSource(
    'sync',
    actor,
    candidate(1, payload('sync')),
    payload('sync'),
  );
  const reused = await store.reserve('reuse', actor, request(source));
  expect(reused).toEqual(edited);
  expect(reused.sourceGeneration).toBe(1);
  expect(await store.readPayload(reused.digest!)).toBe(payload('user edits').json);
  for (const action of ['fail', 'recover'] as const)
    await expect(store.transition(action, actor, reused, action)).rejects.toThrow(
      'skill_capture_state',
    );
});

test('a stale edit cannot overwrite a newer ready edit', async () => {
  const draft = await initialize();
  const ready = await store.transition('complete', actor, draft, 'complete', payload());
  const edited = await store.transition('edit-one', actor, ready, 'edit', payload('one'));
  await expect(store.transition('edit-two', actor, ready, 'edit', payload('two'))).rejects.toThrow(
    'skill_capture_conflict',
  );
  expect(await store.readDraft(draftId, actor)).toEqual(edited);
});

test('lost acknowledgement resolves the original receipt after later state advancement without replay', async () => {
  const source = candidate();
  const content = payload();
  const loseReply = async () => {
    await store.commitSource('uncertain', actor, source, content);
    throw new Error('transport_lost_after_commit');
  };
  await expect(loseReply()).rejects.toThrow('transport_lost_after_commit');
  await store.commitSource('later', actor, candidate(1, payload('later')), payload('later'));
  const receipt = await store.resolve(
    'uncertain',
    captureRequestDigest('source', actor, source, content),
  );
  expect(receipt?.result).toEqual({ ...source, generation: 1 });
  await expect(store.commitSource('uncertain', actor, source, content)).rejects.toThrow(
    'skill_capture_operation_exists',
  );
  expect((await store.readSource(sourceId, actor.tenantId))?.generation).toBe(2);
});

test('receipt identity binds actor, tenant and every operation input', async () => {
  const source = candidate();
  await store.commitSource('bound', actor, source, payload());
  for (const [who, input] of [
    [{ ...actor, ownerId: 'other' }, source],
    [{ ...actor, tenantId: 'other' }, source],
    [actor, { ...source, upstreamRevision: 'd'.repeat(40) }],
  ] as const) {
    await expect(
      store.resolve('bound', captureRequestDigest('source', who, input, payload())),
    ).rejects.toThrow('skill_capture_receipt_mismatch');
  }
});

test('receipt resolution ignores object key order for source, reservation and every transition', async () => {
  const content = payload();
  const source = candidate();
  await store.commitSource('source', actor, source, content);
  const reorderedSource = {
    upstreamRevision,
    digest: content.digest,
    generation: 0,
    tenantId: actor.tenantId,
    _id: sourceId,
  };
  expect(
    await store.resolve(
      'source',
      captureRequestDigest('source', actor, reorderedSource, {
        digest: content.digest,
        json: content.json,
      }),
    ),
  ).not.toBeNull();
  const reservation = request({ ...source, generation: 1 });
  const draft = await store.reserve('reserve', actor, reservation);
  expect(
    await store.resolve(
      'reserve',
      captureRequestDigest('reserve', actor, {
        sourceDigest: reservation.sourceDigest,
        sourceGeneration: 1,
        sourceId,
        name: reservation.name,
        _id: draftId,
      }),
    ),
  ).not.toBeNull();
  let current = draft;
  for (const action of ['fail', 'recover', 'complete', 'edit'] as const) {
    const before = current;
    const bytes = action === 'complete' || action === 'edit' ? content : undefined;
    current = await store.transition(action, actor, before, action, bytes);
    const reordered = Object.fromEntries(Object.entries(before).reverse()) as CaptureDraft;
    expect(
      (await store.resolve(action, captureRequestDigest(action, actor, reordered, bytes ?? null)))
        ?.result,
    ).toEqual(current);
  }
});

test('concurrent reuse of an operation ID cannot commit two unrelated mutations', async () => {
  const outcomes = await Promise.allSettled(
    ['a', 'b'].map((id) =>
      store.commitSource(
        'shared',
        actor,
        { ...candidate(0, payload(id)), _id: id.repeat(24) },
        payload(id),
      ),
    ),
  );
  expect(outcomes.filter((r) => r.status === 'fulfilled')).toHaveLength(1);
  expect(await connection.db!.collection('capture_sources').countDocuments()).toBe(1);
  expect(await connection.db!.collection('capture_receipts').countDocuments()).toBe(1);
});

test('caller mutation after invocation cannot change persisted source or bytes', async () => {
  const content = payload();
  const source = candidate();
  const committing = store.commitSource('detached', actor, source, content);
  source.upstreamRevision = 'd'.repeat(40);
  content.json = '{}';
  const result = await committing;
  expect(result.upstreamRevision).toBe(upstreamRevision);
  expect(await store.readPayload(result.digest)).toBe(payload().json);
});

test('source generation overflow fails closed before database writes', async () => {
  await expect(
    store.commitSource('overflow', actor, candidate(Number.MAX_SAFE_INTEGER), payload()),
  ).rejects.toThrow('skill_capture_counter');
  expect(await connection.db!.collection('capture_sources').countDocuments()).toBe(0);
});

test('a transaction snapshot ACL read alone permits a stale authorized commit', async () => {
  const authority = connection.db!.collection<{ _id: string; allowed: boolean; fence: number }>(
    'test_authority',
  );
  await authority.insertOne({ _id: 'grant', allowed: true, fence: 0 });
  const session = await connection.startSession();
  try {
    session.startTransaction({
      readConcern: { level: 'snapshot' },
      writeConcern: { w: 'majority' },
    });
    expect((await authority.findOne({ _id: 'grant' }, { session }))?.allowed).toBe(true);
    await authority.updateOne({ _id: 'grant' }, { $set: { allowed: false }, $inc: { fence: 1 } });
    await connection.db!.collection('test_results').insertOne({ accepted: true }, { session });
    await session.commitTransaction();
    expect(await connection.db!.collection('test_results').countDocuments()).toBe(1);
    expect((await authority.findOne({ _id: 'grant' }))?.allowed).toBe(false);
  } finally {
    if (session.inTransaction()) await session.abortTransaction();
    await session.endSession();
  }
});

test('a real shared write conflicts with revocation after the capture snapshot was read', async () => {
  const authority = connection.db!.collection<{ _id: string; allowed: boolean; fence: number }>(
    'test_authority',
  );
  await authority.insertOne({ _id: 'grant', allowed: true, fence: 0 });
  const capture = await connection.startSession();
  const revoke = await connection.startSession();
  try {
    capture.startTransaction({
      readConcern: { level: 'snapshot' },
      writeConcern: { w: 'majority' },
    });
    expect((await authority.findOne({ _id: 'grant' }, { session: capture }))?.allowed).toBe(true);
    revoke.startTransaction({ writeConcern: { w: 'majority' } });
    await authority.updateOne(
      { _id: 'grant' },
      { $set: { allowed: false }, $inc: { fence: 1 } },
      { session: revoke },
    );
    await revoke.commitTransaction();
    await expect(
      authority.updateOne(
        { _id: 'grant', allowed: true, fence: 0 },
        { $inc: { fence: 1 } },
        { session: capture },
      ),
    ).rejects.toMatchObject({ code: 112 });
    await capture.abortTransaction();
    expect(await connection.db!.collection('test_results').countDocuments()).toBe(0);
  } finally {
    if (capture.inTransaction()) await capture.abortTransaction();
    if (revoke.inTransaction()) await revoke.abortTransaction();
    await capture.endSession();
    await revoke.endSession();
  }
});
