/* Uses an already approved toolchain. Installs nothing and creates no environment. */
const { spawnSync } = require('node:child_process');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

if (Number(process.versions.node.split('.')[0]) !== 24) {
  throw new Error('Run the preview fixture with the existing Node 24 toolchain.');
}
if (!process.env.PREVIEW_TEST_TOOLS || !process.env.PREVIEW_TEST_PYTHON) {
  throw new Error(
    'Set PREVIEW_TEST_TOOLS to the approved npm toolchain root and PREVIEW_TEST_PYTHON to the existing venv executable.',
  );
}
const tools = path.resolve(process.env.PREVIEW_TEST_TOOLS, 'node_modules');
const root = path.resolve(__dirname, '../../../../..');
const source = path.join(root, 'packages/api/src/coding/preview');
const typescript = require(path.join(tools, 'typescript'));
const repositoryConfig = typescript.readConfigFile(
  path.join(root, 'packages/api/tsconfig.json'),
  typescript.sys.readFile,
);
if (repositoryConfig.error) throw new Error('Cannot read the repository TypeScript config.');
const { target, lib } = repositoryConfig.config.compilerOptions;
if (
  typeof target !== 'string' ||
  !Array.isArray(lib) ||
  lib.some((name) => typeof name !== 'string')
) {
  throw new Error(
    'Expected explicit target and library settings in the repository TypeScript config.',
  );
}
const temporary = fs.mkdtempSync(path.join(os.tmpdir(), 'preview-http-build-'));
const build = path.join(temporary, 'compiled');
function run(script, args, env = process.env) {
  const result = spawnSync(process.execPath, [script, ...args], {
    cwd: root,
    env,
    stdio: 'inherit',
    timeout: 120000,
  });
  if (result.error) throw result.error;
  if (result.status !== 0)
    throw new Error(`Preview fixture command failed (${result.status ?? result.signal}).`);
}
try {
  run(path.join(tools, 'typescript/bin/tsc'), [
    '--strict',
    '--noEmitOnError',
    '--target',
    target,
    '--lib',
    lib.join(','),
    '--module',
    'commonjs',
    '--moduleResolution',
    'node',
    '--esModuleInterop',
    '--skipLibCheck',
    '--typeRoots',
    path.join(tools, '@types'),
    '--types',
    'node,express',
    '--rootDir',
    root,
    '--outDir',
    build,
    path.join(source, 'controller.ts'),
    path.join(source, 'types.ts'),
  ]);
  run(
    path.join(tools, 'jest/bin/jest.js'),
    [
      '--runInBand',
      '--detectOpenHandles',
      '--config',
      JSON.stringify({
        rootDir: root,
        testEnvironment: 'node',
        testMatch: [path.join(__dirname, 'route.test.cjs')],
        transform: {},
        modulePaths: [tools],
        cacheDirectory: path.join(temporary, 'jest-cache'),
        moduleNameMapper: {
          '^@librechat/api/coding$': path.join(
            build,
            'packages/api/src/coding/preview/controller.js',
          ),
        },
      }),
    ],
    { ...process.env, PREVIEW_TEST_BUILD: path.join(build, 'packages/api/src/coding/preview') },
  );
} finally {
  fs.rmSync(temporary, { recursive: true, force: true });
}
