---
name: community-ops
description: Use when designing or building a community ops platform for a developer community — a single-surface system that aggregates data from multiple tools and pushes actions back into those same tools.
author: Ryan Crowe
author_url: https://www.linkedin.com/in/drcrowe/
---

# Community Ops Platform

## The Core Insight

Most community tools are read-only monitors. A community ops platform is a **bidirectional hub**.

The problem it solves: community managers switch between Discord, a ticketing system, a CRM, a docs platform, and Slack just to handle one support thread. By the time they've assembled the full picture, context is lost and response time has suffered.

A community ops platform solves this with two principles:

1. **Single surface** — every system's data flows into one place. The community manager sees the full 360 on a customer (their tickets, their community history, their billing status, their account flags) without opening another tab.

2. **Bidirectional flow** — the platform doesn't just read from your tools, it writes back to them. Reply, create a ticket, flag a thread, post a digest — all from the same surface.

## The 360 View

The most valuable feature is customer context at the moment of response. When a mod sees a support thread, they should immediately see:
- Has this person opened tickets before?
- What's their account status / billing tier?
- Have they been suspended? Refunded?
- What did they report last time?

This requires correlating a community username to an account ID in your backend. Build this lookup early — it's what transforms a "support thread" into a "customer interaction."

## When You Need a Platform (Not Just a Bot)

You've outgrown a bot when:
- More than one person is working community
- You're operating across more than one channel or platform
- Issues are falling through the cracks between systems
- You're manually copying context from one tool to another

## What It's Not

A bot is a single-platform, event-driven responder. A platform is a cross-platform system of record with a persistent data model, triage logic, and internal team workflows.

| | Bot | Community Ops Platform |
|---|---|---|
| Scope | One platform | Multi-platform |
| Users | Community members | Community team |
| Data | Stateless events | Persistent records + history |
| Output | Replies in channel | Tickets, digests, dashboards, alerts |

## Who Can Build This

You don't need an engineering team. This was built by a community manager using AI to write the code. If you can describe what you need in plain language, you can build this. The architecture is the hard part — the code is solvable.

## Architecture Pattern

```
Inbound signals → Aggregation layer → Triage → Action layer → Outbound
(community         (normalize to       (classify, (ticket,     (reply,
 platforms,         common schema:      route,     alert,        update,
 ticketing,         who, when, what,    score)     summarize)    notify)
 CRM, docs)         account context)
```

**Aggregation** normalizes everything into a common "interaction" object: who, when, where, what they said, their account status, prior history.

**Triage** classifies each interaction: type, urgency, owner, escalation path.

**Action layer** closes the loop. This is what separates a platform from a dashboard.

## Key Integrations to Plan For

**Inbound (where community lives):**
- Community platforms (Discord, Slack, forum)
- Support ticketing system
- CRM or billing system (for account context)

**Workflow (where work gets done):**
- Issue tracker for engineering escalations
- Internal messaging (Slack, Teams) for team alerts and digests
- Knowledge base for AI-assisted responses

**Outbound (where actions land):**
- Back to community platforms (replies, reactions, flags)
- Ticketing system (create, update, close)
- Issue tracker (create engineering bugs)

## Commands Pattern

Build two types of commands:

**Inbound commands** — staff sends a command *to* the platform from inside a community tool. The human initiates. Examples: paste a conversation and get a formatted brief, ask for a drafted reply using the knowledge base, trigger an immediate escalation report.

**Outbound commands** — the platform proactively pushes data *to* your tools. The system initiates. Examples: daily digest of unresolved engineering issues, unanswered ticket alerts after an SLA window, incident signals when multiple users report the same issue.

## Triage Design

1. **Auto-classify** — use an LLM to categorize each interaction. Define categories that map directly to your escalation paths (e.g. Bug → engineering, Billing → finance, Suspension → ops).
2. **Human override** — give staff a one-action escalation (emoji reaction, slash command) to correct what auto-triage missed.
3. **Hard rules** — certain categories always escalate, no exceptions. Don't let the model override this.
4. **SLA tracking** — every open interaction gets a clock. Surface breaches before they happen, not after.

## What to Build First

1. **Message capture** — store every support message with author, timestamp, channel
2. **Session model** — group messages by user + channel + day into sessions
3. **Basic triage** — classify sessions (even just Bug/Billing/Other to start)
4. **Ticketing integration** — create tickets from actionable sessions
5. **Dashboard** — single surface showing open queue, recent sessions, unresolved issues
6. **Digest** — daily summary pushed to your team's messaging tool
7. **Staff commands** — let mods act from inside your community tools
8. **360 view** — enrich sessions with account/billing data from your CRM or billing system

The 360 view comes last not because it's least important — it's your most powerful feature — but because it requires the account ID lookup infrastructure, which should be built deliberately once the core pipeline is stable.

## Common Mistakes

- **Building the dashboard before the session model** — you'll have nothing useful to show. Data model first.
- **Skipping the account ID lookup** — without it, every interaction is anonymous. You have community data but no customer intelligence.
- **Treating the bot as the platform** — a bot that replies in Discord is a component, not a platform. Don't stop there.
- **Auto-classifying without a human override** — models make mistakes. Always give staff a one-action correction path.
- **Building outbound before inbound** — you can't push data you haven't collected. Aggregation comes before digests.

---

*Built by Ryan Crowe — Head of Community & Social at Fireworks AI. This skill documents the architecture behind Logger, a community ops platform built without a traditional engineering background using AI-assisted development. [LinkedIn](https://www.linkedin.com/in/drcrowe/)*
