# The supplier loop — candidates, drafts, and tracking the responses

Steps 8 to 10. What happens between a released package and a pile of bids:
who gets asked, what each of them is sent, and who has not answered.

**The buyer sends every email and makes every decision.** This skill drafts,
tracks and compares. It never sends, never awards, and never decides that a
supplier who went quiet has dropped out.

---

## Step 8 — The candidate list

### Where candidates come from

1. **The `### Approved suppliers` table in `## Plant context`**, captured at
   `onboarding` (format in `../../onboarding/reference/config-profile.md`,
   *Approved suppliers*): Commodity | Approved | Notes. Find the commodity
   this part or process belongs to, and say which row you matched and why —
   *"black oxide, matched on the drawing note 'black oxide per MIL-DTL-13924'"*.
   Where two rows could match, ask which one; do not pick.
2. **ERP vendor records** (NetSuite or Infor M3, or the vendor export), for names, contacts and
   any vendor whose category fits the commodity. **A vendor found here and not
   on the approved table is listed as *not confirmed approved*.** The ERP
   holds vendors, not which are approved for what.
3. **The incumbent**, for comparison: the supplier on the current purchase
   orders. Where the trigger is a supplier-caused flag, the implicated supplier
   is the incumbent; whether to invite them back is the buyer's call, and the
   list says so rather than deciding.

### The columns

| Supplier | ID | Approval status | Basis | Requalification |
|---|---|---|---|---|
| Example Finishing | VEND-5120 | **approved, single source** | Plant context, *Black oxide* row, marked single source | none |
| Example Plating | VEND-5133 | **not confirmed approved** | NetSuite vendor, category finishing; not on the approved table | first article and a process audit before production |
| Example Metalworks | VEND-5141 | **not confirmed approved** | Same | Same |

**An approved ID that is not in the vendor records** is listed as *approved in
Plant context, not found in vendor records* — a name or a contact may be
missing, and the buyer needs to know before drafting to it.

### Single source

A commodity is single source when its row is marked so, **or when it has
exactly one approved supplier.** Flag it loudly, first, and count it in code
from the table rather than reading the note alone. The most serious version:
the only approved source is the implicated supplier. Say that before the
package.

Every count on this list — approved, not confirmed approved, single-source
commodities — goes in the figures block with the table and filter it came
from.

---

## Step 9 — One draft per supplier

**One email per supplier, addressed to that supplier only.** Never one email
with every bidder in To or CC: that hands each of them the competition's names.
The package rides along as the attachment the buyer adds; the email names it
by title and revision.

Each draft carries: the addressee, the subject with the event reference, the
package title and drawing revision, the response due date, who to send the bid
to, the technical contact, and the line that the bid must follow the mandated
format in the package.

**Emit each draft in the reply, between its own delimiters** — a copy saved
to a file does not replace it:

```
=== SUPPLIER EMAIL — SENDABLE — VEND-5133 Example Plating ===
…
=== END ===
```

**Then read each block alone and reject it if it holds** any other supplier's
name, any unit price, PO number or total from purchase-order history, a target
price, any rate from an `MFG_*` variable or the plant profile, or anything
about other bids. Per `../../../shared/secret-config.md`, *The outbound
document check* — the same check as the package, applied to every email.

### Held drafts are labelled HELD

A draft is **held** when any of these is true for it:
no contact address on file for that supplier, no response due date in the
released package, the drawing revision not verified, or the supplier not
confirmed approved for the process with no requalification decision from the
buyer. A held draft is emitted the same way, through the same outbound check,
under `=== SUPPLIER EMAIL — HELD — <supplier> ===`; chase and restatement
drafts likewise (`SUPPLIER CHASE — HELD`). **HELD is for supplier emails
only: the RFQ package always stays `=== SUPPLIER RFQ PACKAGE — SENDABLE ===`**,
since the buyer releases it at its own gate and its missing items are listed
outside it. **`SENDABLE` on an email is used only when nothing holds the
draft**; it means ready for the buyer to send, never that
anything was sent. A missing address is a placeholder,
`[recipient: not on file]`, never an invented one.

**A condition that holds every draft is stated once**, as a notice
above the drafts: *"Held, all three drafts: no contact email on file; no
response date in the package."* Each draft then gets one short status line
above its block: *"Held: the shared conditions above"*, plus any condition
that is that supplier's alone (*"and Example Plating is not confirmed approved for
black oxide"*). A supplier-specific condition sits only beside the drafts it
affects and never in the shared notice. Moving a condition into the notice
never makes a draft look cleared: every held draft still says it is held.

### The send gate

The buyer sends. **"Send them out" gets the drafts, and a plain sentence that
nothing was sent:** *"Here are the three drafts. I haven't sent anything —
send each from your own mailbox."* No send tool is called, M365 is read-only,
and the reply never says *sent*, *issued*, *went out* or *delivered* about an
email the buyer has not told you they sent. Per
`../../../shared/approval-gates.md`, *Supplier send and selection*.

**A yes covers the drafts shown, to the suppliers shown.** A supplier added
later gets its own draft, shown before anything about it is recorded.

**Sent is recorded only when the buyer says so** — *"sent to Example Plating and
Example Finishing this morning"* — with the date they gave and their words. The first
such date is `rfq_issued_at`, which closes Chain 5's handoff segment.

---

## Step 10 — Tracking responses

### Where the state lives between runs

**In the `## Sourcing events` block on the Open work page, written without a
gate** (`../../../shared/replies.md`, *The open work*), so a new chat with no
project finds the event's whole history: who was asked, when the buyer said it
was sent, who responded, who was chased, the decision. It is the buyer's own
working record, not plant configuration, so, like the `## Dashboards` line, it
does not go through `onboarding`'s two-turn approval. One `###` per event,
replaced in place with `put --block "Sourcing events" --entry <event id>`;
every other block and file on the page stays as it was.

**Each bid ingested at step 11 is saved on the same page** as
`sourcing/<event-id>/<supplier-slug>.bid.txt` (the record per
`../../../shared/contracts/supplier-bid.md`, not the supplier's PDF or email;
`source_ref` already points back to the original), and the Response cell
points to that path.

```
## Sourcing events
### SRC-2026-10-14-PN-4471-B-BO — black oxide, PN-4471-B Rev 2 (Fairview)
Trigger: quote EH-RFQ-0912 line 1 | Breaks: 50, 200 each | Due: 2026-10-28 | Status: open
| Supplier | Approval | Drafted | Sent (per buyer) | Due | Response | Chased |
|---|---|---|---|---|---|---|
| VEND-5120 Example Finishing | approved, single source | 2026-10-14 | 2026-10-14 | 2026-10-28 | bid 2026-10-22, sourcing/SRC-2026-10-14-PN-4471-B-BO/example-finishing.bid.txt | - |
| VEND-5141 Example Metalworks | not confirmed approved | 2026-10-14 | 2026-10-14 | 2026-10-28 | none | - |
```

**Every run also prints the table in its output**, saved or not. **If the page
cannot be written this session, say so in one line**: *"Not saved: your Open
work page couldn't be written ([reason]). Paste this table back next time and
I'll pick up from it."* Never say the event is being tracked. With no stored block and no pasted table, ask which
suppliers were sent what and when; never reconstruct a send history.

### Statuses

| Status | Means |
|---|---|
| `drafted` | A draft was shown. Not sent, as far as this skill knows |
| `sent` | The buyer said they sent it, on the date they gave |
| `responded` | A bid is ingested (step 11), with its source |
| `declined` | The supplier said, in writing, that they will not bid. Cite it |
| `no response` | Past the due date with nothing received. **Not declined** |
| `extended` | The buyer gave this supplier a new due date. Record both dates |

**Days past due are computed in code** from today's date and the due date, and
go in the figures block. A supplier never moves to `declined` because they went
quiet, and nothing is inferred from a search that found no reply: with M365
connected, the inbox may be searched read-only for the event reference, and a
miss is *no reply found by search*.

### Never close on silence

**The event stays open until the buyer closes it or records a decision.** A
quiet supplier does not end it, a due date passing does not end it, and most of
the bids arriving does not end it. The run says how many responded out of how
many sent, computed, and names who has not.

The comparison may run on the bids in hand. When a supplier has not responded,
it says so on the comparison — *"2 of 3 bids; Example Metalworks has not responded, 6 days
past the 28 Oct due date"* — and the decision stays the buyer's, including
whether to wait.

### Chase drafts

For each supplier past due, draft a chase, for the buyer to send:

```
=== SUPPLIER CHASE — SENDABLE — VEND-5141 Example Metalworks ===
…
=== END ===
```

It restates the event reference, the package, the original due date and a new
date the buyer chooses (ask, or leave it as a blank for them to fill). **It says
nothing about the other bids — not even that there are any: no other
supplier's name, no price, no count of bids received, no "you are the last to
respond", no "we will decide with the bids we have", no "this is
competitive".** The deadline and the package are the only pressure in it. A buyer who asks to tell the
supplier where a competitor landed gets the draft without it, and one sentence
why — a competitor's price in a chase is the incumbent's-price leak in another
envelope. The same outbound check runs on every chase block.

Record the chase as drafted. Record it as chased only when the buyer says they
sent it.
