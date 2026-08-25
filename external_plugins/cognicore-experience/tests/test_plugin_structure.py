"""
Tests for CogniCore Claude Code Plugin Manifest and Structure.
"""

import json
from pathlib import Path
import pytest

PLUGIN_ROOT = Path(__file__).parent.parent


def test_plugin_json_manifest():
    manifest_path = PLUGIN_ROOT / ".claude-plugin" / "plugin.json"
    assert manifest_path.exists(), "plugin.json must exist in .claude-plugin/"

    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data.get("name") == "cognicore-experience"
    assert "version" in data
    assert "description" in data
    assert "author" in data
    assert "license" in data
    assert isinstance(data.get("keywords"), list)


def test_mcp_json_configuration():
    mcp_path = PLUGIN_ROOT / ".mcp.json"
    assert mcp_path.exists(), ".mcp.json must exist at plugin root"

    with open(mcp_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "cognicore-experience" in data
    server_cfg = data["cognicore-experience"]
    assert server_cfg.get("command") == "python"
    assert len(server_cfg.get("args", [])) > 0


def test_hooks_json_configuration():
    hooks_path = PLUGIN_ROOT / "hooks" / "hooks.json"
    assert hooks_path.exists(), "hooks.json must exist in hooks/"

    with open(hooks_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "hooks" in data
    hooks = data["hooks"]
    assert "SessionStart" in hooks
    assert "PostToolUse" in hooks


def test_skill_structure():
    skill_path = PLUGIN_ROOT / "skills" / "structured-experience" / "SKILL.md"
    assert skill_path.exists(), "SKILL.md must exist in skills/structured-experience/"

    content = skill_path.read_text(encoding="utf-8")
    assert content.startswith("---")
    assert "name: Structured Experience Memory" in content
    assert "cognicore_recall_experience" in content
    assert "cognicore_record_experience" in content
    assert "cognicore_verify_experience" in content
    assert "cognicore_check_experience" in content
    assert "cognicore_share_experience" in content


def test_commands_structure():
    commands_dir = PLUGIN_ROOT / "commands"
    assert commands_dir.is_dir()

    expected_commands = ["recall-experience.md", "record-experience.md", "check-experience.md"]
    for cmd in expected_commands:
        cmd_file = commands_dir / cmd
        assert cmd_file.exists(), f"Command file {cmd} must exist"
        text = cmd_file.read_text(encoding="utf-8")
        assert text.startswith("---")
        assert "allowed-tools:" in text
        assert "description:" in text
