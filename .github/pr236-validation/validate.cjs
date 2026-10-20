'use strict';
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const cp = require('node:child_process');
const assert = require('node:assert/strict');

const [sourceArg, evidenceArg, patchArg] = process.argv.slice(2);
const source = path.resolve(sourceArg);
const evidence = path.resolve(evidenceArg);
const patch = path.resolve(patchArg);
const workspace = path.join(source, 'packages/data-provider');
const expectedHead = '63f65f2a17e771bee79332c7537e7cdaf0eb536f';
const patchHash = '1a3132431cc7519fc3a00a4301140d8d86ca066f410a2589915bc3481381efbe';
const historicalHash = '52824158c3802b81fde03f4e96073e9670a61c468088a8b92d555ecd230510ff';
const names = ['mcp.spec.ts', 'parsers.spec.ts', 'request-interceptor-subdir.spec.ts'];
const files = names.map(name => 'packages/data-provider/specs/' + name);
const expectedHashes = [
  '05f16ad947cc8da7b637fc477bad832f79a0e1a057ca4d03b8a44b9b8475d7bf',
  'feabe898d6cb0bc31726f59bac0dda0fea03ae27a3a6f348386116d9c8a2b54f',
  '821dbe7d078abb1f400f803b494a15502ebd519fa830a8741ba9e52955a778be',
];
fs.mkdirSync(evidence, { recursive: true });
const hash = data => crypto.createHash('sha256').update(data).digest('hex');
const write = (name, value) => fs.writeFileSync(path.join(evidence, name), JSON.stringify(value, null, 2) + '\n');
const results = [];
const env = { ...process.env, PATH: path.join(source, 'node_modules/.bin') + path.delimiter + process.env.PATH };
delete env.FORCE_COLOR;
let failed = false;

function run(name, command, args, cwd = source, required = true, timeout = 300000) {
  const logPath = path.join(evidence, name + '.log');
  const fd = fs.openSync(logPath, 'w');
  const start = Date.now();
  let result;
  try {
    result = cp.spawnSync(command, args, { cwd, env, stdio: ['ignore', fd, fd], timeout, killSignal: 'SIGKILL' });
  } finally {
    fs.closeSync(fd);
  }
  const data = fs.readFileSync(logPath);
  const record = { name, command, args, cwd, exitCode: result.status, signal: result.signal, error: result.error?.message, elapsedMs: Date.now() - start, bytes: data.length, sha256: hash(data) };
  results.push(record);
  write('commands.json', results);
  console.log(JSON.stringify(record));
  console.log(data.toString('utf8'));
  if (required && (result.status !== 0 || result.error)) throw new Error(name + ' failed');
  return { ...record, text: data.toString('utf8') };
}

try {
  assert.equal(process.version, 'v24.16.0');
  assert.equal(hash(fs.readFileSync(patch)), patchHash);
  assert.equal(run('baseline-head', 'git', ['rev-parse', 'HEAD']).text.trim(), expectedHead);
  assert.equal(run('baseline-clean', 'git', ['status', '--porcelain']).text.trim(), '');
  const lockBytes = fs.readFileSync(path.join(source, 'package-lock.json'));
  const lock = JSON.parse(lockBytes);
  const manifest = JSON.parse(fs.readFileSync(path.join(source, 'package.json')));
  assert.equal(manifest.packageManager, 'npm@11.13.0');
  assert.equal(lock.packages['node_modules/typescript'].version, '5.9.3');
  write('lifecycle-review.json', {
    policy: 'All install lifecycle scripts disabled; none are required for these checks. Stop on missing native prerequisites; do not rebuild packages.',
    rootScripts: manifest.scripts,
    packagesWithInstallScripts: Object.entries(lock.packages).filter(([, value]) => value.hasInstallScript).map(([name, value]) => ({ name, version: value.version })),
  });
  write('provenance.json', { head: expectedHead, validationCommit: process.env.GITHUB_SHA, runId: process.env.GITHUB_RUN_ID, node: process.version, patchSha256: patchHash, lockSha256: hash(lockBytes), expectedHistoricalBaselineSha256: historicalHash });
  env.npm_config_cache = path.join(process.env.RUNNER_TEMP, 'pr236-npm-cache');
  const npmPrefix = path.join(process.env.RUNNER_TEMP, 'pr236-npm-11');
  run('npm-bootstrap', 'npm', ['install', '--prefix', npmPrefix, '--ignore-scripts', '--no-audit', '--no-fund', '--package-lock=false', 'npm@11.13.0'], process.env.RUNNER_TEMP);
  const npmCli = path.join(npmPrefix, 'node_modules/npm/bin/npm-cli.js');
  assert.equal(run('npm-version', process.execPath, [npmCli, '--version']).text.trim(), '11.13.0');
  run('dependency-install', process.execPath, [npmCli, 'ci', '--ignore-scripts', '--no-audit', '--no-fund'], source, true, 600000);
  assert.equal(hash(fs.readFileSync(path.join(source, 'package-lock.json'))), hash(lockBytes));
  assert.equal(run('typescript-version', 'tsc', ['--version']).text.trim(), 'Version 5.9.3');
  run('locked-tools', process.execPath, ['-e', "const fs = require('node:fs'); for (const p of ['typescript','jest','babel-jest','eslint','prettier','@happy-dom/jest-environment']) console.log(p + '@' + JSON.parse(fs.readFileSync('node_modules/' + p + '/package.json')).version)"]);
  const baseline = run('baseline-spec', 'tsc', ['--project', 'tsconfig.spec.json', '--noEmit', '--incremental', 'false'], workspace, false);
  const diagnostics = [...baseline.text.matchAll(/^(.+?)\((\d+),(\d+)\): error TS(\d+):/gm)].map(match => ({ file: match[1], line: Number(match[2]), column: Number(match[3]), code: Number(match[4]) }));
  const expectedCounts = { 'specs/mcp.spec.ts:2339': 4, 'specs/parsers.spec.ts:7053': 9, 'specs/request-interceptor-subdir.spec.ts:2790': 1 };
  const counts = {};
  for (const diagnostic of diagnostics) {
    const key = diagnostic.file + ':' + diagnostic.code;
    counts[key] = (counts[key] || 0) + 1;
  }
  write('baseline-comparison.json', { expectedCounts, actualCounts: counts, diagnostics, bytes: baseline.bytes, sha256: baseline.sha256, historicalHashMatches: baseline.sha256 === historicalHash });
  assert.equal(baseline.exitCode, 2, 'Unexpected baseline compiler exit');
  assert.deepEqual(counts, expectedCounts, 'Baseline diagnostic set differs');
  assert.equal(baseline.sha256, historicalHash, 'Baseline bytes differ; preserve evidence and stop for review');
  assert.equal(baseline.bytes, 2833);
  const jestArgs = ['--runInBand', '--runTestsByPath', ...names.map(name => 'specs/' + name)];
  env.JEST_JUNIT_OUTPUT_DIR = evidence;
  env.JEST_JUNIT_OUTPUT_NAME = 'baseline-junit.xml';
  failed = run('baseline-jest', 'jest', jestArgs, workspace, false).exitCode !== 0 || failed;
  run('patch-check', 'git', ['apply', '--check', patch]);
  run('patch-apply', 'git', ['apply', patch]);
  for (let index = 0; index < files.length; index++) assert.equal(hash(fs.readFileSync(path.join(source, files[index]))), expectedHashes[index]);
  const changed = run('changed-files', 'git', ['diff', '--name-only']).text.trim().split('\n').sort();
  assert.deepEqual(changed, [...files].sort());
  run('patch-whitespace', 'git', ['diff', '--check']);
  fs.writeFileSync(path.join(evidence, 'applied.patch'), run('applied-diff', 'git', ['diff']).text);
  failed = run('repaired-spec', 'tsc', ['--project', 'tsconfig.spec.json', '--noEmit', '--incremental', 'false'], workspace, false).exitCode !== 0 || failed;
  env.JEST_JUNIT_OUTPUT_NAME = 'repaired-junit.xml';
  failed = run('repaired-jest', 'jest', jestArgs, workspace, false).exitCode !== 0 || failed;
  failed = run('package-types', 'tsc', ['--project', 'tsconfig.json', '--noEmit', '--incremental', 'false'], workspace, false).exitCode !== 0 || failed;
  failed = run('scoped-lint', 'eslint', files, source, false).exitCode !== 0 || failed;
  failed = run('scoped-format', 'prettier', ['--check', ...files], source, false).exitCode !== 0 || failed;
  assert.equal(hash(fs.readFileSync(path.join(source, 'package-lock.json'))), hash(lockBytes));
  assert.deepEqual(run('final-changed-files', 'git', ['diff', '--name-only']).text.trim().split('\n').sort(), [...files].sort());
} catch (error) {
  failed = true;
  write('failure.json', { message: error.message, stack: error.stack });
  console.error(error);
} finally {
  write('result.json', { status: failed ? 'FAILED_OR_BLOCKED' : 'PASSED', commands: results });
  const hashes = fs.readdirSync(evidence).filter(name => fs.statSync(path.join(evidence, name)).isFile()).map(name => ({ name, sha256: hash(fs.readFileSync(path.join(evidence, name))) }));
  write('SHA256SUMS.json', hashes);
}
process.exitCode = failed ? 1 : 0;
