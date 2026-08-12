import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


HOOK = Path(__file__).with_name("security_reminder_hook.py")
CODEX_STOP_FIELDS = {
    "continue",
    "decision",
    "reason",
    "stopReason",
    "suppressOutput",
    "systemMessage",
}


class CodexStopOutputTest(unittest.TestCase):
    def test_codex_stop_payload_filters_claude_only_fields_without_thread_env(self):
        payload = {
            "session_id": "codex-stop-regression",
            "turn_id": "019ff6f0-dd42-77d1-a8b3-c61302cb8ea7",
            "cwd": str(Path.cwd()),
            "hook_event_name": "Stop",
            "stop_hook_active": True,
        }

        with tempfile.TemporaryDirectory() as state_dir:
            env = os.environ.copy()
            env.pop("CODEX_THREAD_ID", None)
            env["SECURITY_WARNINGS_STATE_DIR"] = state_dir
            result = subprocess.run(
                [sys.executable, str(HOOK)],
                input=json.dumps(payload),
                text=True,
                capture_output=True,
                env=env,
                check=False,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        output = json.loads(result.stdout)
        self.assertLessEqual(set(output), CODEX_STOP_FIELDS)


if __name__ == "__main__":
    unittest.main()
