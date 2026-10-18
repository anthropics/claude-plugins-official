"""The Stop diff picks its files before reading any diff and reads them one
at a time (a turn that wrote ~1 GB of data files made one
hook process hold 2-17 GB)."""
import os

from conftest import make_repo

import diffstate
import gitutil

SRC = "import os\nos.system(input())\n"


def _diff(repo):
    paths, base, root, untracked, _m = diffstate.compute_v2_review_set(
        str(repo), None, None, {})
    return gitutil.get_git_diff(root, base, paths=paths, untracked_paths=untracked)


def _count_git_diff_calls(monkeypatch):
    calls = []
    real = gitutil._run_capped

    def spy(cmd, *a, **kw):
        if "diff" in cmd:
            calls.append(cmd)
        return real(cmd, *a, **kw)

    monkeypatch.setattr(gitutil, "_run_capped", spy)
    return calls


def test_pathological_review_set_reads_no_diff(tmp_path, monkeypatch):
    repo = make_repo(tmp_path / "repo")
    for i in range(10 * gitutil._REVIEW_PATH_CAP + 1):
        (repo / f"f{i:04d}.py").write_text(SRC)
    calls = _count_git_diff_calls(monkeypatch)
    assert _diff(repo) == ""
    assert calls == []


def test_over_cap_set_is_diffed_one_file_per_call_riskiest_first(tmp_path, monkeypatch):
    repo = make_repo(tmp_path / "repo")
    for i in range(gitutil._REVIEW_PATH_CAP + 20):
        (repo / f"plain_{i:03d}.py").write_text(SRC)
    (repo / "zz_auth_handler.py").write_text(SRC)
    calls = _count_git_diff_calls(monkeypatch)
    files = [f for f, _ in gitutil.parse_diff_into_files(_diff(repo))]
    assert len(calls) == gitutil._REVIEW_PATH_CAP
    assert all(c[-2] == "--" for c in calls)
    assert len(files) == gitutil._REVIEW_PATH_CAP
    assert "zz_auth_handler.py" in files


def test_large_and_non_source_files_are_not_read(tmp_path, monkeypatch):
    repo = make_repo(tmp_path / "repo")
    (repo / "big.py").write_text("x = 1\n" * (gitutil.MAX_REVIEW_FILE_BYTES // 6 + 10))
    (repo / "photo.png").write_bytes(b"\0" * 1024)
    (repo / "app.py").write_text(SRC)
    calls = _count_git_diff_calls(monkeypatch)
    files = [f for f, _ in gitutil.parse_diff_into_files(_diff(repo))]
    assert files == ["app.py"]
    assert [c[-1] for c in calls] == ["app.py"]


def test_one_file_over_the_output_cap_does_not_drop_the_rest(tmp_path, monkeypatch):
    repo = make_repo(tmp_path / "repo", {"README.md": "init\n", "gone.py": "y = 2\n" * 50_000})
    os.remove(repo / "gone.py")
    (repo / "app.py").write_text(SRC)
    monkeypatch.setattr(gitutil, "MAX_FILE_DIFF_BYTES", 4096)
    files = [f for f, _ in gitutil.parse_diff_into_files(_diff(repo))]
    assert files == ["app.py"]


def test_run_capped_reports_overflow_as_failure(tmp_path):
    rc, out = gitutil._run_capped(["yes"], str(tmp_path), max_bytes=1 << 20)
    assert (rc, out) == (None, None)
