# BA Benchmark Runner

`benchmark_runner.py` runs BA benchmark cases directly against the Gemini API so benchmark iterations do not require manual copy/paste through LibreChat.

It is intentionally **not** an evaluator. It sends only the benchmark prompt/input and, for a skill run, the selected `SKILL.md`. Evaluator-only `gold-standard.md` and `scoring-rubric.md` are never loaded by the runner.

## Synology compatibility

The runner is standard-library-only and supports **Python 3.8+**. It does **not** require the `git` executable.

For NAS hosts without git, use `bootstrap_nas.py` once to create the local lab tree under `/volume1/docker/librechat-ba-lab`. The runner can then refresh the current benchmark input/prompt/skill from GitHub before every run using `--refresh-from-github`.

This keeps the live LibreChat deployment checkout untouched.

## API keys

Gemini key lookup order:

1. `GEMINI_API_KEY`
2. `GOOGLE_KEY`
3. `GOOGLE_API_KEY`

Use the existing private LibreChat `.env` without printing the key:

```bash
--env-file /volume1/docker/librechat/.env
```

For publishing benchmark outputs back to GitHub without git, the default token variable is:

```text
GITHUB_BA_BENCHMARK_TOKEN
```

Use a fine-grained token scoped to `justinthenick/LibreChat` with **Contents: Read and write**. A different existing token variable may be selected explicitly with `--github-token-env NAME` if it has sufficient permission.

Tokens are never written to benchmark result files.

## Benchmark 003 example

After bootstrap:

```bash
python3 /volume1/docker/librechat-ba-lab/custom/ba-agent/tools/benchmark_runner.py \
  /volume1/docker/librechat-ba-lab/custom/ba-agent/benchmarks/003-access-request-decomposition \
  --model gemini-3.5-flash \
  --mode skill \
  --env-file /volume1/docker/librechat/.env \
  --refresh-from-github \
  --publish-github
```

If reusing another token variable with appropriate Contents write permission:

```bash
--github-token-env GITHUB_TELEMETRY_TOKEN
```

## Results

Each provider call creates:

- a `.md` file containing run metadata and raw model response;
- a `.json` metadata sidecar;
- one invocation manifest JSON.

Results are written under the benchmark's `results/` directory. With `--publish-github`, the generated files are uploaded directly to the configured GitHub branch using the GitHub Contents API.

Metadata includes model, generation settings, input/prompt/skill SHA-256 hashes, skill version, timestamps, usage metadata when returned, provider status, Python version and GitHub source branch. No API key/token value is recorded.

## Quota behavior

The runner deliberately does **not** switch models or silently retry.

- HTTP `429` -> `quota_blocked`, then remaining calls stop.
- HTTP `503` -> `provider_busy`.
- Other provider/network failures are recorded as failures rather than substituted with another model.

## Experimental caveat

The runner injects the body of `SKILL.md` as Gemini's system instruction after stripping YAML frontmatter. This is a controlled approximation of LibreChat Skill execution, not the exact LibreChat Skills plumbing.

For model/skill comparisons within the runner, keep runner version, model ID, temperature, prompt and input unchanged. Periodic manual validation through LibreChat can be used to confirm the runner remains representative.

## Generation defaults

- temperature: `0.0`
- max output tokens: `8192`
- timeout: `180` seconds
- no retries
- no model fallback
