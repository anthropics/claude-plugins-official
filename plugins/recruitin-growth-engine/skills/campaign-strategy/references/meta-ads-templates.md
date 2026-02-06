# Meta Ads Templates for Recruitment Campaigns

## Ad Format Templates

### Format 1: Single Image - Benefit-Led

```
Campaign Objective: Conversions (Sollicitaties)
Placement: Facebook Feed + Instagram Feed

Primary Text (125 chars):
"[Salary range] | [Key benefit] | [Location]. Klaar voor je volgende stap? Solliciteer direct →"

Headline (40 chars):
"[Job Title] bij [Company]"

Description (30 chars):
"Direct solliciteren"

Visual Prompt:
Platform: Meta
Format: 4:5 Portrait (1080x1350px)
Style: Photography with text overlay
Primary Subject: Professional in target role environment, natural lighting
Brand Colors: Client brand palette
Text Overlay: Job title + 1 key benefit + company logo
Mood: Warm, inviting, authentic
```

### Format 2: Carousel - Culture Showcase

```
Campaign Objective: Conversions
Placement: Facebook + Instagram Feed

Primary Text:
"Waarom [X] professionals dit jaar kozen voor [Company]? Dit is waarom →"

Card 1: Team photo + "Het team"
Card 2: Office/workspace + "[Key benefit 1]"
Card 3: Event/social moment + "[Key benefit 2]"
Card 4: Growth metrics + "[Key benefit 3]"
Card 5: CTA + "Jij ook? Solliciteer nu"

Each card headline: Benefit statement (25 chars)
Each card description: Supporting detail
```

### Format 3: Video - Pain Point Led

```
Campaign Objective: Conversions
Placement: Reels + Stories + Feed

Primary Text:
"Herkenbaar? [Pain point in current job]. Bij [Company] is dat anders. Ontdek hoe →"

Video Script (15 seconds):
0-3s: [Pain point scenario - text on screen]
3-7s: "Stel je voor..." [transition to positive scenario]
7-12s: [3 quick benefit flashes with text]
12-15s: Logo + CTA "Solliciteer nu"

Visual Prompt:
Platform: Meta
Format: 9:16 Vertical (1080x1920px)
Style: Motion graphics with kinetic typography
Primary Subject: Animated text transitions showing pain → solution
Brand Colors: Client palette with high contrast
Text Overlay: Key phrases from script
Mood: Energetic, transformative
```

### Format 4: Lead Form - Passive Candidate

```
Campaign Objective: Lead Generation
Placement: Facebook + Instagram Feed

Primary Text:
"Niet actief op zoek, maar wel benieuwd? Laat je gegevens achter en wij vertellen je meer over deze [Job Title] positie bij [Company]."

Headline:
"Vrijblijvend informeren"

Lead Form Fields:
1. Voornaam (pre-filled)
2. Email (pre-filled)
3. Telefoonnummer
4. "Wat spreekt je aan?" (multiple choice: Salaris, Groei, Cultuur, Locatie, Anders)

Thank You Screen:
"Bedankt! We nemen binnen 24 uur contact op."
```

## Audience Targeting Templates

### Template A: Direct Match (Active Job Seekers)

```
Targeting:
- Job titles: [Target title] + [Senior/Junior variant] + [Alternative titles]
- Industries: [Target industry] + [Adjacent industries]
- Location: [City] + [Radius km]
- Behaviors: Job seekers (LinkedIn data)
- Age: [Range based on experience level]
- Exclude: Current employees of [Client company]
```

### Template B: Lookalike (Based on Current Employees)

```
Source Audience: Client employee email list (min 100 emails)
Lookalike: 1% Netherlands
Additional Filters:
- Education level: [Minimum requirement]
- Location: [Commutable radius]
```

### Template C: Interest-Based (Passive Candidates)

```
Targeting:
- Interests: [Industry publications], [Professional associations], [Tools/software]
- Job titles: [Current and aspirational titles]
- NOT job seekers (exclude active seeker behavior)
- Engagement: People who engage with career content
```

## Budget Allocation Framework

### Per Vacancy Budget Distribution

| Budget Range | Meta Split | LinkedIn Split | Recommended Duration |
|-------------|-----------|---------------|---------------------|
| €500-1000 | 80% Meta | 20% LinkedIn | 2-3 weeks |
| €1000-2500 | 70% Meta | 30% LinkedIn | 3-4 weeks |
| €2500-5000 | 60% Meta | 40% LinkedIn | 4-6 weeks |
| €5000+ | 50% Meta | 50% LinkedIn | 6-8 weeks |

### Within Meta Budget

| Phase | % of Budget | Duration | Objective |
|-------|-----------|----------|-----------|
| Testing | 20% | Days 1-5 | Run 3 variants, identify winner |
| Scaling | 60% | Days 6-20 | Scale winning variant |
| Retargeting | 20% | Days 10+ | Retarget website visitors who didn't apply |

## A/B Testing Protocol

For every campaign, test these variables in order of impact:

1. **Creative (highest impact):** Image vs. video vs. carousel
2. **Primary Text:** Benefit-led vs. pain-point-led vs. social proof
3. **Audience:** Direct match vs. lookalike vs. interest-based
4. **Placement:** Automatic vs. feed-only vs. stories-only

**Testing Rules:**
- Minimum €50 per variant before drawing conclusions
- Minimum 1000 impressions per variant
- Statistical significance: wait for 95% confidence
- Kill underperformers after 48 hours if CTR < 0.5%

## Reporting Metrics

Track and log these metrics weekly to Supabase:

| Metric | Target (Recruitment) | Formula |
|--------|---------------------|---------|
| CPM | < €8.00 | Cost / (Impressions / 1000) |
| CTR | > 1.2% | Clicks / Impressions |
| CPC | < €2.50 | Cost / Clicks |
| Conversion Rate | > 3% | Applications / Clicks |
| Cost per Application | < €25 | Cost / Applications |
| Cost per Hire | < €500 | Cost / Hires |
| Quality Score | > 60% | Qualified Applications / Total Applications |
