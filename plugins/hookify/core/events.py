"""Event helpers for hookify hook executors."""

FILE_TOOLS = {"Edit", "Write", "MultiEdit"}


def event_for_tool(tool_name: str) -> str:
    """Return the hookify event bucket for a Claude tool name."""
    if tool_name == "Bash":
        return "bash"
    if tool_name in FILE_TOOLS:
        return "file"
    return "other"
