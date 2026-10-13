import os from 'node:os';
import path from 'node:path';
import express from 'express';
import { randomUUID } from 'node:crypto';
import { createServer, request as httpRequest } from 'node:http';
import { mkdtemp, mkdir, writeFile, readFile, readdir, rm } from 'node:fs/promises';
import type { Server, RequestListener } from 'node:http';
import type { RequestHandler } from 'express';
import type { ReviewServiceConfig } from './transport';
import type { ServerRequest } from '../../types/http';
import {
  tenantContextMiddleware,
  _resetTenantMiddlewareStrictCache,
} from '../../middleware/tenant';
import { createReviewClient, createReviewService } from './transport';
import { createReviewHttpHandler } from './http';
import { createReviewRouter } from './routes';

const token = 'offline-http-fixture-token-not-a-real-secret';
const model = 'gpt-5.6-sol';
const request = { repository: 'fixture', base: 'a'.repeat(40), head: 'b'.repeat(40) };
const principal = { userId: 'alice', tenantId: 'tenant-a' };
const fixture = `#!/usr/bin/python3
import json, os, sys, time
from pathlib import Path
repo = Path(sys.argv[sys.argv.index('--repo')+1])
(repo/'started').write_text(str(os.getpid()))
while (repo/'hang').exists(): time.sleep(0.01)
print(json.dumps(dict(ok=True, mode='review', base=sys.argv[sys.argv.index('--base')+1],
head=sys.argv[sys.argv.index('--head')+1], status='human_review_required',
provider='chatgpt_subscription', model=os.environ['CODING_OPENHANDS_MODEL'], finding_count=0, findings=[])))
`;

async function until(check: () => Promise<boolean>) {
  for (let i = 0; i < 300; i++) {
    if (await check()) return;
    await new Promise((resolve) => setTimeout(resolve, 10));
  }
  throw new Error('fixture timed out');
}

describe('offline HTTP bridge and authenticated route composition', () => {
  let root: string;
  let repo: string;
  let scratch: string;
  let config: ReviewServiceConfig;
  const servers: Server[] = [];
  async function listen(make: (url: string) => RequestListener) {
    const server = createServer();
    servers.push(server);
    await new Promise<void>((resolve) => server.listen(0, '127.0.0.1', resolve));
    const address = server.address();
    if (!address || typeof address === 'string') throw new Error('fixture address');
    const url = `http://127.0.0.1:${address.port}/review`;
    server.on('request', make(url));
    return url;
  }
  beforeEach(async () => {
    root = await mkdtemp(path.join(os.tmpdir(), 'review-http-'));
    repo = path.join(root, 'repo');
    scratch = path.join(root, 'scratch');
    const authRoot = path.join(root, 'empty-auth');
    await Promise.all([mkdir(repo), mkdir(scratch, { mode: 0o700 }), mkdir(authRoot)]);
    const python = path.join(root, 'fixture');
    await writeFile(python, fixture, { mode: 0o700 });
    config = {
      enabled: true,
      url: 'http://127.0.0.1:9876/review',
      token,
      worker: {
        python,
        sourceRoot: root,
        scratchRoot: scratch,
        authRoot,
        model,
        repositories: new Map([['fixture', repo]]),
        authorize: async (identity) =>
          identity.userId === 'alice' &&
          (identity.tenantId === 'tenant-a' || identity.tenantId === undefined),
      },
    };
  });
  afterEach(async () => {
    await rm(path.join(repo, 'hang'), { force: true });
    await until(async () => (await readdir(scratch)).length === 0);
    await Promise.all(
      servers.splice(0).map(
        (server) =>
          new Promise<void>((resolve, reject) => {
            server.closeAllConnections();
            server.close((error) => (error ? reject(error) : resolve()));
          }),
      ),
    );
    await rm(root, { recursive: true, force: true });
  });

  const fixtureAuth: RequestHandler = (req, res, next) => {
    if (req.headers.authorization !== 'Bearer fixture-user') {
      res.sendStatus(401);
      return;
    }
    Object.assign(req, { user: { id: 'alice', tenantId: req.headers['x-fixture-tenant'] } });
    tenantContextMiddleware(req as ServerRequest, res, next);
  };
  const fixtureBan: RequestHandler = (req, res, next) => {
    if (req.headers['x-fixture-ban']) {
      res.sendStatus(403);
      return;
    }
    next();
  };
  async function routes(enabled = true, send = createReviewService(config)) {
    return listen(() => {
      const app = express();
      app.use(express.json({ limit: '3mb' }));
      app.use(
        '/review',
        createReviewRouter(
          { enabled, client: { ...config, model, send } },
          { authenticate: fixtureAuth, checkBan: fixtureBan },
        ),
      );
      return app;
    });
  }
  function post(url: string, body: object, headers: Record<string, string> = {}) {
    return fetch(url, {
      method: 'POST',
      headers: {
        'content-type': 'application/json',
        authorization: 'Bearer fixture-user',
        'x-fixture-tenant': 'tenant-a',
        ...headers,
      },
      body: JSON.stringify(body),
    });
  }

  it('recovers a completed result after a lost route response without resubmission', async () => {
    const service = createReviewService(config);
    const send = jest.fn(async (incoming: Request) => {
      const response = await service(incoming);
      if (incoming.url === config.url) throw new Error('delivery lost after completion');
      return response;
    });
    const url = await routes(true, send);
    const id = randomUUID();
    expect((await post(url, { id, request })).status).toBe(502);
    const recovery = await post(`${url}/status`, { id, request });
    expect(recovery.status).toBe(200);
    expect(await recovery.json()).toMatchObject({
      id,
      state: 'completed',
      request,
      result: {
        ...request,
        model,
        status: 'human_review_required',
        findings: [],
      },
    });
    expect(send.mock.calls.filter(([incoming]) => incoming.url === config.url)).toHaveLength(1);
    const unauthorized = await post(`${url}/status`, { id, request }, { authorization: 'wrong' });
    expect(unauthorized.status).toBe(401);
    const banned = await post(`${url}/status`, { id, request }, { 'x-fixture-ban': 'yes' });
    expect(banned.status).toBe(403);
  });

  it('reconnects over HTTP after accepted delivery abort and observes the original result', async () => {
    await writeFile(path.join(repo, 'hang'), '');
    const url = await listen((url) => createReviewHttpHandler({ ...config, url }));
    const client = createReviewClient({ enabled: true, url, token, model });
    const id = randomUUID();
    const controller = new AbortController();
    const delivery = client.run(request, principal, controller.signal, id).catch((error) => error);
    await until(async () => (await readdir(repo)).includes('started'));
    const pid = await readFile(path.join(repo, 'started'), 'utf8');
    controller.abort();
    expect(await delivery).toMatchObject({ code: 'cancelled' });
    expect(await client.status(id, request, principal)).toMatchObject({
      state: 'running',
      cancelRequested: false,
    });
    await rm(path.join(repo, 'hang'));
    await until(async () => (await readdir(scratch)).length === 0);
    expect(await client.status(id, request, principal)).toMatchObject({
      state: 'completed',
      result: request,
    });
    expect(await readFile(path.join(repo, 'started'), 'utf8')).toBe(pid);
  });

  it('isolates result ownership, immutable identity and current repository authorization', async () => {
    let allowed = true;
    config.worker.authorize = async () => allowed;
    const service = createReviewService(config);
    const client = createReviewClient({ ...config, model, send: service });
    const id = randomUUID();
    await client.run(request, principal, undefined, id);
    for (const identity of [
      { ...principal, userId: 'other' },
      { ...principal, tenantId: 'other' },
      { userId: principal.userId },
    ]) {
      expect(await client.status(id, request, identity)).toEqual({ id, state: 'unknown' });
    }
    const stale = { ...request, head: 'c'.repeat(40) };
    await expect(client.status(id, stale, principal)).rejects.toMatchObject({
      code: 'invalid_request',
    });
    await expect(client.run(stale, principal, undefined, id)).rejects.toMatchObject({
      code: 'invalid_request',
    });
    allowed = false;
    await expect(client.status(id, request, principal)).rejects.toMatchObject({
      code: 'forbidden',
    });
    allowed = true;
    expect(await client.status(id, request, principal)).toMatchObject({ state: 'completed' });
  });

  it('keeps result expiry fixed despite reads and cancel; restart and expiry remain unknown', async () => {
    const client = createReviewClient({ ...config, model, send: createReviewService(config) });
    const id = randomUUID();
    await client.run(request, principal, undefined, id);
    const result = await client.status(id, request, principal);
    if (result.state !== 'completed') throw new Error('fixture result');
    const clock = jest.spyOn(Date, 'now').mockReturnValue(result.expiresAt - 1);
    try {
      await client.cancel(id, principal);
      expect(await client.status(id, request, principal)).toEqual(result);
      clock.mockReturnValue(result.expiresAt);
      expect(await client.status(id, request, principal)).toEqual({ id, state: 'unknown' });
    } finally {
      clock.mockRestore();
    }
    const replacement = createReviewClient({ ...config, model, send: createReviewService(config) });
    expect(await replacement.status(id, request, principal)).toEqual({ id, state: 'unknown' });
    const preCancelled = randomUUID();
    await replacement.cancel(preCancelled, principal);
    expect(await replacement.status(preCancelled, request, principal)).toEqual({
      id: preCancelled,
      state: 'unknown',
    });
    expect(await readFile(path.join(repo, 'started'), 'utf8')).toMatch(/^\d+$/);
  });

  it('does not delete a replacement run when an expired status authorization settles late', async () => {
    let wait = false;
    let release = () => {};
    const gate = new Promise<void>((resolve) => {
      release = resolve;
    });
    config.worker.authorize = async () => {
      if (wait) {
        wait = false;
        await gate;
      }
      return true;
    };
    const client = createReviewClient({ ...config, model, send: createReviewService(config) });
    const id = randomUUID();
    await client.run(request, principal, undefined, id);
    const initial = await client.status(id, request, principal);
    if (initial.state !== 'completed') throw new Error('fixture result');
    wait = true;
    const oldLookup = client.status(id, request, principal);
    await until(async () => !wait);
    const clock = jest.spyOn(Date, 'now').mockReturnValue(initial.expiresAt + 1);
    try {
      const replacement = { ...request, head: 'c'.repeat(40) };
      await client.run(replacement, principal, undefined, id);
      release();
      expect(await oldLookup).toEqual({ id, state: 'unknown' });
      expect(await client.status(id, replacement, principal)).toMatchObject({
        state: 'completed',
        request: replacement,
      });
    } finally {
      release();
      clock.mockRestore();
    }
  });

  it('expires retained records even with no further retrieval', async () => {
    const realTimeout = global.setTimeout;
    jest
      .spyOn(global, 'setTimeout')
      .mockImplementation(((callback: () => void, ms?: number) =>
        realTimeout(callback, ms === 600000 ? 50 : ms)) as typeof setTimeout);
    const client = createReviewClient({ ...config, model, send: createReviewService(config) });
    const id = randomUUID();
    await client.run(request, principal, undefined, id);
    expect(await client.status(id, request, principal)).toMatchObject({ state: 'completed' });
    await new Promise((resolve) => setTimeout(resolve, 80));
    expect(await client.status(id, request, principal)).toEqual({ id, state: 'unknown' });
  });

  it('retains explicit cancellation and timeout only after worker cleanup settles', async () => {
    await writeFile(path.join(repo, 'hang'), '');
    const client = createReviewClient({ ...config, model, send: createReviewService(config) });
    const id = randomUUID();
    const running = client.run(request, principal, undefined, id).catch((error) => error);
    await until(async () => (await readdir(repo)).includes('started'));
    await client.cancel(id, principal);
    expect(await running).toMatchObject({ code: 'cancelled' });
    await until(async () => (await readdir(scratch)).length === 0);
    expect(await client.status(id, request, principal)).toMatchObject({
      state: 'failed',
      code: 'cancelled',
    });
    const realTimeout = global.setTimeout;
    jest
      .spyOn(global, 'setTimeout')
      .mockImplementation(((callback: () => void, ms?: number) =>
        realTimeout(callback, ms === 165000 ? 50 : ms)) as typeof setTimeout);
    const next = randomUUID();
    await expect(client.run(request, principal, undefined, next)).rejects.toMatchObject({
      code: 'timeout',
    });
    await until(async () => (await readdir(scratch)).length === 0);
    expect(await client.status(next, request, principal)).toMatchObject({
      state: 'failed',
      code: 'timeout',
    });
  });

  it('caps retained execution slots instead of evicting unexpired results or starting more work', async () => {
    config.worker.authorize = async () => false;
    const client = createReviewClient({ ...config, model, send: createReviewService(config) });
    for (let i = 0; i < 64; i++) {
      await expect(client.run(request, principal, undefined, randomUUID())).rejects.toMatchObject({
        code: 'forbidden',
      });
    }
    await expect(client.run(request, principal, undefined, randomUUID())).rejects.toMatchObject({
      code: 'busy',
    });
    expect(await readdir(repo)).toEqual([]);
  });

  it('rejects hostile recovered identities and oversized recovery responses without retries', async () => {
    const id = randomUUID();
    const result = {
      ...request,
      model,
      provider: 'chatgpt_subscription',
      status: 'human_review_required',
      findings: [],
    };
    for (const body of [
      { id: randomUUID(), state: 'unknown' },
      {
        id,
        state: 'running',
        request: { ...request, head: 'c'.repeat(40) },
        cancelRequested: false,
      },
      {
        id,
        state: 'completed',
        request,
        result: { ...result, model: 'other' },
        expiresAt: Date.now() + 1000,
      },
      {
        id,
        state: 'completed',
        request,
        result: { ...result, head: 'c'.repeat(40) },
        expiresAt: Date.now() + 1000,
      },
      { id, state: 'unknown', result },
    ]) {
      const send = jest.fn(async () => Response.json(body));
      await expect(
        createReviewClient({ ...config, model, send }).status(id, request, principal),
      ).rejects.toMatchObject({ code: 'invalid_response' });
      expect(send).toHaveBeenCalledTimes(1);
    }
    const send = jest.fn(
      async () =>
        new Response('x'.repeat(132097), { headers: { 'content-type': 'application/json' } }),
    );
    await expect(
      createReviewClient({ ...config, model, send }).status(id, request, principal),
    ).rejects.toMatchObject({ code: 'output_limit' });
    expect(send).toHaveBeenCalledTimes(1);
  });

  it('preserves strict tenant rejection before forwarding', async () => {
    const previous = process.env.TENANT_ISOLATION_STRICT;
    process.env.TENANT_ISOLATION_STRICT = 'true';
    _resetTenantMiddlewareStrictCache();
    try {
      const send = jest.fn(createReviewService(config));
      const url = await routes(true, send);
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          authorization: 'Bearer fixture-user',
          'content-type': 'application/json',
        },
        body: JSON.stringify({ id: randomUUID(), request }),
      });
      expect(response.status).toBe(403);
      expect(send).not.toHaveBeenCalled();
    } finally {
      if (previous === undefined) delete process.env.TENANT_ISOLATION_STRICT;
      else process.env.TENANT_ISOLATION_STRICT = previous;
      _resetTenantMiddlewareStrictCache();
    }
  });

  it('bounds cancel tombstones and renews an expired cancellation before a delayed start', async () => {
    const send = createReviewService(config);
    const client = createReviewClient({ ...config, model, send });
    const id = randomUUID();
    const now = Date.now();
    await client.cancel(id, principal);
    const clock = jest.spyOn(Date, 'now').mockReturnValue(now + 600001);
    try {
      await client.cancel(id, principal);
      await expect(client.run(request, principal, undefined, id)).rejects.toMatchObject({
        code: 'cancelled',
      });
      for (let i = 0; i < 1023; i++) await client.cancel(randomUUID(), principal);
      await expect(client.cancel(randomUUID(), principal)).rejects.toMatchObject({ code: 'busy' });
      await expect(client.run(request, principal, undefined, randomUUID())).rejects.toMatchObject({
        code: 'busy',
      });
      expect(await readdir(repo)).toEqual([]);
    } finally {
      clock.mockRestore();
    }
  });

  it('runs the real worker through a loopback HTTP bridge with exact identity', async () => {
    const url = await listen((url) => createReviewHttpHandler({ ...config, url }));
    const client = createReviewClient({ enabled: true, url, token, model });
    const id = randomUUID();
    await expect(client.run(request, principal, undefined, id)).resolves.toMatchObject(request);
    await expect(client.run(request, principal, undefined, id)).rejects.toMatchObject({
      code: 'busy',
    });
    await expect(client.cancel(id, principal)).resolves.toBeUndefined();
    await expect(client.cancel(id, principal)).resolves.toBeUndefined();
  });

  it('keeps accepted HTTP work alive after socket loss; explicit cancel cleans it', async () => {
    await writeFile(path.join(repo, 'hang'), '');
    const url = await listen((url) => createReviewHttpHandler({ ...config, url }));
    const id = randomUUID();
    const connection = httpRequest(url, {
      method: 'POST',
      headers: {
        authorization: `Bearer ${token}`,
        'content-type': 'application/json',
        'x-review-id': id,
      },
    });
    connection.on('error', () => undefined);
    connection.end(JSON.stringify({ request, principal }));
    await until(async () => (await readdir(repo)).includes('started'));
    const pid = Number(await readFile(path.join(repo, 'started'), 'utf8'));
    connection.destroy();
    await new Promise((resolve) => setTimeout(resolve, 40));
    expect(() => process.kill(pid, 0)).not.toThrow();
    const client = createReviewClient({ enabled: true, url, token, model });
    await expect(client.cancel(id, { ...principal, tenantId: 'other' })).rejects.toMatchObject({
      code: 'forbidden',
    });
    expect(() => process.kill(pid, 0)).not.toThrow();
    await client.cancel(id, principal);
    await client.cancel(id, principal);
    await until(async () => (await readdir(scratch)).length === 0);
    expect(() => process.kill(pid, 0)).toThrow();
  });

  it('handles cancellation arriving before admission and rejects cross-owner ID reuse', async () => {
    const send = createReviewService(config);
    const client = createReviewClient({ ...config, model, send });
    const absentTenantId = randomUUID();
    await client.cancel(absentTenantId, { userId: principal.userId });
    await expect(client.cancel(absentTenantId, principal)).rejects.toMatchObject({
      code: 'forbidden',
    });
    const id = randomUUID();
    await client.cancel(id, principal);
    await client.cancel(id, principal);
    await expect(client.run(request, principal, undefined, id)).rejects.toMatchObject({
      code: 'cancelled',
    });
    await expect(
      client.run(request, { ...principal, userId: 'other' }, undefined, id),
    ).rejects.toMatchObject({ code: 'forbidden' });
    expect(await readdir(repo)).toEqual([]);
    await expect(client.run(request, principal, undefined, randomUUID())).resolves.toMatchObject(
      request,
    );
  });

  it('rejects missing ID, wrong host, bad credential and partial bodies before spawning', async () => {
    const partialId = randomUUID();
    let partialReceived = false;
    const url = await listen((url) => {
      const handler = createReviewHttpHandler({ ...config, url });
      return (incoming, outgoing) => {
        if (incoming.headers['x-review-id'] === partialId) partialReceived = true;
        return handler(incoming, outgoing);
      };
    });
    const cases: Record<string, string>[] = [
      {},
      { 'x-review-id': randomUUID(), host: 'untrusted' },
      { 'x-review-id': randomUUID(), authorization: 'Bearer wrong' },
    ];
    for (const headers of cases) {
      const response = await post(url, { request, principal }, headers);
      expect([400, 403]).toContain(response.status);
    }
    const connection = httpRequest(url, {
      method: 'POST',
      headers: {
        authorization: `Bearer ${token}`,
        'content-type': 'application/json',
        'x-review-id': partialId,
        'content-length': 500,
      },
    });
    connection.on('error', () => undefined);
    connection.write('{');
    await until(async () => partialReceived);
    connection.destroy();
    await new Promise((resolve) => setTimeout(resolve, 30));
    expect(await readdir(repo)).toEqual([]);
  });

  it('keeps the HTTP bridge disabled by default', async () => {
    const url = await listen(() =>
      createReviewHttpHandler({ ...config, enabled: undefined, url: '', token: '' }),
    );
    expect((await post(url, {})).status).toBe(503);
    expect(await readdir(repo)).toEqual([]);
  });

  it('uses trusted route identity including absent tenant and enforces auth/ban/default off', async () => {
    const send = jest.fn(createReviewService(config));
    const url = await routes(true, send);
    const body = () => ({ id: randomUUID(), request });
    expect((await post(url, body(), { authorization: 'wrong' })).status).toBe(401);
    expect((await post(url, body(), { 'x-fixture-ban': 'yes' })).status).toBe(403);
    expect(send).not.toHaveBeenCalled();
    expect((await post(url, body())).status).toBe(200);
    const noTenant = await fetch(url, {
      method: 'POST',
      headers: {
        'content-type': 'application/json',
        authorization: 'Bearer fixture-user',
      },
      body: JSON.stringify(body()),
    });
    expect(noTenant.status).toBe(200);
    const disabled = await routes(false, send);
    expect((await post(disabled, body())).status).toBe(503);
    expect(send).toHaveBeenCalledTimes(2);
  });

  it('rejects spoofed identity, unknown repository, oversized parsed body and malformed requests', async () => {
    const url = await routes();
    for (const body of [
      { id: randomUUID(), request, principal },
      { id: randomUUID(), request: { ...request, head: 'main' } },
      { id: randomUUID(), request, tenantId: 'other' },
      { id: randomUUID(), request, excess: 'x'.repeat(5000) },
    ]) {
      expect((await post(url, body)).status).toBe(400);
    }
    expect(
      (await post(url, { id: randomUUID(), request: { ...request, repository: 'other' } })).status,
    ).toBe(403);
    expect(await readdir(repo)).toEqual([]);
  });

  it('does not retry an uncertain service outcome and limits start admission', async () => {
    const send = jest.fn(async () => {
      throw new Error('PRIVATE');
    });
    const url = await routes(true, send);
    for (let i = 0; i < 10; i++) {
      const response = await post(url, { id: randomUUID(), request });
      expect(response.status).toBe(502);
      expect(await response.json()).toEqual({ code: 'worker_failed' });
    }
    expect((await post(url, { id: randomUUID(), request })).status).toBe(429);
    expect(send).toHaveBeenCalledTimes(10);
  });

  it('supports route cancel after browser disconnect without cancelling another owner or run', async () => {
    await writeFile(path.join(repo, 'hang'), '');
    const url = await routes();
    const id = randomUUID();
    const controller = new AbortController();
    const delivery = fetch(url, {
      method: 'POST',
      signal: controller.signal,
      headers: {
        authorization: 'Bearer fixture-user',
        'x-fixture-tenant': 'tenant-a',
        'content-type': 'application/json',
      },
      body: JSON.stringify({ id, request }),
    }).catch(() => undefined);
    await until(async () => (await readdir(repo)).includes('started'));
    const pid = Number(await readFile(path.join(repo, 'started'), 'utf8'));
    controller.abort();
    await delivery;
    expect(() => process.kill(pid, 0)).not.toThrow();
    expect((await post(`${url}/cancel`, { id }, { authorization: 'wrong' })).status).toBe(401);
    expect((await post(`${url}/cancel`, { id }, { 'x-fixture-ban': 'yes' })).status).toBe(403);
    expect((await post(`${url}/cancel`, { id }, { 'x-fixture-tenant': 'other' })).status).toBe(403);
    expect((await post(`${url}/cancel`, { id: randomUUID() })).status).toBe(200);
    expect(() => process.kill(pid, 0)).not.toThrow();
    expect((await post(`${url}/cancel`, { id })).status).toBe(200);
    expect((await post(`${url}/cancel`, { id })).status).toBe(200);
    await until(async () => (await readdir(scratch)).length === 0);
  });
});
