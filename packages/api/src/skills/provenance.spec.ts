import { assertManagedDraftUpstream, validateManagedDraftProvenance } from './provenance';

const digest = (n: number) => n.toString(16).padStart(40, '0');
const id = '123456789012345678901234';
const failure = /Keep your edits/;

function fixture() {
  const identity = {
    provider: 'github',
    sourceId: 'source',
    owner: 'owner',
    repo: 'repo',
    ref: 'main',
    skillPath: 'skills/writer',
  };
  const draft: Record<string, unknown> = {
    ...identity,
    lifecycle: 'draft',
    draftOfSkillId: id,
    baseVersion: 1,
    baseCommitSha: digest(1),
    baseSkillBlobSha: digest(7),
  };
  const published = {
    _id: id,
    source: 'github',
    version: 1,
    sourceMetadata: { ...identity, commitSha: digest(1), skillBlobSha: digest(7) },
  };
  const responses = new Map<string, unknown>([
    [`/git/commits/${digest(1)}`, { sha: digest(1), tree: { sha: digest(2) } }],
    [
      `/git/trees/${digest(2)}`,
      {
        sha: digest(2),
        truncated: false,
        tree: [{ path: 'skills', type: 'tree', mode: '040000', sha: digest(3) }],
      },
    ],
    [
      `/git/trees/${digest(3)}`,
      {
        sha: digest(3),
        truncated: false,
        tree: [{ path: 'writer', type: 'tree', mode: '040000', sha: digest(4) }],
      },
    ],
    [
      `/git/trees/${digest(4)}`,
      {
        sha: digest(4),
        truncated: false,
        tree: [
          { path: 'SKILL.md', type: 'blob', mode: '100644', sha: digest(7) },
          { path: 'reference.txt', type: 'blob', mode: '100644', sha: digest(8) },
        ],
      },
    ],
  ]);
  const getJson = jest.fn(async (path: string): Promise<unknown> => {
    if (!responses.has(path)) throw new Error('missing');
    return responses.get(path);
  });
  const target = { commitSha: digest(1), treeSha: digest(2) };
  const check = () =>
    assertManagedDraftUpstream(validateManagedDraftProvenance(draft, published), target, getJson);
  return { draft, published, responses, getJson, target, check };
}

describe('managed draft source provenance', () => {
  it.each(['SKILL.md', 'skill.md', 'Skill.md', 'SKILL.MD'])(
    'returns the exact direct definition filename %s',
    async (name) => {
      const f = fixture();
      f.responses.set(`/git/trees/${digest(4)}`, {
        sha: digest(4),
        truncated: false,
        tree: [{ path: name, type: 'blob', mode: '100644', sha: digest(7) }],
      });
      const result = await f.check();
      expect(result).toEqual({ path: name, mode: '100644' });
      expect(Object.isFrozen(result)).toBe(true);
    },
  );

  it('preserves an executable definition mode', async () => {
    const f = fixture();
    f.responses.set(`/git/trees/${digest(4)}`, {
      sha: digest(4),
      truncated: false,
      tree: [{ path: 'Skill.md', type: 'blob', mode: '100755', sha: digest(7) }],
    });
    await expect(f.check()).resolves.toEqual({ path: 'Skill.md', mode: '100755' });
  });

  it.each(['blob', 'tree'])(
    'rejects ambiguous case variants even when one is a %s',
    async (type) => {
      const f = fixture();
      f.responses.set(`/git/trees/${digest(4)}`, {
        sha: digest(4),
        truncated: false,
        tree: [
          { path: 'SKILL.md', type: 'blob', mode: '100644', sha: digest(7) },
          { path: 'skill.md', type, mode: type === 'tree' ? '040000' : '100644', sha: digest(99) },
        ],
      });
      await expect(f.check()).rejects.toThrow(failure);
    },
  );

  it.each([false, true])(
    'does not inspect a child skill tree (direct definition present: %s)',
    async (hasDirectDefinition) => {
      const f = fixture();
      const childTree = `/git/trees/${digest(15)}`;
      f.responses.set(`/git/trees/${digest(4)}`, {
        sha: digest(4),
        truncated: false,
        tree: [
          { path: 'nested', type: 'tree', mode: '040000', sha: digest(15) },
          ...(hasDirectDefinition
            ? [{ path: 'Skill.md', type: 'blob', mode: '100644', sha: digest(7) }]
            : []),
        ],
      });
      f.responses.set(childTree, {
        sha: digest(15),
        truncated: false,
        tree: [{ path: 'SKILL.md', type: 'blob', mode: '100644', sha: digest(7) }],
      });
      if (hasDirectDefinition) {
        await expect(f.check()).resolves.toEqual({ path: 'Skill.md', mode: '100644' });
      } else {
        await expect(f.check()).rejects.toThrow(failure);
      }
      expect(f.getJson).not.toHaveBeenCalledWith(childTree);
      expect(f.getJson.mock.calls.every(([path]) => !path.includes('?recursive'))).toBe(true);
    },
  );

  it.each(['nested', 'coercible path', 'symlink', 'wrong blob'])(
    'rejects %s without falling back to another definition',
    async (kind) => {
      const f = fixture();
      const definitionPath = kind === 'nested' ? 'nested/skill.md' : 'skill.md';
      f.responses.set(`/git/trees/${digest(4)}`, {
        sha: digest(4),
        truncated: false,
        tree: [
          {
            path: kind === 'coercible path' ? ['skill.md'] : definitionPath,
            type: 'blob',
            mode: kind === 'symlink' ? '120000' : '100644',
            sha: kind === 'wrong blob' ? digest(99) : digest(7),
          },
        ],
      });
      await expect(f.check()).rejects.toThrow(failure);
      expect(f.getJson.mock.calls.every(([path]) => !path.includes('?recursive'))).toBe(true);
    },
  );

  it('rejects lifecycle and Git mode values that would pass string coercion', async () => {
    const f = fixture();
    f.draft.lifecycle = ['draft'];
    expect(() => f.check()).toThrow(failure);
    f.draft.lifecycle = 'draft';
    f.responses.set(`/git/trees/${digest(4)}`, {
      sha: digest(4),
      truncated: false,
      tree: [{ path: 'SKILL.md', type: 'blob', mode: ['100644'], sha: digest(7) }],
    });
    await expect(f.check()).rejects.toThrow(failure);
  });
  it.each(['draft', 'trial', 'publish_pending'])(
    'accepts intact %s provenance',
    async (lifecycle) => {
      const f = fixture();
      f.draft.lifecycle = lifecycle;
      await expect(f.check()).resolves.toEqual({ path: 'SKILL.md', mode: '100644' });
    },
  );

  it.each([
    'baseVersion',
    'baseCommitSha',
    'baseSkillBlobSha',
    'sourceId',
    'owner',
    'repo',
    'ref',
    'skillPath',
  ])('rejects missing %s without reading upstream', async (key) => {
    const f = fixture();
    delete f.draft[key];
    expect(() => f.check()).toThrow(failure);
    expect(f.getJson).not.toHaveBeenCalled();
  });

  it.each(['sourceId', 'owner', 'repo', 'ref', 'skillPath'])(
    'rejects changed source identity %s',
    (key) => {
      const f = fixture();
      f.draft[key] = 'different';
      expect(() => f.check()).toThrow(failure);
    },
  );

  it.each(['../writer', 'skills//writer', '/skills/writer', 'skills/./writer', 'skills\\writer'])(
    'rejects noncanonical path %s',
    (skillPath) => {
      const f = fixture();
      f.draft.skillPath = skillPath;
      f.published.sourceMetadata.skillPath = skillPath;
      expect(() => f.check()).toThrow(failure);
    },
  );

  it('rejects invalid version and coercible revision values', () => {
    const f = fixture();
    f.draft.baseVersion = '1';
    expect(() => f.check()).toThrow(failure);
    f.draft.baseVersion = 1;
    f.draft.baseCommitSha = [digest(1)];
    expect(() => f.check()).toThrow(failure);
  });

  it('rejects a changed synced SKILL.md before upstream reads', () => {
    const f = fixture();
    f.published.sourceMetadata.skillBlobSha = digest(9);
    expect(() => f.check()).toThrow(failure);
    expect(f.getJson).not.toHaveBeenCalled();
  });

  it('allows unrelated upstream changes and sync version advancement with the same subtree', async () => {
    const f = fixture();
    f.target.commitSha = digest(10);
    f.target.treeSha = digest(11);
    f.published.version = 3;
    f.published.sourceMetadata.commitSha = digest(10);
    f.responses.set(`/git/trees/${digest(11)}`, {
      sha: digest(11),
      truncated: false,
      tree: [
        { path: 'skills', type: 'tree', mode: '040000', sha: digest(3) },
        { path: 'unrelated.txt', type: 'blob', mode: '100644', sha: digest(99) },
      ],
    });
    await expect(f.check()).resolves.toEqual({ path: 'SKILL.md', mode: '100644' });
  });

  it.each(['definition', 'file modification', 'file addition', 'file deletion', 'mode change'])(
    'rejects a changed subtree (%s) even when synced SKILL.md is unchanged',
    async () => {
      const f = fixture();
      f.target.commitSha = digest(10);
      f.target.treeSha = digest(11);
      f.responses.set(`/git/trees/${digest(11)}`, {
        sha: digest(11),
        truncated: false,
        tree: [{ path: 'skills', type: 'tree', mode: '040000', sha: digest(12) }],
      });
      f.responses.set(`/git/trees/${digest(12)}`, {
        sha: digest(12),
        truncated: false,
        tree: [{ path: 'writer', type: 'tree', mode: '040000', sha: digest(13) }],
      });
      await expect(f.check()).rejects.toThrow(failure);
    },
  );

  it.each(['truncated', 'missing', 'symlink', 'wrong response identity', 'duplicate'])(
    'fails closed for a %s tree response',
    async (kind) => {
      const f = fixture();
      const entry = { path: 'writer', type: 'tree', mode: '040000', sha: digest(4) };
      let tree = [{ ...entry, mode: kind === 'symlink' ? '120000' : '040000' }];
      if (kind === 'missing') tree = [];
      if (kind === 'duplicate') tree = [entry, entry];
      f.responses.set(`/git/trees/${digest(3)}`, {
        sha: kind === 'wrong response identity' ? digest(99) : digest(3),
        truncated: kind === 'truncated',
        tree,
      });
      await expect(f.check()).rejects.toThrow(failure);
    },
  );

  it('rejects a historical definition blob that does not match recorded provenance', async () => {
    const f = fixture();
    f.responses.set(`/git/trees/${digest(4)}`, {
      sha: digest(4),
      truncated: false,
      tree: [{ path: 'SKILL.md', type: 'blob', mode: '100644', sha: digest(99) }],
    });
    await expect(f.check()).rejects.toThrow(failure);
  });

  it('uses pinned commit/tree IDs if a branch moves during validation', async () => {
    const f = fixture();
    await expect(f.check()).resolves.toEqual({ path: 'SKILL.md', mode: '100644' });
    expect(
      f.getJson.mock.calls.every(([path]) => /^\/git\/(trees|commits)\/[a-f0-9]{40}$/.test(path)),
    ).toBe(true);
    // No ref reread or atomicity claim: later upstream movement remains a publication race.
  });
});
