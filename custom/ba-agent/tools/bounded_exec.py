#!/usr/bin/env python3
"""Run one command with a hard wall-clock timeout and append output to a log.

Python 3.8+ standard library only. Intended for the Synology BA lab wrapper so a
wedged provider call or worker cannot hold the scheduler lock indefinitely.
"""

import argparse
import datetime as dt
import os
import signal
import subprocess
import sys


def stamp():
    return dt.datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S")


def main():
    p = argparse.ArgumentParser(description="Run a command with a hard timeout.")
    p.add_argument("--timeout", type=int, required=True)
    p.add_argument("--log", required=True)
    p.add_argument("command", nargs=argparse.REMAINDER)
    args = p.parse_args()

    command = list(args.command)
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        print("ERROR: no command supplied", file=sys.stderr)
        return 2
    if args.timeout < 1:
        print("ERROR: timeout must be positive", file=sys.stderr)
        return 2

    with open(args.log, "a", encoding="utf-8", errors="replace") as log:
        log.write("{} bounded start timeout={}s command={}\n".format(stamp(), args.timeout, command[0]))
        log.flush()
        proc = subprocess.Popen(
            command,
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        try:
            rc = proc.wait(timeout=args.timeout)
        except subprocess.TimeoutExpired:
            log.write("{} TIMEOUT after {}s command={} pid={}\n".format(stamp(), args.timeout, command[0], proc.pid))
            log.flush()
            try:
                os.killpg(proc.pid, signal.SIGTERM)
            except Exception:
                try:
                    proc.terminate()
                except Exception:
                    pass
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except Exception:
                    try:
                        proc.kill()
                    except Exception:
                        pass
                proc.wait()
            return 124
        log.write("{} bounded end rc={} command={}\n".format(stamp(), rc, command[0]))
        log.flush()
        return rc


if __name__ == "__main__":
    raise SystemExit(main())
