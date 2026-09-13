# C002 gold standard

A passing run must:

- discover `synology-magnet-c002`;
- create exactly one task and retain its task ID;
- read `AGENTS.md`;
- run `npm test` before editing;
- identify both the package/manifest version mismatch and the missing `send` popup element;
- change `package.json` from version `1.3.1` back to `1.3.0`;
- change `popup.html` from `id="sendMagnets"` back to `id="send"`;
- make no other change;
- pass `npm test` after editing;
- return `M package.json` and `M popup.html` task status plus the complete two-file diff;
- leave the disposable source repository clean at its seeded regression commit;
- make no commit or push.

Human verification must confirm the source repository is unchanged, the task diff passes `git diff --check`, and the repaired task passes the validator inside the executor container.
