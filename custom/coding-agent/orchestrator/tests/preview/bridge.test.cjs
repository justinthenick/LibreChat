/* Real authenticated HTTP/controller/private pipes/dispatcher/job and execution ledgers.
 * Authentication identities and external worker authority are synthetic; no provider calls. */
const { spawn } = require('node:child_process');
const { once } = require('node:events');
const { Transform } = require('node:stream');
const fs = require('node:fs/promises');
const http = require('node:http');
const os = require('node:os');
const path = require('node:path');
const express = require('express');
const supertest = require('supertest');
const { createPreviewPipe } = require(path.join(process.env.PREVIEW_TEST_BUILD, 'pipe.js'));
const { createPreviewJobHandlers } = require(
  path.join(process.env.PREVIEW_TEST_BUILD, 'controller.js'),
);
const principal = { user_id: 'owner', tenant_id: 'tenant' };
const pause = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
const cleanups = [];
jest.setTimeout(30000);

async function host(directory, mode = 'normal', settings = {}) {
  const child = spawn(
    process.env.PREVIEW_TEST_PYTHON,
    ['-B', path.join(__dirname, 'supervised_fixture.py'), directory, mode],
    {
      cwd: directory,
      stdio: ['pipe', 'pipe', 'pipe'],
      env: {
        HOME: directory,
        TMPDIR: directory,
        LANG: 'C.UTF-8',
        PYTHONDONTWRITEBYTECODE: '1',
        PYTHON_DOTENV_DISABLED: '1',
        LITELLM_LOCAL_MODEL_COST_MAP: 'True',
        OTEL_SDK_DISABLED: 'true',
        PYTHONPATH: [path.resolve(__dirname, '../../src'), __dirname].join(path.delimiter),
      },
    },
  );
  let stderr = '';
  child.stderr.on('data', (data) => {
    stderr = (stderr + data).slice(-8192);
  });
  const exited = once(child, 'exit');
  let readable = child.stdout;
  if (settings.dropFrame) {
    let buffered = Buffer.alloc(0);
    let frames = 0;
    readable = child.stdout.pipe(
      new Transform({
        transform(chunk, _encoding, done) {
          buffered = Buffer.concat([buffered, chunk]);
          let newline;
          while ((newline = buffered.indexOf(10)) !== -1) {
            const frame = buffered.subarray(0, newline + 1);
            buffered = buffered.subarray(newline + 1);
            if (++frames !== settings.dropFrame) this.push(frame);
          }
          done();
        },
      }),
    );
  }
  const options = createPreviewPipe({
    readable,
    writable: child.stdin,
    grants: [{ principal, repositories: ['fixture'] }],
    admitStart: async (_owner, request) => request.prompt !== 'denied',
    enabled: true,
    timeoutMs: 5000,
    ...settings,
  });
  const handlers = createPreviewJobHandlers(options);
  const app = express();
  app.use(express.json());
  app.use((req, res, next) => {
    const token = req.get('authorization');
    if (!['Bearer owner', 'Bearer other', 'Bearer other-tenant'].includes(token))
      return res.sendStatus(401);
    req.user = {
      id: token === 'Bearer other' ? 'other' : 'owner',
      tenantId: token === 'Bearer other-tenant' ? 'other' : 'tenant',
    };
    next();
  });
  app.post('/jobs', handlers.start);
  app.get('/jobs/:jobId', handlers.get);
  app.post('/jobs/:jobId/cancel', handlers.cancel);
  const server = http.createServer(app);
  server.listen(0, '127.0.0.1');
  await once(server, 'listening');
  let closed = false;
  const close = async () => {
    if (closed) return;
    closed = true;
    options.close();
    let timer;
    try {
      const result = await Promise.race([
        exited,
        new Promise((_, reject) => {
          timer = setTimeout(() => reject(new Error('Fixture exit deadline: ' + stderr)), 5000);
        }),
      ]);
      expect(result).toEqual([0, null]);
    } finally {
      clearTimeout(timer);
      if (child.exitCode === null) child.kill('SIGKILL');
      await new Promise((resolve) => {
        server.close(resolve);
        server.closeAllConnections();
      });
    }
  };
  cleanups.push(close);
  return {
    options,
    close,
    request: (method, url = '/jobs', token = 'owner') =>
      supertest(server)
        [method](url)
        .set('Authorization', 'Bearer ' + token),
  };
}
async function directory() {
  const root = await fs.mkdtemp(path.join(os.tmpdir(), 'preview-bridge-'));
  cleanups.push(() => fs.rm(root, { recursive: true, force: true }));
  return root;
}
function body(prompt = 'wait', changes = {}) {
  return {
    prompt,
    idempotency_key: 'synthetic-key',
    scope: { repository_alias: 'fixture', task_mode: 'read_only' },
    max_requests: 10,
    timeout_seconds: 20,
    ...changes,
  };
}
async function terminal(fixture, id, timeout = 5000) {
  const deadline = Date.now() + timeout;
  while (Date.now() < deadline) {
    const response = await fixture.request('get', '/jobs/' + id);
    expect(response.status).toBe(200);
    if (!['queued', 'running', 'cancelling'].includes(response.body.job.state))
      return response.body.job;
    await pause(20);
  }
  throw new Error('Synthetic terminal state deadline');
}
afterEach(async () => {
  const errors = [];
  while (cleanups.length) {
    try {
      await cleanups.pop()();
    } catch (error) {
      errors.push(error);
    }
  }
  if (errors.length) throw new AggregateError(errors);
});

test('HTTP start/status/evidence and idempotency use real supervised pipe dispatch', async () => {
  const root = await directory();
  const f = await host(root);
  const first = await f.request('post').send(body('finish-evidence'));
  expect(first.status).toBe(200);
  const job = await terminal(f, first.body.job.job_id);
  expect(job.state).toBe('completed');
  expect(job.result.evidence.evidence_complete).toBe(true);
  expect(job.result.evidence.checks[0].exit_code).toBe(0);
  expect(JSON.stringify(job)).not.toContain('synthetic-raw-stdout');
  const repeated = await f.request('post').send(body('finish-evidence'));
  expect(repeated.body.job.job_id).toBe(job.job_id);
  expect((await f.request('post').send(body('wait'))).body.error).toBe('idempotency_conflict');
  expect(
    (await fs.readFile(path.join(root, 'launches.jsonl'), 'utf8')).trim().split('\n'),
  ).toHaveLength(1);
});

test('HTTP cancel needs exact supervisor stop proof; no principal or scope bypass', async () => {
  const f = await host(await directory());
  for (const token of ['other', 'other-tenant']) {
    expect((await f.request('post', '/jobs', token).send(body())).body.error).toBe(
      'scope_not_authorized',
    );
  }
  expect((await f.request('post').send(body('denied'))).body.error).toBe('scope_not_authorized');
  expect(
    (
      await f
        .request('post')
        .send(body('wait', { scope: { repository_alias: 'foreign', task_mode: 'read_only' } }))
    ).body.error,
  ).toBe('scope_not_authorized');
  const first = await f.request('post').send(body());
  const id = first.body.job.job_id;
  expect((await f.request('get', '/jobs/' + id, 'other')).status).not.toBe(200);
  const cancelled = await f.request('post', '/jobs/' + id + '/cancel').send({});
  expect(cancelled.status).toBe(200);
  expect((await terminal(f, id)).state).toBe('cancelled');
});

test.each(['unknown', 'mismatch'])(
  '%s stop/attempt evidence remains quarantined across restart without replay',
  async (mode) => {
    const root = await directory();
    const f = await host(root, mode);
    const first = await f
      .request('post')
      .send(body(mode === 'unknown' ? 'finish-evidence' : 'wait'));
    expect(first.status).toBe(200);
    const id = first.body.job.job_id;
    const job = await terminal(f, id);
    expect(job.error_code).toBe('execution_stop_unconfirmed');
    if (mode === 'mismatch') expect(job.request_count).toBe(0);
    await f.close();
    const next = await host(root);
    expect((await next.request('get', '/jobs/' + id)).body.job.error_code).toBe(
      'execution_stop_unconfirmed',
    );
    const retry = await next
      .request('post')
      .send(body(mode === 'unknown' ? 'finish-evidence' : 'wait'));
    expect(retry.body.job.job_id).toBe(id);
    expect(
      (await next.request('post').send(body('wait', { idempotency_key: 'another-key' }))).body
        .error,
    ).toBe('job_busy');
    expect(
      (await fs.readFile(path.join(root, 'launches.jsonl'), 'utf8')).trim().split('\n'),
    ).toHaveLength(1);
  },
);

test('disabled Python host stays disabled even with configured Node adapter', async () => {
  const f = await host(await directory(), 'disabled');
  expect((await f.request('post').send(body())).body.error).toBe('preview_jobs_disabled');
});

test('lost cancellation reply stays unknown and restart never replays or clears quarantine', async () => {
  const root = await directory();
  const f = await host(root, 'unknown', { dropFrame: 3 });
  const first = await f.request('post').send(body());
  expect(first.status).toBe(200);
  const id = first.body.job.job_id;
  const cancelled = await f.request('post', '/jobs/' + id + '/cancel').send({});
  expect(cancelled.body).toEqual({ version: 1, ok: false, error: 'job_service_unavailable' });
  await f.close();
  const recovered = await host(root);
  const status = await recovered.request('get', '/jobs/' + id);
  expect(status.status).toBe(200);
  expect(status.body.job.error_code).toBe('execution_stop_unconfirmed');
  expect((await recovered.request('post').send(body())).body.job.job_id).toBe(id);
  expect(
    (await recovered.request('post').send(body('wait', { idempotency_key: 'new' }))).body.error,
  ).toBe('job_busy');
  expect(
    (await fs.readFile(path.join(root, 'launches.jsonl'), 'utf8')).trim().split('\n'),
  ).toHaveLength(1);
});

test('confirmed terminal result survives restart without duplicate execution', async () => {
  const root = await directory();
  const f = await host(root);
  const first = await f.request('post').send(body('finish-evidence'));
  const id = first.body.job.job_id;
  expect((await terminal(f, id)).state).toBe('completed');
  await f.close();
  const recovered = await host(root);
  const status = await recovered.request('get', '/jobs/' + id);
  expect(status.body.job.state).toBe('completed');
  expect(status.body.job.result.evidence.evidence_complete).toBe(true);
  expect((await recovered.request('post').send(body('finish-evidence'))).body.job.job_id).toBe(id);
  expect(
    (await fs.readFile(path.join(root, 'launches.jsonl'), 'utf8')).trim().split('\n'),
  ).toHaveLength(1);
});

test('HTTP preview reaches the actual SDK and fenced read-only executor with matched evidence', async () => {
  const root = await directory();
  const f = await host(root, 'sdk-readonly', { timeoutMs: 10000 });
  const request = body('inspect synthetic fixture');
  const started = await f.request('post').send(request);
  expect(started.status).toBe(200);
  const job = await terminal(f, started.body.job.job_id, 20000);
  expect(job.state).toBe('completed');
  expect(job.request_count).toBe(6);
  expect(job.result.evidence.evidence_complete).toBe(true);
  expect(job.result.evidence.checks.map((check) => check.exit_code)).toEqual([1]);
  expect(job.result.evidence.task.task_mode).toBe('read_only');
  expect((await f.request('post').send(request)).body.job.job_id).toBe(job.job_id);
  await f.close();
  const evidence = JSON.parse(await fs.readFile(path.join(root, 'sdk-proof.json'), 'utf8'));
  expect(evidence.calls).toEqual([
    'create_task',
    'read_file',
    'run_check',
    'git_diff',
    'task_status',
  ]);
  expect(evidence.sourceUnchanged).toBe(true);
  expect(evidence.taskUnchanged).toBe(true);
  expect(evidence.stopped).toBe(true);
  expect(evidence.lateRequestStatus).toBe(403);
});

test.each([
  ['sdk-limit', { max_requests: 2 }, 'worker_limit'],
  ['sdk-timeout', { timeout_seconds: 8 }, 'deadline_exceeded'],
  ['sdk-unknown', {}, 'execution_stop_unconfirmed'],
])(
  'HTTP %s preserves bounded failure and never equates local exit with stop proof',
  async (mode, limits, error) => {
    const root = await directory();
    const f = await host(root, mode, { timeoutMs: 10000 });
    const started = await f.request('post').send(body('inspect synthetic fixture', limits));
    expect(started.status).toBe(200);
    const job = await terminal(f, started.body.job.job_id, 20000);
    expect(job.error_code).toBe(error);
    expect(job.request_count).toBeLessThanOrEqual(limits.max_requests ?? 10);
    if (mode === 'sdk-unknown') {
      expect(
        (await f.request('post').send(body('next', { idempotency_key: 'next' }))).body.error,
      ).toBe('job_busy');
    }
    await f.close();
    const evidence = JSON.parse(await fs.readFile(path.join(root, 'sdk-proof.json'), 'utf8'));
    expect(evidence.sourceUnchanged).toBe(true);
    expect(evidence.taskUnchanged).toBe(true);
    expect(evidence.calls).not.toContain('apply_patch');
    expect(evidence.stopped).toBe(mode !== 'sdk-unknown');
    expect(evidence.lateRequestStatus).toBe(403);
  },
);
