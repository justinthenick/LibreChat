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
