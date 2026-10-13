const mockAuthenticate = jest.fn((req, res, next) => {
  if (req.headers.authorization !== 'Bearer fixture') return res.sendStatus(401);
  req.user = { id: 'fixture-user', tenantId: 'fixture-tenant' };
  return next();
});
const mockCheckBan = jest.fn((req, res, next) => {
  if (req.headers['x-fixture-ban']) return res.sendStatus(403);
  return next();
});
jest.mock('~/server/middleware', () => ({
  requireJwtAuth: mockAuthenticate,
  checkBan: mockCheckBan,
}));

const express = require('express');
const supertest = require('supertest');
const { createServer } = require('node:http');
const createRouter = require('./reviews');

it('composes the production wrapper with mandatory auth and ban middleware while disabled', async () => {
  const app = express();
  app.use('/reviews', createRouter({ client: { url: '', token: '', model: 'fixture' } }));
  const server = createServer(app);
  await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
  try {
    const client = supertest(server);
    await client.post('/reviews').send({}).expect(401);
    expect(mockCheckBan).not.toHaveBeenCalled();
    await client
      .post('/reviews')
      .set('Authorization', 'Bearer fixture')
      .set('x-fixture-ban', 'yes')
      .send({})
      .expect(403);
    await client
      .post('/reviews')
      .set('Authorization', 'Bearer fixture')
      .send({})
      .expect(503, { code: 'configuration' });
    await client
      .post('/reviews/cancel')
      .set('Authorization', 'Bearer fixture')
      .set('x-fixture-ban', 'yes')
      .send({})
      .expect(403);
  } finally {
    server.closeAllConnections();
    await new Promise((resolve) => server.close(resolve));
  }
});
