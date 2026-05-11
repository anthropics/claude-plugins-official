# Contributing to Claude for Legal

Notes for anyone writing or editing a plugin in this repo. Keep this short — the
design principles that matter most for the quality of the output, not a style
guide.

## Before your first PR

Sign the CLA. The first time you open a pull request, the CLA Assistant bot will
comment with a link to the [CLA](CLA.md) and ask you to confirm. Reply with
`I have read the CLA Document and I hereby sign the CLA` and the check will pass.
You only need to do this once.

## Design principle: SKILL.md encodes the right behavior; CLAUDE.md guardrails
are the net

Every plugin in this repo ships with two layers of instruction:

1. **`<plugin>/skills/<skill>/SKILL.md`** — what this specific skill does, step by
   step. The narrow, task-specific scaffold.
2. **`<plugin>/CLAUDE.md`** — the shared guardrails and the practice profile.
   "Scaffolding, not blinders," source-tag discipline, "verify user-stated legal
   facts," premise verification, destination check, cross-skill severity floor,
   pre-flight citation banner. The wide, plugin-level safety net.

**If a skill's correct output depends on a CLAUDE.md guardrail catching a
mistake the SKILL.md would have made, that's a design smell.** The SKILL.md
should tell the model what to do directly; the guardrails should catch what the
SKILL.md missed. Every time a guardrail has to rescue a skill, we're relying on
the guardrail firing consistently — and on a bad run, a weaker model, a terser
prompt, or a future editor who reads only the skill text, the rescue doesn't
happen.

**Rule of thumb: if a QA test passes only because a guardrail fired, add the
behavior to the SKILL.md directly.** The guardrail stays (belt and suspenders),
but the skill now carries the knowledge it needs on its own.

Examples of this rule in practice:

- A design patent question should not pass an infringement triage only because
  "Scaffolding, not blinders" lets the model override the utility-patent
  workflow. The skill should branch on the D-prefix itself and route to the
  ordinary-observer test.
- A renewal cancel-by date that falls on a Sunday should not land on the user's
  calendar correctly only because the user thought to ask about weekdays. The
  register schema and the Mode 2 output should carry the business-day roll-back
  themselves.
- An FLSA back-pay computation should not get the regular-rate formula right
  only because the model happens to remember §207(e). The skill should have a
  §207(e) checklist that forces the inclusions, the 0.5× vs. 1.5× posture, the
  liquidated-damages doubling, and the SOL lookback into every answer.

## A few concrete things that follow

- **Put the doctrine in the skill.** If a skill's mode covers patents, cover
  design patents. If it covers overtime, cover the regular-rate formula. Not a
  pointer to "and also think about" — the actual checklist.
- **Attach provenance tags to numbers, not to paragraphs.** `[model calculation
  — verify against the notice clause]` next to the date; `[verify — consult
  wage-and-hour counsel before asserting or paying]` on the line the back-pay
  number appears. Tags on surrounding prose get lost; tags on the load-bearing
  digit do not.
- **Make the decline pathway a scaffold, not an escape hatch.** If the right
  answer to some category of question is "I decline to compute," bake that into
  the skill as a hard gate. `legal-clinic`'s `/deadlines` do-not-compute rule is
  the pattern: stated plainly, non-overridable, owned by the skill.
- **Write the gate header so the gate is default-on.** If there is an
  exemption, phrase the heading as the gate and narrow the exemption in a
  sub-bullet, not the other way around. A load-bearing parenthetical is a bug
  waiting to be reintroduced by the next edit.

## Workflow notes

- **Read the plugin's `CLAUDE.md` before editing any skill in that plugin.** The
  practice profile, the integrations table, the shared guardrails, and the
  decision-posture statement all shape what the skill should say and omit.
- **Bump the plugin version on a material change.** Patch bumps for behavior
  additions; minor bumps for new skills or new required inputs.
- **Run the validators.** `scripts/validate.py` and `scripts/lint-tool-scope.py`
  check the structural invariants the plugin loader depends on.
- **Do not remove the shared guardrails from CLAUDE.md.** The net stays. The
  goal is a skill that doesn't need the net, not a plugin without one.
