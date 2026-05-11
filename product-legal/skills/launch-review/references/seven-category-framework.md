# Eight-Category Launch Review Framework

Default framework if the team doesn't have their own. Adapted from internal
product-legal practice. Each category has a key question and an auto-skip
condition.

The categories are stable framing concepts. What counts as "Needs work" vs.
"Blocker" *within* a category depends on the applicable jurisdictions, sector
regimes, and the company's own calibration in `~/.claude/plugins/config/claude-for-legal/product-legal/CLAUDE.md`. Research the
regulatory regimes applicable to the product's sector, audience, and
jurisdictions before concluding that a specific fact pattern is or isn't a
problem.

## 1. Contractual commitments

**Key question:** Does this conflict with any customer-facing promise?

Check: Terms of Service, SLA commitments, marketing materials, customer
contracts (especially enterprise MSAs with custom terms), published
documentation.

**Auto-skip if:** No customer-facing changes — internal tool, infra, or change
invisible to users.

**Common findings:**
- New feature contradicts a ToS restriction
- SLA implications of a new dependency
- Feature marketed as "included" moving to a paid tier

## 2. Privacy

**Key question:** New data collection, new purpose, or new sharing?

Check: What data is touched, whether it's new or existing, whether the purpose
is covered by the current privacy policy, whether any new third party sees it.
Research the applicable privacy regimes for the affected users' jurisdictions
before concluding whether a new notice, consent, or assessment is required.

**Auto-skip if:** No data changes — pure UI, pure infra without new logging.

**Common findings:** See the privacy-legal plugin's PIA skill.

## 3. Security

**Key question:** New attack surface?

Check: new endpoints, new data at rest, new access paths, new auth requirements.

**Auto-skip if:** UI-only change, no backend. (But check that it really is
UI-only — "UI change" that adds a new API call is not.)

**Not legal's call alone** — loop security team. Legal's role is ensuring the
security review happened and any findings are addressed.

## 4. IP

**Key question:** Any third-party code, content, or potentially infringing output?

Check: new open-source dependencies (license compatibility — some copyleft
licenses create obligations inconsistent with a proprietary product; research
the specific license), third-party content (stock images, fonts, datasets),
features that output content that could infringe (AI generation, user
uploads displayed publicly).

**Auto-skip if:** No new dependencies, no content generation, no user uploads.

**Common findings:**
- Copyleft license in a new dependency
- Training data provenance unclear
- User-generated content without a notice-and-takedown process — research the
  applicable safe-harbor regime

## 5. Third-party interactions

**Key question:** New vendor, partner, or integration?

Check: is there a contract, is there a data processing agreement if data
flows, is the third party's failure our problem (uptime, security).

**Auto-skip if:** No new external parties.

**Common findings:**
- New vendor without a DPA
- Integration partner with different data practices
- API dependency without SLA

## 6. Regulatory / sector-specific

**Key question:** Does this touch a regulated sector, audience, or jurisdiction?

Research the regulatory regimes applicable to the product's sector (for
example, health, financial services, children and students, insurance,
telecommunications, employment, advertising), audience, and jurisdictions
(US federal, US state, EU, UK, and other regions the product reaches). Also
consider accessibility and export-control regimes where relevant. Cite the
controlling primary sources and verify currency — regulated sectors and
jurisdictions change frequently.

**Auto-skip if:** Same users, same sectors, same jurisdictions as the existing
product — nothing new in regulatory scope.

**Common findings:**
- Expansion into a regulated sector without the supporting infrastructure
  (contracts, controls, disclosures) the regime requires
- Feature that could be used by a regulated audience (e.g., children) without
  the protections the applicable regime requires
- International expansion into a jurisdiction with localization, licensing, or
  notice requirements

## 7. Marketing claims

**Key question:** Any claims that need substantiation?

See the marketing-claims-review skill.

**Auto-skip if:** No marketing component — silent launch, internal feature, flag flip.

## 8. AI governance

**Key question:** Does this use AI in any form? Is the use case in the
registry? Is an AI impact assessment done? Have vendor AI terms been reviewed?

Check: third-party models, internally built models, AI-powered vendor
features, automated scoring or classification, generative content,
recommendations, predictions. Research the applicable AI governance regimes
for the affected users' jurisdictions and the use case type — AI-specific
rules are evolving and vary substantially by region and sector.

**Auto-skip if:** No AI component detected.

**Common findings:**
- Use case not in the AI registry
- Vendor AI terms permit training on inputs
- Automated decision-making without a human-in-the-loop design where one may
  be required
