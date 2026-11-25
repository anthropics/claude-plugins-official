"""The commit and push reviews read `git show` / `git diff` without holding it:
a file keeps what the review sends of it, and a diff they give up on for its
file count is only counted."""
import random
import subprocess
import tracemalloc

import pytest

from conftest import (
    GIT_ENV, VULN_PY, bash_payload, commit_file, git, make_repo, metrics_of, run_hook,
)

import gitutil


@pytest.fixture(autouse=True)
def _fresh_read_state():
    def reset():
        gitutil._unparsed_diff_headers.clear()
        gitutil._diff_read.update(bytes=0, cut_files=0, cut_bytes=0, timeouts=0)

    reset()
    yield
    reset()


def _section(path, body_lines, old=None, extra=""):
    return (f"diff --git a/{old or path} b/{path}\n" + extra
            + "index 1111111..2222222 100644\n"
            f"--- a/{old or path}\n+++ b/{path}\n"
            f"@@ -1,2 +1,{len(body_lines)} @@\n"
            + "".join(f"+{ln}\n" for ln in body_lines))


def _rename(old, new):
    return (f"diff --git a/{old} b/{new}\nsimilarity index 100%\n"
            f"rename from {old}\nrename to {new}\n")


def _empty(path):
    return f"diff --git a/{path} b/{path}\nnew file mode 100644\nindex 0000000..e69de29\n"


PREAMBLE = "commit 1111111\nAuthor: t <t@example.com>\n\n    message\n\n"


FILE_CHARS = 80000


def _keep(raw, max_files, rng=None, file_chars=FILE_CHARS):
    keeper = gitutil._ReviewDiffKeeper(max_files, file_chars)
    pos = 0
    while pos < len(raw):
        n = rng.choice([1, 2, 7, 13, 64, 500, 4096]) if rng else 4096
        keeper.feed(raw[pos:pos + n])
        pos += n
    return keeper, keeper.result().decode(errors="replace")


def _raw_keep(raw, max_files, file_chars):
    keeper = gitutil._ReviewDiffKeeper(max_files, file_chars)
    keeper.feed(raw)
    return keeper.result()


def _random_diff(rng):
    out = [PREAMBLE]
    for i in range(rng.randrange(1, 30)):
        kind = rng.randrange(6)
        name = rng.choice(["a/b%d.py", "café%d.js", "x y%d.ts", "data%d.csv", "n%d.txt"]) % i
        if kind == 0:
            out.append(_rename(f"old{i}.txt", name))
        elif kind == 1:
            out.append(_empty(name))
        elif kind == 2:
            out.append(_section(name, ["x = 1"], old=f"old{i}.md",
                                extra=f"similarity index 90%\nrename from old{i}.md\nrename to {name}\n"))
        else:
            out.append(_section(name, ["l%d" % rng.randrange(99)] * rng.randrange(1, 60)))
    return "".join(out).encode()


class TestFileLimit:
    @pytest.mark.parametrize("seed", range(40))
    def test_same_files_as_reading_it_whole(self, seed):
        rng = random.Random(seed)
        raw = _random_diff(rng)
        want = gitutil.parse_diff_into_files(raw.decode())
        keeper, kept = _keep(raw, 300, rng)
        assert gitutil.parse_diff_into_files(kept) == want
        assert keeper.seen == len(raw)

    @pytest.mark.parametrize("seed", range(20))
    def test_past_the_limit_the_same_files_are_still_counted(self, seed):
        rng = random.Random(seed)
        raw = _random_diff(rng)
        want = gitutil.parse_diff_into_files(raw.decode())
        _, kept = _keep(raw, 3, rng)
        got = gitutil.parse_diff_into_files(kept)
        assert [p for p, _ in got] == [p for p, _ in want]
        if len(want) <= 3:
            assert got == want

    @pytest.mark.parametrize("lines", [5000, 2])
    def test_past_the_limit_almost_nothing_is_kept(self, lines):
        body = ["value = %d" % i for i in range(lines)]
        raw = "".join(_section(f"m{i}.py", body) for i in range(60)).encode()
        keeper, kept = _keep(raw, 5)
        assert len(gitutil.parse_diff_into_files(kept)) == 60
        assert len(kept) < 60 * 130

    @pytest.mark.parametrize("text", ["plain ascii text", "текст", "日本語の行", "status \U0001F680", "caf\u00e9"])
    @pytest.mark.parametrize("cap", [50, 1000])
    def test_a_file_keeps_what_the_review_sends(self, text, cap):
        """The prompt takes the first `cap` characters and marks a longer file
        as cut, so a longer file must stay longer."""
        raw = (_section("big.py", [text] * 1000) + _section("after.py", ["x"])).encode()
        for chunk in (None, random.Random(1)):
            _, kept = _keep(raw, 300, chunk, file_chars=cap)
            got = dict(gitutil.parse_diff_into_files(kept))
            want = dict(gitutil.parse_diff_into_files(raw.decode()))
            assert got["big.py"][:cap] == want["big.py"][:cap]
            assert cap < len(got["big.py"]) < cap + 6000
            assert got["after.py"] == want["after.py"]

    def test_bytes_that_are_not_utf8_lose_nothing(self):
        raw = (_section("big.py", ["A"]).encode()
               + b"+\x80\x81\xff\xfe text\n" * 900 + _section("after.py", ["x"]).encode())
        whole = dict(gitutil.parse_diff_into_files(raw.decode(errors="replace")))
        got = dict(gitutil.parse_diff_into_files(
            _raw_keep(raw, 300, 500).decode(errors="replace")))
        assert got["big.py"][:500] == whole["big.py"][:500]
        assert len(got["big.py"]) > 500

    def test_text_that_is_not_utf8_is_bounded_too(self):
        raw = (_section("big.py", ["A"]).encode() + b"+" + b"\x80" * 200_000 + b"\n"
               + _section("after.py", ["x"]).encode())
        kept = _raw_keep(raw, 300, 500)
        assert len(kept) < 8000
        got = dict(gitutil.parse_diff_into_files(kept.decode(errors="replace")))
        whole = dict(gitutil.parse_diff_into_files(raw.decode(errors="replace")))
        assert got["big.py"][:500] == whole["big.py"][:500] and len(got["big.py"]) > 500
        assert got["after.py"] == whole["after.py"]

    @pytest.mark.parametrize("seed", range(10))
    def test_the_same_files_are_picked_as_when_read_whole(self, seed):
        """A large rewrite lists its removed lines first: cut before its added
        ones it would rank below files that barely changed."""
        rng = random.Random(seed)
        sections = []
        for i in range(60):
            removed = rng.choice([0, 5, 900])
            added = rng.choice([1, 5, 40, 900])
            body = "".join("-old line %d\n" % n for n in range(removed)) \
                + "".join("+new line %d\n" % n for n in range(added))
            sections.append(f"diff --git a/m{i}.py b/m{i}.py\n--- a/m{i}.py\n+++ b/m{i}.py\n"
                            f"@@ -1,{removed} +1,{added} @@\n" + body)
        raw = "".join(sections).encode()

        def picked(text):
            files = gitutil.parse_diff_into_files(text)
            return [p for p, _ in gitutil._prioritize_diff_files(files, 20)[0]]

        _, kept = _keep(raw, 300, rng, file_chars=400)
        assert picked(kept) == picked(raw.decode())
        assert len(kept) < len(raw)

    def test_the_count_of_added_lines_is_bounded(self, monkeypatch):
        monkeypatch.setattr(gitutil, "_MAX_COUNTED_LINES", 10)
        _, kept = _keep(_section("a.py", ["x"] * 5000).encode(), 300, file_chars=100)
        assert len(kept) < 3000

    @pytest.mark.parametrize("body", [
        b"Binary data follows\n" + b"unindented text\n" * 200,
        b"no line end " * 200,
    ])
    def test_a_long_section_without_content_lines_does_not_swallow_the_next(self, body):
        # `git show` with format.pretty=email prints the message unindented.
        raw = (b"diff --git a/logo.png b/logo.png\n" + body
               + (b"" if body.endswith(b"\n") else b"\n")
               + _section("app.py", ["os.system(x)"]).encode())
        for limit in (300, 0):
            kept = _raw_keep(raw, limit, 100).decode()
            assert [p for p, _ in gitutil.parse_diff_into_files(kept)] == ["app.py"]

    def test_bytes_that_count_for_nothing_are_read_in_few_steps(self):
        # One character short of the cap, then continuation bytes only: once
        # one step per byte, long enough for git's time limit to end the read.
        head = _section("a.py", [])
        room = 3 * len(head.partition("\n")[0]) + 512 + FILE_CHARS
        raw = head.encode() + b"+" + b"x" * (room - len(head) - 1) + b"\x80" * 300_000 + b"\n"
        keeper = gitutil._ReviewDiffKeeper(300, FILE_CHARS)
        keeper.feed(raw)
        assert keeper._bytes_left == 0
        assert len(keeper._section) < 1000

    @pytest.mark.parametrize("per_file, total, want", [
        (80000, 400000, 80000), (-1, 400000, 400000), (10**9, 400000, 400000),
        (80000, 1000, 1000), (80000, -5, 0)])
    def test_the_caps_of_the_prompt_set_what_is_kept(self, monkeypatch, per_file, total, want):
        import security_reminder_hook as hook
        monkeypatch.setattr(hook, "DIFF_PER_FILE_BYTES", per_file)
        monkeypatch.setattr(hook, "DIFF_TOTAL_BYTES", total)
        keeper = hook._review_diff_keeper(300)
        assert (keeper._max_files, keeper._file_chars) == (300, want)

    def test_files_without_a_hunk_do_not_count_towards_the_limit(self):
        raw = ("".join(_rename(f"old/r{i}.py", f"new/r{i}.py") for i in range(50))
               + "".join(_empty(f"pkg{i}/__init__.py") for i in range(50))
               + _section("app.py", ["os.system(cmd)"] * 2000)).encode()
        _, kept = _keep(raw, 5)
        assert gitutil.parse_diff_into_files(kept) == gitutil.parse_diff_into_files(raw.decode())

    def test_one_file_in_two_sections_counts_once(self):
        two = _section("link.py", ["a"], extra="deleted file mode 120000\n") \
            + _section("link.py", ["b"], extra="new file mode 100644\n")
        raw = (two * 3 + _section("app.py", ["x"] * 2000)).encode()
        _, kept = _keep(raw, 2)
        assert dict(gitutil.parse_diff_into_files(kept))["app.py"] == \
            dict(gitutil.parse_diff_into_files(raw.decode()))["app.py"]

    def test_long_names_are_still_counted(self):
        deep = "/".join(["d" * 200] * 15)
        raw = "".join(
            _section(f"{deep}/n{i}.py", ["x"] * 3000, old=f"{deep}/o{i}.py",
                     extra=f"similarity index 60%\nrename from {deep}/o{i}.py\n"
                           f"rename to {deep}/n{i}.py\n")
            for i in range(8)).encode()
        _, kept = _keep(raw, 2)
        assert len(gitutil.parse_diff_into_files(kept)) == 8

    @pytest.mark.parametrize("lines", [1, 3000])
    def test_a_dropped_file_keeps_the_lines_before_its_content(self, lines):
        raw = (_section(".env", ["KEY=1"] * lines, extra="deleted file mode 100644\n")
               + _rename("notes.txt", "other.txt")
               + _section("new.txt", ["words"] * lines, old="old.txt",
                          extra="similarity index 80%\nrename from old.txt\nrename to new.txt\n")
               + _section("app.py", ["x"])).encode()
        _, kept = _keep(raw, 300)
        assert "deleted file mode 100644\n" in kept
        assert "rename from notes.txt\nrename to other.txt\n" in kept
        assert "rename from old.txt\nrename to new.txt\n" in kept
        assert "KEY=1" not in kept and "words" not in kept
        assert [p for p, _ in gitutil.parse_diff_into_files(kept)] == ["app.py"]

    def test_what_comes_before_the_first_file_is_not_kept(self):
        _, kept = _keep((PREAMBLE + _section("app.py", ["x"])).encode(), 300)
        assert kept == _section("app.py", ["x"])
        _, kept = _keep((PREAMBLE + "diff --cc app.py\n" + "++x\n" * 9000).encode(), 300)
        assert kept == ""


def _push(repo, ws):
    old = git(repo, "rev-parse", "--short", "HEAD~1").strip()
    new = git(repo, "rev-parse", "--short", "HEAD").strip()
    git(repo, "push", "-q", "origin", "main")
    return bash_payload(repo, "git push origin main",
                        stderr=f"To {ws / 'up.git'}\n   {old}..{new}  main -> main\n")


@pytest.fixture
def repo_with_upstream(tmp_path):
    repo = make_repo(tmp_path / "repo")
    git(tmp_path, "init", "-q", "--bare", "-b", "main", "up.git")
    git(repo, "remote", "add", "origin", str(tmp_path / "up.git"))
    git(repo, "push", "-q", "-u", "origin", "main")
    return repo


def _payload(kind, repo, ws, change):
    """Make the change as a commit, an amend or a push; the hook's payload."""
    if kind == "amend":
        commit_file(repo, "wip.py", "y = 1\n")
        change(repo, False)
        git(repo, "add", "-A")
        out = git(repo, "commit", "--amend", "-m", "import")
        return bash_payload(repo, "git commit --amend -m import", stdout=out[:20000])
    _, out = change(repo, True)
    if kind == "push":
        return _push(repo, ws)
    return bash_payload(repo, "git commit -m import", stdout=out[:20000])


@pytest.mark.parametrize("kind", ["commit", "amend", "push"])
class TestHooks:
    def test_over_the_cut_off_is_skipped_with_the_full_count(
            self, kind, repo_with_upstream, tmp_path, hook_env, stub_api):
        def change(repo, commit):
            for i in range(25):
                (repo / f"mod{i}.py").write_text("x = 1\n" * 400)
            return commit_file(repo, "app.py", VULN_PY) if commit else None

        payload = _payload(kind, repo_with_upstream, tmp_path, change)
        env = {**hook_env, "MAX_DIFF_FILES": "2", "SG_PUSH_SWEEP_MAX_FILES": "2"}
        rc, out, err = run_hook(payload, env)
        m = metrics_of(out)
        assert rc == 0, err
        assert m["skip_reason"] == 31
        assert m["diff_files_count"] == (25 if kind == "amend" else 26)
        assert "diff_mb" not in m
        assert not [b for b in stub_api.bodies if "mod1.py" in b]

    def test_a_large_file_does_not_hide_the_others(
            self, kind, repo_with_upstream, tmp_path, hook_env, stub_api):
        def change(repo, commit):
            (repo / "gen.json").write_text('{"k": "some generated text"}\n' * 400_000)
            (repo / "dump.txt").write_text("not a reviewed type\n" * 400_000)
            if commit:
                return commit_file(repo, "zapp.py", VULN_PY)
            (repo / "zapp.py").write_text(VULN_PY)

        payload = _payload(kind, repo_with_upstream, tmp_path, change)
        rc, out, err = run_hook(payload, hook_env)
        m = metrics_of(out)
        assert rc == 0, err
        assert m["files_reviewed"] == 2
        body = "\n".join(stub_api.bodies)
        assert "subprocess.call('ls ' + user, shell=True)" in body
        assert "not a reviewed type" not in body

    def test_what_was_read_is_on_the_row_of_a_skipped_import(
            self, kind, repo_with_upstream, tmp_path, hook_env, stub_api):
        def change(repo, commit):
            for i in range(12):
                (repo / f"mod{i}.py").write_text("x = 'some generated text'\n" * 12000)
            return commit_file(repo, "app.py", VULN_PY) if commit else None

        payload = _payload(kind, repo_with_upstream, tmp_path, change)
        env = {**hook_env, "MAX_DIFF_FILES": "1", "SG_PUSH_SWEEP_MAX_FILES": "1"}
        rc, out, err = run_hook(payload, env)
        m = metrics_of(out)
        assert rc == 0, err
        assert m["skip_reason"] == 31
        assert m["diff_mb"] == 3


@pytest.mark.parametrize("kind", ["commit", "amend", "push"])
def test_files_under_the_cut_off_are_sent_whole(
        kind, repo_with_upstream, tmp_path, hook_env, stub_api):
    """More files than are sent, fewer than the cut-off, one of them long."""
    def change(repo, commit):
        for i in range(8):
            (repo / f"mod{i}.py").write_text(f"x{i} = 'ordinary file {i}'\n" * 3)
        # Its name puts it among the files that are sent.
        (repo / "auth.py").write_text("y = 'filler line'\n" * 40_000 + "LAST_LINE_OF_AUTH = 1\n")
        return commit_file(repo, "app.py", VULN_PY) if commit else None

    payload = _payload(kind, repo_with_upstream, tmp_path, change)
    env = {**hook_env, "MAX_DIFF_FILES": "2", "SG_PUSH_SWEEP_MAX_FILES": "2",
           # The Stop review's cap, which does not apply here.
           "SG_MAX_FILE_DIFF_BYTES": "1",
           "DIFF_PER_FILE_BYTES": "900000", "DIFF_TOTAL_BYTES": "900000"}
    rc, out, err = run_hook(payload, env)
    m = metrics_of(out)
    assert rc == 0, err
    assert m["files_reviewed"] == 2
    assert m["diff_files_dropped"] == (7 if kind == "amend" else 8)
    body = "\n".join(stub_api.bodies)
    assert "LAST_LINE_OF_AUTH = 1" in body
    assert body.count("filler line") == 40_000


def test_several_commits_found_in_the_reflog(tmp_path, hook_env, stub_api):
    repo = make_repo(tmp_path / "repo")
    (repo / "gen.json").write_text('{"k": "some generated text"}\n' * 100_000)
    commit_file(repo, "first.py", VULN_PY)
    (repo / "gen2.json").write_text('{"k": "some generated text"}\n' * 100_000)
    commit_file(repo, "second.py", VULN_PY)
    rc, out, err = run_hook(bash_payload(
        repo, "git add . && git commit -q -m a && git add . && git commit -q -m b"), hook_env)
    m = metrics_of(out)
    assert rc == 0, err
    assert m["reflog_shas_n"] >= 2
    body = "\n".join(stub_api.bodies)
    assert "first.py" in body and "second.py" in body


def test_a_diff_that_hits_the_time_limit(tmp_path, monkeypatch):
    import sys
    cmd = [sys.executable, "-c", "import time; print('diff --git a/a.py b/a.py', flush=True); time.sleep(60)"]
    with pytest.raises(subprocess.TimeoutExpired):
        gitutil._run_diff_bounded(cmd, 1, gitutil._ReviewDiffKeeper(300, FILE_CHARS))
    import security_reminder_hook as hook
    assert hook._diff_read_metrics() == {"diff_timeout": 1}
    monkeypatch.setattr(gitutil, "_run_diff_bounded",
                        lambda *a, **k: (_ for _ in ()).throw(subprocess.TimeoutExpired("git", 30)))
    assert gitutil._git_diff_range(str(tmp_path), "HEAD~1",
                                   keeper=gitutil._ReviewDiffKeeper(300, FILE_CHARS)) is None


class TestMemory:
    @pytest.mark.parametrize("ext", [".txt", ".py"])
    def test_import_is_not_held(self, tmp_path, monkeypatch, ext):
        for k, v in GIT_ENV.items():
            monkeypatch.setenv(k, v)
        repo = make_repo(tmp_path / "repo")
        line = "row = compute('some generated text of about sixty bytes')\n"
        for i in range(400):
            (repo / f"gen{i}{ext}").write_text(line * 2500)
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", "import")
        size = 400 * 2500 * len(line)
        tracemalloc.start()
        try:
            text = gitutil._git_diff_range(
                str(repo), "HEAD~1", keeper=gitutil._ReviewDiffKeeper(20, FILE_CHARS))
            files = gitutil.parse_diff_into_files(text)
            peak = tracemalloc.get_traced_memory()[1]
        finally:
            tracemalloc.stop()
        assert len(files) == (400 if ext == ".py" else 0)
        # 57 MB of text. Reading it whole peaks at three times that or more.
        assert peak < size // 10

    def test_a_failed_command_is_still_an_error(self, tmp_path):
        repo = make_repo(tmp_path / "repo")
        assert gitutil._git_diff_range(str(repo), "no-such-ref", keeper=gitutil._ReviewDiffKeeper(20, FILE_CHARS)) is None
        assert gitutil._git_diff_range(str(repo), "HEAD", keeper=gitutil._ReviewDiffKeeper(20, FILE_CHARS)) == ""

    def test_a_range_read_without_a_limit_keeps_every_file(self, tmp_path, monkeypatch):
        for k, v in GIT_ENV.items():
            monkeypatch.setenv(k, v)
        repo = make_repo(tmp_path / "repo")
        commit_file(repo, "a.py", "x = 1\n")
        text = gitutil._git_diff_range(str(repo), "HEAD~1")
        raw = subprocess.run(["git", "diff", "-p", "HEAD~1", "HEAD"], cwd=repo,
                             capture_output=True).stdout.decode()
        assert gitutil.parse_diff_into_files(text) == gitutil.parse_diff_into_files(raw)
