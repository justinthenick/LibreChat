from __future__ import annotations

import os
import selectors
import signal
import subprocess
import time


def run(argv: list[str], *, cwd=None, timeout: int = 60, limit: int = 65536) -> str:
    """Capture bounded output; terminate the process group on overflow or timeout."""
    environment = {
        "PATH": "/usr/local/bin:/usr/bin:/bin", "HOME": "/tmp/coding-agent-home",
        "LANG": "C.UTF-8", "GIT_TERMINAL_PROMPT": "0", "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_OPTIONAL_LOCKS": "0",
    }
    with subprocess.Popen(argv, cwd=cwd, env=environment, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, start_new_session=True) as process:
        chunks = bytearray()
        deadline = time.monotonic() + timeout
        try:
            with selectors.DefaultSelector() as selector:
                selector.register(process.stdout, selectors.EVENT_READ)
                while selector.get_map():
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        raise RuntimeError("maintenance command timed out")
                    for key, _ in selector.select(min(remaining, 0.2)):
                        chunk = os.read(key.fd, 8192)
                        if not chunk:
                            selector.unregister(key.fileobj)
                            continue
                        chunks.extend(chunk)
                        if len(chunks) > limit:
                            raise RuntimeError("maintenance output limit exceeded")
                process.wait(timeout=max(0.01, deadline - time.monotonic()))
            if process.returncode:
                raise RuntimeError("maintenance command failed; inspect operator diagnostics")
            return chunks.decode("utf-8", errors="replace")
        finally:
            # Also reap background descendants after their parent exits.
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()
