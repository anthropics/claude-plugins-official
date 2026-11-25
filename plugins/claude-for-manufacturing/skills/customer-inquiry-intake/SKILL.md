---
name: customer-inquiry-intake
description: "Reads a customer RFQ in whatever shape it arrived — a PDF drawing package, a 40-line spreadsheet, a portal export, a phone photo of a marked-up print, or a forwarded thread where the real requirement is four messages down — and pulls specifications, quantities and dates into one consistent intake form with every field traceable to the file and page it came from. Records how each tolerance was read and which geometry path each line takes. Reports what was never stated separately from what was stated two different ways. Checks the request against what the plant can actually build before asking the customer anything, drafts the questions back as sendable text, and returns a provisional bid/no-bid that names which unanswered question would change it. Use when someone says \"an RFQ came in,\" \"can we quote this,\" \"should we bid this job,\" \"read this inquiry,\" or \"what's missing from this RFQ?\""
compatibility: "Requires none. Reads Microsoft 365 mail, attachments and document libraries, and the ERP (Oracle NetSuite or Infor M3) for closed-work-order actual cost and quote history. Runs on a pasted email or an uploaded PDF with no connector. Never infers a tolerance from a drawing, never computes machine hours, never asserts a no-bid as a decision, and never closes an inquiry because a customer went quiet."
---

# Customer Inquiry Intake

An RFQ is a customer asking *what would this cost, and when could I have it?*

In make-to-order manufacturing there is **no standard format**, and the
estimator's first job is always the same one: extract the specs, quantities,
dates and terms into a consistent shape, and work out what is missing. That
extraction is mechanical, high-volume, and currently done by the most expensive
person in the department.

**Quick start**

```
→ Ingest everything as ONE inquiry, however many attachments arrived
→ Extract into the intake form; every field cites its file and page
→ Per line: what geometry arrived, and its path (C2 drawing, C1 STEP, B prior part, A text, none). A text-only line is a ROM at most
→ Per tolerance: how it was read. A general note applied to a feature is reading, and cites the note
→ Split what was never stated from what was stated two ways. Two registers
→ Check manufacturability FIRST. A hard disqualifier stops here, before we ask the customer anything
→ Draft the questions back as a sendable email, not a checklist
→ Recommend bid or no-bid PROVISIONALLY — never wait for answers; name which answer would change it
→ Answers re-enter at extract, not at scoring. Re-score and say what moved
→ No reply? Surface as stale. Stale never cancels, declines or closes
→ Never infer a tolerance. Never decide. Recommend
→ Stop at the registers, the questions and the bid/no-bid. No hours, no cycle times, no costing — that is quote-build's
```

---

## Inputs

**First, find the plant setup:** from the task's own folder (never `cd` into the plugin), run
`python3 -I <this skill's folder>/../../shared/scripts/plant_setup.py find`, do its `setup_page_first` step, then read the profile at
`profile_path` and any rate at `rates_path`, per `../../shared/replies.md`.

| Input | Source | Form |
|---|---|---|
| The RFQ itself | M365 Outlook mail and attachments, or a SharePoint folder | PDF, XLSX, DOCX, image, email body |
| Prior quotes for similar parts | M365 documents, NetSuite quote history. Infor M3 gives none (`../../shared/erp-connectors.md`): documents only | Documents and connector |
| Plant capability profile | `## Plant context`, captured during `onboarding` | Config |
| Plant constraint set | `## Plant context` | Config |
| Actual cost on comparable prior jobs | `production_work_orders` actual-cost columns in the dataset: NetSuite, Infor M3, or any ERP `custom-connector` mapped | Dataset |

---

## Workflow

### Step 1 — Ingest

**First, look for it on the Open work page.** Before building a form, look
for the RFQ reference (or the customer and part) in `## Open inquiries`
(`../../shared/replies.md`, *The open work*). If it is there, resume that form
from the page at its `paused_at_step` rather than starting a new one. **The
reply's first line says so:** *"Picking up EH-RFQ-0912 from your Open work
page, paused at step 5."* An
answer pasted into a new chat with nothing attached is enough to resume.

Accept an email with attachments, a folder, or a pasted document.

**A multi-attachment RFQ is one inquiry with several line items, never several
inquiries.** Different parts in one package legitimately carry different dates
and quantities; the form holds those per line.

Detect whether this revises an earlier RFQ and **link rather than duplicate**.
Read `reference/arrival-formats.md`.

### Step 2 — Extract into the intake form

Header, line items, quantities as a structure, specs, dates, commercial terms.

**Every extracted field carries its source — which file, which page** — so the
estimator can verify without re-reading the package. An estimator who cannot
trace a number will re-derive all of them, and the skill has saved nobody
anything.

**Never average a quantity range or a set of price breaks.** Setup amortizes
across quantity, which is the whole reason unit price drops with volume.

**Read the drawing fully, callout by callout.** Every dimension and tolerance
with its view and zone; the datums as the drawing identifies them; every key
characteristic by its label. **Each `specs` entry records its
`reading_basis`**: `printed_callout`, `general_note`, `from_text` or
`unreadable_flagged`. **Applying the drawing's stated general tolerance to a
feature that carries no callout is reading, not inferring** — cite the note
beside the feature. Assigning a tolerance from what is typical is still never
done.

**Per line, record the geometry that arrived and classify its path.** List each
file or statement the part's shape can be read from in `geometry_inputs` —
name, type, revision, source — and set `geometry_path`:

| Path | The package holds | What it means downstream |
|---|---|---|
| `C2` | A drawing — PDF, image or text extract | The normal case |
| `C1` | A STEP or 3D file and no drawing | Imported and read, nothing generated. STEP import is unverified |
| `B` | A drawing plus a **different** prior part's model named as the starting point | That model is adapted and saved as new; without it, C2 |
| `A` | Written specifications, no drawing | Built from the text. A ROM at most, never a firm quote |
| `none` | A part number only — a repeat part | Priced from its routing, or a question |

Classifying is reading the package; it never builds anything, and **a line is
never relabelled to a path it is not**. **A new revision of a part we have run before
is `C2`**: the drawing is the geometry, and the earlier revision's routing and
actuals are history for `quote-build`, not a model to adapt. Do not tell the
estimator the old routing is where pricing will start — a routing for another
revision is superseded.

### Step 3 — Flag missing and ambiguous, separately

**Never stated** is a different problem from **stated two different ways.** The
first needs a question to the customer; the second needs a decision. Each
register carries why it matters, and the ambiguous one carries every value found
with its source.

Never silently resolve an ambiguity — not to the later value, not to the
stricter one. Read `reference/registers.md`.

**Two drawing facts always reach the missing register.** A drawing — or a
part — with no revision stated: the quote must say which revision it is priced
to, and nobody can yet. And **a change the customer mentions as pending**
("engineering may change the port thread"): a risk to the revision being
quoted, with the customer's own words as its source. Both become questions in
Step 5.

### Step 4 — Check manufacturability, before anything goes to the customer

Check the request against the plant's known constraints — materials, processes,
size envelope, demonstrated tolerance capability, certifications held — on
whatever is stated so far. **The envelope and the tolerances read off the
drawing count as stated**, with their source: a 0.002 in true position read
from KC-2 is checked against demonstrated capability like any other stated
requirement.

**Report each violated constraint specifically**, never as a general fail.
"0.0005 in true position is below this plant's demonstrated capability on this
process" is actionable; "does not meet plant capability" is not.

**A hard disqualifier stops the sequence here.** Wrong process entirely, outside
the size envelope, a certification the plant does not hold — return a no-bid
recommendation with its specific reason, before any questions go out. There is
no point asking a customer five questions about a part the plant physically
cannot make.

Two limits on that stop, and both matter:

- **It stops the automated sequence, not the inquiry.** The estimator can
  override and proceed. The inquiry stays open.
- **Only violations determinable from stated facts qualify.** Anything resting
  on a field that is missing is a *scoring input* for step 6, not a stop. A
  disqualifier inferred from a blank is a guess.

Softer concerns — tight but achievable tolerances, an awkward material, a date
that looks difficult — carry forward to step 6 as scoring input rather than
stopping the flow.

### Step 5 — Draft the questions back

One clear list, written **as an email the estimator can send**, in the order a
person would ask, with enough context that the customer can answer without
opening the file again.

A bulleted list of field names is a to-do list. A short note is what gets the
answer back today.

**Keep the email word for word in the form's `open_questions`, numbered as
sent**, so a later chat matches each answer to its question without guessing.
If the estimator says they changed it before sending, store their version.

### Step 6 — Score the provisional bid/no-bid recommendation

Against capability, against the constraint check above, and against **actual
cost on comparable closed work orders** rather than standard cost — because
actual cost is the number that says whether the last job of this kind made
money.

Cite each comparable as of the date its work order closed, and say how old it
is. A comparable from two years ago was priced in a different material market,
and an estimator weighing it needs to know that without going to look.

**Score each line, then roll up.** Each line gets its own
`line_recommendation`; the inquiry's is `bid`, `no_bid` or `partial`, and each
entry in `would_change_recommendation` names the line it moves. "No-bid line 1"
lives in those fields, never only in prose, because `quote-build` reads the
fields to decide which lines to quote.

**This runs immediately on what is known. It never waits for the customer's
answers.** Most RFQs arrive with at least one gap, so a recommendation that
blocked on answers would stall on nearly all of them — which defeats the point
of the skill.

**While questions are open the recommendation is marked provisional, and it
names which specific unanswered questions would change it** — *"if the material
is 4140 rather than 4130 this becomes a no-bid."* That tells the estimator which
answer to chase rather than chasing all of them equally, and it is the
difference between a recommendation and a guess wearing one's clothes.

**Recommend with reasoning. Never decide.** The skill does not know about the
customer relationship or the strategic reason to take a marginal job. Read
`reference/bid-no-bid.md`.

**This skill stops at the registers, the questions and the bid/no-bid.** The
actual-cost evidence the score rests on is cited — work order, date, outcome —
and that is all. **No machine hours, no setup or cycle times, no per-operation
work content, no comparables analysis and no costing**: those are
`quote-build`'s, derived from the ladder after Gate 3. An hours figure written
here would be a second, unlabelled estimate of the same job, and the quote
would have to pick between them.

### Step 7 — Fold in the answers, and handle the ones that never come

**An answer is new source material, so it re-enters at step 2, not here.** It is
extracted like anything else, with its own source reference; the gaps register
shrinks; and step 6 re-scores on the fuller picture. It is a **revision of the
existing inquiry, never a new one** — the same mechanism a revised RFQ uses.

**Where an answer flips the recommendation, say plainly that it changed and
why.** A recommendation that silently reverses between two readings is worse
than either version of it.

**After a configurable interval with no reply, surface the inquiry as stale** —
with its provisional recommendation and its still-open questions attached — so
the estimator either quotes it with exclusions or drops it deliberately. The
interval is `MFG_RFQ_STALE_DAYS`, else the profile's *RFQ stale after* line,
else **5 business days, stated as the default, not plant-set**. There is always
an interval: an unconfigured plant whose inquiries never go stale is the unbid
book this rule exists to prevent. Check it every time this skill or
`rfq-to-quote` runs, reading `stale_after` from the Open work page, so a new
chat surfaces stale inquiries with nothing attached. The clock starts at `questions_sent_at`; with no send
recorded, it starts at `received_at` and says so. An inquiry already declined
is never surfaced as stale.

**Stale is a visibility change, never a status change.** The skill does not
cancel, decline, close or no-bid an inquiry because a customer went quiet. It
stays open, with its provisional score and open questions intact, and the
decision stays the estimator's.

This step is not optional. Silently aging out is the single most common way an
RFQ joins the unbid book — the number this skill exists to reduce.

---

## Approval gates

**Nothing goes to the customer.** The open questions are drafted as sendable
text and **the estimator sends them — that is Chain 1's first gate.** Microsoft
365 is read-only by default and no mail is sent on anyone's behalf.

**The bid/no-bid is a recommendation the estimator confirms** — Chain 1's second
gate, and what makes the chain valuable rather than merely fast. It sits after
the questions rather than at the very front because a sound call often needs
those questions already in flight, but it is still ahead of every costing step.
`quote-build` proceeds on a `no_bid` if the estimator says to, because it is a
recommendation and not a verdict.

The intake form leaves this skill with `bid_decision_state: draft` every time.
Only an estimator moves it to `confirmed` or `declined`, and the form records
who and when. Never emit a state other than `draft` — the gate is theirs to
pass, and a form that arrives at `quote-build` already marked confirmed by the
skill that wrote it is not a gate at all.

Nothing is written back to the ERP.

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

**The intake form** — per `../../shared/contracts/intake-form.md`, in exactly
the shape `quote-build` consumes. Customer and contact, RFQ reference, dates
received and due, commercial terms as stated (payment, freight, packaging,
liability), and per line: part and description, revision, quantities with their
breaks, material, key specs and tolerances each with its reading basis, finish,
certifications, per-line delivery date, estimated annual usage for a repeat
part, and the line's geometry inputs and geometry path.

**Print the form itself, with its field names**, as a field table (field,
value, source, reading basis), not a YAML block —
`geometry_path: C2`, each tolerance with its `reading_basis` and `source_ref`
— after the summary, not in place of it. A summary that says "line 1 is C2"
is not the form: `quote-build` and the estimator check the fields, and a field
nobody printed is a field nobody checked.

Flag a customer term that clashes with the plant's standard. Do not silently
accept it.

**Open questions** — drafted as sendable email text.

**Missing register** — never stated: the field, why it matters, where it should
have come from.

**Ambiguous register** — stated more than once: every value with its source, and
why the difference matters.

**Bid/no-bid recommendation** — with reasoning and the specific constraint
violations behind it. Marked **provisional** while questions are open, naming
which unanswered questions would change it, and re-scored when answers land with
a plain statement of what moved.

**Staleness** — where the configured interval has passed with no reply, the
inquiry is surfaced as stale with its provisional recommendation and open
questions attached. It remains open.

The intake summary renders in the house artifact style
(`../../shared/artifact-style.md`); the questions to the customer are plain
sendable text.

---

## Edge cases and failure modes

- **The drawing is an image with no dimensions in text** — extract what is
  visible and mark the line for human review. **Never infer a tolerance from a
  drawing.**
- **A feature with no callout, under a general tolerance note** — apply the
  note, `reading_basis: general_note`, citing the note. That is reading.
- **No drawing revision, or a change the customer says is coming** — both on
  the missing register, both as questions.
- **Asked for hours or a price at intake** — say that is `quote-build`'s step,
  after the bid is confirmed. Do not estimate them here.
- **Quantity given as a range or with price breaks** — capture the structure.
  Never average.
- **This RFQ revises an earlier one** — detect and link. Do not create a
  duplicate inquiry. **Customer answers to open questions use the same
  mechanism** — they revise the existing inquiry, they do not start a new one.
- **The customer never answers** — after the configured interval, surface as
  stale with the provisional recommendation and open questions attached. The
  inquiry stays open; **a timeout is never a decline.** Never let it go quiet
  either — that is how the unbid book grows.
- **Answers arrive that flip the recommendation** — re-score and **say plainly
  that it changed and why.** A recommendation that silently reverses between
  readings is worse than either version.
- **A hard disqualifier is only arguable from a missing field** — that is not a
  disqualifier. It is a scoring input. Never stop the sequence on a blank.
- **Multiple parts with different dates** — one inquiry, multiple line items,
  per-line dates.
- **Customer terms conflict with our standard terms** — flag it. Do not silently
  accept.

---

## Degradation

Runs on a pasted email and an uploaded PDF with no connector at all.

| Not available | What happens |
|---|---|
| M365 | Accept the RFQ pasted or uploaded. Extraction is unchanged |
| Capability profile | The recommendation is **constraint-free and says so.** It cannot have checked manufacturability against a profile it did not have |
| ERP closed-work-order cost | Score on capability and dates alone, **and say so.** No actual-cost comparable is available |
| Prior quote history | No precedent to compare against. State it rather than reading absence as a new part |

A recommendation that does not name what it could not check reads exactly like
one that checked everything — which is the failure
`../../shared/absent-is-not-zero.md` exists to prevent.

---

## Chain position

**Chain 1, RFQ to quote** — step 1, feeding `data-consolidate` and then
`quote-build`. The front door of the clearest revenue story in the plugin.

**The chain does not run in one sitting.** Steps 1–6 happen on arrival, then it
pauses while the customer's answers are pending — often days, and usually the
longest single stretch in quote turnaround. Treat the inquiry as resumable
state, not one pass: answers re-enter at step 2 and the recommendation
re-scores.

**Metric.** Quote turnaround.

---

## Reference files

| File | Load when |
|---|---|
| `reference/arrival-formats.md` | Steps 1 and 2 — the five formats, multi-attachment handling, and revisions |
| `reference/registers.md` | Step 3 — missing versus ambiguous, and quantity structure |
| `reference/bid-no-bid.md` | Steps 4, 6 and 7 — the constraint check and its hard-disqualifier stop, actual-cost comparables, the provisional recommendation, staleness, and the two stated degradations |
| `../../shared/contracts/intake-form.md` | On emit — the exact shape `quote-build` consumes |
