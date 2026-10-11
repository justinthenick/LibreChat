import { isPathWithinRoots } from './path';

test.each([
  ['skills/writer/child', true],
  ['skills/writer/child/SKILL.md', true],
  ['skills/writer/child/deep/file.txt', true],
  ['skills/writer/childish/file.txt', false],
  ['skills/writer/CHILD/file.txt', false],
  ['skills/writer', false],
])('matches complete case-sensitive root segments in %s', (path, expected) => {
  expect(isPathWithinRoots(path, new Set(['skills/writer/child']))).toBe(expected);
});

test('handles the repository root and empty root sets', () => {
  expect(isPathWithinRoots('', new Set(['']))).toBe(true);
  expect(isPathWithinRoots('child/file', new Set(['']))).toBe(true);
  expect(isPathWithinRoots('child/file', new Set())).toBe(false);
});

test.each([10, 3000])('bounds ancestor lookups independently of %i child roots', (count) => {
  const roots = new Set(Array.from({ length: count }, (_, i) => `skills/writer/child-${i}`));
  const has = jest.spyOn(roots, 'has');
  for (let i = 0; i < 10000; i++) {
    expect(isPathWithinRoots(`skills/writer/child-${i % count}/notes.txt`, roots)).toBe(true);
    expect(isPathWithinRoots(`skills/writer/sibling-${i}/notes.txt`, roots)).toBe(false);
  }
  expect(has.mock.calls.length).toBeLessThanOrEqual(7 * 10000);
});
