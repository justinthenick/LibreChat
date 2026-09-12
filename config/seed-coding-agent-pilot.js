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
  if (String(value || '').trim().toLowerCase() === 'openrouter') {
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
  return manifest;
}

async function resolveOwner(User) {
  const requestedEmail = String(process.env.PRODUCTION_AGENT_OWNER_EMAIL || '').trim().toLowerCase();
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
    console.warn(\n      `Multiple ADMIN users exist; assigning coding-agent pilot to the oldest admin (${admins[0]._id})`,\n    );
  }
  return admins[0];
}

function desiredAgent(manifest, author) {
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
    skills: [],
    skills_enabled: false,
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

function validatePersistedAgent(agent, manifest) {
  const expectedTools = persistedToolIds(manifest);
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
  if ((agent.skills || []).length !== 0 || agent.skills_enabled === true) {
    throw new Error(`${manifest.id} unexpectedly retained skills`);
  }
  if (agent.edges?.length || agent.subagents != null) {
    throw new Error(`${manifest.id} unexpectedly retained orchestration wiring`);
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

  let existing = await db.getAgent({ id: manifest.id });
  let adoptedManualAgent = false;
  if (!existing) {
    const sameName = await db.getAgents({ name: manifest.name, author: owner._id });
    if (sameName.length > 1) {
      throw new Error(\n      `Multiple admin-owned agents are named ${manifest.name}; refusing ambiguous adoption`,\n    );
    }
    existing = sameName[0] || null;
    adoptedManualAgent = Boolean(existing);
  }

  const ownerId = existing?.author?.toString() || defaultOwnerId;
  const desired = desiredAgent(manifest, ownerId);
  let agent;
  let outcome;
  if (existing) {
    const { author, ...updates } = desired;
    if (existing.id === manifest.id) {
      delete updates.id;
    }
    agent = await db.updateAgent(\n      { _id: existing._id },\n      updates,\n      { updatingUserId: ownerId },\n    );
    outcome = adoptedManualAgent ? 'adopted-and-updated' : 'updated';
  } else {
    agent = await db.createAgent(desired);
    outcome = 'created';
  }

  if (!agent) {
    throw new Error(`Seeder did not return ${manifest.id}`);
  }
  validatePersistedAgent(agent, manifest);
  await ensureOwnerPermissions({ grantPermission, agent, ownerId });

  const result = {
    ok: true,
    id: manifest.id,
    outcome,
    owner: ownerId,
    model: agent.model,
    mcpServerNames: sortedStrings(agent.mcpServerNames),
    tools: sortedStrings(agent.tools),
  };
  console.log(JSON.stringify(result, null, 2));
  return result;
}

if (require.main === module) {
  seed()
    .then(async () => {
      const mongoose = require('mongoose');
      await mongoose.disconnect();
      process.exit(0);
    })
    .catch(async (error) => {
      console.error(`Coding-agent pilot seed failed: ${error.message}`);
      try {
        const mongoose = require('mongoose');
        await mongoose.disconnect();
      } catch (_) {}
      process.exit(1);
    });
}

module.exports = {
  seed,
  loadManifest,
  persistedToolIds,
  desiredAgent,
  validatePersistedAgent,
  parseAllowedModels,
  chooseModel,
  normalizeProvider,
};
