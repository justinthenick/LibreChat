import os from 'node:os';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { mkdtempSync, mkdirSync, writeFileSync, rmSync } from 'node:fs';
import type { GitHubGenerationInput } from './generation';

interface GitResponse {
  sha: string;
  commit?: { tree: { sha: string } };
  tree?: Array<{ path: string; mode: string; type: string; sha: string; size?: number }>;
  truncated?: boolean;
  content?: string;
  encoding?: string;
  size?: number;
}

export interface GenerationFixture {
  input: GitHubGenerationInput;
  responses: Map<string, GitResponse>;
  requests: string[];
  close: () => void;
}

/** Real Git writes the fixture objects; only the external GitHub HTTP boundary is replaced. */
export function createGenerationFixture(
  files: Record<string, string> = {
    'SKILL.md': '---\nname: writer\ndescription: Writes\n---\nOriginal instructions',
    'notes/readme.txt': 'original bytes',
  },
  special?:
    | 'symlink'
    | 'submodule'
    | 'duplicate-definition'
    | 'case-colliding-children'
    | 'oversized-component'
    | 'multibyte-component'
    | 'deep-path'
    | 'cumulative-paths'
    | 'long-valid-paths'
    | 'wide-prefix'
    | 'request-budget'
    | 'byte-budget',
  skillPath = 'skills/writer',
): GenerationFixture {
  const root = mkdtempSync(path.join(os.tmpdir(), 'skill-generation-'));
  const git = (...args: string[]) =>
    execFileSync('git', args, { cwd: root, maxBuffer: 8 * 1024 * 1024 });
  const writeTree = (entries: string[]) =>
    execFileSync('git', ['mktree', '-z'], {
      cwd: root,
      input: entries.join('\0') + '\0',
      maxBuffer: 8 * 1024 * 1024,
    })
      .toString()
      .trim();
  try {
    git('init', '--quiet');
    git('config', 'core.autocrlf', 'false');
    for (const [name, content] of Object.entries(files)) {
      const file = path.join(root, skillPath, name);
      mkdirSync(path.dirname(file), { recursive: true });
      writeFileSync(file, content);
    }
    git('add', '--', '.');
    if (special === 'case-colliding-children') {
      for (const [directory, name] of [
        ['child', 'first-child'],
        ['CHILD', 'second-child'],
      ]) {
        const blob = execFileSync('git', ['hash-object', '-w', '--stdin'], {
          cwd: root,
          input: `---\nname: ${name}\n---\nChild`,
        })
          .toString()
          .trim();
        git(
          'update-index',
          '--add',
          '--cacheinfo',
          `100644,${blob},${path.posix.join(skillPath, directory, 'SKILL.md')}`,
        );
      }
    } else if (special && ['symlink', 'submodule', 'duplicate-definition'].includes(special)) {
      const blob = git('rev-parse', `:${path.posix.join(skillPath, 'SKILL.md')}`)
        .toString()
        .trim();
      const mode = special === 'symlink' ? '120000' : '160000';
      const indexMode = special === 'duplicate-definition' ? '100644' : mode;
      const indexPath = path.posix.join(
        skillPath,
        special === 'duplicate-definition' ? 'skill.md' : 'unsupported',
      );
      git('update-index', '--add', '--cacheinfo', `${indexMode},${blob},${indexPath}`);
    }
    let tree = git('write-tree').toString().trim();
    if (special && ['wide-prefix', 'request-budget', 'byte-budget'].includes(special)) {
      const blob = git('rev-parse', `:${path.posix.join(skillPath, 'SKILL.md')}`)
        .toString()
        .trim();
      const definition = `100644 blob ${blob}\tSKILL.md`;
      tree = writeTree([definition]);
      if (special === 'wide-prefix') {
        const siblings = Array.from(
          { length: 6000 },
          (_, i) => `100644 blob ${blob}\tfile-${i}.txt`,
        );
        tree = writeTree([...siblings, `040000 tree ${tree}\tb`]);
        tree = writeTree([...siblings, `040000 tree ${tree}\ta`]);
        skillPath = 'a/b';
      } else if (special === 'request-budget') {
        tree = writeTree([
          definition,
          ...Array.from({ length: 256 }, (_, i) => `040000 tree ${tree}\tchild-${i}`),
        ]);
      } else {
        for (const segment of ['h', 'g', 'f', 'e', 'd', 'c', 'b', 'a']) {
          tree = writeTree([`040000 tree ${tree}\t${segment}`]);
        }
        skillPath = 'a/b/c/d/e/f/g/h';
      }
    }
    if (
      special &&
      [
        'oversized-component',
        'multibyte-component',
        'deep-path',
        'cumulative-paths',
        'long-valid-paths',
      ].includes(special)
    ) {
      const blob = git('rev-parse', `:${path.posix.join(skillPath, 'SKILL.md')}`)
        .toString()
        .trim();
      const definition = `100644 blob ${blob}\tSKILL.md`;
      const wide = special === 'oversized-component' || special === 'cumulative-paths';
      tree = writeTree(
        Array.from({ length: wide ? 9000 : 1 }, (_, i) => `100644 blob ${blob}\tfile-${i}.txt`),
      );
      if (special === 'oversized-component' || special === 'multibyte-component') {
        const name = special === 'oversized-component' ? 'x'.repeat(1024 * 1024) : 'é'.repeat(128);
        tree = writeTree([definition, `040000 tree ${tree}\t${name}`]);
      } else if (special === 'long-valid-paths') {
        tree = writeTree([definition, `100644 blob ${blob}\t${'f'.repeat(200)}.txt`]);
        const component = 'p'.repeat(200);
        for (let i = 0; i < 2; i++) tree = writeTree([`040000 tree ${tree}\t${component}`]);
        skillPath = `${component}/${component}`;
      } else {
        for (let i = 0; i < (special === 'deep-path' ? 17 : 4); i++) {
          tree = writeTree([`040000 tree ${tree}\t${'d'.repeat(255)}`]);
        }
        tree = writeTree([definition, `040000 tree ${tree}\tchildren`]);
      }
    }
    const commit = git(
      '-c',
      'user.name=Fixture',
      '-c',
      'user.email=fixture@example.invalid',
      '-c',
      'commit.gpgsign=false',
      'commit-tree',
      tree,
      '-m',
      'Offline fixture',
    )
      .toString()
      .trim();
    const base = 'https://api.github.com/repos/example/skills';
    const responses = new Map<string, GitResponse>();
    responses.set(`${base}/commits/${commit}`, { sha: commit, commit: { tree: { sha: tree } } });
    const addTree = (sha: string) => {
      if (responses.has(`${base}/git/trees/${sha}`)) return;
      const entries = git('ls-tree', '-z', sha)
        .toString()
        .split('\0')
        .filter(Boolean)
        .map((line) => {
          const [metadata, filePath] = line.split('\t');
          const [mode, type, object] = metadata.split(' ');
          if (type === 'tree') {
            addTree(object);
            return { path: filePath, mode, type, sha: object };
          }
          if (type === 'commit') return { path: filePath, mode, type, sha: object };
          const cached = responses.get(`${base}/git/blobs/${object}`);
          if (cached) return { path: filePath, mode, type, sha: object, size: cached.size };
          const bytes = git('cat-file', 'blob', object);
          responses.set(`${base}/git/blobs/${object}`, {
            sha: object,
            size: bytes.length,
            encoding: 'base64',
            content: bytes.toString('base64'),
          });
          return { path: filePath, mode, type, sha: object, size: bytes.length };
        });
      responses.set(`${base}/git/trees/${sha}`, { sha, tree: entries, truncated: false });
    };
    addTree(tree);
    const requests: string[] = [];
    const fetchFn: GitHubGenerationInput['fetchFn'] = async (url) => {
      const key = String(url);
      requests.push(key);
      const response = responses.get(key);
      if (!response) throw new Error(`Unexpected offline request: ${key}`);
      return new Response(JSON.stringify(response), { status: 200 });
    };
    return {
      responses,
      requests,
      input: {
        selection: {
          skillId: 'a'.repeat(24),
          tenantId: 'tenant',
          sourceId: 'selected',
          owner: 'example',
          repo: 'skills',
          commitSha: commit,
          skillPath,
          name: 'writer',
        },
        source: {
          id: 'selected',
          owner: 'example',
          repo: 'skills',
          ref: 'main',
          paths:
            special && ['long-valid-paths', 'wide-prefix', 'byte-budget'].includes(special)
              ? [skillPath]
              : ['skills'],
          tenantId: 'tenant',
          credentialKey: 'offline',
        },
        token: 'offline-placeholder',
        fetchFn,
        assertNotCancelled: () => undefined,
      },
      close: () => rmSync(root, { recursive: true, force: true }),
    };
  } catch (error) {
    rmSync(root, { recursive: true, force: true });
    throw error;
  }
}
