"""Custom rule regexes run with a time limit, so a slow rule cannot hold a hook."""
import subprocess
import time

import pytest

import extensibility
import security_reminder_hook as hook

SLOW = "(a+){2,}$"
SLOW_TEXT = "a" * 40 + "!"


def _rule(name, regex):
    return {"ruleName": "user:" + name, "reminder": name, "regex": regex, "_source": "t"}


@pytest.fixture(autouse=True)
def fresh(monkeypatch):
    monkeypatch.setattr(extensibility, "_regex_seconds_left", 30.0)
    monkeypatch.setattr(extensibility, "_stopped_regexes", set())
    monkeypatch.setattr(extensibility, "slowest_regex", 0.0)
    monkeypatch.setattr(hook, "SECURITY_PATTERNS", [
        {"ruleName": "builtin", "reminder": "builtin", "substrings": ["danger"]}])


def _short_limit(monkeypatch, seconds=3.0):
    monkeypatch.setattr(extensibility, "_regex_seconds_left", seconds)


def _check(monkeypatch, rules, content):
    monkeypatch.setattr(extensibility, "_user_patterns", rules)
    return [name for name, _ in hook.check_patterns("a.py", content)]


def test_found_and_not_found(monkeypatch):
    rules = [_rule("yes", r"needle\d"), _rule("no", "absent")]
    assert _check(monkeypatch, rules, "x needle1") == ["user:yes"]


def test_non_ascii_content_is_searched(monkeypatch):
    assert _check(monkeypatch, [_rule("r", "é+z")], "caféz \udc80") == ["user:r"]


def test_order_stays_built_in_then_custom_as_listed(monkeypatch):
    substring = {"ruleName": "user:sub", "reminder": "sub", "substrings": ["needle"], "_source": "t"}
    rules = [_rule("first", "needle"), substring, _rule("third", "needle")]
    assert _check(monkeypatch, rules, "danger needle") == [
        "builtin", "user:first", "user:sub", "user:third"]


def test_slow_rule_is_stopped_and_the_others_still_run(monkeypatch):
    _short_limit(monkeypatch)
    rules = [_rule("before", "a!"), _rule("slow", SLOW), _rule("after", "a!")]
    started = time.perf_counter()
    got = _check(monkeypatch, rules, "danger " + SLOW_TEXT)
    assert time.perf_counter() - started < 8
    assert got == ["builtin", "user:before", "user:after"]
    assert extensibility.slowest_regex >= 1.0


def test_stopped_rule_is_not_tried_again(monkeypatch):
    _short_limit(monkeypatch)
    rules = [_rule("slow", SLOW), _rule("other", "a")]
    assert _check(monkeypatch, rules, SLOW_TEXT) == ["user:other"]
    monkeypatch.setattr(extensibility, "_regex_seconds_left", 30.0)
    started = time.perf_counter()
    assert _check(monkeypatch, rules, SLOW_TEXT) == ["user:other"]
    assert time.perf_counter() - started < 5


def test_nothing_runs_when_the_time_is_gone(monkeypatch):
    _short_limit(monkeypatch, 0)
    assert _check(monkeypatch, [_rule("r", "a")], "a") == []


def test_load_starts_a_new_allowance(monkeypatch, tmp_path):
    monkeypatch.setattr(extensibility, "_regex_seconds_left", 0)
    monkeypatch.setattr(extensibility, "_stopped_regexes", {"x"})
    monkeypatch.setattr(extensibility, "_load_guidance", lambda cwd: "")
    monkeypatch.setattr(extensibility, "_load_user_patterns", lambda cwd: [])
    monkeypatch.setattr(extensibility, "_guidance_block", "")
    monkeypatch.setattr(extensibility, "_user_patterns", [])
    monkeypatch.setattr(extensibility, "_refused_regexes", 0)
    extensibility.load_for_session(str(tmp_path))
    assert extensibility._regex_seconds_left == extensibility.REGEX_TIME_LIMIT_S
    assert not extensibility._stopped_regexes


def test_no_child_without_a_custom_regex(monkeypatch):
    def boom(*a, **k):
        raise AssertionError("started a child")
    monkeypatch.setattr(subprocess, "run", boom)
    assert _check(monkeypatch, [], "danger") == ["builtin"]
    # A rule the path filter turns away needs no search either.
    rule = dict(_rule("r", "x"), path_filter=lambda p: False)
    assert _check(monkeypatch, [rule], "x") == []


def test_worker_that_cannot_start_falls_back(monkeypatch):
    def fail(*a, **k):
        raise OSError("no")
    monkeypatch.setattr(subprocess, "run", fail)
    assert _check(monkeypatch, [_rule("r", "x")], "x") == ["user:r"]


def test_worker_that_fails_falls_back(monkeypatch):
    monkeypatch.setattr(extensibility, "_REGEX_WORKER", "import sys; sys.exit(1)")
    assert _check(monkeypatch, [_rule("r", "x")], "x") == ["user:r"]
