"""A push whose tip is a merge reviews what the push added, not the rest of main."""
import json
import os
import subprocess

import pytest

from conftest import GIT_ENV, bash_payload, commit_file, git, make_repo, metrics_of, run_hook

import diffstate
import gitutil
import security_reminder_hook as hook


def _record_reviewed(repo, *shas):
    diffstate._append_reviewed_shas(str(repo), list(shas))


def _forward_repo(tmp_path):
    """main holds work the release branch lacks; both are on the remote."""
    repo = make_repo(tmp_path / "repo", {"app.py": "a = 1\n"})
    remote = tmp_path / "remote.git"
    git(tmp_path, "init", "-q", "--bare", str(remote))
    git(repo, "remote", "add", "origin", str(remote))
    git(repo, "push", "-q", "-u", "origin", "main")
    git(repo, "branch", "release")
    commit_file(repo, "future.py", "main_only = 1\n")
    git(repo, "push", "-q", "origin", "main")
    git(repo, "switch", "-q", "release")
    return repo, remote


def _on_release(repo, name):
    sha, _ = commit_file(repo, name, f"{name[:-3]} = 1\n")
    git(repo, "push", "-q", "origin", "release")
    return sha


def _merge_forward(repo):
    git(repo, "switch", "-q", "-c", "fwd", "main")
    git(repo, "merge", "-q", "--no-ff", "--no-edit", "origin/release")
    return git(repo, "rev-parse", "HEAD").strip()


def _merge_with_conflict(repo, ref):
    """Start a merge and check that it stopped on a conflict, not on some
    other refusal: exit 1 with the merge still open."""
    r = subprocess.run(["git", "merge", "--no-ff", "--no-edit", ref], cwd=repo,
                       capture_output=True, env={**os.environ, **GIT_ENV})
    assert r.returncode == 1 and (repo / ".git" / "MERGE_HEAD").exists(), r.stderr


def _push_fwd(repo, remote, env):
    git(repo, "push", "-q", "-u", "origin", "fwd")
    out = f"To {remote}\n * [new branch]      fwd -> fwd\n"
    return run_hook(bash_payload(repo, "git push -u origin fwd", out), env)


def _reviewed_text(stub_api):
    return [json.dumps(b) for b, c in zip(stub_api.bodies, stub_api.calls)
            if c.endswith("/v1/messages")]


def test_clean_forward_merge_of_reviewed_commits_needs_no_review(tmp_path, hook_env, stub_api):
    repo, remote = _forward_repo(tmp_path)
    fix = _on_release(repo, "fix.py")
    _record_reviewed(repo, fix)
    merge = _merge_forward(repo)

    rc, so, _ = _push_fwd(repo, remote, hook_env)

    m = metrics_of(so)
    assert rc == 0 and m["merges_settled"] == 1 and m["skip_reason"] == 30
    assert _reviewed_text(stub_api) == []
    assert merge in diffstate._load_reviewed_shas(str(repo))


def test_conflict_resolution_is_still_reviewed(tmp_path, hook_env, stub_api):
    repo, remote = _forward_repo(tmp_path)
    git(repo, "switch", "-q", "main")
    commit_file(repo, "app.py", "a = 2\n")
    git(repo, "push", "-q", "origin", "main")
    git(repo, "switch", "-q", "release")
    fix, _ = commit_file(repo, "app.py", "a = 3\n")
    other, _ = commit_file(repo, "fix.py", "fix = 1\n")
    git(repo, "push", "-q", "origin", "release")
    _record_reviewed(repo, fix, other)
    git(repo, "switch", "-q", "-c", "fwd", "main")
    _merge_with_conflict(repo, "origin/release")
    (repo / "app.py").write_text("a = resolved_by_hand\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "--no-edit")

    rc, so, _ = _push_fwd(repo, remote, hook_env)

    m = metrics_of(so)
    assert rc == 0 and m["merges_settled"] == 1 and m["files_reviewed"] == 1
    sent = _reviewed_text(stub_api)
    assert sent and all("resolved_by_hand" in t and "@@@" in t for t in sent)
    assert not any("future.py" in t or "fix.py" in t for t in sent)


def test_unreadable_merge_is_not_settled(tmp_path, monkeypatch):
    monkeypatch.setattr(hook, "_git_merge_resolved_files", lambda *a: None)
    assert hook._merge_resolved_diff_files(str(tmp_path), ["x"]) is None


def test_edit_after_a_merge_keeps_both_diffs(tmp_path, hook_env, stub_api):
    repo, remote = _forward_repo(tmp_path)
    git(repo, "switch", "-q", "main")
    commit_file(repo, "app.py", "a = 2\n")
    git(repo, "push", "-q", "origin", "main")
    git(repo, "switch", "-q", "release")
    fix, _ = commit_file(repo, "app.py", "a = 3\n")
    git(repo, "push", "-q", "origin", "release")
    _record_reviewed(repo, fix)
    git(repo, "switch", "-q", "-c", "fwd", "main")
    _merge_with_conflict(repo, "origin/release")
    (repo / "app.py").write_text("a = resolved_by_hand\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "--no-edit")
    commit_file(repo, "app.py", "a = resolved_by_hand\nb = later_edit\n")

    rc, so, _ = _push_fwd(repo, remote, hook_env)

    m = metrics_of(so)
    assert rc == 0 and m["files_reviewed"] == 1
    sent = _reviewed_text(stub_api)
    assert sent and all("resolved_by_hand" in t and "later_edit" in t for t in sent)


def test_hand_edit_in_a_merge_is_reviewed(tmp_path, hook_env, stub_api):
    repo, remote = _forward_repo(tmp_path)
    _record_reviewed(repo, _on_release(repo, "fix.py"))
    _merge_forward(repo)
    (repo / "extra.py").write_text("added_in_merge = 1\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "--amend", "--no-edit")

    rc, so, _ = _push_fwd(repo, remote, hook_env)

    sent = _reviewed_text(stub_api)
    assert rc == 0 and sent and all("added_in_merge" in t for t in sent)
    assert not any("future.py" in t for t in sent)


def test_unreviewed_merged_side_is_reviewed(tmp_path, hook_env, stub_api):
    repo, remote = _forward_repo(tmp_path)
    _on_release(repo, "fix.py")
    _merge_forward(repo)

    rc, so, _ = _push_fwd(repo, remote, hook_env)

    m = metrics_of(so)
    assert rc == 0 and "merges_settled" not in m and m["files_reviewed"] == 1
    sent = _reviewed_text(stub_api)
    assert sent and all("fix.py" in t for t in sent)
    assert not any("future.py" in t for t in sent)


def test_partly_reviewed_side_does_not_pull_in_main(tmp_path, hook_env, stub_api):
    repo, remote = _forward_repo(tmp_path)
    _record_reviewed(repo, _on_release(repo, "fix.py"))
    _on_release(repo, "second.py")
    _merge_forward(repo)

    rc, so, _ = _push_fwd(repo, remote, hook_env)

    sent = _reviewed_text(stub_api)
    assert rc == 0 and sent and all("second.py" in t for t in sent)
    assert not any("future.py" in t for t in sent)


def test_commit_after_a_settled_merge_is_reviewed_alone(tmp_path, hook_env, stub_api):
    repo, remote = _forward_repo(tmp_path)
    _record_reviewed(repo, _on_release(repo, "fix.py"))
    _merge_forward(repo)
    commit_file(repo, "after.py", "after_merge = 1\n")

    rc, so, _ = _push_fwd(repo, remote, hook_env)

    m = metrics_of(so)
    assert rc == 0 and m["merges_settled"] == 1 and m["files_reviewed"] == 1
    sent = _reviewed_text(stub_api)
    assert sent and all("after_merge" in t for t in sent)
    assert not any("future.py" in t or "fix.py" in t for t in sent)


def test_linear_push_keeps_its_base(tmp_path, hook_env, stub_api):
    repo, remote = _forward_repo(tmp_path)
    before = git(repo, "rev-parse", "HEAD").strip()
    first, _ = commit_file(repo, "one.py", "one = 1\n")
    _record_reviewed(repo, first)
    tip, _ = commit_file(repo, "two.py", "two = 1\n")
    git(repo, "push", "-q", "origin", "release")
    out = f"To {remote}\n   {before[:7]}..{tip[:7]}  release -> release\n"

    rc, so, _ = run_hook(bash_payload(repo, "git push origin release", out), hook_env)

    m = metrics_of(so)
    assert rc == 0 and m["prefix_advanced"] == 1 and "merges_settled" not in m
    sent = _reviewed_text(stub_api)
    assert sent and all("two.py" in t and "one.py" not in t for t in sent)


def _parents(**rows):
    return {k: v.split() for k, v in rows.items()}


@pytest.mark.parametrize("range_, reviewed, parents, want", [
    # The issue's shape: the reviewed prefix ends on the merged-in branch.
    (["r1", "r2", "M"], {"r1", "r2"}, _parents(r1="o", r2="r1", M="p r2"), ("M", ["M"])),
    # A reviewed commit on the first-parent line is a valid base.
    (["c", "r", "M"], {"c"}, _parents(c="p", r="o", M="c r"), ("c", [])),
    (["c", "r", "M"], {"c", "r"}, _parents(c="p", r="o", M="c r"), ("M", ["M"])),
    # Nothing reviewed before the merge.
    (["r", "M"], set(), _parents(r="o", M="p r"), ("prev", [])),
    # A merge on the merged-in side is not settled.
    (["s", "m2", "M"], {"s"}, _parents(s="o", m2="s q", M="p m2"), ("prev", [])),
    # Merges one after another.
    (["r", "M1", "M2"], {"r"}, _parents(r="o", M1="p r", M2="M1 o"), ("M2", ["M1", "M2"])),
])
def test_base_with_merges(range_, reviewed, parents, want):
    assert hook._push_sweep_base_with_merges("prev", range_, reviewed, parents) == want


def test_cleanly_merged_file_is_not_called_resolved(tmp_path):
    repo = make_repo(tmp_path / "repo", {"both.py": "".join(f"l{i}\n" for i in range(12))})
    git(repo, "switch", "-q", "-c", "side")
    commit_file(repo, "both.py", "first\n" + "".join(f"l{i}\n" for i in range(1, 12)))
    git(repo, "switch", "-q", "main")
    commit_file(repo, "both.py", "".join(f"l{i}\n" for i in range(11)) + "last\n")
    git(repo, "merge", "-q", "--no-ff", "--no-edit", "side")
    head = git(repo, "rev-parse", "HEAD").strip()
    assert gitutil._git_merge_resolved_files(str(repo), head) == []


@pytest.mark.skipif(os.name == "nt", reason='file names cannot hold " on Windows')
def test_resolved_path_with_a_quote(tmp_path):
    name = 'we"ird.py'
    repo = make_repo(tmp_path / "repo", {name: "base\n"})
    git(repo, "switch", "-q", "-c", "side")
    commit_file(repo, name, "side\n")
    git(repo, "switch", "-q", "main")
    commit_file(repo, name, "main\n")
    _merge_with_conflict(repo, "side")
    (repo / name).write_text("resolved\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "--no-edit")
    head = git(repo, "rev-parse", "HEAD").strip()
    assert [p for p, _ in gitutil._git_merge_resolved_files(str(repo), head)] == [name]
