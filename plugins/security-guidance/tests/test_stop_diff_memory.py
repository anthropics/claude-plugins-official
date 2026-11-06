"""The Stop review reads `git diff` output without holding all of it: files it
would drop come back as a header line, and one file's diff is cut at a cap."""
import random
import subprocess
import sys
import tempfile
import time
import tracemalloc

import pytest

from conftest import (
    GIT_ENV, VULN_PY, make_repo, metrics_of, run_hook, stop_payload,
    ups_payload,
)

import gitutil


@pytest.fixture(autouse=True)
def _fresh_read_state():
    yield
    gitutil._unparsed_diff_headers.clear()
    gitutil._diff_read.update(bytes=0, cut_files=0, cut_bytes=0, timeouts=0)


def _rewrite(path, removed, added):
    return (f"diff --git a/{path} b/{path}\n"
            "index 1111111..2222222 100644\n"
            f"--- a/{path}\n+++ b/{path}\n"
            f"@@ -1,{len(removed)} +1,{len(added)} @@\n"
            + "".join(f"-{ln}\n" for ln in removed)
            + "".join(f"+{ln}\n" for ln in added))


@pytest.fixture
def git_env(tmp_path, monkeypatch):
    d = tmp_path / "tmproot"
    d.mkdir()
    monkeypatch.setattr(tempfile, "tempdir", str(d))
    for k, v in GIT_ENV.items():
        monkeypatch.setenv(k, v)


def _section(path, body_lines, old=None):
    return (f"diff --git a/{old or path} b/{path}\n"
            "index 1111111..2222222 100644\n"
            f"--- a/{old or path}\n+++ b/{path}\n"
            f"@@ -1,2 +1,{len(body_lines)} @@\n"
            + "".join(f"+{ln}\n" for ln in body_lines))


def _keep(raw, chunk_sizes):
    keeper = gitutil._DiffKeeper()
    pos = 0
    while pos < len(raw):
        n = next(chunk_sizes)
        keeper.feed(raw[pos:pos + n])
        pos += n
    return keeper, keeper.result()


def _sizes(*cycle):
    while True:
        yield from cycle


MIXED = (
    _section("app.py", ["import os", "os.system(cmd)"])
    + _section("notes.txt", ["plain text", "diff --git a/fake.py b/fake.py is only text here"])
    + _section("web/café.js", ["eval(x)"])
    + 'diff --git "a/we\\"ird.py" "b/we\\"ird.py"\n--- "a/we\\"ird.py"\n+++ "b/we\\"ird.py"\n@@ -1 +1 @@\n+x = 1\n'
    + "diff --git nonsense header\n@@ -1 +1 @@\n+y\n"
    + _section("new_name.py", ["z = 2"], old="old_name.txt")
    + _section("data.csv", ["1,2,3"] * 50)
    + _section("last.sh", ["rm -rf $1"])
).encode()


class TestDiffKeeper:
    @pytest.mark.parametrize("seed", range(40))
    def test_same_files_as_reading_it_whole_at_any_chunking(self, seed):
        rng = random.Random(seed)
        sizes = iter(lambda: rng.choice([1, 2, 3, 7, 11, 12, 13, 64, 500]), None)
        gitutil._unparsed_diff_headers.clear()
        want = gitutil.parse_diff_into_files(MIXED.decode())
        want_unparsed = set(gitutil._unparsed_diff_headers)
        gitutil._unparsed_diff_headers.clear()
        keeper, kept = _keep(MIXED, sizes)
        assert gitutil.parse_diff_into_files(kept.decode()) == want
        assert gitutil._unparsed_diff_headers == want_unparsed
        assert [p for p, _ in want] == ["app.py", "web/café.js", 'we"ird.py', "new_name.py", "last.sh"]
        assert keeper.seen == len(MIXED)
        assert keeper.cut_files == 0

    def test_dropped_file_keeps_its_header_line_only(self):
        _, kept = _keep(MIXED, _sizes(4096))
        text = kept.decode()
        assert "diff --git a/notes.txt b/notes.txt\n" in text
        assert "plain text" not in text and "1,2,3" not in text
        assert len(kept) < len(MIXED)

    def test_untouched_when_every_file_is_reviewable_and_small(self):
        raw = (_section("a.py", ["x"]) + _section("b.js", ["y"])).encode()
        assert _keep(raw, _sizes(5))[1] == raw

    @pytest.mark.parametrize("chunk", [1, 17, 4096])
    def test_large_file_is_cut_and_the_next_file_survives(self, monkeypatch, chunk):
        monkeypatch.setattr(gitutil, "MAX_FILE_DIFF_BYTES", 300)
        big = _section("big.json", ["k" * 37] * 100)
        raw = (big + _section("after.py", ["import os"])).encode()
        keeper, kept = _keep(raw, _sizes(chunk))
        files = dict(gitutil.parse_diff_into_files(kept.decode()))
        assert set(files) == {"big.json", "after.py"}
        assert files["after.py"] == dict(gitutil.parse_diff_into_files(raw.decode()))["after.py"]
        # The start of the section, then as much again of its added lines.
        assert 300 < len(files["big.json"]) <= 2 * 300 + len(gitutil._CUT_MARK) + 2
        assert keeper.cut_files == 1
        assert keeper.cut_bytes == len(big) - 2 * 300

    def test_cut_file_says_so_on_its_last_line(self, monkeypatch):
        monkeypatch.setattr(gitutil, "MAX_FILE_DIFF_BYTES", 300)
        raw = (_section("big.json", ["k" * 37] * 100) + _section("after.py", ["x"])).encode()
        _, kept = _keep(raw, _sizes(64))
        files = dict(gitutil.parse_diff_into_files(kept.decode()))
        assert files["big.json"].endswith(gitutil._CUT_MARK.decode())
        assert "cut by security-guidance" not in files["after.py"]
        assert kept.count(gitutil._CUT_MARK) == 1

    @pytest.mark.parametrize("chunk", [1, 23, 4096])
    def test_rewrite_past_the_cap_keeps_its_added_lines(self, monkeypatch, chunk):
        monkeypatch.setattr(gitutil, "MAX_FILE_DIFF_BYTES", 400)
        raw = (_rewrite("views.py", ["old line %03d" % i for i in range(200)],
                        ["os.system(cmd)"] + ["new line %03d" % i for i in range(200)])
               + _section("after.py", ["x"])).encode()
        keeper, kept = _keep(raw, _sizes(chunk))
        body = dict(gitutil.parse_diff_into_files(kept.decode()))["views.py"]
        assert "+os.system(cmd)\n" in body
        assert "-old line 199" not in body
        past = body[400:]
        assert all(ln.startswith(("+", "\\")) for ln in past.splitlines()[1:])
        assert len(body) <= 2 * 400 + len(gitutil._CUT_MARK) + 2
        assert keeper.cut_files == 1

    def test_dropped_large_file_is_not_counted_as_cut(self, monkeypatch):
        monkeypatch.setattr(gitutil, "MAX_FILE_DIFF_BYTES", 300)
        raw = (_section("big.log", ["k" * 37] * 100) + _section("after.py", ["x"])).encode()
        keeper, kept = _keep(raw, _sizes(64))
        assert keeper.cut_files == 0 and keeper.cut_bytes == 0
        assert [p for p, _ in gitutil.parse_diff_into_files(kept.decode())] == ["after.py"]

    def test_renamed_from_a_secret_shaped_name_keeps_its_header_only(self):
        raw = (_section("config.py", ["TOKEN = 'abc'"], old=".env")
               + _section("after.py", ["x"])).encode()
        want = gitutil.parse_diff_into_files(raw.decode())
        _, kept = _keep(raw, _sizes(64))
        assert gitutil.parse_diff_into_files(kept.decode()) == want
        assert [p for p, _ in want] == ["after.py"]
        assert b"TOKEN" not in kept

    def test_past_the_total_later_files_keep_less_and_less(self, monkeypatch):
        monkeypatch.setattr(gitutil, "MAX_FILE_DIFF_BYTES", 2000)
        monkeypatch.setattr(gitutil, "MAX_KEPT_DIFF_BYTES", 3000)
        monkeypatch.setattr(gitutil, "_LATE_FILE_DIFF_BYTES", 200)
        monkeypatch.setattr(gitutil, "_LAST_FILE_DIFF_BYTES", 120)
        raw = "".join(_section(f"f{i}.py", ["v" * 30] * 400) for i in range(40)).encode()
        keeper, kept = _keep(raw, _sizes(333))
        files = gitutil.parse_diff_into_files(kept.decode())
        assert [p for p, _ in files] == [f"f{i}.py" for i in range(40)]
        sizes = [len(body) for _, body in files]
        mark = len(gitutil._CUT_MARK) + 2
        assert sizes[0] > 2000 and sizes[0] <= 4000 + mark
        assert 200 < sizes[5] <= 400 + mark
        assert sizes[-1] <= 120 + mark
        assert sizes[0] > sizes[5] > sizes[-1]
        assert keeper.cut_files == 40
        # Everything not kept is counted; a cut may add a newline or two.
        from_git = len(kept) - 40 * len(gitutil._CUT_MARK)
        assert from_git - 80 <= len(raw) - keeper.cut_bytes <= from_git

    def test_output_cut_inside_a_line_ends_with_a_newline(self, monkeypatch):
        monkeypatch.setattr(gitutil, "MAX_FILE_DIFF_BYTES", 300)
        raw = _rewrite("big.json", ["k" * 37] * 100, []).encode()
        keeper, kept = _keep(raw, _sizes(64))
        assert kept == raw[:300] + b"\n" + gitutil._CUT_MARK
        assert keeper.cut_bytes == len(raw) - 300
        both = kept + _section("next.py", ["x"]).encode()
        assert [p for p, _ in gitutil.parse_diff_into_files(both.decode())] == ["big.json", "next.py"]

    def test_empty_output(self):
        keeper, kept = _keep(b"", _sizes(1))
        assert kept == b"" and keeper.seen == 0


class TestRunDiffBounded:
    def test_returns_what_run_would(self):
        code = ("import sys; sys.stdout.buffer.write(b'diff --git a/a.py b/a.py\\n@@ -1 +1 @@\\n+x\\n'); "
                "sys.stderr.write('warn'); sys.exit(3)")
        r = gitutil._run_diff_bounded([sys.executable, "-c", code], 30)
        assert r.returncode == 3
        assert r.stdout == b"diff --git a/a.py b/a.py\n@@ -1 +1 @@\n+x\n"
        assert r.stderr == b"warn"

    def test_timeout_kills_and_raises(self):
        code = "import sys, time; sys.stdout.write('x' * 100000); sys.stdout.flush(); time.sleep(60)"
        before = gitutil._diff_read["timeouts"]
        with pytest.raises(subprocess.TimeoutExpired):
            gitutil._run_diff_bounded([sys.executable, "-c", code], 0.5)
        assert gitutil._diff_read["timeouts"] == before + 1

    def test_timeout_holds_while_another_process_keeps_the_pipe_open(self):
        # What a `git diff` that started a fetch looks like: the program is
        # gone, something it started still holds its stdout.
        code = ("import subprocess, sys; "
                "subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(8)']); "
                "sys.stdout.write('x'); sys.stdout.flush()")
        before = gitutil._diff_read["timeouts"]
        t0 = time.monotonic()
        with pytest.raises(subprocess.TimeoutExpired):
            gitutil._run_diff_bounded([sys.executable, "-c", code], 1)
        assert time.monotonic() - t0 < 5
        assert gitutil._diff_read["timeouts"] == before + 1

    def test_a_timed_out_read_still_reports_its_size(self):
        code = "import sys, time; sys.stdout.write('x' * 300000); sys.stdout.flush(); time.sleep(60)"
        with pytest.raises(subprocess.TimeoutExpired):
            gitutil._run_diff_bounded([sys.executable, "-c", code], 1)
        assert gitutil._diff_read["bytes"] >= 200000

    def test_a_read_that_breaks_is_an_error_not_a_short_diff(self, monkeypatch):
        def broken(self, data):
            raise MemoryError("no room")
        monkeypatch.setattr(gitutil._DiffKeeper, "feed", broken)
        code = "import sys; sys.stdout.write('diff --git a/a.py b/a.py\\n' * 50000)"
        t0 = time.monotonic()
        with pytest.raises(OSError):
            gitutil._run_diff_bounded([sys.executable, "-c", code], 30)
        assert time.monotonic() - t0 < 10

    def test_no_thread_to_read_with_is_an_error(self, monkeypatch):
        def refuse(self):
            raise RuntimeError("can't start new thread")
        monkeypatch.setattr(gitutil.threading.Thread, "start", refuse)
        with pytest.raises(OSError):
            gitutil._run_diff_bounded([sys.executable, "-c", "print('x')"], 30)

    def test_missing_program_raises_like_run(self):
        with pytest.raises(FileNotFoundError):
            gitutil._run_diff_bounded(["sg-no-such-program"], 5)


class TestGetGitDiff:
    def test_large_data_file_is_not_held(self, tmp_path, git_env):
        repo = make_repo(tmp_path / "repo", {"app.py": "print('hi')\n"})
        (repo / "app.py").write_text(VULN_PY)
        line = "generated text line that is about eighty bytes long once the number is on it %07d\n"
        (repo / "gen.txt").write_text("".join(line % i for i in range(250000)))
        paths = [str(repo / "app.py"), str(repo / "gen.txt")]
        tracemalloc.start()
        try:
            diff = gitutil.get_git_diff(str(repo), "HEAD", paths=paths, untracked_paths=["gen.txt"])
            peak = tracemalloc.get_traced_memory()[1]
        finally:
            tracemalloc.stop()
        assert [p for p, _ in gitutil.parse_diff_into_files(diff)] == ["app.py"]
        assert "diff --git a/gen.txt b/gen.txt\n" in diff and "generated text" not in diff
        assert gitutil._diff_read["bytes"] > 20 * 1024 * 1024
        assert gitutil._diff_read["cut_files"] == 0
        # Reading it whole took several times the 20 MB of output.
        assert peak < 8 * 1024 * 1024

    def test_timeout_is_none(self, tmp_path, git_env, monkeypatch):
        repo = make_repo(tmp_path / "repo", {"app.py": "x = 1\n"})

        def slow(cmd, timeout, **kwargs):
            raise subprocess.TimeoutExpired(cmd, timeout)

        monkeypatch.setattr(gitutil, "_run_diff_bounded", slow)
        assert gitutil.get_git_diff(str(repo), "HEAD", paths=[str(repo / "app.py")],
                                    untracked_paths=[]) is None

    @pytest.mark.parametrize("value, want", [
        ("", 4 * 1024 * 1024), ("junk", 4 * 1024 * 1024), ("0", 4 * 1024 * 1024),
        ("-5", 4 * 1024 * 1024), ("1000", 256 * 1024), ("1000000", 1000000)])
    def test_cap_setting_cannot_break_the_read(self, monkeypatch, value, want):
        monkeypatch.setenv("SG_MAX_FILE_DIFF_BYTES", value)
        assert gitutil._file_diff_cap() == want

    def test_rewritten_large_file_still_shows_what_is_new(self, tmp_path, git_env):
        body = "".join(f"def handler_{i}(request):\n    return render(request, 'page_{i}.html')\n"
                       for i in range(18000))
        repo = make_repo(tmp_path / "repo", {"app.py": "x = 1\n"})
        (repo / "views.py").write_bytes(body.replace("\n", "\r\n").encode())
        subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "views"], cwd=repo, check=True)
        assert (repo / "views.py").stat().st_size > 1200000
        (repo / "views.py").write_bytes(("import os\nos.system(request.GET['cmd'])\n" + body).encode())
        diff = gitutil.get_git_diff(str(repo), "HEAD", paths=[str(repo / "views.py")], untracked_paths=[])
        assert gitutil._diff_read["cut_files"] == 0
        files = gitutil.filter_preexisting_from_diff(
            gitutil.parse_diff_into_files(diff), str(repo), "HEAD")
        assert "+os.system(request.GET['cmd'])" in files[0][1][:2000]

    def test_rewrite_past_the_cap_still_shows_what_is_new(self, tmp_path, git_env, monkeypatch):
        monkeypatch.setattr(gitutil, "MAX_FILE_DIFF_BYTES", 200000)
        body = "".join(f"def handler_{i}(request):\n    return render(request, 'page_{i}.html')\n"
                       for i in range(18000))
        repo = make_repo(tmp_path / "repo", {"views.py": body.replace("\n", "\r\n")})
        (repo / "views.py").write_bytes(("import os\nos.system(request.GET['cmd'])\n" + body).encode())
        diff = gitutil.get_git_diff(str(repo), "HEAD", paths=[str(repo / "views.py")], untracked_paths=[])
        assert gitutil._diff_read["cut_files"] == 1
        assert len(diff) < 2 * 200000 + 1000
        files = gitutil.filter_preexisting_from_diff(
            gitutil.parse_diff_into_files(diff), str(repo), "HEAD")
        assert "+os.system(request.GET['cmd'])" in files[0][1][:2000]

    def test_failed_diff_is_still_none(self, tmp_path, git_env):
        repo = make_repo(tmp_path / "repo", {"app.py": "x = 1\n"})
        assert gitutil.get_git_diff(str(repo), "0" * 40, paths=[str(repo / "app.py")],
                                    untracked_paths=[]) is None


class TestStopHook:
    def test_reports_what_it_read_and_reviews_the_source(self, tmp_path, hook_env, stub_api):
        repo = make_repo(tmp_path / "repo", {"app.py": "print('hi')\n"})
        run_hook(ups_payload(repo), hook_env)
        (repo / "app.py").write_text(VULN_PY)
        (repo / "gen.txt").write_text("some generated text\n" * 150000)
        (repo / "big.json").write_text('"k": "some generated value",\n' * 20000)
        env = {**hook_env, "SG_MAX_FILE_DIFF_BYTES": "1000"}
        rc, so, se = run_hook(stop_payload(repo), env)
        m = metrics_of(so)
        assert not m.get("skipped"), m
        assert m["files_reviewed"] == 2
        assert m["diff_mb"] == 3
        assert m["diff_cut_files"] == 1
        # 256 KiB from the start and as much again of added lines were read;
        # the prompt took 80,000 bytes of that.
        assert m["diff_truncated"] > 20000 * 29 - 80000 - 1000
        assert "diff_timeout" not in m
        assert stub_api.calls

    def test_small_turn_reports_nothing_new(self, tmp_path, hook_env, stub_api):
        repo = make_repo(tmp_path / "repo", {"app.py": "print('hi')\n"})
        run_hook(ups_payload(repo), hook_env)
        (repo / "app.py").write_text(VULN_PY)
        m = metrics_of(run_hook(stop_payload(repo), hook_env)[1])
        assert m["files_reviewed"] == 1
        assert not {"diff_mb", "diff_cut_files", "diff_timeout"} & set(m)
