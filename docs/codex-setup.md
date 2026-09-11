# Codex setup

[AGENTS.md](../AGENTS.md) contains the shared patching, testing and recording
rules. Keep machine-specific PCSX2 paths and harness notes in `Codex.local.md`
at the repository root. That file is gitignored, and `AGENTS.md` explicitly
instructs Codex to read it when present.

## Session startup

[.codex/hooks.json](../.codex/hooks.json) contains no project lifecycle hooks.
Startup, resume and clear do not automatically pull the repository.
[session-start-git-pull.py](../.codex/hooks/session-start-git-pull.py) remains
available as an optional manual update helper:

```text
python .codex/hooks/session-start-git-pull.py
```

Requirements: Git and Python 3 on PATH (`python` on Windows, `python3` on
macOS/Linux). The script needs only the Python standard library.
For authenticated HTTPS remotes, install GitHub CLI and sign in with
`gh auth login`. The helper uses its credential helper without changing Git
configuration, avoiding interactive credential dialogs on this laptop.

The helper only fast-forwards the current branch from its configured upstream.
It skips detached HEAD, branches without an upstream and staged or unstaged
tracked changes. Untracked files are preserved; Git refuses a pull that
would overwrite them. It never merges, rebases or resets local work.
The helper reports pull failures and the commit range after a successful update.
It runs only when explicitly invoked; starting a session does not invoke it.

## Verify changes

Run the manual update helper tests from the repository root:

```text
python -B -m unittest discover -s tools -p test_session_start_git_pull.py -v
```

The tests use local Git repositories and require no network or model calls.
Their temporary fixtures are retained, with the location printed, so they
can be inspected and cleaned up under the local Recycle Bin rules.
