import { getSkillSelectionRevision } from './selection';

describe('skill selection definition digest', () => {
  const skill = { name: 'example', body: 'Reviewed body', version: 3 };

  it('binds actual content even if the numeric version is unchanged', () => {
    expect(getSkillSelectionRevision(skill)).not.toBe(
      getSkillSelectionRevision({ ...skill, body: 'Changed body' }),
    );
  });

  it.each([
    { version: 4 },
    { name: 'renamed' },
    { frontmatter: { instruction: 'changed' } },
    { allowedTools: [] },
    { userInvocable: false },
  ])('invalidates changed definition fields: %p', (change) => {
    expect(getSkillSelectionRevision(skill)).not.toBe(
      getSkillSelectionRevision({ ...skill, ...change }),
    );
  });

  it('canonicalizes nested object keys while preserving array order', () => {
    const left = { ...skill, frontmatter: { z: [{ b: 2, a: 1 }], a: 'x' } };
    const right = { ...skill, frontmatter: { a: 'x', z: [{ a: 1, b: 2 }] } };
    expect(getSkillSelectionRevision(left)).toBe(getSkillSelectionRevision(right));
    expect(getSkillSelectionRevision({ ...skill, allowedTools: ['a', 'b'] })).not.toBe(
      getSkillSelectionRevision({ ...skill, allowedTools: ['b', 'a'] }),
    );
  });
});
