---
description: Generate a detailed safety risk report for text or a file
argument-hint: [file path or text]
---

# Safety Risk Report

Generate a comprehensive safety analysis:
1. If a file path is provided, read the file and scan its contents
2. If text is provided, scan that text directly

Present the report showing:
- Overall risk level
- Whether content would be blocked
- Findings grouped by category (prompt_injection, pii, harmful_content, toxicity, hallucination)
- Specific findings with risk levels
- Redacted text if PII was found
