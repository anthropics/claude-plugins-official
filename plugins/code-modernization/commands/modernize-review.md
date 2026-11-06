---
description: Confirm or correct the business rules that need a person's judgement; the plan and the build read your answers
argument-hint: <system> [flagged|p0|all]
arguments: system scope
---

Ask a person to decide the business rules in `analysis/$system/BUSINESS_RULES.md` that depend on judgement, and record each answer so the plan and the build honor it. Agents mined the rules and a second agent checked every citation, but only someone who knows the business can say whether a rule is *right*: whether a truncation is intended or a defect, whether a threshold is still the policy. This command asks in a pop-up and never edits `BUSINESS_RULES.md`.

## 1 — Choose the rules

Read `BUSINESS_RULES.md` (each card has `### RULE-NNN`, Priority, Confidence, and sometimes a suspected defect or an SME question) and, if it exists, `analysis/$system/RULE_REVIEWS.json`; rules already decided are skipped, and you say how many. `$scope` picks the rest:

- **flagged** (the default): P0 rules that have a suspected defect, an SME question or less than High confidence, plus any rule the brief's open questions name.
- **p0**: every P0 rule. **all**: every rule.

Say how many rules will be asked (about a minute per ten). If none is left, say so and give the next command.

## 2 — Ask

Use the AskUserQuestion tool, never chat text, up to four rules per call. One question per rule: its id as the header; the title, the plain-English statement, its Given/When/Then in one line, the cited lines (`file:line`) and the suspected defect or SME question if it has one as the question; and three options: **Right** (the rule is correct and wanted), **Wrong, or not wanted** (it misdescribes the code, or the code does this today but should not), **Not sure** (needs a discussion). The person can type a note instead of choosing: what is right, or the question that needs answering. Keep it, in their words. Stop when they say to. Verdicts the person already typed in the request (`RULE-004 wrong: it truncates on purpose`) are recorded as given, with no pop-up for those rules. Without the tool and without typed verdicts (a headless run) do not guess: leave every rule unreviewed and say so.

## 3 — Record

Merge the answers into `analysis/$system/RULE_REVIEWS.json`, the same file the live progress pane's review deck (`/modernize-review-pane`) writes:

```json
{ "system": "<name>", "version": 1, "reviews": {
    "RULE-004": { "verdict": "confirmed", "at": "<ISO time>", "title": "<the rule's title>", "note": "<their words, optional>" } } }
```

`verdict` is `confirmed` (Right), `wrong` (Wrong, or not wanted) or `discuss` (Not sure). Change an earlier entry only when a new answer replaces it. Write `analysis/$system/RULE_REVIEWS.md` from it: a short paragraph, then a table `Rule | Verdict | When | Title | Note`, sorted by rule number. Refresh the report (`python3 "${CLAUDE_PLUGIN_ROOT}/scripts/build_report.py" $system`, a convenience: if it fails or `python3` is missing, say so in one line and carry on).

## 4 — What happens next

Tell the person, in three lines: rules marked wrong or needing discussion are not settled; `brief` lists them as open questions and never builds a Behavior Contract on them; `transform` and `reimagine` will not pin a wrong rule as the oracle and stop on a P0 rule still under discussion. Then the next command: `/code-modernization:modernize-brief $system` (run it again if the brief exists and any rule changed), or the brief's next build command when the plan is already approved.
