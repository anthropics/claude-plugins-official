# The interview — every config group, in order

**Who is answering.** A quality manager, a supervisor, an estimator or a plant
manager. Not an IT admin. Ask in their language, one question at a time, and
accept "I'd have to ask" as a complete answer.

**The whole interview is answerable in one sitting**, and every group can be
deferred. A deferred group goes on the gaps list with the affected skills named.
Nothing here blocks setup.

Group numbers match the step numbers in `../SKILL.md`. Time configuration is
group 4 and has its own file, `time-config.md`; the document drop is group 2
and has its own file, `document-intake.md`; connector options are Step 12 and
have their own file, `connector-options.md`.

---

## Order, and why

Run in this order. It front-loads what can be read rather than asked, so the
user answers fewer questions.

| # | Group | Mostly read, or mostly asked |
|---|---|---|
| 1 | Systems | Asked by category, then the four supported connectors tested |
| 2 | Documents | Collected in bulk, classified, mined |
| 3 | Export folder and dropped files | Read, then confirmed one at a time |
| 4 | Time configuration | Asked, then tested |
| 5 | Vocabulary and report depth | Asked, short — or confirm-or-correct from documents |
| 6 | Sites | Asked, short |
| 7 | Capability profile and machining data | Asked, medium — mostly confirm-or-correct where a routing or asset register came in |
| 8 | Standards, clauses and approved suppliers | Collected as documents |
| 9 | Templates | Collected as files |
| 10 | Commercial rates | Asked, shown once for a yes, saved as confirmed in the plant profile unless set in the environment |

**Any question a Step 2 document already answered is asked as *confirm or
correct*, naming the file.** *"Your quality manual says AS9100 Rev D, certificate
expiring March 2027 — still right?"* Never ask the user to retype what they
just handed over.

Sites is group 6 rather than last because groups 4, 5 and 7 are site-scoped. Ask
whether there is more than one plant before capturing anything that varies by
plant.

---

## 1 — Systems

One open question per category. **Name no product as an option**: a list of
examples reads as the plugin's preference, and the person types what they
actually run. Any name, or none, is accepted.

> *"First, what you run. What do you use for orders and invoicing?"*
>
> *"What do you use for design or CAD, if anything?"*
>
> *"What do you use for maintenance, if anything?"*
>
> *"And for documents and email?"*

**One of the four supported connectors** (Microsoft 365, Oracle NetSuite,
Infor M3, Autodesk Fusion) — test it now.

- **What is live, what is not.**
- **What it actually returns for this account.** Do not assume the standard
  schema. NetSuite in particular is heavily customised per customer, so read
  back the record types and a sample of fields that actually came through.
  For Infor M3, the test is `MNS150MI_GetUserData_CurrentUser`; read back the
  company, division, facility and warehouse it returns, and the calls in
  `../../../shared/erp-connectors.md` that answer. Name the M3 data the plugin
  cannot get from it (standard cost, quote history), once, here.
- **Infor M3 is not Infor CloudSuite Industrial or Infor LN.** "Infor" alone
  is asked which one. Only M3 is supported; the others are named systems.
- **Not live** — quote its row in the setup-steps table word for word.
- **Do not pull business data during this step.** This is a reachability and
  shape check, not a data pull.

**Anything else** — accept the name as given and say what happens next, nothing
more:

> *"No supported connector for Limble. I'll run your maintenance data on exports
> for now and look at connector options at the end of setup."*

No search, no setup steps, no mention of `custom-connector` here. Step 12 does
that once, for every system at the same time.

Record each answer in the profile's `### Systems` section: the name, and one of
`live (supported)`, `live (custom)`, `file`, `none`.

**Never connect anything on the user's behalf, and never take a credential in
conversation.** Credentials go into connector settings. Where a connector needs
an admin action the plant person cannot perform, say exactly what to ask for and
who to ask.

---

## 2 — Documents

See `document-intake.md`. The exact list, the skip tags for what a live
connector covers, classification before deep reading, and the guardrails on
what a mined value may and may not do.

---

## 3 — Export folder and dropped files

The plugin's data foundation is not "connect to the MES." It is a folder where
the plant's existing scheduled exports land, on a predictable path and cadence.

1. **Ask where the exports land.** "Your MES and inspection reports get dropped
   somewhere on SharePoint or OneDrive on a schedule. Where do they land?"
2. **List what is actually there.**
3. **Infer what each file is from its headers, then have the user confirm each
   one.** Never accept the inference alone. A file identified wrong is worse than
   a file not identified, because it will be joined.
4. **Record the refresh cadence and coverage window per file.**

**A file dragged into the conversation is a valid first-run source.** Confirm it
the same way, one at a time, and record its cadence as **manual, not
scheduled**. Then say what that means in one line: *"That works today. The
morning pulse runs on its own overnight, so it needs this file landing on a
schedule or a live connector — here's the export spec for IT."*

### When the exports do not exist yet

Common, and not a dead end. Produce an export request specification the plant's
IT can implement without a follow-up call: exact fields with types and units,
file format and encoding, naming convention, landing path, cadence, the window
each file covers, and what to do about late or corrected records.

IT is far more willing to schedule a report than to issue credentials, so this is
frequently the fastest path to data in the whole build. It is also the path from
a manual, dragged-in file to a scheduled one.

### The maintenance export, specified

Where the plant's CMMS has no live connector, this is the spec to hand IT. It is
what `breakdown-diagnosis`, `daily-production-report` and `data-consolidate`
read in place of a CMMS connector.

| Field | Type | Unit / format | Required | Notes |
|---|---|---|---|---|
| `work_order_id` | text | — | yes | The CMMS's own ID, unchanged |
| `asset_id` | text | — | yes | The same asset ID the MES downtime export uses; if the systems differ, both columns |
| `asset_name` | text | — | yes | Plant's name for the machine |
| `type` | text | `corrective` / `preventive` / `inspection` | yes | Map the CMMS's own types; never leave blank |
| `status` | text | `open` / `in_progress` / `closed` | yes | |
| `opened_at` | timestamp | ISO 8601 **with offset** (`2026-09-08T06:12:00-04:00`) | yes | Naive timestamps break cross-system correlation |
| `closed_at` | timestamp | ISO 8601 with offset | when closed | Blank, never zero, while open |
| `failure_mode` | text | — | no | The CMMS's failure code or category |
| `close_out_note` | text | — | no | Free text, verbatim; `breakdown-diagnosis` mines it |
| `parts_used` | text | `part_no:qty;…` | no | |
| `labor_hours` | number | hours, decimal | no | |
| `pm_plan_id` | text | — | no | Which PM plan, for preventive work |

- **Format:** CSV, UTF-8, header row, comma-delimited, quoted text fields.
- **Naming:** `cmms_maintenance_<YYYY-MM-DD>.csv`, dated the day of export.
- **Landing path:** the plant's export folder, beside the MES files.
- **Cadence:** nightly, landing by 02:00 local, or whatever the MES files use.
- **Window:** a rolling 90 days of `opened_at`, so a work order reopened or
  closed late is picked up on the next export.
- **Late or corrected records:** re-exported in full inside the window; the
  newest file wins on `work_order_id`.
- **Asset register:** a second file, `cmms_assets_<YYYY-MM-DD>.csv` — `asset_id`,
  `asset_name`, `work_center`, `cell`, `make`, `model`, `install_date` — weekly
  is enough.

---

## 4 — Time configuration

See `time-config.md`. Per-source zones, shift pattern, production-day boundary,
cross-midnight attribution, planned-production-time definition, then the offset
self-check.

---

## 5 — Vocabulary and report depth

Short, and it changes every output the plant ever reads.

> *"A couple of quick ones so my reports sound like your plant. Do you call it a
> job, a work order, or a traveler? And is it a cell, a line, or a work center?"*

Capture the plant's word for each of the six join keys and for their
organizational units. Canonical names are in
`../../data-consolidate/reference/join-keys.md`; the plant's words are what gets
displayed.

Where the plant's word collides with a build term, record both. **"Work order" is
the one that always collides**, because maintenance systems call repair tickets
work orders too.

**Report depth**, one optional question:

> *"When I write up an NCR or an 8D, do you want the summary first with the
> detail behind it, or the full detail straight away?"*

Recorded as `summary-first` or `full`. Deferred means `full`.

---

## 6 — Sites

> *"Is this one plant, or several?"*

If several: get the names, and ask which is the default for a run that does not
say. Then ask groups 4, 5 and 7 per site, offering inheritance rather than
repeating the whole interview.

> *"Brantford — same vocabulary and capability as Fairview, or different? I only
> need the differences."*

---

## 7 — Capability profile and machining data

Feeds `customer-inquiry-intake`'s manufacturability check and bid/no-bid
recommendation. Ask as what the plant can and cannot build, not as a spec sheet.

- **Materials** routinely run, and any explicitly not run
- **Processes** available in-house, and what goes outside
- **Size envelope** — the largest thing that fits the machines
- **Tolerance capability** — the tightest tolerance demonstrated, by process. Ask
  for demonstrated, not aspirational; this number is the basis for declining work
- **Certifications held**, with expiry dates where relevant

Missing this group means bid/no-bid degrades to a constraint-free recommendation
and must say so. That is a real loss, so it is worth the five minutes.

### Machining data

Feeds `quote-build`'s hours ladder when a part has no current routing. Where a
routing export or asset register came in at Step 2 or 3, most of this is
*confirm or correct*.

> *"For quoting from drawings, I need a few shop-floor numbers. What kinds of
> machines do you have — saws, 3-axis mills, lathes — and which work centers
> and cells are they? Roughly how long is a typical setup on each, and how long
> does a tool change take?"*

- **Machine classes** — each class, its work centers and cell, setup hours and
  tool-change minutes. **Ask whether each figure was measured or is a best
  guess, and record `measured` or `assumed`.** An assumed figure is still
  used; it is named whenever it drives a variance.
- **Cutting data** — per material and tool class, surface speed (SFM) and chip
  load (inch per tooth). Or the name of the plant's Fusion tool library, if
  that is where they keep it. *"If you don't keep cutting data, that's fine —
  hours from a drawing will be labelled as library defaults until you do."*
  An estimator's ballpark is recorded as `assumed`, never as plant data.
- **Variance-flag threshold** — *"How far apart can two estimates of the same
  operation be before you want it flagged?"* Deferred means the 15% default,
  labelled as not plant-set.
- **Stale interval** — *"How old can a cost or an actual be before you'd stop
  trusting it?"* In days.

Fields and format: `config-profile.md`, *Machining data*.

---

## 8 — Standards, clauses and approved suppliers

- **Which standards the plant is certified to** — ISO 9001, AS9100, IATF 16949,
  with revision
- **Standard quality clauses** imposed on suppliers — material certs, first
  article inspection, PPAP submission level, right-of-access for audits
- **Standard commercial terms** — payment, freight, packaging, liability, tooling
  ownership

- **Approved suppliers, by commodity** — bar stock, castings, black oxide,
  heat treat. Where the ERP (NetSuite or Infor M3) is live, read the vendor list and ask only which
  are approved for what; the ERP holds vendors, not approvals.

Ask for the plant's existing standard clause list and approved supplier list as
documents rather than reconstructing them in conversation. They exist; somebody
in purchasing has them.

---

## 9 — Templates

> *"Send me one real example of each and I'll work out the shape from it — no need
> to describe them."*

Five documents, each plant-specific and often customer-program-specific:

| Template | Consumed by |
|---|---|
| NCR form | `ncr-writeup` |
| 8D format | `root-cause-capa` |
| Quote layout | `quote-build` |
| Supplier RFQ package | `supplier-quote-request` |
| Trade study memo | `trade-study-report` |

**Derive the structure from a real example, never from a generic version.** A
customer-required 8D has a contractual shape, and a plausible-looking substitute
is worse than an admitted gap.

Collect the templates whenever the user has them to hand, and let them defer
freely — a plant that hasn't run a trade study yet has no reason to produce
a trade study memo template on day one. Say that honestly rather than
implying urgency.

---

## 10 — Commercial rates

Labor rate, burden rate and margin rules are commercially sensitive; downtime
cost per hour is derived from them and inherits the same handling. Capture
the actual values — this group is asked for real, not as a pointer to who
holds them. The storage rule is `../../../shared/secret-config.md`.

Check the four `MFG_*` variables by name first, without printing them. Any
that is set is recorded as *set in environment* and not asked. Ask for the
rest:

> *"Last one — and this one's sensitive. Do you have your labour rate and
> burden rate to hand? I'll save them in the plant profile, so quotes and the
> morning report can use them without asking again. Anyone at the plant who
> can see this plugin's memory can read that profile, and the numbers never
> go on a customer quote. If you'd rather keep them out of the profile
> entirely, your IT team can set them as environment variables instead."*

Then margin, in plain words — never ask anyone to write JSON:

> *"What margin do you usually quote at? And is there any customer, or any
> kind of job — prototypes, rush work — where it's different?"*

Record the answer as a `default` plus `by_customer` and `by_job_type`
overrides, in the shape of `MFG_MARGIN_RULES`. A rule that does not fit that
shape ("depends on the job") is recorded as said and goes on the gaps list.

Then downtime:

> *"And a figure for what an hour of downtime costs you — that's the one that
> makes the morning report price a stoppage in dollars rather than minutes."*

Four values, not three. **Downtime cost per hour is asked, never derived.**
Deriving it from labor and burden understates it — it omits lost contribution
and the cost of the missed commitment — and the plant's own figure is the one
they will defend in a production meeting. If they don't have one, that is a
placeholder and a gaps-list row like any other.

**Ask who is giving the rates** if they haven't said: *"And who should I put
down as the source for these?"* Every confirmed rate carries that name and
the date. Never infer the name.

**Show the values once, for a check.** The approval draft carries a section
headed *Commercial rates — internal, check these before you say yes*, with
each rate's value. That section is the only place in the conversation the
values are restated; the question asking for the yes, the confirmation after
the write and everything else name the rates without their values. Written
only on an explicit yes, as **confirmed**, with the name and the date.

Sensitivity here is about **storage and audience, not secrecy from every
consumer.** These values are usable and displayable in internal artifacts
(`quote-build`'s cost-basis sheet, priced downtime in the morning report) —
never in a customer-facing artifact, the readable setup summary, the config
profile page, the gaps list, sample data, or logs. After the write, confirm by
name ("labor rate is confirmed in the plant profile"), not by value.

**Credentials are never taken this way.** If someone pastes a token,
password or API key in the middle of this group, it is refused and never
repeated, per `../../../shared/secret-config.md`.

**Scrap costing basis is not in this group, and isn't asked as a question
here.** It's internal-only but not confidential in the same way (it
already sits in the ERP), so at this point in the interview — not Step
1's reachability check, which never pulls business data — read it
directly from the NetSuite connector if it's live: "standard cost from
NetSuite" is a method, not a rate, and the connector is the source of
truth for which method the plant actually uses. Infor M3 does not give
standard cost to this plugin (`../../../shared/erp-connectors.md`), so with M3
it is asked, like any other unconnected ERP. Where NetSuite isn't
connected, ask for it here instead, as a plain (non-sensitive) config
value, and record which source supplied it.

Expect "I'd have to ask" throughout this group. That is a complete answer —
record a marked placeholder with its assumption and put it on the gaps
list, naming the rate, never its value. When the real value arrives later
("update our labour rate"), it becomes confirmed and drops off the gaps list.
