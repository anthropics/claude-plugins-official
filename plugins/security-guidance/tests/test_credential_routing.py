"""Which credential a review sends to the default API host. Made-up values."""
import os
import sys

import pytest

import llm
from conftest import edit_payload, run_hook, stop_payload, ups_payload, VULN_PY

OAT = "sk-ant-oat01-made-up"
KEY = "sk-ant-api03-made-up"
BEARER = "vck_made-up"
K, T, B = "ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_BASE_URL"
GATEWAY = "https://gateway.example.com"


def _route(env, portable=False):
    env = dict(env)
    return llm._route_credentials(env, portable), env


@pytest.mark.parametrize("portable", [False, True])
@pytest.mark.parametrize("before, after", [
    ({K: OAT}, {T: OAT}),
    ({K: OAT, B: ""}, {T: OAT, B: ""}),
    ({K: OAT, B: "  "}, {T: OAT, B: "  "}),
    ({K: OAT, T: ""}, {T: OAT}),
    # The session's own token is kept, the key could not have worked.
    ({K: OAT, T: OAT + "2"}, {T: OAT + "2"}),
    ({K: KEY}, {K: KEY}),
    ({K: KEY, T: OAT}, {K: KEY, T: OAT}),
    ({K: ""}, {K: ""}),
    ({T: OAT}, {T: OAT}),
    ({}, {}),
    ({K: OAT, B: "https://api.anthropic.com"}, {T: OAT, B: "https://api.anthropic.com"}),
    # With a base URL the token was meant for it.
    ({T: BEARER, B: "https://api.anthropic.com"}, {T: BEARER, B: "https://api.anthropic.com"}),
    ({K: OAT, B: "https://["}, {K: OAT, B: "https://["}),
    # A gateway decides for itself what it takes.
    ({K: OAT, B: GATEWAY}, {K: OAT, B: GATEWAY}),
    ({T: BEARER, B: GATEWAY}, {T: BEARER, B: GATEWAY}),
])
def test_claude_ai_token_as_key(before, after, portable):
    assert _route(before, portable) == (False, after)


@pytest.mark.parametrize("before, after", [
    ({T: BEARER}, {}),
    ({T: BEARER, B: ""}, {B: ""}),
    ({K: KEY, T: BEARER}, {K: KEY}),
    ({K: OAT, T: BEARER}, {T: OAT}),
])
def test_other_bearer_without_a_base_url_on_another_host(before, after):
    assert _route(before, portable=True) == (True, after)


@pytest.mark.parametrize("env", [{T: BEARER}, {K: KEY, T: BEARER}, {K: OAT, T: BEARER}])
def test_other_bearer_in_claude_code_is_left_alone(env):
    assert _route(env) == (False, env)


@pytest.mark.parametrize("env", [{K: OAT}, {T: BEARER}, {K: OAT, T: BEARER}])
def test_cloud_provider_is_left_alone(env, monkeypatch):
    monkeypatch.setattr(llm, "_HAS_3P_PROVIDER_AT_LOAD", True)
    assert _route(env, portable=True) == (False, env)


def _load(hook_env, **extra):
    """What a fresh import of llm makes of the environment."""
    import subprocess
    env = {k: v for k, v in hook_env.items() if k not in (K, T, B, "CLAUDECODE", "CLAUDE_CODE_ENTRYPOINT")}
    env.update(extra)
    code = ("import sys; sys.path.insert(0, %r); import llm; e = llm._agentic_spawn_env(); "
            "import os; child = {**os.environ, **e}; "
            "print(repr([llm.ANTHROPIC_API_KEY, llm.ANTHROPIC_AUTH_TOKEN, llm.HAS_API_CREDENTIALS, "
            "llm.AUTH_TOKEN_HELD_BACK, child.get('ANTHROPIC_API_KEY') or '', "
            "child.get('ANTHROPIC_AUTH_TOKEN') or child.get('CLAUDE_CODE_OAUTH_TOKEN') or '']))"
            % os.path.dirname(llm.__file__))
    r = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    import ast
    return ast.literal_eval(r.stdout.strip().splitlines()[-1])


def test_the_reviewing_cli_gets_the_token_as_a_token(hook_env):
    assert _load(hook_env, **{K: OAT}) == ["", OAT, True, False, "", OAT]


def test_api_key_is_unchanged(hook_env):
    assert _load(hook_env, **{K: KEY}) == [KEY, "", True, False, KEY, ""]


def test_held_back_token_reaches_nothing(hook_env):
    assert _load(hook_env, SECURITY_GUIDANCE_PORTABLE_OUTPUT="1", **{T: BEARER}) == [
        "", "", False, True, "", ""]


def test_same_token_in_claude_code_is_sent_as_before(hook_env):
    assert _load(hook_env, **{T: BEARER}) == ["", BEARER, True, False, "", BEARER]


class TestHook:
    @pytest.fixture
    def env(self, hook_env):
        e = {k: v for k, v in hook_env.items() if k not in (K, T, B)}
        for name in ("CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC", "DISABLE_TELEMETRY", "DO_NOT_TRACK"):
            e.pop(name, None)
        e["SECURITY_GUIDANCE_PORTABLE_OUTPUT"] = "1"
        return e

    @pytest.mark.parametrize("other", [{}, {"DISABLE_TELEMETRY": "1"}])
    def test_held_back_token_is_said_once(self, workspace, env, other):
        _, repo = workspace
        env.update(other)
        env[T] = BEARER
        (repo / "app.py").write_text(VULN_PY)
        payload = edit_payload(repo, repo / "app.py", new_string=VULN_PY)
        _, out, _ = run_hook(payload, env)
        assert "ANTHROPIC_BASE_URL is not set, so it was not sent anywhere" in out
        assert BEARER not in out
        _, out, _ = run_hook(payload, env)
        assert "not running" not in out

    def test_with_its_base_url_the_review_runs(self, workspace, env, stub_api):
        _, repo = workspace
        env[T] = BEARER
        env[B] = f"http://127.0.0.1:{stub_api.server_port}"
        run_hook(ups_payload(repo), env)
        (repo / "app.py").write_text(VULN_PY)
        run_hook(stop_payload(repo), env)
        assert stub_api.calls.count("/v1/messages") == 1
