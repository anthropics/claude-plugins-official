#!/usr/bin/env python3
"""Session Start - Load memories and inject as context."""

import json
import sys
from pathlib import Path


def main():
    try:
        data = json.load(sys.stdin)
        cwd = data.get("cwd", ".")
        memory_file = Path(cwd) / ".claude" / "memories" / "project_memory.json"

        if not memory_file.exists():
            print(json.dumps({
                "systemMessage": "\033[1;97m🧠 Claude Never Forgets: Ready to learn.\033[0m"
            }))
            sys.exit(0)

        memories = json.load(open(memory_file, "r", encoding="utf-8"))

        manual = memories.get("manual_memories", [])
        realtime = memories.get("realtime_memories", [])

        if not manual and not realtime:
            print(json.dumps({
                "systemMessage": "\033[1;97m🧠 Claude Never Forgets: No memories yet.\033[0m"
            }))
            sys.exit(0)

        lines = ["## Project Memory", "", "Apply these in your responses:", ""]

        if manual:
            lines.append("### User Rules")
            for m in manual[:10]:
                lines.append(f"- {m.get('content', '')}")
            lines.append("")

        if realtime:
            lines.append("### Learned")
            for m in realtime[-10:]:
                lines.append(f"- [{m.get('type', 'info')}] {m.get('content', '')}")
            lines.append("")

        count = len(manual) + len(realtime)
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": "\n".join(lines)
            },
            "systemMessage": f"\033[1;97m🧠 Claude Never Forgets: Loaded {count} memories.\033[0m"
        }))

    except Exception:
        print(json.dumps({}))

    sys.exit(0)


if __name__ == "__main__":
    main()
