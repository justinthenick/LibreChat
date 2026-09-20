# C003 gold standard

The task passes only when all of the following are demonstrated.

## Boundary and workflow

- Exactly one executor task is created from the operator-approved source baseline.
- The source repository remains unchanged.
- Relevant repository instructions and implementation files are inspected before editing.
- The existing test command is run before editing and its result is reported.
- No commit, push, merge, package installation or non-allowlisted command is attempted.

## Required implementation

- New `synology-host.js` exports the pure host-normalization and host-pattern functions.
- `popup.js` imports those functions and no longer contains duplicate local implementations.
- `popup.html` loads `popup.js` as an ES module.
- New `tests/synology-host.test.mjs` uses the Node test runner.
- `package.json` runs both the existing extension validation and the new unit tests.
- Existing runtime behavior and user-facing validation messages remain materially unchanged.

## Required test coverage

Tests prove that normalization:

- accepts an HTTP or HTTPS origin and removes the root trailing slash through `URL.origin`;
- rejects malformed input;
- rejects non-HTTP(S) protocols;
- rejects embedded usernames or passwords;
- rejects non-root paths;
- rejects query strings;
- rejects fragments.

Tests also prove that the permission-pattern function returns the normalized protocol and host followed by `/*`.

## Evidence

- Post-change `npm test` exits zero.
- `task_status` reports only the three required existing-file changes and two required new files.
- `git_diff` is complete, untruncated and includes both new files.
- The implementation remains uncommitted and unpushed.
