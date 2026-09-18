import { format } from 'date-fns';
import { useNavigate } from 'react-router-dom';
import {
  InvocationMode,
  PermissionTypes,
  Permissions,
  getSkillLifecycle,
  getSkillLogicalName,
} from 'librechat-data-provider';
import { Button, TooltipAnchor, useToastContext } from '@librechat/client';
import { Pencil, Pin, User, Calendar, EarthIcon, Sparkles, GitBranch, PencilLine } from 'lucide-react';
import type { TSkill } from 'librechat-data-provider';
import type { TranslationKeys } from '~/hooks';
import { useLocalize, useAuthContext, useHasAccess } from '~/hooks';
import {
  useCreateSkillDraftMutation,
  useSetSkillLifecycleMutation,
  usePublishSkillDraftMutation,
} from '~/data-provider';
import DeleteSkill from '../dialogs/DeleteSkill';
import { ShareSkill } from '../buttons';

const invocationLabelMap: Record<InvocationMode, TranslationKeys> = {
  [InvocationMode.auto]: 'com_ui_invocation_auto',
  [InvocationMode.manual]: 'com_ui_invocation_manual',
  [InvocationMode.both]: 'com_ui_invocation_both',
};

interface SkillDetailHeaderProps {
  skill: TSkill;
  showActions?: boolean;
}

const SkillDetailHeader = ({ skill, showActions = true }: SkillDetailHeaderProps) => {
  const localize = useLocalize();
  const navigate = useNavigate();
  const { user } = useAuthContext();
  const { showToast } = useToastContext();
  const canCreateSkill = useHasAccess({
    permissionType: PermissionTypes.SKILLS,
    permission: Permissions.CREATE,
  });
  const createDraft = useCreateSkillDraftMutation({
    onSuccess: (draft) => navigate(`/skills/${draft._id}/edit`),
  });
  const setLifecycle = useSetSkillLifecycleMutation();
  const publishDraft = usePublishSkillDraftMutation({
    onSuccess: (response) => {
      showToast({
        status: 'success',
        message: `Draft published to PR #${response.pullRequestNumber}`,
      });
    },
    onError: (error: unknown) => {
      const message =
        (error as { response?: { data?: { message?: string } } })?.response?.data?.message ??
        'Unable to publish draft to GitHub';
      showToast({ status: 'error', message });
    },
  });
  const lifecycle = getSkillLifecycle(skill);
  const logicalName = getSkillLogicalName(skill);
  const isManagedDraft = lifecycle !== 'published';
  const formattedDate = skill.createdAt ? format(new Date(skill.createdAt), 'MMM d, yyyy') : null;
  const isOwner = skill.author === user?.id;
  const isShared = !isOwner && Boolean(skill.authorName);
  const isPublic = skill.isPublic === true;
  const externallyManaged = skill.source !== 'inline';

  return (
    <div className="flex flex-col gap-3 py-2 sm:flex-row sm:items-center sm:gap-4">
      <div className="min-w-0 flex-1 overflow-hidden">
        <div className="flex min-w-0 items-center gap-2">
          <h2 className="truncate text-xl font-bold text-text-primary" title={logicalName}>
            {logicalName}
          </h2>
          {isPublic && (
            <TooltipAnchor
              description={localize('com_ui_sr_public_skill')}
              side="top"
              render={
                <EarthIcon
                  className="h-5 w-5 shrink-0 text-accent-primary"
                  aria-label={localize('com_ui_sr_public_skill')}
                />
              }
            />
          )}
          <span
            className={
              lifecycle === 'published' && skill.source === 'github'
                ? 'inline-flex shrink-0 items-center gap-1 rounded-full border border-border-medium bg-surface-secondary px-2 py-1 text-xs font-medium text-text-secondary'
                : 'inline-flex shrink-0 items-center gap-1 rounded-full border border-status-warning-border bg-status-warning-subtle px-2 py-1 text-xs font-medium text-status-warning'
            }
            title={
              lifecycle === 'published' && skill.source === 'github'
                ? 'Published and managed from GitHub'
                : lifecycle === 'trial'
                  ? 'Author draft enabled for trial'
                  : lifecycle === 'publish_pending'
                    ? 'Draft queued for publication'
                    : isManagedDraft
                      ? 'Editable author draft'
                      : 'Local skill — not managed by GitHub Skill Sync'
            }
          >
            {lifecycle === 'published' && skill.source === 'github' ? (
              <GitBranch className="size-3" aria-hidden="true" />
            ) : (
              <PencilLine className="size-3" aria-hidden="true" />
            )}
            {lifecycle === 'trial'
              ? 'Draft · Trial'
              : lifecycle === 'publish_pending'
                ? 'Draft · Publish pending'
                : isManagedDraft
                  ? 'Draft'
                  : skill.source === 'github'
                    ? 'GitHub managed'
                    : 'Local'}
          </span>
          {skill.alwaysApply === true && (
            <TooltipAnchor
              description={localize('com_ui_skills_always_apply_pin_title')}
              side="top"
              render={
                <Pin
                  className="h-5 w-5 shrink-0 text-cyan-500"
                  aria-label={localize('com_ui_skills_always_apply_pin_title')}
                />
              }
            />
          )}
        </div>
        {skill.description && (
          <p className="text-sm text-text-secondary sm:truncate">{skill.description}</p>
        )}
        <div className="mt-1 flex flex-wrap items-center gap-3 text-xs text-text-secondary">
          {isShared && (
            <span className="flex items-center gap-1">
              <User className="h-3 w-3 text-text-secondary" aria-hidden="true" />
              {localize('com_ui_by_author', { 0: skill.authorName })}
            </span>
          )}
          <span className="flex items-center gap-1">
            <Sparkles className="h-3 w-3" aria-hidden="true" />
            {localize('com_ui_invoked_by')}:{' '}
            {localize(invocationLabelMap[skill.invocationMode ?? InvocationMode.auto])}
          </span>
          {formattedDate && (
            <time className="flex items-center gap-1" dateTime={skill.createdAt}>
              <Calendar className="h-3 w-3" aria-hidden="true" />
              {formattedDate}
            </time>
          )}
        </div>
      </div>
      {showActions && (
        <div className="flex shrink-0 flex-wrap items-center gap-2">
          {!isManagedDraft && <ShareSkill skill={skill} />}
          {skill.source === 'github' && lifecycle === 'published' && canCreateSkill && (
            <Button
              variant="outline"
              disabled={createDraft.isLoading}
              onClick={() => createDraft.mutate({ skillId: skill._id })}
            >
              Create Draft
            </Button>
          )}
          {isManagedDraft && isOwner && (
            <>
              <Button
                variant="outline"
                onClick={() => navigate(`/skills/${skill._id}/edit`)}
              >
                <Pencil className="mr-1 size-4" aria-hidden="true" />
                Edit Draft
              </Button>
              {lifecycle !== 'trial' ? (
                <Button
                  variant="outline"
                  disabled={setLifecycle.isLoading || lifecycle === 'publish_pending'}
                  onClick={() =>
                    setLifecycle.mutate({ skillId: skill._id, lifecycle: 'trial' })
                  }
                >
                  Test Draft
                </Button>
              ) : (
                <Button
                  variant="outline"
                  disabled={setLifecycle.isLoading}
                  onClick={() =>
                    setLifecycle.mutate({ skillId: skill._id, lifecycle: 'draft' })
                  }
                >
                  End Trial
                </Button>
              )}
              {lifecycle !== 'publish_pending' ? (
                <Button
                  disabled={publishDraft.isLoading}
                  onClick={() => publishDraft.mutate({ skillId: skill._id })}
                >
                  Publish Draft
                </Button>
              ) : typeof (skill.sourceMetadata as Record<string, unknown> | undefined)?.githubPrUrl ===
                'string' ? (
                <Button
                  variant="outline"
                  onClick={() =>
                    window.open(
                      (skill.sourceMetadata as Record<string, unknown>).githubPrUrl as string,
                      '_blank',
                      'noopener,noreferrer',
                    )
                  }
                >
                  View PR
                </Button>
              ) : null}
              <DeleteSkill
                skillId={skill._id}
                skillName={logicalName}
                onDelete={() => navigate('/skills')}
              />
            </>
          )}
          {isOwner && !externallyManaged && !isManagedDraft && (
            <>
              <TooltipAnchor
                description={localize('com_ui_edit')}
                side="bottom"
                render={
                  <Button
                    variant="outline"
                    size="icon"
                    className="size-9"
                    aria-label={localize('com_ui_edit_skill')}
                    onClick={() => navigate(`/skills/${skill._id}/edit`)}
                  >
                    <Pencil className="size-5" aria-hidden="true" />
                  </Button>
                }
              />
              <DeleteSkill
                skillId={skill._id}
                skillName={skill.name}
                onDelete={() => navigate('/skills')}
              />
            </>
          )}
        </div>
      )}
    </div>
  );
};

export default SkillDetailHeader;
