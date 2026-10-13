import { useEffect, useId, useRef, useState } from 'react';
import { isAxiosError } from 'axios';
import { Button, Input, Label } from '@librechat/client';
import type { CodeReviewRequest, CodeReviewResult } from 'librechat-data-provider';
import { useAuthContext } from '~/hooks/AuthContext';
import { useReviewActions } from '~/data-provider';
import useLocalize from '~/hooks/useLocalize';

type Notice =
  | 'idle'
  | 'running'
  | 'uncertain'
  | 'unknown'
  | 'cancelled'
  | 'timeout'
  | 'forbidden'
  | 'busy'
  | 'invalid_request'
  | 'failed'
  | 'completed';
const notices = {
  idle: 'com_ui_review_idle',
  running: 'com_ui_review_running',
  uncertain: 'com_ui_review_uncertain',
  unknown: 'com_ui_review_unknown',
  cancelled: 'com_ui_review_cancelled',
  timeout: 'com_ui_review_timeout',
  forbidden: 'com_ui_review_forbidden',
  busy: 'com_ui_review_busy',
  invalid_request: 'com_ui_review_invalid',
  failed: 'com_ui_review_failed',
  completed: 'com_ui_review_completed',
} as const;
const severities = {
  blocker: 'com_ui_review_blocker',
  major: 'com_ui_review_major',
  minor: 'com_ui_review_minor',
} as const;
const sameRequest = (left: CodeReviewRequest, right: CodeReviewRequest) =>
  left.repository === right.repository && left.base === right.base && left.head === right.head;
const validResult = (result: CodeReviewResult, request: CodeReviewRequest) =>
  result &&
  sameRequest(result, request) &&
  result.provider === 'chatgpt_subscription' &&
  result.status === 'human_review_required' &&
  typeof result.model === 'string' &&
  Array.isArray(result.findings) &&
  result.findings.length <= 100 &&
  result.findings.every(
    (finding) =>
      finding &&
      Object.prototype.hasOwnProperty.call(severities, finding.severity) &&
      typeof finding.path === 'string' &&
      Number.isSafeInteger(finding.line) &&
      finding.line > 0 &&
      typeof finding.title === 'string' &&
      typeof finding.evidence === 'string' &&
      typeof finding.recommendation === 'string',
  );
function failure(code?: string, terminal = false): Notice {
  if (!terminal && code === 'cancelled') return 'uncertain';
  if (
    code === 'cancelled' ||
    code === 'timeout' ||
    code === 'forbidden' ||
    code === 'busy' ||
    code === 'invalid_request'
  )
    return code;
  return terminal ? 'failed' : 'uncertain';
}

/** Not mounted in navigation/routes. Both the caller gate and authenticated identity are required. */
export default function ReviewPanel({
  enabled = false,
  repositories = [],
}: {
  enabled?: boolean;
  /** Server-authorized repository IDs, never filesystem paths. */
  repositories?: readonly string[];
}) {
  const { user, isAuthenticated, isAuthReady } = useAuthContext();
  const localize = useLocalize();
  if (enabled !== true || !isAuthenticated || !isAuthReady || !user?.id)
    return <p role="status">{localize('com_ui_review_disabled')}</p>;
  return (
    <ReviewForm
      key={JSON.stringify([user.id, user.tenantId, repositories])}
      repositories={repositories}
    />
  );
}

function ReviewForm({ repositories }: { repositories: readonly string[] }) {
  const localize = useLocalize();
  const prefix = useId();
  const actions = useReviewActions();
  const [request, setRequest] = useState<CodeReviewRequest>({ repository: '', base: '', head: '' });
  const [id, setId] = useState('');
  const [notice, setNotice] = useState<Notice>('idle');
  const [result, setResult] = useState<CodeReviewResult | null>(null);
  const [expires, setExpires] = useState<number>();
  const [busy, setBusy] = useState(false);
  const [cancelBusy, setCancelBusy] = useState(false);
  const [cancelAcknowledged, setCancelAcknowledged] = useState(false);
  const activity = useRef<{
    alive: boolean;
    sequence: number;
    busy: boolean;
    cancelling: boolean;
    operation?: 'start' | 'status';
    controllers: Set<AbortController>;
  }>({ alive: true, sequence: 0, busy: false, cancelling: false, controllers: new Set() });
  const invalidate = () => {
    const state = activity.current;
    state.sequence++;
    state.controllers.forEach((controller) => controller.abort());
    state.controllers.clear();
    state.busy = false;
    state.cancelling = false;
    state.operation = undefined;
  };
  useEffect(() => {
    const state = activity.current;
    state.alive = true;
    return () => {
      state.alive = false;
      invalidate();
    };
  }, []);
  const changed = () => {
    invalidate();
    setBusy(false);
    setCancelBusy(false);
    setCancelAcknowledged(false);
    setResult(null);
    setExpires(undefined);
    setNotice('idle');
  };
  const valid =
    repositories.includes(request.repository) &&
    /^[0-9a-f]{40}$/.test(request.base) &&
    /^[0-9a-f]{40}$/.test(request.head);
  const validId = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(id);
  const current = (sequence: number) =>
    activity.current.alive && sequence === activity.current.sequence;

  async function run(retrieve: boolean) {
    if (!valid || (retrieve ? !validId : Boolean(id)) || activity.current.cancelling) return;
    if (activity.current.busy && (!retrieve || activity.current.operation !== 'start')) return;
    if (retrieve && activity.current.operation === 'start') invalidate();
    activity.current.operation = retrieve ? 'status' : 'start';
    activity.current.busy = true;
    setBusy(true);
    setResult(null);
    setExpires(undefined);
    setCancelAcknowledged(false);
    const sequence = activity.current.sequence;
    const selected = { ...request };
    const runId = retrieve ? id : crypto.randomUUID();
    setId(runId);
    setNotice('running');
    const controller = new AbortController();
    activity.current.controllers.add(controller);
    try {
      if (!retrieve) {
        const value = await actions.start.mutateAsync({
          id: runId,
          request: selected,
          signal: controller.signal,
        });
        if (!current(sequence)) return;
        if (!validResult(value, selected)) throw new Error('invalid_response');
        setResult(value);
        setNotice('completed');
      } else {
        const value = await actions.status.mutateAsync({
          id: runId,
          request: selected,
          signal: controller.signal,
        });
        if (!current(sequence)) return;
        if (
          value.id !== runId ||
          (value.state !== 'unknown' && !sameRequest(value.request, selected))
        )
          throw new Error('invalid_response');
        if (value.state === 'completed') {
          if (
            !validResult(value.result, selected) ||
            !Number.isFinite(new Date(value.expiresAt).getTime())
          )
            throw new Error('invalid_response');
          setResult(value.result);
          setExpires(value.expiresAt);
          setNotice('completed');
        } else if (value.state === 'running') {
          setNotice('running');
          setCancelAcknowledged(value.cancelRequested);
        } else if (value.state === 'failed') {
          setNotice(failure(value.code, true));
        } else if (value.state === 'unknown') {
          setNotice('unknown');
        } else throw new Error('invalid_response');
      }
    } catch (error) {
      if (current(sequence))
        setNotice(
          isAxiosError<{ code?: string }>(error)
            ? failure(error.response?.data?.code)
            : 'uncertain',
        );
    } finally {
      activity.current.controllers.delete(controller);
      if (current(sequence)) {
        activity.current.busy = false;
        setBusy(false);
      }
    }
  }

  async function cancel() {
    if (!validId || activity.current.cancelling) return;
    if (activity.current.busy && activity.current.operation === 'status') {
      invalidate();
      setBusy(false);
    }
    const sequence = activity.current.sequence;
    activity.current.cancelling = true;
    setCancelBusy(true);
    const controller = new AbortController();
    activity.current.controllers.add(controller);
    try {
      const response = await actions.cancel.mutateAsync({ id, signal: controller.signal });
      if (current(sequence)) {
        if (response.cancelled !== true) throw new Error('invalid_response');
        setCancelAcknowledged(true);
      }
    } catch {
      if (current(sequence)) setNotice('uncertain');
    } finally {
      activity.current.controllers.delete(controller);
      if (current(sequence)) {
        activity.current.cancelling = false;
        setCancelBusy(false);
      }
    }
  }

  return (
    <section
      aria-label={localize('com_ui_review_title')}
      className="mx-auto flex max-w-3xl flex-col gap-4 p-4 text-text-primary"
    >
      <h1 className="text-xl font-semibold">{localize('com_ui_review_title')}</h1>
      <p>{localize('com_ui_review_limits')}</p>
      <p>{localize('com_ui_review_navigation')}</p>
      <div className="flex flex-col gap-2">
        <Label htmlFor={`${prefix}-repository`}>{localize('com_ui_review_repository')}</Label>
        <Input
          id={`${prefix}-repository`}
          list={`${prefix}-repositories`}
          value={request.repository}
          onChange={(event) => {
            changed();
            setRequest({ ...request, repository: event.target.value });
          }}
        />
        <datalist id={`${prefix}-repositories`}>
          {repositories.map((repository) => (
            <option key={repository} value={repository} />
          ))}
        </datalist>
        {(['base', 'head'] as const).map((field) => (
          <div key={field} className="flex flex-col gap-2">
            <Label htmlFor={`${prefix}-${field}`}>
              {localize(field === 'base' ? 'com_ui_review_base' : 'com_ui_review_head')}
            </Label>
            <Input
              id={`${prefix}-${field}`}
              value={request[field]}
              maxLength={40}
              spellCheck={false}
              onChange={(event) => {
                changed();
                setRequest({ ...request, [field]: event.target.value });
              }}
            />
          </div>
        ))}
        <Label htmlFor={`${prefix}-id`}>{localize('com_ui_review_id')}</Label>
        <Input
          id={`${prefix}-id`}
          value={id}
          maxLength={36}
          spellCheck={false}
          onChange={(event) => {
            changed();
            setId(event.target.value);
          }}
        />
        <p className="text-sm text-text-secondary">{localize('com_ui_review_id_help')}</p>
      </div>
      <div className="flex flex-wrap gap-2">
        <Button
          type="button"
          disabled={!valid || busy || Boolean(id)}
          onClick={() => void run(false)}
        >
          {localize('com_ui_review_start')}
        </Button>
        <Button
          type="button"
          variant="outline"
          disabled={
            !valid || !validId || cancelBusy || (busy && activity.current.operation === 'status')
          }
          onClick={() => void run(true)}
        >
          {localize('com_ui_review_retrieve')}
        </Button>
        <Button
          type="button"
          variant="outline"
          disabled={!validId || cancelBusy}
          onClick={() => void cancel()}
        >
          {localize('com_ui_review_cancel')}
        </Button>
      </div>
      <p role="status" aria-live="polite">
        {localize(notices[notice])}
      </p>
      {cancelAcknowledged && !result && <p>{localize('com_ui_review_cancel_ack')}</p>}
      <aside className="rounded-lg border border-border-light p-3">
        <h2 className="font-semibold">{localize('com_ui_review_coverage')}</h2>
        <p>{localize('com_ui_review_coverage_detail')}</p>
      </aside>
      {result && (
        <section aria-label={localize('com_ui_review_result')} className="flex flex-col gap-3">
          <h2 className="font-semibold">{localize('com_ui_review_human')}</h2>
          <dl className="break-all text-sm">
            <dt>{localize('com_ui_review_repository')}</dt>
            <dd>{result.repository}</dd>
            <dt>{localize('com_ui_review_base')}</dt>
            <dd>{result.base}</dd>
            <dt>{localize('com_ui_review_head')}</dt>
            <dd>{result.head}</dd>
            <dt>{localize('com_ui_review_model')}</dt>
            <dd>{result.model}</dd>
            <dt>{localize('com_ui_review_id')}</dt>
            <dd>{id}</dd>
            <dt>{localize('com_ui_review_result_status')}</dt>
            <dd>{result.status}</dd>
            {expires && (
              <>
                <dt>{localize('com_ui_review_expiry')}</dt>
                <dd>{new Date(expires).toISOString()}</dd>
              </>
            )}
          </dl>
          <p>{localize('com_ui_review_material')}</p>
          {result.findings.length === 0 && <p>{localize('com_ui_review_empty')}</p>}
          {result.findings.map((finding, index) => (
            <article key={index} className="rounded-lg border border-border-light p-3">
              <h3 className="font-semibold">
                {localize(severities[finding.severity])}: {finding.title}
              </h3>
              <p className="break-all font-mono text-sm">
                {finding.path}:{finding.line}
              </p>
              <h4>{localize('com_ui_review_evidence')}</h4>
              <pre className="whitespace-pre-wrap break-words text-sm">{finding.evidence}</pre>
              <h4>{localize('com_ui_review_recommendation')}</h4>
              <p className="whitespace-pre-wrap break-words">{finding.recommendation}</p>
            </article>
          ))}
        </section>
      )}
    </section>
  );
}
