# Strategic Analysis Skill

> Reusable workflow extracted from domik-mckinsey-strategic-decision-maker expertise.

## Purpose
Apply McKinsey-level strategic analysis using MECE frameworks, hypothesis-driven problem solving, and quantitative prioritization to drive transformational business decisions with executive-ready recommendations.

## When to Use
- Strategic initiative prioritization
- Business transformation planning
- Technology investment decisions
- Market entry/expansion strategy
- Digital transformation roadmaps
- M&A evaluation and due diligence
- Portfolio optimization
- Go/no-go decisions for major projects
- Executive decision support

## Workflow Steps

1. **Situation Assessment**
   - Define the strategic question clearly
   - Understand current state and context
   - Identify key stakeholders and their perspectives
   - Map competitive landscape
   - Gather relevant data and metrics
   - Document constraints and assumptions

2. **Issue Tree Construction (MECE)**
   - Break down the strategic question into components
   - Ensure Mutually Exclusive, Collectively Exhaustive structure
   - Create hypothesis-driven issue tree
   - Identify key decision drivers
   - Prioritize branches for deep dive analysis

3. **Hypothesis Formation**
   - Formulate testable hypotheses about the answer
   - Define what evidence would prove/disprove each
   - Create hypothesis tree with supporting logic
   - Identify critical assumptions
   - Plan data collection to test hypotheses

4. **Quantitative Analysis**
   - Gather data to test hypotheses
   - Apply ISE Prioritization Framework (if applicable)
   - Calculate financial impact (NPV, IRR, ROI)
   - Perform sensitivity analysis
   - Create scenario models (best/base/worst case)

5. **Qualitative Assessment**
   - Evaluate strategic fit with company vision
   - Assess organizational capability and readiness
   - Consider market timing and competitive dynamics
   - Evaluate execution risk and mitigation strategies
   - Assess stakeholder alignment

6. **Framework Application**
   - Apply relevant strategic frameworks:
     - Porter's Five Forces (competitive analysis)
     - 7S Framework (organizational alignment)
     - Three Horizons (innovation portfolio)
     - Value Chain Analysis (competitive advantage)
     - SWOT Analysis (strategic positioning)
   - Synthesize insights across frameworks

7. **Recommendation Development**
   - Synthesize analysis into clear recommendation
   - Create executive summary (three key messages)
   - Develop implementation roadmap
   - Identify quick wins and long-term plays
   - Define success metrics and KPIs

8. **Executive Communication**
   - Structure as situation-complication-question-answer
   - Lead with recommendation, support with analysis
   - Create visual "so what" slides
   - Prepare for objections and questions
   - Define clear next steps with ownership

## Inputs Required
- **Strategic Question**: Clear, specific decision to be made
- **Business Context**: Company strategy, market position, competitive landscape
- **Financial Data**: Revenue, costs, growth rates, market size
- **Organizational Context**: Capabilities, resources, constraints
- **Timeline**: Decision deadline, implementation window
- **Stakeholders**: Key decision-makers and their priorities

## Outputs Produced
- **Executive Summary**: Three key messages with recommendation
- **Strategic Analysis Report**: Detailed issue tree and hypothesis testing
- **Quantitative Models**: Financial projections, scenario analysis, ROI
- **Decision Framework Scorecards**: ISE or custom scoring with justification
- **Implementation Roadmap**: Phased plan with milestones and accountability
- **Risk Assessment**: Key risks with mitigation strategies
- **Presentation Deck**: Executive-ready slides for decision meeting

## MECE Framework Principles

### Mutually Exclusive
- No overlap between categories
- Each item fits in only one bucket
- Clear boundaries between segments

### Collectively Exhaustive
- All possibilities covered
- Nothing left out
- Complete picture of the problem space

### Example Issue Tree
```
Should we enter Market X?

├─ Market Attractiveness (IS the opportunity good?)
│  ├─ Market size and growth
│  ├─ Competitive intensity
│  └─ Profitability potential
│
├─ Strategic Fit (SHOULD we pursue it?)
│  ├─ Alignment with company strategy
│  ├─ Synergies with existing business
│  └─ Risk profile compatibility
│
└─ Ability to Win (CAN we succeed?)
   ├─ Competitive advantage
   ├─ Required capabilities vs current state
   └─ Resource availability and commitment
```

## ISE Prioritization Framework

### Initiative-Level Assessment (1-5 scale)

#### Customer Value
- **5**: CxO-validated outcomes with precise benchmarks
- **4**: Defined outcomes with preliminary benchmarks
- **3**: Aspirational outcomes without clear benchmarks
- **2**: Problem identified, outcomes vague
- **1**: No clear problem or impact defined

#### Microsoft Value (Annual NNR)
- **5**: >$50M annual NNR
- **4**: $20M-$50M annual NNR
- **3**: $5M-$20M annual NNR
- **2**: $1M-$5M annual NNR
- **1**: <$1M annual NNR

#### Ecosystem Impact
- **5**: Microsoft-wide blueprint with PG interest
- **4**: Multi-industry use case, strong partner enablement
- **3**: High relevance across industry, aligned to priority use case
- **2**: Replicable across customer segment, moderate TAM
- **1**: Replicable to 1-2 similar customers, low TAM
- **0**: Highly tailored, not replicable

#### Technical Innovation
- **5**: Transformational initiative co-led with PG
- **4**: Deep frontier tech use, co-engineering with PG
- **3**: Technically innovative, partially aligned with PG
- **2**: Moderate complexity, some key Azure services
- **1**: Not new, novel, or complex

#### Engineering Time to Solution
- **5**: <60 Dev Days
- **4**: 61-199 Dev Days
- **3**: 200-499 Dev Days
- **2**: 500-999 Dev Days
- **1**: >1000 Dev Days

#### Time to Full Production
- **5**: ≤2 months
- **4**: 2-4 months
- **3**: 4-8 months
- **2**: 8-12 months
- **1**: >12 months or no Azure tenant

### Composite Score Calculation
```
Total Score = (Customer Value + Microsoft Value + Ecosystem Impact +
               Technical Innovation + Engineering Efficiency +
               Time to Production) / 6

Interpretation:
4.5-5.0: Strategic priority - immediate investment
3.5-4.4: Strong candidate - detailed planning
2.5-3.4: Conditional - requires optimization
1.5-2.4: Deferred - not currently strategic
<1.5: Decline - does not meet minimum criteria
```

## Executive Summary Template

```markdown
# Strategic Recommendation: [Clear Decision Title]

## Recommendation
[One sentence: What should we do?]

## Three Key Messages
1. **[First key message]** - [Why it matters]
2. **[Second key message]** - [Supporting evidence]
3. **[Third key message]** - [What it means]

## Strategic Rationale
[2-3 paragraphs explaining the "why" behind the recommendation]

## Expected Impact
- Financial: [Revenue/cost impact with timeframe]
- Strategic: [Competitive advantage, market position]
- Organizational: [Capability building, culture]

## Implementation Roadmap
- **Phase 1 (Months 1-3)**: [Quick wins, foundations]
- **Phase 2 (Months 4-6)**: [Scale, optimization]
- **Phase 3 (Months 7-12)**: [Full deployment, measurement]

## Key Risks & Mitigation
1. **[Risk]** - Mitigation: [Strategy]
2. **[Risk]** - Mitigation: [Strategy]

## Investment Required
- Capital: $[amount]
- People: [FTE count] over [timeframe]
- Timeline: [Duration]
- Expected ROI: [X]% by [timeframe]

## Success Metrics
- [KPI 1]: [Target by date]
- [KPI 2]: [Target by date]
- [KPI 3]: [Target by date]

## Next Steps
1. **[Action]** - Owner: [Name], Due: [Date]
2. **[Action]** - Owner: [Name], Due: [Date]
```

## Example Usage

```
Input: Should we invest in building an AI-powered customer service platform?

Workflow Execution:
1. Situation: Current support costs $5M/year, 24-hour response time,
   customer satisfaction 3.2/5

2. Issue Tree (MECE):
   ├─ Market Opportunity
   │  ├─ Cost savings potential
   │  ├─ Customer experience improvement
   │  └─ Competitive differentiation
   ├─ Technical Feasibility
   │  ├─ AI/ML capabilities required
   │  ├─ Data availability and quality
   │  └─ Integration complexity
   └─ Business Case
      ├─ Development cost and timeline
      ├─ ROI and payback period
      └─ Risk vs reward profile

3. Hypothesis: "AI platform will reduce support costs by 60% while
   improving satisfaction to 4.5/5 within 18 months"

4. Quantitative Analysis:
   - Current cost: $5M/year
   - Projected savings: $3M/year (60% reduction)
   - Development cost: $2M
   - Payback period: 8 months
   - 5-year NPV: $12M

5. ISE Framework Scoring:
   - Customer Value: 5/5 (CxO-validated cost savings + satisfaction)
   - Company Value: 4/5 ($3M annual recurring savings)
   - Ecosystem Impact: 3/5 (replicable across industry)
   - Technical Innovation: 4/5 (frontier AI/ML)
   - Engineering Effort: 4/5 (120 dev days)
   - Time to Production: 4/5 (3 months MVP)
   Composite Score: 4.0/5 - STRONG STRATEGIC PRIORITY

6. Framework: Porter's Five Forces shows AI as key competitive moat

7. Recommendation: "Invest $2M to build AI customer service platform"

8. Executive Summary: Three key messages format with roadmap

Output:
✅ RECOMMEND: Proceed with AI platform development
Expected Impact: $3M annual savings, 4.5/5 customer satisfaction
ROI: 150% over 5 years, 8-month payback
Next Step: Approve $2M budget, kickoff with 6-person team by Q2
```

## Strategic Frameworks Catalog

### Porter's Five Forces
- Threat of new entrants
- Bargaining power of suppliers
- Bargaining power of buyers
- Threat of substitute products
- Competitive rivalry

### 7S Framework (McKinsey)
- Strategy, Structure, Systems
- Shared Values, Style, Staff, Skills

### Three Horizons Model
- Horizon 1: Core business optimization
- Horizon 2: Emerging opportunities
- Horizon 3: Transformational bets

### Value Chain Analysis
- Primary: Inbound logistics, operations, outbound, marketing, service
- Support: Infrastructure, HR, technology, procurement

### BCG Growth-Share Matrix
- Stars, Cash Cows, Question Marks, Dogs

## Related Agents
- **domik-mckinsey-strategic-decision-maker** - Full agent with deep analysis
- **satya-board-of-directors** - System-thinking strategic guidance
- **antonio-strategy-expert** - Business strategy frameworks
- **amy-cfo** - Financial analysis and ROI modeling
- **ali-chief-of-staff** - Strategic initiative coordination

## Decision Quality Criteria

### Six Tests of a Good Decision
1. **Framing**: Right question being answered?
2. **Alternatives**: Multiple options considered?
3. **Information**: Reliable data gathered?
4. **Values**: Aligned with company values/strategy?
5. **Logic**: Sound reasoning and analysis?
6. **Commitment**: Stakeholders aligned and committed?

## ISE Engineering Fundamentals Alignment
- Architecture Decision Records (ADRs) for strategic tech decisions
- Trade studies before major investments
- Technical spikes for high-risk unknowns
- Data-driven decision making with metrics
- Iterative approach: pilot → scale → optimize
