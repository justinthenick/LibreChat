/* Child-process fixture only; fake worker output and empty credential directory. */
const fs = require('node:fs/promises');
const path = require('node:path');
const { createServer } = require('node:http');
const subprocess = require('node:child_process');
const originalSpawn = subprocess.spawn;
let helper;
subprocess.spawn = (...args) => {
  const child = originalSpawn(...args);
  if (args[1]?.some((arg) => String(arg).endsWith('review_journal.py'))) helper = child;
  return child;
};
const {
  createReviewJournal,
  createReviewHttpHandler,
  createReviewDiagnosticLog,
} = require('@librechat/api/coding');
const dir = process.argv[2];
const mode = process.argv[3];
const root = path.resolve(__dirname, '../../../../..');
async function exists(name) {
  try {
    await fs.stat(path.join(dir, name));
    return true;
  } catch {
    return false;
  }
}
(async () => {
  const journal = await createReviewJournal({
    python:
      mode === 'admit-ack' || mode === 'finish-ack'
        ? path.join(dir, 'journal-python')
        : '/usr/bin/python3',
    sourceRoot: path.join(root, 'custom/coding-agent/orchestrator/src'),
    path: path.join(dir, 'private/reviews.sqlite'),
  });
  if (mode === 'cancel-before-finish') {
    const finish = journal.finish.bind(journal);
    journal.finish = async (id, principal, result) => {
      if (result) await journal.cancel(id, principal);
      return finish(id, principal, result);
    };
  }
  const logDirectory = await fs.mkdtemp(path.join(dir, 'diagnostics-'));
  const diagnosticLog = await createReviewDiagnosticLog({
    directory: logDirectory,
    maxBytes: 1024,
    protectedRoots: [
      path.join(dir, 'private'),
      path.join(dir, 'empty-auth'),
      path.join(dir, 'scratch'),
      path.join(dir, 'repository'),
    ],
  });
  if (mode === 'diagnostic-capacity') {
    for (let i = 0; i < 64; i++)
      diagnosticLog.onDiagnostic({ type: 'stage', stage: 'provider_ready' });
  }
  if (mode === 'diagnostic-closed') await diagnosticLog.close();
  const server = createServer();
  await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
  const url = `http://127.0.0.1:${server.address().port}/review`;
  server.on(
    'request',
    createReviewHttpHandler({
      enabled: true,
      url,
      token: 'offline-review-service-token-fixture',
      journal,
      worker: {
        onDiagnostic: diagnosticLog.onDiagnostic,
        python: path.join(dir, 'worker-python'),
        sourceRoot: path.join(root, 'custom/coding-agent/orchestrator/src'),
        scratchRoot: path.join(dir, 'scratch'),
        authRoot: path.join(dir, 'empty-auth'),
        model: mode === 'wrong-model' ? 'different-model' : 'fixture-model',
        repositories: new Map([['fixture', path.join(dir, 'repository')]]),
        authorize: async (principal, alias) => {
          if (mode === 'authorization') {
            await fs.writeFile(path.join(dir, 'authorizing'), '');
            while (await exists('auth-hold'))
              await new Promise((resolve) => setTimeout(resolve, 10));
          }
          return (
            ['alice', 'bob'].includes(principal.userId) &&
            principal.tenantId === 'tenant-a' &&
            alias === 'fixture'
          );
        },
      },
    }),
  );
  process.send({ url, helper: helper.pid, logDirectory });
})().catch(() => process.exit(1));
