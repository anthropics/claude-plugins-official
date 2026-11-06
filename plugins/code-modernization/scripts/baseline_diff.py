#!/usr/bin/env python3
"""Compare a fresh test run with the baseline recorded before a same-stack uplift.

    python3 baseline_diff.py <BASELINE.md> --junit DIR_OR_FILE [--junit ...] [--json] [--max-list N]

BASELINE.md (analysis/<system>/BASELINE.md) records how the tests behaved on the OLD version. This
script reads it and the fresh results, and reports what changed. Nothing is judged by a model.

Baseline, any of these (the most detailed one found is used):
  a per-test table      | Test | Result |      one row per test, PASS / FAIL / ERROR / SKIP
  a per-module table    | Module | Pass | Fail | Error | Skip |     (the first column may be a module,
                        project or test class; column names are matched, their order does not matter)
  a totals table        | Executed | 946 |, | Passed | 945 |, | Failed | 1 | ...
  a line                target-only: <why the old version could not run here>   (nothing to compare)

Measured or typed: a baseline typed by hand proves nothing about the old version. The old version's own evidence is looked for in
analysis/<system>/baseline/ and at the paths on a "Recorded:" or "Machine-readable:" line of BASELINE.md inside analysis/<system>/ (JUnit or .trx XML, a per-test JSON map of test ids to
outcomes, or a raw runner log with a known summary line; a file that only holds counts is ignored, and sources that disagree are a conflict). When it exists, it is what the fresh results are compared with,
and the typed table must agree with it; when it does not, the report says "typed table only".

Fresh results: JUnit-style XML (Maven surefire, Gradle, pytest --junitxml, Ant, jest-junit ...) or
Visual Studio .trx files. Give a file or a folder; a folder is searched for result files, links are
never followed, and a file that declares a DTD or entity is refused. A test id is
"<classname>#<name>"; a repeated id in one file gets a "~N" suffix in document order (the first
stays plain); the module's own absolute path in a parameterized name is replaced by <MODULE>.

Reported: regressions (passed before, fails now), new failures (a test the baseline never listed),
tests that still fail as they did, tests that now pass, tests that were skipped and now run, tests
that no longer run, missing modules, skipped growth and a drop in executed tests. When test names
drifted inside a class but its counts did not get worse, that is counted as renamed, not missing.

Exit 0 when nothing regressed and something ran; 1 on any regression or new failure, or when no test
executed; 2 for input that cannot be used. Standard library only.
"""
import argparse
import json
import os
import re
import stat
import sys
from xml.parsers import expat

BAD = ("FAIL", "ERROR")
MAX_FILE, MAX_FILES, MAX_CASES, MAX_DEPTH, KEEP = 200 << 20, 20000, 2000000, 60, 200
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv"}
STATUS = {"pass": "PASS", "passed": "PASS", "ok": "PASS", "success": "PASS", "green": "PASS", "fail": "FAIL", "failed": "FAIL", "failure": "FAIL",
          "red": "FAIL", "error": "ERROR", "errors": "ERROR", "errored": "ERROR", "skip": "SKIP", "skipped": "SKIP", "ignored": "SKIP",
          "pending": "SKIP", "disabled": "SKIP"}
COLUMNS = (("pass", r"pass|passed|passing|ok|successes?"), ("fail", r"fail|failed|failing|failures?"), ("error", r"errors?|errored"),
           ("skip", r"skip|skipped|ignored|pending|disabled"))
TOTALS = {"executed": "executed", "test cases": "cases", "passed": "pass", "pass": "pass", "failed": "fail", "failures": "fail", "errors": "error",
          "skipped": "skip", "ignored": "skip"}


def clean(value, limit=200):
    text = " ".join(re.sub(r"[\x00-\x1f\x7f-\x9f\u2028\u2029]", " ", str(value if value is not None else "")).split())
    return text if len(text) <= limit else text[:limit - 1] + "…"


class InputError(Exception):
    pass


def read_capped(path, cap):
    """Bytes of a regular file inside the size cap; raises InputError with a plain reason for a link, a huge file or an unreadable one."""
    try:
        st = os.lstat(path)
        if not stat.S_ISREG(st.st_mode):
            raise InputError("%s is a link or not a regular file" % clean(os.path.basename(path), 80))
        if st.st_size > cap:
            raise InputError("%s is larger than %d MB" % (clean(os.path.basename(path), 80), cap >> 20))
        with open(path, "rb") as fh:
            return fh.read()
    except OSError as err:
        raise InputError("cannot read %s (%s)" % (clean(os.path.basename(path), 80), err.__class__.__name__))


# ---------------------------------------------------------------- the baseline
def cell(text):
    text = text.replace("\\|", "|").strip()
    if len(text) > 4 and text.startswith("**") and text.endswith("**"):
        text = text[2:-2].strip()
    if len(text) >= 2 and text.startswith("`") and text.endswith("`"):
        text = text[1:-1]
    return text


def split_row(line):
    s = line.strip()
    s = s[1:] if s.startswith("|") else s
    s = s[:-1] if s.endswith("|") and not s.endswith("\\|") else s
    return [cell(c) for c in re.split(r"(?<!\\)\|", s[:20000])]


def join_cut_rows(lines):
    """A test name that contains a newline cuts its table row in two; put the row back together (at most 3 extra lines)."""
    out, i = [], 0
    while i < len(lines):
        line, extra = lines[i], 0
        while (line.lstrip().startswith("|") and not line.rstrip().endswith("|") and extra < 3 and i + 1 < len(lines)
               and lines[i + 1].strip() and not lines[i + 1].lstrip().startswith(("|", "#"))):
            i += 1
            extra += 1
            line += "\n" + lines[i]
        out.append(line)
        i += 1
    return out


def md_tables(text):
    """(nearest heading, header cells, [row cells]) for every pipe table."""
    lines, heading = join_cut_rows(text.split("\n")), ""
    i = 0
    while i < len(lines):
        h = re.match(r"#{1,6}[ \t]+(.*)", lines[i][:2000])
        heading = h.group(1) if h else heading
        if "|" in lines[i] and i + 1 < len(lines) and re.fullmatch(r"\s*\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)*\|?\s*", lines[i + 1][:5000]):
            rows, j = [], i + 2
            while j < len(lines) and "|" in lines[j] and lines[j].strip():
                rows.append(split_row(lines[j]))
                j += 1
            yield heading, split_row(lines[i]), rows
            i = j
        else:
            i += 1


def to_int(text):
    t = text.strip().replace(",", "")
    if t in ("", "-", "\u2013", "\u2014"):
        return 0
    return int(t) if re.fullmatch(r"\d{1,12}", t) else None


def parse_baseline(text):
    """-> {targetOnly, why, modules {name: counts}, tests {id: status}, totals {name: n}}."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    m = re.search(r"(?im)^\W*target-only:[ \t]*(.*)$", text)
    out = {"targetOnly": bool(m), "why": clean(m.group(1), 300) if m else "", "modules": {}, "tests": {}, "totals": {}, "flaky": [], "approved": {}}
    for heading, header, rows in md_tables(text):
        low = [h.lower() for h in header]
        if re.search(r"(?i)flak", heading):                    # tests the baseline itself says flip on the same version
            out["flaky"] += [clean(r[0], 400) for r in rows if r and r[0]]
            continue
        if re.search(r"(?i)approved", heading):                # differences a person accepted: | Test | Reason |
            for r in rows:
                if r and r[0]:
                    out["approved"].setdefault(clean(r[0], 400), clean(r[1] if len(r) > 1 else "", 300))
            continue
        cols = {key: next((i for i, h in enumerate(low) if re.fullmatch(rx, h)), None) for key, rx in COLUMNS}
        result = next((i for i, h in enumerate(low) if re.fullmatch(r"result|status|outcome|verdict", h)), None)
        if cols["pass"] is not None and any(cols[k] is not None for k in ("fail", "error", "skip")):
            for row in rows:
                name, nums = row[0] if row else "", {k: to_int(row[i]) if i is not None and i < len(row) else 0 for k, i in cols.items()}
                if name and not re.fullmatch(r"(?i)totals?|all|sum", name) and None not in nums.values():
                    out["modules"][name[:300]] = nums
        elif result is not None:
            name_col = next((i for i, h in enumerate(low) if re.fullmatch(r"tests?|test name|test id|id|name|cases?|test case", h)), 0)
            for row in rows:
                status = STATUS.get(row[result].lower()) if result < len(row) else None
                if status and name_col < len(row) and row[name_col] and result != name_col:
                    out["tests"][row[name_col][:400]] = status
        elif len(header) >= 2:
            for row in rows:
                label, n = (row[0].lower() if row else ""), to_int(row[1]) if len(row) > 1 else None
                if label in TOTALS and n is not None:
                    out["totals"][TOTALS[label]] = n
    if not (out["modules"] or out["tests"] or out["totals"]):
        counts = {}
        for word, key in (("pass(?:ed|ing)", "pass"), ("fail(?:ed|ing|ures?)", "fail"), ("skipped", "skip"), ("errors?", "error")):
            hit = re.search(r"(?i)(\d{1,9})\s+(?:tests?\s+|cases?\s+)?" + word, text)
            if hit:
                counts[key] = int(hit.group(1))
        out["totals"] = counts
    return out


def tally(statuses):
    c = {"pass": 0, "fail": 0, "error": 0, "skip": 0}
    for s in statuses:
        c[s.lower()] += 1
    c["executed"] = c["pass"] + c["fail"] + c["error"]
    return c


def baseline_counts(base):
    """(counts, where they came from)."""
    if base["tests"]:
        return tally(base["tests"].values()), "per-test table"
    if base["modules"]:
        c = {k: sum(v[k] for v in base["modules"].values()) for k in ("pass", "fail", "error", "skip")}
        c["executed"] = c["pass"] + c["fail"] + c["error"]
        return c, "per-module table"
    t = base["totals"]
    if t:
        c = {k: t.get(k, 0) for k in ("pass", "fail", "error", "skip")}
        c["executed"] = t["executed"] if "executed" in t else c["pass"] + c["fail"] + c["error"]
        return c, "totals"
    return None, "nothing"


# ---------------------------------------------------------------- the fresh results
def refuse(*_):
    raise ValueError("it declares a DTD or an entity, which test results never do")


def parse_results(path):
    """[(classname, name, status, skip message given, suite name)] from one JUnit or TRX file. Raises ValueError."""
    cases, suites, cur, depth = [], [], [], [0]
    trx = {"Passed": "PASS", "Failed": "FAIL", "Error": "ERROR", "Timeout": "ERROR", "Aborted": "ERROR"}

    def start(tag, attrs):
        depth[0] += 1
        if depth[0] > MAX_DEPTH:
            raise ValueError("the XML is nested more than %d levels deep" % MAX_DEPTH)
        if tag == "testsuite":
            suites.append(attrs.get("name", "")[:300])
        elif tag == "testcase":
            if len(cases) >= MAX_CASES:
                raise ValueError("more than %d test cases" % MAX_CASES)
            flag = (attrs.get("status") or attrs.get("result") or "").lower()
            cur[:] = [(attrs.get("classname") or (suites[-1] if suites else ""))[:300], attrs.get("name", "")[:400],
                      "SKIP" if flag in ("skipped", "ignored", "notrun", "notexecuted", "disabled") else "PASS", False]
        elif cur and tag in ("failure", "error", "skipped"):
            if tag == "skipped":
                cur[3] = bool(attrs.get("message", "").strip())
            new = {"failure": "FAIL", "error": "ERROR", "skipped": "SKIP"}[tag]
            if cur[2] == "PASS" or (cur[2] == "SKIP" and new != "SKIP"):
                cur[2] = new
        elif tag == "UnitTestResult":
            name = attrs.get("testName", "")[:400]
            head, sep, tail = name.partition("(")
            klass, dot, method = head.rpartition(".")
            outcome = attrs.get("outcome", "")
            cases.append((klass[:300] if dot else "", (method + sep + tail) if dot else name, trx.get(outcome, "SKIP"), False, ""))

    def end(tag):
        depth[0] -= 1
        if tag == "testcase" and cur:
            cases.append((cur[0], cur[1], cur[2], cur[3], suites[-1] if suites else ""))
            cur.clear()
        elif tag == "testsuite" and suites:
            suites.pop()

    parser = expat.ParserCreate()
    parser.StartDoctypeDeclHandler = refuse
    parser.EntityDeclHandler = refuse
    parser.StartElementHandler = start
    parser.EndElementHandler = end
    try:
        with open(path, "rb") as fh:
            parser.ParseFile(fh)
    except expat.ExpatError as err:
        raise ValueError("the XML is not well formed (%s)" % expat.ErrorString(err.code))
    return cases


def result_files(paths):
    """([files], [problems]) from files and folders. Links are never followed."""
    found, problems = [], []
    for p in paths:
        if os.path.isfile(p) and not os.path.islink(p):
            found.append(p)
        elif os.path.isdir(p) and not os.path.islink(p):
            for base, dirs, names in os.walk(p):
                dirs[:] = [d for d in sorted(dirs) if d not in SKIP_DIRS and not os.path.islink(os.path.join(base, d))]
                for n in sorted(names):
                    full = os.path.join(base, n)
                    if os.path.islink(full) or not n.lower().endswith((".xml", ".trx")):
                        continue
                    try:
                        with open(full, "rb") as fh:
                            head = fh.read(4096)
                    except OSError:
                        continue
                    if b"<testsuite" in head or b"<TestRun" in head:
                        found.append(full)
                if len(found) > MAX_FILES:
                    problems.append("More than %d result files were found; the rest were not read." % MAX_FILES)
                    return found[:MAX_FILES], problems
        else:
            problems.append("%s is not a file or folder that can be read." % clean(p, 120))
    return found, problems


def module_label(path):
    """The module folder a Maven or Gradle report belongs to (its parent of target/ or build/), or ''."""
    parts = os.path.abspath(path).split(os.sep)
    for i in range(len(parts) - 2, 1, -1):
        if parts[i] in ("target", "build") and parts[i + 1] in ("surefire-reports", "failsafe-reports", "test-results"):
            return os.sep.join(parts[:i]) or os.sep
    return ""


def read_results(paths):
    """-> {tests {id: status}, skipReasons {id: bool}, classes, modules, suites, files, unreadable [str], problems [str], oldest, newest}."""
    files, problems = result_files(paths)
    out = {"tests": {}, "skipReasons": {}, "classes": {}, "modules": {}, "suites": {}, "files": 0, "unreadable": [], "problems": problems, "oldest": None, "newest": None}
    for path in files:
        label = clean(os.path.basename(path), 100)
        try:
            if os.path.getsize(path) > MAX_FILE:
                raise ValueError("the file is larger than %d MB" % (MAX_FILE >> 20))
            cases = parse_results(path)
        except (OSError, ValueError) as err:
            out["unreadable"].append("%s: %s" % (label, clean(err, 120)))
            continue
        root = module_label(path)
        roots = sorted({root, os.path.realpath(root), root[len("/private"):] if root.startswith("/private/") else root} - {os.sep}, key=len, reverse=True) if root else []
        seen, mtime = {}, os.path.getmtime(path)
        out["files"] += 1
        out["oldest"] = mtime if out["oldest"] is None else min(out["oldest"], mtime)
        out["newest"] = mtime if out["newest"] is None else max(out["newest"], mtime)
        for klass, name, status, has_reason, suite in cases:
            for r in roots:
                name = name.replace(r, "<MODULE>")
            name = re.sub(r"(test)\d+(\.tmp)", r"\1<N>\2", name)
            base = "%s#%s" % (klass, name) if klass else name
            n = seen.get(base, 0)
            seen[base] = n + 1
            tid = base if n == 0 else "%s~%d" % (base, n)
            out["tests"][tid] = status
            out["skipReasons"][tid] = has_reason
            for key, store in ((klass, out["classes"]), (root and os.path.basename(root), out["modules"]), (suite, out["suites"])):
                if key:
                    store.setdefault(key, []).append(status)
    for store in ("classes", "modules", "suites"):
        out[store] = {k: tally(v) for k, v in out[store].items()}
    return out


# ---------------------------------------------------------------- raw runner logs (a saved run's own summary lines)
LOG_CAP, LOG_LINE = 16 << 20, 2000
NUM_WORD = re.compile(r"(\d+)\s+([A-Za-z]+)")


def words(text):
    """{'passed': 10, 'failed': 2} from '2 failed, 10 passed' style text."""
    out = {}
    for n, w in NUM_WORD.findall(text[:LOG_LINE]):
        out[w.lower()] = out.get(w.lower(), 0) + int(n)
    return out


def _maven(m):
    run, f, e, sk = (int(g) for g in m.groups())
    return max(0, run - f - e - sk), f + e, sk


def _pytest(m):
    w = words(m.group(1))
    return w.get("passed", 0) + w.get("xpassed", 0) + w.get("xfailed", 0), w.get("failed", 0) + w.get("error", 0) + w.get("errors", 0), w.get("skipped", 0)


def _jest(m):
    w = words(m.group(1))
    return w.get("passed", 0), w.get("failed", 0), w.get("skipped", 0)


def _php(m):
    w = {k.lower(): int(v) for k, v in re.findall(r"([A-Za-z]+):\s*(\d+)", m.group(1)[:LOG_LINE])}
    failed, skipped = w.get("failures", 0) + w.get("errors", 0), w.get("skipped", 0) + w.get("incomplete", 0)
    return max(0, w.get("tests", 0) - failed - skipped), failed, skipped


def _ctest(m):
    failed, total = int(m.group(1)), int(m.group(2))
    return max(0, total - failed), failed, 0


def _gradle(m):
    total, failed, skipped = int(m.group(1)), int(m.group(2) or 0), int(m.group(3) or 0)
    return max(0, total - failed - skipped), failed, skipped


# runner, a line pattern, and how to read (passed, failed, skipped) from a match. Every pattern is anchored and bounded.
LOG_LINES = (
    ("maven", re.compile(r"^(?:\[\w+\]\s*)?Tests run: (\d+), Failures: (\d+), Errors: (\d+), Skipped: (\d+)\s*$"), _maven),
    ("gradle", re.compile(r"^(\d+) tests? completed(?:, (\d+) failed)?(?:, (\d+) skipped)?\s*$"), _gradle),
    ("cargo", re.compile(r"^test result: (?:ok|FAILED)\. (\d+) passed; (\d+) failed; (\d+) ignored;"), lambda m: (int(m.group(1)), int(m.group(2)), int(m.group(3)))),
    ("pytest", re.compile(r"^(?:=+ )?((?:\d+ [a-z]+(?:, )?)+) in [\d.]+s(?: \([\d:]+\))?(?: =+)?\s*$"), _pytest),
    ("pytest", re.compile(r"^(?:=+ )?no tests ran in [\d.]+s"), lambda m: (0, 0, 0)),
    ("go test", re.compile(r"^\s*--- (PASS|FAIL|SKIP): \S"), lambda m: {"PASS": (1, 0, 0), "FAIL": (0, 1, 0), "SKIP": (0, 0, 1)}[m.group(1)]),
    ("go test -json", re.compile(r'^\{.*"Action":"(pass|fail|skip)".*"Test":"[^"]+"'), lambda m: {"pass": (1, 0, 0), "fail": (0, 1, 0), "skip": (0, 0, 1)}[m.group(1)]),
    ("dotnet test", re.compile(r"^(?:Passed|Failed)!\s+-\s+Failed:\s+(\d+),\s+Passed:\s+(\d+),\s+Skipped:\s+(\d+)"), lambda m: (int(m.group(2)), int(m.group(1)), int(m.group(3)))),
    ("jest", re.compile(r"^\s*Tests:\s+(.*\b\d+ total)\s*$"), _jest),
    ("vitest", re.compile(r"^\s*Tests\s{2,}(.*)\(\d+\)\s*$"), _jest),
    ("ctest", re.compile(r"^\d+% tests passed, (\d+) tests? failed out of (\d+)"), _ctest),
    ("phpunit", re.compile(r"^OK \((\d+) tests?, \d+ assertions?\)"), lambda m: (int(m.group(1)), 0, 0)),
    ("phpunit", re.compile(r"^(Tests: \d+, Assertions: \d+.*?)\.?\s*$"), _php),
)
UNITTEST_RAN = re.compile(r"^Ran (\d+) tests? in [\d.]+s\s*$")
UNITTEST_END = re.compile(r"^(?:OK|FAILED)(?: \(([^)]*)\))?\s*$")


def parse_runner_log(text):
    """(executed, failed, skipped, runners) from the runner's own summary lines, summed over the log; None when no line is recognised.
    Recognised: Maven/Gradle, cargo, pytest, unittest, go test (-v or -json), dotnet test, jest, vitest, ctest, phpunit."""
    passed = failed = skipped = 0
    seen, ran = [], None
    for line in text.split("\n")[:3000000]:
        line = line.rstrip("\r")[:LOG_LINE]
        if ran is not None and line.strip():
            m = UNITTEST_END.match(line)
            if m:
                w = {k: int(v) for k, v in re.findall(r"(\w+)=(\d+)", (m.group(1) or "")[:LOG_LINE])}
                f, sk = w.get("failures", 0) + w.get("errors", 0), w.get("skipped", 0)
                passed, failed, skipped = passed + max(0, ran - f - sk), failed + f, skipped + sk
                seen.append("unittest")
            ran = None
        m = UNITTEST_RAN.match(line)
        if m:
            ran = int(m.group(1))
            continue
        for name, rx, read in LOG_LINES:
            m = rx.match(line)
            if m:
                p, f, sk = read(m)
                passed, failed, skipped = passed + p, failed + f, skipped + sk
                seen.append(name)
                break
    return (passed + failed, failed, skipped, sorted(set(seen))) if seen else None


def read_logs(paths):
    """Saved runner logs -> {"files", "executed", "failed", "skipped", "runners", "oldest", "newest", "unrecognised"}. A log without a summary line of a known runner is no evidence."""
    out = {"files": 0, "executed": 0, "failed": 0, "skipped": 0, "runners": [], "oldest": None, "newest": None, "unrecognised": []}
    for path in paths:
        try:
            st = os.lstat(path)
            if not stat.S_ISREG(st.st_mode) or st.st_size > LOG_CAP:
                out["unrecognised"].append("%s (a link, not a file, or larger than %d MB)" % (clean(os.path.basename(path), 80), LOG_CAP >> 20))
                continue
            with open(path, "rb") as fh:
                got = parse_runner_log(fh.read(LOG_CAP).decode("utf-8", "replace"))
        except OSError:
            out["unrecognised"].append("%s (could not be read)" % clean(os.path.basename(path), 80))
            continue
        if got is None:
            out["unrecognised"].append("%s (no summary line of a runner this script knows)" % clean(os.path.basename(path), 80))
            continue
        out["files"] += 1
        out["executed"], out["failed"], out["skipped"] = out["executed"] + got[0], out["failed"] + got[1], out["skipped"] + got[2]
        out["runners"] = sorted(set(out["runners"]) | set(got[3]))
        out["oldest"] = st.st_mtime if out["oldest"] is None else min(out["oldest"], st.st_mtime)
        out["newest"] = st.st_mtime if out["newest"] is None else max(out["newest"], st.st_mtime)
    return out


# ---------------------------------------------------------------- measured baselines: result files, raw logs, machine-readable results
EVIDENCE_EXT = (".xml", ".trx", ".json", ".txt", ".log", ".out")
PATH_TOKEN = re.compile(r"[A-Za-z0-9_.@+~-]+(?:/[A-Za-z0-9_.@+~-]+)*/?")


RECORDED = re.compile(r"^[ \t>*-]*\**[ \t]*(?:recorded|machine-readable)\b[^:\n]{0,40}:", re.I)


def evidence_paths(baseline_path, text):
    """Where the old version's measured results are kept: the folder analysis/<system>/baseline/, and the paths on a line of BASELINE.md
    that starts with "Recorded:" or "Machine-readable:" (a folder, or a file ending in .xml .trx .json .txt .log .out). Paths mentioned
    anywhere else in the file are prose, not evidence. A path with a `..`, a link anywhere below the analysis folder, or a place outside
    analysis/<system>/ is never used. -> the existing paths, at most 50."""
    adir = os.path.dirname(os.path.abspath(baseline_path))
    system, real_adir, found, seen = os.path.basename(adir), os.path.realpath(adir), [], set()

    def add(comps):
        cur = adir
        for c in comps:
            cur = os.path.join(cur, c)
            if os.path.islink(cur):
                return
        if not os.path.lexists(cur):
            return
        real = os.path.realpath(cur)
        try:
            ok = os.path.commonpath([real_adir, real]) == real_adir
        except ValueError:
            ok = False
        if ok and real not in seen and (os.path.isdir(cur) or os.path.isfile(cur)):
            seen.add(real)
            found.append(cur)

    add(["baseline"])
    for line in text.split("\n")[:20000]:
        if not RECORDED.match(line[:4000]):
            continue
        for m in PATH_TOKEN.finditer(line[:4000]):
            tok = m.group(0)
            if not (tok.lower().endswith(EVIDENCE_EXT) or tok.endswith("/")):
                continue
            comps = [c for c in tok.split("/") if c]
            if comps and comps[0] == "analysis":
                comps = comps[2:] if len(comps) >= 3 and comps[1] == system else []
            if comps and not any(c in (".", "..") for c in comps):
                add(comps)
            if len(found) >= 50:
                return found
    return found


def parse_results_json(data):
    """{test id: status} from a machine-readable per-test results document, or None. Recognised: {"test id": "PASS", ...}, {"tests": ...}
    and [{"name": ..., "status": ...}, ...]. A document that only holds counts ({"PASS": 10, "FAIL": 1}) is not evidence of any test: anyone
    can type one, so it is ignored."""
    def status(v):
        return STATUS.get(re.sub(r"[^a-z]", "", v.lower())) if isinstance(v, str) else None

    obj = data["tests"] if isinstance(data, dict) and isinstance(data.get("tests"), (dict, list)) else data
    tests = {}
    if isinstance(obj, dict):
        items = list(obj.items())[:MAX_CASES]
        good = {str(k)[:400]: status(v) for k, v in items if status(v)}
        if good and len(good) >= 0.9 * len(items):
            tests = good
    elif isinstance(obj, list):
        for e in obj[:MAX_CASES]:
            if isinstance(e, dict):
                name = next((e[k] for k in ("test", "id", "name", "fullName", "fullname") if isinstance(e.get(k), str) and e[k]), None)
                st = next((status(e[k]) for k in ("status", "result", "outcome") if status(e.get(k))), None)
                if name and st:
                    tests.setdefault(name[:400], st)
    return tests or None


def read_baseline_evidence(paths):
    """Read what evidence_paths found: JUnit/TRX XML, machine-readable per-test JSON, and raw runner logs with a known summary line.
    Two sources that disagree are reported as conflicts, never resolved by taking the first.
    -> {"tests": {id: status} or None, "counts": {...} or None (a log alone), "sources", "considered", "ignored", "unreadable", "conflicts", "measured"}."""
    out = {"tests": None, "counts": None, "sources": [], "considered": [], "ignored": [], "unreadable": [], "conflicts": [], "measured": False}
    files = []
    for p in paths:
        if os.path.islink(p):
            continue
        if os.path.isdir(p):
            for base, dirs, names in os.walk(p, followlinks=False):
                dirs[:] = [d for d in sorted(dirs) if d not in SKIP_DIRS and not os.path.islink(os.path.join(base, d))]
                files += [os.path.join(base, n) for n in sorted(names) if n.lower().endswith(EVIDENCE_EXT) and not os.path.islink(os.path.join(base, n))]
                if len(files) >= 2000:
                    break
        elif p.lower().endswith(EVIDENCE_EXT):
            files.append(p)
    files = files[:2000]
    out["considered"] = [clean(os.path.basename(f), 80) for f in files[:20]]
    cat = lambda st: "BAD" if st in BAD else st  # noqa: E731
    tests, conflicts = {}, []

    def merge(more, label):
        for k, v in more.items():
            if k not in tests:
                tests[k] = v
            elif cat(tests[k]) != cat(v):
                conflicts.append("%s: %s in one source, %s in %s" % (clean(k, 100), tests[k], v, label))

    xml = [f for f in files if f.lower().endswith((".xml", ".trx"))]
    if xml:
        got = read_results(xml)
        out["unreadable"] += got["unreadable"][:5]
        if got["files"]:
            merge(got["tests"], "the result files")
            out["sources"].append({"kind": "result files", "files": got["files"], "tests": len(got["tests"])})
    for f in [f for f in files if f.lower().endswith(".json")]:
        name = clean(os.path.basename(f), 80)
        try:
            t = parse_results_json(json.loads(read_capped(f, MAX_FILE).decode("utf-8-sig")))
        except (InputError, ValueError, RecursionError) as err:
            out["unreadable"].append("%s: %s" % (name, clean(err, 100)))
            continue
        if t:
            merge(t, name)
            out["sources"].append({"kind": "machine-readable results", "files": 1, "tests": len(t), "name": name})
        else:
            out["ignored"].append(name)              # counts only, or no test entries: nothing that can be checked test by test
    logs = read_logs([f for f in files if f.lower().endswith((".txt", ".log", ".out"))])
    if logs["files"]:
        out["sources"].append({"kind": "runner log", "files": logs["files"], "executed": logs["executed"], "runners": logs["runners"]})
        if tests:
            c = tally(tests.values())
            if c["executed"] != logs["executed"] or c["fail"] + c["error"] != logs["failed"]:
                conflicts.append("the runner log says %d executed and %d failed; the per-test results say %d and %d" % (logs["executed"], logs["failed"], c["executed"], c["fail"] + c["error"]))
    out["tests"] = tests or None
    out["counts"] = {"executed": logs["executed"], "failed": logs["failed"], "skipped": logs["skipped"]} if logs["files"] and not tests else None
    out["conflicts"] = conflicts[:20]
    out["measured"] = bool(tests or out["counts"])
    return out


def assess_baseline(base, measured):
    """Is BASELINE.md measured or only typed? -> {"kind": "target-only" | "measured" | "typed" | "none", "sources", "disagree", "examples", ...}.
    A typed table is measured only when a result file, a machine-readable results file or a raw log that this script parsed backs it, and
    agrees with it (the same tests with the same outcomes, or the same executed and failed counts)."""
    typed = bool(base["tests"] or base["modules"] or base["totals"])
    info = {"kind": "typed" if typed else "none", "sources": [], "disagree": 0, "examples": [], "conflict": 0, "conflictExamples": [], "considered": list((measured or {}).get("considered", []))[:20],
            "ignored": list((measured or {}).get("ignored", []))[:10], "unreadable": list((measured or {}).get("unreadable", []))[:5], "measuredTests": 0,
            "measuredExecuted": None, "measuredFailed": None}
    if base["targetOnly"]:
        info["kind"] = "target-only"
        return info
    if not measured or not measured["measured"]:
        return info
    info["kind"], info["sources"] = "measured", list(measured["sources"])[:10]
    info["conflict"] = len(measured.get("conflicts", []))
    info["conflictExamples"] = [clean(c, 200) for c in measured.get("conflicts", [])[:3]]
    cat = lambda st: "BAD" if st in BAD else st  # noqa: E731
    typed_counts, _ = baseline_counts(base)
    if measured["tests"] is not None:
        c = tally(measured["tests"].values())
        info.update(measuredTests=len(measured["tests"]), measuredExecuted=c["executed"], measuredFailed=c["fail"] + c["error"])
        if base["tests"]:
            bad = [t for t, st in base["tests"].items() if cat(measured["tests"].get(t, "")) != cat(st)]
            info["disagree"], info["examples"] = len(bad), [clean(t, 120) for t in bad[:5]]
        elif typed_counts and (typed_counts["executed"] != c["executed"] or typed_counts["fail"] + typed_counts["error"] != c["fail"] + c["error"]):
            info["disagree"], info["examples"] = 1, ["typed: %d executed, %d failed; measured: %d executed, %d failed" % (
                typed_counts["executed"], typed_counts["fail"] + typed_counts["error"], c["executed"], c["fail"] + c["error"])]
    else:
        m = measured["counts"]
        info.update(measuredExecuted=m["executed"], measuredFailed=m["failed"])
        if typed_counts and (typed_counts["executed"] != m["executed"] or typed_counts["fail"] + typed_counts["error"] != m["failed"]):
            info["disagree"], info["examples"] = 1, ["typed: %d executed, %d failed; measured: %d executed, %d failed" % (
                typed_counts["executed"], typed_counts["fail"] + typed_counts["error"], m["executed"], m["failed"])]
    totals = base["totals"]            # a Totals table typed beside the rows must say what the evidence says
    ex, fl = info["measuredExecuted"], info["measuredFailed"]
    if totals and ex is not None and (("executed" in totals and totals["executed"] != ex) or (("fail" in totals or "error" in totals) and totals.get("fail", 0) + totals.get("error", 0) != fl)):
        info["disagree"] += 1
        info["examples"].append("the Totals table says %s executed and %s failed; measured: %d and %d" % (totals.get("executed", "?"), totals.get("fail", 0) + totals.get("error", 0), ex, fl))
    return info


# ---------------------------------------------------------------- the comparison
def keep(items):
    return items[:KEEP]


def compare(base, fresh):
    """-> the report dict (see the module docstring)."""
    counts_b, source = baseline_counts(base)
    counts_f = tally(fresh["tests"].values())
    if base.get("measuredTests"):
        source = "measured results"
    rep = {"baseline": {"targetOnly": base["targetOnly"], "why": base["why"], "source": source, "counts": counts_b, "assessment": base.get("assessment")},
           "fresh": {"files": fresh["files"], "counts": counts_f, "unreadable": fresh["unreadable"][:20], "unreadableCount": len(fresh["unreadable"]),
                     "oldest": fresh["oldest"], "newest": fresh["newest"]},
           "regressions": [], "flaky": [], "newFailures": [], "stillFailing": [], "fixed": [], "newlySkipped": [], "missing": [], "renamed": 0,
           "missingModules": [], "moduleDiffs": [], "executedDrop": None, "skippedGrowth": None, "problems": list(fresh["problems"])}
    bt, ft, flaky = base["tests"], fresh["tests"], set(base.get("flaky", []))
    if bt:
        missing = [t for t in bt if t not in ft]
        added = [t for t in ft if t not in bt]
        for t, b in bt.items():
            f = ft.get(t)
            if f is None:
                continue
            if b == "PASS" and f in BAD:
                (rep["flaky"] if t in flaky else rep["regressions"]).append({"id": t, "before": b, "now": f})
            elif b in BAD and f in BAD:
                rep["stillFailing"].append(t)
            elif b in BAD and f == "PASS":
                rep["fixed"].append(t)
            elif b == "PASS" and f == "SKIP":
                rep["newlySkipped"].append(t)
            elif b == "SKIP" and f in BAD:
                rep["newFailures"].append(t)
        by_class = {}
        for t in missing:
            by_class.setdefault(t.split("#", 1)[0], [[], []])[0].append(t)
        for t in added:
            by_class.setdefault(t.split("#", 1)[0], [[], []])[1].append(t)
        drifting = {k for k, (gone, new) in by_class.items() if gone and new}
        grouped_b, grouped_f = {}, {}
        for src, dst in ((bt, grouped_b), (ft, grouped_f)):
            for t, v in src.items():
                if t.split("#", 1)[0] in drifting:
                    dst.setdefault(t.split("#", 1)[0], []).append(v)
        for klass, (gone, new) in by_class.items():
            b_counts, f_counts = tally(grouped_b.get(klass, [])), tally(grouped_f.get(klass, []))
            if gone and new and f_counts["executed"] >= b_counts["executed"] and f_counts["fail"] + f_counts["error"] <= b_counts["fail"] + b_counts["error"]:
                rep["renamed"] += len(gone)
            else:
                rep["missing"] += gone
                rep["newFailures"] += [t for t in new if ft[t] in BAD]
    for name, b in base["modules"].items():
        f = fresh["classes"].get(name) or fresh["modules"].get(name) or fresh["suites"].get(name)
        if f is None:
            rep["missingModules"].append(name)
            continue
        problems = []
        if f["executed"] < b["pass"] + b["fail"] + b["error"]:
            problems.append("%d test(s) executed, %d before" % (f["executed"], b["pass"] + b["fail"] + b["error"]))
        if f["skip"] > b["skip"]:
            problems.append("%d skipped, %d before" % (f["skip"], b["skip"]))
        if not bt and f["fail"] + f["error"] > b["fail"] + b["error"]:
            rep["regressions"].append({"id": name + " (all its tests)", "before": "%d failing" % (b["fail"] + b["error"]), "now": "%d failing" % (f["fail"] + f["error"])})
        if problems:
            rep["moduleDiffs"].append({"module": name, "problems": problems})
    if counts_b:
        if counts_f["executed"] < counts_b["executed"]:
            rep["executedDrop"] = {"before": counts_b["executed"], "now": counts_f["executed"]}
        if counts_f["skip"] > counts_b["skip"]:
            rep["skippedGrowth"] = {"before": counts_b["skip"], "now": counts_f["skip"]}
    rep["approved"] = []
    for key, label in (("regressions", "passed before, fails now"), ("newFailures", "not in the baseline, fails now")):
        kept = []
        for item in rep[key]:
            tid = item["id"] if isinstance(item, dict) else item
            if tid in base.get("approved", {}):
                rep["approved"].append({"id": tid, "reason": base["approved"][tid], "was": label})
            else:
                kept.append(item)
        rep[key] = kept
    for key in ("regressions", "flaky", "newFailures", "stillFailing", "fixed", "newlySkipped", "missing", "missingModules", "moduleDiffs", "approved"):
        rep[key + "Count"], rep[key] = len(rep[key]), keep(rep[key])
    rep["ok"] = counts_f["executed"] > 0 and not rep["regressionsCount"] and not rep["newFailuresCount"]
    return rep


def render(rep, limit=10):
    b, f = rep["baseline"]["counts"], rep["fresh"]["counts"]
    show = lambda c: "%d executed (%d pass, %d fail, %d error, %d skip)" % (c["executed"], c["pass"], c["fail"], c["error"], c["skip"])  # noqa: E731
    lines = ["baseline (%s): %s" % (rep["baseline"]["source"], show(b) if b else "nothing readable"),
             "this run (%d result file(s)): %s" % (rep["fresh"]["files"], show(f))]
    if rep["baseline"]["targetOnly"]:
        lines.append("BASELINE.md says target-only (%s): there is no old-version result to compare with." % (rep["baseline"]["why"] or "no reason given"))
    a = rep["baseline"].get("assessment")
    if a and a["kind"] == "measured":
        lines.append("baseline evidence: measured (%s)" % "; ".join("%s%s" % (s["kind"], " %s" % s["name"] if s.get("name") else "") for s in a["sources"][:4]))
        if a["conflict"]:
            lines.append("  but the sources disagree with each other: %s" % "; ".join(a["conflictExamples"][:3]))
        elif a["disagree"]:
            lines.append("  but the typed table disagrees with it on %d test(s): %s" % (a["disagree"], "; ".join(a["examples"][:3])))
    elif a and a["kind"] == "typed":
        lines.append("baseline evidence: typed table only. No result file, per-test results file or raw log that this script can read was found in analysis/<system>/baseline/ or on a Recorded: or Machine-readable: line of BASELINE.md.%s" % (
            " Ignored (counts only): " + ", ".join(a["ignored"][:3]) if a["ignored"] else ""))

    def block(title, key, fmt=lambda x: clean(x, 160)):
        if rep[key + "Count"]:
            lines.append("%s: %d" % (title, rep[key + "Count"]))
            lines.extend("  " + fmt(x) for x in rep[key][:limit])
            if rep[key + "Count"] > limit:
                lines.append("  ... and %d more (use --json)" % (rep[key + "Count"] - limit))
        else:
            lines.append("%s: 0" % title)
    block("regressions (passed before, fail now)", "regressions", lambda x: "%s: %s -> %s" % (clean(x["id"], 140), x["before"], x["now"]))
    block("differences a person approved in BASELINE.md (not counted)", "approved", lambda x: "%s: %s (%s)" % (clean(x["id"], 120), x["was"], clean(x["reason"], 100)))
    block("flaky flips the baseline lists (not counted)", "flaky", lambda x: "%s: %s -> %s" % (clean(x["id"], 140), x["before"], x["now"]))
    block("new failures (not in the baseline)", "newFailures")
    block("still failing, as in the baseline", "stillFailing")
    block("now passing (failed before)", "fixed")
    block("skipped now that ran before", "newlySkipped")
    block("baseline tests that did not run", "missing")
    block("modules missing from this run", "missingModules")
    block("modules with fewer tests or more skips", "moduleDiffs", lambda x: "%s: %s" % (clean(x["module"], 100), "; ".join(x["problems"])))
    if rep["renamed"]:
        lines.append("renamed: %d test name(s) changed but their class did not get worse" % rep["renamed"])
    if rep["executedDrop"]:
        lines.append("executed tests dropped from %(before)d to %(now)d" % rep["executedDrop"])
    if rep["skippedGrowth"]:
        lines.append("skipped tests grew from %(before)d to %(now)d" % rep["skippedGrowth"])
    lines += ["%d result file(s) could not be read: %s" % (rep["fresh"]["unreadableCount"], "; ".join(rep["fresh"]["unreadable"][:3])) if rep["fresh"]["unreadableCount"] else "all result files were read"]
    lines += rep["problems"]
    lines.append("OK: nothing regressed and %d test(s) executed" % f["executed"] if rep["ok"] else "NOT OK: %s" % (
        "no test executed" if not f["executed"] else "%d regression(s), %d new failure(s)" % (rep["regressionsCount"], rep["newFailuresCount"])))
    return "\n".join(lines)


def run(baseline_path, paths, measured="auto"):
    """-> the report. Raises InputError for a baseline or results that cannot be used. `measured` is the old version's own evidence
    (from read_baseline_evidence); by default it is looked for beside BASELINE.md (see evidence_paths). Measured per-test results,
    when there are any, are what the fresh results are compared with; the typed table is only checked against them."""
    if os.path.islink(baseline_path):
        raise InputError("%s is a symbolic link" % baseline_path)
    try:
        with open(baseline_path, "rb") as fh:
            text = fh.read(16 << 20).decode("utf-8", "replace")
    except OSError as err:
        raise InputError("cannot read %s: %s" % (baseline_path, err.__class__.__name__))
    base = parse_baseline(text)
    if not (base["targetOnly"] or base["modules"] or base["tests"] or base["totals"]):
        raise InputError("%s has no per-test table, per-module table, totals or target-only line that can be read" % baseline_path)
    if measured == "auto":
        found = evidence_paths(baseline_path, text)
        measured = read_baseline_evidence(found) if found else None
    base["assessment"] = assess_baseline(base, measured)
    if base["assessment"]["kind"] == "measured" and measured["tests"]:
        base["tests"], base["measuredTests"] = measured["tests"], True
    return compare(base, read_results(paths))


def main(argv=None):
    ap = argparse.ArgumentParser(description="Compare a fresh test run with BASELINE.md.")
    ap.add_argument("baseline", help="analysis/<system>/BASELINE.md")
    ap.add_argument("--junit", "--trx", action="append", default=[], metavar="PATH", help="a results file or a folder to search (repeat for several)")
    ap.add_argument("--baseline-evidence", action="append", default=[], metavar="PATH",
                    help="a file or folder with the old version's own results (XML, JSON map, raw log); default: analysis/<system>/baseline/ and the paths BASELINE.md names")
    ap.add_argument("--json", action="store_true", help="print the full report as JSON")
    ap.add_argument("--max-list", type=int, default=10, help="how many entries to print per list (default 10)")
    args = ap.parse_args(argv)
    if not args.junit:
        print("baseline_diff.py: give at least one --junit file or folder", file=sys.stderr)
        return 2
    try:
        rep = run(args.baseline, args.junit, read_baseline_evidence(args.baseline_evidence) if args.baseline_evidence else "auto")
    except InputError as err:
        print("baseline_diff.py: %s" % err, file=sys.stderr)
        return 2
    print(json.dumps(rep, indent=1, ensure_ascii=True) if args.json else render(rep, max(1, args.max_list)))
    return 0 if rep["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
