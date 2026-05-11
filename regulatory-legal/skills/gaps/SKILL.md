---
name: gaps
description: Open gaps tracker — what's flagged and not yet closed. Use when the user asks "what gaps are open", "gap tracker", "remediation status", or wants to close (--close GAP-ID) or risk-accept (--accept GAP-ID) a tracked gap.
argument-hint: "[optional: --close GAP-ID | --accept GAP-ID]"
---

# /gaps

1. Read the gap tracker at `~/.claude/plugins/config/claude-for-legal/regulatory-legal/gap-tracker.yaml`.
2. If `--close`: mark gap closed with resolution note.
3. If `--accept`: record the risk-acceptance rationale and acceptor, status → risk-accepted.
4. Otherwise: report open gaps by age and materiality.

> Detailed tracker schema, status-report format, owner-notification logic (per-send confirmation, no exceptions), reminder cadence, the close/risk-accept modes, and the consequential-action gate live in the **gap-surfacer** reference skill — load it before doing substantive work.
