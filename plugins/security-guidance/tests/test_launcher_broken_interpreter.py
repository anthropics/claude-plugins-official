"""sg-python.sh tells a broken interpreter from a missing one.

Both used to end in the same "no working Python 3 interpreter found", so a
version manager's shim with no version set read as Python not being installed.
What failed is on the first line, because Claude Code's terminal shows only
that one for a failed hook. See anthropics/claude-code#86709.

The interpreters are shell scripts, which Git Bash starts as well, so this
runs on Windows too.
"""
import os
import shutil
import subprocess
import sys

import pytest

from conftest import HOOKS_DIR

SHIM = HOOKS_DIR / "sg-python.sh"
BASH = shutil.which("bash") or "/bin/bash"
try:
    BASH_MAJOR = int(subprocess.run([BASH, "-c", "echo ${BASH_VERSINFO[0]}"], capture_output=True,
                                    text=True).stdout.strip() or 0)
except (OSError, ValueError):
    BASH_MAJOR = 0
FIRST = "security-guidance: no working Python 3 interpreter found."
WHY = " On PATH but not usable: "


@pytest.fixture
def box(tmp_path):
    (tmp_path / "bin").mkdir()
    (tmp_path / "hook.py").write_text("import sys\nprint('ran', sys.stdin.read())\n")
    return tmp_path


def _add(folder, name, body):
    folder.mkdir(exist_ok=True)
    path = folder / name
    path.write_bytes(("#!/bin/sh\n%s\n" % body).encode())
    path.chmod(0o755)


def _run(box, *folders, ostype=None):
    env = {"HOME": str(box), "SECURITY_WARNINGS_STATE_DIR": str(box / "state")}
    for name in ("SYSTEMROOT", "USERPROFILE", "TEMP"):
        if name in os.environ:
            env[name] = os.environ[name]
    if ostype:
        env["OSTYPE"] = ostype
    # The launcher's own PATH, set inside: Git Bash adds its folders to the one it is given.
    script = 'export PATH="$1"; for f in "${@:4}"; do PATH="$PATH:$f"; done; exec "$2" "$3" "$HOOK"'
    env["HOOK"] = str(box / "hook.py")
    posix = [_posix(f) for f in (folders or (box / "bin",))]
    return subprocess.run([BASH, "-c", script, "bash", posix[0], _posix(BASH), _posix(SHIM)] + posix[1:],
                          input="payload", capture_output=True, text=True, timeout=60, env=env, cwd=box)


def _posix(path):
    path = str(path)
    if sys.platform == "win32" and path[1:2] == ":":
        path = "/" + path[0].lower() + path[2:].replace("\\", "/")
    return path


def test_the_first_line_names_what_failed(box):
    _add(box / "bin", "python3", "exit 127")
    _add(box / "bin", "python", "exit 49")
    r = _run(box)
    assert r.returncode == 1
    lines = r.stderr.splitlines()
    assert lines[0] == FIRST + WHY + "python3 (exit 127), python (exit 49)."
    assert "  failed: python3 (exit 127), python (exit 49)" in lines


def test_the_first_line_has_python3_and_a_later_one_has_them_all(box):
    for minor in (13, 12, 11, 10):
        _add(box / "bin", "python3.%d" % minor, "exit 127")
    _add(box / "bin", "python3", "exit 1")
    lines = _run(box).stderr.splitlines()
    assert lines[0] == FIRST + WHY + "python3 (exit 1), and more."
    assert ("  failed: python3.13 (exit 127), python3.12 (exit 127), python3.11 (exit 127), "
            "python3.10 (exit 127), python3 (exit 1)") in lines


@pytest.mark.parametrize("name", ["python3.12", "python3.14"])
def test_a_versioned_name_is_named_when_it_is_all_there_is(box, name):
    _add(box / "bin", name, "exit 1")
    assert _run(box).stderr.splitlines()[0] == FIRST + WHY + name + " (exit 1)."


@pytest.mark.parametrize("name", ["python3.12", "python3", "python3.14"])
@pytest.mark.parametrize("body", ["exit 0", "echo no version is set; exit 0"])
def test_a_name_that_exits_0_with_no_version_is_named(box, name, body):
    _add(box / "bin", name, body)
    r = _run(box)
    assert r.returncode == 1
    assert r.stderr.splitlines()[0] == FIRST + WHY + name + " (unexpected answer)."
    assert "version is set" not in r.stderr + r.stdout


def test_the_interpreters_own_words_are_not_repeated(box):
    _add(box / "bin", "python3", "echo own-words >&2; echo own-words; exit 1")
    r = _run(box)
    assert r.returncode == 1
    assert "own-words" not in r.stderr + r.stdout


def test_nothing_is_named_when_nothing_is_there(box):
    r = _run(box)
    assert r.returncode == 1
    assert r.stderr.splitlines()[0] == FIRST
    assert "failed:" not in r.stderr and "--version" not in r.stderr


@pytest.mark.parametrize("name", ["python3.12", "python3.14"])
@pytest.mark.parametrize("answer", ["3.9", "1.2.3 is not installed"])
def test_a_versioned_name_with_another_version_is_named(box, name, answer):
    _add(box / "bin", name, "echo '%s'" % answer)
    assert _run(box).stderr.splitlines()[0] == FIRST + WHY + name + " (unexpected answer)."


def test_an_older_python3_is_still_used_and_nothing_is_said(box):
    _add(box / "bin", "python3.12", "echo 3.9")
    _add(box / "bin", "python3", "[ \"$1\" = -c ] && { echo 3.9; exit 0; }; echo older ran")
    r = _run(box)
    assert (r.returncode, r.stdout.strip(), r.stderr) == (0, "older ran", "")


def test_a_folder_named_like_a_version_is_a_path(box):
    _add(box / "bin", "python3", "exit 4")
    _add(box / "python3.12", "python3", "exit 5")
    first = _run(box, box / "bin", "python3.12").stderr.splitlines()[0]
    assert first == FIRST + WHY + "python3 (exit 4), python3 (exit 5)."


def test_several_versioned_names_alone(box):
    _add(box / "bin", "python3.12", "exit 1")
    _add(box / "bin", "python3.14", "exit 2")
    assert _run(box).stderr.splitlines()[0] == FIRST + WHY + "python3.12 (exit 1), and more."


def test_a_wrapper_that_talks_before_it_answers(box):
    _add(box / "bin", "python3", "echo notice; exec '%s' \"$@\"" % _posix(sys.executable))
    r = _run(box)
    assert r.returncode == 1
    assert r.stderr.splitlines()[0] == FIRST + WHY + "python3 (unexpected answer)."


def test_the_py_launcher_is_named_with_its_option(box):
    _add(box / "bin", "py", "exit 103")
    lines = _run(box).stderr.splitlines()
    assert lines[0] == FIRST + WHY + "py -3 (exit 103)."
    assert "  failed: py -3 (exit 103)" in lines


@pytest.mark.parametrize("second", ["second", "Doe, John"])
def test_full_paths_are_kept_off_the_first_line(box, second):
    _add(box / "bin", "python3", "exit 1")
    _add(box / second, "python3", "exit 2")
    lines = _run(box, box / "bin", box / second).stderr.splitlines()
    assert lines[0] == FIRST + WHY + "python3 (exit 1), python3 (exit 2)."
    assert any(line.startswith("  failed: python3 (exit 1), ") and line.endswith(second + "/python3 (exit 2)")
               for line in lines)


def test_a_second_one_that_gives_no_version(box):
    _add(box / "bin", "python3", "exit 1")
    _add(box / "second", "python3", "exit 0")
    first = _run(box, box / "bin", box / "second").stderr.splitlines()[0]
    assert first == FIRST + WHY + "python3 (exit 1), python3 (unexpected answer)."


def test_the_same_failure_in_two_folders_is_on_the_first_line_once(box):
    _add(box / "bin", "python3", "exit 127")
    _add(box / "second", "python3", "exit 127")
    assert _run(box, box / "bin", box / "second").stderr.splitlines()[0] == FIRST + WHY + "python3 (exit 127)."


def _skipped_alias(box, code):
    """The launcher as Git Bash runs it: python is App Installer's alias, one more behind it."""
    apps = box / "AppData" / "Local" / "Microsoft" / "WindowsApps"
    target = box / "Microsoft.DesktopAppInstaller_8wekyb3d8bbwe"
    _add(target, "AppInstallerPythonRedirector.exe", "exit 49")
    apps.mkdir(parents=True)
    os.symlink(target / "AppInstallerPythonRedirector.exe", apps / "python")
    _add(box / "Doe, John", "python", "exit %d" % code)
    return apps


@pytest.mark.skipif(sys.platform == "win32", reason="the alias is emulated with a link")
@pytest.mark.skipif(BASH_MAJOR < 4, reason="the launcher tells aliases apart in bash 4 and later")
def test_a_broken_one_behind_a_skipped_alias(box):
    apps = _skipped_alias(box, 127)
    r = _run(box, apps, box / "Doe, John", ostype="msys")
    lines = r.stderr.splitlines()
    assert lines[0] == FIRST + WHY + "python (exit 127)."
    assert any(line.startswith("  not started: python (") for line in lines)


def test_failures_are_listed_next_to_an_interpreter_that_cannot_read_the_hook(box):
    _add(box / "bin", "python3", "exit 3")
    _add(box / "bin", "python", "exit 127")
    r = _run(box)
    assert r.returncode == 1
    assert "cannot read the hook script" in r.stderr.splitlines()[0]
    assert "  also tried: python (exit 127)" in r.stderr.splitlines()
    assert "launcher_unreadable" in r.stdout


@pytest.mark.parametrize("body", ["exit 1", "exit 0", "echo 3.9"])
def test_a_failed_name_is_not_reported_when_another_works(box, body):
    _add(box / "bin", "python3.13", body)
    _add(box / "bin", "python3", "exit 1")
    _add(box / "bin", "python", "exec '%s' \"$@\"" % _posix(sys.executable))
    r = _run(box)
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == "ran payload"
    assert r.stderr == ""
