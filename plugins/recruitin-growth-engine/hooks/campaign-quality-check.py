#!/usr/bin/env python3
"""
Campaign Quality Check Hook for Recruitin Growth Engine

This hook runs on the 'stop' event to validate that generated campaign content
meets the quality standards before the user acts on it.

It checks for:
- Generic filler phrases that reduce content quality
- Missing visual prompt specifications
- Incomplete ad copy structures
- Dutch language quality indicators
"""

import json
import re
import sys


# Generic filler phrases to flag (Dutch and English)
FILLER_PHRASES = [
    "in de huidige markt",
    "in today's competitive market",
    "passie voor",
    "passionate about",
    "dynamisch team",
    "dynamic team",
    "een van de snelst groeiende",
    "one of the fastest growing",
    "unieke kans",
    "unique opportunity",
    "wij zijn op zoek naar een enthousiaste",
    "we are looking for an enthusiastic",
    "ben jij de",
    "are you the",
    "no-nonsense",
    "hands-on mentaliteit",
    "aansprekend salaris",
    "marktconform salaris",
    "uitstekende arbeidsvoorwaarden",
    "gezellig team",
    "informele werksfeer",
    "korte lijnen",
    "platte organisatie",
]

# Required visual prompt fields
REQUIRED_VISUAL_FIELDS = [
    "platform",
    "format",
    "style",
    "mood",
]


def check_content_quality(text: str) -> list[dict]:
    """Check generated content for quality issues."""
    warnings = []

    text_lower = text.lower()

    # Check for filler phrases
    for phrase in FILLER_PHRASES:
        if phrase.lower() in text_lower:
            warnings.append({
                "type": "filler_phrase",
                "severity": "warn",
                "message": f"Generic filler phrase detected: '{phrase}'. Consider replacing with a specific, concrete detail.",
            })

    # Check if visual prompt is mentioned but incomplete
    if "visual prompt" in text_lower or "visual_prompt" in text_lower:
        missing_fields = []
        for field in REQUIRED_VISUAL_FIELDS:
            if field not in text_lower:
                missing_fields.append(field)
        if missing_fields:
            warnings.append({
                "type": "incomplete_visual_prompt",
                "severity": "warn",
                "message": f"Visual prompt may be incomplete. Missing fields: {', '.join(missing_fields)}",
            })

    # Check for Meta ad copy completeness
    if "primary text" in text_lower or "headline" in text_lower:
        if "primary text" in text_lower and "headline" not in text_lower:
            warnings.append({
                "type": "incomplete_ad_copy",
                "severity": "warn",
                "message": "Meta ad copy appears incomplete: has primary text but missing headline.",
            })
        if "headline" in text_lower and "description" not in text_lower:
            warnings.append({
                "type": "incomplete_ad_copy",
                "severity": "warn",
                "message": "Meta ad copy appears incomplete: has headline but missing description.",
            })

    return warnings


def main():
    """Process the hook input and return quality warnings."""
    try:
        input_data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, EOFError):
        # No input or invalid JSON, skip check
        print(json.dumps({"result": "pass"}))
        return

    # Extract the assistant's response text
    transcript = input_data.get("transcript", [])
    if not transcript:
        print(json.dumps({"result": "pass"}))
        return

    # Get the last assistant message
    last_messages = [
        msg for msg in transcript
        if msg.get("role") == "assistant"
    ]
    if not last_messages:
        print(json.dumps({"result": "pass"}))
        return

    last_message = last_messages[-1]
    content = ""
    if isinstance(last_message.get("content"), str):
        content = last_message["content"]
    elif isinstance(last_message.get("content"), list):
        content = " ".join(
            block.get("text", "")
            for block in last_message["content"]
            if isinstance(block, dict) and block.get("type") == "text"
        )

    # Only check if content looks like campaign output
    campaign_indicators = [
        "campagne", "campaign", "linkedin", "meta ad",
        "visual prompt", "tone of voice", "cta",
        "solliciteer", "vacature", "recruitment",
    ]
    is_campaign_content = any(
        indicator in content.lower() for indicator in campaign_indicators
    )

    if not is_campaign_content:
        print(json.dumps({"result": "pass"}))
        return

    warnings = check_content_quality(content)

    if warnings:
        warning_messages = "\n".join(
            f"  - [{w['severity'].upper()}] {w['message']}" for w in warnings
        )
        result = {
            "result": "pass",
            "message": f"Campaign Quality Check found {len(warnings)} issue(s):\n{warning_messages}\n\nConsider addressing these before publishing.",
        }
    else:
        result = {"result": "pass"}

    print(json.dumps(result))


if __name__ == "__main__":
    main()
