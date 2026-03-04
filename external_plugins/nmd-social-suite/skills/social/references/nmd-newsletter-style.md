# NMD Newsletter Style Guide
# "NMD — No Money Down | Credit Intelligence"

Pulled directly from nmdzaza.github.io/nmd-newsletters — 15 live editions analyzed.

---

## Newsletter Identity
- **Brand name in newsletter:** NMD — No Money Down
- **Subtitle/tagline:** Credit Intelligence
- **Tone:** Insider confidence. Direct. Data-backed. Street-smart meets finance professional.
- **Theme:** Dark, premium, high-authority — not corporate, not flashy

---

## Writing Style — Exact Rules

### Headlines (always punchy declarations)
- Use action verbs: "Chase just took...", "Capital One just dropped..."
- Make it feel like breaking news even when it's education
- Treat credit moves as major events — because they ARE
- Use numbers when possible: "$20 billion in card balances"
- Examples from live newsletters:
  - "Chase just took Apple Card"
  - "Capital One just dropped Discover"
  - "They said bankruptcy would close every door"
  - "The score you're watching isn't the one they're using"
  - "$1,000,000 in total credit lines"
  - "VS4 apparently likes me. Does it like you?"

### Section Labels (used as category tags)
Use these labels above the headline:
- Breaking News
- Breaking
- Credit Guide
- Client Story
- Real Talk
- Elite Strategy
- BNPL Intelligence
- Business Credit
- Auto Strategy
- Debt Strategy
- Consumer Protection
- Credit Builders

### Opening Sentences
Short. Punchy. Immediate. No warm-up.
- "Goldman Sachs is out. JPMorgan Chase is in."
- "FICO vs VantageScore is not just academic."
- "A $1M total credit limit isn't luck."

### Body Writing
- Translate complex financial concepts into personal relevance
- Always answer "what does this mean for YOU"
- Use specific numbers and institutional names — credibility through specificity
- Short paragraphs — 2-3 sentences max
- Never use jargon without immediately explaining it
- Position the reader as someone who deserves to know this inside info

### Closing / CTA
- End with what action to take or what to watch for
- Connect to NMD services naturally, never forcefully
- "Stay locked in" or similar closing

---

## Newsletter Structure (HTML Template)
Each newsletter is a self-contained HTML file with:
1. NMD header/logo
2. Section label (Breaking / Real Talk / Elite Strategy / etc.)
3. Bold headline
4. Subheadline or lede (1-2 lines)
5. Full article body
6. CTA section
7. Footer with unsubscribe / social links

---

## Topic Categories (from live newsletters)
1. **Breaking industry news** — major credit card mergers, bank moves, regulatory changes
2. **Score intelligence** — FICO vs VantageScore, model differences, what lenders actually pull
3. **Credit building strategy** — secured loans, pledge loans, Navy Federal, tier-building
4. **Business credit** — business cards, credit lines, EIN building, net-30
5. **Elite strategy** — $1M credit files, strategic sequencing, advanced tactics
6. **Consumer protection** — CFPB, credit unions, rights under FCRA/FDCPA
7. **Client stories** — real post-bankruptcy approvals, comeback narratives
8. **BNPL intelligence** — Affirm, Apple Pay Later, how they affect FICO
9. **Auto strategy** — car loans, dealer financing, leveraging auto tradelines
10. **Debt strategy** — consolidation, pay-for-delete, goodwill letters

---

## Publishing Workflow (GitHub Pages)
Newsletters are HTML files pushed to: github.com/nmdzaza/nmd-newsletters

**To publish a new newsletter:**
1. Create new HTML file (naming: `topic-keyword.html` e.g., `capital-one-discover.html`)
2. Update `index.html` to add the new newsletter card
3. Commit both files: `git add . && git commit -m "New newsletter: [title]"`
4. Push to main: `git push origin main`
5. GitHub Pages auto-deploys — live at nmdzaza.github.io/nmd-newsletters within 2-3 minutes

**When /social creates a newsletter:**
- Generate full HTML file ready to push
- Generate the index card snippet to add to index.html
- Provide the git commands to deploy

---

## Live Newsletter URL
https://nmdzaza.github.io/nmd-newsletters/

## GitHub Repo
https://github.com/nmdzaza/nmd-newsletters
