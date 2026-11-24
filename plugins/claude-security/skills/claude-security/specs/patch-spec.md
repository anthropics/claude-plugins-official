# Patch products specification

The shape of what the fix job writes. Three parts: the working record the Security Lead writes by hand (`patches.json`), the files into which it copies each reviewer's attack paths, and the products `patch_artifacts.py` renders from both plus the raw diffs git wrote. The Security Lead narrates and decides; the script writes the products, so no diff byte and no confidence claim is ever re-typed by a model on its way to the user.

## The working record — `patches.json`

Written by the Security Lead into the patch working ground (`<report dir>/.claude-security-run/patch-<ts>/patches.json`). One object with a `units` array, one entry per unit that `--prepare` printed:

```json
{
  "units": [
    {
      "id": "F1",
      "title": "SQL injection in report export query",
      "status": "patch_written",
      "summary": "The export endpoint interpolated the user-supplied table name into SQL; the patch binds it against the allowlist of exportable tables instead.",
      "claims": {
        "targeted": { "state": "CONFIDENT", "evidence": "one hunk, export.py:88-94, only the query construction moved" },
        "no_new_vulnerability": { "state": "CONFIDENT", "evidence": "the allowlist is the existing EXPORT_TABLES constant; no new input reaches SQL" },
        "behaviour_unchanged": { "state": "CONFIDENT", "evidence": "tests/test_export.py covers all three exportable tables and passes" }
      },
      "untested": false,
      "tests_run": "python -m pytest tests/ -q (41 passed)",
      "reviewed_paths": ["M src/export.py"],
      "attempts": 1
    },
    {
      "id": "F3",
      "title": "Path traversal in attachment download",
      "status": "declined",
      "attempts": 1,
      "claims": {
        "behaviour_unchanged": { "state": "UNSURE", "evidence": "no test covers the download handler and three callers pass paths I could not trace" }
      },
      "decline_reason": "I couldn't establish that the fix leaves existing download behaviour unchanged, and the fresh reviewer found the finding's exploit still reachable through the thumbnail handler, so no patch was written.",
      "recommendation": "Resolve the requested path against the attachments root and reject anything outside it before opening the file."
    },
    {
      "id": "F5",
      "title": "SQL injection via sort parameter in note search",
      "status": "declined",
      "attempts": 1,
      "confirmed": false,
      "decline_reason": "The verifier found the sort parameter only selects one of three constant column names and the query is parameterised, so the injection the report describes does not work at this revision.",
      "recommendation": "Whitelist the sort values and never format request data into the SQL string."
    }
  ]
}
```

Fields, per unit:

| field             | when                                  | meaning                                                                 |
| ----------------- | ------------------------------------- | ----------------------------------------------------------------------- |
| `id`              | always                                | the finding id, `^F[0-9]{1,9}$` — the only report-derived value acted on |
| `title`           | always                                | the finding's title, quoted                                             |
| `status`          | always                                | `patch_written`, `declined`, or `skipped_stale`                         |
| `summary`         | `patch_written`                       | one line: root cause and what the change does                           |
| `confirmed`       | a `declined` unit declined as not confirmed | `false`: the verifier named what in the pre-change code defeats the finding's exploit, so the unit was declined as not confirmed; `true` is accepted and carried to `patches.jsonl` but renders nothing; omitted otherwise, and ignored on a `skipped_stale` unit |
| `attempts`        | `patch_written` / `declined`          | how many fix attempts were made: 1 for every unit whose generator was dispatched, or 2 for one that went through the revision round; 0 only for a declined unit whose workspace could not be opened; ignored on a `skipped_stale` unit |
| `claims`          | `patch_written` (all three); otherwise those the verifier stated | `targeted`, `no_new_vulnerability`, `behaviour_unchanged`, each `{state, evidence}`; `state` is `CONFIDENT`, `NOT_CONFIDENT`, or `UNSURE` |
| `untested`        | `patch_written` (required, true/false)  | `true` when no test in the project's own suite ran the patched code (a verifier's ad-hoc harness does not count) |
| `tests_run`       | `patch_written`                       | the verifier's verbatim test commands, or "none possible: …"            |
| `reviewed_paths`  | `patch_written`                       | the verifier's `REVIEWED_PATHS` (name-status form)                      |
| `decline_reason`  | `declined` / `skipped_stale`          | why no patch was written, in a sentence the user can read               |
| `recommendation`  | `declined` (optional)                 | the report's original fix recommendation, so the user still has it     |

The attack paths are not a field here: the script reads them from the files below.

`title`, `summary`, `tests_run` and each claim's `evidence` are one-line fields written into the patch's `#` comment header, so each run of white space in any of them is folded to one space. Longer explanation belongs in the note fields, which are markdown body, not header lines.

The script refuses the record (exit 1, a message naming the field) when:

- a unit id is malformed, a status is unknown, or `attempts` is missing on a written or declined unit, is not 0, 1 or 2, or is 0 on a written one;
- a `patch_written` unit lacks a claim, has any claim not `CONFIDENT`, or omits `untested`;
- a unit lacks the `F<n>.paths.<round>` file of one of its attempts, or a file does not hold a whole block;
- such a file exists for an attempt that the record does not count (a further attempt, a unit that it leaves out, or a stale one) and is not empty;
- a `patch_written` unit's last round says `NO REPORT`, or holds a path that is not `set_aside`;
- a declined unit has no reason, or `confirmed` is not true or false, is false on a unit that is not declined, or is false beside a `still_reachable` attack path;
- a required `F<n>.diff` is missing or does not start with a `diff --git` header;
- the record names a unit id `--prepare` did not lay out in `findings/`.

Patches are byte-faithful: the diff git wrote reaches `F<n>.patch` unchanged, CRLF and non-UTF-8 files included. It also refuses to deliver anywhere but a `patches/` directory inside a `CLAUDE-SECURITY-<timestamp>` report folder. A refusal is corrected and the script rerun — never worked around.

## The attack paths — `<patch dir>/F<n>.paths.<round>`

One file for each attempt of each unit, beside `patches.json`. The Security Lead writes it as the fresh `scan-researcher`'s reply arrives. It holds the block that ends that reply, exactly as written, in the form that `patch-review-brief.md` asks for. Beside `confirmed` false, a `still_reachable` path into other code gets the kind `set_aside`. `<round>` is the attempt's number: 1, or 2 for the revision round.

```
1 | still_reachable | GET /thumb?name=../../etc/passwd reaches the same unconfined attachment_path helper through the thumbnail handler
2 | set_aside | GET /attachments?sort= reaches a query built from the request at attachments.py:40
PATHS: 2
```

Each line has its number, from 1 up, the path's kind (`opened`, `still_reachable` or `set_aside`), and the path on one line. The count comes last, and `PATHS: 0` alone means that the researcher found none. The script reads a kind whatever its case, spacing or hyphens, and any word that is none of the three kinds as `still_reachable`, with the word kept in the path's text. The one line `NO REPORT` stands for an attempt with no whole block, or with no researcher.

A declined unit shows every round's paths. A written patch shows its last round's, and an earlier round's `set_aside` ones.

## The products — `<report dir>/patches/`

Besides what the table lists, a written patch's `F<n>.md` gives the report's recommendation, where its finding record has one, and the verifier's lines from `F<n>.notes`, or a warning where none were recorded. `patches.jsonl` has those lines as `verifier_notes`: `[]` for `none`, `null` where none were recorded and for a unit with no patch. Unless the verifier noted `none`, the patch's header and `PATCHES.md` say that the patch may not fully fix the finding, and name `F<n>.md`.

| file             | content                                                                                 |
| ---------------- | --------------------------------------------------------------------------------------- |
| `F<n>.patch`     | the raw diff git wrote (`F<n>.diff`), with a `#`-comment header above the first `diff --git` line naming the finding, the finding's mark where it has one (`older_than_the_change`), the trust label -- analyzed by a panel of agents (the independent verifier plus the fresh reviewer who challenges the diff for an attack path it opens, or a route it leaves open to the finding's exploit) -- the three claims and their evidence, the untested notice when `untested` is true, and a pointer to `F<n>.md`. Where the apply check names a step, the header opens with a warning: not to apply the patch as it is, the check's words, and the step. `git apply` ignores the header. |
| `F<n>.md`        | the note beside each unit, with the finding's mark where it has one: for a written patch, the same panel-of-agents trust label, the summary, claims, diffstat (a rename shown as `old => new`, a file's permission change named beside its path, a binary file sized as `(binary)`), tests run, the apply check's outcome, and the step that it calls for, with a command only where one fits -- the report path in that command shell-quoted, so a space in a parent directory's name keeps the command pasteable; for a declined unit, how many attempts were made and that none passed the panel's review — or, when `confirmed` is false, that the review found the finding not exploitable as the report describes at this revision — the reason, any claim not made with confidence, the rejected attempt's diffstat (when the verifier reviewed a diff), and the original recommendation; for either, the attack paths the fresh reviewer reported, each under its kind, a set-aside one marked as not addressed here, and each attempt for which no list was recorded. |
| `PATCHES.md`     | the one-page index, with each finding's mark where it has one: patches written (each noted as analyzed by a panel of agents, and a caveat flagged when `untested` is true, and a pointer to `F<n>.md` where the apply check was not clean or gave no answer), units with no patch, after how many attempts or that the finding was not confirmed, and why, the paths the reviewers set aside, and the apply instructions. The trust label the user reads is always the panel's analysis -- never a "tested"/"untested" label. |
| `patches.jsonl`  | one record per unit: `provenance` (the fixed mark of this script, which a reader may require before trusting the record), `id`, `status`, `base` (the revision every patch applies to), `patch`, `note`, `summary`, `claims`, `untested`, `tests_run`, `reviewed_paths`, `attack_paths`, `no_report` (the attempts for which no list of attack paths was recorded), `attempts`, `confirmed`, `diffstat`, `apply_check`, `decline_reason`. |

The render moves the products that an earlier run left in the folder into a new `earlier-<UTC time>/` folder inside it, and removes any product's leftover `<name>.partial`; other files in the folder are never touched. Its removal of the working ground afterwards never fails the run: a path it cannot remove there is a printed warning.
