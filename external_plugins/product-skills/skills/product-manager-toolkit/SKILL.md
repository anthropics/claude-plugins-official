---
name: product-manager-toolkit
description: >
  Comprehensive toolkit for product managers including RICE prioritization,
  customer interview analysis, PRD templates, discovery frameworks, and
  go-to-market strategies. Use for feature prioritization, user research
  synthesis, requirement documentation, and product strategy development.
license: MIT + Commons Clause
metadata:
  version: 1.0.0
  author: borghei
  category: product
  domain: product-management
  updated: 2026-03-31
  tags: [product-management, rice, okr, roadmap, prioritization]
---
# Product Manager Toolkit

Essential tools and frameworks for modern product management, from discovery to delivery.

---

## Table of Contents

- [Quick Start](#quick-start)
- [Core Workflows](#core-workflows)
  - [Feature Prioritization](#feature-prioritization-process)
  - [Customer Discovery](#customer-discovery-process)
  - [PRD Development](#prd-development-process)
- [Tools Reference](#tools-reference)
  - [RICE Prioritizer](#rice-prioritizer)
  - [Customer Interview Analyzer](#customer-interview-analyzer)
- [Input/Output Examples](#inputoutput-examples)
- [Integration Points](#integration-points)
- [Common Pitfalls](#common-pitfalls-to-avoid)

---

## Quick Start

### For Feature Prioritization
```bash
# Create sample data file
python scripts/rice_prioritizer.py sample

# Run prioritization with team capacity
python scripts/rice_prioritizer.py sample_features.csv --capacity 15
```

### For Interview Analysis
```bash
python scripts/customer_interview_analyzer.py interview_transcript.txt
```

### For PRD Creation
1. Choose template from `references/prd_templates.md`
2. Fill sections based on discovery work
3. Review with engineering for feasibility
4. Version control in project management tool

---

## Core Workflows

### Feature Prioritization Process

```
Gather → Score → Analyze → Plan → Validate → Execute
```

#### Step 1: Gather Feature Requests
- Customer feedback (support tickets, interviews)
- Sales requests (CRM pipeline blockers)
- Technical debt (engineering input)
- Strategic initiatives (leadership goals)

#### Step 2: Score with RICE
```bash
# Input: CSV with features
python scripts/rice_prioritizer.py features.csv --capacity 20
```

See `references/frameworks.md` for RICE formula and scoring guidelines.

#### Step 3: Analyze Portfolio
Review the tool output for:
- Quick wins vs big bets distribution
- Effort concentration (avoid all XL projects)
- Strategic alignment gaps

#### Step 4: Generate Roadmap
- Quarterly capacity allocation
- Dependency identification
- Stakeholder communication plan

#### Step 5: Validate Results
**Before finalizing the roadmap:**
- [ ] Compare top priorities against strategic goals
- [ ] Run sensitivity analysis (what if estimates are wrong by 2x?)
- [ ] Review with key stakeholders for blind spots
- [ ] Check for missing dependencies between features
- [ ] Validate effort estimates with engineering

#### Step 6: Execute and Iterate
- Share roadmap with team
- Track actual vs estimated effort
- Revisit priorities quarterly
- Update RICE inputs based on learnings

---

### Customer Discovery Process

```
Plan → Recruit → Interview → Analyze → Synthesize → Validate
```

#### Step 1: Plan Research
- Define research questions
- Identify target segments
- Create interview script (see `references/frameworks.md`)

#### Step 2: Recruit Participants
- 5-8 interviews per segment
- Mix of power users and churned users
- Incentivize appropriately

#### Step 3: Conduct Interviews
- Use semi-structured format
- Focus on problems, not solutions
- Record with permission
- Take minimal notes during interview

#### Step 4: Analyze Insights
```bash
python scripts/customer_interview_analyzer.py transcript.txt
```

Extracts:
- Pain points with severity
- Feature requests with priority
- Jobs to be done patterns
- Sentiment and key themes
- Notable quotes

#### Step 5: Synthesize Findings
- Group similar pain points across interviews
- Identify patterns (3+ mentions = pattern)
- Map to opportunity areas using Opportunity Solution Tree
- Prioritize opportunities by frequency and severity

#### Step 6: Validate Solutions
**Before building:**
- [ ] Create solution hypotheses (see `references/frameworks.md`)
- [ ] Test with low-fidelity prototypes
- [ ] Measure actual behavior vs stated preference
- [ ] Iterate based on feedback
- [ ] Document learnings for future research

---

### PRD Development Process

```
Scope → Draft → Review → Refine → Approve → Track
```

#### Step 1: Choose Template
Select from `references/prd_templates.md`:

| Template | Use Case | Timeline |
|----------|----------|----------|
| Standard PRD | Complex features, cross-team | 6-8 weeks |
| One-Page PRD | Simple features, single team | 2-4 weeks |
| Feature Brief | Exploration phase | 1 week |
| Agile Epic | Sprint-based delivery | Ongoing |

#### Step 2: Draft Content
- Lead with problem statement
- Define success metrics upfront
- Explicitly state out-of-scope items
- Include wireframes or mockups

#### Step 3: Review Cycle
- Engineering: feasibility and effort
- Design: user experience gaps
- Sales: market validation
- Support: operational impact

#### Step 4: Refine Based on Feedback
- Address technical constraints
- Adjust scope to fit timeline
- Document trade-off decisions

#### Step 5: Approval and Kickoff
- Stakeholder sign-off
- Sprint planning integration
- Communication to broader team

#### Step 6: Track Execution
**After launch:**
- [ ] Compare actual metrics vs targets
- [ ] Conduct user feedback sessions
- [ ] Document what worked and what didn't
- [ ] Update estimation accuracy data
- [ ] Share learnings with team

---

### Positioning Statement Framework

Create a Geoffrey Moore-style positioning statement to clarify product differentiation and value. Use this before writing PRDs, go-to-market plans, or pitch decks.

#### Core Positioning Template

```
For [target user/persona]
who [underserved need or painful moment],
[product name] is a [product category]
that [primary outcome delivered].
Unlike [main alternative: competitor, workaround, or status quo],
[product name] [unique differentiation in outcome terms].
```

#### One-Sentence Value Proposition

Write a single sentence a PM can reuse in docs and slides.

#### Differentiation Proof Points

List 3 concrete proof points that support the "unlike" claim. Focus on outcomes and evidence, not adjectives.

#### Writing Rules

- Use persona-first language.
- Focus on outcomes, not feature lists.
- Keep wording specific and testable.
- "Unlike X" should name the real alternative, including status quo.
- Strong differentiation is about outcomes and evidence, not adjectives.

#### Optional Variants

- **Executive variant:** Shorter strategic wording for board decks.
- **Customer-facing variant:** Clear plain-language wording for marketing.

#### Next Steps

1. Generate 3 alternate positioning directions (Recommended)
2. Create a competitor comparison message matrix
3. Convert into homepage headline + subheadline options

---

### Recommendation Canvas

Evaluate product opportunities holistically using a structured canvas that connects problem framing to solution evidence. Useful for investment decisions, portfolio reviews, and stakeholder alignment.

#### Canvas Sections

```markdown
## Product Name
[Name of the product or service]

## Business Outcome
[Direction] [Metric] [Outcome] [Context] [Acceptance criteria]

## Product Outcome
[Direction] [Metric] [Outcome] [Context] [Acceptance criteria]

## Problem Statement Narrative
[2-3 sentences telling the persona's story from their point-of-view]

## Solution Hypothesis
If we [action/solution] for [target persona],
then we will [desirable outcome].

### Tiny Acts of Discovery
- [Small experiment focused on viability]
- [Small experiment focused on customer value]

### Proof-of-Life
Within [timeframe], we observe:
- [Quantitative measurable outcome]
- [Qualitative measurable outcome]

## Positioning Statement
For [target persona] that need [underserved need],
[product] is a [category] that [benefit].
Unlike [competitor], [product] provides [differentiation].

## Assumptions & Unknowns
- [Assumption 1]
- [Assumption 2]

## Issues/Risks (PESTEL lens)
- Political: [Risk]
- Economic: [Risk]
- Social: [Risk]
- Technological: [Risk]
- Environmental: [Risk]
- Legal: [Risk]

## Value Justification
[Yes/Yes with caveats/No with alternatives/No]
Justification: [Why this is or isn't valuable]

## Success Metrics
1. [SMART metric 1]
2. [SMART metric 2]
3. [SMART metric 3]

## What's Next
1. [Next step with owner]
2. [Next step with owner]
```

#### When to Use

- Evaluating whether to invest in a new product or feature.
- Preparing for portfolio review or investment committee.
- Aligning stakeholders on go/no-go decisions.

---

## Tools Reference

### RICE Prioritizer

Advanced RICE framework implementation with portfolio analysis.

**Features:**
- RICE score calculation with configurable weights
- Portfolio balance analysis (quick wins vs big bets)
- Quarterly roadmap generation based on capacity
- Multiple output formats (text, JSON, CSV)

**CSV Input Format:**
```csv
name,reach,impact,confidence,effort,description
User Dashboard Redesign,5000,high,high,l,Complete redesign
Mobile Push Notifications,10000,massive,medium,m,Add push support
Dark Mode,8000,medium,high,s,Dark theme option
```

**Commands:**
```bash
# Create sample data
python scripts/rice_prioritizer.py sample

# Run with default capacity (10 person-months)
python scripts/rice_prioritizer.py features.csv

# Custom capacity
python scripts/rice_prioritizer.py features.csv --capacity 20

# JSON output for integration
python scripts/rice_prioritizer.py features.csv --output json

# CSV output for spreadsheets
python scripts/rice_prioritizer.py features.csv --output csv
```

---

### Customer Interview Analyzer

NLP-based interview analysis for extracting actionable insights.

**Capabilities:**
- Pain point extraction with severity assessment
- Feature request identification and classification
- Jobs-to-be-done pattern recognition
- Sentiment analysis per section
- Theme and quote extraction
- Competitor mention detection

**Commands:**
```bash
# Analyze interview transcript
python scripts/customer_interview_analyzer.py interview.txt

# JSON output for aggregation
python scripts/customer_interview_analyzer.py interview.txt json
```

---

## Input/Output Examples

### RICE Prioritizer Example

**Input (features.csv):**
```csv
name,reach,impact,confidence,effort
Onboarding Flow,20000,massive,high,s
Search Improvements,15000,high,high,m
Social Login,12000,high,medium,m
Push Notifications,10000,massive,medium,m
Dark Mode,8000,medium,high,s
```

**Command:**
```bash
python scripts/rice_prioritizer.py features.csv --capacity 15
```

**Output:**
```
============================================================
RICE PRIORITIZATION RESULTS
============================================================

📊 TOP PRIORITIZED FEATURES

1. Onboarding Flow
   RICE Score: 16000.0
   Reach: 20000 | Impact: massive | Confidence: high | Effort: s

2. Search Improvements
   RICE Score: 4800.0
   Reach: 15000 | Impact: high | Confidence: high | Effort: m

3. Social Login
   RICE Score: 3072.0
   Reach: 12000 | Impact: high | Confidence: medium | Effort: m

4. Push Notifications
   RICE Score: 3840.0
   Reach: 10000 | Impact: massive | Confidence: medium | Effort: m

5. Dark Mode
   RICE Score: 2133.33
   Reach: 8000 | Impact: medium | Confidence: high | Effort: s

📈 PORTFOLIO ANALYSIS

Total Features: 5
Total Effort: 19 person-months
Total Reach: 65,000 users
Average RICE Score: 5969.07

🎯 Quick Wins: 2 features
   • Onboarding Flow (RICE: 16000.0)
   • Dark Mode (RICE: 2133.33)

🚀 Big Bets: 0 features

📅 SUGGESTED ROADMAP

Q1 - Capacity: 11/15 person-months
   • Onboarding Flow (RICE: 16000.0)
   • Search Improvements (RICE: 4800.0)
   • Dark Mode (RICE: 2133.33)

Q2 - Capacity: 10/15 person-months
   • Push Notifications (RICE: 3840.0)
   • Social Login (RICE: 3072.0)
```

---

### Customer Interview Analyzer Example

**Input (interview.txt):**
```
Customer: Jane, Enterprise PM at TechCorp
Date: 2024-01-15

Interviewer: What's the hardest part of your current workflow?

Jane: The biggest frustration is the lack of real-time collaboration.
When I'm working on a PRD, I have to constantly ping my team on Slack
to get updates. It's really frustrating to wait for responses,
especially when we're on a tight deadline.

I've tried using Google Docs for collaboration, but it doesn't
integrate with our roadmap tools. I'd pay extra for something that
just worked seamlessly.

Interviewer: How often does this happen?

Jane: Literally every day. I probably waste 30 minutes just on
back-and-forth messages. It's my biggest pain point right now.
```

**Command:**
```bash
python scripts/customer_interview_analyzer.py interview.txt
```

**Output:**
```
============================================================
CUSTOMER INTERVIEW ANALYSIS
============================================================

📋 INTERVIEW METADATA
Segments found: 1
Lines analyzed: 15

😟 PAIN POINTS (3 found)

1. [HIGH] Lack of real-time collaboration
   "I have to constantly ping my team on Slack to get updates"

2. [MEDIUM] Tool integration gaps
   "Google Docs...doesn't integrate with our roadmap tools"

3. [HIGH] Time wasted on communication
   "waste 30 minutes just on back-and-forth messages"

💡 FEATURE REQUESTS (2 found)

1. Real-time collaboration - Priority: High
2. Seamless tool integration - Priority: Medium

🎯 JOBS TO BE DONE

When working on PRDs with tight deadlines
I want real-time visibility into team updates
So I can avoid wasted time on status checks

📊 SENTIMENT ANALYSIS

Overall: Negative (pain-focused interview)
Key emotions: Frustration, Time pressure

💬 KEY QUOTES

• "It's really frustrating to wait for responses"
• "I'd pay extra for something that just worked seamlessly"
• "It's my biggest pain point right now"

🏷️ THEMES

- Collaboration friction
- Tool fragmentation
- Time efficiency
```

---

## Integration Points

Compatible tools and platforms:

| Category | Platforms |
|----------|-----------|
| **Analytics** | Amplitude, Mixpanel, Google Analytics |
| **Roadmapping** | ProductBoard, Aha!, Roadmunk, Productplan |
| **Design** | Figma, Sketch, Miro |
| **Development** | Jira, Linear, GitHub, Asana |
| **Research** | Dovetail, UserVoice, Pendo, Maze |
| **Communication** | Slack, Notion, Confluence |

**JSON export enables integration with most tools:**
```bash
# Export for Jira import
python scripts/rice_prioritizer.py features.csv --output json > priorities.json

# Export for dashboard
python scripts/customer_interview_analyzer.py interview.txt json > insights.json
```

---

## Common Pitfalls to Avoid

| Pitfall | Description | Prevention |
|---------|-------------|------------|
| **Solution-First** | Jumping to features before understanding problems | Start every PRD with problem statement |
| **Analysis Paralysis** | Over-researching without shipping | Set time-boxes for research phases |
| **Feature Factory** | Shipping features without measuring impact | Define success metrics before building |
| **Ignoring Tech Debt** | Not allocating time for platform health | Reserve 20% capacity for maintenance |
| **Stakeholder Surprise** | Not communicating early and often | Weekly async updates, monthly demos |
| **Metric Theater** | Optimizing vanity metrics over real value | Tie metrics to user value delivered |

---

## Best Practices

**Writing Great PRDs:**
- Start with the problem, not the solution
- Include clear success metrics upfront
- Explicitly state what's out of scope
- Use visuals (wireframes, flows, diagrams)
- Keep technical details in appendix
- Version control all changes

**Effective Prioritization:**
- Mix quick wins with strategic bets
- Consider opportunity cost of delays
- Account for dependencies between features
- Buffer 20% for unexpected work
- Revisit priorities quarterly
- Communicate decisions with context

**Customer Discovery:**
- Ask "why" five times to find root cause
- Focus on past behavior, not future intentions
- Avoid leading questions ("Wouldn't you love...")
- Interview in the user's natural environment
- Watch for emotional reactions (pain = opportunity)
- Validate qualitative with quantitative data

---

## Quick Reference

```bash
# Prioritization
python scripts/rice_prioritizer.py features.csv --capacity 15

# Interview Analysis
python scripts/customer_interview_analyzer.py interview.txt

# Generate sample data
python scripts/rice_prioritizer.py sample

# JSON outputs
python scripts/rice_prioritizer.py features.csv --output json
python scripts/customer_interview_analyzer.py interview.txt json
```

---

## Reference Documents

- `references/prd_templates.md` - PRD templates for different contexts
- `references/frameworks.md` - Detailed framework documentation (RICE, MoSCoW, Kano, JTBD, etc.)

---

## Tool Reference

### rice_prioritizer.py

RICE framework implementation with portfolio analysis and quarterly roadmap generation.

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `input` | positional | (optional) | CSV file with features or "sample" to create sample |
| `--capacity` | int | 10 | Team capacity per quarter in person-months |
| `--output` | choice | text | Output format: `text`, `json`, `csv` |

**CSV columns:** `name, reach, impact, confidence, effort, description`

**Impact values:** massive, high, medium, low, minimal
**Confidence values:** high (100%), medium (80%), low (50%)
**Effort values:** xl (13mo), l (8mo), m (5mo), s (3mo), xs (1mo)

```bash
python scripts/rice_prioritizer.py sample                          # Create sample CSV
python scripts/rice_prioritizer.py features.csv                    # Default capacity (10)
python scripts/rice_prioritizer.py features.csv --capacity 20      # Custom capacity
python scripts/rice_prioritizer.py features.csv --output json      # JSON for integration
python scripts/rice_prioritizer.py features.csv --output csv       # CSV for spreadsheets
```

### customer_interview_analyzer.py

Keyword-based interview transcript analysis for extracting actionable insights.

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `interview_file` | positional | (required) | Path to interview transcript text file |
| `json` | positional | (optional) | Add "json" as second arg for JSON output |

**Extraction capabilities:** pain points (with severity), feature requests (with type and priority), jobs-to-be-done patterns, sentiment analysis, key themes, notable quotes, metrics mentioned, competitor mentions.

```bash
python scripts/customer_interview_analyzer.py interview.txt        # Human-readable
python scripts/customer_interview_analyzer.py interview.txt json   # JSON output
```

---

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| RICE scores cluster together | Impact/confidence not differentiated enough | Calibrate scoring rubric with team; use specific examples for each level |
| Roadmap overcommits capacity | Effort estimates too optimistic | Add 20% buffer; validate estimates with engineering before finalizing |
| Interview analysis misses key insights | Transcript is too short or uses unexpected phrasing | Supplement with manual review; ensure transcripts capture full context |
| Stakeholders disagree with priorities | Different value perceptions | Share raw RICE inputs transparently; allow stakeholders to adjust weights |
| Quick wins dominate roadmap | Bias toward low-effort items | Reserve 30-40% of capacity for strategic big bets |
| PRD scope creeps after approval | Insufficient out-of-scope definition | Explicitly list excluded items; require change request for additions |
| Feature factory behavior | Shipping without measuring impact | Define success metrics in PRD before development starts |

---

## Success Criteria

| Criterion | Target | How to Measure |
|-----------|--------|----------------|
| Prioritization velocity | <2 hours from data to ranked backlog | Time from CSV input to roadmap output |
| Interview analysis coverage | >80% of pain points captured | Compare tool output to manual expert review |
| Estimation accuracy | Actual effort within 1.5x of RICE estimate | Track actual vs estimated effort post-delivery |
| Roadmap confidence | >70% of Q1 roadmap items shipped in quarter | Shipped items / Planned items |
| Discovery cadence | 5-8 interviews per segment per quarter | Count completed interviews |
| PRD quality | 0 scope change requests after approval | Track change requests per PRD |
| Feature impact rate | >60% of shipped features hit success metrics | Post-launch metric comparison |

---

## Scope & Limitations

**In scope:**
- RICE prioritization with portfolio analysis
- Quarterly roadmap generation with capacity planning
- Customer interview transcript analysis
- Pain point, feature request, and JTBD extraction
- Sentiment analysis using keyword heuristics
- PRD development process and templates
- CSV/JSON import and export

**Out of scope:**
- Real-time analytics integration (use Amplitude/Mixpanel APIs)
- NLP model-based analysis (tool uses keyword heuristics, not ML)
- Multi-language transcript analysis (English only)
- Visual wireframe or prototype generation
- Competitive intelligence gathering (see business-growth skills)
- Revenue impact modeling (see finance skills)

---

## Integration Points

| Tool / Platform | Integration Method | Use Case |
|-----------------|-------------------|----------|
| Jira / Linear | `--output json` from rice_prioritizer | Import prioritized features as tickets |
| Google Sheets | `--output csv` from rice_prioritizer | Share roadmap with stakeholders |
| Dovetail / Notion | JSON output from interview analyzer | Aggregate interview insights in research repo |
| agile-product-owner | RICE priorities feed sprint backlog | Connect strategy to execution |
| product-strategist | OKR cascade informs RICE reach/impact | Align features with strategic objectives |
| Slack / Email | Human-readable output from both tools | Async stakeholder communication |
