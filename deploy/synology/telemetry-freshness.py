#!/usr/bin/env python3
"""Exit 0 when the last successful NAS telemetry publication is due."""

import os
import sys
import time

MIN_INTERVAL_SECONDS = 60 * 60
MAX_FUTURE_SKEW_SECONDS = 5 * 60


def publication_due(marker_path, now=None):
    if now is None:
        now = time.time()
    try:
        last_publish = os.stat(marker_path).st_mtime
    except OSError:
        # No usable marker: attempt publication, retaining the old behavior.
        return True
    age = now - last_publish
    return age >= MIN_INTERVAL_SECONDS or age < -MAX_FUTURE_SKEW_SECONDS


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: telemetry-freshness.py MARKER")
    sys.exit(0 if publication_due(sys.argv[1]) else 1)
