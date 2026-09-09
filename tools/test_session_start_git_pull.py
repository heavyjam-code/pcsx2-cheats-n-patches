#!/usr/bin/env python3
"""Test startup sync against local remotes; retain fixtures for inspection.

Run: python -m unittest discover -s tools -p test_session_start_git_pull.py -v
The printed temporary directory is deliberately never deleted by this suite.
"""

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


HOOK = Path(__file__).resolve().parents[1] / ".codex/hooks/session-start-git-pull.py"
SPEC = importlib.util.spec_from_file_location("session_start_git_pull", HOOK)
sync_hook = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(sync_hook)


class CheckoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixtures = Path(tempfile.mkdtemp(prefix="codex-git-sync-tests-"))
        print(f"\nRetained Git fixtures: {cls.fixtures}", file=sys.stderr)
        cls.env = os.environ.copy()
        cls.env.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1",
                       GIT_TERMINAL_PROMPT="0", GCM_INTERACTIVE="never")

    def git(self, repo, *args):
        result = subprocess.run(
            ["git", "-C", str(repo), *args], env=self.env,
            capture_output=True, text=True, encoding="utf-8", timeout=10,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result.stdout.strip()

    def setUp(self):
        self.root = self.fixtures / self._testMethodName
        self.root.mkdir()
        self.remote = self.root / "remote.git"
        self.git(self.root, "init", "--bare", "--initial-branch=main", str(self.remote))
        self.producer = self.root / "producer"
        self.git(self.root, "clone", str(self.remote), str(self.producer))
        self.configure(self.producer)
        self.commit(self.producer, "tracked.txt", "initial\n")
        self.git(self.producer, "push", "-u", "origin", "main")
        self.checkout = self.root / "checkout"
        self.git(self.root, "clone", str(self.remote), str(self.checkout))
        self.configure(self.checkout)
        self.original = self.git(self.checkout, "rev-parse", "HEAD")

    def configure(self, repo):
        self.git(repo, "config", "user.name", "Hook Test")
        self.git(repo, "config", "user.email", "hook-test@example.invalid")
        self.git(repo, "config", "commit.gpgsign", "false")
        self.git(repo, "config", "core.autocrlf", "false")

    def commit(self, repo, filename, content):
        (repo / filename).write_text(content, encoding="utf-8")
        self.git(repo, "add", "--", filename)
        self.git(repo, "commit", "-m", f"Update {filename}")

    def advance_remote(self, filename="tracked.txt", content="remote update\n"):
        self.commit(self.producer, filename, content)
        self.git(self.producer, "push", "origin", "main")

    def run_hook(self, cwd=None):
        result = subprocess.run(
            [sys.executable, str(HOOK)], cwd=cwd or self.checkout, env=self.env,
            capture_output=True, text=True, encoding="utf-8", timeout=20,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        return json.loads(result.stdout) if result.stdout.strip() else None

    def assert_unchanged(self):
        self.assertEqual(self.git(self.checkout, "rev-parse", "HEAD"), self.original)

    def test_behind_fast_forwards(self):
        self.advance_remote()
        result = self.run_hook()
        self.assertIn("Pulled 1 commit(s) from origin/main", result["systemMessage"])
        self.assertEqual(result["hookSpecificOutput"]["hookEventName"], "SessionStart")
        self.assertIn("working tree was updated", result["hookSpecificOutput"]["additionalContext"])
        self.assertEqual(self.git(self.checkout, "rev-parse", "HEAD"),
                         self.git(self.producer, "rev-parse", "HEAD"))

    def test_up_to_date_is_quiet(self):
        self.assertIsNone(self.run_hook())
        self.assert_unchanged()

    def test_unstaged_work_is_preserved(self):
        self.advance_remote()
        (self.checkout / "tracked.txt").write_text("local work\n", encoding="utf-8")
        self.assertIsNone(self.run_hook())
        self.assert_unchanged()
        self.assertEqual((self.checkout / "tracked.txt").read_text(), "local work\n")

    def test_staged_work_is_preserved(self):
        self.advance_remote()
        (self.checkout / "tracked.txt").write_text("staged work\n", encoding="utf-8")
        self.git(self.checkout, "add", "tracked.txt")
        self.assertIsNone(self.run_hook())
        self.assert_unchanged()
        self.assertEqual(self.git(self.checkout, "show", ":tracked.txt"), "staged work")

    def test_staged_edit_and_unstaged_reversal_are_preserved(self):
        self.advance_remote()
        tracked = self.checkout / "tracked.txt"
        tracked.write_text("staged work\n", encoding="utf-8")
        self.git(self.checkout, "add", "tracked.txt")
        tracked.write_text("initial\n", encoding="utf-8")
        self.assertEqual(self.git(self.checkout, "diff", "HEAD", "--"), "")
        self.assertIsNone(self.run_hook())
        self.assert_unchanged()
        self.assertEqual(self.git(self.checkout, "show", ":tracked.txt"), "staged work")
        self.assertEqual(tracked.read_text(), "initial\n")

    def test_untracked_file_allows_fast_forward(self):
        self.advance_remote()
        (self.checkout / "notes.txt").write_text("my notes\n", encoding="utf-8")
        self.assertIsNotNone(self.run_hook())
        self.assertEqual((self.checkout / "notes.txt").read_text(), "my notes\n")

    def test_untracked_collision_reports_and_preserves_file(self):
        self.advance_remote("notes.txt", "remote notes\n")
        (self.checkout / "notes.txt").write_text("my notes\n", encoding="utf-8")
        result = self.run_hook()
        self.assertIn("would be overwritten", result["systemMessage"])
        self.assertNotIn("hookSpecificOutput", result)
        self.assert_unchanged()
        self.assertEqual((self.checkout / "notes.txt").read_text(), "my notes\n")

    def test_diverged_history_reports_without_merge(self):
        self.advance_remote()
        self.commit(self.checkout, "local.txt", "local commit\n")
        self.original = self.git(self.checkout, "rev-parse", "HEAD")
        result = self.run_hook()
        self.assertIn("git pull --ff-only failed", result["systemMessage"])
        self.assert_unchanged()
        self.assertFalse((self.checkout / ".git/MERGE_HEAD").exists())

    def test_ahead_history_is_quiet(self):
        self.commit(self.checkout, "local.txt", "local commit\n")
        self.original = self.git(self.checkout, "rev-parse", "HEAD")
        self.assertIsNone(self.run_hook())
        self.assert_unchanged()

    def test_no_upstream_is_quiet(self):
        self.advance_remote()
        self.git(self.checkout, "branch", "--unset-upstream")
        self.assertIsNone(self.run_hook())
        self.assert_unchanged()

    def test_detached_head_is_quiet(self):
        self.advance_remote()
        self.git(self.checkout, "checkout", "--detach")
        self.assertIsNone(self.run_hook())
        self.assert_unchanged()

    def test_session_in_subdirectory_fast_forwards(self):
        self.advance_remote()
        nested = self.checkout / "nested"
        nested.mkdir()
        self.assertIsNotNone(self.run_hook(nested))
        self.assertEqual((self.checkout / "tracked.txt").read_text(), "remote update\n")

    def test_non_repository_is_quiet(self):
        self.assertIsNone(self.run_hook(self.root))


class ProcessTests(unittest.TestCase):
    def test_credentials_and_timeout_are_subprocess_local(self):
        before = os.environ.copy()
        with patch.object(sync_hook.subprocess, "run") as run:
            sync_hook._git(Path.cwd(), "pull", timeout=15)
        args, kwargs = run.call_args
        self.assertEqual(args[0][1:5], ["-c", "credential.helper=", "-c",
                                       "credential.helper=!gh auth git-credential"])
        self.assertEqual(kwargs["env"]["GIT_TERMINAL_PROMPT"], "0")
        self.assertEqual(kwargs["env"]["GCM_INTERACTIVE"], "never")
        self.assertEqual(kwargs["timeout"], 15)
        self.assertEqual(dict(os.environ), before)

    def test_timeout_does_not_block_session(self):
        with patch.object(sync_hook, "_git", side_effect=subprocess.TimeoutExpired("git", 15)):
            self.assertIsNone(sync_hook.sync())

    def test_missing_git_is_nonfatal(self):
        with patch.object(sync_hook, "_git", side_effect=FileNotFoundError("git unavailable")):
            self.assertIn("git unavailable", sync_hook.sync()["systemMessage"])

    def test_auth_and_offline_failures_are_quiet(self):
        for reason in ("fatal: Authentication failed", "fatal: Could not resolve host"):
            with self.subTest(reason=reason):
                results = [
                    subprocess.CompletedProcess([], 0, stdout=value, stderr="")
                    for value in (".git", "refs/heads/main", "origin/main", "", "", "abc")
                ]
                results.append(subprocess.CompletedProcess([], 1, stdout="", stderr=reason))
                with patch.object(sync_hook, "_git", side_effect=results):
                    self.assertIsNone(sync_hook.sync())


if __name__ == "__main__":
    unittest.main()
