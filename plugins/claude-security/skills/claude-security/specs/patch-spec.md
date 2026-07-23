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
      "reviewed_paths": ["M src/export.py"]
    },
    {
      "id": "F3",
      "title": "Path traversal in attachment download",
      "status": "declined",
      "claims": {
        "behaviour_unchanged": { "state": "UNSURE", "evidence": "no test covers the download handler and three callers pass paths I could not trace" }
      },
      "decline_reason": "I couldn't establish that the fix leaves existing download behaviour unchanged, so no patch was written.",
      "recommendation": "Resolve the requested path against the attachments root and reject anything outside it before opening the file."
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
| `claims`          | always (all three for `patch_written`) | `targeted`, `no_new_vulnerability`, `behaviour_unchanged`, each `{state, evidence}`; `state` is `CONFIDENT`, `NOT_CONFIDENT`, or `UNSURE` |
| `untested`        | `patch_written` (required, true/false)  | `true` when no test in the project's own suite exercises the patched code (a verifier's ad-hoc harness does not count) |
| `tests_run`       | `patch_written`                       | the verifier's verbatim test commands, or "none possible: …"            |
| `reviewed_paths`  | `patch_written`                       | the verifier's `REVIEWED_PATHS` (name-status form)                      |
| `decline_reason`  | `declined` / `skipped_stale`          | why no patch was written, in a sentence the user can read               |
| `recommendation`  | `declined` (optional)                 | the report's original fix recommendation, so the user still has it     |

A rejected attempt is not kept — neither its working tree nor its raw diff survives the run, because it was rejected; the declined note carries the blocking claim and the attempt's diffstat instead. There is no field naming a scratch directory or a saved diff, since the whole working ground is removed once the products are written.

`title`, `summary`, `tests_run`, and each claim's `evidence` are one-line fields: they are written into the patch's `#` comment header, so an embedded line break in any of them is folded to a space. Longer explanation belongs in the note fields, which are markdown body, not header lines.

The script refuses the record (exit 1, a message naming the field) when a unit id is malformed, a status is unknown, a `patch_written` unit lacks a claim, has any claim not `CONFIDENT`, or omits `untested`, a declined unit has no reason, or a required `F<n>.diff` is missing or holds no `diff --git` section. Patches are byte-faithful: the diff git wrote reaches `F<n>.patch` unchanged, CRLF and non-UTF-8 files included. It also refuses to write anywhere but a `patches/` directory inside a `CLAUDE-SECURITY-<timestamp>` report folder, so a mistaken path never gets an arbitrary directory fenced with a `.gitignore`. A refusal is corrected and the script rerun — never worked around.

## The products — `<report dir>/patches/`

| file             | content                                                                                 |
| ---------------- | --------------------------------------------------------------------------------------- |
| `F<n>.patch`     | the raw diff git wrote (`F<n>.diff`), with a `#`-comment header above the first `diff --git` line naming the finding, the trust label -- verified by a panel of agents (the independent verifier plus the fresh reviewer of the bare diff) -- the three claims and their evidence, the coverage notice when `untested` is true, and the one-line apply command. `git apply` ignores the header. |
| `F<n>.md`        | the note beside each unit: for a written patch, the same panel-of-agents trust label, the summary, claims, diffstat (a rename shown as `old => new`, a file's permission change named beside its path), tests run, the `git apply --check` outcome, and how to apply it -- the report path in that command shell-quoted, so a space in a parent directory's name keeps the command pasteable; for a declined unit, the blocking claim, the reason, the rejected attempt's diffstat (when the verifier reviewed a diff), and the original recommendation. |
| `PATCHES.md`     | the one-page index: patches written (each noted as verified by a panel of agents, with the coverage caveat flagged when `untested` is true), units with no patch and why, and the apply instructions. The trust label the user reads is always the panel's verification -- never a "tested"/"untested" label. |
| `patches.jsonl`  | one record per unit: `id`, `status`, `base` (the revision every patch applies to), `patch`, `note`, `claims`, `untested`, `tests_run`, `reviewed_paths`, `diffstat`, `apply_check`, `decline_reason`. |

On every run the script also removes any `F<n>.patch` / `F<n>.md` an earlier run left in the folder that it did not write this time, so the folder always matches its index (a finding that earned a patch before and is declined now never keeps a stale, unlisted patch); other files in the folder are never touched. The script also fences the report directory with a `.gitignore` containing `*` when it lacks one (a scan writes it up front; a patch run against an older report directory adds it), so a stray `git add` never sweeps a suggested patch into a commit, and it validates every written patch read-only against the user's repository with `git apply --check`, recording the result — a patch that no longer applies cleanly is reported, never dropped, because it was built against the recorded revision and the working tree may simply have moved. Finally it removes the whole patch working ground: every scratch workspace (`scratch-F<n>`), then the `patch-<ts>` directory itself with `patches.json` and the raw diffs, and the `.claude-security-run/` directory above it when nothing else remains. Each removal is fenced to that exact layout, and a path that cannot be removed is a printed warning, never a failed run. A fix run leaves only the `patches/` products behind.
