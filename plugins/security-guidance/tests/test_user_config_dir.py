"""User-level claude-security-guidance.md and security-patterns files are
found in the directory CLAUDE_CONFIG_DIR names, as well as in ~/.claude."""
import json
import os

import pytest

import extensibility

MARKER = "MARKER_POLICY_LINE"
PATTERNS = {"patterns": [{"rule_name": "marker_rule", "substrings": ["x"], "reminder": "r"}]}


@pytest.fixture
def home(tmp_path, monkeypatch):
    h = tmp_path / "home"
    h.mkdir()
    monkeypatch.setenv("HOME", str(h))
    monkeypatch.setenv("USERPROFILE", str(h))
    monkeypatch.delenv("CLAUDE_CONFIG_DIR", raising=False)
    return h


def write_user_files(d, marker=MARKER, rule="marker_rule"):
    d.mkdir(parents=True, exist_ok=True)
    (d / "claude-security-guidance.md").write_text(f"- {marker}\n")
    patterns = {"patterns": [dict(PATTERNS["patterns"][0], rule_name=rule)]}
    (d / "security-patterns.json").write_text(json.dumps(patterns))


def load():
    extensibility.load_for_session(None)
    return extensibility.guidance_block(), [r["ruleName"] for r in extensibility.user_patterns()]


def test_files_in_configured_dir_are_loaded(home, monkeypatch):
    cfg = home / ".claude-work"
    write_user_files(cfg)
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(cfg))
    guidance, rules = load()
    assert MARKER in guidance
    assert rules == ["user:marker_rule"]


def test_default_dir_still_loaded_when_config_dir_is_set(home, monkeypatch):
    write_user_files(home / ".claude")
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(home / ".claude-work"))
    guidance, rules = load()
    assert MARKER in guidance
    assert rules == ["user:marker_rule"]


def test_both_dirs_loaded_default_first(home, monkeypatch):
    write_user_files(home / ".claude", marker="FROM_DEFAULT", rule="default_rule")
    cfg = home / ".claude-work"
    write_user_files(cfg, marker="FROM_CONFIGURED", rule="configured_rule")
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(cfg))
    guidance, rules = load()
    assert guidance.index("FROM_DEFAULT") < guidance.index("FROM_CONFIGURED")
    assert rules == ["user:default_rule", "user:configured_rule"]


@pytest.mark.parametrize("spelling", ["{home}/.claude", "{home}/.claude/", "~/.claude", "{home}/link"])
def test_config_dir_naming_the_default_dir_is_read_once(home, monkeypatch, spelling):
    write_user_files(home / ".claude")
    os.symlink(home / ".claude", home / "link")
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", spelling.format(home=home))
    guidance, rules = load()
    assert guidance.count(MARKER) == 1
    assert rules == ["user:marker_rule"]


@pytest.mark.parametrize("value", ["", "   "])
def test_empty_config_dir_is_not_set(home, monkeypatch, value):
    write_user_files(home / ".claude")
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", value)
    assert extensibility._user_config_dirs() == [str(home / ".claude")]
    guidance, rules = load()
    assert guidance.count(MARKER) == 1


def test_tilde_in_config_dir_is_expanded(home, monkeypatch):
    write_user_files(home / ".claude-work")
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", "~/.claude-work")
    guidance, _ = load()
    assert MARKER in guidance


def test_project_files_unchanged(home, monkeypatch, tmp_path):
    cfg = home / ".claude-work"
    write_user_files(cfg, marker="FROM_USER")
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(cfg))
    proj = tmp_path / "proj"
    write_user_files(proj / ".claude", marker="FROM_PROJECT", rule="project_rule")
    extensibility.load_for_session(str(proj))
    guidance = extensibility.guidance_block()
    assert guidance.index("FROM_USER") < guidance.index("FROM_PROJECT")
    assert [r["ruleName"] for r in extensibility.user_patterns()] == ["user:marker_rule", "user:project_rule"]
