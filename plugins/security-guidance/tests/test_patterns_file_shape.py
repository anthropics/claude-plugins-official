"""A security-patterns file that parses to something other than a mapping is
skipped on its own; rules from the other locations still load."""
import json

import pytest

import extensibility

from conftest import run_hook

VALID = {"patterns": [{"rule_name": "demo_rule", "regex": "AKIA[0-9A-Z]{16}",
                       "reminder": "DEMO_RULE_REMINDER"}]}


@pytest.fixture
def project(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    monkeypatch.delenv("CLAUDE_CONFIG_DIR", raising=False)
    monkeypatch.setattr(extensibility, "_user_patterns", [])
    monkeypatch.setattr(extensibility, "_guidance_block", "")
    proj = tmp_path / "proj"
    (proj / ".claude").mkdir(parents=True)
    (proj / ".claude" / "security-patterns.json").write_text(json.dumps(VALID))
    return proj


def loaded(proj):
    extensibility.load_for_session(str(proj))
    return [r["ruleName"] for r in extensibility.user_patterns()]


def rule(name="x", **kw):
    return dict(VALID["patterns"][0], rule_name=name, **kw)


WRONG_SHAPE_JSON = [
    json.dumps([rule()]),
    "5",
    '"just a string"',
    '{"patterns": 5}',
    '{"patterns": "demo"}',
    '{"patterns": {"rule_name": "x"}}',
    '{"patterns": {}}',
    '{"patterns": null}',
    "{not json",
    json.dumps({"patterns": [rule(regex="a{99999999999}")]}),
]


@pytest.mark.parametrize("body", WRONG_SHAPE_JSON)
def test_wrong_shape_local_json_keeps_the_project_rules(project, body):
    (project / ".claude" / "security-patterns.local.json").write_text(body)
    assert loaded(project) == ["user:demo_rule"]


@pytest.mark.parametrize("body", [
    "just a bare scalar\n",
    "- rule_name: x\n  regex: a\n  reminder: r\n",
    "patterns: 5\n",
    "a: [1\n",
    "when: 2001-13-45\n",
])
def test_wrong_shape_local_yaml_keeps_the_project_rules(project, body):
    pytest.importorskip("yaml")
    (project / ".claude" / "security-patterns.local.yaml").write_text(body)
    assert loaded(project) == ["user:demo_rule"]


def test_file_that_is_not_utf8_keeps_the_project_rules(project):
    body = json.dumps({"patterns": [rule("local_rule")]}).encode("utf-16")
    (project / ".claude" / "security-patterns.local.json").write_bytes(body)
    assert loaded(project) == ["user:demo_rule"]


@pytest.mark.parametrize("body", ["- a\n- b\n", "patterns: 5\n"])
def test_unusable_yaml_does_not_hide_the_json_next_to_it(project, body):
    pytest.importorskip("yaml")
    (project / ".claude" / "security-patterns.yaml").write_text(body)
    assert loaded(project) == ["user:demo_rule"]


def test_one_bad_rule_does_not_drop_the_rest_of_its_file(project):
    local = {"patterns": [rule("bad", regex="a{99999999999}"), rule("local_rule")]}
    (project / ".claude" / "security-patterns.local.json").write_text(json.dumps(local))
    assert loaded(project) == ["user:demo_rule", "user:local_rule"]


def test_rules_from_a_valid_local_file_still_load(project):
    local = {"patterns": [rule("local_rule")]}
    (project / ".claude" / "security-patterns.local.json").write_text(json.dumps(local))
    assert loaded(project) == ["user:demo_rule", "user:local_rule"]


def test_wrong_shape_file_is_named_in_the_debug_log(project, monkeypatch):
    lines = []
    monkeypatch.setattr(extensibility, "debug_log", lines.append)
    (project / ".claude" / "security-patterns.local.json").write_text("[1, 2]")
    assert loaded(project) == ["user:demo_rule"]
    assert any("security-patterns.local.json" in l and "got list" in l for l in lines)


def test_edit_hook_still_warns_with_a_wrong_shape_file_present(project, hook_env):
    (project / ".claude" / "security-patterns.local.json").write_text("[1, 2]")
    env = dict(hook_env, HOME=str(project.parent / "home"), CLAUDE_PROJECT_DIR=str(project))
    env.pop("CLAUDE_CONFIG_DIR", None)
    payload = {
        "session_id": "s1", "hook_event_name": "PostToolUse", "tool_name": "Write",
        "tool_input": {"file_path": str(project / "cfg.py"),
                       "content": "KEY = 'AKIAABCDEFGHIJKLMNOP'\n"},
        "cwd": str(project), "tool_response": {},
    }
    _rc, stdout, stderr = run_hook(payload, env)
    assert "DEMO_RULE_REMINDER" in stdout + stderr
