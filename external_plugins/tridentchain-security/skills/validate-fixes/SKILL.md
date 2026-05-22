---
description: Validate dependency upgrades by re-scanning and comparing TridentChain results
---

# Validate fixes after patch

When the user upgrades dependencies or asks to confirm a fix:

1. **Baseline** — Run `scan_project` on `project_path` and save the JSON result.
2. **Upgrade** — Apply dependency changes (`npm update`, `pip install -U`, etc.).
3. **Re-scan** — Run the same `scan_project` on the same path.
4. **Validate** — Call `validate_after_patch` with `baseline_json` and `after_patch_json`.
5. **Report** — Summarise `resolved_count`, `remaining_count`, `new_count`, and `validation_passed`.

## CLI fallback (no MCP)

```bash
tridentchain-security --validate \
  --baseline-report baseline.json \
  --after-report .tridentchain-out/scan-report.json
```
