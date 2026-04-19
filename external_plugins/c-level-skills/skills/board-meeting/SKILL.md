---
name: board-meeting
description: >
  Multi-agent board meeting protocol for strategic decisions. Runs a structured
  6-phase deliberation: context loading, independent C-suite contributions,
  critic analysis, synthesis, founder review, and decision extraction. Prevents
  groupthink through isolated contributions. Use when making major strategic
  decisions, resolving cross-functional disagreements, evaluating irreversible
  choices, or when user mentions board meeting, executive deliberation,
  strategic decision, multi-perspective, or structured deliberation.
license: MIT + Commons Clause
metadata:
  version: 2.0.0
  author: borghei
  category: c-level
  domain: board-protocol
  updated: 2026-03-09
  frameworks:
    - 6-phase-protocol
    - two-layer-memory
    - independent-contributions
    - groupthink-prevention
    - synthesis-framework
    - decision-extraction
  triggers:
    - board meeting
    - executive deliberation
    - strategic decision
    - multi-perspective
    - structured deliberation
    - convene the board
    - C-suite meeting
    - executive council
    - founder review
    - decision extraction
    - multi-agent deliberation
    - need all perspectives
    - complex decision
---
# Board Meeting Protocol

Structured multi-agent deliberation that prevents groupthink, captures minority views, and produces clean, actionable decisions. Every phase has a purpose, a format, and rules that cannot be skipped.

## Keywords

board meeting, executive deliberation, strategic decision, C-suite, multi-agent, founder review, decision extraction, independent perspectives, groupthink prevention, synthesis, critic analysis, structured deliberation

---

## The 6-Phase Protocol

```
PHASE 1: Context Gathering
    |
PHASE 2: Independent Contributions (ISOLATED)
    |
PHASE 3: Critic Analysis (Executive Mentor)
    |
PHASE 4: Synthesis (Chief of Staff)
    |
PHASE 5: Founder Review (FULL STOP -- human decides)
    |
PHASE 6: Decision Extraction and Logging
```

---

### Phase 1: Context Gathering

**Purpose**: Load all relevant context before anyone contributes.

```
Step 1: Load company context (if exists)
Step 2: Load decision history (Layer 2 ONLY -- NEVER raw transcripts)
Step 3: Reset session state -- no bleed from previous conversations
Step 4: Present agenda and activated roles
Step 5: Wait for founder confirmation before proceeding
```

#### Role Activation Matrix

Not all roles attend every meeting. Select based on topic:

| Topic Domain | Activate | Exclude |
|-------------|----------|---------|
| Market expansion | CEO, CMO, CFO, CRO, COO | CTO (unless tech expansion) |
| Product direction | CEO, CPO, CTO, CMO | CFO (unless budget question) |
| Hiring / org | CEO, CHRO, CFO, COO | CMO, CTO (unless their teams) |
| Pricing | CMO, CFO, CRO, CPO | CTO, CHRO |
| Technology | CTO, CPO, CFO, CISO | CMO, CRO |
| Fundraising | CEO, CFO, CRO | CISO, CHRO |
| Security incident | CEO, CTO, CISO, COO | CMO, CRO |
| M&A | CEO, CFO, CTO, CHRO, COO | -- (all relevant) |

**Maximum attendees**: 6 roles per meeting. More than 6 creates noise, not insight.

---

### Phase 2: Independent Contributions (ISOLATED)

**Critical Rule**: No cross-pollination. Each advisor contributes without seeing others' outputs. This is the primary groupthink prevention mechanism.

#### Contribution Order

```
1. Research/data gathering (if needed)
2. CMO  -- market perspective
3. CFO  -- financial perspective
4. CEO  -- strategic perspective
5. CTO  -- technical perspective
6. COO  -- operational perspective
7. CHRO -- people perspective
8. CRO  -- revenue perspective
9. CISO -- security/risk perspective
10. CPO -- product perspective
```

#### Contribution Format (Strict)

Each advisor's contribution must follow this exact format:

```
## [ROLE] -- [DATE]

Key Points (maximum 5):
  1. [Finding] -- Confidence: [High/Medium/Low] -- Source: [data source]
  2. [Finding] -- Confidence: [High/Medium/Low] -- Source: [data source]
  3. [Finding] -- Confidence: [High/Medium/Low] -- Source: [data source]

Recommendation: [Clear position statement]
Confidence: [High / Medium / Low]
Key Assumption: [The one assumption this recommendation depends on]
What Would Change My Mind: [Specific condition or data point]
```

#### Reasoning Techniques by Role

| Role | Technique | How It Works |
|------|-----------|-------------|
| CEO | Tree of Thought | Explore 3 possible futures, evaluate each |
| CFO | Chain of Thought | Show the math, step by step |
| CMO | Recursion of Thought | Draft -> self-critique -> refine |
| CPO | First Principles | Decompose to fundamental user needs |
| CRO | Chain of Thought | Pipeline math must be explicit |
| COO | Step by Step | Map the operational process |
| CTO | Analyze then Act | Research -> analyze -> recommend |
| CISO | Risk-Based | Probability x Impact for every option |
| CHRO | Empathy + Data | Human impact first, then validate with metrics |

---

### Phase 3: Critic Analysis

**Purpose**: The Executive Mentor receives ALL Phase 2 outputs simultaneously and performs adversarial review.

#### Critic Checklist

| Check | Question |
|-------|----------|
| Suspicious consensus | Where did agents agree too easily? |
| Shared assumptions | What assumptions are shared but unvalidated? |
| Missing voice | Who is not in the room? (customer voice? front-line ops?) |
| Unmentioned risk | What risk has nobody mentioned? |
| Domain bleed | Did any agent operate outside their domain? |
| Data quality | Which claims are backed by data vs. assumption? |
| Reversibility | Has anyone assessed if this decision can be undone? |

#### Critic Output Format

```
## CRITIC ANALYSIS

Consensus Assessment:
  [Genuine agreement / Suspicious alignment / Split decision]

Unvalidated Assumptions:
  1. [Assumption shared by multiple advisors but not verified]
  2. [Assumption]

Missing Perspectives:
  - [Voice or data point not represented]

Unmentioned Risks:
  - [Risk nobody raised]

Domain Violations:
  - [If any agent operated outside their domain]

The Uncomfortable Truth:
  [The one thing nobody wants to say but needs to be said]
```

---

### Phase 4: Synthesis

**Purpose**: Chief of Staff combines all inputs into a decision-ready format.

#### Synthesis Structure

```
## BOARD MEETING SYNTHESIS
Topic: [topic]
Date: [date]
Attendees: [roles]

### Decision Required
[One sentence: what must be decided]

### Perspectives Summary
| Role | Position | Confidence | Key Concern |
|------|----------|-----------|-------------|
| [Role] | [1-line summary] | [H/M/L] | [Top concern] |
| [Role] | [1-line summary] | [H/M/L] | [Top concern] |

### Where They Agree
[2-3 consensus points]

### Where They Disagree
[Named conflicts with each side's reasoning]
[What the disagreement is really about]

### Critic's View
[The uncomfortable truth from Phase 3]

### Recommended Decision
[Clear recommendation with rationale]

### Action Items (if approved)
1. [Action] -- Owner: [role] -- Deadline: [date]
2. [Action] -- Owner: [role] -- Deadline: [date]
3. [Action] -- Owner: [role] -- Deadline: [date]

### Your Call
[If you disagree with the recommendation, here are alternatives:]
Option A: [description] -- Trade-off: [what you gain/lose]
Option B: [description] -- Trade-off: [what you gain/lose]
```

---

### Phase 5: Founder Review

**FULL STOP. Wait for the founder. No agent acts beyond this point.**

```
FOUNDER REVIEW

[Paste synthesis above]

Options:
  [A] Approve as recommended
  [M] Modify (specify changes)
  [R] Reject (specify reason)
  [Q] Ask follow-up question to specific role
  [D] Defer decision (specify timeline)
```

#### Phase 5 Rules

| Rule | Rationale |
|------|-----------|
| Founder corrections override all agent proposals | Human judgment is final |
| No pushback on founder decisions | Agents advise, founder decides |
| 30-minute inactivity auto-closes as "pending review" | Prevents zombie meetings |
| Founder can reopen any time | Decisions are not time-locked |
| Follow-up questions go to specific role | Keeps discussion focused |

---

### Phase 6: Decision Extraction

**Purpose**: After founder approval, extract and log all decisions.

```
Step 1: Write full transcript to Layer 1
  --> memory/board-meetings/YYYY-MM-DD-raw.md

Step 2: Run conflict detection against existing decisions
  --> Check for DO_NOT_RESURFACE violations
  --> Check for topic contradictions
  --> Check for owner conflicts

Step 3: Surface any conflicts to founder for resolution

Step 4: Append approved decisions to Layer 2
  --> memory/board-meetings/decisions.md

Step 5: Mark rejected proposals with DO_NOT_RESURFACE

Step 6: Confirm to founder:
  "Meeting concluded. Logged: [N] decisions, [M] action items,
   [K] DO_NOT_RESURFACE flags."
```

---

## Failure Mode Reference

| Failure | Detection | Fix |
|---------|-----------|-----|
| Groupthink | All advisors agree without tension | Re-run Phase 2 isolated; force "strongest argument against" |
| Analysis paralysis | Discussion exceeds 5 points per advisor | Cap at 5; force recommendation even with Low confidence |
| Bikeshedding | Discussion on minor points, major decisions deferred | Log as async action; return to main agenda |
| Role bleed | CFO making product calls, CTO pricing | Critic flags in Phase 3; exclude from synthesis |
| Layer contamination | Raw transcripts loaded in Phase 1 | Hard rule: decisions.md only. Never raw. |
| Founder absence | Phase 5 timeout | Auto-close as pending. No decisions without founder. |
| Stale context | Company context not loaded | Phase 1 mandatory context check |
| Missing role | Key perspective not activated | Chief of Staff reviews topic against routing matrix |

---

## Meeting Cadence

| Trigger | Meeting Type | Typical Duration |
|---------|-------------|-----------------|
| Scheduled quarterly | Full strategic review | 2-3 hours |
| Complexity score >= 8 | On-demand strategic | 1-2 hours |
| Cross-functional conflict | Resolution meeting | 1 hour |
| Crisis or urgent decision | Emergency session | 30-60 minutes |
| Founder request | Any topic | Varies |

---

## Red Flags

- Board meetings consistently produce no decisions -- meeting is theater
- Same topic discussed in 3+ meetings -- decision avoidance
- Phase 2 contributions all align perfectly -- isolation was breached or topic is trivial
- No Phase 3 (critic) conducted -- groupthink risk
- Founder skipping Phase 5 -- decisions without accountability
- Decisions logged but never reviewed -- decision logger not functioning
- Meeting attendees always include all roles -- topic selection not working

---

## Output Artifacts

| Request | Deliverable |
|---------|-------------|
| "Convene the board on [topic]" | Full 6-phase protocol execution |
| "Quick advisory meeting" | Abbreviated: Phase 1-2-4-5 (skip critic) |
| "Review a past meeting" | Load Layer 1 raw transcript (explicit request only) |
| "What did we decide about [topic]?" | Search Layer 2 decision history |
| "Resume a pending meeting" | Reload Phase 5 with pending synthesis |

---

## Tool Reference

### meeting_simulator.py

Validates role activation, contribution completeness, and phase sequencing.

```bash
# Simulate with defaults
python scripts/meeting_simulator.py

# Specify topic and complexity
python scripts/meeting_simulator.py --topic "Series B timing" --type fundraising --complexity 9

# Specify activated roles
python scripts/meeting_simulator.py --type m_and_a --roles CEO CFO CTO CHRO

# List all topic types and required roles
python scripts/meeting_simulator.py --list-topics

# JSON output
python scripts/meeting_simulator.py --type strategy --json
```

### decision_tracker.py

Tracks board decisions, detects conflicts, flags overdue reviews and actions.

```bash
# Track demo decisions
python scripts/decision_tracker.py

# From decision log file
python scripts/decision_tracker.py --input decisions.json

# JSON output
python scripts/decision_tracker.py --json
```

### complexity_scorer.py

Scores decision complexity to determine single/dual/multi-advisor or board routing.

```bash
# Score with CLI flags
python scripts/complexity_scorer.py --topic "Market expansion" --domains 2 --reversibility 2 --financial 1 --team 2 --urgency 0

# Add modifiers
python scripts/complexity_scorer.py --topic "Acquisition" --domains 2 --reversibility 2 --financial 2 --team 2 --urgency 1 --modifiers cross_functional external_stakeholders sets_precedent

# JSON output
python scripts/complexity_scorer.py --topic "Pricing change" --json
```

---

## Troubleshooting

| Problem | Likely Cause | Fix |
|---------|-------------|-----|
| All advisors agree without any tension in Phase 2 | Groupthink or trivial topic; isolation may have been breached | Re-run Phase 2 with forced "strongest argument against" from each role |
| Discussion exceeds 5 points per advisor | Analysis paralysis; no cap enforced | Hard cap at 5 key points; force a recommendation even with Low confidence |
| Phase 5 times out with no founder response | Founder absence or decision avoidance | Auto-close as "pending review" at 30 min; no decisions without founder |
| Same topic discussed in 3+ meetings | Decision avoidance or new data not surfaced | Escalate: force decision or formally defer with stated timeline |
| Decisions logged but never reviewed | Decision logger not integrated into meeting cadence | Add "previous decisions review" to Phase 1 context loading |
| Roles operating outside their domain | No critic analysis conducted or critic missed it | Enforce Phase 3 critic checklist; flag domain violations explicitly |

---

## Success Criteria

- Every board meeting produces at least 1 logged decision with owner, deadline, and review date
- Phase 2 contributions are independently generated (zero cross-pollination incidents per quarter)
- Phase 3 critic analysis identifies at least 1 unvalidated assumption per meeting
- Founder approval/modification/rejection captured within 30 minutes of synthesis presentation
- Decision history has zero conflicting active decisions (conflicts detected and resolved)
- Meeting duration stays within 2 hours for standard strategic reviews, 1 hour for resolution meetings
- 90%+ of logged decisions have action items completed by their stated deadlines

---

## Scope & Limitations

**In Scope**: Multi-agent deliberation protocol, role activation matrix, contribution formats, critic analysis, synthesis, decision extraction, decision conflict detection, meeting simulation.

**Out of Scope**: Actual AI agent orchestration (this is a protocol specification, not runtime code), real-time meeting facilitation, video/audio recording, external board member management.

**Limitations**: The protocol assumes all advisor contributions are available in text format. Complexity scoring provides routing guidance but cannot account for political dynamics. Decision conflict detection works on exact topic matching -- semantic conflicts across different topics require human judgment.

---

## Integration Points

| Skill | Integration |
|-------|-------------|
| `chief-of-staff` | Routes questions that score 9-10 complexity into the board meeting protocol |
| `decision-logger` | Phase 6 feeds decisions directly into the two-layer decision memory |
| `board-deck-builder` | Board deck sections provide pre-read context for Phase 1 |
| `executive-mentor` | Phase 3 critic analysis can be performed by the Executive Mentor skill |
| `ceo-advisor` through `ciso-advisor` | All C-suite advisors contribute independently in Phase 2 |
| `strategic-alignment` | Validates that meeting decisions align with strategic goals |
