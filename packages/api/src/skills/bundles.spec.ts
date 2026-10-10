import { createHash } from 'node:crypto';
import { encodeSkillSelection, parseSkillSelection } from 'librechat-data-provider';
import type {
  SkillBundleActor,
  SkillBundleAccess,
  SkillBundleManifest,
  SkillBundleSnapshot,
} from './bundles';
import {
  captureSkillBundle,
  createSkillBundleHost,
  encodeSkillBundleSelection,
  validateSkillBundle,
} from './bundles';
import { getSkillSelectionRevision } from './selection';

const id = '123456789012345678901234';
const actor: SkillBundleActor = { userId: 'reader', tenantId: 'tenant', agentId: 'agent' };
const failure = /invalid_skill_selection/;

function fixture() {
  const source = new Map([
    ['references/a.txt', Buffer.from('reviewed reference')],
    ['assets/image.png', Buffer.from([137, 80, 78, 71, 0, 255])],
  ]);
  const manifest: SkillBundleManifest = {
    skillId: id,
    tenantId: 'tenant',
    logicalName: 'writer',
    sourceRevision: 'committed-publication-1',
    definition: {
      name: 'writer-draft',
      description: 'Writes text',
      body: 'Read references/a.txt',
      version: 3,
      frontmatter: { metadata: { b: 2, a: 1 } },
    },
    files: [...source].map(([path, bytes]) => ({
      path,
      mimeType: path.endsWith('.png') ? 'image/png' : 'text/plain',
      bytes: bytes.length,
      sha256: createHash('sha256').update(bytes).digest('hex'),
    })),
  };
  const readFile = async ({ path }: { path: string }) => {
    const bytes = source.get(path);
    if (!bytes) throw new Error('deleted');
    return (async function* () {
      yield bytes;
    })();
  };
  return { source, manifest, readFile };
}

async function environment() {
  const f = fixture();
  const snapshot = await captureSkillBundle(f);
  const token = encodeSkillBundleSelection(snapshot);
  const store = new Map<string, SkillBundleSnapshot>([[snapshot.revision, snapshot]]);
  let access: SkillBundleAccess | null = {
    skillId: id,
    tenantId: 'tenant',
    canView: true,
    active: true,
    userInvocable: true,
    inAgentScope: true,
  };
  const calls = { access: 0, load: 0, inspect: 0 };
  let duringLoad = () => {};
  let duringInspection = () => {};
  const host = createSkillBundleHost({
    getAccess: async (_id, currentActor) => {
      calls.access++;
      return currentActor.userId === 'reader' && currentActor.agentId === 'agent' ? access : null;
    },
    loadSnapshot: async (revision) => {
      calls.load++;
      duringLoad();
      return store.get(revision) ?? null;
    },
    inspect: async () => {
      calls.inspect++;
      duringInspection();
    },
  });
  return {
    ...f,
    snapshot,
    token,
    store,
    calls,
    host,
    revoke: () => {
      access = null;
    },
    setAccess: (patch: Partial<SkillBundleAccess>) => {
      if (access) access = { ...access, ...patch };
    },
    onLoad: (fn: () => void) => {
      duringLoad = fn;
    },
    onInspect: (fn: () => void) => {
      duringInspection = fn;
    },
    read: (path = 'references/a.txt') => host.read({ selection: token, actor, path }),
  };
}

describe('immutable host skill bundles', () => {
  it.each([
    ['"userInvocable":true', '"userInvocable":"false"'],
    ['"userInvocable":true', '"userInvocable":{}'],
    ['"frontmatter":{', '"allowedTools":false,"frontmatter":{'],
    ['"frontmatter":{', '"unboundLabel":"approved","frontmatter":{'],
    ['"skillId":', '"unboundLabel":"approved","skillId":'],
  ])('rejects malformed or unbound stored manifest fields', async (from, to) => {
    const e = await environment();
    e.store.set(e.snapshot.revision, {
      ...e.snapshot,
      manifestJson: e.snapshot.manifestJson.replace(from, to),
    });
    await expect(e.read()).rejects.toThrow(failure);
  });

  it('preflights oversized stored arrays before mapping them', async () => {
    const e = await environment();
    const files = Array.from({ length: 65 }, () => e.snapshot.files[0]);
    const map = jest.spyOn(files, 'map');
    e.store.set(e.snapshot.revision, { ...e.snapshot, files });
    await expect(e.read()).rejects.toThrow(failure);
    expect(map).not.toHaveBeenCalled();
  });

  it('copies tiny/reused stream chunks with bounded buffering and rejects empty-chunk floods', async () => {
    const f = fixture();
    const snapshot = await captureSkillBundle({
      manifest: f.manifest,
      readFile: async ({ path }) =>
        (async function* () {
          const chunk = Buffer.alloc(1);
          for (const value of f.source.get(path) ?? []) {
            chunk[0] = value;
            yield chunk;
            yield Buffer.alloc(0);
          }
        })(),
    });
    expect(validateSkillBundle(snapshot).files).toHaveLength(2);
    let chunks = 0;
    await expect(
      captureSkillBundle({
        manifest: f.manifest,
        readFile: async () =>
          (async function* () {
            for (let i = 0; i < 2000; i++) {
              chunks++;
              yield Buffer.alloc(0);
            }
          })(),
      }),
    ).rejects.toThrow(failure);
    expect(chunks).toBeLessThan(1100);
  });
  it('captures exact definition and binary/text bytes; source and returned-buffer mutation cannot change reads', async () => {
    const e = await environment();
    e.source.get('references/a.txt')?.fill(0);
    e.manifest.definition.body = 'new draft';
    expect((await e.host.prime({ selection: e.token, actor })).definition.body).toBe(
      'Read references/a.txt',
    );
    const first = await e.read();
    first.bytes.fill(0);
    expect((await e.read()).bytes.toString()).toBe('reviewed reference');
    expect((await e.read('assets/image.png')).bytes).toEqual(
      Buffer.from([137, 80, 78, 71, 0, 255]),
    );
    expect((await e.read('SKILL.md')).bytes.toString()).toBe('Read references/a.txt');
    expect(Object.isFrozen(e.snapshot.files[0])).toBe(true);
    expect(e.calls.access).toBe(10);
  });

  it('is independent of manifest order and nested frontmatter key order', async () => {
    const f = fixture();
    const first = await captureSkillBundle(f);
    f.manifest.files.reverse();
    f.manifest.definition.frontmatter = { metadata: { a: 1, b: 2 } };
    expect((await captureSkillBundle(f)).revision).toBe(first.revision);
  });

  it.each(['replace', 'delete', 'mixed-sync'])(
    'rejects %s during capture rather than certifying a mixed bundle',
    async (change) => {
      const f = fixture();
      let reads = 0;
      await expect(
        captureSkillBundle({
          manifest: f.manifest,
          readFile: async (file) => {
            reads++;
            if (change === 'replace' || (change === 'mixed-sync' && reads === 2))
              f.source.set(file.path, Buffer.from('different bytes'));
            if (change === 'delete') f.source.delete(file.path);
            return f.readFile(file);
          },
        }),
      ).rejects.toThrow(failure);
    },
  );

  it('copies manifest before awaiting concurrent draft edits', async () => {
    const f = fixture();
    const snapshot = await captureSkillBundle({
      manifest: f.manifest,
      readFile: async (file) => {
        f.manifest.definition.body = 'concurrent edit';
        f.manifest.files.length = 0;
        return f.readFile(file);
      },
    });
    expect(validateSkillBundle(snapshot).definition.body).toBe('Read references/a.txt');
    expect(snapshot.files).toHaveLength(2);
  });

  it('publication/sync creates another identity and old pins never switch to newer content', async () => {
    const e = await environment();
    e.manifest.definition.body = 'published revision';
    e.manifest.sourceRevision = 'committed-publication-2';
    e.manifest.files = e.manifest.files.filter((file) => file.path !== 'references/a.txt');
    e.source.delete('references/a.txt');
    const next = await captureSkillBundle(e);
    e.store.set(next.revision, next);
    expect(next.revision).not.toBe(e.snapshot.revision);
    expect((await e.read()).bytes.toString()).toBe('reviewed reference');
    await expect(
      e.host.read({ selection: encodeSkillBundleSelection(next), actor, path: 'references/a.txt' }),
    ).rejects.toThrow(failure);
    e.store.delete(e.snapshot.revision);
    await expect(e.read()).rejects.toThrow(failure);
  });

  it.each(['canView', 'active', 'userInvocable', 'inAgentScope'] as const)(
    'checks current %s even after a successful cached read',
    async (key) => {
      const e = await environment();
      await e.read();
      e.setAccess({ [key]: false });
      await expect(e.read()).rejects.toThrow(failure);
      expect(e.calls.load).toBe(1);
    },
  );

  it('denies current skill deletion and revocation during snapshot loading or inspection', async () => {
    for (const phase of ['before', 'load', 'inspect']) {
      const e = await environment();
      if (phase === 'before') e.revoke();
      if (phase === 'load') e.onLoad(e.revoke);
      if (phase === 'inspect') e.onInspect(e.revoke);
      await expect(e.read()).rejects.toThrow(failure);
    }
  });

  it.each(['load', 'inspect'])('denies manual eligibility revocation during %s', async (phase) => {
    const e = await environment();
    const revoke = () => e.setAccess({ userInvocable: false });
    if (phase === 'load') e.onLoad(revoke);
    else e.onInspect(revoke);
    await expect(e.host.prime({ selection: e.token, actor })).rejects.toThrow(failure);
    await expect(e.read()).rejects.toThrow(failure);
  });

  it.each(['{}', '{"userInvocable":"false"}', '{"userInvocable":null}'])(
    'fails closed for missing or malformed current eligibility: %s',
    async (json) => {
      const e = await environment();
      const patch = JSON.parse(json) as Partial<SkillBundleAccess>;
      e.setAccess({ userInvocable: undefined, ...patch });
      await expect(e.read()).rejects.toThrow(failure);
    },
  );

  it.each([
    { ...actor, tenantId: 'other' },
    { ...actor, userId: 'other' },
    { ...actor, agentId: 'other' },
  ])('does not treat a pin as authority for another actor: %j', async (otherActor) => {
    const e = await environment();
    await expect(
      e.host.read({ selection: e.token, actor: otherActor, path: 'SKILL.md' }),
    ).rejects.toThrow(failure);
    expect(e.calls.load).toBe(0);
  });

  it('rejects ACL responses for another resource or tenant', async () => {
    for (const patch of [{ skillId: '223456789012345678901234' }, { tenantId: 'other' }]) {
      const e = await environment();
      e.setAccess(patch);
      await expect(e.read()).rejects.toThrow(failure);
    }
  });

  it.each(['bytes', 'manifest', 'wrong-snapshot', 'missing-file'])(
    'validates whole bundle on every read: %s',
    async (change) => {
      const e = await environment();
      const altered = { ...e.snapshot, files: e.snapshot.files.map((f) => ({ ...f })) };
      if (change === 'bytes')
        altered.files[0].base64 = Buffer.from('tampered unrequested image').toString('base64');
      if (change === 'manifest')
        altered.manifestJson = altered.manifestJson.replace(
          'Read references/a.txt',
          'changed definition',
        );
      if (change === 'missing-file') altered.files.pop();
      if (change === 'wrong-snapshot') {
        e.manifest.sourceRevision = 'new-publication';
        Object.assign(altered, await captureSkillBundle(e));
      }
      e.store.set(e.snapshot.revision, altered);
      await expect(e.read('SKILL.md')).rejects.toThrow(failure);
    },
  );

  it('applies current inspection policy, without leaking content on rejection', async () => {
    const e = await environment();
    e.onInspect(() => {
      throw new Error('private policy detail');
    });
    await expect(e.read()).rejects.toThrow(failure);
    await expect(e.read()).rejects.not.toThrow('private policy detail');
  });

  it.each(['../private', '/mnt/data/skills/writer/file', 'a/../b', 'a\\b', 'a//b'])(
    'rejects unsafe path %s',
    async (path) => {
      const e = await environment();
      await expect(e.read(path)).rejects.toThrow(failure);
      expect(e.calls.load).toBe(0);
      e.manifest.files[0].path = path;
      await expect(captureSkillBundle(e)).rejects.toThrow(failure);
    },
  );

  it.each(['sandbox-mount', 'execute'] as const)(
    'rejects unsupported pinned %s before loading bytes',
    async (execution) => {
      const e = await environment();
      await expect(e.host.prime({ selection: e.token, actor, execution })).rejects.toThrow(failure);
      expect(e.calls.load).toBe(0);
    },
  );

  it('keeps PR191 definition tokens distinct, and never upgrades name-only or malformed tokens', async () => {
    const e = await environment();
    const revision = getSkillSelectionRevision(e.manifest.definition);
    const definitionToken = encodeSkillSelection({
      _id: id,
      name: 'writer',
      selectionRevision: revision,
    });
    expect(parseSkillSelection('writer')).toEqual({ name: 'writer' });
    expect(parseSkillSelection(definitionToken).revision).toBe(revision);
    expect(parseSkillSelection(e.token)).toMatchObject({
      explicit: true,
      skillId: id,
      revision: undefined,
    });
    for (const selection of [
      'writer',
      definitionToken,
      `${e.token}@@extra`,
      e.token.replace(id, 'bad'),
    ]) {
      await expect(e.host.prime({ selection, actor })).rejects.toThrow(failure);
    }
  });

  it('enforces capture limits, exact lengths, duplicate paths, and model-only exclusion', async () => {
    for (const change of ['size', 'count', 'duplicate', 'short', 'model-only']) {
      const e = await environment();
      if (change === 'size') e.manifest.files[0].bytes = 6 * 1024 * 1024;
      if (change === 'count')
        e.manifest.files = Array.from({ length: 65 }, () => e.manifest.files[0]);
      if (change === 'duplicate') e.manifest.files.push({ ...e.manifest.files[0] });
      if (change === 'short') e.manifest.files[0].bytes += 1;
      if (change === 'model-only') {
        e.manifest.definition.userInvocable = false;
        const snapshot = await captureSkillBundle(e);
        e.store.set(snapshot.revision, snapshot);
        await expect(
          e.host.prime({ selection: encodeSkillBundleSelection(snapshot), actor }),
        ).rejects.toThrow(failure);
      } else await expect(captureSkillBundle(e)).rejects.toThrow(failure);
    }
  });
});
