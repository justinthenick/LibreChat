import { format } from 'date-fns';
import { useNavigate } from 'react-router-dom';
import { Button, TooltipAnchor, useToastContext } from '@librechat/client';
import {
  Calendar,
  EarthIcon,
  GitBranch,
  Pencil,
  PencilLine,
  Pin,
  Sparkles,
  User,
} from 'lucide-react';
import {
  InvocationMode,
  PermissionTypes,
  Permissions,
  getSkillLifecycle,
  getSkillLogicalName,
} from 'librechat-data-provider';
import type { TSkill } from 'librechat-data-provider';
import type { ReactNode } from 'react';
import type { TranslationKeys } from '~/hooks';
import {
  useCreateSkillDraftMutation,
  usePublishSkillDraftMutation,
  useSetSkillLifecycleMutation,
} from '~/data-provider';
import {
  useAuthContext,
  useHasAccess,
  useLocalize,
  useSkillActiveState,
} from '~/hooks';
import { ShareSkill, SkillToggle } from '../buttons';
import DeleteSkill from '../dialogs/DeleteSkill';

const invocationLabelMap: Record<InvocationMode, TranslationKeys> = {
  [InvocationMode.auto]: 'com_ui_invocation_auto',
  [InvocationMode.manual]: 'com_ui_invocation_manual',
  [InvocationMode.both]: 'com_ui_invocation_both',
};

interface SkillDetailHeaderProps {
  skill: TSkill;
  showActions?: boolean;
  onEdit?: () => void;
  onDelete?: () => void;
}

const SkillDetailHeader = ({
  skill,
  showActions = true,
  onEdit,
  onDelete,
}: SkillDetailHeaderProps) => {
  const localize = useLocalize();
  const navigate = useNavigate();
  const { user } = useAuthContext();
  const { showToast } = useToastContext();
  const { isActive, toggle } = useSkillActiveState();
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
        message: localize('com_ui_skill_draft_publish_success', {
          0: String(response.pullRequestNumber),
        }),
      });
    },
    onError: (error: unknown) => {
      const message =
        (error as { response?: { data?: { message?: string } } })?.response?.data?.message ??
        localize('com_ui_skill_draft_publish_error');
      showToast({ status: 'error', message });
    },
  });

  const lifecycle = getSkillLifecycle(skill);
  const logicalName = getSkillLogicalName(skill);
  const isManagedDraft = lifecycle !== 'published';
  const isPublishedGithub = lifecycle === 'published' && skill.source === 'github';
  const formattedDate = skill.createdAt ? format(new Date(skill.createdAt), 'MMM d, yyyy') : null;
  const isOwner = skill.author === user?.id;
  const isShared = !isOwner && Boolean(skill.authorName);
  const isPublic = skill.isPublic === true;
  const externallyManaged = skill.source !== 'inline';
  const skillEnabled = isActive(skill);

  let lifecycleTitleKey: TranslationKeys = 'com_ui_skill_lifecycle_local_description';
  let lifecycleLabelKey: TranslationKeys = 'com_ui_skill_lifecycle_local';
  if (isPublishedGithub) {
    lifecycleTitleKey = 'com_ui_skill_lifecycle_published_description';
    lifecycleLabelKey = 'com_ui_skill_lifecycle_github_managed';
  } else if (lifecycle === 'trial') {
    lifecycleTitleKey = 'com_ui_skill_lifecycle_trial_description';
    lifecycleLabelKey = 'com_ui_skill_lifecycle_trial';
  } else if (lifecycle === 'publish_pending') {
    lifecycleTitleKey = 'com_ui_skill_lifecycle_publish_pending_description';
    lifecycleLabelKey = 'com_ui_skill_lifecycle_publish_pending';
  } else if (isManagedDraft) {
    lifecycleTitleKey = 'com_ui_skill_lifecycle_draft_description';
    lifecycleLabelKey = 'com_ui_skill_lifecycle_draft';
  }

  const sourceMetadata =
    skill.sourceMetadata && typeof skill.sourceMetadata === 'object'
      ? (skill.sourceMetadata as Record<string, unknown>)
      : undefined;
  const githubPrUrl =
    typeof sourceMetadata?.githubPrUrl === 'string' ? sourceMetadata.githubPrUrl : null;

  const handleEdit = onEdit ?? (() => navigate(`/skills/${skill._id}/edit`));
  const handleDelete = onDelete ?? (() => navigate('/skills'));

  let publishAction: ReactNode = null;
  if (lifecycle !== 'publish_pending') {
    publishAction = (
      <Button
        disabled={publishDraft.isLoading}
        onClick={() => publishDraft.mutate({ skillId: skill._id })}
      >
        {localize('com_ui_skill_publish_draft')}
      </Button>
    );
  } else if (githubPrUrl) {
    publishAction = (
      <Button
        variant="outline"
        onClick={() => window.open(githubPrUrl, '_blank', 'noopener,noreferrer')}
      >
        {localize('com_ui_skill_view_pr')}
      </Button>
    );
  }

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
              isPublishedGithub
                ? 'inline-flex shrink-0 items-center gap-1 rounded-full border border-border-medium bg-surface-secondary px-2 py-1 text-xs font-medium text-text-secondary'
                : 'inline-flex shrink-0 items-center gap-1 rounded-full border border-status-warning-border bg-status-warning-subtle px-2 py-1 text-xs font-medium text-status-warning'
            }
            title={localize(lifecycleTitleKey)}
          >
            {isPublishedGithub ? (
              <GitBranch className="size-3" aria-hidden="true" />
            ) : (
              <PencilLine className="size-3" aria-hidden="true" />
            )}
            {localize(lifecycleLabelKey)}
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
          <SkillToggle enabled={skillEnabled} onChange={() => toggle(skill)} />
          {!isManagedDraft && <ShareSkill skill={skill} />}

          {isPublishedGithub && canCreateSkill && (
            <Button
              variant="outline"
              disabled={createDraft.isLoading}
              onClick={() => createDraft.mutate({ skillId: skill._id })}
            >
              {localize('com_ui_skill_create_draft')}
            </Button>
          )}

          {isManagedDraft && isOwner && (
            <>
              <Button variant="outline" onClick={handleEdit}>
                <Pencil className="mr-1 size-4" aria-hidden="true" />
                {localize('com_ui_skill_edit_draft')}
              </Button>

              {lifecycle !== 'trial' ? (
                <Button
                  variant="outline"
                  disabled={setLifecycle.isLoading || lifecycle === 'publish_pending'}
                  onClick={() =>
                    setLifecycle.mutate({ skillId: skill._id, lifecycle: 'trial' })
                  }
                >
                  {localize('com_ui_skill_test_draft')}
                </Button>
              ) : (
                <Button
                  variant="outline"
                  disabled={setLifecycle.isLoading}
                  onClick={() =>
                    setLifecycle.mutate({ skillId: skill._id, lifecycle: 'draft' })
                  }
                >
                  {localize('com_ui_skill_end_trial')}
                </Button>
              )}

              {publishAction}
              <DeleteSkill skillId={skill._id} skillName={logicalName} onDelete={handleDelete} />
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
                    onClick={handleEdit}
                  >
                    <Pencil className="size-5" aria-hidden="true" />
                  </Button>
                }
              />
              <DeleteSkill skillId={skill._id} skillName={skill.name} onDelete={handleDelete} />
            </>
          )}
        </div>
      )}
    </div>
  );
};

export default SkillDetailHeader;
