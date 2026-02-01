#!/usr/bin/env python3
"""Stop Hook - Trigger cleanup if 10+ memories."""

import json
import sys
from pathlib import Path


def main():
    try:
        data = json.loads(sys.stdin.read())
        cwd = data.get("cwd", ".")
        memory_file = Path(cwd) / ".claude" / "memories" / "project_memory.json"

        if not memory_file.exists():
            print(json.dumps({}))
            sys.exit(0)

        memories = json.load(open(memory_file, "r", encoding="utf-8"))
        count = len(memories.get("realtime_memories", []))

        if count >= 10:
            print(json.dumps({
                "decision": "block",
                "reason": f"""🧹 Memory cleanup required. You have {count} memories.

Read .claude/memories/project_memory.json and consolidate realtime_memories.

SIGNAL (keep): preferences, decisions, corrections, tech choices, completed features, conventions
NOISE (remove): greetings, thanks, praise without context, exact duplicates

For each memory ask: "Will this help me serve the user better next session?" If yes, keep it.

Merge related memories into single entries. Target: 5-7 memories. Write back silently."""
            }))
        else:
            print(json.dumps({}))

    except Exception:
        print(json.dumps({}))

    sys.exit(0)


if __name__ == "__main__":
    main()
