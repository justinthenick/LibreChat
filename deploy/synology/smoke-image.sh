#!/bin/sh
set -eu

IMAGE=${1:?Usage: smoke-image.sh IMAGE EXPECTED_COMMIT}
EXPECTED_COMMIT=${2:?Expected source commit is required}
RUN_NAME="lc-synology-smoke-$$"
MONGO_NAME="$RUN_NAME-mongo"
API_NAME="$RUN_NAME-api"

cleanup() {
  docker rm -fv "$API_NAME" "$MONGO_NAME" >/dev/null 2>&1 || true
  docker network rm "$RUN_NAME" >/dev/null 2>&1 || true
}
trap cleanup EXIT HUP INT TERM

docker run --rm -e EXPECTED_COMMIT="$EXPECTED_COMMIT" "$IMAGE" node -e '
  const assert = require("node:assert/strict");
  const fs = require("node:fs");
  assert.equal(process.env.BUILD_COMMIT, process.env.EXPECTED_COMMIT);
  assert.ok(fs.statSync("client/dist/index.html").size > 0);
  require("@librechat/api");
  require("@librechat/api/telemetry");
  console.log("Source identity, frontend and runtime modules verified");
'
docker run --rm "$IMAGE" python3 --version
docker network create "$RUN_NAME" >/dev/null
docker run -d --name "$MONGO_NAME" --network "$RUN_NAME" mongo:4.4.18 >/dev/null
ready=0
for attempt in $(seq 1 60); do
  if docker exec "$MONGO_NAME" mongo --quiet --eval 'quit(db.adminCommand({ping:1}).ok ? 0 : 1)' >/dev/null 2>&1; then
    ready=1
    break
  fi
  sleep 2
done
[ "$ready" = 1 ] || { echo 'MongoDB 4.4.18 did not become ready'; exit 1; }
docker exec "$MONGO_NAME" mongo LibreChat --quiet --eval '
  db.users.insertOne({name:"Image smoke owner",username:"image-smoke",email:"image-smoke@example.invalid",provider:"local",role:"ADMIN",createdAt:new Date()});
' >/dev/null

docker run -d --name "$API_NAME" --network "$RUN_NAME" \
  -e HOST=0.0.0.0 -e PORT=3080 -e NODE_ENV=production \
  -e MONGO_URI="mongodb://$MONGO_NAME:27017/LibreChat" \
  -e CREDS_KEY=0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef \
  -e CREDS_IV=0123456789abcdef0123456789abcdef \
  -e JWT_SECRET=image-smoke-disposable-jwt \
  -e JWT_REFRESH_SECRET=image-smoke-disposable-refresh \
  -e SEARCH=false -e SCHEDULES_SINGLE_PROCESS=true \
  -e DEPLOYMENT_SKILLS_DIR=/app/custom/ba-agent/skills \
  "$IMAGE" npm run backend >/dev/null

ready=0
for attempt in $(seq 1 90); do
  if [ "$(docker inspect -f '{{.State.Running}}' "$API_NAME")" != true ]; then
    break
  fi
  if docker exec "$API_NAME" node -e '
    fetch("http://127.0.0.1:3080/readyz", {signal:AbortSignal.timeout(3000)})
      .then(r => process.exit(r.status === 200 ? 0 : 1)).catch(() => process.exit(1));
  ' >/dev/null 2>&1; then
    ready=1
    break
  fi
  sleep 2
done
docker logs --tail 100 "$API_NAME"
[ "$ready" = 1 ] || { echo 'Image failed startup or readiness'; exit 1; }

# Match production ordering: normal LibreChat startup seeds built-in access roles;
# only after readiness do the deployment agent seeders run.
#
# Production mirrors the coding skill from GitHub before the pilot seeder runs.
# This disposable smoke intentionally has no production GitHub credential, so
# create the same source-identity prerequisite through LibreChat's own skill
# model API rather than weakening the pilot seeder or inserting raw Mongo data.
docker exec "$API_NAME" node -e '
  const crypto = require("node:crypto");
  const path = require("node:path");
  const mongoose = require("mongoose");
  require("module-alias")({ base: path.resolve("/app/api") });
  const connect = require("/app/config/connect");
  const { createModels } = require("@librechat/data-schemas");

  const sourceId = "coding-agent-skills";
  const upstreamId = "coding-agent-skills:.agents/skills/codebase-design";

  (async () => {
    await connect();
    createModels(mongoose);
    const db = require("~/models");
    let skill = await db.findSkillBySourceIdentity({ source: "github", upstreamId });

    if (!skill) {
      const author = new mongoose.Types.ObjectId(
        crypto.createHash("sha256").update(`github:${sourceId}`).digest("hex").slice(0, 24),
      );
      const created = await db.createSkill({
        name: "codebase-design",
        description:
          "Disposable image-smoke fixture for the validated codebase-design GitHub mirror.",
        body:
          "---\\nname: codebase-design\\ndescription: Disposable image-smoke fixture for the validated codebase-design GitHub mirror.\\n---\\n\\nSmoke fixture only.",
        author,
        authorName: "GitHub Sync",
        source: "github",
        sourceMetadata: {
          provider: "github",
          sourceId,
          upstreamId,
          owner: "justinthenick",
          repo: "LibreChat",
          ref: "server/synology",
          skillPath: ".agents/skills/codebase-design",
          commitSha: process.env.BUILD_COMMIT || "smoke-fixture",
          skillBlobSha: "smoke-fixture",
          syncedAt: new Date().toISOString(),
          syncStatus: "synced",
        },
      });
      skill = created.skill;
    }

    if (
      skill.name !== "codebase-design" ||
      skill.source !== "github" ||
      skill.sourceMetadata?.upstreamId !== upstreamId ||
      skill.sourceMetadata?.syncStatus !== "synced"
    ) {
      throw new Error("Coding-agent smoke skill fixture does not match the validated mirror identity");
    }
    console.log("Coding-agent mirrored skill prerequisite verified");
  })()
    .then(() => mongoose.disconnect())
    .catch(async (error) => {
      console.error(error);
      await mongoose.disconnect().catch(() => {});
      process.exit(1);
    });
'
docker exec "$API_NAME" node config/seed-production-agents.js /app/custom/ba-agent/production
docker exec "$API_NAME" node config/seed-coding-agent-pilot.js /app/custom/coding-agent/production
docker exec "$API_NAME" node -e '
  fetch("http://127.0.0.1:3080/api/config", {signal:AbortSignal.timeout(5000)})
    .then(r => { if (r.status !== 200) throw new Error(`HTTP ${r.status}`); return r.json(); })
    .then(() => console.log("/api/config: HTTP 200 with valid JSON"))
    .catch(e => { console.error(e.message); process.exit(1); });
'
docker exec "$API_NAME" node config/seed-production-agents.js /app/custom/ba-agent/production
docker exec "$API_NAME" node config/seed-coding-agent-pilot.js /app/custom/coding-agent/production
echo 'Synology image smoke passed, including idempotent production and coding-pilot seeds'
