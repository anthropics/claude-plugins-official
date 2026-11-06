"""Each LLM review leaves one usage line in the plugin's debug log."""
import re

from conftest import (
    VULN_PY, bash_payload, commit_file, edit_payload, git, metrics_of, run_hook,
    stop_payload, ups_payload,
)

USAGE = re.compile(
    r"Review usage: review=(\w+) session=(\S+) model=(\S+) calls=(\d+) "
    r"in=(\d+) out=(\d+) cache_read=(\d+) cache_write=(\d+) est_cost_usd=(\d+\.\d{4}~?)$"
)


def _usage_lines(env):
    log = env["SECURITY_GUIDANCE_DEBUG_LOG"]
    try:
        text = open(log).read()
    except FileNotFoundError:
        return []
    return [m.groups() for m in map(USAGE.search, text.splitlines()) if m]


def _env(hook_env, tmp_path):
    return {**hook_env, "SECURITY_GUIDANCE_DEBUG_LOG": str(tmp_path / "log.txt"),
            "SECURITY_REVIEW_MODEL": "claude-opus-5-5"}


def test_stop_review_logs_its_usage_with_the_session(workspace, hook_env, tmp_path):
    _, repo = workspace
    env = _env(hook_env, tmp_path)
    run_hook(ups_payload(repo, session_id="sess-1"), env)
    (repo / "app.py").write_text(VULN_PY)
    run_hook(edit_payload(repo, repo / "app.py", VULN_PY, session_id="sess-1"), env)
    assert _usage_lines(env) == []
    rc, so, _ = run_hook(stop_payload(repo, session_id="sess-1"), env)

    m = metrics_of(so)
    assert m["api_calls"] == 1
    # "stub" is not in the price table, so the estimate is marked.
    assert _usage_lines(env) == [
        ("stop", "sess-1", "stub", "1", "1", "1", "0", "0", f"{m['cost_usd']:.4f}~"),
    ]


def test_commit_review_logs_review_commit(workspace, hook_env, tmp_path):
    _, repo = workspace
    env = _env(hook_env, tmp_path)
    _, out = commit_file(repo, "app.py", VULN_PY)
    run_hook(bash_payload(repo, "git commit -m change", out, session_id="sess 2/x"), env)

    lines = _usage_lines(env)
    assert len(lines) == 1
    assert lines[0][:2] == ("commit", "sess_2_x") and lines[0][3] == "1"


def test_no_line_when_no_review_ran(workspace, hook_env, tmp_path):
    _, repo = workspace
    env = _env(hook_env, tmp_path)
    run_hook(ups_payload(repo), env)
    run_hook(stop_payload(repo), env)
    assert _usage_lines(env) == []


def test_failed_request_logs_no_usage(workspace, hook_env, stub_api, tmp_path):
    _, repo = workspace
    env = _env(hook_env, tmp_path)
    stub_api.status = 400
    _, out = commit_file(repo, "app.py", VULN_PY)
    run_hook(bash_payload(repo, "git commit -m change", out), env)
    assert _usage_lines(env) == []


def test_push_review_logs_review_push(workspace, hook_env, tmp_path):
    _, repo = workspace
    env = _env(hook_env, tmp_path)
    remote = tmp_path / "remote.git"
    git(tmp_path, "init", "-q", "--bare", str(remote))
    git(repo, "remote", "add", "origin", str(remote))
    git(repo, "push", "-q", "-u", "origin", "main")
    base = git(repo, "rev-parse", "HEAD").strip()
    sha, _ = commit_file(repo, "app.py", VULN_PY)
    git(repo, "push", "-q", "origin", "main")
    out = f"To {remote}\n   {base[:7]}..{sha[:7]}  main -> main\n"
    run_hook(bash_payload(repo, "git push origin main", out), env)

    lines = _usage_lines(env)
    assert len(lines) == 1 and lines[0][0] == "push"


def test_line_carries_the_same_numbers_as_the_metrics(tmp_path, monkeypatch):
    import _base
    logged = []
    monkeypatch.setattr(_base, "debug_log", logged.append)
    monkeypatch.setattr(_base, "_USAGE", {
        "in": 0, "out": 0, "cr": 0, "cw": 0, "cost": 0.0, "n": 0,
        "http_err_last": 0, "http_err_count": 0, "models": [], "default_priced": False,
    })
    monkeypatch.setattr(_base, "_USAGE_CONTEXT", {"session_id": "abc", "review": "stop"})
    _base._log_usage(_base._usage_metrics())
    assert logged == []

    _base._record_usage({"input_tokens": 31994, "output_tokens": 3250,
                         "cache_read_input_tokens": 7, "cache_creation_input_tokens": 9},
                        "claude-opus-5-5")
    _base._record_usage({"input_tokens": 1, "output_tokens": 1}, "opus", cost_usd=0.5)
    _base._record_usage({"input_tokens": 1, "output_tokens": 1},
                        "bad model\nReview usage: forged")
    usage = _base._usage_metrics()
    _base._log_usage(usage)
    assert logged == [
        "Review usage: review=stop session=abc "
        "model=claude-opus-5-5,opus,bad_model_Review_usage:_forged calls=3 "
        f"in=31996 out=3252 cache_read=7 cache_write=9 est_cost_usd={usage['cost_usd']:.4f}~"
    ]
    assert usage["cost_usd"] > 0.69
