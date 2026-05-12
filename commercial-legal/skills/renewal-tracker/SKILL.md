---
name: renewal-tracker
description: >
  Show contracts with cancel-by deadlines coming up and warn before notice windows
  close, working from a maintained renewal register. Use when the user asks "what's
  renewing soon", "what renewals are due", "did we miss a cancellation window", "add
  this to the renewal tracker", or on a scheduled basis. Receives handoffs from
  saas-msa-review.
argument-hint: "[--days N to change window | --missed for lapsed windows]"
---

# /renewal-tracker

Surfaces what's renewing and when you have to cancel by.

## Instructions

1. **Read `~/.claude/plugins/config/claude-for-legal/commercial-legal/renewal-register.yaml`** (the config directory — survives plugin updates).

2. **Default mode:** Mode 2 — what's coming up in the next 90 days, grouped by urgency using half-open intervals so each deadline lands in exactly one band: 🔴 0–13 days, 🟠 14–44 days, 🟡 45–89 days. Days 14, 45, and 90 are boundaries — each belongs to exactly one band, not two.

3. **`--days N`:** Change the window.

4. **`--missed`:** Mode 4 — cancel-by deadlines that passed without recorded cancellation.

5. **If register is empty and the [CLM] is connected:** Offer Mode 3 — scan the [CLM] for active agreements with renewal dates and bulk-load.

6. **Output includes recommended actions:** who to ping (the business owner from each register entry), which ones have uncapped pricing (get leverage before window closes).

## Examples

```
/commercial-legal:renewal-tracker
```

```
/commercial-legal:renewal-tracker --days 180
```

```
/commercial-legal:renewal-tracker --missed
```

---

## Purpose

Nobody reads a contract twice. The renewal date is extracted once, at review time, and then it lives somewhere — ideally somewhere that shouts at you 45 days before the cancel-by deadline, not 45 days after.

This skill maintains the renewal register and surfaces what's coming.

## The register

Lives at `~/.claude/plugins/config/claude-for-legal/commercial-legal/renewal-register.yaml` (the config directory — survives plugin updates). Each entry:

```yaml
- counterparty: "Acme SaaS Inc."
  agreement: "Acme Platform Subscription Agreement"
  signed_date: 2025-06-15
  initial_term_end: 2026-06-15
  current_term_end: 2026-06-15     # rolls forward after each auto-renewal; compute cancel_by_* from this
  renewal_mechanism: "auto-renew annual"
  notice_period_days: 60
  notice_method: "email"           # email / portal / certified mail / registered post / courier / per contract §X
  transit_buffer_days: 0           # 0 for electronic, 5 for domestic certified mail, 10 for international registered post — or per contract if specified
  cancel_by_calendar: 2026-04-16    # current_term_end minus notice_period_days
  cancel_by_effective: 2026-04-16   # rolled back to last business day if needed
  send_by_effective: 2026-04-16    # cancel_by_effective minus transit_buffer_days — the date you must SEND the notice
  cancel_by_roll_note: ""           # e.g., "rolled back from Sunday 2026-11-01; verify against contract's business-day definition"
  cancel_by_provenance: "[model calculation — verify against the notice clause]"
  price_on_renewal: "then-current list (uncapped)"
  annual_value: 48000
  business_owner: "jane@company.com"
  clm_id:        "IC-12345"        # if connected
  docusign_envelope: "abc-123"   # if connected
  status: "active"               # active | cancelled | renewed | lapsed
  notes: "Pricing uncapped — revisit before renewal. Alt vendors: X, Y."
```

**Notice transit time — alert off `send_by_effective`, not `cancel_by_effective`.** A 60-day window with a certified-mail requirement is really ~55 days. The tracker that alerts on the received-by date is the tracker that misses the deadline. Compute `send_by_effective = cancel_by_effective - transit_buffer_days` and fire alerts (the 🔴 / 🟠 / 🟡 urgency bands in Mode 2) off `send_by_effective`. Mode 2's urgency column shows `send_by_effective`; a detail column surfaces `cancel_by_effective`, `notice_method`, and `transit_buffer_days` so the reader can see the delta and challenge the buffer.

**Rolling renewals — the register that doesn't roll forward is the register that's right once.** Store `initial_term_end` for the record, but compute `cancel_by_*` from `current_term_end`. When a renewal fires (the cancel window passes and no notice was given), prompt:

> This contract auto-renewed on [date]. Update the register: new `current_term_end` is [date + renewal period], new `cancel_by_effective` is [computed], new `send_by_effective` is [computed]. Confirm?

After year one, `initial_term_end` is wrong and only `current_term_end` produces a correct cancel-by date.

## Business-day check on every cancel-by date

**The register's cancel-by date must be the last BUSINESS DAY on which notice
is effective, not the calendar date.** A calendar date that falls on a
weekend is the single most common way a renewal deadline gets missed. The
register catches it.

When you compute (or ingest) a cancel-by date:

1. **Compute the calendar date.** `cancel_by_calendar = initial_term_end − notice_period_days` (or whatever the clause specifies). This is the raw arithmetic.
2. **Business-day roll-back keyed to governing law.** The contract's governing law determines which holidays count. US: federal holidays + the state's holidays if governing law is a state. England & Wales: bank holidays. Germany: Feiertage (vary by Bundesland — ask which). Canada: federal + provincial. Singapore: public holidays. If Saturday, roll back to Friday. If Sunday, roll back to Friday. If a holiday in the governing-law jurisdiction, roll back to the prior business day. Roll BACK, never forward — forward means notice arrives after the window closes. For non-US governing law, if you can't determine the holiday calendar, flag it: "Governing law is [X] — business-day roll-back uses US federal holidays as a placeholder. Verify against the [jurisdiction] holiday calendar before relying on the effective date."
3. **Check the contract's own day-counting rule.** Look for "business day," "received by," "deemed received," "5:00 p.m. [local time]," or a notice-method clause. If the contract defines "business day" or specifies receipt mechanics (certified mail, email with read receipt), that definition controls. Flag any mismatch between the default roll-back and the contract's own rule.
4. **Record BOTH dates in the register.** `cancel_by_calendar` is the raw arithmetic; `cancel_by_effective` is the last business day on which notice is effective; `cancel_by_roll_note` records why they differ (e.g., "rolled back from Sunday 2026-11-01; verify against contract's business-day definition"). Every computed `cancel_by_effective` carries a `cancel_by_provenance` tag of `[model calculation — verify against the notice clause]` so the verify flag travels with the date, not with the surrounding prose.
5. **Fire alerts off the EFFECTIVE date, not the calendar date.** Urgency bands (🔴 / 🟠 / 🟡 in Mode 2) use `cancel_by_effective`. Mode 2 output shows `cancel_by_effective` in the urgency column and surfaces `cancel_by_calendar` and `cancel_by_roll_note` in a detail column where the roll-back happened, so the reader can see it and challenge it.

A Mode 2 report that prints `cancel_by: 2026-11-01` (a Sunday) with no weekday and no warning is a silently wrong effective deadline. The register is the place to catch it — once, at ingest — not later, when the window has already moved.

## Modes

### Mode 1: Ingest a renewal (handoff from review)

When saas-msa-review or vendor-agreement-review finds a renewal clause, it hands off a record. Append it to the register. If the counterparty already has an entry, ask whether this is a replacement (renewed agreement) or an additional agreement.

### Mode 2: What's coming up

**Default lookback window:** next 90 days.

**Urgency bands are half-open intervals — a deadline lives in exactly one band.** Use days-until-cancel-by (`cancel_by_effective - today`). Day 14, 45, and 90 each belong to exactly one band, not two; an off-by-one here puts the most-urgent items into the less-urgent bucket.

- 🔴 **0–13 days** (cancel-by in less than 14 days — including today)
- 🟠 **14–44 days**
- 🟡 **45–89 days**
- (everything 90+ days is outside the default lookback window; include only if the user passed `--horizon` beyond 90)

```markdown
## Renewals — next 90 days

### 🔴 Cancel-by deadline in 0–13 days

| Counterparty | Cancel by | Renewal date | Annual $ | Owner | Notes |
|---|---|---|---|---|---|
| [name] | **[date]** | [date] | $[n] | [email] | [notes] |

### 🟠 Cancel-by deadline in 14–44 days

[same table]

### 🟡 Cancel-by deadline in 45–89 days

[same table]

---

**Recommended actions:**
- [ ] [Counterparty] — ping [business owner]: do we want to keep this?
- [ ] [Counterparty] — pricing is uncapped; get a quote from an alternative before we lose leverage
```

If the register has more than ~10 renewals in the window, or any time the user asks: offer the dashboard (see CLAUDE.md `## Outputs → Dashboard offer for data-heavy outputs`). Shape the offer for this output — counts by urgency tier (🔴 / 🟠 / 🟡), a cancel-by timeline, and a sortable register with counterparty, renewal date, annual $, and owner.

### Mode 3: Scan the [CLM] / e-signature tool to populate the register

If MCPs are connected and the register is empty or stale:

1. Query the [CLM] for all agreements with status "Active" and a renewal date field
2. Query DocuSign for completed envelopes in the last 24 months with "subscription" / "renewal" / "auto-renew" in metadata
3. For each hit, extract renewal mechanics and add to register
4. Flag any where the renewal date can't be determined from metadata — those need a human to read the contract

This is a one-time bulk load. After that, ingest happens at review time.

### Mode 4: Missed windows (the bad news report)

```markdown
## Missed cancellation windows

The following agreements had cancel-by deadlines that have passed and no
cancellation was recorded:

| Counterparty | Cancel-by was | Renewal date | Status |
|---|---|---|---|
| [name] | [date] | [date] | Will auto-renew on [date] |

**Options:**
- Negotiate late cancellation (rarely works but worth asking)
- Accept the renewal, mark next year's cancel-by now
- Check the agreement for any other termination rights (for convenience, for cause)
```

## Gate: accepting or declining a renewal

Tracking a renewal date is research. *Acting* on it — sending a notice of non-renewal, letting an auto-renewal fire, or countersigning a renewal form — is a consequential legal step.

**Before proceeding to accept or decline a renewal (including sending a non-renewal notice or letting an auto-renewal run past the cancel-by date):** Read `## Who's using this` in `~/.claude/plugins/config/claude-for-legal/commercial-legal/CLAUDE.md`. If the Role is Non-lawyer:

> This step has legal consequences (you're either committing to another term or terminating the relationship). Have you reviewed this with an attorney? If yes, proceed. If no, here's a brief to bring to them:
>
> [Generate a 1-page summary: counterparty, current term end and cancel-by date, renewal price mechanism, what happens if we do nothing, alternative vendors if we want to shop, and the three things to ask the attorney before the window closes.]
>
> If you need to find an attorney, solicitor, barrister, or other authorised legal professional: contact your professional regulator (state bar in the US, SRA/Bar Standards Board in England & Wales, Law Society in Scotland/NI/Ireland/Canada/Australia, or your jurisdiction's equivalent) for a referral service.

Do not proceed past this gate without an explicit yes.

## Integration: renewal-watcher agent

The renewal-watcher agent in this plugin runs this skill on a schedule (weekly by default) and posts the "coming up" report to the channel named in `~/.claude/plugins/config/claude-for-legal/commercial-legal/CLAUDE.md` → `## House style` → where work product goes. Mode 2 is the agent's primary output.

## What this skill does not do

- It does not cancel contracts. It tells you when to decide.
- It does not decide whether to renew. It surfaces the deadline and the business owner.
- It does not read contracts to find renewal dates — that happens at review time. If a contract is in the register without a renewal date, it was added manually and someone needs to fill in the gap.
