const assert = require('node:assert/strict');
const { test, beforeEach, afterEach } = require('node:test');
const { fork, execFileSync } = require('node:child_process');
const { once } = require('node:events');
const { randomUUID } = require('node:crypto');
const fs = require('node:fs/promises');
const path = require('node:path');
const os = require('node:os');
let dir, children;
const request = {
  repository: 'fixture',
  base: 'a'.repeat(40),
  head: 'b'.repeat(40),
  pullRequest: { number: 7, repositoryId: 123 },
};
const principal = { userId: 'alice', tenantId: 'tenant-a' };
async function exists(name) {
  try {
    await fs.stat(path.join(dir, name));
    return true;
  } catch {
    return false;
  }
}
async function until(check) {
  for (let i = 0; i < 1000; i++) {
    if (await check()) return;
    await new Promise((resolve) => setTimeout(resolve, 10));
  }
  throw new Error('Restart fixture timed out');
}
async function launch(mode = '') {
  const child = fork(path.join(__dirname, 'restart-service.cjs'), [dir, mode], {
    stdio: ['ignore', 'pipe', 'pipe', 'ipc'],
    env: {
      PATH: '/usr/bin:/bin',
      HOME: path.join(dir, 'empty-auth'),
      NODE_ENV: 'test',
      NODE_OPTIONS: process.env.NODE_OPTIONS,
    },
  });
  children.push(child);
  let stderr = '';
  child.stderr.on('data', (chunk) => {
    stderr += chunk;
  });
  const ready = await Promise.race([
    once(child, 'message').then(([value]) => value),
    once(child, 'exit').then(([code]) => {
      throw new Error(`Fixture exited ${code}: ${stderr}`);
    }),
  ]);
  child.helper = ready.helper;
  return { ...ready, child };
}
async function stop(service) {
  if (service.child.exitCode === null && service.child.signalCode === null) {
    const done = once(service.child, 'exit');
    service.child.kill('SIGKILL');
    await done;
  }
  if (service.helper)
    await until(async () => {
      try {
        const state = await fs.readFile(`/proc/${service.helper}/stat`, 'utf8');
        return state.split(' ')[2] === 'Z';
      } catch {
        return true;
      }
    });
}
async function post(service, route, body, runId) {
  return fetch(service.url + route, {
    method: 'POST',
    headers: {
      authorization: 'Bearer offline-review-service-token-fixture',
      'content-type': 'application/json',
      ...(runId ? { 'x-review-id': runId } : {}),
    },
    body: JSON.stringify(body),
  });
}
const start = (service, id, selected = request, owner = principal) =>
  post(service, '', { request: selected, principal: owner }, id);
const status = (service, id, selected = request, owner = principal) =>
  post(service, '/status', { id, request: selected, principal: owner });
const cancel = (service, id, owner = principal) =>
  post(service, '/cancel', { id, principal: owner });
async function count() {
  return (await exists('dispatches'))
    ? (await fs.readFile(path.join(dir, 'dispatches'), 'utf8')).trim().split('\n').length
    : 0;
}
beforeEach(async () => {
  children = [];
  dir = await fs.mkdtemp(path.join(os.tmpdir(), 'review-restart-'));
  for (const name of ['repository', 'scratch', 'empty-auth'])
    await fs.mkdir(path.join(dir, name), { mode: 0o700 });
  await fs.writeFile(
    path.join(dir, 'worker-python'),
    `#!/usr/bin/python3
import json, os, sys, time
from pathlib import Path
root=Path(__file__).parent
with (root/'dispatches').open('a') as f: f.write(str(os.getpid())+'\\n')
while (root/'hold').exists(): time.sleep(.01)
print(json.dumps({'ok':True,'mode':'review','base':sys.argv[sys.argv.index('--base')+1],'head':sys.argv[sys.argv.index('--head')+1],'status':'human_review_required','provider':'chatgpt_subscription','model':'fixture-model','finding_count':0,'findings':[]}))
`,
    { mode: 0o700 },
  );
});
afterEach(async () => {
  for (const child of children) {
    if (child.exitCode === null && child.signalCode === null) {
      const done = once(child, 'exit');
      child.kill('SIGKILL');
      await done;
    }
    if (child.helper)
      await until(async () => {
        try {
          const state = await fs.readFile(`/proc/${child.helper}/stat`, 'utf8');
          return state.split(' ')[2] === 'Z';
        } catch {
          return true;
        }
      });
  }
  if (await exists('dispatches'))
    for (const pid of (await fs.readFile(path.join(dir, 'dispatches'), 'utf8'))
      .trim()
      .split('\n')) {
      try {
        const command = await fs.readFile(`/proc/${pid}/cmdline`, 'utf8');
        assert.ok(command.includes(path.join(dir, 'worker-python')));
        process.kill(-Number(pid), 'SIGKILL');
      } catch (error) {
        if (error.code !== 'ENOENT' && error.code !== 'ESRCH') throw error;
      }
    }
  assert.deepEqual(await fs.readdir(path.join(dir, 'empty-auth')), []);
  await fs.rm(dir, { recursive: true, force: true });
});
test('restart: settled result retains owner, exact PR identity and model without redispatch', async () => {
  let service = await launch();
  const id = randomUUID();
  assert.equal((await start(service, id)).status, 200);
  assert.equal(await count(), 1);
  assert.deepEqual(await fs.readdir(path.join(dir, 'scratch')), []);
  await stop(service);
  service = await launch();
  const recovered = await (await status(service, id)).json();
  assert.equal(recovered.state, 'completed');
  assert.deepEqual(recovered.request, request);
  assert.deepEqual(recovered.result.pullRequest, request.pullRequest);
  assert.equal(
    (await (await status(service, id, request, { userId: 'bob', tenantId: 'tenant-a' })).json())
      .state,
    'unknown',
  );
  assert.equal(
    (await (await status(service, id, request, { userId: 'alice', tenantId: 'tenant-b' })).json())
      .state,
    'unknown',
  );
  assert.equal(
    (await status(service, id, { ...request, pullRequest: { number: 8, repositoryId: 123 } }))
      .status,
    400,
  );
  assert.equal((await start(service, id)).status, 409);
  assert.equal(await count(), 1);
  await stop(service);
  service = await launch('wrong-model');
  assert.equal((await status(service, id)).status, 503);
  assert.equal((await start(service, id)).status, 400);
  assert.equal(await count(), 1);
});
test('restart: an orphaned execution remains explicit and quarantines all new dispatch', async () => {
  let service = await launch();
  const id = randomUUID();
  await fs.writeFile(path.join(dir, 'hold'), '');
  const pending = start(service, id).catch(() => undefined);
  await until(async () => (await count()) === 1);
  await stop(service);
  await pending;
  service = await launch();
  assert.equal((await (await status(service, id)).json()).state, 'interrupted');
  assert.equal((await start(service, id)).status, 409);
  assert.equal((await start(service, randomUUID())).status, 409);
  assert.equal((await cancel(service, id, { userId: 'bob', tenantId: 'tenant-a' })).status, 403);
  assert.equal((await cancel(service, id)).status, 200);
  await stop(service);
  service = await launch();
  const record = await (await status(service, id)).json();
  assert.equal(record.state, 'interrupted');
  assert.equal(record.cancelRequested, true);
  assert.equal(await count(), 1);
});
test('restart: cancellation before admission persists without taking the execution slot', async () => {
  let service = await launch();
  const id = randomUUID();
  assert.equal((await cancel(service, id)).status, 200);
  await stop(service);
  service = await launch();
  assert.equal((await start(service, id)).status, 499);
  assert.equal(await count(), 0);
  assert.equal((await start(service, randomUUID())).status, 200);
  assert.equal(await count(), 1);
});
test('helper loss: delayed authorization in old service cannot dispatch after a new service starts', async () => {
  await fs.writeFile(path.join(dir, 'auth-hold'), '');
  const old = await launch('authorization');
  const id = randomUUID();
  const pending = start(old, id);
  await until(() => exists('authorizing'));
  process.kill(old.helper, 'SIGKILL');
  await until(async () => {
    try {
      const s = await fs.readFile(`/proc/${old.helper}/stat`, 'utf8');
      return s.split(' ')[2] === 'Z';
    } catch {
      return true;
    }
  });
  const fresh = await launch();
  assert.equal((await start(fresh, id)).status, 200);
  await fs.rm(path.join(dir, 'auth-hold'));
  assert.notEqual((await pending).status, 200);
  assert.equal((await start(old, randomUUID())).status, 503);
  assert.equal(await count(), 1);
});
test('retention: expired findings are removed while original ID remains non-dispatchable', async () => {
  let service = await launch();
  const id = randomUUID();
  assert.equal((await start(service, id)).status, 200);
  execFileSync('/usr/bin/python3', [
    '-c',
    "import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); c.execute('UPDATE jobs SET updated_at=1'); c.commit()",
    path.join(dir, 'private/reviews.sqlite'),
  ]);
  assert.equal((await (await status(service, id)).json()).state, 'unknown');
  assert.equal((await start(service, id)).status, 409);
  await stop(service);
  service = await launch();
  assert.equal((await (await status(service, id)).json()).state, 'unknown');
  assert.equal((await start(service, id)).status, 409);
  assert.equal(await count(), 1);
  const stored = execFileSync(
    '/usr/bin/python3',
    [
      '-c',
      "import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); print(c.execute('SELECT result IS NULL, request IS NOT NULL FROM jobs').fetchone())",
      path.join(dir, 'private/reviews.sqlite'),
    ],
    { encoding: 'utf8' },
  ).trim();
  assert.equal(stored, '(1, 1)');
});
for (const boundary of ['admit', 'finish'])
  test(`restart: crash after ${boundary} commit but before acknowledgement never replays`, async () => {
    await fs.writeFile(
      path.join(dir, 'journal-python'),
      `#!/usr/bin/python3
import runpy, sys, time
from pathlib import Path
root=Path(__file__).parent
script=sys.argv[4]; database=sys.argv[5]
sys.path.insert(0,str(Path(script).parent))
sys.argv=[script,database]
module=runpy.run_path(script,run_name='fixture_journal')
emit=module['emit']
def gated(value):
    if value.get('sequence') == ${boundary === 'admit' ? 1 : 2}:
        (root/'committed').write_text('')
        while True: time.sleep(.01)
    emit(value)
module['main'].__globals__['emit']=gated
raise SystemExit(module['main']())
`,
      { mode: 0o700 },
    );
    let service = await launch(`${boundary}-ack`);
    const id = randomUUID();
    const pending = start(service, id).catch(() => undefined);
    await until(() => exists('committed'));
    process.kill(service.helper, 'SIGKILL');
    await stop(service);
    await pending;
    const expectedCount = boundary === 'admit' ? 0 : 1;
    assert.equal(await count(), expectedCount);
    service = await launch();
    assert.equal(
      (await (await status(service, id)).json()).state,
      boundary === 'admit' ? 'interrupted' : 'completed',
    );
    assert.equal((await start(service, id)).status, 409);
    assert.equal(await count(), expectedCount);
    if (boundary === 'admit') assert.equal((await start(service, randomUUID())).status, 409);
  });
test('locking: a competing service fails closed without disturbing the lock owner', async () => {
  const service = await launch();
  await assert.rejects(launch(), /Fixture exited 1/);
  assert.equal((await start(service, randomUUID())).status, 200);
  assert.equal(await count(), 1);
});

test('cancel race: cancellation before successful finish withholds findings and releases settled execution', async () => {
  let service = await launch('cancel-before-finish');
  const id = randomUUID();
  assert.equal((await start(service, id)).status, 499);
  let record = await (await status(service, id)).json();
  assert.equal(record.state, 'failed');
  assert.equal(record.code, 'cancelled');
  assert.equal(record.result, undefined);
  assert.equal(await count(), 1);
  await stop(service);
  service = await launch();
  record = await (await status(service, id)).json();
  assert.equal(record.state, 'failed');
  assert.equal(record.code, 'cancelled');
  assert.equal(record.result, undefined);
  assert.equal((await start(service, id)).status, 499);
  assert.equal(await count(), 1);
  assert.equal((await start(service, randomUUID())).status, 200);
  assert.equal(await count(), 2);
});
