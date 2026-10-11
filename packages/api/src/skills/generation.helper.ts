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
  special?: 'symlink' | 'submodule' | 'duplicate-definition',
  skillPath = 'skills/writer',
): GenerationFixture {
  const root = mkdtempSync(path.join(os.tmpdir(), 'skill-generation-'));
  const git = (...args: string[]) =>
    execFileSync('git', args, { cwd: root, maxBuffer: 8 * 1024 * 1024 });
  try {
    git('init', '--quiet');
    for (const [name, content] of Object.entries(files)) {
      const file = path.join(root, skillPath, name);
      mkdirSync(path.dirname(file), { recursive: true });
      writeFileSync(file, content);
    }
    git('add', '--', '.');
    if (special) {
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
    const tree = git('write-tree').toString().trim();
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
          paths: ['skills'],
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
