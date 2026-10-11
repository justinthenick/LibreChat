import { SKILL_NAME_PATTERN } from 'librechat-data-provider';
import type { SkillBundleManifest, SkillBundleSnapshot } from './bundles';
import { captureSkillBundle, validateSkillBundle } from './bundles';
import { SkillSelectionError } from './selection';

export interface CommittedSkillSource {
  readonly generation: number;
  readonly snapshot: SkillBundleSnapshot;
}

export interface SkillDraftCapture {
  readonly draftId: string;
  readonly name: string;
  readonly ownerId: string;
  readonly tenantId: string | null;
  readonly source: CommittedSkillSource;
  readonly attempt: number;
  readonly status: 'initializing' | 'failed' | 'ready';
  readonly snapshot: SkillBundleSnapshot | null;
}

export type SkillDraftCaptureRequest = Pick<
  SkillDraftCapture,
  'draftId' | 'name' | 'ownerId' | 'tenantId'
>;

function fail(): never {
  throw new SkillSelectionError();
}

function increment(value: number): number {
  if (!Number.isSafeInteger(value) || value < 0 || value === Number.MAX_SAFE_INTEGER) fail();
  return value + 1;
}

function immutableSnapshot(snapshot: SkillBundleSnapshot): SkillBundleSnapshot {
  validateSkillBundle(snapshot);
  return Object.freeze({
    format: snapshot.format,
    revision: snapshot.revision,
    manifestJson: snapshot.manifestJson,
    files: Object.freeze(snapshot.files.map(({ path, base64 }) => Object.freeze({ path, base64 }))),
  });
}

function immutableSource(source: CommittedSkillSource): CommittedSkillSource {
  if (!Number.isSafeInteger(source.generation) || source.generation < 1) fail();
  return Object.freeze({
    generation: source.generation,
    snapshot: immutableSnapshot(source.snapshot),
  });
}

/** Persist the returned record only with an atomic generation CAS and current authorization. */
export function commitSkillSource(
  current: CommittedSkillSource | null,
  expectedGeneration: number,
  candidate: SkillBundleSnapshot,
): CommittedSkillSource {
  if (expectedGeneration !== (current?.generation ?? 0)) fail();
  const snapshot = immutableSnapshot(candidate);
  const next = validateSkillBundle(snapshot);
  if (current) {
    const previous = validateSkillBundle(immutableSource(current).snapshot);
    if (previous.skillId !== next.skillId || previous.tenantId !== next.tenantId) fail();
  }
  return Object.freeze({ generation: increment(expectedGeneration), snapshot });
}

function draftManifest(draft: SkillDraftCapture): SkillBundleManifest {
  const manifest = validateSkillBundle(draft.source.snapshot);
  return {
    ...manifest,
    skillId: draft.draftId,
    logicalName: draft.name,
    sourceRevision: `capture:${manifest.skillId}:${draft.source.generation}:${draft.source.snapshot.revision}`,
    definition: { ...manifest.definition, name: draft.name },
  };
}

function immutableDraft(draft: SkillDraftCapture): SkillDraftCapture {
  const source = immutableSource(draft.source);
  const manifest = validateSkillBundle(source.snapshot);
  if (
    typeof draft.draftId !== 'string' ||
    !/^[a-f0-9]{24}$/.test(draft.draftId) ||
    draft.draftId === manifest.skillId ||
    typeof draft.name !== 'string' ||
    !SKILL_NAME_PATTERN.test(draft.name) ||
    draft.name.length > 64 ||
    typeof draft.ownerId !== 'string' ||
    !draft.ownerId ||
    draft.tenantId !== manifest.tenantId ||
    !Number.isSafeInteger(draft.attempt) ||
    draft.attempt < 1 ||
    !['initializing', 'failed', 'ready'].includes(draft.status) ||
    (draft.status === 'ready') !== (draft.snapshot !== null)
  )
    fail();
  const snapshot = draft.snapshot === null ? null : immutableSnapshot(draft.snapshot);
  if (snapshot) {
    const content = validateSkillBundle(snapshot);
    if (
      content.skillId !== draft.draftId ||
      content.tenantId !== draft.tenantId ||
      content.logicalName !== draft.name ||
      content.definition.name !== draft.name
    )
      fail();
  }
  return Object.freeze({ ...draft, source, snapshot });
}

/** A ready draft is reused unchanged; an incomplete draft must never be returned as usable. */
export function beginSkillDraft(
  source: CommittedSkillSource,
  existing: SkillDraftCapture | null,
  request: SkillDraftCaptureRequest,
): SkillDraftCapture {
  const candidate = immutableDraft({
    ...request,
    source,
    attempt: 1,
    status: 'initializing',
    snapshot: null,
  });
  if (!existing) return candidate;
  const current = immutableDraft(existing);
  if (
    current.draftId !== candidate.draftId ||
    current.ownerId !== candidate.ownerId ||
    current.tenantId !== candidate.tenantId ||
    current.name !== candidate.name ||
    validateSkillBundle(current.source.snapshot).skillId !==
      validateSkillBundle(candidate.source.snapshot).skillId ||
    current.status !== 'ready'
  )
    fail();
  return current;
}

function initializing(draft: SkillDraftCapture, expectedAttempt: number): SkillDraftCapture {
  const current = immutableDraft(draft);
  if (current.status !== 'initializing' || current.attempt !== expectedAttempt) fail();
  return current;
}

/** Copy failures leave initialization pending until explicitly failed or recovered; never delete. */
export async function copySkillDraft(
  draft: SkillDraftCapture,
  expectedAttempt: number,
  readFile: Parameters<typeof captureSkillBundle>[0]['readFile'],
): Promise<SkillBundleSnapshot> {
  const current = initializing(draft, expectedAttempt);
  return captureSkillBundle({ manifest: draftManifest(current), readFile });
}

/** Persist with an atomic initializing/attempt CAS; bytes must equal the pinned source in full. */
export function completeSkillDraft(
  draft: SkillDraftCapture,
  expectedAttempt: number,
  copied: SkillBundleSnapshot,
): SkillDraftCapture {
  const current = initializing(draft, expectedAttempt);
  const snapshot = immutableSnapshot(copied);
  if (
    snapshot.manifestJson !== JSON.stringify(draftManifest(current)) ||
    JSON.stringify(snapshot.files) !== JSON.stringify(current.source.snapshot.files)
  )
    fail();
  return Object.freeze({ ...current, status: 'ready', snapshot });
}

export function failSkillDraft(
  draft: SkillDraftCapture,
  expectedAttempt: number,
): SkillDraftCapture {
  return Object.freeze({ ...initializing(draft, expectedAttempt), status: 'failed' });
}

/** Explicit recovery fences every old worker and keeps the original committed source pinned. */
export function recoverSkillDraft(
  draft: SkillDraftCapture,
  expectedAttempt: number,
): SkillDraftCapture {
  const current = immutableDraft(draft);
  if (current.status === 'ready' || current.attempt !== expectedAttempt) fail();
  return Object.freeze({ ...current, attempt: increment(current.attempt), status: 'initializing' });
}
