#!/usr/bin/env python3
"""Tests for hookify rule_engine."""

import sys
import unittest
from pathlib import Path

# Add hookify plugin root to path
HOOKIFY_DIR = Path(__file__).resolve().parent.parent
if str(HOOKIFY_DIR) not in sys.path:
    sys.path.insert(0, str(HOOKIFY_DIR))

from core.config_loader import Rule, Condition
from core.rule_engine import RuleEngine


class TestRuleEngine(unittest.TestCase):
    """Test suite for RuleEngine."""

    def setUp(self):
        self.engine = RuleEngine()

    def test_pretooluse_block_includes_permission_decision_reason(self):
        """PreToolUse blocking rule includes permissionDecisionReason with rule name and message."""
        rule = Rule(
            name="demo-block",
            enabled=True,
            event="bash",
            action="block",
            conditions=[
                Condition(field="command", operator="regex_match", pattern=r"hookify-demo-marker")
            ],
            message="Demo rule: this command is blocked on purpose."
        )

        input_data = {
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {
                "command": "echo hookify-demo-marker"
            }
        }

        result = self.engine.evaluate_rules([rule], input_data)

        self.assertIn("hookSpecificOutput", result)
        hook_output = result["hookSpecificOutput"]
        self.assertEqual(hook_output.get("hookEventName"), "PreToolUse")
        self.assertEqual(hook_output.get("permissionDecision"), "deny")
        self.assertEqual(
            hook_output.get("permissionDecisionReason"),
            "**[demo-block]**\nDemo rule: this command is blocked on purpose."
        )
        self.assertEqual(
            result.get("systemMessage"),
            "**[demo-block]**\nDemo rule: this command is blocked on purpose."
        )

    def test_pretooluse_warn_does_not_deny(self):
        """Warning rule does not emit permissionDecision deny."""
        rule = Rule(
            name="demo-warn",
            enabled=True,
            event="bash",
            action="warn",
            conditions=[
                Condition(field="command", operator="contains", pattern="rm -rf")
            ],
            message="Please be careful with rm -rf."
        )

        input_data = {
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {
                "command": "rm -rf /tmp/scratch"
            }
        }

        result = self.engine.evaluate_rules([rule], input_data)
        self.assertNotIn("hookSpecificOutput", result)
        self.assertEqual(
            result.get("systemMessage"),
            "**[demo-warn]**\nPlease be careful with rm -rf."
        )

    def test_non_matching_input_returns_empty(self):
        """Non-matching input returns empty dict."""
        rule = Rule(
            name="demo-block",
            enabled=True,
            event="bash",
            action="block",
            conditions=[
                Condition(field="command", operator="contains", pattern="dangerous")
            ],
            message="Blocked dangerous command."
        )

        input_data = {
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {
                "command": "ls -la"
            }
        }

        result = self.engine.evaluate_rules([rule], input_data)
        self.assertEqual(result, {})

    def test_stop_block_decision_and_reason(self):
        """Stop event blocking rule returns decision: block and reason."""
        rule = Rule(
            name="check-completion",
            enabled=True,
            event="stop",
            action="block",
            conditions=[
                Condition(field="reason", operator="contains", pattern="done")
            ],
            message="Please verify all checks before stopping."
        )

        input_data = {
            "hook_event_name": "Stop",
            "reason": "Task is done"
        }

        result = self.engine.evaluate_rules([rule], input_data)
        self.assertEqual(result.get("decision"), "block")
        self.assertEqual(
            result.get("reason"),
            "**[check-completion]**\nPlease verify all checks before stopping."
        )


if __name__ == "__main__":
    unittest.main()
