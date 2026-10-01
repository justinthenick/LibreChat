import { resolveSkillActiveState, resolveSkillDefaultActive } from '../useSkillActiveState';

describe('resolveSkillDefaultActive', () => {
  test('activates deployment skills for every user by default', () => {
    expect(
      resolveSkillDefaultActive(
        { author: 'deployment-registry', source: 'deployment' },
        'user-1',
        false,
      ),
    ).toBe(true);
  });

  test('activates owned inline skills by default', () => {
    expect(resolveSkillDefaultActive({ author: 'user-1', source: 'inline' }, 'user-1', false)).toBe(
      true,
    );
  });

  test('uses the shared-skill configuration for non-owned inline skills', () => {
    const skill = { author: 'user-2', source: 'inline' } as const;
    expect(resolveSkillDefaultActive(skill, 'user-1', false)).toBe(false);
    expect(resolveSkillDefaultActive(skill, 'user-1', true)).toBe(true);
  });
});


describe('resolveSkillActiveState', () => {
  const sharedSkill = {
    _id: 'shared-1',
    author: 'user-2',
    source: 'inline',
  } as const;

  test('uses an agent-selected shared default when no user override exists', () => {
    expect(resolveSkillActiveState(sharedSkill, {}, 'user-1', true)).toBe(true);
  });

  test('keeps an explicit user false authoritative over the agent-selected default', () => {
    expect(resolveSkillActiveState(sharedSkill, { 'shared-1': false }, 'user-1', true)).toBe(false);
  });
});
