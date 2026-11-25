---
name: onboarding
description: "Sets the plugin up for one plant on first run. Asks which ERP, CAD, CMMS and document system the plant uses and tests the four supported connectors (Microsoft 365, Oracle NetSuite, Infor M3, Autodesk Fusion), takes a bulk drop of the plant's own documents so it asks only what they don't answer, profiles the export folder, and runs the time interview with a clock-skew check. Also captures vocabulary, sites, capability, machining data, standards, templates and commercial rates, reports which skills are limited by anything missing, and ends with connector options for every other system named. Unknowns are deferred, never blocking. Use on a first session or when someone says \"set us up,\" \"get started,\" \"configure the plugin,\" \"which of our systems can you reach,\" \"which ERP can you reach,\" \"can you connect to our CMMS,\" \"here are our documents,\" \"our shifts changed,\" \"we added a plant,\" \"update our labour rate,\" \"change our margin,\" or \"reconfigure.\""
compatibility: "Requires none. Tests Microsoft 365, Oracle NetSuite, Infor M3 and Autodesk Fusion. Any other system is named in the interview, runs on exports, and gets a connector-options check at the end of setup. Writes a Plant context memory block, including commercial rates the plant confirms, and renders a config profile page."
---

# Onboarding

Every configurable value in this plugin has its home here, and no skill
hard-codes one. Nine other skills read what this produces.

**Who is answering.** A quality manager, a supervisor, an estimator or a plant
manager — not an IT admin. Ask in their language, one question at a time, and
treat "I'd have to ask" as a complete answer.

**Hand-hold, don't interrogate.** Say what each step is for before asking
anything in it, read what the plant can hand over before asking what it
can't, and turn every question a document already answered into *confirm or
correct*, naming the file.

**Setup never blocks.** Every group can be deferred. A deferred group goes on the
gaps list with the skills it limits named, and the run completes.

**Quick start**

```
→ 1  Ask which ERP, CAD, CMMS and documents system; test the four supported connectors
→ 2  Bulk document drop: name the exact documents, skip what a live connector covers
→ 3  Export folder and dropped files; confirm every file one at a time
→ 4  Time interview, then cross-check a shared event for clock skew
→ 5–9  Vocabulary, sites, capability and machining data, standards, templates
→ 10 Commercial rates into the profile, shown once for a yes — internal-use only
→ 11 Show the profile, write it on approval, render the config page; gaps list
→ 12 Connector options for every named system that isn't one of the four
```

---

## The connector model

**The plugin works with four connectors once they are connected: Microsoft
365, Oracle NetSuite, Infor M3 and Autodesk Fusion.** Only Fusion is declared
in the plugin's `.mcp.json`; the other three are enabled in Claude. These four
are the supported connectors: the only rows in the setup-steps table in
`../custom-connector/reference/known-systems.md`, and the only ones this skill
tests or gives setup steps for. NetSuite and M3 are the two ERP options, and a
plant runs one; read `../../shared/erp-connectors.md` before testing M3.

**Every other system is named, not one of the four.** The plant names whatever it
runs — SAP, SolidWorks, Limble, a homegrown MES — and any name is accepted.
It runs on exports from then on, and Step 12 reports how it could be
connected. `custom-connector` does the connecting, later, when the plant
chooses.

---

## Workflow

**First, find the plant setup:** from the task's own folder (never `cd` into the plugin), run
`python3 -I <this skill's folder>/../../shared/scripts/plant_setup.py find`, do its `setup_page_first` step, then read any existing profile at
`profile_path` and rates at `rates_path` (a reconfigure starts from them), per `../../shared/replies.md`.

**A dropped plant profile** (a `## Plant context` file, "save this as our plant setup"): check it with
`plant_setup.py render --profile <file> --out <a new folder>` (it refuses rate values and emails), show it
and its gaps, and on a yes in a later turn save it as Step 11 does. Ask only what it leaves out.

### Step 1 — Systems interview and connector test

One open question per category. Name no product as an option: the person
types what they run, and any name, or none, is accepted:

```
ERP / invoicing    "What do you use for orders and invoicing?"
Design / CAD       "What do you use for design or CAD, if anything?"
Maintenance / CMMS "What do you use for maintenance, if anything?"
Documents / mail   "What do you use for documents and email?"
```

Per answer:

- **One of the four supported connectors** — test it now and report **what it
  actually returns for this account**. Do not assume the standard schema:
  for the ERP, check the record types the plugin uses and ask the scope,
  revision, cost-field and work-order questions in `reference/erp-scope.md`. If it is not live, give
  its setup steps by **quoting its row in the known-systems table word for
  word**.
- **Anything else** — *"No supported connector for SolidWorks. I'll run it on
  exports for now and look at connector options at the end."* Record the name
  for Step 12. Nothing else: Step 1 does not search, does not describe setup
  steps for it, does not quote its registry row, and does not mention
  `custom-connector`. **Step 12 is not pulled forward**, even when the user
  asks for "just the systems part": connector options come after the gaps
  list, or when the user asks for them by name ("what are our connector
  options").

This is a reachability and shape check. **Do not pull business data here.**

**A connector is live only when its tools exist in this session and return.**
Not because `.mcp.json` declares it, and not because someone says it is set up.

**The setup-steps table is the only place the steps are written.** Never
improvise one — not "install it from the connector directory," not "sign in
and authorise," not a service name that is not in the row.

**Asked "did you try connecting it?" the answer is no.** *"I didn't attempt a
connection; connector auth is always owner-initiated."* Then the steps, for a
supported connector; for anything else, "connector options come at the end."

Record each choice in the `### Systems` section of the profile — name and
state (`live (supported)`, `live (custom)`, `file`, `none`) — per
`reference/config-profile.md`.

### Step 2 — Bulk document intake

Runs once Step 1 has established what is live, so the list never asks for
something a live connector already covers. **Name the exact documents, grouped,
and tag each line a live connector covers** `(skip — NetSuite is connected)`.
The list, the routing table and how each kind of file is mined are
`reference/document-intake.md`.

- **Skippable, and re-runnable later** ("here's more").
- **Classify first, deep-read second.** The first pass reads a header row or a
  first page only. Only a file that routes to a step is read in full.
- **Mined is not confirmed.** A value read from a file is shown labelled
  *inferred, from <file>* — never in a table of findings as if it were settled —
  and stays inferred until the user says yes to it in its own step, where the question becomes *confirm or
  correct*, with the file named. **The production-day boundary is still asked
  directly** in Step 4, whatever a shift calendar says.
- **No vocabulary or capability from a single document.** Two consistent
  sources, or ask.
- **A rate found in a file follows Step 10.** It appears only in the approval
  draft's internal rates section, once, with the file name as its source, and
  is written only on a yes.
- **An unidentifiable file goes on the gaps list by name**, asked about in one
  line.

### Step 3 — Export folder and dropped files

The data foundation is not "connect to the MES." It is a folder where the plant's
existing scheduled exports already land.

List what is there, infer what each file is from its headers, and **have the user
confirm each one**. Never accept the inference alone — a file identified wrong is
worse than a file not identified, because it will be joined. Record the refresh
cadence and coverage window per file.

**Put the files to the user one at a time.** *"`mes_downtime.csv` looks like
downtime events from the MES — asset, start, end, minutes, reason code. Is that
right?"* Then the next. Never one table of every file with "confirm or correct
each line": it gets a single "looks fine," which confirms none of them. **Record
an identity only once that file was confirmed**; the rest stay inferred, marked
unconfirmed, and go on the gaps list. If the user asks to confirm the remainder
in one go, show the remaining list and take that yes — they have now seen it.
Per `../../shared/approval-gates.md`.

**If the exports do not exist yet, or any one expected source is missing from
the folder**, write the export request specification for that source in this
run — exact fields with types and units, format, naming, landing path,
cadence, window, late-record handling — rather than only listing it on the
gaps. A missing historian or quality export gets its spec the same as an empty
folder does. Details in `reference/interview.md`.

**A file dragged into the conversation is a valid first-run source**, from
Step 2 or here. Confirm its identity one at a time like any other, and record
its cadence as **manual, not scheduled**. Say plainly what that means: the
scheduled skills (`morning-plant-pulse`) need a scheduled export or a live
connector, and the export request spec is the path from manual to scheduled.

### Step 4 — Run the time interview

Per-source timezones and whether timestamps are zone-aware or naive, then shift
pattern, production-day boundary, cross-midnight attribution and the
planned-production-time definition.

**Ask the production-day boundary as its own direct question, in the plant's
terms**, and never assume midnight: *"Your 23:00 shift runs past midnight.
Does its output belong to the day it started or the day it ended, and when
does your production day begin?"* A folder whose files show a 23:00 shift is
the cue; the question is asked whether or not the answer looks obvious, because
a wrong boundary moves a whole shift of output to the wrong day on every
report that follows.

**Then run the offset self-check.** Take one event recorded in two systems,
convert both timestamps using the declarations just captured, and report the
observed skew. A non-zero skew means the declared config is wrong, and catching
it here is the entire point of the step.

The full procedure, including how to read each result, is
`reference/time-config.md`. This is the highest-risk configuration in the plugin.

### Step 5 — Map vocabulary

Capture the plant's own word for each join key and organizational unit, so every
output speaks their language. Short step, and it changes every report they ever
read.

**Report depth** (optional, one question): *"Do you want reports summary-first
with the detail behind it, or full detail?"* Stored in the profile; read by
`ncr-writeup` and `root-cause-capa`. Not asked again if deferred — the default
is full detail.

### Step 6 — Confirm sites

One plant or several. Site-scoped groups are time, vocabulary, capability and
machining data; ask those per site and offer inheritance rather than repeating
the interview. The inheritance rule is in `reference/config-profile.md`.

### Step 7 — Capture the capability profile and machining data

Materials, processes, size envelope, demonstrated tolerance capability, and
certifications held. Ask for demonstrated capability, not aspirational — this is
the basis on which work gets declined.

**Then the machining data `quote-build` derives hours from.** Machine classes
with their work centers, cell, setup hours and tool-change time; cutting data
per material and tool class (SFM and chip load), or the name of the plant's
Fusion tool library; the variance-flag threshold; and the stale interval for
cost history. **Every setup and tool-change figure carries `basis: measured`
or `basis: assumed`** — an assumed 0.5-minute tool change once explained a 36%
hours gap, and nobody could see it was a guess. An estimator's ballpark is
recorded as assumed, never as plant data. A routing or asset export from
Step 2 or 3 answers most of this as *confirm or correct*. Fields and format:
`reference/config-profile.md`, *Machining data*.

### Step 8 — Capture standards, clauses and approved suppliers

Which standards the plant is certified to, its standard supplier quality
clauses, its standard commercial terms, and **its approved supplier list by
commodity** — `supplier-quote-request` builds its candidate list from it.
Ask for each existing list as a document rather than reconstructing it in
conversation. Where the ERP (NetSuite or Infor M3) is live, read the vendor list from it
and ask only which vendors are approved for what.

### Step 9 — Collect templates

One real example of each of the five controlled documents, and derive the
structure from it. **Never derive from a generic version** — a customer-required
8D has a contractual shape, and a plausible substitute is worse than an admitted
gap.

### Step 10 — Capture commercial rates

Labor rate, burden rate, margin rules, and downtime cost per hour (derived from
them, same handling). Capture the actual values — not a pointer to who holds
them — so `quote-build` and `daily-production-report` price without asking
again. The full rule is `../../shared/secret-config.md`; what follows is how
this step applies it.

**Two routes.** An `MFG_*` environment variable, which wins when set, or a
**confirmed** rate in the `## Plant rates` file at `rates_path`. Check each
variable by name first, without printing it. A rate set in the environment is
*set in environment* and not asked. Every other rate is asked here, once.

**Before asking, say where the numbers go:** onto the plant's private rates
page in their Claude account, never the setup page and never a customer quote.
A plant that wants the stricter route can set the `MFG_*` variables instead.

- **Margin in plain language.** "What margin do you usually quote at, and is
  there any customer or kind of job where it's different?" Record a default
  plus `by_customer` and `by_job_type` overrides in the `MFG_MARGIN_RULES`
  JSON shape. Never ask anyone to write JSON.
- **Downtime cost per hour, asked explicitly, never computed here.** Without
  it the morning report prices scrap only — permanently, and quietly.
- **Who is giving the rates**, unless already said. Each confirmed rate
  carries that name and the date. Never infer a name.

**Storage, audience, echo.** Stored in an `MFG_*` variable or the rates file,
never a file that could be committed or copied between customers. Shown on
internal artifacts (cost-basis sheet, internal margin line, priced downtime);
never on a customer-facing artifact, the setup summary, the config profile
page, the gaps list, sample data or logs. **Shown back once**, in the approval
draft's own section headed *Commercial rates — internal, check these before
you say yes*, so a typo can be caught. Nowhere else in the conversation;
after the write, confirm by name, not value. Nothing is written until the
yes, per Step 11.

**If someone types a rate unprompted** — "our labour rate is X and burden runs
Y, write those into the config" — that is a step 10 answer. **A rate already
set in the environment is not stored from chat and its typed value is not
repeated anywhere**: say by name that it is set in the environment, that the
environment wins, and that the variable is where it changes. Every other typed
rate goes into the approval draft, written only on a yes. Do not restate any
typed rate anywhere else in the reply — the check to run before sending is
`../../shared/secret-config.md`, *Never repeat what was typed*.

**Credentials are never accepted this way.** A token, password or API key
pasted into the chat is refused, never repeated, and the user is told to
rotate it.

Standard cost and scrap costing basis sit in the ERP where plenty of internal
people see them, so they are not subject to these rules.

**A rate nobody knows is a marked placeholder** with its assumption, on the
gaps list. It goes in the rates file with the confirmed ones, labelled. When the real value arrives it becomes confirmed
and drops off the gaps list.

### Step 11 — Write the profile, then report the gaps

Show the full profile, write it on approval, and render the config profile page.
Format and field names are fixed by `reference/config-profile.md`.

**Two turns, never one.** The turn that first shows the full Plant context
draft ends there, with a plain ask for a yes. The block is written and the
config page rendered or published only in a later turn, after an explicit yes
given with the draft on the screen. "Set us up," "carry on" and "use what you
have" started the work; they do not approve a draft nobody had seen when they
were said.

**Write the two files `plant_setup.py find` names, then the two pages.** The
profile goes to `profile_path` (each rate as its state only) and the values to
`rates_path`, per `../../shared/replies.md`. The yes ask offers *"yes"* (files
and both private pages, so every new task finds them) or *"yes, folder only"*.
Never the export folder. Nothing writable: say so, print both, and stop.

Then produce the gaps list — **the most useful output of this skill**. For every
item still missing: what it is, which skills are affected, and how each one
degrades. Generated from the degradation map in `reference/config-profile.md`.
**Name every affected skill the map lists, not only the most affected one** —
without a CMMS connector that is `breakdown-diagnosis` *and*
`daily-production-report`'s maintenance-work-orders-in-progress line, among
others.

### Step 12 — Connector options

Runs once, after the gaps list, over **every system named in Step 1 that is
not one of the four**: the registry row first, then a search for a
vendor-published MCP (vendor domain or vendor docs only; where web search is
not available, say so and give *"not in our registry — check your vendor's
docs"*), then the registry's access tier and what `custom-connector` would
need. One table: *System · What exists · Route · Next step*. The procedure is
`reference/connector-options.md`.

**Onboarding reports options; it never connects.** No setup steps for these
systems, no attempted connection, no credential taken. The plant chooses, and
`custom-connector` does the work. **Deferrable:** "later" ends the step, and
each system stays on the gaps list as *connector options not reviewed*.

### Reconfigure

Setup is not a one-time event. Shift patterns change, connectors come online,
sites get added. Re-running touches only what changed: show current against
proposed, change what the user confirms, and **never wipe unrelated
configuration**.

**Updating a rate.** "Update our labour rate," "change our margin" or "our
burden went up" re-runs Step 10 for the named rates only — none of Steps 1 to
9. Show each rate's current state against the proposed value, in the same
internal section of the draft, and write only the `### Commercial rates`
section after a yes. A rate set in the environment cannot be changed from
here: say it is set in the environment, by name, and that the variable is
where it changes.

**Clearing a rate.** "Clear our rates" or "remove the labour rate" sets the
named rates to **not set**, after the same yes. Say which lines each one will
block from then on.

**More documents.** "Here's more" re-runs Step 2 over the new files only, then
the steps they route to, each as *confirm or correct*.

---

## Approval gates

- **Show the profile before writing it.** Display the full draft and wait for an
  explicit yes, given after the draft was shown. Never show and write in the
  same turn. What counts as a yes is `../../shared/approval-gates.md`.
- **Never overwrite silently.** On a re-run, show current against proposed
  side by side before changing anything.
- **Never connect a tool on the user's behalf.** Guide; do not act. Connector
  auth is always owner-initiated. Step 12 reports options; it never attempts a
  connection and never describes setup steps outside the four-row table.
- **Never accept a credential in conversation.** API keys and client secrets go
  into connector settings. If someone pastes one, say plainly that it should be
  rotated because it has touched the transcript, that nothing was done with it,
  and that connector auth happens in Claude's connector settings.
- **Never repeat a pasted credential — not any part of it.** Not quoted, not
  in code formatting, not in the rotation instruction itself. It is "the token
  you pasted," "the secret you pasted." Before sending, check the reply for any
  run of eight or more characters from the pasted value, and rewrite if one is
  there. Per `../../shared/secret-config.md`.
- **Show a typed rate once, in the approval draft, and nowhere else.** Not in
  the sentence that asks for the yes, not in the confirmation after the write,
  not in the setup summary, the config profile page or the gaps list. Before
  sending, check the reply for any rate number the user typed outside the
  draft's internal rates section, and rewrite if one is there.
- **Never pull business data during Step 1.** Step 2 reads only what the user
  hands over, and classifies before it deep-reads.
- **Never push for a deferred answer.** "I'd have to ask" ends the question.

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

**The `## Plant context` memory block** — authoritative, read by every skill via
heading match. Schema in `reference/config-profile.md`.

**The config profile page** — an HTML artifact in the house style
(`../../shared/artifact-style.md`), as the plant's own readable record. A
rendering of the block, regenerated rather than hand-edited. It shows each
commercial rate by state, who gave it and the date, and never renders a rate
value.

**The setup summary** — plain language: what is configured, what each live
connector gives this plant specifically, and one line per file read in Step 2
saying what it supplied. Commercial rates appear by state, who
gave them and the date, never by value. One line more: *"Paused RFQs, supplier
quotes and dashboard links will be kept on a private Open work page the first
time you need one."*

**The time configuration report** — declared zones per source, the shift and day
boundary rules, and the offset self-check result including a zero result. **The
Source clocks table has one row per source, each with its own timezone and
zone-aware flag**: every export file (MES production, MES downtime, historian,
quality, planning) and every live connector (the ERP, a CMMS connector) is its
own row,
per the template in `reference/config-profile.md`. Never merge sources into a
shared "date-only" row; the row a source is missing from is the one whose
clock nobody checked.

**The gaps list** — every missing item, the skills it affects, and how each one
degrades.

**The connector options table** — Step 12's *System · What exists · Route ·
Next step*, one row per named system that is not one of the four supported
connectors.

---

## Edge cases and failure modes

- **The user does not know an answer** — very common for rates, machining data
  **and time config alike**. Record a marked placeholder with its assumption,
  put it on the gaps list, and move on. Never block. A placeholder isn't a
  sensitive value; a real rate, once supplied, is shown by state, never by
  value, outside the approval draft and internal artifacts. A placeholder
  source clock is never acted on as verified: a skill correlating across it
  refuses and reports the alignment gap (`reference/time-config.md`).
- **The user names a system the plugin has never heard of** — accept it,
  record it, run it on exports, and give it a Step 12 row. Never steer them
  toward one of the four.
- **No documents to hand** — skip Step 2; ask every later step directly.
- **A document contradicts the user** — the user's answer wins, and the
  contradiction is named once with the file, so a stale document is found.
- **Exports are not set up yet** — the export request specification.
- **Multi-site plant** — config per site with shared values inherited. Getting
  this wrong means one plant's shift boundary silently applied to another.
- **Connectors not yet provisioned** — partial config now, resumable later, with
  the gaps list reflecting it.
- **The offset self-check finds a skew and the user insists the config is
  right** — report it, do not override. A real clock drift is a finding worth
  surfacing to their IT.
- **No shared event exists to test the offset against** — record the config as
  declared but unverified, and put it on the gaps list.
- **A single-site plant** — still gets one site block, named `(default)`, so
  adding a second site later changes nothing about how the first is read.

---

## Chain position

Not part of a chain. It is the utility every chain depends on, and the
configuration it captures is what keeps the other skills from hard-coding
assumptions or re-asking the same questions every run.

**Metric.** Adoption and setup quality. No plant metric.

---

## Reference files

| File | Load when |
|---|---|
| `reference/interview.md` | Running the interview — every group, in order, with the wording |
| `reference/erp-scope.md` | Step 1 — the ERP record types, this plant's scope, revision, cost fields, work order source, RFQ staleness |
| `reference/document-intake.md` | Step 2 — the document list, the routing table, what each file is mined for |
| `reference/time-config.md` | Step 4 — per-source clocks, shift definition, and the offset self-check |
| `reference/config-profile.md` | Step 11 — the storage schema, site inheritance, and the degradation map |
| `reference/connector-options.md` | Step 12 — the options check and its table |
| `../custom-connector/reference/known-systems.md` | Steps 1 and 12 — the setup steps for the four supported connectors, quoted word for word, and the registry |
| `../../shared/approval-gates.md` | Steps 3 and 11 — confirming one at a time, and what approves a draft |
