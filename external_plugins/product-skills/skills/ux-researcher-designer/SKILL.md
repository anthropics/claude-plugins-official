---
name: ux-researcher-designer
description: >
  UX research and design toolkit for Senior UX Designer/Researcher including
  data-driven persona generation, journey mapping, usability testing frameworks,
  and research synthesis. Use for user research, persona creation, journey
  mapping, and design validation.
license: MIT + Commons Clause
metadata:
  version: 1.0.0
  author: borghei
  category: product
  domain: ux-research
  updated: 2026-03-31
  tags: [ux-research, usability-testing, user-interviews, personas]
---
# UX Researcher & Designer

Generate user personas from research data, create journey maps, plan usability tests, and synthesize research findings into actionable design recommendations.

---

## Table of Contents

- [Trigger Terms](#trigger-terms)
- [Workflows](#workflows)
  - [Workflow 1: Generate User Persona](#workflow-1-generate-user-persona)
  - [Workflow 2: Create Journey Map](#workflow-2-create-journey-map)
  - [Workflow 3: Plan Usability Test](#workflow-3-plan-usability-test)
  - [Workflow 4: Synthesize Research](#workflow-4-synthesize-research)
- [Tool Reference](#tool-reference)
- [Quick Reference Tables](#quick-reference-tables)
- [Knowledge Base](#knowledge-base)

---

## Trigger Terms

Use this skill when you need to:

- "create user persona"
- "generate persona from data"
- "build customer journey map"
- "map user journey"
- "plan usability test"
- "design usability study"
- "analyze user research"
- "synthesize interview findings"
- "identify user pain points"
- "define user archetypes"
- "calculate research sample size"
- "create empathy map"
- "identify user needs"

---

## Workflows

### Workflow 1: Generate User Persona

**Situation:** You have user data (analytics, surveys, interviews) and need to create a research-backed persona.

**Steps:**

1. **Prepare user data**

   Required format (JSON):
   ```json
   [
     {
       "user_id": "user_1",
       "age": 32,
       "usage_frequency": "daily",
       "features_used": ["dashboard", "reports", "export"],
       "primary_device": "desktop",
       "usage_context": "work",
       "tech_proficiency": 7,
       "pain_points": ["slow loading", "confusing UI"]
     }
   ]
   ```

2. **Run persona generator**
   ```bash
   # Human-readable output
   python scripts/persona_generator.py

   # JSON output for integration
   python scripts/persona_generator.py json
   ```

3. **Review generated components**

   | Component | What to Check |
   |-----------|---------------|
   | Archetype | Does it match the data patterns? |
   | Demographics | Are they derived from actual data? |
   | Goals | Are they specific and actionable? |
   | Frustrations | Do they include frequency counts? |
   | Design implications | Can designers act on these? |

4. **Validate persona**

   - Show to 3-5 real users: "Does this sound like you?"
   - Cross-check with support tickets
   - Verify against analytics data

5. **Reference:** See `references/persona-methodology.md` for validity criteria

### Proto-Persona Canvas (Lightweight Alternative)

When you lack research data but need a hypothesis-driven persona to align the team, use a proto-persona canvas. Proto-personas are assumption tools -- not validated truth -- meant to be tested and refined.

**Use when:** Starting a new initiative with no research budget, aligning a cross-functional team quickly, or creating a testable hypothesis about your user.

**Proto-Persona Canvas Template:**

```markdown
### [Alliterative Name] (e.g., "Careful Carlos")

**Bio & Demographics:**
- Age, geography, social status, career stage
- Online presence, leisure activities, partner status

**Quotes** (what they say, feel, think):
- "[Direct quote capturing their perspective]"
- "[Quote revealing frustration or aspiration]"

**Pains:**
- [Pain related to the problem space]
- [Pain related to current workarounds]

**What They're Trying to Accomplish:**
- [Observable behavior 1]
- [Observable behavior 2]

**Goals** (wants, needs, dreams):
- [Short-term goal]
- [Long-term aspiration]

**Attitudes & Influences:**
- Decision Making Authority: [Can they buy/adopt your solution?]
- Decision Influencers: [Who influences their decisions?]
- Beliefs & Attitudes: [What beliefs impact their choices?]

**Assumptions to Validate:**
- [Top assumption that must be true for this persona to be viable]
- [Second assumption]
- [Third assumption]
```

**Next steps after proto-persona:**
1. Generate interview questions to validate assumptions (Recommended)
2. Generate an anti-persona to define scope boundaries
3. Convert into a one-page stakeholder brief

---

### Workflow 2: Create Journey Map

**Situation:** You need to visualize the end-to-end user experience for a specific goal.

**Steps:**

1. **Define scope**

   | Element | Description |
   |---------|-------------|
   | Persona | Which user type |
   | Goal | What they're trying to achieve |
   | Start | Trigger that begins journey |
   | End | Success criteria |
   | Timeframe | Hours/days/weeks |

2. **Gather journey data**

   Sources:
   - User interviews (ask "walk me through...")
   - Session recordings
   - Analytics (funnel, drop-offs)
   - Support tickets

3. **Map the stages**

   Typical B2B SaaS stages:
   ```
   Awareness → Evaluation → Onboarding → Adoption → Advocacy
   ```

4. **Fill in layers for each stage**

   ```
   Stage: [Name]
   ├── Actions: What does user do?
   ├── Touchpoints: Where do they interact?
   ├── Emotions: How do they feel? (1-5)
   ├── Pain Points: What frustrates them?
   └── Opportunities: Where can we improve?
   ```

5. **Map three experience paths** (not just the happy path)

   | Stage | Happy Path | Fail Path | Difficult Path |
   |---|---|---|---|
   | Awareness | Finds product via search | Never discovers product | Finds competitor first |
   | Consideration | Clear value proposition | Confused by pricing | Needs manager approval |
   | Decision | Easy signup flow | Form errors, abandons | Legal review delays |
   | Delivery & Use | Smooth onboarding | Can't import data | Workaround needed |
   | Loyalty | Becomes advocate | Churns silently | Stays but complains |

   - **Happy Path:** Everything works as designed.
   - **Fail Path:** User cannot complete their goal and drops off.
   - **Difficult Path:** User completes the goal but with friction, workarounds, or frustration.

6. **Add KPIs and ownership per stage**

   | Stage | Leading KPI | Lagging KPI | Team Owner |
   |---|---|---|---|
   | Awareness | Site visits, ad impressions | Brand recall | Marketing |
   | Consideration | Demo requests, pricing page views | MQL conversion | Marketing/Sales |
   | Decision | Trial starts, contract sent | Close rate | Sales |
   | Use | Feature adoption, DAU | Retention rate | Product |
   | Loyalty | NPS, referral count | LTV, expansion revenue | Customer Success |

7. **Identify top friction points and interventions**

   For each friction point, document:

   | Friction Point | Why It Matters | Intervention | Expected Impact | Effort | Confidence |
   |---|---|---|---|---|---|
   | [Description] | [User/business impact] | [Proposed fix] | High/Med/Low | S/M/L | High/Med/Low |

   Priority Score = Frequency x Severity x Solvability

8. **Reference:** See `references/journey-mapping-guide.md` for templates

---

### Workflow 3: Plan Usability Test

**Situation:** You need to validate a design with real users.

**Steps:**

1. **Define research questions**

   Transform vague goals into testable questions:

   | Vague | Testable |
   |-------|----------|
   | "Is it easy to use?" | "Can users complete checkout in <3 min?" |
   | "Do users like it?" | "Will users choose Design A or B?" |
   | "Does it make sense?" | "Can users find settings without hints?" |

2. **Select method**

   | Method | Participants | Duration | Best For |
   |--------|--------------|----------|----------|
   | Moderated remote | 5-8 | 45-60 min | Deep insights |
   | Unmoderated remote | 10-20 | 15-20 min | Quick validation |
   | Guerrilla | 3-5 | 5-10 min | Rapid feedback |

3. **Design tasks**

   Good task format:
   ```
   SCENARIO: "Imagine you're planning a trip to Paris..."
   GOAL: "Book a hotel for 3 nights in your budget."
   SUCCESS: "You see the confirmation page."
   ```

   Task progression: Warm-up → Core → Secondary → Edge case → Free exploration

4. **Define success metrics**

   | Metric | Target |
   |--------|--------|
   | Completion rate | >80% |
   | Time on task | <2× expected |
   | Error rate | <15% |
   | Satisfaction | >4/5 |

5. **Prepare moderator guide**

   - Think-aloud instructions
   - Non-leading prompts
   - Post-task questions

6. **Reference:** See `references/usability-testing-frameworks.md` for full guide

---

### Workflow 4: Synthesize Research

**Situation:** You have raw research data (interviews, surveys, observations) and need actionable insights.

**Steps:**

1. **Code the data**

   Tag each data point:
   - `[GOAL]` - What they want to achieve
   - `[PAIN]` - What frustrates them
   - `[BEHAVIOR]` - What they actually do
   - `[CONTEXT]` - When/where they use product
   - `[QUOTE]` - Direct user words

2. **Cluster similar patterns**

   ```
   User A: Uses daily, advanced features, shortcuts
   User B: Uses daily, complex workflows, automation
   User C: Uses weekly, basic needs, occasional

   Cluster 1: A, B (Power Users)
   Cluster 2: C (Casual User)
   ```

3. **Calculate segment sizes**

   | Cluster | Users | % | Viability |
   |---------|-------|---|-----------|
   | Power Users | 18 | 36% | Primary persona |
   | Business Users | 15 | 30% | Primary persona |
   | Casual Users | 12 | 24% | Secondary persona |

4. **Extract key findings**

   For each theme:
   - Finding statement
   - Supporting evidence (quotes, data)
   - Frequency (X/Y participants)
   - Business impact
   - Recommendation

5. **Prioritize opportunities**

   | Factor | Score 1-5 |
   |--------|-----------|
   | Frequency | How often does this occur? |
   | Severity | How much does it hurt? |
   | Breadth | How many users affected? |
   | Solvability | Can we fix this? |

6. **Reference:** See `references/persona-methodology.md` for analysis framework

---

## Tool Reference

### persona_generator.py

Generates data-driven personas from user research data.

| Argument | Values | Default | Description |
|----------|--------|---------|-------------|
| format | (none), json | (none) | Output format |

**Sample Output:**

```
============================================================
PERSONA: Alex the Power User
============================================================

📝 A daily user who primarily uses the product for work purposes

Archetype: Power User
Quote: "I need tools that can keep up with my workflow"

👤 Demographics:
  • Age Range: 25-34
  • Location Type: Urban
  • Tech Proficiency: Advanced

🎯 Goals & Needs:
  • Complete tasks efficiently
  • Automate workflows
  • Access advanced features

😤 Frustrations:
  • Slow loading times (14/20 users)
  • No keyboard shortcuts
  • Limited API access

💡 Design Implications:
  → Optimize for speed and efficiency
  → Provide keyboard shortcuts and power features
  → Expose API and automation capabilities

📈 Data: Based on 45 users
    Confidence: High
```

**Archetypes Generated:**

| Archetype | Signals | Design Focus |
|-----------|---------|--------------|
| power_user | Daily use, 10+ features | Efficiency, customization |
| casual_user | Weekly use, 3-5 features | Simplicity, guidance |
| business_user | Work context, team use | Collaboration, reporting |
| mobile_first | Mobile primary | Touch, offline, speed |

**Output Components:**

| Component | Description |
|-----------|-------------|
| demographics | Age range, location, occupation, tech level |
| psychographics | Motivations, values, attitudes, lifestyle |
| behaviors | Usage patterns, feature preferences |
| needs_and_goals | Primary, secondary, functional, emotional |
| frustrations | Pain points with evidence |
| scenarios | Contextual usage stories |
| design_implications | Actionable recommendations |
| data_points | Sample size, confidence level |

---

## Quick Reference Tables

### Research Method Selection

| Question Type | Best Method | Sample Size |
|---------------|-------------|-------------|
| "What do users do?" | Analytics, observation | 100+ events |
| "Why do they do it?" | Interviews | 8-15 users |
| "How well can they do it?" | Usability test | 5-8 users |
| "What do they prefer?" | Survey, A/B test | 50+ users |
| "What do they feel?" | Diary study, interviews | 10-15 users |

### Persona Confidence Levels

| Sample Size | Confidence | Use Case |
|-------------|------------|----------|
| 5-10 users | Low | Exploratory |
| 11-30 users | Medium | Directional |
| 31+ users | High | Production |

### Usability Issue Severity

| Severity | Definition | Action |
|----------|------------|--------|
| 4 - Critical | Prevents task completion | Fix immediately |
| 3 - Major | Significant difficulty | Fix before release |
| 2 - Minor | Causes hesitation | Fix when possible |
| 1 - Cosmetic | Noticed but not problematic | Low priority |

### Interview Question Types

| Type | Example | Use For |
|------|---------|---------|
| Context | "Walk me through your typical day" | Understanding environment |
| Behavior | "Show me how you do X" | Observing actual actions |
| Goals | "What are you trying to achieve?" | Uncovering motivations |
| Pain | "What's the hardest part?" | Identifying frustrations |
| Reflection | "What would you change?" | Generating ideas |

---

## Knowledge Base

Detailed reference guides in `references/`:

| File | Content |
|------|---------|
| `persona-methodology.md` | Validity criteria, data collection, analysis framework |
| `journey-mapping-guide.md` | Mapping process, templates, opportunity identification |
| `example-personas.md` | 3 complete persona examples with data |
| `usability-testing-frameworks.md` | Test planning, task design, analysis |

---

## Validation Checklist

### Persona Quality
- [ ] Based on 20+ users (minimum)
- [ ] At least 2 data sources (quant + qual)
- [ ] Specific, actionable goals
- [ ] Frustrations include frequency counts
- [ ] Design implications are specific
- [ ] Confidence level stated

### Journey Map Quality
- [ ] Scope clearly defined (persona, goal, timeframe)
- [ ] Based on real user data, not assumptions
- [ ] All layers filled (actions, touchpoints, emotions)
- [ ] Pain points identified per stage
- [ ] Opportunities prioritized

### Usability Test Quality
- [ ] Research questions are testable
- [ ] Tasks are realistic scenarios, not instructions
- [ ] 5+ participants per design
- [ ] Success metrics defined
- [ ] Findings include severity ratings

### Research Synthesis Quality
- [ ] Data coded consistently
- [ ] Patterns based on 3+ data points
- [ ] Findings include evidence
- [ ] Recommendations are actionable
- [ ] Priorities justified

---

## Tool Reference

### persona_generator.py

Generates data-driven personas from user research data, classifying users into archetypes with demographics, psychographics, behaviors, goals, frustrations, and design implications.

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `format` | positional | (none) | Add `json` for JSON output; omit for human-readable |

**Archetypes supported:** power_user, casual_user, business_user, mobile_first

**Output components:** name, archetype, tagline, quote, demographics, psychographics, behaviors, needs_and_goals, frustrations, scenarios, data_points, design_implications

```bash
python scripts/persona_generator.py           # Human-readable formatted output
python scripts/persona_generator.py json      # JSON for programmatic use
```

**Data input format (customize in script):**
```json
[{
  "user_id": "user_1",
  "age": 32,
  "usage_frequency": "daily",
  "features_used": ["dashboard", "reports", "export"],
  "primary_device": "desktop",
  "usage_context": "work",
  "tech_proficiency": 7,
  "pain_points": ["slow loading", "confusing UI"]
}]
```

---

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Persona confidence level is "Low" | Fewer than 20 users in sample data | Collect more data points; combine quantitative analytics with qualitative interviews |
| All users classified as same archetype | Insufficient variation in input data | Ensure data includes diverse usage frequencies, devices, and contexts |
| Frustrations are generic (fallback defaults) | Not enough pain_points in user data | Enrich user data with pain_points from interviews and support tickets |
| Design implications too vague | Patterns don't strongly differentiate | Add more behavioral signals (features_used, session duration, task completion) |
| Journey map has flat emotion curve | All stages scored similarly | Re-evaluate with actual user data; conduct contextual interviews per stage |
| Usability test sample too small | Fewer than 5 participants | 5 participants find ~85% of usability issues; recruit to minimum 5 |
| Research synthesis has no clear patterns | Data not coded consistently | Use consistent tagging scheme (GOAL, PAIN, BEHAVIOR, CONTEXT, QUOTE) |

---

## Success Criteria

| Criterion | Target | How to Measure |
|-----------|--------|----------------|
| Persona validity | Validated by 3+ real users ("sounds like me") | Post-creation validation interviews |
| Persona coverage | All key segments represented | Count of personas vs identified user segments |
| Data confidence level | "High" (31+ users) | persona_generator data_points.confidence_level |
| Research cadence | 5-8 interviews per segment per quarter | Count of completed research sessions |
| Insight-to-action rate | >70% of findings result in design changes | Track findings through to implementation |
| Usability issue resolution | All critical/major issues fixed before release | Issue severity tracking |
| Journey map freshness | Updated at least quarterly | Last-updated date on each journey map |

---

## Scope & Limitations

**In scope:**
- Data-driven persona generation from user research
- Archetype classification (power, casual, business, mobile-first)
- User journey mapping frameworks
- Usability test planning and scoring
- Research synthesis and coding methodology
- Interview question frameworks
- Empathy map and opportunity identification

**Out of scope:**
- Automated user interview recording/transcription
- Real-time analytics integration (use analytics platforms)
- Quantitative survey design and distribution (use Typeform/SurveyMonkey)
- Eye tracking or biometric data analysis
- AI-powered sentiment analysis (tool uses heuristic classification)
- Persona illustration or visual asset generation
- Accessibility auditing (see product-designer or design-system-lead skills)

---

## Integration Points

| Tool / Platform | Integration Method | Use Case |
|-----------------|-------------------|----------|
| Dovetail / Condens | Export research data, import persona JSON | Centralize research insights |
| Figma / Miro | Paste persona output as design artifact | Reference personas during design work |
| Notion / Confluence | Human-readable output | Document and share personas with team |
| product-manager-toolkit | Persona pain points inform RICE scoring | Connect user needs to feature prioritization |
| agile-product-owner | Persona data informs user story personas | Write stories grounded in research |
| product-designer | Persona feeds into journey mapping and usability test recruitment | End-to-end design research workflow |
