import { getDevelopmentReviewConfig } from './development';

const env = {
  NODE_ENV: 'development',
  CODING_REVIEW_DEVELOPMENT: 'true',
  CODING_REVIEW_URL: 'http://127.0.0.1:9876/review',
  CODING_REVIEW_TOKEN: 'offline-development-fixture-token-only',
  CODING_REVIEW_MODEL: 'gpt-5.6-sol',
  CODING_REVIEW_REPOSITORIES: JSON.stringify([{ id: 'fixture', tenantId: 'tenant-a' }]),
};

it('accepts only explicit development configuration and preserves tenant-scoped IDs', () => {
  expect(getDevelopmentReviewConfig(env)).toMatchObject({
    enabled: true,
    repositories: [{ id: 'fixture', tenantId: 'tenant-a' }],
    client: { enabled: true, model: 'gpt-5.6-sol' },
  });
});
it.each([
  {},
  { NODE_ENV: 'production' },
  { NODE_ENV: 'test' },
  { CODING_REVIEW_DEVELOPMENT: 'false' },
  { CODING_REVIEW_DEVELOPMENT: '1' },
  { CODING_REVIEW_URL: 'http://example.invalid/review' },
  { CODING_REVIEW_URL: 'http://127.0.0.1:9876/review?token=secret' },
  { CODING_REVIEW_TOKEN: 'short' },
  { CODING_REVIEW_MODEL: '' },
  { CODING_REVIEW_REPOSITORIES: 'not json' },
  { CODING_REVIEW_REPOSITORIES: '[]' },
  { CODING_REVIEW_REPOSITORIES: JSON.stringify([{ id: '/tmp/repo' }]) },
  { CODING_REVIEW_REPOSITORIES: JSON.stringify([{ id: 'fixture', tenantId: '' }]) },
  { CODING_REVIEW_REPOSITORIES: JSON.stringify([{ id: 'fixture', path: '/tmp/repo' }]) },
  { CODING_REVIEW_REPOSITORIES: JSON.stringify([{ id: 'fixture' }, { id: 'fixture' }]) },
  { CODING_REVIEW_REPOSITORIES: ' '.repeat(16385) },
])('fails closed for missing, non-development or malformed settings: %j', (override) => {
  const input = Object.keys(override).length ? { ...env, ...override } : {};
  expect(getDevelopmentReviewConfig(input)).toEqual({
    enabled: false,
    repositories: [],
    client: { enabled: false, url: '', token: '', model: '' },
  });
});
