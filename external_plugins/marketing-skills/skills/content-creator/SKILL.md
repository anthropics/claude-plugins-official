---
name: content-creator
description: >
  Create SEO-optimized marketing content with consistent brand voice. Includes
  brand voice analyzer, SEO optimizer, content frameworks, and social media
  templates. Use when writing blog posts, creating social media content,
  analyzing brand voice, optimizing SEO, planning content calendars, or when
  user mentions content creation, brand voice, SEO optimization, social media
  marketing, or content strategy.
license: MIT + Commons Clause
metadata:
  version: 1.0.0
  author: borghei
  category: marketing
  domain: content-marketing
  updated: 2025-10-20
  python-tools: brand_voice_analyzer.py, seo_optimizer.py
  tech-stack: SEO, social-media-platforms
---
# Content Creator

Professional-grade brand voice analysis, SEO optimization, and platform-specific content frameworks.

---

## Table of Contents

- [Keywords](#keywords)
- [Quick Start](#quick-start)
- [Core Workflows](#core-workflows)
- [Tools](#tools)
- [Reference Guides](#reference-guides)
- [Best Practices](#best-practices)
- [Integration Points](#integration-points)

---

## Keywords

content creation, blog posts, SEO, brand voice, social media, content calendar, marketing content, content strategy, content marketing, brand consistency, content optimization, social media marketing, content planning, blog writing, content frameworks, brand guidelines, social media strategy

---

## Quick Start

### Brand Voice Development

1. Run `scripts/brand_voice_analyzer.py` on existing content to establish baseline
2. Review `references/brand_guidelines.md` to select voice attributes
3. Apply chosen voice consistently across all content

### Blog Content Creation

1. Choose template from `references/content_frameworks.md`
2. Research keywords for topic
3. Write content following template structure
4. Run `scripts/seo_optimizer.py [file] [primary-keyword]` to optimize
5. Apply recommendations before publishing

### Social Media Content

1. Review platform best practices in `references/social_media_optimization.md`
2. Use appropriate template from `references/content_frameworks.md`
3. Optimize based on platform-specific guidelines
4. Schedule using `assets/content_calendar_template.md`

---

## Core Workflows

### Workflow 1: Establish Brand Voice (First Time Setup)

For new brands or clients:

**Step 1: Analyze Existing Content (if available)**

```bash
python scripts/brand_voice_analyzer.py existing_content.txt
```

**Step 2: Define Voice Attributes**

- Review brand personality archetypes in `references/brand_guidelines.md`
- Select primary and secondary archetypes
- Choose 3-5 tone attributes
- Document in brand guidelines

**Step 3: Create Voice Sample**

- Write 3 sample pieces in chosen voice
- Test consistency using analyzer
- Refine based on results

### Workflow 2: Create SEO-Optimized Blog Posts

**Step 1: Keyword Research**

- Identify primary keyword (search volume 500-5000/month)
- Find 3-5 secondary keywords
- List 10-15 LSI keywords

**Step 2: Content Structure**

- Use blog template from `references/content_frameworks.md`
- Include keyword in title, first paragraph, and 2-3 H2s
- Aim for 1,500-2,500 words for comprehensive coverage

**Step 3: Optimization Check**

```bash
python scripts/seo_optimizer.py blog_post.md "primary keyword" "secondary,keywords,list"
```

**Step 4: Apply SEO Recommendations**

- Adjust keyword density to 1-3%
- Ensure proper heading structure
- Add internal and external links
- Optimize meta description

### Workflow 3: Create Social Media Content

**Step 1: Platform Selection**

- Identify primary platforms based on audience
- Review platform-specific guidelines in `references/social_media_optimization.md`

**Step 2: Content Adaptation**

- Start with blog post or core message
- Use repurposing matrix from `references/content_frameworks.md`
- Adapt for each platform following templates

**Step 3: Optimization Checklist**

- Platform-appropriate length
- Optimal posting time
- Correct image dimensions
- Platform-specific hashtags
- Engagement elements (polls, questions)

### Workflow 4: Plan Content Calendar

**Step 1: Monthly Planning**

- Copy `assets/content_calendar_template.md`
- Set monthly goals and KPIs
- Identify key campaigns/themes

**Step 2: Weekly Distribution**

- Follow 40/25/25/10 content pillar ratio
- Balance platforms throughout week
- Align with optimal posting times

**Step 3: Batch Creation**

- Create all weekly content in one session
- Maintain consistent voice across pieces
- Prepare all visual assets together

---

## Tools

### Brand Voice Analyzer

Analyzes text content for voice characteristics, readability, and consistency.

**Usage:**

```bash
# Human-readable output
python scripts/brand_voice_analyzer.py content.txt

# JSON output for integrations
python scripts/brand_voice_analyzer.py content.txt json
```

**Parameters:**

| Parameter | Required | Description |
|-----------|----------|-------------|
| `file` | Yes | Path to content file |
| `format` | No | Output format: `text` (default) or `json` |

**Output:**

- Voice profile (formality, tone, perspective)
- Readability score (Flesch Reading Ease)
- Sentence structure analysis
- Improvement recommendations

### SEO Optimizer

Analyzes content for SEO optimization and provides actionable recommendations.

**Usage:**

```bash
# Basic analysis
python scripts/seo_optimizer.py article.md "main keyword"

# With secondary keywords
python scripts/seo_optimizer.py article.md "main keyword" "secondary,keywords,list"

# JSON output
python scripts/seo_optimizer.py article.md "keyword" --json
```

**Parameters:**

| Parameter | Required | Description |
|-----------|----------|-------------|
| `file` | Yes | Path to content file (md or html) |
| `primary_keyword` | Yes | Main target keyword |
| `secondary_keywords` | No | Comma-separated secondary keywords |
| `--json` | No | Output in JSON format |

**Output:**

- SEO score (0-100)
- Keyword density analysis
- Structure assessment
- Meta tag suggestions
- Specific optimization recommendations

---

## Reference Guides

### When to Use Each Reference

**references/brand_guidelines.md**

- Setting up new brand voice
- Ensuring consistency across content
- Training new team members
- Resolving voice/tone questions

**references/content_frameworks.md**

- Starting any new content piece
- Structuring different content types
- Creating content templates
- Planning content repurposing

**references/social_media_optimization.md**

- Platform-specific optimization
- Hashtag strategy development
- Understanding algorithm factors
- Setting up analytics tracking

**references/analytics_guide.md**

- Tracking content performance
- Setting up measurement frameworks
- Creating performance reports
- Attribution modeling

---

## Best Practices

### Content Creation Process

1. Start with audience need/pain point
2. Research before writing
3. Create outline using templates
4. Write first draft without editing
5. Optimize for SEO
6. Edit for brand voice
7. Proofread and fact-check
8. Optimize for platform
9. Schedule strategically

### Quality Indicators

- SEO score above 75/100
- Readability appropriate for audience
- Consistent brand voice throughout
- Clear value proposition
- Actionable takeaways
- Proper visual formatting
- Platform-optimized

### Common Pitfalls to Avoid

- Writing before researching keywords
- Ignoring platform-specific requirements
- Inconsistent brand voice
- Over-optimizing for SEO (keyword stuffing)
- Missing clear CTAs
- Publishing without proofreading
- Ignoring analytics feedback

---

## Integration Points

This skill works best with:

- **Analytics platforms** - Google Analytics, social media insights for tracking (see `references/analytics_guide.md`)
- **SEO tools** - For keyword research and competitive analysis
- **Design tools** - Canva, Figma for visual content
- **Scheduling platforms** - Buffer, Hootsuite for content distribution
- **Email marketing systems** - For newsletter content campaigns

---

## Troubleshooting

| Problem | Likely Cause | Solution |
|---------|-------------|----------|
| SEO score is low despite keyword inclusion | Keywords present but not in strategic positions (title, H1, first paragraph, H2s) | Place primary keyword in the first paragraph, at least one H2, and the page title. Keyword density alone is no longer a ranking factor -- placement and natural integration matter more in 2026 |
| Brand voice analyzer shows inconsistent results across content | Multiple authors writing without shared voice guidelines | Establish a baseline by running `brand_voice_analyzer.py` on your best-performing content. Document the formality score, tone, and perspective as your target profile. Have all authors reference this baseline |
| Content ranks initially then drops | Thin content or lack of E-E-A-T signals | Google's December 2025 core update and helpful content system penalize shallow content. Add first-person experience, original data (3+ fresh statistics per 1,000 words), expert quotes, and case studies. Content must demonstrate Experience that AI cannot replicate |
| AI-generated content flagged or not ranking | Unedited AI output lacking human oversight, expertise, or originality | Google does not penalize AI-assisted content per se, but mass-produced AI content without human review, original perspective, or expertise signals will underperform. Always add personal experience, proprietary data, and fact-checked claims. Layer in E-E-A-T signals: author bylines with credentials, cited sources, real examples |
| SEO optimizer recommends increasing keyword density above 3% | Legacy recommendation conflicting with current best practice | Override any density target above 2%. A 2026 study of 1,500+ Google results found no correlation between keyword density and ranking. Pages in the top 10 have 50% lower keyword density than two years ago. Focus on topical coverage and semantic relevance instead |
| Content not winning featured snippets | Missing concise answer format near the top of the page | Provide a 2-3 sentence direct answer to the core question within the first 120-150 words. Use short paragraphs (2-4 sentences), bulleted lists, and clear H2/H3 subheadings. Featured snippets have 42.9% CTR -- the highest of any SERP feature |
| Social media content underperforming despite good blog content | Direct copy-paste without platform adaptation | Each platform requires format-specific adaptation. LinkedIn favors 1,300-character posts with carousel documents (21.77% median engagement rate). Instagram prioritizes visual-first carousel posts. TikTok requires short-form video. Use the repurposing matrix in `references/content_frameworks.md` |

---

## Success Criteria

- **SEO Score**: Achieve 75+/100 on the SEO optimizer for all published content. Top-performing content averages 80-90. Track scores before and after optimization to measure improvement
- **Content Length**: Target 1,500-2,500 words for comprehensive blog posts. Top-10 Google results average 1,447 words; position-1 results average 1,890 words. Content over 3,000 words wins 3x more traffic and 4x more shares but requires strong structure
- **Keyword Placement**: Primary keyword must appear in the page title, first paragraph, and at least one H2. Keyword density between 1-2% (not higher). Secondary keywords should appear naturally throughout with no forced repetition
- **Readability**: Target Flesch Reading Ease score of 60-70 for general audiences (8th-9th grade level). B2B technical content can target 40-55. Sentence variety should be rated "medium" or "high" by the brand voice analyzer
- **E-E-A-T Compliance**: Every piece of content must include at least one first-person experience element, 3+ cited statistics per 1,000 words, and author attribution with relevant credentials. This is non-negotiable for ranking in 2026 following Google's helpful content updates
- **Brand Voice Consistency**: Maintain consistent formality, tone, and perspective scores across all content pieces as measured by `brand_voice_analyzer.py`. Variance of more than 15 points in formality score between pieces indicates inconsistency
- **Content Calendar Adherence**: Follow the 40/25/25/10 content pillar ratio (educational/thought leadership/product/promotional). Publish at minimum 2-4 blog posts per month and 5-7 social posts per week across primary platforms

---

## Scope & Limitations

**In Scope:**
- Brand voice analysis: formality scoring, tone detection, perspective analysis, readability (Flesch Reading Ease), sentence structure analysis
- SEO content optimization: keyword density, content structure evaluation, meta tag suggestions, heading analysis, link audit, SEO score (0-100)
- Content framework guidance via reference documents (blog templates, social media formats, email structures)
- Content calendar planning and platform-specific optimization guidance

**Out of Scope:**
- AI content generation (this skill analyzes and optimizes content, it does not generate it)
- Keyword research and search volume data (use dedicated SEO tools like Ahrefs, SEMrush, or Moz, or the app-store-optimization skill for mobile)
- Image or video creation and optimization (use design tools like Canva or Figma)
- Social media scheduling and publishing (use Buffer, Hootsuite, or native platform tools)
- Backlink analysis and link building (requires external SEO tools)
- Real-time SERP tracking or rank monitoring
- AI content detection scoring (Google does not penalize AI content by detection alone; focus on quality signals instead)

---

## Integration Points

| Integration | Purpose | How to Connect |
|-------------|---------|----------------|
| **Google Search Console** | Monitor indexing, search queries, CTR, and position data | Use Search Console data to identify underperforming pages, then run `seo_optimizer.py` to diagnose and fix issues. Track position changes after optimization |
| **Google Analytics 4 (GA4)** | Content performance measurement, engagement metrics | Measure page views, time on page, bounce rate, and conversions per content piece. Feed insights back into content strategy decisions |
| **SEO Tools (Ahrefs, SEMrush, Moz)** | Keyword research, backlink data, competitive analysis | Export target keywords from SEO tools to use as input for `seo_optimizer.py`. Use competitive gap analysis to inform content topics |
| **CMS Platforms (WordPress, Webflow, Ghost)** | Content publishing and meta tag implementation | Apply meta tag suggestions from `seo_optimizer.py` directly to CMS fields. Implement heading structure recommendations in post editor |
| **social-media-analyzer skill** | Social content performance tracking | Analyze which content formats and topics perform best on social, then use findings to inform content creation priorities |
| **campaign-analytics skill** | Content ROI measurement | Track content-attributed conversions through campaign analytics. Identify which content pieces drive the most pipeline or revenue |
| **app-store-optimization skill** | App description writing | Apply SEO writing principles and brand voice consistency to app store descriptions using shared voice guidelines |

---

## Tool Reference

### brand_voice_analyzer.py

**Type:** CLI script (positional arguments, no argparse flags)

**Usage:**
```bash
python brand_voice_analyzer.py <file> [format]
```

| Argument | Position | Required | Default | Description |
|----------|----------|----------|---------|-------------|
| `file` | 1st | Yes | -- | Path to text content file to analyze |
| `format` | 2nd | No | `text` | Output format: `text` (human-readable) or `json` (machine-readable) |

**Output Fields:**
- `word_count` -- Total words in content
- `readability_score` -- Flesch Reading Ease (0-100). Below 30 = difficult, 30-60 = moderate, 60-70 = standard, 70+ = easy
- `voice_profile` -- Per-dimension analysis:
  - `formality` -- Dominant: formal or casual (based on keyword matching)
  - `tone` -- Dominant: professional or friendly
  - `perspective` -- Dominant: authoritative or conversational
- `sentence_analysis` -- Average sentence length (words), variety (low/medium/high), total count
- `recommendations` -- Actionable suggestions for readability, sentence variety, and voice consistency

### seo_optimizer.py

**Type:** CLI script (positional arguments with one optional flag)

**Usage:**
```bash
python seo_optimizer.py <file> [primary_keyword] [secondary_keywords] [--json]
```

| Argument | Position/Flag | Required | Default | Description |
|----------|--------------|----------|---------|-------------|
| `file` | 1st | Yes | -- | Path to content file (markdown or HTML) |
| `primary_keyword` | 2nd | No | None | Main target keyword for density and placement analysis |
| `secondary_keywords` | 3rd | No | None | Comma-separated secondary keywords (e.g., `"seo,content,optimization"`) |
| `--json` | Flag | No | text output | Output raw JSON instead of human-readable format |

**Output Fields:**
- `optimization_score` -- Overall SEO score (0-100). Scoring: content length (20 pts), keyword optimization (30 pts), structure (25 pts), readability (25 pts)
- `content_length` -- Word count
- `keyword_analysis`:
  - `primary_keyword` -- Count, density (0-1 scale), in_first_paragraph (bool), in_headings (bool)
  - `secondary_keywords` -- Per-keyword count and density
  - `lsi_keywords` -- Top 10 semantically related terms extracted from content
- `structure_analysis` -- Heading counts (h1/h2/h3), paragraph count, average paragraph length, list count, internal/external link counts
- `readability` -- Score (0-100), level (Easy/Moderate/Difficult/Very Difficult), average sentence length
- `meta_suggestions` -- Generated title, meta description, URL slug, Open Graph tags
- `recommendations` -- Prioritized list of specific improvement actions
