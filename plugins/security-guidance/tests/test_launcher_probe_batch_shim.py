"""The code sg-python.sh gives to `python -c` survives a batch file.

pyenv-win's `python3` is a shell script that ends in a .bat file, so cmd.exe
reads the arguments again. Released versions (3.1.1) store them with
`set "cmdline=%*"`, whose first quote puts quoted text outside quotes: a ">=" in
the probe then wrote an empty file named `(3` in the project, and Python got
the rest of the line and failed. With no other Python no hook ran. See #7172.
"""
import os
import re
import shutil
import subprocess
import sys

import pytest

from conftest import HOOKS_DIR

SHIM = HOOKS_DIR / "sg-python.sh"
REAL = os.path.realpath(sys.executable)
BASH = shutil.which("bash") or "/bin/bash"

# Keeps the code of each probe, then behaves like the real interpreter.
RECORDING = """#!{bash}
[ "${{1:-}}" = "-c" ] && printf '%s\\0' "$2" >> '{log}'
exec '{real}' "$@"
"""
# A packaged alias: cannot read the hook script, but says where its interpreter is.
ALIAS = """#!{bash}
printf '%s\\0' "$2" >> '{log}'
case "$2" in *sys.argv*) exit 3 ;; esac
echo '{own}'
"""


def _add(folder, name, template, **kw):
    (folder / "bin").mkdir(exist_ok=True)
    path = folder / "bin" / name
    path.write_text(template.format(bash=BASH, real=REAL, **kw))
    path.chmod(0o755)
    return path


def _run(folder):
    (folder / "hook.py").write_text("print('ran')\n")
    return subprocess.run([BASH, str(SHIM), str(folder / "hook.py")], input="", capture_output=True,
                          text=True, timeout=60, env={"PATH": str(folder / "bin"), "HOME": "/"})


@pytest.fixture(scope="module")
def probes(tmp_path_factory):
    """The code of both kinds of probe, as the interpreter gets it."""
    if sys.platform == "win32":
        pytest.skip("POSIX shell wrappers")
    folder = tmp_path_factory.mktemp("probes")
    log = folder / "log"
    own = _add(folder, "own", RECORDING, log=log)
    _add(folder, "python3", ALIAS, log=log, own=own)
    r = _run(folder)
    assert r.returncode == 0 and r.stdout.strip() == "ran", r.stderr
    alias_version, alias_path, own_version = log.read_text().split("\0")[:-1]
    assert alias_version == own_version and "sys.executable" in alias_path
    return own_version, alias_path


def test_probes_have_only_characters_that_arrive_unchanged(probes):
    for code in probes:
        assert re.fullmatch(r"""[a-zA-Z0-9_ "'.,:;=()\[\]{}]+""", code), code
        assert code.count('"') % 2 == 0, code


def test_there_is_no_other_python_code_in_the_launcher():
    text = "\n".join(line for line in SHIM.read_text(encoding="utf-8").splitlines()
                     if not line.lstrip().startswith("#"))
    calls = [m for m in re.findall(r"(\S+)\s+-\w*c(?![\w-])", text) if m not in ("[", "&&")]
    assert calls == ['"$@"', "$cmd"]


@pytest.mark.parametrize("platform, version, path", [
    ("win32", (3, 9, 18), False), ("win32", (3, 10, 0), True), ("win32", (3, 14, 0), True),
    ("win32", (4, 0, 0), True), ("linux", (3, 14, 0), False), ("darwin", (3, 14, 0), False)])
@pytest.mark.parametrize("target", ["", "hook.py"])
def test_path_is_printed_on_windows_from_3_10(probes, tmp_path, platform, version, path, target):
    (tmp_path / "hook.py").write_text("")
    code = (f"import sys; sys.version_info = {version + ('final', 0)}; sys.platform = {platform!r}; "
            "sys.executable = 'EXE'\n" + probes[0])
    r = subprocess.run([REAL, "-c", code, target], cwd=tmp_path, capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr
    assert r.stdout.splitlines() == [f"{version[0]}.{version[1]}"] + ["EXE"] * path


@pytest.mark.parametrize("platform, code", [("win32", 3), ("linux", 0), ("darwin", 0)])
def test_a_lost_argument_is_noticed_on_windows_only(probes, platform, code):
    r = subprocess.run([REAL, "-c", f"import sys; sys.platform = {platform!r}\n" + probes[0]],
                       capture_output=True, text=True, timeout=60)
    assert r.returncode == code, r.stderr


def _git_bash():
    """Git for Windows' bash: PATH's can be the WSL launcher, which cannot open C:/ paths."""
    git = shutil.which("git")
    if not git:
        return None
    folder = os.path.realpath(git)
    while folder != os.path.dirname(folder):
        folder = os.path.dirname(folder)
        bash = os.path.join(folder, "bin", "bash.exe")
        if os.path.isfile(bash):
            r = subprocess.run([bash, "-c", "echo $OSTYPE"], capture_output=True, timeout=30)
            if r.stdout.strip().startswith((b"msys", b"cygwin")):
                return bash
    return None


def _run_git_bash(tmp_path, folder, names):
    bash = _git_bash()
    if not bash:
        pytest.skip("no Git Bash")
    bin_dir, project, plugin = tmp_path / "bin", tmp_path / "project", tmp_path / folder
    for d in (bin_dir, project, plugin):
        d.mkdir()
    for name, text in names.items():
        (bin_dir / name).write_bytes(text)
    (plugin / "hook.py").write_text("import sys; print('ran', sys.stdin.read()); sys.exit(2)\n")
    root = os.environ["SystemRoot"]
    env = {"PATH": os.pathsep.join([str(bin_dir), os.path.dirname(bash), os.path.join(root, "System32")]),
           "SystemRoot": root, "ComSpec": os.environ["ComSpec"], "PATHEXT": ".COM;.EXE;.BAT;.CMD",
           "HOME": str(tmp_path), "TEMP": str(tmp_path), "TMP": str(tmp_path),
           "SG_TEST_LOG": str(tmp_path / "log"), "SG_TEST_REAL": REAL}
    r = subprocess.run([bash, "--noprofile", "--norc", SHIM.as_posix(), (plugin / "hook.py").as_posix()],
                       cwd=project, input="payload", capture_output=True, text=True, timeout=120, env=env)
    assert os.listdir(project) == []
    assert (r.returncode, r.stdout.strip()) == (2, "ran payload"), r.stderr
    return (tmp_path / "log").read_text()


windows = pytest.mark.skipif(sys.platform != "win32" or sys.version_info < (3, 10),
                             reason="cmd.exe, Python 3.10")


@windows
@pytest.mark.parametrize("folder", ["plain", "with space"])
def test_launcher_through_a_batch_file_that_drops_the_quoting(tmp_path, folder):
    # 3.13 is the first name tried, so no other Python comes before it.
    assert "started" in _run_git_bash(tmp_path, folder, {
        "python3.13": b'#!/bin/sh\nexec "$(dirname "$0")/shim.bat" "$@"\n',
        "shim.bat": b'@set "cmdline=%*"\r\n@echo started>>"%SG_TEST_LOG%"\r\n'
                    b'@"%SG_TEST_REAL%" %cmdline%\r\n'})


@windows
def test_a_name_that_loses_arguments_is_started_by_its_real_path(tmp_path):
    log = _run_git_bash(tmp_path, "plain", {"python3": b"""#!/bin/sh
echo "$1" >> "$SG_TEST_LOG"
[ "$1" = "-c" ] && exec "$SG_TEST_REAL" -c "$2"
exec "$SG_TEST_REAL"
"""})
    # Asked for its version and its real path, never given the hook.
    assert len(log.split()) >= 2 and set(log.split()) == {"-c"}
