#!/usr/bin/env python3
"""Tests for tool_response.* field lookup in _extract_field.

Run from plugin root:
    cd plugins/hookify
    python3 -m unittest tests.test_tool_response_fields -v
"""

import os
import sys
import unittest

# Make plugin root importable
PLUGIN_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PLUGIN_ROOT not in sys.path:
    sys.path.insert(0, PLUGIN_ROOT)

from core.config_loader import Condition, Rule
from core.rule_engine import RuleEngine


class ToolResponseFieldExtractTests(unittest.TestCase):
    """Direct tests of RuleEngine._extract_field for `tool_response.<key>` paths."""

    def setUp(self):
        self.engine = RuleEngine()

    def _extract(self, field, tool_input=None, input_data=None):
        return self.engine._extract_field(
            field=field,
            tool_name='Bash',
            tool_input=tool_input or {},
            input_data=input_data,
        )

    def test_extracts_exit_code_as_string(self):
        """`tool_response.exitCode` returns the numeric exit code as a string."""
        result = self._extract(
            'tool_response.exitCode',
            input_data={'tool_response': {'exitCode': 0, 'stdout': '', 'stderr': ''}},
        )
        self.assertEqual(result, '0')

    def test_extracts_non_zero_exit_code_as_string(self):
        """Non-zero exit codes stringify correctly."""
        result = self._extract(
            'tool_response.exitCode',
            input_data={'tool_response': {'exitCode': 127}},
        )
        self.assertEqual(result, '127')

    def test_extracts_stdout_as_string(self):
        """`tool_response.stdout` returns the stdout string verbatim."""
        result = self._extract(
            'tool_response.stdout',
            input_data={'tool_response': {'stdout': 'hello world\n'}},
        )
        self.assertEqual(result, 'hello world\n')

    def test_extracts_stderr_as_string(self):
        """`tool_response.stderr` returns the stderr string verbatim."""
        result = self._extract(
            'tool_response.stderr',
            input_data={'tool_response': {'stderr': 'E: permission denied'}},
        )
        self.assertEqual(result, 'E: permission denied')

    def test_missing_key_under_tool_response_returns_none(self):
        """Referencing a sub-key that does not exist returns None (rule won't match)."""
        result = self._extract(
            'tool_response.nonexistent',
            input_data={'tool_response': {'exitCode': 0}},
        )
        self.assertIsNone(result)

    def test_missing_tool_response_returns_none(self):
        """PreToolUse has no tool_response; lookup returns None (rule won't match)."""
        result = self._extract(
            'tool_response.exitCode',
            input_data={'tool_input': {'command': 'ls'}},  # no tool_response
        )
        self.assertIsNone(result)

    def test_tool_response_not_a_dict_returns_none(self):
        """Malformed tool_response (non-dict) does not crash; returns None."""
        result = self._extract(
            'tool_response.exitCode',
            input_data={'tool_response': 'oops'},
        )
        self.assertIsNone(result)

    def test_none_input_data_returns_none(self):
        """Field needs input_data; None input_data returns None (back-compat)."""
        result = self._extract('tool_response.exitCode', input_data=None)
        self.assertIsNone(result)


class ToolResponseRuleEvaluationTests(unittest.TestCase):
    """End-to-end rule evaluation: a plan-sync-style rule that fires only on exit 0."""

    def setUp(self):
        self.engine = RuleEngine()
        self.rule = Rule(
            name='plan-sync-on-success',
            enabled=True,
            event='bash',
            action='warn',
            tool_matcher='Bash',
            conditions=[
                Condition(
                    field='command',
                    operator='regex_match',
                    pattern=r'terraform\s+apply|ansible-playbook\s+\S+\.ya?ml',
                ),
                Condition(
                    field='tool_response.exitCode',
                    operator='equals',
                    pattern='0',
                ),
            ],
            message='Plan-sync reminder!',
        )

    def test_fires_on_terraform_apply_success(self):
        result = self.engine.evaluate_rules(
            [self.rule],
            {
                'hook_event_name': 'PostToolUse',
                'tool_name': 'Bash',
                'tool_input': {'command': 'terraform apply plan.tfplan'},
                'tool_response': {'exitCode': 0, 'stdout': 'Apply complete!', 'stderr': ''},
            },
        )
        self.assertIn('systemMessage', result)
        self.assertIn('Plan-sync reminder!', result['systemMessage'])

    def test_does_not_fire_on_terraform_apply_failure(self):
        result = self.engine.evaluate_rules(
            [self.rule],
            {
                'hook_event_name': 'PostToolUse',
                'tool_name': 'Bash',
                'tool_input': {'command': 'terraform apply plan.tfplan'},
                'tool_response': {'exitCode': 1, 'stdout': '', 'stderr': 'Error: ...'},
            },
        )
        self.assertEqual(result, {})

    def test_does_not_fire_on_ansible_playbook_failure(self):
        result = self.engine.evaluate_rules(
            [self.rule],
            {
                'hook_event_name': 'PostToolUse',
                'tool_name': 'Bash',
                'tool_input': {'command': 'ansible-playbook site.yml'},
                'tool_response': {'exitCode': 2, 'stdout': '', 'stderr': 'failed=1'},
            },
        )
        self.assertEqual(result, {})

    def test_does_not_fire_on_unrelated_command(self):
        result = self.engine.evaluate_rules(
            [self.rule],
            {
                'hook_event_name': 'PostToolUse',
                'tool_name': 'Bash',
                'tool_input': {'command': 'ls -la'},
                'tool_response': {'exitCode': 0, 'stdout': '', 'stderr': ''},
            },
        )
        self.assertEqual(result, {})

    def test_does_not_fire_on_pretooluse_missing_tool_response(self):
        """Same rule attached to event=bash also loads for PreToolUse; without
        tool_response the exit-code condition short-circuits and the rule does
        not match — this is the desired PreToolUse behaviour."""
        result = self.engine.evaluate_rules(
            [self.rule],
            {
                'hook_event_name': 'PreToolUse',
                'tool_name': 'Bash',
                'tool_input': {'command': 'terraform apply plan.tfplan'},
                # no tool_response at all
            },
        )
        self.assertEqual(result, {})


class BackwardCompatibilityTests(unittest.TestCase):
    """Ensure tool_response patch doesn't regress existing field extraction."""

    def setUp(self):
        self.engine = RuleEngine()

    def test_bash_command_still_works(self):
        result = self.engine._extract_field(
            field='command', tool_name='Bash',
            tool_input={'command': 'rm -rf /'}, input_data={},
        )
        self.assertEqual(result, 'rm -rf /')

    def test_file_path_still_works(self):
        result = self.engine._extract_field(
            field='file_path', tool_name='Edit',
            tool_input={'file_path': '/tmp/x.py', 'new_string': 'pass'},
            input_data={},
        )
        self.assertEqual(result, '/tmp/x.py')

    def test_user_prompt_still_works(self):
        result = self.engine._extract_field(
            field='user_prompt', tool_name='', tool_input={},
            input_data={'user_prompt': 'deploy to production'},
        )
        self.assertEqual(result, 'deploy to production')


if __name__ == '__main__':
    unittest.main(verbosity=2)
