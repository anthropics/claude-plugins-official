# PrivacyScrubber

[PrivacyScrubber](https://privacyscrubber.com) is a zero-trust, client-side data sanitization engine and Model Context Protocol (MCP) server for AI workflows.

It intercepts sensitive data (API credentials, private keys, database connection strings, and customer PII) locally in RAM before prompts reach cloud LLMs, assigns deterministic tokens (e.g. `[API_KEY_1]`, `[EMAIL_1]`), and restores genuine values upon receiving AI completions.

## Available Tools

- **`guard_exec`** — executes shell commands and redacts credentials/PII from terminal outputs in RAM before returning them to Claude.
- **`guard_read_file`** — safely inspects `.env`, secrets, or production logs with in-memory token masking.
- **`guard_git_diff`** — reviews staged or unstaged git diffs without exposing credentials to the cloud context.
- **`guard_apply_patch`** — writes code back to disk, locally restoring genuine credentials without network transit.
- **`sanitize_text`** — masks sensitive text and code across 25+ regulatory profiles (General, Dev, Medical/HIPAA, Finance/PCI, Legal, HR).
- **`reveal_text`** — reverses token placeholders back to authentic values.

## License Key (optional)

PrivacyScrubber works out of the box on the Free tier. For enterprise character limits and specialized profiles:

```bash
export PRIVACYSCRUBBER_KEY="your-license-key"
```

---

Maintained by [PrivacyScrubber](https://privacyscrubber.com). Source: [moxno/privacyscrubber-mcp](https://github.com/moxno/privacyscrubber-mcp).
