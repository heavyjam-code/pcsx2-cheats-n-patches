# Codex setup

[AGENTS.md](../AGENTS.md) contains the shared patching, testing and recording
rules. Keep machine-specific PCSX2 paths and harness notes in `Codex.local.md`
at the repository root. That file is gitignored, and `AGENTS.md` explicitly
instructs Codex to read it when present.

## Session startup

[.codex/hooks.json](../.codex/hooks.json) registers a `SessionStart` hook for
startup, resume and clear. It runs
[session-start-git-pull.py](../.codex/hooks/session-start-git-pull.py) before
work starts, including when Codex is opened in a repository subdirectory.
It does not pull during compaction in the middle of an investigation.

Requirements: Git and Python 3 on PATH (`python` on Windows, `python3` on
macOS/Linux). The Windows command uses the built-in Windows PowerShell;
the script needs only the Python standard library.
For authenticated HTTPS remotes, install GitHub CLI and sign in with
`gh auth login`. The hook uses its credential helper without changing Git
configuration, avoiding interactive credential dialogs on this laptop.

Open the repository as a trusted project in Codex. On the first session,
use `/hooks` in the Codex CLI to review and trust this hook. Codex skips
untrusted hook definitions; changing a definition requires another review.
The hook uses Codex's default-enabled hooks feature. See the
[official hooks documentation](https://learn.chatgpt.com/docs/hooks).

The hook only fast-forwards the current branch from its configured upstream.
It skips detached HEAD, branches without an upstream and staged or unstaged
tracked changes. Untracked files are preserved; Git refuses a pull that
would overwrite them. It never merges, rebases or resets local work.
Offline or authentication failures leave the session usable. An actionable
pull failure is reported, and a successful update tells Codex which commit
range arrived. Any user-wide pull hook should skip repositories with their
own `.codex/hooks.json` to avoid duplicate pulls.

## Verify changes

Run the startup hook tests from the repository root:

```text
python -B -m unittest discover -s tools -p test_session_start_git_pull.py -v
```

The tests use local Git repositories and require no network or model calls.
Their temporary fixtures are retained, with the location printed, so they
can be inspected and cleaned up under the local Recycle Bin rules.
