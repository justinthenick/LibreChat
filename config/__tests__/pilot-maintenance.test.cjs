const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const test = typeof jest === 'undefined' ? require('node:test').test : globalThis.test;

const root = path.resolve(__dirname, '../..');
const manifest = JSON.parse(fs.readFileSync(path.join(root, 'custom/coding-agent/production/software-engineering-pilot.json')));
function seeder(value = manifest) {
  const module = { exports: {} };
  const imports = {
    fs: { ...fs, readFileSync: () => JSON.stringify(value) },
    path,
    'module-alias': () => {},
    'librechat-data-provider': {},
    './connect': () => {},
  };
  vm.runInNewContext(fs.readFileSync(path.join(root, 'config/seed-coding-agent-pilot.js'), 'utf8'), {
    require: (name) => { if (!(name in imports)) throw Error(name); return imports[name]; },
    module, __dirname: path.join(root, 'config'), process: { argv: [], env: {} }, console,
  });
  return module.exports;
}

test('reconciliation persists exactly seven maintenance tools alongside existing coding tools', () => {
  const api = seeder();
  api.loadManifest();
  const skills = [{ id: 'skill-id' }];
  const agent = api.desiredAgent(manifest, 'owner-id', skills);
  assert.equal(agent.tools.length, 16);
  assert.deepEqual(Array.from(agent.mcpServerNames), ['coding_executor', 'coding_maintenance']);
  assert.deepEqual(Array.from(agent.tools.filter((tool) => tool.endsWith('_mcp_coding_maintenance'))),
    ['executor_health', 'repository_status', 'task_inventory', 'executor_logs', 'fresh_repository_status', 'preview_cleanup', 'cleanup_task'].map((tool) => `${tool}_mcp_coding_maintenance`));
  api.validatePersistedAgent(agent, manifest, skills);
  agent.tools.push('restart_executor_mcp_coding_maintenance');
  assert.throws(() => api.validatePersistedAgent(agent, manifest, skills), /allowlist/);
});

test('manifest refuses maintenance wildcard, mutation and missing tool declarations', () => {
  for (const tools of [['*'], ['executor_health', 'restart_executor'], []]) {
    assert.throws(() => seeder({ ...manifest, maintenance_mcp_tools: tools }).loadManifest(), /seven constrained/);
  }
});

test('instructions prohibit maintenance worktrees and executor fallback', () => {
  assert.match(manifest.instructions, /Do not call create_task or any coding_executor tool/);
  assert.match(manifest.instructions, /report the integration failure and stop/);
  assert.doesNotMatch(manifest.instructions, /For every task, first list/);
});
