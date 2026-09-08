# Self-hosted Code Interpreter on Synology

This deployment adds the official `LibreChat-AI/code-interpreter` service as a separate, pinned Docker Compose stack and connects only its API gateway to LibreChat's existing Docker network.

## Security model

Code Interpreter runs model-generated code. The Synology integration therefore fails closed:

- **KVM/libkrun microVM isolation is required.** `/dev/kvm` must exist and be usable by the root deployment task.
- The weaker direct NsJail mode is **not** selected automatically because it shares the NAS kernel.
- `LOCAL_MODE=false` and `CODEAPI_AUTH_PROVIDER=librechat-jwt` are mandatory.
- LibreChat owns the Ed25519 private signing key. Code Interpreter receives only the matching public JWKS verifier.
- Worker-to-sandbox execution manifests use a separate Ed25519 keypair.
- Internal Code API, bridge, Redis, MinIO and egress-grant credentials are generated randomly and stored only in private host env files.
- No Code Interpreter service publishes a NAS host port. Only the Code API gateway joins `librechat_librechat`, under the DNS alias `librechat-codeapi`.
- The sandbox stack uses an internal Docker network and the upstream egress gateway.

The upstream source is pinned by `manage-code-interpreter.sh` to:

`725f79900bf06298653668a029eefd69460d900e`

Do not move that pin as an incidental update. Treat an upstream Code Interpreter update as a compatibility/security change and rerun the functional Agent tests.

## Host paths

- LibreChat repo: `/volume1/docker/librechat`
- Code Interpreter source checkout: `/volume1/docker/librechat-code-interpreter`
- Code Interpreter private data/env: `/volume1/docker/librechat-code-interpreter-data`
- Private Code Interpreter env: `/volume1/docker/librechat-code-interpreter-data/codeapi.env`

The source checkout can be recreated from GitHub because persistent credentials/data live outside it.

## Preflight

Run:

```sh
printf 'ARCH='; uname -m
if [ -c /dev/kvm ]; then
  echo 'KVM=AVAILABLE'
  ls -l /dev/kvm
else
  echo 'KVM=NOT_AVAILABLE'
fi
```

If KVM is unavailable, stop. Do not expose direct NsJail execution to general Agent use on the NAS.

## Bootstrap

After the feature is deployed to `server/synology`:

```sh
cd /volume1/docker/librechat
sudo sh deploy/synology/bootstrap-code-interpreter.sh
```

The bootstrap:

1. checks Docker, `/dev/kvm` and the existing LibreChat network;
2. clones/checks out the exact upstream Code Interpreter pin;
3. backs up the private LibreChat `.env`;
4. runs upstream's `scripts/setup-local-auth-env.js` in an ephemeral Node container;
5. generates/reuses production internal service secrets without displaying them;
6. builds and starts the hardened Code Interpreter stack;
7. recreates only the LibreChat API so the JWT signer and internal Code API URL are loaded;
8. verifies LibreChat and Code Interpreter health over the Docker-internal route.

On failure it restores the previous LibreChat private configuration and removes the optional Code Interpreter stack.

The first KVM build compiles and bakes the supported language runtimes into the sandbox root image, so it can take materially longer than an ordinary LibreChat deploy.

## Status and lifecycle

```sh
sudo sh deploy/synology/manage-code-interpreter.sh status
sudo sh deploy/synology/manage-code-interpreter.sh check
sudo sh deploy/synology/manage-code-interpreter.sh reconcile
sudo sh deploy/synology/manage-code-interpreter.sh down
```

`reconcile` is idempotent. It rebuilds the Code Interpreter images only when the pinned source changes or required images are missing.

## Functional verification

After bootstrap, use the production BA Supervisor in a new conversation:

```text
Use the execute_code tool to calculate the SHA-256 hash of this exact UTF-8 string:
Justin LibreChat test 2026
Return only the hexadecimal hash. Do not calculate it mentally.
```

A passing test must show an actual code-tool invocation and the expected digest. A model claim that code ran is not sufficient evidence.

Then continue the production-agent verification sequence: `file_search`, OCR, artifacts, Release evidence assessment, and BA -> Release handoff.

## Diagnostics

Runtime summary:

```sh
sudo sh deploy/synology/manage-code-interpreter.sh status
sudo docker ps -a --filter name=librechat-codeapi
```

Sandbox health:

```sh
sudo docker inspect -f '{{.State.Health.Status}}' librechat-codeapi-sandbox
```

Recent service logs (no env values):

```sh
sudo docker logs --tail 100 librechat-codeapi
sudo docker logs --tail 100 librechat-codeapi-worker
sudo docker logs --tail 100 librechat-codeapi-sandbox
```

Verify LibreChat loaded the self-hosted route without displaying private signing material:

```sh
sudo docker exec librechat sh -lc '
[ "$LIBRECHAT_CODE_BASEURL" = "http://librechat-codeapi:3112/v1" ] && echo CODE_BASEURL=OK || echo CODE_BASEURL=WRONG
[ "$CODEAPI_AUTH_PROVIDER" = "librechat-jwt" ] && echo CODE_AUTH=JWT || echo CODE_AUTH=WRONG
[ -n "$CODEAPI_JWT_PRIVATE_JWK_JSON" ] && echo CODE_SIGNER=CONFIGURED || echo CODE_SIGNER=MISSING
'
```
