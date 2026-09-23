from __future__ import annotations

import fcntl
import os
import stat
from contextlib import contextmanager
from functools import wraps
from pathlib import Path


@contextmanager
def maintenance_lock(task_root: Path, *, exclusive: bool = False, lock_path: Path | None = None):
    """Nonblocking cross-process gate shared by MCP calls and maintenance."""
    configured = lock_path or os.environ.get("CODING_MAINTENANCE_LOCK")
    if configured:
        descriptor = os.open(configured, os.O_RDONLY | os.O_NOFOLLOW)
    else:
        descriptor = os.open(task_root / ".maintenance.lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise RuntimeError("invalid maintenance lock")
        mode = fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH
        try:
            fcntl.flock(descriptor, mode | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise RuntimeError("executor_busy: retry after the current operation finishes") from error
        yield
    finally:
        os.close(descriptor)


def coordinated(task_root: Path):
    def decorate(function):
        @wraps(function)
        def invoke(*args, **kwargs):
            with maintenance_lock(task_root):
                return function(*args, **kwargs)
        return invoke
    return decorate
