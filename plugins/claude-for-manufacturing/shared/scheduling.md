# Scheduling — what the plugin provides, and what it does not

Chain 3 is the only scheduled chain, and the reason it
matters is simple: the morning report is rewritten overnight so it exists before anyone
asks for it. That is the plugin's clearest demonstration of its own concept.

**A plugin cannot schedule itself.** It ships skills — markdown that shapes how
Claude works — not a running process. Nothing inside this repository can wake up
at 4am. Pretending otherwise is how a plant ends up believing a report is being
produced when nothing is producing it.

So the responsibility splits, and both halves have to hold:

| | |
|---|---|
| **The plugin provides** | A run that is safe to execute unattended: it asks nobody anything, it is idempotent, and it reports its own gaps rather than stalling on them |
| **The host provides** | The trigger — whatever wakes a Claude session on a cadence |

---

## What "safe to execute unattended" actually requires

Three properties, and each is a real constraint on how the skills are written.

**It asks nobody anything.** There is no one at 4am to answer. Where an
attended run would ask — which date range, which export to use when several are
present — the unattended run takes the production-day range from the
`## Plant context` block and says which it used. A run that blocks on a question
produces nothing, and nothing is worse than a partial report because nobody
finds out until the meeting.

**It is idempotent.** A re-run for the same production day rewrites that day's
report rather than appending a second one. Someone will re-run it — after a late
export lands, or because the first run was mistrusted — and two reports for one
day is worse than one, because now the meeting argues about which is right.

**It reports gaps rather than failing on them.** If last night's export did not
land, the run still completes and says so at the top. A missing export is a
finding, not an exception. Silence, stale data, or a crashed run all read the
same way to a supervisor at 6am: nothing to look at.

The corollary is that **the approval-gate posture is what makes this safe at
all.** Chain 3 writes to no system of record — it reads and produces a page. It
is the only chain with no approval gate, and that is precisely why it is the
only one that may run unattended. No other chain in this build should ever be
scheduled.

## How a plant actually schedules it

Any mechanism that starts a Claude session on a cadence works. The plugin does
not care which, and does not ship one:

- **Claude Code's own scheduling**, where the customer runs Claude Code and it
  is available to them
- **The operating system** — cron, systemd timers, Task Scheduler — invoking
  Claude headlessly against a prompt like *"run the morning production report
  for yesterday"*
- **A person**, which is a legitimate answer. Saying "morning report" at 6:15am
  produces the same artifact. It costs the supervisor two minutes rather than
  the ninety they typically spend assembling it by hand, and it is where
  most plants will start

The plugin's job is to make all three produce the same output. That is what
idempotence and the no-questions rule buy.

## What a skill may claim

**A skill may say it is safe to run unattended.** It may describe the run as
overnight, because that is the intended cadence and it shapes correct behavior —
the production-day boundary, the freshness banner, the fallback date range.

**A skill may not claim it schedules itself, or report a scheduled run as having
happened.** "Chain 3 runs this overnight" describes the design. "I have
scheduled the morning report" would be false, and no skill says it.

**A skill may say the dashboard was updated**, but only when the publish
call returned a URL in that same run, per `live-dashboard.md`. That is a
statement about a call that ran. It is still never a statement about a
schedule: *"Updated the Operations Command Center"* is allowed after a
successful publish; *"the dashboard will update every morning"* is not, because
nothing in the plugin makes that happen.

**Whether a scheduled, unattended session can publish at all is unverified.**
No scheduled run has been observed publishing or updating an artifact. So the
pulse checks for the publish tools on every run, and when they are absent it
falls back to the page in the conversation and says the dashboard was not
updated. A skill never claims that a scheduled run published anything; only
that run's own tool results can say so.

If a customer asks the plugin to schedule something, the honest answer is this
file: here is what the run needs, here is how to trigger it on your side.
