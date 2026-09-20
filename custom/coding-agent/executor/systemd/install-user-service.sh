#!/usr/bin/env bash
set -euo pipefail

UNIT_NAME=librechat-coding-selfdev-worker.service
SOURCE="$HOME/coding-agent/dev/repos/LibreChat/custom/coding-agent/executor/systemd/$UNIT_NAME"
TARGET_DIR="$HOME/.config/systemd/user"
TARGET="$TARGET_DIR/$UNIT_NAME"
SOCKET="$HOME/coding-agent/dev/selfdev/worker.sock"

if ! command -v systemctl >/dev/null 2>&1; then
  echo "ERROR: systemctl is not available in this WSL distribution." >&2
  exit 1
fi

if ! systemctl --user show-environment >/dev/null 2>&1; then
  echo "ERROR: the systemd user manager is not available." >&2
  echo "Enable systemd for WSL before installing this service." >&2
  exit 1
fi

if [ ! -f "$SOURCE" ]; then
  echo "ERROR: service definition not found at $SOURCE" >&2
  exit 1
fi

mkdir -p   "$TARGET_DIR"   "$HOME/coding-agent/dev/selfdev"   "$HOME/coding-agent/dev/candidate"   "$HOME/coding-agent/dev/tasks"

chmod 700   "$HOME/coding-agent/dev/selfdev"   "$HOME/coding-agent/dev/candidate"

cp "$SOURCE" "$TARGET"
chmod 600 "$TARGET"

systemctl --user daemon-reload
systemctl --user enable --now "$UNIT_NAME"

for _ in 1 2 3 4 5 6 7 8 9 10; do
  [ -S "$SOCKET" ] && break
  sleep 1
done

if [ ! -S "$SOCKET" ]; then
  echo "ERROR: worker service started but the Unix socket did not appear." >&2
  systemctl --user --no-pager --full status "$UNIT_NAME" || true
  exit 1
fi

echo "Self-development worker service installed."
echo "socket=$SOCKET"
systemctl --user --no-pager --full status "$UNIT_NAME"
