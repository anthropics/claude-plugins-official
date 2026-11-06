import json
import os
import shutil

import pytest

from conftest import (
    VULN_PY, edit_payload, make_repo, metrics_of, run_hook, stop_payload, ups_payload,
)

OFF_SWITCHES = [
    pytest.param({"ENABLE_STOP_REVIEW": "0"}, id="stop-review-off"),
    pytest.param({"ENABLE_CODE_SECURITY_REVIEW": "0"}, id="all-reviews-off"),
]
OLD = "import os\nos.system(cmd)\n"


@pytest.fixture
def on(hook_env, tmp_path):
    """hook_env with the Stop review on, and a `git` first on PATH that
    records each call before running it."""
    shim = tmp_path / "bin"
    shim.mkdir()
    log = tmp_path / "git.log"
    log.write_text("")
    (shim / "git").write_text(
        f'#!/bin/sh\nprintf \'%s\\n\' "$*" >> "{log}"\nexec "{shutil.which("git")}" "$@"\n')
    (shim / "git").chmod(0o755)
    env = {k: v for k, v in hook_env.items() if k != "CLAUDE_CODE_REMOTE_SESSION_ID"}
    env.update(HOME=str(tmp_path), PATH=f"{shim}{os.pathsep}{hook_env['PATH']}",
               GIT_CALLS=str(log))
    return env


def _listed_untracked(env):
    with open(env["GIT_CALLS"]) as f:
        return any("ls-files --others" in line for line in f)


def _state(env, session_id="s1"):
    path = os.path.join(env["SECURITY_WARNINGS_STATE_DIR"],
                        f"security_warnings_state_{session_id}.json")
    with open(path) as f:
        return json.load(f)


def _repo(tmp_path):
    repo = make_repo(tmp_path / "repo", {"app.py": OLD})
    (repo / "notes.txt").write_text("scratch\n")
    return repo


def _write_payload(cwd, file_path, content, session_id="s1"):
    return {
        "session_id": session_id,
        "hook_event_name": "PostToolUse",
        "tool_name": "Write",
        "tool_input": {"file_path": str(file_path), "content": content},
        "tool_response": {},
        "cwd": str(cwd),
    }


def _reviewed(stub_api):
    n = len(stub_api.calls)
    del stub_api.calls[:]
    return n > 0


pytestmark = pytest.mark.skipif(os.name == "nt", reason="the git recorder is a sh script")


class TestPrompt:
    def test_review_on_takes_the_snapshot(self, tmp_path, on):
        repo = _repo(tmp_path)
        rc, _, _ = run_hook(ups_payload(repo), on)
        assert rc == 0
        assert _listed_untracked(on)
        assert list(_state(on)["untracked_at_baseline"]) == ["notes.txt"]

    @pytest.mark.parametrize("off", OFF_SWITCHES)
    def test_review_off_does_not_list_the_worktree(self, tmp_path, on, off):
        repo = _repo(tmp_path)
        rc, _, _ = run_hook(ups_payload(repo), {**on, **off})
        assert rc == 0
        assert not _listed_untracked(on)
        assert "untracked_at_baseline" not in _state(on)

    @pytest.mark.parametrize("off", OFF_SWITCHES)
    def test_review_off_write_filter_still_knows_what_was_there(self, tmp_path, on, off):
        """The stash baseline is still captured: a full-file Write that keeps
        a risky call from before the prompt is not reported as new."""
        repo = _repo(tmp_path)
        env = {**on, **off, "CLAUDE_PROJECT_DIR": str(repo)}
        (repo / "app.py").write_text(OLD + "# edited before the prompt\n")
        run_hook(ups_payload(repo), env)

        _rc, out, _ = run_hook(_write_payload(repo, repo / "app.py", OLD + "print('x')\n"), env)
        assert "additionalContext" not in out
        _rc, out, _ = run_hook(_write_payload(
            repo, repo / "app.py", OLD + "import pickle\npickle.loads(data)\n"), env)
        assert "pickle" in out and "os.system" not in out

    def test_review_off_uses_the_repo_hint_without_listing(self, tmp_path, on):
        repo = _repo(tmp_path)
        outside = tmp_path / "not-a-repo"
        outside.mkdir()
        (repo / "app.py").write_text(VULN_PY)
        # The hint a commit review that resolved the repo leaves behind.
        with open(os.path.join(on["SECURITY_WARNINGS_STATE_DIR"],
                               "security_warnings_state_s1.json"), "w") as f:
            json.dump({"shown_warnings": [], "repo_root_hint": str(repo)}, f)
        rc, _, _ = run_hook(ups_payload(outside), {**on, "ENABLE_STOP_REVIEW": "0"})
        assert rc == 0
        assert not _listed_untracked(on)
        assert _state(on).get("baseline_sha")

    def test_review_off_drops_the_snapshot_of_an_older_baseline(self, tmp_path, on):
        repo = _repo(tmp_path)
        run_hook(ups_payload(repo), on)
        assert "untracked_at_baseline" in _state(on)
        run_hook(ups_payload(repo), {**on, "ENABLE_STOP_REVIEW": "0"})
        assert "untracked_at_baseline" not in _state(on)


class TestTurn:
    def test_review_on_reviews_only_new_untracked_files(self, tmp_path, on, stub_api):
        repo = _repo(tmp_path)
        (repo / "old_vuln.py").write_text(VULN_PY)
        run_hook(ups_payload(repo), on)
        _rc, out, _ = run_hook(stop_payload(repo), on)
        assert metrics_of(out)["skip_reason"] == 9      # empty review set
        assert not _reviewed(stub_api)

        run_hook(ups_payload(repo), on)
        (repo / "new_vuln.py").write_text(VULN_PY)
        _rc, out, _ = run_hook(stop_payload(repo), on)
        assert metrics_of(out)["files_reviewed"] == 1
        assert _reviewed(stub_api)

    @pytest.mark.parametrize("off", OFF_SWITCHES)
    def test_review_switched_back_on_at_the_next_prompt(self, tmp_path, on, stub_api, off):
        """Old untracked files are not reviewed as this turn's work."""
        repo = _repo(tmp_path)
        (repo / "old_vuln.py").write_text(VULN_PY)
        run_hook(ups_payload(repo), {**on, **off})
        run_hook(stop_payload(repo), {**on, **off})

        run_hook(ups_payload(repo), on)
        _rc, out, _ = run_hook(stop_payload(repo), on)
        assert metrics_of(out)["skip_reason"] == 9
        assert not _reviewed(stub_api)

    def test_review_switched_back_on_after_an_interrupted_turn(self, tmp_path, on, stub_api):
        """The interrupted turn's baseline is kept, so its edit is reviewed,
        and the old untracked file beside it is not."""
        off = {**on, "ENABLE_STOP_REVIEW": "0"}
        repo = _repo(tmp_path)
        (repo / "old_vuln.py").write_text(VULN_PY)
        run_hook(ups_payload(repo), off)
        (repo / "app.py").write_text(VULN_PY)
        run_hook(edit_payload(repo, repo / "app.py"), off)   # no Stop: interrupted
        baseline = _state(on)["baseline_sha"]

        run_hook(ups_payload(repo), on)
        assert _state(on)["baseline_sha"] == baseline
        _rc, out, _ = run_hook(stop_payload(repo), on)
        assert metrics_of(out)["files_reviewed"] == 1
        assert _reviewed(stub_api)
