import { createHash } from 'node:crypto';
import { SKILL_BODY_MAX_LENGTH, SKILL_NAME_PATTERN } from 'librechat-data-provider';
import { validateRelativePath, validateSkillFrontmatter } from '@librechat/data-schemas';
import type { TSkill } from 'librechat-data-provider';
import { getSkillSelectionRevision, SkillSelectionError } from './selection';

const MAX_FILES = 64;
const MAX_BYTES = 5 * 1024 * 1024;
const MAX_MANIFEST_BYTES = 256 * 1024;
const SHA256 = /^[a-f0-9]{64}$/;
const OBJECT_ID = /^[a-f0-9]{24}$/;
const TOKEN = /^([a-z0-9][a-z0-9-]{0,63})@@([a-f0-9]{24})@@bundle-v1:([a-f0-9]{64})$/;

export type SkillBundleDefinition = Pick<
  TSkill,
  'name' | 'description' | 'body' | 'version' | 'frontmatter' | 'allowedTools' | 'userInvocable'
>;

export interface SkillBundleFile {
  path: string;
  mimeType: string;
  bytes: number;
  sha256: string;
}

/** Must come from one committed publication, never synthesized from unrelated live rows. */
export interface SkillBundleManifest {
  skillId: string;
  tenantId: string | null;
  logicalName: string;
  sourceRevision: string;
  definition: SkillBundleDefinition;
  files: SkillBundleFile[];
}

/** Serialized manifests and base64 bytes have no externally mutable Buffer/object references. */
export interface SkillBundleSnapshot {
  readonly format: 'host-bundle-v1';
  readonly revision: string;
  readonly manifestJson: string;
  readonly files: ReadonlyArray<Readonly<{ path: string; base64: string }>>;
}

export interface SkillBundleActor {
  userId: string;
  tenantId: string | null;
  agentId: string;
}

export interface SkillBundleAccess {
  skillId: string;
  tenantId: string | null;
  canView: boolean;
  active: boolean;
  inAgentScope: boolean;
}

export interface SkillBundleHostDeps {
  /** Fetch authoritative current ACL, tenant, activation and agent scope; null means deleted. */
  getAccess: (
    skillId: string,
    actor: Readonly<SkillBundleActor>,
  ) => Promise<SkillBundleAccess | null>;
  loadSnapshot: (revision: string) => Promise<SkillBundleSnapshot | null>;
  /** Apply current content inspection before exposing the definition or any bundled bytes. */
  inspect: (snapshot: SkillBundleSnapshot, actor: Readonly<SkillBundleActor>) => Promise<void>;
}

function fail(): never {
  throw new SkillSelectionError();
}

function hash(bytes: string | Uint8Array): string {
  return createHash('sha256').update(bytes).digest('hex');
}

function normalizeManifest(input: SkillBundleManifest): SkillBundleManifest {
  const json = JSON.stringify(input);
  if (Buffer.byteLength(json, 'utf8') > MAX_MANIFEST_BYTES) fail();
  const manifest = JSON.parse(json) as SkillBundleManifest;
  const { definition, files } = manifest;
  if (
    typeof manifest.skillId !== 'string' ||
    !OBJECT_ID.test(manifest.skillId) ||
    (manifest.tenantId !== null && typeof manifest.tenantId !== 'string') ||
    typeof manifest.logicalName !== 'string' ||
    !SKILL_NAME_PATTERN.test(manifest.logicalName) ||
    manifest.logicalName.length > 64 ||
    typeof manifest.sourceRevision !== 'string' ||
    !manifest.sourceRevision ||
    manifest.sourceRevision.length > 256 ||
    typeof definition.name !== 'string' ||
    !SKILL_NAME_PATTERN.test(definition.name) ||
    definition.name.length > 64 ||
    typeof definition.description !== 'string' ||
    definition.description.length > 1024 ||
    typeof definition.body !== 'string' ||
    definition.body.length > SKILL_BODY_MAX_LENGTH ||
    !Number.isSafeInteger(definition.version) ||
    definition.version < 1 ||
    (definition.userInvocable !== undefined && typeof definition.userInvocable !== 'boolean') ||
    (definition.allowedTools !== undefined &&
      (!Array.isArray(definition.allowedTools) ||
        definition.allowedTools.length > 128 ||
        definition.allowedTools.some((tool) => typeof tool !== 'string' || tool.length > 256))) ||
    validateSkillFrontmatter(definition.frontmatter).some(
      (issue) => issue.severity !== 'warning',
    ) ||
    !Array.isArray(files) ||
    files.length > MAX_FILES
  )
    fail();

  manifest.definition = {
    name: definition.name,
    description: definition.description,
    body: definition.body,
    version: definition.version,
    frontmatter: definition.frontmatter ?? {},
    allowedTools: definition.allowedTools,
    userInvocable: definition.userInvocable !== false,
  };

  let bytes = 0;
  const paths = new Set<string>();
  for (const file of files) {
    if (
      validateRelativePath(file.path).length > 0 ||
      file.path.toLowerCase() === 'skill.md' ||
      paths.has(file.path.toLowerCase()) ||
      !SHA256.test(file.sha256) ||
      typeof file.mimeType !== 'string' ||
      !file.mimeType ||
      file.mimeType.length > 256 ||
      !Number.isSafeInteger(file.bytes) ||
      file.bytes < 0
    )
      fail();
    paths.add(file.path.toLowerCase());
    bytes += file.bytes;
    if (bytes > MAX_BYTES) fail();
  }
  manifest.files = files.map(({ path, mimeType, bytes: size, sha256 }) => ({
    path,
    mimeType,
    bytes: size,
    sha256,
  }));
  manifest.files.sort((a, b) => (a.path < b.path ? -1 : Number(a.path > b.path)));
  return {
    skillId: manifest.skillId,
    tenantId: manifest.tenantId,
    logicalName: manifest.logicalName,
    sourceRevision: manifest.sourceRevision,
    definition: manifest.definition,
    files: manifest.files,
  };
}

function revisionOf(manifest: SkillBundleManifest): string {
  return hash(
    JSON.stringify({
      format: 'host-bundle-v1',
      skillId: manifest.skillId,
      tenantId: manifest.tenantId,
      logicalName: manifest.logicalName,
      sourceRevision: manifest.sourceRevision,
      definition: getSkillSelectionRevision(manifest.definition),
      description: manifest.definition.description,
      files: manifest.files.map(({ path, mimeType, bytes, sha256 }) => ({
        path,
        mimeType,
        bytes,
        sha256,
      })),
    }),
  );
}

/** Capture only bytes matching a committed manifest; concurrent edits cause rejection, never mixing. */
export async function captureSkillBundle({
  manifest: input,
  readFile,
}: {
  manifest: SkillBundleManifest;
  readFile: (file: Readonly<SkillBundleFile>) => Promise<AsyncIterable<Uint8Array>>;
}): Promise<SkillBundleSnapshot> {
  try {
    const manifest = normalizeManifest(input);
    const files: Array<Readonly<{ path: string; base64: string }>> = [];
    for (const file of manifest.files) {
      const buffer = Buffer.alloc(file.bytes);
      let bytes = 0;
      let chunks = 0;
      for await (const chunk of await readFile(Object.freeze({ ...file }))) {
        chunks++;
        if (chunks > file.bytes + 1024 || bytes + chunk.byteLength > file.bytes) fail();
        buffer.set(chunk, bytes);
        bytes += chunk.byteLength;
      }
      if (bytes !== file.bytes || hash(buffer) !== file.sha256) fail();
      files.push(Object.freeze({ path: file.path, base64: buffer.toString('base64') }));
    }
    return Object.freeze({
      format: 'host-bundle-v1',
      revision: revisionOf(manifest),
      manifestJson: JSON.stringify(manifest),
      files: Object.freeze(files),
    });
  } catch {
    return fail();
  }
}

function preflightSnapshot(snapshot: SkillBundleSnapshot): void {
  if (
    snapshot.format !== 'host-bundle-v1' ||
    !SHA256.test(snapshot.revision) ||
    typeof snapshot.manifestJson !== 'string' ||
    snapshot.manifestJson.length > MAX_MANIFEST_BYTES ||
    Buffer.byteLength(snapshot.manifestJson, 'utf8') > MAX_MANIFEST_BYTES ||
    !Array.isArray(snapshot.files) ||
    snapshot.files.length > MAX_FILES
  )
    fail();
  for (const file of snapshot.files) {
    if (
      typeof file.path !== 'string' ||
      typeof file.base64 !== 'string' ||
      file.base64.length > 4 * Math.ceil(MAX_BYTES / 3)
    )
      fail();
  }
}

/** Checks the entire payload, including unrequested files, on every cache/store retrieval. */
export function validateSkillBundle(snapshot: SkillBundleSnapshot): SkillBundleManifest {
  try {
    preflightSnapshot(snapshot);
    const manifest = normalizeManifest(JSON.parse(snapshot.manifestJson) as SkillBundleManifest);
    if (snapshot.manifestJson !== JSON.stringify(manifest)) fail();
    if (
      snapshot.revision !== revisionOf(manifest) ||
      snapshot.files.length !== manifest.files.length
    )
      fail();
    for (let i = 0; i < manifest.files.length; i++) {
      const expected = manifest.files[i];
      const actual = snapshot.files[i];
      if (
        actual.path !== expected.path ||
        actual.base64.length !== 4 * Math.ceil(expected.bytes / 3)
      )
        fail();
      const bytes = Buffer.from(actual.base64, 'base64');
      if (
        bytes.length !== expected.bytes ||
        bytes.toString('base64') !== actual.base64 ||
        hash(bytes) !== expected.sha256
      )
        fail();
    }
    return manifest;
  } catch {
    return fail();
  }
}

export function encodeSkillBundleSelection(snapshot: SkillBundleSnapshot): string {
  const manifest = validateSkillBundle(snapshot);
  return `${manifest.logicalName}@@${manifest.skillId}@@bundle-v1:${snapshot.revision}`;
}

/** A dormant host-only boundary: no routes, storage migration, picker activation or sandbox hooks. */
export function createSkillBundleHost(deps: SkillBundleHostDeps) {
  async function resolve(selection: string, inputActor: SkillBundleActor) {
    try {
      const match = TOKEN.exec(selection);
      if (!match) fail();
      const [, name, skillId, revision] = match;
      const actor = Object.freeze({ ...inputActor });
      if (
        typeof actor.userId !== 'string' ||
        !actor.userId ||
        typeof actor.agentId !== 'string' ||
        !actor.agentId
      )
        fail();
      const authorize = async () => {
        const access = await deps.getAccess(skillId, actor);
        if (
          !access ||
          access.skillId !== skillId ||
          access.tenantId !== actor.tenantId ||
          access.canView !== true ||
          access.active !== true ||
          access.inAgentScope !== true
        )
          fail();
      };
      await authorize();
      const stored = await deps.loadSnapshot(revision);
      if (!stored) fail();
      preflightSnapshot(stored);
      const snapshot: SkillBundleSnapshot = Object.freeze({
        format: stored.format,
        revision: stored.revision,
        manifestJson: stored.manifestJson,
        files: Object.freeze(
          stored.files.map(({ path, base64 }) => Object.freeze({ path, base64 })),
        ),
      });
      const manifest = validateSkillBundle(snapshot);
      if (
        snapshot.revision !== revision ||
        manifest.skillId !== skillId ||
        manifest.logicalName !== name ||
        manifest.tenantId !== actor.tenantId ||
        manifest.definition.userInvocable === false
      )
        fail();
      await deps.inspect(snapshot, actor);
      await authorize();
      return { snapshot, manifest };
    } catch {
      return fail();
    }
  }

  return {
    async prime({
      selection,
      actor,
      execution = 'host-read-only',
    }: {
      selection: string;
      actor: SkillBundleActor;
      execution?: 'host-read-only' | 'sandbox-mount' | 'execute';
    }) {
      if (execution !== 'host-read-only') fail();
      const { snapshot, manifest } = await resolve(selection, actor);
      return { selection, revision: snapshot.revision, definition: manifest.definition };
    },
    async read({
      selection,
      actor,
      path,
    }: {
      selection: string;
      actor: SkillBundleActor;
      path: string;
    }): Promise<{ bytes: Buffer; mimeType: string; revision: string }> {
      if (path !== 'SKILL.md' && validateRelativePath(path).length > 0) fail();
      const { snapshot, manifest } = await resolve(selection, actor);
      if (path === 'SKILL.md') {
        return {
          bytes: Buffer.from(manifest.definition.body, 'utf8'),
          mimeType: 'text/markdown',
          revision: snapshot.revision,
        };
      }
      const index = manifest.files.findIndex((file) => file.path === path);
      if (index < 0) fail();
      return {
        bytes: Buffer.from(snapshot.files[index].base64, 'base64'),
        mimeType: manifest.files[index].mimeType,
        revision: snapshot.revision,
      };
    },
  };
}
