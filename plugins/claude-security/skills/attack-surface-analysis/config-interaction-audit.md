# Stage 3: Configuration Interaction Audit

This is stage 3 of the attack-surface-analysis pipeline; the rules in SKILL.md bind here. Audit the target's runtime configuration options (config file and CLI) for dangerous combinations: combinations of two or more options that together implicitly disable or bypass a security-relevant feature, and combinations that are logically inconsistent, accepted without error yet silently disabling functionality or leaving the attack surface reachable. Findings are exclusively joint effects the developer did not intend; derive candidate combinations from the code's own structure instead of enumerating tuples, prove every finding with a recorded trace, and propose fixes that reject inconsistent configurations at load. Not a bug-hunting stage; individual vulnerabilities found along the way are a byproduct, not the goal. Never reach out to the internet for any reason.

A single misconfigured option is an operator error. A pair of individually reasonable options that together silently disables enforcement is a product defect: no operator can be expected to know the cross-product of every option against every other.

Findings are exclusively joint effects the developer did not intend. A self-describing disable switch is of no interest, alone or in any combination: its effect is the documented intent. The target is the implicit interaction, such as enabling two features where something about one makes the other unusable while leaving its code reachable, or implicitly disables a security-sensitive part of it.

The combination space over N options is exponential, but joint effects arise where the code connects option values; the residue that does not is bounded in Scope and limits. Never enumerate option tuples. Derive every candidate combination from the code: from the guard conditions at security enforcement points, and from the places where option values meet. That turns the analysis from exponential in option count into linear in enforcement points and code connections.

## The two finding classes

1. **Implicit disabling combinations**: an assignment of two or more options, none of them a self-describing disable switch for the affected feature, under which a security-relevant feature does not run, runs vacuously (the check executes but is made trivially true), or is bypassed by an alternate path. A finding requires a minimal disabling set of size two or more: no single option's value alone produces the effect. An undocumented single-option disable is outside the audit's scope, but flag it to the user as a byproduct.
2. **Inconsistent combinations**: an assignment the program accepts without error, warning, or documented description although the code requires it excluded, with the consequence that one enabled feature is made unusable while its code stays reachable, the attack surface the combination implies is off remains reachable, or two mutually exclusive features leave an undefined winner.

A combination whose joint effect the developer anticipated is not a finding, whatever the effect: if configuration validation rejects it, the program warns about it at startup, or the documentation describes the joint effect, record it as known and move on. Known combinations prove coverage; they do not appear among findings.

## Procedure

### 1. Record the pin and inventory the runtime configuration

- Record the pin that your starting instructions give; every claim is relative to it.
- Consume the stage-2 handoff when one exists: compare its pin with yours before using anything else in it. Its authentication boundary locations and recorded enforcement points seed step 2's inventory — verify each against the code before use; they are leads, never substitutes for the inventory.
- Scope: options read at runtime from a configuration file or CLI flags. Where another source (an environment variable, a runtime command) writes the same internal variable, record it as a precedence source for that variable.
- Enumerate options from parser ground truth: option registries, config-file parsers, CLI flag tables. Documentation is a source of intent claims, never the inventory.
- Normalize to internal state variables: aliases, negated forms, and deprecated names often map several user-facing options onto one internal flag. Interactions happen between internal variables; reports map back to user-facing names.
- Record per option: user-facing names, internal variable, type, default value, validation applied, and read sites.
- Record the resolution order: precedence across sources, last-write-wins rules, includes, conditional configuration blocks, reload semantics. Every path by which a security-relevant setting is silently overridden by a later or higher-precedence source is an interaction site.
- Record doc-vs-code mismatches immediately: undocumented options, options accepted but never read, wrong documented defaults.

### 2. Inventory security enforcement points

List the mechanisms: authentication, authorization, transport security and certificate verification, cryptographic parameter selection, sandboxes and privilege dropping, input validation and strictness modes, resource and rate limits, audit logging. For each, record its enforcement points (the code locations where the check actually executes) and the protected handlers or resources the check guards. This list defines "security-relevant feature" for the audit: a feature is in scope because its enforcement point is, not because an option's name sounds like security.

### 3. Bound the analysis

- Classify options by read site, never by name: an option is security-relevant if its internal variable can influence an enforcement point, by appearing in a guard on the enforcement path, gating initialization the enforcement depends on, or feeding data the enforcement consumes. Options named debug, compat, legacy, performance, or test frequently classify as security-relevant by this test. Record the rationale per option, and the exclusions.
- Build the interaction map. Two options are connected only where the code connects them: a predicate referencing both; a normalization write where one option's value rewrites another's (a frequent source: every later read of the rewritten option sees the overridden value, with nothing marking the override); a read site of one reachable only under a value of the other; a shared enforcement point or protected resource; one logical setting writable from multiple sources through precedence.
- Only connected combinations are analyzed; record each connection with the connecting code. Escalate from pairs to triples only when a pair analysis exposes a third option term in the same guard, never by blind enumeration.

### 4. Find disabling combinations (backward from enforcement)

For each enforcement point, extract the condition under which enforcement runs, expressed over operator-set option values, after applying the resolution order and normalization writes: the operator sets the pre-normalization values and reasons about those. Reduce non-boolean options to security-distinct value classes (enum value classes; numeric boundary and sentinel values such as zero, unlimited, or empty). The resulting truth table is small, because real guards reference few options, so evaluate it exhaustively. Every assignment where enforcement does not run or runs vacuously is a candidate; screen out assignments involving a self-describing disable switch for the feature and combinations whose joint effect is known (rejected, warned, or documented), then compute each survivor's minimal disabling set. Then check the inverse route: option-gated paths that reach the same protected handlers or resources without traversing the enforcement point at all. These bypasses never appear in the point's own guard, so enumerate the paths that reach the protected resource, and check the pattern list below.

### 5. Find inconsistent combinations (declared vs required)

- Collect the declared constraints: what configuration validation actually rejects, plus documented dependencies and exclusions.
- Collect the required constraints from code: a path guarded by one option uses state initialized only under another; a feature routes through a subsystem another option disables; code turned off by one option remains reachable because dispatch is controlled by another.
- Findings are the gap: assignments the code requires excluded but the program accepts with no error, warning, or documented description. Classify each by its traced consequence: security feature implicitly disabled (report under class 1), an enabled feature made unusable with its code still reachable, attack surface left reachable, or an undefined winner between mutually exclusive features.
- A combination rejected, warned about, or documented is known: record it as covered and move on.

### 6. Prove every finding

- Never assert a joint effect from option names, docs, or configuration intent. Per finding, record: the exact option names and values with their source layer; the connecting code verbatim with file:line; the trace from configuration load through normalization to the decision point showing the effect; proof, from the loader's and validator's code, that the configuration is accepted without error, warning, or documented description; and the minimal change from the default configuration that realizes it.
- If a trace cannot be completed, the candidate is unproven: keep it out of every claim and count, and list it separately with what blocked the trace.

### 7. Validate adversarially

Every finding in both classes goes to a clean agent ("Adversarial validation: the clean agent" in SKILL.md). Give it the exact option names and values, the claimed joint effect, and the affected enforcement point — never your trace or notes. Only confirmed findings enter the report and the counts; refuted and unresolved items are recorded separately. Byproducts flagged to the user (an undocumented single-option disable, a likely vulnerability) go to a clean agent too.

### 8. Design fixes

In preference order: reject the inconsistent combination at configuration load with a clear error; fix normalization ordering so a security option cannot be silently rewritten; make a dependency explicit, so enabling one option requires the other, with a logged notice. Fixes must not change behavior for any valid configuration; a fix that rejects a previously accepted configuration is a compatibility break: write it all the same, and mark it in the report as a break for the user to weigh. Prefer rejection over silent correction: a silently corrected configuration is itself a surprise to the operator. Deliver each fix as a patch file under this stage's fixes/, reported as unverified; if you write a fix for a finding that is not confirmed, it takes the prefix that SKILL.md gives, and is counted nowhere; the user's checkout is never edited.

### 9. Measure the result

Report numbers, not adjectives: options inventoried and the security-relevant subset; enforcement points analyzed out of the total found; interaction-map connections, pairs, and triples analyzed; known combinations recorded as covered; findings per class and consequence, each with minimal-set size. Rank findings by exposure of the affected mechanism and by distance from the default configuration (fewer changes means likelier deployed).

### 10. Give the report

Write this stage's findings/ and inventory.md in the layout that SKILL.md gives, and give its report as your final message; the report stands alone. This is the last stage; it writes no handoff, and its report closes the pipeline.

## Interaction patterns to check

- Fallback downgrade: a strict option paired with a compat or legacy option whose path skips the strict check.
- Master-switch shadowing: a broad off silently neuters a narrow on the operator believes is active. When the master switch is documented to have that reach, the combination is known; when not, report under class 2.
- Normalization override: configuration-loading code where one option's value rewrites another's.
- Precedence override: one internal variable writable from two sources; one source silently wins.
- Mode crossover: debug, test, or maintenance options that weaken enforcement when combined with normal serving options.
- Split enforcement: a check configured on one entry path while another option opens a second path to the same handlers without it.
- Limit bypass: a limit enforced on the primary path while another option enables an alternate path without it.
- Feature collision: two independently enabled features where initialization or resource choices of one make the other unusable or unverified while its code stays reachable.

## Scope and limits

- The audit covers combinations connected in code. Interactions mediated purely through data values and shared state, with no shared predicate, initialization, or enforcement point, are caught only when the influence reaches an enforcement point; name that residue in the results rather than papering over it.
- This audit covers runtime configuration (config file and CLI), not compile-time configuration.
- Stage 1 covers what the default configuration reaches; this audit covers how non-default combinations interact. The stages compose: once the user has applied an opt-in gate from stage 1, the option that it adds is a dependency for a later run of this audit to validate.
- Severity of any individual bug found along the way is not the point; flag it and keep the audit's focus on combinations.

## Pause and ask the user when

- A combination might be a deliberate escape hatch (test, migration, or recovery modes): nothing documents the joint effect, but it might still be intended. Ask before reporting it as a finding.
- The security-relevant set or a single guard exceeds what is exhaustively enumerable: ask which mechanisms to prioritize, by exposure, never alphabetically.
- A combination looks exploitable in deployed software: flag it immediately, treat the details as sensitive, and leave all reporting (coordinated disclosure included) to the user.
- You are about to contact upstream, file a report, or publish anything externally: STOP, the user does this.

## Done when

- [ ] The pin from the starting instructions recorded with the results.
- [ ] Runtime option inventory from parser ground truth, normalized to internal variables, with defaults, read sites, and the resolution order; doc-vs-code mismatches listed.
- [ ] Enforcement points and their protected handlers or resources recorded for every security mechanism in scope.
- [ ] Security-relevant subset classified by read site with per-option rationale; exclusions recorded.
- [ ] Interaction map recorded; every connection cites the connecting code.
- [ ] Every in-scope enforcement point has its guard extracted over operator-set values and truth-table evaluated; known combinations screened out; minimal disabling sets computed; alternate paths to its protected resources checked.
- [ ] Declared-vs-required constraint comparison recorded; every accepted gap classified by traced consequence; known combinations recorded as covered.
- [ ] Every finding carries the full evidence record; unproven candidates excluded from all counts and listed separately.
- [ ] Each finding has a proposed fix that changes no behavior for valid configurations, or one marked in the report as a compatibility break.
- [ ] Results measured in numbers: inventory counts, enforcement points, connections, pairs and triples, known combinations covered, findings by class and consequence.
- [ ] Every finding confirmed by a clean agent; refuted and unresolved items recorded separately and excluded from all counts.
- [ ] findings/ and inventory.md written in the layout that SKILL.md gives, on local disk only, and the report given as the final message.
- [ ] No network access occurred.
- [ ] Nothing was published, reported or sent to anyone on the user's behalf.
