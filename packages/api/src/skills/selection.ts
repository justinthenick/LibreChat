import { createHash } from 'node:crypto';
import { ErrorTypes } from 'librechat-data-provider';

interface SkillDefinition {
  name: string;
  body: string;
  version?: number;
  frontmatter?: object;
  allowedTools?: string[];
  userInvocable?: boolean;
}

/** Binds the loaded prime definition, not subsequent reads of bundled files. */
export function getSkillSelectionRevision(skill: SkillDefinition): string {
  const definition = {
    name: skill.name,
    body: skill.body,
    version: skill.version,
    frontmatter: skill.frontmatter ?? {},
    allowedTools: skill.allowedTools ?? null,
    userInvocable: skill.userInvocable !== false,
  };
  const canonical = JSON.stringify(definition, (_key, value: unknown) => {
    if (value && typeof value === 'object' && !Array.isArray(value)) {
      return Object.fromEntries(
        Object.entries(value).sort(([left], [right]) => {
          if (left === right) return 0;
          return left < right ? -1 : 1;
        }),
      );
    }
    return value;
  });
  return createHash('sha256').update(canonical).digest('hex');
}

export class SkillSelectionError extends Error {
  constructor() {
    super(JSON.stringify({ type: ErrorTypes.INVALID_SKILL_SELECTION }));
    this.name = 'SkillSelectionError';
  }
}
