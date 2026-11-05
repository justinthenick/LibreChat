import type { ReviewServiceConfig } from './transport';
import { selectReviewExecutionBackend } from './execution';
import { createCodeReviewWorker } from './worker';
import { createReviewService } from './transport';
import { reviewRequestSchema } from './schema';

describe('internal review execution selection', () => {
  it.each([undefined, 'local'] as const)('keeps %s on the existing local factory', (mode) => {
    expect(selectReviewExecutionBackend(mode)).toBe(createCodeReviewWorker);
  });

  it.each(
    ['supervisor', '', 'LOCAL', 'unknown', null, false, ['local'], {}].map((backend) => ({ backend })),
  )(
    'refuses unsupported runtime selection $backend before configuration access',
    async ({ backend }) => {
      const read = jest.fn((): never => {
        throw new Error('execution configuration must not be read');
      });
      const config: ReviewServiceConfig = {
        enabled: true,
        get url() {
          return read();
        },
        get token() {
          return read();
        },
        get worker() {
          return read();
        },
        get journal() {
          return read();
        },
      };
      Object.defineProperty(config, 'backend', { value: backend });
      const service = createReviewService(config);
      for (const endpoint of ['review', 'review/status', 'review/cancel']) {
        const response = await service(new Request(`http://127.0.0.1:9876/${endpoint}`));
        expect(response.status).toBe(503);
        expect(await response.json()).toEqual({ code: 'configuration' });
      }
      expect(read).not.toHaveBeenCalled();
    },
  );

  it('does not read backend or execution configuration while disabled', async () => {
    const read = jest.fn((): never => {
      throw new Error('disabled configuration must not be read');
    });
    const config: ReviewServiceConfig = {
      get backend() {
        return read();
      },
      get url() {
        return read();
      },
      get token() {
        return read();
      },
      get worker() {
        return read();
      },
      get journal() {
        return read();
      },
    };
    const response = await createReviewService(config)(new Request('http://127.0.0.1:9876/review'));
    expect(response.status).toBe(503);
    expect(read).not.toHaveBeenCalled();
  });

  it('does not allow request payloads to select a backend', () => {
    expect(
      reviewRequestSchema.safeParse({
        repository: 'fixture',
        base: 'a'.repeat(40),
        head: 'b'.repeat(40),
        backend: 'local',
      }).success,
    ).toBe(false);
  });
});
