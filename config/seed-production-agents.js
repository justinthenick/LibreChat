const fs = require('fs');
const path = require('path');

require('module-alias')({ base: path.resolve(__dirname, '..', 'api') });

const { initializeDeploymentSkills } = require('@librechat/api');
const {
  AccessRoleIds,
  ResourceType,
  PrincipalType,
  SystemRoles,
} = require('librechat-data-provider');
const connect = require('./connect');

const MANIFEST_DIR = process.argv[2] || process.env.PRODUCTION_AGENTS_DIR || '/app/production-agents';
const WORKFLOW_FILE =
  process.env.PRODUCTION_AGENT_WORKFLOW_FILE ||
  path.join(MANIFEST_DIR, 'workflows', 'ba-to-release-assurance.json');
const ALLOWED_MANIFESTS = ['ba-supervisor.json', 'release-change-assurance.json'];
const BA_AGENT_ID = 'agent_ba_supervisor_v01';
const RELEASE_AGENT_ID = 'agent_release_change_assurance_v01';
const EXPECTED_AGENT_IDS = new Set([BA_AGENT_ID, RELEASE_AGENT_ID]);
const ALLOWED_ARTIFACT_MODES = new Set(['default', 'code', 'artifacts']);
const OPENROUTER_ENDPOINT_NAME = 'OpenRouter';

function parseAllowedModels(raw) {
  return String(raw || '')
    .split(/[\r\n,]+/)
    .map((value) => value.trim())
    .filter(Boolean);
}

function chooseModel() {
  return parseAllowedModels(process.env.ALLOWED_MODELS)[0] || 'deepseek/deepseek-v3.2';
}

function normalizeProvider(value) {
  const normalized = String(value || '').trim().toLowerCase();
  if (normalized === 'openrouter') {
    // Agent.provider is an endpoint lookup key in the pinned LibreChat runtime.
    // Keep it aligned with the configured custom endpoint name so model
    // validation resolves modelsConfig.OpenRouter instead of modelsConfig.openrouter.
    return OPENROUTER_ENDPOINT_NAME;
  }
  throw new Error(`Unsupported production-agent provider: ${value}`);
}

function loadManifest(filename) {
  const fullPath = path.resolve(MANIFEST_DIR, filename);
  const root = path.resolve(MANIFEST_DIR) + path.sep;
  if (!fullPath.startsWith(root)) {
    throw new Error(`Manifest path escaped production directory: ${filename}`);
  }
  const manifest = JSON.parse(fs.readFileSync(fullPath, 'utf8'));
  if (!EXPECTED_AGENT_IDS.has(manifest.id)) {
    throw new Error(`Unexpected production agent id in ${filename}: ${manifest.id}`);
  }
  if (manifest.status !== 'validated-for-independent-use') {
    throw new Error(`${manifest.id} is not independently validated for production use`);
  }
  if (!Array.isArray(manifest.skills) || manifest.skills.length === 0) {
    throw new Error(`${manifest.id} has no bounded skill allowlist`);
  }
  if (!Array.isArray(manifest.tools)) {
    throw new Error(`${manifest.id} tools must be an array`);
  }
  if (!ALLOWED_ARTIFACT_MODES.has(manifest.artifacts)) {
    throw new Error(`${manifest.id} has unsupported artifact mode: ${manifest.artifacts}`);
  }
  return manifest;
}

function loadWorkflow() {
  const fullPath = path.resolve(WORKFLOW_FILE);
  const root = path.resolve(MANIFEST_DIR) + path.sep;
  if (!fullPath.startsWith(root)) {
    throw new Error(`Workflow path escaped production directory: ${WORKFLOW_FILE}`);
  }
  const workflow = JSON.parse(fs.readFileSync(fullPath, 'utf8'));
  if (workflow.status !== 'validated-for-production-activation' || workflow.enabled !== true) {
    throw new Error('BA to Release / Change Assurance workflow is not validated and enabled');
  }
  if (workflow.pattern !== 'conditional_handoff') {
    throw new Error(`Unsupported production workflow pattern: ${workflow.pattern}`);
  }
  if (workflow.from_agent !== BA_AGENT_ID || workflow.to_agent !== RELEASE_AGENT_ID) {
    throw new Error(
      `Unexpected production handoff ${workflow.from_agent} -> ${workflow.to_agent}`,
    );
  }
  return workflow;
}

function desiredEdges(manifestId, workflow) {
  if (manifestId !== workflow.from_agent) {
    return [];
  }
  return [
    {
      from: workflow.from_agent,
      to: workflow.to_agent,
      edgeType: 'handoff',
    },
  ];
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
    throw new Error('No ADMIN user exists; production agents cannot be given a safe owner');
  }
  if (admins.length > 1) {
    console.warn(`Multiple ADMIN users exist; assigning production agents to the oldest admin (${admins[0]._id})`);
  }
  return admins[0];
}

function desiredAgent(manifest, author, workflow) {
  const skillIds = manifest.skills.map((skill) => String(skill.id));
  return {
    id: manifest.id,
    name: manifest.name,
    description: manifest.description,
    instructions: manifest.instructions,
    provider: normalizeProvider(manifest.provider),
    model: chooseModel(),
    model_parameters: {},
    tools: manifest.tools.map(String),
    skills: skillIds,
    skills_enabled: manifest.skills_enabled === true,
    memory_scope: manifest.memory_scope || 'agent',
    artifacts: manifest.artifacts,
    edges: desiredEdges(manifest.id, workflow),
    conversation_starters: Array.isArray(manifest.conversation_starters)
      ? manifest.conversation_starters.map(String)
      : [],
    category: manifest.id === BA_AGENT_ID ? 'business-analysis' : 'release-assurance',
    author,
  };
}

function normalizePersistedEdges(agent) {
  return (agent.edges || []).map((edge) => ({
    from: String(edge.from || ''),
    to: String(edge.to || ''),
    edgeType: String(edge.edgeType || ''),
  }));
}

async function ensureOwnerPermissions({ grantPermission, agent, ownerId }) {
  const resourceId = agent._id;
  await grantPermission({
    principalType: PrincipalType.USER,
    principalId: ownerId,
    resourceType: ResourceType.AGENT,
    resourceId,
    accessRoleId: AccessRoleIds.AGENT_OWNER,
    grantedBy: ownerId,
  });
  await grantPermission({
    principalType: PrincipalType.USER,
    principalId: ownerId,
    resourceType: ResourceType.REMOTE_AGENT,
    resourceId,
    accessRoleId: AccessRoleIds.REMOTE_AGENT_OWNER,
    grantedBy: ownerId,
  });
}

async function seed() {
  if (!fs.existsSync(MANIFEST_DIR)) {
    throw new Error(`Production agent manifest directory not found: ${MANIFEST_DIR}`);
  }

  const workflow = loadWorkflow();
  await initializeDeploymentSkills({ projectRoot: path.resolve(__dirname, '..') });
  await connect();

  const db = require('~/models');
  const { User } = require('~/db/models');
  const { grantPermission } = require('~/server/services/PermissionService');
  const owner = await resolveOwner(User);
  const defaultOwnerId = owner._id.toString();

  const results = [];
  for (const filename of ALLOWED_MANIFESTS) {
    const manifest = loadManifest(filename);
    const existing = await db.getAgent({ id: manifest.id });
    const ownerId = existing?.author?.toString() || defaultOwnerId;
    const desired = desiredAgent(manifest, ownerId, workflow);

    let agent;
    let outcome;
    if (existing) {
      const { id, author, ...updates } = desired;
      agent = await db.updateAgent(
        { id },
        updates,
        { updatingUserId: ownerId },
      );
      outcome = 'updated';
    } else {
      agent = await db.createAgent(desired);
      outcome = 'created';
    }

    if (!agent) {
      throw new Error(`Seeder did not return ${manifest.id}`);
    }
    const expectedSkills = manifest.skills.map((skill) => String(skill.id)).sort();
    const persistedSkills = (agent.skills || []).map(String).sort();
    if (
      agent.skills_enabled !== true ||
      expectedSkills.length !== persistedSkills.length ||
      expectedSkills.some((id, index) => id !== persistedSkills[index])
    ) {
      throw new Error(`${manifest.id} skill allowlist was pruned or widened; refusing production seed`);
    }
    for (const tool of ['file_search', 'execute_code', 'web_search']) {
      if (!agent.tools?.includes(tool)) {
        throw new Error(`${manifest.id} is missing required tool ${tool}`);
      }
    }
    if (agent.memory_scope !== 'agent') {
      throw new Error(`${manifest.id} did not retain isolated agent memory scope`);
    }
    if (agent.artifacts !== manifest.artifacts) {
      throw new Error(`${manifest.id} did not retain artifact mode ${manifest.artifacts}`);
    }

    const expectedEdges = desiredEdges(manifest.id, workflow);
    const persistedEdges = normalizePersistedEdges(agent);
    if (JSON.stringify(persistedEdges) !== JSON.stringify(expectedEdges)) {
      throw new Error(
        `${manifest.id} handoff edges differ from validated production workflow; refusing production seed`,
      );
    }

    await ensureOwnerPermissions({ grantPermission, agent, ownerId });
    results.push({
      id: manifest.id,
      outcome,
      owner: ownerId,
      model: agent.model,
      artifacts: agent.artifacts,
      edges: persistedEdges,
    });
  }

  console.log(JSON.stringify({ ok: true, workflow: workflow.id, agents: results }, null, 2));
  return results;
}

if (require.main === module) {
  seed()
    .then(async () => {
      const mongoose = require('mongoose');
      await mongoose.disconnect();
      process.exit(0);
    })
    .catch(async (error) => {
      console.error(`Production agent seed failed: ${error.message}`);
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
  loadWorkflow,
  desiredEdges,
  desiredAgent,
  parseAllowedModels,
  chooseModel,
  normalizeProvider,
};
