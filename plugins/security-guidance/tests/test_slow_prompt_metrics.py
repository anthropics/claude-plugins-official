import json
import os
import re
import shutil
import subprocess

import pytest

import gitutil
from conftest import git, make_repo, metrics_of, run_hook, ups_payload

SLOW = 1.2
STASH = '*"stash create"*'
MOUNTS = (
    "25 30 8:32 / / rw,relatime - ext4 /dev/sdc rw\n"
    "60 25 0:50 / /mnt/c rw,noatime - 9p C:\\134 rw,aname=drivers\n"
    "61 25 0:51 / /mnt/my\\040disk rw,noatime - 9p D:\\134 rw\n"
    "62 60 8:40 / /mnt/c/data rw - ext4 /dev/sdd rw\n"
    "63 25 0:52 / /mnt/a\\134b rw - drvfs E:\\134 rw\n"
)

# The stalling git is a shell script, and on Windows a clean prompt can itself
# take a second.
pytestmark = pytest.mark.skipif(os.name == "nt", reason="needs a shell-script git")


@pytest.fixture
def repo(tmp_path):
    return make_repo(tmp_path / "repo", {"app.py": "print('hi')\n", "lib.py": "x = 1\n"})


def _slow(hook_env, tmp_path, match):
    """hook_env with a `git` first on PATH that stalls on commands matching
    `match` (a shell case pattern)."""
    shim = tmp_path / "bin"
    shim.mkdir(exist_ok=True)
    (shim / "git").write_text(
        f'#!/bin/sh\ncase "$*" in {match}) sleep {SLOW};; esac\n'
        f'exec "{shutil.which("git")}" "$@"\n')
    (shim / "git").chmod(0o755)
    return {**hook_env, "PATH": f"{shim}{os.pathsep}{hook_env['PATH']}"}


def test_slow_capture_reports_where_the_time_went(repo, hook_env, tmp_path):
    rc, out, _ = run_hook(ups_payload(str(repo)), _slow(hook_env, tmp_path, STASH))
    m = metrics_of(out)
    assert rc == 0
    assert m["ups_ms"] >= SLOW * 1000
    assert m["ups_baseline_ms"] >= SLOW * 1000
    assert m["ups_untracked_ms"] < m["ups_baseline_ms"]
    assert m["ups_index_entries"] == 2
    assert not {"ups_no_baseline", "ups_wsl_drive", "ups_baseline_fail"} & set(m)


def test_slow_untracked_listing_is_told_apart(repo, hook_env, tmp_path):
    env = _slow(hook_env, tmp_path, '*"ls-files"*"--others"*')
    m = metrics_of(run_hook(ups_payload(str(repo)), env)[1])
    assert m["ups_untracked_ms"] >= SLOW * 1000
    assert m["ups_baseline_ms"] < m["ups_untracked_ms"]


def test_slow_prompt_with_stop_review_off_lists_nothing(repo, hook_env, tmp_path):
    env = {**_slow(hook_env, tmp_path, STASH), "ENABLE_STOP_REVIEW": "0"}
    m = metrics_of(run_hook(ups_payload(str(repo)), env)[1])
    assert m["ups_baseline_ms"] >= SLOW * 1000
    assert m["ups_untracked_ms"] == 0


def test_slow_prompt_without_a_baseline_says_so(hook_env, tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    subprocess.run(["git", "init", "-q", str(empty)], check=True)
    env = _slow(hook_env, tmp_path, '*"rev-parse HEAD"*')
    m = metrics_of(run_hook(ups_payload(str(empty)), env)[1])
    assert m["ups_no_baseline"] == 1 and "ups_index_entries" not in m


def test_git_that_stalls_past_its_timeout_still_reports(repo, hook_env, tmp_path):
    """A hung git reads as "not a repository"; the row must still go out."""
    shim = tmp_path / "bin"
    shim.mkdir()
    (shim / "git").write_text('#!/bin/sh\nexec sleep 6\n')
    (shim / "git").chmod(0o755)
    env = {**hook_env, "PATH": f"{shim}{os.pathsep}{hook_env['PATH']}"}
    m = metrics_of(run_hook(ups_payload(str(repo)), env)[1])
    assert m["ups_no_baseline"] == 1 and m["ups_ms"] >= 5000


def test_failed_snapshot_is_flagged(repo, hook_env, tmp_path):
    shim = tmp_path / "bin"
    shim.mkdir()
    (shim / "git").write_text(
        f'#!/bin/sh\ncase "$*" in {STASH}) sleep {SLOW}; exit 1;; esac\n'
        f'exec "{shutil.which("git")}" "$@"\n')
    (shim / "git").chmod(0o755)
    env = {**hook_env, "PATH": f"{shim}{os.pathsep}{hook_env['PATH']}"}
    m = metrics_of(run_hook(ups_payload(str(repo)), env)[1])
    assert m["ups_baseline_fail"] == 1


def test_fast_prompt_prints_nothing(repo, hook_env):
    rc, out, _ = run_hook(ups_payload(str(repo)), hook_env)
    assert rc == 0 and out.strip() == ""


def test_slow_launcher_is_reported_on_a_fast_prompt(repo, hook_env):
    env = {**hook_env, "SG_LAUNCHER_PROBE_MS": "4350", "SG_LAUNCHER_PROBE_MAX_MS": "4000"}
    m = metrics_of(run_hook(ups_payload(str(repo)), env)[1])
    assert m["launcher_probe_ms"] == 4350 and m["ups_ms"] < 1000


def test_other_hosts_get_no_output(repo, hook_env, tmp_path):
    env = {k: v for k, v in _slow(hook_env, tmp_path, STASH).items()
           if k not in ("CLAUDECODE", "CLAUDE_CODE_ENTRYPOINT", "PLUGIN_ROOT")}
    env["SECURITY_GUIDANCE_PORTABLE_OUTPUT"] = "1"
    assert run_hook(ups_payload(str(repo)), env)[1].strip() == ""


def test_row_holds_no_path_and_valid_keys(repo, hook_env, tmp_path):
    _, out, _ = run_hook(ups_payload(str(repo)), _slow(hook_env, tmp_path, STASH))
    assert str(repo) not in out and str(tmp_path) not in out
    metrics = json.loads(out)["metrics"]
    assert all(re.fullmatch(r"[a-z][a-z0-9_]{0,39}", k) for k in metrics)
    assert all(isinstance(v, (int, float)) for v in metrics.values())


def test_slow_capture_saves_the_same_baseline(repo, hook_env, tmp_path):
    (repo / "app.py").write_text("print('changed')\n")
    (repo / "new.txt").write_text("untracked\n")
    states = []
    for name, env in (("fast", hook_env), ("slow", _slow(hook_env, tmp_path, STASH))):
        d = tmp_path / name
        d.mkdir()
        env = {k: v for k, v in env.items() if k != "CLAUDE_CODE_REMOTE_SESSION_ID"}
        env["SECURITY_WARNINGS_STATE_DIR"] = str(d)
        run_hook(ups_payload(str(repo)), env)
        with open(d / "security_warnings_state_s1.json") as f:
            states.append(json.load(f))
    fast, slow = states
    assert git(repo, "rev-parse", fast["baseline_sha"] + "^{tree}") == \
        git(repo, "rev-parse", slow["baseline_sha"] + "^{tree}")
    assert fast["baseline_sha"] != fast["head_at_capture"]
    assert "new.txt" in fast["untracked_at_baseline"]
    assert fast["untracked_at_baseline"] == slow["untracked_at_baseline"]


@pytest.mark.parametrize("path,expected", [
    ("/mnt/c/code/app", True),
    ("/mnt/c", True),
    ("/mnt/my disk/app", True),
    ("/mnt/a\\b/app", True),
    ("/mnt/cool/app", False),
    ("/home/me/app", False),
    ("/mnt/c/data/app", False),
])
def test_windows_drive_mount(path, expected):
    assert gitutil.windows_drive_mount(path, MOUNTS) is expected


@pytest.mark.parametrize("junk", ["junk\n", "1 2 - \n", "1 2 3 / /mnt/c rw -   \n"])
def test_windows_drive_mount_skips_malformed_lines(junk):
    assert gitutil.windows_drive_mount("/mnt/c/x", junk + MOUNTS) is True


def test_wsl_drive_reaches_the_row(monkeypatch):
    import security_reminder_hook as hook
    monkeypatch.setattr(hook, "on_windows_drive", lambda cwd: True)
    assert hook._slow_prompt_metrics("/x", 2.0, 1.5, 0.1, True, 0)["ups_wsl_drive"] == 1


def test_index_entry_count(repo, tmp_path):
    assert gitutil.index_entry_count(str(repo / ".git" / "index")) == 2
    assert gitutil.index_entry_count(str(tmp_path / "missing")) is None
    (tmp_path / "bad").write_bytes(b"not an index")
    assert gitutil.index_entry_count(str(tmp_path / "bad")) is None
