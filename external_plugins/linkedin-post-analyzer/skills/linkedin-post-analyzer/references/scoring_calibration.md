# Scoring Calibration Log

## Version History

| Version | Date | What Changed |
|---|---|---|
| 1.0.0 | 2026-03-21 | Initial build. 5 primary dimensions + AI Generation Risk penalty. Equal weights. 82% rewrite threshold. Eval-tested on 3 posts. |
| 1.1.0 | 2026-03-21 | Added Narrative & Retention as 6th primary dimension. Added Spam/Cringe Risk as 2nd penalty flag. Switched to weighted scoring (Hook/Narrative/Authenticity 20%, Viral/Expert 15%, Algorithm 10%). Added mandatory fix trigger for any dimension < 70. |
| 1.2.0 | 2026-03-21 | Voice profile system. Amit's calibration moved to voice-profiles/amit-mohod.md. Added VOICE_PROFILE_TEMPLATE.md for other users. Generic rewrite standards added as fallback. Onboarding prompt added for users without a profile. |

**How to version:** When you update scoring guidance or add edge cases, bump the version in `SKILL.md` frontmatter (`1.0.0 → 1.1.0` for calibration changes, `1.x.x → 2.0.0` for structural changes) and add a row here.

---

This file tracks scoring decisions and adjustments made over time. When a real post evaluation produces a score that feels wrong — either too harsh or too generous — log it here and update the relevant dimension guidance in SKILL.md.

---

## How to use this

When a score feels off during a real evaluation:
1. Note the post title/date and the dimension that felt miscalibrated
2. Record what the skill scored vs. what felt right
3. Explain why — what was present or absent that the score didn't account for
4. Update the scoring guidance in SKILL.md to reflect the adjustment

---

## Calibration Log

### [2026-03-21] Hook Power — Strict stance confirmed

**Post:** CHRO/dashboard post (mid-tier eval)
**Skill scored:** 76/100
**Assertion expected:** 80+
**Decision:** Keep the strict calibration.

**Reasoning:** The post had a strong opening scene but the second half broke voice ("enterprise conversations", "We're asking leaders to drive with no dashboard"). The skill correctly penalized this consistency gap. Hook Power should reflect the *whole post's pull*, not just the opening three lines — because if the second half breaks the hook's promise, the reader feels let down.

**Calibration note:** An opener that drops into a vivid scene AND maintains that energy through the second half = 85+. An opener that starts strong but shifts to polished editorial = 70–79. This is intentionally strict.

---

## Dimension Targets (Current — v1.1.0)

| Dimension | Target | Weight | Notes |
|---|---|---|---|
| Hook Power | 85+ | 20% | Strict — full-post voice consistency, not just the opening |
| Narrative & Retention | 85+ | 20% | Strict — penalizes front-loaded excitement with flat second half |
| Authenticity | 85+ | 20% | Strict — penalizes any LinkedIn clichés, even single phrases |
| Viral Potential | 80+ | 15% | Moderate — ending question is the main lever |
| Expert Status | 80+ | 15% | Moderate — one scale signal or "I was wrong" moment is enough |
| Algorithm Compatibility | 85+ | 10% | Lenient — Amit's natural style already scores 90+ here |
| AI Generation Risk | <30% | Penalty flag | Strict — any perfect parallel structure pushes this up |
| Spam / Cringe Risk | <20% | Penalty flag | Low risk for this author, but catches broetry and forced vulnerability |

---

## Known Edge Cases

**Openers with dialogue:** A post that opens with a quote ("We tried this two years ago. Fell apart.") should score 85+ on Hook Power even if the setup is 2-3 lines — the dialogue does the work of the scene.

**Second-half metaphors:** Metaphors that summarize the story ("driving with no dashboard") tend to push AI Generation Risk up and Authenticity down. They feel constructed rather than observed. Flag them in fixes but don't over-penalize — if the rest is strong, -3 to -5 points is appropriate.

**iMocha/enterprise product references:** The post should not name iMocha products. Generic references to "the platform", "the tool", "our solution" are fine. Flag only if a product name appears.
