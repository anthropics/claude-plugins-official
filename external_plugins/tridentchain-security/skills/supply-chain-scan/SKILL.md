---
description: Scan the workspace for supply-chain vulnerabilities using TridentChain Security
---

# Supply chain scan

When the user asks about dependency vulnerabilities, CVEs, supply-chain risk, or security of `package.json` / lockfiles / `requirements.txt`:

1. Use the **tridentchain** MCP tools.
2. Prefer **`scan_project`** for speed; use **`scan_full`** for system tools and IDE extensions too.
3. Pass **`project_path`** as the workspace root (absolute path).
4. Use **`output_dir`** `.tridentchain-out` under the project unless the user specifies another path.
5. Summarize **`findings`** by severity; mention **`output_paths`** for HTML reports.
6. **No API keys** are required for the default profile.

## CLI fallback (if MCP unavailable)

```bash
tridentchain-security --scan project --project-path <workspace> --output-dir .tridentchain-out
```

Read `.tridentchain-out/scan-report.json` for details.

## Do not

- Put API keys in chat; use environment variables only.
- Scan paths outside the user's project without permission.
