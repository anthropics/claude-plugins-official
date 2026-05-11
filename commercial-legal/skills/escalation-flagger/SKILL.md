---
name: escalation-flagger
description: >
  Route a contract issue to the right approver per the escalation matrix in
  `~/.claude/plugins/config/claude-for-legal/commercial-legal/CLAUDE.md`, and draft the ask. Use when the user
  says "who needs to approve this", "escalate this", "does this need GC sign-off",
  "route this for approval", or when another skill finds an issue that exceeds the
  reviewer's authority.
argument-hint: "[describe the issue, or reference a review memo]"
---

# /escalation-flagger

Names the approver for a contract issue per the `~/.claude/plugins/config/claude-for-legal/commercial-legal/CLAUDE.md` escalation matrix and drafts the message so you're not writing "hey got a sec" at 5pm.

## Instructions

1. **Load `~/.claude/plugins/config/claude-for-legal/commercial-legal/CLAUDE.md`** → Escalation section. If missing, say so — the practice profile needs editing.

2. **Characterize the issue:** dollar threshold / term deviation / automatic trigger / business decision.

3. **Match to matrix, name the approver.** Be specific — a person or role, not "legal leadership."

4. **Draft the ask** per the template below: what the contract says, what playbook says, options with recommendation, decision-by date.

5. **Do not send.** Draft it, show it, let the lawyer send.

## Examples

```
/commercial-legal:escalation-flagger
The Acme MSA has uncapped liability — who approves and what do I say?
```

```
/commercial-legal:escalation-flagger
Reference: acme-review-memo.md
Issue: §8.2 indemnity carveouts
```

---

## Matter context

**Matter context.** Check `## Matter workspaces` in the practice-level CLAUDE.md. If `Enabled` is `✗` (the default for in-house users), skip the rest of this paragraph — skills use practice-level context and the matter machinery is invisible. If enabled and there is no active matter, ask: "Which matter is this for? Run `/commercial-legal:matter-workspace switch <slug>` or say `practice-level`." Load the active matter's `matter.md` for matter-specific context and overrides. Write outputs to the matter folder at `~/.claude/plugins/config/claude-for-legal/commercial-legal/matters/<matter-slug>/`. Never read another matter's files unless `Cross-matter context` is `on`.

---

## Purpose

Every contracts team has an escalation matrix, written or not. This skill reads the written one (in `~/.claude/plugins/config/claude-for-legal/commercial-legal/CLAUDE.md`), matches a contract issue against it, names the approver, and drafts the ask so the lawyer isn't writing "hey do you have a sec" messages at 5pm.

## Load the matrix

**Which side?** Before matching to the matrix, determine which side the company is on for the contract whose issue is being escalated. Usually obvious: if the counterparty is a vendor/supplier providing goods or services, you're purchasing-side. If the counterparty is a customer buying your product/service, you're sales-side. If it's not obvious, ask. Read the matching playbook section (`### Sales-side playbook` or `### Purchasing-side playbook`) to evaluate whether the term is inside fallbacks or triggers an automatic escalation — a term that's fine on one side can be a hard-no on the other. Note which side in the drafted ask so the approver knows which playbook was applied.

Read `~/.claude/plugins/config/claude-for-legal/commercial-legal/CLAUDE.md` → `## Escalation`. If it's missing or vague, say so — the cold-start interview should have captured this, and if it didn't, the practice profile needs editing.

Expected structure:

| Can approve | Threshold | Escalates to | Via |
|---|---|---|---|
| Paralegal | Standard terms, <$50K | Counsel | Slack |
| Counsel | Non-standard but within fallbacks, <$500K | GC | Slack or email |
| GC | Everything else | CFO/Board | Meeting |

Plus **automatic escalation triggers** — things that escalate regardless of dollar value. Typically: unlimited liability, IP assignment, anything on the "never accept" lists.

## Workflow

### Step 1: Characterize the issue

What's being escalated?

- **Dollar threshold:** Contract value exceeds someone's approval authority
- **Term deviation:** A term is outside the playbook fallbacks — someone more senior needs to decide whether to accept
- **Automatic trigger:** One of the always-escalate items is present
- **Business decision:** Not a legal call — needs the business owner, not legal leadership

Don't escalate things that are actually fine. If the term is within the fallbacks in `~/.claude/plugins/config/claude-for-legal/commercial-legal/CLAUDE.md`, it doesn't need to go up.

### Step 2: Match to the matrix

```
Is the issue an automatic trigger?
  → YES: escalate to [person named for that trigger]
  → NO: continue

Is the contract value above the reviewer's threshold?
  → YES: escalate to whoever has authority at that dollar level
  → NO: continue

Is the term deviation outside all documented fallbacks?
  → YES: escalate to whoever can approve non-standard terms
  → NO: reviewer can approve — no escalation needed
```

### Step 3: Name the approver

Be specific. Not "escalate to legal leadership" — name the person or role from `~/.claude/plugins/config/claude-for-legal/commercial-legal/CLAUDE.md`. If the matrix doesn't name anyone for this situation, say so: "The escalation matrix doesn't cover [situation]. Suggest asking [GC name] who owns this."

### Step 4: Draft the ask

The approver should be able to decide from the message alone — no "let me pull up the contract."

```markdown
**Escalating to:** [name]
**Via:** [Slack #channel / email / meeting — per `~/.claude/plugins/config/claude-for-legal/commercial-legal/CLAUDE.md`]
**Urgency:** [deadline if there is one]

---

Hey [name] —

Need your call on the [Counterparty] [agreement type]. [One sentence on deal context.]

**The issue:** [Plain English, one paragraph. What they want, why it's outside
our standard, what the risk actually is.]

**What the contract says:**
> "[exact quote]"

**What our playbook says:** [quote from `~/.claude/plugins/config/claude-for-legal/commercial-legal/CLAUDE.md`]

**Options:**
1. **Accept** — [one line on why this might be okay]
2. **Push back with:** "[proposed counter-language]" — [one line on likely counterparty reaction]
3. **Walk** — [one line on whether that's realistic given the business context]

**My recommendation:** [which option and why, briefly]

**Need a decision by:** [date, if there is a deadline]

[Link to full review memo]
```

### Step 5: Record the escalation

If this team uses a ticket system or [CLM] approval workflows, log it. If not, note in the review memo that the escalation was sent, to whom, and when. The next person who reads the memo should see the status.

## Calibration: when in doubt, escalate with a note

The cost of an unnecessary escalation is ~30 seconds of the approver's time — they read, say "fine, proceed," and the record shows they saw it. The cost of a missed escalation is signing an unapproved term, which is a one-way door. The costs are not symmetric. **When in doubt, escalate.**

The calibration for what warrants escalation lives in `~/.claude/plugins/config/claude-for-legal/commercial-legal/CLAUDE.md`, not in this skill. Check the playbook's stated position, its fallbacks, and its "automatic escalation regardless of dollar value" list:

- **Clearly inside the fallback range:** no escalation needed.
- **Clearly outside the range, or on the automatic-escalation list:** escalate.
- **Uncertain — the term is ambiguous, novel, or arguably inside the range but the argument is a stretch:** escalate anyway, and note the uncertainty explicitly. The draft flags the specific question the approver needs to decide and why the skill couldn't confidently place it inside the fallback. The approver narrows; the skill does not.

Do not suppress an escalation because over-escalation might train approvers to skim. That's an approver-experience problem the attorney solves by adjusting thresholds in the playbook, not a problem the skill solves by making its own subjective call on a term it's uncertain about.

If a term comes up that the playbook doesn't address, don't guess the threshold — ask the reviewing attorney whether this class of issue should escalate, and offer to record the answer in `~/.claude/plugins/config/claude-for-legal/commercial-legal/CLAUDE.md` so future reviews are consistent.

## What this skill does not do

- It does not approve anything. It routes.
- It does not decide between the options. The draft includes a recommendation but the approver decides.
- It does not send the escalation message — it drafts it. The lawyer sends it after reading.
