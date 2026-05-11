# Regulatory Source Catalog

A starting catalog for the reg-feed-watcher. The cold-start interview configures
which sources to watch; this catalog provides the options. URLs verified as of
**May 2026** — feed URLs change; verify if a source stops returning results.

**How to read this catalog:**
- **Format** — what the feed returns: JSON API (structured, best), RSS/Atom (semi-structured, good), HTML page (needs scraping or change detection), Email only (requires Gmail/Outlook MCP).
- **Tier** — *Primary* means the regulator itself; *Secondary* means a commentator, aggregator, or law firm summarizing primary sources. Always trace a secondary source back to the primary before treating it as authoritative.
- **Auth** — None means open; Key means a free-but-registered API key; Paid means a subscription.
- **Notes** — any gotchas (rate limits, feed retirement, discovery steps).

Sources flagged ⚠️ have been reported by users or regulators as unreliable or
discontinued — verify before configuring.

---

## US Federal — Primary

| Source | Feed URL | Format | Covers | Auth | Notes |
|---|---|---|---|---|---|
| Federal Register | `https://www.federalregister.gov/api/v1/documents.json` | JSON API | All federal rules, proposed rules, notices, presidential documents | None | Filter by `conditions[agencies][]=<slug>`, `conditions[publication_date][gte]=<YYYY-MM-DD>`, `conditions[type][]=RULE\|PRORULE\|NOTICE\|PRESDOCU`. Well-documented: federalregister.gov/developers/documentation/api/v1. Returns abstract, effective date, comment deadline, citation. **Use this first** — most federal agency documents flow through here. |
| Regulations.gov | `https://api.regulations.gov/v4/documents` | JSON API | Rulemaking dockets, public comments, supporting documents | Key (free) | Key at open.gsa.gov/api/regulationsgov/. Use for docket-level tracking and pulling comments. |
| Congress.gov | `https://api.congress.gov/v3/bill` | JSON API | Federal bills, laws, committee reports | Key (free) | Key at api.congress.gov/sign-up. Pre-built RSS also at congress.gov/rss (narrower: bills presented to President, most-viewed, floor). |
| SEC Press Releases | `https://www.sec.gov/news/pressreleases.rss` | RSS | Rules, enforcement, speeches (press release only) | None | SEC RSS hub: sec.gov/about/rss-feeds. Also has EDGAR structured-filing feeds at sec.gov/structureddata/rss-feeds (updated every 10 min, business hours). Rules-adopted news typically also posts to Federal Register — deduplicate. |
| FTC Press Releases | `https://www.ftc.gov/feeds/press-release.xml` | RSS | Enforcement, rules, blog posts, settlements | None | Sub-feeds by topic: `ftc.gov/feeds/press-release-consumer-protection.xml`, `press-release-competition.xml`, blog feed `ftc.gov/feeds/business-blog.xml`. Feed hub: ftc.gov/news-events/stay-connected/ftc-rss-feeds. |
| CFPB Newsroom | `https://www.consumerfinance.gov/about-us/newsroom/` | HTML + RSS option on page | Rules, enforcement, circulars, blog | None | Page offers RSS subscription; the activity log at `consumerfinance.gov/activity-log/` is the broadest single URL. Major rules also in Federal Register. |
| DOJ Antitrust Division | `https://www.justice.gov/atr/news-feeds` | RSS (multiple feeds) | Press releases, speeches, statements of interest | None | Page lists several Atom/RSS URLs by content type. DOJ main press-release feed is a sibling at justice.gov (navigate from `justice.gov/news`). |
| DOJ Main | `https://www.justice.gov/news/rss` | RSS | All DOJ press releases across divisions | None | Filter client-side by topic. Civil Division, ATR, Civil Rights Division all feed in. |
| FCC Daily Digest | Subscribe via `fcc.gov/news-events/rss-feeds-and-email-updates-fcc` | RSS + email | Orders, notices, public notices | None | Also has ECFS docket-specific feeds — pick docket from "Hot Dockets," right-click RSS icon. |
| HHS OCR | `https://www.hhs.gov/ocr/newsroom/index.html` | HTML | HIPAA enforcement, settlements, guidance | None | No direct RSS located; HHS-wide press-release feed at `hhs.gov/rss` covers OCR. Follow `@HHSOCR` on X for push alerts. |
| OFAC Recent Actions | `https://ofac.treasury.gov/recent-actions` | HTML + email | Sanctions designations, general licenses, FAQs | None | ⚠️ RSS retired January 31, 2025. Email is the supported push channel — subscribe at service.govdelivery.com/service/multi_subscribe.html?code=USTREAS. Page has a browsable list. |
| BIS (Commerce) | `https://www.bis.gov/news-updates` | HTML | Export control updates, Entity List, final rules | None | Federal Register notices index at `bis.gov/regulations/federal-register-notices` is the cleanest list. No public RSS located. |
| DOL News Releases | `https://www.dol.gov/rss/releases.xml` | RSS | Wage/hour, OSHA, OFCCP, EBSA press releases | None | Other feeds indexed at `dol.gov/rss`. |
| NIST Cybersecurity | `https://www.nist.gov/news-events/cybersecurity/rss.xml` | RSS | Cybersecurity news by topic | None | AI/blog feed: `nist.gov/blogs/cybersecurity-insights/rss.xml`. |
| CISA Alerts/Advisories | `https://www.cisa.gov/news-events/cybersecurity-advisories` | HTML + RSS option | ICS advisories, alerts | None | Verify feed URL on page; multiple sub-feeds by content type. |

---

## US State — Primary

Coverage is uneven. States with active privacy/consumer protection enforcement
prioritized here. Many state regulators publish HTML-only pages — if no RSS,
configure as "manual" or set up web-page change detection.

| Source | Feed URL | Format | Covers | Auth | Notes |
|---|---|---|---|---|---|
| California AG | `https://oag.ca.gov/news/feed/729/oag.ca.gov` | RSS | Press releases, CCPA enforcement, multistate actions | None | Main press page: `oag.ca.gov/media/news`. |
| California Privacy Protection Agency (CPPA) | `https://cppa.ca.gov/announcements/` | HTML | CCPA regulations, enforcement, advisories | None | ⚠️ No direct RSS URL located — primary channel is email list (sign-up on page). Monitor page for changes or use manual entry. |
| New York AG | `https://ag.ny.gov/press-releases` | HTML | Press releases, multistate AG actions | None | ⚠️ No public RSS located. Monthly archive at `ag.ny.gov/press-releases-for-month` is structured enough to scrape. |
| Texas AG — News Releases | `https://www2.texasattorneygeneral.gov/feeds/feeds.php?feed=pr` | RSS | Press releases | None | Additional feeds on `www2.texasattorneygeneral.gov/agency/feeds`. |
| Illinois AG | `https://illinoisattorneygeneral.gov/news-room/` | HTML | Press releases | None | ⚠️ No public RSS located. |
| Washington AG | `https://www.atg.wa.gov/news` | RSS option on page | Latest news, AGO opinions, consumer alerts | None | Separate feeds for news, opinions, consumer alerts — subscribe from the page. |
| Colorado AG | `https://coag.gov/press-releases/` | HTML | Press releases, CPA rulemaking | None | ⚠️ No public RSS located. Colorado Privacy Act rulemaking also published via SOS. |
| Connecticut AG | `https://portal.ct.gov/ag/press-releases/press-releases` | HTML | Press releases | None | ⚠️ No public RSS located. |
| Virginia AG | `https://www.oag.state.va.us/media-center/news-releases` | HTML | Press releases, VCDPA oversight | None | ⚠️ No public RSS located. |
| Massachusetts AG | `https://www.mass.gov/orgs/office-of-attorney-general-maura-healey/news` | HTML | Press releases | None | ⚠️ No public RSS located. Mass.gov has per-org newsroom pages. |
| NYDFS | `https://www.dfs.ny.gov/reports_and_publications/press_releases` | HTML | Enforcement, regulations, cybersecurity (Part 500) | None | ⚠️ No public RSS located. |

---

## EU / UK — Primary

| Source | Feed URL | Format | Covers | Auth | Notes |
|---|---|---|---|---|---|
| EDPB News | `https://www.edpb.europa.eu/news/news_en` | RSS (2 feeds offered) | Guidelines, opinions, enforcement summaries, binding decisions | None | Feeds advertised at `edpb.europa.eu/sme-data-protection-guide/faq-frequently-asked-questions/answer/how-can-i-keep-edpbs-work_en`. |
| European Commission Press Corner | `https://ec.europa.eu/commission/presscorner/` | RSS + email | Press releases, speeches, Q&As — DSA, DMA, AI Act implementing acts | None | Subscribe at `ec.europa.eu/commission/presscorner/login/en`. Narrower sub-feeds by topic. |
| EUR-Lex (OJ) | `https://eur-lex.europa.eu/` | Webservice + RSS by search | Official Journal publications | Key (free, webservice) | Use for tracking final-form regulations and directives. |
| ICO (UK) | `https://ico.org.uk/global/rss-feeds/` | RSS (multiple feeds) | Enforcement, guidance, news, consultations | None | Separate feeds for news, enforcement actions, and blog. Enforcement list also at `ico.org.uk/action-weve-taken/enforcement/`. |
| CNIL (France) | `https://www.cnil.fr/en/rss.xml` (verify — feeder.co indexes this) | RSS | French DPA decisions, guidance, sanctions | None | English-language news at `cnil.fr/en/news`. Third-party indexes suggest feed exists; verify before relying. |
| DPC (Ireland) | `https://www.dataprotection.ie/en/news-media/latest-news` | HTML | Inquiries, decisions, guidance — lead DPA for most US tech firms | None | ⚠️ No public RSS located. Critical source for GDPR enforcement against US companies; worth a change-detection or email subscription. |
| BfDI (Germany) | `https://www.bfdi.bund.de/EN/Home/home_node.html` | HTML | Federal German DPA | None | ⚠️ No public RSS located. |
| ENISA | — | Email | Cybersecurity, NIS2 guidance | None | ⚠️ **RSS feeds discontinued** with new website. Email alerts only until new subscription mechanism launches (`enisa.europa.eu/rss-feeds-discontinued-new-subscription-mechanism-coming-soon`). |
| FCA (UK) | `https://www.fca.org.uk/news/rss.xml` (verify) | RSS + email | UK financial services rules, enforcement, warnings | None | Email alerts at `fca.org.uk/newsletters-emails-sign-up` are the supported channel; RSS historically offered. |
| EDPS | `https://www.edps.europa.eu/press-publications/press-news_en` | HTML + RSS option | EU-institutional DPA | None | |

---

## International

| Source | Feed URL | Format | Covers | Auth | Notes |
|---|---|---|---|---|---|
| OECD AI Policy Observatory | `https://oecd.ai/en/` | HTML + newsletter | National AI policies, OECD guidance | None | Best for tracking non-EU, non-US AI rulemaking. |
| Council of Europe | `https://www.coe.int/en/web/portal/news` | RSS + HTML | CoE treaties including AI Framework Convention | None | |
| UK Parliament Bills | `https://bills.parliament.uk/rss/publicbills.rss` (verify) | RSS | UK bills | None | |

---

## Secondary / Aggregators

**Treat content from these sources as leads, not authority.** A secondary
source saying "the FTC issued X" means: find X on ftc.gov, then rely on it.
Tag items pulled from these feeds as `[secondary source]` in the digest.

| Source | Feed URL | Format | Covers | Auth | Notes |
|---|---|---|---|---|---|
| IAPP Daily Dashboard | `https://iapp.org/rss/daily-dashboard/` | RSS | Global privacy + AI governance news, curated | None (some items paywalled) | Highest signal-to-noise for privacy teams. |
| Future of Privacy Forum | `https://fpf.org/feed/` | RSS (WordPress) | Privacy commentary, state law trackers, reports | None | |
| Hogan Lovells | `https://www.hoganlovells.com/en/rss` | RSS (multiple by practice) | Client alerts, engagements | None | Offers per-practice sub-feeds. |
| Covington & Burling | `https://www.cov.com/` (verify per blog) | RSS by blog | InsidePrivacy, Global Policy Watch, Inside Global Tech, Inside Tech Media | None | Each topic blog is a WordPress-style site with a standard `/feed` endpoint. |
| WilmerHale | `https://www.wilmerhale.com/` | Email / HTML | Client alerts | None | ⚠️ No consolidated public RSS located; email subscription is primary. |
| Wilson Sonsini | `https://www.wsgr.com/` | Email / HTML | Client alerts | None | ⚠️ No consolidated public RSS located. |
| Lexology | `https://www.lexology.com/account/rss` | RSS (customizable by topic/jurisdiction) | Aggregated firm alerts | Account (free) | Powerful: build topic+jurisdiction feeds. Owned by LBR. |
| JD Supra | `https://www.jdsupra.com/legal-news/rss-law-feeds.aspx` | RSS (multiple by topic) | Aggregated firm alerts | None | Broader and noisier than Lexology. |
| Artificial Lawyer | `https://www.artificiallawyer.com/feed/` | RSS | Legal tech / AI regulation news | None | |
| LawSites (Bob Ambrogi) | `https://www.lawsitesblog.com/feed` | RSS | Legal tech, also covers regulation of legal AI | None | |

---

## Sources without feeds (need web monitoring or email)

Some important sources don't publish feeds, or their RSS has been retired.
Monitoring them requires either:
- Web-page change detection (not currently built in)
- Email newsletter forwarding (requires Gmail/Outlook MCP integration)
- Manual checking via the reg-feed-watcher "manual entry" path

| Source | URL | Notes |
|---|---|---|
| OFAC Recent Actions | `https://ofac.treasury.gov/recent-actions` | RSS retired Jan 2025; email is supported channel |
| ENISA | `https://www.enisa.europa.eu/news` | RSS discontinued; new subscription mechanism pending |
| DPC Ireland | `https://www.dataprotection.ie/en/news-media/latest-news` | No RSS; critical for GDPR enforcement |
| CPPA | `https://cppa.ca.gov/announcements/` | Email list only; no RSS located |
| Most state AGs (NY, IL, CO, CT, VA, MA) | See state table above | Press-release HTML pages; no RSS |
| NYDFS | `https://www.dfs.ny.gov/reports_and_publications/press_releases` | HTML only |
| BIS (Commerce) | `https://www.bis.gov/news-updates` | HTML only; use Federal Register API for rule-level events |
| HHS OCR standalone | `https://www.hhs.gov/ocr/newsroom/` | Included in HHS-wide RSS but no OCR-specific feed |
| BfDI (Germany) | `https://www.bfdi.bund.de/EN/` | HTML only |
| WilmerHale, Wilson Sonsini | Firm sites | Email subscription is the primary channel |

---

## Suggested starter packs

**Privacy-focused in-house team (US + EU):**
Federal Register (FTC, HHS/OCR agency filters), FTC RSS, CFPB, CA AG, CPPA (email),
NY AG (page watch), EDPB, ICO, CNIL, DPC Ireland (page watch), IAPP, FPF.

**Commercial / regulatory in-house team (broad):**
Federal Register (all agencies of interest), SEC RSS, CFPB, DOJ Antitrust, DOJ
Main, FCC, DOL, BIS page watch, OFAC email, European Commission Press Corner,
FCA. Add IAPP + Lexology for aggregator coverage.

**AI governance team:**
Federal Register (filter: FTC, HHS, NIST, Commerce), NIST Cybersecurity RSS, EU
Commission Press Corner, EDPB, OECD AI Observatory, Council of Europe, IAPP, FPF,
Artificial Lawyer, CA AG (ADMT), CPPA.

---

## Adding a source

To add a source that isn't in this catalog:
1. Find a feed URL (try `/rss`, `/feed`, `/news.rss`, or view page source for `<link rel="alternate" type="application/rss+xml">`).
2. Validate it returns XML/JSON in a browser or with `curl`.
3. Add to the user's regulatory-legal CLAUDE.md under **Feed configuration → Direct regulator feeds**, with: source name, URL, format, what it covers.
4. If no feed exists, add it under **Sources without feeds** and decide: manual, email, or change detection.
