import { createHash } from 'node:crypto';
import type { SkillBundleManifest, SkillBundleSnapshot } from './bundles';
import type { SkillBundlePublicationDeps } from './publication';
import { publishSkillBundle } from './publication';

const skillId = '123456789012345678901234';
const actor = { userId: 'publisher', tenantId: 'tenant' };
const failure = /invalid_skill_selection/;

function deferred() {
  let resolve!: () => void;
  const promise = new Promise<void>((done) => {
    resolve = done;
  });
  return { promise, resolve };
}

function fixture() {
  const bytes = Buffer.from('committed content');
  const manifest: SkillBundleManifest = {
    skillId,
    tenantId: 'tenant',
    logicalName: 'writer',
    sourceRevision: 'generation-1',
    definition: { name: 'writer', description: 'Writes', body: 'Read a.txt', version: 1 },
    files: [
      {
        path: 'a.txt',
        mimeType: 'text/plain',
        bytes: bytes.length,
        sha256: createHash('sha256').update(bytes).digest('hex'),
      },
    ],
  };
  const state = {
    sourceRevision: manifest.sourceRevision,
    publishedRevision: null as string | null,
    exists: true,
    authorized: true,
    snapshots: new Map<string, SkillBundleSnapshot>(),
  };
  const readFile = jest.fn(async () =>
    (async function* () {
      yield bytes;
    })(),
  );
  const deps: SkillBundlePublicationDeps = {
    loadCandidate: jest.fn(async () => ({
      manifest,
      expectedPublishedRevision: state.publishedRevision,
      readFile,
    })),
    inspect: jest.fn(async () => {}),
    compareAndPublish: jest.fn(async (commit) => {
      // Synchronous fixture transaction: no await between comparison and durable state changes.
      if (
        !state.exists ||
        !state.authorized ||
        commit.actor.tenantId !== 'tenant' ||
        commit.expectedSourceRevision !== state.sourceRevision ||
        commit.expectedPublishedRevision !== state.publishedRevision
      )
        return false;
      state.snapshots.set(commit.snapshot.revision, commit.snapshot);
      state.publishedRevision = commit.snapshot.revision;
      return true;
    }),
  };
  return { manifest, bytes, state, deps, readFile };
}

describe('dormant skill bundle publication protocol', () => {
  it('publishes exactly the inspected snapshot in one compare-and-publish operation', async () => {
    const f = fixture();
    const snapshot = await publishSkillBundle(f.deps, skillId, actor);
    expect(f.state.snapshots.get(snapshot.revision)).toBe(snapshot);
    expect(f.state.publishedRevision).toBe(snapshot.revision);
    expect(f.deps.inspect).toHaveBeenCalledWith(snapshot, actor);
    expect(f.deps.compareAndPublish).toHaveBeenCalledTimes(1);
  });

  it.each(['definition', 'file', 'sync', 'edit-and-revert'])(
    'rejects a newer %s generation committed during inspection',
    async () => {
      const f = fixture();
      const entered = deferred();
      const resume = deferred();
      f.deps.inspect = async () => {
        entered.resolve();
        await resume.promise;
      };
      const publication = publishSkillBundle(f.deps, skillId, actor);
      await entered.promise;
      f.state.sourceRevision = 'generation-2';
      resume.resolve();
      await expect(publication).rejects.toThrow(failure);
      expect(f.state.publishedRevision).toBeNull();
      expect(f.state.snapshots.size).toBe(0);
      expect(f.deps.compareAndPublish).toHaveBeenCalledTimes(1);
    },
  );

  it('allows only one publisher to advance the same observed publication pointer', async () => {
    const f = fixture();
    const both = deferred();
    const resume = deferred();
    let arrivals = 0;
    f.deps.inspect = async () => {
      if (++arrivals === 2) both.resolve();
      await resume.promise;
    };
    const first = publishSkillBundle(f.deps, skillId, actor);
    const second = publishSkillBundle(f.deps, skillId, actor);
    await both.promise;
    resume.resolve();
    const results = await Promise.allSettled([first, second]);
    expect(results.map((result) => result.status).sort()).toEqual(['fulfilled', 'rejected']);
    expect(f.state.snapshots.size).toBe(1);
  });

  it.each(['exists', 'authorized'] as const)('rechecks %s at atomic commit', async (field) => {
    const f = fixture();
    f.deps.inspect = async () => {
      f.state[field] = false;
    };
    await expect(publishSkillBundle(f.deps, skillId, actor)).rejects.toThrow(failure);
    expect(f.state.snapshots.size).toBe(0);
    expect(f.state.publishedRevision).toBeNull();
  });

  it('rejects mixed-generation bytes before any commit attempt', async () => {
    const f = fixture();
    f.bytes.fill(0);
    await expect(publishSkillBundle(f.deps, skillId, actor)).rejects.toThrow(failure);
    expect(f.deps.compareAndPublish).not.toHaveBeenCalled();
  });

  it('does not publish when current inspection fails', async () => {
    const f = fixture();
    f.deps.inspect = async () => {
      throw new Error('policy');
    };
    await expect(publishSkillBundle(f.deps, skillId, actor)).rejects.toThrow(failure);
    expect(f.deps.compareAndPublish).not.toHaveBeenCalled();
  });

  it('does not retry an uncertain acknowledgement, even if the store committed', async () => {
    const f = fixture();
    const commit = f.deps.compareAndPublish;
    f.deps.compareAndPublish = jest.fn(async (request) => {
      await commit(request);
      throw new Error('connection closed after commit');
    });
    await expect(publishSkillBundle(f.deps, skillId, actor)).rejects.toThrow(failure);
    expect(f.state.snapshots.size).toBe(1);
    expect(f.deps.compareAndPublish).toHaveBeenCalledTimes(1);
  });

  it('captures actor identity before awaiting the candidate', async () => {
    const f = fixture();
    const input = { ...actor };
    const load = f.deps.loadCandidate;
    f.deps.loadCandidate = async (...args) => {
      input.tenantId = 'other';
      input.userId = 'other';
      return load(...args);
    };
    await publishSkillBundle(f.deps, skillId, input);
    expect(f.deps.compareAndPublish).toHaveBeenCalledWith(expect.objectContaining({ actor }));
  });

  it.each(['skillId', 'tenantId'] as const)('rejects a mismatched candidate %s', async (field) => {
    const f = fixture();
    f.manifest[field] = field === 'skillId' ? 'aaaaaaaaaaaaaaaaaaaaaaaa' : 'other';
    await expect(publishSkillBundle(f.deps, skillId, actor)).rejects.toThrow(failure);
    expect(f.readFile).not.toHaveBeenCalled();
    expect(f.deps.compareAndPublish).not.toHaveBeenCalled();
  });

  it.each([{ invalid: ['a'.repeat(64)] }, { invalid: { toString: () => 'a'.repeat(64) } }])(
    'rejects a non-string publication revision before reading bytes: %p',
    async ({ invalid }) => {
      const f = fixture();
      f.state.publishedRevision = invalid as unknown as string;
      await expect(publishSkillBundle(f.deps, skillId, actor)).rejects.toThrow(failure);
      expect(f.readFile).not.toHaveBeenCalled();
      expect(f.deps.compareAndPublish).not.toHaveBeenCalled();
    },
  );
});
