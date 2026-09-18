import React from 'react';
import { Clock4 } from 'lucide-react';
import { cn } from '~/utils';

export interface MentionItemProps {
  name: string;
  onClick: (e: React.MouseEvent<HTMLButtonElement>) => void;
  index: number;
  type?: 'prompt' | 'mention' | 'add-convo' | 'skill';
  icon?: React.ReactNode;
  isActive?: boolean;
  description?: string;
  badge?: string;
  style?: React.CSSProperties;
}

export default function MentionItem({
  name,
  onClick,
  index,
  icon,
  isActive,
  description,
  badge,
  style,
  type = 'mention',
}: MentionItemProps) {
  return (
    <button
      type="button"
      style={style}
      tabIndex={index}
      onClick={onClick}
      id={`${type}-item-${index}`}
      className="w-full touch-manipulation"
    >
      <div
        className={cn(
          'text-token-text-primary group flex min-h-[44px] items-center gap-2 rounded-lg px-2 text-sm font-medium hover:bg-surface-secondary active:bg-surface-active',
          isActive === true ? 'bg-surface-active' : 'bg-transparent',
        )}
      >
        <div className="flex h-5 w-5 flex-shrink-0 items-center justify-center">{icon}</div>
        <div className="flex min-w-0 flex-grow items-center justify-between">
          <div className="truncate">
            <span className="font-medium">{name}</span>
            {description != null && description ? (
              <span className="text-token-text-tertiary ml-2 text-sm font-light">
                {description}
              </span>
            ) : null}
          </div>
          <div className="ml-2 flex flex-shrink-0 items-center gap-2">
            {badge ? (
              <span className="rounded-full border border-border-medium bg-surface-secondary px-1.5 py-0.5 text-[10px] font-medium text-text-secondary">
                {badge}
              </span>
            ) : null}
            <Clock4 size={16} />
          </div>
        </div>
      </div>
    </button>
  );
}
