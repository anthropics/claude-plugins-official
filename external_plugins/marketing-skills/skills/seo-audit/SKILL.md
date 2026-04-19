---
name: seo-audit
description: >
  Comprehensive technical SEO auditing covering crawlability, indexation, Core
  Web Vitals, on-page optimization, content quality, and competitive gap
  analysis. Includes 85-point audit checklist, severity-weighted scoring, and
  prioritized remediation plans.
license: MIT + Commons Clause
metadata:
  version: 1.0.0
  author: borghei
  category: marketing-growth
  updated: 2026-03-31
  tags:
    - seo
    - audit
    - technical-seo
    - core-web-vitals
    - indexation
    - crawl-analysis
---
# SEO Audit

Production-grade SEO audit framework with an 85-point checklist across 8 dimensions, severity-weighted scoring, automated diagnostic workflows, and prioritized remediation plans. Covers technical SEO, on-page optimization, content quality, competitive positioning, and migration readiness.

---

## Table of Contents

- [Operating Modes](#operating-modes)
- [Initial Assessment](#initial-assessment)
- [The 85-Point Audit Checklist](#the-85-point-audit-checklist)
- [Severity-Weighted Scoring](#severity-weighted-scoring)
- [Core Web Vitals Deep Dive](#core-web-vitals-deep-dive)
- [Crawl and Indexation Analysis](#crawl-and-indexation-analysis)
- [On-Page SEO Analysis](#on-page-seo-analysis)
- [Content Quality Assessment](#content-quality-assessment)
- [Competitive Gap Analysis](#competitive-gap-analysis)
- [Migration Audit Checklist](#migration-audit-checklist)
- [Prioritized Remediation Plan](#prioritized-remediation-plan)
- [Output Artifacts](#output-artifacts)
- [Related Skills](#related-skills)

---

## Operating Modes

### Mode 1: Full Site Audit
Comprehensive audit across all 8 dimensions. Use for initial assessment or annual reviews.

### Mode 2: Focused Audit
Single-dimension deep dive. Use when the problem area is already identified (e.g., "our Core Web Vitals are failing" or "we have indexation issues").

### Mode 3: Pre-Migration Audit
Checklist for planned URL changes, platform switches, or redesigns. Establishes baseline and creates the redirect mapping framework.

### Mode 4: Traffic Drop Diagnosis
Emergency diagnostic when organic traffic drops. Follows the traffic drop decision tree to isolate the cause.

---

## Initial Assessment

### Required Context

| Question | Why It Matters |
|----------|---------------|
| What type of site? (SaaS, e-commerce, blog, local business) | Determines which audit dimensions to weight |
| What is the primary SEO goal? | Focuses the audit on business-relevant outcomes |
| What is the current organic traffic baseline? | Establishes the benchmark for measuring improvement |
| Any recent changes? (migration, redesign, content update, algorithm update) | Identifies potential cause of current issues |
| Do you have Google Search Console access? | Essential for indexation and performance data |
| Who are 3 organic competitors? | For competitive gap analysis |

### Scope Definition

| Scope | Pages to Audit | Recommended When |
|-------|---------------|-----------------|
| Full site | All indexed pages + sample of non-indexed | Annual audit, new client onboarding |
| Section audit | One directory or content type | Known problem area |
| Top pages | Top 50 by traffic + top 50 by impressions | Quick wins identification |
| New pages | Pages published in last 90 days | Content quality check |

---

## The 85-Point Audit Checklist

### Dimension 1: Crawlability (12 points)

| # | Check | Severity | Pass Criteria |
|---|-------|----------|---------------|
| 1.1 | robots.txt accessible and valid | Critical | 200 response, no syntax errors |
| 1.2 | Important pages not blocked by robots.txt | Critical | No disallow rules for key pages |
| 1.3 | XML sitemap exists and is valid | High | Submitted in GSC, < 50K URLs per file |
| 1.4 | Sitemap reflects actual site structure | High | No 404s, no redirects, no noindex pages in sitemap |
| 1.5 | Crawl depth < 4 clicks from homepage | Medium | 95%+ of pages within 3 clicks |
| 1.6 | No infinite crawl traps | Critical | No parameter-based infinite loops |
| 1.7 | Internal links use crawlable HTML | High | No JavaScript-only navigation |
| 1.8 | Pagination uses rel=next/prev or load-more | Medium | Paginated content is crawlable |
| 1.9 | No orphan pages (indexed but no internal links) | High | 0 orphan pages in indexed set |
| 1.10 | Crawl budget not wasted on low-value pages | Medium | < 10% crawl budget on utility pages |
| 1.11 | Server response time < 500ms | High | TTFB < 500ms for 95% of pages |
| 1.12 | No 5xx errors in crawl | Critical | 0% server errors |

### Dimension 2: Indexation (10 points)

| # | Check | Severity | Pass Criteria |
|---|-------|----------|---------------|
| 2.1 | Target pages are indexed | Critical | > 95% of target pages in Google index |
| 2.2 | No duplicate content issues | High | No duplicate titles, no near-duplicate content |
| 2.3 | Canonical tags implemented correctly | High | Self-referencing on unique pages, cross-domain where needed |
| 2.4 | No conflicting signals (canonical vs noindex vs sitemap) | Critical | No page that is both noindex and in sitemap |
| 2.5 | Hreflang tags correct (if multilingual) | High | Valid hreflang with return tags |
| 2.6 | No index bloat (unnecessary pages indexed) | Medium | Utility pages not indexed |
| 2.7 | Thin content pages identified | High | No pages with < 200 words of unique content |
| 2.8 | Parameter handling configured | Medium | URL parameters handled in GSC or via canonical |
| 2.9 | JavaScript-rendered content indexable | High | Key content visible in cached/rendered version |
| 2.10 | New pages getting indexed within 7 days | Medium | Using IndexNow or manual submission |

### Dimension 3: Core Web Vitals (10 points)

| # | Check | Severity | Pass Criteria |
|---|-------|----------|---------------|
| 3.1 | LCP < 2.5s | High | 75th percentile of page loads |
| 3.2 | INP < 200ms | High | 75th percentile of interactions |
| 3.3 | CLS < 0.1 | High | 75th percentile of page loads |
| 3.4 | Mobile CWV passing | Critical | Mobile scores meeting thresholds |
| 3.5 | Desktop CWV passing | Medium | Desktop scores meeting thresholds |
| 3.6 | No render-blocking resources | Medium | CSS/JS delivery optimized |
| 3.7 | Images optimized (WebP/AVIF, lazy loading) | Medium | All above-fold images preloaded |
| 3.8 | Font loading optimized | Low | No FOUT/FOIT, font-display: swap |
| 3.9 | Third-party script impact measured | Medium | No third-party scripts adding > 500ms |
| 3.10 | HTTPS with no mixed content | Critical | All resources served over HTTPS |

### Dimension 4: On-Page SEO (15 points)

| # | Check | Severity | Pass Criteria |
|---|-------|----------|---------------|
| 4.1 | Unique title tags on every page | Critical | No duplicates, < 60 chars |
| 4.2 | Title includes primary keyword | High | Keyword in first 60 chars |
| 4.3 | Unique meta descriptions | High | No duplicates, < 155 chars, includes keyword |
| 4.4 | H1 tag present and unique per page | High | One H1 per page with primary keyword |
| 4.5 | Heading hierarchy logical (H1 > H2 > H3) | Medium | No skipped levels |
| 4.6 | Internal links with descriptive anchor text | High | No "click here" or naked URLs |
| 4.7 | Images have alt text | Medium | Descriptive alt text on all meaningful images |
| 4.8 | URL structure is clean and descriptive | Medium | No IDs, parameters, or excessive depth |
| 4.9 | Primary keyword in first 100 words | Medium | Natural inclusion in opening |
| 4.10 | Content matches search intent | Critical | Page type matches what Google ranks for query |
| 4.11 | No keyword cannibalization | High | No two pages targeting the same primary keyword |
| 4.12 | Open Graph and Twitter Card tags | Low | Social sharing metadata present |
| 4.13 | Structured data implemented | Medium | Relevant schema types present |
| 4.14 | Internal links to relevant pages | High | 3-5 contextual internal links per content page |
| 4.15 | Breadcrumbs present | Medium | Functional breadcrumbs with schema |

### Dimension 5: Content Quality (12 points)

| # | Check | Severity | Pass Criteria |
|---|-------|----------|---------------|
| 5.1 | Content provides unique value | Critical | Not available elsewhere in same form |
| 5.2 | Content depth matches intent | High | Comprehensive coverage of the topic |
| 5.3 | Content freshness appropriate | Medium | Updated within last 12 months for evergreen |
| 5.4 | No AI-generated content markers | High | No generic filler, overused phrases, or em-dash patterns |
| 5.5 | E-E-A-T signals present | High | Author attribution, credentials, experience evidence |
| 5.6 | Content readability appropriate | Medium | Matches target audience reading level |
| 5.7 | No thin content pages | High | All pages > 300 words of unique content |
| 5.8 | No content duplication across pages | High | Jaccard similarity < 50% between any two pages |
| 5.9 | Content supports conversion goal | Medium | Clear CTA aligned with page intent |
| 5.10 | Visual content present | Medium | Images, charts, or videos enhance understanding |
| 5.11 | Content organized with subheadings | Medium | Scannable structure with clear sections |
| 5.12 | External references and citations | Low | Links to authoritative sources where relevant |

### Dimension 6: Technical Infrastructure (10 points)

| # | Check | Severity | Pass Criteria |
|---|-------|----------|---------------|
| 6.1 | HTTPS properly configured | Critical | Valid certificate, no mixed content |
| 6.2 | Proper redirects (301 not 302) | High | Permanent redirects for permanent moves |
| 6.3 | No redirect chains (> 2 hops) | Medium | Direct redirect from origin to destination |
| 6.4 | No broken internal links (404s) | High | 0 broken internal links |
| 6.5 | No broken external links | Low | < 5% broken outbound links |
| 6.6 | Mobile-responsive design | Critical | Passes Google's mobile-friendly test |
| 6.7 | Proper 404 page | Low | Custom 404 with navigation and search |
| 6.8 | Server uptime > 99.9% | Critical | Monitoring in place |
| 6.9 | CDN configured for global audience | Medium | If international traffic > 20% |
| 6.10 | Security headers present | Low | HSTS, CSP, X-Frame-Options |

### Dimension 7: Off-Page Signals (8 points)

| # | Check | Severity | Pass Criteria |
|---|-------|----------|---------------|
| 7.1 | Backlink profile health | High | No toxic link patterns |
| 7.2 | Referring domain diversity | Medium | > 50 unique referring domains |
| 7.3 | Anchor text distribution natural | Medium | < 30% exact-match anchors |
| 7.4 | No manual actions in GSC | Critical | Clean manual actions report |
| 7.5 | Google Business Profile (if local) | High | Claimed, verified, complete |
| 7.6 | Social profiles linked | Low | Active profiles on major platforms |
| 7.7 | Brand mentions without links | Low | Unlinked mentions as link opportunities |
| 7.8 | Competitor link gap identified | Medium | Top competitors' link sources mapped |

### Dimension 8: Analytics and Tracking (8 points)

| # | Check | Severity | Pass Criteria |
|---|-------|----------|---------------|
| 8.1 | Google Search Console verified | Critical | All properties verified |
| 8.2 | GA4 properly configured | High | Events tracking, no duplicate tags |
| 8.3 | Conversion tracking in place | High | Key conversions tracked |
| 8.4 | GSC and GA4 linked | Medium | Data flowing between tools |
| 8.5 | Bing Webmaster Tools configured | Low | Verified and sitemap submitted |
| 8.6 | Search Console coverage report clean | High | No unexpected errors |
| 8.7 | Core Web Vitals field data available | Medium | Enough traffic for CrUX data |
| 8.8 | UTM parameter strategy | Low | Consistent campaign tracking |

---

## Severity-Weighted Scoring

### Scoring Formula

```
Total Score = Sum of (Dimension Weight x Dimension Pass Rate)

Dimension Pass Rate = (Passed Checks x Severity Multiplier) / (Total Checks x Severity Multiplier)

Severity Multipliers:
  Critical = 4x
  High = 3x
  Medium = 2x
  Low = 1x
```

### Overall Health Grades

| Score | Grade | Assessment |
|-------|-------|-----------|
| 90-100 | A | Excellent -- focus on competitive edge |
| 80-89 | B | Good -- fix remaining high-priority items |
| 70-79 | C | Fair -- significant improvements available |
| 60-69 | D | Poor -- critical issues blocking performance |
| < 60 | F | Failing -- foundational problems require immediate attention |

---

## Core Web Vitals Deep Dive

### LCP Optimization Priority Stack

| Cause | Detection | Fix | Impact |
|-------|-----------|-----|--------|
| Slow server response | TTFB > 600ms | CDN, server upgrade, caching | High |
| Render-blocking CSS/JS | PageSpeed Insights flags | Inline critical CSS, defer JS | High |
| Large hero image | LCP element is an image > 500KB | WebP/AVIF, responsive sizes, preload | High |
| Client-side rendering | LCP requires JS execution | SSR or prerendering | Medium |
| Web font blocking | FOUT delays LCP text | font-display: swap, preload fonts | Medium |

### INP Optimization Priority Stack

| Cause | Detection | Fix | Impact |
|-------|-----------|-----|--------|
| Long JavaScript tasks | Chrome DevTools Performance tab | Break into smaller tasks, use requestIdleCallback | High |
| Heavy event handlers | Slow click/scroll responses | Debounce, optimize handler code | High |
| Main thread blocking | Third-party scripts | Defer or lazy-load third-party JS | Medium |
| Layout thrashing | Forced reflows on interaction | Batch DOM reads/writes | Medium |

### CLS Optimization Priority Stack

| Cause | Detection | Fix | Impact |
|-------|-----------|-----|--------|
| Images without dimensions | CLS in PageSpeed Insights | Add width/height attributes | High |
| Dynamic content injection | Ads, embeds loading late | Reserve space with CSS aspect-ratio | High |
| Web fonts causing reflow | Text shifts when font loads | font-display: optional or swap | Medium |
| Late-loading CSS | Styles applied after render | Inline critical CSS | Medium |

---

## Crawl and Indexation Analysis

### Indexation Gap Analysis

Compare these three data sets to find gaps:

```
Set A: Pages in XML sitemap (your intended index)
Set B: Pages indexed in Google (site: query + GSC Coverage)
Set C: Pages receiving organic traffic (GSC Performance)

A - B = Submitted but not indexed (quality or crawl issue)
B - A = Indexed but not in sitemap (orphan or forgotten pages)
B - C = Indexed but receiving zero traffic (rank 100+ or deindexed from results)
```

### Traffic Drop Decision Tree

```
Traffic dropped →
  ├── Sitewide drop?
  │   ├── Yes → Check for manual action in GSC
  │   │         Check for algorithm update (timeline match?)
  │   │         Check for robots.txt or noindex changes
  │   │         Check server uptime/5xx errors
  │   └── No (specific pages/sections) →
  │       ├── Check for cannibalization (new page stealing from old)
  │       ├── Check for content freshness (competitor updated, you didn't)
  │       ├── Check for lost backlinks to those pages
  │       └── Check for SERP feature changes (new featured snippet, AI overview)
  └── Gradual decline vs sudden drop?
      ├── Sudden → Technical issue or algorithm update
      └── Gradual → Content decay, competitive pressure, or authority erosion
```

---

## On-Page SEO Analysis

### Keyword Cannibalization Detection

Two or more pages targeting the same keyword compete with each other. Detection method:

1. Export all pages + their primary keyword from GSC (queries with most impressions per page)
2. Group by keyword -- any keyword assigned to 2+ pages is cannibalized
3. Check which page ranks higher for each cannibalized keyword
4. Action: Consolidate (merge into one page), differentiate (change one page's target), or canonical (point one to the other)

### Intent Match Scoring

For each target keyword, verify that your page type matches what Google actually ranks:

| Google Ranks | Your Page Type | Match? | Action |
|-------------|---------------|--------|--------|
| Listicles | Single product page | No | Create a listicle targeting this keyword |
| How-to guides | Blog opinion piece | No | Restructure as how-to |
| Comparison tables | Feature page | Partial | Add comparison elements |
| Videos | Text-only page | No | Add video or target a different keyword |

---

## Content Quality Assessment

### AI Content Detection Signals

Watch for these patterns that signal low-quality AI-generated content:

| Signal | Example | Fix |
|--------|---------|-----|
| Excessive em dashes | "The tool -- which is powerful -- delivers results" | Use commas or periods |
| Filler hedging | "It's important to note that..." | Delete and get to the point |
| Generic superlatives | "This groundbreaking, cutting-edge solution" | Use specific, evidence-based language |
| Perfect paragraph symmetry | Every section has exactly 3 paragraphs of 4 sentences | Vary structure naturally |
| No first-person experience | Zero personal anecdotes or experience markers | Add genuine experience signals |
| Overused transitions | "Furthermore", "Moreover", "Additionally" at every paragraph | Vary connectors or remove them |

### E-E-A-T Scoring

| Signal | Weight | Check |
|--------|--------|-------|
| Author byline with credentials | High | Named author with bio and expertise |
| Author page with sameAs links | High | Links to LinkedIn, publications |
| Original research or data | High | First-party data, surveys, experiments |
| Experience evidence | High | Screenshots, photos, personal narrative |
| Citations to authoritative sources | Medium | Links to primary sources |
| Publication date and update date | Medium | Visible and accurate |
| About page with team credentials | Medium | Company expertise established |
| External reviews and mentions | Low | Third-party validation |

---

## Competitive Gap Analysis

### Framework

For each of your top 3 competitors, compare:

| Dimension | Your Site | Competitor 1 | Competitor 2 | Competitor 3 |
|-----------|----------|-------------|-------------|-------------|
| Domain Rating | | | | |
| Indexed pages | | | | |
| Organic keywords (top 100) | | | | |
| Estimated organic traffic | | | | |
| Content publishing frequency | | | | |
| Avg content depth (word count) | | | | |
| Referring domains | | | | |
| Top-performing content types | | | | |

### Keyword Gap Priority Matrix

| Gap Type | Description | Priority |
|----------|-------------|----------|
| Uncontested | Keyword with volume, no competitor ranks | Highest |
| Weak competition | You could realistically rank page 1 | High |
| Content gap | Competitor has content, you don't | Medium |
| Quality gap | Both have content, theirs ranks better | Medium |
| Authority gap | Competitor's DR advantage is the barrier | Lower (long-term) |

---

## Migration Audit Checklist

### Pre-Migration (2-4 weeks before)

- [ ] Crawl entire current site and export all URLs
- [ ] Map every old URL to its new URL (1:1 redirect mapping)
- [ ] Export current rankings and organic traffic baseline
- [ ] Document all existing 301 redirects (chain them to new destinations)
- [ ] Verify robots.txt will be correct on new site
- [ ] Verify XML sitemap will be updated
- [ ] Test new site in staging environment
- [ ] Verify all schema markup transfers to new templates

### During Migration

- [ ] Implement all 301 redirects
- [ ] Submit updated XML sitemap to GSC
- [ ] Verify robots.txt is not blocking critical pages
- [ ] Test 50 sample redirects for correctness
- [ ] Monitor server errors in real-time

### Post-Migration (2-8 weeks after)

- [ ] Monitor GSC Coverage report daily for 2 weeks
- [ ] Track organic traffic vs. baseline daily
- [ ] Check for crawl errors in GSC
- [ ] Verify old URLs redirect correctly (batch test)
- [ ] Monitor rankings for top 50 keywords
- [ ] Check for broken internal links on new site
- [ ] Verify analytics tracking is firing correctly

---

## Prioritized Remediation Plan

### Priority Framework

Every finding gets classified:

| Priority | Criteria | Timeline |
|----------|----------|----------|
| P0 Emergency | Blocking indexation or causing active ranking loss | Fix today |
| P1 Critical | Major negative impact on rankings or traffic | Fix this week |
| P2 High | Significant improvement potential | Fix this month |
| P3 Medium | Moderate improvement, standard best practice | Fix this quarter |
| P4 Low | Minor improvement or nice-to-have | Backlog |

### Remediation Plan Template

| # | Finding | Dimension | Severity | Current State | Recommended Fix | Expected Impact | Effort |
|---|---------|-----------|----------|--------------|----------------|-----------------|--------|
| 1 | | | | | | | |
| 2 | | | | | | | |

---

## Output Artifacts

| Artifact | Format | Description |
|----------|--------|-------------|
| Executive Summary | 3-5 bullet points | Overall grade, top issues, quick wins |
| Full Audit Report | 85-point checklist | Pass/fail per check with evidence |
| Severity Scorecard | Weighted score table | Per-dimension scores and overall grade |
| Prioritized Fix List | Ranked table | Every finding with severity, fix, effort, impact |
| Keyword Cannibalization Map | Table | Pages competing for same keywords with resolution action |
| Competitive Gap Report | Comparison matrix | Your site vs. 3 competitors across 8 dimensions |
| Migration Checklist | Checkbox list | Pre/during/post migration tasks |

---

## Related Skills

- **programmatic-seo** -- Use when audit reveals keyword gap clusters that could be addressed with template-based page generation at scale.
- **schema-markup** -- Use when audit reveals missing or broken structured data opportunities.
- **site-architecture** -- Use when audit uncovers structural issues (orphan pages, deep nesting, poor internal linking) requiring architectural redesign.
- **content-creator** -- Use when audit reveals content quality issues requiring editorial improvement.
- **competitor-alternatives** -- Use when competitive gap analysis reveals positioning opportunities for comparison content.

---

## Troubleshooting

| Problem | Likely Cause | Fix |
|---------|-------------|-----|
| Sitewide traffic drop after algorithm update | Core update changed quality thresholds or E-E-A-T weight | Run full E-E-A-T audit, compare content against newly ranking competitors, add experience signals |
| Pages indexed but receiving zero impressions | Keyword cannibalization or content quality below ranking threshold | Run cannibalization detection, consolidate or differentiate competing pages |
| Core Web Vitals failing on mobile only | Third-party scripts or unoptimized images loading on mobile viewport | Defer non-critical JS, serve responsive images, audit third-party script impact |
| Crawl budget exhausted on low-value pages | Parameter URLs, tag archives, or pagination consuming crawl resources | Noindex thin pages, consolidate parameters, block faceted navigation in robots.txt |
| Manual action in Search Console | Unnatural links, thin content, or structured data misuse detected | Follow Google's reconsideration process — fix all flagged issues, document changes, submit review |
| Rankings dropped for specific pages only | Competitor published stronger content or lost key backlinks | Check backlink profile changes, compare content depth against new page 1 results |
| INP failing despite fast server response | Long JavaScript tasks blocking main thread on user interaction | Break JS into smaller tasks, defer non-critical scripts, audit event handler performance |

---

## Success Criteria

- **Overall audit score**: Achieve grade B (80+) or higher on the severity-weighted scoring system
- **Zero critical failures**: All Critical-severity checks passing across all 8 dimensions
- **Core Web Vitals pass rate**: All three metrics (LCP < 2.5s, INP < 200ms, CLS < 0.1) passing at 75th percentile — benchmark: only 47-55% of sites pass as of 2026
- **Indexation coverage**: 95%+ of target pages indexed with zero conflicting signals (canonical vs noindex vs sitemap)
- **Crawl error rate**: Zero 5xx errors and fewer than 0.5% 4xx errors in the indexed page set
- **Organic CTR**: Position 1 pages achieving 25%+ CTR, position 2-3 achieving 10%+ (2026 benchmarks: pos 1 avg 27.6%, pos 2 avg 15.8%)
- **Remediation velocity**: All P0 emergency findings fixed within 24 hours, P1 critical within 7 days

---

## Scope & Limitations

**In scope:**
- Technical SEO across all 8 audit dimensions (crawlability, indexation, CWV, on-page, content quality, infrastructure, off-page, analytics)
- Severity-weighted scoring with prioritized remediation plans
- Traffic drop diagnosis and root cause analysis
- Competitive gap analysis across technical and content dimensions
- Pre-migration and post-migration audit checklists
- AI content quality detection signals

**Out of scope:**
- Content creation or rewriting (use Content Creator)
- Structured data implementation (use Schema Markup)
- Site architecture redesign (use Site Architecture)
- Link building execution (audit identifies gaps, not outreach)
- Paid search or advertising campaign audits
- Server infrastructure provisioning or CDN setup

**Known limitations:**
- Field CWV data requires sufficient traffic volume for CrUX reporting — low-traffic sites must rely on lab data
- Off-page signals (backlinks, brand mentions) require third-party tools (Ahrefs, SEMrush) for comprehensive data
- AI Overview impact on CTR varies by query type — no universal benchmark exists
- Google's algorithm changes 500-600 times per year; audit findings reflect a point-in-time snapshot

---

## Integration Points

- **AI SEO** -- Run after audit to optimize for AI search citation alongside traditional SEO findings.
- **Schema Markup** -- Use when audit reveals missing or broken structured data opportunities.
- **Site Architecture** -- Use when audit uncovers structural issues requiring architectural redesign.
- **Content Humanizer** -- Use when audit flags AI content detection signals on key pages.
- **Content Strategy** -- Use when audit reveals content gaps or pillar coverage weaknesses.

---

## Scripts

```bash
# Check redirect chains and status codes
python scripts/redirect_checker.py --url https://example.com/old-page --json

# Analyze XML sitemap for errors
python scripts/sitemap_analyzer.py --sitemap https://example.com/sitemap.xml

# Score content quality for SEO
python scripts/content_scorer.py article.md --json
```
