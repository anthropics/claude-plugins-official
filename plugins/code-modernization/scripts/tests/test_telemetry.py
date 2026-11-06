"""Tests for the usage counts (scripts/telemetry.py, scripts/telemetry.sh and the hooks that call them).

Run:  python3 -m unittest discover -s plugins/code-modernization/scripts/tests
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
import threading
import time
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(PLUGIN, "scripts"))
import telemetry as tm  # noqa: E402

RULES = """# Business rules

### RULE-001 · Interest posting
**Priority:** P0
**Confidence:** High
**Source:** a.cbl:10-20

Given a balance, when the month closes, then interest is posted.

### RULE-002 · Rounding
**Priority:** P1
**Source:** a.cbl:30-31

Given an amount, then it is truncated.

### RULE-003 · Odd limit
**Priority:** P0
**Suspected defect:** the limit is off by one
**Source:** b.java:5-6

Given a limit, then it applies.
"""
BRIEF = """# Brief

#### Phase 1: pilot
#### Phase 2: the rest

## 8. Approval Block

```
Approved by: Jane Doe  Date: 2026-09-24
Approval covers: Phase 1 only
```
"""
UNSIGNED = "## 8. Approval Block\n\n```\nApproved by: ________________  Date: __________\n```\n"
SECURITY = "# Security\n\n| Severity | Count |\n|---|---|\n| Critical | 2 |\n| High | 5 |\n| Medium | 9 |\n"
TOPOLOGY = {"root": {"kind": "root", "children": [
    {"kind": "module", "file": "a.cbl", "loc": 3000, "language": "cobol"},
    {"kind": "module", "file": "b.java", "loc": 1200, "language": "java"},
    {"kind": "module", "file": "Makefile", "loc": 5000, "language": "make"}]}, "edges": []}
CHECKS = ("tests", "rules", "same", "fresh", "canary", "source")


def module(name, **states):
    checks = [{"id": c, "state": states.get(c, "pass"), "detail": "x"} for c in CHECKS]
    return {"name": name, "track": "rewrite", "checks": checks, "evidence": {
        "tests": {"executed": 5, "failed": 0, "skipped": 0}, "fresh": {"inputs": 12, "executed": 12, "same": 12, "differs": 0, "missing": 0}}}


VERIFICATION = {"modules": [module("a"), module("b", canary="gap"), module("c", canary="gap"), module("d", tests="fail"), module("e", same="fail"),
                            module("f", source="fail")],
                "signoff": {"name": "", "role": "", "date": "", "decision": ""}}
CASES = [{"id": "s%d" % i, "verdict": "same"} for i in range(9)] + [{"id": "d1", "verdict": "differs"}, {"id": "m1", "verdict": "missing"}] + [
    {"id": "a%d" % i, "verdict": "differs-approved", "approvedDifference": "the owner accepted it"} for i in range(2)]
EQUIVALENCE = {"cases": CASES, "selfCheck": {"passed": True}}
REVIEWS = {"system": "sys", "version": 1, "reviews": {"RULE-001": {"verdict": "confirmed"}, "RULE-002": {"verdict": "wrong"},
                                                     "RULE-003": {"verdict": "discuss"}}}
STEP_BITS = dict(tm.STEPS)


def put(root, rel, data):
    path = os.path.join(root, *rel.split("/"))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(data if isinstance(data, str) else json.dumps(data))
    return path


def workspace(root, system="sys", parts=None):
    parts = parts or {}
    files = {"PREFLIGHT.md": "# Preflight\n", "ASSESSMENT.md": "# Assessment\n", "topology.json": TOPOLOGY, "BUSINESS_RULES.md": RULES,
             "RULE_REVIEWS.json": REVIEWS, "MODERNIZATION_BRIEF.md": BRIEF, "EQUIVALENCE.json": EQUIVALENCE, "VERIFICATION.json": VERIFICATION,
             "SECURITY_FINDINGS.md": SECURITY, "REPORT.html": "<html></html>"}
    files.update(parts)
    for name, data in files.items():
        if data is not None:
            put(root, "analysis/%s/%s" % (system, name), data)
    put(root, "modernized/%s/mod-a/x.txt" % system, "x")
    put(root, "modernized/%s/mod-b/x.txt" % system, "x")
    return root


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.data = os.path.join(self.tmp, "data")
        os.makedirs(self.data)
        clean = {k: v for k, v in os.environ.items() if k not in ("CODE_MODERNIZATION_TELEMETRY", "CLAUDE_PLUGIN_OPTION_TELEMETRY", "DISABLE_TELEMETRY",
                                                                  "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC", "CLAUDE_PLUGIN_DATA")}
        patcher = mock.patch.dict(os.environ, {**clean, "CLAUDE_PLUGIN_DATA": self.data}, clear=True)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.ws = workspace(os.path.join(self.tmp, "ws"))

    def hook(self, mode, payload):
        out = io.StringIO()
        with mock.patch.object(sys, "stdin", io.StringIO(json.dumps(payload))), contextlib.redirect_stdout(out):
            tm.hook(mode)
        return out.getvalue()


class Counts(Base):
    def test_the_full_workspace_is_counted_the_way_the_artifacts_say(self):
        s = tm.state_metrics(self.ws)
        self.assertEqual({k: s[k] for k in ("rules", "p0", "rev_ok", "rev_wrong", "phases", "built", "eq_cases", "eq_diff", "eq_appr",
                                            "v_proven", "v_partly", "v_not", "sec_crit", "sec_high", "map_kloc", "lang", "goal")},
                         dict(rules=3, p0=2, rev_ok=1, rev_wrong=1, phases=2, built=2, eq_cases=12, eq_diff=2, eq_appr=2, v_proven=1,
                              v_partly=2, v_not=3, sec_crit=2, sec_high=5, map_kloc=9, lang=1, goal=3))
        steps = ("preflight", "assess", "map", "rules", "reviewed", "brief", "approved", "built", "verified", "hardened", "report")
        self.assertEqual(s["done"], sum(STEP_BITS[n] for n in steps))

    def test_a_signed_proof_and_an_unsigned_brief(self):
        put(self.ws, "analysis/sys/VERIFICATION.json", dict(VERIFICATION, signoff={"name": "A. Person", "decision": "accepted"}))
        put(self.ws, "analysis/sys/MODERNIZATION_BRIEF.md", UNSIGNED)
        done = tm.state_metrics(self.ws)["done"]
        self.assertTrue(done & STEP_BITS["signed"])
        self.assertFalse(done & STEP_BITS["approved"])
        self.assertTrue(done & STEP_BITS["brief"])

    def test_nothing_is_reported_where_the_plugin_has_left_nothing(self):
        empty = os.path.join(self.tmp, "empty")
        put(empty, "analysis/other/data.csv", "a,b\n1,2\n")
        self.assertIsNone(tm.state_metrics(empty))
        self.assertIsNone(tm.state_metrics(os.path.join(self.tmp, "nowhere")))
        self.assertEqual(self.hook("state", {"cwd": empty}), "")

    def test_the_language_is_the_biggest_one_that_is_code(self):
        def lang(rows):
            return tm.language_code({"root": {"children": [{"kind": "module", "file": "f", "loc": n, "language": name} for name, n in rows]}})
        self.assertEqual(lang([("artifact", 9000), ("c", 2900), ("cpp", 650), ("make", 500)]), 7)
        self.assertEqual(lang([("C#", 10), ("Java", 5)]), 3)
        self.assertEqual(lang([("javascript", 10), ("java", 50)]), 2)
        self.assertEqual(lang([("make", 10), ("yaml", 5)]), 0)
        self.assertEqual(lang([("PL/I", 90000), ("JCL", 500)]), 99)
        self.assertEqual(lang([("C/C++", 10), ("make", 900)]), 7)
        self.assertEqual(lang([("Node.js", 10)]), 9)
        self.assertEqual(lang([("ASP.NET", 10), ("VB6", 20)]), 3)
        self.assertEqual(lang([("Java/JSP", 10)]), 2)
        self.assertEqual(lang([("Fortran", 10), ("Assembler", 5)]), 15)
        self.assertEqual(lang([("some new language", 10)]), 99)
        self.assertEqual(lang([]), 0)
        self.assertEqual(tm.language_code(None), 0)

    def test_the_goal_is_the_answer_after_the_word_goal_and_nothing_else(self):
        cases = [("- Goal: reimagine (rebuild it from scratch)", 4), ("## Goal\n- **Goal:** `uplift`. Then transform it.", 2),
                 ("## Goal\n**Transform** piece by piece", 3), ("- Goal: Understand it first", 1),
                 ("## Goal\n- **Goal:** `not-sure`. Run assess, then pick (uplift / transform / reimagine / understand).", 0),
                 ("- Goal: Move to a newer version of the same technology", 2), ("- Goal: Rewrite it in a different technology", 3),
                 ("nothing here about it, but uplift is a word", 0), ("", 0)]
        for text, want in cases:
            self.assertEqual(tm.goal_code(text, None), want, text)
        self.assertEqual(tm.goal_code("", ""), 3)
        self.assertEqual(tm.goal_code("", "-uplifted"), 2)
        self.assertEqual(tm.goal_code("- Goal: not sure", "-reimagined"), 4)

    def test_uplift_and_reimagine_leave_their_own_marks(self):
        ws = os.path.join(self.tmp, "up")
        put(ws, "analysis/sys/DELTA_CATALOG.md", "# Deltas\n")
        put(ws, "analysis/sys/BASELINE.md", "# Baseline\n")
        put(ws, "analysis/sys/PLAYBOOK.md", "# Playbook\n")
        put(ws, "modernized/sys-uplifted/pom.xml", "<x/>")
        put(ws, "modernized/sys-uplifted/mod/a.java", "x")
        s = tm.state_metrics(ws)
        self.assertEqual((s["goal"], s["built"]), (2, 1))
        self.assertEqual(s["done"], STEP_BITS["deltas"] + STEP_BITS["baseline"] + STEP_BITS["playbook"] + STEP_BITS["built"])

    def test_hostile_artifacts_give_whole_numbers_and_nothing_else(self):
        put(self.ws, "analysis/sys/VERIFICATION.json", {"modules": "x", "signoff": ["not", "a", "dict"]})
        put(self.ws, "analysis/sys/EQUIVALENCE.json", {"cases": [{"verdict": ["same"]}, 5, None, {"verdict": "same", "approvedDifference": {"a": 1}}]})
        put(self.ws, "analysis/sys/RULE_REVIEWS.json", {"reviews": {"RULE-001": "confirmed", "RULE-002": {"verdict": ["wrong"]}}})
        put(self.ws, "analysis/sys/topology.json", "{not json")
        s = tm.state_metrics(self.ws)
        self.assertEqual((s["v_proven"], s["v_partly"], s["v_not"]), (0, 0, 0))
        self.assertEqual((s["rev_ok"], s["rev_wrong"], s["map_kloc"], s["lang"]), (0, 0, 0, 0))
        self.assertTrue(all(type(v) is int and 0 <= v <= tm.COUNT_LIMIT for v in tm.ok(s).values()))

    def test_the_counts_come_from_the_case_list_and_the_modules_checks_not_from_the_files_own_totals(self):
        put(self.ws, "analysis/sys/EQUIVALENCE.json", {"cases": [{"id": "1", "verdict": "differs"}, {"id": "2", "verdict": "same"}, {"id": "3", "verdict": "differs"}],
                                                       "totals": {"executed": 100, "differs": 0, "differsApproved": 0, "missing": 0}})
        put(self.ws, "analysis/sys/VERIFICATION.json", {"modules": [module("a", tests="fail")], "overall": {"counts": {"PROVEN": 5, "PARTLY PROVEN": 0, "NOT PROVEN": 0}}})
        s = tm.state_metrics(self.ws)
        self.assertEqual((s["eq_cases"], s["eq_diff"], s["eq_appr"]), (3, 2, 0))
        self.assertEqual((s["v_proven"], s["v_partly"], s["v_not"]), (0, 0, 1))

    def test_a_linked_artifact_is_not_read(self):
        outside = os.path.join(self.tmp, "outside.md")
        with open(outside, "w") as fh:
            fh.write(RULES)
        os.remove(os.path.join(self.ws, "analysis", "sys", "BUSINESS_RULES.md"))
        try:
            os.symlink(outside, os.path.join(self.ws, "analysis", "sys", "BUSINESS_RULES.md"))
        except OSError:
            self.skipTest("no symbolic links here")
        s = tm.state_metrics(self.ws)
        self.assertEqual((s["rules"], s["done"] & STEP_BITS["rules"]), (0, 0))

    def test_the_newest_system_is_the_one_counted(self):
        workspace(self.ws, "old", {"BUSINESS_RULES.md": "### RULE-001 · One\n**Priority:** P0\n"})
        for f in os.scandir(os.path.join(self.ws, "analysis", "old")):
            os.utime(f.path, (1, 1))
        os.utime(os.path.join(self.ws, "analysis", "old"), (1, 1))
        self.assertEqual(tm.state_metrics(self.ws)["rules"], 3)
        put(self.ws, "analysis/old/NEW.md", "x")
        self.assertEqual(tm.state_metrics(self.ws)["rules"], 1)


class Commands(Base):
    def cmd(self, prompt):
        return tm.command_metrics(prompt, self.ws)

    def test_the_plugins_commands_have_a_number_each(self):
        for verb, n in tm.COMMANDS.items():
            prompt = "/code-modernization:modernize" + ("-" + verb if verb else "")
            self.assertEqual(self.cmd(prompt + " sys")["cmd"], n, prompt)
        self.assertEqual(self.cmd("/modernize")["cmd"], 1)
        self.assertEqual(self.cmd("  /code-modernization:modernize-verify")["cmd"], 11)
        self.assertEqual(self.cmd("/code-modernization:modernize-harden-scan x")["cmd"], 99)
        self.assertEqual([self.cmd("/modernize-" + v)["cmd"] for v in ("panel", "review-pane", "sign")], [20, 21, 22])
        self.assertEqual(self.cmd("/code-modernization:modernize-review")["cmd"], 6)
        self.assertEqual(self.cmd("/modernize-review")["cmd"], 6)          # the bare name is the plugin's command now that the pane's deck has its own

    def test_other_prompts_are_not_counted(self):
        for prompt in ("", None, "modernize this", "/modernizer", "/other:modernize", "please /modernize", "/code-modernization:assess", 5, {"a": 1}):
            self.assertIsNone(self.cmd(prompt), prompt)

    def test_the_command_says_where_the_system_stands_and_whether_source_was_given(self):
        s = self.cmd("/code-modernization:modernize-verify sys --source /work/x")
        self.assertEqual((s["has_source"], s["fresh"], s["systems"], s["goal"]), (1, 0, 1, 3))
        self.assertEqual(s["done"], tm.state_metrics(self.ws)["done"])
        new = tm.command_metrics("/code-modernization:modernize billing --source /a", os.path.join(self.tmp, "fresh-folder"))
        self.assertEqual((new["fresh"], new["systems"], new["done"], new["has_source"]), (1, 0, 0, 1))

    def test_the_permission_mode_is_a_number_from_a_fixed_list(self):
        for mode, want in (("default", 1), ("auto", 4), ("bypassPermissions", 5), ("something new", 0), (None, 0), (7, 0)):
            self.assertEqual(tm.command_metrics("/modernize", self.ws, mode)["perm"], want, mode)
        out = self.hook("command", {"cwd": self.ws, "prompt": "/modernize", "permission_mode": "plan"})
        self.assertEqual(json.loads(out)["metrics"]["perm"], 3)

    def test_a_named_system_is_the_one_counted_and_its_name_is_never_sent(self):
        workspace(self.ws, "other", {"BUSINESS_RULES.md": None, "EQUIVALENCE.json": None, "VERIFICATION.json": None})
        os.utime(os.path.join(self.ws, "analysis", "sys"), (1, 1))
        for f in os.scandir(os.path.join(self.ws, "analysis", "sys")):
            os.utime(f.path, (1, 1))
        named = self.cmd("/code-modernization:modernize-status sys")
        newest = self.cmd("/code-modernization:modernize-status")
        self.assertNotEqual(named["done"], newest["done"])
        self.assertEqual(named["systems"], 2)
        for value in named.values():
            self.assertIsInstance(value, int)


class Sending(Base):
    def test_every_key_is_defined_and_every_value_is_a_whole_number(self):
        self.assertLessEqual(len(tm.STATE_KEYS), tm.MAX_KEYS)
        self.assertLessEqual(len(tm.COMMAND_KEYS), tm.MAX_KEYS)
        self.assertEqual(list(tm.MEANING)[0], "pv")
        for keys in (tm.STATE_KEYS, tm.COMMAND_KEYS):
            self.assertEqual(keys[0], "pv")
            for k in keys:
                self.assertRegex(k, r"^[a-z][a-z0-9_]{0,39}$")
                self.assertIn(k, tm.MEANING)
        for out in (self.hook("state", {"cwd": self.ws}), self.hook("command", {"cwd": self.ws, "prompt": "/code-modernization:modernize-map"})):
            line = json.loads(out)
            self.assertEqual(list(line), ["metrics"])
            self.assertTrue(all(type(v) is int and 0 <= v <= tm.CAP for v in line["metrics"].values()), line)
            self.assertEqual(out.count("\n"), 1)

    def test_a_key_that_is_not_defined_never_goes_out(self):
        got = tm.ok({"pv": 1, "path": "/secret", "rules": "7", "p0": True, "goal": 2.9, "done": -3})
        self.assertEqual(dict(got), {"pv": 1, "rules": 7, "p0": 1, "goal": 2, "done": 0})

    def test_the_plugin_version_is_sent_and_matches_the_manifest(self):
        with open(os.path.join(PLUGIN, ".claude-plugin", "plugin.json")) as fh:
            major, minor, patch = (int(x) for x in json.load(fh)["version"].split("."))
        self.assertEqual(tm.plugin_version(), major * 10000 + minor * 100 + patch)
        self.assertGreater(tm.plugin_version(), 0)
        self.assertEqual(json.loads(self.hook("state", {"cwd": self.ws}))["metrics"]["pv"], tm.plugin_version())

    def test_the_same_counts_are_sent_once_and_a_change_is_sent_again(self):
        self.assertTrue(self.hook("state", {"cwd": self.ws}))
        self.assertEqual(self.hook("state", {"cwd": self.ws}), "")
        put(self.ws, "analysis/sys/RULE_REVIEWS.json", {"reviews": {"RULE-001": {"verdict": "wrong"}}})
        self.assertIn('"rev_wrong":1', self.hook("state", {"cwd": self.ws}))
        self.assertEqual(self.hook("state", {"cwd": self.ws}), "")
        self.assertTrue(self.hook("command", {"cwd": self.ws, "prompt": "/modernize"}))
        self.assertTrue(self.hook("command", {"cwd": self.ws, "prompt": "/modernize"}))

    def test_when_it_cannot_remember_it_sends_nothing_rather_than_repeat_every_turn(self):
        os.environ["CLAUDE_PLUGIN_DATA"] = os.path.join(self.tmp, "does-not-exist")
        blocked = os.path.join(self.tmp, "blocked")
        with mock.patch.object(tm.tempfile, "gettempdir", return_value=blocked), mock.patch.object(tm.os, "makedirs", side_effect=OSError("read-only")):
            self.assertEqual(self.hook("state", {"cwd": self.ws}), "")

    def test_the_debug_switch_says_why_each_hook_run_sent_nothing_in_the_plugins_data_folder(self):
        log = os.path.join(self.data, "telemetry-debug.log")
        with mock.patch.dict(os.environ, {"CODE_MODERNIZATION_TELEMETRY_DEBUG": "1"}):
            self.hook("state", {"cwd": self.ws})
            self.hook("state", {"cwd": self.ws})
            self.hook("state", {"cwd": os.path.join(self.tmp, "nowhere")})
            self.hook("command", {"cwd": self.ws, "prompt": "hello"})
            self.hook("command", {"cwd": self.ws, "prompt": "/modernize"})
            with mock.patch.dict(os.environ, {"CODE_MODERNIZATION_TELEMETRY": "0"}):
                self.hook("state", {"cwd": self.ws})
            with mock.patch.object(tm, "state_metrics", side_effect=KeyError("x")), mock.patch.object(sys, "stdin", io.StringIO("{}")), \
                    contextlib.redirect_stdout(io.StringIO()):
                tm.main(["telemetry.py", "state"])
        with open(log, encoding="utf-8") as fh:
            text = fh.read()
        for want in ("state: sent 19 values", "state: not sent, the counts are the same as last time", "state: not sent, the plugin has left no files here",
                     "command: not sent, not one of the plugin's commands", "command: sent 12 values", "state: not sent, CODE_MODERNIZATION_TELEMETRY is off",
                     "state: error KeyError at line"):
            self.assertIn(want, text)
        self.assertNotIn(self.tmp, text)

    def test_the_debug_switch_never_writes_anywhere_else_and_never_follows_a_link(self):
        victim = os.path.join(self.tmp, "victim.txt")
        with open(victim, "w") as fh:
            fh.write("keep")
        try:
            os.symlink(victim, os.path.join(self.data, "telemetry-debug.log"))
        except OSError:
            self.skipTest("no symbolic links here")
        elsewhere = os.path.join(self.tmp, "somewhere-else.log")
        with mock.patch.dict(os.environ, {"CODE_MODERNIZATION_TELEMETRY_DEBUG": elsewhere}):
            self.hook("state", {"cwd": self.ws})
        self.assertFalse(os.path.exists(elsewhere))      # a path in the variable is not a switch
        with mock.patch.dict(os.environ, {"CODE_MODERNIZATION_TELEMETRY_DEBUG": "1"}):
            self.hook("command", {"cwd": self.ws, "prompt": "/modernize"})
        with open(victim) as fh:
            self.assertEqual(fh.read(), "keep")

    def test_each_off_switch_stops_everything(self):
        for name, value in (("CODE_MODERNIZATION_TELEMETRY", "0"), ("CODE_MODERNIZATION_TELEMETRY", "Off"), ("CLAUDE_PLUGIN_OPTION_TELEMETRY", "false"),
                            ("CODE_MODERNIZATION_TELEMETRY", "disabled"), ("CODE_MODERNIZATION_TELEMETRY", "n"), ("CODE_MODERNIZATION_TELEMETRY", "none"),
                            ("CODE_MODERNIZATION_TELEMETRY", "2"), ("CLAUDE_PLUGIN_OPTION_TELEMETRY", "no"),
                            ("DISABLE_TELEMETRY", "1"), ("CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC", "true")):
            with mock.patch.dict(os.environ, {name: value}):
                self.assertTrue(tm.off_reason(), name)
                self.assertEqual(self.hook("state", {"cwd": self.ws}), "", name)
                self.assertEqual(self.hook("command", {"cwd": self.ws, "prompt": "/modernize"}), "", name)
        for name, value in (("CODE_MODERNIZATION_TELEMETRY", "1"), ("CODE_MODERNIZATION_TELEMETRY", ""), ("CLAUDE_PLUGIN_OPTION_TELEMETRY", "true"),
                            ("CLAUDE_PLUGIN_OPTION_TELEMETRY", "  TRUE "), ("DISABLE_TELEMETRY", "0")):
            with mock.patch.dict(os.environ, {name: value}):
                self.assertEqual(tm.off_reason(), "", name)

    def test_bad_hook_input_never_raises_and_never_prints(self):
        for raw in ("", "not json", "[1,2]", '{"cwd": 5, "prompt": ["x"]}', '{"cwd": "/no/such/dir"}'):
            out = io.StringIO()
            with mock.patch.object(sys, "stdin", io.StringIO(raw)), contextlib.redirect_stdout(out), mock.patch.object(tm.os, "getcwd", return_value=self.tmp):
                self.assertEqual(tm.main(["telemetry.py", "command"]), 0)
                self.assertEqual(tm.main(["telemetry.py", "state"]), 0)
            self.assertEqual(out.getvalue(), "", raw)

    def test_show_prints_what_would_be_sent_in_words_and_as_json(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            tm.show([self.ws, "--prompt", "/code-modernization:modernize-verify sys"])
        text = out.getvalue()
        for word in ("Sending is on", "rules", "business rules found", "steps that have left their file", "preflight, assess, map, rules", "modernize-verify"):
            self.assertIn(word, text)
        out = io.StringIO()
        with contextlib.redirect_stdout(out), mock.patch.dict(os.environ, {"CODE_MODERNIZATION_TELEMETRY": "0"}):
            tm.show([self.ws, "--json"])
        got = json.loads(out.getvalue())
        self.assertEqual(got["off"], "CODE_MODERNIZATION_TELEMETRY is off")
        self.assertEqual(got["state"]["rules"], 3)


class Hardening(Base):
    """What a hostile or odd workspace must not be able to do."""

    def test_counts_from_a_hundred_up_are_rounded_and_every_key_has_a_ceiling(self):
        got = tm.ok({"pv": 10000, "rules": 97, "p0": 26, "map_kloc": 344, "eq_cases": 17727, "sec_high": 10 ** 12, "done": 43247, "goal": 9, "perm": 99,
                     "phases": 5000, "systems": 500})
        self.assertEqual(dict(got), {"pv": 10000, "rules": 97, "p0": 26, "map_kloc": 340, "eq_cases": 18000, "sec_high": tm.COUNT_LIMIT, "done": 43247,
                                     "goal": 4, "perm": 6, "phases": 99, "systems": 99})
        self.assertEqual([tm.rounded(n) for n in (99, 100, 104, 105, 999, 1049, 1050, 17727)], [99, 100, 100, 110, 1000, 1000, 1100, 18000])

    def test_a_folder_of_another_tool_is_not_the_plugins_even_with_the_same_file_names(self):
        other = os.path.join(self.tmp, "other")
        put(other, "analysis/2024-q3/topology.json", TOPOLOGY)
        put(other, "analysis/2024-q3/BASELINE.md", "# baseline\n")
        put(other, "analysis/2024-q3/ASSESSMENT.md", "# assessment\n")
        self.assertIsNone(tm.state_metrics(other))
        put(other, "analysis/2024-q3/PREFLIGHT.md", "# the plugin's\n")
        self.assertIsNotNone(tm.state_metrics(other))

    def test_another_tools_commands_are_not_counted_and_the_newest_folder_need_not_be_the_plugins(self):
        self.assertIsNone(tm.command_metrics("/modernize-schema", self.ws))
        self.assertEqual(tm.command_metrics("/code-modernization:modernize-schema", self.ws)["cmd"], 99)
        put(self.ws, "analysis/zzz-data/results.csv", "a,b\n")
        self.assertEqual(tm.state_metrics(self.ws)["rules"], 3)

    def test_a_new_name_is_a_new_system_and_a_flags_value_is_not_a_name(self):
        new = tm.command_metrics("/code-modernization:modernize-preflight billing --source /x", self.ws)
        self.assertEqual((new["fresh"], new["done"], new["goal"], new["has_source"]), (1, 0, 0, 1))
        newest = tm.command_metrics("/modernize --source elsewhere", self.ws)
        self.assertEqual((newest["fresh"], newest["has_source"]), (0, 1))
        self.assertEqual(tm.system_word(["--source", "abc", "def"]), "def")
        self.assertIsNone(tm.system_word(["--source", "abc", "/work/x"]))

    def test_links_that_lead_outside_the_workspace_are_not_followed(self):
        outside = os.path.join(self.tmp, "outside")
        for i in range(7):
            put(outside, "d%d/x.txt" % i, "x")
        shutil.rmtree(os.path.join(self.ws, "modernized", "sys"))
        try:
            os.symlink(outside, os.path.join(self.ws, "modernized", "sys"))
        except OSError:
            self.skipTest("no symbolic links here")
        self.assertEqual(tm.state_metrics(self.ws)["built"], 0)
        elsewhere = os.path.join(self.tmp, "elsewhere")
        workspace(elsewhere, "real")
        linked = os.path.join(self.tmp, "linked")
        os.makedirs(linked)
        os.symlink(os.path.join(elsewhere, "analysis"), os.path.join(linked, "analysis"))
        self.assertEqual(tm.systems_in(linked), [])
        self.assertIsNone(tm.state_metrics(linked))

    def test_a_dangling_link_inside_a_system_does_not_drop_the_system(self):
        try:
            os.symlink(os.path.join(self.tmp, "gone"), os.path.join(self.ws, "analysis", "sys", "dangling"))
        except OSError:
            self.skipTest("no symbolic links here")
        self.assertEqual(tm.state_metrics(self.ws)["rules"], 3)

    def test_a_data_folder_that_is_itself_a_link_still_works(self):
        real = os.path.join(self.tmp, "real-data")
        os.makedirs(real)
        link = os.path.join(self.tmp, "data-link")
        try:
            os.symlink(real, link)
        except OSError:
            self.skipTest("no symbolic links here")
        with mock.patch.dict(os.environ, {"CLAUDE_PLUGIN_DATA": link}):
            self.assertTrue(self.hook("state", {"cwd": self.ws}))
        self.assertTrue(os.path.exists(os.path.join(real, "telemetry-state.json")))

    def test_an_artifact_built_to_make_a_pattern_slow_does_not_hold_anything_up(self):
        nasty = "### RULE-001 - t" + " " * 4000 + "x\n**Priority:** P0" + " " * 4000 + "x\n"
        put(self.ws, "analysis/sys/BUSINESS_RULES.md", nasty * 3)
        put(self.ws, "analysis/sys/SECURITY_FINDINGS.md", "| a |" + " " * 8000 + "x|\n|" + "-" * 5000 + "|\n")
        started = time.time()
        s = tm.state_metrics(self.ws)
        self.assertLess(time.time() - started, 3)
        self.assertGreaterEqual(s["rules"], 1)

    def test_whatever_happens_the_hook_gives_up_within_a_few_seconds_and_says_nothing(self):
        code = ("import sys, time; sys.path.insert(0, %r); import telemetry as tm; tm.state_metrics = lambda cwd: time.sleep(30); tm.hook('state')" %
                os.path.join(PLUGIN, "scripts"))
        started = time.time()
        done = subprocess.run([sys.executable, "-c", code], input=json.dumps({"cwd": self.ws}), capture_output=True, text=True, timeout=20,
                              env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
        self.assertLess(time.time() - started, 10)
        self.assertEqual((done.returncode, done.stdout), (0, ""))

    def test_the_alarm_is_cancelled_when_the_hook_returns(self):
        import signal
        self.hook("state", {"cwd": self.ws})
        if hasattr(signal, "alarm"):
            self.assertEqual(signal.alarm(0), 0)


class Environment(Base):
    """What the plugin says about the machine it runs on."""

    def test_the_shell_wrappers_answers_are_used_and_bounded(self):
        with mock.patch.dict(os.environ, {"CODE_MODERNIZATION_OS": "3", "CODE_MODERNIZATION_PY": "4", "CODE_MODERNIZATION_PATHF": "5"}):
            got = tm.command_metrics("/modernize", self.ws)
        self.assertEqual((got["os"], got["py"], got["pathf"]), (3, 4, 5))
        self.assertEqual(got["pyv"], sys.version_info[0] * 100 + sys.version_info[1])
        with mock.patch.dict(os.environ, {"CODE_MODERNIZATION_OS": "77", "CODE_MODERNIZATION_PY": "-1", "CODE_MODERNIZATION_PATHF": "x"}):
            got = tm.command_metrics("/modernize", self.ws)
        self.assertEqual((got["os"], got["py"]), (9, 0))
        self.assertIn(got["os"], range(0, 10))

    def test_this_machine_is_recognised_without_the_wrapper(self):
        self.assertIn(tm.os_code(), (1, 2, 3, 4))
        self.assertEqual(tm.python_status(), 0)

    def test_a_path_that_breaks_scripts_is_flagged_in_bits(self):
        self.assertEqual([tm.path_flags(p) for p in ("/plain/path", "/has a space", "/caf\u00e9", "/a b/caf\u00e9", "/" + "x" * 250, "/a b/caf\u00e9/" + "x" * 250)],
                         [0, 1, 2, 3, 4, 7])

    def test_health_carries_only_the_environment(self):
        got = json.loads(self.hook("health", {"cwd": self.ws}))["metrics"]
        self.assertEqual(sorted(got), sorted(tm.HEALTH_KEYS if hasattr(tm, "HEALTH_KEYS") else ["pv", "os", "py", "pyv", "pathf"]))
        self.assertTrue(all(type(v) is int for v in got.values()))


class Failures(Base):
    """A failure becomes a tool number and a kind number. Its text is read here and never sent."""

    CASES = [("Bash", "Exit code 127\nbash: python3: command not found", 1), ("Bash", "Exit code 127\n(eval):1: command not found: python3", 1),
             ("Bash", "'python3' is not recognized as an internal or external command", 1), ("Bash", "env: python3: No such file or directory", 1),
             ("Bash", "Python was not found; run without arguments to install from the Microsoft Store.", 2),
             ("Bash", "xcode-select: note: no developer tools were found at '/Applications/Xcode.app'", 3),
             ("Bash", "Exit code 1\n  File \"x.py\", line 3\nSyntaxError: invalid syntax", 4),
             ("Bash", "Traceback (most recent call last):\n  File \"/x/code-modernization/1.0.0/scripts/build_report.py\", line 9\nKeyError: 'a'", 5),
             ("Edit", "Permission for this action was denied by the auto mode classifier", 6), ("Bash", "Permission to use Bash with command x has been denied.", 6),
             ("Write", "EACCES: permission denied, open '/x'", 7), ("Bash", "Exit code 124\ncommand timed out after 120s", 8),
             ("Read", "File does not exist. Note: your current working directory is /x.", 9), ("Bash", "Exit code 127\n(eval):1: command not found: python3_not_a_real_program", 9),
             ("WebFetch", "connect ECONNREFUSED 127.0.0.1:443", 10), ("Bash", "npm ERR! 401 Unauthorized", 10), ("Bash", "ENOSPC: no space left on device", 11),
             ("Workflow", "scriptPath must be inside the working directory", 12), ("Read", "something nobody has seen before", 99)]

    def fail(self, tool, error, session="s1", **more):
        return tm.failure_metrics({"hook_event_name": "PostToolUseFailure", "tool_name": tool, "error": error, "session_id": session, **more}, self.ws)

    def test_each_kind_of_failure_gets_its_code(self):
        for tool, text, want in self.CASES:
            self.assertEqual(tm.failure_kind(text) or 99, want, text)
        for name, want in (("Bash", 1), ("Read", 2), ("MultiEdit", 3), ("Grep", 4), ("Task", 5), ("Workflow", 6), ("AskUserQuestion", 7), ("Skill", 8), ("WebSearch", 9),
                           ("mcp__x__y", 10), ("Whatever", 99), (None, 99)):
            self.assertEqual(tm.tool_code(name), want, name)

    def test_a_failure_is_numbers_only_and_once_per_kind_per_session(self):
        first = self.fail("Bash", "Exit code 127\nbash: python3: command not found")
        self.assertEqual((first["tool"], first["kind"]), (1, 1))
        self.assertEqual(list(first), ["pv", "os", "py", "pyv", "pathf", "tool", "kind"])
        self.assertTrue(all(type(v) is int for v in tm.ok(first).values()))
        self.assertNotIn("python", json.dumps(tm.ok(first)))
        self.assertIsNone(self.fail("Bash", "Exit code 127\nbash: python3: command not found"))
        self.assertIsNotNone(self.fail("Bash", "Exit code 127\nbash: python3: command not found", session="s2"))
        self.assertIsNotNone(self.fail("Bash", "ENOSPC: no space left on device"))
        self.assertIsNotNone(self.fail("Read", "ENOSPC: no space left on device"))

    def test_a_plain_non_zero_exit_and_an_interruption_say_nothing(self):
        self.assertIsNone(self.fail("Bash", "Exit code 1"))
        self.assertIsNone(self.fail("Bash", "  Exit code 2  "))
        self.assertIsNone(self.fail("Bash", "Exit code 127\nbash: python3: command not found", is_interrupt=True))
        self.assertIsNotNone(self.fail("Bash", "Exit code 1\ngrep: unmatched ["))

    def test_hostile_failure_text_never_crashes_and_never_leaves(self):
        for text in ("x" * 2_000_000, "\x00\x01" * 5000, "\u202e" * 3000, None, 5, {"a": 1}, ["Traceback"] * 100):
            got = self.fail("Bash", text, session="h%s" % id(text))
            if got is not None:
                self.assertTrue(all(type(v) is int for v in got.values()))
        secret = self.fail("Bash", "ENOSPC while writing /home/alice/secret-project/passwords.txt", session="p")
        self.assertNotIn("alice", json.dumps(tm.ok(secret)))

    def test_a_model_call_that_ended_a_turn_is_one_code(self):
        for text, want in (("rate_limit", 1), ("authentication_failed", 2), ("billing_error", 3), ("invalid_request", 4), ("server_error", 5), ("overloaded_error", 5),
                           ("max_output_tokens", 6), ("request timeout", 7), ("", 99), ("something new", 99)):
            got = tm.failure_metrics({"hook_event_name": "StopFailure", "error": text, "session_id": "m-" + text}, self.ws)
            self.assertEqual(got["api"], want, text)
            self.assertNotIn("tool", got)

    def test_the_hook_prints_one_line_of_numbers_and_then_nothing(self):
        payload = {"cwd": self.ws, "hook_event_name": "PostToolUseFailure", "tool_name": "Read", "error": "File does not exist.", "session_id": "z"}
        line = json.loads(self.hook("failure", payload))["metrics"]
        self.assertEqual((line["tool"], line["kind"]), (2, 9))
        self.assertEqual(self.hook("failure", payload), "")


class Runs(Base):
    def test_the_last_extraction_is_counted_from_its_own_statistics(self):
        put(self.ws, "analysis/sys/rules_result.json", {"stats": {"agents": 172, "failedModules": ["a", "b"], "droppedModules": ["c"], "skippedModules": ["d"], "unverified": 5}})
        got = tm.ok(tm.run_metrics(self.ws))
        self.assertEqual(dict(got), {"pv": tm.plugin_version(), "agents": 170, "wf_failed": 3, "wf_skip": 1, "wf_unver": 5})
        self.assertTrue(self.hook("run", {"cwd": self.ws}))
        self.assertEqual(self.hook("run", {"cwd": self.ws}), "")

    def test_no_statistics_or_odd_ones_say_nothing_or_zeros(self):
        self.assertIsNone(tm.run_metrics(self.ws))
        put(self.ws, "analysis/sys/rules_result.json", {"stats": {"agents": "many", "failedModules": "x", "unverified": [1]}})
        got = tm.ok(tm.run_metrics(self.ws))
        self.assertEqual((got["agents"], got["wf_failed"], got["wf_skip"], got["wf_unver"]), (0, 0, 0, 0))


class OwnErrors(Base):
    def crash(self, error):
        out = io.StringIO()
        with mock.patch.object(tm, "state_metrics", side_effect=error), mock.patch.object(sys, "stdin", io.StringIO("{}")), contextlib.redirect_stdout(out):
            self.assertEqual(tm.main(["telemetry.py", "state"]), 0)
        return out.getvalue()

    def test_the_plugins_own_errors_are_sent_as_a_kind_and_a_line_once(self):
        first = self.crash(ValueError("secret text about /home/alice"))
        line = json.loads(first)["metrics"]
        self.assertEqual(line["err"], 2)
        self.assertGreater(line["err_at"], 0)
        self.assertNotIn("secret", first)
        self.assertEqual(self.crash(ValueError("again")), "")
        self.assertEqual(json.loads(self.crash(UnicodeDecodeError("utf-8", b"", 0, 1, "bad")))["metrics"]["err"], 8)
        self.assertEqual(json.loads(self.crash(KeyError("k")))["metrics"]["err"], 1)
        self.assertEqual(json.loads(self.crash(RuntimeError("odd")))["metrics"]["err"], 99)

    def test_an_error_is_not_reported_when_counts_are_off(self):
        with mock.patch.dict(os.environ, {"CODE_MODERNIZATION_TELEMETRY": "0"}):
            self.assertEqual(self.crash(KeyError("k")), "")

    def test_without_an_alarm_signal_a_timer_stands_in_and_is_cancelled(self):
        class NoAlarm:
            pass
        with mock.patch.object(tm, "signal", NoAlarm()):
            self.assertTrue(self.hook("state", {"cwd": self.ws}))
        self.assertEqual([t for t in threading.enumerate() if isinstance(t, threading.Timer)], [])


class Shell(unittest.TestCase):
    """scripts/telemetry.sh must start Python only when the plugin is in use."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.bin = os.path.join(self.tmp, "bin")
        os.makedirs(self.bin)
        self.ws = workspace(os.path.join(self.tmp, "ws"))
        self.data = os.path.join(self.tmp, "data")
        os.makedirs(self.data)
        os.symlink(sys.executable, os.path.join(self.bin, "python3"))

    def run_hook(self, mode, payload, cwd=None, path=None, env=None):
        env = {"PATH": path if path is not None else self.bin + os.pathsep + "/usr/bin:/bin", "CLAUDE_PLUGIN_DATA": self.data, **(env or {})}
        done = subprocess.run(["/bin/sh", os.path.join(PLUGIN, "scripts", "telemetry.sh"), mode], input=json.dumps(payload), capture_output=True, text=True,
                              cwd=cwd or self.ws, env=env, timeout=60)
        self.assertEqual(done.returncode, 0, done.stderr)
        return done.stdout

    def test_a_plugin_command_is_counted_and_the_end_of_a_turn_in_a_workspace_is_counted(self):
        out = self.run_hook("command", {"cwd": self.ws, "prompt": "/code-modernization:modernize-status sys"})
        self.assertEqual(json.loads(out)["metrics"]["cmd"], 13)
        self.assertEqual(json.loads(self.run_hook("state", {"cwd": self.ws}))["metrics"]["rules"], 3)
        self.assertEqual(self.run_hook("state", {"cwd": self.ws}), "")

    def test_it_starts_nothing_when_the_plugin_is_not_in_use(self):
        no_python = os.path.join(self.tmp, "nopy")
        os.makedirs(no_python)
        for tool in ("grep", "dirname", "uname", "cat"):
            os.symlink(shutil.which(tool), os.path.join(no_python, tool))
        elsewhere = os.path.join(self.tmp, "elsewhere")
        os.makedirs(elsewhere)
        self.assertEqual(self.run_hook("command", {"prompt": "write me a poem"}), "")
        self.assertEqual(self.run_hook("command", {"prompt": "/commit"}), "")
        self.assertEqual(self.run_hook("state", {"cwd": elsewhere}, cwd=elsewhere), "")
        self.assertEqual(self.run_hook("nonsense", {}), "")
        # no python at all: quiet for a turn's end, and a typed command is reported in numbers by the shell itself
        self.assertEqual(self.run_hook("state", {"cwd": self.ws}, path=no_python), "")
        said = json.loads(self.run_hook("command", {"prompt": "/modernize"}, path=no_python))["metrics"]
        self.assertEqual((said["cmd"], said["py"], said["pyv"]), (1, 1, 0))

    def toolbox(self, name, **fake):
        """A PATH folder holding only the tools the wrapper uses plus fake ones: name=script text, or "python" for the real interpreter."""
        d = os.path.join(self.tmp, name)
        os.makedirs(d)
        for tool in ("grep", "dirname", "sed", "head", "id", "mkdir", "cat", "uname"):
            if tool not in fake and shutil.which(tool):
                os.symlink(shutil.which(tool), os.path.join(d, tool))
        for tool, body in fake.items():
            path = os.path.join(d, tool)
            if body == "python":
                os.symlink(sys.executable, path)
            else:
                with open(path, "w") as fh:
                    fh.write(body)
                os.chmod(path, 0o755)
        return d

    def say(self, mode, payload, **kw):
        out = self.run_hook(mode, payload, **kw)
        return json.loads(out)["metrics"] if out else None

    def test_windows_is_recognised_and_a_missing_python_is_reported_by_the_shell(self):
        box = self.toolbox("win", uname="#!/bin/sh\necho MINGW64_NT-10.0-19045\n")
        got = self.say("command", {"prompt": "/code-modernization:modernize-verify x"}, path=box)
        self.assertEqual((got["os"], got["py"], got["cmd"], got["pyv"]), (3, 1, 11, 0))

    def test_the_windows_store_placeholder_is_a_broken_python3_and_python_is_used_instead(self):
        stub = "#!/bin/sh\necho 'Python was not found; run without arguments to install from the Microsoft Store.' >&2\nexit 49\n"
        box = self.toolbox("store", python3=stub, uname="#!/bin/sh\necho MSYS_NT-10.0\n")
        self.assertEqual(self.say("command", {"prompt": "/modernize"}, path=box)["py"], 3)       # nothing else to fall back to
        box = self.toolbox("store2", python3=stub, python="python", uname="#!/bin/sh\necho MSYS_NT-10.0\n")
        got = self.say("command", {"prompt": "/modernize"}, path=box)                             # python does the work, and says so
        self.assertEqual((got["os"], got["py"], got["cmd"]), (3, 4, 1))
        self.assertEqual(got["pyv"], sys.version_info[0] * 100 + sys.version_info[1])

    def test_a_python_that_is_too_old_and_one_that_crashes_are_told_apart(self):
        old = "#!/bin/sh\ncase \"$1\" in -c) echo 307 ;; *) exit 1 ;; esac\n"
        crash = "#!/bin/sh\ncase \"$1\" in -c) echo 311 ;; *) exit 1 ;; esac\n"
        self.assertEqual(self.say("command", {"prompt": "/modernize"}, path=self.toolbox("old", python3=old))["py"], 5)
        self.assertEqual(self.say("command", {"prompt": "/modernize"}, path=self.toolbox("crash", python3=crash))["py"], 6)

    def test_health_is_sent_once_per_version_even_when_python_is_missing(self):
        box = self.toolbox("nopy")
        first = self.say("health", {"cwd": self.ws}, path=box)
        self.assertEqual((first["py"], sorted(first)), (1, ["os", "pathf", "pv", "py", "pyv"]))
        self.assertIsNone(self.say("health", {"cwd": self.ws}, path=box))
        self.assertTrue(any(n.startswith("health-sent-") for n in os.listdir(self.data)))

    def test_health_from_python_is_sent_once_and_the_off_switch_stops_it(self):
        self.assertEqual(self.say("health", {"cwd": self.ws}, env={"CODE_MODERNIZATION_TELEMETRY": "0"}), None)
        self.assertFalse(any(n.startswith("health-sent-") for n in os.listdir(self.data)))
        first = self.say("health", {"cwd": self.ws})
        self.assertEqual(first["py"], 0)
        self.assertIsNone(self.say("health", {"cwd": self.ws}))

    def test_a_python_failure_is_reported_by_the_shell_when_python_cannot_run(self):
        box = self.toolbox("nopy2")
        put(self.ws, "analysis/sys/PREFLIGHT.md", "# x\n")
        got = self.say("failure", {"tool_name": "Bash", "error": "Exit code 127\nbash: python3: command not found"}, path=box)
        self.assertEqual((got["tool"], got["kind"], got["py"]), (1, 1, 1))
        self.assertIsNone(self.say("failure", {"tool_name": "Read", "error": "File does not exist."}, path=box))

    def test_a_folder_with_a_space_and_an_accent_is_flagged(self):
        odd = os.path.join(self.tmp, "my caf\u00e9 work")
        os.makedirs(odd)
        got = self.say("command", {"prompt": "/modernize"}, cwd=odd)
        self.assertEqual(got["pathf"], 3)

    def test_python_starts_only_where_the_plugin_has_left_its_files(self):
        marker = os.path.join(self.tmp, "started")
        fake = os.path.join(self.tmp, "fakebin")
        os.makedirs(fake)
        with open(os.path.join(fake, "python3"), "w") as fh:
            fh.write("#!/bin/sh\ntouch %s\ncat >/dev/null\n" % marker)
        os.chmod(os.path.join(fake, "python3"), 0o755)
        path = fake + os.pathsep + "/usr/bin:/bin"
        other = os.path.join(self.tmp, "other")
        put(other, "analysis/results/data.csv", "a,b\n")
        self.run_hook("state", {"cwd": other}, cwd=other, path=path)
        self.assertFalse(os.path.exists(marker))
        put(other, "analysis/results/PREFLIGHT.md", "# x\n")
        self.run_hook("state", {"cwd": other}, cwd=other, path=path)
        self.assertTrue(os.path.exists(marker))

    def test_it_leaves_no_bytecode_in_the_plugins_folder(self):
        root = os.path.join(self.tmp, "plugin")
        for rel in ("scripts/telemetry.sh", "scripts/telemetry.py", "scripts/build_report.py", ".claude-plugin/plugin.json"):
            os.makedirs(os.path.dirname(os.path.join(root, rel)), exist_ok=True)
            shutil.copy(os.path.join(PLUGIN, rel), os.path.join(root, rel))
        done = subprocess.run(["/bin/sh", os.path.join(root, "scripts", "telemetry.sh"), "state"], input=json.dumps({"cwd": self.ws}), capture_output=True,
                              text=True, cwd=self.ws, env={"PATH": self.bin + os.pathsep + "/usr/bin:/bin", "CLAUDE_PLUGIN_DATA": self.data}, timeout=60)
        self.assertIn('"metrics"', done.stdout)
        self.assertEqual(sorted(os.listdir(os.path.join(root, "scripts"))), ["build_report.py", "telemetry.py", "telemetry.sh"])

    def test_the_off_switch_reaches_the_script(self):
        self.assertEqual(self.run_hook("state", {"cwd": self.ws}, env={"CODE_MODERNIZATION_TELEMETRY": "0"}), "")


class Shipped(unittest.TestCase):
    """What ships must agree with itself: the manifest, the hooks, the README and the changelog."""

    def read(self, *parts):
        with open(os.path.join(PLUGIN, *parts), encoding="utf-8") as fh:
            return fh.read()

    def test_the_hooks_call_scripts_that_exist_and_are_asynchronous(self):
        hooks = json.loads(self.read("hooks", "hooks.json"))["hooks"]
        want = {"UserPromptSubmit": ["command"], "Stop": ["state", "run"], "SessionStart": ["health"], "PostToolUseFailure": ["failure"], "StopFailure": ["failure"]}
        self.assertEqual(sorted(hooks), sorted(want))
        for event, groups in hooks.items():
            modes = []
            for group in groups:
                for h in group["hooks"]:
                    self.assertTrue(h["asyncRewake"])
                    script = re.search(r"\$\{CLAUDE_PLUGIN_ROOT\}/(scripts/\w+\.sh)", h["command"]).group(1)
                    self.assertTrue(os.path.isfile(os.path.join(PLUGIN, script)), script)
                    modes.append(h["command"].split()[-1])
            self.assertEqual(modes, want[event], event)

    def test_the_manifest_has_a_version_and_the_option_that_turns_counts_off(self):
        manifest = json.loads(self.read(".claude-plugin", "plugin.json"))
        self.assertRegex(manifest["version"], r"^\d+\.\d+\.\d+$")
        option = manifest["userConfig"]["telemetry"]
        self.assertEqual((option["type"], option["default"]), ("boolean", True))
        with open(os.path.join(PLUGIN, "..", "..", ".claude-plugin", "marketplace.json"), encoding="utf-8") as fh:
            entry = next(p for p in json.load(fh)["plugins"] if p["name"] == "code-modernization")
        self.assertNotIn("version", entry)  # the manifest is the one place the number lives

    def test_the_changelog_names_the_manifest_version_first(self):
        version = json.loads(self.read(".claude-plugin", "plugin.json"))["version"]
        first = re.search(r"(?m)^## \[?(\d+\.\d+\.\d+)", self.read("CHANGELOG.md"))
        self.assertEqual(first.group(1), version)

    def test_the_readme_lists_every_key_that_can_be_sent_and_the_off_switches(self):
        readme = self.read("README.md")
        section = readme[readme.index("## Telemetry"):]
        section = section[:section.index("\n## ", 5)] if "\n## " in section[5:] else section
        for key in tm.MEANING:
            self.assertIn("`%s`" % key, section, key)
        for word in ("CODE_MODERNIZATION_TELEMETRY", "Usage counts", "DISABLE_TELEMETRY", "telemetry.py show", "two significant figures", "TELEMETRY_DEBUG"):
            self.assertIn(word, section)


if __name__ == "__main__":
    unittest.main()
