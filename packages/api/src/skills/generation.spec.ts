import { skillSyncGitHubSourceSchema } from 'librechat-data-provider';
import type { GenerationFixture } from './generation.helper';
import { createGenerationFixture } from './generation.helper';
import { captureGitHubSkillGeneration } from './generation';
import { validateSkillBundle } from './bundles';
import * as repoPaths from './sync/path';

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

test('uses the selected skill name when its description is omitted', async () => {
  fixture.close();
  fixture = createGenerationFixture({ 'SKILL.md': '---\nname: writer\n---\nBody' });
  const manifest = validateSkillBundle(await captureGitHubSkillGeneration(fixture.input));
  expect(manifest.definition.description).toBe('writer');
});

test('excludes independently discovered nested skill files before download and size accounting', async () => {
  fixture.close();
  fixture = createGenerationFixture({
    'SKILL.md': '---\nname: writer\ndescription: Writes\n---\nParent',
    'notes.txt': 'parent notes',
    'child/SkIlL.md': '---\nname: child\ndescription: Child\n---\nChild',
    'child/large.txt': 'x'.repeat(5 * 1024 * 1024),
  });
  const snapshot = await captureGitHubSkillGeneration(fixture.input);
  expect(snapshot.files.map((file) => file.path)).toEqual(['notes.txt']);
  expect(fixture.requests.filter((url) => url.includes('/blobs/'))).toHaveLength(2);
});

test('keeps files beneath a nested definition outside configured discovery depth', async () => {
  fixture.close();
  fixture = createGenerationFixture({
    'SKILL.md': '---\nname: writer\ndescription: Writes\n---\nParent',
    'child/SKILL.md': '---\nname: child\ndescription: Child\n---\nChild',
    'child/notes.txt': 'child notes',
  });
  fixture.input.source.skillDiscoveryDepth = 1;
  const snapshot = await captureGitHubSkillGeneration(fixture.input);
  expect(snapshot.files.map((file) => file.path)).toEqual(['child/SKILL.md', 'child/notes.txt']);
});

test.each([
  ['description: Explicit', 'Explicit'],
  ['when-to-use: Contextual', 'Contextual'],
])('preserves description semantics for %s', async (field, expected) => {
  fixture.close();
  const markdown = `---\nname: writer\n${field}\n---\nBody`;
  fixture = createGenerationFixture({ 'SKILL.md': markdown });
  const manifest = validateSkillBundle(await captureGitHubSkillGeneration(fixture.input));
  expect(manifest.definition.description).toBe(expected);
  expect(manifest.definition.body).toBe(markdown);
});

test('still rejects a missing selected name', async () => {
  fixture.close();
  fixture = createGenerationFixture({ 'SKILL.md': '---\ndescription: Writes\n---\nBody' });
  await expect(captureGitHubSkillGeneration(fixture.input)).rejects.toThrow(
    'invalid_skill_selection',
  );
});

test.each(['skills/writer', ''])('separates child packages at selected root %s', async (root) => {
  fixture.close();
  fixture = createGenerationFixture(
    {
      'SKILL.md': '---\nname: writer\n---\nParent',
      'child/sKiLl.Md': '---\nname: child\n---\nChild',
      'child/notes.txt': 'child notes',
      'childish/notes.txt': 'parent sibling',
    },
    undefined,
    root,
  );
  const childRoot = root ? `${root}/child` : 'child';
  fixture.input.source.paths = [root, childRoot];
  fixture.input.source.skillDiscoveryDepth = 0;
  const parent = await captureGitHubSkillGeneration(fixture.input);
  expect(parent.files.map((file) => file.path)).toEqual(['childish/notes.txt']);
  fixture.input.selection.skillPath = childRoot;
  fixture.input.selection.name = 'child';
  const child = await captureGitHubSkillGeneration(fixture.input);
  expect(child.files.map((file) => file.path)).toEqual(['notes.txt']);
  expect(validateSkillBundle(child).definition.description).toBe('child');
});

test('excludes the discovered child directory itself before parent path validation', async () => {
  fixture.close();
  fixture = createGenerationFixture({
    'SKILL.md': '---\nname: writer\n---\nParent',
    'notes.txt': 'parent notes',
    'bad child/SKILL.md': '---\nname: child\n---\nChild',
  });
  const snapshot = await captureGitHubSkillGeneration(fixture.input);
  expect(snapshot.files.map((file) => file.path)).toEqual(['notes.txt']);
  expect(fixture.requests.filter((url) => url.includes('/blobs/'))).toHaveLength(2);
});

test('excludes independently discovered child directory case collisions from the parent', async () => {
  fixture.close();
  fixture = createGenerationFixture(
    {
      'SKILL.md': '---\nname: writer\n---\nParent',
      'notes.txt': 'parent notes',
    },
    'case-colliding-children',
  );
  const snapshot = await captureGitHubSkillGeneration(fixture.input);
  expect(snapshot.files.map((file) => file.path)).toEqual(['notes.txt']);
  expect(fixture.requests.filter((url) => url.includes('/blobs/'))).toHaveLength(2);
});

test.each(['discovery', 'filtering'] as const)(
  'checks cancellation between entries during child %s',
  async (phase) => {
    fixture.close();
    fixture = createGenerationFixture({
      'SKILL.md': '---\nname: writer\n---\nParent',
      'first/SKILL.md': '---\nname: first\n---\nChild',
      'second/SKILL.md': '---\nname: second\n---\nChild',
      'third/SKILL.md': '---\nname: third\n---\nChild',
    });
    const scan = jest.spyOn(
      repoPaths,
      phase === 'discovery' ? 'isSkillRootWithinDiscoveryDepth' : 'isPathWithinRoots',
    );
    const cancelled = new Error('cancelled during scan');
    fixture.input.assertNotCancelled = () => {
      if (scan.mock.calls.length) throw cancelled;
    };
    try {
      await expect(captureGitHubSkillGeneration(fixture.input)).rejects.toBe(cancelled);
      expect(scan).toHaveBeenCalledTimes(1);
      expect(fixture.requests.some((url) => url.includes('/blobs/'))).toBe(false);
    } finally {
      scan.mockRestore();
    }
  },
);

test.each(['oversized-component', 'multibyte-component', 'deep-path', 'cumulative-paths'] as const)(
  'rejects Git-authenticated path amplification from %s before blob reads',
  async (special) => {
    fixture.close();
    fixture = createGenerationFixture(undefined, special, '');
    fixture.input.source.paths = ['.'];
    await expect(captureGitHubSkillGeneration(fixture.input)).rejects.toMatchObject({
      code: 'GITHUB_OBJECT_INVALID',
    });
    expect(fixture.requests.some((url) => url.includes('/blobs/'))).toBe(false);
    if (special === 'oversized-component' || special === 'multibyte-component') {
      expect(fixture.requests.filter((url) => url.includes('/trees/'))).toHaveLength(1);
    }
  },
);

test('keeps acquisition path budgets distinct from package-relative path limits', async () => {
  fixture.close();
  fixture = createGenerationFixture(undefined, 'long-valid-paths', '');
  const snapshot = await captureGitHubSkillGeneration(fixture.input);
  expect(snapshot.files.map((file) => file.path)).toEqual([`${'f'.repeat(200)}.txt`]);
  expect(fixture.input.selection.skillPath.length + snapshot.files[0].path.length).toBeGreaterThan(
    500,
  );
});

test('rejects excessive selected-path depth before any ancestor request', async () => {
  fixture.input.selection.skillPath = Array.from({ length: 65 }, () => 'a').join('/');
  fixture.input.source.paths = [fixture.input.selection.skillPath];
  await expect(captureGitHubSkillGeneration(fixture.input)).rejects.toMatchObject({
    code: 'GITHUB_OBJECT_INVALID',
  });
  expect(fixture.requests.filter((url) => url.includes('/trees/'))).toHaveLength(0);
});

test.each(['wide-prefix', 'request-budget'] as const)(
  'bounds total Git tree acquisition for %s',
  async (special) => {
    fixture.close();
    fixture = createGenerationFixture(undefined, special, '');
    fixture.input.source.paths = [fixture.input.selection.skillPath || '.'];
    await expect(captureGitHubSkillGeneration(fixture.input)).rejects.toMatchObject({
      code: 'GITHUB_OBJECT_INVALID',
    });
    expect(fixture.requests.filter((url) => url.includes('/trees/'))).toHaveLength(
      special === 'wide-prefix' ? 2 : 256,
    );
    expect(fixture.requests.some((url) => url.includes('/blobs/'))).toBe(false);
  },
);

test('charges streamed ancestor response bytes to one acquisition budget', async () => {
  fixture.close();
  fixture = createGenerationFixture(undefined, 'byte-budget', '');
  const original = fixture.input.fetchFn;
  fixture.input.fetchFn = async (url, init) => {
    const response = await original(url, init);
    if (!String(url).includes('/trees/')) return response;
    return new Response(
      JSON.stringify({
        ...fixture.responses.get(String(url)),
        padding: 'x'.repeat(5 * 1024 * 1024),
      }),
    );
  };
  await expect(captureGitHubSkillGeneration(fixture.input)).rejects.toMatchObject({
    code: 'GITHUB_OBJECT_INVALID',
  });
  expect(fixture.requests.filter((url) => url.includes('/trees/'))).toHaveLength(7);
  expect(fixture.requests.some((url) => url.includes('/blobs/'))).toBe(false);
});

test('starts a fresh acquisition budget for each capture', async () => {
  const first = await captureGitHubSkillGeneration(fixture.input);
  expect(await captureGitHubSkillGeneration(fixture.input)).toEqual(first);
});

test.each([
  'always-apply:',
  'always-apply: # TODO',
  'alwaysApply:',
  'always-apply: true\nalwaysApply: not-a-boolean',
])('cleans accepted boolean placeholders from %s while retaining raw Markdown', async (fields) => {
  fixture.close();
  const markdown = `---\nname: writer\ndescription: Writes\n${fields}\n---\nBody`;
  fixture = createGenerationFixture({ 'SKILL.md': markdown });
  const manifest = validateSkillBundle(await captureGitHubSkillGeneration(fixture.input));
  expect(manifest.definition.body).toBe(markdown);
  expect(manifest.definition.frontmatter).toEqual(
    fields.includes('true') ? { 'always-apply': true } : {},
  );
});

test.each(['always-apply: invalid', 'alwaysApply: invalid'])(
  'still rejects invalid effective boolean %s',
  async (field) => {
    fixture.close();
    fixture = createGenerationFixture({
      'SKILL.md': `---\nname: writer\ndescription: Writes\n${field}\n---\nBody`,
    });
    await expect(captureGitHubSkillGeneration(fixture.input)).rejects.toThrow(
      'invalid_skill_selection',
    );
  },
);

test.each([
  ['123', '456', '123', '456'],
  ['true', 'false', 'true', 'false'],
])(
  'retains scalar name %s and description %s normalization',
  async (name, description, expectedName, expectedDescription) => {
    fixture.close();
    const markdown = `---\nname: ${name}\ndescription: ${description}\n---\nBody`;
    fixture = createGenerationFixture({ 'SKILL.md': markdown });
    fixture.input.selection.name = expectedName;
    const manifest = validateSkillBundle(await captureGitHubSkillGeneration(fixture.input));
    expect(manifest.definition.name).toBe(expectedName);
    expect(manifest.definition.description).toBe(expectedDescription);
    expect(manifest.definition.frontmatter).toEqual({});
    expect(manifest.definition.body).toBe(markdown);
  },
);

test.each([
  ['writer', '"   "'],
  ['claude-reserved', 'Writes'],
])('rejects nonpersistable normalized name %s or description %s', async (name, description) => {
  fixture.close();
  fixture = createGenerationFixture({
    'SKILL.md': `---\nname: ${name}\ndescription: ${description}\n---\nBody`,
  });
  fixture.input.selection.name = name;
  await expect(captureGitHubSkillGeneration(fixture.input)).rejects.toThrow(
    'invalid_skill_selection',
  );
});

test('preserves UTF-8 BOM and CRLF bytes in the raw definition', async () => {
  fixture.close();
  const markdown = '\uFEFF---\r\nname: writer\r\ndescription: Writes\r\n---\r\nBody\r\n';
  fixture = createGenerationFixture({ 'SKILL.md': markdown });
  const manifest = validateSkillBundle(await captureGitHubSkillGeneration(fixture.input));
  expect(Buffer.from(manifest.definition.body, 'utf8')).toEqual(Buffer.from(markdown, 'utf8'));
});

test.each([
  ['You have exceeded a secondary rate limit', 'GITHUB_RATE_LIMITED'],
  ['Abuse detection mechanism triggered', 'GITHUB_RATE_LIMITED'],
  ['Resource not accessible by token', 'GITHUB_AUTH_FAILED'],
])('classifies bounded headerless 403 message %s', async (message, code) => {
  fixture.input.fetchFn = async () => new Response(JSON.stringify({ message }), { status: 403 });
  await expect(captureGitHubSkillGeneration(fixture.input)).rejects.toMatchObject({ code });
});

test('bounds and cancels an oversized 403 error without exposing its body', async () => {
  let cancelled = false;
  fixture.input.fetchFn = async () =>
    new Response(
      new ReadableStream<Uint8Array>({
        start(controller) {
          controller.enqueue(new Uint8Array(16 * 1024 + 1));
        },
        cancel() {
          cancelled = true;
        },
      }),
      { status: 403 },
    );
  await expect(captureGitHubSkillGeneration(fixture.input)).rejects.toMatchObject({
    code: 'GITHUB_AUTH_FAILED',
    message: 'GitHub request failed with HTTP 403',
  });
  expect(cancelled).toBe(true);
});

test.each(['invalid-json', 'read-error', 'empty-chunks'])(
  'releases bounded 403 reader after %s',
  async (failure) => {
    let pulls = 0;
    let cancelled = false;
    const body = new ReadableStream<Uint8Array>({
      pull(controller) {
        pulls++;
        if (failure === 'read-error') controller.error(new Error('untrusted provider details'));
        else if (failure === 'invalid-json') {
          controller.enqueue(new TextEncoder().encode('not JSON'));
          controller.close();
        } else controller.enqueue(new Uint8Array());
      },
      cancel() {
        cancelled = true;
      },
    });
    fixture.input.fetchFn = async () => new Response(body, { status: 403 });
    await expect(captureGitHubSkillGeneration(fixture.input)).rejects.toMatchObject({
      code: 'GITHUB_AUTH_FAILED',
      message: 'GitHub request failed with HTTP 403',
    });
    expect(body.locked).toBe(false);
    expect(pulls).toBeLessThanOrEqual(258);
    if (failure === 'empty-chunks') expect(cancelled).toBe(true);
  },
);

test('settles a nonclosing 403 by deadline even when cancellation never settles', async () => {
  let cancelled = false;
  const body = new ReadableStream<Uint8Array>({
    start(controller) {
      controller.enqueue(new Uint8Array([1]));
    },
    cancel() {
      cancelled = true;
      return new Promise<void>(() => {});
    },
  });
  fixture.input.fetchFn = async () => new Response(body, { status: 403 });
  jest.useFakeTimers();
  try {
    const result = captureGitHubSkillGeneration(fixture.input).then(
      () => {
        throw new Error('Expected rejected capture');
      },
      (error: Error) => error,
    );
    await jest.advanceTimersByTimeAsync(500);
    expect(await result).toMatchObject({
      code: 'GITHUB_AUTH_FAILED',
      message: 'GitHub request failed with HTTP 403',
    });
    expect(cancelled).toBe(true);
    expect(body.locked).toBe(false);
    expect(jest.getTimerCount()).toBe(0);
  } finally {
    jest.useRealTimers();
  }
});

test.each(
  ['oversized', 'chunks', 'invalid-utf8', 'invalid-json', 'read-error'].flatMap((failure) =>
    ['pending', 'rejecting'].map((cancelMode) => ({ failure, cancelMode })),
  ),
)(
  'settles strict response $failure with $cancelMode cancellation',
  async ({ failure, cancelMode }) => {
    let cancelled = false;
    let pulls = 0;
    const readError = new Error('read failed');
    const body = new ReadableStream<Uint8Array>({
      start(controller) {
        if (failure === 'chunks') return;
        if (failure === 'read-error') {
          controller.error(readError);
          return;
        }
        let bytes = new TextEncoder().encode('not JSON');
        if (failure === 'oversized') bytes = new Uint8Array(8 * 1024 * 1024 + 1);
        if (failure === 'invalid-utf8') bytes = new Uint8Array([255]);
        controller.enqueue(bytes);
        if (failure !== 'oversized') controller.close();
      },
      pull(controller) {
        pulls++;
        if (failure === 'chunks') controller.enqueue(new Uint8Array());
      },
    });
    const getReader = body.getReader.bind(body);
    jest.spyOn(body, 'getReader').mockImplementation(() => {
      const reader = getReader();
      const cancel = reader.cancel.bind(reader);
      jest.spyOn(reader, 'cancel').mockImplementation((reason) => {
        cancelled = true;
        void cancel(reason).catch(() => undefined);
        return cancelMode === 'pending'
          ? new Promise<void>(() => {})
          : Promise.reject(new Error('cancel failed'));
      });
      return reader;
    });
    fixture.input.fetchFn = async () => new Response(body, { status: 200 });
    const result = captureGitHubSkillGeneration(fixture.input);
    if (failure === 'oversized' || failure === 'chunks') {
      await expect(result).rejects.toMatchObject({ code: 'GITHUB_OBJECT_INVALID' });
    } else if (failure === 'read-error') {
      await expect(result).rejects.toBe(readError);
    } else {
      await expect(result).rejects.toMatchObject({
        name: failure === 'invalid-utf8' ? 'TypeError' : 'SyntaxError',
      });
    }
    expect(cancelled).toBe(true);
    expect(body.locked).toBe(false);
    expect(pulls).toBeLessThanOrEqual(100003);
  },
  5000,
);

test.each(['pending', 'rejecting'])(
  'retains successful capture with %s cancellation',
  async (cancelMode) => {
    const original = fixture.input.fetchFn;
    const bodies: ReadableStream<Uint8Array>[] = [];
    fixture.input.fetchFn = async (url, init) => {
      const response = await original(url, init);
      const body = response.body!;
      bodies.push(body);
      const getReader = body.getReader.bind(body);
      jest.spyOn(body, 'getReader').mockImplementation(() => {
        const reader = getReader();
        const cancel = reader.cancel.bind(reader);
        jest.spyOn(reader, 'cancel').mockImplementation((reason) => {
          void cancel(reason).catch(() => undefined);
          return cancelMode === 'pending'
            ? new Promise<void>(() => {})
            : Promise.reject(new Error('cancel failed'));
        });
        return reader;
      });
      return response;
    };
    const snapshot = await captureGitHubSkillGeneration(fixture.input);
    expect(validateSkillBundle(snapshot).definition.name).toBe('writer');
    expect(bodies.length).toBeGreaterThan(0);
    expect(bodies.every((body) => !body.locked)).toBe(true);
  },
);
