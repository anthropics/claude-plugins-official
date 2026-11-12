# What a reply holds — documents, records, memory and names

**Shared across every skill.** Four rules about what goes in front of the
person and where things are kept.

---

## Documents are printed in full; records are summarised

A **document** is what a person reads, signs or sends: the quote, the cost
sheet, the NCR, the 8D, the RFQ package, an email draft, the morning report,
the intake form. **It is printed in the reply, in full.** Saving a copy to a
file as well is fine; a file *instead of* the reply is not. The person reads
the reply, and every delimited block and outbound check lives in it.

### Reports are the exception: a short reply when the page was written

The morning report, the Operations page and the supplier bid comparison are
read on a page, not in the chat. For
the bid comparison the headline is the provisional recommendation and its main
tradeoff, the exceptions are the requirements still open before an award, and
the decision waiting is the next-step question. **When this run wrote the full page
somewhere the person can open** (a publish returned its URL, or the page was
saved as an HTML file and the reply names the file), the reply is a summary
of about 150 words. **200 words is a hard limit: count before sending.** Each
item below is one sentence; an exception or a decision is the thing and its
number, with the explanation left on the page.

1. Safety first, one line per item: a safety-flagged record, a record under
   *"Blocked — safety status unknown"*, or *"Safety status: not assessed"*.
2. The site, the production day, and the freshness state in one line: data
   complete, or the gap.
3. The headline: good output against plan, and OEE or why it is not computed.
4. Up to three exceptions, one line each.
5. The decisions waiting today, or *"No decisions waiting today."*
6. Where the full page is: the URL or the file path.

No tables, logs or methods in the summary; they are on the page. Every
number in the summary is one the page prints. **This is for the whole
report only.** A request that picks sections or skips some ("freshness and
the rankings, skip OEE this time"), a question, a record the person asked to
see, or text to paste is answered in the reply in full, in report order, as
always; the page may still be saved as well. **When nothing could be written**
(no file writer and no publish), the page is printed in the reply in full, as
above. Where a skill offers "the page in the conversation", a saved file named
in the reply is that offer. Documents someone signs or sends (quotes, NCRs,
8Ds, RFQ packages, email drafts) are always printed in full.

### Saved copies: Word for documents, Excel for tables, never .txt

When a document is also saved as a file, and it should be wherever the person
downloads from a file card (Cowork), the file is one a plant opens without
thinking about it:

| What it is | File |
|---|---|
| A controlled document: customer quote, supplier RFQ package, NCR, escape notification, 8D, trade study memo | `.docx` |
| A table someone works in: internal cost sheet, bid comparison, ranked candidates, scrap or downtime lists | `.xlsx` |
| A report or dashboard | the HTML page, per `artifact-style.md` |
| A record (contract payload, day record, register row) | its contract's format, as below |

**Never `.txt` or `.md` for a document.** A plain-text quote reads as a draft
nobody finished, and it is what a person gets when no format is named.

- **How.** Use the session's Word or Excel skill where there is one (Cowork
  has both); else `python-docx` or `openpyxl` where already installed. Never
  install a package for it and never hand-build the file's XML: a file Word
  cannot open is worse than none. With no writer, write no file and say so in
  one line: *"No Word copy this session: no Word writer available."* The
  reply already holds the document.
- **The plant's template.** A controlled document keeps the structure
  `onboarding` captured. Where that example is a `.docx` in the documents
  folder, start the Word copy from that file; otherwise use a plain layout
  and keep the *template not on file* flag the document already carries.
- **What goes in which file.** The customer's file holds only what the
  sendable block holds. Internal figures (hours, rates, margin, the cost
  build-up) go in their own file, the internal cost sheet, and never into the
  customer's.
- **Names.** What it is and its reference: `quote-Q-EXAMPLE-MEDICAL-4402A-01.docx`,
  `cost-sheet-Q-EXAMPLE-MEDICAL-4402A-01.xlsx`, `NCR-2026-0141.docx`. Name each file in
  the reply.

A **record** is a handoff to another skill or a store: a contract payload (a
downtime record, a geometry estimate), a register row, a pulse day record, a
supplier bid record, a selection record, a sourcing-event row. **It is never
pasted into the reply as a raw YAML or JSON block.** A quality manager, a
buyer or an estimator should not have to read 150 lines of field names to
find out what happened.

Instead:

1. **Save the full record** where its contract says, or to a file next to the
   run's other outputs, and **name the file** in the reply.
2. **Show a short table of the fields a person decides on**, under their
   contract names so nothing is lost in translation — the key, the status,
   and whichever of these the record has: `fields_missing`, `data_complete`,
   `decided_by`, `decided_at`, `follows_recommendation`, `actuals_confidence`,
   `geometry_path`, `reading_basis`, `approval`. One row per record, or one
   row per field for a single record. Never more than about a dozen rows.
3. **If the record cannot be saved** (no write access this session), print it
   in full, **as a table, not a code block**, marked *not stored — paste this
   back next time*.

The person can always ask for the raw record ("show me the YAML"). Then print
it.

## Where the plant's memory lives

### The plant setup, the rates and the open work: three private pages

The plant profile and the plant's rates are written once, by `onboarding`, and
every later run finds them with no folder, no project and nothing to upload.
**Every skill that reads the profile or a rate first runs, from the task's own
folder (never from inside the plugin's folder, which the script refuses)**

    python3 -I <this skill's folder>/../../shared/scripts/plant_setup.py find

**and does its `setup_page_first` step before anything else.** That step lists
the user's artifacts for two private pages and brings them into the task:

| Page | File | Holds |
|---|---|---|
| `Plant setup: <company>` | `setup/plant-context.txt` | The `## Plant context` block. No rate values, so it can be shared with teammates |
| `Plant rates: <company>` | `setup/plant-rates.txt` | The `## Plant rates` block: each rate's value, state, who gave it and when. Its readable view shows states only. It stays private |
| `Open work: <company>` | `setup/open-work.txt`, plus `inquiries/` and `sourcing/` | The three working blocks, the paused intake forms and the bid records. Its readable view shows references and states, never a price. Private |

The pages are read and published with the artifact tools: `Artifact` in
Claude Code, `mcp__claude-artifacts__*` in Cowork. Either counts. An older page
may hold the same file as `.md` (`setup/plant-context.md`,
`setup/plant-rates.md`); read that when the `.txt` file is not there.

Then read the profile at `profile_path` and any rate at `rates_path`. **No page
and no file at `profile_path`:** read the `## Plant context` block from
`CLAUDE.local.md` (Claude Code) or the project's memory (Cowork); that is an
older profile. No
artifact tools, or a call to them refused: use the files as printed and say
nothing about a page.

**Saving** (onboarding's yes, or a value written back later): write the files
at `profile_path` and `rates_path`, then follow `install`'s
`after_any_change`, or for a first save: `render` each file (`--kind rates` for
the rates file), read the page itself before publishing when it already exists,
publish with the `file_path` and `files` printed, read the file back, and give
`saved`'s line word for word. `"yes, folder only"` skips the pages; in Cowork
the files then last only for this task, so say so. A rate value never goes in
the setup file: `render` refuses it.

### The open work: `Open work: <company>`

Three blocks persist between conversations: `## Dashboards` (the dashboard
URLs, `live-dashboard.md`), `## Open inquiries` (one line per paused RFQ,
`contracts/intake-form.md`) and `## Sourcing events` (the supplier tracker,
`supplier-quote-request`). With them go the files they point to: each paused
intake form (`inquiries/<customer-slug>-<rfq_reference>.intake.txt`) and each
ingested bid record and selection record
(`sourcing/<event-id>/<supplier-slug>.bid.txt`, `decision.txt`). All of it
lives on the third private page, **in Claude Code and in Cowork alike**
whenever the artifact tools exist, so a new chat with no project and nothing
attached picks up where the last one stopped. The headings are unchanged; a
paused line closed out (quoted, declined, withdrawn; an event decided and
closed by the buyer) moves to `## Closed` with its date, and its files are
dropped 90 days later. A Closed line reads `- <reference> | <state> <close
date>`: the close date is the first date after the reference.

**Finding it**, in this order, every time a skill reads or writes one of the
three blocks:

1. **The page.** `find`'s `setup_page_first` step brings it in when it exists:
   `install --kind work`, then the blocks are at `work_path` and the files
   beside it.
2. **An older block**: no page, but a block kept in memory
   (`CLAUDE.local.md` in Claude Code, the project's memory in Cowork).
   Read it. On this skill's next write, move it: `migrate --from <that file>
   --company <company>`, publish, check `saved`, then say *"Moved your open
   RFQs and supplier tracker to your Open work page. The old copy in [where]
   is untouched; you can delete it."* Never delete or keep writing to the old
   copy. A line whose intake file cannot be found keeps `file: missing`; ask
   for the RFQ when it is resumed.
3. **A table the person pastes**, as before. Never reconstruct a send history.
4. **Nothing found**: ask, as before.

**More than one `Plant setup:` page and no company named: ask which plant
before reading any page.** A company's open work is the page titled exactly
`Open work: <company>`, the same company string as its setup page. Never merge
two companies' open work. No setup page at all: create the Open work page
anyway, titled from the company the person names; if they name none, ask.
Never "unnamed plant".

**Writing** needs no approval gate: it is the person's working record, not
plant configuration, and the gates inside each workflow are unchanged.
Change one block, or one entry in it, with

    python3 -I <this skill's folder>/../../shared/scripts/plant_setup.py put --block "<block>" --entry <reference or event id> --text-file <file holding the new text> [--company "<company>"] --by <skill>

(`--remove` drops the entry). Every other block and every other file is left
byte for byte. Write an intake form or bid record as a `.txt` file at the path
its line names, under `work_path`'s folder. Then save the page in the same
turn: `put` prints `after_any_change` (prune, render, read the page just before
publishing, publish, read every file back, `saved`). A first save publishes
without a URL, titled as `render` prints. If the publish is refused because a
newer version exists, re-read it, `install` it, re-run only this run's `put`
and publish again; never force; after two refusals stop and print the block,
marked not saved.

**The skill's own result is what opens, never a memory page.** The person
sees the artifact published last. When a run publishes its own result (a
dashboard, a register, a report page) and also saves one of the three pages,
save the page first and publish the result last. Where the order can't be kept
(a first run that needs the result's URL for `## Dashboards`), finish by opening
the result (`Artifact` action `open` with its URL, or the same call in
`mcp__claude-artifacts__*`) and end the reply with the result's link. Never end
on the setup, rates or Open work page unless saving it was the whole request.

**Say "saved to your Open work page" only after `saved` returned `ok: true` in
this run.** Otherwise print the block (and the form) in the reply, marked
*Not saved to your Open work page: [reason]*. Example: *"Saved the sourcing
tracker to your Open work page."*

**No artifact tools, or a call refused:** write the blocks to `CLAUDE.local.md`
at the workspace root (Claude Code) and the files to `plant-setup/open-work/`
beside the task, and say once that they last only as long as that folder. If
the workspace is a git repository and `CLAUDE.local.md` is not ignored, add it
to `.gitignore` and say so. **Never** in the export folder, a shared or synced
folder, or a file a repository commits.

## Who said yes is asked, never inferred

An approval, a decision, a confirmed rate or a selection record carries **the
name the person gave**. It is never taken from the session account, an email
address, git config, the operating-system user, or a file's metadata — the
person at the keyboard is often not the person whose name belongs on a quote
release or a supplier award.

If the name has not been given in the conversation, **ask once**, in the same
turn as the request for the yes: *"Who should I record as approving this?"*
If they decline, record `not given` and say so. Never fill it in.

## A system the profile lists as file-based is not "waiting to be connected"

When the `### Systems` section says a system is `file`, that is the plant's
decision, recorded at onboarding. A skill working from that system's exports
says so — *"NetSuite: from the export, per your profile"* — and does **not**
tell the person it "needs authorising" or give connector setup steps, unless
they ask how to connect it. Where data a connector would have supplied is
missing, name the export or document that would supply it.

A system the profile lists as `live` that turns out not to be live this
session is different: say it is not live right now, and give its setup row
from `../skills/custom-connector/reference/known-systems.md`, word for word.
