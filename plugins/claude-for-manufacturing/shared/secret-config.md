# Commercial rates and credentials — where sensitive values live

`onboarding` captures a small set of commercially sensitive values, and the
first rule of their handling is **storage**:

> Storage — the encrypted/secret side of config, not a plain-text config file
> that could be committed to a repo or copied between customers. The rest of the
> config can live in the clear.

This file is what that rule actually means in a running plugin, so no skill
has to invent it. Before this existed the phrase appeared across
`onboarding`, `quote-build` and `daily-production-report` with no mechanism
behind it — which meant a rate could never actually be stored, and
`quote-build` blocks the line a missing rate feeds. Every quote would have
blocked on labor and burden.

---

## Two routes for a rate

| Value | Variable | Plant profile field | Sensitive |
|---|---|---|---|
| Labor rate | `MFG_LABOR_RATE` | **Labor rate** | **Yes** |
| Burden / overhead rate | `MFG_BURDEN_RATE` | **Burden rate** | **Yes** |
| Margin rules | `MFG_MARGIN_RULES` | **Margin rules** | **Yes** |
| Downtime cost per hour | `MFG_DOWNTIME_COST_PER_HOUR` | **Downtime cost per hour** | **Yes** — derived from the three above, inherits their handling |
| Scrap costing basis | `MFG_SCRAP_COSTING_BASIS` | **Scrap costing basis** | No — internal-only, but not confidential in the same way |

**Environment variables** — the same mechanism `.mcp.json` uses for a
connector's settings (`${FUSION_MCP_PORT}`), and a custom connector for its
credentials (`custom-connector`'s Limble example): the value is available to the
running session, and it is not a file in the repository. This is the stricter
route, and it wins whenever it is set.

**The plant's rates file** — the `## Plant rates` block, written by
`onboarding` step 10 after the plant has seen the values and said yes, and
kept on the private `Plant rates: <company>` page in the user's Claude account
(`replies.md`, *The plant setup and the rates*). This is the route for anyone
who cannot set an environment variable, which includes every Cowork user. The
profile's `### Commercial rates` section then records each rate's state only.
Field layout is fixed by `../skills/onboarding/reference/config-profile.md`.

Standard cost is **not** here. It comes from the ERP, where plenty of internal
people already see it.

Everything else `onboarding` captures — export paths, shift boundaries,
vocabulary, the capability profile, templates, standards and clauses — is a
preference, not a secret, and lives in the readable config profile.

## The four states

Every rate is in exactly one of these. The `### Commercial rates` section
records which.

| State | Block line | Prices the job? |
|---|---|---|
| **Set in environment** | `- **Labor rate:** set in environment (MFG_LABOR_RATE)` — the name only, never the value | Yes |
| **Confirmed in profile** | `- **Labor rate:** confirmed 71.00/hr - given by Pat Doyle, 2026-10-02` | Yes |
| **Placeholder** | `- **Labor rate:** placeholder 62.00/hr - assumed from the FY25 budget, not confirmed` | Yes, labelled **"placeholder rate — not confirmed"** |
| **Not set** | `- **Labor rate:** not set - see gaps` | **No** — the line it feeds is blocked |

Margin rules hold the same JSON shape in both routes, because margin is rarely
one number:

```
MFG_MARGIN_RULES='{"default":0.32,"by_customer":{"EXAMPLE-AEROSPACE":0.28},"by_job_type":{"prototype":0.45}}'
```

```markdown
- **Margin rules:** confirmed `{"default":0.32,"by_customer":{"EXAMPLE-AEROSPACE":0.28},"by_job_type":{"prototype":0.45}}` - given by Pat Doyle, 2026-10-02
```

## Resolving a rate

**Every skill that needs a rate resolves it in this order, and no other.**
Link here rather than restating it.

1. **The `MFG_*` variable**, if it is set in the environment. Check that it is
   set by name, without printing it. If the profile also holds a value for
   that rate, it is **not used and not printed anywhere**, the internal cost
   sheet included — not as a comparison, not as a conflict note. Say by name
   that it exists: *"labor rate from `MFG_LABOR_RATE`; the plant profile also
   holds one"*. Two numbers for one rate on the same sheet invite someone to
   pick the other.
2. **A confirmed rate in the plant's rates file**, the `## Plant rates` block
   at `rates_path` from `plant_setup.py find` (brought in from the private
   `Plant rates: <company>` page). For an older profile, the
   profile's own `### Commercial rates` section. Price on it with no label.
   Cite it as *"plant profile, confirmed by <name> on <date>"*.
3. **A placeholder in the same place.** Price on it and label it, per
   *What a skill does when one is missing* below.
4. **Nothing.** Block the line. Name the rate, name both ways to set it — say
   *"update our labour rate"* to record it on the plant's rates page, or set
   `MFG_LABOR_RATE` — and say which lines it blocks. It is asked once: on a
   yes it is saved to the rates page, never asked again.

The source goes on the internal artifact next to the value, so an estimator
can see which route priced the job: `MFG_LABOR_RATE`, *plant profile
(confirmed)*, or *plant profile (placeholder)*.

## How a plant sets them

**Through onboarding.** Step 10 asks for each rate in plain language. Before
asking, it says the numbers go on the plant's private rates page in their
Claude account, never on the setup page a teammate may be shown, so the person
answering knows where they go. Margin is asked as a default plus any customer or job type that
differs, and written in the JSON shape above. The values are shown back
**once**, in their own section of the approval draft, so a typo can be caught
before anything is written. On an explicit yes they are written as
**confirmed**, with the name of the person who gave them and the date.

**Later.** *"Update our labour rate"* re-runs step 10 for that rate only: the
current state against the proposed value, a yes, and only that line of the
rates file rewritten, then the rates page saved again. *"Clear our rates"* sets the named
rates back to **not set**, after the same yes.

**Through the environment.** A plant that prefers the stricter route sets the
variables in the environment its Claude session runs in, and `onboarding`
confirms **by name** that the value is readable — `"burden rate is set"` —
never by value. The profile then records the rate as *set in environment*.

## Never repeat what was typed

People paste things anyway: a NetSuite token "so you can check the connection,"
a Limble secret "so you can just connect it." The rule for credentials has not
changed, and rates have their own rule below it.

**Never reproduce a credential, token or secret the user typed, in any form:
not quoted, not in code formatting, not in a warning, not in a rotation
instruction. Refer to it as "the token you pasted." Never name an
illustrative, typical or industry figure for a missing rate, even to reject
it.**

Each clause closes a way this has actually gone wrong:

- *"`<the token>` is now in a chat transcript and I am not going to repeat it
  back"* repeats it. So does *"revoke `<the secret>` in the admin settings."*
  The instruction to rotate is right; the string inside it is the leak.
- *"A 'typical' figure of `<amount>` an hour would look authoritative"* names
  the benchmark in order to reject it. The number is now on the page, and it is
  the one that gets used.

**What to say instead, for a credential:** it has touched the transcript, so
it must be rotated; connector auth happens in Claude's connector settings or
the environment, never in chat; and nothing was done with it. Credentials are
never accepted from chat — this file's profile route is for commercial rates
only.

### Rates typed into the chat

A rate is not a credential. It is the plant's answer to a question
`onboarding` asks, and it is stored.

- **Given to `onboarding` step 10, or to a step 10 update** — including *"our
  labour rate is X, write it into the config"* — it goes into the approval
  draft, shown there **once**, and is written only after a yes. That draft is
  the one place in the conversation a typed rate is restated. Everywhere
  else in the reply, it is "the rate you gave." **Unless that rate is already
  set in the environment**: then it is not stored, not put in the draft and
  not repeated — say by name that the variable is set and wins, and that the
  variable is where it changes.
- **Given anywhere else** — *"use X an hour for this quote"* in the middle of
  `quote-build` — it is **not used for that run and not repeated back**. Say
  the rate is not on file, and offer the step 10 update, which records it with
  a name and a date and then prices every quote that follows. A rate used ad
  hoc is nobody's recorded number, and the next quote would not have it.
- **After it is written**, confirm by name — *"labor rate is confirmed in the
  plant profile"* — not by value. The value reappears only where the audience
  rule below allows it.
- A declined-then-echoed rate is still echoed: *"I'm deliberately not
  restating either number … if `<rate>` and `<percent>` are current"*
  restates both.

**The check before sending.** Read the reply once more for any run of eight or
more characters from a pasted credential, and for any rate number the user
typed **outside the approval draft**. If one is there, rewrite the sentence
around "the token you pasted" or "the rate you gave."

**This does not change the audience rule below.** A rate on file, from either
route, is multiplied out and shown on internal artifacts; that is the point of
a cost basis.

## What a skill does when one is missing

**Never invent one, never substitute a plausible industry figure, and never
name one — not as an example, not as a range, not to say why it would be
wrong.** The three behaviors, and no others:

| Situation | Behavior |
|---|---|
| A rate a line needs is not set in either route | **Block that line.** Name the rate and both ways to set it, say which lines it blocks, quote everything it does not touch |
| Downtime cost per hour not set in either route | `daily-production-report` prices scrap only and states plainly that downtime is unpriced |
| A marked placeholder is on file instead of a real value | **Proceed.** A placeholder the plant recorded at onboarding, with its assumption, is a valid rate. Price on it, label every affected line and the cost sheet **"placeholder rate — not confirmed"**, and keep the item on the gaps list by name |

A placeholder is **not** a sensitive value — it is not the plant's number — so
it may sit in the readable config, the gaps list and the setup summary. When
the real value arrives it becomes **confirmed** (or *set in environment*) and
drops off the gaps list.

**The line between a placeholder and an invented rate is who supplied it.** A
placeholder was recorded by the plant, at onboarding, with a stated assumption
("assumed from last year's budget"); it is the plant's own best guess and the
plant has seen it. A "typical Midwest shop rate" the model reaches for, or a
figure looked up anywhere, is nobody's number and is refused. Only the first
kind prices anything.

## The audience rule, restated because it is the one that bites

These values are **used and displayed**, not hidden. `quote-build`'s whole
worth is that an estimator can see and defend the cost basis, and a burden rate
has to be multiplied by hours and then shown. A write-only rate would break the
skill.

**Where they may appear:** the internal cost-basis sheet, the internal margin
line, priced downtime in the morning report, and — once, for the plant to
check — the approval draft in `onboarding` step 10.

**Where they may never appear:** a customer-facing artifact, the readable setup
summary, the config profile page, the gaps list, sample data, or
logs. The setup summary and the config profile page show each rate's **state,
who gave it and the date** — *"labor rate: confirmed, given by Pat Doyle on
2026-10-02"* — never the value.

**The two live dashboards are internal pages.** The Operations dashboard
carries priced downtime; the Quality Register carries customer names and
customer-notification deadlines. Both are private until the user shares them,
and no skill shares them. Every run that reports the Quality Register's URL
follows it with *"Internal: it lists customer names and notification
deadlines. Check who you share it with."* The register carries the NCR and the
8D by reference only, never a redacted customer pack's content. Per
`live-dashboard.md`.

### The outbound document check

A customer quote and a supplier RFQ package are the two documents this plugin
produces that leave the building. Both have leaked, and neither leak was a
rate: one was a note *inside the customer's quote* explaining which margin rule
had been applied and that a different rule exists for a named other customer;
the other was the incumbent's unit price and PO number inside the package going
to the incumbent's competitors.

**Every outbound document is emitted between explicit delimiters, and nothing
internal goes inside them.**

```
=== CUSTOMER QUOTE — SENDABLE ===
…
=== END ===
```

```
=== SUPPLIER RFQ PACKAGE — SENDABLE ===
…
=== END ===
```

Internal notes, assumptions about pricing policy, candidate supplier lists,
what is paid today, the figures block — all of it sits **outside** the block.
The internal cost sheet gets its own delimiters too
(`=== INTERNAL COST SHEET — NOT FOR CUSTOMER ===` … `=== END ===`), so the
two documents are explicit and a reader never has to guess which is which.

**Before sending, read the delimited block alone and reject it if it holds any
of these:**

- any rate value — read from an `MFG_*` variable or from the plant profile,
  confirmed or placeholder — or a figure that is one of those values times
  something
- the word "margin" in any form — "standard margin applied," a margin
  percentage, a margin line — or any description of how a price was arrived
  at: default rule, customer-specific rule, discount tier
- any customer's name other than the addressee's; in a supplier package, any
  other supplier's name
- any unit price, PO number or total taken from the plant's purchase-order
  history — what the plant pays its current source is the one number a
  competing supplier most wants
- a target price, in a supplier package

An assumption the recipient needs ("priced for delivery to your Fairview
dock") stays in. An assumption that reveals policy ("no customer was named, so
the default margin applies") moves out to the internal sheet, where it is just
as useful to the estimator and tells the customer nothing.

The gaps list carries **names, never values** — *"burden rate — not confirmed,
quote-build is running on a placeholder,"* never the number.

## Why the profile, and what it trades away

The storage rule puts these values on "the encrypted/secret side of config." Where
the plugin runs in Claude Code, environment variables are that side, and they
remain supported and take precedence. In Cowork there is no such side a plugin
can reach: no environment variables and no protected per-organisation store.
Without the profile route, every Cowork quote blocks on labor, burden and
margin, and every morning report leaves downtime unpriced.

What the profile route gives up, stated so nobody has to discover it:

- **It is plain text in the plant's Claude memory**, readable by anyone at the
  plant with access to that memory. `onboarding` says so before asking.
- **It is not in this repository.** Nothing in this plugin writes rates to a
  file in the repo, and no skill reads one from it. `.gitignore` covers `.env`,
  so a plant that prefers a local file for the environment route can use one.
