import os from 'node:os';
import path from 'node:path';
import { mkdtemp, mkdir, writeFile, readFile, readdir, rm } from 'node:fs/promises';
import type { CodeReviewResult } from 'librechat-data-provider';
import type { ReviewServiceConfig } from './transport';
import { createReviewService, createReviewClient } from './transport';

const url = 'http://127.0.0.1:9876/review';
const token = 'offline-fixture-credential-not-a-real-secret';
const request = { repository: 'fixture', base: 'a'.repeat(40), head: 'b'.repeat(40) };
const principal = { userId: 'fixture-user', tenantId: 'fixture-tenant' };
const model = 'gpt-5.6-sol';
const result: CodeReviewResult = {
  ...request,
  status: 'human_review_required',
  provider: 'chatgpt_subscription',
  model,
  findings: [],
};
const fixture = `#!/usr/bin/python3
import json, os, resource, subprocess, sys, time
from pathlib import Path
repo = Path(sys.argv[sys.argv.index('--repo') + 1])
assert resource.getrlimit(resource.RLIMIT_AS) == (4294967296, 4294967296)
assert not any(x in os.environ for x in ('OPENAI_API_KEY', 'CODING_EXECUTOR_TOKEN', 'HTTPS_PROXY'))
(repo / 'started').write_text(str(os.getpid()))
if (repo / 'scenario').read_text() == 'hang':
    child = subprocess.Popen(['/usr/bin/python3', '-c', 'import time; time.sleep(300)'])
    (repo / 'descendant').write_text(str(child.pid))
    time.sleep(300)
print(json.dumps(dict(ok=True, mode='review', base=sys.argv[sys.argv.index('--base') + 1],
    head=sys.argv[sys.argv.index('--head') + 1], status='human_review_required',
    provider='chatgpt_subscription', model=os.environ['CODING_OPENHANDS_MODEL'],
    finding_count=0, findings=[])))
`;

function incoming(body: string, overrides: RequestInit = {}) {
  return new Request(url, {
    method: 'POST',
    headers: { authorization: `Bearer ${token}`, 'content-type': 'application/json' },
    body,
    ...overrides,
  });
}

async function until(check: () => Promise<boolean>) {
  for (let attempt = 0; attempt < 200; attempt++) {
    if (await check()) return;
    await new Promise((resolve) => setTimeout(resolve, 10));
  }
  throw new Error('fixture did not settle');
}

describe('offline review transport composed with the real worker', () => {
  let root: string;
  let repo: string;
  let scratch: string;
  let config: ReviewServiceConfig;

  beforeEach(async () => {
    root = await mkdtemp(path.join(os.tmpdir(), 'review-transport-'));
    repo = path.join(root, 'repo');
    scratch = path.join(root, 'scratch');
    const auth = path.join(root, 'empty-auth');
    await Promise.all([mkdir(repo), mkdir(scratch, { mode: 0o700 }), mkdir(auth)]);
    const python = path.join(root, 'fixture');
    await writeFile(python, fixture, { mode: 0o700 });
    await writeFile(path.join(repo, 'scenario'), 'success');
    config = {
      enabled: true,
      url,
      token,
      worker: {
        python,
        sourceRoot: root,
        scratchRoot: scratch,
        authRoot: auth,
        model,
        repositories: new Map([['fixture', repo]]),
        authorize: async (identity, repository) =>
          identity.userId === principal.userId &&
          identity.tenantId === principal.tenantId &&
          repository === request.repository,
      },
    };
  });

  afterEach(async () => {
    await until(async () => (await readdir(scratch)).length === 0);
    await rm(root, { recursive: true, force: true });
  });

  function client(service = createReviewService(config)) {
    return createReviewClient({ enabled: true, url, token, model, send: service });
  }

  it('round trips through authentication, authorization, OS limits and exact identity', async () => {
    const authorize = jest.fn(config.worker.authorize);
    const service = createReviewService({ ...config, worker: { ...config.worker, authorize } });
    await expect(client(service).run(request, principal)).resolves.toEqual(result);
    expect(authorize).toHaveBeenCalledWith(principal, 'fixture');
    expect(await readdir(repo)).toEqual(['scenario', 'started']);
  });

  it('defaults to disabled without configuration reads or requests', async () => {
    const send = jest.fn(
      createReviewService({ ...config, enabled: undefined, token: '', url: '' }),
    );
    await expect(
      createReviewClient({ url: '', token: '', model, send }).run(request, principal),
    ).rejects.toMatchObject({ code: 'configuration' });
    expect(send).not.toHaveBeenCalled();
    const response = await send(incoming(JSON.stringify({ request, principal })));
    expect(response.status).toBe(503);
    expect(await readdir(repo)).toEqual(['scenario']);
  });

  it.each(['', 'Bearer wrong', `Bearer ${token}x`])(
    'rejects incorrect credentials %s before authorization',
    async (authorization) => {
      const authorize = jest.fn(config.worker.authorize);
      const service = createReviewService({ ...config, worker: { ...config.worker, authorize } });
      const response = await service(
        incoming('{}', { headers: { authorization, 'content-type': 'application/json' } }),
      );
      expect(response.status).toBe(403);
      expect(authorize).not.toHaveBeenCalled();
    },
  );

  it('rejects the wrong destination or method', async () => {
    const service = createReviewService(config);
    const response = await service(new Request('http://127.0.0.1:9876/other', { method: 'POST' }));
    expect(response.status).toBe(400);
    expect((await service(new Request(url))).status).toBe(400);
    expect(await readdir(repo)).toEqual(['scenario']);
  });

  it.each([
    { ...principal, tenantId: 'other-tenant' },
    { ...principal, userId: 'other-user' },
  ])('rejects unauthorized forwarded identity %j', async (identity) => {
    await expect(client().run(request, identity)).rejects.toMatchObject({ code: 'forbidden' });
    expect(await readdir(repo)).toEqual(['scenario']);
  });

  it('rejects unknown repositories before spawning', async () => {
    await expect(
      client().run({ ...request, repository: 'other' }, principal),
    ).rejects.toMatchObject({ code: 'forbidden' });
    expect(await readdir(repo)).toEqual(['scenario']);
  });

  it.each([
    { request: { ...request, path: '/arbitrary' }, principal },
    { request, principal, command: 'publish' },
    { request, principal: { ...principal, role: 'admin' } },
    { request: { ...request, head: 'HEAD' }, principal },
    { request, principal: { ...principal, tenantId: '' } },
  ])('rejects hostile envelope fields %j', async (body) => {
    const response = await createReviewService(config)(incoming(JSON.stringify(body)));
    expect(response.status).toBe(400);
    expect(await readdir(repo)).toEqual(['scenario']);
  });

  it.each(['{', ' '.repeat(4097)])('bounds and validates request bodies', async (body) => {
    const response = await createReviewService(config)(incoming(body));
    expect(response.status).toBe(400);
    expect(await readdir(repo)).toEqual(['scenario']);
  });

  it('rejects pre-cancelled work without starting the child', async () => {
    const controller = new AbortController();
    controller.abort();
    await expect(client().run(request, principal, controller.signal)).rejects.toMatchObject({
      code: 'cancelled',
    });
    expect(await readdir(repo)).toEqual(['scenario']);
  });

  it('cancels descendants, cleans scratch, rejects busy and releases its slot', async () => {
    await writeFile(path.join(repo, 'scenario'), 'hang');
    const remote = client();
    const controller = new AbortController();
    const pending = remote
      .run(request, principal, controller.signal)
      .catch((error: Error) => error);
    await until(async () => (await readdir(repo)).includes('descendant'));
    const pid = Number(await readFile(path.join(repo, 'started'), 'utf8'));
    const descendant = Number(await readFile(path.join(repo, 'descendant'), 'utf8'));
    await expect(remote.run(request, principal)).rejects.toMatchObject({ code: 'busy' });
    controller.abort();
    expect(await pending).toMatchObject({ code: 'cancelled' });
    await until(async () => (await readdir(scratch)).length === 0);
    expect(() => process.kill(pid, 0)).toThrow();
    const state = await readFile(`/proc/${descendant}/stat`, 'utf8').catch(() => '');
    expect(state).toMatch(/^$|^\d+ \(.+\) Z /);
    await writeFile(path.join(repo, 'scenario'), 'success');
    await expect(remote.run(request, principal)).resolves.toEqual(result);
  });

  it('bounds hanging authorization without accumulating requests or spawning later', async () => {
    let release: (allowed: boolean) => void = () => undefined;
    const authorize = jest.fn(
      () =>
        new Promise<boolean>((resolve) => {
          release = resolve;
        }),
    );
    const remote = client(
      createReviewService({ ...config, worker: { ...config.worker, authorize } }),
    );
    const realTimeout = global.setTimeout;
    jest
      .spyOn(global, 'setTimeout')
      .mockImplementation(((callback: () => void, ms?: number) =>
        realTimeout(callback, ms === 165000 ? 30 : ms)) as typeof setTimeout);
    await expect(remote.run(request, principal)).rejects.toMatchObject({ code: 'timeout' });
    await expect(remote.run(request, principal)).rejects.toMatchObject({ code: 'busy' });
    expect(authorize).toHaveBeenCalledTimes(1);
    release(true);
    await new Promise((resolve) => realTimeout(resolve, 20));
    expect(await readdir(repo)).toEqual(['scenario']);
  });
});

describe('bounded review client response contract', () => {
  it.each([
    { ...result, head: 'c'.repeat(40) },
    { ...result, repository: 'other' },
    { ...result, model: 'other' },
    { ...result, provider: 'other' },
    { ...result, status: 'approved' },
    { ...result, command: 'publish' },
    {
      ...result,
      findings: [
        {
          severity: 'major',
          path: '../outside',
          line: 1,
          title: 'bad',
          evidence: 'bad',
          recommendation: 'bad',
        },
      ],
    },
  ])('rejects mismatched or hostile results %j', async (body) => {
    const send = jest.fn<Promise<Response>, [Request]>(async () => Response.json(body));
    await expect(
      createReviewClient({ enabled: true, url, token, model, send }).run(request, principal),
    ).rejects.toMatchObject({ code: 'invalid_response' });
    expect(send).toHaveBeenCalledTimes(1);
    expect(send.mock.calls[0][0].redirect).toBe('error');
  });

  it.each([
    () => new Response('{', { headers: { 'content-type': 'application/json' } }),
    () => new Response(new Uint8Array([255]), { headers: { 'content-type': 'application/json' } }),
    () => Response.json({ code: 'busy', private: 'secret' }, { status: 409 }),
    () => Response.json({ code: 'busy' }, { status: 500 }),
    () => Response.json(result, { status: 201 }),
  ])('rejects malformed response or error envelopes', async (response) => {
    await expect(
      createReviewClient({ enabled: true, url, token, model, send: async () => response() }).run(
        request,
        principal,
      ),
    ).rejects.toMatchObject({ code: 'invalid_response' });
  });

  it('cancels a response body rejected by content type', async () => {
    const cancel = jest.fn();
    const send = async () =>
      new Response(new ReadableStream({ cancel }), {
        headers: { 'content-type': 'text/plain' },
      });
    await expect(
      createReviewClient({ enabled: true, url, token, model, send }).run(request, principal),
    ).rejects.toMatchObject({ code: 'invalid_response' });
    expect(cancel).toHaveBeenCalled();
  });

  it('enforces output bytes and cancels its response stream', async () => {
    const cancel = jest.fn();
    const body = new ReadableStream({
      start(controller) {
        controller.enqueue(new Uint8Array(128001));
      },
      cancel,
    });
    const send = async () =>
      new Response(body, { headers: { 'content-type': 'application/json' } });
    await expect(
      createReviewClient({ enabled: true, url, token, model, send }).run(request, principal),
    ).rejects.toMatchObject({ code: 'output_limit' });
    expect(cancel).toHaveBeenCalled();
  });

  it('bounds a stalled response body', async () => {
    const cancel = jest.fn();
    const realTimeout = global.setTimeout;
    jest
      .spyOn(global, 'setTimeout')
      .mockImplementation(((callback: () => void, ms?: number) =>
        realTimeout(callback, ms === 170000 ? 20 : ms)) as typeof setTimeout);
    const send = async () =>
      new Response(new ReadableStream({ cancel }), {
        headers: { 'content-type': 'application/json' },
      });
    await expect(
      createReviewClient({ enabled: true, url, token, model, send }).run(request, principal),
    ).rejects.toMatchObject({ code: 'timeout' });
    expect(cancel).toHaveBeenCalled();
  });

  it('sanitizes network failures and never retries', async () => {
    const send = jest.fn(async () => {
      throw new Error('PRIVATE_CREDENTIAL');
    });
    await expect(
      createReviewClient({ enabled: true, url, token, model, send }).run(request, principal),
    ).rejects.toMatchObject({
      code: 'worker_failed',
      message: 'Code review failed: worker_failed',
    });
    expect(send).toHaveBeenCalledTimes(1);
  });

  it.each([
    'http://example.com/review',
    'https://user:pass@example.com/review',
    'https://example.com/review?token=bad',
    'https://example.com/other',
  ])('rejects unsafe configuration %s', (destination) => {
    expect(() => createReviewClient({ enabled: true, url: destination, token, model })).toThrow(
      'configuration',
    );
  });
});
