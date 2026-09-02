#!/usr/bin/env bash
# SessionStart hook: fast-forward this clone from its upstream before work starts.
#
# This repo is edited from more than one machine, so whichever clone sat idle is
# behind the other. The hook is committed so every clone runs it. On a machine
# whose own ~/.claude/settings.json already runs a session-start git pull, it
# stands down, so the two hooks never pull the same checkout at the same time.
#
# Deliberately conservative:
#   - not a git repo, detached HEAD, or no upstream -> do nothing
#   - uncommitted changes to tracked files          -> do nothing
#   - --ff-only, so it never merges, rebases, or rewrites local history
#   - never prompts for credentials (would hang session start)
# Silent unless it actually moved HEAD or hit a non-fast-forward.

set -u

# A machine-wide session-start pull hook takes precedence over this one.
grep -qs 'session-start-git-pull' "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/settings.json" && exit 0

repo="${CLAUDE_PROJECT_DIR:-$PWD}"

git -C "$repo" rev-parse --git-dir >/dev/null 2>&1 || exit 0

upstream=$(git -C "$repo" rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null) || exit 0
[ -n "$upstream" ] || exit 0

# Uncommitted work: leave the tree alone. (Untracked files don't block a fast-forward.)
git -C "$repo" diff --quiet HEAD -- 2>/dev/null || exit 0

before=$(git -C "$repo" rev-parse HEAD 2>/dev/null) || exit 0

export GIT_TERMINAL_PROMPT=0 GCM_INTERACTIVE=never
out=$(git -C "$repo" pull --ff-only --no-rebase --quiet 2>&1)
rc=$?

after=$(git -C "$repo" rev-parse HEAD 2>/dev/null) || exit 0

# Strip anything that would break the JSON below, and keep it short.
sanitize() { printf '%s' "$1" | tr -d '\042\134' | tr '\n\r\t' '   ' | cut -c1-300; }

if [ "$rc" -ne 0 ]; then
  # Offline / unreachable remote is not worth a message every session.
  case "$out" in
    *"Could not resolve host"*|*"unable to access"*|*"could not read"*|\
    *"Connection "*|*"connect to"*|*"timed out"*|*"Authentication failed"*)
      exit 0 ;;
  esac
  detail=$(printf '%s' "$out" | grep -v '^hint:')
  printf '{"systemMessage":"git pull --ff-only failed in %s: %s"}' \
    "$(sanitize "$(basename "$repo")")" "$(sanitize "$detail")"
  exit 0
fi

[ "$before" = "$after" ] && exit 0

n=$(git -C "$repo" rev-list --count "$before..$after" 2>/dev/null || echo "some")
range="$(git -C "$repo" rev-parse --short "$before")..$(git -C "$repo" rev-parse --short "$after")"
msg="Pulled $n commit(s) from $(sanitize "$upstream") ($range)"

printf '{"systemMessage":"%s","hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"%s - the working tree was updated before this session started."}}' \
  "$msg" "$msg"
