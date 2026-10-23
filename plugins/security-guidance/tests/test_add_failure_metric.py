"""A failed `git add --intent-to-add` leaves new files out of the Stop review's
diff. The review goes on as before; the Stop row says that it happened."""
import os
import subprocess
import tempfile
from types import SimpleNamespace

import pytest

from conftest import (
    GIT_ENV, VULN_PY, make_repo, metrics_of, run_hook, stop_payload,
    ups_payload,
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
        run_hook(ups_payload(repo), hook_env)
        (repo / "handlers.py").write_text(VULN_PY)
        m = metrics_of(run_hook(stop_payload(repo), hook_env)[1])
        assert m["skip_reason"] == 6, m
        assert m["review_set_count"] == 1
        assert m["add_fail"] == 100001
        assert not stub_api.calls

    def test_tracked_edit_is_still_reviewed(self, tmp_path, hook_env, stub_api, read_only_objects):
        repo = make_repo(tmp_path / "repo", {"app.py": "print('hi')\n"})
        read_only_objects(repo)
        run_hook(ups_payload(repo), hook_env)
        (repo / "app.py").write_text(VULN_PY)
        (repo / "a.py").write_text("print('a')\n")
        (repo / "b.py").write_text("print('b')\n")
        m = metrics_of(run_hook(stop_payload(repo), hook_env)[1])
        assert not m.get("skipped"), m
        assert m["files_reviewed"] == 1
        assert m["add_fail"] == 100002


class TestStopRow:
    def test_other_git_error(self, tmp_path, hook_env, stub_api):
        # git refuses --literal-pathspecs together with a user's icase setting.
        repo = make_repo(tmp_path / "repo", {"app.py": "print('hi')\n"})
        env = {**hook_env, "GIT_ICASE_PATHSPECS": "1"}
        run_hook(ups_payload(repo), env)
        (repo / "handlers.py").write_text(VULN_PY)
        m = metrics_of(run_hook(stop_payload(repo), env)[1])
        assert m["skip_reason"] == 6, m
        assert m["add_fail"] == 200001

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

    def test_object_store_refusal(self, repo, monkeypatch):
        self._adds_fail_with(monkeypatch, [SimpleNamespace(
            returncode=128,
            stderr=b"fatal: cannot create an empty blob in the object database")])
        gitutil.get_git_diff(str(repo), "HEAD", paths=[str(repo / "new.py")],
                             untracked_paths=["new.py"])
        assert gitutil._add_failed["code"] == 100001

    def test_a_later_add_that_works_keeps_the_failure(self, repo, monkeypatch):
        gitutil._add_failed["code"] = 300001
        gitutil.get_git_diff(str(repo), "HEAD", paths=[str(repo / "new.py")],
                             untracked_paths=["new.py"])
        assert gitutil._add_failed["code"] == 300001
