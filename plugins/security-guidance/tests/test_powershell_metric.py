"""Commits and pushes made through the PowerShell tool are counted; nothing is reviewed."""
import json
import os
import subprocess
import sys
import time

import pytest

from conftest import (
    HOOK_SCRIPT, HOOKS_DIR, STUB_VULN, VULN_PY, bash_payload, commit_file, metrics_of,
)

import security_reminder_hook as hook

COMMIT_OUT = "[main 1a2b3c4] change\n 1 file changed, 1 insertion(+)\n"


def _payload(cwd, command, stdout="", tool_use_id="toolu_x", **response):
    p = bash_payload(cwd, command, stdout, tool_use_id=tool_use_id)
    p["tool_name"] = "PowerShell"
    p["tool_response"].update(response)
    return p


def _run(payload, env, *args):
    r = subprocess.run([sys.executable, str(HOOK_SCRIPT), *args], input=json.dumps(payload),
                       capture_output=True, text=True, env=env, timeout=120)
    return r.returncode, r.stdout, r.stderr


def _sampled_id(sampled):
    for n in range(1000):
        tid = f"toolu_{n}"
        if hook._unmatched_bash_sampled({"tool_use_id": tid}) is sampled:
            return tid


def test_commit_is_counted_and_not_reviewed(workspace, hook_env, stub_api):
    ws, repo = workspace
    stub_api.vulns = [STUB_VULN]
    _, out = commit_file(repo, "app.py", VULN_PY)
    before = sorted(os.listdir(os.path.join(repo, ".git")))
    rc, so, se = _run(_payload(repo, "git commit -m change", out), hook_env, "commit")
    m = metrics_of(so)
    assert rc == 0 and se == "" and not stub_api.calls
    assert m["skip_reason"] == 50 and m["pv"]
    assert m["ps_known"] is True and m["ps_op"] is False and m["ps_on"] is True
    # No claim file, no reviewed sha: the next push from Bash still sees the commit.
    assert sorted(os.listdir(os.path.join(repo, ".git"))) == before
    # Keys that mark a Bash commit review stay off this row.
    assert not {"skipped", "commit_review", "push_sweep"} & set(m)


def test_the_row_holds_only_numbers_and_flags(workspace, hook_env):
    rc, so, _ = _run(_payload("/w", "git commit -m 'secret words'", COMMIT_OUT), hook_env, "commit")
    out = json.loads(so)
    assert list(out) == ["metrics"]
    assert all(isinstance(v, (bool, int, float)) for v in out["metrics"].values())
    assert "secret" not in so and "1a2b3c4" not in so


@pytest.mark.parametrize("command,kinds,known", [
    ("git commit -m x", {"commit"}, True),
    ("git -C sub commit -m x", {"commit"}, True),
    ("git push origin main", {"push"}, True),
    ("git add -A; git commit -m x; git push", {"commit", "push"}, True),
    ("git commit --amend --no-edit", {"commit"}, True),
    ("git.exe commit -m x", {"commit"}, False),
    ("git.exe commit -m 'git commit fix'", {"commit"}, False),
    ("GIT commit -m x", {"commit"}, False),
    ("& 'C:\\Program Files\\Git\\cmd\\git.exe' push", {"push"}, False),
    ('& "C:\\Program Files\\Git\\cmd\\git.exe" -C sub commit -m x', {"commit"}, False),
    ("if ($?) { git commit -m x }", {"commit"}, True),
    ("git commit -m @'\nline\n'@", {"commit"}, True),
])
def test_spellings(command, kinds, known):
    for entry in ("commit", "push"):
        row = hook._powershell_row(_payload("/w", command), entry)
        if entry in kinds:
            assert row["skip_reason"] == {"commit": 50, "push": 51}[entry]
            assert row["ps_known"] is known and row["ps_both"] is (len(kinds) == 2)
        else:
            assert row is None


@pytest.mark.parametrize("command", [
    "git status", "git commit-graph write", "git stash push", "Get-ChildItem | Select-Object Name",
    "digit commit", "git log --grep push-it", "Get-Content commit.txt", "git --help commit",
    'Write-Host "Git Commit failed"',  # subcommands are lower case
])
def test_other_commands_are_not_counted_as_commits(command):
    for entry in ("commit", "push"):
        p = _payload("/w", command, tool_use_id=_sampled_id(False))
        assert hook._powershell_row(p, entry) is None
        p = _payload("/w", command, tool_use_id=_sampled_id(True))
        assert hook._powershell_row(p, entry) == {"ps_no_match": hook._UNMATCHED_BASH_SAMPLE}


@pytest.mark.parametrize("op,entry,seen", [
    ({"commit": {"sha": "1a2b3c4", "kind": "committed"}}, "commit", True),
    ({"commit": {"sha": "1a2b3c4", "kind": "committed"}}, "push", False),
    ({"push": {"branch": "main"}}, "push", True),
    (None, "commit", False), ("commit", "commit", False),
])
def test_whether_claude_code_saw_it_happen(op, entry, seen):
    p = _payload("/w", "git commit -m x; git push", gitOperation=op)
    assert hook._powershell_row(p, entry)["ps_op"] is seen


def test_reviews_turned_off_are_marked(hook_env):
    for var, kind in (("ENABLE_COMMIT_REVIEW", "commit"), ("ENABLE_CODE_SECURITY_REVIEW", "commit"),
                      ("ENABLE_CODE_SECURITY_REVIEW", "push")):
        _, so, _ = _run(_payload("/w", f"git {kind}"), {**hook_env, var: "0"}, kind)
        assert metrics_of(so)["ps_on"] is False, var


@pytest.mark.parametrize("change", [
    {"tool_input": None}, {"tool_input": {}}, {"tool_input": "git commit"}, {"tool_input": ["a"]}, {"tool_input": {"command": ["git", "commit"]}},
    {"tool_input": {"command": "git commit"}, "tool_response": "text"},
    {"tool_input": {"command": "git commit"}, "tool_response": None},
])
def test_odd_payloads_never_fail(hook_env, change):
    p = {**_payload("/w", "x", tool_use_id=_sampled_id(False)), **change}
    for args in (["commit"], ["push"], []):
        rc, _, se = _run(p, hook_env, *args)
        assert rc == 0 and se == ""


def test_other_hosts_and_other_events_get_no_row(hook_env):
    markers = ("CLAUDECODE", "CLAUDE_CODE_ENTRYPOINT", "SECURITY_GUIDANCE_PORTABLE_OUTPUT")
    env = {k: v for k, v in hook_env.items() if k not in markers}
    env["PLUGIN_ROOT"] = "/p"
    assert _run(_payload("/w", "git commit -m x"), env, "commit") == (0, "", "")
    p = {**_payload("/w", "git commit -m x"), "hook_event_name": "PreToolUse"}
    assert _run(p, hook_env, "commit") == (0, "", "")


def test_the_pattern_is_linear():
    t0 = time.perf_counter()
    assert not hook._PS_GIT_RE.search("git " + '-c "git" ' * 3000)
    assert time.perf_counter() - t0 < 0.5
    for unit in ('-c "a"', "--no-a=b", "--git-dir x", "--no-pager", '-c a="b c"'):
        t0 = time.perf_counter()
        assert not hook._PS_GIT_RE.search("git " + " ".join([unit] * 40) + " commitfoo")
        assert time.perf_counter() - t0 < 0.05


def test_hooks_json_entries():
    post = json.loads((HOOKS_DIR / "hooks.json").read_text())["hooks"]["PostToolUse"]
    group = [g for g in post if g.get("matcher") == "PowerShell"][0]["hooks"]
    assert [(h["if"], h["command"].rsplit(" ", 1)[1]) for h in group] == [
        ("PowerShell(git*commit*)", "commit"), ("PowerShell(git*push*)", "push")]
    # In the background, so the tool call never waits for a count.
    assert all(h["asyncRewake"] is True for h in group)
