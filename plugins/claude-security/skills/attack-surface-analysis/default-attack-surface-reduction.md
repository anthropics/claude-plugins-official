# Stage 1: Default Attack Surface Reduction

This is stage 1 of the attack-surface-analysis pipeline; the rules in SKILL.md bind here. Find code that is reachable in the default configuration but unused by any default functionality, prove the reachability with a code trace, gate it with zero change to default behavior, write the regression suite that tests the gates, and measure the reduction. Nothing of the target is built or run. Not a bug-hunting stage; individual vulnerabilities found along the way are a byproduct, not the goal. Never reach out to the internet for any reason.

A vulnerability report removes one bug. A reachability gate puts every bug in the gated code, including those not yet found, out of an attacker's reach. The highest leverage targets are complex code that can move from pre-authentication to post-authentication reachability, or from 0-click to 1-click.

Heavily audited, high-quality codebases still ship default-reachable code that nothing in a default install uses; assume the target does, regardless of its reputation.

## The reachability axes

Classify every candidate along all four:

1. **Authentication**: can an unauthenticated attacker reach this code? Move code reachable pre-authentication to post-authentication where that is the intention of the developer. There will be many cases where code is meant to be reachable pre-authentication and others where it is not intentional. The goal is to find where it was not intentional.
2. **Interaction**: 0-click -> 1-click. Does reaching it require any victim action?
3. **Configuration gating**: reachable in the default configuration -> reachable only behind an explicit opt-in -> compiled out. Reachability must track explicit configuration intent, in both directions: code that is not explicitly enabled must not be reachable, with the enablement check running before any parsing of attacker input; and code that the shipped default configuration turns on but that default functionality does not use should be moved behind an explicit opt-in. If the component has no configuration option to gate it, adding one (defaulting to off) is part of the fix.
4. **Protocol session state depth**: reachable at the first message -> only after negotiation -> only in a deep, established session. Each state transition the attacker must legitimately drive shrinks the attack surface that is reachable outside of a predefined state machine model. Treat this as the weakest of the four: state machines can often be driven cheaply, so prefer the other axes when available. It remains useful for ordering checks inside a pre-auth attack surface.

Moving complex code one step along any axis is the goal; making it unreachable entirely is better.

## Procedure

### 1. Establish the baseline

This stage receives no handoff.

- The target's code is the local checkout named in your starting instructions; fetch no code.
- Record the pin that your starting instructions give; every reachability claim is relative to it.
- Determine, from the code that sets the defaults, what the DEFAULT configuration actually enables. Do not trust changelogs or docs: "not enabled by default" in a changelog is a statement of configuration intent, not of reachability.
- Inventory the entry points: network listeners and their pre-auth message handlers, entry files, exposed endpoints, and any bundled tools.
- Inventory, by reading, what a default install actually uses. The gap between "reachable by default" and "used by default" is the candidate set.

### 2. Find candidates

Look for code reachable in the default configuration but unused by any default functionality. Patterns to check:

- **Parse-before-check**: input is parsed or verified before the code checks whether that input type is enabled in configuration. If parsing comes first, everything the parser touches is attack surface even when the feature is off.
- **Experimental or complex code reachable without explicit enablement**, especially cryptographic parsing and verification of attacker-supplied material.
- **Legacy client protocols** that ship enabled but that no default workflow uses.
- **Wrong-mode code**: code for a mode the install is not in, such as multi-tenant signup and activation paths on a single-tenant install, or installer and setup UI still reachable after installation.
- **Redundant authentication channels**: alternate login or credential mechanisms that default functionality never exercises.
- **Enumeration paths**, especially several routes to the same identity or metadata.
- **Administrative and diagnostic conveniences** reachable by default, such as debug endpoints and in-application file editors.
- **Fingerprinting emitters**: version strings and metadata the application volunteers.

Prioritize candidates by code complexity times exposure: pre-auth 0-click parsing code first.

### 3. Prove reachability

- Never assert reachability from file names, docs, or configuration intent. Trace the actual code path from the entry point to the candidate code and record it. Confirm ordering facts (parse before check) in the code before claiming them.
- For each candidate record: the entry point, authentication required, interaction required, the code path, and the LoC that become reachable. Keep these records under findings/, named for the candidate's id, so every claim can be checked against a trace.
- If you cannot complete a trace, mark the candidate unproven and keep it out of every claim and count; name in the report what blocked the trace.

### 4. Design gates with zero change to default behavior

The hard requirement: a fresh default install behaves identically with every gate applied. You are maintaining the developer's original intent while reducing what is reachable.

- Where the bug is ordering, fix the ordering itself: check whether the type is enabled by configuration before any parsing or verification.
- Otherwise use the platform's smallest native always-on mechanisms: an existing option, a new option that defaults to off where the component has none, a build flag, a server rule. Resist custom frameworks; the smaller the gate, the easier it is to review and adopt.
- If a gate changes behavior for some non-default configuration, PAUSE and ask the user before including it. A gate that refuses any input that is accepted today is such a gate in three cases: a default install also uses the handler for that input; no option lets the input through again; or the target's own files name an older client that sent it. Deliver such a gate's patch with a `waiting-` name.
- Adversarially review every gate patch before it goes to validation: it is new code and can introduce new bugs, including memory-safety bugs.
- Deliver each gate as a patch file under this stage's gates/; the user's checkout is never edited.

### 5. Write the regression suite

- Write a regression test suite covering all basic functionality of a default install (front end, login, content creation and editing, feeds, search, API writes, whatever the target's defaults offer). It is meant to pass on the ungated default install before any gate is applied; that baseline is what "passes unchanged" is measured against.
- The suite is meant to pass unchanged with every gate applied. A gate that, by your reading, would break any check is not a zero-behavior-change gate; rework or drop it.
- Run nothing. Deliver the suite as regression.patch in this stage's directory: one patch that adds its files under a new folder, attack-surface-regression/, with a README on how to run it on the ungated install and then with the gates applied. Report every gate as unverified until the user has run it.

### 6. Validate adversarially

Every proven candidate, and every gate's zero-behavior-change claim, goes to a clean agent ("Adversarial validation: the clean agent" in SKILL.md). Give it the claim and its coordinates, never your trace or notes. For a gate's zero-behavior-change claim, the clean agent also receives the gate patch and regression.patch — the claim cannot be checked without them; it still sees none of your reasoning. A claim that speaks of every gate is given every gate's patch. Finish regression.patch before you send a gate's claim: if it changes afterwards, the report says what changed. Only confirmed candidates enter the report and the counts; refuted and unresolved items are recorded separately. A gate whose claim is refuted is dropped or reworked. Either way, its patch file gets a `refuted-` name, and the report names it as not to be applied. A reworked gate is a new patch file, and its claim goes to a fresh clean agent. A gate left unresolved is delivered with an `unresolved-` name and counted nowhere.

### 7. Measure the result

Report numbers, not adjectives:

- LoC that the gates would make unreachable, by reading (absolute and as % of core LoC), recording what you counted as "core"; the percentage is meaningless without it.
- Entry points that the gates would close, out of the total.
- Per-candidate axis movement (for example pre-authentication to post-authentication, 0-click to 1-click, default-reachable to explicit opt-in, first-message to deep-session, or unreachable).
- What the regression suite covers, by functionality, and that it has not been run.

### 8. Prepare the patches

- Give a concrete patch, not only advice.
- Say in the report that a rewrite of a gate, by the user or a maintainer, is new code again and needs the same review.
- STOP before you publish or report anything. Upstream contact, vulnerability reports, and public patches are sent by the user, not by you. Leave the gate patches under this stage's gates/ for the user; your report is the writeup.

### 9. Write the handoff and give the report

- Write this stage's findings/ and inventory.md in the layout that SKILL.md gives, and give its report as your final message: the pin, the stage's scope, measurements in numbers, confirmed candidates with their axis movement, the gates, each unverified, and unproven, unresolved, and refuted items listed separately.
- Write handoff.md for stage 2 per the specification in SKILL.md: the pin, the entry points, what the default configuration actually enables, the confirmed candidates one line each with their axis movement, the gates, regression.patch, summary numbers, and open items.

## Scope and limits

- This method covers the DEFAULT configuration's attack surface. Non-default but insecure configurations are also routinely exploited; gating the default attack surface does not address those.
- This stage gates what the default configuration reaches; it does not produce the reachability inventory. A configuration-independent map of the code reachable pre-authentication, 0-click, or before a required protocol state transition — including code that is used, intended, and cannot be gated — is stage 2's job. The two compose: stage 2 marks unintended-early findings that are reachable in the default configuration and unused by default functionality as candidates for gating here.
- Severity of individual bugs found in candidate code is not the point: even a low-severity bug in experimental code underscores that such code should not be reachable without explicit enablement.
- Track every code path at the scale of the whole codebase, but every claim still needs a recorded trace.

## Pause and ask the user when

- A reachability trace cannot be completed but the candidate ranks high on complexity times exposure.
- A gate cannot avoid changing behavior for some non-default configuration: ask whether the user is aware of the tradeoff.
- You find a likely vulnerability mid-audit: flag it immediately, treat the details as sensitive, and leave all reporting (coordinated disclosure included) to the user.
- You are about to contact upstream, file a report, or publish anything externally: STOP, the user does this.

## Done when

- [ ] The pin from the starting instructions recorded with the results.
- [ ] Every claimed candidate has a recorded reachability trace from a named entry point; unproven candidates are excluded from all counts and listed separately.
- [ ] Every proven candidate is classified on all four reachability axes.
- [ ] Each gate fixes an ordering itself, or uses the platform's smallest native always-on mechanism; none brings a framework of its own.
- [ ] A regression suite covering all basic default functionality is delivered as regression.patch, with how to run it, and every gate is reported as unverified.
- [ ] Results measured: LoC that the gates would make unreachable (absolute and % of core, with "core" defined), entry points that they would close out of total, per-candidate axis movement.
- [ ] Every reported candidate and gate claim confirmed by a clean agent; refuted and unresolved items recorded separately and excluded from all counts.
- [ ] findings/, inventory.md and handoff.md written in the layout that SKILL.md gives, on local disk only, and the report given as the final message.
- [ ] No network access occurred.
- [ ] Gate patches drafted and adversarially reviewed.
- [ ] Nothing was published, reported or sent to anyone on the user's behalf.
