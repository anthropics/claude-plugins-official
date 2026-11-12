"""Review rows keep their result, kind and time when they have more keys than
Claude Code keeps (the first 20)."""
import json

import pytest

import security_reminder_hook as hook

_USAGE = {"tok_in": 1, "tok_out": 1, "tok_cache_r": 0, "tok_cache_w": 0,
          "cost_usd": 0.1, "api_calls": 3}
_HTTP_ERR = {"http_err_last": 429, "http_err_count": 2}
# The keys the commit and push handlers pass, in their order.
_REFLOG = {"sha_via_reflog": True, "reflog_shas_n": 1}
_COMMIT_BASE = {"commit_review": True, "commit_review_on": True, "cwd_is_repo": False,
                "repo_resolution": 2, **_REFLOG, "diff_files_dropped": 3, "rate_count": 1}
_PUSH_BASE = {"push_sweep": True, "push_sweep_on": True, "cwd_is_repo": False,
              "repo_resolution": 2, "diff_files_dropped": 3, "rate_count": 1}
# A commit made with `git commit -q`, the common shape of a row with findings.
_QUIET_COMMIT = {"vulns_found": 1, "commit_review": True, "commit_review_on": True,
                 **_REFLOG, "rate_count": 1, "agentic": True, "candidates": 1, "survived": 1,
                 "race_winner": 1, "critical_count": 0, "high_count": 1,
                 "files_reviewed": 4, "review_ms": 9500}
_COMMIT_FINDINGS = {"vulns_found": 2, **_COMMIT_BASE, "agentic": True, "candidates": 3,
                    "survived": 3, "survived_after_sev": 2, "race_winner": 1,
                    "critical_count": 1, "high_count": 1,
                    "files_reviewed": 4, "review_ms": 9500, "deduped": 1}
_COMMIT_CLEAN = {"vulns_found": 0, **_COMMIT_BASE, "agentic": True, "candidates": 3,
                 "survived": 0, "race_winner": 1, "files_reviewed": 4, "review_ms": 9500}
_COMMIT_KNOWN = {"vulns_found": 0, **_COMMIT_BASE, "agentic": True, "candidates": 3,
                 "survived": 3, "race_winner": 1, "deduped": 3,
                 "files_reviewed": 4, "review_ms": 9500}
_PUSH = {**_PUSH_BASE, "pushed": 2, "unreviewed": 1, "prefix_advanced": 1, "vulns_found": 2,
         "files_reviewed": 4, "review_ms": 9500, "deduped": 1, "inflight_wait_s": 4}
_COMMIT_FAILED = {**_COMMIT_BASE, "agentic": False, "agentic_fallback": 2,
                  "race_winner": 1, "files_reviewed": 4, "review_ms": 9500}
_PUSH_FAILED = {**_PUSH_BASE, "inflight_wait_s": 4, "pushed": 2, "unreviewed": 1,
                "files_reviewed": 4, "review_ms": 9500}


@pytest.fixture(autouse=True)
def _clean(monkeypatch):
    monkeypatch.setattr(hook, "_PV", 20000)
    monkeypatch.setattr(hook, "_TAIL_METRICS", {"diff_seen": 0, "child_stderr": 2})
    monkeypatch.setattr(hook, "_REVIEWER_EFFORT_METRICS", {"rv_effort": 5})
    monkeypatch.setattr(hook, "_LAUNCHER_METRICS", {})
    monkeypatch.setattr(hook, "_LAUNCHER_DIRECT", {})
    monkeypatch.setattr(hook, "_log_usage", lambda usage: None)
    monkeypatch.setattr(hook, "_usage_metrics", lambda: dict(_USAGE))
    monkeypatch.setattr(hook, "_precheck_miss", False)
    monkeypatch.setattr(hook, "_net_error_metric", lambda: 0)
    monkeypatch.setattr(hook.llm, "gateway_cfg", lambda: 3)
    monkeypatch.delenv("SG_LAUNCHER_FALLBACK", raising=False)


def _row(capsys):
    return json.loads(capsys.readouterr().out)["metrics"]


def _kept(row, cap=hook._METRIC_KEY_CAP):
    """The part of a row Claude Code forwards."""
    return dict(list(row.items())[:cap])


_ROWS = {"quiet-commit": _QUIET_COMMIT, "commit-findings": _COMMIT_FINDINGS,
         "commit-clean": _COMMIT_CLEAN, "commit-known": _COMMIT_KNOWN, "push": _PUSH}


@pytest.mark.parametrize("http_err", [{}, _HTTP_ERR], ids=["", "http-errors"])
@pytest.mark.parametrize("name", _ROWS)
def test_result_and_time_are_kept(capsys, monkeypatch, name, http_err):
    metrics = _ROWS[name]
    monkeypatch.setattr(hook, "_usage_metrics", lambda: {**_USAGE, **http_err})
    hook.emit_metrics(metrics)
    row = _row(capsys)
    assert len(row) > hook._METRIC_KEY_CAP
    kept = _kept(row)
    must = ("vulns_found", "review_ms", "files_reviewed", "commit_review",
            "push_sweep", "agentic", "deduped")
    assert {k: kept.get(k) for k in must} == {k: metrics.get(k) for k in must}
    assert {"pv", *_USAGE, *http_err} <= set(kept)


def test_quiet_commit_loses_one_descriptive_key(capsys):
    hook.emit_metrics(_QUIET_COMMIT)
    row = _row(capsys)
    assert set(_QUIET_COMMIT) - set(_kept(row)) == {"high_count"}


@pytest.mark.parametrize("kind, metrics, split", [
    ("Commit", _COMMIT_FAILED, "commit_review"), ("Push", _PUSH_FAILED, "push_sweep")])
def test_failed_review_keeps_result_and_time(capsys, monkeypatch, kind, metrics, split):
    """With every key that can come ahead of them."""
    monkeypatch.setattr(hook, "_usage_metrics", lambda: {**_USAGE, **_HTTP_ERR})
    monkeypatch.setattr(hook, "_net_error_metric", lambda: 2001)
    monkeypatch.setattr(hook, "_precheck_miss", True)
    monkeypatch.setenv("SG_LAUNCHER_FALLBACK", "1")
    monkeypatch.setattr(hook, "atomic_check_and_mark_warning", lambda *a: False)
    with pytest.raises(SystemExit):
        hook._exit_review_failed(kind, "s1", metrics, 429)
    kept = _kept(_row(capsys))
    assert kept["review_failed"] is True and kept[split] is True
    assert (kept["api_error"], kept["vulns_found"]) == (429, 0)
    assert (kept["review_ms"], kept["files_reviewed"]) == (9500, 4)
    assert kept["net_err"] == 2001 and kept.get("agentic") == metrics.get("agentic")


@pytest.mark.parametrize("metrics, split", [
    (_QUIET_COMMIT, "commit_review"), (_PUSH, "push_sweep")])
def test_kind_and_time_fit_the_old_cap_of_ten(capsys, metrics, split):
    hook.emit_metrics(metrics)
    kept = _kept(_row(capsys), 10)
    assert {"vulns_found", split, "review_ms"} <= set(kept)


def test_only_the_order_changes(capsys):
    hook.emit_metrics(_COMMIT_FINDINGS)
    row = _row(capsys)
    added = {"pv", *_USAGE, "gateway_cfg", "diff_seen", "child_stderr", "rv_effort"}
    assert {k: v for k, v in row.items() if k not in added} == _COMMIT_FINDINGS
    rest = [k for k in _COMMIT_FINDINGS if k not in hook._LEAD_METRIC_KEYS]
    assert [k for k in row if k in rest] == rest


@pytest.mark.parametrize("metrics", [
    {"skipped": True, "skip_reason": 21, "commit_review": True, "commit_review_on": True},
    {"skipped": True, "skip_reason": 35, "diff_strategy_v2": True, "deduped": 2, "review_ms": 900},
])
def test_skip_rows_are_unchanged(capsys, monkeypatch, metrics):
    monkeypatch.setattr(hook, "_usage_metrics", dict)
    hook.emit_metrics(metrics)
    assert list(_row(capsys))[:1 + len(metrics)] == ["pv", *metrics]
