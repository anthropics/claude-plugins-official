# Claude for Manufacturing

**Maintenance status:** Reference implementation. Not actively maintained or monitored, and not accepting contributions. Issues and pull requests may not receive a response. This project is provided AS IS, without warranty.

Skills for the work a plant actually runs on. Quoting make-to-order jobs, writing
nonconformances and 8Ds, diagnosing breakdowns, reporting the morning numbers —
and underneath all of it, one dataset joined out of the systems and exports the
plant already has.

You do not need to memorize anything. Describe what you need and the right skill
picks it up. Every skill that would change something pauses first: nothing is
applied, sent, or written to your systems without your say-so.

---

## Getting started

1. Install **Claude for Manufacturing** from the Claude plugin directory.

2. Say **"set us up"**. `onboarding` asks which ERP, CAD, maintenance and
   document systems you use, tests the four it works with, takes a drop of
   whatever documents you have to hand so it only asks what they don't answer,
   learns your exports, shift pattern and vocabulary, and hands back a list of
   anything still missing, the skills it limits, and the options for
   connecting every other system you named.
3. From then on, just describe what you need.

**No connectors? Eleven of the twelve skills still work.** Scheduled exports are
the designed path, not a fallback — a folder of CSVs runs them. Connectors make
it fresher, never mandatory.

The exception is `design-space-explore`, which generates CAD variants and so
needs a live CAD connection: **Autodesk Fusion on the desktop**, or a CAD
system connected through `custom-connector`. There is no fallback — no MCP
exists for SolidWorks, Creo, NX or Inventor, so a shop running one of those has
no path to that one skill. Its partner
`trade-study-report` is unaffected: it reads a variant manifest a person can
fill in by hand.

### Connecting your systems

The plugin works with four connectors once they are connected. Three are
enabled in Claude itself and are not declared by the plugin. NetSuite and
Infor M3 are the two ERP options; a plant connects one:

| System | What to do |
|---|---|
| **Microsoft 365** | Enable the Microsoft 365 connector in Claude's connector settings. Documents, mail and the export folder |
| **Oracle NetSuite** | Enable the Oracle NetSuite connector in Claude's connector settings. Read and write; the sign-in picks your account, so there is no account ID to enter here |
| **Infor M3** | Add your company's Infor M3 MCP server as a custom connector in Claude's connector settings, using the server address your Infor administrator gives you. The plugin only reads from it |

Only Autodesk Fusion is declared in this plugin's `.mcp.json`, so its address
is already set — but it still needs one action from you before it will connect:

| System | What to do |
|---|---|
| **Autodesk Fusion** | In the Fusion **desktop** app: *Preferences → General → API* → enable **Fusion MCP Server**. It runs locally on your machine and needs Fusion open with a document. If you changed the port from 27182, set `FUSION_MCP_PORT` |

### Running the morning report automatically

Chain 3 — the morning plant pulse — is built to run unattended: it asks nothing,
it is idempotent, and if last night's export did not land it still runs and says
so at the top. **What it needs from you is the trigger.** A plugin cannot wake
itself up, so schedule it: a scheduled task in Cowork (or Claude Code's own
scheduling) pointed at *"run the morning production report for yesterday."*

Saying "morning report" yourself at 6:15am produces exactly the same page. That
is a legitimate way to start, and it is still ninety minutes a supervisor gets
back. Details in `shared/scheduling.md`.

Anything else — your CMMS, MES, historian, quality system, planning tool, a
different ERP or CAD — reaches the plugin as a scheduled export into a folder
until you connect it. At the end of setup, `onboarding` reports the options for
every system you named: Limble, for example, publishes its own MCP server.
Say **"connect our CMMS"** or name the system, and `custom-connector` works out the best available path and writes the setup steps or the export
specification for your IT.

---

## What's in this repo

| Path | What it is |
|---|---|
| `skills/` | The seventeen skills — twelve atomic, five chains. Each `SKILL.md` is the entry point; detail is in each skill's `reference/` |
| `shared/` | Rules every skill links (approval gates, computed figures, replies and saved pages, live dashboards), the contracts in `shared/contracts/`, and the plant setup script in `shared/scripts/` |
| `.claude-plugin/`, `.mcp.json` | The plugin manifest and the one declared connector (Fusion) |

| | |
|---|---|
| Version | 1.0.0 |
| Skills | 17 — 12 atomic, 5 chains |
| Contracts | 11 — handoffs between skills, and the records the dashboards and the plant setup keep |
| Connectors | 1 declared in `.mcp.json` — Autodesk Fusion. Also works with Microsoft 365, Oracle NetSuite and Infor M3 once you connect them in Claude |

To run it from a local checkout: `claude --plugin-dir .`, then say "set us up".

---

## What you can say today

**Set us up**
- "Set us up" · "get started" · "configure the plugin"
- "Our shifts changed" · "we added a plant" · "reconfigure"

`onboarding` tests which systems are reachable, finds the folder your scheduled
exports land in and confirms what each file is, pins down your shift pattern and
where the production day starts, learns what your plant calls things, and hands
back a list of anything still missing with the skills it limits. Unknowns are
deferred, never blocking — "I'd have to ask" is a complete answer.

**An RFQ came in**
- "An RFQ came in" · "can we quote this?" · "should we bid this job?"
- "Read this inquiry" · "what's missing from this RFQ?"

`customer-inquiry-intake` reads the RFQ in whatever shape it arrived — a drawing
package, a 40-line spreadsheet, a portal export, a phone photo of a marked-up
print, a forwarded thread where the real requirement is four messages down — and
pulls it into one consistent form where every field says which file and page it
came from. It keeps what was never stated separate from what was stated two
different ways, because those need different things from you. Then it checks the
job against what your plant can actually build, names the specific constraint if
one fails, and recommends bid or no-bid without ever deciding for you.

**Price this job**
- "Build the quote" · "price this job" · "what should we charge?"
- "Quote this RFQ" · "the customer came back on price"

`quote-build` shows its working. Material at the price you actually paid on a
named purchase order rather than a standard cost, labor and machine time against
the routing, setup re-amortized at every quantity break so the price curve
explains itself, and margin on its own line where you can see it. It checks the
date against real shop load before committing to one, and when a customer
counters it revises the quote in place with a record of what moved and why —
rather than leaving four versions in circulation.

**When the RFQ is a drawing**, the chain builds the part in Fusion from the
drawing's dimensions, tolerances and notes, shows you the model, the tolerance
reading and the operation list for a yes, then derives setup hours and cycle
time per operation — from the CAM toolpath where your cutting data is on file,
and from the features otherwise. Every operation on the internal sheet names
where its hours came from (a current routing, closed-job actuals, the design,
or first principles), the spread, and how far two sources disagree. Actuals
that look like backflushed standards are flagged and never outrank the design.
Hours, ranges and basis labels never reach the customer's quote. Without
Fusion it still runs, a rung down the ladder, and says so. A part close to one
you already make starts from that part's model, saved as a new document so the
original is never touched; a 3D STEP file is read rather than rebuilt; and
written specs with no drawing give a budgetary estimate, never a firm quote.

**We found bad parts**
- "Write up this nonconformance" · "raise an NCR" · "we found bad parts"
- "The inspector rejected this lot" · "a customer is complaining about a part"

`ncr-writeup` writes the nonconformance against the specific requirement it
violates, cited to a document and a page rather than asserted. It reasons out
how many parts are actually suspect and shows that reasoning, places every one
of them across all five locations — including the ones nobody has checked yet,
which it will not let read as clear — and searches your prior NCRs at the moment
of writing to tell you whether this has happened before and whether the last fix
held. If any of those parts are already at a customer, it drafts the
notification against its contractual clock without being asked.

**Why did this happen?**
- "Root cause" · "why did this happen?" · "write the 8D" · "CAPA"
- "Investigate this nonconformance" · "the customer wants a corrective action report"

`root-cause-capa` puts your sensor history, inspection measurements, maintenance
records and prior tickets on one timeline — after checking that the clocks in
those systems actually agree, and refusing to draw a correlation when they
don't. It computes the control charts and the clustering rather than eyeballing
them, then gives you ranked candidate causes with the evidence against each one
as well as for it, and the cheapest test that would settle which is right. It
drafts D1 through D5 and D7 of the 8D, and leaves D6 and D8 empty because those
need something to actually have happened.

**Source this part**
- "Source this part" · "send an RFQ to suppliers" · "get quotes on this"
- "We need an alternate supplier" · "who else can make this?"

`supplier-quote-request` builds the package that goes out to suppliers and, more
usefully, tells you exactly what a complete package needed that it could not
find. It mandates the shape the bids come back in — unit price at each quantity,
tooling priced separately, lead time split — so you can actually compare them
instead of spending an afternoon normalising three different formats. It stops
outright if the drawing revision in your library disagrees with your ERP, and it
says so loudly when a part turns out to have exactly one qualified supplier.

Then it runs the loop: candidates from your approved supplier list, one draft
email per supplier for your buyer to send, a tracker that chases the quiet ones
without ever closing the event on them, each bid read into one shape with what
it left out listed, and a side-by-side comparison per quantity break with a
recommendation. It never awards. When your buyer decides, it records who and
when, and the winning price flows into the quote as a sourced outside-processing
line.

**A machine is down**
- "The machine is down" · "what's wrong with cell 3?" · "diagnose this"
- "Why does this keep failing?" · "which machines are hurting us most?"

`breakdown-diagnosis` reads the sensor window before the failure, the machine's
repair history including the notes your technicians actually wrote when they
closed those tickets, photos of what they can see, and the manufacturer's
troubleshooting tree — then ranks the likely causes with the cheapest test that
tells them apart. Safety implications always come first. It drafts the
preventive-maintenance change that would stop it happening again, and in batch
mode it ranks every machine by how much pain it is causing you.

**The morning production report**
- "Morning report" · "production report" · "how did we do yesterday?"
- "What's our OEE?" · "downtime report" · "what's late?"

`daily-production-report` builds what a supervisor otherwise spends 60 to 90
minutes assembling by hand: output against plan, OEE with its three components
shown separately, the downtime log ranked both by minutes and by how often
things stopped, scrap and downtime in dollars rather than counts, what moved
since last week, and the exceptions that need a decision today. For each
exception it drafts one specific schedule move and traces what it displaces.

Run as the morning pulse, it publishes one **Operations Command Center**
dashboard per site to your Claude artifact store on the first run and updates
that same page every run after — today's numbers, plus 14- and 30-day trends
built from the days it has stored. The NCR and 8D skills keep a **Quality
Register** dashboard the same way: every open corrective action, customer
notification clocks first. Both are private until you share them, and a run
says "updated" only when the publish actually returned.

**Pull the data together**
- "Pull the data together" · "consolidate the exports" · "build the dataset"
- "Join production to the ERP" · "why don't these numbers match?"

`data-consolidate` reads your export folder plus whatever is connected, joins it
on the identifiers you already have — part number, production work order, sales
order, lot, asset, supplier — and hands back one workbook plus a report naming
every record that did not match and what to do about it.

It works with no connector at all. Scheduled exports are the designed path, not
a fallback.

**Explore the design space**
- "Explore the design space" · "generate variants" · "run a parameter sweep"
- "Try different wall thicknesses" · "vary this and see what happens"

`design-space-explore` generates a batch of CAD variants directly in Fusion
by applying changed parameters to the model you already have
open — it never designs from scratch and it never touches the base. It
checks first whether what you want to vary actually drives the geometry,
and stops before generating anything if it doesn't. Before it runs a single
variant it shows you the resulting count and waits for a yes, because a
live CAD connection makes 3,000 variants as easily as 30. Every variant,
including the ones that failed to regenerate, comes out in the shape
`trade-study-report` will read.

**Which design should we pick?**
- "Compare these options" · "write the trade study" · "which design should we pick?"
- "Score these against the requirements" · "how sensitive is this decision to the weighting?"

`trade-study-report` turns a filled-in matrix and whatever analysis exists
into a ranked, cited comparison — never inventing a score for a cell nobody
filled in. It runs the sensitivity analysis every time, not just when
someone asks: where the winner flips, which criterion the decision actually
rests on, and whether an option never wins under any plausible weighting.
An option that fails a hard requirement is disqualified outright, not
marked down. The memo it writes names what was ruled out and why, and the
risks that are still open even in the option it recommends.

**We use a system you don't support**
- "Connect our ERP" · "we use SAP" · "can you reach our MES?"
- "Set up a connector for this" · "our system isn't supported"

`custom-connector` works down a seven-tier ladder — vendor MCP, community
MCP, a scoped API wrapper, a read-only database view, a Zapier bridge,
screen automation as a last resort, or a scheduled export — and stops at
the highest rung that actually works. Most of the time the honest answer
is that a vendor already ships an MCP quietly and nothing needs building,
just an admin turning it on; it checks that first, not last. Whatever it
reaches, it maps onto the same dataset every other skill already reads, so
nothing downstream changes. Credentials never touch the conversation, and
it tells you exactly how the connection will eventually break before it
hands it over.

---

## The skills

**Core (3):** `data-consolidate` · `onboarding` · `custom-connector`

**Sales (2):** `customer-inquiry-intake` · `quote-build`

**Quality (2):** `ncr-writeup` · `root-cause-capa`

**Supply chain (1):** `supplier-quote-request`

**Operations (2):** `breakdown-diagnosis` · `daily-production-report`

**Design (2):** `design-space-explore` · `trade-study-report`

### The five chains, all running

| Chain | Path |
|---|---|
| RFQ to quote | customer-inquiry-intake → data-consolidate → design step in Fusion → quote-build, four gates |
| Inspection to CAPA | ncr-writeup → root-cause-capa |
| Morning plant pulse *(scheduled)* | data-consolidate → daily-production-report |
| Breakdown to next report | breakdown-diagnosis → daily-production-report |
| Supplier escape to alternate source | ncr-writeup → root-cause-capa → supplier-quote-request |

Morning plant pulse is the only one with no approval gates anywhere in it —
it writes to no system of record (its dashboard lives in your own artifact
store), which is precisely why it is safe to run unattended overnight.

---

## The systems it runs on

It works with four connectors once connected: Microsoft 365 for documents, mail and the export
landing folder; Oracle NetSuite or Infor M3 for the ERP records; Autodesk
Fusion for CAD and CAM. [Getting started](#getting-started) has what each one needs.

Microsoft 365, NetSuite and Infor M3 are connectors you enable in Claude, so
the plugin declares none of them — NetSuite's and M3's addresses are specific
to your account. Infor M3 gives the plugin no standard cost, quote history or
routings; the skills say so and use their fallbacks
(`shared/erp-connectors.md`). Fusion is declared in `.mcp.json` at a local address,
because its MCP server runs inside the desktop app on your machine rather than
in the cloud.

A maintenance system, a different ERP or CAD, an MES — any of them is named
during setup and runs on exports. Where the vendor publishes an MCP server
(Limble does), `custom-connector` adds it when
you choose.

Anything else reaches the plugin as a scheduled file export, which is how most
manufacturing data moves anyway. A plant that cannot give you an API can almost
always give you a nightly CSV, because it is already producing one for somebody's
spreadsheet.

---

## How it keeps you safe

- **Nothing is applied without a yes.** Corrections to your data are proposed,
  shown, and applied only on approval. Coding a fix and applying it are two
  separate decisions.
- **No invented numbers.** A figure that cannot be read is reported as
  unreadable, never guessed. An empty result is reported as empty, never as
  zero.
- **Freshness is a headline.** If an export stopped running three weeks ago, you
  are told at the top, not in a footnote.
- **Your data stays yours.** Skills read what they need for the run and write
  only what you approve. Microsoft 365 is read-only by default, so outputs come
  back to you as files and pages you place yourself — except the two
  dashboards, which live privately in your own Claude artifact store.
