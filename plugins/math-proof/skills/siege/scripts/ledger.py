#!/usr/bin/env python3
"""Bookkeeping helper for the math-proof plugin's siege skill: the four mechanical
decisions of the round loop and its waves that should not depend on a
model's judgment.

    ledger.py check DIR R WAVE MIN_ROUNDS ATTEMPT
        After the round-R plan step: validates the shape of what the judge
        wrote, applies the early-conclusion gate, commits the round's ledger
        lines (numbered on) to DIR/ledger.md once the round's plan is final,
        and prints ONE verdict line for the orchestrator:
            WAVE <n> FLOOR <f>  run round R's wave (files roundR_q1.md .. roundR_q<n>.md);
                                stop the run if fewer than <f> of its queries come
                                back answered or partial
            CONCLUDE <why>    leave the round loop
            RETRY: <text>     relaunch the plan step with <text> as an added
                              first paragraph (ATTEMPT < 3 only)
            TAIL: <why>       give up on this round and go to the proof tail
    ledger.py append DIR R
        Number the lines of DIR/roundR_ledger_block.md on from the ledger of
        rounds before R, write DIR/roundR_ledger.md, rebuild DIR/ledger.md.
        Idempotent (safe to re-run for the same round).
    ledger.py gate DIR [R]
        Print CONCLUDE or "REJECT: <reason>" for the early-conclusion gate on
        the assembled ledger as it stands (plus round R's not-yet-appended
        block, numbered on, when R is given).
    ledger.py answers DIR Q1 [Q2 ...]
        After a wave's workers have all returned: decide which answer files
        are finished. A worker that finishes writes the end line
        "=== END OF ANSWER <Q> ===" last; a file without it was cut off. For
        each query stem Q (e.g. round2_q3) prints "Q: answered" (DIR/Q.answer.md
        ends with Q's end line), "Q: partial" (only an unfinished file exists)
        or "Q: no answer", then one TOTAL line with the number of queries and
        the three counts. Side effects, so that a .answer.md file always means
        a finished answer: an unfinished DIR/Q.answer.md is moved to
        DIR/Q.partial.md (if an older, longer Q.partial.md is already there,
        that one stays and the new file goes to Q.partial.prev.md instead; a
        shorter older one moves to Q.partial.prev.md), and an empty
        DIR/Q.answer.md is deleted. Nothing a worker wrote is ever deleted or
        overwritten except an older Q.partial.prev.md. Idempotent; an ERROR
        line (and nothing touched) if a stem is wrong.

A malformed command (DIR not an existing directory, a missing or non-numeric
argument) prints an ERROR line and touches nothing. Standard library only
(Python 3.7 or later); files are read and written as UTF-8 regardless of the
platform's default encoding. Always exits 0 and says what it decided on
stdout; any internal error prints a fail-closed verdict (RETRY/REJECT, or an
ERROR line from `answers`) rather than a traceback the orchestrator might
misread.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

MAX_ATTEMPTS = 3  # plan attempts per round before a shortfall is accepted
ENC = dict(encoding="utf-8", errors="replace")

# ---- ledger parsing and the early-conclusion gate --------------------------
_LEDGER_STATUS_WORDS = ("OPEN", "PROVED", "REFUTED", "RETRACT", "RETRACTED", "SKETCHED")
_SETTLED = ("PROVED", "REFUTED")


def _take_tags(text: str, tags: set) -> str:
    """Strip a leading cluster of short bracketed tags ("[GOAL] ",
    "[AUDIT]: ") off text, adding each (upper-cased) to tags; a
    bracketed STATUS word is not a tag and stops the scan. Tags count
    only in this leading position — a prose mention later in the line
    ("the key step toward [GOAL]") is not a tag."""
    while True:
        m = re.match(r"^[*_\s]*\[([A-Za-z]{1,6})\]\s*[:\-–—]?\s*", text)
        if not m or m.group(1).upper() in _LEDGER_STATUS_WORDS:
            return text
        tags.add(m.group(1).upper())
        text = text[m.end() :]


def _cited_ids(text: str) -> set:
    """Ledger-id citations in an entry's free text. Two forms count:
    the word forms ("entry 12", "line 12", "claim 12", "item 12",
    "no. 12", and hybrids like "entry L5" — case-insensitive, the
    same family the RETRACT target parser tolerates) and the "#12"
    form. A prose "L12" deliberately does NOT count: every
    prose-position L-number matcher tried was fail-open on analysis
    prose — "in L2", "the L2 norm", "L2(R)", and coordinated lists
    like "verified the L1 and L2 bounds" collide exactly with the
    small ids early-round goals get. The plan brief and the RETRY
    correction teach the counted forms, so a judge writing
    "cites L12" is re-asked and can correct — a missed citation only
    costs a retry (fail-closed), where a spurious one ends a paid run
    early. Decimal and slash-fraction references never count ("Claim
    2.4 of the draft", "line 1/2" — ledger ids are integers), and the
    L hybrid ("entry L5") is not accepted after "line"/"lines", where
    it collides with geometry prose ("lines L2 and L4 are tangent").
    Bare integers are never citations (math prose is full of them)."""
    ids = set()
    for m in re.finditer(r"#(\d{1,4})\b(?![./]\d)", text):
        ids.add(int(m.group(1)))
    for m in re.finditer(
        r"\b(?:entry|entries|claim|claims|item|items|id|ids|no\.|number)"
        r"\s+#?L?(\d{1,4})\b(?![./]\d)"
        r"|\b(?:line|lines)\s+#?(\d{1,4})\b(?![./]\d)",
        text,
        re.IGNORECASE,
    ):
        ids.add(int(m.group(1) or m.group(2)))
    return ids


def ledger_entries(ledger_text: str) -> dict[int, dict]:
    """Parse the assembled numbered ledger ("12. OPEN: claim — locator",
    "13. RETRACT 4: reason") into {n: {status, text, retracted_by,
    goal, audit}}. Tolerant of what judges actually write after the
    number this script assigns: a self-assigned id ("L3.", "(L5)", "#7:"),
    markdown emphasis around the status word ("**OPEN**:"), any case,
    and RETRACT spelled "RETRACTED" / aimed at "L4", "#4", "entry 4" or
    "claim 4". status is upper-cased (PROVED / REFUTED / OPEN / RETRACT
    / whatever other word the judge used); retracted_by is the number
    of the RETRACT line that removed the entry from force, if any.
    goal/audit are set only by a [GOAL]/[AUDIT] tag in tag position —
    immediately before or after the status word — never by a prose
    mention elsewhere in the line."""
    out: dict[int, dict] = {}
    for ln in ledger_text.splitlines():
        m = re.match(r"\s*(\d+)\.\s+(.*)", ln)
        if not m:
            continue
        n, rest = int(m.group(1)), m.group(2)
        # a self-assigned id is dropped only when punctuated or bracketed
        # ("L3." / "L3:" / "(L3)" / "#3:"), so prose like "L2 norm" survives
        rest = re.sub(
            r"^[*_\s]*(?:\(\s*(?:L|#)?\s*\d+\s*\)\s*[.:\-–—]?|(?:L|#)\s*\d+\s*[.:)\-–—])\s*",
            "",
            rest,
        )
        tags: set = set()
        rest = _take_tags(rest, tags)
        sm = re.match(
            r"[*_\s\[]*([A-Za-z]+)[*_\]]*\s*[:.\-–—]?\s*(.*)", rest, re.DOTALL
        )
        if not sm:
            continue
        status, text = sm.group(1).upper(), sm.group(2)
        if status.startswith("RETRACT"):
            status = "RETRACT"
        text = _take_tags(text, tags)
        out[n] = {
            "status": status,
            "text": text,
            "retracted_by": None,
            "goal": "GOAL" in tags,
            "audit": "AUDIT" in tags,
        }
    for n, e in out.items():
        if e["status"] == "RETRACT":
            tm = re.match(
                r"[*_\s]*(?:entry|claim|item|line|no\.?|number)?\s*[#(]?\s*L?\s*(\d+)",
                e["text"],
                re.IGNORECASE,
            )
            if tm and int(tm.group(1)) in out and int(tm.group(1)) != n:
                out[int(tm.group(1))]["retracted_by"] = n
    return out


def early_conclude_ok(entries: dict[int, dict], known_locators=None) -> bool:
    """Early-conclusion gate. True when the ledger's goal is settled and
    twice audited:

    - the NEWEST in-force [GOAL]-tagged line is PROVED or REFUTED (the
      ledger's own supersession rule: a later unsettled [GOAL] update
      takes the goal back out of play without needing a RETRACT);
    - at least two in-force PROVED [AUDIT] lines — the goal line itself
      never counts as its own audit, byte-duplicate lines count once —
      each cite the goal line, or a line its text cites, by ledger id
      ("entry 12" / "#12"; a prose "L12" does not count — see
      _cited_ids; ids must resolve to existing entries), and at least
      one cites the goal line itself;
    - when known_locators is given (check and gate pass the stems of the
      result files that actually exist), each counted audit line must
      name one — matched case-insensitively, since the files are all
      lowercase while a judge may title-case at sentence start — and
      the counted audits must span at least two distinct locators,
      tying the certifications to queries that really ran, from at
      least two separate queries.

    REFUTED settles a prove-or-disprove goal as surely as PROVED (an
    audited disproof concludes the run). One consequence of the
    cite-the-goal requirement, by design: audits recorded before the
    [GOAL] line existed (or before a [GOAL] re-statement) cite older
    ids and so cannot satisfy it — append-only history is never
    implicitly re-tagged — and the concluding plan's own ledger block
    must re-state at least one certification citing the goal line's
    id (the RETRY correction names this fix). The gate is a structured
    attestation check on judge-written ledger text, not an independent
    proof check: the run's correctness still rests on the audits being
    real, which the locator requirement grounds but cannot prove."""
    live = {n: e for n, e in entries.items() if e["retracted_by"] is None}
    goals = sorted(n for n, e in live.items() if e.get("goal"))
    if not goals:
        return False
    g = goals[-1]
    if live[g]["status"] not in _SETTLED:
        return False
    chain = {g} | {m for m in _cited_ids(live[g]["text"]) if m in live}
    audits = []
    seen = set()
    for n in sorted(live):
        e = live[n]
        if e["status"] != "PROVED" or not e.get("audit") or e.get("goal") or n == g:
            continue
        cites = _cited_ids(e["text"]) & chain
        if not cites:
            continue
        norm = " ".join(e["text"].split()).lower()
        if norm in seen:
            continue
        locs = None
        if known_locators is not None:
            locs = {
                loc
                for loc in known_locators
                if re.search(
                    rf"(?<![A-Za-z0-9_]){re.escape(loc)}(?![A-Za-z0-9_])",
                    e["text"],
                    re.IGNORECASE,
                )
            }
            if not locs:
                continue
        seen.add(norm)
        audits.append((n, cites, locs))
    if len(audits) < 2:
        return False
    if not any(g in cites for _, cites, _ in audits):
        return False
    if known_locators is not None:
        spanned = set().union(*(locs for _, _, locs in audits))
        if len(spanned) < 2:
            return False
    return True


# ---- end of ledger parsing and the gate -----------------------------------


def _round_of(p: Path) -> int:
    m = re.fullmatch(r"round(\d+)_ledger", p.stem)
    return int(m.group(1)) if m else -1


def _parts(d: Path) -> list:
    return sorted(
        (p for p in d.glob("round*_ledger.md") if _round_of(p) >= 0), key=_round_of
    )


def ledger_text(d: Path, before=None) -> str:
    """The assembled ledger: the per-round numbered parts, in round order."""
    out = []
    for p in _parts(d):
        if before is not None and _round_of(p) >= before:
            continue
        out.append(p.read_text(**ENC))
    return "".join(out)


def numbered_lines(d: Path, r: int, block: str) -> list:
    """Round r's new lines, numbered on from the ledger of rounds < r, with
    the judge's bullets / numbering / self-assigned ids stripped."""
    prior = ledger_text(d, before=r)
    n = sum(1 for ln in prior.splitlines() if ln.strip())
    lines = []
    for raw in (block or "").splitlines():
        ln = re.sub(r"^(?:[-*]|\d{1,4}\.)\s+", "", raw.strip())
        ln = re.sub(
            r"^(?:\((?:L|#)?\d{1,4}\)(?:[.:]\s*|\s+)|(?:L|#)\d{1,4}[.:]\s+)(?=\S)",
            "",
            ln,
        )
        if ln:
            n += 1
            lines.append(f"{n}. {ln}")
    return lines


def append(d: Path, r: int) -> int:
    bp = d / f"round{r}_ledger_block.md"
    block = bp.read_text(**ENC) if bp.exists() else ""
    lines = numbered_lines(d, r, block)
    (d / f"round{r}_ledger.md").write_text(
        "".join(f"{ln}\n" for ln in lines), encoding="utf-8"
    )
    (d / "ledger.md").write_text(ledger_text(d), encoding="utf-8")
    return len(lines)


def known_locators(d: Path) -> set:
    return {p.name[: -len(".answer.md")] for p in d.glob("*.answer.md")}


def gate_reason(text: str, locs: set) -> str:
    """'' when the early-conclusion gate passes on this ledger text, else
    the first failing condition in plain words (the pass/fail decision
    itself is early_conclude_ok's)."""
    entries = ledger_entries(text)
    if early_conclude_ok(entries, locs):
        return ""
    live = {n: e for n, e in entries.items() if e["retracted_by"] is None}
    goals = sorted(n for n, e in live.items() if e.get("goal"))
    if not goals:
        return "the ledger has no [GOAL]-tagged line in force"
    g = goals[-1]
    if live[g]["status"] not in _SETTLED:
        return f"the newest [GOAL] line (entry {g}) is {live[g]['status']}, not PROVED or REFUTED"
    audits = [
        n
        for n, e in live.items()
        if e["status"] == "PROVED" and e.get("audit") and not e.get("goal") and n != g
    ]
    if len(audits) < 2:
        return f"only {len(audits)} PROVED [AUDIT] line(s) in force besides the goal line (entry {g}); two are needed"
    return (
        f"the [AUDIT] lines do not yet form a qualifying pair: each must cite the [GOAL] line "
        f"(entry {g}) or a line it cites as 'entry N' or '#N' (at least one citing entry {g} itself), "
        f"each must name the locator of an answer file that exists (e.g. round3_q2), and together "
        f"they must come from two different queries"
    )


def round_queries(d: Path, r: int) -> list:
    qs = [
        p for p in d.glob(f"round{r}_q*.md") if re.fullmatch(rf"round{r}_q\d+", p.stem)
    ]
    return sorted(qs, key=lambda p: int(p.stem.rsplit("_q", 1)[1]))


def is_attack(p: Path) -> bool:
    """kind: attempt declared near the top (first three non-empty lines that
    contain letters — tolerates a front-matter fence or a heading first)."""
    seen = 0
    for ln in p.read_text(**ENC).splitlines():
        if not re.search(r"[A-Za-z]", ln):
            continue
        if re.match(
            r"[*_\s`#>-]*kind[*_`\s]*[:=][\s\"'*_`]*(attempt|attack)", ln, re.IGNORECASE
        ):
            return True
        seen += 1
        if seen >= 3:
            return False
    return False


def is_withdrawn(p: Path) -> bool:
    """An emptied or '(withdrawn)' query file left over from a re-plan."""
    t = p.read_text(**ENC).strip()
    return not t or bool(
        re.fullmatch(r"[(\[]?\s*withdrawn\s*[)\]]?\.?", t, re.IGNORECASE)
    )


def wave_floor(n: int) -> int:
    """Fewest queries of a round's wave that may come back answered or
    partial before the run stops (3 in 10 of the wave, rounded down, and at
    least 1)."""
    return max(1, (3 * n) // 10)


_STEM = re.compile(r"[A-Za-z0-9_]+")


def is_end_line(line: str, stem: str) -> bool:
    """True when line is the end line of query `stem`, "=== END OF ANSWER
    <stem> ===", compared tolerantly: any case; the '=' rails in any
    length or absent, or drawn with other symbols; markdown dressing (a
    heading '#', a quote '>', a list marker, a wrapper or inner emphasis of
    backticks, asterisks, underscores or quotes, an escaped underscore
    'round2\\_q3'); a colon after ANSWER; a final period; and the stem given
    bare, as "<stem>.md", as "<stem>.answer.md" or as a plain path ending in
    one of those; a checklist item ("- [ ] ...") never counts. What must
    survive is exactly the words END OF ANSWER followed by this query's own
    name and nothing else: an end line copied in from another query's text
    (spliced into a task file by the judge, say) names that other query, and
    a sentence that merely mentions the end line has other words around it;
    neither counts."""
    if re.search(r"\[[ xX]\]", line):  # a checklist item is a plan, not an end line
        return False
    t = line.replace("\\_", "_")
    t = re.sub(r"[^A-Za-z0-9_./ -]+", " ", t)  # drop rails, emphasis, quotes
    t = " ".join(t.split()).strip("_- ")
    t = re.sub(r"^\d{1,2}\. ", "", t)  # a numbered-list marker
    name = rf"(?:[A-Za-z0-9_./-]*/)?{re.escape(stem)}(?:\.answer\.md|\.md)?"
    return bool(re.fullmatch(rf"END OF ANSWER {name} ?\.?", t, re.IGNORECASE))


_TAG_ONLY = re.compile(r"(?:\s*</?[A-Za-z_][\w:.-]*\s*/?>)+\s*")


def _last_line(text: str) -> str:
    """The last line of text that contains a letter or digit ('' if none),
    so that a closing code fence or a rule drawn under the end line does
    not hide it. A line made of nothing but bare markup tags without
    attributes (a stray '</details>' or similar closing tag a model sometimes
    emits after its last real line) is skipped the same way: a worker does not
    write its end line in that form, and skipping such a line can only
    reveal an end line the worker did write above it."""
    for ln in reversed(text.splitlines()):
        if not re.search(r"[A-Za-z0-9]", ln) or _TAG_ONLY.fullmatch(ln):
            continue
        return ln
    return ""


def answers(d: Path, args: list) -> str:
    """Classify each query's answer file and set unfinished ones aside (see
    the module docstring). Only one line of DIR/Q.answer.md is looked at, the
    last that contains a letter or digit and is not a bare markup tag;
    nothing else in any file is read for meaning."""
    stems, seen = [], set()
    for arg in args:
        stem = Path(arg).name  # tolerate a path or a file name for a stem
        for suffix in (".answer.md", ".partial.md", ".md"):
            if stem.endswith(suffix):
                stem = stem[: -len(suffix)]
                break
        if not _STEM.fullmatch(stem):
            return f"ERROR: {arg!r} is not a query stem (letters, digits and underscores only, e.g. round2_q3, extra_q1, r3_q2, r3_verify); nothing was touched"
        if not any((d / f"{stem}{x}").exists() for x in (".md", ".answer.md", ".partial.md")):
            return f"ERROR: there is no query file {stem}.md in {d} (wrong DIR, or a mistyped stem); nothing was touched"
        if stem not in seen:
            seen.add(stem)
            stems.append(stem)
    out, counts = [], {"answered": 0, "partial": 0, "no answer": 0}
    for stem in stems:
        a, p = d / f"{stem}.answer.md", d / f"{stem}.partial.md"
        status = None
        if a.exists():
            text = a.read_text(**ENC)
            if is_end_line(_last_line(text), stem):
                status = "answered"
            elif not text.strip():
                a.unlink()  # an empty file is no answer; any older partial stays
            elif p.exists() and p.stat().st_size > len(text.encode("utf-8", "replace")):
                # an older, longer unfinished file stays the partial; keep this one beside it
                a.replace(d / f"{stem}.partial.prev.md")
            else:
                if p.exists() and p.read_text(**ENC).strip():
                    p.replace(d / f"{stem}.partial.prev.md")
                a.replace(p)
        if status is None:
            partial = p.exists() and p.read_text(**ENC).strip()
            status = "partial" if partial else "no answer"
        counts[status] += 1
        out.append(f"{stem}: {status}")
    out.append(
        f"TOTAL ({len(stems)} {'query' if len(stems) == 1 else 'queries'}): answered {counts['answered']}, partial {counts['partial']}, no answer {counts['no answer']}"
    )
    return "\n".join(out)


GATE_RULE = (
    "Concluding before round {m} requires the claims ledger to hold the headline goal settled "
    "as a PROVED or REFUTED line tagged [GOAL], plus at least two PROVED lines tagged [AUDIT] "
    "from two separate verify queries, each naming its query's locator (e.g. round3_q2) and "
    "citing the [GOAL] line or its chain by ledger id written 'entry 12' or '#12', at least one "
    "citing the [GOAL] line itself. Only the newest [GOAL] line counts, it never counts as one of "
    "its own audits, and audits recorded before that line cite older ids — re-state the "
    "certifications citing its id (one suffices when the [GOAL] line itself cites the line they "
    "certify; otherwise two, from separate queries). Either compose a wave — for example verify "
    "queries whose certifications complete the chain — or conclude once the ledger qualifies."
)
STILL_THERE = (
    " The files from your previous attempt at this round (summary, ledger block, notes, any query "
    "files) are still in place and this round's ledger block has NOT been appended to DIR/ledger.md "
    "yet: rewrite DIR/round{r}_ledger_block.md so that it holds ALL of this round's new ledger lines, "
    "and if you now conclude instead of composing a wave, delete this round's query files "
    "(DIR/round{r}_q*.md) first — existing query files take precedence over a conclusion."
)


def check(d: Path, r: int, wave: int, min_rounds: int, attempt: int) -> str:
    """The round-r plan verdict. The round's ledger block is committed to
    ledger.md only together with a terminal verdict (WAVE / CONCLUDE /
    TAIL), never on RETRY — so a re-planned round simply rewrites its block,
    and the early-conclusion gate is evaluated on the ledger of earlier
    rounds plus this attempt's not-yet-appended lines."""
    final = attempt >= MAX_ATTEMPTS
    wave = max(1, wave)
    sp = d / f"round{r}_summary.md"
    if not sp.exists() or not sp.read_text(**ENC).strip():
        what = f"no running summary (DIR/round{r}_summary.md is missing or empty)"
        return (
            f"TAIL: {what} after {attempt} attempts"
            if final
            else f"RETRY: Correction — the previous attempt at this step wrote {what}. "
            f"Write DIR/round{r}_summary.md, then EITHER DIR/round{r}_DONE.md OR between 1 and {wave} query files."
            + STILL_THERE.format(r=r)
        )
    qs = round_queries(d, r)
    for p in [q for q in qs if is_withdrawn(q)]:
        p.replace(p.with_name(p.stem + ".withdrawn.md"))
        qs.remove(p)
    for k, p in enumerate(qs, 1):  # close gaps so the wave is q1..qn
        want = d / f"round{r}_q{k}.md"
        if p != want:
            p.replace(want)
            qs[k - 1] = want
    done = d / f"round{r}_DONE.md"
    if qs:  # composed queries take precedence over a verdict
        if done.exists():
            done.replace(d / f"round{r}_DONE.superseded.md")
        extra = ""
        if len(qs) > wave:
            for p in qs[wave:]:
                p.replace(p.with_name(p.stem + ".overcount.md"))
            qs = qs[:wave]
            extra = f"; over-count: files beyond q{wave} set aside"
        need = (len(qs) + 1) // 2
        got = sum(1 for p in qs if is_attack(p))
        if got < need and not final:
            return (
                f"RETRY: Correction — the previous plan step composed {len(qs)} queries but marked only {got} "
                f"with a first line 'kind: attempt'; at least {need} (half, rounded up) must be attempt queries "
                f"aimed at this run's own flagged open questions, each beginning with the line 'kind: attempt' "
                f"and naming the open question it attempts. Rewrite the query files DIR/round{r}_q1.md … "
                f"(overwrite them; if you now compose fewer, delete the surplus files with rm) so that the wave "
                f"satisfies this." + STILL_THERE.format(r=r)
            )
        n_new = append(d, r)
        note = f", kind=attempt {got}/{len(qs)}" + (
            " accepted below quota after retries" if got < need else ""
        )
        return (
            f"WAVE {len(qs)} FLOOR {wave_floor(len(qs))} (ledger +{n_new}{note}{extra})"
        )
    if done.exists() and done.read_text(**ENC).strip():
        if r >= min_rounds:
            n_new = append(d, r)
            return f"CONCLUDE (round {r} >= floor {min_rounds}; ledger +{n_new})"
        bp = d / f"round{r}_ledger_block.md"
        pending = numbered_lines(d, r, bp.read_text(**ENC) if bp.exists() else "")
        text = ledger_text(d, before=r) + "".join(f"{ln}\n" for ln in pending)
        why = gate_reason(text, known_locators(d))
        if not why:
            n_new = append(d, r)
            return f"CONCLUDE (audited chain accepted before round {min_rounds}; ledger +{n_new})"
        if final:
            n_new = append(d, r)
            return f"CONCLUDE (accepted before round {min_rounds} after {attempt} plan attempts without a qualifying chain — {why}; ledger +{n_new})"
        done.replace(d / f"round{r}_DONE.rejected{attempt}.md")
        return (
            f"RETRY: Correction — your conclusion at round {r} was not accepted: {why}. "
            + GATE_RULE.format(m=min_rounds)
            + STILL_THERE.format(r=r)
        )
    what = f"neither DIR/round{r}_DONE.md nor any query file DIR/round{r}_q1.md …"
    if final:
        n_new = append(d, r)
        return f"TAIL: {what} after {attempt} attempts (ledger +{n_new})"
    return (
        f"RETRY: Correction — the previous attempt at this step wrote {what}. The required shape is: "
        f"DIR/round{r}_summary.md, then EITHER DIR/round{r}_DONE.md (only if the goal is fully established) "
        f"OR between 1 and {wave} query files. Write exactly that."
        + STILL_THERE.format(r=r)
    )


USAGE = (
    "usage: ledger.py check DIR R WAVE MIN_ROUNDS ATTEMPT | append DIR R | gate DIR [R] | "
    "answers DIR Q1 [Q2 ...] (bookkeeping for the math-proof siege skill; DIR is the run directory)"
)
# per command: its usage form, then how many arguments follow DIR (at least,
# at most) and how many of those must be whole numbers
_FORMS = {
    "check": ("check DIR R WAVE MIN_ROUNDS ATTEMPT", 4, 4, 4),
    "append": ("append DIR R", 1, 1, 1),
    "gate": ("gate DIR [R]", 0, 1, 1),
    "answers": ("answers DIR Q1 [Q2 ...]", 1, None, 0),
}


def _malformed(argv: list) -> str:
    """'' when the command line has the right shape, else an ERROR line."""
    cmd, rest = argv[1], argv[3:]
    if cmd not in _FORMS:
        return f"ERROR: unknown command {cmd!r}. {USAGE}; nothing was touched"
    form, lo, hi, nints = _FORMS[cmd]
    if len(argv) < 3 or len(rest) < lo or (hi is not None and len(rest) > hi):
        return f"ERROR: usage: ledger.py {form} (DIR first, as an absolute path); nothing was touched"
    d = Path(argv[2])
    if not d.is_dir():
        return f"ERROR: '{d}' is not an existing run directory; give the run directory's absolute path first (ledger.py {form}); nothing was touched"
    if not all(a.isascii() and a.isdigit() for a in rest[:nints]):
        return f"ERROR: usage: ledger.py {form}; the arguments after DIR must be whole numbers (got {' '.join(rest[:nints])}); nothing was touched"
    return ""


def main(argv: list) -> str:
    if len(argv) < 2 or argv[1] in ("-h", "--help"):
        return USAGE
    try:
        bad = _malformed(argv)
        if bad:
            return bad
        cmd = argv[1]
        d = Path(argv[2])
        if cmd == "append":
            return f"APPENDED {append(d, int(argv[3]))}"
        if cmd == "gate":  # on ledger.md as it stands, plus round R's pending block if R given
            text = ledger_text(d)
            if len(argv) > 3:
                r = int(argv[3])
                bp = d / f"round{r}_ledger_block.md"
                text = ledger_text(d, before=r) + "".join(
                    f"{ln}\n"
                    for ln in numbered_lines(
                        d, r, bp.read_text(**ENC) if bp.exists() else ""
                    )
                )
            why = gate_reason(text, known_locators(d))
            return "CONCLUDE" if not why else f"REJECT: {why}"
        if cmd == "answers":
            return answers(d, argv[3:])
        if cmd == "check":
            r, wave, min_rounds, attempt = (int(x) for x in argv[3:7])
            # the orchestrator's attempt count is advisory: every RETRY this
            # script has already issued for round r is logged, so a confused
            # caller passing attempt=1 forever still reaches the terminal
            # verdicts after MAX_ATTEMPTS plan steps
            logp = d / "judge" / f"plan_r{r}_retries.log"
            issued = len(logp.read_text(**ENC).splitlines()) if logp.exists() else 0
            attempt = max(attempt, issued + 1)
            verdict = check(d, r, wave, min_rounds, attempt)
            if verdict.startswith("RETRY"):
                logp.parent.mkdir(parents=True, exist_ok=True)
                with logp.open("a", encoding="utf-8") as f:
                    f.write(f"attempt {attempt}: {verdict[:120]}\n")
            # corrections are pasted into a brief whose paths are absolute
            return verdict.replace("DIR/", str(d).rstrip("/") + "/")
        return USAGE
    except Exception as e:  # fail closed, in words the orchestrator can relay
        if len(argv) > 1 and argv[1] == "answers":
            return f"ERROR: the bookkeeping script could not classify the answer files ({type(e).__name__}: {str(e)[:200]}); check DIR and the query stems and run the command again"
        attempt = 0
        try:
            attempt = int(argv[6]) if len(argv) > 6 and argv[1] == "check" else 0
        except ValueError:
            pass
        err = f"the bookkeeping script could not process this round's files ({type(e).__name__}: {str(e)[:200]})"
        if attempt >= MAX_ATTEMPTS:
            return f"TAIL: {err}, still failing after {attempt} attempts"
        return f"RETRY: Correction — {err}; re-check the file names and formats the brief asks for and write them again."


if __name__ == "__main__":
    try:  # the verdict goes out as UTF-8 whatever the console's code page (Windows)
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
    print(main(sys.argv))
