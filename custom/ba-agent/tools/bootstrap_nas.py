#!/usr/bin/env python3
"""Bootstrap/sync the BA benchmark lab on a Synology NAS without git.

Python 3.8+ standard library only.
"""

import argparse
import base64
import json
from pathlib import Path
import urllib.error
import urllib.parse
import urllib.request

DEFAULT_REPO = "justinthenick/LibreChat"
DEFAULT_BRANCH = "feature/ba-agent-v0.1"
DEFAULT_ROOT = "/volume1/docker/librechat-ba-lab"
DEFAULT_BENCHMARK = "003-access-request-decomposition"


class BootstrapError(RuntimeError):
    pass


def github_fetch_text(repo, branch, repo_path):
    encoded_path = urllib.parse.quote(repo_path.strip("/"), safe="/")
    ref = urllib.parse.quote(branch, safe="")
    url = "https://api.github.com/repos/{}/contents/{}?ref={}".format(repo, encoded_path, ref)
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "ba-agent-nas-bootstrap/1.0",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
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
    path.write_text(text, encoding="utf-8")
    print("synced {}".format(path))
    return path


def main():
    parser = argparse.ArgumentParser(description="Bootstrap BA benchmark runner on Synology without git.")
    parser.add_argument("--repo", default=DEFAULT_REPO)
    parser.add_argument("--branch", default=DEFAULT_BRANCH)
    parser.add_argument("--root", default=DEFAULT_ROOT)
    parser.add_argument("--benchmark", default=DEFAULT_BENCHMARK)
    args = parser.parse_args()

    root = Path(args.root).resolve()
    benchmark_rel = "custom/ba-agent/benchmarks/{}".format(args.benchmark)

    for tool_rel in (
        "custom/ba-agent/tools/benchmark_runner.py",
        "custom/ba-agent/tools/benchmark_worker.py",
        "custom/ba-agent/tools/run_worker_once.sh",
    ):
        write_repo_file(root, tool_rel, github_fetch_text(args.repo, args.branch, tool_rel))

    jobs_rel = "custom/ba-agent/automation/jobs.json"
    write_repo_file(root, jobs_rel, github_fetch_text(args.repo, args.branch, jobs_rel))

    config_rel = benchmark_rel + "/benchmark.json"
    config_text = github_fetch_text(args.repo, args.branch, config_rel)
    write_repo_file(root, config_rel, config_text)
    config = json.loads(config_text)

    input_name = str(config.get("input") or "input.md")
    prompt_name = str(config.get("prompt") or "prompt.md")
    for name in (input_name, prompt_name):
        rel = benchmark_rel + "/" + name
        write_repo_file(root, rel, github_fetch_text(args.repo, args.branch, rel))

    skill_config = config.get("skill")
    if skill_config:
        benchmark_dir = root / benchmark_rel
        skill_path = (benchmark_dir / str(skill_config)).resolve()
        try:
            skill_rel = skill_path.relative_to(root).as_posix()
        except ValueError:
            raise BootstrapError("Configured skill resolves outside lab root: {}".format(skill_path))
        write_repo_file(root, skill_rel, github_fetch_text(args.repo, args.branch, skill_rel))

    results = root / benchmark_rel / "results"
    results.mkdir(parents=True, exist_ok=True)

    print("")
    print("Bootstrap complete.")
    print("Root: {}".format(root))
    print("Python 3.8+ supported.")
    print("")
    print("Recommended worker invocation (one poll, safe for DSM Task Scheduler):")
    print("sh {}".format(root / "custom/ba-agent/tools/run_worker_once.sh"))
    print("")
    print("For unattended operation, schedule that command every 5 minutes in DSM Task Scheduler.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BootstrapError as exc:
        print("ERROR: {}".format(exc))
        raise SystemExit(2)
