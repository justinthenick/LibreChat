# Contained ACP candidate

The host Broker owns task authorization, the immutable OpenCode image pin, sandbox
creation and validation, and the lifetime of a local ACP stdio connection. This is
an operator-side adapter; it is not an additional HTTP or MCP tool and does not
grant an agent Docker access.

## Client entry point

An operator-installed host package provides:

```text
coding-agent-acp --task <managed-task-id>
```

The equivalent module entry point is `python -m host_maintenance.acp_stream` with
the same task argument. The trusted launcher supplies `CODING_MAINTENANCE_CONFIG`
pointing to operator policy outside the repository and task mounts. The policy
uses the existing Broker schema and additionally requires `acp_image_id` pinned
to an immutable SHA-256 image ID. The configured executor must contain the
`task-identity` maintenance helper. Do not point candidate acceptance at the live
executor: use a separately named candidate with the reviewed mount and shared
maintenance-lock contract.

An ACPX/OpenClaw custom-agent command can launch this stdio entry point with the
operator-selected task ID. The command accepts no image, path, container name,
Docker flag, shell command, or network override. Client configuration and provider
credentials are not installed or changed by this implementation.

## Session behavior

1. Acquire the Broker mutex and a nonblocking per-task file lock next to the
   configured maintenance lock. Lock files must be regular, single-link,
   owner-only files owned by the Broker account. They persist to avoid inode
   replacement races between waiting processes.
2. Authorize the canonical managed task through the candidate executor. Create
   and immediately validate a new stopped sandbox. An existing sandbox is never
   adopted or replaced.
3. Start and revalidate the sandbox, bind the stream to its immutable container
   ID, and verify the pinned runtime image, reviewed entry point and non-TTY mode.
4. Hold the shared maintenance gate while forwarding ACP bytes. Check the task
   directory device/inode again after acquiring the gate. Exclusive maintenance
   is refused during the connection; the per-task lock excludes overlapping
   Broker lifecycle operations across processes.
5. Keep protocol stdout and diagnostics stderr separate. Each direction buffers
   at most 64 KiB and applies backpressure. The session lasts at most one hour,
   allows at most 64 MiB each of input and stdout, and at most 1 MiB of stderr.
   Client EOF has a ten-second drain deadline. Docker signal proxying and detach
   keys are disabled.
6. On EOF, an error, SIGINT or SIGTERM, terminate/reap the attach subprocess and
   revalidate the owned sandbox before removal. Normal completion returns the
   attach exit code; adapter failure returns nonzero. Policy/identity drift
   refuses cleanup rather than deleting an unvalidated object. A failed initial
   validation leaves the newly created specimen for operator inspection.

The sandbox remains UID/GID 1000, read-only except for the exact task mount and
private tmpfs mounts, with no network, no added capabilities, no Docker socket
or host credentials, and the existing fixed resource limits. The transport does
not add model/provider connectivity. Session state in the private home tmpfs is
discarded with the sandbox. SIGKILL/host failure cannot run Python cleanup;
leftover objects require validated operator recovery, not automatic adoption.

The host account and installed Broker code are trusted, as in the existing
maintenance design. These locks coordinate cooperating Broker processes; they
do not restrict another trusted process with independent Docker access.

## Candidate evidence — 2026-10-04

Base: `cb0d7177f35b759033e2d2671b174e9d8da6947a`.

- Existing executor candidate, reused without rebuilding:
  `sha256:3d35507d0fe4c8fd93b97d3d352bd85175e04d03a2a3fbe261cfd8cc312d384b`.
- Pinned OpenCode 1.18.34 image:
  `sha256:485b8145db51ff2b7b494f117b8409d1e3a68ffcb315fc9d814b1d5662d5a276`.
- Phase 3C.12B task identity: PASS, including all identity checks and exclusive
  gate evidence. The earlier NameError was the shell-quoted validation print.
- Real modified Broker create → inspect → start → remove: PASS.
- Real CLI initialize: PASS, protocol version 1 and OpenCode 1.18.34.
- Real EOF and SIGTERM cleanup: PASS, with no ACP sandbox left behind.
- Active-session removal refusal, held maintenance gate and CLI image-override
  refusal: PASS.
- Focused ACP tests: 49 passed. Full host suite: 93 passed. Full executor suite:
  119 passed. Full suites ran using dependencies already in the candidate image,
  a read-only task mount and no network; no WSL dependency installation was needed.
- Source remained clean and the live executor ID/image/start time stayed unchanged.
  Temporary candidate executors and ACP sandboxes were removed.

One defect was found and corrected during acceptance: raising `InterruptedError`
from the signal handler is swallowed by Python's selector. The handler now raises
`RuntimeError`; a real-signal regression test and the real SIGTERM smoke cover it.

This evidence covers the contained Broker/stdio boundary. It does not establish
an OpenClaw/ACPX routed model turn, provider authentication, or deployment
acceptance. Changes remain in the canonical task worktree pending review.


## Reviewed executable and deployment paths

Each host Codex invocation opens the resolved executable read-only, validates
its digest and version through that descriptor, then executes the same open
descriptor. A symlink or pathname replacement cannot switch a validated
invocation to a different inode. Subsequent requests revalidate the configured
path and reject unreviewed upgrades. The operator account and installation
remain trusted, as with the host Broker itself.

The Broker requires the relay signing key to match its own policy before
creating a session. Missing, duplicate, malformed or rotated relay keys are
refused without including key material in diagnostics.

The adapter socket and workspace use the fixed operator-home
~/.local/share/coding-maintenance/codex-adapter root shared by the systemd
unit and Broker. A nondefault CODING_CODEX_ADAPTER_ROOT is unsupported and
is rejected before deployment performs any Git, build or runtime operation.
