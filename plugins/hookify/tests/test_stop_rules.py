#!/usr/bin/env python3
"""Regression tests for Hookify stop-event rule handling."""

import sys
import unittest
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from core.config_loader import Rule
from core.rule_engine import RuleEngine


class StopRuleRegressionTests(unittest.TestCase):
    """Verify stop rules target the correct stop-event fields."""

    def test_simple_stop_pattern_maps_to_last_assistant_message(self) -> None:
        rule = Rule.from_dict(
            {
                "name": "test-stop",
                "enabled": True,
                "event": "stop",
                "pattern": r"(?i)probably",
                "action": "block",
            },
            "Test message",
        )

        self.assertEqual(len(rule.conditions), 1)
        self.assertEqual(rule.conditions[0].field, "last_assistant_message")

    def test_stop_rule_matches_last_assistant_message_and_blocks(self) -> None:
        rule = Rule.from_dict(
            {
                "name": "test-stop",
                "enabled": True,
                "event": "stop",
                "pattern": r"(?i)probably",
                "action": "block",
            },
            "Test message",
        )
        engine = RuleEngine()

        result = engine.evaluate_rules(
            [rule],
            {
                "hook_event_name": "Stop",
                "last_assistant_message": "This will probably work.",
                "reason": "Completed task",
            },
        )

        self.assertEqual(result.get("decision"), "block")
        self.assertIn("test-stop", result.get("reason", ""))
        self.assertIn("Test message", result.get("reason", ""))

    def test_extract_field_reads_last_assistant_message(self) -> None:
        engine = RuleEngine()

        value = engine._extract_field(
            "last_assistant_message",
            tool_name="",
            tool_input={},
            input_data={"last_assistant_message": "Probably yes."},
        )

        self.assertEqual(value, "Probably yes.")


if __name__ == "__main__":
    unittest.main()
