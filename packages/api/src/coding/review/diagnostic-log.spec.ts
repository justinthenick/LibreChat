import os from 'node:os';
import path from 'node:path';
import fs from 'node:fs/promises';
import type { ReviewDiagnosticLog } from './diagnostic-log';
import type { ReviewWorkerDiagnostic } from './worker';
import { createReviewDiagnosticLog } from './diagnostic-log';
import { reviewRunIdSchema } from './identity';

const id = '12345678-1234-4123-8123-123456789abc';
const stage = { type: 'stage', stage: 'provider_ready', reviewId: id } as const;
describe('private operator diagnostic log', () => {
  let root: string, directory: string, protectedRoot: string;
  let sinks: ReviewDiagnosticLog[];
  const filename = () => path.join(directory, 'review-diagnostics.jsonl');
  const make = (extra = {}) =>
    createReviewDiagnosticLog({
      directory,
      protectedRoots: [protectedRoot],
      ...extra,
    }).then((sink) => {
      sinks.push(sink);
      return sink;
    });
  const records = async () =>
    (await fs.readFile(filename(), 'utf8'))
      .trim()
      .split('\n')
      .filter(Boolean)
      .map((line) => JSON.parse(line));
  beforeEach(async () => {
    root = await fs.mkdtemp(path.join(os.tmpdir(), 'diagnostic-log-test-'));
    directory = path.join(root, 'logs');
    protectedRoot = path.join(root, 'auth');
    await fs.mkdir(directory, { mode: 0o700 });
    await fs.mkdir(protectedRoot, { mode: 0o700 });
    sinks = [];
  });
  afterEach(async () => {
    await Promise.all(sinks.map((sink) => sink.close()));
    jest.restoreAllMocks();
    await fs.rm(root, { recursive: true, force: true });
  });

  it('records only allowlisted scalars in a private new file', async () => {
    const sink = await make();
    sink.onDiagnostic({
      ...stage,
      secret: 'CANARY',
      stderr: 'CANARY',
      toJSON: () => 'CANARY',
    } as ReviewWorkerDiagnostic);
    sink.onDiagnostic({
      type: 'exit',
      reviewId: id,
      exitCode: 0,
      signal: null,
      stdoutBytes: 999999,
      stderrBytes: 999999,
      classification: 'success',
    });
    await sink.close();
    const rows = await records();
    expect(rows[0]).toEqual({ version: 1, timestamp: expect.any(String), sequence: 1, ...stage });
    expect(rows[1]).toMatchObject({ type: 'child_exit', stdoutBytes: 128000, stderrBytes: 64000 });
    expect(await fs.readFile(filename(), 'utf8')).not.toContain('CANARY');
    expect((await fs.stat(filename())).mode & 0o777).toBe(0o600);
    expect(sink.health()).toMatchObject({ state: 'closed', accepted: 2, dropped: 0 });
  });

  it.each(['CANARY\nsecret', 'x'.repeat(100000), '', '12345678-1234-4123-g123-123456789abc'])(
    'replaces invalid correlation IDs with null (%s)',
    async (reviewId) => {
      const sink = await make();
      sink.onDiagnostic({ ...stage, reviewId });
      await sink.close();
      expect((await records())[0].reviewId).toBeNull();
    },
  );

  it.each([
    '00000000-0000-0000-0000-000000000000',
    'FFFFFFFF-FFFF-FFFF-FFFF-FFFFFFFFFFFF',
    ...Array.from(
      '0123456789abcdef',
      (nibble) => `12345678-9AbC-${nibble}123-${nibble}123-123456789AbC`,
    ),
  ])('uses admission grammar for direct log UUID %s', async (reviewId) => {
    const canonical = reviewRunIdSchema.parse(reviewId);
    const sink = await make();
    sink.onDiagnostic({ ...stage, reviewId });
    sink.onDiagnostic({
      type: 'exit',
      reviewId,
      exitCode: 0,
      signal: null,
      stdoutBytes: 1,
      stderrBytes: 0,
      classification: 'success',
    });
    await sink.close();
    const rows = await records();
    expect(rows).toHaveLength(2);
    expect(rows.every((row) => row.reviewId === canonical)).toBe(true);
  });

  it('drops unknown labels, malformed scalar fields and throwing getters', async () => {
    const sink = await make();
    const exit = {
      type: 'exit',
      exitCode: 0,
      signal: null,
      stdoutBytes: 1,
      stderrBytes: 2,
      classification: 'success',
    };
    for (const event of [
      { ...stage, stage: 'CANARY\nprovider_ready' },
      { ...stage, type: 'CANARY' },
      { ...exit, exitCode: -1 },
      { ...exit, exitCode: 256 },
      { ...exit, signal: 'CANARY' },
      { ...exit, classification: 'CANARY' },
      { ...exit, stdoutBytes: Infinity },
      { ...exit, stderrBytes: -1 },
      { ...exit, stdoutBytes: 1.5 },
      {
        get type() {
          throw new Error('CANARY');
        },
      },
      null,
    ])
      sink.onDiagnostic(event as ReviewWorkerDiagnostic);
    await sink.close();
    expect(await fs.readFile(filename(), 'utf8')).toBe('');
    expect(sink.health().dropped).toBe(11);
  });

  it('does not serialize values substituted by getters or signal objects', async () => {
    const sink = await make();
    let reads = 0;
    sink.onDiagnostic({
      type: 'stage',
      get stage() {
        return ++reads === 1 ? 'provider_ready' : { toJSON: () => 'CANARY' };
      },
    } as ReviewWorkerDiagnostic);
    sink.onDiagnostic({
      type: 'exit',
      exitCode: 0,
      signal: { toString: () => 'SIGKILL', toJSON: () => 'CANARY' },
      stdoutBytes: 0,
      stderrBytes: 0,
      classification: 'success',
    } as unknown as ReviewWorkerDiagnostic);
    await sink.close();
    expect(reads).toBe(1);
    expect(await fs.readFile(filename(), 'utf8')).not.toContain('CANARY');
    expect(sink.health().dropped).toBe(1);
  });

  it('bounds pending writes without waiting for disk', async () => {
    const original = fs.open;
    let release!: () => void;
    const blocked = new Promise<void>((resolve) => {
      release = resolve;
    });
    jest.spyOn(fs, 'open').mockImplementation(async (...args: Parameters<typeof fs.open>) => {
      const file = await original(...args);
      const write = file.write.bind(file);
      jest.spyOn(file, 'write').mockImplementation((async (...values: unknown[]) => {
        await blocked;
        return (write as (...args: unknown[]) => unknown)(...values);
      }) as typeof file.write);
      return file;
    });
    const sink = await make({ maxPendingRecords: 2 });
    for (let i = 0; i < 100; i++) sink.onDiagnostic(stage);
    await new Promise<void>((resolve) => setImmediate(resolve));
    expect(sink.health()).toMatchObject({ accepted: 2, dropped: 98, writtenBytes: 0 });
    release();
    await sink.close();
    expect((await records()).length).toBe(2);
  });

  it('stops at capacity and never truncates or reopens retained evidence', async () => {
    const sink = await make({ maxBytes: 1024 });
    for (let i = 0; i < 40; i++) sink.onDiagnostic(stage);
    await sink.close();
    expect(sink.health().state).toBe('capacity');
    expect((await fs.stat(filename())).size).toBeLessThanOrEqual(1024);
    const original = await fs.readFile(filename());
    await expect(make()).rejects.toThrow('configuration unavailable');
    expect(await fs.readFile(filename())).toEqual(original);
  });

  it('handles partial writes and preserves line ordering', async () => {
    const original = fs.open;
    jest.spyOn(fs, 'open').mockImplementation(async (...args: Parameters<typeof fs.open>) => {
      const file = await original(...args);
      const write = file.write.bind(file);
      jest
        .spyOn(file, 'write')
        .mockImplementation((async (buffer: Buffer, offset: number, length: number) =>
          write(buffer, offset, Math.min(length, 7))) as typeof file.write);
      return file;
    });
    const sink = await make();
    sink.onDiagnostic(stage);
    sink.onDiagnostic(stage);
    await sink.close();
    expect((await records()).map((row) => row.sequence)).toEqual([1, 2]);
  });

  it.each(['throw', 'zero'])(
    'contains %s write failures without emitting errors or retrying',
    async (mode) => {
      const original = fs.open;
      const write = jest.fn(async () => {
        if (mode === 'throw') throw new Error('CANARY disk error');
        return { bytesWritten: 0, buffer: Buffer.alloc(0) };
      });
      jest.spyOn(fs, 'open').mockImplementation(async (...args: Parameters<typeof fs.open>) => {
        const file = await original(...args);
        jest.spyOn(file, 'write').mockImplementation(write as unknown as typeof file.write);
        return file;
      });
      const sink = await make();
      sink.onDiagnostic(stage);
      sink.onDiagnostic(stage);
      await sink.close();
      expect(sink.health()).toMatchObject({ state: 'failed', writtenBytes: 0 });
      expect(write).toHaveBeenCalledTimes(1);
      expect(JSON.stringify(sink.health())).not.toContain('CANARY');
    },
  );

  it('closes once, drains accepted records and rejects later events', async () => {
    const sink = await make();
    sink.onDiagnostic(stage);
    const closed = sink.close();
    expect(sink.close()).toBe(closed);
    sink.onDiagnostic(stage);
    await closed;
    expect((await records()).length).toBe(1);
    expect(sink.health().dropped).toBe(1);
  });

  it.each([0o755, 0o770, 0o777])('rejects directory mode %s', async (mode) => {
    await fs.chmod(directory, mode);
    await expect(make()).rejects.toThrow('configuration unavailable');
  });
  it('rejects mismatched directory ownership', async () => {
    const original = fs.lstat;
    jest.spyOn(fs, 'lstat').mockImplementation((async (name: string) => {
      const stat = await original(name);
      if (name === directory) stat.uid += 1;
      return stat;
    }) as typeof fs.lstat);
    await expect(make()).rejects.toThrow('configuration unavailable');
  });
  it('rejects symlink directories and Git ancestry', async () => {
    const alias = path.join(root, 'alias');
    await fs.symlink(directory, alias);
    await expect(make({ directory: alias })).rejects.toThrow('configuration unavailable');
    await fs.writeFile(path.join(root, '.git'), 'gitdir: CANARY');
    await expect(make()).rejects.toThrow('configuration unavailable');
  });
  it('rejects files, hardlinks, symlinks and nonempty directories without changing them', async () => {
    await fs.writeFile(path.join(protectedRoot, 'retained'), 'CANARY');
    await fs.symlink(path.join(protectedRoot, 'retained'), filename());
    await expect(make()).rejects.toThrow('configuration unavailable');
    await fs.unlink(filename());
    await fs.link(path.join(protectedRoot, 'retained'), filename());
    await expect(make()).rejects.toThrow('configuration unavailable');
    expect(await fs.readFile(filename(), 'utf8')).toBe('CANARY');
    await fs.unlink(filename());
    await fs.mkdir(filename());
    await expect(make()).rejects.toThrow('configuration unavailable');
  });
  it('allows only one concurrent opener', async () => {
    const outcomes = await Promise.allSettled([make(), make()]);
    expect(outcomes.filter((outcome) => outcome.status === 'fulfilled')).toHaveLength(1);
  });
  it.each([
    { directory: 'relative' },
    { protectedRoots: [] },
    { maxBytes: 0 },
    { maxBytes: 16777217 },
    { maxPendingRecords: 0 },
    { maxPendingRecords: 257 },
  ])('rejects unsafe configuration %j', async (extra) => {
    await expect(make(extra)).rejects.toThrow('configuration unavailable');
  });
  it('rejects overlap with protected runtime roots', async () => {
    await expect(make({ protectedRoots: [directory] })).rejects.toThrow(
      'configuration unavailable',
    );
    await expect(make({ protectedRoots: [root] })).rejects.toThrow('configuration unavailable');
    const nested = path.join(directory, 'nested');
    await fs.mkdir(nested);
    await expect(make({ protectedRoots: [nested] })).rejects.toThrow('configuration unavailable');
  });
});
