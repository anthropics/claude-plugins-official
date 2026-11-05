"""The agentic reviewer stops as soon as its credentials are refused, instead
of waiting for the inner CLI to give up, and leaves every other run alone."""
import os
import subprocess
import sys
import types

import pytest

import llm
from conftest import write_cli


class _Assistant:
    def __init__(self, error=None):
        self.content, self.error = [], error


class _System:
    subtype = "api_retry"

    def __init__(self, status):
        self.data = {"error_status": status}


@pytest.fixture
def sdk(monkeypatch, tmp_path):
    """Replays `script.messages`, then a clean result, and counts what the
    review read of them."""
    script = types.SimpleNamespace(messages=[], read=0)

    class ClaudeAgentOptions:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class ResultMessage:
        subtype, usage, total_cost_usd = "success", {}, 0.0
        structured_output = {"findings": []}

    async def query(prompt, options):
        for m in script.messages:
            script.read += 1
            yield m
        yield ResultMessage()

    mod = types.ModuleType("claude_agent_sdk")
    mod.ClaudeAgentOptions, mod.ResultMessage, mod.query = ClaudeAgentOptions, ResultMessage, query
    mod.AssistantMessage = _Assistant
    monkeypatch.setitem(sys.modules, "claude_agent_sdk", mod)
    monkeypatch.setenv("SG_AGENTIC_CLI_PATH", "")
    monkeypatch.setenv("SECURITY_WARNINGS_STATE_DIR", str(tmp_path / "state"))
    monkeypatch.delenv("CLAUDE_CODE_REMOTE", raising=False)
    return script


def _review(repo):
    return llm.agentic_review(str(repo), [("a.py", "+x = 1\n")], ["a.py"])[2]


class TestStopsOnRefusedCredentials:
    def test_first_auth_failure_ends_the_review(self, sdk, tmp_path):
        sdk.messages = [_Assistant(error="authentication_failed") for _ in range(50)]
        m = _review(tmp_path)
        assert sdk.read == 1
        assert m["agentic_fallback"] == "investigate:_ReviewerAuthFailed"

    def test_repeated_401_retries_end_the_review(self, sdk, tmp_path):
        sdk.messages = [_System(401) for _ in range(10)]
        m = _review(tmp_path)
        assert sdk.read == llm._AGENTIC_MAX_401_RETRIES
        assert m["agentic_fallback"] == "investigate:_ReviewerAuthFailed"


class TestLeavesOtherRunsAlone:
    def test_a_remote_session_rides_out_401_retries(self, sdk, tmp_path, monkeypatch):
        monkeypatch.setenv("CLAUDE_CODE_REMOTE", "true")
        sdk.messages = [_System(401) for _ in range(10)]
        assert "agentic_fallback" not in _review(tmp_path)

    def test_a_login_renewed_after_one_401_goes_on(self, sdk, tmp_path):
        sdk.messages = [_System(401), _Assistant()]
        assert "agentic_fallback" not in _review(tmp_path)

    def test_401s_that_are_not_in_a_row_do_not_add_up(self, sdk, tmp_path):
        sdk.messages = [_System(401), _System(401), _Assistant()] * 3
        assert "agentic_fallback" not in _review(tmp_path)

    def test_other_retries_do_not_count(self, sdk, tmp_path):
        sdk.messages = [_System(s) for s in (529, 429, None, 500, 529, 529)]
        assert "agentic_fallback" not in _review(tmp_path)

    def test_other_assistant_errors_do_not_stop_it(self, sdk, tmp_path):
        sdk.messages = [_Assistant(error="rate_limit"), _Assistant(error="server_error")]
        assert "agentic_fallback" not in _review(tmp_path)

    def test_a_message_without_the_field_is_read_as_before(self, sdk, tmp_path):
        class Old:
            content = []
        sys.modules["claude_agent_sdk"].AssistantMessage = Old
        sdk.messages = [Old()]
        assert "agentic_fallback" not in _review(tmp_path)


_REFUSED_CLI = """
import json, os, sys, time
open(os.environ["SG_TEST_PID_FILE"], "w").write(str(os.getpid()))
def send(m):
    sys.stdout.write(json.dumps(m) + chr(10)); sys.stdout.flush()
for line in sys.stdin:
    m = json.loads(line)
    if m.get("type") == "control_request":
        send({"type": "control_response", "response": {"subtype": "success",
              "request_id": m["request_id"], "response": {}}})
    elif m.get("type") == "user":
        for _ in range(500):
            send({"type": "assistant", "error": "authentication_failed", "message": {
                  "role": "assistant", "model": "m", "content": [{"type": "text", "text": "401"}]}})
            time.sleep(0.02)
        time.sleep(60)
"""

_DRIVER = """
import json, llm, os, sys, time
start = time.time()
metrics = llm.agentic_review(sys.argv[1], [("a.py", "+x = 1")], ["a.py"])[2]
pid = int(open(os.environ["SG_TEST_PID_FILE"]).read())
try:
    os.kill(pid, 0); alive = True
except OSError:
    alive = False
print(json.dumps({"fallback": metrics.get("agentic_fallback"), "alive": alive}), flush=True)
os._exit(0)
"""


def test_real_sdk_closes_the_cli_quietly(tmp_path):
    """Stops the real SDK's child, and prints no traceback for the hook's
    stderr, which reaches the session."""
    pytest.importorskip("claude_agent_sdk")
    env = {**os.environ, "SG_TEST_PID_FILE": str(tmp_path / "pid"),
           "SG_AGENTIC_CLI_PATH": str(write_cli(tmp_path, "claude", _REFUSED_CLI)),
           "SECURITY_WARNINGS_STATE_DIR": str(tmp_path / "state"),
           "PYTHONPATH": str(os.path.dirname(llm.__file__))}
    r = subprocess.run([sys.executable, "-c", _DRIVER, str(tmp_path)], env=env,
                       capture_output=True, text=True, timeout=60)
    assert "Traceback" not in r.stderr, r.stderr
    assert '"fallback": "investigate:_ReviewerAuthFailed"' in r.stdout, (r.stdout, r.stderr)
    assert '"alive": false' in r.stdout, r.stdout
