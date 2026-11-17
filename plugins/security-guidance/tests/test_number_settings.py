"""A setting that is not a number is ignored. It used to end every hook of the
session while the hook's modules loaded."""
import json
import re
import subprocess
import sys

import pytest

import _base
import llm
import security_reminder_hook as hook
from conftest import (
    HOOKS_DIR, VULN_PY, bash_payload, commit_file, edit_payload, make_repo, run_hook,
    stop_payload, ups_payload,
)
from test_reviewer_tools import sdk  # noqa: F401  fixture

# setting -> (module, name there, default)
AT_LOAD = {
    "MAX_STOP_HOOK_FIRINGS": ("security_reminder_hook", "MAX_STOP_HOOK_FIRINGS", 3),
    "MAX_DIFF_FILES": ("security_reminder_hook", "MAX_DIFF_FILES", 30),
    "MAX_REVIEW_SET_PATHS": ("security_reminder_hook", "MAX_REVIEW_SET_PATHS", 100000),
    "MAX_COMMIT_REVIEWS_PER_HOUR": ("security_reminder_hook", "MAX_COMMIT_REVIEWS_PER_HOUR", 20),
    "MAX_COMMIT_REVIEWS_PER_SESSION": ("security_reminder_hook", "MAX_COMMIT_REVIEWS_PER_HOUR", 20),
    "COMMIT_REVIEW_RATE_WINDOW_S": ("security_reminder_hook", "COMMIT_REVIEW_RATE_WINDOW_S", 3600),
    "SG_PUSH_SWEEP_MAX_FILES": ("security_reminder_hook", "MAX_PUSH_SWEEP_FILES", 30),
    "SG_PUSH_SWEEP_MAX_RANGE": ("security_reminder_hook", "MAX_PUSH_SWEEP_RANGE", 50),
    "SG_PUSH_SWEEP_REPORT_CAP": ("security_reminder_hook", "PUSH_SWEEP_REPORT_CAP", 3),
    "SG_INFLIGHT_WAIT_S": ("security_reminder_hook", "INFLIGHT_WAIT_S", 240),
    "PREVIOUS_FINDINGS_TTL_SEC": ("diffstate", "PREVIOUS_FINDINGS_TTL_SEC", 3600),
    "SG_REPO_SCAN_MAX_DEPTH": ("reporesolve", "SCAN_MAX_DEPTH", 3),
    "SG_REPO_SCAN_MAX_REPOS": ("reporesolve", "SCAN_MAX_REPOS", 64),
    "SG_REPO_SCAN_BUDGET_S": ("reporesolve", "SCAN_BUDGET_S", 4.0),
    "DIFF_PER_FILE_BYTES": ("review_api", "DIFF_PER_FILE_BYTES", 80000),
    "DIFF_TOTAL_BYTES": ("review_api", "DIFF_TOTAL_BYTES", 400000),
}


@pytest.fixture
def env(hook_env, tmp_path):
    e = {k: v for k, v in hook_env.items()
         if k not in (*AT_LOAD, "SECURITY_GUIDANCE_DISABLE", "ENABLE_SECURITY_REMINDER",
                      "ENABLE_PATTERN_RULES")}
    # No SDK install and no review: these tests are about the hook starting.
    e.update(ENABLE_CODE_SECURITY_REVIEW="0", SECURITY_GUIDANCE_DEBUG_LOG=str(tmp_path / "debug.log"))
    return e


def loaded(env):
    """What each setting is in a fresh process."""
    code = ("import importlib, json, sys; sys.path.insert(0, sys.argv[1]);"
            "print(json.dumps({k: getattr(importlib.import_module(m), n)"
            " for k, (m, n, _) in json.loads(sys.argv[2]).items()}))")
    r = subprocess.run([sys.executable, "-c", code, str(HOOKS_DIR), json.dumps(AT_LOAD)],
                       env=env, capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


DEFAULTS = {k: d for k, (_, _, d) in AT_LOAD.items()}


def test_defaults_when_unset(env):
    assert loaded(env) == DEFAULTS


@pytest.mark.parametrize("value", ["abc", "", " ", "1e3x"])
def test_defaults_when_not_numbers(env, value):
    assert loaded({**env, **dict.fromkeys(AT_LOAD, value)}) == DEFAULTS


def test_whole_number_settings_ignore_a_fraction(env):
    got = loaded({**env, **dict.fromkeys(AT_LOAD, "1.5")})
    assert got == {**DEFAULTS, "SG_REPO_SCAN_BUDGET_S": 1.5}


@pytest.mark.parametrize("value", ["7", " 7 ", "0", "-1", "1_000"])
def test_numbers_are_taken_as_before(env, value):
    got = loaded({**env, **dict.fromkeys(AT_LOAD, value)})
    assert got == {k: int(value) for k in AT_LOAD}


@pytest.mark.parametrize("hour, session, want", [
    ("5", "7", 5), ("0", "7", 0), ("", "7", 7), ("abc", "7", 7),
    ("5", "abc", 5), ("abc", "abc", 20), (None, "7", 7), (None, "abc", 20),
])
def test_per_hour_before_per_session(env, hour, session, want):
    env = {**env, "MAX_COMMIT_REVIEWS_PER_SESSION": session}
    if hour is not None:
        env["MAX_COMMIT_REVIEWS_PER_HOUR"] = hour
    assert loaded(env)["MAX_COMMIT_REVIEWS_PER_HOUR"] == want


ALL_BAD = dict.fromkeys(AT_LOAD, "abc")


@pytest.fixture
def repo(tmp_path):
    return make_repo(tmp_path / "repo")


def edit(env, repo):
    f = repo / "b.js"
    f.write_text("eval(x)\n")
    return run_hook(edit_payload(repo, f, "eval(x)\n"), env)


def test_edit_still_gets_its_pattern_warning(env, repo):
    code, out, err = edit({**env, **ALL_BAD}, repo)
    assert code == 0, err
    assert "eval" in json.loads(out)["hookSpecificOutput"]["additionalContext"]


@pytest.mark.parametrize("payload", [ups_payload, stop_payload])
def test_prompt_and_stop_hooks_run(env, repo, payload):
    code, _, err = run_hook(payload(repo), {**env, **ALL_BAD})
    assert code == 0, err


def test_commit_is_still_reviewed(env, repo, stub_api):
    sha, out = commit_file(repo, "app.py", VULN_PY)
    run_hook(bash_payload(repo, "git commit -m change", stdout=out),
             {**env, **ALL_BAD, "SG_AGENTIC_RACE_DELAY_S": "abc", "ENABLE_CODE_SECURITY_REVIEW": "1"})
    assert any("shell=True" in b for b in stub_api.bodies)


def test_kill_switch_still_works(env, repo):
    code, out, err = edit({**env, **ALL_BAD, "SECURITY_GUIDANCE_DISABLE": "1"}, repo)
    assert code == 0, err
    assert "eval" not in out


def test_ignored_value_is_in_the_debug_log(env, repo, tmp_path):
    edit({**env, "MAX_DIFF_FILES": "a" * 200, "MAX_STOP_HOOK_FIRINGS": "",
          "SG_REPO_SCAN_BUDGET_S": "4s", "MAX_COMMIT_REVIEWS_PER_HOUR": "5",
          "MAX_COMMIT_REVIEWS_PER_SESSION": "abc"}, repo)
    log = (tmp_path / "debug.log").read_text()
    assert f"Ignoring MAX_DIFF_FILES='{'a' * 40}': not a whole number" in log
    assert "Ignoring SG_REPO_SCAN_BUDGET_S='4s': not a number" in log
    assert log.count("Ignoring ") == 2  # not the empty one, nor the unused old name


def test_review_api_import_writes_nothing(env, tmp_path):
    """Other programs import it."""
    r = subprocess.run([sys.executable, "-c", "import sys; sys.path.insert(0, sys.argv[1]); import review_api",
                        str(HOOKS_DIR)], env={**env, "DIFF_TOTAL_BYTES": "abc"}, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert not (tmp_path / "debug.log").exists()


@pytest.mark.parametrize("value", ["abc", "", "1.5"])
def test_race_delay_does_not_end_the_commit_review(monkeypatch, value):
    monkeypatch.setenv("SG_AGENTIC_RACE_DELAY_S", value)
    monkeypatch.delenv("SG_AGENTIC_NO_RACE", raising=False)
    monkeypatch.setattr(hook, "agentic_review", lambda *a, **k: ("finding", [{"x": 1}], {}))
    monkeypatch.setattr(hook, "_single_shot_review", lambda *a, **k: ("other", [], {"review_failed": False}))
    guidance, _, metrics = hook._agentic_review_with_race("/r", [("a.py", "x")], ["a.py"], [])
    assert (guidance, metrics["race_delay_s"]) == ("finding", 180)


@pytest.mark.parametrize("value", ["abc", "", "1.5"])
def test_max_turns_does_not_end_the_agentic_review(sdk, monkeypatch, tmp_path, value):
    monkeypatch.setenv("SG_AGENTIC_MAX_TURNS", value)
    _, vulns, _ = llm.agentic_review(str(tmp_path), [("a.py", "+x = 1\n")], ["a.py"])
    assert len(vulns) == 1
    assert sdk[0]["max_turns"] == 18


def test_no_setting_is_turned_into_a_number_without_the_helper():
    bare = re.compile(r"\b(?:int|float)\(\s*os\.(?:environ\.get|environ\[|getenv)")
    found = [f.name for f in HOOKS_DIR.glob("*.py") if bare.search(f.read_text(encoding="utf-8"))]
    assert found == ["gitutil.py"]  # _file_diff_cap, which catches it


def test_env_number(monkeypatch):
    monkeypatch.setenv("SG_T", "2.5")
    assert _base.env_number("SG_T", 1) == 1
    assert _base.env_number("SG_T", 1.0, float) == 2.5
