"""The agent SDK is not installed for reviews that are switched off.

ensure_agent_sdk.py (SessionStart) and the PostToolUse rescue spawn built a
venv of a few hundred MB whatever the environment said, including under
SECURITY_GUIDANCE_DISABLE=1, and the rescue started ensure_agent_sdk.py again
every five minutes on machines whose SDK lives in that venv. See #5331.
"""
import importlib.util
import subprocess
import sys

import pytest

from conftest import HOOKS_DIR
import _base
import ensure_agent_sdk as boot
import llm
import security_reminder_hook as hook

OFF = [
    {"SECURITY_GUIDANCE_DISABLE": "1"},
    {"SECURITY_GUIDANCE_DISABLE": "true"},
    {"ENABLE_SECURITY_REMINDER": "0"},
    {"ENABLE_CODE_SECURITY_REVIEW": "0"},
    {"ENABLE_STOP_REVIEW": "0", "ENABLE_COMMIT_REVIEW": "0"},
]
STILL_ON = [{}, {"ENABLE_STOP_REVIEW": "0"}, {"ENABLE_COMMIT_REVIEW": "0"},
            {"SECURITY_GUIDANCE_DISABLE": "0"}]
SWITCHES = ("SECURITY_GUIDANCE_DISABLE", "ENABLE_SECURITY_REMINDER",
            "ENABLE_CODE_SECURITY_REVIEW", "ENABLE_STOP_REVIEW", "ENABLE_COMMIT_REVIEW")


@pytest.fixture
def state(tmp_path, monkeypatch):
    """Empty state dir, no SDK in the interpreter, switches unset."""
    for name in SWITCHES:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("SECURITY_WARNINGS_STATE_DIR", str(tmp_path / "state"))
    monkeypatch.setattr(boot, "_sdk_on_syspath", lambda: False)
    return tmp_path / "state"


@pytest.fixture
def builds(monkeypatch):
    """Records the venv / pip commands instead of running them."""
    calls = []

    def run(cmd, **kwargs):
        calls.append([str(c) for c in cmd])
        return subprocess.CompletedProcess(cmd, 0, b"", b"")
    monkeypatch.setattr(boot.subprocess, "run", run)
    return calls


@pytest.fixture
def spawns(state, monkeypatch):
    """Records the rescue's detached starts of ensure_agent_sdk.py."""
    calls = []
    monkeypatch.setattr(importlib.util, "find_spec", lambda name: None)
    monkeypatch.setattr(hook, "_SDK_BOOTSTRAP_THROTTLE", str(state / ".sdk_bootstrap_spawned"))
    monkeypatch.setattr(hook.subprocess, "Popen", lambda cmd, **kw: calls.append(cmd))
    return calls


def _install(root, finished=True):
    pkg = root / "claude_agent_sdk"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text("")
    if finished:
        (root / "claude_agent_sdk-0.2.0.dist-info").mkdir()


@pytest.mark.parametrize("env", OFF)
def test_session_start_builds_nothing_when_reviews_are_off(state, builds, monkeypatch, env):
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    assert boot.main() == (boot.SKIP_REVIEWS_OFF, "", "")
    assert builds == [] and not state.exists()


@pytest.mark.parametrize("env", STILL_ON)
def test_session_start_still_builds_when_a_review_can_run(state, builds, monkeypatch, env):
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    assert boot.main()[0] == boot.BUILT
    assert [c[1:3] for c in builds] == [["-m", "venv"], ["-m", "pip"]]


@pytest.mark.parametrize("env", OFF[2:])
def test_rescue_does_not_start_the_bootstrap_when_reviews_are_off(spawns, monkeypatch, env):
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    hook._maybe_bootstrap_agent_sdk_async()
    assert spawns == []


def test_rescue_starts_the_bootstrap_once_when_nothing_is_installed(spawns):
    hook._maybe_bootstrap_agent_sdk_async()
    hook._maybe_bootstrap_agent_sdk_async()
    assert len(spawns) == 1 and spawns[0][1].endswith("ensure_agent_sdk.py")


@pytest.mark.parametrize("where", [
    "agent-sdk-venv/lib/python3.12/site-packages",
    "agent-sdk-venv/Lib/site-packages",
    "agent-sdk-libs",
])
def test_rescue_leaves_an_existing_install_alone(spawns, state, where):
    _install(state / where)
    hook._maybe_bootstrap_agent_sdk_async()
    assert spawns == [] and not (state / ".sdk_bootstrap_spawned").exists()


def test_rescue_still_runs_for_an_install_that_was_cut_short(spawns, state):
    _install(state / "agent-sdk-venv/lib/python3.12/site-packages", finished=False)
    hook._maybe_bootstrap_agent_sdk_async()
    assert len(spawns) == 1


def test_reviewer_and_bootstrap_agree_on_where_the_sdk_is_installed(state, monkeypatch):
    for where in ("agent-sdk-venv/lib/python3.12/site-packages", "agent-sdk-libs"):
        _install(state / where)
    monkeypatch.setattr(sys, "path", list(sys.path))
    assert llm._inject_agent_sdk_venv_into_syspath(str(state))
    assert {str(state / "agent-sdk-venv/lib/python3.12/site-packages"),
            str(state / "agent-sdk-libs")} <= set(sys.path)


def test_switches_are_read_the_same_way_as_the_hook_reads_them(monkeypatch):
    for env in OFF + STILL_ON:
        for name in SWITCHES:
            monkeypatch.delenv(name, raising=False)
        for k, v in env.items():
            monkeypatch.setenv(k, v)
        out = subprocess.run(
            [sys.executable, "-c",
             "import security_reminder_hook as h; "
             "print(h.SECURITY_GUIDANCE_DISABLED or not h.ENABLE_CODE_SECURITY_REVIEW"
             " or not (h.ENABLE_STOP_REVIEW or h.ENABLE_COMMIT_REVIEW))"],
            cwd=HOOKS_DIR, capture_output=True, text=True).stdout.strip()
        assert out == str(_base.llm_reviews_switched_off()), env


def test_disabled_plugin_says_nothing_on_a_python_below_3_10(state, builds, monkeypatch):
    monkeypatch.setenv("SECURITY_GUIDANCE_DISABLE", "1")
    monkeypatch.setattr(boot.sys, "version_info", (3, 9, 6, "final", 0))
    assert boot.main()[0] == boot.SKIP_REVIEWS_OFF


def test_install_the_session_cannot_use_is_counted(state, tmp_path, monkeypatch):
    monkeypatch.setattr(llm, "HAS_API_CREDENTIALS", False)
    monkeypatch.setattr(boot, "_near_git_repo", lambda: False)
    assert boot._install_context_metrics(boot.BUILT, state) == {"sdk_no_creds": 1, "sdk_no_git": 1}
    assert boot._install_context_metrics(boot.BUILD_FAILED, state) == {}
    monkeypatch.setattr(llm, "HAS_API_CREDENTIALS", True)
    monkeypatch.setattr(boot, "_near_git_repo", lambda: True)
    assert boot._install_context_metrics(boot.NOOP_VENV, state) == {}


def test_session_directory_in_or_holding_a_repository(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
    if boot._near_git_repo():
        pytest.skip("the temp dir is itself inside a git work tree")
    (tmp_path / "ws" / "repo" / ".git").mkdir(parents=True)
    (tmp_path / "ws" / "repo" / "src").mkdir()
    for inside in ("ws", "ws/repo", "ws/repo/src"):
        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path / inside))
        assert boot._near_git_repo(), inside


@pytest.mark.parametrize("cfg, counted", [
    ("home = /usr/bin\nversion = 3.99.1\n", {"sdk_venv_py": 399}),
    ("home = /usr/bin\nversion_info = 3.99.1.final.0\n", {"sdk_venv_py": 399}),
    (f"version = {sys.version_info[0]}.{sys.version_info[1]}.0\n", {}),
    ("home = /usr/bin\n", {}),
])
def test_venv_built_by_another_python_is_counted(state, monkeypatch, cfg, counted):
    monkeypatch.setattr(boot, "_near_git_repo", lambda: True)
    monkeypatch.setattr(llm, "HAS_API_CREDENTIALS", True)
    (state / "agent-sdk-venv").mkdir(parents=True)
    (state / "agent-sdk-venv" / "pyvenv.cfg").write_text(cfg)
    assert boot._install_context_metrics(boot.NOOP_VENV, state) == counted
    assert boot._install_context_metrics(boot.BUILT, state) == {}
