---
name: policy-redraft
description: Produce a proposed marked-up policy redraft that closes a gap found by /regulatory-legal:gaps or /regulatory-legal:policy-diff. A first draft for internal review — not for direct application to approved policy documents. Use when the user says "redraft the policy", "draft the policy fix", "mark up the policy", or when gap-surfacer hands off a gap for drafting.
argument-hint: "[GAP-ID or gap description]"
---

# /policy-redraft

1. Load `~/.claude/plugins/config/claude-for-legal/regulatory-legal/CLAUDE.md` → policy library index + practice profile.
2. Use the workflow below.
3. Gather inputs: the gap (from `/regulatory-legal:gaps` output or described directly), the current approved policy text, the rule text.
4. Verify the rule is current (per the policy-diff rule-status check). If you can't verify, emit the `⚠️ RULE STATUS UNVERIFIED` banner.
5. Produce a marked-up redraft of the affected policy section(s) — smallest-possible edit, `[verify]` tags carried through, inline comments explaining WHY each change was made.
6. Output a Policy Redraft Memo. Write it to a new file named `[policy-name]-proposed-redraft-[YYYY-MM-DD].md` — never write to the source policy document.
7. Do NOT close the gap in the tracker. The gap closes when the redraft is applied AND approved, which is the policy owner's action.

---

> This skill produces a **proposal**, not an edit. It writes to a new file with a clearly-marked draft filename. It never writes over a source policy document, and it never closes a gap in the tracker — the gap closes when the redraft is applied AND approved by the policy owner.

## Matter context

**Matter context.** Check `## Matter workspaces` in the practice-level CLAUDE.md. If `Enabled` is `✗` (the default for in-house users), skip the rest of this paragraph — skills use practice-level context and the matter machinery is invisible. If enabled and there is no active matter, ask: "Which matter is this for? Run `/regulatory-legal:matter-workspace switch <slug>` or say `practice-level`." Load the active matter's `matter.md` for matter-specific context and overrides. Write outputs to the matter folder at `~/.claude/plugins/config/claude-for-legal/regulatory-legal/matters/<matter-slug>/`. Never read another matter's files unless `Cross-matter context` is `on`.

---

## Purpose

Gap-surfacer finds the gap. Policy-diff names what needs to change. This skill takes the next step and produces a marked-up redraft of the affected policy section — small, specific, flagged — as a first draft for the policy owner's review.

## Hard guardrails — read these first

These are the load-bearing rules. If any of them would be violated, stop and ask.

1. **This is a PROPOSAL, not an edit.** Never write directly to a source policy document. The output goes to a new file at `[policy-name]-proposed-redraft-[YYYY-MM-DD].md`, or into the matter workspace. Not `[policy-name].md`.
2. **Never close the gap in the tracker.** Gaps close when the redraft is APPLIED AND APPROVED — that is the policy owner's action, not yours. If the user says "close the gap now that you've redrafted it," decline: "I produce the proposal. The gap closes when you've reviewed, applied, and approved the change. When that's done, tell me and I'll update the tracker."
3. **"Apply this for me" is not in scope.** If the user asks you to apply the redraft to the source policy: "I don't apply policy changes — that's the policy owner's action after review and approval. I produce the proposal. When it's been reviewed and approved, tell me and I'll update the gap tracker."
4. **Confirm the policy version before redrafting.** If the user gives you a file, ask: "Is this the approved version of the policy, and is it the latest? A redraft against an outdated policy creates divergence." If they paste text, trust but flag in the reviewer note.
5. **Smallest-possible edit.** Strike a word before a sentence, a sentence before a paragraph, a paragraph before a section. Only touch sections affected by the gap. Don't restyle the policy.
6. **Carry `[verify]` tags through.** Any effective date, threshold, citation, or requirement that came from model knowledge or an unverified source gets tagged in the redraft itself, not just in the memo.

## Step 1: Gather inputs

Three inputs are required. If any is missing, ask — don't infer.

### 1a. The gap

One of:
- A `GAP-ID` from the gap tracker — load the entry from `~/.claude/plugins/config/claude-for-legal/regulatory-legal/gap-tracker.yaml` (or the matter-level equivalent).
- A gap described in the user's message — capture the requirement, the regulation, and the affected policy.
- A diff summary pasted from `/regulatory-legal:policy-diff` output.

### 1b. The current policy text

One of:
- A file path — read it, then ask: "Is this the approved version of the policy, and is it the latest? A redraft against an outdated policy creates divergence." Note the answer in the reviewer note.
- Pasted text — trust but flag in the reviewer note: "Policy text was pasted directly; I assumed it was the current approved version. Confirm before applying."
- Neither — ask for one. Do not guess at the policy text from the gap tracker or from web search.

### 1c. The rule text

One of:
- The diff output (already has the rule extracted and tagged).
- A fetched regulation — note the source with a provenance tag.
- Pasted rule text from the user — tag `[user provided]`.

If the rule text is partial or ambiguous, apply the **no silent supplement** rule from CLAUDE.md: offer the user the options (paste full text, point at primary source, web-search-with-verify-tag, or stop), and wait.

## Step 2: Verify the rule is current

Use the same rule-status check pattern as `policy-diff`. Red flags that the rule may not be in force:

- The applicability/compliance date has passed by more than 30 days with no confirmation it wasn't delayed.
- The rule is more than 12 months old.
- The rule is a politically contentious final rule (major rulemakings are frequently challenged).

When you see a red flag, check (via research MCP, web search if enabled, or the Federal Register docket) for: delays, stays, injunctions, rescission proposals, vacatur, or amendments. If you can verify the rule is in force, proceed. If you cannot verify:

> `⚠️ RULE STATUS UNVERIFIED — I could not confirm this rule is currently in force. Final rules are frequently stayed, enjoined, delayed, or rescinded after publication. Do not apply this redraft until you confirm the rule's status at the Federal Register docket or with outside counsel.`

Emit that banner above the work-product header. Tag every effective/compliance date in the redraft as `[effective date per published rule — status unverified]`.

## Step 3: Produce the redraft

A marked-up version of the affected policy section.

### Redline granularity — smallest possible edit

- Strike a word before a sentence.
- Strike a sentence before a paragraph.
- Strike a paragraph before a section.
- Only touch sections affected by the gap. Don't restyle the whole policy.

### Conventions

- Struck text: `~~struck text~~`
- Inserted text: **inserted text**
- Each change carries an inline comment explaining WHY — the rule, the cite, the gap being closed:

  > `[Change: added biometric identifiers to the PII definition per COPPA 2025 amendments, 16 CFR 312.2 (effective Apr 22 2026) [verify]]`

- Any effective date, threshold, citation, or requirement that came from model knowledge or an unverified source gets a `[verify]` tag inline — not just in the change summary.
- Carry source tags through from the diff: `[Federal Register]`, `[web search — verify]`, `[model knowledge — verify]`, `[user provided]`. Don't strip them when moving from the diff to the redraft.

### Scope discipline

If a section of the policy isn't affected by the gap, leave it alone. A redraft that touches sections outside the gap looks like the AI opined on things it wasn't asked to opine on, and makes the review harder.

If you see a second gap while redrafting — a provision that's clearly out of step with the rule but wasn't in the original gap — don't silently fix it. Flag it in the reviewer note: "While redrafting for [GAP-ID], I noticed [other provision] appears to have a related issue with [requirement]. Not included in this redraft. Consider a follow-on gap."

## Step 4: Output — Policy Redraft Memo

```markdown
[WORK-PRODUCT HEADER — per plugin config ## Outputs — differs by role; see `## Who's using this`]

> **⚠️ Reviewer note**
> - **Sources:** [Research connector: CourtListener ✓ verified | not connected — cites from training knowledge, verify before relying]
> - **Read:** [sections of the policy reviewed; what wasn't read]
> - **Flagged for your judgment:** [N items marked `[review]` inline | none]
> - **Currency:** [rule status verified against [source], [date] | unverified — see banner above]
> - **Before relying:** confirm this is the current approved version of the policy; verify rule status and effective date; get the policy owner's review; follow your policy-change approval process; update the gap tracker only when applied and approved.

## Policy Redraft: [Policy name]

**Gap:** [GAP-ID or short description]
**Regulation:** [name, citation, effective date]
**Policy:** [name, last-updated date]
**Status:** PROPOSAL — not yet reviewed or approved

### Bottom line

[One sentence: what the gap is. One sentence: what the redraft does. One sentence: what needs review.]

### Marked-up policy section(s)

[The redlined text, with inline `[Change: ...]` comments. Only the affected sections.]

### Change summary

| # | Provision | Current | Proposed | Why | Verify |
|---|---|---|---|---|---|
| 1 | §2.1 PII definition | "…names, addresses, SSNs…" | "…names, addresses, SSNs, biometric identifiers…" | COPPA 2025 amendments expand PII to cover biometrics | [Federal Register] |
| 2 | §4.3 Retention period | "30 days" | "14 days" | New rule imposes 14-day cap | `[verify — model knowledge]` |

### Before applying — checklist

- [ ] Confirm this is the current approved version of the policy being redrafted.
- [ ] Verify the rule status and effective date (Federal Register docket, or outside counsel).
- [ ] Get the policy owner's review.
- [ ] Follow your policy-change approval process.
- [ ] Update the gap tracker when applied and approved — not before.

---

**What next? Pick one and I'll help you build it out:**

1. **Apply and get sign-off** — you review, circulate to the policy owner, walk it through your approval process. When approved, tell me and I'll mark the gap closed.
2. **Get more info on [X]** — if a specific change needs more grounding (a cite verified, a threshold checked, a jurisdiction question resolved), tell me which one and I'll dig in.
3. **Escalate to [owner / GC]** — if the redraft raises something above the policy-owner's authority, I'll draft a short escalation with the facts, the proposed change, and what decision is needed.
4. **Watch and wait** — if the rule's status is uncertain or the policy owner is unavailable, I'll add a revisit note to the gap tracker.
5. **Something else** — tell me what you'd do with it.
```

## Filename

The output file name makes clear it's a draft. Use:

`[policy-name]-proposed-redraft-[YYYY-MM-DD].md`

Not `[policy-name].md`. Not `[policy-name]-v2.md`. The word "proposed-redraft" and the date are load-bearing — they prevent the draft from being mistaken for the current version.

Write to the matter workspace if one is active; otherwise to the current working directory or a location the user names. Do not write to the policy library source directory.

## Config-dependent fallbacks

This skill reads the policy library index and owners from `~/.claude/plugins/config/claude-for-legal/regulatory-legal/CLAUDE.md`. When a value it needs is empty or still `[PLACEHOLDER]`:

- **Policy owner missing:** still produce the redraft. Note in the reviewer note: "No policy owner is set for [policy] in `## Policy library`. Assign one with `/regulatory-legal:cold-start-interview --redo` so the approval path is routable."
- **Policy library empty and the gap doesn't name a specific policy:** stop and ask: "I need the current policy text to redraft. Paste the text of the affected policy, or point me at the file."

Say nothing about config when the values are populated.

## Interactions with other skills

- **Upstream inputs** come from `policy-diff` (per-requirement gap analysis) and `gap-surfacer` (the tracker). Carry their source tags and `[verify]` flags through.
- **Gap tracker state:** this skill does NOT change the tracker. It doesn't mark the gap closed, doesn't mark it in-progress, doesn't touch `notified`. If you want a paper trail that a redraft exists, the policy owner or the user can update the gap entry with a resolution note when the redraft is applied and approved — see `/regulatory-legal:gaps --close`.
- **Severity floor:** if the upstream gap is 🔴 or 🟠, the memo's Bottom line carries that severity. Silent demotion is a contradiction a reviewing lawyer cannot see. See CLAUDE.md `## Cross-skill severity floor`.

## Close with the next-steps decision tree

Included in the output template above. Customize the options to what the redraft actually produced — if the rule status is unverified, option 2 (get more info) moves up; if the policy owner isn't set, option 3 (escalate) gets specific.

## What this skill does not do

- Apply the redraft to the source policy. That's the policy owner's action.
- Close the gap in the tracker. Gaps close when the redraft is applied and approved.
- Rewrite the whole policy. Smallest-possible edit to close the gap.
- Produce multi-policy redrafts. One gap, one policy, one memo. A `:package` command for multi-policy fan-out is a future skill.
- Produce the "apply" workflow. An `:apply` command with an approval gate is a future skill.
