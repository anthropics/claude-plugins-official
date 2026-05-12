---
name: policy-diff
description: Diff a specific regulatory change against the indexed policy library. Use when a reg has changed and you need to know which policies it touches and what the gap is, when the user says "diff this reg against our policies", "which policy does this affect", or "gap analysis", or when reg-feed-watcher hands off a material item.
argument-hint: "[reg name, or paste reg text/summary]"
---

# /policy-diff

1. Load `~/.claude/plugins/config/claude-for-legal/regulatory-legal/CLAUDE.md` → policy library index.
2. Use the workflow below.
3. Extract requirements from the reg. Match to indexed policies.
4. Output: per-requirement gap analysis, which policy needs updating.

---

## Matter context

**Matter context.** Check `## Matter workspaces` in the practice-level CLAUDE.md. If `Enabled` is `✗` (the default for in-house users), skip the rest of this paragraph — skills use practice-level context and the matter machinery is invisible. If enabled and there is no active matter, ask: "Which matter is this for? Run `/regulatory-legal:matter-workspace switch <slug>` or say `practice-level`." Load the active matter's `matter.md` for matter-specific context and overrides. Write outputs to the matter folder at `~/.claude/plugins/config/claude-for-legal/regulatory-legal/matters/<matter-slug>/`. Never read another matter's files unless `Cross-matter context` is `on`.

---

## Purpose

A reg changed. You have policies. This skill finds which policies the change touches and what the gap is between "what the reg now requires" and "what the policy says."

## Load context

`~/.claude/plugins/config/claude-for-legal/regulatory-legal/CLAUDE.md` → policy library index (policies, locations, owners).

## Scope integrity

If the user asks you to exclude a policy section, requirement, or category from the diff:

1. Do it — the user owns the scope.
2. But flag it, loudly and permanently: "⚠️ SCOPE LIMITATION: Section [X] excluded at user request. This diff does not reflect the full policy. Gaps in the excluded area are NOT identified." Above the header, carried to every downstream artifact.
3. Hand the flag to `gap-surfacer`: "This diff was scope-limited. Do not represent it as a complete compliance picture." Include the scope-limitation banner verbatim on any gap tracker entry derived from this diff.
4. Note what the exclusion means: "Excluding vendor management means the diff will show 'no policy addresses vendor management' — which is worse than showing the gap."

A compliance artifact built on an undisclosed scope exclusion looks like concealment in discovery. The flag is the difference between "we scoped the review" and "we hid the problem."

## Workflow

### Step 0: Verify rule status before you diff

Before diffing a rule against policy, confirm the rule is actually in force. Red flags that the rule may not be in force:

- The applicability/compliance date has passed by more than 30 days but you have no confirmation it wasn't delayed
- The rule is more than 12 months old
- The rule is a politically contentious final rule (major rulemakings are frequently challenged)

When you see a red flag, check (via research MCP, web search if enabled, or the Federal Register docket) for: delays, stays, injunctions, rescission proposals, vacatur, or amendments. If you can check and the rule is confirmed in force, proceed. If you cannot verify (no tools connected), emit this banner ABOVE the header, before any content:

> `⚠️ RULE STATUS UNVERIFIED — I could not confirm this rule is currently in force. Final rules are frequently stayed, enjoined, delayed, or rescinded after publication. Do not treat any compliance date below as binding until you confirm the rule's status at the Federal Register docket or with outside counsel.`

Tag every due date in the output: `[due date per published rule — status unverified]`.

Rule-status uncertainty travels downstream. When handing off a gap to `gap-surfacer`, mark the item `status_verified: false` so it never gets routed to an Overdue bucket on the strength of a published date alone.

### Step 1: Extract the new requirements

**No silent supplement.** If the regulatory change text is partial or ambiguous and the fuller rule isn't available from the indexed source, stop and ask. Do NOT fill the gap from web search or model knowledge without asking. Say: "I have [what you have]. To extract requirements accurately I'd need [what's missing]. Options: (1) paste the full text, (2) point me at the primary source, (3) search the web for the rule — results will be tagged `[web search — verify]` and should be checked against the issuing authority before relying, or (4) stop here. Which would you like?" A lawyer decides whether to accept lower-confidence sources; Claude does not decide for them.

**Source attribution.** Tag every citation — the regulatory citation, any cross-references, any policy excerpts — with where it came from: `[<regulator or research tool>]` for items retrieved from a primary source, policy library, or MCP; `[web search — verify]` for items pulled from web search; `[model knowledge — verify]` for items recalled from the model's training data; `[user provided]` for items pasted in by the user. Items tagged `verify` carry higher fabrication risk and should be checked first. Never strip or collapse the tags in the output.

Read the regulatory change. List each discrete new or changed requirement:

| # | Requirement | Effective | Citation |
|---|---|---|---|
| 1 | [what it requires] | [date] | [section] |

Be specific. "Enhanced disclosure requirements" is not a requirement. "Must disclose X in Y format at Z point in the flow" is.

### Step 2: Map to policies

For each requirement, which indexed policy is closest?

- Direct hit: policy explicitly covers this topic
- Indirect: policy covers a related topic, this is a new sub-issue
- No match: no policy addresses this — gap is "policy doesn't exist"

### Step 3: Diff

For each direct or indirect hit, read the policy and compare:

```markdown
### Requirement [N]: [name]

**New rule requires:** [requirement]

**Our policy ([name], last updated [date]) says:**
> "[relevant excerpt]"

**Gap:** [None — policy already covers this | Partial — policy addresses X but not Y | Full — policy contradicts or doesn't address]

**Change needed:** [specific — "add a paragraph on X" not "update the policy"]

**Policy owner:** [from index]
```

### Step 4: No-match gaps

Requirements with no policy match get called out separately:

```markdown
### New policy needed

Requirement [N]: [requirement]

No existing policy covers this. Options:
- Draft new policy (suggested owner: [whoever owns the closest topic])
- Add to existing [related policy] as a new section
- Determine this doesn't need a policy (one-off compliance, not ongoing)
```

## Branches by regulatory input type

### Pre-rule branch (ANPR / RFI)

If the regulatory input is an ANPR or RFI (no imposed requirements), do NOT run a full gap-closure diff. Instead, produce a **pre-positioning analysis**:

- Name the policies that will likely need to change once a final rule issues (not today).
- Flag whether any of the ANPR's issue areas intersect with the company's practice in a way that warrants a comment letter.
- Note the comment deadline and the team's comment-decision owner from `~/.claude/plugins/config/claude-for-legal/regulatory-legal/CLAUDE.md`.
- Do NOT produce per-requirement "no gap" rows for an ANPR — there are no requirements to diff against. Produce one paragraph naming the future exposure and the policies it would touch.

### Negative-finding branch (final rule / NPRM diffed against a policy that isn't the right target)

If every requirement in the extracted list comes out as "no gap against [the named policy]," do NOT produce the full per-requirement analysis — compress to a single short paragraph:

```markdown
## Policy Diff: [Regulation name] — [Policy name]

[REGULATION] doesn't appear to require a change to [POLICY NAME]. [POLICY NAME]
§[X] already covers [Y]. The policies this regulation actually touches are
[other-policy-1] and [other-policy-2] — rerun `/regulatory-legal:policy-diff` against those.

Review on [next cycle — e.g., "at the next annual policy review"] or if
[trigger — e.g., "the rule is finalized or amended"].
```

One paragraph, one recommendation, routing note. Don't repeat the "no gap" finding for every requirement — the summary table handles that. A negative finding against the wrong target policy is a routing problem, not a compliance analysis.

### Gap branch (final rule / NPRM with at least one gap against the target policy)

Full per-requirement analysis as specified below. The detailed diff format is for diffs that actually find gaps.

## Output

```markdown
[WORK-PRODUCT HEADER — per plugin config ## Outputs — differs by role; see `## Who's using this`]

## Policy Diff: [Regulation name]

**Regulation:** [name, link]
**Effective:** [date]
**Requirements extracted:** [N]

### Bottom line

[N gaps need action by [date] — top 3: X, Y, Z]

### Summary

| # | Requirement | Policy affected | Gap | Owner |
|---|---|---|---|---|
| 1 | [short] | [policy name or "none"] | None/Partial/Full | [name] |

### Detailed diffs

[Each requirement block from Step 3]

### New policies needed

[From Step 4, if any]

### No-gap requirements

[List — useful to know what's already covered]

---

**Verify citations before relying on them.** The regulatory citations and policy references above were AI-generated and have not been checked against a primary source. Before acting on any requirement here, confirm the rule against Westlaw, your firm's research platform, or the issuing authority's website — check accuracy, effective date, and current status. AI-generated regulatory citations are sometimes fabricated, misquoted, or stale. Source tags on each requirement (e.g., `[Federal Register]`, `[web search — verify]`) show where the citation came from; `verify` tags carry higher fabrication risk and should be checked first.
```

## Config-dependent fallbacks

This skill reads the policy library index from `~/.claude/plugins/config/claude-for-legal/regulatory-legal/CLAUDE.md`. When the index is empty or still `[PLACEHOLDER]`:

- **Policy library empty:** flag every requirement as "no policy match" by default and append to the output: "The policy library in your configuration is empty, so every requirement is flagged as a new-policy gap. If you have policies that address these requirements, add them to the library with `/regulatory-legal:cold-start-interview --redo` or by editing `~/.claude/plugins/config/claude-for-legal/regulatory-legal/CLAUDE.md`, then re-run the diff."
- **Owner missing for a matched policy:** leave the Owner cell blank in the summary and append: "Policy owners aren't set for [list]. Assign them with `/regulatory-legal:cold-start-interview --redo` or by editing the policy library in `~/.claude/plugins/config/claude-for-legal/regulatory-legal/CLAUDE.md` so gap-surfacer can route."

Say nothing about config when the library is populated and owners are set.

## Handoff

To gap-surfacer: every Partial or Full gap becomes a tracked item with owner and deadline.

## Close with the next-steps decision tree

End with the next-steps decision tree per CLAUDE.md `## Outputs`. Customize the options to what this skill just produced — the five default branches (draft the X, escalate, get more facts, watch and wait, something else) are a starting point, not a lock-in. The tree is the output; the lawyer picks.

## What this skill does not do

- Draft the policy updates. It identifies what needs updating; policy-drafting (or a human) drafts.
- Interpret ambiguous regulatory text definitively. If the reg could be read two ways, say so and flag for counsel.
