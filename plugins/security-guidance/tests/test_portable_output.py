import json
import os
import subprocess
import sys

import pytest

from conftest import (
    HOOKS_DIR, STUB_VULN, VULN_PY, edit_payload, metrics_of, run_hook, stop_payload, ups_payload,
)

# What a host with a closed hook output schema accepts.
STOP_FIELDS = {"continue", "decision", "reason", "stopReason", "suppressOutput", "systemMessage"}
POST_TOOL_USE_FIELDS = STOP_FIELDS | {"hookSpecificOutput"}
HOST_MARKERS = ("CLAUDECODE", "CLAUDE_CODE_ENTRYPOINT", "PLUGIN_ROOT",
                "SECURITY_GUIDANCE_PORTABLE_OUTPUT")


def _env(hook_env, **extra):
    env = {k: v for k, v in hook_env.items() if k not in HOST_MARKERS}
    env.update(extra)
    return env


def _objects(stdout):
    lines = [l for l in stdout.splitlines() if l.strip()]
    return [json.loads(l) for l in lines]


def _review_with_finding(workspace, env, stub_api):
    ws, repo = workspace
    stub_api.vulns = [STUB_VULN]
    run_hook(ups_payload(repo), env)
    (repo / "app.py").write_text(VULN_PY)
    run_hook(edit_payload(repo, repo / "app.py", VULN_PY), env)
    return run_hook(stop_payload(repo), env)


class TestOtherHost:
    def test_stop_skip_path_prints_only_standard_fields(self, workspace, hook_env):
        ws, repo = workspace
        rc, so, se = run_hook(stop_payload(repo), _env(hook_env, PLUGIN_ROOT=str(ws)))
        assert rc == 0
        assert _objects(so) == [{}]

    def test_stop_finding_keeps_the_block_and_the_guidance(self, workspace, hook_env, stub_api):
        rc, so, se = _review_with_finding(workspace, _env(hook_env, PLUGIN_ROOT="/p"), stub_api)
        (out,) = _objects(so)
        assert set(out) <= STOP_FIELDS, out
        assert out["decision"] == "block"
        assert "command_injection" in out["reason"]
        assert "command_injection" in se

    def test_pattern_warning_keeps_the_guidance(self, workspace, hook_env):
        ws, repo = workspace
        env = _env(hook_env, PLUGIN_ROOT="/p")
        (repo / "app.py").write_text(VULN_PY)
        rc, so, se = run_hook(edit_payload(repo, repo / "app.py", VULN_PY), env)
        assert rc == 0
        (out,) = _objects(so)
        assert set(out) <= POST_TOOL_USE_FIELDS, out
        assert out["hookSpecificOutput"]["additionalContext"]

    def test_kill_switch_path(self, workspace, hook_env):
        ws, repo = workspace
        env = _env(hook_env, PLUGIN_ROOT="/p", SECURITY_GUIDANCE_DISABLE="1")
        rc, so, se = run_hook(stop_payload(repo), env)
        assert rc == 0
        assert all(set(o) <= STOP_FIELDS for o in _objects(so))


    def test_mode_is_not_changed_by_the_hook_process_itself(self, hook_env):
        code = ("import os, _base\n"
                "os.environ['CLAUDE_CODE_ENTRYPOINT'] = 'sdk-py'\n"
                "_base.write_hook_output({'metrics': {'x': 1}, 'reason': 'r'})\n")
        r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                           cwd=HOOKS_DIR, env=_env(hook_env, PLUGIN_ROOT="/p"), timeout=60)
        assert _objects(r.stdout) == [{"reason": "r"}], r.stderr


class TestClaudeCodeUnchanged:
    @pytest.mark.parametrize("extra", [
        {},
        {"PLUGIN_ROOT": "/p", "CLAUDECODE": "1"},
        {"PLUGIN_ROOT": "/p", "CLAUDE_CODE_ENTRYPOINT": "cli"},
        {"PLUGIN_ROOT": "/p", "SECURITY_GUIDANCE_PORTABLE_OUTPUT": "0"},
    ])
    def test_metrics_and_summary_are_still_sent(self, workspace, hook_env, stub_api, extra):
        rc, so, se = _review_with_finding(workspace, _env(hook_env, **extra), stub_api)
        (out,) = _objects(so)
        assert out["metrics"]["vulns_found"] == 1
        assert out["rewakeSummary"]
        assert out["decision"] == "block"

    def test_forced_on_under_claude_code(self, workspace, hook_env):
        ws, repo = workspace
        env = _env(hook_env, CLAUDECODE="1", SECURITY_GUIDANCE_PORTABLE_OUTPUT="1")
        rc, so, se = run_hook(stop_payload(repo), env)
        assert metrics_of(so) is None and _objects(so) == [{}]


# SessionStart runs ensure_agent_sdk.py. The wrapper picks the branch without
# installing anything: whether the SDK looks importable, and whether the
# interpreter looks older than the SDK supports.
SESSION_START_FIELDS = STOP_FIELDS | {"hookSpecificOutput"}
_BOOTSTRAP = """
import importlib.util, os, runpy, sys
script, sdk, old_py = sys.argv[1:4]
sys.path.insert(0, os.path.dirname(script))
real = importlib.util.find_spec
def find_spec(name, *a, **k):
    if name == "claude_agent_sdk":
        return object() if sdk == "present" else None
    return real(name, *a, **k)
importlib.util.find_spec = find_spec
class V(tuple):
    major, minor = property(lambda s: s[0]), property(lambda s: s[1])
sys.version_info = V(((3, 9, 6) if old_py == "old" else (3, 12, 0)) + ("final", 0))
sys.argv = [script]
runpy.run_path(script, run_name="__main__")
"""


def _session_start(tmp_path, branch, **extra):
    state = tmp_path / "state"
    state.mkdir(exist_ok=True)
    sdk, old_py = "absent", "new"
    if branch == "noop":
        sdk = "present"
    elif branch == "concurrent_build":
        (state / "agent-sdk-venv.building").touch()
    elif branch == "failure":
        (tmp_path / "file").write_text("")
        state = tmp_path / "file" / "state"
    elif branch == "notice":
        old_py = "old"
    env = {k: v for k, v in os.environ.items() if k not in HOST_MARKERS}
    env.update(SECURITY_WARNINGS_STATE_DIR=str(state), HOME=str(tmp_path),
               PYTHONDONTWRITEBYTECODE="1", **extra)
    r = subprocess.run(
        [sys.executable, "-c", _BOOTSTRAP, str(HOOKS_DIR / "ensure_agent_sdk.py"), sdk, old_py],
        input="{}", capture_output=True, text=True, env=env, timeout=60,
    )
    return r.returncode, r.stdout, r.stderr


SESSION_START_BRANCHES = ["noop", "concurrent_build", "failure", "notice"]


class TestSessionStartOtherHost:
    @pytest.mark.parametrize("branch", SESSION_START_BRANCHES)
    def test_one_document_with_only_standard_fields(self, tmp_path, branch):
        rc, so, se = _session_start(tmp_path, branch, PLUGIN_ROOT="/p")
        assert rc == 0 and se == ""
        out = json.loads(so)  # the whole stream is one JSON document
        assert set(out) <= SESSION_START_FIELDS, out
        assert (out != {}) == (branch == "notice")

    def test_notice_is_kept(self, tmp_path):
        rc, so, se = _session_start(tmp_path, "notice", PLUGIN_ROOT="/p")
        out = json.loads(so)
        assert "Python" in out["systemMessage"]
        assert out["hookSpecificOutput"] == {
            "hookEventName": "SessionStart", "additionalContext": out["systemMessage"]}


class TestSessionStartClaudeCodeUnchanged:
    @pytest.mark.parametrize("branch,outcome", [
        ("noop", 0), ("concurrent_build", 5), ("failure", 3), ("notice", 6)])
    @pytest.mark.parametrize("extra", [
        {},
        {"PLUGIN_ROOT": "/p", "CLAUDECODE": "1"},
        {"PLUGIN_ROOT": "/p", "SECURITY_GUIDANCE_PORTABLE_OUTPUT": "0"},
    ])
    def test_async_line_then_metrics(self, tmp_path, branch, outcome, extra):
        rc, so, se = _session_start(tmp_path, branch, **extra)
        assert rc == 0
        first, second = _objects(so)
        assert first == {"async": True, "asyncTimeout": 180000}
        assert second["metrics"]["sdk_bootstrap"] == outcome
        assert ("systemMessage" in second) == (branch == "notice")
