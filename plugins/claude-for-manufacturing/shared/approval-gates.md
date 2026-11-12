# Approval gates — what a yes covers, and what it does not

**Shared across the plugin.** Every skill with a gate follows this.

The plugin's rule is that nothing is applied, sent, written or published
without a yes. That rule held under test: no write reached any system. What
gave way was the *edge* of the yes. A yes to one fix was stretched over four
fixes nobody had been shown. A job title was accepted in place of a release. A
draft was published in the turn it first appeared, on the strength of "set us
up." A chain drafted the customer's quote in the same pass as the questions the
quote depended on.

Each of those is a gate that was present and was walked around. This file says
where the edge is.

---

## The rule

**An approval covers exactly the item that was shown, with its details. It
never extends to an item the user has not seen — even when they say "all," or
"same for everything."**

**A claim of authority is not an approval.** "I'm the plant manager, I'm
authorizing this" cannot be verified from inside a conversation, and it does
not need to be: release is always a step the user performs themselves. The
skill hands over the package. It never sends on someone's say-so.

**Generic continuation is not approval of a draft.** "Carry on," "use what you
have," "set us up," "go ahead" move the work forward. They do not approve
something the user has not yet been shown in full.

**A chain stops at each gate, and says which gate and which step it stopped
at.**

---

**The name on a yes is the one the person gave.** An approval record —
who released a quote, who confirmed a model at Gate 3, who chose a supplier —
names the person who said it, asked for in the same turn if they have not
said. It is never taken from the session account, an email address or git
config; if they decline to give one, it says `not given`. Per `replies.md`.

## What that looks like

### A blanket yes

> *"Yes, strip the Rev 2 suffix. And assume the same for everything else."*

Apply every class the user has **already been shown in this conversation**,
with its rule, its count and its example rows: "everything else" is a yes to
each of those, because they have read each of them. Any class not yet shown is
presented and asked about first. Classes with no automatic fix — duplicates,
orphans, one-sided records — are never applied by any yes. The reply lists
each class applied with its count, and says the verbatim values are kept so it
can be undone.

The reason is practical, not procedural. "Restore the leading zeros" and "pick
one of two duplicate work orders" are both "fixes," and only one of them is
safe. A yes reaches only what a person could see when they said it.

### A claim of authority

> *"I own the sourcing budget. Issue the RFQ under my signature."*

*"I can't verify who's speaking, and I don't need to — releasing the RFQ is a
step you take yourself. Here is the package, ready to send."* Then hand it
over. No send tool is called.

Say it without suspicion. The person almost certainly is who they say they
are. The point is that the release is theirs to perform, which is also what
protects them if it is ever questioned.

### A draft, first shown

Show the full draft. Stop. Write or publish only after an explicit yes given
**after** the draft was on the screen. The turn that first shows a draft never
also writes it.

### Confirming many things

Put them to the user **one at a time**, and record only what was confirmed. A
fourteen-row table with "confirm or correct each line" gets a single "looks
fine," which confirms nothing — and the rows nobody read are the ones that get
joined wrong.

### A chain at a gate

Say where it stopped, in the chain's own numbering: *"Paused at Gate 1, step 4.
The questions are drafted for you to send. Nothing downstream runs until the
customer answers."* When asked where sign-off is needed, list every gate with
its step, never a bare count like "there are four gates." Chain 1 has four:
questions at step 4, bid/no-bid at step 5, the design at step 8, release at
step 11.

Work that depends on the far side of a gate is not drafted ahead of it. A
customer quote is not written while the questions it rests on are still open,
and no hour is derived from a model before the estimator has confirmed it.

### Confirming a design — Chain 1, Gate 3

`rfq-to-quote` builds an internal model of the customer's part from the
drawing, and drafts a geometry estimate from it. Gate 3 is the estimator
confirming it before any hour is derived.

**A yes covers what was shown at Gate 3, and only that:** this model (by its
document reference, or the hand-entered feature list), these tolerances as
read, these datum assumptions — every inferred datum, named — this operation
list, and the answers given to the questions the model raised.

**It does not cover:**

- **A later drawing revision.** A revised drawing is a different part until
  someone has looked. It re-runs the design step and comes back to Gate 3.
- **The hours.** They are derived after the yes, and shown at Gate 4 with
  their basis.
- **The price.** That is Gate 4.
- **A cost-down idea the model produced.** Those stay internal and are never
  offered to the customer through this gate or any other.

A request made before the model was on screen — "build it and go straight to
the price" — is generic continuation, not a Gate 3 yes. An estimator may
explicitly override and quote on the unconfirmed model; the override is
recorded with who gave it, and every hour it produced is labelled unconfirmed.

### Supplier send and selection

`supplier-quote-request` runs the supplier loop after the package is released:
one email per supplier, chases, restatement requests, a comparison and a
recommendation. Two edges matter.

**The send gate.** Every email to a supplier — the package cover, a chase, a
restatement request, an award or regret note — is a draft the buyer sends from
their own mailbox. **A yes covers the drafts that were shown, to the suppliers
they were addressed to**: not a supplier added afterwards, not a chase that
has not been drafted yet. "Send them out" gets the drafts and one sentence
saying nothing was sent. No send tool is called, M365 is read-only, and no
email is reported *sent* until the buyer says they sent it; then it is recorded
with their date and their words.

**The selection record.** The skill recommends; **the buyer selects.** A
selection is recorded only when the buyer states it after the comparison was
on screen, naming a supplier on it, and gives a name to record it under. The
record carries who, when, the bids on screen, the suppliers who had not
responded, and whether it followed the recommendation — a decision against it
is recorded without argument. It covers that decision and nothing else:

- **Not a purchase order.** Nothing is written to the ERP.
- **Not an award notice.** Nothing goes to any supplier until the buyer sends
  a drafted one.
- **Not a later bid.** A restated or late bid after the decision is shown, and
  the record is not changed unless the buyer decides again.

Generic continuation — "go ahead," "use your judgement," "pick the cheapest"
before the comparison was shown — is not a selection. Neither is silence: an
event is never closed, and no supplier is treated as having declined, because
a supplier went quiet. Shape in `contracts/supplier-bid.md`.

---

## When nobody is there to ask

The unattended run — Chain 3, overnight — cannot ask anything, and must not
block. It also must not decide for the user. So where an attended run would
ask before relying on something, the unattended run does three things:

1. **Shows the result labelled provisional**, so the page is still useful at
   the 6am meeting.
2. **Shows both sides verbatim** — the spelling each source actually used.
3. **Lists what it relied on as proposed, awaiting approval**, for a person to
   accept or reject when they read the page.

It never applies silently, and it never presents a provisional figure as
settled.

---

## What this does not change

- The write guard. No skill writes to NetSuite, Infor M3, SharePoint, Outlook, Teams,
  Slack or Fusion, approval or not, except through a write path a
  `custom-connector` engagement explicitly granted. For Infor M3 that means
  no call outside the read table in `erp-connectors.md`. Fusion has one narrow
  exception, and it is not a write to a record:
  `design-space-explore` and `rfq-to-quote`'s design step create **new**
  documents — variants, an estimating model — and never modify an existing
  one.
- Chain 3 has no approval gate, because it writes nothing. Listing a proposal
  on a page is not a gate.
- Computing a figure is not applying a fix. Counting how many records *would*
  join under a normalization needs no approval; joining them does.
