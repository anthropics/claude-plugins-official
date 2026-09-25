# Patch products specification

The shape of what the fix job writes. Two halves: the working record the Security Lead writes by hand (`patches.json`), and the products `patch_artifacts.py` renders from it plus the raw diffs git wrote. This mirrors `report-spec.md`: the model narrates and decides, the script writes the files, so no diff byte and no confidence claim is ever re-typed by a model on its way to the user.

## The working record — `patches.json`

Written by the Security Lead into the patch working ground (`<report dir>/.claude-security-run/patch-<ts>/patches.json`). One object with a `units` array, one entry per selected finding:

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
      "attempts": 1,
      "attack_paths": [
        { "kind": "set_aside", "text": "GET /admin/diag?host= reaches subprocess.run with shell=True at admin/diag.py:12; a command injection, pre-existing and unrelated to this finding" }
      ]
    },
    {
      "id": "F3",
      "title": "Path traversal in attachment download",
      "status": "declined",
      "attempts": 1,
      "claims": {
        "behaviour_unchanged": { "state": "UNSURE", "evidence": "no test covers the download handler and three callers pass paths I could not trace" }
      },
      "attack_paths": [
        { "kind": "still_reachable", "text": "GET /thumb?name=../../etc/passwd reaches the same unconfined attachment_path helper through the thumbnail handler" }
      ],
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
| `untested`        | `patch_written` (required, true/false)  | `true` when no test in the project's own suite exercises the patched code (a verifier's ad-hoc harness does not count) |
| `tests_run`       | `patch_written`                       | the verifier's verbatim test commands, or "none possible: …"            |
| `reviewed_paths`  | `patch_written`                       | the verifier's `REVIEWED_PATHS` (name-status form)                      |
| `attack_paths`    | `patch_written` (required, `[]` when none); otherwise when any were reported | the fresh `scan-researcher`'s attack paths, each `{kind, text}`: `kind` is `opened` (by the change), `still_reachable` (the finding's exploit, by another route) or `set_aside` (pre-existing and unrelated to the finding), as the researcher labeled it — or `set_aside` for a still-reachable path into other code reported beside `confirmed` false; `text` is the path in its words, one line |
| `decline_reason`  | `declined` / `skipped_stale`          | why no patch was written, in a sentence the user can read               |
| `recommendation`  | `declined` (optional)                 | the report's original fix recommendation, so the user still has it     |

A rejected attempt is not kept — neither its working tree nor its raw diff survives the run, because it was rejected; the declined note carries what blocked it and the attempt's diffstat instead. There is no field naming a scratch directory or a saved diff, since the whole working ground is removed once the products are written.

`title`, `summary`, `tests_run` and each claim's `evidence` are one-line fields written into the patch's `#` comment header, and each attack path's `text` is one bullet of a note, so an embedded line break in any of them is folded to a space. Longer explanation belongs in the note fields, which are markdown body, not header lines.

The script refuses the record (exit 1, a message naming the field) when:

- a unit id is malformed, a status is unknown, or `attempts` is missing on a written or declined unit, is not a whole number, or is 0 on a written one;
- a `patch_written` unit lacks a claim, has any claim not `CONFIDENT`, omits `untested` or `attack_paths`, or carries an attack path not set aside;
- any attack path has an unknown kind or no text;
- a declined unit has no reason, or `confirmed` is not true or false, is false on a unit that is not declined, or is false beside a `still_reachable` attack path;
- a required `F<n>.diff` is missing or holds no `diff --git` section;
- the record names a unit id `--prepare` did not lay out in `findings/`.

Patches are byte-faithful: the diff git wrote reaches `F<n>.patch` unchanged, CRLF and non-UTF-8 files included. It also refuses to write anywhere but a `patches/` directory inside a `CLAUDE-SECURITY-<timestamp>` report folder, so a mistaken path never gets an arbitrary directory fenced with a `.gitignore`. A refusal is corrected and the script rerun — never worked around.

## The products — `<report dir>/patches/`

| file             | content                                                                                 |
| ---------------- | --------------------------------------------------------------------------------------- |
| `F<n>.patch`     | the raw diff git wrote (`F<n>.diff`), with a `#`-comment header above the first `diff --git` line naming the finding, the trust label -- verified by a panel of agents (the independent verifier plus the fresh reviewer who challenges the diff for an attack path it opens, or a route it leaves open to the finding's exploit) -- the three claims and their evidence, the coverage notice when `untested` is true, and the one-line apply command. `git apply` ignores the header. |
| `F<n>.md`        | the note beside each unit: for a written patch, the same panel-of-agents trust label, the summary, claims, diffstat (a rename shown as `old => new`, a file's permission change named beside its path, a binary file sized as `(binary)`), tests run, the `git apply --check` outcome, and how to apply it -- the report path in that command shell-quoted, so a space in a parent directory's name keeps the command pasteable; for a declined unit, how many attempts were made and that none passed the panel's review — or, when `confirmed` is false, that the review found the finding not exploitable as the report describes at this revision — the reason, any claim not made with confidence, the rejected attempt's diffstat (when the verifier reviewed a diff), and the original recommendation; for either, the attack paths the fresh reviewer reported, each under its kind, a set-aside one marked as not addressed here. |
| `PATCHES.md`     | the one-page index: patches written (each noted as verified by a panel of agents, with the coverage caveat flagged when `untested` is true), units with no patch, after how many attempts or that the finding was not confirmed, and why, the paths the reviewers set aside, and the apply instructions. The trust label the user reads is always the panel's verification -- never a "tested"/"untested" label. |
| `patches.jsonl`  | one record per unit: `id`, `status`, `base` (the revision every patch applies to), `patch`, `note`, `claims`, `untested`, `tests_run`, `reviewed_paths`, `attack_paths`, `attempts`, `confirmed`, `diffstat`, `apply_check`, `decline_reason`. |

On every run the script also removes any `F<n>.patch` / `F<n>.md` an earlier run left in the folder that it did not write this time, so the folder always matches its index (a finding that earned a patch before and is declined now never keeps a stale, unlisted patch); other files in the folder are never touched. The script also fences the report directory with a `.gitignore` containing `*` when it lacks one, so a stray `git add` never sweeps a suggested patch into a commit, and it validates every written patch read-only against the user's repository with `git apply --check`, recording the result — a patch that no longer applies cleanly is reported, never dropped, because it was built against the recorded revision and the working tree may simply have moved. Finally it removes the whole patch working ground: every scratch workspace (`scratch-F<n>`), then the `patch-<ts>` directory itself with `patches.json`, the prepared `findings/` and the raw diffs, and the `.claude-security-run/` directory above it when nothing else remains. Each removal is fenced to that exact layout, and a path that cannot be removed is a printed warning, never a failed run. A fix run leaves only the `patches/` products behind.
