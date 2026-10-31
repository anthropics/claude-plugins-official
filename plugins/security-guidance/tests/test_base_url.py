"""A blank ANTHROPIC_BASE_URL means the default endpoint, as it does for the
Anthropic SDK and Claude Code, for every call the plugin makes."""
import io
import json

import pytest

import llm
import security_reminder_hook as hook

DEFAULT = "https://api.anthropic.com"
BLANK = ["", "   ", "\t\n"]


@pytest.mark.parametrize("value", BLANK)
def test_blank_is_the_default_endpoint(monkeypatch, value):
    monkeypatch.setenv("ANTHROPIC_BASE_URL", value)
    assert llm._anthropic_base_url() == DEFAULT


@pytest.mark.parametrize("value, expected", [
    ("https://gw.example.com/", "https://gw.example.com"),
    (" https://gw.example.com/base/ \n", "https://gw.example.com/base"),
])
def test_a_real_value_is_kept(monkeypatch, value, expected):
    monkeypatch.setenv("ANTHROPIC_BASE_URL", value)
    assert llm._anthropic_base_url() == expected


def test_a_stray_slash_is_not_taken_for_blank(monkeypatch):
    # A broken gateway setting must not quietly send code to the default host.
    monkeypatch.setenv("ANTHROPIC_BASE_URL", "/")
    assert llm._anthropic_base_url() == ""


def test_unset_is_the_default_endpoint(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_BASE_URL", raising=False)
    assert llm._anthropic_base_url() == DEFAULT


class _Reply(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


@pytest.mark.parametrize("value", BLANK)
def test_requests_go_to_the_default_endpoint(monkeypatch, value):
    urls = []

    def urlopen(request, timeout):
        urls.append(request.full_url)
        return _Reply(json.dumps({
            "data": [{"id": "claude-opus-4-8"}],
            "content": [{"type": "text", "text": "{}"}],
            "usage": {},
        }).encode())

    for var in llm._PROVIDER_ENV_VARS:
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("ANTHROPIC_BASE_URL", value)
    monkeypatch.setattr(llm, "ANTHROPIC_API_KEY", "key")
    monkeypatch.setattr(llm, "HAS_API_CREDENTIALS", True)
    monkeypatch.setattr(llm, "_urlopen", urlopen)
    assert llm._probe_anthropic()
    llm._fetch_newest_opus()
    llm._call_claude("prompt", {"type": "object"}, thinking_budget=0, model="claude-x")
    assert urls == [f"{DEFAULT}/", f"{DEFAULT}/v1/models?limit=100", f"{DEFAULT}/v1/messages"]


@pytest.mark.parametrize("value", BLANK)
def test_blank_is_not_reported_as_a_gateway(monkeypatch, value):
    for var in llm._PROVIDER_ENV_VARS:
        monkeypatch.delenv(var, raising=False)
    monkeypatch.delenv("ANTHROPIC_CUSTOM_HEADERS", raising=False)
    monkeypatch.setenv("ANTHROPIC_BASE_URL", value)
    assert llm.gateway_cfg() == 0


@pytest.mark.parametrize("value", BLANK)
def test_blank_gets_no_gateway_hint(monkeypatch, value):
    for var in llm._PROVIDER_ENV_VARS:
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("ANTHROPIC_BASE_URL", value)
    assert "ANTHROPIC_CUSTOM_HEADERS" not in hook._review_failure_reason(401)[2]
