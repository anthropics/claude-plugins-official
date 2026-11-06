"""The SDK bootstrap's Python subprocesses must not import from the repository.

`python -c` and `python -m` put the working directory first on the import
path, and hooks run in the user's repository, so every interpreter the
bootstrap starts runs from a directory the plugin owns.
"""
import ast
import os
import sys
from pathlib import Path

import pytest

import ensure_agent_sdk

from conftest import HOOKS_DIR, make_repo


def _spawns(tree):
    for node in ast.walk(tree):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr in ("run", "Popen", "call", "check_call", "check_output")
                and isinstance(node.func.value, ast.Name) and node.func.value.id == "subprocess"):
            yield node


def test_every_spawn_sets_a_plugin_owned_cwd():
    tree = ast.parse((HOOKS_DIR / "ensure_agent_sdk.py").read_text())
    calls = list(_spawns(tree))
    assert len(calls) >= 6
    for call in calls:
        cwd = [k for k in call.keywords if k.arg == "cwd"]
        assert cwd, f"subprocess call on line {call.lineno} inherits the hook's working directory"
        assert ast.unparse(cwd[0].value) == "_spawn_cwd()", call.lineno


def test_spawn_cwd_is_the_state_dir(tmp_path, monkeypatch):
    state = tmp_path / "state"
    monkeypatch.setenv("SECURITY_WARNINGS_STATE_DIR", str(state))
    assert ensure_agent_sdk._spawn_cwd() == str(state)
    assert state.is_dir()


def test_relative_state_dir_is_made_absolute(tmp_path, monkeypatch):
    # Children run in the state dir, so a relative one would be resolved twice.
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("SECURITY_WARNINGS_STATE_DIR", "rel")
    assert ensure_agent_sdk._spawn_cwd() == str(tmp_path / "rel")


@pytest.mark.skipif(sys.platform == "win32", reason="symlinked interpreter")
@pytest.mark.skipif(sys.version_info < (3, 10), reason="bootstrap stops before the probe")
def test_health_check_ignores_module_in_repo(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    make_repo(repo)
    marker = tmp_path / "imported-from-repo"
    (repo / "claude_agent_sdk.py").write_text(
        f"open({str(marker)!r}, 'w').write('x')\n")

    state = tmp_path / "state"
    venv_bin = state / "agent-sdk-venv" / ("Scripts" if sys.platform == "win32" else "bin")
    venv_bin.mkdir(parents=True)
    venv_py = venv_bin / ("python.exe" if sys.platform == "win32" else "python")
    os.symlink(sys.executable, venv_py)

    monkeypatch.setenv("SECURITY_WARNINGS_STATE_DIR", str(state))
    monkeypatch.chdir(repo)
    monkeypatch.setattr(ensure_agent_sdk, "_sdk_on_syspath", lambda: False)
    # No rebuild if the probe fails: this test only covers the probe.
    ensure_agent_sdk._write_cooldown(state)

    outcome, _, _ = ensure_agent_sdk.main()

    assert outcome in (ensure_agent_sdk.NOOP_VENV, ensure_agent_sdk.SKIP_COOLDOWN)
    assert not marker.exists()
