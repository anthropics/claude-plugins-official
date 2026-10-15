"""sg-python.sh gives up on an interpreter name that never answers its probe.

On Windows, python3 / python3.x can be App execution aliases that never exit
when started without a console. Probed with no time limit, one of them ahead
of a working `python` stalls every hook until the host's hook timeout. See
#6315, #3870.

The aliases are emulated with shell scripts, so these tests need a POSIX shell.
"""
import os
import shutil
import signal
import subprocess
import sys
import time

import pytest

from conftest import HOOKS_DIR, metrics_of, run_hook, stop_payload

SHIM = HOOKS_DIR / "sg-python.sh"
BASH = shutil.which("bash") or "/bin/bash"
SLEEP = shutil.which("sleep") or "/bin/sleep"
REAL = os.path.realpath(sys.executable)
# `read -t` tells a timeout from a failure from bash 4 on; stock macOS has 3.2.
# The launcher kills a name that does not answer from bash 4.4 on; stock macOS
# has 3.2.
try:
    BASH_VERSION = tuple(int(n) for n in subprocess.run(
        [BASH, "-c", "echo ${BASH_VERSINFO[0]} ${BASH_VERSINFO[1]}"], capture_output=True,
        text=True).stdout.split())
except OSError:
    BASH_VERSION = ()

shim = pytest.mark.skipif(sys.platform == "win32" or not BASH_VERSION, reason="POSIX shell wrappers")

HOOK = (
    "import os, sys\n"
    "print('timeouts=' + os.environ.get('SG_LAUNCHER_PROBE_TIMEOUTS', ''))\n"
    "sys.stderr.write('ran:' + sys.stdin.read())\n"
)
# Never answers, ignores TERM, and its child keeps the output pipe open.
HANGS = "#!{bash}\ntrap '' TERM\n'{sleep}' 300 &\necho $! >> '{pids}'\nwait\n"
# Never answers; records its pid so a test can see what became of it.
HANGS_ALONE = "#!{bash}\necho $$ >> '{pids}'\nexec '{sleep}' 300\n"
# A working interpreter on a slow start: the probe takes {delay}s to answer.
SLOW = "#!{bash}\n[ \"${{1:-}}\" = -c ] && '{sleep}' {delay}\nexec '{real}' \"$@\"\n"
# Would eat the hook's payload if a probe were given the hook's stdin.
READS_STDIN = "#!{bash}\n[ \"${{1:-}}\" = -c ] && cat >/dev/null\nexec '{real}' \"$@\"\n"

LIMIT = 2


@pytest.fixture
def box(tmp_path):
    (tmp_path / "bin").mkdir()
    (tmp_path / "hook.py").write_text(HOOK)
    (tmp_path / "pids").write_text("")
    yield tmp_path
    for pid in (tmp_path / "pids").read_text().split():
        try:
            os.kill(int(pid), signal.SIGKILL)
        except OSError:
            pass


def _script(box, name, template, delay=0):
    p = box / "bin" / name
    p.write_text(template.format(bash=BASH, sleep=SLEEP, real=REAL, delay=delay, pids=box / "pids"))
    p.chmod(0o755)


def _run(box, limit=LIMIT):
    start = time.monotonic()
    r = subprocess.run(
        [BASH, str(SHIM), str(box / "hook.py")], input='{"k": 1}', capture_output=True, text=True,
        timeout=120, env={"PATH": str(box / "bin"), "HOME": "/", "SG_PROBE_TIMEOUT": str(limit),
                          "SG_LAUNCHER_PROBE_TIMEOUTS": "7"},
    )
    return r, time.monotonic() - start


@shim
@pytest.mark.parametrize("hanging", [["python3"], ["python3.12", "python3"]])
def test_name_that_never_answers_is_skipped(box, hanging):
    for name in hanging:
        _script(box, name, HANGS)
    os.symlink(REAL, box / "bin" / "python")
    r, took = _run(box)
    assert r.returncode == 0, r.stderr
    assert r.stderr == 'ran:{"k": 1}'
    assert r.stdout.splitlines() == ["timeouts=%d" % len(hanging)]
    assert took < LIMIT * len(hanging) + 20


@shim
def test_healthy_interpreter_is_not_counted(box):
    os.symlink(REAL, box / "bin" / "python3")
    r, _ = _run(box)
    assert r.returncode == 0, r.stderr
    # A count inherited from an outer session is dropped.
    assert r.stdout.splitlines() == ["timeouts="]


@shim
def test_all_names_hanging_fails_cleanly(box):
    for name in ("python3", "python"):
        _script(box, name, HANGS)
    r, took = _run(box, limit=1)
    assert r.returncode == 1
    # Each name got the short try, then the longer one.
    assert "no answer within 1s, then 3s, from: python3 python" in r.stderr
    assert "no working Python 3 interpreter found" in r.stderr
    assert metrics_of(r.stdout) == {"launcher_probe_timeout": 2}
    assert 8 <= took < 40


@shim
@pytest.mark.skipif(BASH_VERSION < (4, 4), reason="bash 4.4+ knows the probe's pid")
def test_name_that_never_answers_is_not_left_running(box):
    _script(box, "python3", HANGS_ALONE)
    os.symlink(REAL, box / "bin" / "python")
    r, _ = _run(box)
    assert r.returncode == 0, r.stderr
    (pid,) = (box / "pids").read_text().split()
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline and os.path.exists("/proc/%s" % pid):
        time.sleep(0.1)
    with pytest.raises(OSError):
        os.kill(int(pid), 0)


@shim
def test_slow_interpreter_is_used_when_nothing_else_works(box):
    _script(box, "python3", HANGS)
    _script(box, "python", SLOW, delay=LIMIT + 1)
    r, _ = _run(box)
    assert r.returncode == 0, r.stderr
    assert r.stderr == 'ran:{"k": 1}'
    assert r.stdout.splitlines() == ["timeouts=2"]


@shim
@pytest.mark.parametrize("limit", ["0", "junk", "08"])
def test_limit_setting_is_read_safely(box, limit):
    _script(box, "python3", SLOW, delay=1)
    r, _ = _run(box, limit=limit)
    assert r.returncode == 0, r.stderr
    assert r.stdout.splitlines() == ["timeouts="]


@shim
def test_probe_does_not_read_the_hook_payload(box):
    _script(box, "python3", READS_STDIN)
    r, _ = _run(box)
    assert r.returncode == 0, r.stderr
    assert r.stderr == 'ran:{"k": 1}'


@pytest.mark.parametrize("count", ["2", None])
def test_hook_reports_probe_timeouts(workspace, hook_env, count):
    _, repo = workspace
    env = dict(hook_env)
    env.pop("SG_LAUNCHER_PROBE_TIMEOUTS", None)
    if count:
        env["SG_LAUNCHER_PROBE_TIMEOUTS"] = count
    rc, out, _ = run_hook(stop_payload(repo), env)
    assert rc == 0
    m = metrics_of(out)
    assert m is not None
    assert m.get("launcher_probe_timeout") == (2 if count else None)
