/* Offline HTTP contract tests. JWT cryptography is intentionally out of scope:
 * the existing authentication middleware is stubbed to install known principals.
 * The Express router, compiled controller, dispatcher, store, service and worker
 * are real. No model, credentials, provider, or repository contents are involved.
 */
const { spawn } = require('node:child_process');
const { createHash } = require('node:crypto');
const { once } = require('node:events');
const fs = require('node:fs/promises');
const http = require('node:http');
const os = require('node:os');
const path = require('node:path');
const express = require('express');
const supertest = require('supertest');

if (!process.env.PREVIEW_TEST_PYTHON || !process.env.PREVIEW_TEST_BUILD) {
  throw new Error(
    'Set PREVIEW_TEST_PYTHON and PREVIEW_TEST_BUILD to the approved fixture toolchain.',
  );
}
const ROOT = path.resolve(__dirname, '../../../../..');
const AGENTS = path.join(ROOT, 'api/server/routes/agents');
const ROUTE = path.join(AGENTS, 'preview.js');
jest.doMock(
  '@librechat/api/coding',
  () => jest.requireActual(path.join(process.env.PREVIEW_TEST_BUILD, 'controller.js')),
  { virtual: true },
);
delete process.env.CODING_OPENHANDS_PREVIEW;
const defaultRouter = require(ROUTE);
const { createPreviewRouter } = defaultRouter;
jest.setTimeout(20000);

const OWNER = Object.freeze({ user_id: 'owner', tenant_id: 'tenant' });
const TOKENS = Object.freeze({
  'Bearer owner': { id: 'owner', tenantId: 'tenant' },
  'Bearer other': { id: 'other', tenantId: 'tenant' },
  'Bearer other-tenant': { id: 'owner', tenantId: 'other-tenant' },
  'Bearer no-tenant': { id: 'owner' },
});
const cleanups = [];
let testServer;
let selectedApp;
// Each request is awaited before selecting another app. Supplying an already
// listening server prevents Supertest from opening its default wildcard socket.
function request(app) {
  selectedApp = app;
  return supertest(testServer);
}
const pause = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
function deferred() {
  let resolve;
  let reject;
  const promise = new Promise((yes, no) => {
    resolve = yes;
    reject = no;
  });
  return { promise, resolve, reject };
}
function startBody(changes = {}) {
  return {
    prompt: 'wait',
    idempotency_key: 'request-1',
    scope: { repository_alias: 'fixture', task_mode: 'read_only' },
    timeout_seconds: 10,
    ...changes,
  };
}
function failure(response, status, code) {
  expect(response.status).toBe(status);
  expect(response.body).toEqual({ version: 1, ok: false, error: code });
}
function authenticate(req, res, next) {
  const principal = TOKENS[req.get('authorization')];
  if (!principal) return res.status(401).json({ error: 'fixture_auth_required' });
  req.user = { ...principal };
  next();
}
function appFor(options = {}, router = createPreviewRouter(options)) {
  const app = express();
  // Real Express JSON decoding; the controller independently checks its input.
  app.use(express.json({ limit: 40960 }));
  app.use(authenticate);
  app.use('/api/agents/preview', router);
  app.use((error, _req, res, _next) => {
    res
      .status(error.status === 413 ? 413 : 400)
      .json({ version: 1, ok: false, error: 'invalid_job_message' });
  });
  return app;
}
function call(app, method, suffix = '/jobs', token = 'owner') {
  return request(app)
    [method](`/api/agents/preview${suffix}`)
    .set('Authorization', `Bearer ${token}`);
}
function configured(fixture, overrides = {}) {
  return {
    enabled: true,
    transport: fixture.transport,
    authorize: jest.fn(async () => true),
    ...overrides,
  };
}

class PythonFixture {
  static async create({ unconfirmedStop = false } = {}) {
    const directory = await fs.mkdtemp(path.join(os.tmpdir(), 'preview-http-test-'));
    const child = spawn(
      process.env.PREVIEW_TEST_PYTHON,
      [
        '-B',
        path.join(__dirname, 'fixture.py'),
        ...(unconfirmedStop ? ['--unconfirmed-stop'] : []),
      ],
      {
        cwd: directory,
        // Do not inherit tokens, provider configuration, home files or proxies.
        env: {
          HOME: directory,
          TMPDIR: directory,
          LANG: 'C.UTF-8',
          PYTHONDONTWRITEBYTECODE: '1',
          PYTHON_DOTENV_DISABLED: '1',
          PYTHONPATH: [path.resolve(__dirname, '../../src'), __dirname].join(path.delimiter),
        },
        stdio: ['pipe', 'pipe', 'pipe'],
      },
    );
    const fixture = new PythonFixture(child, directory);
    cleanups.push(() => fixture.close());
    let startupTimer;
    try {
      await Promise.race([
        fixture.ready.promise,
        new Promise((_resolve, reject) => {
          startupTimer = setTimeout(
            () => reject(new Error('Fixture startup deadline exceeded')),
            5000,
          );
        }),
      ]);
    } finally {
      clearTimeout(startupTimer);
    }
    return fixture;
  }

  constructor(child, directory) {
    this.child = child;
    this.directory = directory;
    this.ready = deferred();
    this.buffer = Buffer.alloc(0);
    this.stderr = '';
    this.sequence = Promise.resolve();
    this.pending = null;
    this.transport = { exchange: jest.fn((message) => this.exchange(message)) };
    const fail = (error) => {
      this.ready.reject(error);
      this.pending?.reject(error);
      this.pending = null;
    };
    this.exited = new Promise((resolve) => {
      child.once('error', (error) => {
        fail(error);
        resolve({ error });
      });
      child.once('exit', (code, signal) => {
        fail(new Error(`Fixture exited (${code ?? signal}): ${this.stderr}`));
        resolve({ code, signal });
      });
    });
    child.stdin.on('error', fail);
    child.stderr.on('data', (chunk) => {
      this.stderr = (this.stderr + chunk).slice(0, 8192);
    });
    child.stdout.on('data', (chunk) => {
      this.buffer = Buffer.concat([this.buffer, chunk]);
      if (this.buffer.length > 262145) return fail(new Error('Fixture reply exceeds bound'));
      let newline;
      while ((newline = this.buffer.indexOf(10)) !== -1) {
        const line = this.buffer.subarray(0, newline);
        this.buffer = this.buffer.subarray(newline + 1);
        try {
          const value = JSON.parse(line.toString('utf8'));
          if (value.ready === true) this.ready.resolve();
          else if (this.pending) {
            const pending = this.pending;
            this.pending = null;
            pending.resolve(value);
          } else fail(new Error('Unsolicited fixture reply'));
        } catch (error) {
          fail(error);
        }
      }
    });
  }

  rpc(message) {
    const operation = this.sequence.then(async () => {
      await this.ready.promise;
      const encoded = `${JSON.stringify(message)}\n`;
      if (Buffer.byteLength(encoded) > 49152) throw new Error('Fixture request exceeds bound');
      const pending = deferred();
      this.pending = pending;
      const timer = setTimeout(
        () => pending.reject(new Error('Fixture response deadline exceeded')),
        5000,
      );
      try {
        this.child.stdin.write(encoded, (error) => {
          if (error) pending.reject(error);
        });
        return await pending.promise;
      } finally {
        clearTimeout(timer);
      }
    });
    this.sequence = operation.catch(() => {});
    return operation;
  }

  exchange({ principal, payload }) {
    return this.rpc({ command: 'exchange', principal, payload });
  }
  inspect() {
    return this.rpc({ command: 'inspect' });
  }

  async close() {
    await this.sequence;
    if (this.child.exitCode === null && this.child.signalCode === null) {
      this.child.stdin.end(`${JSON.stringify({ command: 'shutdown' })}\n`);
    }
    const waitForExit = async (milliseconds) => {
      let timer;
      try {
        return await Promise.race([
          this.exited,
          new Promise((resolve) => {
            timer = setTimeout(() => resolve(null), milliseconds);
          }),
        ]);
      } finally {
        clearTimeout(timer);
      }
    };
    const result = await waitForExit(5000);
    if (result === null) {
      this.child.kill('SIGTERM');
      if ((await waitForExit(2000)) === null) {
        this.child.kill('SIGKILL');
        await waitForExit(2000);
      }
      throw new Error('Fixture did not shut down gracefully');
    }
    await fs.rm(this.directory, { recursive: true, force: true });
    expect(result).toEqual({ code: 0, signal: null });
  }
}

beforeEach(async () => {
  testServer = http.createServer((req, res) => selectedApp(req, res));
  testServer.listen(0, '127.0.0.1');
  await once(testServer, 'listening');
  expect(testServer.address().address).toBe('127.0.0.1');
  const server = testServer;
  cleanups.push(
    () =>
      new Promise((resolve, reject) => {
        server.close((error) => (error ? reject(error) : resolve()));
        server.closeAllConnections();
      }),
  );
});

afterEach(async () => {
  const errors = [];
  while (cleanups.length) {
    try {
      await cleanups.pop()();
    } catch (error) {
      errors.push(error);
    }
  }
  if (errors.length) throw new AggregateError(errors, 'Preview fixture cleanup failed');
});

async function waitJob(
  app,
  jobId,
  predicate = (job) => !['queued', 'running', 'cancelling'].includes(job.state),
) {
  const deadline = Date.now() + 4000;
  while (Date.now() < deadline) {
    const response = await call(app, 'get', `/jobs/${jobId}`);
    expect(response.status).toBe(200);
    if (predicate(response.body.job)) return response.body.job;
    await pause(20);
  }
  throw new Error('Synthetic job did not reach the expected state');
}

test('the actual exported default route stays disabled and never dispatches', async () => {
  failure(
    await call(appFor({}, defaultRouter), 'post').send(startBody()),
    404,
    'preview_jobs_disabled',
  );
  const transport = { exchange: jest.fn() };
  const app = appFor({ transport, authorize: jest.fn(async () => true) });
  for (const [method, suffix] of [
    ['post', '/jobs'],
    ['get', `/jobs/${'a'.repeat(32)}`],
    ['post', `/jobs/${'a'.repeat(32)}/cancel`],
    ['post', `/jobs/${'a'.repeat(32)}/resume`],
  ]) {
    failure(
      await call(app, method, suffix).send(method === 'post' ? startBody() : undefined),
      404,
      'preview_jobs_disabled',
    );
  }
  expect(transport.exchange).not.toHaveBeenCalled();
});

test('enabled but unconfigured routes fail closed before transport', async () => {
  const transport = { exchange: jest.fn() };
  for (const options of [
    { enabled: true },
    { enabled: true, transport },
    { enabled: true, authorize: async () => true },
    { enabled: true, transport, authorize: async () => true, timeoutMs: 0 },
  ]) {
    failure(await call(appFor(options), 'post').send(startBody()), 503, 'job_service_unavailable');
  }
  expect(transport.exchange).not.toHaveBeenCalled();
});

test('the actual agents mount runs authentication, ban and user-agent gates before preview', async () => {
  const trace = [];
  const pass = (_req, _res, next) => next();
  const emptyRouter = () => express.Router();
  const steer = Object.assign(pass, {
    SteerDeliveryController: pass,
    SteerCancelController: pass,
    SteerArmController: pass,
  });
  jest.doMock(
    '@librechat/api',
    () => ({
      isEnabled: () => false,
      createMessageFilterPii: () => pass,
      isAgentTriggerRequest: () => false,
      captureScheduleFireContext: () => trace.push('capture'),
    }),
    { virtual: true },
  );
  jest.doMock('@librechat/api/telemetry', () => ({}), { virtual: true });
  jest.doMock(
    '@librechat/data-schemas',
    () => ({ logger: { debug() {}, error() {}, warn() {} } }),
    { virtual: true },
  );
  jest.doMock(
    '~/server/middleware',
    () => ({
      requireJwtAuth(req, res, next) {
        trace.push('jwt');
        authenticate(req, res, next);
      },
      checkBan(req, res, next) {
        trace.push('ban');
        if (req.get('x-fixture-banned')) return res.status(403).json({ error: 'fixture_banned' });
        next();
      },
      uaParser(_req, _res, next) {
        trace.push('ua');
        next();
      },
      moderateText: pass,
      configMiddleware: pass,
      messageIpLimiter: pass,
      messageUserLimiter: pass,
    }),
    { virtual: true },
  );
  jest.doMock('~/server/controllers/agents/steer', () => steer, {
    virtual: true,
  });
  jest.doMock('~/server/controllers/agents/protocol', () => ({}), {
    virtual: true,
  });
  jest.doMock('~/models', () => ({}), { virtual: true });
  jest.doMock('~/server/services/Schedules', () => ({}), { virtual: true });
  for (const sibling of ['responses', 'openai', 'chat']) {
    jest.doMock(path.join(AGENTS, sibling), emptyRouter, { virtual: true });
  }
  jest.doMock(path.join(AGENTS, 'v1'), () => ({ v1: emptyRouter() }), {
    virtual: true,
  });
  let agents;
  jest.isolateModules(() => {
    agents = require(path.join(AGENTS, 'index.js'));
  });
  const app = express();
  app.use(express.json());
  app.use('/api/agents', agents);
  expect((await request(app).post('/api/agents/preview/jobs').send(startBody())).status).toBe(401);
  expect(trace.splice(0)).toEqual(['jwt']);
  expect((await call(app, 'post').set('x-fixture-banned', 'yes').send(startBody())).status).toBe(
    403,
  );
  expect(trace.splice(0)).toEqual(['jwt', 'capture', 'ban']);
  failure(await call(app, 'post').send(startBody()), 404, 'preview_jobs_disabled');
  expect(trace.splice(0)).toEqual(['jwt', 'capture', 'ban', 'ua']);
});

test('only the authenticated server principal reaches Python; body identity cannot override it', async () => {
  const fixture = await PythonFixture.create();
  const app = appFor(configured(fixture));
  for (const spoof of [
    { user: { id: 'other' } },
    { user_id: 'other' },
    { tenant_id: 'other-tenant' },
    { principal: { user_id: 'other', tenant_id: 'tenant' } },
  ]) {
    failure(await call(app, 'post').send(startBody(spoof)), 400, 'invalid_job_message');
  }
  expect(
    (
      await request(app)
        .post('/api/agents/preview/jobs')
        .send(startBody({ user: TOKENS['Bearer owner'] }))
    ).status,
  ).toBe(401);
  const started = await call(app, 'post').send(startBody());
  expect(started.status).toBe(200);
  const inspection = await fixture.inspect();
  expect(inspection.principals).toEqual([OWNER]);
  expect(inspection.worker_starts).toBe(1);
  expect(inspection.store_mode).toBe(0o600);
  expect(started.body.job).not.toHaveProperty('user_id');
  expect(started.body.job).not.toHaveProperty('tenant_id');
});

test('owner and tenant isolation applies to reads and cancellation', async () => {
  const fixture = await PythonFixture.create();
  const app = appFor(configured(fixture));
  const {
    body: { job },
  } = await call(app, 'post').send(startBody());
  for (const token of ['other', 'other-tenant', 'no-tenant']) {
    failure(await call(app, 'get', `/jobs/${job.job_id}`, token), 404, 'job_not_found');
    failure(
      await call(app, 'post', `/jobs/${job.job_id}/cancel`, token).send({}),
      404,
      'job_not_found',
    );
  }
  expect((await fixture.inspect()).cancel_calls).toBe(0);
  expect((await call(app, 'get', `/jobs/${job.job_id}`)).body.job.state).toBe('running');
});

test('Node admission and Python scope admission reject work before a worker starts', async () => {
  const fixture = await PythonFixture.create();
  const authorize = jest.fn(async () => false);
  failure(
    await call(appFor(configured(fixture, { authorize })), 'post').send(startBody()),
    403,
    'scope_not_authorized',
  );
  expect(fixture.transport.exchange).not.toHaveBeenCalled();
  expect(authorize).toHaveBeenCalledWith(
    OWNER,
    { repository_alias: 'fixture', task_mode: 'read_only' },
    { operation: 'start', request: { ...startBody(), max_requests: 10 } },
  );
  const app = appFor(configured(fixture));
  failure(
    await call(app, 'post').send(
      startBody({
        scope: { repository_alias: 'forbidden', task_mode: 'read_only' },
      }),
    ),
    403,
    'scope_not_authorized',
  );
  expect((await fixture.inspect()).worker_starts).toBe(0);
  const {
    body: { job },
  } = await call(app, 'post').send(startBody());
  const deniedApp = appFor(configured(fixture, { authorize }));
  failure(await call(deniedApp, 'get', `/jobs/${job.job_id}`), 403, 'scope_not_authorized');
  failure(
    await call(deniedApp, 'post', `/jobs/${job.job_id}/cancel`).send({}),
    403,
    'scope_not_authorized',
  );
  expect((await fixture.inspect()).cancel_calls).toBe(0);
});

test('idempotent starts execute once; changed payload and overlapping work conflict', async () => {
  const fixture = await PythonFixture.create();
  const authorize = jest.fn(async () => true);
  const app = appFor(configured(fixture, { authorize }));
  const first = await call(app, 'post').send(startBody());
  const repeated = await call(app, 'post').send(startBody());
  expect(first.status).toBe(200);
  expect(repeated.body.job.job_id).toBe(first.body.job.job_id);
  expect(first.body.job.generation_id).toBe(
    `preview:${createHash('sha256').update('request-1').digest('hex')}`,
  );
  expect(first.body.job.generation_epoch).toBe(0);
  failure(
    await call(app, 'post').send(startBody({ prompt: 'finish' })),
    409,
    'idempotency_conflict',
  );
  failure(
    await call(app, 'post').send(startBody({ idempotency_key: 'request-2' })),
    409,
    'job_busy',
  );
  authorize.mockResolvedValue(false);
  const dispatches = fixture.transport.exchange.mock.calls.length;
  failure(await call(app, 'post').send(startBody()), 403, 'scope_not_authorized');
  expect(fixture.transport.exchange).toHaveBeenCalledTimes(dispatches);
  expect((await fixture.inspect()).worker_starts).toBe(1);
});

test('real process completion preserves bounded evidence and zero model requests', async () => {
  const fixture = await PythonFixture.create();
  const app = appFor(configured(fixture));
  const started = await call(app, 'post').send(startBody({ prompt: 'finish' }));
  expect(started.status).toBe(200);
  const job = await waitJob(app, started.body.job.job_id);
  expect(job.state).toBe('completed');
  expect(job.request_count).toBe(0);
  expect(job.result).toEqual({
    execution_status: 'finished',
    final_response: 'Synthetic fixture finished.',
    evidence: {
      repository_alias: 'fixture',
      task: null,
      checks: [],
      final_diff: null,
      final_status: null,
      observed_checks_status: 'not_run',
      evidence_complete: false,
      action_count: 0,
      pending_count: 0,
      errors: [],
    },
  });
  const repeated = await call(app, 'post').send(startBody({ prompt: 'finish' }));
  expect(repeated.body.job).toEqual(job);
  expect((await fixture.inspect()).worker_starts).toBe(1);
});

test('nonempty real collector evidence survives the worker, service and HTTP boundary', async () => {
  const fixture = await PythonFixture.create();
  const app = appFor(configured(fixture));
  const started = await call(app, 'post').send(
    startBody({
      prompt: 'finish-evidence',
      scope: { repository_alias: 'fixture', task_mode: 'modification' },
    }),
  );
  expect(started.status).toBe(200);
  const job = await waitJob(app, started.body.job.job_id);
  const taskId = 'http-fixture-1234abcd';
  const branch = `agent/${taskId}`;
  const diff = 'diff --git a/example.py b/example.py\n+fixture\n';
  const sha256 = (text) => createHash('sha256').update(text).digest('hex');
  expect(job.state).toBe('completed');
  expect(job.request_count).toBe(0);
  expect(job.result.evidence).toEqual({
    repository_alias: 'fixture',
    task: {
      task_id: taskId,
      branch,
      task_branch: branch,
      task_mode: 'modification',
      source_repository: 'fixture',
      source_ref: 'HEAD',
      source_branch: 'main',
      source_commit: 'a'.repeat(40),
      source_status: '',
    },
    checks: [
      {
        command: 'synthetic-check',
        exit_code: 0,
        truncated: false,
        stdout_sha256: sha256('synthetic-raw-stdout\n'),
        stderr_sha256: sha256('synthetic-raw-stderr\n'),
        action_id: 'action-2',
        tool_call_id: 'call-2',
        started: 3,
        completed: 4,
      },
    ],
    final_diff: {
      text: diff,
      sha256: sha256(diff),
      action_id: 'action-3',
      tool_call_id: 'call-3',
      started: 5,
      completed: 6,
    },
    final_status: {
      task_id: taskId,
      branch,
      status: ' M example.py\n',
      action_id: 'action-4',
      tool_call_id: 'call-4',
      started: 7,
      completed: 8,
    },
    observed_checks_status: 'passed',
    evidence_complete: true,
    action_count: 4,
    pending_count: 0,
    errors: [],
  });
  const serialized = JSON.stringify(job);
  for (const omitted of [
    'synthetic-raw-stdout',
    'synthetic-raw-stderr',
    '/synthetic/private-task-path',
  ]) {
    expect(serialized).not.toContain(omitted);
  }
});

test('explicit cancellation preserves progress; an unconfirmed stop remains interrupted', async () => {
  for (const unconfirmedStop of [false, true]) {
    const fixture = await PythonFixture.create({ unconfirmedStop });
    const app = appFor(configured(fixture));
    const {
      body: { job },
    } = await call(app, 'post').send(startBody());
    await waitJob(app, job.job_id, (value) => value.result?.evidence != null);
    const cancelled = await call(app, 'post', `/jobs/${job.job_id}/cancel`).send({});
    expect(cancelled.status).toBe(200);
    const terminal = await waitJob(app, job.job_id);
    expect(terminal.state).toBe(unconfirmedStop ? 'interrupted' : 'cancelled');
    expect(terminal.error_code).toBe(
      unconfirmedStop ? 'execution_stop_unconfirmed' : 'cancel_requested',
    );
    expect(terminal.result.evidence.repository_alias).toBe('fixture');
    expect(terminal.result.evidence.observed_checks_status).toBe('not_run');
    expect(terminal.request_count).toBe(0);
    expect((await call(app, 'post', `/jobs/${job.job_id}/cancel`).send({})).body.job).toEqual(
      terminal,
    );
    const cancelMessages = fixture.transport.exchange.mock.calls
      .map(([value]) => value)
      .filter((value) => value.payload.operation === 'cancel');
    expect(cancelMessages).toHaveLength(2);
    expect(cancelMessages[0].payload.request).toEqual({ job_id: job.job_id });
  }
});

test('invalid, oversized, extra and secret-bearing start fields never reach transport', async () => {
  const transport = { exchange: jest.fn() };
  const app = appFor({ enabled: true, transport, authorize: async () => true });
  const bodies = [
    [],
    {},
    startBody({ prompt: ' ' }),
    startBody({ prompt: 'é'.repeat(16385) }),
    startBody({ max_requests: true }),
    startBody({ max_requests: 11 }),
    startBody({ timeout_seconds: false }),
    startBody({ timeout_seconds: 301 }),
    startBody({ idempotency_key: '../invalid' }),
    startBody({ scope: { repository_alias: 'fixture', task_mode: 'shell' } }),
    startBody({
      scope: {
        repository_alias: 'fixture',
        task_mode: 'read_only',
        path: '/private',
      },
    }),
  ];
  for (const field of [
    'credential',
    'api_key',
    'endpoint',
    'url',
    'path',
    'profile',
    'transport',
    'generation_id',
    'generation_epoch',
  ]) {
    bodies.push(startBody({ [field]: 'synthetic-secret-sentinel' }));
  }
  for (const body of bodies)
    failure(await call(app, 'post').send(body), 400, 'invalid_job_message');
  failure(
    await call(app, 'post').set('Content-Type', 'application/json').send('{"prompt":'),
    400,
    'invalid_job_message',
  );
  failure(
    await call(app, 'post')
      .set('Content-Type', 'application/json')
      .send(JSON.stringify(startBody()).replace('"prompt":', '"__proto__":{},"prompt":')),
    400,
    'invalid_job_message',
  );
  failure(
    await call(app, 'post').send(startBody({ prompt: 'x'.repeat(42000) })),
    413,
    'invalid_job_message',
  );
  expect(transport.exchange).not.toHaveBeenCalled();
});

test('lifecycle bodies, query parameters, resume and steer fail closed without dispatch', async () => {
  const transport = { exchange: jest.fn() };
  const app = appFor({ enabled: true, transport, authorize: async () => true });
  const job = 'a'.repeat(32);
  failure(await call(app, 'get', `/jobs/${job}?owner=other`), 400, 'invalid_job_message');
  failure(await call(app, 'get', '/jobs/not-a-job-id'), 400, 'invalid_job_message');
  failure(
    await call(app, 'get', `/jobs/${job}`).send({ owner: 'other' }),
    400,
    'invalid_job_message',
  );
  failure(
    await call(app, 'post', `/jobs/${job}/cancel`).send({
      generation_id: 'forged',
      generation_epoch: 1,
    }),
    400,
    'invalid_job_message',
  );
  failure(
    await call(app, 'post', `/jobs/${job}/cancel`)
      .set('Content-Type', 'text/plain')
      .send('ignored body'),
    400,
    'invalid_job_message',
  );
  for (const operation of ['resume', 'steer']) {
    failure(
      await call(app, 'post', `/jobs/${job}/${operation}`).send({}),
      405,
      'invalid_job_message',
    );
  }
  expect(transport.exchange).not.toHaveBeenCalled();
});

test('a real HTTP client disconnect does not cancel its admitted job', async () => {
  const fixture = await PythonFixture.create();
  const accepted = deferred();
  const release = deferred();
  cleanups.push(async () => release.resolve());
  const transport = {
    exchange: jest.fn(async (message) => {
      const reply = await fixture.exchange(message);
      if (message.payload.operation === 'start') {
        accepted.resolve(reply);
        await release.promise;
      }
      return reply;
    }),
  };
  const app = appFor(configured(fixture, { transport }));
  const server = app.listen(0, '127.0.0.1');
  await once(server, 'listening');
  cleanups.push(
    () =>
      new Promise((resolve, reject) => {
        server.close((error) => (error ? reject(error) : resolve()));
        server.closeAllConnections();
      }),
  );
  const body = JSON.stringify(startBody());
  const client = http.request({
    host: '127.0.0.1',
    port: server.address().port,
    path: '/api/agents/preview/jobs',
    method: 'POST',
    headers: {
      Authorization: 'Bearer owner',
      'Content-Type': 'application/json',
      'Content-Length': Buffer.byteLength(body),
    },
  });
  client.on('error', () => {});
  client.end(body);
  const reply = await accepted.promise;
  const closed = new Promise((resolve) => client.once('close', resolve));
  client.destroy();
  await closed;
  release.resolve();
  const live = await call(app, 'get', `/jobs/${reply.job.job_id}`);
  expect(live.status).toBe(200);
  expect(live.body.job.state).toBe('running');
  expect((await fixture.inspect()).cancel_calls).toBe(0);
  expect(transport.exchange.mock.calls.map(([value]) => value.payload.operation)).toEqual([
    'start',
    'get',
  ]);
});

test('malformed, oversized and secret-bearing replies are rejected without exposing content', async () => {
  const fixture = await PythonFixture.create();
  const goodApp = appFor(configured(fixture));
  const {
    body: { job },
  } = await call(goodApp, 'post').send(startBody({ prompt: 'finish' }));
  const completed = await waitJob(goodApp, job.job_id);
  const success = { version: 1, ok: true, job: completed };
  const replies = [
    null,
    'not-json',
    { version: 2, ok: true, job: completed },
    { version: 1, ok: false, error: 'synthetic-secret-sentinel' },
    { ...success, secret: 'synthetic-secret-sentinel' },
    {
      ...success,
      job: {
        ...completed,
        result: { ...completed.result, final_response: 'x'.repeat(262145) },
      },
    },
    { ...success, job: { ...completed, owner: 'synthetic-secret-sentinel' } },
    { ...success, job: { ...completed, generation_epoch: 9007199254740992 } },
    {
      ...success,
      job: {
        ...completed,
        result: {
          ...completed.result,
          evidence: { ...completed.result.evidence, repository_alias: 'other' },
        },
      },
    },
  ];
  for (const reply of replies) {
    const transport = { exchange: jest.fn(async () => reply) };
    failure(
      await call(appFor(configured(fixture, { transport })), 'get', `/jobs/${job.job_id}`),
      502,
      'job_service_unavailable',
    );
    expect(transport.exchange).toHaveBeenCalledTimes(1);
  }
  const transport = {
    exchange: jest.fn(async () => {
      throw new Error('synthetic-secret-sentinel');
    }),
  };
  failure(
    await call(appFor(configured(fixture, { transport })), 'get', `/jobs/${job.job_id}`),
    503,
    'job_service_unavailable',
  );
});

test('start, get and cancel reject stale or mismatched reply identity', async () => {
  const fixture = await PythonFixture.create();
  const transport = {
    exchange: jest.fn(async (message) => {
      const reply = await fixture.exchange(message);
      if (reply.ok && message.payload.operation === 'start') {
        reply.job.generation_id = `preview:${'0'.repeat(64)}`;
      }
      return reply;
    }),
  };
  failure(
    await call(appFor(configured(fixture, { transport })), 'post').send(startBody()),
    502,
    'job_service_unavailable',
  );
  const goodApp = appFor(configured(fixture));
  const {
    body: { job },
  } = await call(goodApp, 'post').send(startBody());
  const wrongJob = {
    exchange: jest.fn(async (message) => {
      const reply = await fixture.exchange(message);
      if (reply.ok) reply.job.job_id = '0'.repeat(32);
      return reply;
    }),
  };
  failure(
    await call(appFor(configured(fixture, { transport: wrongJob })), 'get', `/jobs/${job.job_id}`),
    502,
    'job_service_unavailable',
  );
  const staleCancel = {
    exchange: jest.fn(async (message) => {
      const reply = await fixture.exchange(message);
      if (reply.ok && message.payload.operation === 'cancel')
        reply.job.generation_id = `preview:${'0'.repeat(64)}`;
      return reply;
    }),
  };
  failure(
    await call(
      appFor(configured(fixture, { transport: staleCancel })),
      'post',
      `/jobs/${job.job_id}/cancel`,
    ).send({}),
    502,
    'job_service_unavailable',
  );
  expect(staleCancel.exchange.mock.calls.map(([value]) => value.payload.operation)).toEqual([
    'get',
    'cancel',
  ]);
});

test('a transport timeout means unknown state and never retries or cancels admitted work', async () => {
  const fixture = await PythonFixture.create();
  const accepted = deferred();
  const release = deferred();
  cleanups.push(async () => release.resolve());
  const transport = {
    exchange: jest.fn(async (message) => {
      const reply = await fixture.exchange(message);
      accepted.resolve(reply);
      await release.promise;
      return reply;
    }),
  };
  const app = appFor(configured(fixture, { transport, timeoutMs: 100 }));
  failure(await call(app, 'post').send(startBody()), 504, 'job_service_unavailable');
  const reply = await accepted.promise;
  expect(transport.exchange).toHaveBeenCalledTimes(1);
  expect((await fixture.inspect()).cancel_calls).toBe(0);
  release.resolve();
  const live = await call(appFor(configured(fixture)), 'get', `/jobs/${reply.job.job_id}`);
  expect(live.status).toBe(200);
  expect(live.body.job.state).toBe('running');
  expect((await fixture.inspect()).worker_starts).toBe(1);
});
