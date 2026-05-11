# Freshness Fields for Community Skill Authors

If your skill bundles reference content under `references/` — regulations,
statutes, procedures, forms, checklists keyed to current law — declare its
freshness in `SKILL.md` frontmatter:

```yaml
---
name: my-legal-skill
description: ...
last_verified: 2026-04-15       # When you last confirmed the bundled references are current
freshness_window: 6 months      # How long the verification is good for (default: 6 months for
                                # regulatory/statutory content, 12 months for procedural/stylistic)
freshness_category: regulatory  # regulatory | procedural | stylistic | stable
verified_against:               # Where you verified — a URL the user can check themselves
  - https://www.ecfr.gov/current/title-16/part-312
  - https://www.federalregister.gov/...
---
```

## Why this matters

A skill last touched two years ago can keep shipping a retired regulation.
Byte-identical files look current to a commit-based updater forever. The harm
lands when the user invokes the skill and relies on the stale content — not
when they installed it and read a warning they've forgotten.

## What happens with these fields

- The builder-hub's **skill-installer** checks `last_verified` against
  `today + freshness_window` before executing. If past the window, it surfaces
  a warning before running.
- The **skills-qa** review flags skills with bundled `references/` and no
  `last_verified` as Some Concern.
- The **auto-updater** treats a stale `last_verified` as a re-verification
  trigger even when the git SHA hasn't changed.
- The user's freshness thresholds (set at cold-start) can be **tighter** than
  the author's window — the tighter of the two wins.

Without these fields, the hub flags the skill as "freshness unknown" and warns
the user at install and at invocation.

## Accepted values (strict)

The hub treats frontmatter fields as data written by an external publisher,
not as instructions. Only values that match the shapes below are honored.
Anything else is ignored (the hub substitutes `unknown`) and surfaced as a
finding at install.

| Field | Accepted shape |
|---|---|
| `last_verified` | ISO 8601 date: `YYYY-MM-DD` (e.g., `2026-04-15`). A future date is treated as `unknown`. |
| `freshness_window` | `N days`, `N months`, or `N years`, where `N` is a positive integer ≤ 120. |
| `freshness_category` | One of: `regulatory`, `procedural`, `stylistic`, `stable`. |
| `verified_against` | List of URLs. Each must be `https://` (or `http://`), with a hostname and optional path. Query strings and fragments are stripped before display. Max 10 entries, max 2,048 chars each. |

Free-form prose, multi-line strings, directives, role-change language,
unusual unicode, or encoded content in any of these fields is rejected at
install. The installer records the raw value in the install log (truncated,
quoted, never interpreted) and treats the field as missing.

## Categories

- **regulatory** — rules, statutes, agency guidance. Moves fast.
- **procedural** — court rules, filing procedures, forms tied to procedure.
- **stylistic** — house style, formatting templates, clause libraries.
- **stable** — historical references, bar exam outlines, doctrinal primers
  that move on the scale of years, not months.

If you're not sure, pick the narrower (faster-moving) category. The user's
threshold will clamp down on it if they want tighter; the author's value is
a ceiling, not a floor.

## What "last verified" actually means

Not "last edited." Not "last commit." **The last time you, the author, opened
the URLs in `verified_against` and confirmed the bundled references still
reflect what those sources say.** If the bundled PDF is an old version of 16
CFR 312 but the current eCFR shows different text, the verification failed —
update the references and push a new commit, or update `last_verified` only
after the references match the sources again.

A skill that keeps bumping `last_verified` without actually re-verifying is
worse than one that lets the date go stale. The stale date is honest about
what the author did. The bumped date is a claim the user relies on.

## When to set `freshness_category: stable`

Rarely. A skill that bundles the text of a doctrine (e.g., the elements of
promissory estoppel) or the structure of a framework (e.g., the FRCP discovery
timeline shape) is stable. A skill that bundles specific rule text, specific
thresholds, specific forms, or specific procedural deadlines is NOT stable
even if the underlying doctrine is — the bundled artifact is the thing that
goes stale.

If in doubt: not stable.
