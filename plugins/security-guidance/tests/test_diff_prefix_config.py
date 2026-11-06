"""A user's diff prefix settings must not hide files from the reviews."""
import os
import subprocess

import pytest

from conftest import (
    GIT_ENV, VULN_PY, commit_file, bash_payload, git, make_repo, metrics_of,
    run_hook, stop_payload, ups_payload,
)

import gitutil

PREFIX_CONFIGS = [
    ("diff.mnemonicPrefix", "true"),
    ("diff.noprefix", "true"),
    ("diff.srcPrefix", "x/"),
    ("diff.dstPrefix", "y/"),
]


@pytest.fixture
def git_env(monkeypatch):
    for k, v in GIT_ENV.items():
        monkeypatch.setenv(k, v)


@pytest.mark.parametrize("key,value", PREFIX_CONFIGS)
class TestParsers:
    def test_work_tree_diff(self, tmp_path, git_env, key, value):
        repo = make_repo(tmp_path / "repo", {"app.py": "x = 1\n"})
        git(repo, "config", key, value)
        (repo / "app.py").write_text("x = 1\ny = 2\n")
        diff = gitutil.get_git_diff(str(repo), "HEAD")
        assert [f for f, _ in gitutil.parse_diff_into_files(diff)] == ["app.py"]
        assert gitutil.extract_file_paths_from_diff(diff) == ["app.py"]

    def test_commit_diff(self, tmp_path, git_env, key, value):
        repo = make_repo(tmp_path / "repo", {"app.py": "x = 1\n"})
        git(repo, "config", key, value)
        commit_file(repo, "app.py", "x = 1\ny = 2\n")
        show = subprocess.run(
            [*gitutil.GIT_CMD, "show", "-p", "--no-color", "HEAD", "--"],
            cwd=repo, capture_output=True,
        ).stdout.decode("utf-8", errors="replace")
        assert [f for f, _ in gitutil.parse_diff_into_files(show)] == ["app.py"]
        diff = gitutil._git_diff_range(str(repo), "HEAD~1")
        assert [f for f, _ in gitutil.parse_diff_into_files(diff)] == ["app.py"]


@pytest.mark.parametrize("key,value", PREFIX_CONFIGS[:2])
class TestWholeHook:
    def test_stop_review_runs(self, tmp_path, hook_env, stub_api, key, value):
        repo = make_repo(tmp_path / "repo", {"app.py": "x = 1\n"})
        git(repo, "config", key, value)
        run_hook(ups_payload(repo), hook_env)
        (repo / "app.py").write_text(VULN_PY)
        rc, so, se = run_hook(stop_payload(repo), hook_env)
        m = metrics_of(so)
        assert m.get("skip_reason") is None, m
        assert stub_api.calls


class TestWholeHookCommit:
    def test_commit_review_runs_with_noprefix(self, tmp_path, hook_env, stub_api):
        repo = make_repo(tmp_path / "repo", {"app.py": "x = 1\n"})
        git(repo, "config", "diff.noprefix", "true")
        sha, out = commit_file(repo, "app.py", VULN_PY)
        rc, so, se = run_hook(bash_payload(repo, "git commit -m change", stdout=out), hook_env)
        assert metrics_of(so).get("skip_reason") != 30
