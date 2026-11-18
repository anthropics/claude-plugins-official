"""A Stop review leaves a baseline for the next Stop: the checkout as that
review read it."""
import json
import os
import re
import shutil
import time
from pathlib import Path

import pytest

from conftest import (
    STUB_VULN, commit_file, edit_payload, git, make_repo, metrics_of, run_hook,
    stop_payload, ups_payload,
)

posix_only = pytest.mark.skipif(os.name == "nt", reason="needs a shell-script git")


class FindingAfter(list):
    """The stub's one finding, returned once `action` has run: the stub reads
    its findings while the hook waits for the review."""

    def __init__(self, action):
        super().__init__([STUB_VULN])
        self.action = action

    def __iter__(self):
        action, self.action = self.action, None
        if action:
            action()
        return super().__iter__()


@pytest.fixture
def repo(tmp_path):
    return make_repo(tmp_path / "repo", {"app.py": "a = 1\n", "lib.py": "b = 1\n"})


@pytest.fixture
def stop(repo, hook_env, stub_api):
    def run(finding_after=None, cwd=repo, env=(), **fields):
        """Returns the MARK_* names in what was sent for review."""
        del stub_api.bodies[:]
        stub_api.vulns = FindingAfter(finding_after) if finding_after else []
        rc, out, _ = run_hook({**stop_payload(cwd), **fields}, {**hook_env, **dict(env)})
        assert rc == (2 if finding_after else 0)
        run.row = metrics_of(out)
        return set(re.findall(r"MARK_\w+", "".join(stub_api.bodies)))
    return run


def commit_tree_of(repo):
    """A commit of the tracked files as they are, as a hook's snapshot is."""
    return git(repo, "stash", "create").strip()


def write(repo, name, mark):
    with open(repo / name, "a") as f:
        f.write(f"{mark} = 1\n")


@pytest.mark.parametrize("name", ["app.py", "new.py"])
def test_changes_with_a_finding_are_not_reviewed_again(repo, hook_env, stop, name):
    run_hook(ups_payload(repo), hook_env)
    write(repo, name, "MARK_first")
    assert stop(lambda: None) == {"MARK_first"}
    assert stop() == set()


@pytest.mark.parametrize("name", ["lib.py", "new.py"])
def test_later_change_goes_to_the_next_review(repo, hook_env, stop, name):
    run_hook(ups_payload(repo), hook_env)
    write(repo, "app.py", "MARK_first")
    assert stop(lambda: write(repo, name, "MARK_second")) == {"MARK_first"}
    assert stop() == {"MARK_second"}


def test_later_commit_goes_to_the_next_review(repo, hook_env, stop):
    run_hook(ups_payload(repo), hook_env)
    write(repo, "app.py", "MARK_first")
    stop(lambda: commit_file(repo, "lib.py", "MARK_second = 1\n"))
    assert stop() == {"MARK_second"}


def test_baseline_of_a_later_prompt_stays(repo, hook_env, stop):
    def next_turn():
        write(repo, "new.py", "MARK_between")
        run_hook(ups_payload(repo), hook_env)
        write(repo, "lib.py", "MARK_second")
        run_hook(edit_payload(repo, repo / "lib.py"), hook_env)
    run_hook(ups_payload(repo), hook_env)
    write(repo, "app.py", "MARK_first")
    stop(next_turn)
    assert stop() == {"MARK_second"}


def test_later_change_in_another_checkout_goes_to_the_next_review(repo, hook_env, stop, tmp_path):
    other = make_repo(tmp_path / "other", {"app.py": "a = 1\n", "lib.py": "b = 1\n"})
    run_hook(ups_payload(repo), hook_env)
    write(other, "app.py", "MARK_first")
    stop(lambda: write(other, "lib.py", "MARK_second"), cwd=other)
    assert stop(cwd=other) == {"MARK_second"}
    assert stop.row["bl_origin"] == 0


def on_command(hook_env, tmp_path, words, before=":", after=":"):
    """Have git run a shell command before or after each call with `words`."""
    shim = tmp_path / "bin"
    shim.mkdir()
    (shim / "git").write_text(
        f'#!/bin/sh\ncase "$*" in *"{words}"*) {before}; "{shutil.which("git")}" "$@"; '
        f'rc=$?; {after}; exit $rc;; esac\n'
        f'exec "{shutil.which("git")}" "$@"\n')
    (shim / "git").chmod(0o755)
    hook_env["PATH"] = f"{shim}{os.pathsep}{hook_env['PATH']}"


def on_snapshot(hook_env, tmp_path, command):
    """Have git run the shell `command` as it starts a snapshot."""
    on_command(hook_env, tmp_path, "add -u", before=command)


@posix_only
def test_change_just_before_the_snapshot_is_in_this_review(repo, hook_env, stop, tmp_path):
    run_hook(ups_payload(repo), hook_env)
    write(repo, "app.py", "MARK_first")
    on_snapshot(hook_env, tmp_path, f'echo "MARK_second = 1" >> "{repo}/lib.py"')
    assert stop(lambda: None) == {"MARK_first", "MARK_second"}


@posix_only
def test_file_that_goes_before_the_second_listing(repo, hook_env, stop, tmp_path):
    run_hook(ups_payload(repo), hook_env)
    write(repo, "app.py", "MARK_first")
    write(repo, "passing.py", "MARK_passing")
    on_snapshot(hook_env, tmp_path, f'rm -f "{repo}/passing.py"')
    assert stop(lambda: None) == {"MARK_first"}
    assert stop() == set()


@posix_only
def test_file_written_after_the_listing_is_reviewed_once(repo, hook_env, stop, tmp_path):
    run_hook(ups_payload(repo), hook_env)
    write(repo, "app.py", "MARK_first")
    on_command(hook_env, tmp_path, "ls-files --others",
               after=f'[ -e "{repo}/new.py" ] || echo "MARK_new = 1" > "{repo}/new.py"')
    assert stop(lambda: None) == {"MARK_first", "MARK_new"}
    assert stop() == set()


@posix_only
def test_second_listing_that_fails_leaves_the_review_as_it_was(repo, hook_env, stop, tmp_path):
    run_hook(ups_payload(repo), hook_env)
    write(repo, "app.py", "MARK_first")
    on_snapshot(hook_env, tmp_path, f'echo >> "{tmp_path}/taken"')
    shim = tmp_path / "bin" / "git"
    shim.write_text(shim.read_text().replace("exec ", f'case "$*" in *"status --porcelain"*) '
                    f'[ -e "{tmp_path}/taken" ] && exit 128;; esac\nexec '))
    assert stop(lambda: None) == {"MARK_first"}
    assert (tmp_path / "taken").exists()


@pytest.mark.parametrize("bad", ["x", [], None])
def test_unusable_time_in_the_state_does_not_lose_the_finding(repo, hook_env, stop, bad):
    run_hook(ups_payload(repo), hook_env)
    path = next(Path(hook_env["SECURITY_WARNINGS_STATE_DIR"]).glob("security_warnings_state_*.json"))
    path.write_text(json.dumps({**json.loads(path.read_text()), "baseline_at": bad}))
    write(repo, "app.py", "MARK_first")
    assert stop(lambda: None) == {"MARK_first"}
    assert stop() == set()


def test_prompt_in_another_checkout_meanwhile_keeps_its_baseline(repo, hook_env, stop, tmp_path):
    other = make_repo(tmp_path / "other", {"app.py": "a = 1\n"})
    run_hook(ups_payload(repo), hook_env)
    write(repo, "app.py", "MARK_first")
    assert stop(lambda: run_hook(ups_payload(other), hook_env)) == {"MARK_first"}
    path = next(Path(hook_env["SECURITY_WARNINGS_STATE_DIR"]).glob("security_warnings_state_*.json"))
    assert os.path.samefile(json.loads(path.read_text())["baseline_root"], other)


@posix_only
def test_turn_without_changes_takes_no_snapshot(repo, hook_env, stop, tmp_path):
    run_hook(ups_payload(repo), hook_env)
    on_snapshot(hook_env, tmp_path, f'echo >> "{tmp_path}/taken"')
    assert stop() == set()
    assert not (tmp_path / "taken").exists()


def test_prompt_that_took_no_baseline_does_not_hold_the_new_one_back(
        repo, hook_env, stop, tmp_path):
    plain = tmp_path / "plain"
    plain.mkdir()
    run_hook(ups_payload(repo), hook_env)
    write(repo, "app.py", "MARK_first")
    assert stop(lambda: run_hook(ups_payload(plain), hook_env)) == {"MARK_first"}
    assert stop() == set()


@posix_only
def test_no_snapshot_when_nothing_changed_is_reviewable(repo, hook_env, stop, tmp_path):
    run_hook(ups_payload(repo), hook_env)
    write(repo, "notes.md", "MARK_notes")
    on_snapshot(hook_env, tmp_path, f'echo >> "{tmp_path}/taken"')
    assert stop() == set()
    assert not (tmp_path / "taken").exists()


def test_newest_baseline_stays(repo, hook_env, stop):
    """Another Stop review of the same turn stored its own while this one ran."""
    def stored_meanwhile():
        write(repo, "lib.py", "MARK_second")
        state = json.loads(state_file.read_text())
        state_file.write_text(json.dumps(
            {**state, "baseline_sha": later, "baseline_at": time.time()}))
    run_hook(ups_payload(repo), hook_env)
    state_file = next(Path(hook_env["SECURITY_WARNINGS_STATE_DIR"]).glob("security_warnings_state_*.json"))
    write(repo, "app.py", "MARK_first")
    later = commit_tree_of(repo)
    stop(stored_meanwhile)
    assert json.loads(state_file.read_text())["baseline_sha"] == later
    assert stop() == {"MARK_second"}


def test_reviewed_file_past_the_listing_cap_is_not_reviewed_again(repo, hook_env, stop):
    for i in range(2005):
        (repo / f"a{i:04}.txt").write_text("x")
    run_hook(ups_payload(repo), hook_env)
    write(repo, "zz.py", "MARK_first")
    assert stop(lambda: None) == {"MARK_first"}
    assert stop() == set()
