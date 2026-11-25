# Step 2 — Bulk document intake

The plant almost always has the answers to half the interview already, in
documents nobody thought to hand over. This step asks for them up front, reads
them, and turns the interview that follows into *confirm or correct*.

It runs **after** Step 1 on purpose: once the live connectors are known, the
list never asks for a document a connector already covers. Nobody uploads a part
master when the ERP (NetSuite or Infor M3) is connected.

---

## The prompt

Name the exact documents, grouped. Tag every line a live connector covers with
`(skip — <system> is connected)`, generated per line from Step 1's results —
never a fixed list.

> "Drop in whatever you have from this list — any count, any format. I'll read
> through them and only ask what they don't answer.
>
> **Production and maintenance data**
> - MES or production export (jobs, work orders, cycle times, downtime)
> - Maintenance history / work-order dump from your CMMS
> - Asset or equipment register (machines, work centers, cells)
> - Historian or sensor export, if you have one
>
> **Quality**
> - A recent NCR
> - A recent 8D or corrective action report
> - Inspection records or FAI reports
> - Quality manual, or your ISO / AS9100 / IATF certificate
>
> **Quoting and commercial**
> - A recent quote you sent a customer
> - Your supplier RFQ package, if you have a standard one
> - Standard supplier quality clauses and commercial terms
> - A trade study or design memo, if you've done one
>
> **Plant setup**
> - Shift calendar or shift pattern
> - Part master / routing export *(skip — NetSuite is connected)*
> - Machine classes, setup times or cutting data, if you keep them
> - Approved supplier list
>
> Anything else you think is relevant is fine too."

Which lines get the skip tag:

| Line | Skipped when |
|---|---|
| Part master / routing export | NetSuite is live. With Infor M3 live, only the part master is skipped: M3 gives this plugin no routings, so the routing export is still asked for |
| Approved supplier list | Never skipped — the ERP holds vendors, not which are approved for what |
| Maintenance history | A CMMS connector is live (`live (custom)`) |
| Anything in Microsoft 365 | Never skipped — the connector reads documents, it does not know which one is the template |

**Skippable, and re-runnable.** "I don't have any of that" ends the step and
every later question is asked directly. "Here's more" later re-runs this step
over the new files only.

---

## Classify first, deep-read second

**The first pass reads only a header row or a first page.** It decides what
each file is and where it routes. Only a file that routes to a step is read in
full, and only for what that step needs. A quality manual is not read cover to
cover to find a certificate date.

| File looks like | Routes to | Mined |
|---|---|---|
| Tabular export | Step 3 | Source identity, cadence, timezone hints, shift times |
| Asset / equipment register | Step 3 and Step 7 | Assets, work centers, cells → vocabulary and machine classes |
| Routing or cycle-time export | Step 7 | Setup hours and cycle times by work center, as candidate machining data |
| Quote / estimate | Step 9 and Step 10 | Quote layout; labor, burden and margin if stated |
| NCR, 8D, trade memo, RFQ package | Step 9 | Template structure |
| Quality manual / certificate | Step 8 and Step 7 | Standards and revisions, certificate expiry, processes |
| Clause list / T&Cs | Step 8 | Supplier clauses, commercial terms |
| Approved supplier list | Step 8 | Approved suppliers by commodity |
| Shift calendar / HR doc | Step 4 | Shift pattern; day-boundary hint only |
| Unidentifiable | Gaps list | Named; asked about in one line |

---

## Guardrails

1. **Mined is not confirmed.** Every value read from a file is inferred until
   the user says yes to it in the step it routes to, and is **shown labelled
   that way** — *"three shifts, 07:00 / 15:00 / 23:00 (inferred, from
   Fairview-shift-calendar-2026.txt)"*. A table of what each file gave carries
   an *inferred* column or label; a bare value reads as settled. The question becomes
   *confirm or correct*, with the source file named: *"Your shift calendar
   shows three shifts starting 07:00, 15:00 and 23:00 — is that still right?"*
   **The production-day boundary is asked directly in Step 4 regardless** —
   a calendar shows when shifts start, not which day the 23:00 shift's output
   belongs to.
2. **A file-sourced rate follows Step 10.** It goes into the approval draft's
   internal rates section, shown once, with the file name as its source —
   *"labor rate 71.00/hr, from Q-2026-0412 quote.xlsx"* — and is written as
   confirmed only on a yes, with the name of the person who said yes. It is
   never restated anywhere else, including the setup summary's line for that
   file.
3. **No vocabulary or capability from a single document.** One quote that says
   "tolerance ±0.0005" is not a demonstrated capability. Two consistent
   sources, or ask.
4. **A file that contradicts the user loses, and is named.** The user's answer
   is recorded; the contradiction is stated once with the file, so a stale
   document gets found.
5. **Nothing from a file is acted on before Step 11's yes.** Mining is
   reading; the profile is written once, after approval, like everything else.

---

## What the setup summary says about files

One line per file: what it was identified as, which step it fed, and what it
supplied — *"`Fairview shifts 2026.pdf` — shift calendar; supplied the three
shift start times (confirmed)."* A file that supplied a rate says *"supplied
commercial rates (see the approval draft)"*, never the value. An unidentified
file is listed as unidentified.
