#!/usr/bin/env python3
"""Bootstrap/sync the BA benchmark lab on a Synology NAS without git.

Python 3.8+ standard library only. GitHub reads use the existing configured
repository token. `--tools-only` is safe to call from the recurring wrapper and
keeps the lab executables current without touching benchmark evidence.
"""

import argparse
import base64
import json
import os
from pathlib import Path
import urllib.error
import urllib.parse
import urllib.request

DEFAULT_REPO = "justinthenick/LibreChat"
DEFAULT_BRANCH = "feature/ba-agent-v0.1"
DEFAULT_ROOT = "/volume1/docker/librechat-ba-lab"
DEFAULT_BENCHMARK = "003-access-request-decomposition"
DEFAULT_ENV_FILE = "/volume1/docker/librechat/deploy/synology/.env"
DEFAULT_TOKEN_ENV = "GITHUB_TELEMETRY_TOKEN"


class BootstrapError(RuntimeError):
    pass


def load_dotenv(path):
    values = {}
    if not path.exists():
        raise BootstrapError("Environment file not found: {}".format(path))
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        if key:
            values[key] = value
    return values


def github_fetch_text(repo, branch, repo_path, token):
    encoded_path = urllib.parse.quote(repo_path.strip("/"), safe="/")
    ref = urllib.parse.quote(branch, safe="")
    url = "https://api.github.com/repos/{}/contents/{}?ref={}".format(repo, encoded_path, ref)
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "ba-agent-nas-bootstrap/2.0",
        "X-GitHub-Api-Version": "2022-11-28",
        "Authorization": "Bearer {}".format(token),
    }
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise BootstrapError("GitHub HTTP {} for {}: {}".format(exc.code, repo_path, body[:500]))
    except urllib.error.URLError as exc:
        raise BootstrapError("GitHub network error for {}: {}".format(repo_path, exc.reason))

    if not isinstance(data, dict) or data.get("type") != "file" or data.get("encoding") != "base64":
        raise BootstrapError("Unexpected GitHub response for {}".format(repo_path))
    return base64.b64decode(data.get("content", "")).decode("utf-8")


def write_repo_file(root, repo_path, text):
    path = root / repo_path
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".sync-tmp")
    temp.write_text(text, encoding="utf-8")
    temp.replace(path)
    print("synced {}".format(path))
    return path


def main():
    parser = argparse.ArgumentParser(description="Bootstrap BA benchmark runner on Synology without git.")
    parser.add_argument("--repo", default=DEFAULT_REPO)
    parser.add_argument("--branch", default=DEFAULT_BRANCH)
    parser.add_argument("--root", default=DEFAULT_ROOT)
    parser.add_argument("--benchmark", default=DEFAULT_BENCHMARK)
    parser.add_argument("--env-file", default=DEFAULT_ENV_FILE)
    parser.add_argument("--github-token-env", default=DEFAULT_TOKEN_ENV)
    parser.add_argument("--tools-only", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    env_file = Path(args.env_file).resolve()
    env = load_dotenv(env_file)
    env.update(os.environ)
    token = env.get(args.github_token_env, "").strip()
    if not token:
        raise BootstrapError("{} is required for authenticated lab sync".format(args.github_token_env))

    tool_paths = (
        "custom/ba-agent/tools/benchmark_runner.py",
        "custom/ba-agent/tools/agent_pipeline_runner.py",
        "custom/ba-agent/tools/dynamic_agent_worker.py",
        "custom/ba-agent/tools/benchmark_worker.py",
        "custom/ba-agent/tools/autonomy_controller.py",
        "custom/ba-agent/tools/lab_common.py",
        "custom/ba-agent/tools/semantic_evaluator.py",
        "custom/ba-agent/tools/semantic_reviser.py",
        "custom/ba-agent/tools/diagnostic_worker.py",
        "custom/ba-agent/tools/bootstrap_nas.py",
        "custom/ba-agent/tools/run_worker_once.sh",
    )
    fetched = {}
    for tool_rel in tool_paths:
        fetched[tool_rel] = github_fetch_text(args.repo, args.branch, tool_rel, token)
    for tool_rel in tool_paths:
        if tool_rel != "custom/ba-agent/tools/bootstrap_nas.py":
            write_repo_file(root, tool_rel, fetched[tool_rel])
    write_repo_file(root, "custom/ba-agent/tools/bootstrap_nas.py", fetched["custom/ba-agent/tools/bootstrap_nas.py"])

    if args.tools_only:
        print("Authenticated tool sync complete.")
        return 0

    jobs_rel = "custom/ba-agent/automation/jobs.json"
    write_repo_file(root, jobs_rel, github_fetch_text(args.repo, args.branch, jobs_rel, token))

    benchmark_rel = "custom/ba-agent/benchmarks/{}".format(args.benchmark)
    config_rel = benchmark_rel + "/benchmark.json"
    config_text = github_fetch_text(args.repo, args.branch, config_rel, token)
    write_repo_file(root, config_rel, config_text)
    config = json.loads(config_text)

    input_name = str(config.get("input") or "input.md")
    prompt_name = str(config.get("prompt") or "prompt.md")
    for name in (input_name, prompt_name):
        rel = benchmark_rel + "/" + name
        write_repo_file(root, rel, github_fetch_text(args.repo, args.branch, rel, token))

    skill_config = config.get("skill")
    if skill_config:
        benchmark_dir = root / benchmark_rel
        skill_path = (benchmark_dir / str(skill_config)).resolve()
        try:
            skill_rel = skill_path.relative_to(root).as_posix()
        except ValueError:
            raise BootstrapError("Configured skill resolves outside lab root: {}".format(skill_path))
        write_repo_file(root, skill_rel, github_fetch_text(args.repo, args.branch, skill_rel, token))

    (root / benchmark_rel / "results").mkdir(parents=True, exist_ok=True)
    print("Bootstrap complete. Recurring wrapper will self-refresh tools before each poll.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BootstrapError as exc:
        print("ERROR: {}".format(exc))
        raise SystemExit(2)
