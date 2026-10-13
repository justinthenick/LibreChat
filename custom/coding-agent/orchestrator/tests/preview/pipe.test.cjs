const { PassThrough, Writable } = require('node:stream');
const path = require('node:path');
const { createPreviewPipe } = require(path.join(process.env.PREVIEW_TEST_BUILD, 'pipe.js'));

const principal = { user_id: 'owner', tenant_id: 'tenant' };
const payload = { version: 1, operation: 'get', request: { job_id: 'a'.repeat(32) } };
const cleanups = [];
function fixture(changes = {}) {
  const readable = new PassThrough();
  const writable = new PassThrough();
  const frames = [];
  writable.on('data', (chunk) => frames.push(JSON.parse(chunk.toString())));
  const pipe = createPreviewPipe({
    readable,
    writable,
    grants: [{ principal, repositories: ['fixture'] }],
    admitStart: async () => true,
    enabled: true,
    timeoutMs: 300,
    ...changes,
  });
  cleanups.push(pipe.close);
  return {
    pipe,
    readable,
    writable,
    frames,
    exchange: (message = { principal, payload }) => pipe.transport.exchange(message),
    reply: (changes = {}) =>
      Buffer.from(
        JSON.stringify({
          version: 1,
          request_id: frames[0].request_id,
          principal,
          result: { version: 1, ok: false, error: 'job_not_found' },
          ...changes,
        }) + '\n',
      ),
  };
}
afterEach(() => {
  while (cleanups.length) cleanups.pop()();
});

test('default-off adapter never writes, and snapshots read-only owner/repository grants', async () => {
  const f = fixture({ enabled: undefined });
  await expect(f.exchange()).rejects.toThrow('job_service_unavailable');
  expect(f.frames).toHaveLength(0);
  const grants = [{ principal: { ...principal }, repositories: ['fixture'] }];
  const g = fixture({ grants });
  grants[0].repositories.push('foreign');
  grants[0].principal.user_id = 'other';
  await expect(
    g.pipe.authorize(
      principal,
      { repository_alias: 'fixture', task_mode: 'read_only' },
      { operation: 'get' },
    ),
  ).resolves.toBe(true);
  for (const scope of [
    { repository_alias: 'foreign', task_mode: 'read_only' },
    { repository_alias: 'fixture', task_mode: 'modification' },
  ]) {
    await expect(g.pipe.authorize(principal, scope, { operation: 'get' })).resolves.toBe(false);
  }
  await expect(
    g.exchange({ principal: { ...principal, tenant_id: 'other' }, payload }),
  ).rejects.toThrow();
  expect(g.frames).toHaveLength(0);
});

test('start admission does not throttle get or cancel', async () => {
  const admitStart = jest.fn(async () => false);
  const f = fixture({ admitStart });
  const scope = { repository_alias: 'fixture', task_mode: 'read_only' };
  await expect(
    f.pipe.authorize(principal, scope, { operation: 'start', request: {} }),
  ).resolves.toBe(false);
  await expect(f.pipe.authorize(principal, scope, { operation: 'get' })).resolves.toBe(true);
  await expect(f.pipe.authorize(principal, scope, { operation: 'cancel' })).resolves.toBe(true);
  expect(admitStart).toHaveBeenCalledTimes(1);
});

test('bounded single-flight transport accepts fragmented UTF-8 replies', async () => {
  const f = fixture();
  const first = f.exchange();
  await expect(f.exchange()).rejects.toThrow();
  expect(f.frames).toHaveLength(1);
  const response = f.reply({ result: { text: 'caf\u00e9' } });
  const split = response.indexOf(Buffer.from('\u00e9')) + 1;
  f.readable.write(response.subarray(0, split));
  for (let index = split; index < response.length; index += 7)
    f.readable.write(response.subarray(index, index + 7));
  await expect(first).resolves.toEqual({ text: 'caf\u00e9' });
});

test.each(['principal', 'request', 'duplicate', 'utf8', 'oversize', 'trailing', 'eof', 'write'])(
  '%s failure poisons channel without replay',
  async (mode) => {
    const f = fixture();
    const first = f.exchange();
    const rejected = expect(first).rejects.toThrow('job_service_unavailable');
    if (mode === 'principal')
      f.readable.write(f.reply({ principal: { ...principal, user_id: 'other' } }));
    if (mode === 'request') f.readable.write(f.reply({ request_id: 'foreign' }));
    if (mode === 'duplicate')
      f.readable.write(f.reply().toString().replace('"version":1', '"version":1,"version":1'));
    if (mode === 'utf8') f.readable.write(Buffer.from([255, 10]));
    if (mode === 'oversize') f.readable.write(Buffer.alloc(270337));
    if (mode === 'trailing') f.readable.write(Buffer.concat([f.reply(), Buffer.from('{}\n')]));
    if (mode === 'eof') f.readable.end();
    if (mode === 'write') f.writable.emit('error', new Error('synthetic'));
    await rejected;
    await expect(f.exchange()).rejects.toThrow();
    expect(f.frames).toHaveLength(1);
  },
);

test('timeout bounds stalled writes; delayed replies cannot satisfy a subsequent request', async () => {
  const writable = new Writable({ highWaterMark: 1, write(_chunk, _encoding, _callback) {} });
  const f = fixture({ writable, timeoutMs: 15 });
  await expect(f.exchange()).rejects.toThrow('job_service_unavailable');
  expect(writable.destroyed).toBe(true);
  await expect(f.exchange()).rejects.toThrow('job_service_unavailable');
  const g = fixture({ timeoutMs: 15 });
  const delayed = g.exchange();
  const oldReply = g.reply();
  await expect(delayed).rejects.toThrow('job_service_unavailable');
  g.readable.emit('data', oldReply);
  await expect(g.exchange()).rejects.toThrow('job_service_unavailable');
  expect(g.frames).toHaveLength(1);
});

test('oversized outgoing frames fail before writing', async () => {
  const f = fixture();
  await expect(
    f.exchange({ principal, payload: { padding: 'a'.repeat(49152) } }),
  ).rejects.toThrow();
  expect(f.frames).toHaveLength(0);
});
