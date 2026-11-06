/* Offline fixture: existing installed dependencies only; never used by the server. */
const { spawnSync } = require('node:child_process');
const { mkdtempSync, rmSync } = require('node:fs');
const os = require('node:os');
const path = require('node:path');
if (process.platform !== 'linux' || !process.env.REVIEW_TEST_PYTHON) {
  throw new Error(
    'Use Linux and set REVIEW_TEST_PYTHON to the installed orchestrator SDK interpreter.',
  );
}
const home = mkdtempSync(path.join(os.tmpdir(), 'review-contract-home-'));
try {
  const result = spawnSync(
    process.execPath,
    [
      '--test',
      '--test-concurrency=1',
      path.join(__dirname, 'contracts.test.cjs'),
      path.join(__dirname, 'restart.test.cjs'),
    ],
    {
      stdio: 'inherit',
      timeout: 240000,
      env: {
        PATH: `${path.dirname(process.execPath)}:/usr/bin:/bin`,
        HOME: home,
        NODE_ENV: 'test',
        REVIEW_TEST_PYTHON: process.env.REVIEW_TEST_PYTHON,
        NODE_OPTIONS: `--require=${JSON.stringify(path.join(__dirname, 'offline.cjs'))}`,
        OTEL_SDK_DISABLED: 'true',
      },
    },
  );
  if (result.error) throw result.error;
  if (result.status !== 0)
    throw new Error(`Offline review contracts failed: ${result.status ?? result.signal}`);
} finally {
  rmSync(home, { recursive: true, force: true });
}
