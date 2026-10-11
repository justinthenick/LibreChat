import { skillSyncGitHubSourceSchema } from 'librechat-data-provider';
import type { GenerationFixture } from './generation.helper';
import { createGenerationFixture } from './generation.helper';
import { captureGitHubSkillGeneration } from './generation';
import { validateSkillBundle } from './bundles';

let fixture: GenerationFixture;
beforeEach(() => {
  fixture = createGenerationFixture();
});
afterEach(() => {
  fixture.close();
});

test('captures a complete Git-authenticated generation without following the moving configured ref', async () => {
  const snapshot = await captureGitHubSkillGeneration(fixture.input);
  const manifest = validateSkillBundle(snapshot);
  expect(manifest.sourceRevision).toBe(fixture.input.selection.commitSha);
  expect(manifest.definition.body).toContain('Original instructions');
  expect(snapshot.files).toEqual([
    { path: 'notes/readme.txt', base64: Buffer.from('original bytes').toString('base64') },
  ]);
  expect(fixture.requests.some((url) => url.endsWith('/main'))).toBe(false);
  expect(Object.isFrozen(snapshot)).toBe(true);
});

test.each(['tenantId', 'sourceId', 'owner', 'repo', 'skillPath'] as const)(
  'rejects mismatched configured %s before any fetch',
  async (key) => {
    fixture.input.selection[key] = 'other';
    await expect(captureGitHubSkillGeneration(fixture.input)).rejects.toThrow();
    expect(fixture.requests).toHaveLength(0);
  },
);

test.each(['truncated', 'missing-entry', 'changed-mode', 'wrong-tree'])(
  'rejects an incomplete or changed tree: %s',
  async (failure) => {
    const tree = [...fixture.responses.values()].find((value) =>
      value.tree?.some((entry) => entry.path === 'SKILL.md'),
    )!;
    if (failure === 'truncated') tree.truncated = true;
    if (failure === 'missing-entry') tree.tree!.pop();
    if (failure === 'changed-mode') tree.tree![0].mode = '120000';
    if (failure === 'wrong-tree') tree.sha = 'f'.repeat(40);
    await expect(captureGitHubSkillGeneration(fixture.input)).rejects.toThrow('integrity');
  },
);

test.each(['sha', 'bytes', 'size', 'base64'])(
  'rejects downloaded blob corruption: %s',
  async (failure) => {
    const blob = [...fixture.responses.values()].find((value) => value.content)!;
    if (failure === 'sha') blob.sha = 'f'.repeat(40);
    if (failure === 'bytes') blob.content = Buffer.from('replacement').toString('base64');
    if (failure === 'size') blob.size = 999;
    if (failure === 'base64') blob.content += '!';
    await expect(captureGitHubSkillGeneration(fixture.input)).rejects.toThrow('integrity');
  },
);

test('rejects a provider response resolving another commit', async () => {
  [...fixture.responses.values()].find((value) => value.commit)!.sha = 'f'.repeat(40);
  await expect(captureGitHubSkillGeneration(fixture.input)).rejects.toThrow('integrity');
});

test('does not normalize away an unsupported path', async () => {
  fixture.close();
  fixture = createGenerationFixture({
    'SKILL.md': '---\nname: writer\ndescription: Writes\n---\nBody',
    'bad file.txt': 'bytes',
  });
  await expect(captureGitHubSkillGeneration(fixture.input)).rejects.toThrow();
});

test('requires the pinned definition to match the selected logical name', async () => {
  fixture.input.selection.name = 'different';
  await expect(captureGitHubSkillGeneration(fixture.input)).rejects.toThrow(
    'invalid_skill_selection',
  );
});

test.each(['web_search', '[web_search, file_search]'])(
  'preserves false invocation and structured allowed-tools from %s',
  async (allowedTools) => {
    fixture.close();
    fixture = createGenerationFixture({
      'SKILL.md': `---\nname: writer\ndescription: Writes\nuser-invocable: false\nallowed-tools: ${allowedTools}\n---\nBody`,
    });
    const manifest = validateSkillBundle(await captureGitHubSkillGeneration(fixture.input));
    expect(manifest.definition.userInvocable).toBe(false);
    expect(manifest.definition.allowedTools).toEqual(
      allowedTools.startsWith('[') ? ['web_search', 'file_search'] : ['web_search'],
    );
  },
);

test.each(['symlink', 'submodule', 'duplicate-definition'] as const)(
  'rejects a genuine Git tree containing %s before downloading blobs',
  async (special) => {
    fixture.close();
    fixture = createGenerationFixture(undefined, special);
    await expect(captureGitHubSkillGeneration(fixture.input)).rejects.toThrow(
      'invalid_skill_selection',
    );
    expect(fixture.requests.some((url) => url.includes('/blobs/'))).toBe(false);
  },
);

test('checks aggregate size before downloading blobs', async () => {
  fixture.close();
  fixture = createGenerationFixture({
    'SKILL.md': '---\nname: writer\ndescription: Writes\n---\nBody',
    'large.txt': 'x'.repeat(5 * 1024 * 1024),
  });
  await expect(captureGitHubSkillGeneration(fixture.input)).rejects.toThrow(
    'invalid_skill_selection',
  );
  expect(fixture.requests.some((url) => url.includes('/blobs/'))).toBe(false);
});

test('stops between external reads when cancelled', async () => {
  let checks = 0;
  fixture.input.assertNotCancelled = () => {
    if (++checks === 3) throw new Error('cancelled');
  };
  await expect(captureGitHubSkillGeneration(fixture.input)).rejects.toThrow('cancelled');
  expect(fixture.requests).toHaveLength(1);
});

test('bounds and cancels a malformed oversized blob response before parsing', async () => {
  const original = fixture.input.fetchFn;
  let cancelled = false;
  fixture.input.fetchFn = async (url, init) => {
    if (!String(url).includes('/blobs/')) return original(url, init);
    return new Response(
      new ReadableStream<Uint8Array>({
        start(controller) {
          controller.enqueue(new Uint8Array(70000));
        },
        cancel() {
          cancelled = true;
        },
      }),
    );
  };
  await expect(captureGitHubSkillGeneration(fixture.input)).rejects.toThrow('integrity');
  expect(cancelled).toBe(true);
});

test('retains source selection and configuration before asynchronous reads', async () => {
  const original = fixture.input.fetchFn;
  const commit = fixture.input.selection.commitSha;
  fixture.input.fetchFn = async (url, init) => {
    fixture.input.selection.commitSha = 'f'.repeat(40);
    fixture.input.selection.tenantId = 'other';
    fixture.input.source.paths.length = 0;
    return original(url, init);
  };
  const manifest = validateSkillBundle(await captureGitHubSkillGeneration(fixture.input));
  expect(manifest.sourceRevision).toBe(commit);
  expect(manifest.tenantId).toBe('tenant');
});

test('rejects invalid frontmatter before constructing a committed bundle', async () => {
  fixture.close();
  fixture = createGenerationFixture({
    'SKILL.md': '---\nname: writer\ndescription: Writes\ncompatibility: [invalid]\n---\nBody',
  });
  await expect(captureGitHubSkillGeneration(fixture.input)).rejects.toThrow(
    'invalid_skill_selection',
  );
});

test.each(['.', '/'])('accepts a normalized repository-root source from %s', async (root) => {
  fixture.close();
  fixture = createGenerationFixture(undefined, undefined, '');
  fixture.input.source = skillSyncGitHubSourceSchema.parse({
    ...fixture.input.source,
    paths: [root],
  });
  expect(fixture.input.source.paths).toEqual(['']);
  const manifest = validateSkillBundle(await captureGitHubSkillGeneration(fixture.input));
  expect(manifest.definition.name).toBe('writer');
});

test('bounds YAML alias expansion before bundle serialization', async () => {
  fixture.close();
  const aliases = Array.from({ length: 100 }, () => '*a').join(', ');
  fixture = createGenerationFixture({
    'SKILL.md': `---\nname: writer\ndescription: Writes\na: &a [one, two]\nb: &b [${aliases}]\nc: [${Array.from({ length: 100 }, () => '*b').join(', ')}]\n---\nBody`,
  });
  await expect(captureGitHubSkillGeneration(fixture.input)).rejects.toThrow(
    'invalid_skill_selection',
  );
});

test('rejects cyclic YAML aliases before bundle serialization', async () => {
  fixture.close();
  fixture = createGenerationFixture({
    'SKILL.md': '---\nname: writer\ndescription: Writes\nmetadata: &self [*self]\n---\nBody',
  });
  await expect(captureGitHubSkillGeneration(fixture.input)).rejects.toThrow(
    'invalid_skill_selection',
  );
});

test.each([401, 403, 404, 429, 500])('cancels an unread HTTP %s error stream', async (status) => {
  let cancelled = false;
  fixture.input.fetchFn = async () =>
    new Response(
      new ReadableStream<Uint8Array>({
        start(controller) {
          controller.enqueue(new Uint8Array([1]));
        },
        cancel() {
          cancelled = true;
        },
      }),
      { status },
    );
  await expect(captureGitHubSkillGeneration(fixture.input)).rejects.toThrow(/GitHub/);
  expect(cancelled).toBe(true);
});
