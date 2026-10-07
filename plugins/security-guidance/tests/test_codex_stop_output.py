"""Run with python -m unittest discover -s tests -p test_codex_stop_output.py."""
import contextlib
import io
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "hooks"))
from codex_stop_output import run_hook


class StopOutputTests(unittest.TestCase):
    def invoke(self, main, event="Stop", codex=True):
        output = io.StringIO()
        with patch.dict(os.environ, {"CODEX_THREAD_ID": "fixture" if codex else ""}), \
                patch("sys.stdin", io.StringIO(json.dumps({"hook_event_name": event}))), \
                contextlib.redirect_stdout(output):
            try:
                run_hook(main)
            except SystemExit as error:
                code = error.code
            else:
                code = 0
        return output.getvalue(), code

    def test_empty_and_skipped_stop(self):
        for event in ("Stop", "SubagentStop"):
            for main in (lambda: None, lambda: print('{"metrics":{"skipped":true}}')):
                output, code = self.invoke(main, event)
                self.assertEqual(json.loads(output), {})
                self.assertEqual(code, 0)

    def test_multiple_records_preserve_block_and_exit(self):
        def main():
            print('{"metrics":{"skipped":false}}')
            print('{"decision":"block","reason":"review findings","rewakeSummary":"review"}')
            sys.exit(2)
        output, code = self.invoke(main)
        self.assertEqual(json.loads(output), {"decision": "block", "reason": "review findings"})
        self.assertEqual(code, 2)

    def test_claude_and_other_events_keep_telemetry(self):
        def main():
            print('{"metrics":{"skipped":true}}')
        for event, codex in (("Stop", False), ("PostToolUse", True)):
            output, code = self.invoke(main, event, codex)
            self.assertEqual(json.loads(output), {"metrics": {"skipped": True}})
            self.assertEqual(code, 0)

    def test_input_and_stderr_are_preserved(self):
        errors = io.StringIO()
        def main():
            self.assertEqual(json.load(sys.stdin)["hook_event_name"], "Stop")
            print("review findings", file=sys.stderr)
            print('{"systemMessage":"review complete"}')
        with contextlib.redirect_stderr(errors):
            output, _ = self.invoke(main)
        self.assertEqual(errors.getvalue(), "review findings\n")
        self.assertEqual(json.loads(output), {"systemMessage": "review complete"})


if __name__ == "__main__":
    unittest.main()
