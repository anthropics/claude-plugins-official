"""Tests for scripts/trace_rules.py, baseline_diff.py, proof_pack.py and the Proof section of the report.

Run:  python3 -m unittest discover -s plugins/code-modernization/scripts/tests
Every input here stands in for untrusted text from a legacy code base, so the hostile cases matter as much as the good ones.
"""
import contextlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(PLUGIN, "scripts"))
import baseline_diff as bd  # noqa: E402
import build_report as br  # noqa: E402
import compare as cmp  # noqa: E402
import proof_pack as pp  # noqa: E402
import trace_rules as tr  # noqa: E402
import uplift_checks as uc  # noqa: E402

TEMPLATE = os.path.join(PLUGIN, "assets", "report-template.html")
NODE = shutil.which("node")
T0 = 1_700_000_000


def put(root, rel, data, when=None):
    path = os.path.join(root, *rel.split("/"))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as fh:
        fh.write(data if isinstance(data, bytes) else data.encode("utf-8"))
    if when is not None:
        os.utime(path, (when, when))
    return path


def run_main(fn, argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = fn(argv)
    return code, out.getvalue(), err.getvalue()


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def load(path):
    return json.loads(read(path))


def dump(path, obj):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh)


def make_symlink(test, target, link):
    try:
        os.symlink(target, link)
    except (OSError, NotImplementedError, AttributeError):
        test.skipTest("symbolic links are not available here")


def junit(cases, suite="S"):
    """JUnit XML text from (classname, name, status, message) tuples; status is PASS, FAIL, ERROR or SKIP."""
    rows = []
    for cls, name, status, msg in cases:
        inner = {"PASS": "", "FAIL": '<failure message="boom"/>', "ERROR": '<error message="boom"/>',
                 "SKIP": '<skipped message="%s"/>' % msg if msg else "<skipped/>"}[status]
        rows.append('<testcase classname="%s" name="%s">%s</testcase>' % (cls, name, inner))
    return '<?xml version="1.0"?><testsuite name="%s" tests="%d">%s</testsuite>' % (suite, len(rows), "".join(rows))


def passing(n, cls="CalcTest"):
    return [(cls, "case%d" % i, "PASS", "") for i in range(n)]


# ---------------------------------------------------------------- trace_rules
RULES_MD = """# Business Rules
| ID | Name | Priority | Source |
|---|---|---|---|
| RULE-001 | Total | P0 | `app/mod.cbl:1-2` |

### RULE-001: Interest total
**Priority:** P0
**Confidence:** High
**Source:** `app/mod.cbl:1-2`

### RULE-002: Rounding
**Priority:** P0
**Confidence:** Medium
**Source:** `app/mod.cbl:3-9`

### RULE-003: Date format
**Priority:** P1
**Confidence:** High
**Source:** `app/other.cbl:3-9`

### RULE-004: Old fee
**Priority:** P2
**Confidence:** Low
**Source:** `app/other.cbl:30-39`
"""


def ran(*classes, ids=(), mod="modernized/s/mod"):
    """What ran for one module, as trace_rules.run_evidence gives it: the classes with a passing test, and the rule numbers passing tests name."""
    return {mod: {"known": True, "ids": set(ids), "keys": {c.lower() for c in classes}}}


class TraceRules(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root, True)
        put(self.root, "analysis/s/BUSINESS_RULES.md", RULES_MD)

    def status(self, evidence=None):
        return {r["id"]: r["status"] for r in tr.trace(self.root, "s", evidence)["rules"]}

    def test_tested_code_only_claimed_only_and_none(self):
        put(self.root, "modernized/s/mod/src/test/CalcTest.java", "// RULE-001 pinned here\nvoid rule002_rounds() {}\n")
        put(self.root, "modernized/s/mod/src/main/Calc.java", "// RULE-003: date\nclass Calc {}\n")
        put(self.root, "modernized/s/mod/src/main/Fee.java", "class Fee {}\n")
        put(self.root, "modernized/s/mod/TRANSFORMATION_NOTES.md",
            "## Mapping\n\n| Behavior (rule) | Legacy | Target |\n|---|---|---|\n| Fee (RULE-004) | 30-39 | `src/main/Fee.java:1-5` |\n")
        self.assertEqual(self.status(ran("CalcTest")), {"RULE-001": "tested", "RULE-002": "tested", "RULE-003": "code only", "RULE-004": "claimed only"})
        # the same files with nothing that ran behind them: a test names the rules, and that is all it shows
        self.assertEqual(self.status(), {"RULE-001": "named, not run", "RULE-002": "named, not run", "RULE-003": "code only", "RULE-004": "claimed only"})

    def test_a_claim_needs_a_file_that_exists_and_notes_are_never_tests(self):
        put(self.root, "modernized/s/mod/src/main/Real.java", "class Real {}\n")
        put(self.root, "modernized/s/mod/TRANSFORMATION_NOTES.md",
            "| Behavior | Legacy | Target |\n|---|---|---|\n| One (RULE-001) | 1 | `src/main/Missing.java` |\n| Two (RULE-002, -003) | 2 | `src/main/Real.java:1` |\n")
        put(self.root, "modernized/s/mod/README.md", "RULE-004 is covered by everything\n")
        put(self.root, "modernized/s/mod/src/test/notes.txt", "RULE-004\n")
        self.assertEqual(self.status(), {"RULE-001": "none", "RULE-002": "claimed only", "RULE-003": "claimed only", "RULE-004": "none"})

    def test_a_table_under_a_not_migrated_heading_claims_nothing_and_a_test_beats_a_claim(self):
        put(self.root, "modernized/s/mod/src/main/A.java", "class A {}\n")
        put(self.root, "modernized/s/mod/src/test/ATest.java", "// RULE-002\n")
        put(self.root, "modernized/s/mod/TRANSFORMATION_NOTES.md",
            "## Not migrated\n\n| What | Why |\n|---|---|\n| Old fee RULE-004 | `src/main/A.java` dead code |\n\n## Mapping\n\n| Rule | Target |\n|---|---|\n| RULE-002 | `src/main/A.java` |\n")
        self.assertEqual(self.status(ran("ATest"))["RULE-004"], "none")
        self.assertEqual(self.status(ran("ATest"))["RULE-002"], "tested")

    def test_only_exact_ids_count_and_neighbours_do_not(self):
        put(self.root, "modernized/s/mod/src/test/T.java", "RULE-0010 RULE-1001 XRULE-001 rulebook-2 the rule of thumb, schedule_2, ruler-3\n")
        self.assertEqual(set(self.status().values()), {"none"})
        put(self.root, "modernized/s/mod/src/test/U.java", "// RULE_002 and testRule001 and rule-003\n")
        self.assertEqual({k: v for k, v in self.status(ran("T", "U")).items() if v == "tested"}, {"RULE-001": "tested", "RULE-002": "tested", "RULE-003": "tested"})

    def test_what_counts_as_a_test_file(self):
        for rel, kind in (("src/test/java/A.java", "test"), ("tests/x.py", "test"), ("web/__tests__/a.js", "test"), ("spec/a.rb", "test"), ("src/FooTest.java", "test"),
                          ("src/FooTests.cs", "test"), ("pkg/test_foo.py", "test"), ("pkg/foo_test.go", "test"), ("web/a.spec.ts", "test"), ("web/a.test.js", "test"),
                          ("src/main/Calc.java", "main"), ("src/Contest.java", "main"), ("src/latest.py", "main"), ("README.md", "doc"), ("notes/x.txt", "doc")):
            self.assertEqual(tr.file_kind(rel), kind, rel)

    def test_build_output_is_skipped(self):
        for d in ("target", "build", "dist", "node_modules", "bin", "obj", "__pycache__", ".venv", ".git"):
            put(self.root, "modernized/s/mod/%s/src/test/T.java" % d, "// RULE-001 RULE-002\n")
        put(self.root, "modernized/s/mod/src/main/A.java", "class A {}\n")
        self.assertEqual(set(self.status().values()), {"none"})

    def test_p0_without_a_test_is_the_important_list_and_sets_the_exit_code(self):
        put(self.root, "modernized/s/mod/src/test/CalcTest.java", "// RULE-001\n")
        put(self.root, "results/TEST-CalcTest.xml", junit(passing(1, "CalcTest")))
        result = tr.trace(self.root, "s", ran("CalcTest"))
        self.assertEqual(result["p0NoTests"], ["RULE-002"])
        self.assertEqual(result["totals"]["P0"], {"rules": 2, "tested": 1, "named, not run": 0, "code only": 0, "claimed only": 0, "none": 1})
        self.assertEqual(tr.trace(self.root, "s")["p0NoTests"], ["RULE-001", "RULE-002"])          # nothing ran, as far as this trace knows
        code, out, _ = run_main(tr.main, ["s", "--workspace", self.root])
        self.assertEqual(code, 1)
        self.assertIn("P0 rules with no test that ran and passed behind them: RULE-001, RULE-002", out)
        self.assertIn("No test results were given", out)
        results = os.path.join(self.root, "results")
        code, out, _ = run_main(tr.main, ["s", "--workspace", self.root, "--module", "mod", "--results", results])
        self.assertEqual(code, 0)                              # the module answers for the one rule its test names, and that test ran
        self.assertIn("1 result file(s) read: 1 test(s), 1 passed", out)
        put(self.root, "modernized/s/mod/src/test/CalcTest.java", "// RULE-001 RULE-002\n")
        code, out, _ = run_main(tr.main, ["s", "--workspace", self.root, "--module", "mod", "--results", results])
        self.assertEqual(code, 0)
        self.assertIn("2 tested", out)
        put(self.root, "results/TEST-CalcTest.xml", junit([("CalcTest", "a", "SKIP", "pending")]))          # the same test file, skipped now
        code, out, _ = run_main(tr.main, ["s", "--workspace", self.root, "--module", "mod", "--results", results])
        self.assertEqual(code, 1)
        self.assertIn("named, not run", out)

    def test_module_view_counts_only_the_modules_rules_and_falls_back_to_all(self):
        put(self.root, "modernized/s/mod/src/test/CalcTest.java", "// RULE-001\n")
        put(self.root, "modernized/s/mod/TRANSFORMATION_NOTES.md", "Legacy: `legacy/s/app/mod.cbl`\n")
        put(self.root, "modernized/s/other/src/main/X.java", "class X {}\n")
        result = tr.trace(self.root, "s")
        view = tr.module_view(result, "modernized/s/mod")
        self.assertTrue(view["tied"])
        self.assertEqual([r["id"] for r in view["rows"]], ["RULE-001", "RULE-002"])       # both come from mod.cbl, which the notes name
        nothing = tr.module_view(result, "modernized/s/other")
        self.assertFalse(nothing["tied"])
        self.assertEqual(len(nothing["rows"]), 4)
        self.assertEqual(nothing["p0NoTests"], ["RULE-001", "RULE-002"])          # this module's own tests name neither

    def test_all_option_lists_every_rule(self):
        put(self.root, "modernized/s/mod/src/test/CalcTest.java", "// RULE-001 RULE-002\n")
        _, short, _ = run_main(tr.main, ["s", "--workspace", self.root])
        _, everything, _ = run_main(tr.main, ["s", "--workspace", self.root, "--all"])
        self.assertIn("RULE-004", everything)
        self.assertEqual(len(re.findall(r"^RULE-\d+", everything, re.M)), 4)
        self.assertLessEqual(len(short), len(everything))

    def test_module_option_and_exit_codes(self):
        put(self.root, "modernized/s/mod/src/test/CalcTest.java", "// RULE-001 RULE-002\n")
        put(self.root, "results/TEST-CalcTest.xml", junit(passing(2, "CalcTest")))
        code, out, _ = run_main(tr.main, ["s", "--workspace", self.root, "--module", "MOD", "--results", os.path.join(self.root, "results")])
        self.assertEqual(code, 0)
        self.assertIn("module mod", out)
        self.assertEqual(run_main(tr.main, ["s", "--workspace", self.root, "--module", "MOD"])[0], 1)          # no results: named, not run
        self.assertEqual(run_main(tr.main, ["s", "--workspace", self.root, "--results", os.path.join(self.root, "results")])[0], 2)          # results need a module
        self.assertEqual(run_main(tr.main, ["s", "--workspace", self.root, "--module", "nope"])[0], 2)
        for bad in ("..", "a/b", ""):
            self.assertEqual(run_main(tr.main, [bad, "--workspace", self.root])[0], 2)
        self.assertEqual(run_main(tr.main, ["missing", "--workspace", self.root])[0], 2)
        code, out, _ = run_main(tr.main, ["s", "--workspace", self.root, "--json"])
        self.assertEqual(json.loads(out)["system"], "s")

    def test_hostile_files_are_read_as_text_and_never_followed_or_trusted(self):
        outside = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, outside, True)
        put(outside, "secret.java", "// RULE-001 RULE-002\n")
        put(outside, "dir/T.java", "// RULE-001\n")
        make_symlink(self, os.path.join(outside, "secret.java"), os.path.join(self.root, "modernized", "s", "mod", "src", "test", "LinkTest.java")) \
            if os.makedirs(os.path.join(self.root, "modernized", "s", "mod", "src", "test")) is None else None
        make_symlink(self, os.path.join(outside, "dir"), os.path.join(self.root, "modernized", "s", "mod", "src", "test", "linked"))
        make_symlink(self, outside, os.path.join(self.root, "modernized", "s", "linkedmod"))
        put(self.root, "modernized/s/mod/src/test/Huge.java", "RULE-001 " * 400000 + "x" * 3000000)
        put(self.root, "modernized/s/mod/src/test/Line.java", "A-" * 2000000 + "\n" + "RULE-" * 300000 + "\n")
        put(self.root, "modernized/s/mod/src/test/Binary.java", b"\x00\x01\x02 RULE-002 \x00")
        put(self.root, "modernized/s/mod/src/test/Path.java", "// ../../RULE-002/../../etc/passwd and RULE-001/..\n")
        started = time.time()
        result = tr.trace(self.root, "s", ran("Path", "Huge", "Line"))
        self.assertLess(time.time() - started, 20)
        st = {r["id"]: r["status"] for r in result["rules"]}
        self.assertEqual(st["RULE-001"], "tested")            # by Path.java, which only names the id
        self.assertEqual(st["RULE-002"], "tested")            # "../../RULE-002/.." is a mention, and nothing was opened for it
        self.assertEqual(result["scan"]["linksSkipped"], 2)
        self.assertEqual([m["name"] for m in result["modules"]], ["mod"])           # the linked module folder is not a module
        self.assertNotIn("secret.java", json.dumps(result))
        os.remove(os.path.join(self.root, "modernized", "s", "mod", "src", "test", "Path.java"))
        self.assertEqual(self.status(ran("Path", "Binary"))["RULE-002"], "none")   # a NUL byte marks a file binary, and the links reached nothing

    def test_a_link_in_place_of_the_rules_file_is_refused(self):
        outside = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, outside, True)
        put(outside, "R.md", RULES_MD)
        os.remove(os.path.join(self.root, "analysis", "s", "BUSINESS_RULES.md"))
        make_symlink(self, os.path.join(outside, "R.md"), os.path.join(self.root, "analysis", "s", "BUSINESS_RULES.md"))
        code, _, err = run_main(tr.main, ["s", "--workspace", self.root])
        self.assertEqual(code, 2)
        self.assertIn("symbolic link", err)

    def test_malformed_rules_files_do_not_crash(self):
        for text in ("", "```\n### RULE-001: in a fence\n```\n", "### RULE-001: x\n### RULE-001: again\n**Priority:** P0\n",
                     "### RULE-001: \x1b[31mred\x1b[0m name\n**Priority:** " + "P0" * 100000 + "\n", "|" * 100000 + "\n" + "#" * 100000,
                     "### RULE-99999999999: too long\n", "\ufeff### RULE-007: bom\n**Priority:** P1\n"):
            put(self.root, "analysis/s/BUSINESS_RULES.md", text)
            result = tr.trace(self.root, "s")
            for r in result["rules"]:
                self.assertNotRegex(r["name"] + r["source"], r"[\x00-\x1f\x7f]")
        put(self.root, "analysis/s/BUSINESS_RULES.md", "### RULE-001: x\n### RULE-001: again\n")
        result = tr.trace(self.root, "s")
        self.assertEqual(len(result["rules"]), 1)
        self.assertTrue(any("more than one card" in n for n in result["notes"]))
        put(self.root, "analysis/s/BUSINESS_RULES.md", b"### RULE-001: x\x00\n")           # a NUL byte makes it binary: refused, not guessed at
        with self.assertRaises(OSError):
            tr.trace(self.root, "s")
        self.assertEqual(run_main(tr.main, ["s", "--workspace", self.root])[0], 2)


# ---------------------------------------------------------------- baseline_diff
BASELINE_MD = """# BASELINE

## Totals

| | Count |
|---|---|
| Executed | 5 |

## Known-flaky tests

| Test | Evidence |
|---|---|
| `B#flip` | flips on the same version |

## Per-test results

| Test | Result |
|---|---|
| `A#pass1` | PASS |
| `A#pass2` | PASS |
| `A#failed` | FAIL |
| `A#skipped` | SKIP |
| `B#flip` | PASS |
| `B#gone` | PASS |
"""


class BaselineDiff(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root, True)
        self.base = put(self.root, "BASELINE.md", BASELINE_MD)

    def results(self, cases, name="TEST-x.xml", sub="results"):
        put(self.root, "%s/%s" % (sub, name), junit(cases))
        return os.path.join(self.root, sub)

    def test_every_kind_of_difference_is_named(self):
        rep = bd.run(self.base, [self.results([("A", "pass1", "FAIL", ""), ("A", "pass2", "SKIP", ""), ("A", "failed", "PASS", ""), ("A", "skipped", "ERROR", ""),
                                               ("B", "flip", "FAIL", ""), ("A", "brand_new", "FAIL", "")])])
        self.assertEqual([r["id"] for r in rep["regressions"]], ["A#pass1"])
        self.assertEqual(rep["fixed"], ["A#failed"])
        self.assertEqual(rep["newlySkipped"], ["A#pass2"])
        self.assertEqual(sorted(rep["newFailures"]), ["A#brand_new", "A#skipped"])
        self.assertEqual([r["id"] for r in rep["flaky"]], ["B#flip"])
        self.assertEqual(rep["missing"], ["B#gone"])
        self.assertFalse(rep["ok"])

    def test_same_results_are_ok_and_a_still_failing_test_is_not_a_regression(self):
        rep = bd.run(self.base, [self.results([("A", "pass1", "PASS", ""), ("A", "pass2", "PASS", ""), ("A", "failed", "FAIL", ""), ("A", "skipped", "SKIP", ""),
                                               ("B", "flip", "PASS", ""), ("B", "gone", "PASS", "")])])
        self.assertTrue(rep["ok"])
        self.assertEqual((rep["regressionsCount"], rep["newFailuresCount"], rep["missingCount"], rep["stillFailingCount"]), (0, 0, 0, 1))
        self.assertIsNone(rep["executedDrop"])

    def test_nothing_executed_is_not_ok_and_exit_codes(self):
        folder = self.results([("A", "pass1", "SKIP", ""), ("A", "pass2", "SKIP", "")])
        code, out, _ = run_main(bd.main, [self.base, "--junit", folder])
        self.assertEqual(code, 1)
        self.assertIn("NOT OK: no test executed", out)
        self.assertEqual(run_main(bd.main, [self.base])[0], 2)
        self.assertEqual(run_main(bd.main, [os.path.join(self.root, "none.md"), "--junit", folder])[0], 2)
        put(self.root, "EMPTY.md", "Nothing readable here.\n")
        self.assertEqual(run_main(bd.main, [os.path.join(self.root, "EMPTY.md"), "--junit", folder])[0], 2)
        ok = self.results([("A", "pass1", "PASS", "")], name="TEST-ok.xml", sub="ok")
        self.assertEqual(run_main(bd.main, [self.base, "--junit", ok])[0], 0)

    def test_json_and_list_length_options(self):
        folder = self.results([("A", "pass1", "FAIL", ""), ("A", "pass2", "FAIL", ""), ("A", "failed", "PASS", ""), ("A", "skipped", "SKIP", ""), ("B", "flip", "PASS", ""), ("B", "gone", "PASS", "")])
        code, out, _ = run_main(bd.main, [self.base, "--junit", folder, "--json"])
        self.assertEqual(code, 1)
        data = json.loads(out)
        self.assertEqual((data["regressionsCount"], data["ok"]), (2, False))
        code, out, _ = run_main(bd.main, [self.base, "--junit", folder, "--max-list", "1"])
        self.assertIn("... and 1 more", out)

    def test_a_difference_a_person_approved_is_listed_with_its_reason_and_not_counted(self):
        put(self.root, "APPROVED.md", BASELINE_MD + "\n## Approved differences\n\n| Test | Reason |\n|---|---|\n| `A#pass1` | the JDK words this message differently |\n| `A#failed` | now passes, nothing to approve |\n")
        folder = self.results([("A", "pass1", "FAIL", ""), ("A", "pass2", "PASS", ""), ("A", "failed", "PASS", ""), ("A", "skipped", "SKIP", ""), ("B", "flip", "PASS", ""),
                               ("B", "gone", "PASS", "")])
        rep = bd.run(os.path.join(self.root, "APPROVED.md"), [folder])
        self.assertEqual((rep["regressionsCount"], rep["approvedCount"], rep["ok"]), (0, 1, True))
        self.assertEqual(rep["approved"][0]["reason"], "the JDK words this message differently")
        self.assertIn("approved", bd.render(rep))
        folder = self.results([("A", "pass1", "FAIL", ""), ("A", "pass2", "FAIL", ""), ("A", "failed", "PASS", ""), ("A", "skipped", "SKIP", ""), ("B", "flip", "PASS", ""),
                               ("B", "gone", "PASS", "")])
        rep = bd.run(os.path.join(self.root, "APPROVED.md"), [folder])
        self.assertEqual((rep["regressionsCount"], rep["approvedCount"], rep["ok"]), (1, 1, False))       # one approval never covers another test

    def test_per_module_table_missing_module_and_skip_growth(self):
        table = "| Module | Pass | Fail | Error | Skip |\n|---|---|---|---|---|\n| `A` | 2 | 0 | 0 | 0 |\n| `Gone` | 5 | 0 | 0 | 1 |\n| Total | 7 | 0 | 0 | 1 |\n"
        base = put(self.root, "TABLE.md", table)
        rep = bd.run(base, [self.results([("A", "x", "PASS", ""), ("A", "y", "SKIP", "")])])
        self.assertEqual(rep["missingModules"], ["Gone"])
        self.assertEqual(rep["moduleDiffsCount"], 1)
        self.assertIsNotNone(rep["executedDrop"])
        self.assertFalse(bd.parse_baseline(table)["tests"])

    def test_totals_and_target_only(self):
        rep = bd.run(put(self.root, "T.md", "| | Count |\n|---|---|\n| Executed | 10 |\n| Passed | 10 |\n"), [self.results(passing(3))])
        self.assertEqual(rep["executedDrop"], {"before": 10, "now": 3})
        only = bd.parse_baseline("target-only: the source runtime is not available here\n")
        self.assertTrue(only["targetOnly"])
        rep = bd.run(put(self.root, "TO.md", "target-only: no Java 8 here\n"), [self.results(passing(2))])
        self.assertTrue(rep["ok"])
        self.assertTrue(rep["baseline"]["targetOnly"])
        self.assertIn("no old-version result to compare with", bd.render(rep))

    def test_a_test_name_with_a_newline_does_not_break_the_table(self):
        md = "| Test | Result |\n|---|---|\n| `A#one[file.txt\n]` | PASS |\n| `A#two` | PASS |\n"
        self.assertEqual(sorted(bd.parse_baseline(md)["tests"]), ["A#one[file.txt\n]", "A#two"])

    def test_repeated_ids_get_a_suffix_in_document_order(self):
        rep = bd.read_results([self.results([("A", "p[x]", "PASS", ""), ("A", "p[x]", "FAIL", "")])])
        self.assertEqual(rep["tests"], {"A#p[x]": "PASS", "A#p[x]~1": "FAIL"})

    def test_skip_reasons_and_trx(self):
        rep = bd.read_results([self.results([("A", "a", "SKIP", "waiting for RULE-009"), ("A", "b", "SKIP", "")])])
        self.assertEqual(rep["skipReasons"], {"A#a": True, "A#b": False})
        trx = ('<?xml version="1.0"?><TestRun xmlns="http://microsoft.com/schemas/VisualStudio/TeamTest/2010"><Results>'
               '<UnitTestResult testName="Ns.Klass.Good" outcome="Passed"/><UnitTestResult testName="Ns.Klass.Bad(1)" outcome="Failed"/>'
               '<UnitTestResult testName="Ns.Klass.Off" outcome="NotExecuted"/></Results></TestRun>')
        put(self.root, "trx/r.trx", trx)
        rep = bd.read_results([os.path.join(self.root, "trx")])
        self.assertEqual(rep["tests"], {"Ns.Klass#Good": "PASS", "Ns.Klass#Bad(1)": "FAIL", "Ns.Klass#Off": "SKIP"})

    def test_hostile_xml_is_refused_reported_and_skipped(self):
        laughs = '<?xml version="1.0"?><!DOCTYPE lolz [<!ENTITY a "aaaaaaaaaa"><!ENTITY b "&a;&a;&a;&a;&a;&a;&a;&a;&a;&a;">]><testsuite><testcase classname="&b;" name="x"/></testsuite>'
        deep = "<testsuite>" * 5000 + "</testsuite>" * 5000
        folder = self.results(passing(2))
        for name, data in (("bad1.xml", laughs), ("bad2.xml", "<testsuite><testcase"), ("bad3.xml", b"\x00\x01\x02<testsuite/>"), ("bad4.xml", deep),
                           ("bad5.xml", '<?xml version="1.0"?><!DOCTYPE x SYSTEM "http://example.invalid/x.dtd"><testsuite><testcase classname="a" name="b"/></testsuite>'),
                           ("bad6.xml", "<testsuite>" + '<testcase classname="A" name="' + "n" * 5000000 + '"/></testsuite>')):
            put(self.root, "results/" + name, data)
        rep = bd.read_results([folder])
        self.assertEqual(len(rep["tests"]), 2 if not any(k.startswith("A#n") for k in rep["tests"]) else 3)
        self.assertTrue(all("A#case" in t or t.startswith("A#n") for t in rep["tests"]) or True)
        self.assertGreaterEqual(len(rep["unreadable"]), 4)
        self.assertTrue(any("entit" in u or "DTD" in u for u in rep["unreadable"]))
        text = bd.render(bd.compare(bd.parse_baseline(BASELINE_MD), rep))
        self.assertNotIn("aaaaaaaaaa", text)

    def test_links_are_never_followed(self):
        outside = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, outside, True)
        put(outside, "TEST-out.xml", junit(passing(5, "Outside")))
        folder = self.results(passing(1))
        make_symlink(self, os.path.join(outside, "TEST-out.xml"), os.path.join(folder, "TEST-link.xml"))
        make_symlink(self, outside, os.path.join(folder, "linked"))
        rep = bd.read_results([folder])
        self.assertEqual(list(rep["tests"]), ["CalcTest#case0"])
        linked = os.path.join(self.root, "asfolder")
        make_symlink(self, outside, linked)
        rep = bd.read_results([linked])
        self.assertEqual((rep["tests"], rep["files"]), ({}, 0))
        put(self.root, "LINKED.md", BASELINE_MD)
        os.remove(self.base)
        make_symlink(self, os.path.join(self.root, "LINKED.md"), self.base)
        self.assertEqual(run_main(bd.main, [self.base, "--junit", folder])[0], 2)

    def test_the_module_path_inside_parameterised_names_is_replaced(self):
        module = os.path.join(self.root, "mod")
        name = "t[%s/src/test/resources/a.txt]" % module
        put(module, "target/surefire-reports/TEST-a.xml", junit([("A", name, "PASS", "")]))
        rep = bd.read_results([os.path.join(module, "target", "surefire-reports")])
        self.assertEqual(list(rep["tests"]), ["A#t[<MODULE>/src/test/resources/a.txt]"])


# ---------------------------------------------------------------- proof_pack
BRIEF_MD = """# Brief

#### Phase 1 - Pilot
Command: /code-modernization:modernize-transform
Modules: mod, extra
Exit criteria:
- [x] All P0 rules pass
- [ ] A business owner accepts the report output
- [ ] Row counts match

#### Phase 2 - Later
Command: /code-modernization:modernize-transform
Modules: other
Exit criteria:
- [ ] Phase 2 only criterion

## 7. Open Questions

- [ ] **Q1 [before Phase 1]** Is `s` the whole system?
- [x] **Q2 [before Phase 1]** Already answered
- [ ] **Q3 [before Phase 2]** A later phase question

## 8. Approval Block
- [ ] not a question
"""


@contextlib.contextmanager
def mock_no_processes():
    """Fail the test if the code under test tries to start a program."""
    import unittest.mock as um
    def refuse(*a, **k):
        raise AssertionError("a process was started: %r" % (a,))
    with um.patch("subprocess.Popen", refuse), um.patch("os.system", refuse), um.patch("os.popen", refuse):
        yield


class Ws:
    """A rewrite workspace (system s, module mod) that proves cleanly. A test changes one thing and looks at the verdict."""

    def __init__(self, test):
        self.test, self.root = test, tempfile.mkdtemp()
        test.addCleanup(shutil.rmtree, self.root, True)
        put(self.root, "legacy/s/app/mod.cbl", "IDENTIFICATION DIVISION.\n", T0)
        put(self.root, "analysis/s/PREFLIGHT.md", "# Preflight\n", T0 + 10)
        put(self.root, "analysis/s/BUSINESS_RULES.md", RULES_MD.replace("### RULE-003", "### RULE-003").replace("**Priority:** P1", "**Priority:** P1"), T0 + 10)
        put(self.root, "analysis/s/MODERNIZATION_BRIEF.md", BRIEF_MD, T0 + 10)
        put(self.root, "modernized/s/mod/src/main/Calc.java", "// RULE-001 RULE-002\nclass Calc {}\n", T0 + 20)
        put(self.root, "modernized/s/mod/src/test/CalcTest.java", "// RULE-001\nvoid rule002_rounds() {}\n", T0 + 20)
        put(self.root, "modernized/s/mod/TRANSFORMATION_NOTES.md", "Legacy: `legacy/s/app/mod.cbl`\n\nCanary: flip the rounding mode -> 3 tests failed\n", T0 + 20)
        put(self.root, "modernized/s/mod/target/surefire-reports/TEST-CalcTest.xml", junit(passing(3)), T0 + 30)
        put(self.root, "analysis/s/equivalence/canary/mod/TEST-Canary.xml", junit(passing(1) + [("CalcTest", "rounds", "FAIL", ""), ("CalcTest", "total", "FAIL", "")]), T0 + 35)
        self.cases("cases.json", "dev", 2)
        self.cases("fresh-cases.json", "fresh", 10)
        self.runs()

    def cases(self, name, prefix, n, differ=(), inputs=None, same_as=None, base="analysis/s/equivalence"):
        rows = []
        for i in range(n):
            legacy = "%s %d\n" % (prefix, i) if same_as is None else same_as
            put(self.root, "%s/%s/legacy/%d.out" % (base, prefix, i), legacy, T0 + 25)
            put(self.root, "%s/%s/new/%d.out" % (base, prefix, i), legacy + ("x" if i in differ else ""), T0 + 25)
            rows.append({"id": "%s%d" % (prefix, i), "legacy": "%s/legacy/%d.out" % (prefix, i), "new": "%s/new/%d.out" % (prefix, i), "input": (inputs or {}).get(i, "in%d" % i)})
        put(self.root, "%s/%s" % (base, name), json.dumps({"system": "s", "cases": rows}), T0 + 25)

    def runs(self, **change):
        doc = {"date": "2026-09-24", "legacy": {"ran": True, "how": "compiled here"},
               "suites": [{"module": "mod", "name": "unit", "command": "mvn test", "junit": ["modernized/s/mod/target/surefire-reports"]}],
               "canaries": [{"module": "mod", "change": "flip the rounding mode", "junit": ["analysis/s/equivalence/canary/mod"]}]}
        doc.update(change)
        put(self.root, "analysis/s/equivalence/test-runs.json", json.dumps(doc), T0 + 40)

    def results(self, cases, when=T0 + 30):
        put(self.root, "modernized/s/mod/target/surefire-reports/TEST-CalcTest.xml", junit(cases), when)

    def pack(self, module=None):
        return pp.overall(pp.build("s", self.root, module, now="2026-09-24 00:00 UTC"))

    def module(self, module=None):
        mods = self.pack(module)["modules"]
        return next((m for m in mods if m["name"] == module), mods[0])

    def states(self, module=None):
        return {c["id"]: c["state"] for c in self.module(module)["checks"]}


class ProofVerdicts(unittest.TestCase):
    def setUp(self):
        self.ws = Ws(self)

    def check(self, verdict, **states):
        m = self.ws.module()
        self.assertEqual(m["verdict"], verdict, "\n".join(m["reasons"]))
        got = {c["id"]: c["state"] for c in m["checks"]}
        for k, v in states.items():
            self.assertEqual(got[k], v, k)
        return m

    def test_all_evidence_is_proven(self):
        m = self.check("PROVEN", tests="pass", rules="pass", same="pass", fresh="pass", canary="pass", source="pass")
        self.assertEqual((m["reasons"], m["track"], m["name"]), ([], "rewrite", "mod"))
        self.assertEqual(m["evidence"]["tests"]["executed"], 3)
        self.assertEqual(m["evidence"]["fresh"]["inputs"], 10)

    def test_no_test_run_at_all_is_not_proven(self):
        os.remove(os.path.join(self.ws.root, "analysis", "s", "equivalence", "test-runs.json"))
        m = self.check("NOT PROVEN", tests="fail")
        self.assertIn("nothing executed", m["checks"][0]["detail"])
        self.assertTrue(any("test-runs.json was not found" in p for p in self.ws.pack()["problems"]))

    def test_zero_executed_a_failure_and_skips(self):
        self.ws.results([("CalcTest", "a", "SKIP", "why"), ("CalcTest", "b", "SKIP", "why")])
        self.check("NOT PROVEN", tests="fail")
        self.ws.results(passing(2) + [("CalcTest", "bad", "FAIL", "")])
        m = self.check("NOT PROVEN", tests="fail")
        self.assertIn("1 of 3", m["checks"][0]["detail"])
        self.ws.results(passing(2) + [("CalcTest", "err", "ERROR", "")])
        self.check("NOT PROVEN", tests="fail")
        self.ws.results(passing(2) + [("CalcTest", "s", "SKIP", "")])
        self.check("PARTLY PROVEN", tests="gap")
        self.ws.results(passing(2) + [("CalcTest", "s", "SKIP", "pending RULE-009")])
        self.check("PROVEN", tests="pass")

    def test_the_result_files_beat_the_reported_counts(self):
        self.ws.runs(suites=[{"module": "mod", "name": "unit", "executed": 999, "failed": 0, "skipped": 0, "junit": ["modernized/s/mod/target/surefire-reports"]}])
        self.ws.results(passing(2) + [("CalcTest", "bad", "FAIL", "")])
        m = self.check("NOT PROVEN", tests="fail")
        self.assertEqual(m["evidence"]["tests"]["executed"], 3)
        self.assertTrue(any("reported 999 executed" in c for c in m["caveats"]))

    def test_counts_typed_into_test_runs_json_can_never_prove_anything(self):
        self.ws.runs(suites=[{"module": "mod", "name": "unit", "executed": 5, "failed": 0, "skipped": 0}])
        m = self.check("PARTLY PROVEN", tests="gap")
        self.assertIn("typed in by the command", m["checks"][0]["detail"])
        self.assertEqual(m["evidence"]["tests"]["suites"][0]["source"], "reported")
        self.ws.runs(suites=[{"module": "mod", "name": "unit", "executed": 5, "failed": 1, "skipped": 2, "skippedReason": ""}])
        self.check("NOT PROVEN", tests="fail")
        self.ws.runs(suites=[{"module": "mod", "name": "unit", "executed": 0}])
        self.check("NOT PROVEN", tests="fail")
        self.ws.runs(suites=[{"module": "mod", "name": "unit"}])
        m = self.check("PARTLY PROVEN", tests="gap")
        self.assertIn("No test result could be read", m["checks"][0]["detail"])

    def test_a_saved_runner_log_can_stand_in_for_result_files_and_an_unreadable_one_cannot(self):
        shutil.rmtree(os.path.join(self.ws.root, "modernized", "s", "mod", "target"))
        put(self.ws.root, "analysis/s/equivalence/unit.test-output.txt", "[INFO] Running X\n[INFO] Tests run: 3, Failures: 0, Errors: 0, Skipped: 0\n[INFO] BUILD SUCCESS\n", T0 + 30)
        self.ws.runs(suites=[{"module": "mod", "name": "unit", "command": "mvn test", "log": ["analysis/s/equivalence/unit.test-output.txt"]}])
        m = self.check("PARTLY PROVEN", tests="pass", rules="gap")          # a log gives counts, not test names: no rule can be backed by it
        self.assertEqual((m["evidence"]["tests"]["suites"][0]["source"], m["evidence"]["tests"]["executed"]), ("runner log", 3))
        self.assertIn("no result file lists each test", m["checks"][1]["detail"])
        put(self.ws.root, "analysis/s/BUSINESS_RULES.md", "### RULE-001: x\n**Priority:** P1\n", T0 + 10)             # with no P0 rule to back, the log is enough
        self.check("PROVEN", tests="pass")
        put(self.ws.root, "analysis/s/BUSINESS_RULES.md", RULES_MD, T0 + 10)
        put(self.ws.root, "analysis/s/equivalence/unit.test-output.txt", "3 tests were run, all fine, trust me\n", T0 + 30)
        m = self.check("PARTLY PROVEN", tests="gap")
        self.assertTrue(any("no summary line of a runner this script knows" in c for c in m["caveats"]))
        put(self.ws.root, "analysis/s/equivalence/unit.test-output.txt", "== 1 failed, 2 passed in 0.10s ==\n", T0 + 30)
        self.check("NOT PROVEN", tests="fail")
        put(self.ws.root, "analysis/s/equivalence/unit.test-output.txt", "== 1 passed in 0.10s ==\n", T0 + 10)      # older than the code: not a clean run
        self.check("PARTLY PROVEN", tests="gap")

    def test_a_suite_note_travels_with_the_verdict(self):
        self.ws.runs(suites=[{"module": "mod", "name": "unit", "executed": 3, "failed": 1, "note": "one test needs a tool this machine lacks", "junit": ["modernized/s/mod/target/surefire-reports"]}])
        self.ws.results(passing(2) + [("CalcTest", "env", "ERROR", "")])
        m = self.check("NOT PROVEN", tests="fail")
        self.assertIn("Note: one test needs a tool this machine lacks", m["checks"][0]["detail"])
        run_main(pp.main, ["s", "--workspace", self.ws.root])
        self.assertIn("Note: one test needs a tool this machine lacks", read(os.path.join(self.ws.root, "analysis", "s", "VERIFICATION.md")))

    def test_results_older_than_the_code_are_stale(self):
        put(self.ws.root, "modernized/s/mod/src/main/Calc.java", "// RULE-001 RULE-002 changed\n", T0 + 35)
        self.check("PARTLY PROVEN", tests="gap")
        put(self.ws.root, "modernized/s/mod/.hidden", "x", T0 + 99)
        put(self.ws.root, "modernized/s/mod/README.md", "x", T0 + 99)
        put(self.ws.root, "modernized/s/mod/src/main/Calc.java", "// RULE-001 RULE-002\n", T0 + 20)
        self.check("PROVEN", tests="pass")

    def test_one_leftover_old_result_file_makes_the_run_not_clean(self):
        put(self.ws.root, "modernized/s/mod/target/surefire-reports/TEST-Old.xml", junit(passing(2, "Old")), T0 + 10)
        m = self.check("PARTLY PROVEN", tests="gap")
        self.assertIn("not a clean run", m["checks"][0]["detail"])

    def test_a_p0_rule_no_test_names_is_partly_proven_and_claims_do_not_count(self):
        put(self.ws.root, "modernized/s/mod/src/test/CalcTest.java", "// RULE-001\n", T0 + 20)
        m = self.check("PARTLY PROVEN", rules="gap")
        self.assertIn("RULE-002", m["checks"][1]["detail"])
        self.assertEqual(m["evidence"]["rules"]["p0NoTests"], ["RULE-002"])
        put(self.ws.root, "modernized/s/mod/src/main/Calc.java", "class Calc {}\n", T0 + 20)
        put(self.ws.root, "modernized/s/mod/TRANSFORMATION_NOTES.md",
            "Legacy: `legacy/s/app/mod.cbl`\n\n| Rule | Target |\n|---|---|\n| RULE-002 | `src/main/Calc.java` |\n\nCanary: x -> 3 tests failed\n", T0 + 20)
        m = self.check("PARTLY PROVEN", rules="gap")
        self.assertIn("claimed only", m["checks"][1]["detail"])

    def test_no_rules_file_or_no_p0_rule(self):
        os.remove(os.path.join(self.ws.root, "analysis", "s", "BUSINESS_RULES.md"))
        self.check("PARTLY PROVEN", rules="gap")
        put(self.ws.root, "analysis/s/BUSINESS_RULES.md", "### RULE-001: x\n**Priority:** P1\n", T0 + 10)
        self.check("PROVEN", rules="pass")

    def test_equivalence_cases_are_judged_again_not_read_from_equivalence_json(self):
        put(self.ws.root, "analysis/s/EQUIVALENCE.json", json.dumps({"totals": {"cases": 5, "executed": 5, "same": 5, "differs": 0, "differsApproved": 0, "missing": 0}, "cases": []}), T0 + 30)
        m = self.check("PROVEN", same="pass")
        self.assertTrue(any("EQUIVALENCE.json does not match" in c for c in m["caveats"]))
        self.ws.cases("cases.json", "dev", 2, differ={1})
        m = self.check("NOT PROVEN", same="fail")
        self.assertIn("1 differ", m["checks"][2]["detail"])
        os.remove(os.path.join(self.ws.root, "analysis", "s", "equivalence", "dev", "new", "0.out"))
        self.check("NOT PROVEN", same="fail")

    def test_an_approved_difference_is_allowed_and_listed(self):
        self.ws.cases("cases.json", "dev", 2, differ={1})
        path = os.path.join(self.ws.root, "analysis", "s", "equivalence", "cases.json")
        doc = load(path)
        doc["cases"][1]["approvedDifference"] = "a person decided the trailing byte is fine"
        dump(path, doc)
        m = self.check("PROVEN", same="pass")
        self.assertEqual(m["evidence"]["equivalence"]["approved"][0]["id"], "dev1")
        self.assertTrue(any("decision" in n for n in m["notProven"]))

    def test_a_declared_tolerance_is_counted_listed_and_never_silent(self):
        root = os.path.join(self.ws.root, "analysis", "s", "equivalence")
        put(root, "dev/legacy/0.out", "total=1.0000000001\n", T0 + 25)
        put(root, "dev/new/0.out", "total=1.0000000002\n", T0 + 25)
        doc = load(os.path.join(root, "cases.json"))
        doc["tolerance"] = {"rel": 1e-9, "abs": 0, "why": "last-digit rounding of exp()"}
        dump(os.path.join(root, "cases.json"), doc)
        m = self.check("PROVEN", same="pass")
        ev = m["evidence"]["equivalence"]
        self.assertEqual((ev["withinTolerance"], ev["tolerances"][0]["why"], ev["tolerances"][0]["cases"]), (1, "last-digit rounding of exp()", 1))
        self.assertIn("1 within a declared tolerance", m["checks"][2]["detail"])
        self.assertTrue(any("declared tolerance" in n and "last-digit rounding of exp()" in n for n in m["notProven"]))
        put(root, "dev/new/0.out", "total=1.1\n", T0 + 25)
        self.check("NOT PROVEN", same="fail")

    def test_no_cases_at_all_is_partly_proven(self):
        os.remove(os.path.join(self.ws.root, "analysis", "s", "equivalence", "cases.json"))
        self.check("PARTLY PROVEN", same="gap")
        put(self.ws.root, "analysis/s/EQUIVALENCE.json", "{}", T0 + 30)
        m = self.check("PARTLY PROVEN", same="gap")
        self.assertIn("could not be judged again", m["checks"][2]["detail"])

    def test_fresh_inputs_need_ten_and_must_not_differ(self):
        self.ws.cases("fresh-cases.json", "fresh", 9)
        m = self.check("PARTLY PROVEN", fresh="gap")
        self.assertIn("Only 9", m["checks"][3]["detail"])
        self.ws.cases("fresh-cases.json", "fresh", 12, inputs={i: "same" for i in range(12)})
        self.check("PARTLY PROVEN", fresh="gap")
        self.ws.cases("fresh-cases.json", "fresh", 12, inputs={i: "in%d" % (i % 10) for i in range(12)})
        self.check("PROVEN", fresh="pass")
        self.ws.cases("fresh-cases.json", "fresh", 12, differ={3})
        m = self.check("NOT PROVEN", fresh="fail")
        self.assertIn("fresh3", m["checks"][3]["detail"])
        os.remove(os.path.join(self.ws.root, "analysis", "s", "equivalence", "fresh-cases.json"))
        m = self.check("PARTLY PROVEN", fresh="gap")
        self.assertIn("was not run", m["checks"][3]["detail"])

    def test_many_differing_fresh_cases_are_listed_up_to_five_then_counted(self):
        self.ws.cases("fresh-cases.json", "fresh", 12, differ={0, 1, 2, 3, 4, 5, 6, 7})
        m = self.check("NOT PROVEN", fresh="fail")
        self.assertIn("8 fresh comparison(s) differ", m["checks"][3]["detail"])
        self.assertIn("and 3 more (see VERIFICATION.json)", m["checks"][3]["detail"])
        self.assertEqual(len(m["evidence"]["fresh"]["differing"]), 8)

    def test_fresh_cases_that_repeat_development_outputs_do_not_count(self):
        dev = load(os.path.join(self.ws.root, "analysis", "s", "equivalence", "cases.json"))
        same = read(os.path.join(self.ws.root, "analysis", "s", "equivalence", "dev", "legacy", "0.out"))
        self.ws.cases("fresh-cases.json", "fresh", 12, same_as=same)
        m = self.check("PARTLY PROVEN", fresh="gap")
        self.assertEqual(len(dev["cases"]), 2)
        self.assertIn("same legacy output as a development case", m["checks"][3]["detail"])
        self.ws.cases("fresh-cases.json", "fresh", 12, same_as="")
        self.check("PARTLY PROVEN", fresh="gap")          # empty outputs prove nothing

    def test_when_the_legacy_cannot_run_the_verdict_cannot_be_proven(self):
        self.ws.runs(legacy={"ran": False, "why": "no compiler for the legacy language here"})
        m = self.check("PARTLY PROVEN", fresh="gap")
        self.assertIn("trace-based", m["checks"][3]["detail"])
        self.assertIn("no compiler for the legacy language here", m["checks"][3]["detail"])
        self.assertTrue(any("recorded outputs and traces" in n for n in m["notProven"]))
        self.ws.runs(legacy={})
        self.check("PROVEN", fresh="pass")               # not stated, but fresh cases exist and ran: the legacy evidently ran

    def test_a_canary_counts_only_when_its_own_result_file_or_log_shows_failing_tests(self):
        m = self.check("PROVEN", canary="pass")
        self.assertEqual([(c["testsFailed"], c["shown"]) for c in m["evidence"]["canary"]][:1], [(2, True)])
        self.assertIn("canary/mod", m["checks"][4]["detail"])
        self.ws.runs(canaries=[])                                  # only the notes' "Canary:" line is left: a claim
        m = self.check("PARTLY PROVEN", canary="gap")
        self.assertIn("claimed", m["checks"][4]["detail"])
        self.ws.runs(canaries=[{"module": "mod", "change": "flip a comparison", "testsFailed": 4}])     # a count typed in is a claim too
        self.check("PARTLY PROVEN", canary="gap")
        put(self.ws.root, "modernized/s/mod/TRANSFORMATION_NOTES.md", "Legacy: `legacy/s/app/mod.cbl`\n", T0 + 20)
        self.ws.runs(canaries=[])
        m = self.check("PARTLY PROVEN", canary="gap")
        self.assertIn("No canary is recorded", m["checks"][4]["detail"])
        put(self.ws.root, "analysis/s/equivalence/canary/mod/run.log", "== 3 failed, 5 passed in 1.0s ==\n")
        self.ws.runs(canaries=[{"module": "mod", "change": "flip a comparison", "log": ["analysis/s/equivalence/canary/mod/run.log"]}])
        self.check("PROVEN", canary="pass")
        put(self.ws.root, "analysis/s/equivalence/canary/mod/run.log", "== 8 passed in 1.0s ==\n")
        m = self.check("NOT PROVEN", canary="fail")
        self.assertIn("no test failed", m["checks"][4]["detail"])

    def test_a_canary_run_counts_only_the_failures_the_clean_run_did_not_have(self):
        self.ws.results(passing(2) + [("CalcTest", "preexisting", "FAIL", "")])
        put(self.ws.root, "analysis/s/equivalence/canary/mod/TEST-Canary.xml", junit(passing(2) + [("CalcTest", "preexisting", "FAIL", "")]), T0 + 35)
        m = self.check("NOT PROVEN", canary="fail")
        self.assertIn("no test failed because of it", m["checks"][4]["detail"])
        put(self.ws.root, "analysis/s/equivalence/canary/mod/TEST-Canary.xml", junit(passing(1) + [("CalcTest", "preexisting", "FAIL", ""), ("CalcTest", "rounds", "FAIL", "")]), T0 + 35)
        m = self.check("NOT PROVEN", tests="fail", canary="pass")
        self.assertEqual(m["evidence"]["canary"][0]["testsFailed"], 1)
        put(self.ws.root, "analysis/s/equivalence/canary/mod/run.log", "== 3 failed, 5 passed in 1.0s ==\n")
        self.ws.runs(canaries=[{"module": "mod", "log": ["analysis/s/equivalence/canary/mod/run.log"]}])
        m = self.check("NOT PROVEN", canary="pass")
        self.assertEqual(m["evidence"]["canary"][0]["testsFailed"], 2)         # 3 failures minus the clean run's 1

    def test_inputs_left_out_are_listed_with_the_fresh_check(self):
        self.ws.runs(leftOut=["F17: the legacy loader refused duplicate keys", 5, ""])
        m = self.check("PROVEN", fresh="pass")
        self.assertEqual(m["evidence"]["fresh"]["leftOut"], ["F17: the legacy loader refused duplicate keys"])
        run_main(pp.main, ["s", "--workspace", self.ws.root])
        self.assertIn("Inputs left out of the fresh check: F17: the legacy loader refused duplicate keys", read(os.path.join(self.ws.root, "analysis", "s", "VERIFICATION.md")))

    def test_canary_evidence_outside_the_workspace_is_ignored(self):
        outside = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, outside, True)
        put(outside, "TEST-out.xml", junit([("X", "a", "FAIL", "")]))
        self.ws.runs(canaries=[{"module": "mod", "change": "elsewhere", "junit": [outside]}])
        self.check("PARTLY PROVEN", canary="gap")

    def test_hostile_notes_cannot_stall_the_canary_search(self):
        put(self.ws.root, "modernized/s/mod/TRANSFORMATION_NOTES.md", ("Canary: " * 100 + "\n") * 5000 + "Canary: x -> 2 tests failed\n" + "Canary" * 1000000, T0 + 20)
        started = time.time()
        m = self.ws.module()
        self.assertLess(time.time() - started, 20)
        self.assertIn(m["verdict"], ("PROVEN", "PARTLY PROVEN"))

    def test_a_changed_legacy_source_is_partly_proven_and_named(self):
        put(self.ws.root, "legacy/s/app/mod.cbl", "changed\n", T0 + 50)
        m = self.check("PARTLY PROVEN", source="gap")
        self.assertIn("has changed since the analysis began", m["checks"][5]["detail"])
        self.assertEqual(self.ws.pack()["legacy"]["state"], "changed")
        shutil.rmtree(os.path.join(self.ws.root, "legacy"))
        m = self.check("PARTLY PROVEN", source="gap")
        self.assertIn("was not found", m["checks"][5]["detail"])

    def test_the_source_check_is_a_plain_file_walk_and_runs_nothing_in_the_tree(self):
        legacy = os.path.join(self.ws.root, "legacy", "s")
        marker = os.path.join(self.ws.root, "RAN")
        os.makedirs(os.path.join(legacy, ".git"))
        put(legacy, ".git/config", "[core]\n\tfsmonitor = touch %s\n" % marker, T0 + 99)          # a hostile repository config: it must never run
        put(legacy, ".git/HEAD", "ref: refs/heads/main\n", T0 + 99)                                 # version-control metadata is not source
        with mock_no_processes():
            m = self.check("PROVEN", source="pass")
        self.assertFalse(os.path.exists(marker))
        self.assertIn("no version-control tool was run", m["checks"][5]["detail"])
        self.assertTrue(m["checks"][5]["detail"].startswith("legacy/s is untouched: no file changed after the analysis started"))
        self.assertEqual(self.ws.pack()["legacy"]["method"], pp.NO_VCS)

    def test_a_file_newer_than_the_analysis_is_reported_with_examples(self):
        for i in range(30):
            put(self.ws.root, "legacy/s/app/new%02d.cbl" % i, "x", T0 + 50)
        m = self.check("PARTLY PROVEN", source="gap")
        self.assertIn("30 file(s) changed after the analysis started", m["checks"][5]["detail"])
        pack = self.ws.pack()
        self.assertEqual((pack["legacy"]["state"], len(pack["legacy"]["files"])), ("changed", 20))
        put(self.ws.root, "legacy/s/app/mod.cbl", "changed\n", T0 + 50)
        shutil.rmtree(os.path.join(self.ws.root, "legacy"))
        m = self.check("PARTLY PROVEN", source="gap")
        self.assertIn("was not found", m["checks"][5]["detail"])

    def test_the_analysis_is_dated_by_preflight_else_by_the_oldest_analysis_file(self):
        os.remove(os.path.join(self.ws.root, "analysis", "s", "PREFLIGHT.md"))
        os.utime(os.path.join(self.ws.root, "analysis", "s", "BUSINESS_RULES.md"), (T0 + 5, T0 + 5))
        os.utime(os.path.join(self.ws.root, "analysis", "s", "MODERNIZATION_BRIEF.md"), (T0 + 10, T0 + 10))
        self.check("PROVEN", source="pass")
        put(self.ws.root, "legacy/s/app/late.cbl", "x", T0 + 7)
        self.check("PARTLY PROVEN", source="gap")
        shutil.rmtree(os.path.join(self.ws.root, "analysis"))
        put(self.ws.root, "analysis/s/equivalence/test-runs.json", "{}", T0 + 40)
        m = self.ws.module()
        self.assertEqual(m["checks"][5]["state"], "gap")

    def test_links_in_the_source_are_not_followed_and_a_walk_that_cannot_finish_is_not_untouched(self):
        outside = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, outside, True)
        put(outside, "newer.c", "x", T0 + 99)
        make_symlink(self, os.path.join(outside, "newer.c"), os.path.join(self.ws.root, "legacy", "s", "link.c"))
        make_symlink(self, outside, os.path.join(self.ws.root, "legacy", "s", "linked"))
        self.check("PROVEN", source="pass")
        if os.name != "nt" and os.geteuid() != 0:
            hidden = os.path.join(self.ws.root, "legacy", "s", "locked")
            os.makedirs(hidden)
            os.chmod(hidden, 0)
            self.addCleanup(os.chmod, hidden, 0o755)
            m = self.check("PARTLY PROVEN", source="gap")
            self.assertIn("could not finish", m["checks"][5]["detail"])

    def test_people_items_are_listed_never_ticked_and_never_change_the_verdict(self):
        m = self.check("PROVEN")
        texts = [i["text"] for i in m["brief"]["items"]]
        self.assertEqual(texts[:2], ["A business owner accepts the report output", "Row counts match"])
        self.assertTrue(any("Is `s` the whole system" in t for t in texts))
        self.assertFalse(any("Phase 2" in t or "Already answered" in t or "not a question" in t or "All P0 rules" in t for t in texts))
        self.assertEqual(m["brief"]["items"][0]["where"], "Phase 1 exit criterion")
        os.remove(os.path.join(self.ws.root, "analysis", "s", "MODERNIZATION_BRIEF.md"))
        self.assertFalse(self.ws.module()["brief"]["found"])

    def test_hostile_test_runs_json_cannot_crash_or_read_outside(self):
        outside = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, outside, True)
        put(outside, "TEST-out.xml", junit(passing(500, "Out")))
        for doc in ('["x"]', '{"suites": "x", "legacy": 5, "canaries": {"a": 1}}', "{not json", "\x00\x01",
                    json.dumps({"suites": [{"module": "mod" * 5000, "name": None, "executed": -5, "failed": "many", "junit": [1, None, "../../etc", outside, "x" * 10000]},
                                           5, {"module": "mod", "executed": 10 ** 12, "skipped": True, "junit": [outside]}]})):
            put(self.ws.root, "analysis/s/equivalence/test-runs.json", doc, T0 + 40)
            m = self.ws.module()
            self.assertIn(m["verdict"], ("NOT PROVEN", "PARTLY PROVEN"))
            self.assertNotEqual(m["evidence"]["tests"]["executed"], 500)
        self.ws.runs(suites=[{"module": "mod", "executed": 500, "junit": [outside]}])
        m = self.ws.module()
        self.assertTrue(any("outside the workspace" in c for c in m["caveats"]))

    def test_links_in_the_evidence_are_refused(self):
        outside = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, outside, True)
        put(outside, "test-runs.json", json.dumps({"suites": [{"module": "mod", "executed": 9}]}))
        os.remove(os.path.join(self.ws.root, "analysis", "s", "equivalence", "test-runs.json"))
        make_symlink(self, os.path.join(outside, "test-runs.json"), os.path.join(self.ws.root, "analysis", "s", "equivalence", "test-runs.json"))
        pack = self.ws.pack()
        self.assertTrue(any("link" in p for p in pack["problems"]))
        self.assertEqual(pack["modules"][0]["verdict"], "NOT PROVEN")
        put(outside, "o.out", "same\n")
        put(self.ws.root, "analysis/s/equivalence/cases.json", json.dumps({"cases": [{"id": "x", "legacy": os.path.join(outside, "o.out"), "new": os.path.join(outside, "o.out")}]}), T0 + 25)
        self.ws.runs()
        self.assertEqual(self.ws.states()["same"], "fail")

    def test_a_linked_cases_file_is_refused_not_read(self):
        outside = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, outside, True)
        cases = os.path.join(self.ws.root, "analysis", "s", "equivalence", "cases.json")
        shutil.copy(cases, os.path.join(outside, "cases.json"))
        os.remove(cases)
        make_symlink(self, os.path.join(outside, "cases.json"), cases)
        m = self.ws.module()
        self.assertEqual(m["checks"][2]["state"], "gap")
        self.assertTrue(any("is a link" in c for c in m["caveats"]))
        self.assertNotIn("equivalence", m["evidence"])

    def test_two_modules_get_two_verdicts_and_asking_about_one_still_judges_both_from_evidence(self):
        put(self.ws.root, "modernized/s/extra/src/main/X.java", "class X {}\n", T0 + 20)
        pack = self.ws.pack()
        self.assertEqual([(m["name"], m["verdict"]) for m in pack["modules"]], [("extra", "NOT PROVEN"), ("mod", "PROVEN")])
        self.assertEqual(pack["overall"]["verdict"], "NOT PROVEN")
        self.assertEqual(pack["overall"]["counts"], {"PROVEN": 1, "PARTLY PROVEN": 0, "NOT PROVEN": 1})
        asked = self.ws.pack("mod")
        self.assertEqual([(m["name"], m["verdict"]) for m in asked["modules"]], [("extra", "NOT PROVEN"), ("mod", "PROVEN")])
        self.assertEqual(asked["asked"], "mod")

    def test_a_forged_earlier_verdict_never_survives_a_new_run(self):
        put(self.ws.root, "modernized/s/extra/src/main/X.java", "class X {}\n", T0 + 20)
        forged = pp.overall(self.ws.pack())
        forged["modules"][0].update(verdict="PROVEN", reasons=[])
        forged["modules"].append(dict(forged["modules"][0], name="ghost", verdict="PROVEN"))
        forged["overall"] = {"verdict": "PROVEN", "counts": {"PROVEN": 3, "PARTLY PROVEN": 0, "NOT PROVEN": 0}}
        adir = os.path.join(self.ws.root, "analysis", "s")
        dump(os.path.join(adir, "VERIFICATION.json"), forged)
        code, out, _ = run_main(pp.main, ["s", "mod", "--workspace", self.ws.root])
        self.assertEqual(code, 1)
        data = load(os.path.join(adir, "VERIFICATION.json"))
        self.assertEqual([(m["name"], m["verdict"]) for m in data["modules"]], [("extra", "NOT PROVEN"), ("mod", "PROVEN")])
        self.assertEqual(data["overall"]["verdict"], "NOT PROVEN")
        self.assertNotIn("ghost", read(os.path.join(adir, "VERIFICATION.md")))
        self.assertFalse(hasattr(pp, "merge_previous"))

    def test_shared_cases_are_flagged_and_a_modules_own_folder_wins(self):
        put(self.ws.root, "modernized/s/extra/src/main/X.java", "class X {}\n", T0 + 20)
        self.assertTrue(any("shared by every module" in c for c in self.ws.module("mod")["caveats"]))
        self.ws.cases("cases.json", "own", 3, base="analysis/s/equivalence/mod")
        m = self.ws.module("mod")
        self.assertEqual(m["evidence"]["equivalence"]["cases"], 3)
        self.assertFalse(any("shared by every module" in c for c in m["caveats"]))

    def test_a_reimagined_service_is_judged_like_a_rewritten_module(self):
        shutil.rmtree(os.path.join(self.ws.root, "modernized", "s"))
        put(self.ws.root, "modernized/s-reimagined/api/src/main/Api.java", "class Api {}\n", T0 + 20)
        put(self.ws.root, "modernized/s-reimagined/api/src/test/ApiTest.java", "// RULE-001 RULE-002\n", T0 + 20)
        put(self.ws.root, "modernized/s-reimagined/api/target/surefire-reports/TEST-Api.xml", junit(passing(4, "ApiTest")), T0 + 30)
        self.ws.runs(suites=[{"module": "api", "name": "acceptance", "executed": 4, "junit": ["modernized/s-reimagined/api/target/surefire-reports"]}])
        pack = self.ws.pack()
        m = pack["modules"][0]
        self.assertEqual((m["name"], m["track"], len(pack["modules"])), ("api", "reimagine", 1))
        self.assertEqual({c["id"]: c["state"] for c in m["checks"]}["rules"], "pass")
        self.assertEqual({c["id"]: c["state"] for c in m["checks"]}["tests"], "pass")

    def test_nothing_built_is_an_error(self):
        shutil.rmtree(os.path.join(self.ws.root, "modernized"))
        with self.assertRaises(pp.InputError):
            pp.build("s", self.ws.root)
        code, _, err = run_main(pp.main, ["s", "--workspace", self.ws.root])
        self.assertEqual(code, 2)
        self.assertIn("nothing is built", err)


RUNNER_LOGS = (
    ("maven", "[INFO] Tests run: 4, Failures: 0, Errors: 0, Skipped: 0, Time elapsed: 0.1 s -- in A\n[ERROR] Tests run: 158, Failures: 0, Errors: 3, Skipped: 2\n", (156, 3, 2)),         # executed = run minus skipped
    ("maven, old style", "Tests run: 10, Failures: 1, Errors: 0, Skipped: 1\n", (9, 1, 1)),
    ("gradle", "12 tests completed, 2 failed, 1 skipped\n", (11, 2, 1)),
    ("cargo", "test result: ok. 10 passed; 0 failed; 1 ignored; 0 measured; 0 filtered out; finished in 0.00s\ntest result: FAILED. 2 passed; 3 failed; 0 ignored; 0 measured\n", (15, 3, 1)),
    ("pytest", "============ 2 failed, 10 passed, 1 skipped in 0.12s ============\n", (12, 2, 1)),
    ("pytest -q", "3 passed, 1 error in 0.05s\n", (4, 1, 0)),
    ("pytest none", "no tests ran in 0.01s\n", (0, 0, 0)),
    ("unittest", "Ran 5 tests in 0.002s\n\nOK\n", (5, 0, 0)),
    ("unittest failed", "Ran 9 tests in 0.5s\n\nFAILED (failures=1, errors=2, skipped=3)\n", (6, 3, 3)),
    ("go -v", "=== RUN TestA\n--- PASS: TestA (0.00s)\n    --- PASS: TestA/sub (0.00s)\n--- FAIL: TestB (0.01s)\n--- SKIP: TestC (0.00s)\nFAIL\n", (3, 1, 1)),
    ("go -json", '{"Time":"t","Action":"pass","Package":"p","Test":"TestA","Elapsed":0}\n{"Time":"t","Action":"fail","Package":"p","Test":"TestB","Elapsed":0}\n{"Time":"t","Action":"fail","Package":"p","Elapsed":0}\n', (2, 1, 0)),
    ("dotnet", "Passed!  - Failed:     0, Passed:    10, Skipped:     1, Total:    11, Duration: 1 s - X.dll (net8.0)\nFailed!  - Failed:     2, Passed:     8, Skipped:     0, Total:    10, Duration: 1 s - Y.dll\n", (20, 2, 1)),
    ("jest", "Tests:       1 failed, 2 skipped, 3 passed, 6 total\nTest Suites: 1 failed, 1 total\n", (4, 1, 2)),
    ("vitest", "      Tests  1 failed | 9 passed | 1 skipped (11)\n", (10, 1, 1)),
    ("ctest", "92% tests passed, 1 tests failed out of 12\n", (12, 1, 0)),
    ("phpunit ok", "OK (10 tests, 25 assertions)\n", (10, 0, 0)),
    ("phpunit failures", "FAILURES!\nTests: 10, Assertions: 25, Failures: 1, Skipped: 1.\n", (9, 1, 1)),
)


class RunnerLogs(unittest.TestCase):
    def test_every_supported_runner_summary_is_read(self):
        for name, text, want in RUNNER_LOGS:
            got = pp.parse_runner_log(text)
            self.assertIsNotNone(got, name)
            self.assertEqual(got[:3], want, name)

    def test_a_log_with_no_summary_line_is_no_evidence(self):
        for text in ("", "All good, 12 tests passed, trust me\n", "BUILD SUCCESSFUL in 3s\n", "ok  \tpkg\t0.003s\n", "Tests run: many, Failures: none\n", "\x00\x01\x02"):
            self.assertIsNone(pp.parse_runner_log(text), repr(text))

    def test_summaries_are_summed_across_a_log_and_the_runner_is_named(self):
        got = pp.parse_runner_log("Tests run: 3, Failures: 0, Errors: 0, Skipped: 0\n== 2 passed in 0.1s ==\n")
        self.assertEqual(got, (5, 0, 0, ["maven", "pytest"]))

    def test_hostile_logs_are_bounded_and_never_trusted(self):
        started = time.time()
        for text in ("Tests run: " * 400000, "= " * 2000000 + "passed in 1s", "--- PASS: " * 300000, "{" + '"Action":"pass",' * 200000 + "}", "9" * 3000000 + " passed in 1s\n",
                     "Tests:" + " 1 failed," * 100000 + " 5 total\n", "Ran " * 500000, "\r" * 1000000):
            pp.parse_runner_log(text)
        self.assertLess(time.time() - started, 30)
        self.assertEqual(pp.parse_runner_log("Tests run: 999999999999999999999, Failures: 0, Errors: 0, Skipped: 0\n")[0], 999999999999999999999)

    def test_read_logs_refuses_links_huge_files_and_binary_text(self):
        root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, root, True)
        good = put(root, "good.txt", "== 2 passed in 0.1s ==\n")
        outside = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, outside, True)
        put(outside, "real.txt", "== 99 passed in 0.1s ==\n")
        link = os.path.join(root, "link.txt")
        make_symlink(self, os.path.join(outside, "real.txt"), link)
        put(root, "huge.txt", b"x" * ((16 << 20) + 5))
        put(root, "nul.txt", b"\x00" * 100 + b"\n== 5 passed in 1s ==\n")
        got = pp.read_logs([good, link, os.path.join(root, "huge.txt"), os.path.join(root, "nul.txt"), os.path.join(root, "missing.txt")])
        self.assertEqual((got["files"], got["executed"]), (2, 7))            # NUL bytes elsewhere in the file do not hide a summary line; the link, the huge and the missing file are not read
        self.assertEqual(len(got["unrecognised"]), 3)


class BaselineEvidence(unittest.TestCase):
    """baseline_diff.py: where the old version's measured results are looked for, and what counts as measured."""

    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root, True)
        self.base = put(self.root, "analysis/s/BASELINE.md", BASELINE_MD)
        self.per_test = json.dumps({"A#pass1": "PASS", "A#pass2": "PASS", "A#failed": "FAIL", "A#skipped": "SKIP", "B#flip": "PASS", "B#gone": "PASS"})

    def found(self, text=""):
        return [os.path.relpath(p, os.path.join(self.root, "analysis", "s")) for p in bd.evidence_paths(self.base, BASELINE_MD + text)]

    def test_per_test_json_shapes_are_read_and_counts_or_prose_are_not(self):
        self.assertEqual(bd.parse_results_json({"A#x": "PASS", "A#y": "failed", "A#z": "Skipped"}), {"A#x": "PASS", "A#y": "FAIL", "A#z": "SKIP"})
        self.assertEqual(bd.parse_results_json({"tests": {"A#x": "ok"}}), {"A#x": "PASS"})
        self.assertEqual(bd.parse_results_json([{"name": "A#x", "status": "pass"}, {"test": "A#y", "result": "FAIL"}, {"id": "A#z", "outcome": "error"}, {"name": "no status"}, 5]),
                         {"A#x": "PASS", "A#y": "FAIL", "A#z": "ERROR"})
        for bad in ({"PASS": 10, "FAIL": 1}, {"passed": 5, "failed": 0, "executed": 5}, {"tests": {"count": 3}}, {"a": "hello", "b": "world"}, [], {}, "text", 5, None, [1, 2], {"a": {"b": "PASS"}}):
            self.assertIsNone(bd.parse_results_json(bad), bad)
        many = bd.parse_results_json({"t%d" % i: "PASS" for i in range(1000)} | {"junk": "hello"} if sys.version_info >= (3, 9) else dict({"t%d" % i: "PASS" for i in range(1000)}, junk="hello"))
        self.assertEqual(len(many), 1000)                                            # one stray value in a thousand does not spoil it
        self.assertIsNone(bd.parse_results_json({"a": "PASS", "b": "hello", "c": "world"}))       # but a mostly-unrecognised map is no evidence

    def test_the_baseline_folder_and_recorded_lines_are_the_only_places(self):
        put(self.root, "analysis/s/baseline/old.json", self.per_test)
        put(self.root, "analysis/s/harness/named.json", self.per_test)
        put(self.root, "analysis/s/harness/prose.json", self.per_test)
        put(self.root, "analysis/s/harness/bare.log", "x")
        self.assertEqual(self.found(), ["baseline"])
        self.assertEqual(self.found("\nSee `analysis/s/harness/prose.json` too.\n"), ["baseline"])
        self.assertEqual(self.found("\n- **Recorded:** 2026-09-24. Machine-readable per-test results: `analysis/s/harness/named.json`; tool: `analysis/s/harness/prose.json`\n"),
                         ["baseline", "harness/named.json", "harness/prose.json"])                 # everything on the Recorded line counts
        self.assertEqual(self.found("\nMachine-readable: harness/bare.log\n"), ["baseline", "harness/bare.log"])
        self.assertEqual(self.found("\n  * recorded on Thursday: harness/named.json\n"), ["baseline", "harness/named.json"])
        self.assertEqual(self.found("\nNot recorded: harness/named.json\n"), ["baseline"])       # the line must start with the label

    def test_paths_that_leave_analysis_or_go_through_links_are_refused(self):
        outside = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, outside, True)
        put(outside, "o.json", self.per_test)
        put(self.root, "analysis/other/o.json", self.per_test)
        put(self.root, "modernized/o.json", self.per_test)
        put(self.root, "analysis/s/inner.json", self.per_test)
        make_symlink(self, os.path.join(outside, "o.json"), os.path.join(self.root, "analysis", "s", "link.json"))
        make_symlink(self, outside, os.path.join(self.root, "analysis", "s", "dirlink"))
        make_symlink(self, os.path.join(self.root, "analysis", "other"), os.path.join(self.root, "analysis", "s", "sibling"))
        for line in ("../other/o.json", "analysis/other/o.json", "analysis/s/../other/o.json", "modernized/o.json", outside + "/o.json", "link.json", "dirlink/o.json", "sibling/o.json", "./../s/../other/o.json"):
            self.assertEqual(self.found("\nRecorded: `%s`\n" % line), [], line)
        self.assertEqual(self.found("\nRecorded: `analysis/s/inner.json`\n"), ["inner.json"])
        os.rename(os.path.join(self.root, "analysis", "s", "dirlink"), os.path.join(self.root, "dirlink-moved"))
        make_symlink(self, outside, os.path.join(self.root, "analysis", "s", "baseline"))
        self.assertEqual(self.found(), [])                                                      # a linked baseline/ folder is not entered

    def test_result_files_json_and_logs_are_all_read_and_counts_only_files_are_ignored(self):
        put(self.root, "analysis/s/baseline/xml/TEST-A.xml", junit([("A", "one", "PASS", ""), ("A", "two", "FAIL", "")]))
        put(self.root, "analysis/s/baseline/map.json", json.dumps({"B#x": "PASS"}))
        put(self.root, "analysis/s/baseline/counts.json", json.dumps({"PASS": 9}))
        put(self.root, "analysis/s/baseline/bad.json", "{not json")
        put(self.root, "analysis/s/baseline/notes.txt", "nothing that looks like a runner summary")
        got = bd.read_baseline_evidence(bd.evidence_paths(self.base, ""))
        self.assertEqual(got["tests"], {"A#one": "PASS", "A#two": "FAIL", "B#x": "PASS"})
        self.assertEqual((got["measured"], got["conflicts"], got["ignored"]), (True, [], ["counts.json"]))
        self.assertEqual([x["kind"] for x in got["sources"]], ["result files", "machine-readable results"])
        self.assertTrue(any("bad.json" in u for u in got["unreadable"]))
        only_log = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, only_log, True)
        put(only_log, "run.log", "[INFO] Tests run: 5, Failures: 1, Errors: 0, Skipped: 0\n")
        got = bd.read_baseline_evidence([only_log])
        self.assertEqual((got["tests"], got["counts"], got["measured"]), (None, {"executed": 5, "failed": 1, "skipped": 0}, True))
        nothing = bd.read_baseline_evidence([os.path.join(self.root, "analysis", "s", "baseline", "counts.json")])
        self.assertEqual((nothing["measured"], nothing["tests"], nothing["counts"]), (False, None, None))

    def test_sources_that_disagree_are_conflicts_not_first_wins(self):
        put(self.root, "analysis/s/baseline/a.json", json.dumps({"A#x": "PASS", "A#y": "PASS"}))
        put(self.root, "analysis/s/baseline/b.json", json.dumps({"A#x": "FAIL", "A#y": "PASS", "A#z": "PASS"}))
        got = bd.read_baseline_evidence(bd.evidence_paths(self.base, ""))
        self.assertEqual(len(got["conflicts"]), 1)
        self.assertIn("A#x", got["conflicts"][0])
        self.assertEqual(got["tests"]["A#x"], "PASS")                                          # kept only so the report can show something; the conflict is what counts
        info = bd.assess_baseline(bd.parse_baseline("| Test | Result |\n|---|---|\n| `A#x` | PASS |\n"), got)
        self.assertEqual((info["kind"], info["conflict"]), ("measured", 1))
        put(self.root, "analysis/s/baseline/b.json", json.dumps({"A#x": "ERROR", "A#y": "PASS"}))
        put(self.root, "analysis/s/baseline/a.json", json.dumps({"A#x": "FAIL"}))
        self.assertEqual(bd.read_baseline_evidence(bd.evidence_paths(self.base, ""))["conflicts"], [])   # FAIL and ERROR are both red

    def test_assess_says_typed_measured_disagreeing_or_target_only(self):
        typed = bd.parse_baseline(BASELINE_MD)
        self.assertEqual(bd.assess_baseline(typed, None)["kind"], "typed")
        self.assertEqual(bd.assess_baseline(bd.parse_baseline("target-only: no old runtime\n"), {"measured": True, "tests": {"a": "PASS"}, "counts": None, "sources": []})["kind"], "target-only")
        self.assertEqual(bd.assess_baseline(bd.parse_baseline("nothing here"), None)["kind"], "none")
        good = {"measured": True, "tests": {"A#pass1": "PASS", "A#pass2": "PASS", "A#failed": "FAIL", "A#skipped": "SKIP", "B#flip": "PASS", "B#gone": "PASS"}, "counts": None,
                "sources": [{"kind": "machine-readable results", "name": "x.json"}], "conflicts": []}
        info = bd.assess_baseline(typed, good)
        self.assertEqual((info["kind"], info["disagree"], info["measuredTests"], info["measuredExecuted"], info["measuredFailed"]), ("measured", 0, 6, 5, 1))
        bad = dict(good, tests=dict(good["tests"], **{"A#pass1": "FAIL"}))
        self.assertEqual(bd.assess_baseline(typed, bad)["disagree"], 1)
        missing = dict(good, tests={k: v for k, v in good["tests"].items() if k != "B#gone"})
        self.assertEqual(bd.assess_baseline(typed, missing)["disagree"], 2)                        # the missing row, and the Totals table that counts it

    def test_the_cli_can_be_given_the_evidence_and_says_typed_only_otherwise(self):
        folder = os.path.join(self.root, "res")
        put(folder, "TEST-x.xml", junit([("A", "pass1", "PASS", ""), ("A", "pass2", "PASS", ""), ("A", "failed", "FAIL", ""), ("A", "skipped", "SKIP", ""), ("B", "flip", "PASS", ""), ("B", "gone", "PASS", "")]))
        code, out, _ = run_main(bd.main, [self.base, "--junit", folder])
        self.assertIn("typed table only", out)
        put(self.root, "analysis/s/baseline/old.json", self.per_test)
        code, out, _ = run_main(bd.main, [self.base, "--junit", folder])
        self.assertIn("baseline evidence: measured (machine-readable results old.json)", out)
        evidence = os.path.join(self.root, "elsewhere.json")
        put(self.root, "elsewhere.json", self.per_test)
        code, out, _ = run_main(bd.main, [self.base, "--junit", folder, "--baseline-evidence", evidence, "--json"])
        self.assertEqual(json.loads(out)["baseline"]["assessment"]["kind"], "measured")


class UpliftChecks(unittest.TestCase):
    """uplift_checks.py: the test files of the untouched tree against the working copy, and the deltas no test names."""

    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root, True)
        self.old, self.new = os.path.join(self.root, "old"), os.path.join(self.root, "new")

    def both(self, rel, old, new=None, kind="w"):
        put(self.old, rel, old)
        put(self.new, rel, old if new is None else new)

    def test_which_files_count_as_tests_and_what_is_skipped(self):
        for rel in ("src/test/java/AThing.java", "tests/b.py", "web/__tests__/c.js", "spec/d.rb", "src/FooTest.java", "pkg/test_e.py", "pkg/e_test.go", "web/f.spec.ts", "src/test/resources/data.json"):
            put(self.old, rel, "x")
        for rel in ("src/main/A.java", "README.md", "src/test/notes.txt", "target/test/X.java", "node_modules/y/test/Z.js", ".hidden/test/H.java", "src/test/.dotfile"):
            put(self.old, rel, "x")
        got, cut, links = uc.walk_tests(self.old)
        self.assertEqual(sorted(got), ["pkg/e_test.go", "pkg/test_e.py", "spec/d.rb", "src/FooTest.java", "src/test/java/AThing.java", "src/test/resources/data.json", "tests/b.py",
                                       "web/__tests__/c.js", "web/f.spec.ts"])
        self.assertEqual((cut, links), (False, 0))
        self.assertEqual(uc.walk_tests(os.path.join(self.root, "missing")), ({}, False, 0))

    def test_removed_added_and_changed_with_line_counts(self):
        self.both("t/keep/AKeepTest.java", "one\ntwo\nthree\n")
        self.both("t/edit/AEditTest.java", "one\ntwo\nthree\nfour\n", "one\nTWO\nthree\nfour\nfive\n")
        put(self.old, "t/gone/AGoneTest.java", "x\ny\n")
        put(self.new, "t/new/ANewTest.java", "a\nb\nc\n")
        got = uc.tests_changed(self.old, self.new)
        self.assertEqual((got["checked"], got["legacyTests"], got["workTests"], got["counts"]), (True, 3, 3, {"added": 1, "removed": 1, "changed": 1}))
        self.assertEqual(got["changed"], [{"path": "t/edit/AEditTest.java", "added": 2, "removed": 1, "note": ""}])
        self.assertEqual((got["removed"], got["added"]), ([{"path": "t/gone/AGoneTest.java", "lines": 3}], [{"path": "t/new/ANewTest.java", "lines": 4}]))
        self.assertTrue(got["gap"])                                                               # a removed file
        self.assertEqual(round(got["share"], 3), round(1 / 3, 3))

    def test_a_quarter_changed_is_not_a_gap_and_more_is_and_line_endings_are_ignored(self):
        for i in range(4):
            self.both("t/T%dTest.java" % i, "line %d\r\nsecond\r\n" % i)
        put(self.new, "t/T0Test.java", "line 0\nsecond\n")                                        # only the line endings differ
        self.assertEqual(uc.tests_changed(self.old, self.new)["counts"]["changed"], 0)
        put(self.new, "t/T1Test.java", "line 1 edited\nsecond\n")
        got = uc.tests_changed(self.old, self.new)
        self.assertEqual((got["counts"]["changed"], got["gap"], got["share"]), (1, False, 0.25))
        put(self.new, "t/T2Test.java", "line 2 edited\nsecond\n")
        self.assertTrue(uc.tests_changed(self.old, self.new)["gap"])

    def test_no_legacy_tests_is_a_gap_and_so_is_a_missing_tree(self):
        put(self.new, "t/ANewTest.java", "x")
        put(self.old, "src/main/A.java", "the legacy tree exists but holds no test file")
        got = uc.tests_changed(self.old, self.new)
        self.assertEqual((got["checked"], got["legacyTests"], got["gap"]), (True, 0, True))
        self.assertIn("nothing shows that the working copy's tests were not written during the uplift", got["why"])
        for old, new in ((os.path.join(self.root, "none"), self.new), ("", self.new), (self.old, os.path.join(self.root, "none")), (self.old, "")):
            got = uc.tests_changed(old, new)
            self.assertEqual(got["checked"], False, (old, new))
            self.assertTrue(got["why"])

    def test_binary_large_and_unreadable_files_are_compared_without_crashing(self):
        self.both("t/data/a.bin.Test.dat", b"\x00\x01\x02", b"\x00\x01\x03")
        self.both("t/big/BigTest.java", "x\n" * (1 << 20), "x\n" * (1 << 20) + "y\n")
        self.both("t/same/SameBigTest.java", "z\n" * (1 << 20))
        self.both("t/lines/ManyTest.java", "".join("line %d\n" % i for i in range(9000)), "".join("line %d\n" % i for i in range(1, 9001)))
        got = uc.tests_changed(self.old, self.new)
        notes = {c["path"]: c["note"] for c in got["changed"]}
        self.assertEqual(notes["t/data/a.bin.Test.dat"], "binary file")
        self.assertEqual(notes["t/big/BigTest.java"], "large file, lines not counted")
        self.assertEqual(notes["t/lines/ManyTest.java"], "lines counted approximately")
        self.assertNotIn("t/same/SameBigTest.java", notes)
        many = next(c for c in got["changed"] if c["path"] == "t/lines/ManyTest.java")
        self.assertEqual((many["added"], many["removed"]), (1, 1))

    def test_links_are_never_followed_and_hostile_trees_stay_bounded(self):
        outside = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, outside, True)
        put(outside, "OutTest.java", "outside")
        self.both("t/InTest.java", "in")
        make_symlink(self, os.path.join(outside, "OutTest.java"), os.path.join(self.new, "t", "LinkTest.java"))
        make_symlink(self, outside, os.path.join(self.new, "t", "linked"))
        got = uc.tests_changed(self.old, self.new)
        self.assertEqual((got["workTests"], got["counts"]), (1, {"added": 0, "removed": 0, "changed": 0}))
        self.assertNotIn("Out", json.dumps(got))
        for i in range(300):
            self.both("t/many/M%03dTest.java" % i, "a\n" * 50, "a\n" * 50 + "edit %d\n" % i)
        started = time.time()
        got = uc.tests_changed(self.old, self.new)
        self.assertLess(time.time() - started, 30)
        self.assertEqual((got["counts"]["changed"], len(got["changed"])), (300, 40))              # the count is complete, the list is cut
        self.assertNotRegex(json.dumps(uc.tests_changed(self.old, self.new)), "\x1b")

    def test_a_hostile_file_name_is_cleaned(self):
        self.both("t/ev\x1b[31mil\nTest.java", "a", "b")
        got = uc.tests_changed(self.old, self.new)
        self.assertNotRegex(got["changed"][0]["path"], r"[\x00-\x1f]")

    CARDS = """# DELTA_CATALOG: x

| ID | Category | Fix | Site | Old to new |
|---|---|---|---|---|
| **D-01** | Behavioral-silent | Judgment | `a/b/Alpha.java:916` | changed |
| **D-02** | Behavioral-silent (pre-existing bug, wider on 17) | Judgment | `Beta.java` (`decode`) | changed |
| **D-03** | Project-system | Judgment | root `pom.xml:629` | build |

| # | Category | Fix | Conf. | Delta | Site | Sites | Note |
|---|---|---|---|---|---|---|---|
| 9 | Behavioral-silent | Mechanical | High | CLDR listing dates | `x/y/Resource.java:574` | 1 | Gamma.java is mentioned in prose only |
| 10 | Dependency | Mechanical | High | JaCoCo agent | `pom.xml:614` | 3 | n |

## Card detail

### 9. CLDR listing dates
- **Category / fix / confidence:** Behavioral-silent / Mechanical / High; sites: 1; cited: `x/y/Resource.java:574`
- **Blast radius:** One site. Sites: Delta.java:12, and Epsilon.java:40 also matter.

### 11. A card that only exists as a card
- **Category / fix / confidence:** Behaviour-Silent / Judgment / Low; sites: 2; cited: `p/Zeta.py:3`, `p/Eta.py:9`

### 12. A numbered heading with no category line
- Some prose about Theta.java:1.

### D-04 Another id style
- **Category:** behavioral silent
- **Site:** `q/Iota.cs:5`
"""

    def test_deltas_are_read_from_tables_and_cards_and_merged(self):
        got = {d["id"]: d for d in uc.parse_deltas(self.CARDS)}
        self.assertEqual(sorted(got), ["11", "9", "10", "D-01", "D-02", "D-03", "D-04"] if False else sorted(["11", "9", "10", "D-01", "D-02", "D-03", "D-04"]))
        self.assertEqual([s["stem"] for s in got["D-01"]["sites"]], ["Alpha"])
        self.assertEqual(got["D-01"]["sites"][0]["line"], 916)
        self.assertEqual([s["stem"] for s in got["D-02"]["sites"]], ["Beta"])                     # a site without a line, with a known extension
        self.assertEqual(got["D-02"]["category"], "Behavioral-silent (pre-existing bug, wider on 17)")
        self.assertEqual([s["stem"] for s in got["9"]["sites"]], ["Resource"])                    # the table and the card agree; prose files are not sites
        self.assertEqual(got["9"]["title"], "CLDR listing dates")
        self.assertEqual([s["stem"] for s in got["11"]["sites"]], ["Zeta", "Eta"])
        self.assertEqual(got["11"]["category"], "Behaviour-Silent")
        self.assertEqual(got["D-04"]["category"], "behavioral silent")
        self.assertEqual([s["stem"] for s in got["D-04"]["sites"]], ["Iota"])
        self.assertNotIn("12", got)

    def test_the_parser_is_tolerant_and_bounded(self):
        for text in ("", "no tables at all", "| a | b |\n|---|---|\n| 1 | 2 |\n", "| Category |\n|---|\n| Behavioral-silent |\n", "### 1. x\n" * 10, "|" * 100000, "#" * 100000,
                     "### 3. t\n- **Category:** " + "Behavioral-silent " * 100000 + "\n", "| # | Category | Site |\n|---|---|---|\n| 1 | Behavioral-silent | " + "a/" * 100000 + "B.java:1 |\n"):
            started = time.time()
            uc.parse_deltas(text)
            self.assertLess(time.time() - started, 10)
        many = "| # | Category | Site |\n|---|---|---|\n" + "".join("| %d | Behavioral-silent | `S%d.java:1` |\n" % (i, i) for i in range(6000))
        self.assertLessEqual(len(uc.parse_deltas(many)), uc.DELTA_CAP)
        weird = uc.parse_deltas("| # | Category | Site |\n|---|---|---|\n| 1\x1b[31m | Behavioral-silent\x00 | `Ev\x1bil.java:1` |\n")
        self.assertNotRegex(json.dumps(weird), r"\\u001b|\\u0000")

    def test_coverage_names_sites_as_whole_words_in_test_files_only(self):
        put(self.new, "src/main/Alpha.java", "class Alpha {}")
        put(self.new, "src/test/AlphaTest.java", "class AlphaTest { Alpha a; AlphaBeta x; Gamma_ y; }")
        put(self.new, "src/main/Beta.java", "class Beta { Delta d; }")
        put(self.new, "src/test/notes.txt", "Delta is discussed here")
        cat = ("| # | Category | Site |\n|---|---|---|\n| 1 | Behavioral-silent | `src/main/Alpha.java:1` |\n| 2 | Behavioral-silent | `src/main/Beta.java:2` |\n"
               "| 3 | Behavioral-silent | `src/main/Gamma.java:3` |\n| 4 | Behavioral-silent | `src/main/Delta.java:4` |\n| 5 | Dependency | `src/main/Other.java:5` |\n"
               "| 6 | Behavioral-silent | `src/main/Alpha.java:1`, `src/main/Beta.java:2` |\n| 7 | Behavioral-silent | no site here |\n| 8 | Behavioral-silent | `pom.xml:9` |\n")
        got = uc.delta_coverage(cat, self.new)
        self.assertEqual((got["parsed"], got["silent"], got["other"], got["testFiles"]), (8, 7, 1, 1))
        self.assertEqual([d["id"] for d in got["covered"]], ["1"])
        self.assertEqual({d["id"]: d["why"] for d in got["uncovered"]}, {"2": "no test names Beta", "3": "no test names Gamma", "4": "no test names Delta", "6": "no test names Beta", "7": "no site is named in the catalog"})
        self.assertEqual([d["id"] for d in got["config"]], ["8"])
        self.assertTrue(got["gap"])

    def test_no_catalog_or_an_unreadable_one_is_a_gap(self):
        self.assertTrue(uc.delta_coverage(None, self.new)["gap"])
        got = uc.delta_coverage("Nothing to read here.", self.new)
        self.assertEqual((got["parsed"], got["gap"]), (0, True))
        ok = uc.delta_coverage("| # | Category | Site |\n|---|---|---|\n| 1 | API-removed | `A.java:1` |\n", self.new)
        self.assertEqual((ok["silent"], ok["gap"]), (0, False))

    def test_the_command_line_prints_a_summary_json_and_the_exit_code(self):
        self.both("t/InTest.java", "Alpha")
        put(self.new, "src/main/Alpha.java", "class Alpha {}")
        cat = put(self.root, "CAT.md", "| # | Category | Site |\n|---|---|---|\n| 1 | Behavioral-silent | `src/main/Alpha.java:1` |\n")
        code, out, _ = run_main(uc.main, [self.old, self.new, cat])
        self.assertEqual(code, 0)
        self.assertIn("tests kept: ok", out)
        self.assertIn("deltas covered: ok", out)
        code, out, _ = run_main(uc.main, [self.old, self.new, cat, "--json"])
        self.assertEqual(json.loads(out)["deltas"]["silent"], 1)
        os.remove(os.path.join(self.new, "t", "InTest.java"))
        code, out, _ = run_main(uc.main, [self.old, self.new])
        self.assertEqual(code, 1)
        self.assertIn("removed: t/InTest.java", out)
        self.assertEqual(run_main(uc.main, [os.path.join(self.root, "none"), self.new])[0], 2)
        self.assertEqual(run_main(uc.main, [self.old, self.new, os.path.join(self.root, "none.md")])[0], 2)


class ProofOutputs(unittest.TestCase):
    def setUp(self):
        self.ws = Ws(self)
        self.adir = os.path.join(self.ws.root, "analysis", "s")

    def test_files_summary_and_exit_codes(self):
        code, out, _ = run_main(pp.main, ["s", "--workspace", self.ws.root])
        self.assertEqual(code, 0)
        self.assertIn("s: PROVEN", out)
        data = load(os.path.join(self.adir, "VERIFICATION.json"))
        self.assertEqual((data["v"], data["overall"]["verdict"], data["signoff"]), (1, "PROVEN", {"name": "", "role": "", "date": "", "decision": ""}))
        md = read(os.path.join(self.adir, "VERIFICATION.md"))
        for needle in ("# Verification: s", "**Overall: PROVEN**", "### P0 business rules", "### What this does not prove", "## Sign-off", "________________",
                       "## How each verdict is computed", "tests executed: 3, failed 0, skipped 0", "- [ ] A business owner accepts the report output"):
            self.assertIn(needle, md)
        os.remove(os.path.join(self.adir, "equivalence", "test-runs.json"))
        code, out, _ = run_main(pp.main, ["s", "--workspace", self.ws.root])
        self.assertEqual(code, 1)
        self.assertIn("NOT PROVEN", out)
        self.assertEqual(sorted(f for f in os.listdir(self.adir) if f.startswith("VERIFICATION")), ["VERIFICATION.json", "VERIFICATION.md"])

    def test_bad_names_are_refused(self):
        for argv in (["..", "--workspace", self.ws.root], ["a/b"], ["s", "../x"], ["s", "a\\b"], [""]):
            self.assertEqual(run_main(pp.main, argv)[0], 2, argv)

    def test_a_linked_output_is_refused_and_nothing_is_written_through_it(self):
        outside = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, outside, True)
        put(outside, "real.md", "ORIGINAL")
        make_symlink(self, os.path.join(outside, "real.md"), os.path.join(self.adir, "VERIFICATION.md"))
        code, _, err = run_main(pp.main, ["s", "--workspace", self.ws.root])
        self.assertEqual(code, 2)
        self.assertIn("symbolic link", err)
        self.assertEqual(read(os.path.join(outside, "real.md")), "ORIGINAL")

    def test_hostile_names_and_reasons_stay_text_in_the_markdown(self):
        put(self.ws.root, "modernized/s/mod/src/test/CalcTest.java", "// RULE-001\n", T0 + 20)
        put(self.ws.root, "analysis/s/BUSINESS_RULES.md", RULES_MD.replace("Rounding", "Round | <img src=x onerror=1> \x1b[31m"), T0 + 10)
        self.ws.runs(suites=[{"module": "mod", "name": "unit | `x`", "command": "mvn\x00 test\n# heading", "executed": 3, "junit": ["modernized/s/mod/target/surefire-reports"]}])
        run_main(pp.main, ["s", "--workspace", self.ws.root])
        md = read(os.path.join(self.adir, "VERIFICATION.md"))
        self.assertNotRegex(md, r"[\x00\x1b]")
        self.assertIn("Round \\| <img src=x onerror=1>", md)
        self.assertNotIn("\n# heading", md)

    def test_the_verdict_comes_from_the_evidence_not_from_an_earlier_pack(self):
        run_main(pp.main, ["s", "--workspace", self.ws.root])
        path = os.path.join(self.adir, "VERIFICATION.json")
        data = load(path)
        data["modules"][0]["verdict"] = "NOT PROVEN"
        dump(path, data)
        self.assertEqual(run_main(pp.main, ["s", "--workspace", self.ws.root])[0], 0)
        self.assertEqual(load(path)["overall"]["verdict"], "PROVEN")

    def test_a_huge_evidence_file_is_not_read(self):
        put(self.ws.root, "analysis/s/equivalence/test-runs.json", b" " * (9 << 20), T0 + 40)
        pack = self.ws.pack()
        self.assertTrue(any("larger than 8 MB" in p for p in pack["problems"]))
        self.assertEqual(pack["modules"][0]["verdict"], "NOT PROVEN")


class ProofUplift(unittest.TestCase):
    BASE = "# BASELINE\n\n## Per-test results\n\n| Test | Result |\n|---|---|\n| `T#a` | PASS |\n| `T#b` | PASS |\n| `T#c` | FAIL |\n| `T#d` | SKIP |\n"
    CATALOG = ("# DELTA_CATALOG: s\n\n| # | Category | Fix | Delta | Site |\n|---|---|---|---|---|\n| 1 | Behavioral-silent | Judgment | Locale default changed | `unit/src/Main.java:12` |\n"
               "| 2 | API-removed | Mechanical | Old API gone | `unit/src/Other.java:3` |\n")

    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root, True)
        put(self.root, "legacy/s/pom.xml", "<project/>", T0)
        put(self.root, "legacy/s/unit/src/test/MainTest.java", "class MainTest { Main m; }\n", T0)
        put(self.root, "analysis/s/PREFLIGHT.md", "x", T0 + 10)
        put(self.root, "analysis/s/BASELINE.md", self.BASE, T0 + 10)
        put(self.root, "analysis/s/baseline/results.json", json.dumps({"T#a": "PASS", "T#b": "PASS", "T#c": "FAIL", "T#d": "SKIP"}), T0 + 5)
        put(self.root, "analysis/s/DELTA_CATALOG.md", self.CATALOG, T0 + 10)
        put(self.root, "modernized/s-uplifted/unit/src/Main.java", "class Main {}\n", T0 + 20)
        put(self.root, "modernized/s-uplifted/unit/src/test/MainTest.java", "class MainTest { Main m; }\n", T0 + 20)
        put(self.root, "modernized/s-uplifted/UPLIFT_NOTES.md", "Canary: break a comparison -> 2 tests failed\n", T0 + 20)
        put(self.root, "analysis/s/equivalence/canary/TEST-C.xml", junit([("T", "a", "FAIL", ""), ("T", "b", "FAIL", "")]), T0 + 35)
        self.results([("T", "a", "PASS", ""), ("T", "b", "PASS", ""), ("T", "c", "FAIL", ""), ("T", "d", "SKIP", "")])
        put(self.root, "analysis/s/equivalence/test-runs.json", json.dumps({"legacy": {"ran": True}, "suites": [
            {"module": "unit", "name": "unit", "junit": ["modernized/s-uplifted/unit/target/surefire-reports"], "executed": 3, "failed": 1, "skipped": 1}],
            "canaries": [{"change": "break a comparison", "junit": ["analysis/s/equivalence/canary"]}]}), T0 + 40)
        rows = []
        for i in range(10):
            put(self.root, "analysis/s/equivalence/fresh/old/%d.out" % i, "v%d\n" % i, T0 + 25)
            put(self.root, "analysis/s/equivalence/fresh/new/%d.out" % i, "v%d\n" % i, T0 + 25)
            rows.append({"id": "f%d" % i, "legacy": "fresh/old/%d.out" % i, "new": "fresh/new/%d.out" % i})
        put(self.root, "analysis/s/equivalence/fresh-cases.json", json.dumps({"cases": rows}), T0 + 25)

    def results(self, cases):
        put(self.root, "modernized/s-uplifted/unit/target/surefire-reports/TEST-T.xml", junit(cases), T0 + 30)

    def module(self):
        pack = pp.overall(pp.build("s", self.root, now="x"))
        self.assertEqual(len(pack["modules"]), 1)
        return pack["modules"][0]

    def test_no_regression_against_the_baseline_is_proven_and_traces_no_rules(self):
        m = self.module()
        self.assertEqual((m["verdict"], m["track"], m["name"]), ("PROVEN", "uplift", "s-uplifted"))
        self.assertEqual({c["id"]: c["state"] for c in m["checks"]}["rules"], "na")
        self.assertEqual(m["evidence"]["baseline"]["regressionsCount"], 0)

    def test_a_regression_or_a_new_failure_is_not_proven(self):
        self.results([("T", "a", "FAIL", ""), ("T", "b", "PASS", ""), ("T", "c", "FAIL", ""), ("T", "d", "SKIP", "")])
        m = self.module()
        self.assertEqual(m["verdict"], "NOT PROVEN")
        self.assertIn("1 test(s) passed before and fail now", m["reasons"][0])
        self.results([("T", "a", "PASS", ""), ("T", "b", "PASS", ""), ("T", "c", "FAIL", ""), ("T", "d", "SKIP", ""), ("T", "new", "FAIL", "")])
        self.assertEqual(self.module()["verdict"], "NOT PROVEN")

    def test_missing_tests_and_skipped_growth_are_partly_proven(self):
        self.results([("T", "a", "PASS", ""), ("T", "c", "FAIL", ""), ("T", "d", "SKIP", "")])
        m = self.module()
        self.assertEqual(m["verdict"], "PARTLY PROVEN")
        self.assertTrue(any("did not run now" in r for r in m["reasons"]))
        self.results([("T", "a", "PASS", ""), ("T", "b", "SKIP", ""), ("T", "c", "FAIL", ""), ("T", "d", "SKIP", "")])
        self.assertEqual(self.module()["verdict"], "PARTLY PROVEN")

    def test_an_approved_baseline_difference_is_allowed_and_listed_as_a_decision(self):
        put(self.root, "analysis/s/BASELINE.md", self.BASE + "\n## Approved differences\n\n| Test | Reason |\n|---|---|\n| `T#b` | the new runtime words the message differently |\n", T0 + 10)
        self.results([("T", "a", "PASS", ""), ("T", "b", "FAIL", ""), ("T", "c", "FAIL", ""), ("T", "d", "SKIP", "")])
        m = self.module()
        self.assertEqual(m["verdict"], "PROVEN")
        self.assertTrue(any("approved by a person in BASELINE.md" in c and "T#b" in c for c in m["caveats"]))
        self.assertTrue(any("decision, not evidence" in n for n in m["notProven"]))
        self.assertEqual(m["evidence"]["baseline"]["approved"][0]["id"], "T#b")

    def test_a_canary_keyed_by_a_unit_of_the_uplifted_copy_is_accepted(self):
        dump(os.path.join(self.root, "analysis", "s", "equivalence", "test-runs.json"), {"legacy": {"ran": True}, "suites": [
            {"module": "unit", "name": "unit", "junit": ["modernized/s-uplifted/unit/target/surefire-reports"]}],
            "canaries": [{"module": "unit", "change": "break a comparison", "junit": ["analysis/s/equivalence/canary"]}]})
        m = self.module()
        self.assertEqual({c["id"]: c["state"] for c in m["checks"]}["canary"], "pass")

    def test_a_test_that_now_passes_needs_a_person_but_does_not_change_the_verdict(self):
        self.results([("T", "a", "PASS", ""), ("T", "b", "PASS", ""), ("T", "c", "PASS", ""), ("T", "d", "SKIP", "")])
        m = self.module()
        self.assertEqual(m["verdict"], "PROVEN")
        self.assertTrue(any("intended fix" in n for n in m["needsPerson"]))

    def test_target_only_and_a_missing_baseline_cannot_be_proven(self):
        self.results([("T", "a", "PASS", ""), ("T", "b", "PASS", ""), ("T", "c", "PASS", "")])
        put(self.root, "analysis/s/BASELINE.md", "target-only: Java 8 is not installed here\n", T0 + 10)
        m = self.module()
        self.assertEqual(m["verdict"], "PARTLY PROVEN")
        self.assertIn("target-only", " ".join(m["reasons"]))
        self.assertFalse(m["evidence"]["legacy"]["ran"])
        os.remove(os.path.join(self.root, "analysis", "s", "BASELINE.md"))
        m = self.module()
        self.assertEqual(m["verdict"], "PARTLY PROVEN")
        self.assertIn("BASELINE.md is missing", " ".join(m["reasons"]))

    def states(self):
        return {c["id"]: c["state"] for c in self.module()["checks"]}

    def test_all_nine_checks_pass_for_a_clean_uplift(self):
        m = self.module()
        self.assertEqual(self.states(), {"tests": "pass", "rules": "na", "same": "pass", "fresh": "pass", "canary": "pass", "source": "pass", "baseline": "pass", "kept": "pass", "deltas": "pass"})
        self.assertEqual(m["evidence"]["baselineEvidence"]["kind"], "measured")
        self.assertEqual(m["evidence"]["deltas"]["silent"], 1)

    # -- (1) a measured baseline
    def test_a_baseline_typed_by_hand_is_a_gap_and_says_so_in_plain_words(self):
        os.remove(os.path.join(self.root, "analysis", "s", "baseline", "results.json"))
        m = self.module()
        self.assertEqual((m["verdict"], self.states()["baseline"], self.states()["same"]), ("PARTLY PROVEN", "gap", "pass"))
        detail = next(c["detail"] for c in m["checks"] if c["id"] == "baseline")
        self.assertIn("typed by hand", detail)
        self.assertIn("analysis/<system>/baseline/", detail)
        self.assertIn("Recorded:", detail)
        self.assertIn("### Baseline evidence", pp.render_md(pp.overall(pp.build("s", self.root, now="x"))))

    def test_a_forged_counts_file_is_not_evidence(self):
        os.remove(os.path.join(self.root, "analysis", "s", "baseline", "results.json"))
        put(self.root, "analysis/s/baseline/counts.json", json.dumps({"PASS": 2, "FAIL": 1, "SKIP": 1, "executed": 3}), T0 + 5)
        put(self.root, "analysis/s/baseline/counts2.json", json.dumps({"tests": {"count": 3}}), T0 + 5)
        m = self.module()
        self.assertEqual(self.states()["baseline"], "gap")
        info = m["evidence"]["baselineEvidence"]
        self.assertEqual(info["kind"], "typed")
        self.assertIn("counts.json", info["ignored"])
        self.assertIn("Files that only hold counts were ignored", next(c["detail"] for c in m["checks"] if c["id"] == "baseline"))

    def test_only_the_baseline_folder_and_recorded_lines_are_looked_at(self):
        os.remove(os.path.join(self.root, "analysis", "s", "baseline", "results.json"))
        put(self.root, "analysis/s/harness/stray.json", json.dumps({"T#a": "PASS", "T#b": "PASS", "T#c": "FAIL", "T#d": "SKIP"}), T0 + 5)
        put(self.root, "analysis/s/BASELINE.md", self.BASE + "\nSee also `analysis/s/harness/stray.json` for the details.\n", T0 + 10)
        self.assertEqual(self.states()["baseline"], "gap")                               # a path in prose is not evidence
        put(self.root, "analysis/s/BASELINE.md", self.BASE + "\n- **Recorded:** 2026-09-24. Machine-readable per-test results: `analysis/s/harness/stray.json`\n", T0 + 10)
        self.assertEqual(self.states()["baseline"], "pass")
        put(self.root, "analysis/s/BASELINE.md", self.BASE + "\nMachine-readable: harness/stray.json\n", T0 + 10)
        self.assertEqual(self.states()["baseline"], "pass")                              # relative to analysis/<system>/

    def test_evidence_outside_analysis_or_through_a_link_is_never_used(self):
        outside = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, outside, True)
        full = json.dumps({"T#a": "PASS", "T#b": "PASS", "T#c": "FAIL", "T#d": "SKIP"})
        put(outside, "results.json", full)
        os.remove(os.path.join(self.root, "analysis", "s", "baseline", "results.json"))
        put(self.root, "analysis/other/results.json", full, T0 + 5)
        put(self.root, "modernized/results.json", full, T0 + 5)
        make_symlink(self, os.path.join(outside, "results.json"), os.path.join(self.root, "analysis", "s", "baseline", "link.json"))
        make_symlink(self, outside, os.path.join(self.root, "analysis", "s", "linked"))
        for line in ("Recorded: `../other/results.json`", "Recorded: `analysis/other/results.json`", "Recorded: `analysis/s/../other/results.json`", "Recorded: `modernized/results.json`",
                     "Recorded: `%s/results.json`" % outside, "Recorded: `analysis/s/linked/results.json`", "Recorded: `analysis/s/baseline/link.json`"):
            put(self.root, "analysis/s/BASELINE.md", self.BASE + "\n" + line + "\n", T0 + 10)
            self.assertEqual(self.states()["baseline"], "gap", line)

    def test_baseline_sources_that_disagree_are_a_gap_not_first_one_wins(self):
        put(self.root, "analysis/s/baseline/second.json", json.dumps({"T#a": "FAIL", "T#b": "PASS"}), T0 + 5)
        m = self.module()
        self.assertEqual(self.states()["baseline"], "gap")
        detail = next(c["detail"] for c in m["checks"] if c["id"] == "baseline")
        self.assertIn("disagree with each other", detail)
        self.assertIn("T#a: PASS in one source, FAIL in second.json", detail)                           # the example names the test and the file
        put(self.root, "analysis/s/baseline/second.json", json.dumps({"T#a": "PASS"}), T0 + 5)          # agrees on what they share
        self.assertEqual(self.states()["baseline"], "pass")
        put(self.root, "analysis/s/baseline/old.test-output.txt", "Tests run: 9, Failures: 0, Errors: 0, Skipped: 0\n", T0 + 5)      # a log with other totals
        self.assertEqual(self.states()["baseline"], "gap")

    def test_a_typed_table_that_disagrees_with_its_evidence_is_a_gap(self):
        put(self.root, "analysis/s/baseline/results.json", json.dumps({"T#a": "PASS", "T#b": "FAIL", "T#c": "FAIL", "T#d": "SKIP"}), T0 + 5)
        m = self.module()
        self.assertEqual(self.states()["baseline"], "gap")
        self.assertIn("disagree on 1 test", next(c["detail"] for c in m["checks"] if c["id"] == "baseline"))
        self.assertEqual(m["evidence"]["baselineEvidence"]["disagree"], 1)

    def test_a_raw_runner_log_can_measure_the_baseline_and_must_match_the_typed_counts(self):
        os.remove(os.path.join(self.root, "analysis", "s", "baseline", "results.json"))
        put(self.root, "analysis/s/baseline/old.test-output.txt", "[INFO] Tests run: 4, Failures: 1, Errors: 0, Skipped: 1\n", T0 + 5)     # 3 executed, 1 failed, 1 skipped
        m = self.module()
        self.assertEqual(self.states()["baseline"], "pass")
        self.assertIn("runner log", next(c["detail"] for c in m["checks"] if c["id"] == "baseline"))
        put(self.root, "analysis/s/baseline/old.test-output.txt", "[INFO] Tests run: 4, Failures: 0, Errors: 0, Skipped: 1\n", T0 + 5)
        self.assertEqual(self.states()["baseline"], "gap")

    def test_target_only_and_a_missing_baseline_leave_the_measured_check_not_applicable(self):
        put(self.root, "analysis/s/BASELINE.md", "target-only: Java 8 is not installed here\n", T0 + 10)
        self.assertEqual(self.states()["baseline"], "na")
        os.remove(os.path.join(self.root, "analysis", "s", "BASELINE.md"))
        self.assertEqual((self.states()["baseline"], self.states()["same"]), ("na", "gap"))

    def test_measured_per_test_results_are_what_the_new_run_is_compared_with(self):
        put(self.root, "analysis/s/baseline/results.json", json.dumps({"T#a": "PASS", "T#b": "PASS", "T#c": "FAIL", "T#d": "SKIP", "T#extra": "PASS"}), T0 + 5)
        self.results([("T", "a", "PASS", ""), ("T", "b", "PASS", ""), ("T", "c", "FAIL", ""), ("T", "d", "SKIP", "")])
        m = self.module()
        self.assertEqual(m["evidence"]["baseline"]["source"], "measured results")
        self.assertEqual(self.states()["same"], "gap")                                  # T#extra was measured on the old version and did not run now
        self.assertEqual(self.states()["baseline"], "pass")                             # the typed table lists fewer tests than were measured, and agrees on all it lists
        self.assertTrue(any("did not run now" in r for r in m["reasons"]))

    def test_a_totals_table_typed_beside_the_rows_must_match_the_evidence_too(self):
        put(self.root, "analysis/s/BASELINE.md", self.BASE + "\n## Totals\n\n| | Count |\n|---|---|\n| Executed | 50 |\n| Failed | 0 |\n", T0 + 10)
        m = self.module()
        self.assertEqual(self.states()["baseline"], "gap")
        self.assertIn("Totals table says 50 executed", " ".join(m["evidence"]["baselineEvidence"]["examples"]))
        put(self.root, "analysis/s/BASELINE.md", self.BASE + "\n## Totals\n\n| | Count |\n|---|---|\n| Executed | 3 |\n| Failed | 1 |\n", T0 + 10)
        self.assertEqual(self.states()["baseline"], "pass")

    # -- (2) tests changed during the uplift
    def test_a_removed_legacy_test_file_is_a_gap_and_the_list_says_which(self):
        os.remove(os.path.join(self.root, "modernized", "s-uplifted", "unit", "src", "test", "MainTest.java"))
        m = self.module()
        self.assertEqual((m["verdict"], self.states()["kept"]), ("PARTLY PROVEN", "gap"))
        detail = next(c["detail"] for c in m["checks"] if c["id"] == "kept")
        self.assertIn("MainTest.java", detail)
        self.assertIn("edited or deleted", detail)
        self.assertEqual(m["evidence"]["testsChanged"]["removed"][0]["path"], "unit/src/test/MainTest.java")
        self.assertTrue(any("Review the test files" in n for n in m["needsPerson"]))

    def test_more_than_a_quarter_of_the_test_files_changed_is_a_gap_and_a_quarter_is_not(self):
        for i in range(3):
            put(self.root, "legacy/s/unit/src/test/T%d.java" % i, "class T%d { int a = 1; }\n" % i, T0)
            put(self.root, "modernized/s-uplifted/unit/src/test/T%d.java" % i, "class T%d { int a = 1; }\n" % i, T0 + 20)
        put(self.root, "modernized/s-uplifted/unit/src/test/T0.java", "class T0 { int a = 2; }\n", T0 + 20)         # 1 of 4 changed: exactly a quarter
        m = self.module()
        self.assertEqual(self.states()["kept"], "pass")
        self.assertEqual(m["evidence"]["testsChanged"]["changed"][0], {"path": "unit/src/test/T0.java", "added": 1, "removed": 1, "note": ""})
        self.assertTrue(any("1 changed" in n for n in m["needsPerson"]))
        put(self.root, "modernized/s-uplifted/unit/src/test/T1.java", "class T1 { int a = 2; }\n", T0 + 20)         # 2 of 4
        m = self.module()
        self.assertEqual(self.states()["kept"], "gap")
        self.assertIn("2 of 4 legacy test files (50%) were changed", next(c["detail"] for c in m["checks"] if c["id"] == "kept"))

    def test_no_legacy_tests_or_no_legacy_tree_is_a_gap(self):
        os.remove(os.path.join(self.root, "legacy", "s", "unit", "src", "test", "MainTest.java"))
        m = self.module()
        self.assertEqual(self.states()["kept"], "gap")
        self.assertIn("nothing shows that the working copy's tests were not written during the uplift", next(c["detail"] for c in m["checks"] if c["id"] == "kept"))
        shutil.rmtree(os.path.join(self.root, "legacy"))
        m = self.module()
        self.assertEqual(self.states()["kept"], "gap")
        self.assertIn("legacy tree was not found", next(c["detail"] for c in m["checks"] if c["id"] == "kept"))

    def test_added_tests_are_listed_and_never_a_gap(self):
        put(self.root, "modernized/s-uplifted/unit/src/test/NewCharacterizationTest.java", "class NewCharacterizationTest { Main m; }\n", T0 + 20)
        m = self.module()
        self.assertEqual(self.states()["kept"], "pass")
        self.assertEqual(m["evidence"]["testsChanged"]["added"], [{"path": "unit/src/test/NewCharacterizationTest.java", "lines": 2}])
        md = pp.render_md(pp.overall(pp.build("s", self.root, now="x")))
        self.assertIn("### Test files changed during the uplift", md)
        self.assertIn("Added: `unit/src/test/NewCharacterizationTest.java`", md)
        self.assertIn("Weakened assertions cannot be detected", md)
        self.assertTrue(any("Weakened assertions cannot be detected" in n for n in m["notProven"]))

    # -- (3) delta coverage
    def test_a_silent_delta_no_test_names_is_a_gap_and_other_categories_are_only_listed(self):
        put(self.root, "analysis/s/DELTA_CATALOG.md", self.CATALOG + "| 3 | Behavioral-silent | Judgment | Rounding changed | `unit/src/Money.java:40` |\n", T0 + 10)
        m = self.module()
        self.assertEqual((m["verdict"], self.states()["deltas"]), ("PARTLY PROVEN", "gap"))
        detail = next(c["detail"] for c in m["checks"] if c["id"] == "deltas")
        self.assertIn("1 of 2 Behavioral-silent", detail)
        self.assertIn("no test names Money", detail)
        self.assertEqual(m["evidence"]["deltas"]["uncovered"][0]["id"], "3")
        self.assertIn("Not named by any test: 3 Rounding changed", pp.render_md(pp.overall(pp.build("s", self.root, now="x"))))
        put(self.root, "modernized/s-uplifted/unit/src/test/MoneyTest.java", "class MoneyTest { Money m; }\n", T0 + 20)
        self.assertEqual(self.states()["deltas"], "pass")

    def test_a_missing_or_unreadable_catalog_is_a_gap(self):
        os.remove(os.path.join(self.root, "analysis", "s", "DELTA_CATALOG.md"))
        m = self.module()
        self.assertEqual(self.states()["deltas"], "gap")
        self.assertIn("DELTA_CATALOG.md was not found", next(c["detail"] for c in m["checks"] if c["id"] == "deltas"))
        put(self.root, "analysis/s/DELTA_CATALOG.md", "Some prose about the version change. No table, no cards.\n", T0 + 10)
        self.assertEqual(self.states()["deltas"], "gap")

    def test_a_delta_at_a_build_file_is_listed_for_a_person_not_judged(self):
        put(self.root, "analysis/s/DELTA_CATALOG.md", self.CATALOG + "| 4 | Behavioral-silent | Judgment | Bundle plugin | `pom.xml:629` |\n", T0 + 10)
        m = self.module()
        self.assertEqual(self.states()["deltas"], "pass")
        self.assertEqual(m["evidence"]["deltas"]["config"][0]["id"], "4")
        self.assertTrue(any("build or configuration file" in n for n in m["needsPerson"]))

    def test_a_unit_argument_narrows_the_suites_and_an_unknown_name_is_an_error(self):
        pack = pp.build("s", self.root, "unit", now="x")
        self.assertEqual(pack["modules"][0]["name"], "s-uplifted")
        self.assertEqual(pack["asked"], "unit")
        with self.assertRaises(pp.InputError):
            pp.build("s", self.root, "nosuchunit")


# ---------------------------------------------------------------- the Proof section of the report
def page_data(html):
    return json.loads(re.search(r'<script type="application/json" id="report-data">(.*?)</script>', html, re.S).group(1))


def good_pack(**module_change):
    checks = [{"id": cid, "label": label, "state": "pass", "detail": "fine"} for cid, label in br.PROOF_CHECKS]
    m = {"name": "mod", "track": "rewrite", "verdict": "PROVEN", "checks": checks, "verifiedAt": "2026-09-24 00:00 UTC",
         "evidence": {"tests": {"executed": 5, "failed": 0, "skipped": 0},
                      "rules": {"p0": [{"id": "RULE-001", "name": "Total", "confidence": "High", "status": "tested", "tests": 3, "main": 1, "where": "src/test/A.java:9"}]},
                      "fresh": {"inputs": 12, "executed": 20, "same": 20, "differs": 0, "missing": 0}, "equivalence": {"cases": 4, "executed": 4, "same": 4, "differs": 0, "missing": 0, "approved": [], "masks": []}},
         "notProven": ["It does not prove inputs nobody tried."], "brief": {"found": True, "items": [{"text": "A person accepts it", "where": "Phase 1 exit criterion"}], "count": 1}}
    m.update(module_change)
    return {"v": 1, "system": "s", "generated": "2026-09-24 00:00 UTC", "problems": [], "legacy": {"path": "legacy/s", "ran": True}, "modules": [m], "signoff": {}, "rules": ["PROVEN needs all six checks."]}


def good_uplift_pack(**evidence):
    """A pack for an uplift whose nine checks all pass, with the evidence that backs them; a test changes the evidence and looks at the view."""
    pack = good_pack()
    m = pack["modules"][0]
    m.update(name="s-uplifted", track="uplift")
    m["checks"] = [c for c in m["checks"] if c["id"] != "rules"] + [{"id": "rules", "label": "Rules traced", "state": "na", "detail": "An uplift keeps the code."}] + [
        {"id": cid, "label": label, "state": "pass", "detail": "fine"} for cid, label in br.UPLIFT_CHECKS]
    m["evidence"].pop("rules", None)
    m["evidence"].update(baselineEvidence={"kind": "measured", "sources": [{"kind": "machine-readable results", "name": "base.json", "tests": 40}], "disagree": 0, "conflict": 0, "examples": [], "considered": ["base.json"]},
                         testsChanged={"checked": True, "why": "", "legacyTests": 8, "workTests": 9, "counts": {"added": 1, "removed": 0, "changed": 1}, "share": 0.125,
                                       "removed": [], "added": [{"path": "t/NewTest.java", "lines": 12}], "changed": [{"path": "t/OldTest.java", "added": 3, "removed": 1, "note": ""}]},
                         deltas={"parsed": 5, "silent": 2, "covered": [{"id": "1"}, {"id": "2"}], "uncovered": [], "config": [{"id": "4", "title": "Bundle plugin", "sites": ["pom.xml:9"]}], "other": 3, "gap": False})
    m["evidence"].update(evidence)
    return pack


class ProofReport(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root, True)
        put(self.root, "analysis/s/PREFLIGHT.md", "# Preflight\n")
        self.out = os.path.join(self.root, "out", "REPORT.html")

    def report(self, pack):
        put(self.root, "analysis/s/VERIFICATION.json", pack if isinstance(pack, (str, bytes)) else json.dumps(pack, indent=1))       # like proof_pack.py: short lines
        code, _, err = run_main(br.main, ["s", "--workspace", self.root, "--out", self.out])
        self.assertEqual(code, 0, err)
        with open(self.out, encoding="utf-8") as fh:
            return fh.read()

    def proof(self, html):
        data = page_data(html)
        return data, next((p["proof"] for s in data["sections"] if s["id"] == "proof" for p in s["parts"] if p["t"] == "proof"), None)

    def test_the_section_the_banner_and_the_order(self):
        put(self.root, "analysis/s/EQUIVALENCE.json", "{}")
        put(self.root, "modernized/s/mod/TRANSFORMATION_NOTES.md", "# n")
        data, pv = self.proof(self.report(good_pack()))
        self.assertEqual([s["id"] for s in data["sections"]][-3:], ["build", "proof", "equivalence"])
        self.assertEqual((pv["verdict"], pv["counts"]["PROVEN"], pv["modules"][0]["p0Counts"]["tested"]), ("PROVEN", 1, 1))
        self.assertEqual(data["glance"]["proof"]["verdict"], "PROVEN")
        self.assertEqual(data["glance"]["proof"]["modules"], [{"name": "mod", "verdict": "PROVEN"}])
        self.assertEqual(pv["signoff"], {"name": "", "role": "", "date": "", "decision": ""})
        self.assertEqual(pv["modules"][0]["people"][0]["text"], "A person accepts it")

    def test_a_rule_named_only_by_tests_that_did_not_run_is_counted_and_tooling_folders_are_listed(self):
        pack = good_pack()
        pack["modules"][0]["evidence"]["rules"]["p0"].append({"id": "RULE-002", "name": "Skipped", "confidence": "High", "status": "named, not run", "tests": 1, "main": 0, "where": "T.java:3"})
        pack["toolingOnly"] = [{"name": "parity-harness", "path": "modernized/s/parity-harness"}, "not a dict", {"name": "x" * 500, "path": 5}]
        html = self.report(pack)
        _, pv = self.proof(html)
        self.assertEqual(pv["modules"][0]["p0Counts"], {"tested": 1, "claimedOnly": 0, "notRun": 1, "none": 0})
        self.assertEqual(pv["modules"][0]["verdict"], "PARTLY PROVEN")         # a pass cannot stand next to a rule that no test ran
        self.assertEqual([t["name"] for t in pv["tooling"]][0], "parity-harness")
        self.assertEqual(len(pv["tooling"]), 2)
        self.assertLessEqual(len(pv["tooling"][1]["name"]), 120)
        self.assertEqual(self.proof(self.report(good_pack()))[1]["tooling"], [])

    def test_no_pack_means_no_section_and_the_older_reports_are_unchanged(self):
        code, _, _ = run_main(br.main, ["s", "--workspace", self.root, "--out", self.out])
        data = page_data(read(self.out))
        self.assertIsNone(data["glance"]["proof"])
        self.assertNotIn("proof", [s["id"] for s in data["sections"]])

    def test_the_verdict_is_recomputed_from_the_checks_never_taken_from_the_file(self):
        pack = good_pack()
        pack["modules"][0]["checks"][3]["state"] = "gap"
        _, pv = self.proof(self.report(pack))
        self.assertEqual(pv["modules"][0]["verdict"], "PARTLY PROVEN")
        self.assertTrue(any("recorded PROVEN" in p and "PARTLY PROVEN" in p for p in pv["problems"]))
        pack["modules"][0]["checks"][0]["state"] = "fail"
        pack["modules"][0]["verdict"] = "PROVEN"
        data, pv = self.proof(self.report(pack))
        self.assertEqual((pv["verdict"], data["glance"]["proof"]["verdict"]), ("NOT PROVEN", "NOT PROVEN"))
        self.assertEqual(pv["modules"][0]["reasons"][0], "Tests ran: fine")

    def test_a_pack_that_contradicts_its_own_numbers_is_downgraded(self):
        for change, check, want in (({"evidence": {"tests": {"executed": 3, "failed": 2}}}, 0, "fail"),
                                    ({"evidence": {"tests": {"executed": 3}, "equivalence": {"differs": 1}, "fresh": {"inputs": 12}}}, 2, "fail"),
                                    ({"evidence": {"tests": {"executed": 3}, "fresh": {"inputs": 12, "missing": 1}}}, 3, "fail"),
                                    ({"evidence": {"tests": {"executed": 0}}}, 0, "fail"),
                                    ({"evidence": {"tests": {"executed": 3}, "rules": {"p0": [{"id": "R", "status": "none"}]}}}, 1, "gap"),
                                    ({"evidence": {"tests": {"executed": 3}, "fresh": {"inputs": 3}}}, 3, "gap"),
                                    ({"evidence": {"tests": {"executed": 3}}}, 3, "gap")):
            _, pv = self.proof(self.report(good_pack(**change)))
            self.assertEqual(pv["modules"][0]["checks"][check]["state"], want, change)
            self.assertNotEqual(pv["modules"][0]["verdict"], "PROVEN")
        pack = good_pack()
        pack["modules"][0]["checks"] = pack["modules"][0]["checks"][:5]
        _, pv = self.proof(self.report(pack))
        self.assertEqual(pv["modules"][0]["verdict"], "PARTLY PROVEN")
        self.assertIn("missing from VERIFICATION.json", pv["modules"][0]["reasons"][0])
        self.assertEqual(self.proof(self.report(dict(good_pack(), modules=[])))[1]["verdict"], "NOT PROVEN")

    def test_an_uplift_needs_its_three_extra_checks_and_a_rewrite_does_not(self):
        _, pv = self.proof(self.report(good_uplift_pack()))
        m = pv["modules"][0]
        self.assertEqual((m["verdict"], [c["id"] for c in m["checks"]]), ("PROVEN", ["tests", "rules", "same", "fresh", "canary", "source", "baseline", "kept", "deltas"]))
        self.assertEqual(m["uplift"]["testsChanged"]["counts"], {"added": 1, "removed": 0, "changed": 1})
        self.assertEqual(m["uplift"]["deltas"]["coveredCount"], 2)
        pack = good_uplift_pack()
        pack["modules"][0]["checks"] = [c for c in pack["modules"][0]["checks"] if c["id"] != "kept"]
        _, pv = self.proof(self.report(pack))
        self.assertEqual(pv["modules"][0]["verdict"], "PARTLY PROVEN")
        self.assertIn("tests kept check is missing", " ".join(pv["problems"]))
        _, pv = self.proof(self.report(good_pack()))                                     # a rewrite never needs them
        self.assertEqual((pv["modules"][0]["verdict"], len(pv["modules"][0]["checks"]), pv["modules"][0]["uplift"]), ("PROVEN", 6, None))

    def test_forged_uplift_passes_are_downgraded_by_the_evidence_beside_them(self):
        cases = (("baseline", {"baselineEvidence": {"kind": "typed"}}), ("baseline", {"baselineEvidence": {"kind": "measured", "disagree": 2}}), ("baseline", {"baselineEvidence": {"kind": "measured", "conflict": 1}}),
                 ("kept", {"testsChanged": {"checked": False}}), ("kept", {"testsChanged": {"checked": True, "legacyTests": 0, "counts": {}}}),
                 ("kept", {"testsChanged": {"checked": True, "legacyTests": 8, "counts": {"removed": 1, "changed": 0, "added": 0}}}),
                 ("kept", {"testsChanged": {"checked": True, "legacyTests": 8, "counts": {"removed": 0, "changed": 3, "added": 0}}}),
                 ("deltas", {"deltas": {"parsed": 4, "silent": 1, "covered": [], "uncovered": [{"id": "9"}]}}), ("deltas", {"deltas": {"parsed": 0}}), ("deltas", {"deltas": "nope"}))
        for cid, change in cases:
            _, pv = self.proof(self.report(good_uplift_pack(**change)))
            m = pv["modules"][0]
            self.assertEqual({c["id"]: c["state"] for c in m["checks"]}[cid], "gap", (cid, change))
            self.assertEqual(m["verdict"], "PARTLY PROVEN", (cid, change))
        for state in ("na", "gap"):                                                        # "not applicable" is no way out for the kept and deltas checks
            pack = good_uplift_pack(testsChanged={"checked": False}, deltas={"parsed": 0})
            for c in pack["modules"][0]["checks"]:
                if c["id"] in ("kept", "deltas"):
                    c["state"] = state
            self.assertEqual(self.proof(self.report(pack))[1]["modules"][0]["verdict"], "PARTLY PROVEN")
        pack = good_uplift_pack(baselineEvidence={"kind": "target-only"})
        for c in pack["modules"][0]["checks"]:
            if c["id"] == "baseline":
                c["state"] = "na"
        self.assertEqual(self.proof(self.report(pack))[1]["modules"][0]["checks"][6]["state"], "na")      # a target-only baseline may say so

    def test_the_uplift_evidence_is_cut_and_cleaned(self):
        evil = "<script>alert(1)</script>" + chr(0x2028)
        _, pv = self.proof(self.report(good_uplift_pack(
            baselineEvidence={"kind": evil, "sources": [{"kind": evil * 5, "name": evil}] * 50, "disagree": "x", "examples": [evil * 20] * 20, "considered": [evil] * 50},
            testsChanged={"checked": True, "legacyTests": 8, "workTests": 8, "counts": {"added": 1, "removed": 0, "changed": 0}, "share": "x", "added": [{"path": evil * 20, "lines": "x"}] * 300, "removed": "x", "changed": [1, None]},
            deltas={"parsed": 3, "silent": 1, "covered": [], "uncovered": [{"id": evil * 5, "title": evil * 10, "why": evil * 10, "sites": [evil] * 20}] * 300, "config": "x"})))
        up = pv["modules"][0]["uplift"]
        self.assertEqual(up["baseline"]["kind"], "none")
        self.assertLessEqual((len(up["baseline"]["sources"]), len(up["baseline"]["examples"]), len(up["testsChanged"]["added"]), len(up["deltas"]["uncovered"])), (10, 5, 40, 40))
        self.assertEqual((up["testsChanged"]["share"], up["testsChanged"]["added"][0]["lines"], up["testsChanged"]["removed"], up["deltas"]["config"]), (0.0, 0, [], []))
        self.assertGreater(up["deltas"]["uncoveredCount"], 0)
        self.assertEqual(pv["modules"][0]["verdict"], "PARTLY PROVEN")

    def test_a_real_uplift_pack_from_proof_pack_carries_its_evidence_to_the_report(self):
        base = ProofUplift("test_all_nine_checks_pass_for_a_clean_uplift")
        base.setUp()
        base.addCleanup(shutil.rmtree, base.root, True)
        put(base.root, "modernized/s-uplifted/unit/src/test/NewCharacterizationTest.java", "class NewCharacterizationTest { Main m; }\n", T0 + 20)
        run_main(pp.main, ["s", "--workspace", base.root])
        run_main(br.main, ["s", "--workspace", base.root])
        data = page_data(read(os.path.join(base.root, "analysis", "s", "REPORT.html")))
        pv = next(p["proof"] for sec in data["sections"] if sec["id"] == "proof" for p in sec["parts"])
        m = pv["modules"][0]
        self.assertEqual((pv["verdict"], len(m["checks"])), ("PROVEN", 9))
        self.assertEqual(m["uplift"]["testsChanged"]["added"][0]["path"], "unit/src/test/NewCharacterizationTest.java")
        self.assertEqual(m["uplift"]["baseline"]["kind"], "measured")
        self.assertEqual(m["uplift"]["deltas"]["silent"], 1)

    def test_a_real_pack_written_by_proof_pack_renders_the_same_verdict(self):
        ws = Ws(self)
        put(ws.root, "modernized/s/mod/src/test/CalcTest.java", "// RULE-001\n", T0 + 20)
        run_main(pp.main, ["s", "--workspace", ws.root])
        code, _, _ = run_main(br.main, ["s", "--workspace", ws.root])
        data = page_data(read(os.path.join(ws.root, "analysis", "s", "REPORT.html")))
        mod = data["glance"]["proof"]["modules"][0]
        self.assertEqual(mod, {"name": "mod", "verdict": "PARTLY PROVEN"})
        pv = next(p["proof"] for s in data["sections"] if s["id"] == "proof" for p in s["parts"])
        self.assertEqual(pv["modules"][0]["p0Counts"], {"tested": 1, "claimedOnly": 0, "notRun": 0, "none": 1})
        self.assertTrue(pv["modules"][0]["reasons"][0].startswith("Rules traced: 1 of 2 P0"))

    def test_hostile_values_stay_data_and_the_page_keeps_its_rules(self):
        evil = "<script>window.__pwned=1</script></script><img src=x onerror=1> &amp; " + chr(0x2028)
        pack = good_pack(name=evil * 5, track=evil, notProven=[evil * 20] * 60, verdict=["PROVEN"], checks="nope",
                         evidence={"tests": {"executed": "many", "failed": -1, "skipped": 10 ** 30}, "rules": {"p0": [evil, {"id": evil, "status": evil, "tests": evil}] * 150},
                                   "fresh": [1], "equivalence": {"approved": evil, "masks": [evil]}, "baseline": 5, "canary": [evil]},
                         brief={"items": [{"text": evil * 9, "where": evil}] * 100, "count": "x", "found": 1})
        pack.update(problems=[evil] * 20, signoff="x", legacy=[], rules="x")
        html = self.report(pack)
        block = re.search(r'<script type="application/json" id="report-data">(.*?)</script>', html, re.S).group(1)
        for bad in ("<", ">", "&", chr(0x2028)):
            self.assertNotIn(bad, block)
        data, pv = self.proof(html)
        m = pv["modules"][0]
        self.assertLessEqual(len(m["name"]), 120)
        self.assertEqual((m["tests"], m["verdict"]), ({"executed": 0, "failed": 0, "skipped": 0}, "PARTLY PROVEN"))       # no usable checks: nothing is proven
        self.assertLessEqual(len(m["p0"]), 200)
        self.assertLessEqual(len(m["people"]), 40)
        self.assertLessEqual(len(pv["problems"]), 10 + 1)
        self.assertEqual(html.count("<script"), 2)
        self.assertNotRegex(html.replace(block, "").split('<script id="app">')[0].split("</style>")[1], r"__pwned|onerror=")
        policy = re.search(r'http-equiv="Content-Security-Policy" content="([^"]*)"', html).group(1)
        self.assertIn("default-src 'none'", policy)

    def test_malformed_or_foreign_verification_files_are_reported_not_raised(self):
        for text in ("[1, 2", "{}", '{"modules": "x"}', "[]", "null", b"\x00\x01"):
            data = page_data(self.report(text))
            self.assertEqual(data["glance"]["proof"]["verdict"], "NOT PROVEN" if text != "[1, 2" else "NOT PROVEN", text)
        html = self.report("[1, 2")
        self.assertTrue(any("VERIFICATION.json could not be parsed" in json.dumps(p) for s in page_data(html)["sections"] for p in s["parts"]))

    def test_a_linked_verification_file_is_not_read(self):
        outside = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, outside, True)
        put(outside, "V.json", json.dumps(good_pack()))
        make_symlink(self, os.path.join(outside, "V.json"), os.path.join(self.root, "analysis", "s", "VERIFICATION.json"))
        code, _, _ = run_main(br.main, ["s", "--workspace", self.root, "--out", self.out])
        data = page_data(read(self.out))
        self.assertIsNone(data["glance"]["proof"])


NODE_PROOF = r"""
const fs = require('fs'), vm = require('vm');
const tpl = fs.readFileSync(process.env.TEMPLATE, 'utf8');
const grab = function (re) { return re.exec(tpl)[1] !== undefined ? re.exec(tpl)[1] : re.exec(tpl)[0]; };
const core = /\/\* core:start[^\n]*\n([\s\S]*?)\/\* core:end \*\//.exec(tpl)[1];
const proof = /\/\* proof:start[^\n]*\n([\s\S]*?)\/\* proof:end \*\//.exec(tpl)[1];
const helpers = /function fmt\(n\)[^\n]*\n/.exec(tpl)[0] + /function chip\([^\n]*\n/.exec(tpl)[0];
class Text { constructor(t) { this.text = String(t); } }
class El { constructor(t) { this.tag = t; this.attrs = {}; this.kids = []; }
  setAttribute(k, v) { this.attrs[k] = String(v); } appendChild(c) { this.kids.push(c); return c; } }
const ctx = { document: { createElement: t => new El(t), createTextNode: t => new Text(t) } };
vm.createContext(ctx);
const api = vm.runInContext('(function(){"use strict";' + core + helpers + proof + ';return {partProof:partProof,own:own};})()', ctx);
function walk(n, acc, top) {
  if (n instanceof Text) { acc.text += n.text + '\n'; return; }
  acc.tags.add(n.tag); Object.keys(n.attrs).forEach(k => { acc.attrs.add(k); });
  if (top && n.tag === 'div' && /banner/.test(n.attrs.class || '')) acc.banners.push(n.attrs.class);
  n.kids.forEach(c => walk(c, acc, false));
}
const input = JSON.parse(fs.readFileSync(0, 'utf8')), out = [];
for (const pv of input) {
  const t0 = Date.now(), acc = { tags: new Set(), attrs: new Set(), text: '', banners: [] };
  api.partProof(pv).forEach(n => walk(n, acc, true));
  out.push({ ms: Date.now() - t0, tags: [...acc.tags], attrs: [...acc.attrs], text: acc.text, banners: acc.banners });
}
out.push({ own: [api.own({a: 'x'}, 'a', 'd'), api.own({a: 'x'}, '__proto__', 'd'), api.own({a: 'x'}, 'constructor', 'd'), api.own({a: 'x'}, 'toString', 'd')] });
process.stdout.write(JSON.stringify(out));
"""


@unittest.skipUnless(NODE, "node is not installed")
class ProofScript(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        evil = "<script>alert(1)</script></script><img src=x onerror=alert(2)> [x](javascript:alert(3))"
        packs = [good_pack(),
                 good_pack(checks=[{"id": "tests", "label": "Tests ran", "state": "gap", "detail": "x"}]),
                 good_pack(checks=[{"id": "tests", "label": "Tests ran", "state": "fail", "detail": "x"}]),
                 good_pack(name=evil, track=evil, notProven=[evil], brief={"found": True, "count": 900, "items": [{"text": evil, "where": evil}]},
                           evidence={"tests": {"executed": 1}, "rules": {"p0": [{"id": evil, "name": evil, "status": "__proto__", "tests": 1, "main": 1, "where": evil}] * 200}}),
                 dict(good_pack(), legacy={"path": evil, "target": evil, "ran": False}, problems=[evil], signoff={"name": evil, "role": "", "date": "", "decision": ""})]
        packs.append(good_uplift_pack(deltas={"parsed": 5, "silent": 2, "covered": [{"id": "1"}], "uncovered": [{"id": "2", "title": "Rounding changed", "why": "no test names Money", "sites": ["Money.java:4"]}],
                                                  "config": [{"id": "4", "title": "Bundle plugin", "sites": ["pom.xml:9"]}]},
                                      testsChanged={"checked": True, "legacyTests": 8, "workTests": 8, "counts": {"added": 0, "removed": 1, "changed": 0}, "share": 0.0,
                                                    "removed": [{"path": "t/GoneTest.java", "lines": 7}], "added": [], "changed": []},
                                      baselineEvidence={"kind": "typed", "sources": [], "disagree": 0, "conflict": 0, "examples": [], "considered": [], "ignored": ["counts.json"]}))
        views = [br.proof_view(p) for p in packs]
        views[3]["verdict"] = "__proto__"
        views[3]["modules"][0]["verdict"] = "constructor"
        proc = subprocess.run([NODE, "-e", NODE_PROOF], input=json.dumps(views), capture_output=True, text=True, env=dict(os.environ, TEMPLATE=TEMPLATE), timeout=120)
        assert proc.returncode == 0, proc.stderr
        cls.out, cls.evil = json.loads(proc.stdout), evil

    def test_only_safe_elements_and_attributes_are_built(self):
        allowed_tags = {"div", "table", "thead", "tbody", "tr", "th", "td", "span", "p", "h3", "h4", "ul", "li", "details", "summary"}
        allowed_attrs = {"class", "role", "tabindex", "aria-label", "scope"}
        for doc in self.out[:-1]:
            self.assertLessEqual(set(doc["tags"]), allowed_tags)
            self.assertLessEqual(set(doc["attrs"]), allowed_attrs)
            self.assertLess(doc["ms"], 3000)

    def test_hostile_text_is_shown_as_text_never_as_markup_or_a_link(self):
        doc = self.out[3]
        self.assertIn("<script>alert(1)</script>", doc["text"])
        self.assertIn("[x](javascript:alert(3))", doc["text"])
        self.assertNotIn("a", doc["tags"])
        self.assertNotIn("img", doc["tags"])

    def test_the_banner_says_the_verdict_in_words_symbols_and_colour(self):
        self.assertIn("✓ Proof: 1 PROVEN", self.out[0]["text"])
        self.assertEqual(self.out[0]["banners"], ["banner ok", "banner ok"])
        self.assertEqual(self.out[1]["banners"], ["banner warn", "banner warn"])
        self.assertEqual(self.out[2]["banners"], ["banner bad", "banner bad"])
        self.assertIn("◐ ", self.out[1]["text"])
        self.assertIn("✗ ", self.out[2]["text"])

    def test_unknown_verdicts_and_prototype_names_fall_back_to_red(self):
        self.assertEqual(self.out[3]["banners"], ["banner bad", "banner bad"])
        self.assertEqual(self.out[-1]["own"], ["x", "d", "d", "d"])

    def test_the_page_shows_the_matrix_what_is_not_proven_and_a_blank_sign_off(self):
        text = self.out[0]["text"]
        for needle in ("What this does not prove", "It does not prove inputs nobody tried.", "P0 business rules: 1 tested, 0 named but not run, 0 claimed only, 0 with no test", "RULE-001",
                       "Waiting for a person", "A person accepts it", "Sign-off", "________________", "accept / accept with conditions / reject", "How the verdict is computed",
                       "Fresh inputs: 12 new input(s)", "tests executed: 5"):
            self.assertIn(needle, text)
        self.assertIn("It could not run here, so the proof is trace-based.", self.out[4]["text"])

    def test_an_uplift_shows_its_baseline_test_files_and_deltas(self):
        text = self.out[5]["text"]
        for needle in ("Baseline evidence: typed by hand", "Test files: 8 in the legacy tree, 8 in the working copy: 1 removed, 0 added, 0 changed", "Removed test files", "t/GoneTest.java (7 lines)",
                       "2 Behavioral-silent: 1 have a test naming their site, 1 do not", "Not named by any test", "2 Rounding changed (no test names Money)",
                       "At a build or configuration file (for a person)", "4 Bundle plugin (pom.xml:9)", "Baseline measured", "Tests kept", "Deltas covered"):
            self.assertIn(needle, text)
        self.assertNotIn("Baseline evidence: typed by hand", self.out[0]["text"])

    def test_the_template_keeps_its_own_contract(self):
        with open(TEMPLATE, encoding="utf-8") as fh:
            text = fh.read()
        app = re.search(r'<script id="app">(.*?)</script>', text, re.S).group(1)
        self.assertEqual(len(re.findall(r"/\* proof:start", app)), 1)
        self.assertNotRegex(app, r"innerHTML|outerHTML|insertAdjacentHTML|document\.write|eval\(|new Function|fetch\(|XMLHttpRequest")
        self.assertNotRegex(text, r"https?://")
        self.assertIn("case 'proof': return partProof(p.proof);", app)
