# C003 task prompt

Work only through `coding_executor` in repository alias `synology-magnet-c003`.

Create exactly one isolated task. Inspect the repository instructions and relevant popup, package and validation files before editing. Run the existing test command before making changes.

Extract the pure Synology host validation and host-permission-pattern logic from the popup script into a new reusable ES module named `synology-host.js`. Import and use those functions from the popup script, and load the popup script as a module.

Add `tests/synology-host.test.mjs` using the Node test runner. Cover successful normalization and rejection of malformed URLs, unsupported protocols, embedded credentials, paths, query strings and fragments. Cover generation of the Chrome host-permission pattern. Update the package test command so the existing extension validation and the new unit tests both run.

Make the smallest justified change. Do not change product behavior beyond the extraction and test integration. Finish with the post-change test result, task status and a complete `git_diff` that includes both new files. Do not commit, push, merge or modify the source repository.
