"""Reviews report whether their diff was reviewed before; nothing is skipped."""
from conftest import bash_payload, commit_file, git, make_repo, metrics_of, run_hook

import diffstate

import pytest

DIFF = [("handlers.py", "@@ -0,0 +1,2 @@\n+def h(x):\n+    return x")]


@pytest.fixture(autouse=True)
def _claude_code_output(monkeypatch):
    # diffstate reads the output mode from the test runner's environment.
    monkeypatch.setattr(diffstate, "portable_output", lambda: False)


def _reviews(stub_api):
    return [c for c in stub_api.calls if c.endswith("/v1/messages")]


def _records(repo):
    p = repo / ".git" / "sg-reviewed-diffs"
    return p.read_text().splitlines() if p.exists() else []


def _recommit(repo, msg):
    git(repo, "reset", "-q", "--soft", "HEAD~1")
    out = git(repo, "commit", "-m", msg)
    return git(repo, "rev-parse", "HEAD").strip(), out


def _seen(repo, diff=DIFF):
    return diffstate._diff_review_started(str(repo), diff)


def _finished(repo, diff=DIFF):
    token, _ = _seen(repo, diff)
    diffstate._diff_review_done(token)


def _hunk(start, context, added):
    return f"@@ -{start},2 +{start},3 @@ def f():\n {context}\n+{added}\n pass"


def test_first_review_of_a_diff_is_not_seen(tmp_path):
    repo = make_repo(tmp_path / "repo", {"app.py": "print('hi')\n"})
    token, m = _seen(repo)
    assert m == {"diff_seen": diffstate.DIFF_SEEN_NO}
    assert token and len(_records(repo)) == 1


def test_unfinished_then_finished_on_same_then_other_tree(tmp_path):
    repo = make_repo(tmp_path / "repo", {"app.py": "print('hi')\n"})
    token, _ = _seen(repo)
    assert _seen(repo)[1] == {"diff_seen": diffstate.DIFF_SEEN_UNFINISHED}
    diffstate._diff_review_done(token)
    assert _seen(repo)[1] == {"diff_seen": diffstate.DIFF_SEEN_SAME_TREE}
    commit_file(repo, "other.py", "x = 1\n")
    assert _seen(repo)[1] == {"diff_seen": diffstate.DIFF_SEEN_OTHER_TREE}


def test_tree_is_the_reviewed_commits_not_where_head_went(tmp_path):
    repo = make_repo(tmp_path / "repo", {"app.py": "print('hi')\n"})
    sha, _ = commit_file(repo, "handlers.py", "def h(x):\n    return x\n")
    token, _ = diffstate._diff_review_started(str(repo), DIFF, tip=sha)
    diffstate._diff_review_done(token)
    git(repo, "reset", "-q", "--hard", "HEAD~1")
    assert _seen(repo)[1] == {"diff_seen": diffstate.DIFF_SEEN_OTHER_TREE}
    assert diffstate._diff_review_started(str(repo), DIFF, tip=sha)[1] == {
        "diff_seen": diffstate.DIFF_SEEN_SAME_TREE}


def test_a_different_change_path_or_place_is_not_seen(tmp_path):
    repo = make_repo(tmp_path / "repo", {"app.py": "print('hi')\n"})
    one = [("auth.py", _hunk(3, "def login():", "return True"))]
    _finished(repo, one)
    for other in ([("auth.py", _hunk(3, "def login():", "return False"))],
                  [("other.py", one[0][1])],
                  # The same added line next to different code.
                  [("auth.py", _hunk(3, "def is_admin():", "return True"))],
                  one + [("b.py", "@@ -0,0 +1 @@\n+1")]):
        assert _seen(repo, other)[1] == {"diff_seen": diffstate.DIFF_SEEN_NO}


def test_a_moved_hunk_keeps_its_key(tmp_path):
    repo = make_repo(tmp_path / "repo", {"app.py": "print('hi')\n"})
    _finished(repo, [("auth.py", _hunk(3, "def login():", "return True"))])
    moved = "@@ -40,2 +44,3 @@ class A:\n def login():\n+return True\n pass"
    assert _seen(repo, [("auth.py", moved)])[1] == {"diff_seen": diffstate.DIFF_SEEN_SAME_TREE}


def test_real_diffs_of_two_commits_match_their_net_diff(tmp_path):
    from gitutil import parse_diff_into_files
    body = "".join(f"line {i}\n" for i in range(60))
    repo = make_repo(tmp_path / "repo", {"app.py": body})
    base = git(repo, "rev-parse", "HEAD").strip()
    commit_file(repo, "app.py", body.replace("line 5\n", "line 5\nx = 1\n"))
    _finished(repo, parse_diff_into_files(git(repo, "show", "-p", "HEAD")))
    commit_file(repo, "app.py", body.replace("line 5\n", "line 5\nx = 1\n")
                .replace("line 50\n", "line 50\ny = 2\n"))
    _finished(repo, parse_diff_into_files(git(repo, "show", "-p", "HEAD")))
    net = parse_diff_into_files(git(repo, "diff", base, "HEAD"))
    assert len(diffstate._hunk_keys(net)) == 2
    # Both hunks had a finished review; the first one on an older tree.
    assert _seen(repo, net)[1] == {"diff_seen": diffstate.DIFF_SEEN_OTHER_TREE}


def test_hunks_past_the_key_cap_are_not_dropped(tmp_path, monkeypatch):
    repo = make_repo(tmp_path / "repo", {"app.py": "print('hi')\n"})
    monkeypatch.setattr(diffstate, "_SEEN_DIFFS_MAX_KEYS", 3)
    hunks = [_hunk(10 * i, f"def f{i}():", f"x = {i}") for i in range(6)]
    _finished(repo, [("app.py", "\n".join(hunks[:5]))])
    assert len(_records(repo)[0].split("\t")[3].split(" ")) == 3
    assert _seen(repo, [("app.py", "\n".join(hunks))])[1] == {"diff_seen": diffstate.DIFF_SEEN_NO}
    assert _seen(repo, [("app.py", "\n".join(hunks[:5]))])[1] == {
        "diff_seen": diffstate.DIFF_SEEN_SAME_TREE}


def test_removed_sql_comment_lines_tell_diffs_apart(tmp_path):
    repo = make_repo(tmp_path / "repo", {"app.py": "print('hi')\n"})
    _finished(repo, [("q.sql", "@@ -1,2 +1 @@\n--- drop table users;\n select 1;")])
    other = [("q.sql", "@@ -1,2 +1 @@\n--- drop table orders;\n select 1;")]
    assert _seen(repo, other)[1] == {"diff_seen": diffstate.DIFF_SEEN_NO}


def test_commits_reviewed_one_by_one_then_as_one_net_diff(tmp_path):
    # Two commit reviews of the same file, then a push review of their net diff.
    repo = make_repo(tmp_path / "repo", {"app.py": "print('hi')\n"})
    h1, h2 = _hunk(3, "def a():", "x = 1"), _hunk(90, "def z():", "y = 2")
    _finished(repo, [("app.py", h1)])
    net = [("app.py", h1 + "\n" + h2), ("b.py", "@@ -0,0 +1 @@\n+b = 2")]
    assert _seen(repo, net)[1] == {"diff_seen": diffstate.DIFF_SEEN_NO}
    _finished(repo, [("app.py", h2)])
    _finished(repo, [net[1]])
    assert _seen(repo, net)[1] == {"diff_seen": diffstate.DIFF_SEEN_SAME_TREE}


def test_old_records_do_not_count(tmp_path, monkeypatch):
    repo = make_repo(tmp_path / "repo", {"app.py": "print('hi')\n"})
    _finished(repo)
    monkeypatch.setattr(diffstate, "_SEEN_DIFFS_TTL_S", -1)
    assert _seen(repo)[1] == {"diff_seen": diffstate.DIFF_SEEN_NO}


@pytest.mark.parametrize("flock", [True, False])
def test_record_is_cut_back_to_its_newest_rows(tmp_path, monkeypatch, flock):
    repo = make_repo(tmp_path / "repo", {"app.py": "print('hi')\n"})
    if not flock:
        def no_flock(fd, exclusive):
            raise ImportError("fcntl")
        monkeypatch.setattr(diffstate, "_flock_nb", no_flock)
    _finished(repo)
    row = len(_records(repo)[0]) + 1
    monkeypatch.setattr(diffstate, "_SEEN_DIFFS_TRIM_BYTES", 6 * row)
    for i in range(12):
        _finished(repo, [("f.py", f"@@ -0,0 +1 @@\n+{i}")])
    rows = _records(repo)
    assert 3 <= len(rows) <= 6
    assert rows[-1].split("\t")[2:] == ["1", diffstate._hunk_keys([("f.py", "@@ -0,0 +1 @@\n+11")])[0]]
    assert _seen(repo, [("f.py", "@@ -0,0 +1 @@\n+11")])[1]["diff_seen"] == diffstate.DIFF_SEEN_SAME_TREE
    assert _seen(repo)[1] == {"diff_seen": diffstate.DIFF_SEEN_NO}


def test_damaged_record_is_read_around_and_shrinks(tmp_path, monkeypatch):
    repo = make_repo(tmp_path / "repo", {"app.py": "print('hi')\n"})
    p = repo / ".git" / "sg-reviewed-diffs"
    p.write_bytes(b"\xff\xfe garbage\nshort\tline\n" + b"9" * 5000 + b"\tt\t1\tk\n"
                  + b"x" * 5000)
    monkeypatch.setattr(diffstate, "_SEEN_DIFFS_TRIM_BYTES", 2000)
    token, m = _seen(repo)
    assert m == {"diff_seen": diffstate.DIFF_SEEN_NO}
    diffstate._diff_review_done(token)
    assert p.stat().st_size < 2000
    assert _seen(repo)[1] == {"diff_seen": diffstate.DIFF_SEEN_SAME_TREE}


def test_a_lock_another_process_keeps_is_not_waited_on(tmp_path, monkeypatch):
    repo = make_repo(tmp_path / "repo", {"app.py": "print('hi')\n"})
    token, _ = _seen(repo)
    monkeypatch.setattr(diffstate, "_flock_nb", lambda fd, exclusive: False)
    monkeypatch.setattr(diffstate, "_SEEN_DIFFS_LOCK_TRIES", 2)
    monkeypatch.setattr(diffstate, "_SEEN_DIFFS_TRIM_BYTES", 0)
    # A start that cannot read the record under the lock does not guess.
    assert _seen(repo) == (None, {"diff_seen": diffstate.DIFF_SEEN_ERROR})
    # A verdict is still noted, and the record is not cut back without the lock.
    diffstate._diff_review_done(token)
    assert [r.split("\t")[2] for r in _records(repo)] == ["0", "1"]


def test_failures_are_reported_and_never_raise(tmp_path):
    assert _seen(tmp_path / "nope") == (None, {"diff_seen": diffstate.DIFF_SEEN_ERROR})
    diffstate._diff_review_done(None)
    repo = make_repo(tmp_path / "repo", {"app.py": "print('hi')\n"})
    (repo / ".git" / "sg-reviewed-diffs").mkdir()
    assert _seen(repo) == (None, {"diff_seen": diffstate.DIFF_SEEN_ERROR})
    diffstate._diff_review_done((str(repo / ".git" / "sg-reviewed-diffs"), ["k"], "t"))


def test_a_record_that_cannot_be_written_is_an_error_not_unseen(tmp_path, monkeypatch):
    repo = make_repo(tmp_path / "repo", {"app.py": "print('hi')\n"})
    def full_disk(f, locked, token, done):
        raise OSError(28, "No space left on device")
    monkeypatch.setattr(diffstate, "_append_diff_row", full_disk)
    assert _seen(repo) == (None, {"diff_seen": diffstate.DIFF_SEEN_ERROR})


def test_nothing_is_recorded_in_portable_output_mode(tmp_path, monkeypatch):
    repo = make_repo(tmp_path / "repo", {"app.py": "print('hi')\n"})
    monkeypatch.setattr(diffstate, "portable_output", lambda: True)
    assert _seen(repo) == (None, {})
    assert _records(repo) == []


def test_recommit_of_the_same_change_is_reviewed_again_and_counted(tmp_path, hook_env, stub_api):
    repo = make_repo(tmp_path / "repo", {"app.py": "print('hi')\n"})
    sha, out = commit_file(repo, "handlers.py", "def h(x):\n    return x\n")
    rc, so, _ = run_hook(bash_payload(repo, "git commit -m change", out), hook_env)
    first = metrics_of(so)
    assert rc == 0 and first["diff_seen"] == diffstate.DIFF_SEEN_NO

    sha2, out2 = _recommit(repo, "same change again")
    assert sha2 != sha
    rc, so, _ = run_hook(bash_payload(repo, "git commit -m 'same change again'", out2), hook_env)
    second = metrics_of(so)
    assert rc == 0 and second["diff_seen"] == diffstate.DIFF_SEEN_SAME_TREE
    # Last in the row, so a row over the key cap loses this and nothing older.
    assert list(second)[-1] == "diff_seen"
    # Count only: both commits were reviewed and recorded.
    assert len(_reviews(stub_api)) == 2
    assert {sha, sha2} <= diffstate._load_reviewed_shas(str(repo))


def test_push_of_a_rebased_reviewed_commit_is_counted(tmp_path, hook_env, stub_api):
    repo = make_repo(tmp_path / "repo", {"app.py": "print('hi')\n"})
    remote = tmp_path / "remote.git"
    git(tmp_path, "init", "-q", "--bare", str(remote))
    git(repo, "remote", "add", "origin", str(remote))
    git(repo, "push", "-q", "-u", "origin", "main")
    git(repo, "checkout", "-q", "-b", "feat")
    sha, out = commit_file(repo, "handlers.py", "def h(x):\n    return x\n")
    run_hook(bash_payload(repo, "git commit -m change", out), hook_env)

    git(repo, "checkout", "-q", "main")
    commit_file(repo, "notes.md", "notes\n")
    git(repo, "push", "-q", "origin", "main")
    git(repo, "checkout", "-q", "feat")
    git(repo, "rebase", "-q", "main")
    git(repo, "push", "-q", "-u", "origin", "feat")
    push_out = f"To {remote}\n * [new branch]      feat -> feat\n"
    rc, so, _ = run_hook(bash_payload(repo, "git push -u origin feat", push_out), hook_env)
    m = metrics_of(so)
    assert rc == 0 and m["push_sweep"] is True and m["unreviewed"] == 1
    assert m["diff_seen"] == diffstate.DIFF_SEEN_OTHER_TREE and list(m)[-1] == "diff_seen"
    assert len(_reviews(stub_api)) == 2


def test_failed_review_leaves_the_diff_unfinished(tmp_path, hook_env, stub_api):
    repo = make_repo(tmp_path / "repo", {"app.py": "print('hi')\n"})
    sha, out = commit_file(repo, "handlers.py", "def h(x):\n    return x\n")
    stub_api.status = 500
    rc, so, _ = run_hook(bash_payload(repo, "git commit -m change", out), hook_env)
    failed = metrics_of(so)
    assert failed["review_failed"] is True and failed["diff_seen"] == diffstate.DIFF_SEEN_NO

    stub_api.status = 200
    sha2, out2 = _recommit(repo, "same change again")
    rc, so, _ = run_hook(bash_payload(repo, "git commit -m 'same change again'", out2), hook_env)
    assert metrics_of(so)["diff_seen"] == diffstate.DIFF_SEEN_UNFINISHED
