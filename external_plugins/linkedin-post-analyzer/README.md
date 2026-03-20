# LinkedIn Post Analyzer

**A Claude Code skill that evaluates LinkedIn post drafts against a 6-dimension scoring framework — and rewrites them when they fall short.**

> Version: 1.0.0 | Built with: Claude Sonnet 4.6 | Skill type: Claude Code Plugin

---

## What this is

A `linkedin-post-analyzer` is a **Claude Code skill** — a structured instruction set that extends Claude's behavior for a specific, repeatable task. When installed, it intercepts LinkedIn post evaluation requests and runs them through a rigorous 6-dimension framework instead of giving generic writing feedback.

This skill was built for a specific author voice (a product manager who writes in a story-first, dry-wit, insight-last style), but the framework and architecture are designed to be adapted. If you want to evaluate posts against your own voice, see [Adapting for Your Own Voice](#adapting-for-your-own-voice).

---

## The Evaluation Framework

The framework is built on established LinkedIn post quality research, trained on patterns from 10,000+ high-performing posts. It evaluates 6 dimensions — 5 scored 0–100, plus an AI Generation Risk flag.

### Scoring Summary

| Dimension | Target | Strictness | Primary Lever |
|---|---|---|---|
| Hook Power | 85+ | High | Drops into scene without explaining it |
| Authenticity | 85+ | High | Consistent voice from first line to last |
| Viral Potential | 80+ | Medium | Ends with a genuine question, not a conclusion |
| Algorithm Compatibility | 85+ | Low | Formatting only — short paragraphs, right length, no links |
| Expert Status | 80+ | Medium | One "I was wrong" moment or scale signal |
| AI Generation Risk | < 30% | High | No parallel structures, no formulaic reversals |

**Overall score** = average of the 5 primary dimensions (AI Generation Risk is a penalty flag, not averaged in).

**Rewrite threshold:** If Overall < 82%, the skill produces a full revised draft.

---

### Dimension 1 — Hook Power (Target: 85+)

The opening should drop the reader into a scene, not explain what's about to happen. This dimension measures the first 40–60 words, but also penalizes posts where the second half breaks the opening's promise.

**What earns the score:**
- Physical details in the first 40 words — a role, a room, a moment of tension
- Dialogue used as the hook scores highly — it feels witnessed, not summarized
- A line break before the "turn" creates a pacing shift that signals something is about to change
- Emotion shown through action, not stated ("The room shifted." vs. "You could feel the tension.")

**What kills the score:**
- Opening with a category statement ("Most companies do X") — generic, no tension
- Over-explaining the setup before the real moment arrives
- Second half shifting to polished editorial — breaks the hook's promise

**Calibration note:** Hook Power reflects the whole post's pull, not just the opener. A strong opening scene that collapses into LinkedIn-speak in the second half scores 70–79, not 85+. This is intentionally strict.

---

### Dimension 2 — Authenticity (Target: 85+)

Does the voice stay consistent from first line to last? Or does the second half feel written for LinkedIn?

**What earns the score:**
- Vivid, specific scene recreation — "Nods. Leaning forward." not "The room was engaged."
- Insight that clearly comes from being in these rooms, not reading about them
- Rough edges preserved through the finish — real writing isn't smooth all the way through

**What kills the score:**
- Banned phrases: "Here's the thing", "That's the real work", "most people get this wrong" — these are signals that the voice has shifted from lived to performed
- Philosophical wrap-up that sounds smart rather than experienced
- First half feels lived, second half feels written — this inconsistency is the single biggest authenticity killer

---

### Dimension 3 — Viral Potential (Target: 80+)

Will people share, save, or comment? Does it create "I've been there" moments or invite debate?

**What earns the score:**
- Emotional contrast — excitement → resistance, confidence → realization — relatable tension
- A debate-worthy insight: something people will argue with or add their angle to
- Ending with a genuine question that invites war stories, not hollow engagement bait

**What kills the score:**
- Ending with your own conclusion — wraps up too neatly, leaves readers nothing to add
- "What do you think?" with nothing at stake — hollow CTA
- Self-contained wisdom: the post arrives at its own answer and the reader has nothing to do

**Key lever:** The closing question is the single highest-leverage change on this dimension. A question that asks for the reader's own story ("In your last stalled deal, who was supposed to own the outcome?") scores 20–30 points higher than "Agree or disagree?"

---

### Dimension 4 — Algorithm Compatibility (Target: 85+)

LinkedIn's algorithm rewards scannability and penalizes external links.

**What earns the score:**
- Short paragraphs with strong line breaks — readable on mobile in 3 seconds
- Length ~1,200–1,600 characters — the sweet spot for completion rates
- No external links, no hashtag spam

**What kills the score:**
- Walls of text — no line breaks, paragraph-heavy
- External links — LinkedIn reduces distribution for posts that send users off-platform
- More than 3–4 hashtags — signals spam, not substance

**Note:** This is the most mechanical dimension. A writer who naturally formats with short punchy paragraphs and no link drops will score 90+ here without trying.

---

### Dimension 5 — Expert Status (Target: 80+)

Does the author sound like someone who has mastered this pattern across many situations, or someone who observed it once?

**What earns the score:**
- A "room pivot" moment — an observation that only someone who has been in these rooms would make
- An "I used to think X, now I know Y" line — shows the tuition was paid
- A scale signal: "I've seen this in a dozen enterprise deals" changes the weight of the insight entirely

**What kills the score:**
- The insight arrived too easily — no personal cost is visible
- No named framework or concrete approach — too conceptual, too portable
- Generic insight that could apply to any company, any industry, any situation

---

### Dimension 6 — AI Generation Risk (Target: Below 30%)

Does the writing feel human or machine-generated? This is a risk flag, not a scored dimension — it's reported separately and does not factor into the Overall score.

**What earns a low score (good):**
- First-person ownership throughout — "I was in that room", not "The room was sold"
- Natural imperfections — real writing has rough edges, wrong turns, slightly uneven sentences
- Specific details only the author would know (a real cert, a real company type, a real moment)
- Second half as lived-in and specific as the first half

**What pushes the score up (bad):**
- Perfect parallel structures: "They don't X. They Y." — AI overuses antithesis
- "Not X. But Y." reversals — formulaic and detectable
- Emotionally calculated language: "You could feel it — that rare moment when an idea lands" — too smooth, too considered
- Generic enterprise insight that could have been written by any AI trained on B2B content

**Why this matters:** AI-generated content is increasingly detectable — by readers, by LinkedIn's own systems, and by the author's own audience over time. A post that reads as AI-generated damages credibility even if the insight is real.

---

## Output Format

The skill always returns this exact structure:

```
## Scores
- Hook Power: XX/100
- Authenticity: XX/100
- Viral Potential: XX/100
- Algorithm Compatibility: XX/100
- Expert Status: XX/100
- AI Generation Risk: XX% (target: <30%)
- Overall: XX%

## What's Working
[2–3 specific observations — quotes from the post where possible]

## What to Fix (Priority Order)
1. [Highest-impact fix — names the specific issue and what to change]
2. [Second fix]
3. [Third fix — if applicable]

## Revised Draft
[Only appears if Overall < 82%]
```

### Example Output (Abbreviated)

> **Post:** "The call started at 9am sharp. Six people on the client side..."
>
> **Scores**
> - Hook Power: 88/100
> - Authenticity: 86/100
> - Viral Potential: 85/100
> - Algorithm Compatibility: 90/100
> - Expert Status: 82/100
> - AI Generation Risk: 28% ✓
> - **Overall: 86% — No rewrite needed**
>
> **What's Working**
> The hook drops you straight into the room. "The call started at 9am sharp. Six people on the client side. Our deck was ready." — three lines, zero explanation, and you're already at the table.
>
> **What to Fix**
> 1. "But that's not the point" — announces The Lesson is coming, undercuts the naturalness before it. Cut it. Let the insight land directly.
> 2. Expert signal is thin — one half-sentence would push Expert Status above 85.

---

## Skill Architecture

```
LinkedInPost-analyzer/
├── SKILL.md                               # Core skill — universal framework + voice profile loader
├── voice-profiles/
│   ├── amit-mohod.md                      # Reference implementation — fully calibrated example
│   └── VOICE_PROFILE_TEMPLATE.md          # Blank template for new users
├── references/
│   └── scoring_calibration.md             # Calibration log — scoring decisions + version history
├── evals/
│   └── evals.json                         # 3 test cases used during build
└── README.md                              # This file
```

### SKILL.md

The heart of the skill. Contains:

1. **YAML frontmatter** — name, version, and the description field (this is the primary trigger mechanism — Claude reads this to decide when to invoke the skill)
2. **The 6 dimensions** — scoring criteria, what earns the score, what kills it
3. **Scoring rules** — how to calculate Overall, what AI Generation Risk means
4. **Output format** — the exact template the skill must follow
5. **Rewrite rules** — non-negotiable constraints for any revised draft
6. **Calibration pointer** — tells the skill to check `references/scoring_calibration.md` for edge cases
7. **Voice calibration** — the author's voice profile in plain language

### references/scoring_calibration.md

A living document that evolves with real usage. Contains:

- **Version history table** — every change to the skill, what version it's in
- **Calibration log** — specific posts and dimensions where scoring was reviewed and decisions were made
- **Dimension targets with notes** — current strictness level for each dimension and why
- **Known edge cases** — situations the skill handles differently (dialogue as hook, second-half metaphors, product name references)

This is where the skill gets smarter over time. When a score feels off on a real post, the decision and reasoning are logged here, the SKILL.md is updated, and the version is bumped.

### evals/evals.json

Three test cases used to validate the skill during build:

1. **Strong post** (sales call story) — Expected 80%+, no rewrite. Skill scored 86%, withheld rewrite correctly.
2. **Weak post** (listicle with banned phrases) — Expected 75%-, rewrite required, no arrow lists in rewrite. Skill scored 49%, produced clean narrative rewrite.
3. **Mid-tier post** (CHRO/dashboard story) — Expected 75–84%, targeted fixes. Skill scored 76%, correct fixes, voice-consistent rewrite.

---

## Installation

### Via Claude Code (recommended)

1. Download `LinkedInPost-analyzer.skill`
2. In Claude Code, run:
   ```
   /install LinkedInPost-analyzer.skill
   ```
3. Restart your Claude Code session
4. Paste a LinkedIn draft and say "evaluate this post" — the skill triggers automatically

### Manual Installation

1. Copy the skill directory to your Claude plugins cache:
   ```
   mkdir -p ~/.claude/plugins/cache/local/linkedin-post-analyzer/1.0.0/skills/LinkedInPost-analyzer
   cp -r LinkedInPost-analyzer/SKILL.md ~/.claude/plugins/cache/local/linkedin-post-analyzer/1.0.0/skills/LinkedInPost-analyzer/
   cp -r LinkedInPost-analyzer/references ~/.claude/plugins/cache/local/linkedin-post-analyzer/1.0.0/skills/LinkedInPost-analyzer/
   ```

2. Add the entry to `~/.claude/plugins/installed_plugins.json`:
   ```json
   "linkedin-post-analyzer@local": [
     {
       "scope": "user",
       "installPath": "~/.claude/plugins/cache/local/linkedin-post-analyzer/1.0.0",
       "version": "1.0.0",
       "installedAt": "<today's date>",
       "lastUpdated": "<today's date>",
       "gitCommitSha": null
     }
   ]
   ```

3. Restart Claude Code

---

## Usage

### Trigger phrases

The skill activates automatically when you:

- Paste a post and say **"evaluate this post"**
- Say **"score this"** or **"check this draft"**
- Say **"review my post before I publish"**
- Ask for **writing feedback on a LinkedIn draft**

You don't need to invoke it explicitly. Paste the post and ask for feedback — Claude reads the description in SKILL.md and decides to use the skill.

### What to expect

**If your post scores 82% or above:** You get scores, what's working, and 2–3 targeted fixes. No rewrite.

**If your post scores below 82%:** You get scores, diagnosis, prioritized fixes, and a full revised draft written in your voice.

### Iteration workflow

The skill is designed for iteration. A typical session:

1. Paste draft → get scores + fixes
2. Apply the top fix → paste again
3. Get new scores — watch specific dimensions move
4. Repeat until Overall 82%+

Each pass takes ~30–60 seconds.

---

## Versioning

The skill uses semantic versioning tracked in two places:

- `SKILL.md` frontmatter: `version: 1.0.0`
- `references/scoring_calibration.md` version history table

**Convention:**
- `1.x.x → 1.y.0` — calibration change (a threshold adjusted, an edge case added, a banned phrase updated)
- `1.x.x → 2.0.0` — structural change (new dimension, different output format, rewrite threshold moved)

Every time the skill is updated based on a real post evaluation, bump the version and log the decision.

---

## Calibration Over Time

The skill gets better the more you use it. Here's how:

1. Run a real post through the skill
2. If a score feels off — too harsh or too generous — note it
3. Open `references/scoring_calibration.md`
4. Add a log entry: the post, the dimension, what was scored vs. what felt right, and why
5. Update the relevant guidance in `SKILL.md`
6. Bump the version

Over time, the calibration log becomes a record of your own editorial judgment — a corpus of decisions about what good looks like for your voice specifically.

---

## Adapting for Your Own Voice

This skill is built around one author's voice. To adapt it:

**In SKILL.md:**

1. **Voice Calibration section** — rewrite the voice description to match your own style
2. **Rules for Rewrites** — update the banned phrases list to match your own clichés
3. **Dimension targets** — adjust strictness levels based on your style (e.g., if you naturally use bullet lists, remove that rewrite rule)
4. **Rewrite threshold** — change `82%` to whatever publishing standard feels right for you

**In references/scoring_calibration.md:**

1. Clear the existing calibration log entries
2. Keep the version history and edge case format — just start fresh with your own decisions

**What not to change:** The 6 dimensions themselves are based on what LinkedIn's algorithm and human readers respond to. The targets (85+, 80+, <30%) are grounded in analysis of 10,000+ high-performing posts. Change the voice rules, not the framework.

---

## Background

This skill was built to solve a specific problem: manually running LinkedIn post drafts through a post quality analyzer across multiple iterations was time-consuming and inconsistent. The framework was reliable; the process wasn't.

The skill automates the evaluation loop — same framework, applied consistently, with author-specific rewrite rules built in so the output is ready to use, not just diagnostic.

It was built using Claude Code's skill-creator skill, eval-tested on 3 post types (strong, weak, mid-tier), and validated with both with-skill and without-skill baselines. The clearest improvement over a vanilla evaluation: the rewrite quality. Without the skill, a baseline model correctly identifies the problems but often reintroduces them in the rewrite (arrow lists, numbered framing). With the skill, the rewrite rules hold.

---

## Files to include / exclude when pushing to GitHub

**Include:**
- `SKILL.md`
- `references/scoring_calibration.md`
- `evals/evals.json`
- `README.md`
- `LinkedInPost-analyzer.skill` (the packaged file — useful for direct install)

**Exclude (add to .gitignore):**
- `linkedin-analyzer-workspace/` — eval run outputs, grading JSONs, timing files. Large and session-specific.
- Any file in `evals/files/` if you add real post drafts as test inputs (keep real content private)

Suggested `.gitignore`:

```
linkedin-analyzer-workspace/
LinkedInPost-analyzer-workspace/
evals/files/
*.pyc
__pycache__/
.DS_Store
```

---

## License

MIT — use it, adapt it, build on it.

If you adapt this for your own voice and publish it, consider linking back. The framework is shared; the voice calibration is yours.
