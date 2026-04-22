---
name: plan-sync-on-success
enabled: true
event: bash
action: warn
tool_matcher: Bash
conditions:
  - field: command
    operator: regex_match
    pattern: terraform\s+apply|ansible-playbook\s+\S+\.ya?ml
  - field: tool_response.exitCode
    operator: equals
    pattern: "0"
---

✅ **IaC change applied successfully — Plan-Sync-Pflicht**

A `terraform apply` or `ansible-playbook <...>.yml` just exited 0. Now update,
in one commit, every affected:

- `docs/parts/part-XX-<slug>/index.md`
- `docs/parts/part-XX-<slug>/plan.md`
- `docs/parts/part-XX-<slug>/dod.md`
- `docs/parts/part-XX-<slug>/rollout-history.md` (date allowed here)
- `docs/parts/part-XX-<slug>/handoff.md`

**Why this fires only on success:** The second condition
`tool_response.exitCode equals "0"` is only available on PostToolUse. On
PreToolUse the field is absent, the rule does not match, and nothing is
emitted.

**Adapt to your project:** change the regex in the first condition to the
IaC commands you care about (`helmfile apply`, `pulumi up`, `kubectl
apply`, …), and rewrite the message body to match your doc layout.
