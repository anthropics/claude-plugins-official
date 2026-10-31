"""`git add --intent-to-add` puts new files in the Stop review's diff. A user
who cannot write the object store gets a retry with a private object directory;
a failure that stays leaves the new files for a later review, unless the turn's
tracked files were reviewed. The Stop row says
what happened."""
import os
import shutil
import subprocess
import tempfile
from types import SimpleNamespace

import pytest

from conftest import (
    GIT_ENV, VULN_PY, edit_payload, git, make_repo, metrics_of, run_hook,
    stop_payload, ups_payload,
)

import gitutil


def _cannot_write_read_only_dirs():
    with tempfile.TemporaryDirectory() as d:
        os.chmod(d, 0o555)
        try:
            return not os.access(d, os.W_OK)
        finally:
            os.chmod(d, 0o755)


@pytest.fixture
def read_only_objects():
    made = []

    def lock(repo):
        made.append(repo / ".git" / "objects")
        subprocess.run(["chmod", "-R", "a-w", str(made[-1])], check=True)

    yield lock
    for objects in made:
        subprocess.run(["chmod", "-R", "u+w", str(objects)], check=True)


@pytest.mark.skipif(os.name == "nt" or not _cannot_write_read_only_dirs(),
                    reason="needs a user that file permissions apply to")
class TestObjectStoreNotWritable:
    def test_turn_that_only_adds_a_file(self, tmp_path, hook_env, stub_api, read_only_objects):
        repo = make_repo(tmp_path / "repo", {"app.py": "print('hi')\n"})
        read_only_objects(repo)
        before = sorted(p for p in (repo / ".git" / "objects").rglob("*"))
        run_hook(ups_payload(repo), hook_env)
        (repo / "handlers.py").write_text(VULN_PY)
        m = metrics_of(run_hook(stop_payload(repo), hook_env)[1])
        assert m["files_reviewed"] == 1, m
        assert m["add_fail"] == 400001
        assert stub_api.calls
        assert sorted(p for p in (repo / ".git" / "objects").rglob("*")) == before

    def test_tracked_edit_and_new_files(self, tmp_path, hook_env, stub_api, read_only_objects):
        repo = make_repo(tmp_path / "repo", {"app.py": "print('hi')\n"})
        read_only_objects(repo)
        run_hook(ups_payload(repo), hook_env)
        (repo / "app.py").write_text(VULN_PY)
        (repo / "a.py").write_text("print('a')\n")
        (repo / "b.py").write_text("print('b')\n")
        m = metrics_of(run_hook(stop_payload(repo), hook_env)[1])
        assert not m.get("skipped"), m
        assert m["files_reviewed"] == 3
        assert m["add_fail"] == 400002

    def test_linked_worktree_and_packed_repo(self, tmp_path, hook_env, stub_api, read_only_objects):
        repo = make_repo(tmp_path / "repo", {"app.py": "print('hi')\n"})
        git(repo, "repack", "-adq")
        wt = tmp_path / "wt"
        git(repo, "worktree", "add", "-q", "-b", "side", str(wt))
        read_only_objects(repo)
        run_hook(ups_payload(wt), hook_env)
        (wt / "handlers.py").write_text(VULN_PY)
        m = metrics_of(run_hook(stop_payload(wt), hook_env)[1])
        assert m["files_reviewed"] == 1, m
        assert m["add_fail"] == 400001

    def test_private_directory_is_gone_afterwards(self, tmp_path, monkeypatch, read_only_objects):
        d = tmp_path / "tmproot"
        d.mkdir()
        monkeypatch.setattr(tempfile, "tempdir", str(d))
        for k, v in GIT_ENV.items():
            monkeypatch.setenv(k, v)
        repo = make_repo(tmp_path / "repo", {"app.py": "print('hi')\n"})
        read_only_objects(repo)
        (repo / "new.py").write_text("print('new')\n")
        out = gitutil.get_git_diff(str(repo), "HEAD", paths=[str(repo / "new.py")],
                                   untracked_paths=["new.py"])
        gitutil._add_failed["code"] = 0
        assert "new.py" in out
        assert not [p for p in d.rglob("*") if gitutil._TEMP_INDEX_PREFIX in p.name]


class TestPathspecSettings:
    @pytest.mark.parametrize("name", ["GIT_ICASE_PATHSPECS", "GIT_GLOB_PATHSPECS"])
    def test_new_file_is_reviewed(self, tmp_path, hook_env, stub_api, name):
        # git refuses --literal-pathspecs together with these two.
        repo = make_repo(tmp_path / "repo", {"app.py": "print('hi')\n"})
        env = {**hook_env, name: "1"}
        run_hook(ups_payload(repo), env)
        (repo / "handlers.py").write_text(VULN_PY)
        m = metrics_of(run_hook(stop_payload(repo), env)[1])
        assert m["files_reviewed"] == 1, m
        assert "add_fail" not in m


@pytest.mark.skipif(os.name == "nt", reason="the stand-in git is a shell script")
class TestAddThatKeepsFailing:
    def _git_that_refuses_add(self, tmp_path):
        d = tmp_path / "shim"
        d.mkdir()
        real = shutil.which("git")
        shim = d / "git"
        shim.write_text('#!/bin/sh\nfor a in "$@"; do\n'
                        '  [ "$a" = --intent-to-add ] && { echo "fatal: refused" >&2; exit 128; }\n'
                        f'done\nexec "{real}" "$@"\n')
        shim.chmod(0o755)
        return d

    def test_new_file_is_reviewed_once_git_works(self, tmp_path, hook_env, stub_api):
        repo = make_repo(tmp_path / "repo", {"app.py": "print('hi')\n"})
        bad = {**hook_env, "PATH": f"{self._git_that_refuses_add(tmp_path)}{os.pathsep}{hook_env['PATH']}"}
        run_hook(ups_payload(repo), bad)
        (repo / "handlers.py").write_text(VULN_PY)
        run_hook(edit_payload(repo, str(repo / "handlers.py")), bad)
        m = metrics_of(run_hook(stop_payload(repo), bad)[1])
        assert m["skip_reason"] == 6, m
        assert m["add_fail"] == 200001
        assert not stub_api.calls

        run_hook(ups_payload(repo), hook_env)
        m = metrics_of(run_hook(stop_payload(repo), hook_env)[1])
        assert m["files_reviewed"] == 1, m
        assert stub_api.calls

    def test_file_no_edit_tool_wrote(self, tmp_path, hook_env, stub_api):
        repo = make_repo(tmp_path / "repo", {"app.py": "print('hi')\n"})
        bad = {**hook_env, "PATH": f"{self._git_that_refuses_add(tmp_path)}{os.pathsep}{hook_env['PATH']}"}
        run_hook(ups_payload(repo), bad)
        (repo / "handlers.py").write_text(VULN_PY)
        m = metrics_of(run_hook(stop_payload(repo), bad)[1])
        assert m["skip_reason"] == 6, m

        run_hook(ups_payload(repo), hook_env)
        m = metrics_of(run_hook(stop_payload(repo), hook_env)[1])
        assert m["files_reviewed"] == 1, m

    def test_tracked_edit_is_still_reviewed(self, tmp_path, hook_env, stub_api):
        repo = make_repo(tmp_path / "repo", {"app.py": "print('hi')\n"})
        bad = {**hook_env, "PATH": f"{self._git_that_refuses_add(tmp_path)}{os.pathsep}{hook_env['PATH']}"}
        run_hook(ups_payload(repo), bad)
        (repo / "app.py").write_text(VULN_PY)
        (repo / "a.py").write_text("print('a')\n")
        m = metrics_of(run_hook(stop_payload(repo), bad)[1])
        assert m["files_reviewed"] == 1, m
        assert m["add_fail"] == 200001


class TestStopRow:
    def test_add_that_works_reports_nothing(self, tmp_path, hook_env, stub_api):
        repo = make_repo(tmp_path / "repo", {"app.py": "print('hi')\n"})
        run_hook(ups_payload(repo), hook_env)
        (repo / "handlers.py").write_text(VULN_PY)
        m = metrics_of(run_hook(stop_payload(repo), hook_env)[1])
        assert m["files_reviewed"] == 1
        assert "add_fail" not in m


class TestGetGitDiff:
    @pytest.fixture(autouse=True)
    def _env(self, tmp_path, monkeypatch):
        d = tmp_path / "tmproot"
        d.mkdir()
        monkeypatch.setattr(tempfile, "tempdir", str(d))
        for k, v in GIT_ENV.items():
            monkeypatch.setenv(k, v)
        yield
        gitutil._add_failed["code"] = 0

    @pytest.fixture
    def repo(self, tmp_path):
        repo = make_repo(tmp_path / "repo", {"app.py": "print('hi')\n"})
        (repo / "new.py").write_text("print('new')\n")
        return repo

    def _adds_fail_with(self, monkeypatch, outcome):
        real = gitutil._run_git_on_review_paths

        def run(args, paths, timeout, **kwargs):
            if args[0] != "add":
                return real(args, paths, timeout, **kwargs)
            if isinstance(outcome, Exception):
                raise outcome
            return outcome

        monkeypatch.setattr(gitutil, "_run_git_on_review_paths", run)

    def test_any_failed_batch_counts(self, repo, monkeypatch):
        self._adds_fail_with(monkeypatch, [
            SimpleNamespace(returncode=0, stderr=b""),
            SimpleNamespace(returncode=128, stderr=b"fatal: nope"),
        ])
        gitutil.get_git_diff(str(repo), "HEAD", paths=[str(repo / "new.py")],
                             untracked_paths=["new.py"])
        assert gitutil._add_failed["code"] == 200001

    def test_timeout_counts_and_still_gives_no_diff(self, repo, monkeypatch):
        self._adds_fail_with(monkeypatch, subprocess.TimeoutExpired("git", 10))
        assert gitutil.get_git_diff(str(repo), "HEAD", paths=[str(repo / "new.py")],
                                    untracked_paths=["new.py"]) is None
        assert gitutil._add_failed["code"] == 300001

    def test_object_store_refusal_on_both_tries(self, repo, monkeypatch):
        self._adds_fail_with(monkeypatch, [SimpleNamespace(
            returncode=128,
            stderr=b"fatal: cannot create an empty blob in the object database")])
        gitutil.get_git_diff(str(repo), "HEAD", paths=[str(repo / "new.py")],
                             untracked_paths=["new.py"])
        assert gitutil._add_failed["code"] == 100001

    def test_retry_reads_the_repositorys_objects_and_writes_elsewhere(self, repo, monkeypatch):
        seen = []
        real = gitutil._run_git_on_review_paths

        def run(args, paths, timeout, **kwargs):
            if args[0] != "add":
                return real(args, paths, timeout, **kwargs)
            seen.append(kwargs["env"])
            return real(args, paths, timeout, **kwargs) if len(seen) > 1 else [
                SimpleNamespace(returncode=128, stderr=b"nope")]

        monkeypatch.setattr(gitutil, "_run_git_on_review_paths", run)
        out = gitutil.get_git_diff(str(repo), "HEAD", paths=[str(repo / "new.py")],
                                   untracked_paths=["new.py"])
        assert "new.py" in out
        assert "GIT_OBJECT_DIRECTORY" not in seen[0]
        assert seen[1]["GIT_OBJECT_DIRECTORY"].endswith(".objects")
        assert os.path.samefile(seen[1]["GIT_ALTERNATE_OBJECT_DIRECTORIES"],
                                repo / ".git" / "objects")
        assert gitutil._add_failed["code"] == 400001

    def test_retry_timeout_keeps_the_tracked_diff(self, repo, monkeypatch):
        (repo / "app.py").write_text("print('changed')\n")
        real = gitutil._run_git_on_review_paths
        adds = []

        def run(args, paths, timeout, **kwargs):
            if args[0] != "add":
                return real(args, paths, timeout, **kwargs)
            adds.append(args)
            if len(adds) > 1:
                raise subprocess.TimeoutExpired("git", 10)
            return [SimpleNamespace(returncode=128, stderr=b"fatal: nope")]

        monkeypatch.setattr(gitutil, "_run_git_on_review_paths", run)
        out = gitutil.get_git_diff(str(repo), "HEAD", untracked_paths=["new.py"])
        assert "app.py" in out
        assert gitutil._add_failed["code"] == 200001

    def test_a_later_add_that_works_keeps_the_failure(self, repo, monkeypatch):
        gitutil._add_failed["code"] = 300001
        gitutil.get_git_diff(str(repo), "HEAD", paths=[str(repo / "new.py")],
                             untracked_paths=["new.py"])
        assert gitutil._add_failed["code"] == 300001


class TestLeftovers:
    def _private_dir(self, parent, name):
        d = parent / name
        (d / "e6").mkdir(parents=True)
        blob = d / "e6" / "9de29"
        blob.write_bytes(b"x")
        blob.chmod(0o444)
        return d

    def test_removed_with_its_copy(self, tmp_path):
        copy = tmp_path / "security_hook_idx_pid1_abcdefgh"
        copy.write_bytes(b"i")
        self._private_dir(tmp_path, copy.name + ".objects")
        gitutil._remove_copy(str(copy))
        assert not list(tmp_path.iterdir())

    @pytest.mark.skipif(os.name == "nt", reason="no pid check on Windows")
    def test_killed_hooks_directory_is_swept(self, tmp_path):
        p = subprocess.Popen(["git", "--version"], stdout=subprocess.DEVNULL)
        p.wait()
        self._private_dir(tmp_path, f"security_hook_idx_pid{p.pid}_abcdefgh.objects")
        gitutil._sweep_stale_indexes(str(tmp_path), None)
        assert not list(tmp_path.iterdir())

    def test_live_hooks_directory_stays(self, tmp_path):
        self._private_dir(tmp_path, f"security_hook_idx_pid{os.getpid()}_abcdefgh.objects")
        gitutil._sweep_stale_indexes(str(tmp_path), None)
        assert list(tmp_path.iterdir())

    def test_other_directories_stay(self, tmp_path):
        (tmp_path / "security_hook_idx_pid1_abcdefgh.other").mkdir()
        gitutil._sweep_stale_indexes(str(tmp_path), None)
        assert list(tmp_path.iterdir())

    @pytest.mark.skipif(os.name == "nt", reason="needs symlinks")
    def test_link_at_the_private_directory_is_not_followed(self, tmp_path):
        victim = tmp_path / "victim"
        victim.mkdir()
        (victim / "keep").write_text("x")
        copy = tmp_path / "security_hook_idx_pid1_abcdefgh"
        (tmp_path / (copy.name + ".objects")).symlink_to(victim)
        gitutil._remove_copy(str(copy))
        assert (victim / "keep").exists()
