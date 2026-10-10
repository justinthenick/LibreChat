const mockRouter = Object.fromEntries(
  ['use', 'get', 'post', 'patch', 'delete'].map((key) => [key, jest.fn()]),
);
jest.mock('express', () =>
  Object.assign(jest.requireActual('express'), { Router: () => mockRouter }),
);
jest.mock('multer', () =>
  Object.assign(() => ({ single: () => jest.fn() }), { memoryStorage: jest.fn() }),
);
jest.mock('@librechat/api', () => ({
  ...jest.requireActual('@librechat/api'),
  createSkillsHandlers: () =>
    Object.fromEntries(
      ['list', 'create', 'get', 'patch', 'delete', 'listFiles', 'downloadFile', 'deleteFile'].map(
        (key) => [key, jest.fn()],
      ),
    ),
  createImportHandler: jest.fn(),
  generateCheckAccess: jest.fn(),
}));
jest.mock('~/models', () => ({
  getSkillById: jest.fn(),
  getSkillSyncStatus: jest.fn(),
  getSkillSyncCredentialToken: jest.fn(),
  listSkillFiles: jest.fn(),
  updateSkill: jest.fn(),
  getRoleByName: jest.fn(),
}));
jest.mock('~/server/middleware', () => ({
  requireJwtAuth: jest.fn(),
  canAccessSkillResource: jest.fn(),
}));
jest.mock('~/server/services/PermissionService', () => ({}));
jest.mock('~/server/services/Files/strategies', () => ({ getStrategyFunctions: jest.fn() }));
jest.mock('~/server/middleware/limiters/uploadLimiters', () => ({
  createFileLimiters: () => ({}),
}));
jest.mock('~/server/services/Skills/sync', () => ({
  maybeRunGitHubSkillSyncForRequest: jest.fn(),
}));
jest.mock('~/server/middleware/config/app', () => jest.fn());
jest.mock('~/server/utils/getFileStrategy', () => ({ getFileStrategy: jest.fn() }));
jest.mock('~/server/services/Endpoints/agents/skillDeps', () => ({
  getSkillDbMethods: () => ({}),
  withDeploymentSkillIds: jest.fn(),
  getSkillStrategyFunctions: jest.fn(),
}));

const models = require('~/models');
require('./skills');
const publish = mockRouter.post.mock.calls.find(([route]) => route === '/:id/publish').at(-1);
const sha = (n) => n.toString(16).padStart(40, '0');
const originalFetch = global.fetch;
let draft;
let published;
let responses;
let res;

beforeEach(() => {
  jest.clearAllMocks();
  const identity = {
    provider: 'github',
    sourceId: 'source',
    owner: 'owner',
    repo: 'repo',
    ref: 'main',
    skillPath: 'skills/writer',
  };
  published = {
    _id: '123456789012345678901234',
    source: 'github',
    name: 'writer',
    version: 1,
    sourceMetadata: { ...identity, commitSha: sha(1), skillBlobSha: sha(7) },
  };
  draft = {
    _id: '123456789012345678905678',
    source: 'inline',
    body: 'edited draft',
    version: 2,
    sourceMetadata: {
      ...identity,
      lifecycle: 'trial',
      draftOfSkillId: published._id,
      logicalName: 'writer',
      baseVersion: 1,
      baseCommitSha: sha(1),
      baseSkillBlobSha: sha(7),
    },
  };
  models.getSkillById.mockImplementation(async (id) => (id === draft._id ? draft : published));
  models.getSkillSyncStatus.mockResolvedValue({ credentialKey: 'synthetic-key' });
  models.getSkillSyncCredentialToken.mockResolvedValue('synthetic-token');
  models.listSkillFiles.mockResolvedValue([]);
  models.updateSkill.mockResolvedValue({ status: 'updated', skill: draft });
  responses = new Map([
    ['/git/ref/heads/main', { object: { sha: sha(1) } }],
    [`/git/commits/${sha(1)}`, { sha: sha(1), tree: { sha: sha(2) } }],
    [
      `/git/trees/${sha(2)}`,
      {
        sha: sha(2),
        truncated: false,
        tree: [{ path: 'skills', type: 'tree', mode: '040000', sha: sha(3) }],
      },
    ],
    [
      `/git/trees/${sha(3)}`,
      {
        sha: sha(3),
        truncated: false,
        tree: [{ path: 'writer', type: 'tree', mode: '040000', sha: sha(4) }],
      },
    ],
    [
      `/git/trees/${sha(4)}`,
      {
        sha: sha(4),
        truncated: false,
        tree: [{ path: 'SKILL.md', type: 'blob', mode: '100644', sha: sha(7) }],
      },
    ],
  ]);
  global.fetch = jest.fn(async (url, options) => {
    const path = String(url).replace('https://api.github.com/repos/owner/repo', '');
    if (options.method === 'GET' && !responses.has(path)) throw new Error('Unexpected mock read');
    return {
      ok: true,
      status: 200,
      text: async () =>
        JSON.stringify(
          options.method === 'GET'
            ? responses.get(path)
            : { sha: sha(50), number: 42, html_url: 'https://example.test/pr/42' },
        ),
    };
  });
  res = { status: jest.fn().mockReturnThis(), json: jest.fn().mockReturnThis() };
});
afterEach(() => {
  global.fetch = originalFetch;
});
const run = () => publish({ params: { id: draft._id }, user: { id: 'owner' } }, res);
const writes = () => global.fetch.mock.calls.filter(([_url, options]) => options.method !== 'GET');

it.each(['baseVersion', 'baseCommitSha', 'baseSkillBlobSha', 'owner'])(
  'rejects legacy/missing %s before credential lookup and any remote call',
  async (key) => {
    delete draft.sourceMetadata[key];
    await run();
    expect(res.status).toHaveBeenCalledWith(409);
    expect(res.json).toHaveBeenCalledWith(
      expect.objectContaining({
        error: 'managed_draft_provenance_conflict',
        message: expect.stringContaining('Keep your edits'),
      }),
    );
    expect(models.getSkillSyncCredentialToken).not.toHaveBeenCalled();
    expect(global.fetch).not.toHaveBeenCalled();
    expect(models.updateSkill).not.toHaveBeenCalled();
    expect(draft.body).toBe('edited draft');
    expect(draft.sourceMetadata.lifecycle).toBe('trial');
  },
);

it('rejects an upstream bundled-file change before any remote writes or draft mutation', async () => {
  responses.set('/git/ref/heads/main', { object: { sha: sha(10) } });
  responses.set(`/git/commits/${sha(10)}`, { sha: sha(10), tree: { sha: sha(11) } });
  responses.set(`/git/trees/${sha(11)}`, {
    sha: sha(11),
    truncated: false,
    tree: [{ path: 'skills', type: 'tree', mode: '040000', sha: sha(12) }],
  });
  responses.set(`/git/trees/${sha(12)}`, {
    sha: sha(12),
    truncated: false,
    tree: [{ path: 'writer', type: 'tree', mode: '040000', sha: sha(13) }],
  });
  await run();
  expect(res.status).toHaveBeenCalledWith(409);
  expect(writes()).toEqual([]);
  expect(models.updateSkill).not.toHaveBeenCalled();
});

it('preserves the valid publication response and writes only after validating trees', async () => {
  await run();
  expect(res.status).toHaveBeenCalledWith(201);
  expect(res.json).toHaveBeenCalledWith(expect.objectContaining({ pullRequestNumber: 42 }));
  const calls = global.fetch.mock.calls;
  const lastValidation = calls.findIndex(([url]) => String(url).endsWith(`/git/trees/${sha(4)}`));
  const firstWrite = calls.findIndex(([_url, options]) => options.method === 'POST');
  expect(lastValidation).toBeGreaterThanOrEqual(0);
  expect(firstWrite).toBeGreaterThan(lastValidation);
  expect(models.updateSkill).toHaveBeenCalledTimes(1);
});

it('rejects a target commit response for a different commit before writes', async () => {
  responses.set(`/git/commits/${sha(1)}`, { sha: sha(99), tree: { sha: sha(2) } });
  await run();
  expect(res.status).toHaveBeenCalledWith(409);
  expect(writes()).toEqual([]);
  expect(models.updateSkill).not.toHaveBeenCalled();
});

it('keeps the selected commit pinned when the upstream ref moves during tree validation', async () => {
  const read = global.fetch.getMockImplementation();
  global.fetch.mockImplementation(async (url, options) => {
    if (String(url).endsWith(`/git/trees/${sha(3)}`)) {
      responses.set('/git/ref/heads/main', { object: { sha: sha(99) } });
    }
    return read(url, options);
  });
  await run();
  expect(res.status).toHaveBeenCalledWith(201);
  const commitWrite = writes().find(([url]) => String(url).endsWith('/git/commits'));
  expect(JSON.parse(commitWrite[1].body).parents).toEqual([sha(1)]);
  expect(
    global.fetch.mock.calls.filter(([url]) => String(url).endsWith('/git/ref/heads/main')),
  ).toHaveLength(1);
  // This intentionally does not claim that a later upstream change is rejected atomically.
});
