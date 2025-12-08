#!/usr/bin/env python3
"""Tool Rejected - Save when user rejects a tool with feedback."""

import json
import sys
from datetime import datetime
from pathlib import Path


def main():
    try:
        data = json.loads(sys.stdin.read())
        error = data.get("error", "")

        if "rejected" not in error.lower() or len(error) < 10:
            print(json.dumps({}))
            sys.exit(0)

        cwd = data.get("cwd", ".")
        memory_file = Path(cwd) / ".claude" / "memories" / "project_memory.json"
        memory_file.parent.mkdir(parents=True, exist_ok=True)

        if memory_file.exists():
            memories = json.load(open(memory_file, "r", encoding="utf-8"))
        else:
            memories = {"memories": [], "manual_memories": [], "realtime_memories": []}

        tool_name = data.get("tool_name", "unknown")
        content = f"[CORRECTION] {tool_name}: {error}"[:300]

        memories.setdefault("realtime_memories", []).append({
            "type": "correction",
            "content": content,
            "added_at": datetime.now().isoformat(),
            "source": "tool_rejection"
        })

        memories["updated_at"] = datetime.now().isoformat()
        json.dump(memories, open(memory_file, "w", encoding="utf-8"), indent=2, ensure_ascii=False)

    except Exception:
        pass

    print(json.dumps({}))
    sys.exit(0)


if __name__ == "__main__":
    main()
