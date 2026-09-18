const path = require('path');
const crypto = require('crypto');
const multer = require('multer');
const express = require('express');
const {
  createSkillsHandlers,
  createImportHandler,
  blockFilteredSkillFile,
  generateCheckAccess,
  getStorageMetadata,
  resolveRequestTenantId,
  restoreTenantContextFromReq,
} = require('@librechat/api');
const { isValidObjectIdString, logger } = require('@librechat/data-schemas');
const {
  PermissionBits,
  PermissionTypes,
  Permissions,
  ResourceType,
  PrincipalType,
  AccessRoleIds,
  FileContext,
  mergeFileConfig,
} = require('librechat-data-provider');
const {
  createSkill,
  getSkillById,
  updateSkill,
  deleteSkill,
  upsertSkillFile,
  deleteSkillFile,
  getSkillFileByPath,
  getRoleByName,
} = require('~/models');
const { requireJwtAuth, canAccessSkillResource } = require('~/server/middleware');
const {
  findAccessibleResources,
  findPubliclyAccessibleResources,
  hasPublicPermission,
  grantPermission,
} = require('~/server/services/PermissionService');
const { getStrategyFunctions } = require('~/server/services/Files/strategies');
const { createFileLimiters } = require('~/server/middleware/limiters/uploadLimiters');
const { maybeRunGitHubSkillSyncForRequest } = require('~/server/services/Skills/sync');
const configMiddleware = require('~/server/middleware/config/app');
const { getFileStrategy } = require('~/server/utils/getFileStrategy');
const {
  getSkillDbMethods,
  withDeploymentSkillIds,
  getSkillStrategyFunctions,
} = require('~/server/services/Endpoints/agents/skillDeps');

const router = express.Router();

// ---------------------------------------------------------------------------
// Multer: memory storage for skill imports (zip processed in-memory)
// ---------------------------------------------------------------------------
const ALLOWED_EXTENSIONS = new Set(['.md', '.zip', '.skill']);
const MAX_IMPORT_SIZE = 50 * 1024 * 1024; // 50 MB

const memoryStorage = multer.memoryStorage();

function getSkillImportSizeLimit(req) {
  const fileConfig = mergeFileConfig(req.config?.fileConfig);
  return fileConfig.skills?.fileSizeLimit ?? MAX_IMPORT_SIZE;
}

const skillImportFilter = (_req, file, cb) => {
  const ext = path.extname(file.originalname).toLowerCase();
  if (ALLOWED_EXTENSIONS.has(ext)) {
    cb(null, true);
  } else {
    // N.B. The error handler at the bottom of this file matches this "Only " prefix.
    cb(new Error('Only .md, .zip, and .skill files are allowed'), false);
  }
};

const skillUpload = (req, res, next) =>
  multer({
    storage: memoryStorage,
    fileFilter: skillImportFilter,
    limits: { fileSize: getSkillImportSizeLimit(req) },
  }).single('file')(req, res, next);

// Per-file upload (for adding individual files to an existing skill)
const MAX_SINGLE_FILE_SIZE = 10 * 1024 * 1024; // 10 MB
const singleFileUpload = multer({
  storage: memoryStorage,
  limits: { fileSize: MAX_SINGLE_FILE_SIZE },
});

// ---------------------------------------------------------------------------
// Role-based capability gates
// ---------------------------------------------------------------------------
const checkSkillAccess = generateCheckAccess({
  permissionType: PermissionTypes.SKILLS,
  permissions: [Permissions.USE],
  getRoleByName,
});
const checkSkillCreate = generateCheckAccess({
  permissionType: PermissionTypes.SKILLS,
  permissions: [Permissions.USE, Permissions.CREATE],
  getRoleByName,
});

// ---------------------------------------------------------------------------
// Rate limiters (reuse existing file upload limiters)
// ---------------------------------------------------------------------------
const { fileUploadIpLimiter, fileUploadUserLimiter } = createFileLimiters();
const skillDbMethods = getSkillDbMethods();

router.use(requireJwtAuth);
router.use(configMiddleware);
router.use(checkSkillAccess);

// ---------------------------------------------------------------------------
// CRUD handlers
// ---------------------------------------------------------------------------
const handlers = createSkillsHandlers({
  createSkill,
  getSkillById: skillDbMethods.getSkillById,
  listSkillsByAccess: skillDbMethods.listSkillsByAccess,
  updateSkill,
  deleteSkill,
  listSkillFiles: skillDbMethods.listSkillFiles,
  deleteSkillFile,
  getSkillFileByPath: skillDbMethods.getSkillFileByPath,
  updateSkillFileContent: skillDbMethods.updateSkillFileContent,
  getStrategyFunctions: getSkillStrategyFunctions,
  findAccessibleResources: async (params) =>
    params.resourceType === 'skill' && params.requiredPermissions === PermissionBits.VIEW
      ? withDeploymentSkillIds(await findAccessibleResources(params))
      : findAccessibleResources(params),
  findPubliclyAccessibleResources: async (params) =>
    params.resourceType === 'skill' && params.requiredPermissions === PermissionBits.VIEW
      ? withDeploymentSkillIds(await findPubliclyAccessibleResources(params))
      : findPubliclyAccessibleResources(params),
  hasPublicPermission: async (params) =>
    params.resourceType === 'skill' && params.requiredPermissions === PermissionBits.VIEW
      ? withDeploymentSkillIds([]).some((id) => id.toString() === params.resourceId.toString()) ||
        hasPublicPermission(params)
      : hasPublicPermission(params),
  grantPermission,
  isValidObjectIdString,
});

// ---------------------------------------------------------------------------
// File storage helper: resolve the active strategy's saveBuffer
// ---------------------------------------------------------------------------
function resolveSkillStorage(req, { isImage = false } = {}) {
  const source = getFileStrategy(req.config, { context: FileContext.skill_file, isImage });
  const strategy = getStrategyFunctions(source);
  if (!strategy.saveBuffer) {
    throw new Error(`Storage backend "${source}" does not support file writes`);
  }
  return { saveBuffer: strategy.saveBuffer, source };
}

// ---------------------------------------------------------------------------
// Import handler (zip/md/skill → create skill + files)
// ---------------------------------------------------------------------------
const importHandler = createImportHandler({
  limits: (req) => ({
    maxZipBytes: getSkillImportSizeLimit(req),
  }),
  createSkill,
  getSkillById,
  deleteSkill,
  upsertSkillFile,
  saveBuffer: (req, { userId, buffer, fileName, basePath, isImage, tenantId }) => {
    const requestTenantId = tenantId ?? resolveRequestTenantId(req);
    const storage = resolveSkillStorage(req, { isImage });
    return storage
      .saveBuffer({ userId, buffer, fileName, basePath, tenantId: requestTenantId })
      .then((filepath) => ({
        filepath,
        source: storage.source,
        ...getStorageMetadata({ filepath, source: storage.source }),
      }));
  },
  deleteFile: (req, file) => {
    const { deleteFile } = getStrategyFunctions(file.source);
    if (deleteFile) {
      return deleteFile(req, file);
    }
    return Promise.resolve();
  },
  grantPermission,
});

// ---------------------------------------------------------------------------
// Managed-skill draft lifecycle
// ---------------------------------------------------------------------------

function getSkillLifecycle(skill) {
  return skill?.sourceMetadata?.lifecycle;
}

function isManagedDraft(skill) {
  return (
    skill?.source === 'inline' &&
    (getSkillLifecycle(skill) === 'draft' ||
      getSkillLifecycle(skill) === 'trial' ||
      getSkillLifecycle(skill) === 'publish_pending') &&
    typeof skill?.sourceMetadata?.draftOfSkillId === 'string'
  );
}

function buildDraftName(published) {
  const suffix = `-draft-${published._id.toString().slice(-6)}`;
  const maxBase = Math.max(1, 64 - suffix.length);
  return `${published.name.slice(0, maxBase)}${suffix}`;
}

async function createManagedDraftHandler(req, res) {
  try {
    const publishedId = req.params.id;
    const published = await getSkillById(publishedId);
    if (!published) {
      return res.status(404).json({ error: 'Skill not found' });
    }
    if (published.source !== 'github') {
      return res.status(400).json({ error: 'Only GitHub-managed skills can create managed drafts' });
    }

    const author = req.user?._id ?? req.user?.id;
    if (!author) {
      return res.status(401).json({ error: 'Authentication required' });
    }

    const draftName = buildDraftName(published);
    const existing = await db.getAuthorSkillByName({
      name: draftName,
      author,
      tenantId: resolveRequestTenantId(req),
    });
    if (existing && isManagedDraft(existing)) {
      return res.status(200).json(existing);
    }

    const inheritedMetadata =
      published.sourceMetadata && typeof published.sourceMetadata === 'object'
        ? published.sourceMetadata
        : {};
    const sourceMetadata = {
      lifecycle: 'draft',
      draftOfSkillId: published._id.toString(),
      logicalName: published.name,
      baseVersion: published.version,
      baseCommitSha: inheritedMetadata.commitSha,
      baseSkillBlobSha: inheritedMetadata.skillBlobSha,
      provider: inheritedMetadata.provider ?? 'github',
      sourceId: inheritedMetadata.sourceId,
      owner: inheritedMetadata.owner,
      repo: inheritedMetadata.repo,
      ref: inheritedMetadata.ref,
      skillPath: inheritedMetadata.skillPath,
      createdFromPublishedAt: new Date().toISOString(),
    };

    const createResult = await createSkill({
      name: draftName,
      displayTitle: published.displayTitle
        ? `${published.displayTitle} — Draft`
        : `${published.name} — Draft`,
      description: published.description,
      body: published.body,
      frontmatter: {
        ...(published.frontmatter ?? {}),
        'disable-model-invocation': true,
        'user-invocable': true,
      },
      category: published.category,
      alwaysApply: false,
      author,
      authorName: req.user.name ?? req.user.username ?? 'Unknown',
      source: 'inline',
      sourceMetadata,
      tenantId: resolveRequestTenantId(req),
    });

    const draft = createResult.skill;
    try {
      await grantPermission({
        principalType: PrincipalType.USER,
        principalId: req.user.id,
        resourceType: ResourceType.SKILL,
        resourceId: draft._id,
        accessRoleId: AccessRoleIds.SKILL_OWNER,
        grantedBy: req.user.id,
      });

      const publishedFiles = await db.listSkillFiles(published._id);
      for (const file of publishedFiles) {
        await db.upsertSkillFile({
          skillId: draft._id,
          relativePath: file.relativePath,
          file_id: crypto.randomUUID(),
          filename: file.filename,
          filepath: file.filepath,
          storageKey: file.storageKey,
          storageRegion: file.storageRegion,
          source: file.source,
          sourceMetadata: {
            ...(file.sourceMetadata ?? {}),
            sharedFromSkillId: published._id.toString(),
            sharedStorage: true,
          },
          mimeType: file.mimeType,
          bytes: file.bytes,
          isExecutable: file.isExecutable,
          author,
          tenantId: resolveRequestTenantId(req),
        });
      }
    } catch (error) {
      await deleteSkill(draft._id.toString()).catch(() => undefined);
      throw error;
    }

    return res.status(201).json(await getSkillById(draft._id));
  } catch (error) {
    logger.error('[POST /skills/:id/draft] Error creating managed draft', error);
    return res.status(500).json({ error: 'Failed to create managed skill draft' });
  }
}

async function setManagedDraftLifecycleHandler(req, res) {
  try {
    const id = req.params.id;
    const draft = await getSkillById(id);
    if (!draft) {
      return res.status(404).json({ error: 'Skill not found' });
    }
    if (!isManagedDraft(draft)) {
      return res.status(400).json({ error: 'Skill is not a managed draft' });
    }
    const lifecycle = req.body?.lifecycle;
    if (!['draft', 'trial', 'publish_pending'].includes(lifecycle)) {
      return res.status(400).json({ error: 'Invalid draft lifecycle' });
    }
    const result = await updateSkill({
      id,
      expectedVersion: draft.version,
      update: {
        sourceMetadata: {
          ...(draft.sourceMetadata ?? {}),
          lifecycle,
          lifecycleUpdatedAt: new Date().toISOString(),
        },
      },
    });
    if (result.status === 'conflict') {
      return res.status(409).json({ error: 'skill_version_conflict', current: result.current });
    }
    if (result.status !== 'updated') {
      return res.status(404).json({ error: 'Skill not found' });
    }
    return res.status(200).json(result.skill);
  } catch (error) {
    logger.error('[POST /skills/:id/lifecycle] Error updating managed draft lifecycle', error);
    return res.status(500).json({ error: 'Failed to update managed skill draft lifecycle' });
  }
}



function githubPathSegment(value) {
  return String(value)
    .split('/')
    .map((segment) => encodeURIComponent(segment))
    .join('/');
}

async function githubJson(token, method, url, body) {
  const response = await fetch(url, {
    method,
    headers: {
      Accept: 'application/vnd.github+json',
      Authorization: `Bearer ${token}`,
      'X-GitHub-Api-Version': '2022-11-28',
      'User-Agent': 'LibreChat-Skill-Publisher',
      ...(body === undefined ? {} : { 'Content-Type': 'application/json' }),
    },
    ...(body === undefined ? {} : { body: JSON.stringify(body) }),
  });
  const text = await response.text();
  let payload = null;
  if (text) {
    try {
      payload = JSON.parse(text);
    } catch {
      payload = { message: text };
    }
  }
  if (!response.ok) {
    const error = new Error(
      payload?.message || `GitHub API request failed with status ${response.status}`,
    );
    error.status = response.status;
    error.payload = payload;
    throw error;
  }
  return payload;
}

async function readSkillFileBuffer(req, file) {
  const strategy = getStrategyFunctions(file.source);
  if (!strategy.getDownloadStream) {
    throw new Error(`Storage backend "${file.source}" cannot read skill files`);
  }
  const stream = await strategy.getDownloadStream(req, file.storageKey || file.filepath);
  const chunks = [];
  for await (const raw of stream) {
    chunks.push(Buffer.isBuffer(raw) ? raw : Buffer.from(raw));
  }
  return Buffer.concat(chunks);
}

async function publishManagedDraftHandler(req, res) {
  try {
    const draftId = req.params.id;
    const draft = await getSkillById(draftId);
    if (!draft) {
      return res.status(404).json({ error: 'Skill not found' });
    }
    if (!isManagedDraft(draft)) {
      return res.status(400).json({ error: 'Skill is not a managed draft' });
    }

    const metadata = draft.sourceMetadata ?? {};
    const published = await getSkillById(metadata.draftOfSkillId);
    if (!published || published.source !== 'github') {
      return res.status(409).json({ error: 'Published source skill is no longer available' });
    }

    const publishedMetadata = published.sourceMetadata ?? {};
    const sourceId = metadata.sourceId ?? publishedMetadata.sourceId;
    const owner = metadata.owner ?? publishedMetadata.owner;
    const repo = metadata.repo ?? publishedMetadata.repo;
    const ref = metadata.ref ?? publishedMetadata.ref;
    const skillPath = metadata.skillPath ?? publishedMetadata.skillPath;
    if (![sourceId, owner, repo, ref, skillPath].every((value) => typeof value === 'string' && value)) {
      return res.status(409).json({ error: 'Managed draft is missing GitHub source metadata' });
    }

    const status = await db.getSkillSyncStatus('github', sourceId, resolveRequestTenantId(req));
    const credentialKey = status?.credentialKey;
    if (!credentialKey) {
      return res.status(409).json({ error: 'No GitHub credential is configured for this skill source' });
    }
    const token = await db.getSkillSyncCredentialToken('github', credentialKey);
    if (!token) {
      return res.status(409).json({ error: 'GitHub credential is not available' });
    }

    const baseApi = `https://api.github.com/repos/${encodeURIComponent(owner)}/${encodeURIComponent(repo)}`;
    const refPath = githubPathSegment(ref);
    const refPayload = await githubJson(token, 'GET', `${baseApi}/git/ref/heads/${refPath}`);
    const baseCommitSha = refPayload?.object?.sha;
    if (!baseCommitSha) {
      throw new Error('Unable to resolve GitHub base commit');
    }
    const baseCommit = await githubJson(token, 'GET', `${baseApi}/git/commits/${baseCommitSha}`);
    const baseTreeSha = baseCommit?.tree?.sha;
    if (!baseTreeSha) {
      throw new Error('Unable to resolve GitHub base tree');
    }

    const draftFiles = await db.listSkillFiles(draft._id);
    const publishedFiles = await db.listSkillFiles(published._id);
    const tree = [];

    const skillBlob = await githubJson(token, 'POST', `${baseApi}/git/blobs`, {
      content: Buffer.from(draft.body ?? '', 'utf8').toString('base64'),
      encoding: 'base64',
    });
    tree.push({
      path: `${skillPath}/SKILL.md`,
      mode: '100644',
      type: 'blob',
      sha: skillBlob.sha,
    });

    const draftPaths = new Set();
    for (const file of draftFiles) {
      draftPaths.add(file.relativePath);
      const buffer = await readSkillFileBuffer(req, file);
      const blob = await githubJson(token, 'POST', `${baseApi}/git/blobs`, {
        content: buffer.toString('base64'),
        encoding: 'base64',
      });
      tree.push({
        path: `${skillPath}/${file.relativePath}`,
        mode: '100644',
        type: 'blob',
        sha: blob.sha,
      });
    }

    for (const file of publishedFiles) {
      if (!draftPaths.has(file.relativePath)) {
        tree.push({
          path: `${skillPath}/${file.relativePath}`,
          mode: '100644',
          type: 'blob',
          sha: null,
        });
      }
    }

    const treePayload = await githubJson(token, 'POST', `${baseApi}/git/trees`, {
      base_tree: baseTreeSha,
      tree,
    });
    const logicalName = metadata.logicalName ?? published.name;
    const commitPayload = await githubJson(token, 'POST', `${baseApi}/git/commits`, {
      message: `feat(skill): publish draft for ${logicalName}`,
      tree: treePayload.sha,
      parents: [baseCommitSha],
    });

    const safeLogicalName = String(logicalName)
      .toLowerCase()
      .replace(/[^a-z0-9-]+/g, '-')
      .replace(/^-+|-+$/g, '')
      .slice(0, 40);
    const branchName = `skill/${safeLogicalName || 'draft'}-${draft._id.toString().slice(-6)}`;
    await githubJson(token, 'POST', `${baseApi}/git/refs`, {
      ref: `refs/heads/${branchName}`,
      sha: commitPayload.sha,
    });

    const pull = await githubJson(token, 'POST', `${baseApi}/pulls`, {
      title: `feat(skill): update ${logicalName}`,
      head: branchName,
      base: ref,
      body:
        'Published from a LibreChat managed skill draft. The existing published skill remains active until this PR is merged and Skill Sync completes.',
    });

    const result = await updateSkill({
      id: draftId,
      expectedVersion: draft.version,
      update: {
        sourceMetadata: {
          ...metadata,
          lifecycle: 'publish_pending',
          lifecycleUpdatedAt: new Date().toISOString(),
          publishBaseCommitSha: baseCommitSha,
          publishCommitSha: commitPayload.sha,
          githubBranch: branchName,
          githubPrNumber: pull.number,
          githubPrUrl: pull.html_url,
        },
      },
    });
    if (result.status !== 'updated') {
      return res.status(409).json({
        error: 'skill_version_conflict',
        message: 'Draft was published to GitHub, but LibreChat could not record the pending state.',
        githubPrUrl: pull.html_url,
      });
    }

    return res.status(201).json({
      skill: result.skill,
      branch: branchName,
      commitSha: commitPayload.sha,
      pullRequestNumber: pull.number,
      pullRequestUrl: pull.html_url,
    });
  } catch (error) {
    logger.error('[POST /skills/:id/publish] Error publishing managed draft', error);
    const status = Number.isInteger(error?.status) ? error.status : 500;
    if (status === 401 || status === 403) {
      return res.status(409).json({
        error: 'github_publish_permission_required',
        message:
          'The configured GitHub credential can read Skill Sync content but cannot publish. Grant Contents and Pull Requests write access, then retry.',
      });
    }
    if (status === 422) {
      return res.status(409).json({
        error: 'github_publish_conflict',
        message: error?.payload?.message || 'GitHub rejected the draft publication request',
      });
    }
    return res.status(500).json({ error: 'Failed to publish managed skill draft' });
  }
}
// ---------------------------------------------------------------------------
// Per-file upload handler (add a single file to an existing skill)
// ---------------------------------------------------------------------------
async function uploadFileHandler(req, res) {
  try {
    const { file } = req;
    if (!file) {
      return res.status(400).json({ error: 'No file provided' });
    }

    const skillId = req.params.id;
    const skill = await getSkillById(skillId);
    if (!skill) {
      return res.status(404).json({ error: 'Skill not found' });
    }
    if (skill.source !== 'inline') {
      return res.status(409).json({
        error: 'skill_external_source_read_only',
        message:
          'Externally managed skills are read-only in LibreChat. Update the upstream source and run Skill Sync.',
      });
    }

    const relativePath = req.body.relativePath;
    if (!relativePath) {
      return res.status(400).json({ error: 'relativePath is required in form body' });
    }
    if (relativePath.toUpperCase() === 'SKILL.MD') {
      return res.status(400).json({ error: 'SKILL.md is reserved; update the skill body instead' });
    }
    // Reject traversal, absolute paths, empty/dot segments — matches model-layer validator
    // so storage writes don't happen before DB rejects the path.
    if (
      !/^[a-zA-Z0-9._\-/]+$/.test(relativePath) ||
      /^\//.test(relativePath) ||
      relativePath.split('/').some((s) => s === '' || s === '.' || s === '..')
    ) {
      return res.status(400).json({ error: 'Invalid file path' });
    }
    if (
      blockFilteredSkillFile(req.config?.filters, res, {
        buffer: file.buffer,
        originalName: file.originalname,
        relativePath,
      })
    ) {
      return res;
    }

    const tenantId = resolveRequestTenantId(req);

    // Look up existing file before saving — needed to clean up old blob on replace
    const existingFile = await getSkillFileByPath(skillId, relativePath);

    const fileId = crypto.randomUUID();
    const filename = file.originalname;
    const storageFileName = `${fileId}__${filename}`;

    const isImage = (file.mimetype || '').startsWith('image/');
    const storage = resolveSkillStorage(req, { isImage });
    const filepath = await storage.saveBuffer({
      userId: req.user.id,
      buffer: file.buffer,
      fileName: storageFileName,
      basePath: 'uploads',
      tenantId,
    });
    const storageMetadata = getStorageMetadata({ filepath, source: storage.source });

    let result;
    try {
      result = await upsertSkillFile({
        skillId,
        relativePath,
        file_id: fileId,
        filename,
        filepath,
        ...storageMetadata,
        source: storage.source,
        mimeType: file.mimetype || 'application/octet-stream',
        bytes: file.size,
        isExecutable: false,
        author: req.user._id,
        tenantId,
      });
    } catch (dbError) {
      // Clean up the stored blob so it doesn't leak on DB failure
      try {
        const { deleteFile } = getStrategyFunctions(storage.source);
        if (deleteFile) {
          await deleteFile(req, { filepath, user: req.user.id, tenantId });
        }
      } catch (cleanupErr) {
        logger.error('[uploadFile] Failed to clean up orphaned blob:', cleanupErr);
      }
      throw dbError;
    }

    // Clean up old blob if this was a replace (different filepath means new storage object)
    if (
      existingFile &&
      existingFile.filepath !== filepath &&
      existingFile.sourceMetadata?.sharedStorage !== true
    ) {
      const { deleteFile: delOld } = getStrategyFunctions(existingFile.source);
      if (delOld) {
        delOld(req, {
          filepath: existingFile.filepath,
          user: existingFile.author ?? req.user.id,
          tenantId: existingFile.tenantId ?? tenantId,
        }).catch((e) => logger.error('[uploadFile] Old blob cleanup failed:', e));
      }
    }

    return res.status(200).json(result);
  } catch (error) {
    if (error.code === 'SKILL_FILE_VALIDATION_FAILED') {
      return res.status(400).json({ error: error.message });
    }
    logger.error('[uploadFile] Error:', error);
    return res.status(500).json({ error: 'Failed to upload file' });
  }
}

// ---------------------------------------------------------------------------
// Routes
// ---------------------------------------------------------------------------
async function maybeStartRequestSkillSync(req, _res, next) {
  try {
    await maybeRunGitHubSkillSyncForRequest(req);
  } catch (error) {
    logger.error('[GET /skills] Failed to start request-scoped skill sync:', error);
  }
  next();
}

// Import: accepts .md / .zip / .skill via multipart
router.post(
  '/import',
  checkSkillCreate,
  fileUploadIpLimiter,
  fileUploadUserLimiter,
  skillUpload,
  restoreTenantContextFromReq,
  importHandler,
);

router.get('/', maybeStartRequestSkillSync, handlers.list);
router.post('/', checkSkillCreate, handlers.create);

router.post(
  '/:id/draft',
  checkSkillCreate,
  canAccessSkillResource({ requiredPermission: PermissionBits.VIEW }),
  createManagedDraftHandler,
);

router.post(
  '/:id/lifecycle',
  checkSkillCreate,
  canAccessSkillResource({ requiredPermission: PermissionBits.EDIT }),
  setManagedDraftLifecycleHandler,
);

router.post(
  '/:id/publish',
  checkSkillCreate,
  canAccessSkillResource({ requiredPermission: PermissionBits.EDIT }),
  publishManagedDraftHandler,
);

router.get(
  '/:id',
  canAccessSkillResource({ requiredPermission: PermissionBits.VIEW }),
  handlers.get,
);

router.patch(
  '/:id',
  checkSkillCreate,
  canAccessSkillResource({ requiredPermission: PermissionBits.EDIT }),
  handlers.patch,
);

router.delete(
  '/:id',
  checkSkillCreate,
  canAccessSkillResource({ requiredPermission: PermissionBits.DELETE }),
  handlers.delete,
);

router.get(
  '/:id/files',
  canAccessSkillResource({ requiredPermission: PermissionBits.VIEW }),
  handlers.listFiles,
);

// Per-file upload (live — replaces 501 stub)
router.post(
  '/:id/files',
  canAccessSkillResource({ requiredPermission: PermissionBits.EDIT }),
  fileUploadIpLimiter,
  fileUploadUserLimiter,
  singleFileUpload.single('file'),
  restoreTenantContextFromReq,
  uploadFileHandler,
);

// Wildcard splat (`*relativePath`) captures nested skill paths (e.g.
// `references/guide.md`) whether the client sends an encoded `%2F` or a proxy
// has already decoded it to a literal slash. A single `:relativePath` segment
// 404s in the latter case, which is why nested files failed behind proxies.
router.get(
  '/:id/files/*relativePath',
  canAccessSkillResource({ requiredPermission: PermissionBits.VIEW }),
  handlers.downloadFile,
);

router.delete(
  '/:id/files/*relativePath',
  canAccessSkillResource({ requiredPermission: PermissionBits.EDIT }),
  handlers.deleteFile,
);

// Multer + file-filter error handler — surface as 400, forward everything else

router.use((err, _req, res, next) => {
  if (err && (err.name === 'MulterError' || err.message?.startsWith('Only '))) {
    return res.status(400).json({ error: err.message });
  }
  return next(err);
});

module.exports = router;
