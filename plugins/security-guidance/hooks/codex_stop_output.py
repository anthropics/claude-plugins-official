"""Keep Codex Stop stdout to one supported JSON object."""
import io
import json
import os
import sys


def run_hook(main):
    if not os.environ.get("CODEX_THREAD_ID"):
        return main()
    raw_payload = sys.stdin.read()
    sys.stdin = io.StringIO(raw_payload)
    try:
        event = json.loads(raw_payload).get("hook_event_name")
    except (ValueError, AttributeError):
        event = None
    if event not in ("Stop", "SubagentStop"):
        return main()
    original_stdout = sys.stdout
    captured = io.StringIO()
    sys.stdout = captured
    try:
        return main()
    finally:
        sys.stdout = original_stdout
        output = {}
        for line in captured.getvalue().splitlines():
            try:
                record = json.loads(line)
            except ValueError:
                continue
            if isinstance(record, dict):
                record.pop("metrics", None)
                record.pop("rewakeSummary", None)
                output.update(record)
        print(json.dumps(output), flush=True)
