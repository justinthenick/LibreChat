import os from 'node:os';
import path from 'node:path';
import fs from 'node:fs/promises';
import { mkdtemp, mkdir, writeFile, readFile, readdir, rm } from 'node:fs/promises';
import type { ReviewWorkerConfig } from './worker';
import { createReviewDiagnosticLog } from './diagnostic-log';
import { createCodeReviewWorker } from './worker';
import { reviewRunIdSchema } from './identity';

const request = { repository: 'librechat', base: 'a'.repeat(40), head: 'b'.repeat(40) };
const principal = { userId: 'operator', tenantId: 'test' };
const fixture = `#!/usr/bin/python3
import json, os, resource, subprocess, sys, time
from pathlib import Path
repo = Path(sys.argv[sys.argv.index('--repo') + 1])
scenario = (repo / 'scenario').read_text()
(repo / 'started').write_text(str(os.getpid()))
assert resource.getrlimit(resource.RLIMIT_AS) == (4294967296, 4294967296)
assert resource.getrlimit(resource.RLIMIT_CPU) == (120, 120)
assert resource.getrlimit(resource.RLIMIT_CORE) == (0, 0)
assert resource.getrlimit(resource.RLIMIT_NOFILE) == (128, 128)
assert not any(name in os.environ for name in ('CODING_EXECUTOR_TOKEN', 'OPENAI_API_KEY', 'HTTPS_PROXY', 'NODE_OPTIONS'))
if scenario == 'hang':
    descendant = subprocess.Popen(['/usr/bin/python3', '-c', 'import time; time.sleep(300)'])
    (repo / 'grandchild').write_text(str(descendant.pid))
    time.sleep(300)
if scenario == 'stdout':
    print('x' * 200000)
    sys.exit(0)
if scenario == 'stderr':
    sys.stderr.write('PRIVATE_VALUE' * 10000)
    sys.exit(1)
if scenario == 'memory':
    bytearray(5 * 1024 * 1024 * 1024)
if scenario == 'fragmented':
    os.write(3, b'evidence_')
    time.sleep(0.02)
    os.write(3, b'validated\\nCANARY\\nprovider_ready\\n')
if scenario == 'flood':
    os.write(3, b'CANARY' * 200)
    os.write(3, b'\\nprovider_ready\\n')
if scenario == 'stages':
    os.write(3, b'evidence_validated\\nprovider_ready\\nconversation_started\\nconversation_finished\\nresult_validated\\n')
if scenario == 'stage_failure':
    os.write(3, b'evidence_validated\\nprovider_ready\\nconversation_started\\nPRIVATE_VALUE\\n')
    print('PRIVATE_VALUE', file=sys.stderr)
    sys.exit(1)
if scenario == 'failure':
    print('PRIVATE_VALUE', file=sys.stderr)
    sys.exit(1)
if scenario == 'unicode':
    sys.stdout.buffer.write(bytes([255]))
    sys.exit(0)
payload = {
    'ok': True, 'mode': 'review', 'base': 'a' * 40, 'head': 'b' * 40,
    'status': 'human_review_required', 'provider': 'chatgpt_subscription',
    'model': os.environ['CODING_OPENHANDS_MODEL'], 'finding_count': 0, 'findings': [],
}
if scenario == 'stale': payload['head'] = 'c' * 40
if scenario == 'model': payload['model'] = 'different-model'
if scenario == 'approve': payload['status'] = 'approved'
if scenario == 'count': payload['finding_count'] = 1
if scenario == 'extra': payload['command'] = 'publish'
if scenario == 'truncated':
    print('{')
    sys.exit(0)
print(json.dumps(payload))
`;

describe('code review worker with real isolated processes', () => {
  let root: string;
  let repo: string;
  let scratch: string;
  let config: ReviewWorkerConfig;

  beforeEach(async () => {
    root = await mkdtemp(path.join(os.tmpdir(), 'review-worker-test-'));
    repo = path.join(root, 'repo');
    scratch = path.join(root, 'scratch');
    const auth = path.join(root, 'auth');
    await Promise.all([mkdir(repo), mkdir(scratch, { mode: 0o700 }), mkdir(auth)]);
    const python = path.join(root, 'fixture');
    await writeFile(python, fixture, { mode: 0o700 });
    await writeFile(path.join(repo, 'scenario'), 'success');
    config = {
      python,
      sourceRoot: root,
      scratchRoot: scratch,
      authRoot: auth,
      model: 'gpt-5.6-sol',
      repositories: new Map([['librechat', repo]]),
      authorize: async () => true,
    };
  });

  afterEach(async () => {
    if ((await readdir(scratch)).length !== 0) {
      throw new Error('Review scratch was not cleaned');
    }
    await rm(root, { recursive: true, force: true });
  });

  async function started(filename = 'started') {
    for (let attempt = 0; attempt < 100; attempt++) {
      try {
        return Number(await readFile(path.join(repo, filename), 'utf8'));
      } catch {
        await new Promise((resolve) => setTimeout(resolve, 10));
      }
    }
    throw new Error('fixture did not start');
  }

  it('runs with OS limits and a cleared environment, returning human-review status', async () => {
    process.env.CODING_EXECUTOR_TOKEN = 'PRIVATE_VALUE';
    process.env.OPENAI_API_KEY = 'PRIVATE_VALUE';
    try {
      const result = await createCodeReviewWorker(config).run(request, principal);
      expect(result).toEqual({
        ...request,
        status: 'human_review_required',
        provider: 'chatgpt_subscription',
        model: 'gpt-5.6-sol',
        findings: [],
      });
    } finally {
      delete process.env.CODING_EXECUTOR_TOKEN;
      delete process.env.OPENAI_API_KEY;
    }
  });

  it.each(['stale', 'model', 'approve', 'count', 'extra', 'truncated', 'unicode'])(
    'rejects %s output',
    async (scenario) => {
      await writeFile(path.join(repo, 'scenario'), scenario);
      await expect(createCodeReviewWorker(config).run(request, principal)).rejects.toMatchObject({
        code: 'invalid_response',
      });
    },
  );

  it.each(['stdout', 'stderr'])(
    'bounds %s without returning sensitive content',
    async (scenario) => {
      await writeFile(path.join(repo, 'scenario'), scenario);
      await expect(createCodeReviewWorker(config).run(request, principal)).rejects.toMatchObject({
        code: 'output_limit',
        message: 'Code review failed: output_limit',
      });
    },
  );

  it.each(['failure', 'memory'])('fails closed on %s', async (scenario) => {
    await writeFile(path.join(repo, 'scenario'), scenario);
    await expect(createCodeReviewWorker(config).run(request, principal)).rejects.toMatchObject({
      code: 'worker_failed',
      message: 'Code review failed: worker_failed',
    });
  });

  it('captures allowlisted stages and bounded exit counts without child text', async () => {
    await writeFile(path.join(repo, 'scenario'), 'stages');
    const events: import('./worker').ReviewWorkerDiagnostic[] = [];
    const worker = createCodeReviewWorker({
      ...config,
      onDiagnostic: (event) => events.push(event),
    });
    await expect(worker.run(request, principal)).resolves.toMatchObject({
      status: 'human_review_required',
    });
    expect(events.filter((event) => event.type === 'stage').map((event) => event.stage)).toEqual([
      'evidence_validated',
      'provider_ready',
      'conversation_started',
      'conversation_finished',
      'result_validated',
      'schema_validated',
    ]);
    expect(events.find((event) => event.type === 'exit')).toMatchObject({
      exitCode: 0,
      signal: null,
      classification: 'success',
    });
    expect(JSON.stringify(events)).not.toContain('PRIVATE_VALUE');
  });

  it('keeps provider stderr secret and reports only fixed failed-exit diagnostics', async () => {
    await writeFile(path.join(repo, 'scenario'), 'stage_failure');
    const events: import('./worker').ReviewWorkerDiagnostic[] = [];
    const worker = createCodeReviewWorker({
      ...config,
      onDiagnostic: (event) => events.push(event),
    });
    await expect(worker.run(request, principal)).rejects.toMatchObject({
      code: 'worker_failed',
    });
    expect(events.filter((event) => event.type === 'stage').map((event) => event.stage)).toEqual([
      'evidence_validated',
      'provider_ready',
      'conversation_started',
    ]);
    expect(events.find((event) => event.type === 'exit')).toMatchObject({
      exitCode: 1,
      classification: 'worker_failed',
    });
    expect(JSON.stringify(events)).not.toContain('PRIVATE_VALUE');
  });

  it('ignores a throwing diagnostics sink without changing the review result', async () => {
    const worker = createCodeReviewWorker({
      ...config,
      onDiagnostic: () => {
        throw new Error('PRIVATE_VALUE');
      },
    });
    await expect(worker.run(request, principal)).resolves.toMatchObject({
      status: 'human_review_required',
    });
  });

  it.each(['success', 'stage_failure'])(
    'ignores rejected asynchronous diagnostic sinks during %s',
    async (scenario) => {
      await writeFile(path.join(repo, 'scenario'), scenario);
      let calls = 0;
      const worker = createCodeReviewWorker({
        ...config,
        onDiagnostic: async () => {
          calls++;
          await Promise.resolve();
          throw new Error('PRIVATE_VALUE');
        },
      });
      if (scenario === 'success') {
        await expect(worker.run(request, principal)).resolves.toMatchObject({
          status: 'human_review_required',
        });
      } else {
        await expect(worker.run(request, principal)).rejects.toMatchObject({
          code: 'worker_failed',
          message: 'Code review failed: worker_failed',
        });
      }
      await new Promise<void>((resolve) => setImmediate(resolve));
      expect(calls).toBeGreaterThan(0);
    },
  );

  it.each([
    'success',
    'stale',
    'truncated',
    'unicode',
    'failure',
    'stdout',
    'stderr',
    'fragmented',
    'flood',
  ])('composes the private sink with real offline worker %s', async (scenario) => {
    await writeFile(path.join(repo, 'scenario'), scenario);
    const directory = path.join(root, 'logs');
    await mkdir(directory, { mode: 0o700 });
    const sink = await createReviewDiagnosticLog({
      directory,
      protectedRoots: [repo, scratch, config.authRoot],
    });
    const worker = createCodeReviewWorker({ ...config, onDiagnostic: sink.onDiagnostic });
    const id = '12345678-1234-4123-8123-123456789abc';
    try {
      const outcome = await worker.run(request, principal, undefined, id).catch((error) => error);
      if (['success', 'fragmented', 'flood'].includes(scenario)) {
        expect(outcome.status).toBe('human_review_required');
      } else {
        expect(outcome.code).toBeDefined();
      }
    } finally {
      await sink.close();
    }
    const text = await readFile(path.join(directory, 'review-diagnostics.jsonl'), 'utf8');
    const events = text
      .trim()
      .split('\n')
      .map((line) => JSON.parse(line));
    expect(events.every((event) => event.reviewId === id)).toBe(true);
    expect(text).not.toMatch(/CANARY|PRIVATE_VALUE/);
    expect(events.filter((event) => event.type === 'child_exit')).toHaveLength(1);
    if (['stale', 'truncated', 'unicode'].includes(scenario)) {
      expect(events.find((event) => event.type === 'child_exit').classification).toBe('success');
      expect(events.some((event) => event.stage === 'schema_validated')).toBe(false);
    }
    if (scenario === 'fragmented') {
      expect(events.filter((event) => event.type === 'stage').map((event) => event.stage)).toEqual([
        'evidence_validated',
        'provider_ready',
        'schema_validated',
      ]);
    }
    if (scenario === 'flood') {
      expect(events.filter((event) => event.type === 'stage').map((event) => event.stage)).toEqual([
        'schema_validated',
      ]);
    }
    expect(await readdir(config.authRoot)).toEqual([]);
  });

  it.each(['cancelled', 'timeout'])(
    'records %s without weakening process cleanup',
    async (failure) => {
      await writeFile(path.join(repo, 'scenario'), 'hang');
      const directory = path.join(root, 'logs');
      await mkdir(directory, { mode: 0o700 });
      const sink = await createReviewDiagnosticLog({
        directory,
        protectedRoots: [repo, scratch, config.authRoot],
      });
      if (failure === 'timeout') {
        const realTimeout = global.setTimeout;
        jest
          .spyOn(global, 'setTimeout')
          .mockImplementation(((callback: () => void, milliseconds?: number) =>
            realTimeout(
              callback,
              milliseconds === 150000 ? 200 : milliseconds,
            )) as typeof setTimeout);
      }
      const controller = new AbortController();
      const running = createCodeReviewWorker({ ...config, onDiagnostic: sink.onDiagnostic })
        .run(request, principal, controller.signal)
        .catch((error) => error);
      if (failure === 'cancelled') {
        await started();
        controller.abort();
      }
      expect((await running).code).toBe(failure);
      await sink.close();
      const text = await readFile(path.join(directory, 'review-diagnostics.jsonl'), 'utf8');
      expect(JSON.parse(text.trim()).classification).toBe(failure);
      expect(await readdir(scratch)).toEqual([]);
    },
  );

  it.each(['success', 'failure'])('disk failure cannot alter worker %s', async (scenario) => {
    await writeFile(path.join(repo, 'scenario'), scenario);
    const directory = path.join(root, 'logs');
    await mkdir(directory, { mode: 0o700 });
    const original = fs.open;
    jest.spyOn(fs, 'open').mockImplementation(async (...args: Parameters<typeof fs.open>) => {
      const file = await original(...args);
      jest.spyOn(file, 'write').mockRejectedValue(new Error('PRIVATE_VALUE'));
      return file;
    });
    const sink = await createReviewDiagnosticLog({
      directory,
      protectedRoots: [repo, scratch, config.authRoot],
    });
    const result = await createCodeReviewWorker({ ...config, onDiagnostic: sink.onDiagnostic })
      .run(request, principal)
      .catch((error) => error);
    await sink.close();
    expect(sink.health().state).toBe('failed');
    if (scenario === 'success') expect(result.status).toBe('human_review_required');
    else expect(result.code).toBe('worker_failed');
  });

  it('validated diagnostics do not mask cleanup failure or retain the local slot', async () => {
    const events: import('./worker').ReviewWorkerDiagnostic[] = [];
    const worker = createCodeReviewWorker({
      ...config,
      onDiagnostic: (event) => events.push(event),
    });
    const remove = jest.spyOn(fs, 'rm').mockRejectedValueOnce(new Error('PRIVATE_VALUE'));
    await expect(worker.run(request, principal)).rejects.toMatchObject({ code: 'worker_failed' });
    expect(
      events.some((event) => event.type === 'stage' && event.stage === 'schema_validated'),
    ).toBe(true);
    remove.mockRestore();
    for (const name of await readdir(scratch))
      await rm(path.join(scratch, name), { recursive: true });
    await expect(worker.run(request, principal)).resolves.toMatchObject({
      status: 'human_review_required',
    });
  });

  it('records a fixed child-exit failure when the fixture executable cannot spawn', async () => {
    await writeFile(config.python, '#!/nonexistent/offline-fixture-interpreter\\n', {
      mode: 0o700,
    });
    const events: import('./worker').ReviewWorkerDiagnostic[] = [];
    await expect(
      createCodeReviewWorker({ ...config, onDiagnostic: (event) => events.push(event) }).run(
        request,
        principal,
      ),
    ).rejects.toMatchObject({ code: 'worker_failed' });
    expect(events.find((event) => event.type === 'exit')).toMatchObject({
      classification: 'worker_failed',
    });
    expect(JSON.stringify(events)).not.toContain('offline-fixture-interpreter');
  });

  it.each([
    '00000000-0000-0000-0000-000000000000',
    'FFFFFFFF-FFFF-FFFF-FFFF-FFFFFFFFFFFF',
    ...Array.from(
      '0123456789abcdef',
      (nibble) => `12345678-9AbC-${nibble}123-${nibble}123-123456789AbC`,
    ),
  ])('preserves admission UUID %s through worker events and private logs', async (reviewId) => {
    const canonical = reviewRunIdSchema.parse(reviewId);
    const events: import('./worker').ReviewWorkerDiagnostic[] = [];
    const directory = path.join(root, 'uuid-logs');
    await mkdir(directory, { mode: 0o700 });
    const sink = await createReviewDiagnosticLog({
      directory,
      protectedRoots: [repo, scratch, config.authRoot],
    });
    try {
      const worker = createCodeReviewWorker({
        ...config,
        onDiagnostic: (event) => {
          events.push(event);
          sink.onDiagnostic(event);
        },
      });
      await expect(worker.run(request, principal, undefined, reviewId)).resolves.toMatchObject({
        status: 'human_review_required',
      });
    } finally {
      await sink.close();
    }
    expect(events.some((event) => event.type === 'stage')).toBe(true);
    expect(events.some((event) => event.type === 'exit')).toBe(true);
    expect(events.every((event) => event.reviewId === canonical)).toBe(true);
    const text = await readFile(path.join(directory, 'review-diagnostics.jsonl'), 'utf8');
    const rows = text
      .trim()
      .split('\n')
      .map((line) => JSON.parse(line));
    expect(rows).toHaveLength(events.length);
    expect(rows.every((row) => row.reviewId === canonical)).toBe(true);
    expect(text).not.toMatch(/CANARY|PRIVATE_VALUE/);
  });

  it('redacts arbitrary direct-caller review IDs before invoking any observer', async () => {
    const events: import('./worker').ReviewWorkerDiagnostic[] = [];
    await createCodeReviewWorker({ ...config, onDiagnostic: (event) => events.push(event) }).run(
      request,
      principal,
      undefined,
      'CANARY\nsecret',
    );
    expect(events.length).toBeGreaterThan(0);
    expect(events.every((event) => event.reviewId === null)).toBe(true);
  });

  it('rejects unexpected request fields before authorization or spawn', async () => {
    const authorize = jest.fn(config.authorize);
    await expect(
      createCodeReviewWorker({ ...config, authorize }).run(
        { ...request, path: '/arbitrary' } as typeof request,
        principal,
      ),
    ).rejects.toMatchObject({ code: 'invalid_request' });
    expect(authorize).not.toHaveBeenCalled();
    expect(await readdir(repo)).toEqual(['scenario']);
  });

  it.each(['HEAD', 'a'.repeat(39), 'a'.repeat(40) + '; echo unsafe', 'a'.repeat(40) + '\n'])(
    'rejects non-SHA %s',
    async (head) => {
      await expect(
        createCodeReviewWorker(config).run({ ...request, head }, principal),
      ).rejects.toMatchObject({ code: 'invalid_request' });
      expect(await readdir(repo)).toEqual(['scenario']);
    },
  );

  it('requires repository and tenant-aware authorization before spawn', async () => {
    const authorize = jest.fn(async () => false);
    const worker = createCodeReviewWorker({ ...config, authorize });
    await expect(worker.run(request, principal)).rejects.toMatchObject({ code: 'forbidden' });
    expect(authorize).toHaveBeenCalledWith(principal, request.repository);
    await expect(worker.run({ ...request, repository: 'other' }, principal)).rejects.toMatchObject({
      code: 'forbidden',
    });
    expect(authorize).toHaveBeenCalledTimes(1);
    expect(await readdir(repo)).toEqual(['scenario']);
  });

  it('sanitizes authorization errors', async () => {
    const worker = createCodeReviewWorker({
      ...config,
      authorize: async () => {
        throw new Error('PRIVATE_VALUE');
      },
    });
    await expect(worker.run(request, principal)).rejects.toMatchObject({
      code: 'forbidden',
      message: 'Code review failed: forbidden',
    });
  });

  it('rejects already cancelled work before spawn', async () => {
    const controller = new AbortController();
    controller.abort();
    await expect(
      createCodeReviewWorker(config).run(request, principal, controller.signal),
    ).rejects.toMatchObject({ code: 'cancelled' });
    expect(await readdir(repo)).toEqual(['scenario']);
  });

  it('cancels the process group, rejects concurrent work, and releases its slot', async () => {
    await writeFile(path.join(repo, 'scenario'), 'hang');
    const worker = createCodeReviewWorker(config);
    const controller = new AbortController();
    const running = worker.run(request, principal, controller.signal);
    const rejected = running.catch((error: Error) => error);
    const pid = await started();
    const descendant = await started('grandchild');
    await expect(worker.run(request, principal)).rejects.toMatchObject({ code: 'busy' });
    controller.abort();
    expect(await rejected).toMatchObject({ code: 'cancelled' });
    const descendantState = await readFile(`/proc/${descendant}/stat`, 'utf8').catch(() => '');
    expect(descendantState).toMatch(/^$|^\d+ \(.+\) Z /);
    expect(() => process.kill(pid, 0)).toThrow();
    await writeFile(path.join(repo, 'scenario'), 'success');
    await expect(worker.run(request, principal)).resolves.toMatchObject({
      status: 'human_review_required',
    });
  });

  it('enforces the wall-clock deadline independently of Python', async () => {
    await writeFile(path.join(repo, 'scenario'), 'hang');
    const realTimeout = global.setTimeout;
    jest
      .spyOn(global, 'setTimeout')
      .mockImplementation(((callback: () => void, milliseconds?: number) =>
        realTimeout(callback, milliseconds === 150000 ? 100 : milliseconds)) as typeof setTimeout);
    await expect(createCodeReviewWorker(config).run(request, principal)).rejects.toMatchObject({
      code: 'timeout',
    });
  });
});
