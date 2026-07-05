import json
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]


class HookifyEventFilteringTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.rules_dir = self.tmpdir / ".claude"
        self.rules_dir.mkdir()
        self.env = dict(os.environ)
        self.env["CLAUDE_PLUGIN_ROOT"] = str(PLUGIN_ROOT)
        self.env["PYTHONPATH"] = str(PLUGIN_ROOT)
        self.env["PYTHONDONTWRITEBYTECODE"] = "1"

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def write_rule(self, name, event, field, pattern, message):
        (self.rules_dir / f"hookify.{name}.local.md").write_text(
            textwrap.dedent(
                f"""\
                ---
                name: {name}
                enabled: true
                event: {event}
                conditions:
                  - field: {field}
                    operator: regex_match
                    pattern: "{pattern}"
                action: warn
                ---
                {message}
                """
            ),
            encoding="utf-8",
        )

    def run_hook(self, hook_name, payload):
        proc = subprocess.run(
            [sys.executable, str(PLUGIN_ROOT / "hooks" / hook_name)],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            cwd=self.tmpdir,
            env=self.env,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return json.loads(proc.stdout or "{}")

    def test_file_rule_does_not_fire_for_read_pretooluse(self):
        self.write_rule("file-only", "file", "file_path", ".*\\.py$", "file message")

        result = self.run_hook(
            "pretooluse.py",
            {
                "hook_event_name": "PreToolUse",
                "tool_name": "Read",
                "tool_input": {"file_path": "example.py"},
            },
        )

        self.assertEqual(result, {})

    def test_file_rule_does_not_fire_for_read_posttooluse(self):
        self.write_rule("file-only", "file", "file_path", ".*\\.py$", "file message")

        result = self.run_hook(
            "posttooluse.py",
            {
                "hook_event_name": "PostToolUse",
                "tool_name": "Read",
                "tool_input": {"file_path": "example.py"},
            },
        )

        self.assertEqual(result, {})

    def test_all_rule_still_fires_for_unmapped_tool(self):
        self.write_rule("all-tools", "all", "file_path", ".*\\.py$", "all message")

        result = self.run_hook(
            "pretooluse.py",
            {
                "hook_event_name": "PreToolUse",
                "tool_name": "Read",
                "tool_input": {"file_path": "example.py"},
            },
        )

        self.assertIn("all message", result.get("systemMessage", ""))

    def test_mapped_events_still_fire(self):
        self.write_rule("file-only", "file", "file_path", ".*\\.py$", "file message")
        self.write_rule("bash-only", "bash", "command", "pytest", "bash message")

        edit_result = self.run_hook(
            "pretooluse.py",
            {
                "hook_event_name": "PreToolUse",
                "tool_name": "Edit",
                "tool_input": {
                    "file_path": "example.py",
                    "old_string": "a",
                    "new_string": "b",
                },
            },
        )
        bash_result = self.run_hook(
            "pretooluse.py",
            {
                "hook_event_name": "PreToolUse",
                "tool_name": "Bash",
                "tool_input": {"command": "pytest tests"},
            },
        )

        self.assertIn("file message", edit_result.get("systemMessage", ""))
        self.assertIn("bash message", bash_result.get("systemMessage", ""))


if __name__ == "__main__":
    unittest.main()
