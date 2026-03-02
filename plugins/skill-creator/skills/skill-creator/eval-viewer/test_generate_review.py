"""Tests for generate_review.py — specifically the HTML embedding safety."""

import html.parser
import json
import sys
from pathlib import Path

# Ensure the module is importable
sys.path.insert(0, str(Path(__file__).parent))

from generate_review import generate_html


class _ScriptExtractor(html.parser.HTMLParser):
    """Extract the text content of <script> tags as a browser would see them.

    Python's html.parser follows the same rule as browsers: a <script> block
    ends at the first </script> closing tag. If the embedded JSON contains a
    raw "</script>", the parser will truncate the script content there — which
    is exactly the bug we want to detect.
    """

    def __init__(self):
        super().__init__()
        self._in_script = False
        self.scripts: list[str] = []
        self._current: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag == "script":
            self._in_script = True
            self._current = []

    def handle_data(self, data):
        if self._in_script:
            self._current.append(data)

    def handle_endtag(self, tag):
        if tag == "script" and self._in_script:
            self.scripts.append("".join(self._current))
            self._in_script = False


def _browser_script_content(full_html: str) -> str:
    """Return the script content that contains EMBEDDED_DATA as a browser
    would parse it (i.e. truncated at any raw </script>).
    """
    parser = _ScriptExtractor()
    parser.feed(full_html)
    for script in parser.scripts:
        if "EMBEDDED_DATA" in script:
            return script
    raise ValueError("No <script> block containing EMBEDDED_DATA found")


def _extract_json_from_script(script_content: str) -> str:
    """Given the JS text of a script block, extract the JSON after
    'const EMBEDDED_DATA = ' up to the trailing ';'.
    """
    marker = "const EMBEDDED_DATA = "
    idx = script_content.index(marker)
    start = idx + len(marker)
    end = script_content.index(";\n", start)
    return script_content[start:end]


def test_script_tag_in_content_does_not_break_html():
    """If file content contains </script>, the generated HTML must not break.

    A literal </script> inside a <script> block causes the browser's HTML
    parser to terminate the script element prematurely. The embedding must
    escape such sequences so they don't appear literally in the HTML.
    """
    original_content = '<html><script>alert("xss")</script></html>'
    runs = [
        {
            "id": "run-1",
            "prompt": "Generate an HTML page",
            "eval_id": 1,
            "outputs": [
                {
                    "name": "index.html",
                    "type": "text",
                    "content": original_content,
                },
            ],
            "grading": None,
        },
    ]

    expected = {
        "skill_name": "test-skill",
        "runs": runs,
        "previous_feedback": {},
        "previous_outputs": {},
    }

    html = generate_html(runs, skill_name="test-skill")

    # 1) Parse the HTML the way a browser would — html.parser truncates the
    #    script content at the first </script>, just like a real browser.
    try:
        script_text = _browser_script_content(html)
    except ValueError as e:
        raise AssertionError(
            f"Browser-level parsing failed: {e}"
        ) from None

    # 2) The browser-visible script must contain the full EMBEDDED_DATA
    #    assignment.  Extract the JSON portion from it.
    try:
        json_str = _extract_json_from_script(script_text)
    except ValueError:
        raise AssertionError(
            "Browser-parsed script content is truncated — the EMBEDDED_DATA "
            "assignment is incomplete. A raw </script> in the JSON likely "
            "caused the browser to end the script block early.\n"
            f"  Browser saw (first 600 chars): {script_text[:600]!r}"
        ) from None

    # 3) The extracted JSON must be parseable
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise AssertionError(
            f"Embedded JSON is not valid — json.loads failed: {e}\n"
            f"  JSON string (first 600 chars): {json_str[:600]!r}"
        ) from None

    # 4) The parsed data must round-trip to the original input
    assert data == expected, (
        f"Round-trip mismatch — the parsed embedded data differs from input.\n"
        f"  Expected: {json.dumps(expected, indent=2)}\n"
        f"  Got:      {json.dumps(data, indent=2)}"
    )


def test_other_dangerous_sequences_escaped():
    """Additional dangerous sequences like <!-- and case-variant </Script>."""
    original_content = "<!-- comment --> and </Script> case insensitive"
    runs = [
        {
            "id": "run-2",
            "prompt": "Test HTML comment",
            "eval_id": 2,
            "outputs": [
                {
                    "name": "test.html",
                    "type": "text",
                    "content": original_content,
                },
            ],
            "grading": None,
        },
    ]

    expected = {
        "skill_name": "test-skill",
        "runs": runs,
        "previous_feedback": {},
        "previous_outputs": {},
    }

    html = generate_html(runs, skill_name="test-skill")

    # 1) Browser-level parse
    try:
        script_text = _browser_script_content(html)
    except ValueError as e:
        raise AssertionError(
            f"Browser-level parsing failed: {e}"
        ) from None

    # 2) Extract JSON from browser-visible script
    try:
        json_str = _extract_json_from_script(script_text)
    except ValueError:
        raise AssertionError(
            "Browser-parsed script content is truncated — the EMBEDDED_DATA "
            "assignment is incomplete.\n"
            f"  Browser saw (first 600 chars): {script_text[:600]!r}"
        ) from None

    # 3) Must be valid JSON
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise AssertionError(
            f"Embedded JSON is not valid — json.loads failed: {e}\n"
            f"  JSON string (first 600 chars): {json_str[:600]!r}"
        ) from None

    # 4) Round-trip check
    assert data == expected, (
        f"Round-trip mismatch — the parsed embedded data differs from input.\n"
        f"  Expected: {json.dumps(expected, indent=2)}\n"
        f"  Got:      {json.dumps(data, indent=2)}"
    )


if __name__ == "__main__":
    test_script_tag_in_content_does_not_break_html()
    print("PASS: test_script_tag_in_content_does_not_break_html")
    test_other_dangerous_sequences_escaped()
    print("PASS: test_other_dangerous_sequences_escaped")
    print("\nAll tests passed!")
