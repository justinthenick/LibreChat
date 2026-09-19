# Synology application image releases

The NAS checkout supplies configuration and managed skills. The application backend and compiled frontend come from the image pinned in `docker-compose.yml`. Updating the checkout alone does not update that application code.

## Build and validate

The **Synology Application Image** workflow builds the full `Dockerfile` Node image for the NAS's `linux/amd64` platform. It runs for application changes on `server/synology` and trusted `release/synology-*` branches, and supports manual dispatch. Release branches allow a candidate image to be tested before changing production.

The workflow verifies source identity, the compiled frontend and runtime modules, then boots the image against the production MongoDB version (4.4.18). Both production-agent seeders must succeed before startup. `/readyz`, `/api/config` and repeat seeding must pass. Only that tested image is pushed to `ghcr.io/justinthenick/librechat-synology:<full-source-commit>`.

This smoke uses disposable containers and a fixture administrator. It never connects to the production database or model providers. It verifies startup and persistence contracts; it does not replace the application unit/E2E suites or post-deployment UI checks.

## Promote

1. Require the source PR's applicable CI and the image workflow to pass.
2. Take the immutable `ghcr.io/justinthenick/librechat-synology@sha256:...` reference from the workflow summary.
3. Confirm the package is publicly readable from the NAS, or configure a pull-only registry credential through the normal private deployment process. Never commit credentials.
4. Change only the API image pin in `deploy/synology/docker-compose.yml` in a reviewed PR. Record source commit, tested digest and previous image in that PR.
5. Merge after validation. The existing NAS autodeploy pulls and recreates the API, then seeds and checks it.
6. Verify the runtime image digest and `BUILD_COMMIT`, deployment success marker, HTTP readiness, production and coding-pilot seeds, six managed skills with zero skips, and authenticated executor connectivity. Exercise the managed draft/trial UI with a disposable draft; do not publish it.

Publishing an image never automatically changes the production pin. A digest pin is immutable even if someone overwrites a tag. The image source commit may precede the configuration-only commit that pins it; record both identities.

## Rollback

Revert the API image-pin change through a PR and let the normal autodeploy recreate the API. The initial previous image was `librechat/lc-dev:cdd4c09076aa43ae9d94bba8f43c55ee35c181d5`. Do not reset the database or remove volumes. Check application/data compatibility before reverting after subsequent migrations or production use of newly introduced features.
