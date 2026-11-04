"""Bash hook starts that match no commit or push are counted; nothing changes."""
import itertools
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import HOOK_SCRIPT, STUB_VULN, VULN_PY, bash_payload, commit_file, metrics_of, run_hook

import security_reminder_hook as hook

WEIGHT = hook._UNMATCHED_BASH_SAMPLE
SHELL_PATTERN = "|".join(f"*{a}*{b}*" for a, b in hook._SHELL_PRECHECK_PAIRS)


def _call_id(sampled):
    for n in itertools.count():
        tool_use_id = f"toolu_{n}"
        if hook._unmatched_bash_sampled({"tool_use_id": tool_use_id}) is sampled:
            return tool_use_id


def _raw(command, stdout="ok"):
    return json.dumps(bash_payload("/w", command, stdout=stdout))


def test_unmatched_call_reports_what_a_text_check_would_do(workspace, hook_env):
    ws, _ = workspace
    loop = bash_payload("/w", "for f in a b; do echo $f; done", tool_use_id=_call_id(True))
    rc, so, se = run_hook(loop, hook_env)
    m = metrics_of(so)
    assert rc == 0 and se == ""
    assert m["bash_no_match"] == WEIGHT and m["precheck_skip"] == WEIGHT and m["pv"]

    # Text mentions pass a text check and still match nothing.
    for command, stdout in (("git log --grep commit", ""), ("ls", "run git push next")):
        p = bash_payload("/w", command, stdout, tool_use_id=_call_id(True))
        rc, so, se = run_hook(p, hook_env)
        m = metrics_of(so)
        assert rc == 0 and m["bash_no_match"] == WEIGHT and m["precheck_skip"] == 0


def test_unsampled_call_stays_silent(workspace, hook_env):
    loop = "for f in a b; do echo $f; done"
    assert run_hook(bash_payload("/w", loop, tool_use_id=_call_id(False)), hook_env) == (0, "", "")
    assert run_hook(bash_payload("/w", loop), hook_env) == (0, "", "")  # no call id


def test_other_hosts_get_no_row(workspace, hook_env):
    markers = ("CLAUDECODE", "CLAUDE_CODE_ENTRYPOINT", "SECURITY_GUIDANCE_PORTABLE_OUTPUT")
    env = {k: v for k, v in hook_env.items() if k not in markers}
    env["PLUGIN_ROOT"] = "/p"
    p = bash_payload("/w", "for f in a b; do echo $f; done", tool_use_id=_call_id(True))
    assert run_hook(p, env) == (0, "", "")


def test_one_call_in_ten_is_sampled():
    picked = sum(hook._unmatched_bash_sampled({"tool_use_id": f"toolu_{n}"}) for n in range(20000))
    assert 20000 / WEIGHT * 0.85 < picked < 20000 / WEIGHT * 1.15
    assert not hook._unmatched_bash_sampled({}) and not hook._unmatched_bash_sampled({"tool_use_id": 7})


def test_pairs_cover_every_verb_in_the_regexes():
    # A verb added to either regex has to be added to _SHELL_PRECHECK_PAIRS
    # and to _commands() below.
    assert hook._GIT_COMMIT_RE.pattern.endswith(r"\s+commit\b(?!-)|\bgt\s+(?:create|modify)\b")
    assert hook._GIT_PUSH_RE.pattern.endswith(r"\s+push\b|\bgt\s+submit\b)")


def _commands():
    """Commands the commit and push regexes match, in the spellings they allow."""
    opts = ["", " -C sub", " -c user.name=x", " -c 'a.b=c d'", " --git-dir=.git", " --no-pager",
            " -P", " --namespace=n", " --work-tree .", " -C a -c b=c --no-pager"]
    seps = [" ", "\t", "  ", "\n"]
    heads = ["", "cd x && ", "FOO=1 ", "(", "for i in 1; do ", "echo \"$(", "/usr/bin/", "x=`"]
    for head, opt, sep, verb in itertools.product(heads, opts, seps, ["commit", "push"]):
        yield f"{head}git{opt}{sep}{verb} -m 'é \"q\" \\ done'"
    for head, sep, verb in itertools.product(heads, seps, ["create", "modify", "submit"]):
        yield f"{head}gt{sep}{verb} --all"


def test_text_check_never_drops_a_reviewed_command():
    matched = [c for c in _commands() if hook._GIT_COMMIT_RE.search(c) or hook._GIT_PUSH_RE.search(c)]
    assert len(matched) > 600
    for command in matched:
        for ensure_ascii in (True, False):
            raw = json.dumps(bash_payload("/w", command), ensure_ascii=ensure_ascii)
            assert hook._shell_precheck_passes(raw), command


CASES = [
    ("ls -la | head", False),
    ("echo commit the git way", False),  # wrong order
    ("grep -c gt app.py", False),
    ("git status && echo 'ready to commit'", True),
    ("gt log; echo submit", True),
    ("git\tpush", True),
    ("digit; echo pushed", True),
]


def test_text_check_on_known_strings():
    for command, passes in CASES:
        assert hook._shell_precheck_passes(_raw(command)) is passes, command


def _working_bash():
    """A bash that runs a script. On Windows that is the one shipped with
    git: the `bash` on PATH there can be the WSL launcher, which is not one."""
    found = []
    git = shutil.which("git")
    if sys.platform == "win32" and git:
        root = Path(git).resolve().parent.parent
        found += [root / "bin" / "bash.exe", root / "usr" / "bin" / "bash.exe"]
    if shutil.which("bash"):
        found.append(Path(shutil.which("bash")))
    for bash in found:
        try:
            r = subprocess.run([str(bash), "-c", "echo ok"], capture_output=True, timeout=30)
        except (OSError, subprocess.SubprocessError):
            continue
        if r.returncode == 0 and r.stdout.strip() == b"ok":
            return str(bash)
    return None


def test_text_check_agrees_with_the_shell_pattern():
    bash = _working_bash()
    if not bash:
        pytest.skip("needs a working bash")
    script = f'input=$(cat); case "$input" in {SHELL_PATTERN}) echo pass ;; *) echo skip ;; esac'
    for command, _ in CASES:
        raw = _raw(command)
        r = subprocess.run([bash, "-c", script], input=raw.encode(), capture_output=True, timeout=30)
        assert r.stdout.strip() in (b"pass", b"skip"), r.stderr
        assert (r.stdout.strip() == b"pass") is hook._shell_precheck_passes(raw), command


def test_reviewed_command_a_text_check_would_drop_is_flagged(workspace, hook_env, stub_api):
    ws, repo = workspace
    stub_api.vulns = [STUB_VULN]
    _, out = commit_file(repo, "app.py", VULN_PY)
    raw = json.dumps(bash_payload(repo, "git commit -m change", out))
    # Same command, with one letter written as a JSON escape.
    raw = raw.replace('"git commit -m change"', '"git \\u0063ommit -m change"')
    assert json.loads(raw)["tool_input"]["command"] == "git commit -m change"
    if hook._shell_precheck_passes(raw):
        pytest.skip("the temporary path itself passes the text check")
    r = subprocess.run([sys.executable, str(HOOK_SCRIPT)], input=raw, capture_output=True,
                       text=True, env=hook_env, timeout=120)
    m = metrics_of(r.stdout)
    assert m["precheck_miss"] == 1 and m.get("commit_review") is True
    assert list(m).index("precheck_miss") < 3  # ahead of the row's own keys

    # The ordinary spelling carries no flag.
    _, out = commit_file(repo, "b.py", VULN_PY)
    rc, so, se = run_hook(bash_payload(repo, "git commit -m change", out), hook_env)
    m = metrics_of(so)
    assert m.get("commit_review") is True and "precheck_miss" not in m
