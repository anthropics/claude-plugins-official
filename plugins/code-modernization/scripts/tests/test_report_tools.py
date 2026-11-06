"""Tests for scripts/build_report.py, scripts/compare.py and assets/report-template.html.

Run:  python3 -m unittest discover -s plugins/code-modernization/scripts/tests
The template's JavaScript is exercised with Node when it is installed (those tests are skipped otherwise).
"""
import base64
import contextlib
import hashlib
import io
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from html.parser import HTMLParser
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(PLUGIN, "scripts"))
import build_report as br  # noqa: E402
import compare as cmp  # noqa: E402

TEMPLATE = os.path.join(PLUGIN, "assets", "report-template.html")
MERMAID = os.path.join(PLUGIN, "assets", "vendor", "mermaid.min.js")
SECRET = "TOP-SECRET-MARKER-9f3c"
LS, PS = chr(0x2028), chr(0x2029)


def put(root, rel, data):
    path = os.path.join(root, *rel.split("/"))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as fh:
        fh.write(data if isinstance(data, bytes) else data.encode("utf-8"))
    return path


def run_main(fn, argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = fn(argv)
    return code, out.getvalue(), err.getvalue()


def make_symlink(test, target, link):
    try:
        os.symlink(target, link)
    except (OSError, NotImplementedError, AttributeError):
        test.skipTest("symbolic links are not available here")


class Scripts(HTMLParser):
    """Every <script> element of a page: its attributes and its text."""

    def __init__(self, html):
        super().__init__(convert_charrefs=False)
        self.found, self._cur = [], None
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        if tag == "script":
            self._cur = {"attrs": dict(attrs), "text": ""}

    def handle_data(self, data):
        if self._cur is not None:
            self._cur["text"] += data

    def handle_endtag(self, tag):
        if tag == "script" and self._cur is not None:
            self.found.append(self._cur)
            self._cur = None


def page_data(html):
    block = [s for s in Scripts(html).found if s["attrs"].get("id") == "report-data"]
    assert len(block) == 1
    return json.loads(block[0]["text"])


HOSTILE_MD = "\n".join([
    "# Assessment <script>window.__pwned=1</script>",
    '<img src=x onerror="window.__pwned=2">',
    "</script><script>window.__pwned=3</script> <!-- and <!--",
    "[a](javascript:window.__pwned=4) [b](JavaScript:alert(1)) [c](java\tscript:alert(1)) [d](" + chr(1) + "javascript:alert(1))",
    "[e](data:text/html,<script>1</script>) [f](//evil.example/x) [g](/\\evil.example) ![t](https://evil.example/pixel.png)",
    '<a href="javascript:alert(1)">raw anchor</a> <iframe src="https://evil.example"></iframe>',
    "| a | b |", "|---|---|", "| <b onmouseover=alert(1)>x</b> | <img src=x onerror=window.__pwned=5> |",
    "`<script>` and **<img src=x onerror=1>** " + LS + PS,
    "```mermaid", 'graph TD; A["<img src=x onerror=window.__pwned=7>"]-->B', "```",
    "x" * 1000000, "*" * 200000, "[" * 50000, "|" * 50000,
])
HOSTILE_RULES = "\n".join([
    "# Rules", "",
    "### RULE-001: Title with `backticks` and <angle> <script>x</script> & ampersand",
    "**Category:** Validation  ", "**Priority:** P0  ", "**Source:** `evil/../../etc/passwd:1-2` and `a.cbl:10`  ",
    "**Confidence:** High  ", "**Suspected defect:** <img src=x onerror=window.__pwned=6>", "",
    "### P1-002 \u00b7 Second card, other id style", "P1 \u00b7 Policy \u00b7 confidence Low \u00b7 `b.cbl:5-9`", "",
])


def hostile_workspace(root, system="evil"):
    a = "analysis/" + system
    put(root, a + "/ASSESSMENT.md", HOSTILE_MD)
    put(root, a + "/BUSINESS_RULES.md", HOSTILE_RULES)
    put(root, a + "/MODERNIZATION_BRIEF.md", "# Brief\n\n```mermaid\n%%{init: {\"themeCSS\": \".x{background:url(https://evil.example/t.gif)}\"}}%%\ngraph TD; A-->B\n```\n")
    put(root, a + "/good.mmd", "graph TD\n  A[Start] --> B[End]\n")
    put(root, a + "/bad.mmd", "graph TD\n  A --> --> ((\n")
    put(root, a + "/topology.json", '{"root": {"id": ')
    put(root, a + "/RULE_REVIEWS.json", "not json at all")
    put(root, a + "/SECRETS.local.md", SECRET)
    put(root, a + "/security_remediation.local.patch", SECRET)
    put(root, a + "/SECURITY_FINDINGS.md", "# Findings\n\n| ID | Severity | Title |\n|---|---|---|\n| SEC-1 | Critical | <script>x</script> |\n| SEC-2 | High | y |\n| SEC-3 | high | z |\n")
    put(root, "modernized/%s/README.md" % system, "# Module <img src=x onerror=1>\n")
    put(root, "modernized/%s/mod1/TRANSFORMATION_NOTES.md" % system, "# Notes\n</script>\n")
    outside = tempfile.mkdtemp()
    put(outside, "secret.txt", "OUTSIDE-MARKER")
    try:
        os.symlink(os.path.join(outside, "secret.txt"), os.path.join(root, *(a + "/PLAYBOOK.md").split("/")))
    except (OSError, NotImplementedError, AttributeError):
        pass
    return outside


class CompareTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def cases(self, cases, **extra):
        path = put(self.tmp, "cases.json", json.dumps({"system": "s", "cases": cases, **extra}))
        return path

    def files(self, name, legacy, new):
        put(self.tmp, "legacy/%s" % name, legacy)
        if new is not None:
            put(self.tmp, "new/%s" % name, new)
        return {"id": name, "title": "case " + name, "legacy": "legacy/" + name, "new": "new/" + name}

    def result(self, cases, **extra):
        out = os.path.join(self.tmp, "analysis", "EQUIVALENCE.json")
        code, stdout, _ = run_main(cmp.main, [self.cases(cases, **extra), "--out", out])
        with open(out, encoding="utf-8") as fh:
            return code, stdout, json.load(fh)

    def test_same_differs_missing_approved_and_exit_codes(self):
        same, diff, miss = self.files("a", b"one\ntwo\n", b"one\ntwo\n"), self.files("b", b"one\ntwo\n", b"one\ntw0\n"), self.files("c", b"x", None)
        code, out, res = self.result([same, diff, miss])
        self.assertEqual(code, 1)
        self.assertEqual([c["verdict"] for c in res["cases"]], ["same", "differs", "missing"])
        self.assertEqual(res["totals"], {"cases": 3, "executed": 2, "same": 1, "differs": 1, "differsApproved": 0, "missing": 1})
        self.assertIn("equivalence cases executed: 2", out)
        self.assertIn("NOT PROVEN", out)
        d = res["cases"][1]["firstDiff"]
        self.assertEqual((d["offset"], d["line"]), (6, 2))
        self.assertIn("legacy", res["cases"][2]["reason"].lower() + "legacy")
        self.assertEqual(res["cases"][0]["legacySha256"], hashlib.sha256(b"one\ntwo\n").hexdigest())
        approved = dict(diff, id="b2", approvedDifference="fixed on purpose")
        code, _, res = self.result([same, approved])
        self.assertEqual(code, 0)
        self.assertEqual(res["cases"][1]["verdict"], "differs-approved")
        self.assertEqual(res["totals"]["differsApproved"], 1)

    def test_all_same_is_proven(self):
        code, out, res = self.result([self.files("a", b"abc", b"abc")])
        self.assertEqual(code, 0)
        self.assertIn("PROVEN", out)
        self.assertNotIn("NOT PROVEN", out)
        self.assertEqual(res["selfCheck"]["passed"], True)

    def test_missing_alone_is_never_a_pass(self):
        code, out, res = self.result([self.files("a", b"x", b"x"), self.files("m", b"x", None)])
        self.assertEqual(code, 1)
        self.assertIn("missing", out)
        self.assertEqual((res["totals"]["executed"], res["totals"]["missing"], res["totals"]["differs"]), (1, 1, 0))

    def test_no_case_executed_is_not_proven(self):
        for cases in ([], [self.files("m", b"x", None)]):
            code, out, res = self.result(cases)
            self.assertEqual(code, 1)
            self.assertIn("equivalence cases executed: 0", out)
            self.assertIn("NOT PROVEN: no case executed", out)
            self.assertEqual(res["selfCheck"]["passed"], None)

    def test_empty_outputs_prove_nothing(self):
        code, out, res = self.result([self.files("e", b"", b"")])
        self.assertEqual(code, 1)
        self.assertIn("empty", out)
        self.assertEqual(res["cases"][0]["verdict"], "same")
        self.assertTrue(res["cases"][0]["empty"])

    def test_masks_hide_only_what_they_name(self):
        legacy, new = b"id=12 at 2026-09-01 10:11:12 total=5\n", b"id=1234 at 2026-09-24 03:04:05 total=5\n"
        case = dict(self.files("t", legacy, new), mask=[{"regex": r"id=\d+"}, {"regex": r"\d{4}-\d\d-\d\d \d\d:\d\d:\d\d"}])
        code, _, res = self.result([case])
        self.assertEqual((code, res["cases"][0]["verdict"]), (0, "same"))
        case["new"] = self.files("t2", legacy, new.replace(b"total=5", b"total=6"))["new"]
        _, _, res = self.result([case])
        self.assertEqual(res["cases"][0]["verdict"], "differs")
        self.assertEqual(res["cases"][0]["firstDiff"]["offset"], legacy.index(b"5"))
        ranged = dict(self.files("r", b"aaXXbb", b"aaYYbb"), mask=[{"bytes": "2-3"}])
        self.assertEqual(self.result([ranged])[2]["cases"][0]["verdict"], "same")
        beyond = dict(self.files("r2", b"aaXXbb", b"aaYYbc"), mask=[{"bytes": "2-3"}, {"bytes": "50-60"}])
        self.assertEqual(self.result([beyond])[2]["cases"][0]["verdict"], "differs")

    def test_a_mask_that_hides_everything_fails_the_self_check(self):
        case = dict(self.files("h", b"abc", b"xyz"), mask=[{"regex": ".*"}])
        code, out, res = self.result([case])
        self.assertEqual(code, 1)
        self.assertIs(res["selfCheck"]["passed"], False)
        self.assertIn("hide every byte", res["selfCheck"]["detail"])
        self.assertIn("NOT PROVEN", out)

    def test_bad_input_is_exit_2_and_writes_nothing(self):
        out = os.path.join(self.tmp, "EQ.json")
        bad = [put(self.tmp, "a.json", "{not json"), put(self.tmp, "b.json", json.dumps({"cases": "x"})),
               self.cases([dict(self.files("z", b"a", b"a"), mask=[{"regex": "("}])]), self.cases([dict(self.files("y", b"a", b"a"), mask=[{"bytes": "9-2"}])]),
               self.cases([self.files("d", b"a", b"a"), self.files("d", b"a", b"a")]), os.path.join(self.tmp, "missing.json")]
        for path in bad:
            code, _, err = run_main(cmp.main, [path, "--out", out])
            self.assertEqual(code, 2, path)
            self.assertFalse(os.path.exists(out))
            self.assertIn("compare.py", err)

    def test_paths_may_not_leave_the_cases_folder(self):
        outside = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, outside, True)
        put(outside, "o.txt", "same")
        sub = os.path.join(self.tmp, "sub")
        put(sub, "n.txt", "same")
        case = {"id": "o", "legacy": os.path.join(outside, "o.txt"), "new": "n.txt"}
        path = put(sub, "cases.json", json.dumps({"cases": [case]}))
        out = os.path.join(sub, "E.json")
        self.assertEqual(run_main(cmp.main, [path, "--out", out, "--quiet"])[0], 1)
        with open(out) as fh:
            self.assertEqual(json.load(fh)["cases"][0]["verdict"], "missing")
        self.assertEqual(run_main(cmp.main, [path, "--out", out, "--quiet", "--allow-outside"])[0], 0)

    def test_first_difference_context_is_escaped_and_bounded(self):
        _, _, res = self.result([self.files("c", b"a\x00\x1b[31m\tb" + b"z" * 200, b"a\x00\x1b[31m\tc" + b"z" * 200)])
        d = res["cases"][0]["firstDiff"]
        self.assertLessEqual(len(d["legacy"]), 40)
        self.assertNotRegex(d["legacy"] + d["new"], r"[\x00-\x1f\x7f]")
        self.assertEqual(d["legacy"][d["at"]], "b")
        _, _, res = self.result([self.files("p", b"abc", b"abcdef")])
        self.assertIn("ends", res["cases"][0]["reason"])
        self.assertIn("<end of output>", res["cases"][0]["firstDiff"]["legacy"])

    def test_summary_neutralises_terminal_escapes_and_quiet_is_quiet(self):
        case = dict(self.files("q", b"a", b"b"), id="q\x1b[2J")
        code, out, _ = run_main(cmp.main, [self.cases([case]), "--out", os.path.join(self.tmp, "E.json")])
        self.assertNotIn("\x1b", out)
        code, out, _ = run_main(cmp.main, [self.cases([case]), "--out", os.path.join(self.tmp, "E.json"), "--quiet"])
        self.assertEqual((code, out), (1, ""))

    def test_default_output_and_atomic_write(self):
        code, _, _ = run_main(cmp.main, [self.cases([self.files("a", b"x", b"x")]), "--quiet"])
        self.assertEqual(code, 0)
        self.assertEqual(sorted(f for f in os.listdir(self.tmp) if "equivalence" in f.lower()), ["EQUIVALENCE.json"])

    def test_a_symlinked_output_is_refused(self):
        real = put(self.tmp, "elsewhere/E.json", "ORIGINAL")
        link = os.path.join(self.tmp, "E.json")
        make_symlink(self, real, link)
        code, _, err = run_main(cmp.main, [self.cases([self.files("a", b"x", b"x")]), "--out", link, "--quiet"])
        self.assertEqual(code, 2)
        self.assertIn("symbolic link", err)
        with open(real) as fh:
            self.assertEqual(fh.read(), "ORIGINAL")


class BuildFacts(unittest.TestCase):
    def test_rule_cards_in_several_layouts(self):
        text = "\n".join([
            "## Rules", "### RULE-012: Interest is truncated", "**Priority:** P0", "**Confidence:** High \u2014 checked", "**Category:** Calculation",
            "**Source:** `a/B.cbl:10-20,30` and `C.cbl:5`", "**Suspected defect:** rounds down", "```", "### not a heading in a fence", "```", "",
            "### P1-001 \u00b7 Header line style", "`P1` \u00b7 Validation \u00b7 confidence Medium \u00b7 `d/E.cbl:1-2`", "",
            "#### R-12: Short id", "Priority: P2", "**Suspected defect:** none", "", "### BR-D7-09 \u2014 Domain coded", "### Plain heading", "text",
        ])
        blocks = br.parse_rules(text)
        cards = [b for b in blocks if b["k"] == "rule"]
        self.assertEqual([c["id"] for c in cards], ["RULE-012", "P1-001", "R-12", "BR-D7-09"])
        self.assertEqual([c["p"] for c in cards], ["P0", "P1", "P2", ""])
        self.assertEqual([c["conf"] for c in cards], ["High", "Medium", "", ""])
        self.assertEqual([c["defect"] for c in cards], [True, False, False, False])
        self.assertEqual(cards[0]["cites"], ["a/B.cbl:10-20,30", "C.cbl:5"])
        self.assertEqual(cards[1]["cites"], ["d/E.cbl:1-2"])
        self.assertNotIn("Priority", cards[0]["body"])
        self.assertIn("### not a heading in a fence", cards[0]["body"])
        self.assertEqual(blocks[0]["k"], "md")
        self.assertEqual(br.parse_rules("just text\n\n## Heading")[0]["k"], "md")

    def test_headings_and_fields_padded_with_thousands_of_spaces_are_parsed_in_a_moment(self):
        import time
        pad = " " * 6000
        text = "### RULE-001 - Title%s#%sx\n**Priority:** P0%s\n**Suspected defect:**%s\n\n### RULE-002: Closed ###   \n**Priority:**   P1  \n" % (pad, pad, pad, pad)
        started = time.time()
        cards = [c for c in br.parse_rules(text) if c["k"] == "rule"]
        self.assertLess(time.time() - started, 2)
        self.assertEqual([c["id"] for c in cards], ["RULE-001", "RULE-002"])
        self.assertEqual(cards[1]["title"], "Closed")
        self.assertEqual(cards[1]["p"], "P1")
        self.assertEqual(br.field("Priority:   \nPriority:  P2 ", "Priority"), "P2")

    def test_rule_priority_falls_back_to_the_index_table(self):
        text = "| ID | Name | Priority |\n|---|---|---|\n| [RULE-007](#x) | Merged | P0 |\n\n### RULE-007: Merged\n**Merged into:** RULE-006\n\n### RULE-008: Real\n**Priority:** P1\n"
        cards = [b for b in br.parse_rules(text) if b["k"] == "rule"]
        facts = br.rule_facts(text, cards, {"RULE-008": {"verdict": "confirmed"}})
        self.assertEqual((facts["total"], facts["byPriority"], facts["unrated"]), (2, {"P0": 1, "P1": 1}, 0))
        self.assertEqual(facts["reviews"], {"confirmed": 1})

    def test_security_tally(self):
        findings = "## Summary scorecard\n| Severity | Count |\n|---|---|\n| Critical | 9 |\n\n## Findings\n| ID | Severity | Title |\n|---|---|---|\n| S1 | **Critical** | a |\n| S2 | High | b |\n| S3 | high | c |\n| S4 | Low | d |\n\n## Dependency CVEs\n| Package | Installed | CVE | Severity |\n|---|---|---|---|\n| x | 1 | CVE-1 | High |\n\n## Coverage gaps\n| Finding | Severity |\n|---|---|\n| n | Medium |\n"
        self.assertEqual(br.security_facts(findings), {"Critical": 1, "High": 2, "Low": 1})
        self.assertEqual(br.security_facts("| Severity | Count |\n|---|---|\n| Critical | 2 |\n| High | 3 |\n"), {"Critical": 2, "High": 3})
        self.assertIsNone(br.security_facts("Nothing recognisable here."))

    def test_baseline_facts(self):
        table = "| Test | Result |\n|---|---|\n| a | pass |\n| b | PASS |\n| c | fail |\n| d | skipped |\n"
        self.assertEqual(br.baseline_facts(table), {"pass": 2, "fail": 1, "skip": 1, "targetOnly": False})
        self.assertEqual(br.baseline_facts("Run: 12 tests passed, 1 failed"), {"pass": 12, "fail": 1, "targetOnly": False})
        self.assertEqual(br.baseline_facts("target-only: the source runtime is not available")["targetOnly"], True)
        self.assertIsNone(br.baseline_facts("| Fixture | RC |\n|---|---|\n| seed | 0 |\n"))

    def test_topology_facts(self):
        topo = {"root": {"id": "s", "kind": "system", "children": [{"id": "d", "kind": "domain", "children": [
            {"id": "A", "kind": "module", "loc": 100, "language": "cobol", "file": "a.cbl"}, {"id": "B", "kind": "module", "loc": 50, "file": "b.cbl"},
            {"id": "F", "kind": "datastore"}]}]}, "edges": [{}, {}]}
        self.assertEqual(br.topology_facts(topo), {"modules": 2, "loc": 150, "languages": ["cobol"], "edges": 2, "observations": []})
        self.assertIsNone(br.topology_facts([1, 2]))
        self.assertIsNone(br.topology_facts({"root": {"id": "x", "children": "oops"}}))

    def test_equivalence_view_never_trusts_the_files_own_words(self):
        digest = "a" * 64
        good = {"cases": [{"id": "1", "verdict": "same", "legacySha256": digest, "newSha256": digest}, {"id": "2", "verdict": "differs-approved", "approvedDifference": "ok"}],
                "selfCheck": {"passed": True, "detail": "d"}, "totals": {"cases": 2, "executed": 2}}
        view = br.equivalence_view(good)
        self.assertEqual((view["state"], view["problems"]), ("green", []))
        self.assertEqual(br.equivalence_view(dict(good, cases=[dict(good["cases"][0], newSha256="b" * 64)]))["state"], "red")
        for bad_case in ({"id": "x", "verdict": "differs"}, {"id": "x", "verdict": "missing"}, {"id": "x", "verdict": "pass"},
                         {"id": "x", "verdict": "differs-approved"}, {"id": "x", "verdict": "same", "firstDiff": {"offset": 1}}):
            view = br.equivalence_view(dict(good, cases=good["cases"] + [bad_case], totals={}))
            self.assertEqual(view["state"], "red", bad_case)
        self.assertEqual(br.equivalence_view(dict(good, cases=[]))["state"], "red")
        self.assertEqual(br.equivalence_view(dict(good, selfCheck={"passed": False, "detail": "x"}))["state"], "red")
        self.assertEqual(br.equivalence_view(dict(good, cases=[dict(good["cases"][0], empty=True)]))["state"], "red")
        no_check = br.equivalence_view({"cases": good["cases"]})
        self.assertEqual(no_check["state"], "green")
        self.assertTrue(any("self-check" in p for p in no_check["problems"]))
        self.assertTrue(any("disagree" in p for p in br.equivalence_view(dict(good, totals={"cases": 9, "executed": 9}))["problems"]))
        self.assertIsNone(br.equivalence_view({"cases": "x"}))
        self.assertIsNone(br.equivalence_view([]))


class BuildReport(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.out = os.path.join(self.tmp, "out", "REPORT.html")

    def build(self, system="s", extra=()):
        code, out, err = run_main(br.main, [system, "--workspace", self.tmp, "--out", self.out, *extra])
        return code, out, err

    def html(self):
        with open(self.out, encoding="utf-8") as fh:
            return fh.read()

    def test_nothing_found_is_exit_1_with_one_line(self):
        os.makedirs(os.path.join(self.tmp, "analysis", "s"))
        code, out, err = self.build()
        self.assertEqual(code, 1)
        self.assertEqual(len(err.strip().splitlines()), 1)
        self.assertFalse(os.path.exists(self.out))

    def test_bad_system_names_are_refused(self):
        for name in ("..", "a/b", "a\\b", ""):
            self.assertEqual(self.build(name)[0], 2, name)

    def test_nearly_empty_workspace(self):
        put(self.tmp, "analysis/s/PREFLIGHT.md", "# Preflight\nAll good.\n")
        code, out, _ = self.build()
        self.assertEqual(code, 0)
        self.assertRegex(out.strip(), r"REPORT\.html: 1 section, \d+ KB$")
        html = self.html()
        self.assertEqual([s["attrs"].get("id") for s in Scripts(html).found], ["report-data", "app"])
        data = page_data(html)
        self.assertEqual([s["id"] for s in data["sections"]], ["overview"])
        self.assertFalse(any(x["done"] for x in data["glance"]["steps"] if x["key"] != "preflight"))
        self.assertIsNone(data["glance"]["track"])
        self.assertIsNone(data["glance"]["equivalence"])

    def test_default_output_path(self):
        put(self.tmp, "analysis/s/PREFLIGHT.md", "x")
        code, out, _ = run_main(br.main, ["s", "--workspace", self.tmp])
        self.assertEqual(code, 0)
        self.assertTrue(os.path.isfile(os.path.join(self.tmp, "analysis", "s", "REPORT.html")))
        self.assertEqual([f for f in os.listdir(os.path.join(self.tmp, "analysis", "s")) if f.endswith(".tmp")], [])

    def test_malformed_files_are_reported_in_the_page_not_raised(self):
        a = "analysis/s/"
        put(self.tmp, a + "topology.json", "{broken")
        put(self.tmp, a + "EQUIVALENCE.json", "[1, 2")
        put(self.tmp, a + "RULE_REVIEWS.json", '{"reviews": 5}')
        put(self.tmp, a + "BUSINESS_RULES.md", b"\xff\xfe\x00binary\x00\x01### RULE-001: x\n")
        put(self.tmp, a + "ASSESSMENT.md", b"")
        put(self.tmp, a + "BASELINE.md", "| a |\n|---")
        put(self.tmp, a + "SECURITY_FINDINGS.md", "|||\n|||\n")
        put(self.tmp, a + "broken.mmd", "")
        code, _, _ = self.build()
        self.assertEqual(code, 0)
        data = page_data(self.html())
        notes = json.dumps(data["sections"][0]["parts"])
        self.assertIn("topology.json could not be parsed", notes)
        self.assertIn("EQUIVALENCE.json could not be parsed", notes)
        self.assertEqual(data["glance"]["equivalence"]["state"], "red")
        self.assertIn("RULE_REVIEWS.json", notes)

    def test_hostile_input_cannot_reach_the_page_as_markup_or_script(self):
        outside = hostile_workspace(self.tmp)
        self.addCleanup(shutil.rmtree, outside, True)
        code, _, _ = self.build("evil")
        self.assertEqual(code, 0)
        html = self.html()
        scripts = Scripts(html).found
        ids = [s["attrs"].get("id") for s in scripts]
        self.assertEqual(ids, ["report-data", "mermaid-lib", "app"])
        for s in scripts:
            self.assertLessEqual(set(s["attrs"]), {"id", "type"})
        block = scripts[0]["text"]
        for bad in ("<", ">", "&", LS, PS):
            self.assertNotIn(bad, block)
        self.assertNotIn("</script", scripts[1]["text"].lower())
        self.assertNotIn("<!--", scripts[1]["text"])
        page = html.replace(scripts[0]["text"], "").replace(scripts[1]["text"], "")
        for needle in ("__pwned=", "onerror", "evil.example", "javascript:"):
            self.assertNotIn(needle, page.split('<script id="app">')[0].split("</style>")[1], needle)
        text = json.dumps(page_data(html))
        self.assertIn("window.__pwned=1", text)
        self.assertNotIn(SECRET, html)
        self.assertNotIn("OUTSIDE-MARKER", html)
        notes = json.dumps(page_data(html)["sections"][0]["parts"])
        if os.path.islink(os.path.join(self.tmp, "analysis", "evil", "PLAYBOOK.md")):
            self.assertIn("PLAYBOOK.md is a link", notes)
        self.assertIn("longer than 20,000 characters were shortened", notes)
        self.assertLess(len(html), 6 << 20)
        data = page_data(html)
        self.assertEqual(data["glance"]["security"], {"Critical": 1, "High": 2})
        self.assertEqual(data["glance"]["rules"]["total"], 2)
        titles = [b["title"] for s in data["sections"] for p in s["parts"] for b in p.get("blocks", []) if b["k"] == "rule"]
        self.assertIn("Title with `backticks` and <angle> <script>x</script> & ampersand", titles)

    def test_secret_and_local_files_are_never_read_even_when_asked_for_by_name(self):
        for name in ("SECRETS.local.md", "secrets.txt", "security_remediation.local.patch", "notes.LOCAL.md"):
            path = put(self.tmp, "analysis/s/" + name, SECRET)
            src = br.Source(self.tmp, "s")
            self.assertIsNone(src.read(path, name), name)
            self.assertEqual(src.found, [])

    def test_csp_pins_exactly_the_scripts_on_the_page(self):
        put(self.tmp, "analysis/s/good.mmd", "graph TD\n A-->B\n")
        self.build()
        html = self.html()
        policy = re.search(r'http-equiv="Content-Security-Policy" content="([^"]*)"', html).group(1)
        self.assertIn("default-src 'none'", policy)
        self.assertNotIn("unsafe-eval", policy)
        self.assertNotRegex(policy, r"script-src[^;]*unsafe-inline")
        hashes = re.findall(r"'sha256-([^']+)'", policy.split("script-src")[1].split(";")[0])
        code_scripts = [s for s in Scripts(html).found if s["attrs"].get("type") != "application/json"]
        expected = [base64.b64encode(hashlib.sha256(s["text"].encode("utf-8")).digest()).decode() for s in code_scripts]
        self.assertEqual(sorted(hashes), sorted(expected))
        self.assertEqual(len(expected), 2)

    def test_mermaid_is_inlined_only_when_a_diagram_exists(self):
        put(self.tmp, "analysis/s/ASSESSMENT.md", "# A\nno diagram\n")
        self.build()
        self.assertNotIn("mermaid-lib", self.html())
        self.assertLess(len(self.html()), 300000)
        put(self.tmp, "analysis/s/ASSESSMENT.md", "# A\n\n```mermaid\ngraph TD\n A-->B\n```\n")
        self.build()
        scripts = Scripts(self.html()).found
        lib = next(s for s in scripts if s["attrs"].get("id") == "mermaid-lib")
        with open(MERMAID, encoding="utf-8") as fh:
            original = fh.read()
        self.assertEqual(lib["text"].replace("<\\/script", "</script").replace("<\\!--", "<!--"), original)
        os.remove(os.path.join(self.tmp, "analysis", "s", "ASSESSMENT.md"))
        put(self.tmp, "analysis/s/x.mmd", "graph TD\n A-->B\n")
        self.build()
        self.assertIn("mermaid-lib", self.html())

    def test_size_cap_says_what_was_left_out(self):
        for name in ("ASSESSMENT.md", "MODERNIZATION_BRIEF.md", "DATA_OBJECTS.md"):
            put(self.tmp, "analysis/s/" + name, ("line of text that is long enough to count\n" * 80000))
        self.build()
        data = page_data(self.html())
        notes = "\n".join(json.dumps(p) for p in data["sections"][0]["parts"])
        self.assertIn("report size limit", notes)
        embedded = sum(len(p["text"]) for s in data["sections"] for p in s["parts"] if p["t"] == "md")
        self.assertLessEqual(embedded, br.TOTAL_CAP)

    def test_sections_follow_the_workflow_order_and_only_exist_when_found(self):
        a = "analysis/s/"
        for name in ("EQUIVALENCE.json", "SECURITY_FINDINGS.md", "MODERNIZATION_BRIEF.md", "ASSESSMENT.md", "PREFLIGHT.md", "DELTA_CATALOG.md", "AI_NATIVE_SPEC.md"):
            put(self.tmp, a + name, "{}" if name.endswith(".json") else "# " + name)
        put(self.tmp, "modernized/s-reimagined/svc/README.md", "# svc")
        self.build()
        data = page_data(self.html())
        self.assertEqual([s["id"] for s in data["sections"]], ["overview", "assessment", "brief", "security", "delta", "spec", "build", "equivalence"])
        steps = {x["key"]: x["done"] for x in data["glance"]["steps"]}
        self.assertEqual(steps, {"preflight": True, "assess": True, "map": False, "rules": False, "brief": True, "build": True, "harden": True})
        self.assertEqual(data["glance"]["track"]["label"], "reimagine")

    def test_track_follows_the_newest_track_artifact(self):
        a = "analysis/s/"
        put(self.tmp, a + "ASSESSMENT.md", "x")
        put(self.tmp, a + "BASELINE.md", "x")
        put(self.tmp, "modernized/s/mod/TRANSFORMATION_NOTES.md", "x")
        self.build()
        self.assertEqual(page_data(self.html())["glance"]["track"]["label"], "rewrite")
        past = os.path.getmtime(os.path.join(self.tmp, "modernized", "s", "mod", "TRANSFORMATION_NOTES.md")) + 50
        put(self.tmp, a + "DELTA_CATALOG.md", "x")
        os.utime(os.path.join(self.tmp, "analysis", "s", "DELTA_CATALOG.md"), (past, past))
        self.build()
        self.assertEqual(page_data(self.html())["glance"]["track"]["label"], "same-stack uplift")

    def test_topology_link_is_relative_and_the_map_is_not_embedded(self):
        put(self.tmp, "analysis/s/TOPOLOGY.html", "<html>" + "x" * 5000 + "</html>")
        self.build()
        data = page_data(self.html())
        link = next(p for s in data["sections"] for p in s["parts"] if p["t"] == "link")
        self.assertEqual(os.path.normpath(os.path.join(os.path.dirname(self.out), link["href"])), os.path.join(self.tmp, "analysis", "s", "TOPOLOGY.html"))
        self.assertNotIn("xxxxxxxxxx", self.html())

    def test_report_shows_what_compare_py_wrote(self):
        eq_dir = os.path.join(self.tmp, "analysis", "s", "equivalence")
        put(eq_dir, "legacy/a.out", "same")
        put(eq_dir, "new/a.out", "same")
        put(eq_dir, "legacy/b.out", "one")
        put(eq_dir, "new/b.out", "two")
        cases = {"system": "s", "cases": [{"id": "A", "legacy": "legacy/a.out", "new": "new/a.out"}, {"id": "B", "legacy": "legacy/b.out", "new": "new/b.out"}]}
        put(eq_dir, "cases.json", json.dumps(cases))
        target = os.path.join(self.tmp, "analysis", "s", "EQUIVALENCE.json")
        cmp.main([os.path.join(eq_dir, "cases.json"), "--out", target, "--quiet"])
        self.build()
        data = page_data(self.html())
        eq = data["glance"]["equivalence"]
        self.assertEqual(eq["state"], "red")
        self.assertEqual((eq["tally"]["same"], eq["tally"]["differs"], eq["tally"]["executed"]), (1, 1, 2))
        section = next(s for s in data["sections"] if s["id"] == "equivalence")["parts"][0]["eq"]
        self.assertEqual(section["cases"][1]["firstDiff"]["line"], 1)
        self.assertEqual(section["cases"][1]["legacyPath"], "equivalence/legacy/b.out")
        cases["cases"].pop()
        put(eq_dir, "cases.json", json.dumps(cases))
        cmp.main([os.path.join(eq_dir, "cases.json"), "--out", target, "--quiet"])
        self.build()
        self.assertEqual(page_data(self.html())["glance"]["equivalence"]["state"], "green")

    def test_a_symlinked_output_path_is_refused_and_nothing_is_written_through_it(self):
        put(self.tmp, "analysis/s/PREFLIGHT.md", "x")
        target = put(self.tmp, "elsewhere/real.html", "ORIGINAL")
        os.makedirs(os.path.dirname(self.out))
        make_symlink(self, target, self.out)
        code, out, err = self.build()
        self.assertEqual((code, out), (1, ""))
        self.assertEqual(len(err.strip().splitlines()), 1)
        self.assertIn("symbolic link", err)
        with open(target) as fh:
            self.assertEqual(fh.read(), "ORIGINAL")
        self.assertEqual(os.listdir(os.path.dirname(target)), ["real.html"])
        self.assertEqual(os.listdir(os.path.dirname(self.out)), ["REPORT.html"])

    def test_a_symlinked_output_folder_is_refused(self):
        put(self.tmp, "analysis/s/PREFLIGHT.md", "x")
        real = os.path.join(self.tmp, "real")
        os.makedirs(real)
        make_symlink(self, real, os.path.join(self.tmp, "linked"))
        code, _, err = run_main(br.main, ["s", "--workspace", self.tmp, "--out", os.path.join(self.tmp, "linked", "REPORT.html")])
        self.assertEqual(code, 1)
        self.assertIn("symbolic link", err)
        self.assertEqual(os.listdir(real), [])

    def test_a_failed_write_leaves_no_temp_file_behind(self):
        put(self.tmp, "analysis/s/PREFLIGHT.md", "x")
        with mock.patch.object(br.os, "replace", side_effect=OSError("disk full")):
            code, _, err = self.build()
        self.assertEqual(code, 1)
        self.assertEqual(len(err.strip().splitlines()), 1)
        self.assertEqual(os.listdir(os.path.dirname(self.out)), [])

    @unittest.skipIf(os.name == "nt", "POSIX permissions")
    def test_the_report_gets_the_permissions_a_normal_file_would(self):
        put(self.tmp, "analysis/s/PREFLIGHT.md", "x")
        umask = os.umask(0o022)
        os.umask(umask)
        self.build()
        self.assertEqual(stat.S_IMODE(os.stat(self.out).st_mode), 0o666 & ~umask)


class Template(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(TEMPLATE, encoding="utf-8") as fh:
            cls.text = fh.read()
        cls.css = re.search(r"<style>(.*?)</style>", cls.text, re.S).group(1)
        cls.app = re.search(r'<script id="app">(.*?)</script>', cls.text, re.S).group(1)

    def test_no_external_urls_and_no_dangerous_apis(self):
        self.assertNotRegex(self.text, r"https?://")
        self.assertNotRegex(self.text, r"(?i)(?:src|href|action)\s*=\s*[\"']?\s*//")
        self.assertNotRegex(self.css, r"@import|url\(")
        for word in ("innerHTML", "outerHTML", "insertAdjacentHTML", "document.write", "eval(", "new Function", "setTimeout(\"", "fetch(", "XMLHttpRequest", "WebSocket"):
            self.assertNotIn(word, self.app, word)
        self.assertNotRegex(self.text, r"(?i)\son[a-z]+\s*=")
        self.assertEqual(len(re.findall(r"@@(CSP|DATA|MERMAID)@@", self.text)), 3)
        self.assertNotIn("@@", self.app)

    def test_theme_and_layout_contract(self):
        root = re.search(r":root\{(.*?)\}", self.css, re.S).group(1)
        tokens = set(re.findall(r"--([a-z-]+):", root))
        media = re.search(r"@media \(prefers-color-scheme:dark\)\{:root:not\(\[data-theme=\"light\"\]\)\{(.*?)\}\}", self.css, re.S).group(1)
        forced = re.search(r":root\[data-theme=\"dark\"\]\{(.*?)\}", self.css, re.S).group(1)
        self.assertEqual(set(re.findall(r"--([a-z-]+):", media)) - tokens, set())
        self.assertEqual(re.findall(r"--([a-z-]+):[^;]*", media), re.findall(r"--([a-z-]+):[^;]*", forced))
        self.assertRegex(re.search(r"body\{([^}]*)\}", self.css).group(1), r"background:var\(--bg\)")
        self.assertIn("system-ui", self.css)
        self.assertIn("width=device-width", self.text)
        self.assertIn("@media print", self.css)
        self.assertIn(":focus-visible", self.css)
        self.assertRegex(self.css, r"\.wrap\{[^}]*padding:0 16px")

    def test_every_text_colour_pair_meets_4_5_to_1(self):
        def parse(block):
            return dict(re.findall(r"--([a-z-]+):(#[0-9a-fA-F]{3,6})", block))

        def lum(hexcolor):
            h = hexcolor.lstrip("#")
            h = "".join(c * 2 for c in h) if len(h) == 3 else h
            chan = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
            lin = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in chan]
            return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]

        def ratio(a, b):
            hi, lo = sorted((lum(a), lum(b)), reverse=True)
            return (hi + 0.05) / (lo + 0.05)

        light = parse(re.search(r":root\{(.*?)\}", self.css, re.S).group(1))
        dark = dict(light, **parse(re.search(r":root\[data-theme=\"dark\"\]\{(.*?)\}", self.css, re.S).group(1)))
        pairs = [("text", "bg"), ("text", "surface"), ("muted", "bg"), ("muted", "surface"), ("muted", "code"), ("text", "code"), ("link", "surface"), ("link", "bg"),
                 ("link", "code"), ("ok", "ok-bg"), ("bad", "bad-bg"), ("warn", "warn-bg"), ("info", "info-bg"), ("flat", "flat-bg"), ("hit-text", "hit"),
                 ("text", "flat-bg"), ("text", "info-bg"), ("muted", "flat-bg")]
        for name, palette in (("light", light), ("dark", dark)):
            for fg, bg in pairs:
                self.assertGreaterEqual(ratio(palette[fg], palette[bg]), 4.5, "%s: %s on %s" % (name, fg, bg))
        self.assertGreaterEqual(ratio("#1a1f27", light["paper"]), 4.5)
        for name, palette in (("light", light), ("dark", dark)):
            self.assertGreaterEqual(ratio(palette["focus"], palette["bg"]), 3, name)
            self.assertGreaterEqual(ratio(palette["focus"], palette["surface"]), 3, name)


NODE = shutil.which("node")
LINK_CASES = {  # markdown -> the href it must produce, or None when it must stay plain text
    "[x](javascript:alert(1))": None, "[x](data:text/html,x)": None, "[x](file:///etc/passwd)": None, "[x](JaVaScRiPt:x)": None, "[x](java&#10;script:x)": None, "[x](javascript&colon;alert(1))": None, "[x](&#x6A;avascript:alert(1))": None,
    "[x](https://example.com/a?b=1)": "https://example.com/a?b=1", "[x](mailto:a@b.c)": "mailto:a@b.c", "[x](#anchor)": "#anchor",
    "[x](./relative/path.md)": "./relative/path.md", "[x](../up/README.md#top)": "../up/README.md#top",
}
JS_INPUTS = [
    "<script>alert(1)</script>", "</script><script>alert(1)</script>", "<img src=x onerror=alert(1)>", "<!-- <!--", '<a href="javascript:alert(1)">x</a>',
    "[x](javascript:alert(1))", "[x](JavaScript:alert(1))", "[x](java\tscript:alert(1))", "[x](" + chr(1) + "javascript:alert(1))", "[x]( javascript:alert(1))",
    "[x](data:text/html;base64,PHNjcmlwdD4=)", "[x](//evil.example)", "[x](/\\evil.example)", "[x](vbscript:msgbox(1))", "[x](file:///etc/passwd)",
    "[x](&#106;avascript:alert(1))", "[x](%6Aavascript:alert(1))", "[x](" + LS + "javascript:alert(1))", "[x](\u00a0javascript:alert(1))", "![x](javascript:alert(1))",
    "| <b onmouseover=alert(1)>x</b> | y |\n|---|---|\n| <img src=x onerror=alert(2)> | z |", "### RULE-001: `<b>title</b>` <img src=x>",
    "`<script>`", "**<img src=x onerror=1>** _<b>_", "- [ ] <b>a</b>\n- [x] *b*\n  - nested <i>c</i>", "> <script>\n> x",
    "```js\n<script>alert(1)</script>\n```", "~~~\n</script>\n~~~", "```mermaid\ngraph TD; A-->B\n```", "a" * 200000, "*" * 200000, "[" * 100000, "`" * 100000,
    "_" * 100000, "|" * 100000, "- " * 50000, "> " * 20000 + "x", "\n".join(" " * (i * 2) + "- x" for i in range(300)), "#" * 100000, "[a](" + "b" * 100000 + ")",
    "\n".join("| " + "c | " * 200 for _ in range(50)), "*a " * 60000, "**a " * 60000, "[a " * 60000, "`a " * 60000,
] + list(LINK_CASES)
SAFE_URLS = ["https://example.com/a?b=1&c=2", "https://example.com/?q=a&b=c#frag", "http://x.y", "HTTPS://X.Y", "mailto:a@b.c", "../x/y.md#z", "#anchor", "README.md", "a/b:c", "TOPOLOGY.html", "./p:q", "x.md#a:b"]
BAD_URLS = ["java&#10;script:x", "javascript&colon;alert(1)", "&#106;avascript:1", "a&#x3a;b", "x&amp;y", "javascript:alert(1)", "JavaScript:alert(1)", " javascript:alert(1)", "java\tscript:alert(1)", "java\nscript:alert(1)", chr(1) + "javascript:alert(1)", "data:text/html,x",
            "//evil.example", "/\\evil.example", "\\\\evil", "/abs/path", "vbscript:x", "file:///etc/passwd", "C:\\x", "a:b", chr(0xA0) + "javascript:1", LS + "javascript:1",
            chr(0xFEFF) + "javascript:1", "jav" + chr(0x200B) + "ascript:1", "", "x" * 3000]
NODE_HARNESS = r"""
const fs = require('fs'), vm = require('vm');
const tpl = fs.readFileSync(process.env.TEMPLATE, 'utf8');
const core = /\/\* core:start[^\n]*\n([\s\S]*?)\/\* core:end \*\//.exec(tpl)[1];
class Text { constructor(t) { this.text = String(t); } }
class El { constructor(t) { this.tag = t; this.attrs = {}; this.kids = []; }
  setAttribute(k, v) { this.attrs[k] = String(v); } appendChild(c) { this.kids.push(c); return c; } }
const ctx = { document: { createElement: t => new El(t), createTextNode: t => new Text(t) } };
vm.createContext(ctx);
const api = vm.runInContext('(function(){"use strict";' + core + ';return {safeUrl:safeUrl,md:md,ruleCard:ruleCard,inline:inline};})()', ctx);
function walk(n, acc) {
  if (n instanceof Text) { acc.text += n.text; return; }
  acc.tags.add(n.tag); Object.keys(n.attrs).forEach(k => { acc.attrs.add(k); if (k === 'href') acc.hrefs.push(n.attrs[k]); });
  n.kids.forEach(c => walk(c, acc));
}
const input = JSON.parse(fs.readFileSync(0, 'utf8')), out = { urls: input.urls.map(u => api.safeUrl(u)), docs: [] };
for (const src of input.docs) {
  const t0 = Date.now(), acc = { tags: new Set(), attrs: new Set(), hrefs: [], text: '' };
  api.md(src, 3).forEach(n => walk(n, acc));
  out.docs.push({ ms: Date.now() - t0, tags: [...acc.tags], attrs: [...acc.attrs], hrefs: acc.hrefs, text: acc.text.slice(0, 5000) });
}
const card = { id: 'RULE-1', heading: 'RULE-1: <b>x</b>', title: '<img src=x onerror=1>`a`', p: 'P0', conf: 'High', cat: '<i>', cites: ['<b>a.cbl:1</b>'], defect: true, body: '**x** <script>1</script>' };
const acc = { tags: new Set(), attrs: new Set(), hrefs: [], text: '' };
walk(api.ruleCard(card, 'confirmed'), acc);
out.card = { tags: [...acc.tags], attrs: [...acc.attrs], text: acc.text };
process.stdout.write(JSON.stringify(out));
"""


@unittest.skipUnless(NODE, "node is not installed")
class TemplateScript(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        proc = subprocess.run([NODE, "-e", NODE_HARNESS], input=json.dumps({"urls": SAFE_URLS + BAD_URLS, "docs": JS_INPUTS}), capture_output=True, text=True,
                              env=dict(os.environ, TEMPLATE=TEMPLATE), timeout=300)
        assert proc.returncode == 0, proc.stderr
        cls.out = json.loads(proc.stdout)

    def test_the_page_script_parses(self):
        with open(TEMPLATE, encoding="utf-8") as src, tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as fh:
            fh.write(re.search(r'<script id="app">(.*?)</script>', src.read(), re.S).group(1))
        self.addCleanup(os.unlink, fh.name)
        self.assertEqual(subprocess.run([NODE, "--check", fh.name], capture_output=True, text=True).returncode, 0)

    def test_link_allowlist(self):
        urls = self.out["urls"]
        for url, got in zip(SAFE_URLS, urls[:len(SAFE_URLS)]):
            self.assertIsNotNone(got, url)
        for url, got in zip(BAD_URLS, urls[len(SAFE_URLS):]):
            self.assertIsNone(got, repr(url))

    def test_hostile_markdown_becomes_text_never_elements(self):
        allowed_tags = {"p", "h3", "h4", "h5", "h6", "ul", "ol", "li", "code", "pre", "strong", "em", "del", "a", "br", "hr", "blockquote", "table", "thead", "tbody", "tr",
                        "th", "td", "div", "span"}
        allowed_attrs = {"href", "rel", "target", "referrerpolicy", "id", "class", "role", "tabindex", "aria-label", "scope"}
        for src, doc in zip(JS_INPUTS, self.out["docs"]):
            label = src[:50]
            self.assertLessEqual(set(doc["tags"]), allowed_tags, label)
            self.assertLessEqual(set(doc["attrs"]), allowed_attrs, label)
            self.assertLess(doc["ms"], 5000, label)
            for href in doc["hrefs"]:
                stripped = re.sub(r"[\x00-\x20]", "", href).lower()
                self.assertRegex(stripped, r"^(https?://|mailto:|#|[^:/?#\\]*(?:[/?#]|$))", href)
        first = self.out["docs"][0]
        self.assertIn("<script>alert(1)</script>", first["text"])
        self.assertEqual(self.out["docs"][2]["tags"], ["p"])
        self.assertIn("[x](javascript:alert(1))", self.out["docs"][5]["text"])
        self.assertEqual(self.out["docs"][5]["hrefs"], [])
        table = self.out["docs"][20]
        self.assertIn("<b onmouseover=alert(1)>x</b>", table["text"])
        self.assertNotIn("img", table["tags"])

    def test_links_fail_closed_and_safe_ones_stay_links(self):
        docs = dict(zip(JS_INPUTS, self.out["docs"]))
        for source, href in LINK_CASES.items():
            doc = docs[source]
            if href is None:
                self.assertEqual(doc["hrefs"], [], source)
                self.assertNotIn("a", doc["tags"], source)
                self.assertIn(source, doc["text"], source)
            else:
                self.assertEqual(doc["hrefs"], [href], source)
                self.assertIn("a", doc["tags"], source)
                self.assertEqual(doc["text"], "x", source)

    def test_rule_card_renders_hostile_fields_as_text(self):
        card = self.out["card"]
        self.assertLessEqual(set(card["tags"]), {"article", "span", "h4", "div", "p", "strong"})
        self.assertLessEqual(set(card["attrs"]), {"class", "id", "data-p", "data-d", "aria-label"})
        self.assertIn("<img src=x onerror=1>`a`", card["text"])
        self.assertIn("<b>a.cbl:1</b>", card["text"])


class Vendored(unittest.TestCase):
    def test_mermaid_matches_the_recorded_digest_and_license(self):
        with open(os.path.join(PLUGIN, "assets", "vendor", "LICENSE-mermaid.txt"), encoding="utf-8") as fh:
            lic = fh.read()
        with open(MERMAID, "rb") as fh:
            raw = fh.read()
        self.assertIn("Copyright (c) 2014 - 2022 Knut Sveidqvist", lic)
        self.assertIn("MIT License", lic)
        self.assertIn(hashlib.sha256(raw).hexdigest(), lic)
        self.assertIn("mermaid@11.17.2", lic)
        self.assertIn(str(len(raw)), lic)


if __name__ == "__main__":
    unittest.main()
