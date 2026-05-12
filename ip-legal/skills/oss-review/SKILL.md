---
name: oss-review
description: >
  Open source license compliance check for a dependency list, a single
  library, or outbound code. Use when reviewing a manifest, SBOM, or repo for
  copyleft obligations and license compatibility, when asked whether a library
  can ship, or when preparing code to be open-sourced.
argument-hint: "[file path to manifest / SBOM | package name | repo path | paste text]"
---

# /oss-review

Runs an open source license compliance check against the practice profile in `~/.claude/plugins/config/claude-for-legal/ip-legal/CLAUDE.md`. Classifies dependencies by license family, maps obligations to the deployment model, flags license-unknown and non-OSI-posing-as-OSS packages, and recommends actions — comply, replace, remove, seek legal review, seek commercial license.

## Instructions

1. **Load `~/.claude/plugins/config/claude-for-legal/ip-legal/CLAUDE.md`.** If placeholders present, stop and prompt: "Run `/ip-legal:cold-start-interview` first — I need to learn your practice profile (and OSS policy, if any) before I can review." If the practice profile points at an uploaded OSS policy, read that too — it is the source of truth for accepted / review / banned licenses on this team.

2. **Establish the scope:** a dependency list (package.json, requirements.txt, go.mod, Gemfile, Cargo.toml, pom.xml, SBOM), a single library, or outbound code the team is preparing to open-source. If the user passed a path, infer from the file; otherwise ask.

3. **Establish the deployment model** before classifying obligations — SaaS, distributed binary, internal only, or embedded. The same dependency list triggers different obligations depending on this.

4. **Follow the workflow below.** In particular:
   - Read the actual license text, not just metadata — LICENSE files can be wrong, package metadata can be stale.
   - Classify each package into permissive / weak copyleft / strong copyleft / public domain / non-OSI / unknown.
   - Flag license-unknown as "needs review," not permissive by default.
   - Flag non-OSI source-available licenses (SSPL, BUSL, Commons Clause, Elastic License, fair-source) — these are not open source.
   - For outbound code, check that the chosen outbound license is compatible with every embedded dependency.

5. **Output the memo** per the template below — work-product header first, bottom line, top-of-memo flags, per-package blocks grouped by severity, jurisdiction note, outbound check (if applicable), approval routing.

6. **Respect the decision posture.** When a copyleft-trigger analysis turns on a contested question (AGPL's "interacts over a network," GPL-3.0's "conveying," LGPL linking scope), flag for attorney review and surface the factors cutting both ways. Anything flagged as strong copyleft or license-unknown goes to an attorney before the dependency ships or the code is released.

## Examples

```
/ip-legal:oss-review ~/code/my-project/package.json
/ip-legal:oss-review ~/code/my-project/requirements.txt
/ip-legal:oss-review redis
/ip-legal:oss-review ~/code/my-project  # repo root — scan all manifests
```

---

## Works better connected

OSS clearance requests usually come in via a ticketing system. Connected to
Jira, Linear, or Asana, this skill can: monitor incoming OSS requests, respond
with guidance directly in the ticket (flagging incomplete info, asking for the
repo link, returning the license-family classification), and track clearance
status across requests.

Without a connector, paste the ticket or describe the request and I'll handle
it one at a time. See `CONNECTORS.md` at the repo root for how to add a
ticketing connector.

## Matter context

**Matter context.** Check `## Matter workspaces` in the practice-level CLAUDE.md. If `Enabled` is `✗` (the default for in-house users), skip the rest of this paragraph — skills use practice-level context and the matter machinery is invisible. If enabled and there is no active matter, ask: "Which matter is this for? Run `/ip-legal:matter-workspace switch <slug>` or say `practice-level`." Load the active matter's `matter.md` for matter-specific context and overrides. Write outputs to the matter folder at `~/.claude/plugins/config/claude-for-legal/ip-legal/matters/<matter-slug>/`. Never read another matter's files unless `Cross-matter context` is `on`.

---

## Purpose

Tell the user what licenses are in their dependency tree, what obligations those licenses trigger given how the code will be deployed, and what to do about each one. The output is a memo the lawyer (or the engineer with attorney access) can act on — comply, replace, remove, seek legal review, seek commercial license.

**This is a first-pass classification.** Copyleft analysis depends on the deployment model, the degree of linking, the jurisdiction, and sometimes on legal questions that have not been tested in court (notably AGPL's "interacts over a network," GPL-3.0's patent clause). For anything that classifies as strong copyleft or license-unknown, an attorney evaluates before the dependency ships or the code is released. The skill reports what it found; the lawyer decides what to do.

## Precondition: load the practice profile

**Before scanning dependencies, read `~/.claude/plugins/config/claude-for-legal/ip-legal/CLAUDE.md`.** If it is missing or still contains placeholders, stop and run `/ip-legal:cold-start-interview`. The practice profile tells you:

- Who owns OSS review on this team (often engineering with legal sign-off)
- Escalation routing for copyleft obligations
- The work-product header to prepend

If the practice profile has an OSS policy uploaded, read that too — it is the source of truth for which licenses the team accepts, which trigger review, and which are banned.

## Workflow

### Step 1: What's the scope?

Ask (or infer from what the user provided):

> What are we reviewing?
>
> 1. **A dependency list** — `package.json`, `requirements.txt`, `go.mod`, `Gemfile`, `Cargo.toml`, `pom.xml`, an SBOM (SPDX / CycloneDX), a lockfile
> 2. **A single library** — one specific package you're considering adding
> 3. **Our own code** — we're planning to open-source this and need to check what's embedded

The analysis path differs:

- Dependency list → classify every entry, roll up obligations
- Single library → classify one package and walk its transitive dependencies if available
- Outbound code → check what's embedded (direct and transitive), check whether chosen outbound license is compatible with all embedded licenses, check that LICENSE / NOTICE files are correct

### Step 2: What's the deployment model?

This is the single most important input after the license list — the same library carries different obligations depending on how the software is delivered. Ask:

> How will this be deployed?
>
> 1. **SaaS / hosted service** — users access over a network; nothing ships to the user
> 2. **Distributed binary** — we ship compiled code to users (desktop app, mobile app, on-prem server, CLI tool)
> 3. **Internal only** — used only inside the company, not distributed outside
> 4. **Embedded / firmware** — shipped in hardware or as closed-system firmware

| Deployment | Licenses that materially matter |
|---|---|
| SaaS | AGPL (network-trigger), permissive attribution in any UI, SSPL/BUSL/Elastic if repurposing as competing service |
| Distributed binary | GPL, LGPL, MPL, EPL (all trigger on distribution), permissive attribution |
| Internal only | Most copyleft does not trigger — no distribution. Permissive attribution still good hygiene. AGPL still triggers if users outside the company interact over the network. |
| Embedded / firmware | GPL is especially hard to comply with here (source disclosure + reproducible build + installation information in some cases). Plan for this before shipping, not after. |

Flag the deployment model in the output memo — the same dependency list reviewed against "SaaS" vs. "distributed binary" yields different obligations.

### Step 3: Classify each dependency

For every package, determine the license. Read the actual license text, not just the metadata — LICENSE files can be wrong (the file says MIT but the headers say GPL; the README claims Apache but there's no license file), and package manager metadata can be stale.

Classify into:

| Bucket | Examples | Key obligations |
|---|---|---|
| **Permissive** | MIT, BSD-2-Clause, BSD-3-Clause, Apache-2.0, ISC, Zlib, Unlicense | Attribution, preserve license text, Apache-2.0 adds patent grant + NOTICE requirement |
| **Weak copyleft** | LGPL-2.1, LGPL-3.0, MPL-2.0, EPL-1.0, EPL-2.0, CDDL | File-level or library-level source disclosure; linking rules vary |
| **Strong copyleft** | GPL-2.0, GPL-3.0, AGPL-3.0, OSL, EUPL (depending on version) | Broad source disclosure; AGPL extends to network use |
| **Public domain / dedication** | CC0, Unlicense, WTFPL | Typically no obligations, but some are contested in jurisdictions that don't recognize dedication to public domain |
| **Non-OSI source-available** | SSPL, BUSL, Commons Clause, Elastic License, Confluent Community, fair-source family | Not open source — restrict commercial use, competing-service use, or both. Read the specific license. |
| **Other / custom / unknown** | vendor-specific, proprietary, missing license file, license conflict between file and headers | Stop — do not treat as permissive by default |

Flag:

- **Dual-licensed packages** — which license are we using? The choice may change obligations.
- **Deprecated packages** — the package is no longer maintained; is there a supported replacement?
- **Packages with a copyleft dependency in their own tree** — the top-level license is permissive but a transitive dependency is copyleft.
- **Packages that changed license recently** — Redis, MongoDB, Elastic, HashiCorp — make sure the version pinned is under the license you think it is.

### Step 4: Map obligations to the deployment model

For each classified dependency, state what the deployment model triggers:

```markdown
### [package@version] — [License]

**Classification:** [Permissive / Weak copyleft / Strong copyleft / Public domain / Non-OSI / Unknown]

**Obligations for our deployment ([SaaS / binary / internal / embedded]):**

- [ ] [Specific obligation — e.g., "Include attribution in a NOTICES file shipped with the app"]
- [ ] [e.g., "If we modify and distribute, publish source of our modifications"]
- [ ] [e.g., "AGPL network trigger — if users access our modified version over a network, source must be offered to them"]

**Risk:** 🔴 Critical | 🟠 High | 🟡 Medium | 🟢 Low

**Recommendation:** [Comply with obligations | Replace with [alternative] | Remove | Attorney review before shipping | Seek commercial license from [vendor]]
```

> **How is the copyleft dependency consumed?** The linking relationship determines whether copyleft actually triggers. Ask or determine:
> - **Static linking / compilation together:** The works are combined into one binary. Strong signal that copyleft triggers (LGPL "work based on the Library," GPL derivative work).
> - **Dynamic linking / shared library:** The works remain separable at runtime. LGPL explicitly permits this ("work that uses the Library"). GPL's position is contested (FSF says derivative, others disagree).
> - **Header inclusion / inline functions:** Can create a derivative work depending on how much is included.
> - **Subprocess / IPC:** Separate processes communicating over well-defined interfaces. Generally not derivative.
> - **Network API call:** For most licenses, no. For **AGPL**, the network-interaction clause means serving the software over a network IS distribution. In a microservices architecture, an AGPL component behind an API still triggers.
> - **File-scope copyleft (MPL):** Only the modified files carry copyleft, not the whole work. Check whether any copyleft files were modified.
>
> **The severity rating depends on this.** "LGPL — weak copyleft, linking rules vary" without the linking analysis is the answer that gets an engineer sued. Static-linked LGPL in a proprietary product is 🔴 Critical. Dynamic-linked LGPL is 🟢 Low. Same license, opposite rating.

**Severity calibration:**

| Level | Means |
|---|---|
| 🔴 Critical | Strong copyleft in a deployment that triggers it (e.g., GPL in a distributed binary, AGPL in a SaaS). Non-OSI license that the business model actually conflicts with (e.g., SSPL while we're building a managed service). License cannot be determined and the package is load-bearing. |
| 🟠 High | Weak copyleft with obligations the team hasn't set up for (file-level disclosure, NOTICE requirements). Dual-licensed where the chosen license is ambiguous. License file says one thing, headers say another. |
| 🟡 Medium | Permissive with attribution requirements that haven't been wired into the build (missing NOTICES file, missing LICENSE in distribution). Transitive copyleft in a position that may or may not trigger, depending on how the library is consumed. |
| 🟢 Low | Permissive with obligations already satisfied. Copyleft in a deployment model that doesn't trigger it (e.g., GPL library used internally only, with no redistribution). |

### Step 5: Flag failure modes

Call out any of the following in a top-of-memo section:

- **License unknown** — classify as "needs review," not permissive. An unclassified dependency should stop a ship decision, not slip through.
- **License file conflicts with file headers** — read both and report the conflict.
- **Incompatible combinations** — GPL-2.0 only + Apache-2.0 historically a known incompatibility; check MPL / EPL / GPL combinations carefully.
- **Non-OSI licenses posing as open source** — SSPL, BUSL, Commons Clause, Elastic License, Confluent Community. Read the license; don't rely on GitHub's "open source" badge.
- **License changes** — if a prior version was permissive and the current version is source-available, the pin matters.

### Step 6: Outbound check (if reviewing our own code before open-sourcing)

If the user is preparing to open-source code:

- Confirm the chosen outbound license is compatible with every embedded dependency's license (e.g., you cannot release under MIT if you've embedded GPL code — the combined work must be GPL)
- Confirm LICENSE file is present and correct
- Confirm NOTICE file is present and lists required attributions (Apache-2.0 and others)
- Confirm third-party license texts are bundled where required
- Confirm no proprietary or confidential code, no customer data, no embedded credentials in the repo history
- Confirm trademark and brand policy for any project name (separate from the copyright license)

### Step 7: Assemble the memo

Prepend the work-product header from `~/.claude/plugins/config/claude-for-legal/ip-legal/CLAUDE.md` → `## Outputs` (differs by user role — see `## Who's using this`).

This memo and any dependency list reviewed may be privileged, confidential, or both. The output inherits that status from the source. Distribute only within the privilege circle; strip the work-product header before any external delivery (including before attaching the memo to an engineering ticket outside the privilege circle).

> **No silent supplement.** If a research query to the configured legal research tool returns few or no results for a rule the memo needs (enforceability of AGPL's network trigger in a given jurisdiction, scope of GPL-3.0's patent grant, latest license text for a recently-relicensed package), report what was found and stop. Do NOT fill the gap from web search or model knowledge without asking. Say: "The search returned [N] results from [tool]. Coverage appears thin for [rule / license / jurisdiction]. Options: (1) broaden the search query, (2) try a different research tool, (3) search the web — results will be tagged `[web search — verify]` and should be checked against a primary source before relying, or (4) flag as unverified and stop. Which would you like?" A lawyer decides whether to accept lower-confidence sources.
>
> **Source attribution.** Where the memo cites a license text, a court decision interpreting a license, or guidance from a steward (FSF, OSI, SPDX, SFLC), tag the citation: `[OSI]`, `[SPDX]`, `[FSF]`, `[SFC/SFLC]`, `[Westlaw]`, or the MCP tool name for citations retrieved from a connector; `[web search — verify]` for web-search citations; `[model knowledge — verify]` for citations recalled from training data; `[user provided]` for license text read directly from the repo. Citations tagged `verify` carry higher fabrication risk. Never strip or collapse the tags.

```markdown
[WORK-PRODUCT HEADER — per plugin config ## Outputs]

# OSS Review: [Project / Dependency List / Package]

**Reviewed:** [date]
**Scope:** [Dependency list / Single library / Outbound code]
**Deployment model:** [SaaS / Binary / Internal / Embedded]

---

## Bottom line

[Two sentences. Can this ship? What has to happen first?]

**Packages reviewed:** [N]
**By classification:** [N permissive, N weak copyleft, N strong copyleft, N public domain, N non-OSI, N unknown]
**Issues:** [N]🔴 [N]🟠 [N]🟡 [N]🟢

**Approval needed from:** [name, per practice profile]

---

## Top-of-memo flags

[License-unknown list, license-conflict list, non-OSI-posing-as-OSS list, incompatible combinations]

---

## By package

[Blocks from Step 4, grouped by severity]

---

## Jurisdiction note

OSS license enforceability varies — AGPL's network trigger has not been broadly tested in court; GPL-3.0's patent clause reads differently under US vs. EU patent law; dedications to public domain are not universally recognized. State the governing-law choice for any downstream distribution (e.g., vendor agreements incorporating the code) and flag jurisdictions the practice profile marks as escalate.

---

## Outbound check (if applicable)

[From Step 6]

---

## Approval routing

[From practice profile — who approves, what triggers automatic escalation]
```

## Decision posture

When a license cannot be confidently classified, flag it as **"needs review"** — do not call it permissive. Under-classifying license risk is a one-way door: a ship decision made on a permissive-by-default assumption becomes a source-disclosure obligation or an injunction months later. Over-flagging is a two-way door — the attorney narrows the list in review.

Likewise, when the copyleft-trigger analysis turns on a contested question (AGPL's "interacts over a network," GPL-3.0's "conveying," the scope of LGPL linking), flag for attorney review and surface the factors cutting both ways.

## Quality checks before delivering

- [ ] Practice profile and any OSS policy were loaded
- [ ] Deployment model was established before classifying obligations
- [ ] Every dependency has a classification, including transitives where available
- [ ] License-unknown packages are flagged, not defaulted to permissive
- [ ] License text was read (not just metadata) for any copyleft or non-OSI finding
- [ ] Source tags applied to citations; no stripped `verify` tags
- [ ] Approver named per practice profile
- [ ] Output marked with the work-product header

## Close with the next-steps decision tree

End with the next-steps decision tree per CLAUDE.md `## Outputs`. Customize the options to what this skill just produced — the five default branches (draft the X, escalate, get more facts, watch and wait, something else) are a starting point, not a lock-in. The tree is the output; the lawyer picks.

If the scan surfaced more than ~10 packages, or any time the user asks: offer the dashboard (see CLAUDE.md `## Outputs → Dashboard offer for data-heavy outputs`). Shape the offer to what's useful here — counts by license family (permissive / weak copyleft / strong copyleft / AGPL / proprietary / unknown), risk distribution, and a table of findings with severity and package version.

