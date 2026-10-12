import {
  activateSkillCapturePersistence,
  captureDigest,
  captureRequestDigest,
  createIsolatedCapturePersistence,
  createIsolatedFencedCapturePersistence,
} from '@librechat/data-schemas/isolated-capture';
import type {
  CaptureDraft,
  CaptureIdentity,
  CapturePayload,
  CaptureSource,
  CapturePersistence,
  CaptureAuthorization,
} from '@librechat/data-schemas/isolated-capture';
import type { Connection } from 'mongoose';
import type { CommittedSkillSource, SkillDraftCapture, SkillDraftCaptureRequest } from './capture';
import type { SkillBundleSnapshot } from './bundles';
import {
  beginSkillDraft,
  commitSkillSource,
  completeSkillDraft,
  failSkillDraft,
  recoverSkillDraft,
  validateSkillDraftCapture,
} from './capture';
import { SkillSelectionError } from './selection';
import { validateSkillBundle } from './bundles';

export interface StoredSkillSource {
  readonly record: Readonly<CaptureSource>;
  readonly capture: CommittedSkillSource;
}

export interface StoredSkillDraft {
  readonly record: Readonly<CaptureDraft>;
  readonly capture: SkillDraftCapture;
}

export interface PreparedSkillCapture<T> {
  readonly operationId: string;
  readonly requestDigest: string;
  readonly commit: () => Promise<T>;
  /** Null means unresolved; it never authorizes replay of the mutation. */
  readonly resolve: () => Promise<T | null>;
}

export interface DraftExpectation {
  draftId: string;
  attempt: number;
  revision: number;
}

export type SkillDraftReservation = Readonly<
  Pick<CaptureDraft, '_id' | 'name' | 'sourceId' | 'status' | 'attempt' | 'revision'>
>;

export interface IsolatedValidatedCapture {
  resolveReceipt: (
    actor: CaptureIdentity,
    operationId: string,
    requestDigest: string,
  ) => Promise<StoredSkillSource | StoredSkillDraft | null>;
  readSource: (actor: CaptureIdentity, sourceId: string) => Promise<StoredSkillSource | null>;
  readDraft: (actor: CaptureIdentity, draftId: string) => Promise<StoredSkillDraft | null>;
  readDraftReservation: (
    actor: CaptureIdentity,
    request: Pick<CaptureDraft, 'sourceId' | 'name'>,
  ) => Promise<SkillDraftReservation | null>;
  prepareSource: (
    operationId: string,
    actor: CaptureIdentity,
    request: {
      sourceId: string;
      expectedGeneration: number;
      upstreamRevision: string;
      snapshot: SkillBundleSnapshot;
    },
  ) => Promise<PreparedSkillCapture<StoredSkillSource>>;
  prepareDraft: (
    operationId: string,
    actor: CaptureIdentity,
    request: Pick<SkillDraftCaptureRequest, 'draftId' | 'name'> &
      Pick<CaptureDraft, 'sourceId' | 'sourceGeneration' | 'sourceDigest'>,
  ) => Promise<PreparedSkillCapture<StoredSkillDraft>>;
  prepareDraftByName: IsolatedValidatedCapture['prepareDraft'];
  prepareComplete: (
    operationId: string,
    actor: CaptureIdentity,
    expected: DraftExpectation,
    snapshot: SkillBundleSnapshot,
  ) => Promise<PreparedSkillCapture<StoredSkillDraft>>;
  prepareEdit: (
    operationId: string,
    actor: CaptureIdentity,
    expected: DraftExpectation,
    snapshot: SkillBundleSnapshot,
  ) => Promise<PreparedSkillCapture<StoredSkillDraft>>;
  prepareFail: (
    operationId: string,
    actor: CaptureIdentity,
    expected: DraftExpectation,
  ) => Promise<PreparedSkillCapture<StoredSkillDraft>>;
  prepareRecover: (
    operationId: string,
    actor: CaptureIdentity,
    expected: DraftExpectation,
  ) => Promise<PreparedSkillCapture<StoredSkillDraft>>;
}

function fail(): never {
  throw new SkillSelectionError();
}

function actorCopy(input: CaptureIdentity): Readonly<CaptureIdentity> {
  const actor = { ownerId: input.ownerId, tenantId: input.tenantId };
  if (
    typeof actor.ownerId !== 'string' ||
    !actor.ownerId ||
    actor.ownerId.length > 256 ||
    (actor.tenantId !== null &&
      (typeof actor.tenantId !== 'string' || !actor.tenantId || actor.tenantId.length > 256))
  )
    fail();
  return Object.freeze(actor);
}

function validId(id: string): string {
  if (typeof id !== 'string' || !/^[a-f0-9]{24}$/.test(id)) fail();
  return id;
}

function validName(name: string): string {
  if (typeof name !== 'string' || !/^[a-z0-9][a-z0-9-]{0,63}$/.test(name)) fail();
  return name;
}

function draftRequestCopy(
  input: Parameters<IsolatedValidatedCapture['prepareDraft']>[2],
): Parameters<IsolatedValidatedCapture['prepareDraft']>[2] {
  const request = {
    draftId: validId(input.draftId),
    name: validName(input.name),
    sourceId: validId(input.sourceId),
    sourceGeneration: input.sourceGeneration,
    sourceDigest: input.sourceDigest,
  };
  if (
    request.draftId === request.sourceId ||
    !Number.isSafeInteger(request.sourceGeneration) ||
    request.sourceGeneration < 1 ||
    typeof request.sourceDigest !== 'string' ||
    !/^[a-f0-9]{64}$/.test(request.sourceDigest)
  )
    fail();
  return Object.freeze(request);
}

function snapshotCopy(snapshot: SkillBundleSnapshot): SkillBundleSnapshot {
  return commitSkillSource(null, 0, snapshot).snapshot;
}

function encode(snapshot: SkillBundleSnapshot): CapturePayload {
  const json = JSON.stringify(snapshot);
  return Object.freeze({ json, digest: captureDigest(json) });
}

export function activateValidatedSkillCapture(): never {
  return activateSkillCapturePersistence();
}

/** Isolated validation/storage integration only. This factory confers no application authority. */
export async function createIsolatedValidatedCapture(
  connection: Connection,
): Promise<IsolatedValidatedCapture> {
  const store = await createIsolatedCapturePersistence(connection);
  return validatedCapture(store);
}

/** Full bundle validation with synthetic commit fencing; still no live application authority. */
export async function createIsolatedFencedValidatedCapture(
  connection: Connection,
  authorization: CaptureAuthorization,
): Promise<IsolatedValidatedCapture> {
  const store = await createIsolatedFencedCapturePersistence(connection, authorization);
  return validatedCapture(store);
}

function validatedCapture(store: CapturePersistence): IsolatedValidatedCapture {
  async function loadSnapshot(digest: string): Promise<SkillBundleSnapshot> {
    const json = await store.readPayload(digest);
    return snapshotCopy(JSON.parse(json) as SkillBundleSnapshot);
  }

  async function sourceRecord(
    record: CaptureSource,
    retained?: CaptureSource,
  ): Promise<StoredSkillSource> {
    validId(record._id);
    if (
      !Number.isSafeInteger(record.generation) ||
      record.generation < 1 ||
      !/^(?:[a-f0-9]{40}|[a-f0-9]{64})$/.test(record.upstreamRevision)
    )
      fail();
    const [snapshot, history] = await Promise.all([
      loadSnapshot(record.digest),
      retained ?? store.readGeneration(record._id, record.tenantId, record.generation),
    ]);
    const manifest = validateSkillBundle(snapshot);
    if (
      !history ||
      history.digest !== record.digest ||
      history.upstreamRevision !== record.upstreamRevision ||
      manifest.skillId !== record._id ||
      manifest.tenantId !== record.tenantId ||
      manifest.sourceRevision !== record.upstreamRevision ||
      manifest.logicalName !== manifest.definition.name
    )
      fail();
    return Object.freeze({
      record: Object.freeze({ ...record }),
      capture: Object.freeze({ generation: record.generation, snapshot }),
    });
  }

  async function draftRecord(record: CaptureDraft): Promise<StoredSkillDraft> {
    validId(record._id);
    validId(record.sourceId);
    actorCopy(record);
    if (!Number.isSafeInteger(record.sourceGeneration) || record.sourceGeneration < 1) fail();
    if (!Number.isSafeInteger(record.revision) || record.revision < 1) fail();
    const history = await store.readGeneration(
      record.sourceId,
      record.tenantId,
      record.sourceGeneration,
    );
    if (
      !history ||
      history.digest !== record.sourceDigest ||
      (record.status === 'ready') !== (record.digest !== null)
    )
      fail();
    const [source, snapshot] = await Promise.all([
      sourceRecord(history),
      record.digest === null ? Promise.resolve(null) : loadSnapshot(record.digest),
    ]);
    const capture = validateSkillDraftCapture({
      draftId: record._id,
      name: record.name,
      ownerId: record.ownerId,
      tenantId: record.tenantId,
      source: source.capture,
      attempt: record.attempt,
      status: record.status,
      snapshot,
    });
    if (
      snapshot &&
      validateSkillBundle(snapshot).sourceRevision !==
        `capture:${record.sourceId}:${record.sourceGeneration}:${source.capture.snapshot.revision}`
    )
      fail();
    return Object.freeze({ record: Object.freeze({ ...record }), capture });
  }

  async function readSource(
    inputActor: CaptureIdentity,
    sourceId: string,
  ): Promise<StoredSkillSource | null> {
    const actor = actorCopy(inputActor);
    const record = await store.readSource(validId(sourceId), actor.tenantId);
    return record ? sourceRecord(record) : null;
  }

  async function readDraft(
    inputActor: CaptureIdentity,
    draftId: string,
  ): Promise<StoredSkillDraft | null> {
    const actor = actorCopy(inputActor);
    const record = await store.readDraft(validId(draftId), actor);
    return record ? draftRecord(record) : null;
  }

  async function readDraftReservation(
    inputActor: CaptureIdentity,
    input: Pick<CaptureDraft, 'sourceId' | 'name'>,
  ): Promise<SkillDraftReservation | null> {
    const actor = actorCopy(inputActor);
    const sourceId = validId(input.sourceId);
    const name = validName(input.name);
    const record = await store.readDraftReservation(name, actor);
    if (!record) return null;
    if (
      record.tenantId !== actor.tenantId ||
      record.ownerId !== actor.ownerId ||
      record.sourceId !== sourceId ||
      record.name !== name ||
      record._id === sourceId ||
      !['initializing', 'failed', 'ready'].includes(record.status) ||
      !Number.isSafeInteger(record.attempt) ||
      record.attempt < 1 ||
      !Number.isSafeInteger(record.revision) ||
      record.revision < 1
    )
      fail();
    return Object.freeze({
      _id: validId(record._id),
      name,
      sourceId,
      status: record.status,
      attempt: record.attempt,
      revision: record.revision,
    });
  }

  async function resolveReceipt(
    inputActor: CaptureIdentity,
    operationId: string,
    requestDigest: string,
  ): Promise<StoredSkillSource | StoredSkillDraft | null> {
    const actor = actorCopy(inputActor);
    const receipt = await store.resolve(operationId, requestDigest);
    if (!receipt) return null;
    const record = receipt.result;
    if (record.tenantId !== actor.tenantId) fail();
    if ('sourceGeneration' in record) {
      if (record.ownerId !== actor.ownerId) fail();
      return draftRecord(record);
    }
    return sourceRecord(record);
  }

  function prepared<T>(
    operationId: string,
    requestDigest: string,
    write: () => Promise<CaptureSource | CaptureDraft>,
    validate: (record: CaptureSource | CaptureDraft) => Promise<T>,
  ): PreparedSkillCapture<T> {
    return Object.freeze({
      operationId,
      requestDigest,
      commit: async () => validate(await write()),
      resolve: async () => {
        const receipt = await store.resolve(operationId, requestDigest);
        return receipt ? validate(receipt.result) : null;
      },
    });
  }

  async function prepareSource(
    operationId: string,
    inputActor: CaptureIdentity,
    input: Parameters<IsolatedValidatedCapture['prepareSource']>[2],
  ): Promise<PreparedSkillCapture<StoredSkillSource>> {
    const actor = actorCopy(inputActor);
    const sourceId = validId(input.sourceId);
    const expectedGeneration = input.expectedGeneration;
    const upstreamRevision = input.upstreamRevision;
    const snapshot = snapshotCopy(input.snapshot);
    const manifest = validateSkillBundle(snapshot);
    if (
      manifest.skillId !== sourceId ||
      manifest.tenantId !== actor.tenantId ||
      manifest.sourceRevision !== upstreamRevision ||
      manifest.logicalName !== manifest.definition.name
    )
      fail();
    const current = await readSource(actor, sourceId);
    const next = commitSkillSource(current?.capture ?? null, expectedGeneration, snapshot);
    const payload = encode(next.snapshot);
    const candidate: CaptureSource = {
      _id: sourceId,
      tenantId: actor.tenantId,
      generation: expectedGeneration,
      digest: payload.digest,
      upstreamRevision,
    };
    return prepared(
      operationId,
      captureRequestDigest('source', actor, candidate, payload),
      () => store.commitSource(operationId, actor, candidate, payload),
      async (result) => {
        if (
          !('generation' in result) ||
          result._id !== sourceId ||
          result.tenantId !== actor.tenantId ||
          result.generation !== next.generation ||
          result.digest !== payload.digest ||
          result.upstreamRevision !== upstreamRevision
        )
          fail();
        return sourceRecord(result);
      },
    );
  }

  async function prepareDraft(
    operationId: string,
    inputActor: CaptureIdentity,
    input: Parameters<IsolatedValidatedCapture['prepareDraft']>[2],
  ): Promise<PreparedSkillCapture<StoredSkillDraft>> {
    const actor = actorCopy(inputActor);
    const request = draftRequestCopy(input);
    const [record, existing] = await Promise.all([
      store.readGeneration(request.sourceId, actor.tenantId, request.sourceGeneration),
      readDraft(actor, request.draftId),
    ]);
    if (!record || record.digest !== request.sourceDigest) fail();
    const source = await sourceRecord(record, record);
    beginSkillDraft(source.capture, existing?.capture ?? null, {
      draftId: request.draftId,
      name: request.name,
      ...actor,
    });
    const reservation = {
      _id: request.draftId,
      name: request.name,
      sourceId: request.sourceId,
      sourceGeneration: request.sourceGeneration,
      sourceDigest: request.sourceDigest,
    };
    return prepared(
      operationId,
      captureRequestDigest('reserve', actor, reservation),
      () => store.reserve(operationId, actor, reservation),
      async (result) => {
        if (
          !('sourceGeneration' in result) ||
          result._id !== request.draftId ||
          result.name !== request.name ||
          result.sourceId !== request.sourceId ||
          result.ownerId !== actor.ownerId ||
          result.tenantId !== actor.tenantId
        )
          fail();
        return draftRecord(result);
      },
    );
  }

  async function prepareDraftByName(
    operationId: string,
    inputActor: CaptureIdentity,
    input: Parameters<IsolatedValidatedCapture['prepareDraft']>[2],
  ): Promise<PreparedSkillCapture<StoredSkillDraft>> {
    const actor = actorCopy(inputActor);
    const request = draftRequestCopy(input);
    const existing = await readDraftReservation(actor, request);
    return prepareDraft(operationId, actor, {
      ...request,
      draftId: existing?._id ?? request.draftId,
    });
  }

  async function transition(
    operationId: string,
    inputActor: CaptureIdentity,
    input: DraftExpectation,
    action: 'complete' | 'edit' | 'fail' | 'recover',
    candidate?: SkillBundleSnapshot,
  ): Promise<PreparedSkillCapture<StoredSkillDraft>> {
    const actor = actorCopy(inputActor);
    const expected = {
      draftId: validId(input.draftId),
      attempt: input.attempt,
      revision: input.revision,
    };
    const snapshot = candidate ? snapshotCopy(candidate) : null;
    const current = await readDraft(actor, expected.draftId);
    if (
      !current ||
      current.record.revision !== expected.revision ||
      current.record.attempt !== expected.attempt
    )
      fail();
    let next: SkillDraftCapture;
    if (action === 'complete') {
      if (!snapshot) fail();
      next = completeSkillDraft(current.capture, expected.attempt, snapshot);
    } else if (action === 'edit') {
      if (!snapshot || current.capture.status !== 'ready') fail();
      next = validateSkillDraftCapture({ ...current.capture, snapshot });
      if (
        validateSkillBundle(snapshot).sourceRevision !==
        validateSkillBundle(current.capture.snapshot!).sourceRevision
      )
        fail();
    } else if (action === 'fail') next = failSkillDraft(current.capture, expected.attempt);
    else next = recoverSkillDraft(current.capture, expected.attempt);
    const payload = snapshot ? encode(next.snapshot!) : undefined;
    const expectedResult: CaptureDraft = {
      ...current.record,
      revision: current.record.revision + 1,
      attempt: next.attempt,
      status: next.status,
      digest: payload?.digest ?? current.record.digest,
    };
    return prepared(
      operationId,
      captureRequestDigest(action, actor, current.record, payload),
      () => store.transition(operationId, actor, current.record, action, payload),
      async (result) => {
        if (
          !('sourceGeneration' in result) ||
          captureRequestDigest(action, actor, result) !==
            captureRequestDigest(action, actor, expectedResult)
        )
          fail();
        return draftRecord(result);
      },
    );
  }

  return {
    readSource,
    readDraft,
    readDraftReservation,
    resolveReceipt,
    prepareSource,
    prepareDraft,
    prepareDraftByName,
    prepareComplete: (id, actor, expected, snapshot) =>
      transition(id, actor, expected, 'complete', snapshot),
    prepareEdit: (id, actor, expected, snapshot) =>
      transition(id, actor, expected, 'edit', snapshot),
    prepareFail: (id, actor, expected) => transition(id, actor, expected, 'fail'),
    prepareRecover: (id, actor, expected) => transition(id, actor, expected, 'recover'),
  };
}
