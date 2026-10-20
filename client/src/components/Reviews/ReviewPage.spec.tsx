import { dataService } from 'librechat-data-provider';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import type { CodeReviewConfig } from 'librechat-data-provider';
import type { ReactNode } from 'react';
import mockTranslations from '~/locales/en/translation.json';
import ReviewPage from './ReviewPage';

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
const config = jest.fn<
  ReturnType<typeof dataService.getReviewConfig>,
  Parameters<typeof dataService.getReviewConfig>
>();
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
function mount() {
  const client = new QueryClient({ logger: { log: () => {}, warn: () => {}, error: () => {} } });
  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={client}>{children}</QueryClientProvider>
  );
  return render(<ReviewPage />, { wrapper });
}
function fill() {
  fireEvent.change(screen.getByLabelText('Repository ID'), {
    target: { value: request.repository },
  });
  fireEvent.change(screen.getByLabelText('Base commit (40-character SHA)'), {
    target: { value: request.base },
  });
  fireEvent.change(screen.getByLabelText('Head commit (40-character SHA)'), {
    target: { value: request.head },
  });
}
beforeEach(() => {
  mockAuth.user = { id: 'alice', tenantId: 'one' };
  mockAuth.isAuthenticated = true;
  mockAuth.isAuthReady = true;
  Object.defineProperty(crypto, 'randomUUID', { configurable: true, value: () => id });
  config.mockReset().mockResolvedValue({ enabled: true, repositories: ['fixture'] });
  start.mockReset().mockRejectedValue(new Error('delivery lost'));
  retrieve.mockReset().mockResolvedValue({ id, state: 'unknown' });
  cancel.mockReset().mockResolvedValue({ cancelled: true });
  jest.spyOn(dataService, 'getReviewConfig').mockImplementation(config);
  jest.spyOn(dataService, 'startReview').mockImplementation(start);
  jest.spyOn(dataService, 'retrieveReview').mockImplementation(retrieve);
  jest.spyOn(dataService, 'cancelReview').mockImplementation(cancel);
});
it.each(['not-ready', 'logged-out', 'disabled', 'forbidden'])(
  'keeps admission disabled for %s',
  async (reason) => {
    if (reason === 'not-ready') mockAuth.isAuthReady = false;
    if (reason === 'logged-out') mockAuth.isAuthenticated = false;
    if (reason === 'disabled') config.mockResolvedValue({ enabled: false, repositories: [] });
    if (reason === 'forbidden') config.mockRejectedValue({ response: { status: 403 } });
    mount();
    await act(async () => {});
    expect(screen.getByText('Code review is not enabled.')).toBeInTheDocument();
    expect(screen.queryByRole('button')).not.toBeInTheDocument();
    expect(start).not.toHaveBeenCalled();
    expect(config).toHaveBeenCalledTimes(['not-ready', 'logged-out'].includes(reason) ? 0 : 1);
  },
);
it('uses server discovery and supports explicit recovery and cancellation without replay', async () => {
  mount();
  await screen.findByRole('button', { name: 'Start review' });
  fill();
  fireEvent.change(screen.getByLabelText('Repository ID'), { target: { value: 'outside' } });
  expect(screen.getByRole('button', { name: 'Start review' })).toBeDisabled();
  fill();
  fireEvent.click(screen.getByRole('button', { name: 'Start review' }));
  await screen.findByText(/Outcome uncertain/);
  expect(start.mock.calls[0][0]).toEqual({ id, request });
  expect(config.mock.calls[0]).toHaveLength(1);
  expect(config.mock.calls[0][0]).toBeInstanceOf(AbortSignal);
  fireEvent.click(screen.getByRole('button', { name: 'Cancel review' }));
  await screen.findByText(/Cancellation request recorded/);
  retrieve.mockResolvedValue({
    id,
    request,
    state: 'failed',
    code: 'cancelled',
    expiresAt: Date.now() + 600000,
  });
  fireEvent.click(screen.getByRole('button', { name: 'Retrieve status / result' }));
  await screen.findByText('Review cancelled. No automatic retry will occur.');
  expect(start).toHaveBeenCalledTimes(1);
  expect(cancel).toHaveBeenCalledTimes(1);
  expect(retrieve).toHaveBeenCalledTimes(1);
});
it.each(['user', 'tenant'] as const)('discards late discovery on %s switch', async (change) => {
  let resolve!: (value: CodeReviewConfig) => void;
  config.mockImplementationOnce(
    () =>
      new Promise((done) => {
        resolve = done;
      }),
  );
  const page = mount();
  await waitFor(() => expect(config).toHaveBeenCalledTimes(1));
  config.mockResolvedValue({ enabled: false, repositories: [] });
  mockAuth.user =
    change === 'user' ? { id: 'bob', tenantId: 'one' } : { id: 'alice', tenantId: 'two' };
  page.rerender(<ReviewPage />);
  await waitFor(() => expect(config).toHaveBeenCalledTimes(2));
  await act(async () => resolve({ enabled: true, repositories: ['fixture'] }));
  expect(config.mock.calls[0][0]?.aborted).toBe(true);
  expect(screen.queryByRole('button')).not.toBeInTheDocument();
  expect(start).not.toHaveBeenCalled();
});
