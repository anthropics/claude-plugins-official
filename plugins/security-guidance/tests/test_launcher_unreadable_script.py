"""sg-python.sh never hands the hook script to an interpreter that cannot see it.

On Windows, python/python3/py can be packaged launcher aliases whose
interpreter answers `-c` but has no view of the plugin directory. Running the
hook with one fails with CPython's "can't open file" and exit code 2, which an
asyncRewake hook reports to the model as review findings, on every Stop.

The aliases are emulated with shell wrappers around the real interpreter, so
these tests need a POSIX shell.
"""
import json
import os
import shutil
import subprocess
import sys

import pytest

from conftest import HOOKS_DIR, metrics_of, run_hook, stop_payload

pytestmark = pytest.mark.skipif(sys.platform == "win32", reason="POSIX shell wrappers")

SHIM = HOOKS_DIR / "sg-python.sh"
BASH = shutil.which("bash") or "/bin/bash"
REAL = os.path.realpath(sys.executable)

# Echoes its stdin and exits 2, like a hook that has findings to report.
HOOK = (
    "import os, sys\n"
    "print('fallback=' + os.environ.get('SG_LAUNCHER_FALLBACK', ''))\n"
    "sys.stderr.write('ran:' + sys.stdin.read())\nsys.exit(2)\n"
)

ALIAS = """#!{bash}
# A packaged alias: `-c` works, files under HIDE are invisible.
HIDE='{hide}'; REAL='{real}'
if [ "${{1:-}}" = "-c" ]; then
  code="$2"; shift 2
  out=$("$REAL" -c "import os as _o, sys as _s
_f = _o.path.isfile
_o.path.isfile = lambda p, _f=_f: False if str(p).startswith('$HIDE') else _f(p)
if '{sealed}': _s.executable = '$0'
$code" "$@"); rc=$?
  [ -n "$out" ] && printf '%s{eol}' "$out"
  exit $rc
fi
case "${{1:-}}" in
  "$HIDE"/*) echo "python: can't open file '$1': [Errno 2] No such file or directory" >&2; exit 2 ;;
esac
exec "$REAL" "$@"
"""


def _alias(bindir, name, hide, sealed=False, crlf=False):
    bindir.mkdir(parents=True, exist_ok=True)
    p = bindir / name
    p.write_text(ALIAS.format(bash=BASH, hide=hide, real=REAL, sealed="1" if sealed else "",
                              eol="\\r\\n" if crlf else "\\n"))
    p.chmod(0o755)


def _run(path_dirs, script, payload='{"k": 1}'):
    return subprocess.run(
        [BASH, str(SHIM), str(script)], input=payload, capture_output=True, text=True, timeout=60,
        env={"PATH": os.pathsep.join(str(d) for d in path_dirs), "HOME": os.environ.get("HOME", "/")},
    )


@pytest.fixture
def plugin(tmp_path):
    d = tmp_path / "plugin" / "hooks"
    d.mkdir(parents=True)
    (d / "hook.py").write_text(HOOK)
    return d


def test_alias_is_replaced_by_the_interpreter_it_reports(plugin, tmp_path):
    for name in ("python3", "python"):
        _alias(tmp_path / "alias", name, plugin)
    r = _run([tmp_path / "alias"], plugin / "hook.py")
    assert "can't open file" not in r.stderr
    # The hook ran, read its payload, and its own exit code came through.
    assert r.stderr == 'ran:{"k": 1}'
    assert r.returncode == 2
    assert r.stdout.strip() == "fallback=1"


def test_regular_interpreter_is_not_marked_as_fallback(plugin, tmp_path):
    (tmp_path / "real").mkdir()
    os.symlink(REAL, tmp_path / "real" / "python3")
    r = subprocess.run(
        [BASH, str(SHIM), str(plugin / "hook.py")], input="{}", capture_output=True, text=True, timeout=60,
        env={"PATH": str(tmp_path / "real"), "HOME": "/", "SG_LAUNCHER_FALLBACK": "1"},
    )
    assert r.returncode == 2
    assert r.stdout.strip() == "fallback="


def test_regular_install_later_on_path_is_used(plugin, tmp_path):
    _alias(tmp_path / "alias", "python3", plugin, sealed=True)
    (tmp_path / "real").mkdir()
    os.symlink(REAL, tmp_path / "real" / "python3")
    r = _run([tmp_path / "alias", tmp_path / "real"], plugin / "hook.py")
    assert r.stderr == 'ran:{"k": 1}'
    assert r.returncode == 2


def test_regular_install_under_another_name_is_used(plugin, tmp_path):
    _alias(tmp_path / "alias", "python3", plugin, sealed=True)
    (tmp_path / "real").mkdir()
    os.symlink(REAL, tmp_path / "real" / "python")
    r = _run([tmp_path / "alias", tmp_path / "real"], plugin / "hook.py")
    assert r.stderr == 'ran:{"k": 1}'
    assert r.returncode == 2


def test_no_interpreter_can_see_the_script_is_not_reported_as_findings(plugin, tmp_path):
    for name in ("python3", "python"):
        _alias(tmp_path / "alias", name, plugin, sealed=True)
    r = _run([tmp_path / "alias"], plugin / "hook.py")
    assert r.returncode == 1
    assert "can't open file" not in r.stderr
    assert "cannot read the hook script" in r.stderr
    assert str(plugin / "hook.py") in r.stderr
    assert metrics_of(r.stdout) == {"launcher_unreadable": 1}


def test_missing_script_is_not_reported_as_findings(plugin, tmp_path):
    (tmp_path / "real").mkdir()
    os.symlink(REAL, tmp_path / "real" / "python3")
    r = _run([tmp_path / "real"], plugin / "gone.py")
    assert r.returncode == 1
    assert "can't open file" not in r.stderr


def test_no_python_keeps_its_own_message(plugin, tmp_path):
    (tmp_path / "empty").mkdir()
    r = _run([tmp_path / "empty"], plugin / "hook.py")
    assert r.returncode == 1
    assert "no working Python 3 interpreter found" in r.stderr


def test_unusable_python_keeps_the_no_interpreter_message(plugin, tmp_path):
    # Runs, but is not Python 3: nothing says the script is unreadable.
    d = tmp_path / "old"
    d.mkdir()
    (d / "python").write_text("#!%s\nexit 1\n" % BASH)
    (d / "python").chmod(0o755)
    r = _run([d], plugin / "hook.py")
    assert r.returncode == 1
    assert "no working Python 3 interpreter found" in r.stderr


def test_alias_with_crlf_output_is_still_resolved(plugin, tmp_path):
    # Native Windows Python prints CRLF; the reported path must survive that.
    _alias(tmp_path / "alias", "python3", plugin, crlf=True)
    r = _run([tmp_path / "alias"], plugin / "hook.py")
    assert r.stderr == 'ran:{"k": 1}'
    assert r.returncode == 2


@pytest.mark.skipif(shutil.which("git") is None, reason="needs git")
def test_real_hook_runs_through_an_alias_only_path(tmp_path):
    for name in ("python3", "python"):
        _alias(tmp_path / "alias", name, HOOKS_DIR)
    payload = json.dumps({"hook_event_name": "UserPromptSubmit", "session_id": "launcher-test",
                          "cwd": str(tmp_path), "prompt": "hello"})
    # git only: its directory usually holds a regular python3 as well.
    git_dir = tmp_path / "git"
    git_dir.mkdir()
    os.symlink(shutil.which("git"), git_dir / "git")
    r = subprocess.run(
        [BASH, str(SHIM), str(HOOKS_DIR / "security_reminder_hook.py")],
        input=payload, capture_output=True, text=True, timeout=120,
        env={"PATH": os.pathsep.join([str(tmp_path / "alias"), str(git_dir)]), "HOME": str(tmp_path),
             "SECURITY_GUIDANCE_DEBUG_LOG": str(tmp_path / "debug.log")},
    )
    assert r.returncode == 0, r.stderr
    assert "hook_event=UserPromptSubmit" in (tmp_path / "debug.log").read_text()


@pytest.mark.parametrize("flag", ["1", None])
def test_hook_reports_launcher_fallback(workspace, hook_env, flag):
    env = dict(hook_env)
    env.pop("SG_LAUNCHER_FALLBACK", None)
    if flag:
        env["SG_LAUNCHER_FALLBACK"] = flag
    rc, out, _ = run_hook(stop_payload(workspace), env)
    assert rc == 0
    m = metrics_of(out)
    assert m is not None
    assert m.get("launcher_fallback") == (1 if flag else None)
