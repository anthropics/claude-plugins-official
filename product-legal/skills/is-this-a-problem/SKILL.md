---
name: is-this-a-problem
description: >
  Fast "is this a problem?" answer for the quick Slack question — pattern-matches
  against your calibration. Use when the user says "is this a problem", "quick
  question", "can we do X", "do I need legal review for", "sanity check", or
  pastes a PM's question that needs a same-minute fine / needs a look / hold call.
argument-hint: "[the question]"
---

# /is-this-a-problem

1. Load `~/.claude/plugins/config/claude-for-legal/product-legal/CLAUDE.md` → Risk calibration.
2. Apply the triage workflow below.
3. Pattern-match. Check for common traps.
4. Answer in one minute: ✅ Fine / ⚠️ Needs a look / 🛑 Hold. One sentence why.
5. If ⚠️ or 🛑: name the next step.

```
/product-legal:is-this-a-problem "Can we use customer logos on the pricing page?"
```

---

## Matter context

**Matter context.** Check `## Matter workspaces` in the practice-level CLAUDE.md. If `Enabled` is `✗` (the default for in-house users), skip the rest of this paragraph — skills use practice-level context and the matter machinery is invisible. If enabled and there is no active matter, ask: "Which matter is this for? Run `/product-legal:matter-workspace switch <slug>` or say `practice-level`." Load the active matter's `matter.md` for matter-specific context and overrides. Write outputs to the matter folder at `~/.claude/plugins/config/claude-for-legal/product-legal/matters/<matter-slug>/`. Never read another matter's files unless `Cross-matter context` is `on`.

---

## Destination check

Before producing output, check where it's going. If the user has named a destination (a channel, a distribution list, a counterparty, "everyone"), ask whether it's inside the privilege circle. Public channels, company-wide lists, counterparty/opposing counsel, vendors, and clients (for work product) waive the protection. When the destination looks outside the circle, flag it and offer (a) the privileged version for legal only, (b) a sanitized version for the broader channel, or (c) both — don't silently apply a privileged header and then help paste it somewhere the header won't protect it. See the canonical `## Shared guardrails → Destination check` in this plugin's CLAUDE.md.

## Purpose

Most "quick legal question" Slacks are one of three things: (a) not a problem, say so fast, (b) a real thing that needs a real look, route it, (c) a thing that looks fine but has a trap, catch the trap. This skill sorts in under a minute using the calibration table.

The goal is speed. The PM asked at 4:47pm. They want an answer, not a memo.

## Load calibration

Read `~/.claude/plugins/config/claude-for-legal/product-legal/CLAUDE.md` → `## Risk calibration`. The whole point of this skill is pattern-matching against that table.

## The triage

### Match against calibration

Does the question match a pattern in the calibration table?

**Matches "usually FYI":**
→ Say so. One line. "You're fine — [pattern]. Ship it."

**Matches "usually requires work":**
→ Name the work. "Needs a [PIA / vendor review / claims check]. Takes [timeline from table]. Want me to start it?"

**Matches "usually blocks":**
→ Stop them. "Hold on — [pattern]. This needs a real look before anyone commits to a date. Let's talk."

**Doesn't match anything:**
→ Say that too. "This doesn't pattern-match to anything I've seen here. Needs a human look — [your name] or me tomorrow?"

### The trap check

Some questions are fine on the surface but have a twist. Recognize the fact pattern, ask the catch question, then research the applicable doctrine for the specific fact pattern before concluding whether it's a problem or not.

| Question sounds like | Why it might not be simple | Catch it by asking |
|---|---|---|
| "Can we add [vendor] to the integration?" | Vendor touches a new data category — flag as potentially implicating privacy and vendor-risk regimes and route for research | "What data flows to them?" |
| "Can we A/B test the pricing page?" | Differential pricing by segment can implicate consumer-protection and anti-discrimination regimes — flag and route for research | "Are both arms seeing the same price for the same thing? How are users assigned to arms?" |
| "Can we auto-enroll users in the new feature?" | Default-on behavior for users who previously opted out can implicate consent and consumer-protection rules — flag and route for research | "Does this respect existing preferences?" |
| "Can we use customer logos on the site?" | Logo use is a separate permission from the contract relationship — flag as potentially implicating publicity / endorsement rules and the customer's own contract terms | "What does the contract say about publicity? Do we have written permission?" |
| "Can we train on this data?" | Usage rights for the original collection purpose may not extend to training — flag and research the notice/consent the users were given at collection | "What did we tell users when we collected it? What jurisdictions are the users in?" |
| "It's just an internal tool" | Internal tools still process personal data — flag as potentially implicating privacy regimes and route for research | "Whose data does it touch? Employees, customers, third parties?" |
| "We already do something similar" | "Similar" is doing a lot of work — the delta is where the issue usually is | "Similar how? What's actually different?" |
| "Can we use [AI vendor / LLM] for this?" | Vendor AI terms may permit training on inputs; use case may need an AIA — flag and route to `/ai-governance-legal:use-case-triage` | "Is there an AI addendum? What data goes into the model?" |
| "Can we add AI to this feature?" | May be a new use case not in the registry; may trigger AIA requirement — flag and route to `/ai-governance-legal:use-case-triage` | "What does the AI do — assistive or automated? Who does it act on?" |
| "The model just decides automatically" | Automated decision-making without human review is regulated in some jurisdictions — flag and research the applicable rules for the affected users' jurisdictions | "Who's affected? Is there a human in the loop? Where are the affected users?" |
| "It's AI-generated content" | Output IP and disclosure duties vary by jurisdiction and vendor terms — flag and route for research | "What's the content type? Does the vendor's ToS address output ownership? Who is the audience?" |
| "We're just fine-tuning on our data" | Training data rights, output IP, and vendor obligations all change — flag and route to `/ai-governance-legal:vendor-ai-review` | "What's in the training data? Is any of it customer or employee data?" |

If a trap might be present, ask the one question before answering. One question, not a checklist. When the answer suggests a real issue, flag for research and route — don't pattern-match to a legal conclusion from the question alone.

## Output format

**For Slack (the common case):**

Slack triage replies are internal legal advice. If the reply is being pasted into a ticket, document, or channel that's broadly shared with non-legal, prepend the work-product header from `~/.claude/plugins/config/claude-for-legal/product-legal/CLAUDE.md` `## Outputs` (it differs by user role — see `## Who's using this`):

```
[WORK-PRODUCT HEADER — per plugin config ## Outputs]
```

For an in-the-flow Slack DM reply to the PM, the short form is:

```
[✅ Fine | ⚠️ Needs a look | 🛑 Hold]

[One sentence: the call and why.]

[If ⚠️: what the look involves, how long]
[If 🛑: who to talk to, when]
```

**Examples:**

```
✅ Fine — adding an analytics event is an FYI here as long as it's covered by
the existing privacy policy categories. This one is.
```

```
⚠️ Needs a PIA — new data collection for [category]. Usually takes a day.
Want me to kick it off?
```

```
🛑 Hold — "train on customer data" triggers a bunch of things. What did the
customer agreement say about data use? Let's pull it before anyone promises
this to the customer.
```

```
⚠️ Needs an AI governance triage — adding an LLM to this workflow means we need
to check the use case against the registry and confirm an AIA is done before it
ships. Takes a day. Want me to run `/ai-governance-legal:use-case-triage` now?
```

## When to NOT use this skill

- The question is actually complex (multiple issues, novel area) → route to launch-review or feature-risk-assessment
- The question is "can you review this PRD" → that's launch-review, not triage
- You're not sure → say "I'm not sure, let me look properly" — a wrong fast answer is worse than a slow right one

## Tone

Fast, direct, helpful. The PM is not asking for a lecture. If it's fine, say "fine" — don't list the seven things you checked. If it's not fine, say what's not fine and what to do about it.

You are the lawyer people want to ask, not the one they route around.

## Close with the next-steps decision tree

End with the next-steps decision tree per CLAUDE.md `## Outputs`. Customize the options to what this skill just produced — the five default branches (draft the X, escalate, get more facts, watch and wait, something else) are a starting point, not a lock-in. The tree is the output; the lawyer picks.
