---
description: Scan text for safety issues using all Sentinel AI scanners
argument-hint: [text to scan]
---

# Scan Text for Safety Issues

Run all 7 Sentinel AI safety scanners against the provided text:
- Prompt injection detection
- PII detection and redaction
- Harmful content filtering
- Hallucination signal detection
- Toxicity detection
- Blocked terms checking
- Tool-use safety analysis

Report findings with risk levels (NONE, LOW, MEDIUM, HIGH, CRITICAL) and whether the content should be blocked.

If PII is detected, also show the redacted version of the text.
