#!/usr/bin/env python3
"""Tests for hookify config_loader."""

import os
import sys
import tempfile
import unittest
from pathlib import Path

# Add hookify plugin root to path
HOOKIFY_DIR = Path(__file__).resolve().parent.parent
if str(HOOKIFY_DIR) not in sys.path:
    sys.path.insert(0, str(HOOKIFY_DIR))

from core.config_loader import load_rules, load_rule_file, extract_frontmatter, Rule


class TestConfigLoader(unittest.TestCase):
    """Test suite for config_loader."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_dir = self.temp_dir.name
        self.claude_dir = os.path.join(self.project_dir, ".claude")
        os.makedirs(self.claude_dir, exist_ok=True)

        # Save original environment and cwd
        self.original_cwd = os.getcwd()
        self.original_claude_project_dir = os.environ.get("CLAUDE_PROJECT_DIR")
        self.original_claude_project_root = os.environ.get("CLAUDE_PROJECT_ROOT")

        # Clean environment
        os.environ.pop("CLAUDE_PROJECT_DIR", None)
        os.environ.pop("CLAUDE_PROJECT_ROOT", None)

    def tearDown(self):
        # Restore environment and cwd
        os.chdir(self.original_cwd)
        if self.original_claude_project_dir is not None:
            os.environ["CLAUDE_PROJECT_DIR"] = self.original_claude_project_dir
        else:
            os.environ.pop("CLAUDE_PROJECT_DIR", None)

        if self.original_claude_project_root is not None:
            os.environ["CLAUDE_PROJECT_ROOT"] = self.original_claude_project_root
        else:
            os.environ.pop("CLAUDE_PROJECT_ROOT", None)

        self.temp_dir.cleanup()

    def _create_rule_file(self, directory: str, name: str, event: str = "bash", pattern: str = "rm -rf", enabled: bool = True):
        claude_dir = os.path.join(directory, ".claude")
        os.makedirs(claude_dir, exist_ok=True)
        file_path = os.path.join(claude_dir, f"hookify.{name}.local.md")
        content = f"""---
name: {name}
enabled: {'true' if enabled else 'false'}
event: {event}
pattern: "{pattern}"
---

Warning message for {name}
"""
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return file_path

    def test_load_rules_relative_cwd(self):
        """Rules are loaded from .claude in cwd when no env var is set."""
        self._create_rule_file(self.project_dir, "rule1")
        os.chdir(self.project_dir)

        rules = load_rules()
        self.assertEqual(len(rules), 1)
        self.assertEqual(rules[0].name, "rule1")

    def test_load_rules_claude_project_dir_when_cwd_differs(self):
        """Rules are loaded from CLAUDE_PROJECT_DIR when cwd is a subfolder."""
        self._create_rule_file(self.project_dir, "root-rule")
        sub_dir = os.path.join(self.project_dir, "subdir", "nested")
        os.makedirs(sub_dir, exist_ok=True)

        os.environ["CLAUDE_PROJECT_DIR"] = self.project_dir
        os.chdir(sub_dir)

        rules = load_rules()
        self.assertEqual(len(rules), 1)
        self.assertEqual(rules[0].name, "root-rule")

    def test_load_rules_claude_project_root_fallback(self):
        """Rules are loaded from CLAUDE_PROJECT_ROOT when cwd is a subfolder."""
        self._create_rule_file(self.project_dir, "root-rule-2")
        sub_dir = os.path.join(self.project_dir, "subdir")
        os.makedirs(sub_dir, exist_ok=True)

        os.environ["CLAUDE_PROJECT_ROOT"] = self.project_dir
        os.chdir(sub_dir)

        rules = load_rules()
        self.assertEqual(len(rules), 1)
        self.assertEqual(rules[0].name, "root-rule-2")

    def test_load_rules_deduplication(self):
        """Rules are not loaded twice when CLAUDE_PROJECT_DIR matches cwd."""
        self._create_rule_file(self.project_dir, "unique-rule")
        os.environ["CLAUDE_PROJECT_DIR"] = self.project_dir
        os.chdir(self.project_dir)

        rules = load_rules()
        self.assertEqual(len(rules), 1)
        self.assertEqual(rules[0].name, "unique-rule")

    def test_load_rules_event_filtering(self):
        """Rules are correctly filtered by event."""
        self._create_rule_file(self.project_dir, "bash-rule", event="bash")
        self._create_rule_file(self.project_dir, "file-rule", event="file")
        os.environ["CLAUDE_PROJECT_DIR"] = self.project_dir

        bash_rules = load_rules(event="bash")
        self.assertEqual(len(bash_rules), 1)
        self.assertEqual(bash_rules[0].name, "bash-rule")

        file_rules = load_rules(event="file")
        self.assertEqual(len(file_rules), 1)
        self.assertEqual(file_rules[0].name, "file-rule")

    def test_load_rules_ignores_disabled(self):
        """Disabled rules are excluded from loaded rules."""
        self._create_rule_file(self.project_dir, "enabled-rule", enabled=True)
        self._create_rule_file(self.project_dir, "disabled-rule", enabled=False)
        os.environ["CLAUDE_PROJECT_DIR"] = self.project_dir

        rules = load_rules()
        self.assertEqual(len(rules), 1)
        self.assertEqual(rules[0].name, "enabled-rule")

    def test_load_rules_skips_invalid_file(self):
        """Files missing YAML frontmatter are skipped safely without crashing."""
        invalid_file = os.path.join(self.claude_dir, "hookify.invalid.local.md")
        with open(invalid_file, "w", encoding="utf-8") as f:
            f.write("Just raw text without frontmatter")

        os.environ["CLAUDE_PROJECT_DIR"] = self.project_dir
        rules = load_rules()
        self.assertEqual(len(rules), 0)


if __name__ == "__main__":
    unittest.main()
