# Command-center pages — what they are, and what they are not

Every chain carries a `Command center:` line naming the page a run
feeds — Sales, Quality, Operations, Supply Chain. This file defines the shape
once, so five skills do not each invent one.

It exists because they were each inventing one, and inventing the same
contradiction: "updates open corrective actions," "updates the maintenance
panel," "attaches the NCR and the 8D." Read literally, those are writes into an
external system. The plugin's own binding rule says otherwise:

> **Microsoft 365 is read-only by default.** Write access is an admin opt-in and
> Teams has no write path at all. No skill may assume it can post a message or
> write a file back into M365.
> — `artifact-style.md`

Both statements cannot be true. This one wins, because it is the platform
constraint rather than a preference.

---

## What a command-center page actually is

**Two kinds, and a skill always knows which one it produced.**

**A live dashboard**, for Operations and Quality. Published to the user's
Claude artifact store on the first run and updated in place at the same URL on
every later run, per `live-dashboard.md`. The artifact store is the user's own
Claude account, not M365 and not a system of record, so publishing to it does
not break the rule above.

**An offered page**, for Sales and Supply Chain, and for Operations or Quality
whenever the dashboard could not be published this run. An artifact produced
in the conversation that the user places: a page they open, read, and save or
forward, written as **a replacement for the last one**, carrying the same
sections in the same order, so a person can put it where the previous version
lived and read the delta at a glance. The plugin does not put it there.

**"Updated" is allowed only after a successful publish.** A skill may say it
updated a dashboard only when the publish call returned a URL in this same
run. Everywhere else the page was *offered*, and the skill says so. Reporting a
panel as updated when a page was offered is the false statement this file was
written to stop, and it still is.

**The dashboard is private until the user shares it.** No skill shares it, and
no skill says it is shared.

## The four pages

| Page | Fed by | Carries |
|---|---|---|
| **Sales** | Chain 1, at quote release | Commercial performance for the period, with the intake record and the quote attached to the run |
| **Quality** | Chain 2, and Chain 5's quality half | Open corrective actions, with the NCR and the 8D by reference. **A live dashboard, the Quality Register**, written by `ncr-writeup` and `root-cause-capa` |
| **Operations** | Chain 3 nightly, Chain 4 on a breakdown | The morning numbers, the downtime log, exceptions, and the maintenance picture. **A live dashboard, published by Chain 3 only.** Chain 4, and `daily-production-report` run alone, offer the page in the conversation; two pages showing the same numbers is how a meeting ends up arguing about which is right |
| **Supply Chain** | Chain 5's sourcing half | The supplier signal and the sourcing package |

Chain 5 produces **two pages from one run** — Quality takes the corrective
action record, Supply Chain takes the supplier signal. They are separate
artifacts with separate audiences, not one page with two sections.

## The rules

**Say what actually happened.** *"Updated **Fairview: Operations Command
Center**, `<url>`. Private to you until you share it"* is honest when the
publish returned that URL in this run. *"Here is the Operations page for
8 September; save it over yesterday's"* is honest when it did not. *"Updated
the Operations command center"* with no URL behind it is not, and a plant
person who believes it will stop checking.

**Every command-center page ends with one of two lines**, not only the first
page in a run:

- **Published:** the dashboard line, with its name and URL.
- **Offered:** the placement line, *"save it over yesterday's"*, or where the
  last one lives. **A page that should have been a dashboard and was not also
  says so:** *"The dashboard was not updated: [reason]."* That fallback never
  stalls the run, and never offers to publish later.

Chain 5 produces two pages; both end that way.

**When asked to do something the plugin never does, hand over the content and
say who acts.** Post to a channel, send the mail, close the ticket, update the
record: give the ready-to-use text, and say plainly that the user performs the
action. *"I don't post to Teams. Here's the text to paste."* **Never offer to
do it "once X is confirmed"** — *"confirm the channel and I will post exactly
this"* promises a capability that does not exist, and the person waits for a
post that never comes. Where the right content is a draft — a close-out note,
a channel message — produce it, labelled as a draft, rather than only saying
it cannot be filed.

**Say what was actually checked, by the call that checked it.** *"I searched
the public MCP registry"* when that is the call that ran. Not *"I checked your
connector directory"* and not *"three connectors are installed on this
account"* unless the account's own listing was queried in this run. A search of
one place reported as a check of another is a false statement about the user's
own systems, and it is the kind they act on.

**Attachments are references, not uploads.** "Attaches the NCR" means the page
carries the NCR's identifier and enough of it to be useful, so a reader can find
the full record. Nothing is uploaded anywhere.

**Sensitive values follow the audience rule.** A Sales page shown to a customer
carries no margin line; the internal one may. See `secret-config.md`.

**Absent is not zero.** A section with no data says so — *"no open corrective
actions in this window"* is different from an empty heading, and different again
from *"we could not read the quality library."* See `absent-is-not-zero.md`.

**House style applies.** Pages render per `artifact-style.md`, except a
controlled document, which keeps the plant's own template.

## If a plant does have a real dashboard

Some plants keep a genuine command-center page in SharePoint or a BI tool. The
plugin still does not write to it. The live dashboards in `live-dashboard.md`
are the plugin's own pages in the user's Claude account; they sit beside a
SharePoint or BI dashboard and never write into one. It produces the page content and the person
pastes it, and where a write path is ever genuinely wanted, that is a
`custom-connector` conversation with an approval gate on the write — not an
assumption a skill makes on its own.
