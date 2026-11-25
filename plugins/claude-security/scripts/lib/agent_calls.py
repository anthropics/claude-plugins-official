"""The agent() calls of a workflow, as the output file that Claude Code writes for it lists them."""

from __future__ import annotations

from collections import Counter

from .display import single_line
from .strictjson import JsonMap, is_list, is_map, is_str


def call_errors(output: JsonMap) -> dict[str, str]:
    """Each failed agent() call's label, on one line, mapped to the error text that the workflow's
    output file holds for it. A label that two rows have is left out, and so is a label that ends
    in ")"."""
    rows = output.get("workflowProgress")
    calls = [
        (single_line(label), call.get("error"))
        for call in (rows if is_list(rows) else ())
        if is_map(call) and is_str(label := call.get("label"))
    ]
    times = Counter(label for label, _ in calls)
    return {
        label: error
        for label, error in calls
        if times[label] == 1 and not label.endswith(")") and is_str(error) and error.strip()
    }
