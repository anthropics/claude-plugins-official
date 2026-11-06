"""Without credentials the LLM reviews are skipped; the user is told."""
import json
import os
import time

import pytest

from conftest import (
    bash_payload, commit_file, edit_payload, git, metrics_of, run_hook,
    stop_payload, ups_payload, VULN_PY,
)
from test_gateway_sign_in import NOT_SIGNED_IN, SIGNED_IN, calls_of, make_cli

# Anything in the developer's shell that changes whether a review would run.
_AMBIENT = (
    "ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN",
    # Makes every session share one state file.
    "CLAUDE_CODE_REMOTE_SESSION_ID",
    "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC", "DISABLE_TELEMETRY", "DO_NOT_TRACK",
    "CLAUDE_CODE_USE_BEDROCK", "CLAUDE_CODE_USE_VERTEX", "CLAUDE_CODE_USE_FOUNDRY",
    "CLAUDE_CODE_USE_MANTLE", "CLAUDE_CODE_USE_ANTHROPIC_AWS",
    "SECURITY_GUIDANCE_DISABLE", "ENABLE_SECURITY_REMINDER",
    "ENABLE_CODE_SECURITY_REVIEW", "ENABLE_STOP_REVIEW", "ENABLE_COMMIT_REVIEW",
    "ENABLE_PATTERN_RULES",
)


def _env(hook_env, creds=False, **extra):
    env = {k: v for k, v in hook_env.items() if k not in _AMBIENT}
    if creds:
        env["ANTHROPIC_API_KEY"] = "test-key"
    env.update(extra)
    return env


def _edit_output(repo, env, name="app.py", content=VULN_PY, session_id="s1"):
    (repo / name).write_text(content)
    rc, out, _ = run_hook(
        edit_payload(repo, repo / name, new_string=content, session_id=session_id), env)
    assert rc == 0
    lines = [l for l in out.splitlines() if l.startswith("{")]
    assert len(lines) <= 1
    return json.loads(lines[0]) if lines else {}


def _notice(repo, env, **kw):
    return _edit_output(repo, env, **kw).get("systemMessage")


def _marker(env):
    return os.path.join(env["SECURITY_WARNINGS_STATE_DIR"], ".no_credentials_notice")


def test_edit_without_credentials_tells_the_user_once(workspace, hook_env):
    _, repo = workspace
    env = _env(hook_env)
    notice = _notice(repo, env)
    assert "is not running" in notice
    assert "No Anthropic credentials were passed" in notice
    assert "only the pattern warnings on edits are active" in notice
    assert "ENABLE_CODE_SECURITY_REVIEW=0" in notice
    assert _notice(repo, env) is None
    assert _notice(repo, env, session_id="s2") is None


def test_notice_comes_back_after_a_week(workspace, hook_env):
    _, repo = workspace
    env = _env(hook_env)
    assert _notice(repo, env)
    six_days, eight_days = time.time() - 6 * 86400, time.time() - 8 * 86400
    os.utime(_marker(env), (six_days, six_days))
    assert _notice(repo, env) is None
    os.utime(_marker(env), (eight_days, eight_days))
    assert _notice(repo, env)
    assert _notice(repo, env) is None


def test_notice_names_every_setting_that_withholds_credentials(workspace, hook_env):
    _, repo = workspace
    notice = _notice(repo, _env(hook_env, DISABLE_TELEMETRY="1", DO_NOT_TRACK="true"))
    assert "while DISABLE_TELEMETRY or DO_NOT_TRACK is set" in notice


@pytest.mark.parametrize("var", ["CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC", "DO_NOT_TRACK"])
def test_notice_names_the_setting(workspace, hook_env, var):
    _, repo = workspace
    assert f"while {var} is set" in _notice(repo, _env(hook_env, **{var: "1"}))


def test_do_not_track_off_is_not_blamed(workspace, hook_env):
    _, repo = workspace
    notice = _notice(repo, _env(hook_env, DO_NOT_TRACK="0"))
    assert "DO_NOT_TRACK" not in notice and "No Anthropic credentials" in notice


def test_notice_does_not_promise_pattern_warnings_that_are_off(workspace, hook_env):
    _, repo = workspace
    notice = _notice(repo, _env(hook_env, ENABLE_PATTERN_RULES="0"))
    assert "is not running" in notice and "pattern warnings" not in notice


def test_notice_rides_along_with_a_pattern_warning(workspace, hook_env):
    _, repo = workspace
    risky = "import os\nos.system('ls ' + name)\n"
    with_creds = _edit_output(
        repo, _env(hook_env, creds=True), name="a.py", content=risky)
    assert with_creds["metrics"]["pattern_hits"] == 1
    assert "systemMessage" not in with_creds
    out = _edit_output(repo, _env(hook_env), name="b.py", content=risky)
    assert "is not running" in out["systemMessage"]
    assert out["metrics"] == with_creds["metrics"]
    assert (out["hookSpecificOutput"]["additionalContext"]
            == with_creds["hookSpecificOutput"]["additionalContext"])


def test_no_notice_with_credentials(workspace, hook_env):
    _, repo = workspace
    assert _notice(repo, _env(hook_env, creds=True)) is None
    assert _notice(repo, _env(hook_env, ANTHROPIC_AUTH_TOKEN="t")) is None
    assert _notice(repo, _env(hook_env, CLAUDE_CODE_USE_BEDROCK="1")) is None
    assert not os.path.exists(_marker(hook_env))


def test_no_notice_when_the_reviews_are_turned_off(workspace, hook_env):
    _, repo = workspace
    assert _notice(repo, _env(hook_env, ENABLE_CODE_SECURITY_REVIEW="0")) is None
    assert _notice(repo, _env(hook_env, SECURITY_GUIDANCE_DISABLE="1")) is None
    assert _notice(repo, _env(
        hook_env, ENABLE_STOP_REVIEW="0", SECURITY_GUIDANCE_COMMIT_REVIEW="off",
        SG_PUSH_SWEEP="off")) is None
    assert not os.path.exists(_marker(hook_env))
    assert _notice(repo, _env(hook_env, ENABLE_STOP_REVIEW="0"))


def test_no_notice_outside_a_git_repo(workspace, hook_env, tmp_path):
    _, repo = workspace
    plain = tmp_path / "plain"
    plain.mkdir()
    env = _env(hook_env)
    assert _notice(plain, env, name="notes.py") is None
    assert not os.path.exists(_marker(env))
    assert _notice(repo, env)


def test_no_notice_when_the_state_dir_is_unwritable(workspace, hook_env, tmp_path):
    _, repo = workspace
    blocker = tmp_path / "not-a-dir"
    blocker.write_text("")
    env = _env(hook_env, SECURITY_WARNINGS_STATE_DIR=str(blocker / "state"))
    assert _notice(repo, env) is None
    assert _notice(repo, env) is None


def test_skipped_reviews_report_the_missing_credentials(workspace, hook_env, stub_api):
    _, repo = workspace
    env = _env(hook_env)
    run_hook(ups_payload(repo), env)
    _edit_output(repo, env)
    rc, out, _ = run_hook(stop_payload(repo), env)
    m = metrics_of(out)
    assert rc == 0 and m["skip_reason"] == 3 and m["no_creds"] is True

    _, commit_out = commit_file(repo, "app.py", VULN_PY + "# again\n")
    rc, out, _ = run_hook(
        bash_payload(repo, "git commit -m change", stdout=commit_out), env)
    m = metrics_of(out)
    assert rc == 0 and m["skip_reason"] == 22 and m["no_creds"] is True

    rc, out, _ = run_hook(bash_payload(repo, "git push origin main"), env)
    m = metrics_of(out)
    assert rc == 0 and m["push_sweep"] and m["skip_reason"] == 22 and m["no_creds"] is True
    assert stub_api.calls == []

    off = _env(hook_env, ENABLE_CODE_SECURITY_REVIEW="0")
    for payload in (stop_payload(repo, session_id="s3"),
                    bash_payload(repo, "git push origin main", session_id="s3")):
        rc, out, _ = run_hook(payload, off)
        assert "no_creds" not in metrics_of(out)


def test_no_notice_in_a_signed_in_gateway_session(workspace, hook_env, tmp_path):
    # Claude Code passes no credential there, but the reviews run through
    # the user's claude, so they are running.
    _, repo = workspace
    cli, calls = make_cli(tmp_path, SIGNED_IN)
    env = _env(hook_env, SG_AGENTIC_CLI_PATH=str(cli))
    assert _notice(repo, env) is None
    # The check counts as this week's: a new session's edit does not ask.
    assert _notice(repo, env, session_id="s2") is None
    assert os.path.exists(_marker(env))
    assert [c.split(" | ")[0] for c in calls_of(calls)] == ["auth status --json"]
    # A week later the edit asks again.
    eight_days = time.time() - 8 * 86400
    os.utime(_marker(env), (eight_days, eight_days))
    assert _notice(repo, env, session_id="s3") is None
    assert len(calls_of(calls)) == 2


def test_edit_outside_a_git_repo_does_not_ask_claude(workspace, hook_env, tmp_path):
    cli, calls = make_cli(tmp_path, SIGNED_IN)
    plain = tmp_path / "plain"
    plain.mkdir()
    env = _env(hook_env, SG_AGENTIC_CLI_PATH=str(cli))
    assert _notice(plain, env, name="notes.py") is None
    assert calls_of(calls) == []


def test_notice_when_the_gateway_session_is_not_signed_in(workspace, hook_env, tmp_path):
    _, repo = workspace
    cli, calls = make_cli(tmp_path, NOT_SIGNED_IN)
    env = _env(hook_env, SG_AGENTIC_CLI_PATH=str(cli))
    assert "is not running" in _notice(repo, env)
    # Within the week no notice is due, so claude is not asked again.
    assert _notice(repo, env, session_id="s2") is None
    assert len(calls_of(calls)) == 1
