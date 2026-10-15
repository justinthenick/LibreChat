import { dataService } from 'librechat-data-provider';
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider, onlineManager } from '@tanstack/react-query';
import type {
  CodeReviewResult,
  CodeReviewSelection,
  CodeReviewRecovery,
} from 'librechat-data-provider';
import type { ReactNode } from 'react';
import mockTranslations from '~/locales/en/translation.json';
import ReviewPanel from './ReviewPanel';

jest.mock('librechat-data-provider', () => {
  const actual = jest.requireActual('librechat-data-provider');
  return { ...actual, dataService: { ...actual.dataService } };
});

const mockAuth = {
  user: { id: 'alice', tenantId: 'one' },
  isAuthenticated: true,
  isAuthReady: true,
};
jest.mock('~/hooks/AuthContext', () => ({ useAuthContext: () => mockAuth }));
jest.mock('~/hooks/useLocalize', () => ({
  __esModule: true,
  default: () => (key: keyof typeof mockTranslations) => mockTranslations[key],
}));

const id = '11111111-1111-4111-8111-111111111111';
const request = { repository: 'fixture', base: 'a'.repeat(40), head: 'b'.repeat(40) };
const result: CodeReviewResult = {
  ...request,
  status: 'human_review_required',
  provider: 'chatgpt_subscription',
  model: 'gpt-5.6-sol',
  findings: [],
};
const start = jest.fn<
  ReturnType<typeof dataService.startReview>,
  Parameters<typeof dataService.startReview>
>();
const retrieve = jest.fn<
  ReturnType<typeof dataService.retrieveReview>,
  Parameters<typeof dataService.retrieveReview>
>();
const cancel = jest.fn<
  ReturnType<typeof dataService.cancelReview>,
  Parameters<typeof dataService.cancelReview>
>();
const resolveSelection = jest.fn<
  ReturnType<typeof dataService.resolveReviewSelection>,
  Parameters<typeof dataService.resolveReviewSelection>
>();
const binding = { number: 7, repositoryId: 123 };
const selection: CodeReviewSelection = {
  request: { ...request, pullRequest: binding },
  pullRequest: 7,
  status: 'resolved',
  checkedAt: '2026-10-14T04:00:00.000Z',
};
const boundResult: CodeReviewResult = {
  ...result,
  pullRequest: binding,
  prCheckedAt: selection.checkedAt,
};
function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((done) => {
    resolve = done;
  });
  return { promise, resolve };
}
function mount(enabled = true) {
  const client = new QueryClient({
    defaultOptions: { mutations: { retry: false } },
    logger: { log: () => {}, warn: () => {}, error: () => {} },
  });
  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={client}>{children}</QueryClientProvider>
  );
  return render(<ReviewPanel enabled={enabled} repositories={['fixture']} />, { wrapper });
}
function fill(runId?: string) {
  fireEvent.change(screen.getByLabelText('Repository ID'), {
    target: { value: request.repository },
  });
  fireEvent.change(screen.getByLabelText('Base commit (40-character SHA)'), {
    target: { value: request.base },
  });
  fireEvent.change(screen.getByLabelText('Head commit (40-character SHA)'), {
    target: { value: request.head },
  });
  if (runId) fireEvent.change(screen.getByLabelText('Review ID'), { target: { value: runId } });
}
beforeEach(() => {
  mockAuth.user = { id: 'alice', tenantId: 'one' };
  mockAuth.isAuthenticated = true;
  mockAuth.isAuthReady = true;
  Object.defineProperty(crypto, 'randomUUID', { configurable: true, value: () => id });
  start.mockReset().mockResolvedValue(result);
  retrieve.mockReset().mockResolvedValue({ id, state: 'unknown' });
  cancel.mockReset().mockResolvedValue({ cancelled: true });
  resolveSelection.mockReset().mockResolvedValue(selection);
  jest.spyOn(dataService, 'resolveReviewSelection').mockImplementation(resolveSelection);
  jest.spyOn(dataService, 'startReview').mockImplementation(start);
  jest.spyOn(dataService, 'retrieveReview').mockImplementation(retrieve);
  jest.spyOn(dataService, 'cancelReview').mockImplementation(cancel);
});
afterEach(() => {
  onlineManager.setOnline(true);
});

it('requires the explicit feature gate and authenticated ready identity', () => {
  const page = mount(false);
  expect(screen.queryByRole('button')).not.toBeInTheDocument();
  mockAuth.isAuthenticated = false;
  page.rerender(<ReviewPanel enabled repositories={['fixture']} />);
  expect(screen.getByText('Code review is not enabled.')).toBeInTheDocument();
  expect(start).not.toHaveBeenCalled();
  expect(retrieve).not.toHaveBeenCalled();
});

it('prevents duplicate starts and shows exact identity, coverage and human-required zero findings', async () => {
  const pending = deferred<CodeReviewResult>();
  start.mockReturnValue(pending.promise);
  mount();
  fill();
  const button = screen.getByRole('button', { name: 'Start review' });
  fireEvent.click(button);
  fireEvent.click(button);
  await waitFor(() => expect(start).toHaveBeenCalledTimes(1));
  expect(start.mock.calls[0][0]).toEqual({ id, request });
  await act(async () => pending.resolve(result));
  expect(await screen.findByRole('heading', { name: 'Human review required' })).toBeInTheDocument();
  expect(screen.getByText(request.head)).toBeInTheDocument();
  expect(screen.getByText('human_review_required')).toBeInTheDocument();
  expect(screen.getByText(/No material findings were returned/)).toBeInTheDocument();
  expect(screen.getByText(/Deletion-only evidence is unsupported/)).toBeInTheDocument();
  expect(button).toBeDisabled();
});

it('renders material evidence as inert text', async () => {
  start.mockResolvedValue({
    ...result,
    findings: [
      {
        severity: 'major',
        path: 'src/a.py',
        line: 3,
        title: '<img src=x onerror=alert(1)>',
        evidence: '<script>bad()</script>',
        recommendation: 'Validate before division.',
      },
    ],
  });
  const page = mount();
  fill();
  fireEvent.click(screen.getByRole('button', { name: 'Start review' }));
  expect(await screen.findByText('<script>bad()</script>')).toBeInTheDocument();
  expect(screen.getByText('src/a.py:3')).toBeInTheDocument();
  expect(page.container.querySelector('script, img')).toBeNull();
});

it('retrieves explicitly after uncertain delivery without resubmission or offline queuing', async () => {
  onlineManager.setOnline(false);
  start.mockRejectedValue(new Error('lost response'));
  mount();
  fill();
  fireEvent.click(screen.getByRole('button', { name: 'Start review' }));
  expect(await screen.findByText(/Outcome uncertain/)).toBeInTheDocument();
  onlineManager.setOnline(true);
  retrieve.mockResolvedValue({ id, request, state: 'completed', result, expiresAt: 1800000000000 });
  fireEvent.click(screen.getByRole('button', { name: 'Retrieve status / result' }));
  expect(await screen.findByText('2027-01-15T08:00:00.000Z')).toBeInTheDocument();
  expect(start).toHaveBeenCalledTimes(1);
  expect(retrieve).toHaveBeenCalledTimes(1);
});

it('can retrieve while a start response hangs, detaching delivery without cancelling work', async () => {
  const pending = deferred<CodeReviewResult>();
  start.mockReturnValue(pending.promise);
  retrieve.mockResolvedValue({ id, request, state: 'running', cancelRequested: false });
  mount();
  fill();
  fireEvent.click(screen.getByRole('button', { name: 'Start review' }));
  await waitFor(() => expect(start).toHaveBeenCalledTimes(1));
  fireEvent.click(screen.getByRole('button', { name: 'Retrieve status / result' }));
  await waitFor(() => expect(retrieve).toHaveBeenCalledTimes(1));
  expect(start.mock.calls[0][1]?.aborted).toBe(true);
  expect(cancel).not.toHaveBeenCalled();
  await act(async () => pending.resolve(result));
  expect(screen.queryByRole('heading', { name: 'Human review required' })).not.toBeInTheDocument();
});

it('hides late responses after selection changes and rejects mismatched recovered identity', async () => {
  const pending = deferred<CodeReviewResult>();
  start.mockReturnValue(pending.promise);
  mount();
  fill();
  fireEvent.click(screen.getByRole('button', { name: 'Start review' }));
  await waitFor(() => expect(start).toHaveBeenCalledTimes(1));
  fireEvent.change(screen.getByLabelText('Head commit (40-character SHA)'), {
    target: { value: 'c'.repeat(40) },
  });
  await act(async () => pending.resolve(result));
  expect(screen.queryByRole('heading', { name: 'Human review required' })).not.toBeInTheDocument();
  retrieve.mockResolvedValue({ id, state: 'completed', request, result, expiresAt: 1800000000000 });
  fireEvent.click(screen.getByRole('button', { name: 'Retrieve status / result' }));
  expect(await screen.findByText(/Outcome uncertain/)).toBeInTheDocument();
  expect(cancel).not.toHaveBeenCalled();
});

it.each(['user', 'tenant', 'logout'] as const)(
  'clears state and ignores late results on %s change',
  async (change) => {
    const pending = deferred<CodeReviewResult>();
    start.mockReturnValue(pending.promise);
    const page = mount();
    fill();
    fireEvent.click(screen.getByRole('button', { name: 'Start review' }));
    await waitFor(() => expect(start).toHaveBeenCalledTimes(1));
    if (change === 'user') mockAuth.user = { id: 'bob', tenantId: 'one' };
    if (change === 'tenant') mockAuth.user = { id: 'alice', tenantId: 'two' };
    if (change === 'logout') mockAuth.isAuthenticated = false;
    page.rerender(<ReviewPanel enabled repositories={['fixture']} />);
    await act(async () => pending.resolve(result));
    expect(
      screen.queryByRole('heading', { name: 'Human review required' }),
    ).not.toBeInTheDocument();
    expect(start.mock.calls[0][1]?.aborted).toBe(true);
    expect(cancel).not.toHaveBeenCalled();
    if (change !== 'logout') expect(screen.getByLabelText('Review ID')).toHaveValue('');
  },
);

it('navigation unmount aborts delivery only and manual retrieval supports unknown/expired state', async () => {
  const pending = deferred<CodeReviewResult>();
  start.mockReturnValue(pending.promise);
  const page = mount();
  fill();
  fireEvent.click(screen.getByRole('button', { name: 'Start review' }));
  await waitFor(() => expect(start).toHaveBeenCalledTimes(1));
  page.unmount();
  expect(start.mock.calls[0][1]?.aborted).toBe(true);
  await act(async () => pending.resolve(result));
  mount();
  fill(id);
  fireEvent.click(screen.getByRole('button', { name: 'Retrieve status / result' }));
  expect(await screen.findByText(/Unknown or expired/)).toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Start review' })).toBeDisabled();
  expect(start).toHaveBeenCalledTimes(1);
  expect(cancel).not.toHaveBeenCalled();
});

it('guards duplicate cancel clicks and distinguishes acknowledgement from confirmed cancellation', async () => {
  const pending = deferred<{ cancelled: true }>();
  cancel.mockReturnValue(pending.promise);
  mount();
  fill(id);
  fireEvent.click(screen.getByRole('button', { name: 'Cancel review' }));
  fireEvent.click(screen.getByRole('button', { name: 'Cancel review' }));
  await waitFor(() => expect(cancel).toHaveBeenCalledTimes(1));
  await act(async () => pending.resolve({ cancelled: true }));
  expect(await screen.findByText(/Cancellation request recorded/)).toBeInTheDocument();
  retrieve.mockResolvedValue({
    id,
    request,
    state: 'failed',
    code: 'cancelled',
    expiresAt: 1800000000000,
  });
  fireEvent.click(screen.getByRole('button', { name: 'Retrieve status / result' }));
  expect(
    await screen.findByText('Review cancelled. No automatic retry will occur.'),
  ).toBeInTheDocument();
  expect(start).not.toHaveBeenCalled();
});

it('rejects unauthorized repository and non-immutable selection locally', () => {
  mount();
  fill();
  fireEvent.change(screen.getByLabelText('Repository ID'), { target: { value: 'outside' } });
  expect(screen.getByRole('button', { name: 'Start review' })).toBeDisabled();
  expect(start).not.toHaveBeenCalled();
});

it.each(['worker_failed', 'output_limit', 'configuration', 'invalid_response'] as const)(
  'shows settled %s as failed',
  async (code) => {
    retrieve.mockResolvedValue({
      id,
      state: 'failed',
      request,
      expiresAt: Date.now() + 600000,
      code,
    });
    mount();
    fill(id);
    fireEvent.click(screen.getByRole('button', { name: 'Retrieve status / result' }));
    await waitFor(() =>
      expect(screen.getByRole('status')).toHaveTextContent(mockTranslations.com_ui_review_failed),
    );
  },
);
it('keeps a direct cancelled response uncertain until settlement is retrieved', async () => {
  start.mockRejectedValue({ isAxiosError: true, response: { data: { code: 'cancelled' } } });
  mount();
  fill();
  fireEvent.click(screen.getByRole('button', { name: 'Start review' }));
  await waitFor(() =>
    expect(screen.getByRole('status')).toHaveTextContent(mockTranslations.com_ui_review_uncertain),
  );
  retrieve.mockResolvedValue({
    id,
    state: 'failed',
    request,
    expiresAt: Date.now() + 600000,
    code: 'cancelled',
  });
  fireEvent.click(screen.getByRole('button', { name: 'Retrieve status / result' }));
  await waitFor(() =>
    expect(screen.getByRole('status')).toHaveTextContent(mockTranslations.com_ui_review_cancelled),
  );
});

it('ignores a status response superseded by a cancellation acknowledgement', async () => {
  const pending = deferred<Awaited<ReturnType<typeof dataService.retrieveReview>>>();
  retrieve.mockReturnValue(pending.promise);
  mount();
  fill(id);
  fireEvent.click(screen.getByRole('button', { name: 'Retrieve status / result' }));
  await waitFor(() => expect(retrieve).toHaveBeenCalledTimes(1));
  fireEvent.click(screen.getByRole('button', { name: 'Cancel review' }));
  expect(await screen.findByText(/Cancellation request recorded/)).toBeInTheDocument();
  expect(retrieve.mock.calls[0][1]?.aborted).toBe(true);
  await act(async () => pending.resolve({ id, request, state: 'running', cancelRequested: false }));
  expect(screen.getByText(/Cancellation request recorded/)).toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Retrieve status / result' })).toBeEnabled();
  expect(start).not.toHaveBeenCalled();
  expect(cancel).toHaveBeenCalledTimes(1);
});

async function selectPr() {
  fireEvent.change(screen.getByLabelText('Pull request number (optional)'), {
    target: { value: '7' },
  });
  fireEvent.click(screen.getByRole('button', { name: 'Resolve PR' }));
  await waitFor(() => expect(resolveSelection).toHaveBeenCalledTimes(1));
  await waitFor(() => expect(screen.getByRole('button', { name: 'Resolve PR' })).toBeEnabled());
}
it('binds resolved PR identity to admission and shows point-in-time verification', async () => {
  start.mockResolvedValue(boundResult);
  mount();
  fill();
  await selectPr();
  fireEvent.click(screen.getByRole('button', { name: 'Start review' }));
  expect(await screen.findByText(selection.checkedAt)).toBeInTheDocument();
  expect(start.mock.calls[0][0]).toEqual({ id, request: selection.request });
  expect(screen.getByText(/It may change afterward/)).toBeInTheDocument();
});
it('hides completed findings on stale recovery and keeps cancellation available', async () => {
  start.mockResolvedValue(boundResult);
  mount();
  fill();
  await selectPr();
  fireEvent.click(screen.getByRole('button', { name: 'Start review' }));
  expect(await screen.findByText(selection.checkedAt)).toBeInTheDocument();
  retrieve.mockRejectedValue({ isAxiosError: true, response: { data: { code: 'stale_review' } } });
  fireEvent.click(screen.getByRole('button', { name: 'Retrieve status / result' }));
  expect(await screen.findByText(/PR closed or selected commits changed/)).toBeInTheDocument();
  expect(screen.queryByRole('heading', { name: 'Human review required' })).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: 'Cancel review' }));
  expect(await screen.findByText(/Cancellation request recorded/)).toBeInTheDocument();
  expect(start).toHaveBeenCalledTimes(1);
});
it.each(['missing-binding', 'wrong-pr', 'wrong-repository', 'missing-check'] as const)(
  'rejects %s in PR results',
  async (change) => {
    const value = { ...boundResult };
    if (change === 'missing-binding') delete value.pullRequest;
    if (change === 'wrong-pr') value.pullRequest = { ...binding, number: 8 };
    if (change === 'wrong-repository') value.pullRequest = { ...binding, repositoryId: 456 };
    if (change === 'missing-check') delete value.prCheckedAt;
    start.mockResolvedValue(value);
    mount();
    fill();
    await selectPr();
    fireEvent.click(screen.getByRole('button', { name: 'Start review' }));
    expect(await screen.findByText(/Outcome uncertain/)).toBeInTheDocument();
    expect(
      screen.queryByRole('heading', { name: 'Human review required' }),
    ).not.toBeInTheDocument();
  },
);
it('preserves the original pair when resolving a moved PR for manual recovery', async () => {
  resolveSelection.mockResolvedValue({
    ...selection,
    status: 'stale',
    request: { ...selection.request, head: 'c'.repeat(40) },
  });
  mount();
  fill(id);
  await selectPr();
  expect(screen.getByLabelText('Head commit (40-character SHA)')).toHaveValue(request.head);
  expect(resolveSelection.mock.calls[0][0]).toEqual({
    repository: request.repository,
    pullRequest: 7,
    expected: { base: request.base, head: request.head },
  });
  fireEvent.click(screen.getByRole('button', { name: 'Retrieve status / result' }));
  await waitFor(() => expect(retrieve).toHaveBeenCalledTimes(1));
  expect(retrieve.mock.calls[0][0]).toEqual({ id, request: selection.request });
  expect(start).not.toHaveBeenCalled();
});
it.each(['user', 'tenant', 'selection'] as const)(
  'ignores a delayed PR resolution after %s changes',
  async (change) => {
    const pending = deferred<CodeReviewSelection>();
    resolveSelection.mockReturnValue(pending.promise);
    const page = mount();
    fill();
    fireEvent.change(screen.getByLabelText('Pull request number (optional)'), {
      target: { value: '7' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Resolve PR' }));
    await waitFor(() => expect(resolveSelection).toHaveBeenCalledTimes(1));
    if (change === 'selection')
      fireEvent.change(screen.getByLabelText('Pull request number (optional)'), {
        target: { value: '8' },
      });
    else {
      mockAuth.user =
        change === 'user' ? { id: 'bob', tenantId: 'one' } : { id: 'alice', tenantId: 'two' };
      page.rerender(<ReviewPanel enabled repositories={['fixture']} />);
    }
    await act(async () => pending.resolve(selection));
    expect(resolveSelection.mock.calls[0][1]?.aborted).toBe(true);
    expect(screen.getByRole('button', { name: 'Start review' })).toBeDisabled();
    expect(start).not.toHaveBeenCalled();
  },
);

it('shows interrupted recovery explicitly and never starts or replays work', async () => {
  retrieve.mockResolvedValue({ id, request, state: 'interrupted', cancelRequested: true });
  mount();
  fill(id);
  fireEvent.click(screen.getByRole('button', { name: 'Retrieve status / result' }));
  expect(
    await screen.findByText(/Review interrupted or execution stop unconfirmed/),
  ).toBeInTheDocument();
  expect(screen.queryByRole('heading', { name: 'Human review required' })).not.toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Start review' })).toBeDisabled();
  expect(start).not.toHaveBeenCalled();
});

it.each(['running', 'completed', 'interrupted', 'failed', 'unknown'] as const)(
  'recovers %s with a canonical response to a mixed-case UUID',
  async (state) => {
    const canonical = 'abcdefab-cdef-4abc-8def-abcdefabcdef';
    const mixed = 'AbCdEfAb-CdEf-4AbC-8dEf-AbCdEfAbCdEf';
    const responses: Record<typeof state, CodeReviewRecovery> = {
      running: { id: canonical, request, state: 'running', cancelRequested: false },
      completed: { id: canonical, request, state: 'completed', result, expiresAt: 1800000000000 },
      interrupted: { id: canonical, request, state: 'interrupted', cancelRequested: true },
      failed: {
        id: canonical,
        request,
        state: 'failed',
        code: 'worker_failed',
        expiresAt: 1800000000000,
      },
      unknown: { id: canonical, state: 'unknown' },
    };
    const notices = {
      running: mockTranslations.com_ui_review_running,
      completed: mockTranslations.com_ui_review_completed,
      interrupted: mockTranslations.com_ui_review_interrupted,
      failed: mockTranslations.com_ui_review_failed,
      unknown: mockTranslations.com_ui_review_unknown,
    };
    retrieve.mockResolvedValue(responses[state]);
    mount();
    fill(mixed);
    fireEvent.click(screen.getByRole('button', { name: mockTranslations.com_ui_review_retrieve }));
    await waitFor(() => expect(retrieve).toHaveBeenCalledTimes(1));
    await waitFor(() => expect(screen.getByLabelText('Review ID')).toHaveValue(canonical));
    await waitFor(() =>
      expect(
        screen.getByRole('button', { name: mockTranslations.com_ui_review_retrieve }),
      ).toBeEnabled(),
    );
    await waitFor(() => expect(screen.getByRole('status')).toHaveTextContent(notices[state]));
    expect(retrieve.mock.calls[0][0]).toEqual({ id: canonical, request });
    expect(start).not.toHaveBeenCalled();
  },
);

it.each(['id', 'request'] as const)(
  'rejects a different recovered %s despite mixed-case normalization',
  async (mismatch) => {
    const canonical = 'abcdefab-cdef-4abc-8def-abcdefabcdef';
    retrieve.mockResolvedValue({
      id: mismatch === 'id' ? id : canonical,
      request: mismatch === 'request' ? { ...request, head: 'c'.repeat(40) } : request,
      state: 'completed',
      result,
      expiresAt: 1800000000000,
    });
    mount();
    fill(canonical.toUpperCase());
    fireEvent.click(screen.getByRole('button', { name: mockTranslations.com_ui_review_retrieve }));
    await waitFor(() =>
      expect(screen.getByRole('status')).toHaveTextContent(
        mockTranslations.com_ui_review_uncertain,
      ),
    );
    expect(
      screen.queryByRole('region', { name: mockTranslations.com_ui_review_result }),
    ).not.toBeInTheDocument();
    expect(start).not.toHaveBeenCalled();
  },
);
