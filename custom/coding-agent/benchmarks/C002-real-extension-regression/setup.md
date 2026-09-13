# C002 setup

Use a disposable Linux-filesystem clone of the real Synology Magnet Sender extension. Do not expose the Windows working repository to the executor.

The approved source baseline is:

- repository: `justinthenick/synology-magnet-sender-chrome`
- branch: `main`
- commit: `f639132676081f8fdc2b19d45aecfcf209366d78`

Create the disposable repository from the existing Windows clone:

```bash
git clone --branch main --single-branch \
  '/mnt/c/Users/Justin Kemp/Documents/Synology-magnet-sender' \
  ~/coding-agent/repos/synology-magnet-c002
cd ~/coding-agent/repos/synology-magnet-c002
git rev-parse HEAD
```

Stop if the reported commit is not the approved source baseline. Do not reset or modify the Windows repository.

Seed exactly two controlled regressions in the disposable clone:

```bash
sed -i 's/"version": "1.3.0"/"version": "1.3.1"/' package.json
sed -i 's/id="send"/id="sendMagnets"/' popup.html
git add package.json popup.html
git commit -m "seed C002 controlled regressions"
docker exec librechat-coding-executor sh -lc \
  'cd /home/justin_kemp/coding-agent/repos/synology-magnet-c002 && npm test'
```

The final command must fail before the pilot is invoked. The seeded commit is the clean source state that the executor must leave unchanged; all repairs belong in its new task worktree.
