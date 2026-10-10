import { useState } from 'react';
import { apiBaseUrl } from 'librechat-data-provider';
import { Button, Input, Label, Textarea } from '@librechat/client';
import type { PreviewState } from 'librechat-data-provider';
import type { TranslationKeys } from '~/hooks/useLocalize';
import { settled } from '~/data-provider/Preview/session';
import { usePreviewJob } from '~/data-provider/Preview';
import { useAuthContext } from '~/hooks/AuthContext';
import useLocalize from '~/hooks/useLocalize';

const states: Record<PreviewState, TranslationKeys> = {
  queued: 'com_ui_preview_queued',
  running: 'com_ui_preview_running',
  cancelling: 'com_ui_preview_cancelling',
  completed: 'com_ui_preview_completed',
  failed: 'com_ui_preview_failed',
  cancelled: 'com_ui_preview_cancelled',
  timed_out: 'com_ui_preview_timed_out',
  interrupted: 'com_ui_preview_interrupted',
};

export const previewUIEnabled = () => import.meta.env.VITE_OPENHANDS_PREVIEW_UI === 'true';

export default function PreviewPanel() {
  const { user, isAuthenticated } = useAuthContext();
  if (!previewUIEnabled() || !isAuthenticated || !user?.id) return null;
  const owner = JSON.stringify([apiBaseUrl(), user.tenantId ?? '', user.id]);
  return <PreviewControls key={owner} owner={owner} />;
}

export function PreviewControls({ owner }: { owner: string }) {
  const localize = useLocalize();
  const preview = usePreviewJob(owner);
  const [prompt, setPrompt] = useState('');
  const [repository, setRepository] = useState('');
  const { job, session } = preview;
  const evidence = job?.result?.evidence;
  const stopUnconfirmed =
    job?.error_code === 'execution_stop_unconfirmed' ||
    job?.error_code === 'job_monitor_interrupted';
  let statusKey: TranslationKeys = job ? states[job.state] : 'com_ui_preview_loading';
  if (stopUnconfirmed) statusKey = 'com_ui_preview_stop_unknown';
  if (preview.failure) statusKey = 'com_ui_preview_stale';
  const valid =
    prompt.trim().length > 0 &&
    new TextEncoder().encode(prompt).length <= 32768 &&
    /^[A-Za-z0-9][A-Za-z0-9_.:@-]{0,127}$/.test(repository);

  return (
    <section
      aria-label={localize('com_ui_preview_title')}
      className="flex h-full flex-col gap-3 overflow-auto p-3 text-text-primary"
    >
      <h2 className="text-lg font-semibold">{localize('com_ui_preview_title')}</h2>
      <p className="text-sm text-text-secondary">{localize('com_ui_preview_description')}</p>
      <form
        className="flex flex-col gap-2"
        onSubmit={(event) => {
          event.preventDefault();
          if (!session && !valid) return;
          void preview.start(prompt, repository);
        }}
      >
        <Label htmlFor="preview-repository">{localize('com_ui_preview_repository')}</Label>
        <Input
          id="preview-repository"
          value={session?.request.scope.repository_alias ?? repository}
          onChange={(event) => setRepository(event.target.value)}
          disabled={!!session || preview.busy}
          maxLength={128}
          required
        />
        <Label htmlFor="preview-prompt">{localize('com_ui_preview_prompt')}</Label>
        <Textarea
          id="preview-prompt"
          value={session?.request.prompt ?? prompt}
          onChange={(event) => setPrompt(event.target.value)}
          disabled={!!session || preview.busy}
          maxLength={32768}
          required
        />
        {!session?.jobId && (
          <Button type="submit" disabled={preview.busy || (!session && !valid)}>
            {localize(session ? 'com_ui_preview_retry_start' : 'com_ui_preview_start')}
          </Button>
        )}
      </form>
      {preview.failure && <p role="alert">{localize(`com_ui_preview_${preview.failure}`)}</p>}
      {session && !session.jobId && <p role="status">{localize('com_ui_preview_start_unknown')}</p>}
      {session?.jobId && (
        <div className="flex flex-wrap gap-2">
          <Button
            variant="outline"
            disabled={preview.loading || preview.busy}
            onClick={preview.refresh}
          >
            {localize('com_ui_preview_refresh')}
          </Button>
          <Button
            variant="outline"
            disabled={preview.busy || (!preview.failure && settled(job))}
            onClick={() => void preview.cancel()}
          >
            {localize('com_ui_preview_cancel')}
          </Button>
        </div>
      )}
      <div role="status" aria-live="polite" aria-atomic="true">
        {preview.loading && !job && localize('com_ui_preview_loading')}
        {job && (
          <>
            <p>{localize(statusKey)}</p>
            <p>
              {localize('com_ui_preview_progress', {
                count: job.request_count,
                max: job.metadata.max_requests,
              })}
            </p>
          </>
        )}
      </div>
      {job?.result?.final_response && (
        <pre className="whitespace-pre-wrap break-words text-sm">{job.result.final_response}</pre>
      )}
      {evidence && (
        <details>
          <summary>{localize('com_ui_preview_evidence')}</summary>
          <p>
            {localize(
              evidence.evidence_complete
                ? 'com_ui_preview_evidence_complete'
                : 'com_ui_preview_evidence_incomplete',
            )}
          </p>
          <pre className="whitespace-pre-wrap break-words text-xs">
            {JSON.stringify(evidence, null, 2)}
          </pre>
        </details>
      )}
      {settled(job) && !preview.failure && (
        <Button variant="outline" onClick={preview.reset} disabled={preview.busy}>
          {localize('com_ui_preview_new')}
        </Button>
      )}
    </section>
  );
}
