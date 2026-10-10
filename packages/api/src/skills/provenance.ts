type JsonObject = Record<string, unknown>;
const SHA = /^[a-f0-9]{40}$/;

export class ManagedDraftProvenanceError extends Error {
  readonly code = 'managed_draft_provenance_conflict';

  constructor() {
    super(
      'This draft has missing, invalid, or stale source provenance. Keep your edits in this draft: rename it to an unused name, sync the source, then create a fresh draft and review/copy your changes before publishing. Editing and Trial remain available.',
    );
    this.name = 'ManagedDraftProvenanceError';
  }
}

function fail(): never {
  throw new ManagedDraftProvenanceError();
}
function object(value: unknown): JsonObject {
  if (!value || typeof value !== 'object' || Array.isArray(value)) fail();
  return value as JsonObject;
}
function text(value: unknown): string {
  if (
    typeof value !== 'string' ||
    !value ||
    value.length > 1024 ||
    value.trim() !== value ||
    /[\x00-\x1f\x7f]/.test(value)
  )
    fail();
  return value;
}
function sha(value: unknown): string {
  const result = text(value);
  if (!SHA.test(result)) fail();
  return result;
}

export interface ManagedDraftProvenance {
  readonly sourceId: string;
  readonly owner: string;
  readonly repo: string;
  readonly ref: string;
  readonly skillPath: string;
  readonly baseCommitSha: string;
  readonly baseSkillBlobSha: string;
  readonly publishedCommitSha: string;
}

/** No credential access or network requests. Never fill missing draft provenance from today's source. */
export function validateManagedDraftProvenance(
  draftMetadata: unknown,
  published: {
    _id: { toString(): string };
    source?: unknown;
    version?: unknown;
    sourceMetadata?: unknown;
  },
): Readonly<ManagedDraftProvenance> {
  const draft = object(draftMetadata);
  const current = object(published.sourceMetadata);
  if (
    published.source !== 'github' ||
    !['draft', 'trial', 'publish_pending'].includes(String(draft.lifecycle)) ||
    draft.draftOfSkillId !== published._id.toString() ||
    draft.provider !== 'github' ||
    current.provider !== 'github' ||
    !Number.isSafeInteger(draft.baseVersion) ||
    Number(draft.baseVersion) < 1 ||
    !Number.isSafeInteger(published.version) ||
    Number(published.version) < Number(draft.baseVersion)
  )
    fail();
  const identity = {} as Record<'sourceId' | 'owner' | 'repo' | 'ref' | 'skillPath', string>;
  for (const key of ['sourceId', 'owner', 'repo', 'ref', 'skillPath'] as const) {
    identity[key] = text(draft[key]);
    if (identity[key] !== text(current[key])) fail();
  }
  const segments = identity.skillPath.split('/');
  if (
    segments.length > 32 ||
    segments.some((part) => !part || part === '.' || part === '..' || part.includes('\\'))
  )
    fail();
  const baseSkillBlobSha = sha(draft.baseSkillBlobSha);
  if (baseSkillBlobSha !== sha(current.skillBlobSha)) fail();
  return Object.freeze({
    ...identity,
    baseCommitSha: sha(draft.baseCommitSha),
    baseSkillBlobSha,
    publishedCommitSha: sha(current.commitSha),
  });
}

/** Compare immutable Git trees at pinned commits, including every bundled file and mode. */
export async function assertManagedDraftUpstream(
  provenance: Readonly<ManagedDraftProvenance>,
  target: { commitSha: string; treeSha: string },
  getJson: (path: string) => Promise<unknown>,
): Promise<void> {
  try {
    const selected = Object.freeze({
      commitSha: sha(target.commitSha),
      treeSha: sha(target.treeSha),
    });
    const trees = new Map<string, JsonObject[]>();
    async function entries(id: string): Promise<JsonObject[]> {
      const key = sha(id);
      const cached = trees.get(key);
      if (cached) return cached;
      const result = object(await getJson(`/git/trees/${key}`));
      if (result.sha !== key || result.truncated !== false || !Array.isArray(result.tree)) fail();
      const list = result.tree.map(object);
      trees.set(key, list);
      return list;
    }
    async function skillTree(root: string): Promise<string> {
      let id = sha(root);
      for (const part of provenance.skillPath.split('/')) {
        const matches = (await entries(id)).filter((entry) => entry.path === part);
        if (matches.length !== 1 || matches[0].type !== 'tree' || matches[0].mode !== '040000')
          fail();
        id = sha(matches[0].sha);
      }
      return id;
    }
    async function rootFor(commit: string): Promise<string> {
      if (commit === selected.commitSha) return selected.treeSha;
      const result = object(await getJson(`/git/commits/${sha(commit)}`));
      if (result.sha !== commit) fail();
      return sha(object(result.tree).sha);
    }
    const original = await skillTree(await rootFor(provenance.baseCommitSha));
    const definition = (await entries(original)).filter((entry) => entry.path === 'SKILL.md');
    if (
      definition.length !== 1 ||
      definition[0].type !== 'blob' ||
      !['100644', '100755'].includes(String(definition[0].mode)) ||
      definition[0].sha !== provenance.baseSkillBlobSha
    )
      fail();
    for (const commit of [provenance.publishedCommitSha, selected.commitSha]) {
      if ((await skillTree(await rootFor(commit))) !== original) fail();
    }
  } catch {
    fail();
  }
}
