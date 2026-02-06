---
name: campaign-strategy
description: This skill should be used when the user wants to "create a recruitment campaign", "plan LinkedIn content", "write Meta ad copy", "build a 12-week campaign", "generate recruitment posts", "create employer branding content", "plan authority content for Recruitin", "generate visual prompts for ads", or needs guidance on campaign planning, content calendars, tone-of-voice selection, or multi-channel recruitment marketing strategy.
version: 0.1.0
---

# Campaign Strategy for Recruitin Growth Engine

The Campaign Strategy skill powers the Creative-Strategic Loop of the Recruitin Growth Intelligence Engine. It produces two distinct campaign types: authority campaigns for Recruitin's own brand, and performance campaigns for client vacancies.

## Campaign Types

### Authority Campaigns (Recruitin Brand)

Purpose: Position Recruitin as thought leader in recruitment marketing on LinkedIn.

**12-Week Planning Cycle:**

| Weeks | Phase | Content Focus |
|-------|-------|---------------|
| 1-3 | Foundation | Industry insights, recruitment trends, data-backed observations |
| 4-6 | Authority | Case studies, methodology reveals, contrarian takes on hiring |
| 7-9 | Engagement | Polls, Q&A series, client testimonials, behind-the-scenes |
| 10-12 | Conversion | Lead magnets, free audits, consultation CTAs |

**Weekly Output Per Cycle:**
- 2 LinkedIn posts (mix of text-only and carousel/image)
- 1 LinkedIn article or newsletter edition (bi-weekly)
- 1 visual prompt specification for image/video generation
- 1 engagement action plan (comment strategy, DM outreach targets)

### Performance Campaigns (Client Vacancies)

Purpose: Drive qualified applicants to client job openings via Meta Ads and LinkedIn.

**Campaign Structure Per Vacancy:**

1. **Audience Definition** - Define target persona: job title, experience level, industry, geographic radius, pain points in current role
2. **Message Matrix** - Create 3 ad variants per campaign:
   - Variant A: Benefit-led (salary, growth, culture)
   - Variant B: Pain-point-led (escape current frustrations)
   - Variant C: Social proof (team testimonials, company achievements)
3. **Channel Allocation** - Recommend budget split between Meta and LinkedIn based on target audience behavior
4. **Visual Prompt Generation** - For each variant, produce a detailed visual prompt specification

## Content Generation Rules

### Tone-of-Voice Framework

Maintain a tone-of-voice registry per client and for Recruitin itself:

- **Recruitin Default:** Professional but approachable, data-informed, occasionally bold/contrarian. No corporate jargon. Short sentences. Dutch language with English terms where industry-standard.
- **Client Profiles:** Store per-client tone preferences in Supabase. Before generating content, query the `client_brand_voices` table.

### LinkedIn Post Structure

Follow this template for authority posts:

```
[Hook Line - max 150 characters, pattern-interrupt]

[Empty line]

[Body - 3-5 short paragraphs, each max 3 sentences]
- Use line breaks generously
- Include 1 data point or specific number
- End with a question or call-to-action

[Empty line]

[3-5 relevant hashtags]
```

### Meta Ad Copy Structure

```
Primary Text (125 chars max):
[Pain point or benefit + clear CTA]

Headline (40 chars max):
[Job title + key differentiator]

Description (30 chars max):
[Urgency or social proof element]

Link Description:
[Simple action: "Solliciteer direct" / "Bekijk vacature"]
```

### Visual Prompt Specification

For every content piece, generate a companion visual prompt:

```
Platform: [LinkedIn / Meta / Both]
Format: [1:1 Square / 4:5 Portrait / 16:9 Landscape / Carousel]
Style: [Photography / Illustration / Typography / Data visualization]
Primary Subject: [Description of main visual element]
Brand Colors: [Reference client or Recruitin brand palette]
Text Overlay: [Any text to include on the image]
Mood: [Professional / Energetic / Warm / Bold]
Tool Recommendation: [PiAPI / Canva / Midjourney / DALL-E]
```

## Workflow Integration

### Before Generating Content

1. Query Supabase `campaign_performance` table for historical results in the same industry/role
2. Check `winning_strategies` view for top-performing tone-of-voice and content-type combinations
3. Load client brand voice from `client_brand_voices` table
4. Review the current 12-week cycle position to maintain strategic coherence
5. **Check market intelligence:** Query `market_intelligence` table for latest vacancy volumes, salary trends, and ghosting risks in the target keyword/region
6. **Check competitor activity:** Query latest concurrent tracker data to avoid topic overlap and find content gaps
7. **Check ICP signals:** Query `icp_scores` for high-scoring prospects and use their hiring signals as campaign context
8. **Select content style:** Use the 4 proven Notion styles (contrarian, data_story, how_to, behind_scenes) matched to the current 12-week phase — see `references/content-styles-notion.md`

### After Generating Content

1. Log the generated content metadata to Supabase `content_log` table
2. Include campaign_id, content_type, tone_of_voice, target_audience, and visual_prompt fields
3. Tag with predicted performance tier based on historical similarity

## ICP Definition Templates

### Recruitin's Own ICP (Authority Campaigns)

- **Primary:** HR Directors and Talent Acquisition Managers at companies with 50-500 employees in the Netherlands
- **Secondary:** Marketing Directors at staffing agencies looking to modernize their recruitment approach
- **Tertiary:** Founders/CEOs of scale-ups experiencing rapid hiring needs

### Client Vacancy ICP (Performance Campaigns)

Construct per-vacancy using this framework:

| Dimension | Questions to Answer |
|-----------|-------------------|
| Demographics | Age range, education level, geographic area |
| Professional | Current job title, years experience, industry |
| Psychographics | Career motivations, frustrations, ambitions |
| Behavioral | Active/passive job seeker, platform usage, content consumption |
| Decision Factors | Salary expectations, remote preference, growth opportunities |

## Quality Criteria

Every generated piece must pass these checks:

- [ ] Matches the registered tone-of-voice for the target brand
- [ ] Contains at least one specific data point or concrete detail
- [ ] Has a clear call-to-action appropriate to the campaign phase
- [ ] Visual prompt is complete and platform-appropriate
- [ ] No generic filler phrases ("in today's competitive market", "passionate team player")
- [ ] Dutch language is natural and conversational, not translated-sounding
