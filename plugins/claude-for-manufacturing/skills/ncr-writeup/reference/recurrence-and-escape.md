# Recurrence and escape

Two steps that both exist because of the same problem: they are things everyone
agrees should happen, and they do not happen, because the moment they need to
happen is the moment everybody is busy.

---

## Recurrence — searched at creation, not on request

**The search runs automatically when the NCR is written.** Not when somebody
thinks to ask for it. The moment of detection is the only moment anyone is
looking at this part and this defect, and if the question is not answered then,
it is not answered at all.

### Search four ways

| Search | Finds |
|---|---|
| Same part number | Has this part done this before |
| Same defect on any part | A process problem wearing a different part number |
| Same process, operation or cell | A machine or a setup that keeps producing this |
| Same supplier or material lot | The signal that routes into Chain 5 |

Search prior NCRs and closed CAPAs in the plant's quality document library.

### The highest-value line in the whole chain

For any match, report **whether the earlier corrective action held.**

A recurrence after a closed CAPA is a materially more serious finding than a
first occurrence. It says the fix did not work, or was never really implemented,
or addressed a symptom. It changes what happens next, it changes who needs to
know, and in an audit it is the difference between a minor observation and a
systemic finding.

Three distinct outcomes, and they must not be collapsed:

- `first_occurrence` — searched, nothing found
- `recurrence_prior_capa_held` — it happened before, the fix worked, this is
  something new
- `recurrence_prior_capa_failed` — it happened before, the fix did not hold

### "No searchable history" is its own answer

`no_searchable_history` is a separate value from `first_occurrence` on purpose.

If there is no quality document library, or it holds nothing for this part, say
**"no searchable history available."** Never say nothing — per
`../../../shared/absent-is-not-zero.md`, silence reads as "no recurrence," which
is a far stronger claim than the evidence supports and exactly the wrong thing to
tell a quality manager.

---

## Escape — the clock starts without you

**An escape is a nonconforming part that reached a customer.** It is triggered
the moment containment places any suspect quantity at `at_customer` or
`installed_at_customer`.

That usually starts a contractual notification window — often 24 to 48 hours in
automotive and aerospace. **Missing that window is a bigger problem than the
defect itself.** A defect is a quality event. A missed notification is a breach,
and it is the thing that costs an approved-supplier status.

### Chained straight off containment

The notification draft is produced **automatically**, as the immediate next
output after containment finds parts at a customer. Nobody has to remember it,
under time pressure, against a clock they are not watching.

This is the single most valuable piece of automation in the skill, and it is
valuable precisely because it is boring.

### What the draft contains

- Part, revision, quantity shipped and the shipments involved
- What the nonconformance is, in plain terms, against the cited requirement
- What we are asking the customer to do — usually quarantine the receipt and
  confirm whether any have been installed or shipped on
- What we are doing about it and when they will hear next
- The NCR reference

### The clock, stated

Record `notification_deadline` as a **timestamp with its zone**, computed from
`found_at` plus the contractual window, and put it at the top of the draft.

Where the contractual window is not known, say so and do not guess one — an
invented 48 hours that is really 24 is worse than an open question. Ask where the
customer's terms are recorded.

### It still does not send

The draft is a draft. Nothing customer-facing leaves without a quality owner
approving it — this is the Chain 2 and Chain 5 approval gate, and an escape
notification is the most consequential thing this plugin will ever put in front
of a person. Speed is the point; unattended sending is not.
