#!/usr/bin/env bash
set -Eeuo pipefail

# Build and activate an immutable host-maintenance release.
#
# The host Python on supported Ubuntu/WSL installs may intentionally have no
# pip/ensurepip. Release packages are therefore installed into a pip-less venv
# by a disposable Python 3.12 container. The running service imports only from
# the release venv; PYTHONPATH is explicitly cleared by the systemd unit.

REPO_ROOT="$(git rev-parse --show-toplevel)"
ROOT="${CODING_MAINTENANCE_ROOT:-$HOME/.local/share/coding-maintenance}"
COMPOSE="${CODING_MAINTENANCE_COMPOSE:-$ROOT/compose.json}"
ENV_FILE="${CODING_MAINTENANCE_ENV_FILE:-$HOME/.config/coding-maintenance.env}"
UNIT="${CODING_MAINTENANCE_UNIT:-$HOME/.config/systemd/user/coding-agent-host-maintenance.service}"
INSTALLER_IMAGE="${CODING_MAINTENANCE_INSTALLER_IMAGE:-python:3.12-slim-bookworm}"
EXPECTED_BRANCH="${CODING_MAINTENANCE_SOURCE_BRANCH:-server/synology}"

cd "$REPO_ROOT"

SHA="$(git rev-parse HEAD)"
BRANCH="$(git branch --show-current)"
SHORT_SHA="${SHA:0:12}"
RELEASE="$ROOT/releases/$SHA"
CURRENT="$ROOT/current"
BACKUP="$ROOT/backups/$(date +%Y%m%dT%H%M%S)-release-deploy"
EXECUTOR_DIR="$REPO_ROOT/custom/coding-agent/executor"
HOST_DIR="$REPO_ROOT/custom/coding-agent/host"
UNIT_TEMPLATE="$HOST_DIR/systemd/coding-agent-host-maintenance.service"
RUNTIME_DROPIN="$UNIT.d/runtime.conf"

read_version() {
  python3 - "$1" <<'PY'
import sys
import tomllib

with open(sys.argv[1], "rb") as handle:
    print(tomllib.load(handle)["project"]["version"])
PY
}

read_env_value() {
  python3 - "$ENV_FILE" "$1" <<'PY'
import sys
from pathlib import Path

path = Path(sys.argv[1])
wanted = sys.argv[2]
for raw in path.read_text().splitlines():
    if raw.startswith(wanted + "="):
        value = raw.split("=", 1)[1].strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
            value = value[1:-1]
        print(value)
        break
else:
    raise SystemExit(f"{wanted} not found in {path}")
PY
}

EXECUTOR_VERSION="$(read_version "$EXECUTOR_DIR/pyproject.toml")"
HOST_VERSION="$(read_version "$HOST_DIR/pyproject.toml")"
TAG="librechat-coding-executor:${EXECUTOR_VERSION}-${SHORT_SHA}"

PROJECT=""
CONFIG=""
OLD_CURRENT=""
ARMED=0

restore_file() {
  local saved="$1"
  local destination="$2"
  if [ -f "$saved" ]; then
    mkdir -p "$(dirname "$destination")"
    cp -a "$saved" "$destination"
  else
    rm -f "$destination"
  fi
}

rollback() {
  trap - ERR
  set +e
  if [ "$ARMED" -eq 1 ]; then
    echo
    echo "=== ROLLBACK ==="
    restore_file "$BACKUP/compose.json" "$COMPOSE"
    restore_file "$BACKUP/policy.json" "$CONFIG"
    restore_file "$BACKUP/unit.service" "$UNIT"
    restore_file "$BACKUP/runtime.conf" "$RUNTIME_DROPIN"

    rm -f "$CURRENT.new"
    if [ -n "$OLD_CURRENT" ]; then
      ln -s "$OLD_CURRENT" "$CURRENT.new"
      mv -Tf "$CURRENT.new" "$CURRENT"
    else
      rm -f "$CURRENT"
    fi

    systemctl --user daemon-reload
    if [ -n "$PROJECT" ]; then
      docker compose -p "$PROJECT" -f "$COMPOSE" up -d --force-recreate coding-executor
    fi
    systemctl --user restart coding-agent-host-maintenance
    echo "Rollback attempted; failed release and image were retained for inspection."
  fi
}
trap rollback ERR

echo "=== PREFLIGHT ==="
test "$BRANCH" = "$EXPECTED_BRANCH"
test -z "$(git status --porcelain)"
test -f "$COMPOSE"
test -f "$ENV_FILE"
test -f "$UNIT_TEMPLATE"
test ! -e "$RELEASE"
if [ -e "$CURRENT" ] && [ ! -L "$CURRENT" ]; then
  echo "STOP: $CURRENT exists but is not a symlink"
  exit 1
fi

CONFIG="$(read_env_value CODING_MAINTENANCE_CONFIG)"
test -f "$CONFIG"

CURRENT_CONTAINER="$(docker inspect librechat-coding-executor --format '{{.Id}}')"
PROJECT="$(docker inspect librechat-coding-executor --format '{{index .Config.Labels "com.docker.compose.project"}}')"
test -n "$CURRENT_CONTAINER"
test -n "$PROJECT"

if [ -L "$CURRENT" ]; then
  OLD_CURRENT="$(readlink -f "$CURRENT")"
fi

echo "source_sha=$SHA"
echo "executor_version=$EXECUTOR_VERSION"
echo "host_version=$HOST_VERSION"
echo "compose_project=$PROJECT"
echo "installer_image=$INSTALLER_IMAGE"

echo
echo "=== PREPARE BACKUP ==="
mkdir -p "$BACKUP"
chmod 700 "$BACKUP"
cp -a "$COMPOSE" "$BACKUP/compose.json"
cp -a "$CONFIG" "$BACKUP/policy.json"
[ ! -f "$UNIT" ] || cp -a "$UNIT" "$BACKUP/unit.service"
[ ! -f "$RUNTIME_DROPIN" ] || cp -a "$RUNTIME_DROPIN" "$BACKUP/runtime.conf"
printf '%s\n' "$OLD_CURRENT" > "$BACKUP/old-current.txt"

echo
echo "=== CREATE IMMUTABLE RELEASE ==="
mkdir -p "$RELEASE/custom/coding-agent"
cp -a "$EXECUTOR_DIR" "$RELEASE/custom/coding-agent/"
cp -a "$HOST_DIR" "$RELEASE/custom/coding-agent/"
python3 -m venv --without-pip "$RELEASE/venv"

PY="$RELEASE/venv/bin/python"
SITE="$("$PY" - <<'PY'
import site

paths = site.getsitepackages()
if len(paths) != 1:
    raise SystemExit(f"expected one site-packages path, got {paths!r}")
print(paths[0])
PY
)"
test -d "$SITE"

echo
echo "=== INSTALL RELEASE PACKAGES ==="
docker image inspect "$INSTALLER_IMAGE" >/dev/null 2>&1 || docker pull "$INSTALLER_IMAGE"
INSTALLER_IMAGE_ID="$(docker image inspect "$INSTALLER_IMAGE" --format '{{.Id}}')"
echo "installer_image_id=$INSTALLER_IMAGE_ID"

docker run --rm   --user "$(id -u):$(id -g)"   --env HOME=/tmp   --volume "$RELEASE/custom/coding-agent:/src:ro"   --volume "$SITE:/target:rw"   "$INSTALLER_IMAGE"   python -m pip install     --disable-pip-version-check     --no-cache-dir     --target /target     /src/executor /src/host

echo
echo "=== VERIFY RELEASE IMPORTS ==="
"$PY" - "$EXECUTOR_VERSION" "$HOST_VERSION" "$RELEASE" <<'PY'
import importlib.metadata as md
import pathlib
import sys

expected_executor, expected_host, release = sys.argv[1:]
import coding_executor
import host_maintenance
import host_maintenance.server
import source_preflight

print("executor_runtime =", coding_executor.__version__)
print("executor_package =", md.version("librechat-coding-executor"))
print("host_package =", md.version("librechat-coding-agent-host"))
print("executor_source =", coding_executor.__file__)
print("host_source =", host_maintenance.__file__)

assert coding_executor.__version__ == expected_executor
assert md.version("librechat-coding-executor") == expected_executor
assert md.version("librechat-coding-agent-host") == expected_host
root = pathlib.Path(release).resolve()
for module in (coding_executor, host_maintenance, source_preflight):
    pathlib.Path(module.__file__).resolve().relative_to(root)
PY

echo
echo "=== RUN RELEASE TESTS ==="
PYTHONDONTWRITEBYTECODE=1 "$PY" -B -m unittest discover   -s "$RELEASE/custom/coding-agent/executor/tests" -v
PYTHONDONTWRITEBYTECODE=1 "$PY" -B -m unittest discover   -s "$RELEASE/custom/coding-agent/host/tests" -v

echo
echo "=== BUILD EXECUTOR IMAGE ==="
docker build -t "$TAG" "$RELEASE/custom/coding-agent/executor"
NEW_IMAGE="$(docker image inspect "$TAG" --format '{{.Id}}')"
test -n "$NEW_IMAGE"
echo "new_image=$NEW_IMAGE"

echo
echo "=== PREPARE SWITCH ==="
ARMED=1
systemctl --user stop coding-agent-host-maintenance

python3 - "$COMPOSE" "$CONFIG" "$NEW_IMAGE" <<'PY'
import json
import re
import sys
from pathlib import Path

compose_path = Path(sys.argv[1])
policy_path = Path(sys.argv[2])
image = sys.argv[3]
if not re.fullmatch(r"sha256:[0-9a-f]{64}", image):
    raise SystemExit(f"invalid executor image ID: {image}")

def rewrite(path: Path, update):
    data = json.loads(path.read_text())
    update(data)
    tmp = path.with_suffix(path.suffix + ".new")
    tmp.write_text(json.dumps(data, indent=2) + "\n")
    tmp.chmod(path.stat().st_mode)
    tmp.replace(path)

def update_compose(data):
    service = data.get("services", {}).get("coding-executor")
    if not isinstance(service, dict):
        raise SystemExit("coding-executor service missing from compose")
    service["image"] = image

def update_policy(data):
    old = data.get("image_id")
    if old is not None and not re.fullmatch(r"sha256:[0-9a-f]{64}", str(old)):
        raise SystemExit(f"unexpected existing policy image_id: {old!r}")
    data["image_id"] = image

rewrite(compose_path, update_compose)
rewrite(policy_path, update_policy)
PY

mkdir -p "$(dirname "$UNIT")"
cp -a "$UNIT_TEMPLATE" "$UNIT"
rm -f "$RUNTIME_DROPIN"
rmdir "$UNIT.d" 2>/dev/null || true

rm -f "$CURRENT.new"
ln -s "$RELEASE" "$CURRENT.new"
mv -Tf "$CURRENT.new" "$CURRENT"

systemctl --user daemon-reload

echo
echo "=== SWITCH EXECUTOR ==="
docker compose -p "$PROJECT" -f "$COMPOSE" up -d --force-recreate coding-executor

echo
echo "=== WAIT FOR EXECUTOR ==="
OK=0
for _ in $(seq 1 30); do
  if HEALTH="$(curl -fsS http://127.0.0.1:8765/health 2>/dev/null)"; then
    echo "$HEALTH"
    if printf '%s' "$HEALTH" | grep -F "\"version\":\"${EXECUTOR_VERSION}\"" >/dev/null; then
      OK=1
      break
    fi
  fi
  sleep 2
done
test "$OK" -eq 1

echo
echo "=== START HOST MAINTENANCE ==="
systemctl --user reset-failed coding-agent-host-maintenance || true
systemctl --user start coding-agent-host-maintenance

for _ in $(seq 1 20); do
  systemctl --user is-active --quiet coding-agent-host-maintenance && break
  sleep 1
done
systemctl --user is-active --quiet coding-agent-host-maintenance

BIND="$(read_env_value CODING_MAINTENANCE_BIND)"
PORT="$(read_env_value CODING_MAINTENANCE_PORT)"
"$PY" - "$BIND" "$PORT" <<'PY'
import socket
import sys
import time

host, port = sys.argv[1], int(sys.argv[2])
target = "127.0.0.1" if host in ("0.0.0.0", "::") else host
for _ in range(20):
    try:
        with socket.create_connection((target, port), timeout=1):
            print(f"maintenance_listener={target}:{port}")
            break
    except OSError:
        time.sleep(1)
else:
    raise SystemExit("maintenance listener did not become reachable")
PY

echo
echo "=== FAIL-CLOSED RUNTIME VERIFICATION ==="
"$CURRENT/venv/bin/python" - "$CONFIG" "$EXECUTOR_VERSION" "$HOST_VERSION" "$CURRENT" <<'PY'
import importlib.metadata as md
import json
import pathlib
import sys

config_path, expected_executor, expected_host, current = sys.argv[1:]
import coding_executor
import host_maintenance
from host_maintenance.broker import Broker

current_root = pathlib.Path(current).resolve()
pathlib.Path(coding_executor.__file__).resolve().relative_to(current_root)
pathlib.Path(host_maintenance.__file__).resolve().relative_to(current_root)
assert coding_executor.__version__ == expected_executor
assert md.version("librechat-coding-executor") == expected_executor
assert md.version("librechat-coding-agent-host") == expected_host

config = json.loads(pathlib.Path(config_path).read_text())
health = Broker(config).health()
assert health["status"] == "running"
assert health["health"] == "healthy"
assert health["version"] == expected_executor
assert health["image_id"] == config["image_id"]

print(json.dumps({
    "executor_version": health["version"],
    "host_version": expected_host,
    "image_id": health["image_id"],
    "status": health["status"],
    "health": health["health"],
}))
PY

SYSTEMD_EXEC="$(systemctl --user show coding-agent-host-maintenance -p ExecStart --value)"
printf '%s\n' "$SYSTEMD_EXEC" | grep -F "$ROOT/current/venv/bin/python" >/dev/null
if systemctl --user show coding-agent-host-maintenance -p Environment --value | grep -E 'PYTHONPATH=[^ ]+' >/dev/null; then
  echo "STOP: maintenance service has a non-empty PYTHONPATH"
  exit 1
fi

ARMED=0
trap - ERR

echo
echo "=== RELEASE DEPLOYMENT COMPLETE ==="
echo "release=$SHA"
echo "executor=$EXECUTOR_VERSION"
echo "host=$HOST_VERSION"
echo "current=$(readlink -f "$CURRENT")"
echo "backup=$BACKUP"
