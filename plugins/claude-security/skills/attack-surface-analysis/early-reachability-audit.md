# Stage 2: Early Reachability Audit

This is stage 2 of the attack-surface-analysis pipeline; the rules in SKILL.md bind here. Map the sensitive and complex code paths that are reachable pre-authentication, 0-click, or before the protocol state transition that should gate them, regardless of the configuration required. Recover the authentication boundary and the protocol state machine from the code, compare implemented against required message ordering, prove every reachability claim with a recorded trace, and produce a ranked audit inventory separating intended early reachability from unintended. Not a bug-hunting stage; individual vulnerabilities found along the way are a byproduct, not the goal. Never reach out to the internet for any reason.

A bug's consequence is set less by the bug than by where it sits. The same defect is critical in a handler an unauthenticated attacker drives with one unsolicited message, and minor in code reachable only by an authenticated peer deep in an established session. This audit maps every sensitive or complex code path reachable before authentication, without victim interaction, or before the protocol state transition that should gate it — and records which of those paths the developer put there deliberately and which are reachable early by accident.

Reachability is computed regardless of configuration: the operator, not the attacker, chooses the configuration, and deployments in the field run all of them — so every configuration-gated branch is treated as takeable, and the options a path requires are recorded as metadata, never used to prune. The output is a ranked audit inventory and its findings, with proven traces — not gates or patches: much of what it maps is code that is used, must stay early-reachable, and can only be audited, not moved; the inventory says where that effort goes first.

## The three boundaries

Classify every path by the boundaries it is reachable before; call such a path early against that boundary:

1. **Authentication**: the code point where the peer's identity is established under the program's own model — the first successful credential check, key verification, or session validation. Pre-authentication code is everything executable on a path from input acceptance to that point, including the authentication code itself. A path is pre-authentication when some execution reaches it before any mechanism has succeeded — the attacker chooses the mechanism, or engages none. A mechanism satisfiable without a secret — anonymous, null, or "none" authentication — does not cross the boundary; code behind only such a mechanism is pre-authentication. Where configuration decides whether the boundary exists at all — authentication optional or off by default — record it as configuration-created and report measurements under both the default and the boundary-maximizing configuration — the one enabling the strongest authentication the program supports.
2. **Interaction**: code that runs on receipt of attacker-controlled input with no action by the victim. For a network daemon every remote path is 0-click; this boundary differentiates client and agent software, where message receipt, auto-decoded media, previews, and background sync run parsers without the victim opening anything.
3. **Protocol state**: the protocol permits a message type only after a transition — version agreed, keys exchanged, channel opened, session bound — but the implementation processes it earlier. The required ordering comes from the protocol's written definition when one exists: label it spec-verified when checked against a copy of the text inside the target (the network rule permits no documentation fetches, and nothing outside the target is read), and spec-recalled when quoted from knowledge with no such copy. Otherwise it is labeled code-reconstructed, from the code's own declared intent (state enums, assertions, comments, the handling of the symmetric peer); where neither exists, the message type is unconstrained. Record which source; recalled and reconstructed requirements are weaker evidence and say so.

All three boundaries yield inventory: sensitive or complex code that sits early, ranked for audit attention. Findings are the subset where early reachability is wrong, defined once here: items classified unintended-early on any boundary (step 6); state-ordering gaps (step 4) — input processed before the transition that is supposed to gate it, an enforcement gap in its own right; and boundary bookkeeping defects met along the way — a mechanism that authenticates without recording the crossing, state shared across connections before identity. That such transitions are often cheap for an attacker to drive makes a gap more reachable, not less of a gap. A defect fitting no named shape is recorded under its own description, never forced into one.

## What counts as sensitive and complex

A path enters the inventory when it is sensitive, complex, or both, and early against any boundary; both criteria are recorded as evidence, not impressions.

A path is **sensitive** when what it does makes a defect there high-consequence: parsing or decoding of attacker-controlled input (protocol messages, certificates, compressed payloads, file formats); cryptographic operations on attacker-supplied material; memory allocation or indexing driven by attacker-controlled lengths and counts; credential handling and the authentication decision itself; session or connection state mutation that persists across messages; privilege operations, process creation, or filesystem access influenced by the input; execution inside the most privileged process rather than a sandboxed or privilege-separated child. Record which of these properties each path has, with the code that shows it.

A path is **complex** by measures, not adjectives: lines of code reachable on the path; cyclomatic complexity of its functions; count of message or record types accepted at the dispatch point; nesting depth and count of length or count fields in the formats parsed; allocation, free, and pointer arithmetic sites on the path in memory-unsafe languages; state variables written before the boundary. Record the numbers per item.

## Procedure

### 1. Record the pin and fix the reachability rule

- Record the pin that your starting instructions give; every reachability claim is relative to it.
- Consume the stage-1 handoff when one exists: compare its pin with yours before using anything else in it. Its entry points are leads, not inventory: stage 1 inventoried what the default configuration exposes, and this stage's rule is configuration-independent — re-verify every inherited entry point against the code and extend to the ones that exist only under some configuration.
- Fix the rule for the whole audit: a configuration-gated branch is takeable. Record per path the options that must be set to reach it; a default is never grounds to prune. The recorded option set must be simultaneously acceptable to the program: a path whose required options the program rejects in combination is unproven, not inventory. Include compile-time optional code when any shipped or supported build enables it, recording the build variant the same way.
- Inventory the entry points: network listeners and their message handlers, IPC endpoints, inputs processed automatically on arrival, and for client or agent software the paths that run on receipt without victim action — including entry points that exist only under some configuration, such as a listener an option starts.

### 2. Recover the boundaries from the code

- Locate the authentication decisions: the exact code locations where an unauthenticated peer becomes authenticated, one per mechanism, recorded with file:line.
- Recover the implemented state machine: the state variables, the dispatch structure, and the guards that consult state. Record states, transitions, and which handlers run in which states — from the code, not from documentation. State is often implicit — scattered variables rather than an enum; record the variables and their write sites rather than inventing a clean automaton.
- Record the required ordering per message type: the earliest state in which the protocol permits processing it, with the spec section or the intent source it was reconstructed from — the sources named under boundary 3, never the dispatch guards under test: a missing guard must not erase the requirement it fails to enforce. Where no written definition exists and the code declares no intent, record the message type as unconstrained rather than inventing a requirement.
- For client or agent targets, record which input paths run with zero victim interaction, with the receiving code.

### 3. Walk the early-reachable attack surface

- From each entry point, trace forward and record every sensitive or complex path executable before the authentication boundary, or before a required transition, or without victim interaction — a path enters the inventory when it is early against any of the three. Never assert reachability from file names, docs, or configuration intent — trace the actual code path from the entry point and record it.
- Patterns to check while walking: dispatch tables that register handlers for all states and leave state checking to each handler; cryptographic parsing of attacker-supplied material — certificate chains, tickets, signatures — before any identity is established; resumption and fast-path machinery that runs application-adjacent code before full authentication completes; unauthenticated control or diagnostic messages multiplexed into an otherwise authenticated channel; error paths that format, reflect, or log attacker input pre-authentication; session objects allocated and mutated for unauthenticated peers, state buildup before identity.
- For each item record: the entry point, the trace, the boundaries it is early against, the configuration required (or none), and the LoC that are reachable — name the counting unit once, count the project's own code, and name large third-party or standard-library closures separately, without counting code that lies outside the target.
- If a trace cannot be completed, the item is unproven: excluded from every claim and count, listed separately with what blocked the trace.

### 4. Compare implemented ordering against required ordering

For every message or input type, compare the earliest state at which the implementation processes it against the earliest state at which the required ordering permits it. Every gap is a finding. Three shapes to check:

- **Missing state guard**: the handler is dispatchable in states where the message is not valid, and nothing checks.
- **Parse before state check**: a guard exists, but the message body is parsed, decompressed, or verified before the guard runs; everything the parser touches is early-reachable even though the message is eventually rejected.
- **Out-of-order and repeated transitions**: transition messages accepted in an order the protocol forbids, or accepted again where the required ordering permits the transition only once — a repeated hello, renegotiation, or re-keying is a gap only where the protocol forbids the repetition — re-entering code that was supposed to run once.

Distinguish processing from rejection: a message rejected at dispatch before its body is touched is correctly gated; the finding is handler or parser code actually executing early.

### 5. Measure sensitivity and complexity

Record per item the sensitivity properties and the complexity numbers defined above. Report numbers, not adjectives: a path is "complexity 41 across 212 lines with 9 allocation sites", not "very complex". Name how each measure was taken, and record n/a where a measure does not fit the language or format, rather than inventing a number. Count by reading, with the text tools that SKILL.md allows; run no complexity tool.

### 6. Classify intent and rank the inventory

- Classify every item: **intended-early** when its function requires running before the boundary — identity cannot be checked without parsing the credential, a session cannot be negotiated without parsing the hello; **unintended-early** when nothing about its function requires early execution and the reachability follows from dispatch structure, a missing or late guard, or an ordering accident. Early reachability is often deliberate and necessary; separate the cases with recorded evidence, never by assumption. For a library or framework, the documented default posture is developer intent: code early because the embedding application configures no boundary is intended-early, noted as such. Where the evidence is genuinely ambiguous, classify as unknown and ask the user.
- Rank by exposure first — early against more boundaries ranks higher, pre-authentication 0-click paths at the top — then, within a tier, by sensitivity-property count, then by the complexity measures.
- Intended-early items head the audit-attention list: they cannot be moved, so they earn scrutiny in proportion to their exposure. Unintended-early items, every state-ordering gap from step 4, and boundary bookkeeping defects are findings; for each, name the smallest change that would fix it (add the state guard, check state before parsing, gate the dispatch, record the crossing). Naming the direction is in scope; designing and applying the change is not.

### 7. Validate adversarially

Every finding — unintended-early items, state-ordering gaps, and boundary bookkeeping defects — goes to a clean agent ("Adversarial validation: the clean agent" in SKILL.md). Give it the claim and its coordinates, never your trace or notes. Only confirmed findings enter the report and the counts; refuted and unresolved items are recorded separately. Inventory items that are not findings keep their recorded traces; the clean agent's time goes to the findings.

### 8. Write the handoff and give the report

- Keep each finding's record under findings/, and every other item's trace in inventory.md, so every claim can be checked against its trace.
- Write this stage's findings/ and inventory.md in the layout that SKILL.md gives, and give its report as your final message; the report stands alone.
- Write handoff.md for stage 3 per the specification in SKILL.md: the pin, the entry points, the authentication boundary locations one per mechanism with file:line, a summary of the implemented state machine (state variables and dispatch structure), the security enforcement points recorded along the way, counts of intended-early and unintended-early items, summary numbers, and open items.
- Report numbers, not adjectives: entry points inventoried; LoC reachable before each boundary (absolute and as % of core LoC, recording what you counted as "core", both configurations reported where a boundary is configuration-created); items per boundary and per intent class; state-ordering findings by shape; unintended-early and boundary-bookkeeping findings by boundary; unproven items listed separately.
- STOP before you publish or report anything. Vulnerability reports, public patches, and maintainer contact are the user's, not yours. Leave the inventory and the findings for the user.

## Scope and limits

- This audit is configuration-independent identification. Stage 1 covers what the default configuration reaches and gates what default functionality does not use; stage 3 covers how non-default configuration combinations interact — silently disabling enforcement or leaving accepted-but-inconsistent state. The stages compose: mark an unintended-early path as a candidate for gating in a future stage-1 run when it is reachable in the default configuration and unused by default functionality; the authentication boundary and state guards recorded here go into the handoff as enforcement points for stage 3. What only this audit covers is code that is used, intended, and cannot be gated — it can only be audited in proportion to its exposure.
- Reachability ordering, not protocol conformance: the audit compares when input is processed against when it is permitted, and makes no broader compliance claims.
- An inventory item is an audit priority, not a vulnerability; no exploitability is claimed, and severity of individual bugs found along the way is not the point.
- Compare every message type against every state across every configuration, but every claim still needs a recorded trace.

## Pause and ask the user when

- A trace cannot be completed but the item would rank high on exposure and complexity.
- The implemented ordering diverges from the written definition in a way that looks deliberate — compatibility with non-conforming peers is common — and the intent classification hinges on evidence the code does not show.
- You find a likely vulnerability mid-audit: flag it immediately, treat the details as sensitive, and leave all reporting (coordinated disclosure included) to the user.
- You are about to contact upstream, file a report, or publish anything externally: STOP, the user does this.

## Done when

- [ ] The pin from the starting instructions recorded with the results.
- [ ] Authentication boundary locations and the implemented state machine recorded with file:line; every required ordering recorded with its spec section, remembered quote, or intent source, and labeled spec-verified, spec-recalled, code-reconstructed, or unconstrained.
- [ ] Every inventory item has a recorded trace from a named entry point; unproven items are excluded from all counts and listed separately.
- [ ] Every item records the boundaries it is early against, the configuration required or none, its sensitivity properties, and its complexity numbers.
- [ ] Every item classified intended-early, unintended-early, or unknown, with recorded evidence; unknowns queued for the user.
- [ ] Every state-ordering gap classified by shape (missing guard, parse before check, out-of-order or repeated acceptance).
- [ ] Findings name the smallest change that would fix them; no gates or patches designed or applied.
- [ ] Results measured: entry points, LoC before each boundary (absolute and % of core, with "core" defined), items per boundary and intent class, state-ordering findings by shape, unintended-early and boundary-bookkeeping findings by boundary.
- [ ] Every finding confirmed by a clean agent; refuted and unresolved items recorded separately and excluded from all counts.
- [ ] findings/, inventory.md and handoff.md written in the layout that SKILL.md gives, on local disk only, and the report given as the final message.
- [ ] No network access occurred.
- [ ] Nothing was published, reported or sent to anyone on the user's behalf.
