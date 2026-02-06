# Recruitin Growth Intelligence Engine

Autonomous growth engine for recruitment marketing. Generates campaigns, measures performance, and self-optimizes based on historical data stored in Supabase.

## Overview

The Recruitin Growth Intelligence Engine is a Claude Code plugin that operates as a self-learning campaign system for recruitment marketing. It combines three interconnected loops:

1. **Creative-Strategic Loop** — Generates LinkedIn authority content for Recruitin and Meta/LinkedIn performance campaigns for client vacancies
2. **Data Analysis & Memory Loop** — Stores and analyzes weekly campaign metrics in Supabase to build institutional knowledge
3. **Continuous Optimization Loop** — Queries historical performance to determine winning strategies before generating new campaigns

The engine learns from every campaign it runs, building an ever-growing database of what works for specific industries, roles, and audiences in the Dutch recruitment market.

## Commands

### /recruitin-campaign

Create a new recruitment marketing campaign.

**Usage:**
```
/recruitin-campaign authority
/recruitin-campaign performance ClientName "Senior Developer Amsterdam"
```

**Features:**
- Generates complete campaign packages with ad copy, visual prompts, and posting schedules
- Consults historical data before generating to apply winning strategies
- Produces 3 ad variants per performance campaign for A/B testing
- Includes visual prompt specifications for PiAPI, Canva, or Midjourney

### /recruitin-report

Generate a weekly performance report.

**Usage:**
```
/recruitin-report
/recruitin-report 6 2026
```

**Features:**
- Executive summary with key metrics and trends
- Per-campaign health scores and recommendations
- Anomaly detection and alerts
- Winning strategy updates
- Client-ready summaries for distribution

### /recruitin-optimize

Run the optimization cycle across active campaigns.

**Usage:**
```
/recruitin-optimize
/recruitin-optimize campaign-id
```

**Features:**
- Scores current strategies against historical performance
- Recommends budget reallocations
- Proposes A/B tests based on data gaps
- Balances exploration vs. exploitation based on confidence levels

## Skills

### 1. Campaign Strategy

**Trigger phrases:** "create campaign", "plan LinkedIn content", "write Meta ad copy", "build 12-week campaign", "generate recruitment posts"

**What it covers:**
- 12-week authority campaign planning for LinkedIn
- Performance campaign creation for client vacancies
- Tone-of-voice framework and brand voice management
- LinkedIn post and Meta ad copy templates
- Visual prompt specification format

**Resources:**
- Core SKILL.md (~1,800 words)
- LinkedIn content templates reference
- Meta Ads templates reference
- Visual prompt generation guide

### 2. Data Memory

**Trigger phrases:** "import campaign data", "analyze performance", "set up database", "track KPIs", "create report"

**What it covers:**
- Supabase database schema design (6 tables + materialized view)
- Weekly data import and validation workflow
- Performance analysis queries
- Anomaly detection rules
- Complete SQL setup script

**Resources:**
- Core SKILL.md (~2,000 words)
- Supabase schema reference with RLS policies
- KPI definitions with Dutch market benchmarks

### 3. Continuous Optimization

**Trigger phrases:** "optimize campaign", "find winning strategy", "improve performance", "reduce cost per hire", "run optimization"

**What it covers:**
- Winning strategy determination algorithm
- Exploration vs. exploitation framework
- A/B testing management
- Weekly optimization reporting
- Feedback loop integration

**Resources:**
- Core SKILL.md (~1,800 words)
- Winning strategy selection logic with scoring algorithm
- A/B testing framework with statistical guidance

## Agents

### Campaign Planner (blue)
Senior recruitment marketing strategist. Creates complete campaign packages including ad copy, visual prompts, and content calendars. Operates in authority mode (Recruitin brand) or performance mode (client vacancies).

### Data Analyst (green)
Campaign performance analyst. Imports weekly metrics, generates reports, detects anomalies, and maintains the winning_strategies knowledge base in Supabase.

### Optimization Engine (yellow)
Strategy optimizer. Determines the best strategy for new campaigns by scoring historical data, manages A/B testing, and detects performance anti-patterns.

## Prerequisites

### Required Plugins
- **Supabase** — For persistent data storage (MCP integration included)

### Recommended Plugins
- **Marketing (Cowork)** — Enhanced content creation capabilities
- **Productivity (Cowork)** — Task management and calendar integration
- **Sales (Cowork)** — ICP prospecting and outreach
- **Slack** — Automated report distribution
- **Playwright** — Landing page monitoring
- **Frontend Design** — Custom landing page creation

## Quick Start

1. **Install the plugin** in Claude Code
2. **Set up Supabase** — Create a new project and run the SQL setup script from the data-memory skill
3. **Register your first client** — Add client details and brand voice to Supabase
4. **Create your first campaign** — Run `/recruitin-campaign` to generate content
5. **Import weekly data** — After the first week, import metrics and run `/recruitin-report`
6. **Optimize** — After 3+ weeks of data, run `/recruitin-optimize` to start the learning cycle

## Architecture

```
┌─────────────────────────────────────────────────┐
│            Recruitin Growth Engine               │
├─────────────────────────────────────────────────┤
│                                                 │
│  Commands                                       │
│  ├── /recruitin-campaign  (create content)      │
│  ├── /recruitin-report    (analyze data)        │
│  └── /recruitin-optimize  (improve strategy)    │
│                                                 │
│  Agents                                         │
│  ├── campaign-planner     (content generation)  │
│  ├── data-analyst         (metrics analysis)    │
│  └── optimization-engine  (strategy selection)  │
│                                                 │
│  Skills                                         │
│  ├── campaign-strategy    (creative knowledge)  │
│  ├── data-memory          (data architecture)   │
│  └── continuous-optimization (learning logic)   │
│                                                 │
│  Hooks                                          │
│  └── campaign-quality-check (content QA)        │
│                                                 │
│  External Integrations (via MCP)                │
│  └── Supabase (persistent data store)           │
│                                                 │
└─────────────────────────────────────────────────┘
```

## Data Flow

```
New Campaign Request
       │
       ▼
[Optimization Engine] ──query──→ [Supabase: winning_strategies]
       │
       │ recommended strategy
       ▼
[Campaign Planner] ──generates──→ Content Package
       │                          (ad copy + visual prompts)
       │
       │ content deployed
       ▼
[Weekly Metrics Import] ──store──→ [Supabase: weekly_metrics]
       │
       │ accumulated data
       ▼
[Data Analyst] ──analyze──→ Performance Report
       │                    Anomaly Alerts
       │                    Strategy Updates
       │
       └──feedback──→ [Supabase: winning_strategies refresh]
                              │
                              └──→ Next campaign is smarter
```

## Version

0.1.0 — Initial release

## Author

Recruitin (info@recruitin.nl)
