import { createHash } from 'node:crypto';
import type { SkillBundleManifest, SkillBundleSnapshot } from './bundles';
import {
  beginSkillDraft,
  commitSkillSource,
  completeSkillDraft,
  copySkillDraft,
  failSkillDraft,
  recoverSkillDraft,
} from './capture';
import { captureSkillBundle, validateSkillBundle } from './bundles';

const skillId = '123456789012345678901234';
const request = {
  draftId: '123456789012345678905678',
  name: 'writer-draft',
  ownerId: 'owner',
  tenantId: 'tenant',
};
const failure = /invalid_skill_selection/;

async function bundle(body = 'original', content = 'file bytes') {
  const bytes = Buffer.from(content);
  const manifest: SkillBundleManifest = {
    skillId,
    tenantId: 'tenant',
    logicalName: 'writer',
    sourceRevision: 'upstream-commit',
    definition: { name: 'writer', description: 'Writes', body, version: 1 },
    files: [
      {
        path: 'a.txt',
        mimeType: 'text/plain',
        bytes: bytes.length,
        sha256: createHash('sha256').update(bytes).digest('hex'),
      },
    ],
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
      if (!stored) throw new Error('missing');
      yield Buffer.from(stored.base64, 'base64');
    })();
}

async function fixture() {
  const source = commitSkillSource(null, 0, await bundle());
  const draft = beginSkillDraft(source, null, request);
  return { source, draft, read: reader(source.snapshot) };
}

describe('dormant committed source and draft capture state machine', () => {
  it('commits a complete immutable source, then exposes a draft only after validated copy', async () => {
    const f = await fixture();
    expect(f.draft.status).toBe('initializing');
    expect(f.draft.snapshot).toBeNull();
    const copied = await copySkillDraft(f.draft, 1, f.read);
    const ready = completeSkillDraft(f.draft, 1, copied);
    expect(ready.status).toBe('ready');
    expect(validateSkillBundle(copied)).toMatchObject({
      skillId: request.draftId,
      logicalName: request.name,
      definition: { name: request.name, body: 'original' },
    });
    expect(ready.source.snapshot.revision).toBe(f.source.snapshot.revision);
    expect(Object.isFrozen(ready.source.snapshot.files[0])).toBe(true);
  });

  it.each(['missing', 'truncated', 'replaced'])(
    'rejects %s sync payload without advancing the committed generation',
    async (kind) => {
      const f = await fixture();
      const changed = await bundle('new definition', 'new bytes');
      const candidate = {
        ...changed,
        files:
          kind === 'missing'
            ? []
            : [{ path: 'a.txt', base64: Buffer.from(kind).toString('base64') }],
      };
      expect(() => commitSkillSource(f.source, 1, candidate)).toThrow(failure);
      expect(f.source.generation).toBe(1);
      expect(validateSkillBundle(f.source.snapshot).definition.body).toBe('original');
    },
  );

  it('rejects stale expectations against refreshed state after sync and edit-and-revert', async () => {
    const f = await fixture();
    const changed = commitSkillSource(f.source, 1, await bundle('new'));
    expect(() => commitSkillSource(changed, 1, f.source.snapshot)).toThrow(failure);
    const reverted = commitSkillSource(changed, 2, f.source.snapshot);
    expect(reverted.generation).toBe(3);
    expect(() => commitSkillSource(reverted, 1, f.source.snapshot)).toThrow(failure);
  });

  it('pins the old complete generation while a newer sync commits during copying', async () => {
    const f = await fixture();
    let current = f.source;
    const copied = await copySkillDraft(f.draft, 1, async (file) => {
      current = commitSkillSource(current, 1, await bundle('new', 'replacement'));
      return f.read(file);
    });
    const ready = completeSkillDraft(f.draft, 1, copied);
    expect(current.generation).toBe(2);
    expect(ready.source.generation).toBe(1);
    expect(validateSkillBundle(copied).definition.body).toBe('original');
    expect(copied.files).toEqual(f.source.snapshot.files);
  });

  it.each(['missing', 'replacement', 'partial', 'failure'])(
    'leaves no usable draft after a %s file copy and recovers explicitly',
    async (kind) => {
      const f = await fixture();
      await expect(
        copySkillDraft(f.draft, 1, async () =>
          (async function* () {
            if (kind === 'failure') throw new Error('copy failed');
            if (kind !== 'missing') yield Buffer.from(kind);
          })(),
        ),
      ).rejects.toThrow(failure);
      expect(f.draft.snapshot).toBeNull();
      const failed = failSkillDraft(f.draft, 1);
      expect(failed.status).toBe('failed');
      const recovered = recoverSkillDraft(failed, 1);
      expect(recovered.attempt).toBe(2);
      expect(recovered.source).toEqual(f.source);
      const copied = await copySkillDraft(recovered, 2, f.read);
      expect(completeSkillDraft(recovered, 2, copied).status).toBe('ready');
    },
  );

  it('never reuses an initializing or failed draft as ready', async () => {
    const f = await fixture();
    expect(() => beginSkillDraft(f.source, f.draft, request)).toThrow(failure);
    expect(() => beginSkillDraft(f.source, failSkillDraft(f.draft, 1), request)).toThrow(failure);
  });

  it('recovery fences both stale completion and stale failure while an old copy is running', async () => {
    const f = await fixture();
    let current = f.draft;
    const stale = await copySkillDraft(current, 1, async (file) => {
      current = recoverSkillDraft(current, 1);
      return f.read(file);
    });
    expect(() => completeSkillDraft(current, 1, stale)).toThrow(failure);
    expect(() => failSkillDraft(current, 1)).toThrow(failure);
    expect(() => recoverSkillDraft(current, 1)).toThrow(failure);
    expect(current.attempt).toBe(2);
  });

  it('rejects repeat completion and cleanup against a refreshed ready record', async () => {
    const f = await fixture();
    const copied = await copySkillDraft(f.draft, 1, f.read);
    const ready = completeSkillDraft(f.draft, 1, copied);
    expect(() => completeSkillDraft(ready, 1, copied)).toThrow(failure);
    expect(() => failSkillDraft(ready, 1)).toThrow(failure);
    expect(() => recoverSkillDraft(ready, 1)).toThrow(failure);
  });

  it('preserves existing ready user edits and their original base after a newer sync', async () => {
    const f = await fixture();
    const copied = await copySkillDraft(f.draft, 1, f.read);
    const ready = completeSkillDraft(f.draft, 1, copied);
    const manifest = validateSkillBundle(copied);
    const edited = await captureSkillBundle({
      manifest: {
        ...manifest,
        sourceRevision: 'user-edit-2',
        definition: { ...manifest.definition, body: 'user edits' },
      },
      readFile: reader(copied),
    });
    const existing = { ...ready, snapshot: edited };
    const synced = commitSkillSource(f.source, 1, await bundle('new source'));
    const reused = beginSkillDraft(synced, existing, request);
    expect(reused.snapshot).toEqual(edited);
    expect(reused.source.generation).toBe(1);
    expect(() => failSkillDraft(reused, 1)).toThrow(failure);
  });

  it('rejects a valid but different complete bundle at completion', async () => {
    const f = await fixture();
    const copied = await copySkillDraft(f.draft, 1, f.read);
    const manifest = validateSkillBundle(copied);
    const changed = await captureSkillBundle({
      manifest: { ...manifest, definition: { ...manifest.definition, body: 'mixed definition' } },
      readFile: reader(copied),
    });
    expect(() => completeSkillDraft(f.draft, 1, changed)).toThrow(failure);
  });

  it.each(['ownerId', 'tenantId', 'draftId', 'name'] as const)(
    'rejects existing-draft identity mismatch: %s',
    async (field) => {
      const f = await fixture();
      const copied = await copySkillDraft(f.draft, 1, f.read);
      const ready = completeSkillDraft(f.draft, 1, copied);
      const changed = { ...request, [field]: field === 'draftId' ? 'a'.repeat(24) : 'other' };
      expect(() => beginSkillDraft(f.source, ready, changed)).toThrow(failure);
    },
  );

  it('detaches caller-owned snapshot objects before asynchronous copy', async () => {
    const snapshot = await bundle();
    const mutable = { ...snapshot, files: snapshot.files.map((file) => ({ ...file })) };
    const source = commitSkillSource(null, 0, mutable);
    mutable.files[0].base64 = '';
    expect(source.snapshot.files[0].base64).toBe(snapshot.files[0].base64);
  });

  it.each(['logicalName', 'definition'] as const)(
    'rejects a ready snapshot with mismatched %s identity',
    async (field) => {
      const f = await fixture();
      const copied = await copySkillDraft(f.draft, 1, f.read);
      const ready = completeSkillDraft(f.draft, 1, copied);
      const manifest = validateSkillBundle(copied);
      const changed = await captureSkillBundle({
        manifest: {
          ...manifest,
          ...(field === 'logicalName'
            ? { logicalName: 'other' }
            : { definition: { ...manifest.definition, name: 'other' } }),
        },
        readFile: reader(copied),
      });
      expect(() => beginSkillDraft(f.source, { ...ready, snapshot: changed }, request)).toThrow(
        failure,
      );
    },
  );

  it('requires adapter CAS to choose between two valid sync proposals from the same input', async () => {
    const f = await fixture();
    const proposals = [
      commitSkillSource(f.source, 1, await bundle('first')),
      commitSkillSource(f.source, 1, await bundle('second')),
    ];
    let stored = f.source;
    const outcomes = proposals.map((proposal) => {
      if (stored.generation !== 1) return false;
      stored = proposal;
      return true;
    });
    expect(outcomes).toEqual([true, false]);
    expect(validateSkillBundle(stored.snapshot).definition.body).toBe('first');
  });

  it('requires adapter CAS to reject completion prepared before recovery', async () => {
    const f = await fixture();
    const copied = await copySkillDraft(f.draft, 1, f.read);
    const staleProposal = completeSkillDraft(f.draft, 1, copied);
    let stored = recoverSkillDraft(f.draft, 1);
    const persist = () => {
      if (stored.status !== 'initializing' || stored.attempt !== 1) return false;
      stored = staleProposal;
      return true;
    };
    expect(persist()).toBe(false);
    expect(stored.status).toBe('initializing');
    expect(stored.attempt).toBe(2);
    expect(stored.snapshot).toBeNull();
  });

  it('fails closed before generation or attempt counters overflow', async () => {
    const f = await fixture();
    expect(() =>
      commitSkillSource(
        { ...f.source, generation: Number.MAX_SAFE_INTEGER },
        Number.MAX_SAFE_INTEGER,
        f.source.snapshot,
      ),
    ).toThrow(failure);
    expect(() =>
      recoverSkillDraft({ ...f.draft, attempt: Number.MAX_SAFE_INTEGER }, Number.MAX_SAFE_INTEGER),
    ).toThrow(failure);
  });
});
