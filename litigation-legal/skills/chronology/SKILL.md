---
name: chronology
description: Build or update a chronology from declared document sources and uploads — dated events extracted, de-duped, and tagged by significance per the matter theory. Use when the user asks to build a chronology or timeline from a production or matter file, says "chron from the production" or "what happened when", or needs a working, statement-of-facts, or witness-specific timeline.
argument-hint: "[slug] [--format=working|sof|witness-[name]]"
---

# /chronology

1. Load `~/.claude/plugins/config/claude-for-legal/litigation-legal/matters/[slug]/matter.md` → theory, pivot fact, key facts.
2. Load `~/.claude/plugins/config/claude-for-legal/litigation-legal/CLAUDE.md` → Document storage sources, default matter folder pattern.
3. Follow the workflow and reference below.
4. Identify sources in order: user-provided paths this session, default matter folder, declared sources from `~/.claude/plugins/config/claude-for-legal/litigation-legal/CLAUDE.md`.
5. For readable sources: extract dated events. For unreachable sources: note in Gaps.
6. De-dupe, merge with sources list per event.
7. Tag significance (🔴/🟡/⚪) per matter theory.
8. Write `~/.claude/plugins/config/claude-for-legal/litigation-legal/matters/[slug]/chronology.md` (or format variant per flag).
9. If prior version exists: version number increments, diff summary presented to user.
10. Confirm before finalizing: "Here's what I built. Scan the 🔴 entries — anything I miscalled?"

---

# Chronology

## Disclosed-document use restrictions

Before working with a set of litigation documents, ask: "Were any of these documents obtained through disclosure or discovery in legal proceedings?" If yes:

- **England & Wales (CPR 31.22):** Documents obtained through disclosure are subject to the implied undertaking — you may only use them for the purpose of the proceedings in which they were disclosed, unless the court grants permission, the disclosing party consents, or the document has been read in open court. Using them for a different matter, a different claim, or a commercial purpose without permission is a contempt.
- **US:** Protective orders and Rule 26(c) may impose similar restrictions. Check the order.
- **Other jurisdictions:** Similar restrictions commonly apply. Check the local rule.

Confirm: "This use is within the proceedings in which the documents were disclosed, or I have permission / consent, or the documents are now public." If not confirmed, flag it: "⚠️ Disclosed documents may have use restrictions. Confirm this use is permitted before proceeding."

## Purpose

Facts happen in order. The chronology is the spine every narrative hangs on — the statement of facts in a brief, reserve memos, settlement memos, depo prep, witness prep. Building a chron by hand is slow; AI is good at structured extraction. The catch: garbage-in, garbage-out. This skill pulls from the sources the configuration declares and from whatever the user uploads.

## Modes

This skill serves two practice settings. Pick a default from the user's `## Role` in the plugin's configuration CLAUDE.md; the user can override per-run with a flag.

- **`--matter` mode (default for in-house litigation counsel).** Matter-history-focused. Reads the matter's case theory and key facts from `matter.md`, pulls from declared document-storage sources (Google Drive, SharePoint, Gmail, iManage, CLM — whatever the `## Landscape` section of CLAUDE.md declares), and treats `history.md` as the running internal log (decisions, holds, reserve memos — intentionally not in the chronology). Output is matter-centric: what happened across the dispute, tagged for advocacy use.
- **`--documents` mode (default for firm associate / paralegal).** Production-document-focused. Reads the case theory from the configuration, then extracts from an eDiscovery export, a custodial file set, or a Bates-numbered production. Output is production-centric: what the documents show, with Bates citations, tagged per the case theory.

Both modes converge on the same output structure (timeline, 🔴/🟡/⚪ significance tags, gaps, SoF variant). The difference is the source profile and the significance frame.

If `## Role` is `solo` or `other`, default to `--matter` but mention both modes on the first run and let the user pick.

## Side framing (significance tags)

The same event is significant in different ways depending on whether the practitioner is proving a claim or disproving it. Read `## Side` in the practice profile (and the per-matter posture if the matter overrides the default):

- **Plaintiff (offensive framing)** — 🔴 marks events that *establish* elements of the claim (liability, causation, damages, notice), *close* gaps the defense will try to open, or *start* statute-of-limitations clocks in the plaintiff's favor. 🟡 marks events that support the claim but are subject to impeachment. ⚪ is background context.
- **Defense (defensive framing)** — 🔴 marks events that *break* elements of the claim (failure of causation, notice, reliance), *open* statute-of-limitations or jurisdictional defenses, or *support* affirmative defenses (release, waiver, assumption of risk, comparative fault). 🟡 marks events that undermine the plaintiff's narrative. ⚪ is background.
- **Both / varies** — ask the user per-chronology which side's framing to apply for significance tags. The underlying timeline is side-neutral; only the significance read changes.

Note the applied framing at the top of the output: `Significance tags applied from [plaintiff / defense] perspective.` When producing a Statement of Facts variant, use the side default unless the user specifies otherwise.

## Load context

Common:
- Plugin configuration CLAUDE.md → case theory context (in-house: `## Landscape` for document sources; firm associate: `## Case theory` and `## Document review` for platform + custodians), `## Outputs` for the work-product header, `## Decision posture` for the privilege-flagging rule.
- Prior `chronology.md` for this matter, if it exists.
- Any files the user uploads or paths they provide in-session.

`--matter` mode also reads:
- `~/.claude/plugins/config/claude-for-legal/litigation-legal/matters/[slug]/matter.md` → case theory, key facts, pivot fact (for significance tagging), key dates.
- Default matter folder pattern from CLAUDE.md → where docs for this slug live.

`--documents` mode also reads:
- eDiscovery platform metadata if a connector is available (Everlaw, Relativity, DISCO, Aurora) — by custodian + date range.
- Bates-range manifest or production index if the user points at one.

**Conflicts gate — unbypassable (`--matter` mode).** Before building the chronology, check `~/.claude/plugins/config/claude-for-legal/litigation-legal/matters/_log.yaml` for the matter slug. If the matter is not in `_log.yaml`, refuse and route:

> "I don't see [matter slug] in the matter log. Run `/litigation-legal:matter-intake` first so the conflicts check runs and the matter workspace is set up. I won't build a chronology on a matter that hasn't been intaken — the conflicts check is the gate."

Do not proceed on an unintaken matter. Intake is what runs conflicts and writes the `_log.yaml` row this skill reads from. `--documents` mode (running against an ad-hoc document set without a matter slug) is exempt from the gate, but its outputs should be treated as pre-matter research and not filed as if matter work product.

## Workflow

### Step 0: Privilege gate (runs first, every time)

Chronology work pulls from documents. Documents are often privileged (attorney-client, work product, common interest, joint defense) — in-house matter files often are by default; eDiscovery productions, especially rolling productions or common-interest productions, often contain privileged or unreviewed material. Extracting content from a privileged document into a chronology that later gets shared can *risk* waiver, depending on who receives it and under what doctrine (common-interest, joint-defense, Kovel, and work-product protections may apply). Waiver analysis is fact-specific — get counsel sign-off before distributing.

The skill will not extract until the user picks a privilege posture:

> Before I extract: how have the sources been privilege-screened?
>
> - **A. All sources cleared** — you've already screened these. I extract without privilege flags. Output is discovery-ready posture; still marked work product.
>
> - **B. Mixed or not yet screened** — I extract and tag every entry with a `priv` flag: `ok` (sourced from clearly non-privileged material), `flag` (sourced from potentially privileged material — A/C, WP, common interest), or `review` (source unclear). Flagged entries are visually marked in the output, and the Statement-of-Facts variant filters them out by default.
>
> - **C. Abort — screen first** — pause the skill. Screen the sources. Return and re-run.

Record the choice in the chronology header as `privilege_posture: A-cleared | B-mixed | C-aborted`. If B or C, record the rationale briefly.

**Why a gate and not just a warning:** a warning gets read once and forgotten. A gate forces the posture decision into the record, which means every chronology file carries its own provenance — anyone reading it later knows whether entries were derived from privilege-screened material.

### Step 1: Identify document sources

**`--matter` mode:**

1. **User-provided paths** — anything dropped in this session (file paths, drive links, email exports).
2. **Default matter folder** — from CLAUDE.md's document-storage pattern, expanded for this slug (e.g., `G:/Legal/Matters/acme-v-us-2026`).
3. **Declared sources** — the `Document storage` table in CLAUDE.md, filtered to ones this matter might touch (e.g., Gmail archive for sender-side communications, SharePoint legal folder).
4. **Ask** — if sources look thin, prompt: "I can build from what I have, but the chronology will be incomplete. Anything else to point me at? Key emails, contracts, internal memos, production letters?"

**`--documents` mode:**

1. **Production export / Bates set** — the user points at the production directory or a manifest; the skill reads by Bates range + date.
2. **eDiscovery connector** — if an MCP connector is available (Everlaw, Relativity, DISCO, Aurora), pull by custodian + date range.
3. **Custodial files** — if the user provides raw custodial mailboxes or drive exports, read those too.
4. **Ask** — if coverage looks thin for a key custodian or date range, prompt.

### Step 2: Pull + read

For each source with readable files:

- **PDFs, emails (.eml), .docx, .txt** — read directly.
- **Email archives (Gmail, Outlook)** — if an MCP connector is authenticated, query by date range + counterparty / key terms; otherwise the user exports relevant threads to a folder.
- **eDiscovery platforms (Everlaw, Relativity, DISCO, Aurora)** — if connector is available, pull by custodian + date range; otherwise the user provides an export.

If the skill can't access a declared source, name it explicitly in the output's Gaps section rather than silently proceeding.

**No silent supplement.** If source coverage for an era of the matter is thin — fewer documents than expected for a claimed time window, a custodian whose mailbox isn't accessible, a production that hasn't landed — report what was found and stop. Do NOT fill gaps from web search, public record search, or model knowledge about the matter without asking. Say: "Sources returned [N] events for [period / custodian]. Coverage appears thin. Options: (1) point me at additional sources (Bates, folder, mailbox), (2) try a different MCP connector if configured, (3) search the web for public-record events in this window — results will be tagged `[web search — verify]` and should be checked against a primary source before relying, or (4) stop here and note the gap. Which would you like?" A lawyer decides whether to accept lower-confidence sources; the skill does not decide for them.

**Source attribution.** Tag every chronology entry with where the event came from: the file path, Bates number, MCP connector, or declared document-storage source for events extracted from retrieved documents (already captured in the Sources column). For any event or date that cannot be traced to a retrieved document — e.g., a fact recalled from model training data, a public-record event found via web search — tag it inline: `[web search — verify]`, `[model knowledge — verify]`, or `[user provided]` where the user stated the fact in-session. Entries tagged `verify` carry higher fabrication risk than document-sourced entries and should be checked first. Never strip or collapse the tags — they are counsel's fastest signal about which entries to verify before pulling them into a brief or SoF.

**Tagging reaches every section that states a legal conclusion, deadline, or computed date — not just timeline entries.** The timeline is sourced from documents. The Gaps section, the Key events section, the Theory tie lines, and any statement of limitations, tolling event, filing deadline, discovery cutoff, or privilege determination are legal analysis the skill writes from model knowledge unless sourced. Every such statement carries a provenance tag: `[computed from: <rule cited with tag>]`, `[model knowledge — verify]`, `[user provided]`, or a research-connector tag if retrieved in this session. A statute-of-limitations window with no tag defaults to `[model knowledge — verify]`. A "key event" line that characterizes a fact's legal significance is analysis and needs the tag. The rule is simple: if it's an assertion about the law, not an assertion about what a document says, it must carry the same provenance tag the timeline entries do. When no research connector is reachable and the skill is computing deadlines or citing rules, record it in the **Sources:** line of the reviewer note (see plugin CLAUDE.md `## Outputs`) — do not emit a standalone banner.

### Step 3: Extract events

For each document, identify dated events:

- **Email:** `[date] [sender] told [recipient] [subject/content]`
- **Meeting:** `[date] [attendees] met about [topic]` (per calendar entry or notes)
- **Decision:** `[date] [decision-maker] decided [what]` (per memorializing doc)
- **Filing / pleading:** `[date] [party] filed [motion/complaint/response]`
- **External event:** `[date] [thing happened]` (contract signed, product launched, regulator acted, event crossed a threshold)

One event per document usually. Occasionally zero (undated or no event established). Sometimes multiple (meeting summary covering several decisions).

**Privilege flag per entry (only when privilege_posture == B-mixed). Three-state rule — never silently decide a subjective privilege test isn't met:**

- `priv: ok` — source is **confidently** non-privileged (filings, regulatory correspondence, public docs, counterparty communications without our counsel). Used only when there's no plausible privilege theory.
- `priv: flag` — source is confidently or likely privileged (communications with counsel, work-product memos, privileged drafts, joint-defense material). **Default for anything uncertain** — if the dominant-purpose call is close, or litigation contemplation is borderline, or the content is mixed, it goes here, not in `ok`.
- `priv: review` — source unclear on its face, but the skill could not make the call at all (no sender/recipient metadata, unreadable, etc.).

When `priv: flag` or `priv: review`, add `[SME VERIFY: privilege status]` inline so the counsel sees it during review. Under-flagging waives privilege (one-way door); over-flagging is corrected by counsel in review (two-way door). Prefer the recoverable error.

### Step 4: De-dupe

The same event surfaces in multiple documents: a meeting is on three calendars and produces a summary email — that's **one event with four sources**, not four events. Merge. The merged entry cites all sources.

### Step 5: Tag significance — per case theory

Read the pivot fact and key facts from `matter.md` (`--matter` mode) or from the configuration's `## Case theory` section (`--documents` mode). Tag each event:

- 🔴 **Key** — event is part of the pivot fact or a key fact for/against us
- 🟡 **Relevant** — context, pattern evidence, supports a secondary argument
- ⚪ **Background** — useful for completeness, not going in the brief

**Discipline:** a chronology of 300 entries with 300 🔴 tags has no tags. Reserve 🔴 for events that would genuinely move a factfinder. If in doubt, 🟡.

**Borderline tagging:** when an entry sits between 🔴 and 🟡 (or 🟡 and ⚪), tag at the lower significance and add `[SME VERIFY — borderline significance call]` inline. Counsel's judgment will override the skill's call. A chronology that confidently over-tags is less useful than one that surfaces its uncertainty.

### Step 6: Write

Default output is the working chronology. Variants on request.

## Output formats

### Working chronology (default)

Location: `~/.claude/plugins/config/claude-for-legal/litigation-legal/matters/[slug]/chronology.md`. Complete, tagged, annotated. The reference doc counsel works from.

```markdown
[WORK-PRODUCT HEADER — per plugin config ## Outputs — differs by role; see `## Who's using this`]

> **Privilege inheritance.** This chronology is derived from matter documents that may be attorney-client-privileged, work-product-protected, common-interest / joint-defense material, or a mix. It inherits the sources' protection status. Distributing it beyond the privilege circle — to business stakeholders outside the engagement, to opposing counsel, to a regulator — can waive protection over both the chronology and the underlying sources. Store with privileged matter material, mark consistently with house privilege conventions, and make distribution decisions deliberately. The privilege-posture choice captured below is the provenance stamp for any later distribution call.

# Chronology — [Matter Name]

> Significance tags (🔴/🟡/⚪) and privilege flags (🔒) are first-pass reads requiring `[SME VERIFY]` before use in any external work product (briefs, SoF, board memo, outside counsel deliverable).

**Matter:** [slug]
**Mode:** matter | documents
**Built:** [YYYY-MM-DD]
**Sources:** [N] documents across [source types]
**Entries:** [N] ([N] 🔴 / [N] 🟡 / [N] ⚪)
**Pivot fact:** [one sentence]
**Privilege posture:** A-cleared | B-mixed | C-aborted
**Flagged entries:** [N] 🔒 *(only present when posture == B-mixed)*

---

## Timeline

| Date | Event | Tag | 🔒 | Sources |
|---|---|---|---|---|
| [YYYY-MM-DD] | [what happened, one sentence] | 🔴/🟡/⚪ | [blank / 🔒-flag / 🔒-review] | [file paths or Bates] |

---

## Key events (🔴 only)

[Pulled out, each with a line on why it matters to the theory.]

### [date] — [event title]
- What: [one line]
- Theory tie: [why this matters]
- Sources: [list]

---

## Gaps

**Date ranges with no events:**
[ranges — where are documents for this period?]

**Expected but missing:**
[events we'd expect to see documented but don't — e.g., "contract amendments between 2024-06 and 2025-03 — not produced"]

**Unreadable sources:**
[sources declared in CLAUDE.md but not accessible this run — e.g., "Everlaw production — no MCP connector; export needed"]

---

## Marker discipline

- `[VERIFY: factual assertion — date, attendees, content]` — not yet confirmed against the underlying doc
- `[UNCERTAIN: legal characterization — e.g., whether an event establishes a regulatory trigger]`
- `[CITE NEEDED: Bates / exhibit / depo page:line]`
- `[SME VERIFY: privilege status | borderline significance call]` — counsel judgment needed

---

## Version
- v[N] built on [date] from [source summary]
- v[N-1] built on [date] (prior, superseded)
```

### Statement-of-facts chronology (on request)

Filter to 🔴 and relevant 🟡 only. Present as prose in chronological narrative order — the skeleton for a brief's fact section. Each paragraph is one event or tightly linked cluster, with record citations.

**Privilege filter default:** when `privilege_posture == B-mixed`, 🔒-flagged and 🔒-review entries are **excluded** by default. The SoF variant is intended for eventual external use (briefs, disclosures, negotiating counterparty) — 🔒 entries don't belong there until counsel confirms privilege status. If the user wants 🔒 entries included anyway, require explicit `--include-flagged` acknowledgment; capture the acknowledgment in the output header as permanent record.

### Witness-specific chronology (on request)

Filter to events where a named witness is sender, recipient, attendee, or subject. Feeds witness prep and helps reconstruct what a witness knew when.

## Incremental builds

If `chronology.md` exists:

- Read prior version
- Build new chronology from current sources
- Diff: new events (since last build), modified entries (new sources added to existing events), removed entries (rare; note why)
- Preserve the prior version number; write new version with `v[N+1]`
- Output summary of what changed

## Integration with matter.md / history.md

**Intentionally separate** (in-house `--matter` mode). `history.md` is counsel's running log — decisions, updates, procedural milestones, internal strategy notes. `chronology.md` is the advocacy-facing timeline of facts. They overlap but don't merge:

- A hold was issued → goes in history.md (internal action). Usually not in chronology (not a fact of the dispute).
- The counterparty sent a breach notice on March 14 → goes in chronology.md (🟡 — establishes their knowledge). Also in history.md if the intake referenced it.
- Our reserve recommendation memo was drafted → history.md only.

When counsel wants history events in the chronology, they can paste them. The default is they stay separate.

## What this skill does not do

- **Resolve contradictions.** When two documents say different things about when an event happened, both entries go in with a flag. Resolution is counsel's call; may require witness interview or further discovery.
- **Invent events not in the sources.** If it's not in the documents (and not in matter.md or the configuration as a captured fact), it's not in the chronology — but "Gaps" might call it out as missing.
- **Guarantee completeness.** A chronology is only as good as the sources. If the eDiscovery production is ongoing and only 20% has landed, the chronology reflects that. Name the limitation.
- **Decide privilege status for the user.** The Step 0 gate forces the posture choice; the per-entry `priv` flag captures first-pass classification. Actual privilege determinations are counsel's call per `[SME VERIFY]` flags.
