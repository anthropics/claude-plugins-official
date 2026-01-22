#!/usr/bin/env python3
"""User Prompt - Save user message and Claude's last response."""

import json
import os
import sys
from datetime import datetime
from pathlib import Path


def get_memories(cwd: str) -> tuple[Path, dict]:
    """Load or create memory file."""
    memory_file = Path(cwd) / ".claude" / "memories" / "project_memory.json"
    memory_file.parent.mkdir(parents=True, exist_ok=True)

    if memory_file.exists():
        try:
            return memory_file, json.load(open(memory_file, "r", encoding="utf-8"))
        except (json.JSONDecodeError, IOError):
            pass

    return memory_file, {
        "memories": [],
        "manual_memories": [],
        "realtime_memories": [],
        "created_at": datetime.now().isoformat()
    }


def get_last_claude_response(transcript_path: str) -> str | None:
    """Get Claude's last response from transcript."""
    if not transcript_path or not os.path.exists(transcript_path):
        return None

    try:
        with open(transcript_path, "r", encoding="utf-8") as f:
            for line in reversed(f.readlines()):
                msg = json.loads(line.strip())
                if msg.get("type") == "assistant":
                    content = msg.get("message", {}).get("content", [])
                    for block in content if isinstance(content, list) else []:
                        if block.get("type") == "text" and len(block.get("text", "")) > 10:
                            return block["text"][:200]
    except Exception:
        pass
    return None


def is_duplicate(content: str, memories: list) -> bool:
    """Check for duplicate."""
    key = content.lower()[:50]
    return any(m.get("content", "").lower()[:50] == key for m in memories)


def main():
    try:
        data = json.loads(sys.stdin.read())
        prompt = data.get("prompt", "")

        if len(prompt) < 5 or prompt.startswith("/"):
            print(json.dumps({}))
            sys.exit(0)

        cwd = data.get("cwd", os.getcwd())
        transcript = data.get("transcript_path", "")
        memory_file, memories = get_memories(cwd)

        if "realtime_memories" not in memories:
            memories["realtime_memories"] = []

        # Save Claude's last response
        response = get_last_claude_response(transcript)
        if response and not is_duplicate(response, memories["realtime_memories"]):
            memories["realtime_memories"].append({
                "type": "claude_response",
                "content": response,
                "added_at": datetime.now().isoformat(),
                "source": "realtime_capture"
            })

        # Save user message
        clean_prompt = " ".join(prompt.split())[:200]
        if not is_duplicate(clean_prompt, memories["realtime_memories"]):
            memories["realtime_memories"].append({
                "type": "message",
                "content": clean_prompt,
                "added_at": datetime.now().isoformat(),
                "source": "realtime_capture"
            })

        memories["updated_at"] = datetime.now().isoformat()
        json.dump(memories, open(memory_file, "w", encoding="utf-8"), indent=2, ensure_ascii=False)

    except Exception:
        pass

    print(json.dumps({}))
    sys.exit(0)


if __name__ == "__main__":
    main()
