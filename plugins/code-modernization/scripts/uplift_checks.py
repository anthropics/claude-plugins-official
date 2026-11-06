#!/usr/bin/env python3
"""Two checks that only an uplift needs, for the proof pack (proof_pack.py imports this; it also runs on its own).

    python3 uplift_checks.py <legacy folder> <working copy> [DELTA_CATALOG.md]

An uplift keeps the code and the tests and changes the version underneath. A green test run then proves less than it seems to in two ways:

  Tests changed during the uplift. The test files of the untouched legacy tree are compared with those of the working copy by walking
  files only (no process is run, no link followed, build output skipped). A test file is a test file by the rules trace_rules.py uses.
  Removed, added and changed files are listed with a line-diff count. A removed test file, more than 25% of the legacy test files
  changed, or a legacy tree with no test files to compare against, is a gap: passing edited or deleted tests proves less, so a person reviews the list. Weakened assertions cannot be detected,
  only that files changed.

  Deltas covered. DELTA_CATALOG.md lists the version changes that hit this code. For every delta whose category says Behavioral-silent
  (the kind nothing reports when it changes behavior) the file of each listed site must be named, as a whole word, by some test file of
  the working copy. A name is not proof that the test exercises the changed behavior; a silent delta no test even names is untested.
  Other categories are listed, not judged.

Everything read is untrusted text: files are only read, links are not followed, sizes and counts are capped, and no pattern here can be made
slow by a hostile line. Exit 0 when neither check finds a gap, 1 when one does, 2 for input that cannot be used.
"""
import argparse
import difflib
import hashlib
import json
import os
import re
import stat
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
sys.path.insert(0, HERE)
import baseline_diff  # noqa: E402
import trace_rules  # noqa: E402

LIST_CAP, FILE_CAP, HASH_CAP, MAX_FILES, TEXT_CAP = 40, 2 << 20, 64 << 20, 60000, 400 << 20
DIFF_LINES, DIFF_BUDGET, SHARE_LIMIT = 4000, 300000000, 0.25
DELTA_CAP, CATALOG_CAP, LINE_CAP = 2000, 8 << 20, 4000
SILENT = re.compile(r"behaviou?ral[\s_-]*silent|silent[\s_-]*behaviou?ral", re.I)
CONFIG_EXT = {"xml", "yml", "yaml", "json", "properties", "gradle", "toml", "ini", "cfg"}      # build and configuration files: a test cannot name them
CODE_EXT = {"java", "kt", "kts", "scala", "groovy", "cs", "vb", "fs", "py", "js", "jsx", "ts", "tsx", "mjs", "cjs", "go", "rs", "rb", "php", "c", "h", "cc", "cpp", "hpp", "swift",
            "m", "sql", "cbl", "cob", "cpy", "jcl", "pl", "pm", "sh", "ps1", "xml", "yml", "yaml", "json", "properties", "gradle", "toml", "ini", "cfg"}
# path/Stem.ext:line, or path/Stem.ext for a known extension; every quantifier is bounded, so a hostile line cannot make it slow
SITE = re.compile(r"((?:[\w.$@+-]{1,80}/){0,12})([A-Za-z_$][\w$-]{0,80})((?:\.[A-Za-z][A-Za-z0-9]{0,7}){1,3})(?::(\d{1,7}))?")
WORD = re.compile(r"[A-Za-z_$][\w$]{0,200}")
DASHED = re.compile(r"[A-Za-z0-9_$]{1,100}(?:-[A-Za-z0-9_$]{1,100}){1,8}")
clean = trace_rules.clean


# ---------------------------------------------------------------- walking test files
def walk_tests(root):
    """({relative path: absolute path}, cut short, links skipped) for every regular test file under `root`.
    A test file is one trace_rules.file_kind calls a test. Links, hidden folders and build output are never entered."""
    out, links = {}, 0
    if os.path.islink(root) or not os.path.isdir(root):
        return out, False, 0
    for base, dirs, names in os.walk(root, followlinks=False):
        keep = []
        for d in sorted(dirs):
            if d in trace_rules.SKIP_DIRS or d.startswith("."):
                continue
            if os.path.islink(os.path.join(base, d)):
                links += 1
                continue
            keep.append(d)
        dirs[:] = keep
        for n in sorted(names):
            full = os.path.join(base, n)
            if n.startswith("."):
                continue
            try:
                st = os.lstat(full)
            except OSError:
                continue
            if stat.S_ISLNK(st.st_mode):
                links += 1
                continue
            rel = os.path.relpath(full, root).replace(os.sep, "/")
            if stat.S_ISREG(st.st_mode) and trace_rules.file_kind(rel) == "test":
                out[rel] = full
                if len(out) >= MAX_FILES:
                    return out, True, links
    return out, False, links


def read_head(path, cap=FILE_CAP):
    """Up to cap+1 bytes of a file, or None."""
    try:
        with open(path, "rb") as fh:
            return fh.read(cap + 1)
    except OSError:
        return None


def digest(path):
    """sha256 of a file's bytes (read in blocks, at most HASH_CAP), or None."""
    h, n = hashlib.sha256(), 0
    try:
        with open(path, "rb") as fh:
            while n < HASH_CAP:
                block = fh.read(1 << 20)
                if not block:
                    break
                h.update(block)
                n += len(block)
    except OSError:
        return None
    return h.hexdigest()


def count_lines(path):
    """Number of lines of a text file (0 for a binary or unreadable one)."""
    raw = read_head(path)
    return len(as_lines(raw)) if raw is not None and b"\x00" not in raw[:8192] else 0


def as_lines(raw):
    return raw.decode("utf-8", "replace").replace("\r\n", "\n").replace("\r", "\n").split("\n")


def line_diff(a, b, budget):
    """(lines added, lines removed) turning list a into list b. difflib for files of ordinary size while the budget lasts, else a count of
    lines that appear more often on one side (order is ignored, which is the price of being fast). -> (added, removed, exact, budget left)."""
    if len(a) <= DIFF_LINES and len(b) <= DIFF_LINES and len(a) * len(b) <= budget:
        added = removed = 0
        for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
            if tag in ("replace", "delete"):
                removed += i2 - i1
            if tag in ("replace", "insert"):
                added += j2 - j1
        return added, removed, True, budget - len(a) * len(b)
    ca, cb = {}, {}
    for line in a:
        ca[line] = ca.get(line, 0) + 1
    for line in b:
        cb[line] = cb.get(line, 0) + 1
    return (sum(max(0, n - ca.get(k, 0)) for k, n in cb.items()), sum(max(0, n - cb.get(k, 0)) for k, n in ca.items()), False, budget)


def compare_files(old, new, budget):
    """None when the two files hold the same content (line endings aside), else ({"added", "removed", "note"}, budget left)."""
    ra, rb = read_head(old), read_head(new)
    if ra is None or rb is None:
        return {"added": 0, "removed": 0, "note": "could not be read"}, budget
    if len(ra) > FILE_CAP or len(rb) > FILE_CAP:
        da, db = digest(old), digest(new)
        return (None, budget) if da is not None and da == db else ({"added": 0, "removed": 0, "note": "large file, lines not counted"}, budget)
    if b"\x00" in ra[:8192] or b"\x00" in rb[:8192]:
        return (None, budget) if ra == rb else ({"added": 0, "removed": 0, "note": "binary file"}, budget)
    la, lb = as_lines(ra), as_lines(rb)
    if la == lb:
        return None, budget
    added, removed, exact, budget = line_diff(la, lb, budget)
    return {"added": added, "removed": removed, "note": "" if exact else "lines counted approximately"}, budget


# ---------------------------------------------------------------- tests changed during the uplift
def tests_changed(legacy_root, work_root):
    """Compare the test files of the untouched legacy tree with those of the working copy.
    -> {"checked", "why", "legacyTests", "workTests", "counts": {added, removed, changed}, "added", "removed", "changed" (lists cut to 40), "share", "gap", "cut"}."""
    out = {"checked": False, "why": "", "legacyTests": 0, "workTests": 0, "counts": {"added": 0, "removed": 0, "changed": 0}, "added": [], "removed": [], "changed": [],
           "share": 0.0, "gap": False, "cut": False}
    if not legacy_root or not os.path.isdir(legacy_root):
        out["why"] = "the legacy tree was not found, so its test files could not be compared with the working copy's"
        return out
    if not work_root or not os.path.isdir(work_root):
        out["why"] = "the working copy was not found"
        return out
    old, cut_a, _ = walk_tests(legacy_root)
    new, cut_b, _ = walk_tests(work_root)
    out.update({"checked": True, "legacyTests": len(old), "workTests": len(new), "cut": cut_a or cut_b})
    removed = sorted(set(old) - set(new))
    added = sorted(set(new) - set(old))
    changed, budget = [], DIFF_BUDGET
    for rel in sorted(set(old) & set(new)):
        got, budget = compare_files(old[rel], new[rel], budget)
        if got is not None:
            changed.append(dict(got, path=clean(rel, 300)))
    out["counts"] = {"added": len(added), "removed": len(removed), "changed": len(changed)}
    changed.sort(key=lambda c: (-(c["added"] + c["removed"]), c["path"]))
    out["removed"] = [{"path": clean(r, 300), "lines": count_lines(old[r])} for r in removed[:LIST_CAP]]
    out["added"] = [{"path": clean(r, 300), "lines": count_lines(new[r])} for r in added[:LIST_CAP]]
    out["changed"] = changed[:LIST_CAP]
    out["share"] = round(len(changed) / len(old), 4) if old else 0.0
    out["gap"] = bool(removed) or not old or len(changed) > SHARE_LIMIT * len(old)
    if not old:
        out["why"] = "the legacy tree has no test files, so nothing shows that the working copy's tests were not written during the uplift"
    return out


# ---------------------------------------------------------------- reading DELTA_CATALOG.md
def norm_id(text):
    return re.sub(r"[\s*`#.]+", "", text or "").lower()[:40]


def sites_in(text):
    """[{"path", "stem", "line"}] for every file mention in `text` that is a file:line, or a file with a known extension."""
    out = []
    for m in SITE.finditer(text[:LINE_CAP]):
        ext = m.group(3).lstrip(".").split(".")[-1].lower()
        stem = m.group(2)
        if len(stem) < 2 or (m.group(4) is None and ext not in CODE_EXT):
            continue
        site = {"path": clean((m.group(1) + stem + m.group(3)), 200), "stem": stem, "line": int(m.group(4)) if m.group(4) else 0, "ext": ext}
        if not any(o["path"] == site["path"] for o in out):
            out.append(site)
    return out[:20]


def add_delta(found, did, title, category, sites):
    key = norm_id(did)
    if not key or (len(found) >= DELTA_CAP and key not in found):
        return
    d = found.setdefault(key, {"id": clean(did.replace("*", "").strip(), 40), "title": "", "category": "", "sites": []})
    d["title"] = d["title"] or clean(title, 200)
    d["category"] = d["category"] or clean(category, 80)
    d["sites"] += [s for s in sites if not any(o["path"] == s["path"] for o in d["sites"])]
    d["sites"] = d["sites"][:20]


def parse_deltas(text):
    """Deltas from DELTA_CATALOG.md, tolerantly: pipe tables with a Category column (an id in the first or an ID/# column, sites in a
    Site column), and cards (`### 9. title` or `### D-01 title`, with a `Category ...:` line and a `cited:` or `Site:` line).
    Rows and cards of the same id are merged. -> [{"id", "title", "category", "sites": [{"path", "stem", "line"}]}]."""
    found = {}
    for _heading, header, rows in baseline_diff.md_tables(text[:CATALOG_CAP]):
        low = [h.lower() for h in header]
        cat = next((i for i, h in enumerate(low) if re.search(r"\bcat", h)), None)
        if cat is None:
            continue
        idc = next((i for i, h in enumerate(low) if re.fullmatch(r"(?:id|#|no\.?|delta|card|ref)", h.strip())), 0)
        titlec = next((i for i, h in enumerate(low) if re.search(r"delta|title|name|change|summary|\bold\b", h) and i != idc), None)
        sitec = [i for i, h in enumerate(low) if re.search(r"\bsites?\b|location|cited|file", h)]
        for row in rows[:5000]:
            if cat >= len(row) or idc >= len(row) or not row[idc].strip():
                continue
            cells = [row[i] for i in sitec if i < len(row) and not re.fullmatch(r"\s*\d+\s*", row[i])]
            sites = sites_in(" ".join(cells)) if sitec else sites_in(" ".join(c for i, c in enumerate(row) if i not in (cat, idc)))
            add_delta(found, row[idc], row[titlec] if titlec is not None and titlec < len(row) else "", row[cat], sites)
    lines, i = [ln[:LINE_CAP] for ln in text[:CATALOG_CAP].split("\n")], 0
    while i < len(lines):
        m = re.match(r"#{2,6}[ \t]+(?:\*\*)?(D-\d{1,4}|\d{1,4})(?:\*\*)?[.):\s][ \t]*(.*)$", lines[i])
        i += 1
        if not m:
            continue
        category, sites = "", []
        while i < len(lines) and not lines[i].startswith("#"):
            line = lines[i]
            c = re.search(r"categor[^:\n]{0,40}:\**[ \t]*(.{1,200})", line, re.I)
            if c and not category:
                category = re.split(r"[/;]", c.group(1))[0].strip(" *`")
            cited = re.search(r"\bcited\s*:", line, re.I) or re.match(r"^[ \t>*-]*\**(?:sites?|location|source)\b[^:\n]{0,30}:", line, re.I)
            if cited:                     # only the site the card cites, never files that its prose merely mentions
                sites += [s for s in sites_in(line[cited.end():]) if not any(o["path"] == s["path"] for o in sites)]
            i += 1
        if category or norm_id(m.group(1)) in found:        # a numbered heading with no Category line is not a delta card
            add_delta(found, m.group(1), m.group(2), category, sites)
    return list(found.values())


# ---------------------------------------------------------------- deltas covered by tests
def test_words(work_root):
    """(the set of words that appear in the working copy's test files, number of test files read). Files are read as text, up to 2 MB each."""
    words, total, files = set(), 0, 0
    tests, _cut, _links = walk_tests(work_root)
    for rel in sorted(tests):
        raw = read_head(tests[rel])
        if raw is None or b"\x00" in raw[:8192]:
            continue
        total += len(raw)
        if total > TEXT_CAP:
            break
        text = raw[:FILE_CAP].decode("utf-8", "replace")
        words.update(WORD.findall(text))
        words.update(DASHED.findall(text))
        files += 1
    return words, files


def delta_coverage(catalog_text, work_root):
    """Which Behavioral-silent deltas have their site's file named by a test in the working copy? A delta whose only sites are build or
    configuration files cannot be named by a test: it is listed for a person, not judged.
    -> {"parsed", "silent", "covered": [...], "uncovered": [...], "config": [...], "other": n, "testFiles", "gap", "why"}."""
    out = {"parsed": 0, "silent": 0, "covered": [], "uncovered": [], "config": [], "other": 0, "testFiles": 0, "gap": False, "why": ""}
    if catalog_text is None:
        out.update(gap=True, why="DELTA_CATALOG.md was not found, so it is not known which version changes hit this code")
        return out
    deltas = parse_deltas(catalog_text)
    out["parsed"] = len(deltas)
    if not deltas:
        out.update(gap=True, why="no delta could be read from DELTA_CATALOG.md (a table with a Category column, or cards with a Category line)")
        return out
    words, out["testFiles"] = test_words(work_root)
    for d in deltas:
        if not SILENT.search(d["category"]):
            out["other"] += 1
            continue
        out["silent"] += 1
        code = [s for s in d["sites"] if s["ext"] not in CONFIG_EXT]
        rec = {"id": d["id"], "title": d["title"], "sites": [s["path"] + (":%d" % s["line"] if s["line"] else "") for s in d["sites"][:5]]}
        if d["sites"] and not code:
            out["config"].append(rec)
            continue
        missing = [s["stem"] for s in code if s["stem"] not in words]
        if code and not missing:
            out["covered"].append(rec)
        else:
            rec["why"] = "no site is named in the catalog" if not code else "no test names " + ", ".join(clean(x, 60) for x in list(dict.fromkeys(missing))[:5])
            out["uncovered"].append(rec)
    out["gap"] = bool(out["uncovered"])
    return out


# ---------------------------------------------------------------- command line
def main(argv=None):
    ap = argparse.ArgumentParser(description="Uplift-only checks: test files changed since the legacy tree, and silent deltas no test names.")
    ap.add_argument("legacy", help="the untouched legacy folder (legacy/<system>)")
    ap.add_argument("work", help="the uplifted working copy (modernized/<system>-uplifted)")
    ap.add_argument("catalog", nargs="?", help="analysis/<system>/DELTA_CATALOG.md")
    ap.add_argument("--json", action="store_true", help="print the full result as JSON")
    args = ap.parse_args(argv)
    for path in (args.legacy, args.work):
        if not os.path.isdir(path):
            print("uplift_checks.py: %s is not a folder" % path, file=sys.stderr)
            return 2
    text = None
    if args.catalog:
        try:
            text = baseline_diff.read_capped(args.catalog, CATALOG_CAP).decode("utf-8", "replace")
        except baseline_diff.InputError as err:
            print("uplift_checks.py: %s" % err, file=sys.stderr)
            return 2
    changed = tests_changed(os.path.realpath(args.legacy), os.path.realpath(args.work))
    deltas = delta_coverage(text, os.path.realpath(args.work)) if args.catalog else None
    if args.json:
        print(json.dumps({"testsChanged": changed, "deltas": deltas}, indent=1, ensure_ascii=True))
    else:
        c = changed["counts"]
        print("test files: %d in the legacy tree, %d in the working copy; %d removed, %d added, %d changed (%.0f%% of the legacy test files)" % (
            changed["legacyTests"], changed["workTests"], c["removed"], c["added"], c["changed"], 100 * changed["share"]))
        for key in ("removed", "changed", "added"):
            for e in changed[key][:10]:
                print("  %s: %s%s" % (key, e["path"], " (+%d -%d lines)" % (e["added"], e["removed"]) if key == "changed" else ""))
        print("tests kept: " + ("GAP" if changed["gap"] else "ok") + ("" if not changed["why"] else " (" + changed["why"] + ")"))
        if deltas is not None:
            print("deltas: %d parsed, %d behavioral-silent, %d covered, %d not named by any test, %d at a build or configuration file" % (
                deltas["parsed"], deltas["silent"], len(deltas["covered"]), len(deltas["uncovered"]), len(deltas["config"])))
            for d in deltas["uncovered"][:10]:
                print("  uncovered: %s %s (%s)" % (d["id"], d["title"], d.get("why", "")))
            print("deltas covered: " + ("GAP" if deltas["gap"] else "ok") + ("" if not deltas["why"] else " (" + deltas["why"] + ")"))
    return 1 if changed["gap"] or (deltas is not None and deltas["gap"]) else 0


if __name__ == "__main__":
    sys.exit(main())
