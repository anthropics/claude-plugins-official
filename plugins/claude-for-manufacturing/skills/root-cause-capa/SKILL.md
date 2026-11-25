---
name: root-cause-capa
description: "Reads sensor history, inspection measurements, maintenance records and prior tickets onto one verified timeline, runs the pattern checks in code rather than by eye — SPC drift, clustering by lot, shift, operator, machine and tool change, correlation with a maintenance event — then proposes ranked candidate causal chains, each with the evidence for it, the evidence against it, and the test that would confirm or kill it. Drafts the 8D. Where the leading candidate points at purchased material, raises the supplier-caused flag that starts a sourcing action. Use when someone says \"why did this happen,\" \"root cause,\" \"write the 8D,\" \"investigate this nonconformance,\" \"CAPA,\" or \"the customer wants a corrective action report.\""
compatibility: "Requires none. Reads the consolidated dataset, historian and inspection exports from Microsoft 365, the ERP (Oracle NetSuite or Infor M3) for lots and material receipts, and maintenance history via data-consolidate. Runs on exports alone with no connector. Never correlates across sources whose clocks it could not align. Never produces a single unqualified verdict."
---

# Root Cause and CAPA

The step between "we found a bad part" and "we fixed the reason." It is slow,
expert work, and the reason it is slow is that the evidence sits in four systems
that nobody looks at together.

**Two rules govern everything below, and they are the whole character of the
skill:**

**Compute, do not eyeball.** Control limits, run rules and group comparisons are
calculated in code and the skill interprets the computed result. A claim that a
process "was drifting," asserted from looking at a data file, is the first thing
a quality manager will test and the fastest way to lose the room.

**Rank, do not conclude.** The output is candidate causal chains with supporting
*and contradicting* evidence. A confident wrong root cause is worse than a
ranked list, because it closes the investigation and the fix fails.

**Quick start**

```
→ Assemble the evidence window; VERIFY time alignment first
→ Misaligned? Refuse to correlate. Say which conclusions still survive
→ Run the computed checks: SPC drift, clustering, maintenance correlation, recurrence
→ Build candidate chains, each link carrying its own evidence for and against
→ Rank by evidential strength; name what would confirm and what would kill each
→ Draft the 8D: D1-D5 and D7 populated, D6 and D8 left as placeholders
→ Material implicated? Raise the supplier-caused flag for Chain 5
→ Customer pack: redact as a reviewable diff, approved before anything leaves
```

---

## Inputs

**First, find the plant setup:** from the task's own folder (never `cd` into the plugin), run
`python3 -I <this skill's folder>/../../shared/scripts/plant_setup.py find`, do its `setup_page_first` step, then read the profile at
`profile_path` and any rate at `rates_path`, per `../../shared/replies.md`.

| Input | Source | Form |
|---|---|---|
| The NCR | `ncr-writeup` | `../../shared/contracts/ncr.md` |
| Sensor and process history for the window | Historian export to M365 | CSV |
| Inspection measurements across the run | Quality system export to M365 | CSV/XLSX |
| Prior NCRs and CAPAs | M365 quality library | Documents |
| Maintenance history on the asset | CMMS, via `data-consolidate`'s consolidated dataset | Structured — connector-sourced when a CMMS connector is live, export-sourced otherwise |
| Work order, lot, material receipts | The ERP. Infor M3 receipts carry no lot (`../../shared/erp-connectors.md`): the lot-to-receipt link is asked, and unverified until confirmed | Connector |
| Supplier and PO for the material lot | The ERP | Connector |
| Process documents and work instructions | M365 | Documents |
| Source clocks, shift boundary, skew self-check | `## Plant context` | Config |

**Two of these are read raw rather than from the consolidated dataset, and
that is deliberate.** The historian export because no workbook tab carries a
high-frequency sensor trace, and the inspection export because a computed
control chart needs the measurement as the gage wrote it, not as the ladder
normalized it. On identity — which lot, which work order — the dataset still
wins. Read *What this dataset is authoritative for* in
`../../shared/contracts/consolidated-dataset.md`.

**An NCR with no cited requirement blocks the 8D, the customer pack and the
diff**, with a pointer back to `ncr-writeup`. Nonconformance is always against
a requirement. The investigation itself proceeds as a draft, per Step 5: ranked
candidates and an evidence appendix, labelled draft and blocked from the 8D.

**Carry the NCR's open questions forward, never close them by omission.** A
scope with `qty_suspect_is_minimum` is printed *at least N* in D2 and in the
customer pack; an `escape_possible` NCR keeps its shipment check open in D3; a
null `qty_found` stays null with its reason.

---

## Workflow

### Step 1 — Assemble the evidence window, and verify the clocks

Align sensor, inspection, production and maintenance data onto one zone-aware
timeline around the event.

**This is most of the work and the highest-risk step in the skill.** Different
systems record time differently, some in plant local and some in UTC, some
zone-naive. Read the per-source clocks and the measured skew from the
`## Plant context` block rather than assuming, then confirm against an event
visible in two sources.

**Where alignment cannot be verified, refuse to correlate** and say which
conclusions survive anyway — lot clustering, for instance, does not depend on
the clocks. Read `reference/time-alignment.md`.

**A join is a join only when the data carries it.** A work order is on the
timeline as a *data join* when a record ties it to the lot, the part or the
event — a lot number on its row, a receipt against it. A work order the NCR's
free text names, with no such record, is on the timeline **labelled "per NCR
text, not a data join"**, and every conclusion resting on it says so. Calling
three work orders a clean traceability join when the data ties the heat to
one of them widens the suspect scope on an assertion, and the scope is the
number a customer gets told.

### Step 2 — Run the pattern checks, computed

- **SPC drift** on the relevant characteristic across this run and the ones
  before it, against computed control limits and run rules
- **Clustering** by material lot, shift, operator, machine and tool change —
  each reported against its base rate
- **Correlation with a maintenance event**, gated on step 1 verifying
- **Recurrence**, carried forward from the NCR's search at creation

Report checks that came back clean, and separately report checks that **could
not run**. Those are different states. Read `reference/pattern-checks.md`.

**Print every figure from the computation, including the comparisons.** The
control limits, the measured value, and *how many times over the limit it is*
all come out of the same code and go into the figures block
(`../../shared/computed-figures.md`). Computing a limit in code and then
dividing by it from memory is how a correct chart gets a wrong sentence written
under it. The prose quotes the block.

**The SPC rows are required whenever measurements exist, whatever they show.**
Five rows in the figures block, every run: **centreline, UCL, LCL, the basis**
(which chart, how many points, which runs), and **the run rule checked** with
its result. They are printed when the process was in control, when the run
rule found nothing, and when the finding is thin — "computed, no drift found"
is a result, and a chart nobody can see is the claim a quality manager tests
first. The only run that omits them is one with no measured characteristic,
and that run says so under *checks that could not run*.

### Step 3 — Build candidate causal chains

Each stated as a chain rather than a label — material lot variation → hardness
above nominal → tool wear accelerated → dimension drift — with supporting and
contradicting evidence attached **to each link**, because a link with no
evidence is where the reasoning is actually weak.

**Every link carries its own two lines, For and Against, each citing the source
record** — not one For and one Against for the whole candidate. A link with
nothing under For is named as the weak point of that chain, in those words. The
format in `reference/8d-and-candidates.md` is the required shape, not an
illustration.

### Step 4 — Rank, and name the discriminating tests

By evidential strength, each candidate carrying what would confirm it and what
would kill it. Where two are supported equally, **present both** — a stated tie
is a real finding and it names the test that would settle it.

**Two separate lines per candidate, and one line for the whole list.** Every
candidate has a *Confirm* test and a *Kill* test on separate lines, never merged
into "confirm or kill by re-measuring". Then, after the ranking, one required
line: **"Cheapest discriminating test:"** naming the single test, across all
candidates, that settles the most for the least effort, and which candidates it
separates. That line is what turns a ranked list into tomorrow morning's plan.

### Step 5 — Draft the 8D

**Draft or block is decided by two conditions, and nothing else.** The 8D is
**blocked** when, per `../../shared/contracts/ncr.md`, the NCR has no cited
requirement (`requirement_cited` null with `requirement_not_locatable` true), or
its `approval_state` is not approved. State which condition blocked it, and
still produce the ranked candidates and the evidence appendix as a draft. In
every other case — thin evidence, an unresolved tie, a request to "fill it in
completely" — the 8D **is produced**: D1 to D5 and D7 populated from the
evidence, with D4 carrying its ranking and uncertainty, and **D6 and D8 as
empty structured placeholders**, because they need a real-world outcome and a
human signature, and a pre-filled D6 is a false record of verification. The
same NCR gives the same outcome every run.

D4 keeps its ranking and its uncertainty. **Every D5 action names the D4 link
it breaks**, on the action's own line — "breaks link 2, hardness above
nominal, by adding incoming hardness verification". An action that breaks no
link, a quarantine or a re-inspection, is not a corrective action: move it to
D3 if it is containment, or label it **"improvement, not corrective action"**
and leave it outside D5. D7 is the system-level change — and where the recurrence
check found a CAPA that failed, D7 addresses **why the earlier fix did not
hold**. Read `reference/8d-and-candidates.md`.

### Step 6 — Route the signal

Where the leading candidate points at purchased material, emit the
supplier-caused flag per `../../shared/contracts/supplier-caused-flag.md`. That
is the trigger into Chain 5.

**A tie for first does not raise the flag.** Where the material candidate is
tied with another, say so, name the cheapest test that would separate them, and
hold the flag until that test runs. A supplier claim is commercially serious,
and a tie is not a lead.

**When the flag is emitted, stamp `determination_made_at` and say what it is
in one line:** *"determination_made_at is the middle timestamp of Chain 5's
escape-to-RFQ metric; it cannot be reconstructed afterwards."* It separates
investigation time from the sourcing handoff, and without it the two collapse
into one number.

The contract requires `evidence_against` and `competing_candidates` even when
the determination is confident, so a supplier is never accused on half the
picture. It carries its own approval state, because a supplier-caused
determination is a commercially significant claim.

### Step 7 — Produce the customer-facing pack

The internal 8D holds cost data, other customers' names, supplier identity and
internal process detail. The customer version must not.

**The redaction pass is a reviewable diff, never a silent filter**, and the diff
is what the quality owner approves. A recurrence stays in — removing it is
misrepresentation, not redaction. **Every removal request is recorded in the
diff, including the ones refused**: who asked, what they asked to remove, and
the refusal with its reason. Where the pack is still blocked and no diff exists
yet, emit a **"Pending redaction log"** now with the same entry, so the
request and the refusal are on the record before the diff is built. Read
`reference/redaction.md`.

### Step 8 — Update the register row, and the Quality Register

`ncr-writeup` wrote this NCR's row in the Quality Register. This step adds
what only the investigation knows, per
`../../shared/contracts/quality-register-record.md`: the 8D step reached, the
leading cause **labelled as a candidate**, the supplier-caused flag, and the
effectiveness-check date once one is committed. Per
`../../shared/live-dashboard.md`, which names every tool call:

1. **Find the register** — the `## Dashboards` line on the Open work page, then the exact
   title *"<Site>: Quality Register"*.
2. **Read the row keyed `<site>_<ncr_ref>` and carry forward every field this
   skill does not own.** The escape clock, containment and recurrence belong
   to `ncr-writeup`; blanking them on a rewrite is how a register loses the
   one deadline that matters. No row yet (the NCR was written elsewhere):
   create it from the NCR this skill was handed.
3. `set` the row, `list` the collection, rebuild the register in code and
   publish it.
4. **Report it** with the dashboard line and the sensitivity line, or the
   fallback and *"The Quality Register was not updated: [reason]."*

**The row carries references, never content.** The NCR and the 8D appear as
their identifiers and a one-line summary. Nothing from the internal 8D's cost
data, and nothing from the redacted customer pack, goes into the register.
**The supplier signal stays on the Supply Chain page**; the register carries
only the flag.

---

## Approval gates

**The source NCR's own `approval_state` gates anything customer-facing.** Per
`../../shared/contracts/ncr.md`, if the NCR isn't `approved`, block the 8D,
the customer-facing pack, and the redaction diff — the investigation itself
may still proceed as a draft, since evidence-gathering doesn't need to wait
on the NCR's sign-off, but nothing built on an unapproved finding goes
further than that.

**A supplier-caused determination needs a human owner.** It says a vendor caused
a defect and it starts a search for an alternate source. The flag carries
`approval_state`, and `supplier-quote-request` blocks on anything not approved.

**Nothing customer-facing leaves without review of the redaction diff.** This is
Chain 2's closing gate. The pack is drafted and handed to a person; it is never
sent.

The investigation itself writes nothing back to any system of record. The 8D is
a document the quality owner files.

---

## Output

**Every document this skill produces is printed in the reply, in full.**
Saving a copy to a file as well is fine, as Word or Excel per `../../shared/replies.md`, never `.txt`; a file *instead of* the reply is not.
The person reads the reply, and every delimited block and outbound check lives
in it — a document only on disk has been neither seen nor checked.
**A record handed to another skill is saved and summarised, never pasted as
raw YAML**; memory blocks are written where the plant's memory lives; and the
name on an approval is asked, never taken from the account. All three per
`../../shared/replies.md`.

**Report depth follows the plant's preference.** The `## Plant context`
block's **Report depth** line is `summary-first` or `full` (absent means
`full`). Summary-first puts a short summary — what was found, what it
affects, what happens next — above the full document; it moves nothing out and
drops nothing. Every required field is still in the document below it.

**Ranked candidate root causes** — each a chain, with For and Against per link
citing the source, a separate Confirm test and Kill test, and after the list
the one **cheapest discriminating test**.

**The drafted 8D** in the plant's or the customer's controlled template captured
during `onboarding`. Per `../../shared/artifact-style.md`, a controlled document
is never house-styled.

**Evidence appendix** — the aligned timeline with its verified skew and residual
uncertainty, the computed SPC view, the lot analysis, the checks that came back
clean, the checks that could not run, and every source file cited.

**The figures block** — required, and part of the appendix. Every limit, mean,
ratio, count and cluster share stated anywhere in the output, with the
computation it came from. A claim that something is absent — no prior NCR, no
maintenance event in the window — carries the query that returned nothing. Per
`../../shared/computed-figures.md`. It stays on the internal side of the
redaction diff.

**Supplier-caused flag** — when applicable.

**Customer-facing redacted pack, plus the diff** — when requested. The diff,
or the pending redaction log while the pack is blocked, records every removal
request and every refusal.

**The register row** — per `../../shared/contracts/quality-register-record.md`,
with its key `<site>_<ncr_ref>` and the 8D fields, in the reply's summary table
on every run, stored or not.

**The Quality command-center page: the Quality Register** — open corrective
actions, carrying the NCR and the 8D by reference, updated in place per
`../../shared/live-dashboard.md`. Nothing is written to a system of record.
**It is reported as updated only when the publish returned a URL in this
run**; otherwise the page is offered in the conversation with *"The Quality
Register was not updated: [reason]."* Never "shared." Read
`../../shared/command-center.md`. This closes Chain 2, and is one of the two
pages Chain 5 produces from one run (the other, Supply Chain, is
`supplier-quote-request`'s).

---

## Edge cases and failure modes

- **The sensor export does not cover the event window** — say so. **Do not reason
  from adjacent data as if it were the event.**
- **Timestamps misaligned across systems** — detect and refuse to correlate. The
  highest-risk failure mode here, and a spurious correlation stated confidently
  is worse than no answer.
- **Evidence supports two candidates equally** — present both. Do not break the
  tie artificially.
- **No prior history exists** — say so. **Absence of recurrence is not evidence of
  a one-off**, and `no_searchable_history` is never read as a first occurrence.
- **The NCR's cited requirement is missing** — block, with a pointer back to
  `ncr-writeup`.
- **The finding is subjective** — no measured characteristic, so the SPC check
  cannot run. Skip it and say why rather than substituting an impression.
- **Clustering on small numbers** — three failures split two-to-one is not a
  pattern. Say that plainly.
- **Clustering by operator** — name the pattern, not the person. An investigation
  that terminates on an individual has usually stopped one question early.

---

## Degradation

Runs on exports alone. Sensor and inspection data reach the plugin as scheduled
files in every plant; that is the designed path.

| Not available | What happens |
|---|---|
| Historian export | No sensor evidence. Very common — most assets are not instrumented. Proceed on inspection, production and maintenance evidence and say sensor data was unavailable |
| Inspection measurements | No SPC drift check. Reason from the condition as described |
| The ERP (NetSuite or Infor M3) | Lot and material-receipt evidence is unavailable, so a supplier-caused determination usually cannot be reached. Say that rather than reaching it on weaker grounds |
| Quality document library | No recurrence check. Reported as `no_searchable_history`, never as a first occurrence |
| The plant's 8D template | Use the standard eight-discipline structure and flag that the controlled template was not available |
| A verified clock alignment | Correlation is refused. Non-time-dependent analysis still runs and the output says which is which |
| The `Artifact` or `ArtifactData` tools | The investigation and the 8D are unaffected. The Quality page is offered in the conversation, showing this NCR only, with "The Quality Register was not updated" |

**If Limble isn't included, or no CMMS connector is live** — minor here. Maintenance history arrives in the
same scheduled export as everything else, through `data-consolidate`, and the
maintenance-correlation check runs on it unchanged. What changes is freshness:
name maintenance explicitly as an export-sourced input in the evidence appendix
rather than letting it read as live, since a repair logged after the last export
will not be on the timeline at all.

---

## Chain position

**Chain 2, inspection to CAPA** — step 2, from `ncr-writeup`. The chain closes on
the 8D and its redacted customer pack.

**Chain 5, supplier escape to alternate source** — step 2, emitting the flag that
triggers `supplier-quote-request`.

**Metric.** CAPA closure time; first-pass yield.

**This skill's investigation time sits inside Chain 5's first segment.** That
chain measures escape detected → supplier-caused determination → RFQ issued, and
the middle timestamp is this skill's to stamp: **record when the supplier-caused
determination is made**, at the moment the flag is raised for approval.

That middle stamp is easy to omit and impossible to reconstruct afterwards, and
without it the investigation time and the sourcing handoff collapse into one
undifferentiated number — which would hide the half the plugin actually moves.

---

## Reference files

| File | Load when |
|---|---|
| `reference/time-alignment.md` | Step 1 — always. The highest-risk step |
| `reference/pattern-checks.md` | Step 2 — the four computed checks and how to report them |
| `../../shared/computed-figures.md` | Step 2 and on emit — the figures block every stated number is quoted from |
| `reference/8d-and-candidates.md` | Steps 3 to 5 — causal chains, ranking, and the eight disciplines |
| `reference/redaction.md` | Step 7 — what comes out, what must stay, and the diff |
| `../../shared/contracts/ncr.md` | On load — what `ncr-writeup` hands over and when to block |
| `../../shared/contracts/supplier-caused-flag.md` | Step 6 — the Chain 5 trigger |
| `../../shared/live-dashboard.md` | Step 8 — finding and updating the Quality Register, and the fallback |
| `../../shared/contracts/quality-register-record.md` | Step 8 — the fields this skill owns, and the ones it carries forward |
