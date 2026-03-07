---
description: Check text for personally identifiable information and show redacted version
argument-hint: [text or file path]
---

# Check for PII

Scan the provided text for personally identifiable information:
1. Detect PII types: emails, SSNs, credit cards (Luhn-validated), phone numbers, API keys, tokens
2. Report what PII types were found with risk levels
3. Show the redacted version with PII replaced by labels like [EMAIL], [SSN], [CREDIT_CARD]

If a file path is provided instead of text, read the file first then scan its contents.
