# BA Agent Lab branch and NAS cache model

This lab deliberately uses different GitHub branches for different responsibilities.

## Branch roles

- `feature/ba-agent-v0.1` — active benchmark workbench and NAS benchmark control/results branch. The DSM worker reads `jobs.json`, benchmark inputs and candidate Skill versions from this branch and publishes raw benchmark results back to it.
- `main` — released repository snapshot. Accepted/frozen Skill versions are integrated here only after benchmark review and release decisions.
- `server/synology` — NAS deployment branch. It contains `main` plus Synology-specific deployment changes and is the branch watched by `deploy/synology/autodeploy.sh`.
- `nas-status` — sanitised deployment telemetry only. It is not a source branch for the benchmark lab or LibreChat deployment.

Do not repoint the benchmark worker to `server/synology`: benchmark result publication would then create deployment commits. Do not treat `main` as the live benchmark queue unless the runner is first changed to separate source and results branches.

## NAS lab cache semantics

The benchmark lab under `/volume1/docker/librechat-ba-lab` is a working cache, not the release source of truth.

Before every benchmark execution the runner refreshes that benchmark's config, input, prompt and configured Skill from `feature/ba-agent-v0.1`. This means a stale local Skill file cannot contaminate a later queued run: the run refreshes its inputs before calling the provider.

A candidate run can nevertheless leave its candidate Skill version in the local cache after the run. If that candidate is later reverted in GitHub and no further job for that Skill runs, the local file can remain newer than the released version even though `main` is correct. That state is operationally harmless to LibreChat because LibreChat does not load Skills from `/volume1/docker/librechat-ba-lab`, but it can be misleading during manual inspection.

When release-state verification matters, use the constrained diagnostic worker to inspect the local Skill version. If a cache reset is required without changing Skill evidence, queue a clearly labelled maintenance baseline job against a benchmark that references the released Skill; refresh occurs before the baseline call and therefore restores the released file without producing a new Skill score.

## Release flow

1. Develop and benchmark on `feature/ba-agent-v0.1`.
2. Freeze or accept a tested Skill version based on evidence.
3. Merge the accepted snapshot into `main`.
4. Reconcile `main` into `server/synology`, preserving Synology-specific deployment commits.
5. Let the NAS autodeployer update `server/synology` and report health through commit status and `nas-status` telemetry.
6. Treat `/volume1/docker/librechat-ba-lab` as an execution cache; verify/reset it separately only when needed.

This separation keeps benchmark iteration, released Skill state, and NAS application deployment from triggering or overwriting one another accidentally.
