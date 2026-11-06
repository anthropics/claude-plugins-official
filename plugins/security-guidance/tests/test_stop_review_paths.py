"""The Stop review still runs when the changed paths of a turn do not fit in
one git command."""
import errno
import os
import subprocess
import tempfile
import types

import pytest

from conftest import (
    GIT_ENV, VULN_PY, make_repo, metrics_of, run_hook, stop_payload,
    ups_payload,
)

import diffstate
import gitutil

GIT_CMD_CHARS = sum(len(a) + 1 for a in gitutil.GIT_CMD)


@pytest.fixture
def git_env(tmp_path, monkeypatch):
    """Git identity for in-process calls, and a temp dir of our own for the
    index copies."""
    d = tmp_path / "tmproot"
    d.mkdir()
    monkeypatch.setattr(tempfile, "tempdir", str(d))
    monkeypatch.setattr(gitutil, "_path_list_too_long", set())
    for k, v in GIT_ENV.items():
        monkeypatch.setenv(k, v)


def _more_than_one_command_holds(repo, exts):
    """3,000 untracked files, cycling through `exts`, whose names add up to
    more than a single command can carry on any platform (the largest limit
    is about 2 MB, on Linux)."""
    deep = repo / ("d" * 180) / ("e" * 180) / ("f" * 180) / ("g" * 180)
    deep.mkdir(parents=True)
    for i in range(3000):
        (deep / f"file_{i:05d}{exts[i % len(exts)]}").write_text("x\n")


def _unusual_argument_limit():
    """The long-path tests are sized for the usual limits: 1 MB (macOS) to
    2 MB (Linux with an 8 MB stack)."""
    try:
        return not 1024 * 1024 <= os.sysconf("SC_ARG_MAX") <= 2 * 1024 * 1024 + 200000
    except (AttributeError, ValueError, OSError):
        return False


long_paths = pytest.mark.skipif(
    os.name == "nt" or _unusual_argument_limit(),
    reason="needs paths longer than Windows allows by default, and the usual "
           "1 to 2 MB limit on one command's arguments")


def _refuse_long_commands(monkeypatch, limit, error):
    """Make starting a command fail like the OS does when its arguments
    exceed `limit` characters. Returns the list of commands run. Popen is
    where subprocess.run and the bounded diff reader both start theirs."""
    real_popen = subprocess.Popen
    ran = []

    def popen(cmd, *args, **kwargs):
        if sum(len(a) + 1 for a in cmd) > limit:
            raise error
        ran.append(cmd)
        return real_popen(cmd, *args, **kwargs)

    monkeypatch.setattr(subprocess, "Popen", popen)
    return ran


class TestPathBatches:
    def test_every_path_once_and_each_batch_bounded(self):
        paths = [f"dir/file_{i}.py" for i in range(100000)]
        batches = list(gitutil._path_batches(paths))
        assert [p for b in batches for p in b] == paths
        assert len(batches) > 1
        assert all(sum(len(p) for p in b) <= gitutil._MAX_PATH_ARGS_BYTES
                   for b in batches)

    def test_budget_is_in_bytes(self, monkeypatch):
        monkeypatch.setattr(gitutil, "_MAX_PATH_ARGS_BYTES", 100)
        assert len(list(gitutil._path_batches(["\u6f22" * 20 + ".py"] * 3))) == 3

    def test_one_overlong_path_still_goes_out(self):
        long = "x" * (gitutil._MAX_PATH_ARGS_BYTES + 10)
        assert list(gitutil._path_batches(["a", long, "b"])) == [["a"], [long], ["b"]]

    def test_no_paths_no_batches(self):
        assert list(gitutil._path_batches([])) == []


class TestGetGitDiff:
    def _review_set(self, tmp_path):
        repo = make_repo(tmp_path / "repo", {f"t{i}.py": "x = 1\n" for i in range(6)})
        for i in range(6):
            (repo / f"t{i}.py").write_text("x = 2\n")
            (repo / f"new{i}.py").write_text("y = 1\n")
        paths, base, root, untracked, _ = diffstate.compute_v2_review_set(str(repo), None, None, {})
        assert len(paths) == 12 and len(untracked) == 6
        return root, base, paths, untracked

    def test_one_command_when_the_paths_fit(self, tmp_path, git_env, monkeypatch):
        root, base, paths, untracked = self._review_set(tmp_path)
        ran = _refuse_long_commands(monkeypatch, 10**9, OSError(errno.E2BIG, "too long"))
        diff = gitutil.get_git_diff(root, base, paths=paths, untracked_paths=untracked)
        assert len(gitutil.parse_diff_into_files(diff)) == 12
        assert len([c for c in ran if "diff" in c]) == 1
        assert len([c for c in ran if "add" in c]) == 1

    @pytest.mark.parametrize("error", [
        OSError(errno.E2BIG, "Argument list too long"),
        # What Python raises on Windows for ERROR_FILENAME_EXCED_RANGE.
        type("WinTooLong", (FileNotFoundError,), {"winerror": 206})(errno.ENOENT, "too long"),
    ], ids=["posix", "windows"])
    def test_batches_when_one_command_is_refused(self, tmp_path, git_env, monkeypatch, error):
        root, base, paths, untracked = self._review_set(tmp_path)
        whole = gitutil.get_git_diff(root, base, paths=paths, untracked_paths=untracked)
        monkeypatch.setattr(gitutil, "_MAX_PATH_ARGS_BYTES", 60)
        limit = GIT_CMD_CHARS + 100  # the six-path add fits, the twelve-path diff does not
        ran = _refuse_long_commands(monkeypatch, limit, error)
        batched = gitutil.get_git_diff(root, base, paths=paths, untracked_paths=untracked)
        assert sorted(gitutil.parse_diff_into_files(batched)) == \
            sorted(gitutil.parse_diff_into_files(whole))
        assert len([c for c in ran if "diff" in c]) > 1
        # The batches are read through the bounded reader, which counts them.
        assert gitutil._diff_read["bytes"] > 0

    def test_only_reviewable_paths_after_a_refusal(self, tmp_path, git_env, monkeypatch):
        repo = make_repo(tmp_path / "repo", {"app.py": "x = 1\n"})
        (repo / "app.py").write_text("x = 2\n")
        for i in range(20):
            (repo / f"note{i:02d}.txt").write_text("x\n")
        paths, base, root, untracked, _ = diffstate.compute_v2_review_set(str(repo), None, None, {})
        whole = gitutil.get_git_diff(root, base, paths=paths, untracked_paths=untracked)
        assert whole.count("diff --git ") == 21
        _refuse_long_commands(monkeypatch, GIT_CMD_CHARS + 100, OSError(errno.E2BIG, "too long"))
        cut = gitutil.get_git_diff(root, base, paths=paths, untracked_paths=untracked)
        assert cut.count("diff --git ") == 1
        assert gitutil.parse_diff_into_files(cut) == gitutil.parse_diff_into_files(whole)

    def test_rename_away_from_a_secret_shaped_name_stays_out_after_a_refusal(
            self, tmp_path, git_env, monkeypatch):
        secret = "".join(f"KEY_{i}=value-{i}\n" for i in range(20))
        repo = make_repo(tmp_path / "repo", {".env": secret, "app.py": "x = 1\n"})
        os.rename(repo / ".env", repo / "settings.py")
        (repo / "app.py").write_text("x = 2\n")
        (repo / "a_much_longer_module_name.py").write_text("y = 1\n")
        for i in range(20):
            (repo / f"note{i:02d}.txt").write_text("x\n")
        paths, base, root, untracked, _ = diffstate.compute_v2_review_set(str(repo), None, None, {})
        whole = gitutil.get_git_diff(root, base, paths=paths, untracked_paths=untracked)
        reviewed = ["a_much_longer_module_name.py", "app.py"]
        assert sorted(f for f, _ in gitutil.parse_diff_into_files(whole)) == reviewed
        # Room for .env beside each batch, and not for the three .py together.
        monkeypatch.setattr(gitutil, "_MAX_PATH_ARGS_BYTES", 60)
        ran = _refuse_long_commands(monkeypatch, GIT_CMD_CHARS + 120, OSError(errno.E2BIG, "too long"))
        cut = gitutil.get_git_diff(root, base, paths=paths, untracked_paths=untracked)
        diffs = [c for c in ran if "diff" in c]
        assert len(diffs) > 1 and all(".env" in c for c in diffs)
        assert sorted(f for f, _ in gitutil.parse_diff_into_files(cut)) == reviewed
        assert "KEY_1=" not in "".join(d for _, d in gitutil.parse_diff_into_files(cut))

    def test_gives_up_when_the_secret_shaped_paths_alone_are_too_many(
            self, tmp_path, git_env, monkeypatch):
        repo = make_repo(tmp_path / "repo", {
            "app.py": "x = 1\n", **{f"dir{i:02d}/.env": "K=v\n" for i in range(20)}})
        (repo / "app.py").write_text("x = 2\n")
        for i in range(20):
            os.remove(repo / f"dir{i:02d}" / ".env")
        paths, base, root, untracked, _ = diffstate.compute_v2_review_set(str(repo), None, None, {})
        monkeypatch.setattr(gitutil, "_MAX_PATH_ARGS_BYTES", 200)
        ran = _refuse_long_commands(monkeypatch, GIT_CMD_CHARS + 100, OSError(errno.E2BIG, "too long"))
        assert gitutil.get_git_diff(root, base, paths=paths, untracked_paths=untracked) is None
        assert [c for c in ran if "diff" in c] == []
        assert "gave_up" in gitutil._path_list_too_long

    def test_secret_shaped_files_still_in_the_work_tree_do_not_ride_along(
            self, tmp_path, git_env, monkeypatch):
        repo = make_repo(tmp_path / "repo", {"app.py": "x = 1\n"})
        (repo / "app.py").write_text("x = 2\n")
        for i in range(20):
            (repo / f"dir{i:02d}").mkdir()
            (repo / f"dir{i:02d}" / ".env").write_text("K=v\n")
        paths, base, root, untracked, _ = diffstate.compute_v2_review_set(str(repo), None, None, {})
        monkeypatch.setattr(gitutil, "_MAX_PATH_ARGS_BYTES", 200)
        ran = _refuse_long_commands(monkeypatch, GIT_CMD_CHARS + 100, OSError(errno.E2BIG, "too long"))
        cut = gitutil.get_git_diff(root, base, paths=paths, untracked_paths=untracked)
        assert [f for f, _ in gitutil.parse_diff_into_files(cut)] == ["app.py"]
        assert not any(".env" in a for c in ran for a in c)
        assert not gitutil._path_list_too_long

    def test_batches_shrink_to_a_lower_system_limit(self, monkeypatch):
        monkeypatch.setattr(os, "sysconf", lambda name: 100000, raising=False)
        budget = gitutil._path_args_budget({"A": "b" * 9997})
        # Half of what the environment leaves, or the platform figure where
        # that is lower (Windows).
        assert budget == min(45000, gitutil._MAX_PATH_ARGS_BYTES)
        paths = [f"dir/file_{i}.py" for i in range(10000)]
        assert all(sum(len(p) + 9 for p in b) <= budget
                   for b in gitutil._path_batches(paths, budget))
        # Never above the platform figure, never uselessly small.
        monkeypatch.setattr(os, "sysconf", lambda name: 10**9, raising=False)
        assert gitutil._path_args_budget({}) == gitutil._MAX_PATH_ARGS_BYTES
        monkeypatch.setattr(os, "sysconf", lambda name: 100, raising=False)
        assert gitutil._path_args_budget({}) == 4096

    def test_gives_up_past_the_batch_limit(self, tmp_path, git_env, monkeypatch):
        root, base, paths, untracked = self._review_set(tmp_path)
        monkeypatch.setattr(gitutil, "_MAX_PATH_ARGS_BYTES", 60)
        monkeypatch.setattr(gitutil, "_MAX_PATH_BATCHES", 2)
        ran = _refuse_long_commands(monkeypatch, GIT_CMD_CHARS + 100, OSError(errno.E2BIG, "too long"))
        assert gitutil.get_git_diff(root, base, paths=paths, untracked_paths=untracked) is None
        assert [c for c in ran if "diff" in c] == []

    def test_other_start_failures_are_not_retried(self, tmp_path, git_env, monkeypatch):
        root, base, paths, untracked = self._review_set(tmp_path)
        ran = _refuse_long_commands(monkeypatch, 0, FileNotFoundError(errno.ENOENT, "git"))
        assert gitutil.get_git_diff(root, base, paths=paths, untracked_paths=[]) is None
        assert ran == []

    def test_batches_share_one_time_limit(self, tmp_path, git_env, monkeypatch):
        repo = make_repo(tmp_path / "repo")
        clock = iter([0, 0, 31])
        monkeypatch.setattr(gitutil, "time", types.SimpleNamespace(monotonic=lambda: next(clock)))
        monkeypatch.setattr(gitutil, "_MAX_PATH_ARGS_BYTES", 30)
        ran = _refuse_long_commands(monkeypatch, GIT_CMD_CHARS + 60, OSError(errno.E2BIG, "too long"))
        with pytest.raises(subprocess.TimeoutExpired):
            gitutil._run_git_on_review_paths(
                ["status"], ["a" * 40, "b" * 40, "c" * 40], timeout=30, cwd=str(repo))
        assert len(ran) == 1

    @long_paths
    def test_more_paths_than_one_command_holds(self, tmp_path, git_env):
        repo = make_repo(tmp_path / "repo", {"app.py": "x = 1\n"})
        (repo / "app.py").write_text("x = 2\n")
        _more_than_one_command_holds(repo, [".py", ".txt"])
        paths, base, root, untracked, _ = diffstate.compute_v2_review_set(str(repo), None, None, {})
        assert sum(len(p) for p in untracked) > 2 * 1024 * 1024
        diff = gitutil.get_git_diff(root, base, paths=paths, untracked_paths=untracked)
        assert diff is not None
        # app.py and the 1,500 .py files, from more than one command.
        assert len(gitutil.parse_diff_into_files(diff)) == 1501
        assert diff.count("diff --git ") == 1501


class TestWholeHook:
    @long_paths
    def test_edit_reviewed_beside_more_paths_than_one_command_holds(self, tmp_path, hook_env, stub_api):
        repo = make_repo(tmp_path / "repo", {"app.py": "x = 1\n"})
        run_hook(ups_payload(repo), hook_env)
        (repo / "app.py").write_text(VULN_PY)
        _more_than_one_command_holds(repo, [".txt"])
        rc, so, se = run_hook(stop_payload(repo), hook_env)
        m = metrics_of(so)
        assert m.get("skip_reason") is None, m
        assert m.get("review_set_count") == 3001
        assert stub_api.calls

    def test_review_set_past_the_cap_skips_without_a_diff(self, tmp_path, hook_env, stub_api):
        repo = make_repo(tmp_path / "repo", {"app.py": "x = 1\n"})
        run_hook(ups_payload(repo), hook_env)
        (repo / "app.py").write_text(VULN_PY)
        (repo / "new.py").write_text(VULN_PY)
        rc, so, se = run_hook(stop_payload(repo), {**hook_env, "MAX_REVIEW_SET_PATHS": "1"})
        m = metrics_of(so)
        assert m.get("skip_reason") == 8, m
        # The skip taken after a diff reports how many files the diff held.
        assert "diff_files_count" not in m
        assert not stub_api.calls

    def test_cap_counts_only_reviewable_paths(self, tmp_path, hook_env, stub_api):
        repo = make_repo(tmp_path / "repo", {"app.py": "x = 1\n"})
        run_hook(ups_payload(repo), hook_env)
        (repo / "app.py").write_text(VULN_PY)
        for i in range(20):
            (repo / f"note{i:02d}.txt").write_text("x\n")
        rc, so, se = run_hook(stop_payload(repo), {**hook_env, "MAX_REVIEW_SET_PATHS": "5"})
        m = metrics_of(so)
        assert m.get("skip_reason") is None, m
        assert m.get("review_set_count") == 21
        assert stub_api.calls

    @long_paths
    def test_giving_up_is_reported_as_too_many_paths(self, tmp_path, hook_env, stub_api):
        repo = make_repo(tmp_path / "repo", {"app.py": "x = 1\n"})
        run_hook(ups_payload(repo), hook_env)
        (repo / "app.py").write_text(VULN_PY)
        # 3,000 reviewable names of about 750 bytes: more than four commands.
        _more_than_one_command_holds(repo, [".py"])
        rc, so, se = run_hook(stop_payload(repo), hook_env)
        m = metrics_of(so)
        assert m.get("skip_reason") == 8, m
        assert not stub_api.calls

    @long_paths
    def test_nothing_reviewable_is_reported_as_no_source_files(self, tmp_path, hook_env, stub_api):
        repo = make_repo(tmp_path / "repo", {"app.py": "x = 1\n"})
        run_hook(ups_payload(repo), hook_env)
        _more_than_one_command_holds(repo, [".txt"])
        rc, so, se = run_hook(stop_payload(repo), hook_env)
        m = metrics_of(so)
        assert m.get("skip_reason") == 7, m
        assert not stub_api.calls

    def test_cap_reads_paths_from_the_repo_root(self, tmp_path, hook_env, stub_api):
        # A directory above the repo named like a skipped one (build/) must
        # not make every path look unreviewable.
        repo = make_repo(tmp_path / "build" / "repo", {"app.py": "x = 1\n"})
        run_hook(ups_payload(repo), hook_env)
        (repo / "app.py").write_text(VULN_PY)
        (repo / "new.py").write_text(VULN_PY)
        rc, so, se = run_hook(stop_payload(repo), {**hook_env, "MAX_REVIEW_SET_PATHS": "1"})
        assert metrics_of(so).get("skip_reason") == 8
        assert not stub_api.calls
