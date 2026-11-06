"""Tests for the "Rules traced" check: a rule is tested only when something that ran and passed backs it, and test-only folders are not judged.

Run:  python3 -m unittest discover -s plugins/code-modernization/scripts/tests
A test that names a rule is not a test that ran: skipped and pending tests, and files whose class never ran, leave the rule "named, not run".
"""
import json
import os
import re
import shutil
import sys
import tempfile
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(PLUGIN, "scripts"))
import build_report as br  # noqa: E402
import proof_pack as pp  # noqa: E402
import trace_rules as tr  # noqa: E402
from test_proof_tools import RULES_MD, T0, Ws, junit, load, passing, put, read, run_main  # noqa: E402

SKIPPED_TEST = '''package p;

class CalcTest {
  @Test
  @Disabled("PENDING RULE-001")
  void RULE_001_totals() {}

  @Test
  @Disabled("PENDING RULE-002")
  void RULE_002_rounds() {}
}
'''
NOT_RUN = "named, not run"


class RuleWs(Ws):
    """The workspace of the proof tests (module mod, P0 rules RULE-001 and RULE-002), with helpers to change what the tests are and what ran."""

    def module(self, module="mod"):
        return super().module(module)

    def p0(self):
        return {r["id"]: r for r in self.module()["evidence"]["rules"]["p0"]}

    def statuses(self):
        return {r["id"]: r["status"] for r in self.module()["evidence"]["rules"]["p0"]}

    def check_rules(self):
        return next(c for c in self.module()["checks"] if c["id"] == "rules")

    def test_file(self, rel, text):
        put(self.root, "modernized/s/mod/src/test/" + rel, text, T0 + 20)

    def keep_only(self, *cases):
        self.results(list(cases))


class RulesNeedExecutedTests(unittest.TestCase):
    def setUp(self):
        self.ws = RuleWs(self)

    def test_the_default_workspace_is_tested_by_files_whose_class_ran(self):
        self.assertEqual(self.ws.statuses(), {"RULE-001": "tested", "RULE-002": "tested"})
        self.assertEqual(self.ws.check_rules()["state"], "pass")
        self.assertIn("backed by a test that ran and passed", self.ws.check_rules()["detail"])
        self.assertEqual(self.ws.module()["verdict"], "PROVEN")

    # (i) the hole that was found: @Disabled("PENDING RULE-001") and a result file that shows it skipped
    def test_a_disabled_pending_test_that_the_results_show_skipped_is_named_not_run(self):
        self.ws.test_file("CalcTest.java", SKIPPED_TEST)
        self.ws.keep_only(("CalcTest", "RULE_001_totals", "SKIP", "PENDING RULE-001"), ("CalcTest", "RULE_002_rounds", "SKIP", "PENDING RULE-002"), ("OtherTest", "works", "PASS", ""))
        self.assertEqual(self.ws.statuses(), {"RULE-001": NOT_RUN, "RULE-002": NOT_RUN})
        c = self.ws.check_rules()
        self.assertEqual(c["state"], "gap")
        self.assertIn("P0 rules named only by tests that did not run: RULE-001, RULE-002 (skipped, pending, failing or missing from the results).", c["detail"])
        m = self.ws.module()
        self.assertEqual(m["verdict"], "PARTLY PROVEN")
        self.assertEqual(m["evidence"]["rules"]["namedNotRun"], ["RULE-001", "RULE-002"])
        self.assertEqual(m["evidence"]["rules"]["p0NoTests"], ["RULE-001", "RULE-002"])
        self.assertTrue(m["evidence"]["rules"]["perTestResults"])
        self.assertTrue(any(r.startswith("Rules traced: P0 rules named only by tests that did not run") for r in m["reasons"]))
        self.assertEqual(m["evidence"]["tests"]["skipped"], 2)

    def test_the_same_test_without_a_skip_marker_but_skipped_at_run_time_is_named_not_run_too(self):
        self.ws.test_file("CalcTest.java", "class CalcTest {\n  // RULE-001 and RULE-002 need a database\n  void a() {}\n}\n")
        self.ws.keep_only(("CalcTest", "a", "SKIP", "no database here"), ("OtherTest", "works", "PASS", ""))
        self.assertEqual(self.ws.statuses(), {"RULE-001": NOT_RUN, "RULE-002": NOT_RUN})
        self.assertEqual({r["by"] for r in self.ws.p0().values()}, {""})

    def test_a_test_that_ran_and_failed_backs_nothing(self):
        self.ws.test_file("CalcTest.java", "class CalcTest {\n  // RULE-001 RULE-002\n  void a() {}\n}\n")
        self.ws.keep_only(("CalcTest", "RULE_001_totals", "FAIL", ""), ("CalcTest", "RULE_002_rounds", "ERROR", ""), ("OtherTest", "works", "PASS", ""))
        self.assertEqual(self.ws.statuses(), {"RULE-001": NOT_RUN, "RULE-002": NOT_RUN})
        self.assertEqual(self.ws.module()["verdict"], "NOT PROVEN")          # the failures fail the tests check as they always did
        self.assertEqual(self.ws.check_rules()["state"], "gap")

    # (ii) an executed, passing testcase that carries the id in its name
    def test_a_passing_test_whose_name_carries_the_id_backs_the_rule_in_any_spelling(self):
        self.ws.test_file("CalcTest.java", SKIPPED_TEST)          # the only file that names the rules is all skipped
        for name in ("RULE-001 totals", "RULE_001_totals", "rule001", "testRule001Totals", "Rule001", "totals[RULE-001]"):
            self.ws.keep_only(("ChecksTest", name, "PASS", ""), ("ChecksTest", "test_RULE_002_rounds", "PASS", ""))
            self.assertEqual(self.ws.statuses(), {"RULE-001": "tested", "RULE-002": "tested"}, name)
        p0 = self.ws.p0()
        self.assertEqual((p0["RULE-001"]["by"], p0["RULE-002"]["by"]), ("test name", "test name"))
        self.assertEqual(self.ws.check_rules()["state"], "pass")
        self.assertEqual(self.ws.module()["verdict"], "PROVEN")

    def test_the_class_name_may_carry_the_id_and_the_shorthand_names_both_rules(self):
        self.ws.test_file("CalcTest.java", SKIPPED_TEST)
        self.ws.keep_only(("com.x.Rule001Test", "a", "PASS", ""), ("com.x.OtherTest", "RULE-002/003", "PASS", ""))
        self.assertEqual(self.ws.statuses(), {"RULE-001": "tested", "RULE-002": "tested"})

    def test_an_id_in_the_name_of_a_test_that_did_not_pass_or_in_another_modules_results_backs_nothing(self):
        self.ws.test_file("CalcTest.java", SKIPPED_TEST)
        self.ws.keep_only(("ChecksTest", "RULE_001_a", "SKIP", "x"), ("ChecksTest", "RULE_002_b", "FAIL", ""), ("ChecksTest", "works", "PASS", ""))
        self.assertEqual(self.ws.statuses(), {"RULE-001": NOT_RUN, "RULE-002": NOT_RUN})
        put(self.ws.root, "modernized/s/extra/src/main/X.java", "class X {}\n", T0 + 20)
        put(self.ws.root, "modernized/s/extra/target/surefire-reports/TEST-X.xml", junit([("XTest", "RULE_001_a", "PASS", ""), ("XTest", "RULE_002_a", "PASS", "")]), T0 + 30)
        self.ws.runs(suites=[{"module": "mod", "name": "unit", "junit": ["modernized/s/mod/target/surefire-reports"]},
                             {"module": "extra", "name": "unit", "junit": ["modernized/s/extra/target/surefire-reports"]}])
        self.assertEqual(self.ws.statuses(), {"RULE-001": NOT_RUN, "RULE-002": NOT_RUN})          # what extra ran does not count for mod

    # (iii) a plain comment in a test file whose class ran
    def test_a_plain_comment_in_a_test_file_whose_class_ran_backs_the_rule(self):
        self.ws.test_file("CalcTest.java", "class CalcTest {\n  // RULE-001 is pinned by these\n  void a() {}\n  void rule002_rounds() {}\n}\n")
        self.ws.keep_only(("com.x.CalcTest", "a", "PASS", ""))
        self.assertEqual(self.ws.statuses(), {"RULE-001": "tested", "RULE-002": "tested"})
        p0 = self.ws.p0()
        self.assertEqual(p0["RULE-001"]["by"], "test file")
        self.assertTrue(p0["RULE-001"]["where"].endswith("src/test/CalcTest.java:2"), p0["RULE-001"]["where"])
        self.assertEqual(self.ws.module()["verdict"], "PROVEN")

    def test_the_where_points_at_the_mention_that_backs_the_rule_not_at_a_skipped_one(self):
        self.ws.test_file("CalcTest.java", SKIPPED_TEST)                                    # sorts before Live.java and names both rules, skipped
        self.ws.test_file("Live.java", "// RULE-001 RULE-002 are checked by these\nclass Live {}\n")
        self.ws.keep_only(("Live", "a", "PASS", ""), ("CalcTest", "RULE_001_totals", "SKIP", "x"))
        p0 = self.ws.p0()
        self.assertTrue(p0["RULE-001"]["where"].endswith("src/test/Live.java:1"), p0["RULE-001"]["where"])
        self.assertEqual(self.ws.statuses(), {"RULE-001": "tested", "RULE-002": "tested"})

    def test_the_class_name_may_be_nested_dotted_a_python_module_or_a_path(self):
        same = (("CalcTest.java", "com.x.CalcTest$Inner"), ("CalcTest.java", "com.x.Outer$Deep$CalcTest"), ("CalcTest.java", "com.x.CalcTest$A$B"), ("test_calc.py", "tests.test_calc.TestCalc"),
                ("test_calc.py", "tests.test_calc"), ("CalcTests.cs", "Ns.CalcTests"), ("calc.spec.ts", "src/calc.spec.ts"), ("CalcTest.java", "calctest"), ("CalcTest.java", "CALCTEST"))
        other = (("CalcTest.java", "com.x.OtherCalcTest"), ("CalcTest.java", "com.calc.test.Other"), ("test_calc.py", "tests.test_other.TestCalc"), ("CalcTest.java", "Calc"), ("CalcTest.java", ""))
        for rel, cls in same + other:
            self.ws.test_file(rel, "// RULE-001 RULE-002\n")
            self.ws.keep_only((cls, "a", "PASS", ""))
            self.assertEqual(self.ws.statuses(), {"RULE-001": "tested", "RULE-002": "tested"} if (rel, cls) in same else {"RULE-001": NOT_RUN, "RULE-002": NOT_RUN}, (rel, cls))
            os.remove(os.path.join(self.ws.root, "modernized", "s", "mod", "src", "test", rel))
            self.ws.test_file("CalcTest.java", "// nothing here\n")

    # (iv) a file none of whose tests ran
    def test_a_rule_named_only_in_a_file_none_of_whose_tests_ran_is_named_not_run(self):
        self.ws.test_file("CalcTest.java", "// RULE-001\nclass CalcTest {}\n")
        self.ws.test_file("GhostTest.java", "// RULE-002 is pinned here, and nothing marks it skipped\nclass GhostTest {}\n")
        self.ws.keep_only(("CalcTest", "a", "PASS", ""), ("GhostTest", "b", "SKIP", "no docker"))
        self.assertEqual(self.ws.statuses(), {"RULE-001": "tested", "RULE-002": NOT_RUN})
        self.ws.keep_only(("CalcTest", "a", "PASS", ""))                     # the class is not in the results at all
        self.assertEqual(self.ws.statuses(), {"RULE-001": "tested", "RULE-002": NOT_RUN})
        c = self.ws.check_rules()
        self.assertEqual(c["state"], "gap")
        self.assertIn("named only by tests that did not run: RULE-002", c["detail"])
        self.assertNotIn("RULE-001", c["detail"])

    # (v) counts only
    def test_counts_only_evidence_never_backs_a_rule(self):
        put(self.ws.root, "analysis/s/equivalence/unit.test-output.txt", "[INFO] Tests run: 3, Failures: 0, Errors: 0, Skipped: 0\n", T0 + 30)
        for suite in ({"module": "mod", "name": "unit", "command": "mvn test", "log": ["analysis/s/equivalence/unit.test-output.txt"]},
                      {"module": "mod", "name": "unit", "executed": 3, "failed": 0, "skipped": 0}):
            self.ws.runs(suites=[suite])
            self.assertEqual(self.ws.statuses(), {"RULE-001": NOT_RUN, "RULE-002": NOT_RUN}, suite)
            m = self.ws.module()
            self.assertFalse(m["evidence"]["rules"]["perTestResults"])
            self.assertEqual(self.ws.check_rules()["state"], "gap")
            self.assertIn("named by tests, but no result file lists each test, so nothing shows one ran: RULE-001, RULE-002.", self.ws.check_rules()["detail"])
            self.assertNotEqual(m["verdict"], "PROVEN")
        self.ws.runs(suites=[{"module": "mod", "name": "unit", "log": ["analysis/s/equivalence/unit.test-output.txt"]},
                             {"module": "mod", "name": "more", "junit": ["modernized/s/mod/target/surefire-reports"]}])          # one suite that lists its tests is enough
        self.assertEqual(self.ws.statuses(), {"RULE-001": "tested", "RULE-002": "tested"})

    def test_no_suite_at_all_or_result_files_with_no_test_in_them_back_nothing(self):
        put(self.ws.root, "modernized/s/mod/target/surefire-reports/TEST-CalcTest.xml", '<?xml version="1.0"?><testsuite name="S" tests="0"></testsuite>', T0 + 30)
        self.assertEqual(self.ws.statuses(), {"RULE-001": NOT_RUN, "RULE-002": NOT_RUN})
        self.ws.runs(suites=[])
        self.assertEqual(self.ws.statuses(), {"RULE-001": NOT_RUN, "RULE-002": NOT_RUN})
        self.assertEqual(self.ws.module()["verdict"], "NOT PROVEN")

    # (vi) Python, and how far a marker reaches
    def test_a_pytest_skip_that_names_the_rule_leaves_it_named_not_run(self):
        put(self.ws.root, "analysis/s/BUSINESS_RULES.md", RULES_MD.replace("**Priority:** P2", "**Priority:** P0"), T0 + 10)
        put(self.ws.root, "modernized/s/mod/src/main/calc.py", "def fee(): pass\n", T0 + 20)
        self.ws.test_file("CalcTest.java", "// RULE-001 RULE-002\nclass CalcTest {}\n")
        self.ws.test_file("test_fee.py", 'import pytest\n\n\n@pytest.mark.skip(reason="RULE-004")\ndef test_fee():\n    pass\n\n\ndef test_other():\n    pass\n')
        self.ws.keep_only(("CalcTest", "a", "PASS", ""), ("tests.test_fee", "test_fee", "SKIP", "RULE-004"), ("tests.test_fee", "test_other", "PASS", ""))
        self.assertEqual(self.ws.statuses(), {"RULE-001": "tested", "RULE-002": "tested", "RULE-004": NOT_RUN})
        self.assertIn("RULE-004", self.ws.check_rules()["detail"])
        self.ws.test_file("test_fee.py", 'import pytest\n\n\ndef test_fee():\n    # RULE-004 is pinned here\n    pass\n')            # no marker: the class ran and passed
        self.assertEqual(self.ws.statuses()["RULE-004"], "tested")

    def test_a_marker_reaches_three_lines_down_and_no_further_and_any_case(self):
        put(self.ws.root, "analysis/s/BUSINESS_RULES.md", "### RULE-001: x\n**Priority:** P0\n", T0 + 10)
        self.ws.keep_only(("CalcTest", "a", "PASS", ""))
        for gap, want in ((0, NOT_RUN), (1, NOT_RUN), (2, NOT_RUN), (3, NOT_RUN), (4, "tested"), (9, "tested")):
            lines = ["@Disabled RULE-001"] if gap == 0 else ["@Disabled"] + ["// filler"] * (gap - 1) + ["// RULE-001"]          # the mention is `gap` lines below the marker
            self.ws.test_file("CalcTest.java", "\n".join(lines) + "\n")
            self.assertEqual(self.ws.statuses()["RULE-001"], want, gap)
        self.ws.test_file("CalcTest.java", "// RULE-001\n// a marker below the mention does not matter: @Disabled\n")
        self.assertEqual(self.ws.statuses()["RULE-001"], "tested")
        for marker in ("@Disabled", "@Ignore", "[Ignore]", "@Skip", "#[ignore]", "xit(", "xdescribe(", "it.skip(", "test.skip(", "describe.skip(", "t.Skip()", "@pytest.mark.skip",
                       "@unittest.skipIf(x)", "pending", "PENDING", "Pending", "todo", "TODO", "@DISABLED", "SKIP", "XIT("):
            self.ws.test_file("CalcTest.java", "%s\n// RULE-001\n" % marker)
            self.assertEqual(self.ws.statuses()["RULE-001"], NOT_RUN, marker)
        self.ws.test_file("CalcTest.java", "// RULE-001 is enabled and runs as a @Test\n")
        self.assertEqual(self.ws.statuses()["RULE-001"], "tested")

    def test_one_live_mention_is_enough_when_the_same_file_also_has_skipped_ones(self):
        put(self.ws.root, "analysis/s/BUSINESS_RULES.md", "### RULE-001: x\n**Priority:** P0\n", T0 + 10)
        self.ws.test_file("CalcTest.java", '@Disabled("PENDING RULE-001")\nvoid a() {}\n\n\n\n\n// RULE-001 also holds for the total\n')
        self.ws.keep_only(("CalcTest", "b", "PASS", ""))
        self.assertEqual(self.ws.statuses()["RULE-001"], "tested")

    def test_a_rule_a_test_file_names_and_main_code_names_is_named_not_run_until_something_ran(self):
        # the default workspace's Calc.java names both rules too: main code never makes a rule tested
        self.ws.test_file("CalcTest.java", SKIPPED_TEST)
        self.ws.keep_only(("OtherTest", "works", "PASS", ""))
        m = self.ws.module()
        self.assertEqual({r["id"]: (r["status"], r["main"] > 0) for r in m["evidence"]["rules"]["p0"]}, {"RULE-001": (NOT_RUN, True), "RULE-002": (NOT_RUN, True)})

    def test_claimed_only_and_missing_rules_keep_their_own_words_beside_named_not_run(self):
        put(self.ws.root, "analysis/s/BUSINESS_RULES.md", RULES_MD.replace("**Priority:** P1", "**Priority:** P0").replace("**Priority:** P2", "**Priority:** P0"), T0 + 10)
        put(self.ws.root, "modernized/s/mod/src/main/Calc.java", "class Calc {}\n", T0 + 20)
        put(self.ws.root, "modernized/s/mod/TRANSFORMATION_NOTES.md", "Legacy: `legacy/s/app/mod.cbl` and `legacy/s/app/other.cbl`\n\n| Rule | Target |\n|---|---|\n| RULE-003 | `src/main/Calc.java` |\n\nCanary: x -> 3 tests failed\n", T0 + 20)
        self.ws.test_file("CalcTest.java", "// RULE-001\n@Disabled\n// RULE-002\n")
        self.ws.keep_only(("CalcTest", "a", "PASS", ""))
        self.assertEqual(self.ws.statuses(), {"RULE-001": "tested", "RULE-002": NOT_RUN, "RULE-003": "claimed only", "RULE-004": "none"})
        d = self.ws.check_rules()["detail"]
        self.assertEqual(self.ws.check_rules()["state"], "gap")
        self.assertIn("P0 rules named only by tests that did not run: RULE-002 (", d)
        self.assertIn("2 of 4 P0 rule(s) are not named by any test: RULE-003, RULE-004 (1 claimed only in the notes).", d)

    def test_a_long_list_is_cut_and_says_how_many_more(self):
        cards = "".join("### RULE-%03d: r\n**Priority:** P0\n\n" % n for n in range(1, 31))
        put(self.ws.root, "analysis/s/BUSINESS_RULES.md", cards, T0 + 10)
        self.ws.test_file("CalcTest.java", "@Disabled\n" + "".join("// RULE-%03d\n@Disabled\n" % n for n in range(1, 31)))
        d = self.ws.check_rules()["detail"]
        self.assertIn("RULE-012 and 18 more", d)
        self.assertNotIn("RULE-013", d)

    def test_an_uplift_still_traces_no_rules(self):
        self.assertEqual(pp.check_rules({"trace": None, "trace_problem": "x", "ran": {}}, {"track": "uplift", "rel": "modernized/s-uplifted"}, {}, [])["state"], "na")

    def test_the_pack_tells_the_report_builder_nothing_it_cannot_read(self):
        self.ws.test_file("CalcTest.java", SKIPPED_TEST)
        self.ws.keep_only(("OtherTest", "works", "PASS", ""))
        pack = self.ws.pack()
        view = br.proof_view(pack)
        m = view["modules"][0]
        self.assertEqual((m["verdict"], pack["modules"][0]["verdict"]), ("PARTLY PROVEN", "PARTLY PROVEN"))
        self.assertEqual(view["problems"], [])                                           # the builder finds nothing to correct
        self.assertEqual(m["p0Counts"]["tested"], 0)
        self.assertTrue(all(r["status"] != "tested" for r in m["p0"]))                   # an unknown status is never shown as tested
        code, out, _ = run_main(pp.main, ["s", "--workspace", self.ws.root])
        self.assertEqual(code, 1)
        self.assertIn("P0 rules named only by tests that did not run", out)

    def test_the_markdown_table_says_named_not_run_in_plain_words(self):
        self.ws.test_file("CalcTest.java", SKIPPED_TEST)
        self.ws.keep_only(("OtherTest", "works", "PASS", ""))
        run_main(pp.main, ["s", "--workspace", self.ws.root])
        md = read(os.path.join(self.ws.root, "analysis", "s", "VERIFICATION.md"))
        rows = [ln for ln in md.split("\n") if ln.startswith("| RULE-00")]
        self.assertEqual(len(rows), 2)
        self.assertTrue(all("| named, not run |" in ln for ln in rows), rows)
        self.assertIn("| 0 of 2 |", md)                                                    # the summary counts tested rules only
        self.assertIn("named, not run; one only the notes name is claimed. Neither is tested.", md)


class TestOnlyFolders(unittest.TestCase):
    def setUp(self):
        self.ws = RuleWs(self)
        put(self.ws.root, "modernized/s/harness/pom.xml", "<project/>", T0 + 20)
        put(self.ws.root, "modernized/s/harness/mvnw", "#!/bin/sh\n", T0 + 20)
        put(self.ws.root, "modernized/s/harness/.mvn/wrapper/x.properties", "x=1", T0 + 20)
        put(self.ws.root, "modernized/s/harness/README.md", "docs are not code", T0 + 20)
        put(self.ws.root, "modernized/s/harness/src/test/java/HarnessTest.java", "// drives the legacy WAR\nclass HarnessTest {}\n", T0 + 20)
        put(self.ws.root, "modernized/s/harness/src/test/java/Storefront.java", "class Storefront {}\n", T0 + 20)
        put(self.ws.root, "modernized/s/harness/target/classes/A.class", "x", T0 + 20)
        self.mod = os.path.join(self.ws.root, "modernized", "s", "harness")

    # (vii)
    def test_a_folder_of_only_test_code_and_build_files_is_listed_not_judged_and_not_counted(self):
        pack = self.ws.pack()
        self.assertEqual([m["name"] for m in pack["modules"]], ["mod"])
        self.assertEqual(pack["toolingOnly"], [{"name": "harness", "track": "rewrite", "path": "modernized/s/harness"}])
        self.assertEqual(pack["overall"], {"verdict": "PROVEN", "counts": {"PROVEN": 1, "PARTLY PROVEN": 0, "NOT PROVEN": 0}})
        code, out, _ = run_main(pp.main, ["s", "--workspace", self.ws.root])
        self.assertEqual(code, 0)
        self.assertIn("harness (rewrite): test tooling, not judged", out)
        self.assertNotIn("harness (rewrite): NOT PROVEN", out)
        data = load(os.path.join(self.ws.root, "analysis", "s", "VERIFICATION.json"))
        self.assertEqual((data["toolingOnly"], [m["name"] for m in data["modules"]], data["overall"]["verdict"]), ([{"name": "harness", "track": "rewrite", "path": "modernized/s/harness"}], ["mod"], "PROVEN"))
        md = read(os.path.join(self.ws.root, "analysis", "s", "VERIFICATION.md"))
        self.assertIn("\n## Test tooling (not judged)\n", md)
        self.assertIn("- `modernized/s/harness` (rewrite)", md)
        self.assertNotIn("## harness", md)
        self.assertEqual(md.count("| mod |"), 1)
        self.assertNotIn("| harness |", md)
        self.assertIn("**Overall: PROVEN** (1 proven)", md)
        view = br.proof_view(data)                                                   # the report builder reads the modules and ignores the new list
        self.assertEqual(([m["name"] for m in view["modules"]], view["verdict"], view["problems"]), (["mod"], "PROVEN", []))

    def test_a_pack_with_no_tooling_has_an_empty_list_and_no_heading(self):
        shutil.rmtree(self.mod)
        run_main(pp.main, ["s", "--workspace", self.ws.root])
        self.assertEqual(load(os.path.join(self.ws.root, "analysis", "s", "VERIFICATION.json"))["toolingOnly"], [])
        self.assertNotIn("Test tooling", read(os.path.join(self.ws.root, "analysis", "s", "VERIFICATION.md")))

    def test_the_tooling_folders_own_suite_and_rule_mentions_change_nothing(self):
        put(self.ws.root, "modernized/s/harness/src/test/java/HarnessTest.java", "// RULE-001 RULE-002\nclass HarnessTest {}\n", T0 + 20)
        put(self.ws.root, "modernized/s/harness/target/surefire-reports/TEST-HarnessTest.xml", junit([("HarnessTest", "a", "FAIL", "")]), T0 + 30)
        self.ws.runs(suites=[{"module": "mod", "name": "unit", "junit": ["modernized/s/mod/target/surefire-reports"]},
                             {"module": "harness", "name": "harness", "junit": ["modernized/s/harness/target/surefire-reports"]}])
        pack = self.ws.pack()
        self.assertEqual((pack["overall"]["verdict"], [m["verdict"] for m in pack["modules"]]), ("PROVEN", ["PROVEN"]))        # a failing harness test is not the module's failure
        self.assertEqual(pack["modules"][0]["evidence"]["tests"]["executed"], 3)

    def test_any_main_code_or_any_file_that_is_not_plainly_tooling_means_it_is_judged(self):
        for rel in ("src/main/java/Harness.java", "harness.py", "data/input.csv", "LICENSE", "src/main/resources/app.properties", "setup.py"):
            put(self.ws.root, "modernized/s/harness/" + rel, "x", T0 + 20)
            self.assertFalse(tr.tooling_only(self.mod), rel)
            self.assertEqual([m["name"] for m in self.ws.pack()["modules"]], ["harness", "mod"], rel)
            os.remove(os.path.join(self.mod, *rel.split("/")))
        self.assertTrue(tr.tooling_only(self.mod))

    def test_a_folder_with_no_test_file_is_not_tooling_and_neither_is_an_uplift(self):
        os.remove(os.path.join(self.mod, "src", "test", "java", "HarnessTest.java"))
        os.remove(os.path.join(self.mod, "src", "test", "java", "Storefront.java"))
        self.assertFalse(tr.tooling_only(self.mod))
        self.assertEqual(sorted(m["name"] for m in self.ws.pack()["modules"]), ["harness", "mod"])
        empty = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, empty, True)
        self.assertFalse(tr.tooling_only(empty))
        put(self.ws.root, "modernized/s-uplifted/src/test/java/ATest.java", "class ATest {}\n", T0 + 20)
        self.assertEqual({m["track"] for m in self.ws.pack()["modules"]}, {"rewrite", "uplift"})          # the whole working copy is one thing to prove, tests or not

    def test_what_counts_as_tooling_files(self):
        for name in ("pom.xml", "mvnw", "mvnw.cmd", "gradlew", "build.gradle", "build.gradle.kts", "package.json", "package-lock.json", "tsconfig.json", "tsconfig.build.json", "jest.config.js",
                     "vitest.config.ts", "conftest.py", "pytest.ini", "pyproject.toml", "go.mod", "Cargo.toml", "composer.json", "phpunit.xml.dist", "App.csproj", "All.sln", "Makefile", "Dockerfile",
                     "docker-compose.yml", "POM.XML"):
            self.assertTrue(tr.is_tooling(name), name)
        for name in ("Calc.java", "main.py", "index.js", "setup.py", "app.properties", "data.json", "run.sh", "LICENSE", "pom.xml.bak", "xpom.xml", "tsconfig"):
            self.assertFalse(tr.is_tooling(name), name)

    def test_only_tooling_at_all_is_not_proven_and_says_why(self):
        shutil.rmtree(os.path.join(self.ws.root, "modernized", "s", "mod"))
        pack = self.ws.pack()
        self.assertEqual((pack["modules"], [t["name"] for t in pack["toolingOnly"]], pack["overall"]["verdict"]), ([], ["harness"], "NOT PROVEN"))
        self.assertIn("there is no module to judge", " ".join(pack["problems"]))
        code, out, _ = run_main(pp.main, ["s", "--workspace", self.ws.root])
        self.assertEqual(code, 1)
        self.assertIn("harness (rewrite): test tooling, not judged", out)

    def test_asking_about_the_tooling_folder_is_allowed_and_changes_nothing(self):
        pack = self.ws.pack("harness")
        self.assertEqual(([m["name"] for m in pack["modules"]], pack["asked"], len(pack["toolingOnly"])), (["mod"], "harness", 1))

    def test_the_trace_still_reads_the_tooling_folders_tests(self):
        put(self.ws.root, "modernized/s/harness/src/test/java/HarnessTest.java", "// RULE-003\nclass HarnessTest {}\n", T0 + 20)
        result = tr.trace(self.ws.root, "s", {"modernized/s/harness": {"known": True, "ids": set(), "keys": {"harnesstest"}}})
        self.assertEqual({r["id"]: r["status"] for r in result["rules"]}["RULE-003"], "tested")
        self.assertEqual([m["name"] for m in result["modules"]], ["harness", "mod"])


class RuleTracePieces(unittest.TestCase):
    def test_class_keys(self):
        cases = {"com.x.CalcTest": {"x", "calctest"}, "com.x.CalcTest$Inner": {"calctest", "inner"}, "a.B$C$D": {"b", "c", "d"}, "tests.test_calc.TestCalc": {"test_calc", "testcalc"},
                 "src/calc.spec.ts": {"spec", "ts", "calc.spec.ts", "calc.spec"}, "": set(), "Only": {"only"}, "github.com/x/y": {"x", "y"}, "C:\\dir\\CalcTest.cs": {"calctest.cs", "calctest"}}
        for name, want in cases.items():
            self.assertTrue(want <= tr.class_keys(name), (name, want, tr.class_keys(name)))
        self.assertEqual(tr.class_keys(None), set())
        self.assertLessEqual(len(tr.class_keys("a." * 10000 + "b")), 4)

    def test_run_evidence_reads_only_tests_that_passed(self):
        res = {"tests": {"CalcTest#RULE_001_a": "PASS", "CalcTest#RULE_002_a": "FAIL", "CalcTest#RULE_003_a": "SKIP", "Other#testRule004": "PASS", "Other#x~1": "PASS"},
               "classes": {"CalcTest": {"pass": 1, "fail": 1, "error": 0, "skip": 1, "executed": 2}, "Ghost": {"pass": 0, "fail": 0, "error": 0, "skip": 3, "executed": 0}, "Other": {"pass": 2}}}
        ev = tr.run_evidence([res])
        self.assertEqual((ev["known"], ev["ids"], ev["keys"]), (True, {1, 4}, {"calctest", "other"}))
        self.assertEqual(tr.run_evidence([]), {"known": False, "ids": set(), "keys": set()})
        self.assertEqual(tr.run_evidence([None, {"tests": {}, "classes": {}}]), {"known": False, "ids": set(), "keys": set()})
        more = tr.run_evidence([res, {"tests": {"Later#RULE_009_a": "PASS"}, "classes": {"Later": {"pass": 1}}}])
        self.assertEqual((more["ids"], more["keys"]), ({1, 4, 9}, {"calctest", "other", "later"}))

    def test_line_marks_and_the_window(self):
        body = "a\nb @Disabled\nc\nd\ne\nf\ng"
        starts, flags = tr.line_marks(body)
        self.assertEqual(flags, [False, True, False, False, False, False, False])
        live = [tr.is_live((starts, flags), starts[i]) for i in range(7)]
        self.assertEqual(live, [True, False, False, False, False, True, True])           # the marker's line and the 3 after it are marked
        self.assertEqual(tr.line_marks("")[1], [False])

    def test_the_command_line_needs_a_module_for_results_and_reports_unreadable_ones(self):
        root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, root, True)
        put(root, "analysis/s/BUSINESS_RULES.md", RULES_MD)
        put(root, "modernized/s/mod/src/test/CalcTest.java", "// RULE-001 RULE-002\n")
        put(root, "res/TEST-bad.xml", "<testsuite><testcase")
        put(root, "res/TEST-ok.xml", junit(passing(2, "CalcTest")))
        self.assertEqual(run_main(tr.main, ["s", "--workspace", root, "--results", os.path.join(root, "res")])[0], 2)
        code, out, _ = run_main(tr.main, ["s", "--workspace", root, "--module", "mod", "--results", os.path.join(root, "res"), "--results", os.path.join(root, "nope")])
        self.assertEqual(code, 0)
        self.assertIn("result file not used: TEST-bad.xml", out)
        self.assertIn("nope is not a file or folder that can be read", out)
        code, out, _ = run_main(tr.main, ["s", "--workspace", root, "--module", "nope", "--results", os.path.join(root, "res")])
        self.assertEqual(code, 2)
        code, out, _ = run_main(tr.main, ["s", "--workspace", root, "--module", "mod", "--results", os.path.join(root, "res"), "--json"])
        self.assertEqual(code, 0)
        data = json.loads(out)
        self.assertEqual({r["id"]: r["status"] for r in data["rules"]}["RULE-001"], "tested")
        self.assertEqual(data["moduleView"]["rows"][0]["by"], "test file")


class HostileInput(unittest.TestCase):
    """(viii) Everything here is untrusted text: nothing may crash, stall or reach the markdown as structure."""

    def setUp(self):
        self.ws = RuleWs(self)

    def test_odd_and_huge_test_names_and_class_names_never_crash_or_reach_the_markdown(self):
        evil = ["RULE-001\n| RULE-999 | injected | x | tested | 9 | 9 | `x` |", "`RULE_002` <img src=x onerror=1> \x1b[31m", "RULE-001" + "x" * 5000, "\x00RULE-002\u202e\u2028", "RULE-1234567 RULE-0", "A" * 100000,
                "RULE-001 | | | |", "rule-\u0660\u0660\u0661", "RULE\u2212001"]
        cases = [(n, m, "PASS", "") for n in evil for m in evil] + [("CalcTest", "ok", "PASS", "")]
        put(self.ws.root, "modernized/s/mod/target/surefire-reports/TEST-CalcTest.xml", junit([(re.sub(r'[<>&"\x00-\x08\x0b\x0c\x0e-\x1f]', "_", c), re.sub(r'[<>&"\x00-\x08\x0b\x0c\x0e-\x1f]', "_", n), s, m) for c, n, s, m in cases]), T0 + 30)
        started = time.time()
        code, out, _ = run_main(pp.main, ["s", "--workspace", self.ws.root])
        self.assertLess(time.time() - started, 20)
        self.assertIn(code, (0, 1))
        md = read(os.path.join(self.ws.root, "analysis", "s", "VERIFICATION.md"))
        self.assertNotIn("injected", md)
        self.assertEqual(len([ln for ln in md.split("\n") if ln.startswith("| RULE-")]), 2)
        self.assertNotIn("RULE-999", md)
        self.assertNotRegex(md, r"[\x00\x1b\u202e\u2028]")
        self.assertEqual(self.ws.module()["evidence"]["rules"]["p0"][0]["id"], "RULE-001")

    def test_hostile_file_names_and_lines_stay_inside_the_p0_table(self):
        self.ws.test_file("Rule001|`x`Y.java", "// RULE-001 | RULE-002 |\n| a | b |\n")
        self.ws.test_file("CalcTest.java", "@Disabled " + "RULE-001 " * 300000 + "x" * 3000000)
        self.ws.keep_only(("Rule001|`x`Y", "a", "PASS", ""), ("CalcTest", "a", "PASS", ""))
        started = time.time()
        pack = self.ws.pack()
        self.assertLess(time.time() - started, 20)
        md = pp.render_md(pack)
        for ln in md.split("\n"):
            if ln.startswith("| RULE-"):
                self.assertEqual(len(re.findall(r"(?<!\\)\|", ln)), 8, ln)
        self.assertEqual(self.ws.statuses(), {"RULE-001": "tested", "RULE-002": "tested"})

    def test_one_line_files_with_the_marker_after_the_mention_and_many_marked_lines_are_read_in_linear_time(self):
        self.ws.test_file("CalcTest.java", "RULE-001 " * 100000 + "@Disabled")
        self.ws.test_file("Lines.java", "".join("// RULE-002 skip\n" for _ in range(100000)))
        self.ws.keep_only(("CalcTest", "a", "PASS", ""), ("Lines", "a", "PASS", ""))
        started = time.time()
        self.assertEqual(self.ws.statuses(), {"RULE-001": NOT_RUN, "RULE-002": NOT_RUN})
        self.assertLess(time.time() - started, 20)

    def test_many_passing_tests_naming_many_rules_are_read_quickly(self):
        cards = "".join("### RULE-%03d: r\n**Priority:** P0\n\n" % n for n in range(1, 400))
        put(self.ws.root, "analysis/s/BUSINESS_RULES.md", cards, T0 + 10)
        self.ws.test_file("CalcTest.java", "// nothing\n")
        self.ws.keep_only(*[("Big", "test_RULE_%03d_x" % n, "PASS", "") for n in range(1, 400)] + [("Big", "u%d" % i, "PASS", "") for i in range(30000)])
        started = time.time()
        p0 = self.ws.module()["evidence"]["rules"]["p0"]
        self.assertLess(time.time() - started, 20)
        self.assertEqual(len(p0), 100)                                                   # the pack keeps the first hundred rows, as before
        self.assertTrue(all(r["status"] == "tested" and r["by"] == "test name" for r in p0))

    def test_a_hostile_tooling_folder_name_stays_one_plain_list_item(self):
        put(self.ws.root, "modernized/s/h`\n## Injected | x/pom.xml", "<project/>", T0 + 20)
        put(self.ws.root, "modernized/s/h`\n## Injected | x/src/test/ATest.java", "class ATest {}\n", T0 + 20)
        pack = self.ws.pack()
        md = pp.render_md(pack)
        self.assertEqual(len(pack["toolingOnly"]), 1)
        self.assertNotRegex(md, r"(?m)^## Injected")
        self.assertEqual(len([ln for ln in md.split("\n") if ln.startswith("- `modernized/s/h")]), 1)
        self.assertNotIn("\n", pack["toolingOnly"][0]["name"])

    def test_a_link_in_a_test_folder_and_binary_test_files_back_nothing(self):
        outside = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, outside, True)
        put(outside, "GhostTest.java", "// RULE-002\n")
        try:
            os.symlink(os.path.join(outside, "GhostTest.java"), os.path.join(self.ws.root, "modernized", "s", "mod", "src", "test", "GhostTest.java"))
        except (OSError, NotImplementedError):
            self.skipTest("symbolic links are not available here")
        self.ws.test_file("CalcTest.java", "// RULE-001\n")
        self.ws.test_file("BinTest.java", b"\x00\x01 RULE-002 \x00")
        self.ws.keep_only(("CalcTest", "a", "PASS", ""), ("GhostTest", "a", "PASS", ""), ("BinTest", "a", "PASS", ""))
        m = self.ws.module()
        self.assertEqual({r["id"]: r["tests"] for r in m["evidence"]["rules"]["p0"]}["RULE-002"], 0)          # code (Calc.java) still names RULE-002, no test file does
        self.assertEqual(self.ws.statuses()["RULE-002"], "code only")


if __name__ == "__main__":
    unittest.main()
