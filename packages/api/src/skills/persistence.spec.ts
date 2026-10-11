import mongoose from 'mongoose';
import { createHash } from 'node:crypto';
import { MongoMemoryReplSet } from 'mongodb-memory-server';
import {
  captureDigest,
  createIsolatedCapturePersistence,
  createIsolatedCaptureAuthority,
} from '@librechat/data-schemas/isolated-capture';
import type {
  CaptureAuthorization,
  CaptureOperation,
} from '@librechat/data-schemas/isolated-capture';
import type { Connection, mongo } from 'mongoose';
import type { IsolatedValidatedCapture, StoredSkillDraft, StoredSkillSource } from './persistence';
import type { SkillBundleManifest, SkillBundleSnapshot } from './bundles';
import type { GenerationFixture } from './generation.helper';
import {
  activateValidatedSkillCapture,
  createIsolatedValidatedCapture,
  createIsolatedFencedValidatedCapture,
} from './persistence';
import { captureSkillBundle, validateSkillBundle } from './bundles';
import { createGenerationFixture } from './generation.helper';
import { prepareGitHubSkillGeneration } from './generation';
import { copySkillDraft } from './capture';

const actor = { ownerId: 'owner', tenantId: 'tenant' };
const sourceId = 'a'.repeat(24);
const draftId = 'b'.repeat(24);
const upstreamRevision = 'c'.repeat(40);
let server: MongoMemoryReplSet;
let connection: Connection;
let api: IsolatedValidatedCapture;

async function bundle(
  body = 'original',
  content = 'original bytes',
  changes: Partial<SkillBundleManifest> = {},
): Promise<SkillBundleSnapshot> {
  const bytes = Buffer.from(content);
  const manifest: SkillBundleManifest = {
    skillId: sourceId,
    tenantId: actor.tenantId,
    logicalName: 'writer',
    sourceRevision: upstreamRevision,
    definition: { name: 'writer', description: 'Writes', body, version: 1 },
    files: [
      {
        path: 'a.txt',
        mimeType: 'text/plain',
        bytes: bytes.length,
        sha256: createHash('sha256').update(bytes).digest('hex'),
      },
    ],
    ...changes,
  };
  return captureSkillBundle({
    manifest,
    readFile: async () =>
      (async function* () {
        yield bytes;
      })(),
  });
}

function reader(snapshot: SkillBundleSnapshot) {
  return async (file: { path: string }) =>
    (async function* () {
      const stored = snapshot.files.find((entry) => entry.path === file.path);
      if (!stored) throw new Error('missing_file');
      yield Buffer.from(stored.base64, 'base64');
    })();
}

function expectation(draft: StoredSkillDraft) {
  return { draftId, attempt: draft.record.attempt, revision: draft.record.revision };
}

function reservation(source: StoredSkillSource) {
  return {
    sourceId: source.record._id,
    sourceGeneration: source.record.generation,
    sourceDigest: source.record.digest,
    draftId,
    name: 'writer-draft',
  };
}

async function currentReservation() {
  const source = await api.readSource(actor, sourceId);
  if (!source) throw new Error('missing_fixture_source');
  return reservation(source);
}

async function source(snapshot?: SkillBundleSnapshot) {
  return (
    await api.prepareSource('source', actor, {
      sourceId,
      expectedGeneration: 0,
      upstreamRevision,
      snapshot: snapshot ?? (await bundle()),
    })
  ).commit();
}

async function initializing() {
  await source();
  return (await api.prepareDraft('reserve', actor, await currentReservation())).commit();
}

async function copied(draft: StoredSkillDraft) {
  return copySkillDraft(draft.capture, draft.record.attempt, reader(draft.capture.source.snapshot));
}

async function ready() {
  const draft = await initializing();
  return (
    await api.prepareComplete('complete', actor, expectation(draft), await copied(draft))
  ).commit();
}

beforeAll(async () => {
  server = await MongoMemoryReplSet.create({ replSet: { count: 1, storageEngine: 'wiredTiger' } });
  connection = await mongoose
    .createConnection(server.getUri(), { dbName: 'test_skill_capture_validators' })
    .asPromise();
  api = await createIsolatedValidatedCapture(connection);
}, 60000);

beforeEach(async () => {
  for (const name of [
    'capture_sources',
    'capture_drafts',
    'capture_blobs',
    'capture_generations',
    'capture_receipts',
    'capture_authority',
  ])
    await connection.db!.collection(name).deleteMany({});
  api = await createIsolatedValidatedCapture(connection);
});

afterAll(async () => {
  await connection?.close();
  await server?.stop();
});

test('live activation stays hard-disabled and a non-isolated database is rejected', async () => {
  expect(activateValidatedSkillCapture).toThrow('skill_capture_authorization_unavailable');
  const other = await mongoose
    .createConnection(server.getUri(), { dbName: 'not_capture_test' })
    .asPromise();
  try {
    await expect(createIsolatedValidatedCapture(other)).rejects.toThrow(
      'skill_capture_isolation_required',
    );
  } finally {
    await other.close();
  }
});

test('pinned Git generations survive sync, draft copy and lost-reply recovery in real Mongo', async () => {
  const first = createGenerationFixture();
  const second = createGenerationFixture({
    'SKILL.md': '---\nname: writer\ndescription: Writes\n---\nReplacement instructions',
    'notes/readme.txt': 'replacement bytes',
  });
  try {
    const plan = await prepareGitHubSkillGeneration(api, 'git-first', actor, 0, first.input);
    const committed = await plan.commit();
    const draft = await (
      await api.prepareDraft('git-draft', actor, reservation(committed))
    ).commit();
    const stale = await prepareGitHubSkillGeneration(api, 'git-stale', actor, 1, first.input);
    await (await prepareGitHubSkillGeneration(api, 'git-second', actor, 1, second.input)).commit();
    await expect(stale.commit()).rejects.toThrow();
    const finished = await (
      await api.prepareComplete('git-complete', actor, expectation(draft), await copied(draft))
    ).commit();
    expect(validateSkillBundle(finished.capture.snapshot!).definition.body).toContain(
      'Original instructions',
    );
    expect(finished.capture.snapshot!.files[0].base64).toBe(
      Buffer.from('original bytes').toString('base64'),
    );
    expect((await api.readSource(actor, sourceId))!.record.generation).toBe(2);
    api = await createIsolatedValidatedCapture(connection);
    expect(await api.resolveReceipt(actor, plan.operationId, plan.requestDigest)).toEqual(
      committed,
    );
    expect(await connection.db!.collection('capture_generations').countDocuments()).toBe(2);
  } finally {
    first.close();
    second.close();
  }
});

describe('explicit Git generation handoff', () => {
  let first: GenerationFixture;
  let second: GenerationFixture;
  let selected: StoredSkillSource;
  let authority: Awaited<ReturnType<typeof createIsolatedCaptureAuthority>>;
  let grant: CaptureAuthorization;
  const operations: CaptureOperation[] = [
    'source',
    'reserve',
    'complete',
    'fail',
    'recover',
    'edit',
  ];

  beforeEach(async () => {
    first = createGenerationFixture();
    second = createGenerationFixture({
      'SKILL.md': '---\nname: writer\ndescription: Writes\n---\nReplacement instructions',
      'notes/readme.txt': 'replacement bytes',
    });
    authority = await createIsolatedCaptureAuthority(connection);
    grant = await authority.replace(actor, sourceId, 0, operations);
    api = await createIsolatedFencedValidatedCapture(connection, grant);
    selected = await (
      await prepareGitHubSkillGeneration(api, 'selected', actor, 0, first.input)
    ).commit();
  });

  afterEach(() => {
    first?.close();
    second?.close();
  });

  async function advance() {
    return (await prepareGitHubSkillGeneration(api, 'advance', actor, 1, second.input)).commit();
  }

  async function finish(draft: StoredSkillDraft) {
    const result = await (
      await api.prepareComplete('finish', actor, expectation(draft), await copied(draft))
    ).commit();
    expect(result.record.sourceGeneration).toBe(selected.record.generation);
    expect(result.record.sourceDigest).toBe(selected.record.digest);
    expect(validateSkillBundle(result.capture.snapshot!).definition.body).toContain(
      'Original instructions',
    );
    expect(result.capture.snapshot!.files[0].base64).toBe(
      Buffer.from('original bytes').toString('base64'),
    );
    return result;
  }

  test('sync before preparation cannot replace the selected retained generation', async () => {
    await advance();
    const plan = await api.prepareDraft('reserve-selected', actor, reservation(selected));
    await finish(await plan.commit());
    expect((await api.readSource(actor, sourceId))!.record.generation).toBe(2);
  });

  test('sync during the actual retained-generation read cannot change the selection', async () => {
    let entered!: () => void;
    let release!: () => void;
    const started = new Promise<void>((resolve) => {
      entered = resolve;
    });
    const released = new Promise<void>((resolve) => {
      release = resolve;
    });
    const original = mongoose.mongo.Collection.prototype.findOne;
    let armed = true;
    const spy = jest
      .spyOn(mongoose.mongo.Collection.prototype, 'findOne')
      .mockImplementation(async function (
        this: mongo.Collection,
        ...args: Parameters<typeof original>
      ) {
        if (armed && this.collectionName === 'capture_generations') {
          armed = false;
          entered();
          await released;
        }
        return original.apply(this, args);
      });
    const pending = api.prepareDraft('during-read', actor, reservation(selected));
    let timer: ReturnType<typeof setTimeout> | undefined;
    try {
      await Promise.race([
        started,
        new Promise<void>((_resolve, reject) => {
          timer = setTimeout(() => reject(new Error('handoff_barrier_timeout')), 4000);
        }),
      ]);
      await advance();
    } finally {
      clearTimeout(timer);
      release();
      spy.mockRestore();
      await pending;
    }
    expect((await finish(await (await pending).commit())).record.sourceGeneration).toBe(1);
  });

  test.each([
    'missing-generation',
    'missing-digest',
    'zero',
    'fraction',
    'future',
    'digest',
    'source',
    'tenant',
  ])('rejects %s without falling back to the current source or writing a receipt', async (kind) => {
    const request = reservation(selected);
    const identity = { ...actor };
    if (kind === 'missing-generation') Reflect.deleteProperty(request, 'sourceGeneration');
    if (kind === 'missing-digest') Reflect.deleteProperty(request, 'sourceDigest');
    if (kind === 'zero') request.sourceGeneration = 0;
    if (kind === 'fraction') request.sourceGeneration = 1.5;
    if (kind === 'future') request.sourceGeneration = 2;
    if (kind === 'digest') request.sourceDigest = 'f'.repeat(64);
    if (kind === 'source') request.sourceId = 'f'.repeat(24);
    if (kind === 'tenant') identity.tenantId = 'other';
    await expect(api.prepareDraft('invalid-selection', identity, request)).rejects.toThrow(
      'invalid_skill_selection',
    );
    expect(await connection.db!.collection('capture_drafts').countDocuments()).toBe(0);
    expect(await connection.db!.collection('capture_receipts').countDocuments()).toBe(1);
    expect(
      (await connection.db!.collection<{ uses: number }>('capture_authority').findOne({}))?.uses,
    ).toBe(1);
  });

  test('detaches actor and selection before asynchronous preparation', async () => {
    const request = reservation(selected);
    const identity = { ...actor };
    const pending = api.prepareDraft('detached-selection', identity, request);
    request.sourceGeneration = 999;
    request.sourceDigest = 'f'.repeat(64);
    request.sourceId = 'f'.repeat(24);
    request.name = 'changed';
    identity.ownerId = 'other';
    identity.tenantId = 'other';
    await advance();
    expect((await finish(await (await pending).commit())).record.sourceGeneration).toBe(1);
  });

  test('rejects a digest from a different committed generation', async () => {
    const newer = await advance();
    await expect(
      api.prepareDraft('mixed-generations', actor, {
        ...reservation(selected),
        sourceGeneration: newer.record.generation,
      }),
    ).rejects.toThrow('invalid_skill_selection');
    expect(await connection.db!.collection('capture_drafts').countDocuments()).toBe(0);
    expect(await connection.db!.collection('capture_receipts').countDocuments()).toBe(2);
  });

  test('competing reservations have one winner and cannot substitute a newer generation', async () => {
    const newer = await advance();
    const plans = await Promise.all([
      api.prepareDraft('competing-old', actor, reservation(selected)),
      api.prepareDraft('competing-new', actor, reservation(newer)),
    ]);
    const outcomes = await Promise.allSettled(plans.map((plan) => plan.commit()));
    expect(outcomes.filter((result) => result.status === 'fulfilled')).toHaveLength(1);
    expect(outcomes.filter((result) => result.status === 'rejected')).toHaveLength(1);
    const winner = outcomes.findIndex((result) => result.status === 'fulfilled');
    const draft = (await api.readDraft(actor, draftId))!;
    expect(draft.record.sourceDigest).toBe([selected, newer][winner].record.digest);
    expect(await plans[winner].resolve()).toEqual(draft);
    expect(await plans[1 - winner].resolve()).toBeNull();
    expect(await connection.db!.collection('capture_drafts').countDocuments()).toBe(1);
  });

  test('newer selection reuses ready edits and preserves historical reservation receipts', async () => {
    const reservationPlan = await api.prepareDraft(
      'reservation-reply-lost',
      actor,
      reservation(selected),
    );
    const draft = await reservationPlan.commit();
    const completionPlan = await api.prepareComplete(
      'completion-reply-lost',
      actor,
      expectation(draft),
      await copied(draft),
    );
    const original = await completionPlan.commit();
    const manifest = validateSkillBundle(original.capture.snapshot!);
    const editedSnapshot = await captureSkillBundle({
      manifest: { ...manifest, definition: { ...manifest.definition, body: 'user edits' } },
      readFile: reader(original.capture.snapshot!),
    });
    const edited = await (
      await api.prepareEdit('edit-selected', actor, expectation(original), editedSnapshot)
    ).commit();
    const newer = await advance();
    expect(
      await (await api.prepareDraft('reuse-selected', actor, reservation(newer))).commit(),
    ).toEqual(edited);
    api = await createIsolatedFencedValidatedCapture(connection, grant);
    expect(
      await api.resolveReceipt(actor, reservationPlan.operationId, reservationPlan.requestDigest),
    ).toEqual(draft);
    expect(
      await api.resolveReceipt(actor, completionPlan.operationId, completionPlan.requestDigest),
    ).toEqual(original);
    await expect(reservationPlan.commit()).rejects.toThrow();
    await expect(completionPlan.commit()).rejects.toThrow();
    await expect(
      api.resolveReceipt(
        { ...actor, ownerId: 'other' },
        reservationPlan.operationId,
        reservationPlan.requestDigest,
      ),
    ).rejects.toThrow('invalid_skill_selection');
    const foreign = await api.prepareDraft(
      'foreign-owner',
      { ...actor, ownerId: 'other' },
      reservation(newer),
    );
    await expect(foreign.commit()).rejects.toThrow();
    expect(await api.readDraft(actor, draftId)).toEqual(edited);
  });

  test('explicit recovery retains selected bytes and fences a stale attempt after sync and revocation', async () => {
    const draft = await (
      await api.prepareDraft('reserve-recovery', actor, reservation(selected))
    ).commit();
    const stale = await api.prepareComplete(
      'stale-completion',
      actor,
      expectation(draft),
      await copied(draft),
    );
    const failed = await (
      await api.prepareFail('fail-selected', actor, expectation(draft))
    ).commit();
    await advance();
    await authority.replace(actor, sourceId, grant.epoch, []);
    await expect(stale.commit()).rejects.toThrow('authorization_denied');
    expect(await stale.resolve()).toBeNull();
    grant = await authority.replace(actor, sourceId, 2, operations);
    api = await createIsolatedFencedValidatedCapture(connection, grant);
    const recovered = await (
      await api.prepareRecover('recover-selected', actor, expectation(failed))
    ).commit();
    await expect(
      api.prepareComplete('wrong-attempt', actor, expectation(draft), await copied(draft)),
    ).rejects.toThrow('invalid_skill_selection');
    const result = await finish(recovered);
    expect(result.record.attempt).toBe(2);
    expect(await stale.resolve()).toBeNull();
  });

  test('revocation blocks a prepared retained-generation reservation without publishing a draft', async () => {
    await advance();
    const plan = await api.prepareDraft('revoked-selection', actor, reservation(selected));
    await authority.replace(actor, sourceId, grant.epoch, []);
    await expect(plan.commit()).rejects.toThrow('authorization_denied');
    expect(await plan.resolve()).toBeNull();
    expect(await connection.db!.collection('capture_drafts').countDocuments()).toBe(0);
    expect(await connection.db!.collection('capture_receipts').countDocuments()).toBe(2);
  });
});

test('an incomplete Git generation leaves no source, payload or receipt', async () => {
  const fixture = createGenerationFixture();
  try {
    const blob = [...fixture.responses.values()].find((value) => value.content)!;
    blob.content = Buffer.from('corrupt').toString('base64');
    await expect(
      prepareGitHubSkillGeneration(api, 'git-invalid', actor, 0, fixture.input),
    ).rejects.toThrow();
    for (const name of [
      'capture_sources',
      'capture_blobs',
      'capture_receipts',
      'capture_generations',
    ]) {
      expect(await connection.db!.collection(name).countDocuments()).toBe(0);
    }
  } finally {
    fixture.close();
  }
});

test('persists and reads a complete validated source and draft', async () => {
  const draft = await ready();
  expect(draft.record.status).toBe('ready');
  expect(validateSkillBundle(draft.capture.snapshot!)).toMatchObject({
    skillId: draftId,
    logicalName: 'writer-draft',
    definition: { name: 'writer-draft', body: 'original' },
  });
  expect(await api.readDraft(actor, draftId)).toEqual(draft);
  expect(Object.isFrozen(draft.capture.snapshot!.files[0])).toBe(true);
});

test.each(['identity', 'tenant', 'provenance', 'name'])(
  'rejects a self-consistent source bundle with wrong %s before persistence',
  async (kind) => {
    let changes: Partial<SkillBundleManifest> = { logicalName: 'other' };
    if (kind === 'identity') {
      changes = { skillId: 'd'.repeat(24) };
    } else if (kind === 'tenant') {
      changes = { tenantId: 'other' };
    } else if (kind === 'provenance') {
      changes = { sourceRevision: 'd'.repeat(40) };
    }
    await expect(source(await bundle('original', 'original bytes', changes))).rejects.toThrow(
      'invalid_skill_selection',
    );
    expect(await connection.db!.collection('capture_sources').countDocuments()).toBe(0);
    expect(await connection.db!.collection('capture_blobs').countDocuments()).toBe(0);
  },
);

test.each(['missing', 'changed', 'noncanonical'])(
  'rejects %s source payloads without advancing a generation',
  async (kind) => {
    await source();
    const valid = await bundle('new');
    let invalid = { ...valid, manifestJson: `${valid.manifestJson} ` };
    if (kind === 'missing') {
      invalid = { ...valid, files: [] };
    } else if (kind === 'changed') {
      invalid = {
        ...valid,
        files: [{ path: 'a.txt', base64: Buffer.from('other').toString('base64') }],
      };
    }
    await expect(
      api.prepareSource('bad', actor, {
        sourceId,
        expectedGeneration: 1,
        upstreamRevision,
        snapshot: invalid,
      }),
    ).rejects.toThrow('invalid_skill_selection');
    expect((await api.readSource(actor, sourceId))?.record.generation).toBe(1);
    expect(await connection.db!.collection('capture_receipts').countDocuments()).toBe(1);
  },
);

test.each(['identity', 'tenant', 'name', 'definition', 'bytes', 'file-set', 'provenance'])(
  'rejects a valid standalone completion with mismatched %s',
  async (kind) => {
    const draft = await initializing();
    const good = await copied(draft);
    const manifest = validateSkillBundle(good);
    const changes: Partial<SkillBundleManifest> = { ...manifest };
    if (kind === 'identity') changes.skillId = 'e'.repeat(24);
    if (kind === 'tenant') changes.tenantId = 'other';
    if (kind === 'name') {
      changes.logicalName = 'other';
      changes.definition = { ...manifest.definition, name: 'other' };
    }
    if (kind === 'definition')
      changes.definition = { ...manifest.definition, body: 'foreign definition' };
    if (kind === 'provenance') changes.sourceRevision = 'foreign';
    if (kind === 'file-set') changes.files = [];
    if (kind === 'bytes') {
      const bytes = Buffer.from('other bytes');
      changes.files = [
        {
          ...manifest.files[0],
          bytes: bytes.length,
          sha256: createHash('sha256').update(bytes).digest('hex'),
        },
      ];
    }
    const wrong = await bundle(
      'original',
      kind === 'bytes' ? 'other bytes' : 'original bytes',
      changes,
    );
    expect(() => validateSkillBundle(wrong)).not.toThrow();
    await expect(
      api.prepareComplete('bad-completion', actor, expectation(draft), wrong),
    ).rejects.toThrow('invalid_skill_selection');
    expect((await api.readDraft(actor, draftId))?.record.status).toBe('initializing');
    expect(await connection.db!.collection('capture_receipts').countDocuments()).toBe(2);
  },
);

test('failed copy leaves no ready draft and explicit recovery fences prepared old completion', async () => {
  const draft = await initializing();
  await expect(
    copySkillDraft(draft.capture, 1, async () =>
      (async function* () {
        yield Buffer.from('partial');
      })(),
    ),
  ).rejects.toThrow('invalid_skill_selection');
  const stale = await api.prepareComplete('stale', actor, expectation(draft), await copied(draft));
  const failed = await (await api.prepareFail('fail', actor, expectation(draft))).commit();
  const recovered = await (
    await api.prepareRecover('recover', actor, expectation(failed))
  ).commit();
  await expect(stale.commit()).rejects.toThrow('skill_capture_conflict');
  expect(await stale.resolve()).toBeNull();
  const complete = await api.prepareComplete(
    'new-complete',
    actor,
    expectation(recovered),
    await copied(recovered),
  );
  expect((await complete.commit()).record.attempt).toBe(2);
});

test('prepared source CAS rejects a concurrent sync without replacing its bundle', async () => {
  await source();
  const first = await api.prepareSource('first', actor, {
    sourceId,
    expectedGeneration: 1,
    upstreamRevision,
    snapshot: await bundle('first'),
  });
  const second = await api.prepareSource('second', actor, {
    sourceId,
    expectedGeneration: 1,
    upstreamRevision,
    snapshot: await bundle('second'),
  });
  await first.commit();
  await expect(second.commit()).rejects.toThrow('skill_capture_conflict');
  expect(
    validateSkillBundle((await api.readSource(actor, sourceId))!.capture.snapshot).definition.body,
  ).toBe('first');
});

test('prepared draft stays pinned across newer source generations', async () => {
  await source();
  const plan = await api.prepareDraft('pin', actor, await currentReservation());
  await (
    await api.prepareSource('sync', actor, {
      sourceId,
      expectedGeneration: 1,
      upstreamRevision,
      snapshot: await bundle('new source'),
    })
  ).commit();
  const draft = await plan.commit();
  expect(draft.record.sourceGeneration).toBe(1);
  const complete = await (
    await api.prepareComplete('complete', actor, expectation(draft), await copied(draft))
  ).commit();
  expect(validateSkillBundle(complete.capture.snapshot!).definition.body).toBe('original');
});

test('valid ready edits survive sync and repeated draft creation, while stale edits conflict', async () => {
  const draft = await ready();
  const manifest = validateSkillBundle(draft.capture.snapshot!);
  const editedSnapshot = await bundle('unused', 'original bytes', {
    ...manifest,
    definition: { ...manifest.definition, body: 'user edits' },
  });
  const first = await api.prepareEdit('edit', actor, expectation(draft), editedSnapshot);
  const stale = await api.prepareEdit(
    'stale-edit',
    actor,
    expectation(draft),
    draft.capture.snapshot!,
  );
  const edited = await first.commit();
  await expect(stale.commit()).rejects.toThrow('skill_capture_conflict');
  await (
    await api.prepareSource('sync', actor, {
      sourceId,
      expectedGeneration: 1,
      upstreamRevision,
      snapshot: await bundle('new sync'),
    })
  ).commit();
  const reused = await (
    await api.prepareDraft('reuse', actor, await currentReservation())
  ).commit();
  expect(reused).toEqual(edited);
  expect(validateSkillBundle(reused.capture.snapshot!).definition.body).toBe('user edits');
  await expect(api.prepareRecover('restart-ready', actor, expectation(reused))).rejects.toThrow(
    'invalid_skill_selection',
  );
});

test.each(['identity', 'name', 'tenant', 'provenance'])(
  'ready edits cannot change %s',
  async (kind) => {
    const draft = await ready();
    const manifest = validateSkillBundle(draft.capture.snapshot!);
    if (kind === 'identity') manifest.skillId = 'd'.repeat(24);
    if (kind === 'tenant') manifest.tenantId = 'other';
    if (kind === 'name') {
      manifest.logicalName = 'other';
      manifest.definition.name = 'other';
    }
    if (kind === 'provenance') manifest.sourceRevision = 'other';
    const wrong = await bundle('unused', 'original bytes', manifest);
    await expect(api.prepareEdit('bad-edit', actor, expectation(draft), wrong)).rejects.toThrow(
      'invalid_skill_selection',
    );
    expect(await api.readDraft(actor, draftId)).toEqual(draft);
  },
);

test('prepared operations detach actor, request and snapshot before their first await', async () => {
  const who = { ...actor };
  const snapshot = JSON.parse(JSON.stringify(await bundle())) as SkillBundleSnapshot;
  const input = { sourceId, expectedGeneration: 0, upstreamRevision, snapshot };
  const preparing = api.prepareSource('detached', who, input);
  who.tenantId = 'other';
  input.sourceId = 'd'.repeat(24);
  Object.assign(snapshot, { files: [] });
  const plan = await preparing;
  const committed = await plan.commit();
  expect(committed.record._id).toBe(sourceId);
  expect(Object.isFrozen(plan)).toBe(true);
  expect(await plan.resolve()).toEqual(committed);
});

test('lost completion reply resolves its historical validated result after a later edit and sync', async () => {
  const draft = await initializing();
  const plan = await api.prepareComplete(
    'uncertain',
    actor,
    expectation(draft),
    await copied(draft),
  );
  const loseReply = async () => {
    await plan.commit();
    throw new Error('lost_reply');
  };
  await expect(loseReply()).rejects.toThrow('lost_reply');
  const committed = (await api.readDraft(actor, draftId))!;
  const manifest = validateSkillBundle(committed.capture.snapshot!);
  const edited = await bundle('unused', 'original bytes', {
    ...manifest,
    definition: { ...manifest.definition, body: 'later edit' },
  });
  await (await api.prepareEdit('edit', actor, expectation(committed), edited)).commit();
  await (
    await api.prepareSource('sync', actor, {
      sourceId,
      expectedGeneration: 1,
      upstreamRevision,
      snapshot: await bundle('later source'),
    })
  ).commit();
  expect(await plan.resolve()).toEqual(committed);
  const restarted = await createIsolatedValidatedCapture(connection);
  expect(await restarted.resolveReceipt(actor, plan.operationId, plan.requestDigest)).toEqual(
    committed,
  );
  await expect(
    restarted.resolveReceipt({ ...actor, ownerId: 'other' }, plan.operationId, plan.requestDigest),
  ).rejects.toThrow('invalid_skill_selection');
  await expect(plan.commit()).rejects.toThrow('skill_capture_operation_exists');
});

test('same operation ID with changed inputs cannot resolve or overwrite its receipt', async () => {
  await source();
  const first = await api.prepareSource('same', actor, {
    sourceId,
    expectedGeneration: 1,
    upstreamRevision,
    snapshot: await bundle('one'),
  });
  const other = await api.prepareSource('same', actor, {
    sourceId,
    expectedGeneration: 1,
    upstreamRevision,
    snapshot: await bundle('two'),
  });
  await first.commit();
  await expect(other.resolve()).rejects.toThrow('skill_capture_receipt_mismatch');
  await expect(other.commit()).rejects.toThrow('skill_capture_operation_exists');
});

test.each(['fail', 'recover'] as const)(
  'a prepared %s receipt survives another recovery',
  async (action) => {
    const draft = await initializing();
    const plan =
      action === 'fail'
        ? await api.prepareFail('uncertain', actor, expectation(draft))
        : await api.prepareRecover('uncertain', actor, expectation(draft));
    const historical = await plan.commit();
    const recovered = await (
      await api.prepareRecover('later', actor, expectation(historical))
    ).commit();
    expect(recovered.record.attempt).toBe(historical.record.attempt + 1);
    expect(await plan.resolve()).toEqual(historical);
    await expect(plan.commit()).rejects.toThrow('skill_capture_operation_exists');
  },
);

test('a prepared ready-reuse receipt survives subsequent edits', async () => {
  const draft = await ready();
  const plan = await api.prepareDraft('reuse', actor, await currentReservation());
  expect(await plan.commit()).toEqual(draft);
  const manifest = validateSkillBundle(draft.capture.snapshot!);
  const edited = await bundle('unused', 'original bytes', {
    ...manifest,
    definition: { ...manifest.definition, body: 'later' },
  });
  await (await api.prepareEdit('edit', actor, expectation(draft), edited)).commit();
  expect(await plan.resolve()).toEqual(draft);
});

test('opaque storage cannot make an invalid bundle trusted merely by hashing it', async () => {
  const raw = await createIsolatedCapturePersistence(connection);
  const json = JSON.stringify({
    format: 'host-bundle-v1',
    revision: '0'.repeat(64),
    manifestJson: '{}',
    files: [],
  });
  const digest = captureDigest(json);
  await raw.commitSource(
    'raw',
    actor,
    { _id: sourceId, tenantId: actor.tenantId, generation: 0, digest, upstreamRevision },
    { digest, json },
  );
  await expect(api.readSource(actor, sourceId)).rejects.toThrow('invalid_skill_selection');
  await expect(
    api.prepareDraft('draft', actor, {
      sourceId,
      draftId,
      name: 'writer-draft',
      sourceGeneration: 1,
      sourceDigest: digest,
    }),
  ).rejects.toThrow('invalid_skill_selection');
});

test('a draft record cannot substitute another valid generation digest', async () => {
  const draft = await initializing();
  const newer = await (
    await api.prepareSource('newer', actor, {
      sourceId,
      expectedGeneration: 1,
      upstreamRevision,
      snapshot: await bundle('new'),
    })
  ).commit();
  await connection
    .db!.collection<{ _id: string; sourceDigest: string }>('capture_drafts')
    .updateOne({ _id: draftId }, { $set: { sourceDigest: newer.record.digest } });
  await expect(api.readDraft(actor, draftId)).rejects.toThrow('invalid_skill_selection');
  await expect(
    api.prepareComplete('bad', actor, expectation(draft), await copied(draft)),
  ).rejects.toThrow('invalid_skill_selection');
});

test('historical receipts also reject corrupted or semantically replaced payloads', async () => {
  const snapshot = await bundle();
  const plan = await api.prepareSource('source', actor, {
    sourceId,
    expectedGeneration: 0,
    upstreamRevision,
    snapshot,
  });
  const committed = await plan.commit();
  await connection
    .db!.collection<{ _id: string; json: string }>('capture_blobs')
    .updateOne({ _id: committed.record.digest }, { $set: { json: '{}' } });
  await expect(plan.resolve()).rejects.toThrow('skill_capture_payload_corrupt');
});

describe('validated capture with the synthetic transactional fence', () => {
  let authority: Awaited<ReturnType<typeof createIsolatedCaptureAuthority>>;
  let grant: CaptureAuthorization;
  const operations: CaptureOperation[] = [
    'source',
    'reserve',
    'complete',
    'fail',
    'recover',
    'edit',
  ];

  async function bounded<T>(operation: Promise<T>): Promise<T> {
    let timer: ReturnType<typeof setTimeout> | undefined;
    try {
      return await Promise.race([
        operation,
        new Promise<T>((_resolve, reject) => {
          timer = setTimeout(() => reject(new Error('synthetic_fixture_timeout')), 4000);
        }),
      ]);
    } finally {
      clearTimeout(timer);
    }
  }

  async function useCount() {
    const row = await connection.db!.collection<{ uses: number }>('capture_authority').findOne({});
    return row?.uses;
  }

  async function edit(draft: StoredSkillDraft, body: string, operationId = 'edit') {
    const manifest = validateSkillBundle(draft.capture.snapshot!);
    const snapshot = await bundle('unused', 'original bytes', {
      ...manifest,
      definition: { ...manifest.definition, body },
    });
    return (await api.prepareEdit(operationId, actor, expectation(draft), snapshot)).commit();
  }

  beforeEach(async () => {
    authority = await createIsolatedCaptureAuthority(connection);
    grant = await authority.replace(actor, sourceId, 0, operations);
    api = await createIsolatedFencedValidatedCapture(connection, grant);
  });

  test('validates and commits source, copied draft and authority receipts together', async () => {
    const draft = await ready();
    expect(validateSkillBundle(draft.capture.snapshot!).definition.body).toBe('original');
    expect(await useCount()).toBe(3);
    const receipts = await connection.db!.collection('capture_receipts').find({}).toArray();
    expect(receipts).toHaveLength(3);
    for (const receipt of receipts)
      expect(receipt.authorization).toEqual({ ...actor, sourceId, epoch: 1 });
    expect(await api.readDraft(actor, draftId)).toEqual(draft);
    expect(activateValidatedSkillCapture).toThrow('skill_capture_authorization_unavailable');
  });

  test('rejects a malformed source and a valid but mismatched completion before any write', async () => {
    const wrong = await bundle('original', 'original bytes', { skillId: 'd'.repeat(24) });
    await expect(source(wrong)).rejects.toThrow('invalid_skill_selection');
    expect(await useCount()).toBe(0);
    const draft = await initializing();
    const exact = await copied(draft);
    const manifest = validateSkillBundle(exact);
    const mismatch = await bundle('unused', 'original bytes', {
      ...manifest,
      definition: { ...manifest.definition, body: 'substituted' },
    });
    await expect(api.prepareComplete('bad', actor, expectation(draft), mismatch)).rejects.toThrow(
      'invalid_skill_selection',
    );
    expect(await useCount()).toBe(2);
    expect(await connection.db!.collection('capture_receipts').countDocuments()).toBe(2);
    expect((await api.readDraft(actor, draftId))?.capture.status).toBe('initializing');
  });

  test('revocation during asynchronous copying prevents completion of the validated bundle', async () => {
    const draft = await initializing();
    let entered!: () => void;
    let release!: () => void;
    const started = new Promise<void>((resolve) => {
      entered = resolve;
    });
    const released = new Promise<void>((resolve) => {
      release = resolve;
    });
    const copying = copySkillDraft(draft.capture, draft.record.attempt, async (file) => {
      entered();
      await released;
      return reader(draft.capture.source.snapshot)(file);
    });
    try {
      await bounded(
        Promise.race([
          started,
          copying.then(() => {
            throw new Error('copy_finished_before_barrier');
          }),
        ]),
      );
      await authority.replace(actor, sourceId, grant.epoch, []);
    } finally {
      release();
      await bounded(
        copying.then(
          () => undefined,
          () => undefined,
        ),
      );
    }
    const snapshot = await copying;
    const plan = await api.prepareComplete('revoked-copy', actor, expectation(draft), snapshot);
    await expect(plan.commit()).rejects.toThrow('authorization_denied');
    expect(await plan.resolve()).toBeNull();
    expect(await useCount()).toBe(2);
    expect(await api.readDraft(actor, draftId)).toEqual(draft);
    expect(await connection.db!.collection('capture_receipts').countDocuments()).toBe(2);
  });

  test('a concurrent revocation transaction blocks the actual validated completion transaction', async () => {
    const draft = await initializing();
    const plan = await api.prepareComplete(
      'contended',
      actor,
      expectation(draft),
      await copied(draft),
    );
    const session = await connection.startSession();
    let completion: Promise<PromiseSettledResult<StoredSkillDraft>[]> | undefined;
    try {
      session.startTransaction({
        readConcern: { level: 'snapshot' },
        writeConcern: { w: 'majority' },
      });
      const changed = await connection
        .db!.collection('capture_authority')
        .updateOne(
          { ...actor, sourceId, epoch: 1 },
          { $set: { operations: [] }, $inc: { epoch: 1 } },
          { session },
        );
      expect(changed.modifiedCount).toBe(1);
      completion = Promise.allSettled([plan.commit()]);
      const outcome = await bounded(completion);
      expect(outcome[0].status).toBe('rejected');
      if (outcome[0].status !== 'rejected') throw new Error('unexpected_capture_commit');
      expect([24, 112]).toContain((outcome[0].reason as mongo.MongoServerError).code);
      await session.commitTransaction();
      expect((await authority.read(actor, sourceId))?.epoch).toBe(2);
      expect(await api.readDraft(actor, draftId)).toEqual(draft);
      expect(await plan.resolve()).toBeNull();
      expect(await useCount()).toBe(2);
      expect(await connection.db!.collection('capture_blobs').countDocuments()).toBe(1);
      expect(await connection.db!.collection('capture_receipts').countDocuments()).toBe(2);
    } finally {
      try {
        if (session.inTransaction()) await bounded(session.abortTransaction());
      } finally {
        try {
          await bounded(session.endSession());
        } finally {
          if (completion) await bounded(completion);
        }
      }
    }
  }, 30000);

  test('ready reuse returns newer edits while retaining its base and still requires the grant', async () => {
    const original = await ready();
    const reuse = await api.prepareDraft('reuse', actor, await currentReservation());
    const edited = await edit(original, 'user edit');
    await (
      await api.prepareSource('sync', actor, {
        sourceId,
        expectedGeneration: 1,
        upstreamRevision,
        snapshot: await bundle('new source'),
      })
    ).commit();
    expect(await reuse.commit()).toEqual(edited);
    expect(edited.record.sourceGeneration).toBe(1);
    const blocked = await api.prepareDraft('blocked-reuse', actor, await currentReservation());
    await authority.replace(actor, sourceId, 1, []);
    await expect(blocked.commit()).rejects.toThrow('authorization_denied');
    expect(await blocked.resolve()).toBeNull();
    expect(await api.readDraft(actor, draftId)).toEqual(edited);
    expect(await useCount()).toBe(6);
  });

  test('lost completion replies resolve exact historical bundles after edit, sync and revocation', async () => {
    const draft = await initializing();
    const plan = await api.prepareComplete(
      'lost-reply',
      actor,
      expectation(draft),
      await copied(draft),
    );
    const completed = await plan.commit();
    await edit(completed, 'later edit');
    await (
      await api.prepareSource('sync', actor, {
        sourceId,
        expectedGeneration: 1,
        upstreamRevision,
        snapshot: await bundle('later source'),
      })
    ).commit();
    await authority.replace(actor, sourceId, 1, []);
    const restarted = await createIsolatedFencedValidatedCapture(connection, grant);
    expect(await plan.resolve()).toEqual(completed);
    expect(await restarted.resolveReceipt(actor, plan.operationId, plan.requestDigest)).toEqual(
      completed,
    );
    await expect(plan.commit()).rejects.toThrow('operation_exists');
    expect(await useCount()).toBe(5);
    await expect(
      restarted.resolveReceipt(
        { ...actor, ownerId: 'other' },
        plan.operationId,
        plan.requestDigest,
      ),
    ).rejects.toThrow('invalid_skill_selection');
    await connection
      .db!.collection<{ _id: string; json: string }>('capture_blobs')
      .updateOne({ _id: completed.record.digest! }, { $set: { json: '{}' } });
    await expect(plan.resolve()).rejects.toThrow('payload_corrupt');
  });

  test('a fresh epoch can recover a failed capture without reviving its old completion', async () => {
    const draft = await initializing();
    const old = await api.prepareComplete('old', actor, expectation(draft), await copied(draft));
    const failed = await (await api.prepareFail('fail', actor, expectation(draft))).commit();
    const recovery = await api.prepareRecover('stale-recovery', actor, expectation(failed));
    await authority.replace(actor, sourceId, 1, []);
    await expect(recovery.commit()).rejects.toThrow('authorization_denied');
    await expect(old.commit()).rejects.toThrow('authorization_denied');
    grant = await authority.replace(actor, sourceId, 2, operations);
    api = await createIsolatedFencedValidatedCapture(connection, grant);
    const recovered = await (
      await api.prepareRecover('recovery', actor, expectation(failed))
    ).commit();
    await expect(
      api.prepareComplete('stale-attempt', actor, expectation(draft), await copied(draft)),
    ).rejects.toThrow('invalid_skill_selection');
    const finished = await (
      await api.prepareComplete('finished', actor, expectation(recovered), await copied(recovered))
    ).commit();
    expect(finished.record.attempt).toBe(2);
    expect(finished.capture.status).toBe('ready');
    expect(await useCount()).toBe(5);
  });

  test.each(['owner', 'tenant', 'source', 'epoch', 'operation'])(
    'valid bundle semantics cannot bypass the bound %s',
    async (boundary) => {
      const ticket = { ...grant };
      if (boundary === 'owner') ticket.ownerId = 'other';
      if (boundary === 'tenant') ticket.tenantId = 'other';
      if (boundary === 'source') ticket.sourceId = 'd'.repeat(24);
      if (boundary === 'epoch') ticket.epoch = 999;
      if (boundary === 'operation') {
        const restricted = await authority.replace(actor, sourceId, 1, ['reserve']);
        ticket.epoch = restricted.epoch;
      }
      api = await createIsolatedFencedValidatedCapture(connection, ticket);
      await expect(source()).rejects.toThrow('authorization_denied');
      expect(await useCount()).toBe(0);
      expect(await connection.db!.collection('capture_sources').countDocuments()).toBe(0);
    },
  );

  test('detaches the authority ticket before the factory awaits database setup', async () => {
    const ticket = { ...grant };
    const pending = createIsolatedFencedValidatedCapture(connection, ticket);
    ticket.epoch = 999;
    ticket.ownerId = 'other';
    api = await pending;
    await expect(source()).resolves.toMatchObject({ record: { generation: 1 } });
    expect(await useCount()).toBe(1);
  });
});
