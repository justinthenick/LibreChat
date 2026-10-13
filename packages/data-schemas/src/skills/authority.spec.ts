import mongoose from 'mongoose';
import { MongoMemoryReplSet } from 'mongodb-memory-server';
import type { Connection } from 'mongoose';
import type { CaptureIdentity, CaptureOperation, CaptureSource } from './persistence';
import {
  activateSkillCapturePersistence,
  captureDigest,
  captureRequestDigest,
  createIsolatedCaptureAuthority,
  createIsolatedFencedCapturePersistence,
} from './persistence';

const actor: CaptureIdentity = { ownerId: 'synthetic-owner', tenantId: 'synthetic-tenant' };
const sourceId = 'a'.repeat(24);
const draftId = 'b'.repeat(24);
const operations: CaptureOperation[] = ['source', 'reserve', 'complete', 'fail', 'recover', 'edit'];
const json = JSON.stringify({ body: 'synthetic opaque storage fixture' });
const payload = { json, digest: captureDigest(json) };
const source: CaptureSource = {
  _id: sourceId,
  tenantId: actor.tenantId,
  generation: 0,
  digest: payload.digest,
  upstreamRevision: 'c'.repeat(40),
};
let server: MongoMemoryReplSet;
let connection: Connection;
let authority: Awaited<ReturnType<typeof createIsolatedCaptureAuthority>>;

async function setup(allowed = operations) {
  const grant = await authority.replace(actor, sourceId, 0, allowed);
  const store = await createIsolatedFencedCapturePersistence(connection, grant);
  return { grant, store };
}

async function initialize() {
  const { grant, store } = await setup();
  const current = await store.commitSource('source', actor, source, payload);
  const request = {
    _id: draftId,
    name: 'synthetic-draft',
    sourceId,
    sourceGeneration: current.generation,
    sourceDigest: current.digest,
  };
  const draft = await store.reserve('reserve', actor, request);
  return { grant, store, draft, request };
}

async function uses(): Promise<number | undefined> {
  const record = await connection.db!.collection<{ uses: number }>('capture_authority').findOne({});
  return record?.uses;
}

beforeAll(async () => {
  server = await MongoMemoryReplSet.create({ replSet: { count: 1, storageEngine: 'wiredTiger' } });
  connection = await mongoose
    .createConnection(server.getUri(), { dbName: 'test_skill_capture_authority' })
    .asPromise();
  authority = await createIsolatedCaptureAuthority(connection);
}, 60000);

beforeEach(async () => {
  for (const name of [
    'capture_sources',
    'capture_drafts',
    'capture_blobs',
    'capture_generations',
    'capture_receipts',
    'capture_authority',
    'test_results',
  ])
    await connection.db!.collection(name).deleteMany({});
});

afterAll(async () => {
  await connection?.close();
  await server?.stop();
});

test('keeps activation disabled and refuses a non-isolated database', async () => {
  expect(activateSkillCapturePersistence).toThrow('skill_capture_authorization_unavailable');
  const other = await mongoose
    .createConnection(server.getUri(), { dbName: 'not_isolated' })
    .asPromise();
  try {
    await expect(createIsolatedCaptureAuthority(other)).rejects.toThrow(
      'skill_capture_isolation_required',
    );
    await expect(
      createIsolatedFencedCapturePersistence(other, { ...actor, sourceId, epoch: 1 }),
    ).rejects.toThrow('skill_capture_isolation_required');
    expect(await other.db!.listCollections().toArray()).toHaveLength(0);
  } finally {
    await other.close();
  }
});

test('commits the shared write, capture state and bound receipt together', async () => {
  const { grant, store } = await setup();
  const result = await store.commitSource('source', actor, source, payload);
  expect(await uses()).toBe(1);
  const receipt = await store.resolve(
    'source',
    captureRequestDigest('source', actor, source, payload),
  );
  expect(receipt?.result).toEqual(result);
  expect(receipt?.authorization).toEqual({ ...actor, sourceId, epoch: grant.epoch });
  expect(await authority.read(actor, sourceId)).toEqual(grant);
});

test('does not treat a missing grant or a stale epoch as permission', async () => {
  const missing = await createIsolatedFencedCapturePersistence(connection, {
    ...actor,
    sourceId,
    epoch: 1,
  });
  await expect(missing.commitSource('missing', actor, source, payload)).rejects.toThrow(
    'authorization_denied',
  );
  const { store } = await setup();
  await authority.replace(actor, sourceId, 1, []);
  await expect(store.commitSource('revoked', actor, source, payload)).rejects.toThrow(
    'authorization_denied',
  );
  expect(await uses()).toBe(0);
  for (const name of [
    'capture_sources',
    'capture_receipts',
    'capture_blobs',
    'capture_generations',
  ])
    expect(await connection.db!.collection(name).countDocuments()).toBe(0);
});

test('retains revoked epochs so regrant cannot revive an old prepared store', async () => {
  const { store } = await setup();
  await authority.replace(actor, sourceId, 1, []);
  const current = await authority.replace(actor, sourceId, 2, operations);
  expect(current.epoch).toBe(3);
  await expect(authority.replace(actor, sourceId, 1, operations)).rejects.toThrow(
    'authorization_denied',
  );
  await expect(authority.replace(actor, sourceId, 0, operations)).rejects.toMatchObject({
    code: 11000,
  });
  await expect(store.commitSource('stale', actor, source, payload)).rejects.toThrow(
    'authorization_denied',
  );
  const fresh = await createIsolatedFencedCapturePersistence(connection, current);
  await expect(fresh.commitSource('fresh', actor, source, payload)).resolves.toMatchObject({
    generation: 1,
  });
});

test.each(['owner', 'tenant', 'null-tenant', 'source'])(
  'does not cross the bound %s boundary',
  async (boundary) => {
    const { store } = await setup();
    const who = { ...actor };
    const candidate = { ...source };
    if (boundary === 'owner') who.ownerId = 'other';
    if (boundary === 'tenant') who.tenantId = 'other';
    if (boundary === 'null-tenant') who.tenantId = null;
    if (boundary === 'source') candidate._id = 'd'.repeat(24);
    candidate.tenantId = who.tenantId;
    await expect(store.commitSource('wrong-scope', who, candidate, payload)).rejects.toThrow(
      'authorization_denied',
    );
    expect(await uses()).toBe(0);
    expect(await connection.db!.collection('capture_receipts').countDocuments()).toBe(0);
  },
);

test('keeps null tenant grants distinct and requires the exact operation', async () => {
  const who = { ...actor, tenantId: null };
  const grant = await authority.replace(who, sourceId, 0, ['reserve']);
  expect(await authority.read(actor, sourceId)).toBeNull();
  const store = await createIsolatedFencedCapturePersistence(connection, grant);
  await expect(
    store.commitSource('wrong-action', who, { ...source, tenantId: null }, payload),
  ).rejects.toThrow('authorization_denied');
  expect(await uses()).toBe(0);
});

test('detaches grant operations, ticket and actor before awaiting database work', async () => {
  const who = { ...actor };
  const allowed = [...operations];
  const pending = authority.replace(who, sourceId, 0, allowed);
  who.ownerId = 'changed';
  allowed.length = 0;
  const grant = await pending;
  const ticket = { ...grant };
  const preparing = createIsolatedFencedCapturePersistence(connection, ticket);
  ticket.epoch = 999;
  ticket.ownerId = 'changed';
  const store = await preparing;
  await expect(store.commitSource('detached', actor, source, payload)).resolves.toMatchObject({
    generation: 1,
  });
  expect(grant.operations).toEqual(operations);
  expect(Object.isFrozen(grant.operations)).toBe(true);
});

test('rolls back the fence when a later capture CAS fails', async () => {
  const { store } = await setup();
  await store.commitSource('first', actor, source, payload);
  await expect(store.commitSource('duplicate', actor, source, payload)).rejects.toMatchObject({
    code: 11000,
  });
  expect(await uses()).toBe(1);
  expect(
    await store.resolve('duplicate', captureRequestDigest('source', actor, source, payload)),
  ).toBeNull();
});

test('fences all draft transitions and ready reuse after revocation', async () => {
  const { store, draft, request } = await initialize();
  const ready = await store.transition('complete', actor, draft, 'complete', payload);
  await authority.replace(actor, sourceId, 1, []);
  const attempts = [
    () => store.reserve('reuse', actor, request),
    () => store.transition('stale-complete', actor, draft, 'complete', payload),
    () => store.transition('stale-fail', actor, draft, 'fail'),
    () => store.transition('stale-recover', actor, draft, 'recover'),
    () => store.transition('stale-edit', actor, ready, 'edit', payload),
  ];
  for (const attempt of attempts) await expect(attempt()).rejects.toThrow('authorization_denied');
  expect(await store.readDraft(draftId, actor)).toEqual(ready);
  expect(await uses()).toBe(3);
});

test('recovery requires a fresh epoch and still fences old completion attempts', async () => {
  const { store, draft } = await initialize();
  const failed = await store.transition('fail', actor, draft, 'fail');
  await authority.replace(actor, sourceId, 1, []);
  await expect(store.transition('blocked', actor, failed, 'recover')).rejects.toThrow(
    'authorization_denied',
  );
  const grant = await authority.replace(actor, sourceId, 2, ['recover', 'complete']);
  const fresh = await createIsolatedFencedCapturePersistence(connection, grant);
  const recovered = await fresh.transition('recover', actor, failed, 'recover');
  await expect(fresh.transition('old-attempt', actor, draft, 'complete', payload)).rejects.toThrow(
    'skill_capture_conflict',
  );
  const ready = await fresh.transition('finish', actor, recovered, 'complete', payload);
  expect(ready.attempt).toBe(2);
  expect(ready.status).toBe('ready');
  expect(await uses()).toBe(5);
});

test('lost-reply receipt resolution is historical evidence and never replays a revoked write', async () => {
  const { store } = await setup();
  const committed = await store.commitSource('lost-reply', actor, source, payload);
  await authority.replace(actor, sourceId, 1, []);
  const restarted = await createIsolatedFencedCapturePersistence(connection, {
    ...actor,
    sourceId,
    epoch: 1,
  });
  const digest = captureRequestDigest('source', actor, source, payload);
  expect((await restarted.resolve('lost-reply', digest))?.result).toEqual(committed);
  await expect(restarted.commitSource('lost-reply', actor, source, payload)).rejects.toThrow(
    'operation_exists',
  );
  await expect(
    restarted.commitSource('new-id', actor, { ...source, generation: 1 }, payload),
  ).rejects.toThrow('authorization_denied');
  expect(await uses()).toBe(1);
});

test('a committed revocation conflicts with a transaction holding an older snapshot', async () => {
  const { grant } = await setup();
  const session = await connection.startSession();
  try {
    session.startTransaction({
      readConcern: { level: 'snapshot' },
      writeConcern: { w: 'majority' },
    });
    await connection.db!.collection('capture_authority').findOne({}, { session });
    await authority.replace(actor, sourceId, 1, []);
    await expect(authority.fence(session, grant, actor, sourceId, 'source')).rejects.toMatchObject({
      code: 112,
    });
    await session.abortTransaction();
    expect(await uses()).toBe(0);
    expect((await authority.read(actor, sourceId))?.epoch).toBe(2);
  } finally {
    if (session.inTransaction()) await session.abortTransaction();
    await session.endSession();
  }
});

test('a stale revocation transaction conflicts after a capture transaction commits first', async () => {
  const { store } = await setup();
  const session = await connection.startSession();
  try {
    session.startTransaction({
      readConcern: { level: 'snapshot' },
      writeConcern: { w: 'majority' },
    });
    await connection.db!.collection('capture_authority').findOne({}, { session });
    await store.commitSource('before-revoke', actor, source, payload);
    await expect(
      connection
        .db!.collection('capture_authority')
        .updateOne({ epoch: 1 }, { $set: { operations: [] }, $inc: { epoch: 1 } }, { session }),
    ).rejects.toMatchObject({ code: 112 });
    await session.abortTransaction();
    await authority.replace(actor, sourceId, 1, []);
    await expect(
      store.commitSource('after-revoke', actor, { ...source, generation: 1 }, payload),
    ).rejects.toThrow('authorization_denied');
    expect(await uses()).toBe(1);
  } finally {
    if (session.inTransaction()) await session.abortTransaction();
    await session.endSession();
  }
});

test('requires an active transaction and rolls back a separately aborted fence', async () => {
  const { grant } = await setup();
  const session = await connection.startSession();
  try {
    await expect(authority.fence(session, grant, actor, sourceId, 'source')).rejects.toThrow(
      'authorization_denied',
    );
    session.startTransaction();
    await authority.fence(session, grant, actor, sourceId, 'source');
    await session.abortTransaction();
    expect(await uses()).toBe(0);
  } finally {
    if (session.inTransaction()) await session.abortTransaction();
    await session.endSession();
  }
});

test.each([-1, 0.5, Number.MAX_SAFE_INTEGER, Number.NaN])(
  'rejects invalid epoch %s',
  async (epoch) => {
    await expect(authority.replace(actor, sourceId, epoch, operations)).rejects.toThrow(
      'authorization_denied',
    );
    expect(await connection.db!.collection('capture_authority').countDocuments()).toBe(0);
  },
);

test('rejects exhausted use counters without writing capture state', async () => {
  const { store } = await setup();
  await connection
    .db!.collection('capture_authority')
    .updateOne({}, { $set: { uses: Number.MAX_SAFE_INTEGER } });
  await expect(store.commitSource('exhausted', actor, source, payload)).rejects.toThrow(
    'authorization_denied',
  );
  expect(await connection.db!.collection('capture_receipts').countDocuments()).toBe(0);
});

test('reserves the terminal epoch for revocation and never authorizes it', async () => {
  await setup();
  const penultimate = Number.MAX_SAFE_INTEGER - 1;
  await connection
    .db!.collection('capture_authority')
    .updateOne({}, { $set: { epoch: penultimate } });
  const store = await createIsolatedFencedCapturePersistence(connection, {
    ...actor,
    sourceId,
    epoch: penultimate,
  });
  await store.commitSource('before-terminal', actor, source, payload);
  await expect(authority.replace(actor, sourceId, penultimate, operations)).rejects.toThrow(
    'authorization_denied',
  );
  const revoked = await authority.replace(actor, sourceId, penultimate, []);
  expect(revoked.epoch).toBe(Number.MAX_SAFE_INTEGER);
  expect(await authority.read(actor, sourceId)).toEqual(revoked);
  await expect(
    store.commitSource('old-epoch', actor, { ...source, generation: 1 }, payload),
  ).rejects.toThrow('authorization_denied');
  await expect(authority.replace(actor, sourceId, revoked.epoch, operations)).rejects.toThrow(
    'authorization_denied',
  );
  await connection.db!.collection('capture_authority').updateOne({}, { $set: { operations } });
  const terminal = await createIsolatedFencedCapturePersistence(connection, revoked);
  await expect(
    terminal.commitSource('terminal', actor, { ...source, generation: 1 }, payload),
  ).rejects.toThrow('authorization_denied');
  expect(await uses()).toBe(1);
});

test('separates operation permissions from the epoch and rejects duplicate grants', async () => {
  const { store, draft, request } = await initialize();
  const failed = await store.transition('fail', actor, draft, 'fail');
  const grant = await authority.replace(actor, sourceId, 1, ['recover']);
  const restricted = await createIsolatedFencedCapturePersistence(connection, grant);
  const recovered = await restricted.transition('recover', actor, failed, 'recover');
  await expect(
    restricted.transition('complete', actor, recovered, 'complete', payload),
  ).rejects.toThrow('authorization_denied');
  await expect(restricted.reserve('reserve-again', actor, request)).rejects.toThrow(
    'authorization_denied',
  );
  await expect(authority.replace(actor, sourceId, 2, ['source', 'source'])).rejects.toThrow(
    'authorization_denied',
  );
  expect((await authority.read(actor, sourceId))?.epoch).toBe(2);
  expect(await uses()).toBe(4);
});
