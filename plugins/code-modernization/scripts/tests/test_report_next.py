"""Tests for the report's next-step decision (scripts/build_report.py next_step)."""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE)))
import build_report as br  # noqa: E402

ALL = dict(preflight=True, assess=True, map=True, rules=True, brief=True, build=True, harden=True)


class NextStep(unittest.TestCase):
    def cmd(self, done, glance=None):
        return br.next_step("sys", dict(ALL, **done), glance or {})["command"]

    def test_the_path_in_order(self):
        order = ["preflight", "assess", "map", "rules"]
        for i, key in enumerate(order):
            done = {k: False for k in order[i:]}
            done.update(brief=False, build=False, harden=False)
            self.assertTrue(self.cmd(done).startswith("/code-modernization:modernize-" + ["preflight", "assess", "map", "extract-rules"][i]))

    def test_flagged_rules_go_to_review_once_and_then_on(self):
        flagged = {"rules": {"defects": 2}}
        self.assertIn("modernize-review", self.cmd({"brief": False}, flagged))
        reviewed = {"rules": {"defects": 2, "reviews": {"confirmed": 1}}}
        self.assertIn("modernize-brief", self.cmd({"brief": False}, reviewed))

    def test_a_build_is_verified_before_anything_else(self):
        self.assertIn("modernize-verify", self.cmd({"harden": False}))
        self.assertIn("modernize-verify", self.cmd({"harden": False}, {"proof": {"verdict": "NOT PROVEN"}}))
        self.assertIn("modernize-harden", self.cmd({"harden": False}, {"proof": {"verdict": "PROVEN"}}))

    def test_everything_done_points_at_status_and_text_is_bounded(self):
        step = br.next_step("s", ALL, {"proof": {"verdict": "PROVEN"}})
        self.assertIn("modernize-status", step["command"])
        hostile = br.next_step("s", ALL, {"proof": {"verdict": "X" * 5000}})
        self.assertLess(len(hostile["why"]), 200)


if __name__ == "__main__":
    unittest.main()
