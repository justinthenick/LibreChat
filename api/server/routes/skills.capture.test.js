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
jest.mock('~/models', () =>
  Object.fromEntries(
    [
      'getSkillById',
      'getAuthorSkillByName',
      'createSkill',
      'listSkillFiles',
      'upsertSkillFile',
      'deleteSkill',
      'getRoleByName',
    ].map((key) => [key, jest.fn()]),
  ),
);
jest.mock('~/server/middleware', () => ({
  requireJwtAuth: jest.fn(),
  canAccessSkillResource: jest.fn(),
}));
jest.mock('~/server/services/PermissionService', () => ({ grantPermission: jest.fn() }));
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
const { grantPermission } = require('~/server/services/PermissionService');
require('./skills');
const createDraft = mockRouter.post.mock.calls.find(([route]) => route === '/:id/draft').at(-1);
const sourceId = '123456789012345678901234';
const draftId = '123456789012345678905678';
const userId = '123456789012345678909999';
const req = { params: { id: sourceId }, user: { id: userId, name: 'Test author' } };
let published;
let files;
let drafts;
let copied;
let res;

function sourceFile(path = 'references/guide.md') {
  return {
    relativePath: path,
    filename: 'guide.md',
    file_id: 'file-A',
    filepath: '/synthetic/A',
    source: 'local',
    mimeType: 'text/markdown',
    bytes: 5,
    isExecutable: false,
    sourceMetadata: { blobSha: 'a'.repeat(40), commitSha: '1'.repeat(40) },
  };
}

function editedDraft(name = 'writer-draft-901234') {
  return {
    _id: '123456789012345678905555',
    name,
    body: 'User edits that must survive',
    version: 9,
    source: 'inline',
    sourceMetadata: { lifecycle: 'trial', draftOfSkillId: sourceId },
  };
}

beforeEach(() => {
  jest.resetAllMocks();
  published = {
    _id: sourceId,
    name: 'writer',
    body: 'Definition A',
    description: 'A writing skill.',
    source: 'github',
    version: 3,
    sourceMetadata: {
      provider: 'github',
      sourceId: 'test-source',
      owner: 'test-owner',
      repo: 'test-repo',
      ref: 'main',
      skillPath: 'skills/writer',
      commitSha: '1'.repeat(40),
      skillBlobSha: 'a'.repeat(40),
    },
  };
  files = [sourceFile()];
  drafts = [];
  copied = [];
  models.getSkillById.mockImplementation(async (id) =>
    structuredClone(id === sourceId ? published : drafts.find((draft) => draft._id === id)),
  );
  models.getAuthorSkillByName.mockImplementation(async ({ name }) =>
    structuredClone(drafts.find((draft) => draft.name === name)),
  );
  models.createSkill.mockImplementation(async (data) => {
    const skill = { ...structuredClone(data), _id: draftId, version: 1 };
    drafts.push(skill);
    return { skill: structuredClone(skill), warnings: [] };
  });
  models.listSkillFiles.mockImplementation(async () => structuredClone(files));
  models.upsertSkillFile.mockImplementation(async (file) => {
    copied.push(structuredClone(file));
  });
  models.deleteSkill.mockImplementation(async (id) => {
    drafts = drafts.filter((draft) => draft._id !== id);
    return { deleted: true };
  });
  res = { status: jest.fn().mockReturnThis(), json: jest.fn().mockReturnThis() };
});

describe('managed draft capture: characterization of current race gaps, not safety acceptance', () => {
  it.each(['replace', 'add', 'delete'])(
    'can copy changed files after capturing old metadata: %s',
    async (change) => {
      grantPermission.mockImplementationOnce(async () => {
        published.body = 'Definition B';
        published.version++;
        published.sourceMetadata.commitSha = '2'.repeat(40);
        if (change === 'delete') {
          files = [];
          return;
        }
        const changed = {
          ...sourceFile(),
          file_id: 'file-B',
          filepath: '/synthetic/B',
          sourceMetadata: { blobSha: 'b'.repeat(40), commitSha: '2'.repeat(40) },
        };
        files =
          change === 'add'
            ? [sourceFile(), { ...changed, relativePath: 'references/new.md' }]
            : [changed];
      });
      await createDraft(req, res);
      expect(res.status).toHaveBeenCalledWith(201);
      expect(drafts[0]).toMatchObject({
        body: 'Definition A',
        sourceMetadata: { baseVersion: 3, baseCommitSha: '1'.repeat(40) },
      });
      expect(copied.map((file) => file.relativePath)).toEqual(
        files.map((file) => file.relativePath),
      );
      expect(copied.map((file) => file.filepath)).toEqual(files.map((file) => file.filepath));
      if (change !== 'delete') {
        expect(
          copied.find((file) => file.filepath === '/synthetic/B').sourceMetadata,
        ).toMatchObject({
          blobSha: 'b'.repeat(40),
          commitSha: '2'.repeat(40),
        });
      }
      expect(models.getSkillById.mock.calls.filter(([id]) => id === sourceId)).toHaveLength(1);
    },
  );

  it('returns a concurrently discovered draft while its files are still being copied', async () => {
    let second;
    models.upsertSkillFile.mockImplementationOnce(async (file) => {
      second = { status: jest.fn().mockReturnThis(), json: jest.fn().mockReturnThis() };
      await createDraft(req, second);
      expect(copied).toHaveLength(0);
      copied.push(structuredClone(file));
    });
    await createDraft(req, res);
    expect(second.status).toHaveBeenCalledWith(200);
    expect(second.json.mock.calls[0][0]._id).toBe(draftId);
    expect(models.createSkill).toHaveBeenCalledTimes(1);
  });

  it('currently deletes a newly visible draft on clone failure even after a concurrent edit', async () => {
    models.upsertSkillFile.mockImplementationOnce(async () => {
      drafts[0].body = 'Concurrent user edits';
      drafts[0].version++;
      throw new Error('synthetic clone failure');
    });
    await createDraft(req, res);
    expect(res.status).toHaveBeenCalledWith(500);
    expect(models.deleteSkill).toHaveBeenCalledWith(draftId);
    expect(drafts).toEqual([]);
  });
});

describe('managed draft recovery: existing edits remain untouched', () => {
  it('returns an existing edited Trial draft without refreshing its base or files', async () => {
    const existing = editedDraft();
    drafts.push(structuredClone(existing));
    await createDraft(req, res);
    expect(res.status).toHaveBeenCalledWith(200);
    expect(res.json).toHaveBeenCalledWith(existing);
    expect(drafts).toEqual([existing]);
    expect(models.createSkill).not.toHaveBeenCalled();
    expect(models.listSkillFiles).not.toHaveBeenCalled();
    expect(models.upsertSkillFile).not.toHaveBeenCalled();
    expect(models.deleteSkill).not.toHaveBeenCalled();
    expect(grantPermission).not.toHaveBeenCalled();
  });

  it.each([false, true])(
    'preserves a previously renamed edited draft when fresh capture fails=%s',
    async (fails) => {
      const retained = editedDraft('writer-my-retained-edits');
      drafts.push(structuredClone(retained));
      if (fails) {
        models.upsertSkillFile.mockRejectedValueOnce(new Error('synthetic clone failure'));
      }
      await createDraft(req, res);
      expect(res.status).toHaveBeenCalledWith(fails ? 500 : 201);
      expect(drafts.find((draft) => draft._id === retained._id)).toEqual(retained);
      expect(models.deleteSkill).not.toHaveBeenCalledWith(retained._id);
      expect(copied.every((file) => file.skillId === draftId)).toBe(true);
    },
  );
});
