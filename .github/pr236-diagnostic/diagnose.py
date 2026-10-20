"""Construct a matched dependency pair; preserve failures without reruns."""
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys

source, control, evidence = (Path(p).resolve() for p in sys.argv[1:])
evidence.mkdir(parents=True, exist_ok=True)
project = source / 'custom/coding-agent/orchestrator'
results = []

def run(name, args, cwd=project, env=None, required=True, timeout=600):
    with (evidence / (name + '.log')).open('w') as out:
        p = subprocess.run([str(a) for a in args], cwd=cwd, env=env,
                           stdout=out, stderr=subprocess.STDOUT, timeout=timeout)
    results.append({'name': name, 'command': [str(a) for a in args], 'exit': p.returncode})
    (evidence / 'commands.json').write_text(json.dumps(results, indent=2))
    print(name, 'exit', p.returncode, flush=True)
    if required and p.returncode:
        print((evidence / (name + '.log')).read_text()[-5000:], flush=True)
        raise RuntimeError(name + ' failed; no matched-pair inference permitted')
    return p.returncode

def inventory(python, name):
    run(name, [python, '-m', 'pip', '--isolated', 'list', '--format=json'])
    return {p['name'].lower().replace('_', '-').replace('.', '-'): p['version']
            for p in json.loads((evidence / (name + '.log')).read_text())}

try:
    assert platform.python_version() == '3.12.15', platform.python_version()
    identity = {k: os.environ.get(k) for k in ['ImageOS', 'ImageVersion', 'RUNNER_OS',
                'RUNNER_ARCH', 'RUNNER_NAME', 'GITHUB_RUN_ID', 'GITHUB_RUN_ATTEMPT', 'GITHUB_SHA']}
    identity.update(python=sys.version, platform=platform.platform())
    (evidence / 'runner.json').write_text(json.dumps(identity, indent=2))
    run('source-head', ['git', 'rev-parse', 'HEAD'], cwd=source)
    assert (evidence / 'source-head.log').read_text().strip() == 'ce8ab335a77c8dbad67a1c90d76ffe8dc35ab8bb'
    # Build this reviewed, hook-free hatchling project once; reuse the same wheel.
    wheelhouse = evidence / 'local-wheel'
    wheelhouse.mkdir()
    run('build-local-wheel', [sys.executable, '-m', 'pip', '--isolated', 'wheel', '--no-deps',
        '--only-binary=:all:', '--index-url', 'https://pypi.org/simple', '--wheel-dir', wheelhouse, '.'])
    wheels = list(wheelhouse.glob('librechat_coding_orchestrator-*.whl'))
    assert len(wheels) == 1
    current = (control / 'current.txt').read_text()
    versions = ['1.106.1', '1.105.1']
    environments, inventories = {}, {}
    expected = dict(line.split('==') for line in current.splitlines() if line.strip())
    for version in versions:
        root = evidence / ('venv-' + version)
        run('venv-' + version, [sys.executable, '-m', 'venv', root])
        python = root / 'bin/python'
        requirements = evidence / ('requirements-' + version + '.txt')
        requirements.write_text(current.replace('litellm==1.106.1', 'litellm==' + version))
        run('install-' + version, [python, '-m', 'pip', '--isolated', 'install',
            '--only-binary=:all:', '--index-url', 'https://pypi.org/simple',
            '--report', evidence / ('install-' + version + '.json'),
            '-r', requirements, wheels[0]])
        run('pip-check-' + version, [python, '-m', 'pip', '--isolated', 'check'])
        inventories[version] = inventory(python, 'inventory-' + version)
        for name, value in expected.items():
            assert inventories[version].get(name) == (version if name == 'litellm' else value), name
        assert set(inventories[version]) == set(expected) | {'pip', 'librechat-coding-orchestrator'}
        environments[version] = python
    old, new = inventories['1.105.1'], inventories['1.106.1']
    differences = {k: [old.get(k), new.get(k)] for k in set(old) | set(new) if old.get(k) != new.get(k)}
    assert differences == {'litellm': ['1.105.1', '1.106.1']}, differences
    (evidence / 'matched-pair.json').write_text(json.dumps({'inventories': inventories, 'differences': differences}, indent=2))
    print('MATCHED_PAIR ' + json.dumps({'inventories': inventories, 'differences': differences}), flush=True)
    for version in versions:
        # These subprocesses invoke the original suite guards with cleared environments.
        env = {'PATH': str(environments[version].parent) + ':/usr/bin:/bin',
               'PYTHONPATH': str(project / 'src'), 'PYTHON_DOTENV_DISABLED': '1'}
        run('probe-' + version, [environments[version], '-B', control / 'probe.py'], env=env, required=False)
        print((evidence / ('probe-' + version + '.log')).read_text(), flush=True)
        run('full-suite-' + version, [environments[version], '-B', 'tests/run_tests.py'], env=env, required=False)
        print('FULL_SUITE ' + version + '\n' + (evidence / ('full-suite-' + version + '.log')).read_text()[-3500:], flush=True)
    run('source-unchanged', ['git', 'diff', '--exit-code'], cwd=source)
finally:
    # Exclude installed environments and wheel payload; include logs, reports and inventories.
    files = sorted(p for p in evidence.iterdir() if p.is_file() and p.name != 'manifest.json')
    manifest = [{'file': p.name, 'bytes': p.stat().st_size,
                 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in files]
    (evidence / 'manifest.json').write_text(json.dumps(manifest, indent=2))
