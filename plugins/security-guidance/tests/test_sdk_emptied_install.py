"""An SDK install whose package directory lost its files is rebuilt.

`import claude_agent_sdk` succeeds on an empty directory (Python imports it
as a namespace package), so the bootstrap reported a healthy venv, the
reviewer's `from claude_agent_sdk import ...` failed on every commit, and
nothing repaired it until the venv was deleted by hand. See #6612.
"""
import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

import _base
import ensure_agent_sdk as boot
from test_sdk_bootstrap_switches import SWITCHES


def _fill(pkg):
    pkg.mkdir(parents=True, exist_ok=True)
    (pkg / "__init__.py").write_text("AssistantMessage = object\n")
    (pkg / "__pycache__").mkdir(exist_ok=True)


def _empty(pkg):
    for f in pkg.rglob("*"):
        if f.is_file():
            f.unlink()


@pytest.fixture
def venv(tmp_path, monkeypatch):
    """A real venv (no pip, so it is quick) holding a stand-in SDK package;
    the build commands are recorded instead of run, the probes run for real."""
    for name in SWITCHES + ("PYTHONPATH",):
        monkeypatch.delenv(name, raising=False)
    state = tmp_path / "state"
    monkeypatch.setenv("SECURITY_WARNINGS_STATE_DIR", str(state))
    monkeypatch.setattr(boot, "_sdk_on_syspath", lambda: False)
    monkeypatch.setattr(boot, "_near_git_repo", lambda: True)
    subprocess.run([sys.executable, "-m", "venv", "--without-pip",
                    str(state / "agent-sdk-venv")], check=True)
    pkg = Path(_base.agent_sdk_site_dirs(str(state))[0]) / "claude_agent_sdk"
    _fill(pkg)
    real_run = subprocess.run
    builds = []

    def run(cmd, **kwargs):
        cmd = [str(c) for c in cmd]
        if "-m" in cmd:
            builds.append(cmd)
            return subprocess.CompletedProcess(cmd, 0, b"", b"")
        return real_run(cmd, **kwargs)
    monkeypatch.setattr(boot.subprocess, "run", run)
    return state, pkg, builds


def test_complete_install_is_left_alone(venv):
    state, _, builds = venv
    outcome = boot.main()[0]
    assert outcome == boot.NOOP_VENV and builds == []
    assert "sdk_venv_emptied" not in boot._install_context_metrics(outcome, state)


def test_emptied_install_is_rebuilt_and_counted(venv):
    state, pkg, builds = venv
    _empty(pkg)
    outcome = boot.main()[0]
    assert outcome == boot.BUILT
    assert builds[0][1:4] == ["-m", "venv", "--clear"]
    assert any("pip" in c and "claude-agent-sdk" in c for c in builds)
    assert boot._install_context_metrics(outcome, state)["sdk_venv_emptied"] == 1
    # The count belongs to the run that found it, not to later ones.
    _fill(pkg)
    outcome = boot.main()[0]
    assert outcome == boot.NOOP_VENV
    assert "sdk_venv_emptied" not in boot._install_context_metrics(outcome, state)


def test_venv_that_never_held_the_sdk_is_not_counted_as_emptied(venv):
    state, pkg, builds = venv
    _empty(pkg)
    (pkg / "__pycache__").rmdir()
    pkg.rmdir()
    outcome = boot.main()[0]
    assert outcome == boot.BUILT and builds
    assert "sdk_venv_emptied" not in boot._install_context_metrics(outcome, state)


# An SDK installed for the interpreter running the tests is found behind the
# emptied directory, which hides what this test looks at.
@pytest.mark.skipif(importlib.util.find_spec("claude_agent_sdk") is not None,
                    reason="claude_agent_sdk is installed for this interpreter")
def test_emptied_fallback_install_is_not_reused(tmp_path, monkeypatch):
    monkeypatch.delenv("PYTHONPATH", raising=False)
    pkg = boot._target_dir(tmp_path) / "claude_agent_sdk"
    _fill(pkg)
    assert boot._target_sdk_importable(tmp_path) is True
    _empty(pkg)
    assert boot._target_sdk_importable(tmp_path) is False
