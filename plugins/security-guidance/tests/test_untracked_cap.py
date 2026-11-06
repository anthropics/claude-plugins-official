import os
import time

from conftest import make_repo, metrics_of, run_hook, stop_payload, ups_payload

import diffstate

SRC = "import os\nos.system(input())\n"


def _review(repo, snapshot):
    paths, _base, root, _untracked, metrics = diffstate.compute_v2_review_set(
        str(repo), None, None, snapshot)
    return sorted(os.path.relpath(p, root) for p in paths), metrics


class TestCappedSnapshot:
    def _repo(self, tmp_path, monkeypatch, n=30, cap=10):
        monkeypatch.setattr(diffstate, "UNTRACKED_BASELINE_CAP", cap)
        monkeypatch.setattr(diffstate, "_CAPPED_BASELINE_SLACK_NS", 20_000_000)
        repo = make_repo(tmp_path / "repo")
        for i in range(n):
            (repo / f"old_{i:03d}.py").write_text(SRC)
        time.sleep(0.1)
        return repo

    def test_snapshot_records_when_it_was_capped(self, tmp_path, monkeypatch):
        repo = self._repo(tmp_path, monkeypatch)
        before = time.time_ns()
        snap = diffstate._list_untracked(str(repo))
        assert before <= snap[diffstate.UNTRACKED_CAPPED_AT_KEY] <= time.time_ns()
        assert len(snap) == 10 + 1

    def test_uncapped_snapshot_has_no_marker(self, tmp_path, monkeypatch):
        repo = self._repo(tmp_path, monkeypatch, n=5)
        assert diffstate.UNTRACKED_CAPPED_AT_KEY not in diffstate._list_untracked(str(repo))

    def test_files_past_the_cap_are_not_reviewed_when_untouched(self, tmp_path, monkeypatch):
        repo = self._repo(tmp_path, monkeypatch)
        snap = diffstate._list_untracked(str(repo))
        review, metrics = _review(repo, snap)
        assert review == []
        assert metrics["preexisting_untracked_excluded"] == 30

    def test_new_and_edited_files_past_the_cap_are_reviewed(self, tmp_path, monkeypatch):
        repo = self._repo(tmp_path, monkeypatch)
        snap = diffstate._list_untracked(str(repo))
        time.sleep(0.1)
        (repo / "zz_new.py").write_text(SRC)
        (repo / "old_025.py").write_text(SRC + "eval(input())\n")
        (repo / "old_003.py").write_text(SRC + "eval(input())\n")  # inside the cap
        review, _ = _review(repo, snap)
        assert review == ["old_003.py", "old_025.py", "zz_new.py"]

    def test_file_moved_in_with_an_old_mtime_is_reviewed(self, tmp_path, monkeypatch):
        repo = self._repo(tmp_path, monkeypatch)
        snap = diffstate._list_untracked(str(repo))
        time.sleep(0.1)
        new = repo / "zz_extracted.py"
        new.write_text(SRC)
        os.utime(new, (1_600_000_000, 1_600_000_000))  # as tar or cp -p would leave it
        review, _ = _review(repo, snap)
        assert review == ["zz_extracted.py"]


def test_stop_hook_does_not_re_review_files_past_the_cap(tmp_path, hook_env, stub_api):
    """More untracked files than the snapshot holds: the same old files must
    not be sent for review turn after turn (#6407)."""
    repo = make_repo(tmp_path / "repo")
    n_files = diffstate.UNTRACKED_BASELINE_CAP + 60
    for i in range(n_files):
        (repo / f"old_{i:05d}.py").write_text(SRC)
    time.sleep(2.2)  # older than the snapshot by more than the timestamp slack

    for _turn in range(2):
        run_hook(ups_payload(repo), hook_env)
        _rc, stdout, _err = run_hook(stop_payload(repo), hook_env)
        # Telemetry: a count above the cap is how this path shows up.
        assert metrics_of(stdout)["preexisting_untracked_excluded"] == n_files
    assert stub_api.calls == []

    run_hook(ups_payload(repo), hook_env)
    (repo / "zz_new.py").write_text(SRC)
    run_hook(stop_payload(repo), hook_env)
    assert len([c for c in stub_api.calls if "messages" in c]) == 1
