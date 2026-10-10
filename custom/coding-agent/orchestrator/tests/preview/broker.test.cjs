/* Real loopback mTLS and HTTP/controller/ledger path; ephemeral synthetic trust only. */
const { spawn, execFileSync } = require('node:child_process');
const { once } = require('node:events');
const { createSecureContext, connect } = require('node:tls');
const { X509Certificate } = require('node:crypto');
const { request: httpsRequest } = require('node:https');
const { createServer } = require('node:http');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const express = require('express');
const supertest = require('supertest');
const { createPreviewHttps } = require(path.join(process.env.PREVIEW_TEST_BUILD, 'https.js'));
const { createPreviewJobHandlers } = require(
  path.join(process.env.PREVIEW_TEST_BUILD, 'controller.js'),
);
const cleanups = [];
let material;
const principal = { user_id: 'owner', tenant_id: 'tenant' };
jest.setTimeout(30000);

function directory() {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'preview-mtls-'));
  cleanups.push(() => fs.rmSync(root, { recursive: true, force: true }));
  if (material) {
    for (const name of fs.readdirSync(material)) {
      if (name.endsWith('.crt') || name.endsWith('.key'))
        fs.copyFileSync(path.join(material, name), path.join(root, name));
    }
    return root;
  }
  const openssl = (...args) =>
    execFileSync('openssl', args, { cwd: root, stdio: 'pipe', timeout: 10000 });
  openssl(
    'req',
    '-x509',
    '-newkey',
    'rsa:2048',
    '-nodes',
    '-keyout',
    'ca.key',
    '-out',
    'ca.crt',
    '-days',
    '1',
    '-subj',
    '/CN=Synthetic Preview CA',
  );
  for (const name of ['server', 'nas', 'foreign', 'wrong-server']) {
    openssl(
      'req',
      '-new',
      '-newkey',
      'rsa:2048',
      '-nodes',
      '-keyout',
      name + '.key',
      '-out',
      name + '.csr',
      '-subj',
      '/CN=' + name,
    );
    fs.writeFileSync(
      path.join(root, 'extension'),
      name.includes('server')
        ? 'extendedKeyUsage=serverAuth\nsubjectAltName=' +
            (name === 'server' ? 'IP:127.0.0.1' : 'DNS:wrong.invalid')
        : 'extendedKeyUsage=clientAuth',
    );
    openssl(
      'x509',
      '-req',
      '-in',
      name + '.csr',
      '-CA',
      'ca.crt',
      '-CAkey',
      'ca.key',
      '-CAcreateserial',
      '-out',
      name + '.crt',
      '-days',
      '1',
      '-extfile',
      'extension',
    );
  }
  openssl(
    'req',
    '-x509',
    '-newkey',
    'rsa:2048',
    '-nodes',
    '-keyout',
    'intruder.key',
    '-out',
    'intruder.crt',
    '-days',
    '1',
    '-subj',
    '/CN=Untrusted',
  );
  return root;
}
function tlsOptions(root, client = 'nas') {
  return {
    ca: fs.readFileSync(path.join(root, 'ca.crt')),
    ...(client
      ? {
          cert: fs.readFileSync(path.join(root, client + '.crt')),
          key: fs.readFileSync(path.join(root, client + '.key')),
        }
      : {}),
    minVersion: 'TLSv1.2',
    rejectUnauthorized: true,
  };
}
function options(root, port, changes = {}) {
  return {
    endpoint: `https://127.0.0.1:${port}/preview/v1`,
    secureContext: createSecureContext(tlsOptions(root)),
    serverSha256: new X509Certificate(fs.readFileSync(path.join(root, 'server.crt'))).fingerprint256
      .replaceAll(':', '')
      .toLowerCase(),
    authorize: async () => true,
    enabled: true,
    timeoutMs: 3000,
    ...changes,
  };
}
async function host(root, mode = 'normal') {
  const child = spawn(
    process.env.PREVIEW_TEST_PYTHON,
    ['-B', path.join(__dirname, 'broker_fixture.py'), root, mode],
    {
      cwd: root,
      stdio: ['pipe', 'pipe', 'pipe'],
      env: {
        HOME: root,
        TMPDIR: root,
        LANG: 'C.UTF-8',
        PYTHONDONTWRITEBYTECODE: '1',
        PYTHON_DOTENV_DISABLED: '1',
        PYTHONPATH: [path.resolve(__dirname, '../../src'), __dirname].join(path.delimiter),
      },
    },
  );
  const exited = once(child, 'exit');
  let stderr = '';
  child.stderr.on('data', (chunk) => {
    stderr = (stderr + chunk).slice(-4000);
  });
  let closed = false;
  const close = async () => {
    if (closed) return;
    closed = true;
    child.stdin.end();
    let timer;
    try {
      expect(
        await Promise.race([
          exited,
          new Promise((_, reject) => {
            timer = setTimeout(() => reject(new Error('broker exit: ' + stderr)), 5000);
          }),
        ]),
      ).toEqual([0, null]);
    } finally {
      clearTimeout(timer);
      if (child.exitCode === null) child.kill('SIGKILL');
    }
  };
  cleanups.push(close);
  const { port } = await new Promise((resolve, reject) => {
    let output = '';
    let settled = false;
    const finish = (error, value) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      child.stdout.off('data', onData);
      if (error) reject(error);
      else resolve(value);
    };
    const onData = (chunk) => {
      output += chunk.toString();
      if (output.length > 1024) return finish(new Error('broker readiness overflow'));
      if (!output.includes('\n')) return;
      try {
        const value = JSON.parse(output.slice(0, output.indexOf('\n')));
        if (!Number.isInteger(value.port) || value.port < 1 || value.port > 65535)
          throw new Error('invalid broker port');
        finish(null, value);
      } catch (error) {
        finish(error);
      }
    };
    const timer = setTimeout(() => finish(new Error('broker startup: ' + stderr)), 5000);
    child.stdout.on('data', onData);
    exited.then(() => finish(new Error('broker exited: ' + stderr)), finish);
  });
  const adapter = createPreviewHttps(options(root, port));
  const handlers = createPreviewJobHandlers(adapter);
  const app = express();
  app.use(express.json());
  app.use((req, res, next) => {
    const identity = req.get('authorization');
    if (!['owner', 'other', 'tenant'].includes(identity)) return res.sendStatus(401);
    req.user = {
      id: identity === 'other' ? 'other' : 'owner',
      tenantId: identity === 'tenant' ? 'foreign' : 'tenant',
    };
    next();
  });
  app.post('/jobs', handlers.start);
  app.get('/jobs/:id', (req, res, next) => {
    req.params.jobId = req.params.id;
    return handlers.get(req, res, next);
  });
  app.post('/jobs/:id/cancel', (req, res, next) => {
    req.params.jobId = req.params.id;
    return handlers.cancel(req, res, next);
  });
  const server = createServer(app);
  cleanups.push(
    () =>
      new Promise((resolve) => {
        server.close(resolve);
        server.closeAllConnections();
      }),
  );
  server.listen(0, '127.0.0.1');
  await once(server, 'listening');
  return {
    root,
    port,
    close,
    adapter,
    request: (method, url = '/jobs', identity = 'owner') =>
      supertest(server)[method](url).set('Authorization', identity),
  };
}
const body = (prompt = 'wait', changes = {}) => ({
  prompt,
  idempotency_key: 'same-key',
  scope: { repository_alias: 'fixture', task_mode: 'read_only' },
  max_requests: 10,
  timeout_seconds: 20,
  ...changes,
});
async function terminal(fixture, id) {
  for (let i = 0; i < 100; i++) {
    const result = await fixture.request('get', '/jobs/' + id);
    expect(result.status).toBe(200);
    if (!['queued', 'running', 'cancelling'].includes(result.body.job.state))
      return result.body.job;
    await new Promise((resolve) => setTimeout(resolve, 20));
  }
  throw new Error('terminal deadline');
}
function wire(fixture, bytes, changes = {}) {
  return new Promise((resolve, reject) => {
    const req = httpsRequest(
      `https://127.0.0.1:${fixture.port}/preview/v1`,
      {
        ...tlsOptions(fixture.root),
        agent: false,
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(bytes) },
        ...changes,
      },
      (res) => {
        const chunks = [];
        res.on('data', (x) => chunks.push(x));
        res.on('end', () =>
          resolve({ status: res.statusCode, body: Buffer.concat(chunks).toString() }),
        );
      },
    );
    req.on('error', reject);
    req.setTimeout(3000, () => req.destroy(new Error('wire timeout')));
    req.end(bytes);
  });
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
  if (errors.length) throw new AggregateError(errors, 'broker fixture cleanup');
});

beforeAll(() => {
  material = directory();
  cleanups.pop();
});
afterAll(() => fs.rmSync(material, { recursive: true, force: true }));

test('certificate-authenticated HTTP start/status/evidence is idempotent and owner isolated', async () => {
  const f = await host(directory());
  const started = await f.request('post').send(body('finish-evidence'));
  expect(started.status).toBe(200);
  const id = started.body.job.job_id;
  expect((await terminal(f, id)).result.evidence.evidence_complete).toBe(true);
  expect((await f.request('post').send(body('finish-evidence'))).body.job.job_id).toBe(id);
  expect((await f.request('post').send(body('different'))).body.error).toBe('idempotency_conflict');
  for (const identity of ['other', 'tenant']) {
    expect((await f.request('get', '/jobs/' + id, identity)).status).not.toBe(200);
    expect((await f.request('post', '/jobs/' + id + '/cancel', identity).send({})).status).not.toBe(
      200,
    );
  }
  expect(
    fs.readFileSync(path.join(f.root, 'launches.jsonl'), 'utf8').trim().split('\n'),
  ).toHaveLength(1);
});

test('cancel requires authoritative proof; stale generation and arbitrary inputs fail closed', async () => {
  const f = await host(directory());
  const started = await f.request('post').send(body());
  const job = started.body.job;
  const frame = {
    version: 1,
    request_id: 'a'.repeat(36),
    principal,
    payload: {
      version: 1,
      operation: 'cancel',
      request: {
        job_id: job.job_id,
        generation_id: 'stale',
        generation_epoch: 1,
      },
    },
  };
  const stale = await wire(f, JSON.stringify(frame) + '\n');
  expect(JSON.parse(stale.body).result.error).toBe('invalid_job_message');
  expect((await f.request('post').send({ ...body(), command: 'anything' })).status).toBe(400);
  expect((await f.request('post', '/jobs/' + job.job_id + '/cancel').send({})).status).toBe(200);
  expect((await terminal(f, job.job_id)).state).toBe('cancelled');
});

test.each(['foreign', 'intruder', null])(
  'unmapped or missing client certificate %s never dispatches',
  async (client) => {
    const f = await host(directory());
    const transport = createPreviewHttps(
      options(f.root, f.port, { secureContext: createSecureContext(tlsOptions(f.root, client)) }),
    ).transport;
    await expect(transport.exchange({ principal, payload: {} })).rejects.toThrow(
      'job_service_unavailable',
    );
    expect(fs.existsSync(path.join(f.root, 'launches.jsonl'))).toBe(false);
  },
);

test.each(['wrong-server', 'disabled'])('%s broker fails closed without jobs', async (mode) => {
  const f = await host(directory(), mode);
  expect((await f.request('post').send(body())).body.error).toBe('job_service_unavailable');
  expect(fs.existsSync(path.join(f.root, 'launches.jsonl'))).toBe(false);
});

test('wrong server pin, disabled client and missing configuration fail closed', async () => {
  const f = await host(directory());
  for (const changes of [{ serverSha256: '0'.repeat(64) }, { enabled: false }]) {
    await expect(
      createPreviewHttps(options(f.root, f.port, changes)).transport.exchange({
        principal,
        payload: {},
      }),
    ).rejects.toThrow();
  }
  for (const changes of [
    { secureContext: undefined },
    { serverSha256: '' },
    { endpoint: 'http://127.0.0.1/preview/v1' },
    { authorize: undefined },
  ]) {
    expect(() => createPreviewHttps(options(f.root, f.port, changes))).toThrow();
  }
});

test.each(['drop-start-unknown', 'drop-cancel-unknown', 'mismatch'])(
  '%s retains durable identity and quarantine across restart',
  async (mode) => {
    const root = directory();
    const f = await host(root, mode);
    const first = await f.request('post').send(body());
    let id;
    if (mode === 'drop-start-unknown') {
      expect(first.body.error).toBe('job_service_unavailable');
      id = (await f.request('post').send(body())).body.job.job_id;
    } else {
      id = first.body.job.job_id;
      if (mode === 'drop-cancel-unknown')
        expect((await f.request('post', '/jobs/' + id + '/cancel').send({})).body.error).toBe(
          'job_service_unavailable',
        );
    }
    await f.close();
    const next = await host(root);
    expect((await next.request('get', '/jobs/' + id)).body.job.error_code).toBe(
      'execution_stop_unconfirmed',
    );
    expect((await next.request('post').send(body())).body.job.job_id).toBe(id);
    expect(
      (await next.request('post').send(body('wait', { idempotency_key: 'new-key' }))).body.error,
    ).toBe('job_busy');
    expect(
      fs.readFileSync(path.join(root, 'launches.jsonl'), 'utf8').trim().split('\n'),
    ).toHaveLength(1);
  },
);

test('oversized, duplicate-key and multi-frame requests dispatch nothing', async () => {
  const f = await host(directory());
  for (const bytes of ['x'.repeat(49153), '{"version":1,"version":1}\n', '{}\n{}\n']) {
    const result = await wire(f, bytes).catch(() => ({ status: 0 }));
    expect(result.status).not.toBe(200);
  }
  expect(fs.existsSync(path.join(f.root, 'launches.jsonl'))).toBe(false);
});

test('absolute broker deadline closes a slow partial body without admission', async () => {
  const f = await host(directory());
  const socket = connect({ host: '127.0.0.1', port: f.port, ...tlsOptions(f.root) });
  socket.on('error', () => {});
  await once(socket, 'secureConnect');
  const closed = new Promise((resolve) => socket.once('close', resolve));
  socket.resume();
  socket.write(
    'POST /preview/v1 HTTP/1.1\r\nHost: fixture\r\nContent-Type: application/json\r\nContent-Length: 100\r\n\r\n{',
  );
  const start = Date.now();
  await closed;
  expect(Date.now() - start).toBeLessThan(2500);
  expect(fs.existsSync(path.join(f.root, 'launches.jsonl'))).toBe(false);
});

test('wrong reply identity is unavailable even when the remote start happened', async () => {
  const f = await host(directory(), 'wrong-reply');
  expect((await f.request('post').send(body())).body.error).toBe('job_service_unavailable');
  expect(
    fs.readFileSync(path.join(f.root, 'launches.jsonl'), 'utf8').trim().split('\n'),
  ).toHaveLength(1);
});
