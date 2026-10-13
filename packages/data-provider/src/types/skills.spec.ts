import { encodeSkillSelection, parseSkillSelection } from './skills';

describe('manual skill selection tokens', () => {
  const id = 'abcdef0123456789abcdef01';
  const revision = 'a'.repeat(64);

  it('round trips an exact definition selection', () => {
    const token = encodeSkillSelection({ _id: id, name: 'example', selectionRevision: revision });
    expect(parseSkillSelection(token)).toEqual({
      name: 'example',
      explicit: true,
      skillId: id,
      revision,
    });
  });

  it('preserves legacy name-only requests', () => {
    expect(parseSkillSelection('example')).toEqual({ name: 'example' });
  });

  it.each([
    'example@@bad',
    `example@@${id}`,
    `example@@${id}@@bad`,
    `example@@${id}@@${revision}@@extra`,
    '@@',
  ])('never downgrades an invalid explicit selection to a name: %s', (token) => {
    expect(parseSkillSelection(token).explicit).toBe(true);
    expect(parseSkillSelection(token).revision).toBeUndefined();
  });

  it('normalizes ObjectId casing', () => {
    expect(parseSkillSelection(`example@@${id.toUpperCase()}@@${revision}`).skillId).toBe(id);
  });

  it('refuses to create a token without server definition evidence', () => {
    expect(() => encodeSkillSelection({ _id: id, name: 'example' })).toThrow();
  });
});
