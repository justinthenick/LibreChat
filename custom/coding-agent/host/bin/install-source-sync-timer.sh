#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="${CODING_AGENT_LIBRECHAT_REPO:-$HOME/coding-agent/repos/LibreChat}"
UNIT_SOURCE="$REPO_ROOT/custom/coding-agent/host/systemd"
UNIT_DEST="$HOME/.config/systemd/user"

if ! command -v systemctl >/dev/null 2>&1; then
  echo "systemctl is required to install the source-sync timer" >&2
  exit 1
fi

if [ ! -f "$UNIT_SOURCE/coding-agent-source-sync.service" ] || \
   [ ! -f "$UNIT_SOURCE/coding-agent-source-sync.timer" ]; then
  echo "source-sync unit files not found under $UNIT_SOURCE" >&2
  exit 1
fi

mkdir -p "$UNIT_DEST"
install -m 0644 "$UNIT_SOURCE/coding-agent-source-sync.service" "$UNIT_DEST/"
install -m 0644 "$UNIT_SOURCE/coding-agent-source-sync.timer" "$UNIT_DEST/"

systemctl --user daemon-reload
systemctl --user enable --now coding-agent-source-sync.timer
systemctl --user start coding-agent-source-sync.service

echo
echo "=== SOURCE SYNC TIMER ==="
systemctl --user --no-pager status coding-agent-source-sync.timer || true
echo
echo "=== LAST SOURCE SYNC ==="
systemctl --user --no-pager status coding-agent-source-sync.service || true
