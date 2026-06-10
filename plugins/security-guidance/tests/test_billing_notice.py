import json
import os
import sys

import pytest

HOOKS_DIR = os.path.join(os.path.dirname(__file__), "..", "hooks")
sys.path.insert(0, os.path.abspath(HOOKS_DIR))

import llm                                  # noqa: E402
import security_reminder_hook as hook       # noqa: E402


@pytest.fixture(autouse=True)
def isolated_state(monkeypatch, tmp_path):
    # Plugin state files honor CLAUDE_CONFIG_DIR (#2078) — point at tmp_path
    # so each test gets a fresh "session". SECURITY_WARNINGS_STATE_DIR is the
    # higher-precedence plugin-specific override; clear it in case the host
    # env sets it.
    monkeypatch.delenv("SECURITY_WARNINGS_STATE_DIR", raising=False)
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path))
    # Neutralize host env so tests control the credential matrix exactly.
    monkeypatch.delenv("ANTHROPIC_BASE_URL", raising=False)
    for var in ("CLAUDE_CODE_USE_BEDROCK", "CLAUDE_CODE_USE_VERTEX",
                "CLAUDE_CODE_USE_FOUNDRY", "CLAUDE_CODE_USE_MANTLE",
                "CLAUDE_CODE_USE_ANTHROPIC_AWS"):
        monkeypatch.delenv(var, raising=False)


@pytest.fixture(autouse=True)
def quiet_git(monkeypatch):
    # Keep UPS off the real filesystem/git.
    monkeypatch.setattr(hook, "capture_git_baseline", lambda cwd: "deadbeef")
    monkeypatch.setattr(hook, "_list_untracked", lambda cwd: {})
    monkeypatch.setattr(hook, "_git_rev_parse_head", lambda cwd: "deadbeef")


def _run_ups(session_id="sess-billing", cwd="/tmp/repo"):
    with pytest.raises(SystemExit) as e:
        hook.handle_user_prompt_submit({"session_id": session_id, "cwd": cwd})
    assert e.value.code == 0


def test_notice_when_key_and_token(monkeypatch, capsys):
    monkeypatch.setattr(llm, "ANTHROPIC_API_KEY", "sk-ant-xxx")
    monkeypatch.setattr(llm, "ANTHROPIC_AUTH_TOKEN", "oauth-xxx")
    _run_ups()
    out = capsys.readouterr().out.strip()
    payload = json.loads(out)            # stdout is valid JSON, nothing else
    assert "billing your" in payload["systemMessage"]


def test_notice_only_once_per_session(monkeypatch, capsys):
    monkeypatch.setattr(llm, "ANTHROPIC_API_KEY", "sk-ant-xxx")
    monkeypatch.setattr(llm, "ANTHROPIC_AUTH_TOKEN", "oauth-xxx")
    _run_ups(); capsys.readouterr()
    _run_ups()
    assert capsys.readouterr().out.strip() == ""


@pytest.mark.parametrize("key,token", [
    ("sk-ant-xxx", ""),    # key-only: expected billing, not surprising
    ("", "oauth-xxx"),     # token-only: subscription billed, nothing to warn
    ("", ""),              # no creds: no API calls at all
])
def test_no_notice_outside_surprising_case(monkeypatch, capsys, key, token):
    monkeypatch.setattr(llm, "ANTHROPIC_API_KEY", key)
    monkeypatch.setattr(llm, "ANTHROPIC_AUTH_TOKEN", token)
    _run_ups()
    assert capsys.readouterr().out.strip() == ""


def test_no_notice_on_3p(monkeypatch, capsys):
    monkeypatch.setattr(llm, "ANTHROPIC_API_KEY", "sk-ant-xxx")
    monkeypatch.setattr(llm, "ANTHROPIC_AUTH_TOKEN", "oauth-xxx")
    monkeypatch.setenv("CLAUDE_CODE_USE_BEDROCK", "1")
    _run_ups()
    assert capsys.readouterr().out.strip() == ""


def test_no_notice_behind_gateway(monkeypatch, capsys):
    monkeypatch.setattr(llm, "ANTHROPIC_API_KEY", "litellm-proxy-key")
    monkeypatch.setattr(llm, "ANTHROPIC_AUTH_TOKEN", "oauth-xxx")
    monkeypatch.setenv("ANTHROPIC_BASE_URL", "https://litellm.internal:4000")
    _run_ups()
    assert capsys.readouterr().out.strip() == ""
