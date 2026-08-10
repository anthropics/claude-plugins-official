"""Tests for the payload-free local per-review usage summary."""

import contextlib
import io
import json
import pathlib
import sys
import tempfile
import unittest
from unittest import mock


HOOKS = pathlib.Path(__file__).resolve().parents[1] / "hooks"
sys.path.insert(0, str(HOOKS))

import _base  # noqa: E402
import security_reminder_hook as hook  # noqa: E402


class LocalUsageSummaryTests(unittest.TestCase):
    def setUp(self):
        with _base._USAGE_LOCK:
            _base._USAGE.clear()
            _base._USAGE.update({
                "in": 0, "out": 0, "cr": 0, "cw": 0, "cost": 0.0,
                "n": 0, "http_err_last": 0, "http_err_count": 0,
                "models": [], "sdk_cost": False, "table_cost": False,
                "local_summary_emitted": False,
            })

    def emit(self, metrics):
        messages = []
        with mock.patch.object(hook, "debug_log", messages.append), \
                contextlib.redirect_stdout(io.StringIO()):
            hook.emit_metrics(metrics)
        return messages

    def test_commit_review_aggregates_models_usage_and_cost_sources(self):
        _base._record_usage({
            "input_tokens": 10, "output_tokens": 4,
            "cache_read_input_tokens": 3, "cache_creation_input_tokens": 2,
        }, "claude-sonnet-4-6-20260101")
        _base._record_usage({
            "input_tokens": 20, "output_tokens": 6,
            "cache_read_input_tokens": 7, "cache_creation_input_tokens": 5,
        }, "claude-opus-4-7", cost_usd=0.125)

        messages = self.emit({
            "commit_review": True, "vulns_found": 2, "review_ms": 321,
        })

        self.assertEqual(len(messages), 1)
        summary = json.loads(messages[0])
        self.assertEqual(summary["review_layer"], "commit_review")
        self.assertEqual(summary["model_ids"], [
            "claude-sonnet-4-6-20260101", "claude-opus-4-7",
        ])
        self.assertEqual(summary["input_tokens"], 30)
        self.assertEqual(summary["output_tokens"], 10)
        self.assertEqual(summary["cache_read_input_tokens"], 10)
        self.assertEqual(summary["cache_creation_input_tokens"], 7)
        self.assertEqual(summary["api_call_count"], 2)
        self.assertAlmostEqual(summary["estimated_api_cost_usd"], 0.1250984)
        self.assertEqual(summary["cost_sources"], ["plugin_price_table", "sdk_reported"])
        self.assertEqual(summary["review_ms"], 321)
        self.assertEqual(summary["outcome"], "findings")

    def test_no_summary_without_api_usage(self):
        self.assertEqual(self.emit({"stop_review": True, "vulns_found": 0}), [])

    def test_summary_is_one_line_and_contains_no_review_payload(self):
        _base._record_usage({"input_tokens": 1}, "model\nFORGED")

        with tempfile.TemporaryDirectory() as td, \
                mock.patch.object(_base, "DEBUG_LOG_FILE", str(pathlib.Path(td) / "log")), \
                contextlib.redirect_stdout(io.StringIO()):
            hook.emit_metrics({
                "push_sweep": True, "vulns_found": 0,
                "prompt": "fixture prompt sentinel",
                "path": "/repo/private.py",
                "secret": "fixture-secret",
            })
            physical_lines = (pathlib.Path(td) / "log").read_text().splitlines()

        self.assertEqual(len(physical_lines), 1)
        line = physical_lines[0]
        self.assertNotIn("fixture prompt sentinel", line)
        self.assertNotIn("/repo/private.py", line)
        self.assertNotIn("fixture-secret", line)
        summary = json.loads(line.split("] ", 1)[1])
        self.assertEqual(summary["model_ids"], ["model\nFORGED"])


if __name__ == "__main__":
    unittest.main()
