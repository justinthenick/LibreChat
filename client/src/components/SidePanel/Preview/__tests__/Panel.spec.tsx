import axios from 'axios';
import { createServer } from 'node:http';
import userEvent from '@testing-library/user-event';
import { createHash, webcrypto } from 'node:crypto';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { act, cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import type { PreviewJob, PreviewStartRequest } from 'librechat-data-provider';
import type { Server, ServerResponse } from 'node:http';
import type { AddressInfo } from 'node:net';
import { acceptJob, settled } from '~/data-provider/Preview/session';
import PreviewPanel, { PreviewControls } from '../Panel';

jest.mock('~/hooks/AuthContext', () => ({
  useAuthContext: () => ({ isAuthenticated: true, user: { id: 'owner', tenantId: 'tenant' } }),
}));

let server: Server;
let client: QueryClient;
let job: PreviewJob;
let starts: PreviewStartRequest[];
let requests: Array<{ method: string; path: string; authorization?: string }>;
let failure: string | null;
let cancelState: 'cancelling' | 'cancelled';
let held: ServerResponse | null;
let holdStart: boolean;
let failStart: boolean;
let failCancel: boolean;
let holdGet: boolean;
let holdCancel: boolean;

const reply = (response: ServerResponse) =>
  response.end(JSON.stringify({ version: 1, ok: true, job }));

beforeAll(async () => {
  Object.defineProperty(globalThis, 'crypto', { value: webcrypto, configurable: true });
  server = createServer((req, res) => {
    res.setHeader('Access-Control-Allow-Origin', 'http://localhost:3080');
    res.setHeader('Access-Control-Allow-Credentials', 'true');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
    res.setHeader('Content-Type', 'application/json');
    if (req.method === 'OPTIONS') {
      res.end();
      return;
    }
    requests.push({
      method: req.method ?? '',
      path: req.url ?? '',
      authorization: req.headers.authorization,
    });
    if (failure) {
      res.statusCode =
        failure === 'preview_jobs_disabled' || failure === 'job_not_found' ? 404 : 503;
      res.end(JSON.stringify({ version: 1, ok: false, error: failure }));
      return;
    }
    if (req.method === 'POST' && req.url === '/api/agents/preview/jobs') {
      let body = '';
      req.on('data', (chunk: Buffer) => {
        body += chunk.toString();
      });
      req.on('end', () => {
        const request: PreviewStartRequest = JSON.parse(body);
        starts.push(request);
        job.generation_id = `preview:${createHash('sha256').update(request.idempotency_key).digest('hex')}`;
        if (holdStart) {
          held = res;
          return;
        }
        if (failStart) {
          res.statusCode = 503;
          res.end(JSON.stringify({ version: 1, ok: false, error: 'job_service_unavailable' }));
          return;
        }
        reply(res);
      });
      return;
    }
    if (req.url?.endsWith('/cancel')) {
      job = {
        ...job,
        state: cancelState,
        updated_at: job.updated_at + 1,
        error_code: cancelState === 'cancelled' ? 'cancelled' : 'cancel_requested',
      };
      if (failCancel) {
        if (holdCancel) {
          held = res;
          return;
        }
        res.statusCode = 503;
        res.end(JSON.stringify({ version: 1, ok: false, error: 'job_service_unavailable' }));
        return;
      }
    }
    if (req.method === 'GET' && holdGet) {
      held = res;
      return;
    }
    reply(res);
  });
  await new Promise<void>((resolve) => server.listen(0, '127.0.0.1', resolve));
  axios.defaults.baseURL = `http://127.0.0.1:${(server.address() as AddressInfo).port}`;
  axios.defaults.headers.common.Authorization = 'Bearer synthetic-owner';
});

afterAll(async () => {
  delete axios.defaults.baseURL;
  delete axios.defaults.headers.common.Authorization;
  await new Promise<void>((resolve, reject) =>
    server.close((error) => (error ? reject(error) : resolve())),
  );
});

beforeEach(() => {
  sessionStorage.clear();
  client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
    logger: { log: console.log, warn: console.warn, error: () => undefined },
  });
  starts = [];
  requests = [];
  failure = null;
  cancelState = 'cancelling';
  held = null;
  holdStart = false;
  failStart = false;
  failCancel = false;
  holdGet = false;
  holdCancel = false;
  job = {
    job_id: 'a'.repeat(32),
    generation_id: '',
    generation_epoch: 0,
    state: 'running',
    created_at: 1,
    updated_at: 2,
    deadline_at: 301,
    metadata: {
      profile_id: 'preview',
      model: 'gpt-5.6-sol',
      repository_alias: 'fixture',
      task_mode: 'read_only',
      max_requests: 10,
      timeout_seconds: 300,
    },
    result: null,
    error_code: null,
    request_count: 1,
  };
});

afterEach(() => {
  if (held) reply(held);
  cleanup();
  client.clear();
  delete process.env.VITE_OPENHANDS_PREVIEW_UI;
});

function mount(owner = 'tenant:owner') {
  return render(
    <QueryClientProvider client={client}>
      <PreviewControls key={owner} owner={owner} />
    </QueryClientProvider>,
  );
}

function start() {
  fireEvent.change(screen.getByLabelText('Repository alias'), { target: { value: 'fixture' } });
  fireEvent.change(screen.getByLabelText('Task'), {
    target: { value: 'Inspect synthetic fixture' },
  });
  fireEvent.click(screen.getByRole('button', { name: 'Start preview' }));
}

async function running() {
  await screen.findByText('Running');
  await waitFor(() => expect(screen.getByRole('button', { name: 'Refresh status' })).toBeEnabled());
}

test('is default off and makes no HTTP requests', () => {
  render(
    <QueryClientProvider client={client}>
      <PreviewPanel />
    </QueryClientProvider>,
  );
  expect(screen.queryByRole('region')).not.toBeInTheDocument();
  expect(requests).toHaveLength(0);
});

test('supports keyboard form entry and exposes live status', async () => {
  const user = userEvent.setup();
  mount();
  await user.tab();
  expect(screen.getByLabelText('Repository alias')).toHaveFocus();
  await user.keyboard('fixture');
  await user.tab();
  expect(screen.getByLabelText('Task')).toHaveFocus();
  await user.keyboard('Inspect synthetic fixture');
  await user.tab();
  expect(screen.getByRole('button', { name: 'Start preview' })).toHaveFocus();
  await user.keyboard('{Enter}');
  await running();
  expect(screen.getByRole('status')).toHaveAttribute('aria-live', 'polite');
});

test('unconfirmed external stop never enables a new job or claims cancelled', async () => {
  job.state = 'failed';
  job.error_code = 'execution_stop_unconfirmed';
  mount();
  start();
  await screen.findByText('Execution stop is unconfirmed. Refresh status to recover.');
  expect(screen.queryByRole('button', { name: 'New preview' })).not.toBeInTheDocument();
  expect(screen.queryByText('Cancellation confirmed by the job service.')).not.toBeInTheDocument();
});

test('uses labelled controls and authenticated HTTP; repeated start is single-flight', async () => {
  holdStart = true;
  mount();
  expect(screen.getByRole('button', { name: 'Start preview' })).toBeDisabled();
  start();
  fireEvent.submit(screen.getByLabelText('Task').closest('form')!);
  await waitFor(() => expect(starts).toHaveLength(1));
  expect(requests[0].authorization).toBe('Bearer synthetic-owner');
  expect(starts[0].scope.task_mode).toBe('read_only');
  await act(async () => {
    reply(held!);
    held = null;
  });
  await running();
});

test('uncertain starts survive reload and retry exactly the same request', async () => {
  failStart = true;
  const view = mount();
  start();
  await screen.findByRole('alert');
  view.unmount();
  failStart = false;
  mount();
  fireEvent.click(screen.getByRole('button', { name: 'Retry same start' }));
  await running();
  expect(starts).toHaveLength(2);
  expect(starts[1]).toEqual(starts[0]);
});

test('reload resumes GET, never POST; a disconnect remains recoverable', async () => {
  const view = mount();
  start();
  await running();
  view.unmount();
  failure = 'job_service_unavailable';
  mount();
  await screen.findByRole('alert');
  expect(starts).toHaveLength(1);
  failure = null;
  fireEvent.click(screen.getByRole('button', { name: 'Refresh status' }));
  await running();
});

test('cancel requested and ambiguous cancellation never claim confirmed', async () => {
  mount();
  start();
  await running();
  fireEvent.click(screen.getByRole('button', { name: 'Request cancellation' }));
  await screen.findByText('Cancellation requested; stopping is not yet confirmed.');
  expect(screen.queryByText('Cancellation confirmed by the job service.')).not.toBeInTheDocument();
  await waitFor(() =>
    expect(screen.getByRole('button', { name: 'Request cancellation' })).toBeEnabled(),
  );
  failure = 'job_service_unavailable';
  fireEvent.click(screen.getByRole('button', { name: 'Request cancellation' }));
  await screen.findByRole('alert');
  expect(screen.queryByText('Cancellation confirmed by the job service.')).not.toBeInTheDocument();
  await waitFor(() =>
    expect(screen.getByRole('button', { name: 'Request cancellation' })).toBeEnabled(),
  );
  failure = null;
  job = { ...job, state: 'cancelled', error_code: 'cancelled', updated_at: 5 };
  fireEvent.click(screen.getByRole('button', { name: 'Refresh status' }));
  await screen.findByText('Cancellation confirmed by the job service.');
});

test.each(['generation', 'job', 'scope'])('rejects stale %s identity on reload', async (field) => {
  const view = mount();
  start();
  await running();
  view.unmount();
  if (field === 'generation') job.generation_id = `preview:${'b'.repeat(64)}`;
  if (field === 'job') job.job_id = 'b'.repeat(32);
  if (field === 'scope') job.metadata = { ...job.metadata, repository_alias: 'another' };
  mount();
  expect(await screen.findByRole('alert')).toHaveTextContent('identity or status is stale');
  expect(screen.queryByText('Running')).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: 'Request cancellation' }));
  await waitFor(() =>
    expect(screen.getByRole('button', { name: 'Request cancellation' })).toBeEnabled(),
  );
  expect(requests.some((request) => request.path.endsWith('/cancel'))).toBe(false);
});

test('a late start response cannot populate a different owner', async () => {
  holdStart = true;
  const view = mount();
  start();
  await waitFor(() => expect(held).not.toBeNull());
  view.unmount();
  mount('another-tenant:another-owner');
  await act(async () => {
    reply(held!);
    held = null;
  });
  expect(screen.getByLabelText('Task')).toHaveValue('');
  expect(screen.queryByText('Running')).not.toBeInTheDocument();
  expect(requests.filter((request) => request.method === 'GET')).toHaveLength(0);
});

test.each(['preview_jobs_disabled', 'job_service_unavailable', 'job_not_found'])(
  'handles %s without success claims',
  async (code) => {
    failure = code;
    mount();
    start();
    await screen.findByRole('alert');
    expect(
      screen.queryByText('Cancellation confirmed by the job service.'),
    ).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Retry same start' })).toBeEnabled();
  },
);

test('renders evidence as text and does not equate completion to checks passing', async () => {
  job.state = 'completed';
  job.result = {
    execution_status: 'finished',
    final_response: '<script>unsafe()</script>',
    evidence: {
      repository_alias: 'fixture',
      task: null,
      checks: [],
      final_diff: null,
      final_status: null,
      observed_checks_status: 'not_run',
      evidence_complete: false,
      action_count: 0,
      pending_count: 0,
      errors: [],
    },
  };
  mount();
  start();
  await screen.findByText('Completed');
  expect(screen.getByText('<script>unsafe()</script>')).toBeInTheDocument();
  expect(document.querySelector('script')).toBeNull();
  expect(
    screen.getByText('Evidence incomplete. Completion does not imply checks passed.'),
  ).toBeInTheDocument();
});

test('recovers automatically when a dispatched cancellation loses its response', async () => {
  mount();
  start();
  await running();
  failCancel = true;
  cancelState = 'cancelled';
  fireEvent.click(screen.getByRole('button', { name: 'Request cancellation' }));
  await screen.findByRole('alert');
  expect(requests.some((request) => request.path.endsWith('/cancel'))).toBe(true);
  expect(screen.queryByText('Cancellation confirmed by the job service.')).not.toBeInTheDocument();
  await screen.findByText('Cancellation confirmed by the job service.', {}, { timeout: 4000 });
  expect(screen.queryByRole('alert')).not.toBeInTheDocument();
});

test('recovers when terminal polling beats a delayed failed cancel response', async () => {
  mount();
  start();
  await running();
  failCancel = true;
  holdCancel = true;
  cancelState = 'cancelled';
  fireEvent.click(screen.getByRole('button', { name: 'Request cancellation' }));
  await waitFor(() => expect(held).not.toBeNull());
  await screen.findByText('Cancellation confirmed by the job service.', {}, { timeout: 4000 });
  await act(async () => {
    held!.statusCode = 503;
    held!.end(JSON.stringify({ version: 1, ok: false, error: 'job_service_unavailable' }));
    held = null;
  });
  await screen.findByRole('alert');
  await screen.findByText('Cancellation confirmed by the job service.', {}, { timeout: 4000 });
  expect(screen.queryByRole('alert')).not.toBeInTheDocument();
}, 10000);

test('a late GET cannot contaminate a new preview after reset', async () => {
  job.state = 'cancelled';
  job.error_code = 'cancelled';
  mount();
  start();
  await screen.findByText('Cancellation confirmed by the job service.');
  await waitFor(() => expect(screen.getByRole('button', { name: 'Refresh status' })).toBeEnabled());
  holdGet = true;
  fireEvent.click(screen.getByRole('button', { name: 'Refresh status' }));
  await waitFor(() => expect(held).not.toBeNull());
  const oldJob = { ...job };
  fireEvent.click(screen.getByRole('button', { name: 'New preview' }));
  job = { ...job, job_id: 'b'.repeat(32), state: 'running', error_code: null };
  holdGet = false;
  fireEvent.click(screen.getByRole('button', { name: 'Start preview' }));
  await running();
  await act(async () => {
    held!.end(JSON.stringify({ version: 1, ok: true, job: oldJob }));
    held = null;
  });
  fireEvent.click(screen.getByRole('button', { name: 'Refresh status' }));
  await running();
  expect(screen.queryByRole('alert')).not.toBeInTheDocument();
});

test('stop-unconfirmed remains recoverable; same-time snapshots cannot regress terminal or cancelling state', () => {
  const session = {
    generation: job.generation_id,
    jobId: job.job_id,
    request: {
      prompt: 'test',
      idempotency_key: 'test',
      scope: { repository_alias: 'fixture', task_mode: 'read_only' as const },
      max_requests: 10,
      timeout_seconds: 300,
    },
  };
  expect(settled({ ...job, state: 'failed', error_code: 'execution_stop_unconfirmed' })).toBe(
    false,
  );
  for (const state of ['cancelled', 'cancelling'] as const) {
    expect(() => acceptJob({ version: 1, ok: true, job }, session, { ...job, state })).toThrow(
      'preview_identity',
    );
  }
});
