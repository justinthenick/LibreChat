/**
 * Repository paths arrive from provider APIs and admin config with inconsistent
 * leading/trailing slashes, and `.` for the repository root. Normalizing both
 * sides through this keeps configured paths, tree entry paths, and stored skill
 * paths directly comparable.
 */
export function normalizeRepoPath(value: string): string {
  const trimmed = value.trim().replace(/^\/+|\/+$/g, '');
  return trimmed === '.' ? '' : trimmed;
}

/** Checks complete path segments with at most one set lookup per ancestor. */
export function isPathWithinRoots(path: string, roots: ReadonlySet<string>): boolean {
  let ancestor = path;
  while (ancestor) {
    if (roots.has(ancestor)) return true;
    const separator = ancestor.lastIndexOf('/');
    if (separator < 0) break;
    ancestor = ancestor.slice(0, separator);
  }
  return roots.has('');
}

export function isSkillRootWithinDiscoveryDepth(
  rootPath: string,
  basePath: string,
  maxDepth: number,
): boolean {
  if (rootPath === basePath) {
    return true;
  }
  if (basePath && !rootPath.startsWith(`${basePath}/`)) {
    return false;
  }
  const relative = basePath ? rootPath.slice(basePath.length).replace(/^\/+/, '') : rootPath;
  if (!relative) {
    return true;
  }
  return relative.split('/').length <= maxDepth;
}
