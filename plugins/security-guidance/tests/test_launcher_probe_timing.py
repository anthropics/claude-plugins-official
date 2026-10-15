"""sg-python.sh times its interpreter probes and the hooks report slow ones.

Measurement only: the launcher still waits for every probe and still picks
the interpreter it picked before.

The slow interpreter is a shell wrapper around the real one, so these tests
need a POSIX shell.
"""
import json
import os
import shutil
import subprocess
import sys

import pytest

from conftest import HOOKS_DIR, edit_payload, metrics_of, run_hook, stop_payload

pytestmark = pytest.mark.skipif(sys.platform == "win32", reason="POSIX shell wrappers")

SHIM = HOOKS_DIR / "sg-python.sh"
BASH = shutil.which("bash") or "/bin/bash"
REAL = os.path.realpath(sys.executable)


def _bash_major():
    try:
        return int(subprocess.run([BASH, "-c", "echo ${BASH_VERSINFO[0]}"],
                                  capture_output=True, text=True, timeout=30).stdout)
    except (OSError, ValueError, subprocess.SubprocessError):
        return 0


BASH5 = sys.platform != "win32" and _bash_major() >= 5

# Prints what the launcher handed over, then its stdin.
HOOK = (
    "import os, sys\n"
    "print('max=' + os.environ.get('SG_LAUNCHER_PROBE_MAX_MS', ''))\n"
    "print('total=' + os.environ.get('SG_LAUNCHER_PROBE_MS', ''))\n"
    "print('name=' + os.environ.get('SG_NAME', ''))\n"
    "print('stdin=' + sys.stdin.read())\n"
)

WRAPPER = """#!{bash}
# Answers the launcher's `-c` probe after DELAY seconds; RC != 0 fails it.
if [ "${{1:-}}" = "-c" ]; then
  sleep {delay}
  [ {rc} -eq 0 ] || exit {rc}
fi
SG_NAME={name} exec '{real}' "$@"
"""


def _python(bindir, name, delay=0, rc=0):
    bindir.mkdir(parents=True, exist_ok=True)
    p = bindir / name
    p.write_text(WRAPPER.format(bash=BASH, delay=delay, rc=rc, name=name, real=REAL))
    p.chmod(0o755)


def _run(bindir, script, extra_env=None, shim=SHIM):
    env = {"PATH": f"{bindir}{os.pathsep}/usr/bin{os.pathsep}/bin", "HOME": os.environ.get("HOME", "/")}
    env.update(extra_env or {})
    r = subprocess.run([BASH, str(shim), str(script)], input="payload", capture_output=True,
                       text=True, timeout=60, env=env)
    assert r.returncode == 0, r.stderr
    return dict(line.split("=", 1) for line in r.stdout.splitlines())


@pytest.fixture
def script(tmp_path):
    p = tmp_path / "hook.py"
    p.write_text(HOOK)
    return p


@pytest.fixture
def bindir(tmp_path):
    """A PATH entry with only what the tests put there (plus sleep)."""
    return tmp_path / "bin"


def _only_these(bindir):
    # Hide the system interpreters: PATH is bindir plus /usr/bin:/bin, so every
    # name the launcher tries gets an entry here, failing unless a test set it.
    for name in ("python3.13", "python3.12", "python3.11", "python3.10", "python3", "python", "py"):
        if not (bindir / name).exists():
            _python(bindir, name, rc=1)


@pytest.mark.skipif(not BASH5, reason="millisecond clock needs bash 5")
def test_fast_probes_are_timed_in_milliseconds(bindir, script):
    _python(bindir, "python3")
    _only_these(bindir)
    out = _run(bindir, script)
    assert out["name"] == "python3" and out["stdin"] == "payload"
    assert 0 < int(out["max"]) <= int(out["total"])


def test_slow_probe_is_waited_for_and_measured(bindir, script):
    _python(bindir, "python3", delay=2.2)
    _python(bindir, "python")
    _only_these(bindir)
    out = _run(bindir, script)
    # Still the first name that answers, however long it took.
    assert out["name"] == "python3" and out["stdin"] == "payload"
    assert 2000 <= int(out["max"]) < 10000
    assert int(out["total"]) >= int(out["max"])


def test_slow_failing_probe_counts_towards_the_wait(bindir, script):
    _python(bindir, "python3", delay=2.2, rc=49)
    _python(bindir, "python")
    _only_these(bindir)
    out = _run(bindir, script)
    assert out["name"] == "python"
    assert int(out["max"]) >= 2000


def test_inherited_values_are_not_reported_again(bindir, script):
    _python(bindir, "python3")
    _only_these(bindir)
    out = _run(bindir, script, {"SG_LAUNCHER_PROBE_MAX_MS": "999999", "SG_LAUNCHER_PROBE_MS": "999999"})
    assert out["max"] != "999999" and out["total"] != "999999"


@pytest.fixture
def whole_second_shim(tmp_path):
    """The launcher as bash 3.2 runs it: no EPOCHREALTIME, only SECONDS."""
    src = SHIM.read_text()
    assert 'case "${EPOCHREALTIME:-}" in' in src
    p = tmp_path / "sg-python-coarse.sh"
    p.write_text(src.replace('case "${EPOCHREALTIME:-}" in', 'case "" in'))
    return p


def test_whole_second_clock_ignores_fast_probes(bindir, script, whole_second_shim):
    _python(bindir, "python3")
    _only_these(bindir)
    out = _run(bindir, script, shim=whole_second_shim)
    assert out["name"] == "python3"
    # A probe of a few ms can straddle a second; that is not reported as 1 s.
    assert out["max"] == "" and out["total"] == ""


def test_whole_second_clock_measures_slow_probes(bindir, script, whole_second_shim):
    _python(bindir, "python3", delay=2.2)
    _only_these(bindir)
    out = _run(bindir, script, shim=whole_second_shim)
    assert out["name"] == "python3"
    assert int(out["max"]) in (2000, 3000) and int(out["total"]) >= int(out["max"])


@pytest.mark.parametrize("slowest,total,expected", [
    ("4200", "4350", {"launcher_probe_ms": 4350, "launcher_probe_max_ms": 4200}),
    ("900", "1500", {"launcher_probe_ms": 1500, "launcher_probe_max_ms": 900}),
    ("999", "999", {}),
    ("86400000", "86400000", {"launcher_probe_ms": 3600000, "launcher_probe_max_ms": 3600000}),
    ("5000", "5", {}),
    ("", "", {}),
    ("junk", "5", {}),
])
def test_stop_hook_reports_only_slow_probes(hook_env, workspace, slowest, total, expected):
    _, repo = workspace
    env = {**hook_env, "SG_LAUNCHER_PROBE_MAX_MS": slowest, "SG_LAUNCHER_PROBE_MS": total}
    rc, out, err = run_hook(stop_payload(repo), env)
    m = metrics_of(out)
    assert m is not None, err
    assert {k: v for k, v in m.items() if k.startswith("launcher_probe")} == expected


def test_launcher_keys_come_last(hook_env, workspace):
    """Claude Code keeps the first 20 keys, so these never displace another."""
    _, repo = workspace
    env = {**hook_env, "SG_LAUNCHER_PROBE_MAX_MS": "4200", "SG_LAUNCHER_PROBE_MS": "4350"}
    rc, out, err = run_hook(stop_payload(repo), env)
    assert list(metrics_of(out))[-2:] == ["launcher_probe_ms", "launcher_probe_max_ms"]


def test_edit_hook_reports_slow_probes_on_pattern_rows(hook_env, workspace):
    _, repo = workspace
    env = {**hook_env, "SG_LAUNCHER_PROBE_MAX_MS": "4200", "SG_LAUNCHER_PROBE_MS": "4350"}
    payload = edit_payload(repo, repo / "app.py", new_string="import os\nos.system('ls ' + x)\n")
    rc, out, err = run_hook(payload, env)
    m = metrics_of(out)
    assert m is not None and "rule_id" in m, (out, err)
    assert m["launcher_probe_ms"] == 4350 and m["launcher_probe_max_ms"] == 4200


def test_values_are_read_once(monkeypatch):
    import _base
    monkeypatch.setenv("SG_LAUNCHER_PROBE_MAX_MS", "7000")
    monkeypatch.setenv("SG_LAUNCHER_PROBE_MS", "7100")
    assert _base.launcher_probe_metrics() == {"launcher_probe_ms": 7100, "launcher_probe_max_ms": 7000}
    assert "SG_LAUNCHER_PROBE_MS" not in os.environ and _base.launcher_probe_metrics() == {}
