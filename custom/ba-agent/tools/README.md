# BA Benchmark Runner

`benchmark_runner.py` runs the BA benchmark cases directly against the Gemini API so benchmark iterations do not require manual copy/paste through LibreChat.

It is intentionally **not** an evaluator. It sends only the benchmark prompt/input (and, for a skill run, the selected `SKILL.md`) to Gemini, then saves the raw model output and reproducibility metadata. The evaluator-only `gold-standard.md` and `scoring-rubric.md` are never loaded by the runner.

## Why run outside the live LibreChat checkout

Use a separate clone/worktree for the BA lab. Do not switch the production Synology deployment checkout away from `server/synology` merely to run benchmarks.

Example one-time lab clone:

```bash
cd /volume1/docker
git clone --branch feature/ba-agent-v0.1 \
  https://github.com/justinthenick/LibreChat.git \
  librechat-ba-lab
cd /volume1/docker/librechat-ba-lab
```

If the lab clone already exists:

```bash
cd /volume1/docker/librechat-ba-lab
git pull --ff-only
```

## API key

The runner accepts any of these environment variables, in this order:

1. `GEMINI_API_KEY`
2. `GOOGLE_KEY`
3. `GOOGLE_API_KEY`

You can point the runner at the existing private LibreChat `.env` without printing or copying the key:

```bash
--env-file /volume1/docker/librechat/.env
```

The key value is never written to result files or displayed. The Google API key is sent using the `x-goog-api-key` request header rather than being placed in the request URL.

## Benchmark 003

`benchmark.json` makes the common invocation compact:

```bash
python3 custom/ba-agent/tools/benchmark_runner.py \
  custom/ba-agent/benchmarks/003-access-request-decomposition \
  --model gemini-3.5-flash \
  --mode both \
  --env-file /volume1/docker/librechat/.env
```

For later skill iterations, the no-skill baseline usually does not need to be rerun. Run only the current skill:

```bash
python3 custom/ba-agent/tools/benchmark_runner.py \
  custom/ba-agent/benchmarks/003-access-request-decomposition \
  --model gemini-3.5-flash \
  --mode skill \
  --env-file /volume1/docker/librechat/.env
```

For repeatability testing (consumes additional quota):

```bash
python3 custom/ba-agent/tools/benchmark_runner.py \
  custom/ba-agent/benchmarks/003-access-request-decomposition \
  --model gemini-3.5-flash \
  --mode skill \
  --repeat 2 \
  --env-file /volume1/docker/librechat/.env
```

## Results

Each model call creates:

- a `.md` file containing run metadata plus the raw model response;
- a `.json` metadata sidecar;
- one manifest JSON for the complete runner invocation.

Files are written under the benchmark's `results/` directory.

Metadata includes the exact model, generation settings, input/prompt/skill SHA-256 hashes, skill version, timestamps, usage metadata when returned, and provider status. It never contains the API key.

## Quota behavior

The runner deliberately does **not** switch models or retry silently.

If Gemini returns HTTP `429`, the run is saved as `quota_blocked` and remaining calls in that invocation stop. This prevents an A/B experiment from silently becoming a mixed-model experiment.

HTTP `503` is saved as `provider_busy`; other provider/network failures are also recorded rather than disguised as model output.

## Git publishing

By default results remain only in the lab checkout.

If that clone already has authenticated GitHub push access, the runner can commit and push its result files automatically:

```bash
python3 custom/ba-agent/tools/benchmark_runner.py \
  custom/ba-agent/benchmarks/003-access-request-decomposition \
  --model gemini-3.5-flash \
  --mode skill \
  --env-file /volume1/docker/librechat/.env \
  --git-commit \
  --git-push
```

This is the mode that enables a largely hands-off cycle: the NAS produces and publishes a raw benchmark result; the result can then be inspected/scored from GitHub and the skill can be revised without manual response copying.

If push authentication is not configured, omit `--git-commit --git-push`; the benchmark still runs and retains the result locally.

## Experimental caveat

The runner injects the body of `SKILL.md` as Gemini's system instruction (YAML frontmatter is stripped). That is a controlled approximation of skill execution rather than the exact LibreChat Skills plumbing.

For model/skill comparisons **within the runner**, keep the runner version, model ID, temperature, prompt and input unchanged. Periodic validation through LibreChat can still be used to check that runner behavior remains representative.

## Generation defaults

- temperature: `0.0`
- max output tokens: `8192`
- timeout: `180` seconds
- no retries
- no model fallback

Override these with CLI flags only when deliberately starting a new comparison series.
