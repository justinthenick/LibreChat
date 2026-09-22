const fs = require('fs');
const path = require('path');

require('module-alias')({ base: path.resolve(__dirname, '..', 'api') });

const {
  AccessRoleIds,
  ResourceType,
  PrincipalType,
  SystemRoles,
} = require('librechat-data-provider');
const connect = require('./connect');

const MANIFEST_DIR =
  process.argv[2] || process.env.CODING_AGENT_MANIFEST_DIR || '/app/coding-agent-pilot';
const MANIFEST_FILE = 'software-engineering-pilot.json';
const PILOT_AGENT_ID = 'agent_software_engineering_pilot_v01';
const MCP_SERVER = 'coding_executor';
const GOOGLE_ENDPOINT_NAME = 'google';
const OPENROUTER_ENDPOINT_NAME = 'OpenRouter';
const EXPECTED_MCP_TOOLS = [
  'list_repositories',
  'create_task',
  'task_status',
  'list_files',
  'read_file',
  'search_text',
  'apply_patch',
  'run_check',
  'git_diff',
];

const EXPECTED_SKILL = Object.freeze({
  name: 'codebase-design',
  source: 'github',
  sourceId: 'coding-agent-skills',
  owner: 'justinthenick',
  repo: 'LibreChat',
  ref: 'server/synology',
  path: '.agents/skills/codebase-design',
});

function parseAllowedModels(raw) {
  return String(raw || '')
    .split(/[\r\n,]+/)
    .map((value) => value.trim())
    .filter(Boolean);
}

function chooseModel(manifest) {
  const allowedModels = parseAllowedModels(process.env.ALLOWED_MODELS);
  const preferredModel = String(manifest?.preferred_model || '').trim();
  if (!preferredModel) {
    throw new Error(`${manifest.id} must declare a preferred model`);
  }
  if (allowedModels.length > 0 && !allowedModels.includes(preferredModel)) {
    throw new Error(
      `${manifest.id} preferred model ${preferredModel} is not present in configured ALLOWED_MODELS`,
    );
  }
  return preferredModel;
}

function normalizeProvider(value) {
  const normalized = String(value || '')
    .trim()
    .toLowerCase();
  if (normalized === 'google') {
    return GOOGLE_ENDPOINT_NAME;
  }
  if (normalized === 'openrouter') {
    return OPENROUTER_ENDPOINT_NAME;
  }
  throw new Error(`Unsupported coding-agent provider: ${value}`);
}

function sortedStrings(values) {
  return (Array.isArray(values) ? values : []).map(String).sort();
}

function sameStrings(left, right) {
  const a = sortedStrings(left);
  const b = sortedStrings(right);
  return a.length === b.length && a.every((value, index) => value === b[index]);
}

function persistedToolIds(manifest) {
  return manifest.mcp_tools.map((tool) => `${tool}_mcp_${manifest.mcp_server}`);
}

function expectedSkillUpstreamId(skill = EXPECTED_SKILL) {
  return `${skill.sourceId}:${skill.path}`;
}

function validateManifestSkillPolicy(manifest) {
  if (manifest.skills_enabled !== true) {
    throw new Error(`${manifest.id} must explicitly enable its validated skill allowlist`);
  }
  if (!Array.isArray(manifest.skills) || manifest.skills.length !== 1) {
    throw new Error(`${manifest.id} must declare exactly one validated skill`);
  }

  const skill = manifest.skills[0];
  const expected = {
    name: EXPECTED_SKILL.name,
    source: EXPECTED_SKILL.source,
    source_id: EXPECTED_SKILL.sourceId,
    owner: EXPECTED_SKILL.owner,
    repo: EXPECTED_SKILL.repo,
    ref: EXPECTED_SKILL.ref,
    path: EXPECTED_SKILL.path,
  };
  for (const [key, value] of Object.entries(expected)) {
    if (skill?.[key] !== value) {
      throw new Error(
        `${manifest.id} skill allowlist differs from validated ${EXPECTED_SKILL.name} identity at ${key}`,
      );
    }
  }
}

async function resolveSkillAllowlist(db, manifest) {
  validateManifestSkillPolicy(manifest);
  const declared = manifest.skills[0];
  const upstreamId = expectedSkillUpstreamId({
    sourceId: declared.source_id,
    path: declared.path,
  });
  const skill = await db.findSkillBySourceIdentity({
    source: declared.source,
    upstreamId,
  });

  if (!skill) {
    throw new Error(
      `${manifest.id} requires mirrored skill ${upstreamId}, but it is not available; refusing to widen the allowlist`,
    );
  }

  const metadata = skill.sourceMetadata || {};
  const expectedMetadata = {
    sourceId: declared.source_id,
    owner: declared.owner,
    repo: declared.repo,
    ref: declared.ref,
    skillPath: declared.path,
    syncStatus: 'synced',
  };
  for (const [key, value] of Object.entries(expectedMetadata)) {
    if (metadata[key] !== value) {
      throw new Error(
        `${manifest.id} resolved skill ${declared.name} has unexpected source metadata ${key}`,
      );
    }
  }
  if (skill.name !== declared.name || skill.disableModelInvocation === true) {
    throw new Error(
      `${manifest.id} resolved skill does not match the validated model-invocable ${declared.name} contract`,
    );
  }

  return [
    {
      id: skill._id.toString(),
      name: skill.name,
      upstreamId,
    },
  ];
}

function loadManifest() {
  const fullPath = path.resolve(MANIFEST_DIR, MANIFEST_FILE);
  const root = path.resolve(MANIFEST_DIR) + path.sep;
  if (!fullPath.startsWith(root)) {
    throw new Error('Coding-agent manifest path escaped the configured directory');
  }
  const manifest = JSON.parse(fs.readFileSync(fullPath, 'utf8'));
  if (manifest.id !== PILOT_AGENT_ID) {
    throw new Error(`Unexpected coding-agent id: ${manifest.id}`);
  }
  if (manifest.status !== 'validated-for-persistent-pilot') {
    throw new Error(`${manifest.id} is not approved for persistent pilot use`);
  }
  if (manifest.mcp_server !== MCP_SERVER) {
    throw new Error(`${manifest.id} must use only the ${MCP_SERVER} MCP server`);
  }
  if (!sameStrings(manifest.mcp_tools, EXPECTED_MCP_TOOLS)) {
    throw new Error(`${manifest.id} MCP tool allowlist differs from the validated nine-tool set`);
  }
  if (manifest.deployment?.production_seeder !== 'enabled') {
    throw new Error(`${manifest.id} persistent seeding has not been explicitly enabled`);
  }
  validateManifestSkillPolicy(manifest);
  return manifest;
}

async function resolveOwner(User) {
  const requestedEmail = String(process.env.PRODUCTION_AGENT_OWNER_EMAIL || '')
    .trim()
    .toLowerCase();
  if (requestedEmail) {
    const owner = await User.findOne({ email: requestedEmail, role: SystemRoles.ADMIN })
      .select('_id email role createdAt')
      .lean();
    if (!owner) {
      throw new Error('PRODUCTION_AGENT_OWNER_EMAIL does not identify an ADMIN user');
    }
    return owner;
  }

  const admins = await User.find({ role: SystemRoles.ADMIN })
    .sort({ createdAt: 1, _id: 1 })
    .select('_id role createdAt')
    .lean();
  if (admins.length === 0) {
    throw new Error('No ADMIN user exists; the coding-agent pilot cannot be given a safe owner');
  }
  if (admins.length > 1) {
    console.warn(
      `Multiple ADMIN users exist; assigning coding-agent pilot to the oldest admin (${admins[0]._id})`,
    );
  }
  return admins[0];
}

function desiredAgent(manifest, author, resolvedSkills) {
  const skillIds = resolvedSkills.map((skill) => String(skill.id));
  return {
    id: manifest.id,
    name: manifest.name,
    description: manifest.description,
    instructions: manifest.instructions,
    provider: normalizeProvider(manifest.provider),
    model: chooseModel(manifest),
    model_parameters: {},
    tools: persistedToolIds(manifest),
    mcpServerNames: [manifest.mcp_server],
    skills: skillIds,
    skills_enabled: manifest.skills_enabled === true,
    execute_code: false,
    web_search: false,
    file_search: false,
    memory: false,
    memory_scope: manifest.memory_scope || 'agent',
    artifacts: manifest.artifacts,
    edges: [],
    subagents: null,
    conversation_starters: Array.isArray(manifest.conversation_starters)
      ? manifest.conversation_starters.map(String)
      : [],
    category: 'software-engineering',
    author,
  };
}

async function ensureOwnerPermissions({ grantPermission, agent, ownerId }) {
  for (const [resourceType, accessRoleId] of [
    [ResourceType.AGENT, AccessRoleIds.AGENT_OWNER],
    [ResourceType.REMOTE_AGENT, AccessRoleIds.REMOTE_AGENT_OWNER],
  ]) {
    await grantPermission({
      principalType: PrincipalType.USER,
      principalId: ownerId,
      resourceType,
      resourceId: agent._id,
      accessRoleId,
      grantedBy: ownerId,
    });
  }
}

function validatePersistedAgent(agent, manifest, resolvedSkills) {
  const expectedTools = persistedToolIds(manifest);
  const expectedSkillIds = resolvedSkills.map((skill) => String(skill.id));
  if (agent.id !== manifest.id) {
    throw new Error(`${manifest.id} did not retain its stable id`);
  }
  if (!sameStrings(agent.tools, expectedTools)) {
    throw new Error(`${manifest.id} persisted tools differ from the validated nine-tool allowlist`);
  }
  if (!sameStrings(agent.mcpServerNames, [MCP_SERVER])) {
    throw new Error(`${manifest.id} MCP server scope differs from ${MCP_SERVER}`);
  }
  if ((agent.tools || []).some((tool) => String(tool).startsWith('sys__all__sys_mcp_'))) {
    throw new Error(`${manifest.id} unexpectedly retained an MCP wildcard token`);
  }
  if (
    agent.skills_enabled !== true ||
    expectedSkillIds.length !== 1 ||
    !sameStrings(agent.skills, expectedSkillIds)
  ) {
    throw new Error(
      `${manifest.id} skill allowlist was pruned, widened, or disabled; refusing persistent seed`,
    );
  }
  if (agent.edges?.length || agent.subagents != null) {
    throw new Error(`${manifest.id} unexpectedly retained orchestration wiring`);
  }
  const expectedProvider = normalizeProvider(manifest.provider);
  if (agent.provider !== expectedProvider) {
    throw new Error(`${manifest.id} did not retain provider ${expectedProvider}`);
  }
  if (agent.model !== manifest.preferred_model) {
    throw new Error(`${manifest.id} did not retain preferred model ${manifest.preferred_model}`);
  }
  if (agent.memory_scope !== 'agent' || agent.artifacts !== manifest.artifacts) {
    throw new Error(`${manifest.id} did not retain isolated memory and artifact settings`);
  }
}

async function seed() {
  if (!fs.existsSync(MANIFEST_DIR)) {
    throw new Error(`Coding-agent manifest directory not found: ${MANIFEST_DIR}`);
  }
  const manifest = loadManifest();
  await connect();

  const db = require('~/models');
  const { User } = require('~/db/models');
  const { grantPermission } = require('~/server/services/PermissionService');
  const owner = await resolveOwner(User);
  const defaultOwnerId = owner._id.toString();
  const resolvedSkills = await resolveSkillAllowlist(db, manifest);

  let existing = await db.getAgent({ id: manifest.id });
  let adoptedManualAgent = false;
  if (!existing) {
    const sameName = await db.getAgents({ name: manifest.name, author: owner._id });
    if (sameName.length > 1) {
      throw new Error(
        `Multiple admin-owned agents are named ${manifest.name}; refusing ambiguous adoption`,
      );
    }
    existing = sameName[0] || null;
    adoptedManualAgent = Boolean(existing);
  }

  const ownerId = existing?.author?.toString() || defaultOwnerId;
  const desired = desiredAgent(manifest, ownerId, resolvedSkills);
  let agent;
  let outcome;
  if (existing) {
    const { author: _author, ...updates } = desired;
    if (existing.id === manifest.id) {
      delete updates.id;
    }
    agent = await db.updateAgent({ _id: existing._id }, updates, { updatingUserId: ownerId });
    outcome = adoptedManualAgent ? 'adopted-and-updated' : 'updated';
  } else {
    agent = await db.createAgent(desired);
    outcome = 'created';
  }

  if (!agent) {
    throw new Error(`Seeder did not return ${manifest.id}`);
  }
  validatePersistedAgent(agent, manifest, resolvedSkills);
  await ensureOwnerPermissions({ grantPermission, agent, ownerId });

  const result = {
    ok: true,
    id: manifest.id,
    outcome,
    owner: ownerId,
    provider: agent.provider,
    model: agent.model,
    mcpServerNames: sortedStrings(agent.mcpServerNames),
    tools: sortedStrings(agent.tools),
    skills_enabled: agent.skills_enabled === true,
    skills: resolvedSkills.map(({ id, name, upstreamId }) => ({ id, name, upstreamId })),
  };
  console.log(JSON.stringify(result, null, 2));
  return result;
}

async function disconnectMongoose({ throwOnInitFailure = true } = {}) {
  const mongoose = require('mongoose');
  const models = Object.values(mongoose.models || {});
  const initResults = await Promise.allSettled(
    models.map((model) => (typeof model.init === 'function' ? model.init() : Promise.resolve())),
  );

  await mongoose.disconnect();

  const initFailures = initResults
    .filter((result) => result.status === 'rejected')
    .map((result) => result.reason);

  if (throwOnInitFailure && initFailures.length > 0) {
    throw new AggregateError(
      initFailures,
      `${initFailures.length} Mongoose model initialization(s) failed before disconnect`,
    );
  }
}

if (require.main === module) {
  seed()
    .then(async () => {
      try {
        await disconnectMongoose();
        process.exit(0);
      } catch (error) {
        console.error(`Coding-agent pilot shutdown failed: ${error.message}`);
        process.exit(1);
      }
    })
    .catch(async (error) => {
      console.error(`Coding-agent pilot seed failed: ${error.message}`);
      await disconnectMongoose({ throwOnInitFailure: false }).catch(() => {});
      process.exit(1);
    });
}

module.exports = {
  seed,
  loadManifest,
  persistedToolIds,
  expectedSkillUpstreamId,
  validateManifestSkillPolicy,
  resolveSkillAllowlist,
  desiredAgent,
  validatePersistedAgent,
  parseAllowedModels,
  chooseModel,
  normalizeProvider,
  disconnectMongoose,
};
