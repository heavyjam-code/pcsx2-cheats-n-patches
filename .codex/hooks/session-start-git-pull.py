#!/usr/bin/env python3
"""Fast-forward a clean, attached checkout before a Codex session starts."""

import json
import os
from pathlib import Path
import subprocess
import time


QUIET_FAILURES = (
    "could not resolve host", "unable to access", "could not read",
    "connection ", "connect to", "timed out", "authentication failed",
    "permission denied (publickey", "terminal prompts disabled",
)


def _git(repo, *args, timeout=2):
    # Clear the multi-valued system helper before adding gh, so GCM cannot
    # open a credential dialog. Keep these overrides local to the subprocess.
    env = os.environ.copy()
    env.update(GIT_TERMINAL_PROMPT="0", GCM_INTERACTIVE="never")
    return subprocess.run(
        ["git", "-c", "credential.helper=", "-c",
         "credential.helper=!gh auth git-credential", "-C", str(repo), *args],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        env=env, timeout=timeout,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )


def sync(repo=None):
    """Return a hook message or None; never merge, rebase, or discard work."""
    repo = Path.cwd() if repo is None else Path(repo)
    deadline = time.monotonic() + 18

    def git(*args, timeout=2):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise subprocess.TimeoutExpired("git", 18)
        return _git(repo, *args, timeout=min(timeout, remaining))

    try:
        if git("rev-parse", "--git-dir").returncode:
            return None
        if git("symbolic-ref", "--quiet", "HEAD").returncode:
            return None
        upstream = git("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
        if upstream.returncode or not upstream.stdout.strip():
            return None
        # Check each layer separately: a staged edit and its unstaged reversal
        # can cancel out in a single diff against HEAD.
        if git("diff", "--quiet", "--no-ext-diff", "--").returncode:
            return None
        if git("diff", "--cached", "--quiet", "--no-ext-diff", "--").returncode:
            return None
        before = git("rev-parse", "HEAD")
        if before.returncode:
            return None
        pulled = git("pull", "--ff-only", "--no-rebase", "--quiet", timeout=15)
        if pulled.returncode:
            detail = "\n".join(
                line for line in (pulled.stdout + pulled.stderr).splitlines()
                if not line.startswith("hint:")
            ).strip()
            if any(reason in detail.lower() for reason in QUIET_FAILURES):
                return None
            return {"systemMessage": f"git pull --ff-only failed in {repo.name}: {detail[:500]}"}
        after = git("rev-parse", "HEAD")
        if after.returncode or before.stdout == after.stdout:
            return None
        old, new = before.stdout.strip(), after.stdout.strip()
        count = git("rev-list", "--count", f"{old}..{new}")
        number = count.stdout.strip() if not count.returncode else "some"
        message = f"Pulled {number} commit(s) from {upstream.stdout.strip()} ({old[:7]}..{new[:7]})"
        return {
            "systemMessage": message,
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": f"{message} - the working tree was updated before this session started.",
            },
        }
    except subprocess.TimeoutExpired:
        # An unreachable remote must not delay or interrupt starting a session.
        return None
    except OSError as error:
        return {"systemMessage": f"Git sync could not run: {error}"}


def main():
    result = sync()
    if result is not None:
        print(json.dumps(result))


if __name__ == "__main__":
    main()
