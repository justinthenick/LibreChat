import { createHash } from 'node:crypto';
import { skillSyncGitHubSourceSchema } from 'librechat-data-provider';
import {
  validateRelativePath,
  validateSkillFrontmatter,
  deriveStructuredFrontmatterFields,
} from '@librechat/data-schemas';
import type { CaptureIdentity } from '@librechat/data-schemas/isolated-capture';
import type {
  SkillFrontmatter,
  SkillFrontmatterValue,
  SkillFrontmatterObject,
  SkillSyncGitHubSourceConfig,
} from 'librechat-data-provider';
import type {
  IsolatedValidatedCapture,
  PreparedSkillCapture,
  StoredSkillSource,
} from './persistence';
import type { SkillBundleFile, SkillBundleSnapshot } from './bundles';
import type { GitHubRepoAdapterConfig } from './sync/adapters/github';
import type { RepoTreeEntry } from './sync/adapters/types';
import { createGitHubRepoAdapter } from './sync/adapters/github';
import { SkillSelectionError } from './selection';
import { normalizeRepoPath } from './sync/path';
import { captureSkillBundle } from './bundles';
import { parseSkillMarkdown } from './parse';

/** Trusted source mapping loaded by the host, never accepted as request authorization. */
export interface GitHubGenerationSelection {
  skillId: string;
  tenantId: string;
  sourceId: string;
  owner: string;
  repo: string;
  commitSha: string;
  skillPath: string;
  name: string;
}

export interface GitHubGenerationInput {
  selection: GitHubGenerationSelection;
  source: SkillSyncGitHubSourceConfig;
  token: string;
  fetchFn: GitHubRepoAdapterConfig['fetchFn'];
  assertNotCancelled: () => void;
}

function fail(): never {
  throw new SkillSelectionError();
}

/** Bounds expansion before validators or manifest serialization traverse YAML aliases. */
function projectFrontmatter(
  input: Record<string, unknown> | undefined,
): SkillFrontmatter | undefined {
  if (input === undefined) return undefined;
  let nodes = 0;
  let bytes = 0;
  const active = new Set<object>();
  function charge(value: string): void {
    if (value.length > 128 * 1024) fail();
    bytes += Buffer.byteLength(JSON.stringify(value), 'utf8');
    if (bytes > 128 * 1024) fail();
  }
  function visit(value: unknown, depth: number): SkillFrontmatterValue {
    if (++nodes > 4096 || depth > 5) fail();
    bytes += 2;
    if (bytes > 128 * 1024) fail();
    if (value === null || typeof value === 'boolean') return value;
    if (typeof value === 'string') {
      charge(value);
      return value;
    }
    if (typeof value === 'number' && Number.isFinite(value)) return value;
    if (typeof value !== 'object' || value === null || active.has(value)) fail();
    const prototype = Object.getPrototypeOf(value);
    if (!Array.isArray(value) && prototype !== Object.prototype && prototype !== null) fail();
    active.add(value);
    try {
      if (Array.isArray(value)) {
        if (value.length > 4096 - nodes) fail();
        return value.map((entry) => visit(entry, depth + 1));
      }
      const projected: SkillFrontmatterObject = {};
      const entries = Object.entries(value);
      if (entries.length > 4096 - nodes) fail();
      for (const [key, entry] of entries) {
        if (['__proto__', 'constructor', 'prototype'].includes(key)) fail();
        charge(key);
        projected[key] = visit(entry, depth + 1);
      }
      return projected;
    } finally {
      active.delete(value);
    }
  }
  const projected = visit(input, 0);
  if (validateSkillFrontmatter(projected).some((issue) => issue.severity !== 'warning')) fail();
  return projected as SkillFrontmatter;
}

/** Produces all bytes from one pinned Git tree; never reads mutable mirror rows. */
export async function captureGitHubSkillGeneration(
  input: GitHubGenerationInput,
): Promise<SkillBundleSnapshot> {
  const selection = { ...input.selection };
  const source = skillSyncGitHubSourceSchema.parse({
    ...input.source,
    paths: input.source.paths.map((path) => (path === '' ? '.' : path)),
  });
  const { assertNotCancelled } = input;
  if (
    !selection.tenantId ||
    source.tenantId !== selection.tenantId ||
    source.id !== selection.sourceId ||
    source.owner !== selection.owner ||
    source.repo !== selection.repo ||
    !/^[a-f0-9]{40}$/.test(selection.commitSha) ||
    !/^[a-f0-9]{24}$/.test(selection.skillId) ||
    normalizeRepoPath(selection.skillPath) !== selection.skillPath ||
    (selection.skillPath !== '' && validateRelativePath(selection.skillPath).length > 0) ||
    !source.paths.some((path) => {
      const root = normalizeRepoPath(path);
      return !root || selection.skillPath === root || selection.skillPath.startsWith(`${root}/`);
    })
  )
    fail();
  const adapter = createGitHubRepoAdapter({
    source: { ...source, ref: selection.commitSha },
    token: input.token,
    fetchFn: input.fetchFn,
    verifyGitObjects: true,
  });
  assertNotCancelled();
  const commit = await adapter.resolveCommit();
  assertNotCancelled();
  const entries = await adapter.fetchTreeEntries(commit, {
    pathPrefix: selection.skillPath,
    assertNotCancelled,
  });
  const prefix = selection.skillPath ? `${selection.skillPath}/` : '';
  const paths = new Set<string>();
  const files: Array<RepoTreeEntry & { relative: string }> = [];
  let total = 0;
  for (const entry of entries) {
    const relative = entry.path.slice(prefix.length);
    if (
      !entry.path.startsWith(prefix) ||
      (relative.toLowerCase() !== 'skill.md' && validateRelativePath(relative).length > 0) ||
      paths.has(relative.toLowerCase())
    )
      fail();
    paths.add(relative.toLowerCase());
    if (entry.type === 'tree') continue;
    if (
      entry.type !== 'blob' ||
      !['100644', '100755'].includes(entry.mode ?? '') ||
      !Number.isSafeInteger(entry.size) ||
      entry.size === undefined ||
      entry.size < 0
    )
      fail();
    total += entry.size;
    if (total > 5 * 1024 * 1024 || files.length >= 65) fail();
    files.push({ ...entry, relative });
  }
  const definitions = files.filter((entry) => entry.relative.toLowerCase() === 'skill.md');
  if (definitions.length !== 1) fail();
  const definitionEntry = definitions[0];
  const buffers = new Map<string, Buffer>();
  for (const entry of files) {
    assertNotCancelled();
    const bytes = await adapter.fetchFileContent(commit, entry);
    assertNotCancelled();
    buffers.set(entry.relative, bytes);
  }
  const markdown = new TextDecoder('utf-8', { fatal: true }).decode(
    buffers.get(definitionEntry.relative),
  );
  const parsed = parseSkillMarkdown(markdown);
  const frontmatter = projectFrontmatter(parsed.frontmatter);
  const structured = deriveStructuredFrontmatterFields(frontmatter);
  if (parsed.parseError || parsed.invalidBooleans.length || parsed.name !== selection.name) fail();
  const manifestFiles: SkillBundleFile[] = files
    .filter((entry) => entry !== definitionEntry)
    .map((entry) => {
      const bytes = buffers.get(entry.relative)!;
      return {
        path: entry.relative,
        mimeType: 'application/octet-stream',
        bytes: bytes.length,
        sha256: createHash('sha256').update(bytes).digest('hex'),
      };
    });
  return captureSkillBundle({
    manifest: {
      skillId: selection.skillId,
      tenantId: selection.tenantId,
      logicalName: selection.name,
      sourceRevision: commit.id,
      definition: {
        name: parsed.name,
        description: parsed.description,
        body: markdown,
        version: 1,
        frontmatter,
        userInvocable: structured.userInvocable,
        allowedTools: structured.allowedTools,
      },
      files: manifestFiles,
    },
    readFile: async (file) =>
      (async function* () {
        yield buffers.get(file.path)!;
      })(),
  });
}

/** Retains the store's generation CAS, receipt recovery and commit-time authority contract. */
export async function prepareGitHubSkillGeneration(
  api: Pick<IsolatedValidatedCapture, 'prepareSource'>,
  operationId: string,
  actor: CaptureIdentity,
  expectedGeneration: number,
  input: GitHubGenerationInput,
): Promise<PreparedSkillCapture<StoredSkillSource>> {
  const retainedActor = { ...actor };
  const retainedInput = { ...input, selection: { ...input.selection } };
  if (retainedActor.tenantId !== retainedInput.selection.tenantId) fail();
  const snapshot = await captureGitHubSkillGeneration(retainedInput);
  retainedInput.assertNotCancelled();
  return api.prepareSource(operationId, retainedActor, {
    sourceId: retainedInput.selection.skillId,
    expectedGeneration,
    upstreamRevision: retainedInput.selection.commitSha,
    snapshot,
  });
}
