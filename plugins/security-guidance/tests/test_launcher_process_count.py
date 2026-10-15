"""sg-python.sh starts as few processes as it can before it runs the hook.

Under Git Bash every command substitution is a new Windows process, and the
launcher runs on every hook, so probing interpreters that are not installed,
probing the same one twice, or calling cygpath for a plain drive path is paid
on each Edit, prompt and Stop. See #6470.

Interpreters and cygpath are emulated with shell scripts, so these tests need
a POSIX shell.
"""
import shutil
import subprocess
import sys

import pytest

from conftest import HOOKS_DIR

pytestmark = pytest.mark.skipif(sys.platform == "win32", reason="POSIX shell wrappers")

SHIM = HOOKS_DIR / "sg-python.sh"
BASH = shutil.which("bash") or "/bin/bash"

# Logs each start; answers the probe with a fixed version, else prints its argv.
PYTHON = """#!{bash}
if [ "${{1:-}}" = "-c" ] || [ "${{1:-}} ${{2:-}}" = "-3 -c" ]; then
  echo "${{0##*/}} probe" >> '{log}'; printf '{version}{eol}'; exit 0
fi
echo "${{0##*/}} $*" >> '{log}'
printf 'ran:%s\\n' "${{0##*/}}"; printf 'arg:%s\\n' "$@"
"""
# ${x^^} in the launcher's Git Bash branch needs bash 4; stock macOS has 3.2.
BASH_MAJOR = int(subprocess.run([BASH, "-c", "echo ${BASH_VERSINFO[0]}"], capture_output=True,
                                text=True).stdout.strip() or 0)

# The Microsoft Store placeholder: on PATH, starts, does nothing.
STUB = """#!{bash}
echo "${{0##*/}} probe" >> '{log}'
exit 49
"""
CYGPATH = """#!{bash}
echo "cygpath $*" >> '{log}'
echo "CYGPATH($2)"
"""


@pytest.fixture
def box(tmp_path):
    (tmp_path / "bin").mkdir()
    (tmp_path / "log").write_text("")
    return tmp_path


def _add(box, name, template, version="", crlf=False):
    p = box / "bin" / name
    p.write_text(template.format(bash=BASH, log=box / "log", version=version,
                                 eol="\\r\\n" if crlf else "\\n"))
    p.chmod(0o755)


def _run(box, *args, ostype="linux-gnu", trace=False):
    cmd = [BASH] + (["-x"] if trace else []) + [str(SHIM), *args]
    return subprocess.run(cmd, input="", capture_output=True, text=True, timeout=60,
                          env={"PATH": str(box / "bin"), "HOME": "/", "OSTYPE": ostype})


def _starts(box):
    return (box / "log").read_text().splitlines()


def test_only_installed_interpreters_are_probed(box):
    _add(box, "python", PYTHON, "3.12")
    r = _run(box, "hook.py", trace=True)
    assert r.stdout.splitlines() == ["ran:python", "arg:hook.py"]
    probes = [line for line in r.stderr.splitlines() if line.startswith("+ probe ")]
    assert probes == ["+ probe python"]
    # xtrace marks what runs in a child process with "++": only that probe did.
    assert len([line for line in r.stderr.splitlines() if line.startswith("++")]) == 1
    assert _starts(box) == ["python probe", "python hook.py"]


def test_store_placeholder_still_falls_through_to_python(box):
    _add(box, "python3", STUB)
    _add(box, "python", PYTHON, "3.13")
    r = _run(box, "hook.py")
    assert r.stdout.splitlines() == ["ran:python", "arg:hook.py"]
    assert _starts(box) == ["python3 probe", "python probe", "python hook.py"]


def test_python_below_3_10_is_probed_once(box):
    _add(box, "python3", PYTHON, "3.9")
    r = _run(box, "hook.py")
    assert r.stdout.splitlines() == ["ran:python3", "arg:hook.py"]
    assert _starts(box) == ["python3 probe", "python3 hook.py"]


def test_first_older_python_wins_when_none_is_3_10(box):
    _add(box, "python3", PYTHON, "3.8")
    _add(box, "python", PYTHON, "3.9")
    r = _run(box, "hook.py")
    assert r.stdout.splitlines() == ["ran:python3", "arg:hook.py"]


def test_newer_python_under_a_later_name_beats_an_older_python3(box):
    _add(box, "python3", PYTHON, "3.9")
    _add(box, "python", PYTHON, "3.12")
    r = _run(box, "hook.py")
    assert r.stdout.splitlines() == ["ran:python", "arg:hook.py"]


def test_py_launcher_is_still_a_candidate(box):
    _add(box, "py", PYTHON, "3.12")
    r = _run(box, "hook.py")
    assert r.stdout.splitlines() == ["ran:py", "arg:-3", "arg:hook.py"]
    assert _starts(box) == ["py probe", "py -3 hook.py"]


def test_crlf_version_output_does_not_cost_further_probes(box):
    # Native Windows Python may print CRLF; 3.12 must still read as 3.10+.
    _add(box, "python", PYTHON, "3.12", crlf=True)
    _add(box, "py", PYTHON, "3.12", crlf=True)
    r = _run(box, "hook.py")
    assert r.stdout.splitlines() == ["ran:python", "arg:hook.py"]
    assert _starts(box) == ["python probe", "python hook.py"]


@pytest.mark.skipif(BASH_MAJOR < 4, reason="needs bash 4+, as Git Bash has")
@pytest.mark.parametrize("posix, native", [
    ("/c/Users/me/.claude/hooks/hook.py", "C:\\Users\\me\\.claude\\hooks\\hook.py"),
    ("/d/a b/hook.py", "D:\\a b\\hook.py"),
    ("/c/", "C:\\"),
])
def test_drive_paths_are_converted_without_cygpath(box, posix, native):
    _add(box, "cygpath", CYGPATH)
    _add(box, "python", PYTHON, "3.12")
    rest = ["--flag", "rel/path", "C:\\already\\native", "C:/d/mixed"]
    r = _run(box, posix, *rest, ostype="msys")
    assert r.stdout.splitlines() == ["ran:python", "arg:" + native] + ["arg:" + a for a in rest]
    assert not [s for s in _starts(box) if s.startswith("cygpath")]


@pytest.mark.parametrize("ostype, posix", [
    ("msys", "/tmp/hook.py"),          # a mount point, not a drive
    ("msys", "/usr/bin"),
    ("msys", "/c"),
    ("msys", "//server/share/hook.py"),
    ("cygwin", "/c/Users/me/hook.py"),  # drives live under /cygdrive there
])
def test_other_absolute_paths_still_go_through_cygpath(box, ostype, posix):
    _add(box, "cygpath", CYGPATH)
    _add(box, "python", PYTHON, "3.12")
    r = _run(box, posix, ostype=ostype)
    assert r.stdout.splitlines() == ["ran:python", "arg:CYGPATH(%s)" % posix]


def test_paths_are_left_alone_without_cygpath(box):
    _add(box, "python3", PYTHON, "3.12")
    r = _run(box, "/c/Users/me/hook.py", ostype="msys")
    assert r.stdout.splitlines() == ["ran:python3", "arg:/c/Users/me/hook.py"]
