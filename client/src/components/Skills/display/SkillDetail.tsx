import React, { useMemo, useState } from 'react';
import type { TSkill } from 'librechat-data-provider';
import SkillMarkdownRenderer from './SkillMarkdownRenderer';
import SkillDetailHeader from './SkillDetailHeader';
import { parseFrontmatter } from '../utils';
import { useLocalize } from '~/hooks';
import ViewToggle from './ViewToggle';

interface SkillDetailProps {
  skill: TSkill;
  onEdit?: () => void;
  onDelete?: () => void;
}

const SKIP_KEYS = new Set(['name', 'description']);

export default function SkillDetail({ skill, onEdit, onDelete }: SkillDetailProps) {
  const localize = useLocalize();
  const [viewMode, setViewMode] = useState<'rendered' | 'source'>('rendered');

  const { fields: frontmatterFields, body: cleanBody } = useMemo(
    () => parseFrontmatter(skill.body ?? '', SKIP_KEYS),
    [skill.body],
  );

  return (
    <article
      className="flex h-full min-w-0 flex-col gap-2 overflow-y-auto px-5 pb-5"
      aria-label={skill.name}
    >
      <SkillDetailHeader skill={skill} onEdit={onEdit} onDelete={onDelete} />

      <div className="flex flex-col gap-1">
        <h3 className="text-xs leading-4 text-text-secondary">{localize('com_ui_description')}</h3>
        <p className="whitespace-pre-wrap text-sm text-text-secondary">{skill.description}</p>
      </div>

      <div className="flex items-center gap-3 py-1">
        <hr className="flex-1 border-border-medium" />
        <ViewToggle viewMode={viewMode} setViewMode={setViewMode} />
      </div>

      {viewMode === 'rendered' && frontmatterFields.length > 0 && (
        <div className="grid grid-cols-[max-content_1fr] items-baseline gap-x-8 gap-y-2 pb-2">
          {frontmatterFields.map(({ key, value }) => (
            <React.Fragment key={key}>
              <span className="text-xs text-text-secondary">{key}</span>
              <span className="text-sm text-text-primary">{value}</span>
            </React.Fragment>
          ))}
        </div>
      )}

      <div className="min-h-0 flex-1 overflow-auto">
        {viewMode === 'rendered' ? (
          <SkillMarkdownRenderer
            content={cleanBody}
            skillId={skill._id}
            currentFilePath="SKILL.md"
          />
        ) : (
          <pre className="whitespace-pre-wrap font-mono text-sm leading-relaxed text-text-primary">
            {skill.body ?? ''}
          </pre>
        )}
      </div>
    </article>
  );
}
