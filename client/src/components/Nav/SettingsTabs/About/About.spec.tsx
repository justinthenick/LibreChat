import React from 'react';
import userEvent from '@testing-library/user-event';
import { Constants } from 'librechat-data-provider';
import { act, render, screen } from '@testing-library/react';
import type { TStartupConfig } from 'librechat-data-provider';
import About from './About';

const mockCopy = jest.fn<boolean, unknown[]>();
jest.mock('copy-to-clipboard', () => ({
  __esModule: true,
  default: (...args: unknown[]) => mockCopy(...args),
}));

const mockUseGetStartupConfig = jest.fn();
jest.mock('~/data-provider', () => ({
  useGetStartupConfig: (...args: unknown[]) => mockUseGetStartupConfig(...args),
}));

jest.mock('~/hooks', () => ({
  useLocalize: () => (key: string) => key,
}));

const populatedBuildInfo: NonNullable<TStartupConfig['buildInfo']> = {
  commit: 'abcdef1234567890abcdef1234567890abcdef12',
  commitShort: 'abcdef1',
  branch: 'dev',
  buildDate: '2026-04-20T12:00:00Z',
};

const populatedCodingAgent: NonNullable<TStartupConfig['codingAgent']> = {
  executor: {
    configured: true,
    status: 'ok',
    version: '0.1.13',
  },
  maintenance: {
    configured: true,
    status: 'running',
  },
};

beforeEach(() => {
  mockCopy.mockReset();
  mockCopy.mockReturnValue(true);
  mockUseGetStartupConfig.mockReturnValue({ data: { buildInfo: populatedBuildInfo } });
});

describe('About', () => {
  describe('rendering', () => {
    it('requests a fresh startup config whenever About mounts', () => {
      render(<About />);

      expect(mockUseGetStartupConfig).toHaveBeenCalledWith({ refetchOnMount: 'always' });
    });

    it('renders version, commit (short), branch, and build date when buildInfo is populated', () => {
      render(<About />);

      expect(screen.getByText(Constants.VERSION as string)).toBeInTheDocument();
      expect(screen.getByText('abcdef1')).toBeInTheDocument();
      expect(screen.getByText('dev')).toBeInTheDocument();
      expect(screen.getByText('2026-04-20 12:00:00 UTC')).toBeInTheDocument();
    });

    it('renders coding-agent runtime rows when status is present', () => {
      mockUseGetStartupConfig.mockReturnValue({
        data: { buildInfo: populatedBuildInfo, codingAgent: populatedCodingAgent },
      });
      render(<About />);

      expect(screen.getByText('com_nav_about_coding_executor')).toBeInTheDocument();
      expect(screen.getByText('ok')).toBeInTheDocument();
      expect(screen.getByText('com_nav_about_coding_executor_version')).toBeInTheDocument();
      expect(screen.getByText('0.1.13')).toBeInTheDocument();
      expect(screen.getByText('com_nav_about_host_maintenance')).toBeInTheDocument();
      expect(screen.getByText('running')).toBeInTheDocument();
    });

    it('does not render coding-agent rows when status is absent', () => {
      render(<About />);

      expect(screen.queryByText('com_nav_about_coding_executor')).not.toBeInTheDocument();
      expect(screen.queryByText('com_nav_about_host_maintenance')).not.toBeInTheDocument();
    });

    it('renders em-dash placeholders when buildInfo is missing', () => {
      mockUseGetStartupConfig.mockReturnValue({ data: {} });
      render(<About />);

      // version still populated from Constants.VERSION; the other three rows fall back to placeholder
      const placeholders = screen.getAllByText('—');
      expect(placeholders.length).toBeGreaterThanOrEqual(3);
    });

    it('renders em-dash placeholders when startupConfig is undefined (initial load)', () => {
      mockUseGetStartupConfig.mockReturnValue({ data: undefined });
      render(<About />);

      const placeholders = screen.getAllByText('—');
      expect(placeholders.length).toBeGreaterThanOrEqual(3);
    });

    it('shows the raw string when buildDate is not a valid ISO', () => {
      mockUseGetStartupConfig.mockReturnValue({
        data: { buildInfo: { ...populatedBuildInfo, buildDate: 'not-a-date' } },
      });
      render(<About />);
      expect(screen.getByText('not-a-date')).toBeInTheDocument();
    });
  });

  describe('copy diagnostics', () => {
    it('writes a preformatted diagnostics blob to the clipboard on click', async () => {
      const user = userEvent.setup();
      render(<About />);

      await user.click(screen.getByRole('button', { name: /com_nav_about_diagnostics_copy/i }));

      expect(mockCopy).toHaveBeenCalledTimes(1);
      const [blob, options] = mockCopy.mock.calls[0] as [string, { format: string }];
      expect(options).toEqual({ format: 'text/plain' });
      expect(blob).toContain(`LibreChat version: ${Constants.VERSION}`);
      expect(blob).toContain(`Commit: ${populatedBuildInfo.commit}`);
      expect(blob).toContain(`Branch: ${populatedBuildInfo.branch}`);
      expect(blob).toContain('Build date: 2026-04-20 12:00:00 UTC');
      expect(blob).toContain('User agent: ');
    });

    it('includes coding-agent status in the diagnostics blob when present', async () => {
      mockUseGetStartupConfig.mockReturnValue({
        data: { buildInfo: populatedBuildInfo, codingAgent: populatedCodingAgent },
      });
      const user = userEvent.setup();
      render(<About />);

      await user.click(screen.getByRole('button', { name: /com_nav_about_diagnostics_copy/i }));

      const [blob] = mockCopy.mock.calls[0] as [string];
      expect(blob).toContain('Coding executor: ok');
      expect(blob).toContain('Coding executor version: 0.1.13');
      expect(blob).toContain('Host maintenance: running');
    });

    it('writes em-dash placeholders into the blob when buildInfo is missing', async () => {
      mockUseGetStartupConfig.mockReturnValue({ data: {} });
      const user = userEvent.setup();
      render(<About />);

      await user.click(screen.getByRole('button', { name: /com_nav_about_diagnostics_copy/i }));

      const [blob] = mockCopy.mock.calls[0] as [string];
      expect(blob).toContain('Commit: —');
      expect(blob).toContain('Branch: —');
      expect(blob).toContain('Build date: —');
    });

    it('does not flip to "Copied" when copy-to-clipboard reports failure', async () => {
      mockCopy.mockReturnValue(false);
      const user = userEvent.setup();
      render(<About />);

      await user.click(screen.getByRole('button', { name: /com_nav_about_diagnostics_copy/i }));

      expect(
        screen.getByRole('button', { name: /com_nav_about_diagnostics_copy/i }),
      ).toBeInTheDocument();
      expect(screen.queryByRole('button', { name: /com_ui_copied/i })).not.toBeInTheDocument();
      expect(screen.getByRole('status').textContent).toBe('');
    });

    it('toggles the button label to "Copied" after click and resets after the timer', async () => {
      jest.useFakeTimers();
      try {
        const user = userEvent.setup({ advanceTimers: jest.advanceTimersByTime });
        render(<About />);

        await user.click(screen.getByRole('button', { name: /com_nav_about_diagnostics_copy/i }));
        expect(screen.getByRole('button', { name: /com_ui_copied/i })).toBeInTheDocument();

        act(() => {
          jest.advanceTimersByTime(2000);
        });
        expect(
          screen.getByRole('button', { name: /com_nav_about_diagnostics_copy/i }),
        ).toBeInTheDocument();
      } finally {
        jest.useRealTimers();
      }
    });

    it('clears the pending reset timer on unmount (no state update on unmounted component)', async () => {
      jest.useFakeTimers();
      const clearSpy = jest.spyOn(globalThis, 'clearTimeout');
      try {
        const user = userEvent.setup({ advanceTimers: jest.advanceTimersByTime });
        const { unmount } = render(<About />);
        await user.click(screen.getByRole('button', { name: /com_nav_about_diagnostics_copy/i }));
        clearSpy.mockClear();
        unmount();
        expect(clearSpy).toHaveBeenCalled();
      } finally {
        clearSpy.mockRestore();
        jest.useRealTimers();
      }
    });
  });

  describe('status live region', () => {
    it('announces the copied state via a dedicated sr-only live region', async () => {
      const user = userEvent.setup();
      render(<About />);

      const status = screen.getByRole('status');
      expect(status.textContent).toBe('');

      await user.click(screen.getByRole('button', { name: /com_nav_about_diagnostics_copy/i }));
      expect(status.textContent).toMatch(/com_ui_copied/);
    });
  });
});
