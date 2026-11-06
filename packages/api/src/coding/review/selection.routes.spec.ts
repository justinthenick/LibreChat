import express from 'express';
import supertest from 'supertest';
import { createServer } from 'node:http';
import type { RequestHandler } from 'express';
import type { Server } from 'node:http';
import type { ServerRequest } from '../../types/http';
import { tenantContextMiddleware } from '../../middleware/tenant';
import { createReviewRouter } from './routes';

let now = 1_800_000_000_000;
let server: Server;
let upstream: jest.SpyInstance;
const input = { repository: 'fixture', pullRequest: 7 };
const authenticate: RequestHandler = (req, res, next) => {
  if (!req.headers['x-fixture-user']) {
    res.sendStatus(401);
    return;
  }
  Object.assign(req, {
    user: { id: req.headers['x-fixture-user'], tenantId: req.headers['x-fixture-tenant'] },
  });
  tenantContextMiddleware(req as ServerRequest, res, next);
};
const checkBan: RequestHandler = (req, res, next) => {
  if (req.headers['x-fixture-ban']) {
    res.sendStatus(403);
    return;
  }
  next();
};

beforeEach(async () => {
  now += 3_600_000;
  jest.spyOn(Date, 'now').mockImplementation(() => now);
  upstream = jest.spyOn(globalThis, 'fetch').mockImplementation(
    async () =>
      new Response(
        JSON.stringify({
          number: 7,
          state: 'open',
          merged: false,
          base: { sha: 'a'.repeat(40), repo: { id: 123, full_name: 'fixture/repo' } },
          head: { sha: 'b'.repeat(40) },
        }),
      ),
  );
  const app = express();
  for (const mount of ['/one', '/two']) {
    app.use(
      mount,
      createReviewRouter(
        {
          enabled: true,
          client: { enabled: false, url: '', token: '', model: 'fixture' },
          repositories: ['tenant-a', 'tenant-b'].map((tenantId) => ({
            id: 'fixture',
            tenantId,
            github: { owner: 'fixture', name: 'repo', repositoryId: 123 },
          })),
        },
        { authenticate, checkBan },
      ),
    );
  }
  server = createServer(app);
  await new Promise<void>((resolve) => server.listen(0, '127.0.0.1', resolve));
});
afterEach(async () => {
  server.closeAllConnections();
  await new Promise<void>((resolve) => server.close(() => resolve()));
});
function post(user: string, tenant = 'tenant-a', mount = '/one', body = input) {
  return supertest(server)
    .post(`${mount}/selection`)
    .set('x-fixture-user', user)
    .set('x-fixture-tenant', tenant)
    .send(body);
}

it('shares capacity across concurrent users, tenants and router instances with safe 429 responses', async () => {
  const responses = await Promise.all(
    Array.from({ length: 40 }, (_, index) =>
      post(`user-${index}`, index % 2 ? 'tenant-a' : 'tenant-b', index % 2 ? '/one' : '/two'),
    ),
  );
  expect(responses.filter(({ status }) => status === 200)).toHaveLength(30);
  expect(responses.filter(({ status }) => status === 429)).toHaveLength(10);
  for (const response of responses.filter(({ status }) => status === 429)) {
    expect(response.body).toEqual({ code: 'busy' });
    expect(response.headers['cache-control']).toBe('no-store');
  }
  expect(upstream).toHaveBeenCalledTimes(30);
  now += 3_599_999;
  await post('new-user').expect(429, { code: 'busy' });
  expect(upstream).toHaveBeenCalledTimes(30);
  now += 1;
  await post('newer-user').expect(200);
  expect(upstream).toHaveBeenCalledTimes(31);
});

it('retains auth, ban, tenant and per-principal protections without charging rejected inputs upstream', async () => {
  await supertest(server).post('/one/selection').send(input).expect(401);
  await post('banned').set('x-fixture-ban', 'yes').expect(403);
  await post('outsider', 'tenant-c').expect(403, { code: 'forbidden' });
  for (let index = 0; index < 30; index++) {
    await post('alice', 'tenant-a', '/one', { ...input, pullRequest: 0 }).expect(400);
  }
  await post('alice').expect(429, { code: 'busy' });
  expect(upstream).not.toHaveBeenCalled();
  await post('alice', 'tenant-b').expect(200);
  await post('bob', 'tenant-a').expect(200);
  expect(upstream).toHaveBeenCalledTimes(2);
});
