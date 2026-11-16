"""sg-python.sh does not start the python/python3 that App Installer provides.

On Windows without a packaged Python, `python3` under ...\\Microsoft\\WindowsApps
is a link to AppInstallerPythonRedirector.exe, which is not a Python. Starting
it on every hook makes the hook wait for Windows' package services, and hang
while they do not answer. See #3870, #6348.

Aliases are shell scripts behind a symbolic link, so these tests need a POSIX
shell; the launcher's Windows branch is switched on with OSTYPE.
"""
import json
import os
import shutil
import subprocess
import sys

import pytest

from conftest import HOOKS_DIR

SHIM = HOOKS_DIR / "sg-python.sh"
BASH = shutil.which("bash") or "/bin/bash"
REAL = os.path.realpath(sys.executable)
try:
    BASH_MAJOR = int(subprocess.run([BASH, "-c", "echo ${BASH_VERSINFO[0]}"], capture_output=True,
                                    text=True, timeout=30).stdout.strip() or 0)
except (OSError, ValueError, subprocess.SubprocessError):
    BASH_MAJOR = 0

pytestmark = pytest.mark.skipif(sys.platform == "win32", reason="POSIX shell wrappers")
needs_bash4 = pytest.mark.skipif(BASH_MAJOR < 4, reason="the Windows branch needs bash 4")

HOOK = "import os, sys\nprint('name=' + os.environ.get('SG_NAME', ''))\nprint('stdin=' + sys.stdin.read())\n"


class Box:
    def __init__(self, root):
        self.apps = root / "AppData" / "Local" / "Microsoft" / "WindowsApps"
        self.pkg = root / "Program Files" / "WindowsApps" / "Microsoft.DesktopAppInstaller_1.29.379.0_x64__8wekyb3d8bbwe"
        self.bin = root / "bin"
        self.late = root / "late"
        self.log = root / "log"
        for d in (self.apps, self.pkg, self.bin, self.late):
            d.mkdir(parents=True)
        self.log.write_text("")
        self.script = root / "hook.py"
        self.script.write_text(HOOK)
        # Names the launcher tries that this machine may really have.
        for name in ("python3.13", "python3.12", "python3.11", "python3.10", "python3.14", "py"):
            self.broken(self.bin / name)

    def write(self, path, text):
        path.write_text(text)
        path.chmod(0o755)

    def broken(self, path):
        self.write(path, f"#!{BASH}\nexit 49\n")

    def python(self, path):
        self.write(path, f"#!{BASH}\necho {path.name} >> '{self.log}'\nSG_NAME={path.name} exec '{REAL}' \"$@\"\n")

    def alias(self, name, target="AppInstallerPythonRedirector.exe", hangs=False):
        """An entry under WindowsApps that leads to `target`, and logs its starts."""
        exe = self.pkg / target
        body = "sleep 300" if hangs else "exit 49"
        self.write(exe, f"#!{BASH}\necho redirector >> '{self.log}'\n{body}\n")
        (self.apps / name).symlink_to(exe)

    def path(self, *first):
        return os.pathsep.join([*(str(p) for p in first), str(self.bin), "/usr/bin", "/bin"])

    def run(self, path, ostype="msys", timeout=60):
        env = {"PATH": path, "HOME": os.environ.get("HOME", "/"), "OSTYPE": ostype,
               "SECURITY_WARNINGS_STATE_DIR": str(self.log.parent / "state")}
        return subprocess.run([BASH, str(SHIM), str(self.script)], input="payload", capture_output=True,
                              text=True, timeout=timeout, env=env)

    @property
    def starts(self):
        return self.log.read_text().split()


def _tools(box):
    """A PATH entry with readlink and no Python of the machine's own."""
    d = box.log.parent / "tools"
    d.mkdir(exist_ok=True)
    for name in ("readlink", "sleep"):
        if not (d / name).exists():
            (d / name).symlink_to(shutil.which(name))
    return str(d)


@pytest.fixture
def box(tmp_path):
    return Box(tmp_path)


@needs_bash4
def test_redirector_is_not_started(box):
    box.alias("python3")
    box.python(box.bin / "python")
    r = box.run(box.path(box.apps))
    assert r.returncode == 0, r.stderr
    assert r.stdout.splitlines() == ["name=python", "stdin=payload"]
    assert "redirector" not in box.starts


@needs_bash4
def test_redirector_that_never_answers_does_not_hold_the_hook(box):
    box.alias("python3", hangs=True)
    box.python(box.bin / "python")
    r = box.run(box.path(box.apps), timeout=30)
    assert r.returncode == 0 and "name=python" in r.stdout


@needs_bash4
def test_both_names_lead_to_the_redirector(box):
    # python and python3 both first on PATH as redirectors, a real python
    # further down: found by its full path, as before.
    box.alias("python3")
    box.alias("python")
    box.python(box.late / "python")
    r = box.run(os.pathsep.join([str(box.apps), str(box.late), str(box.bin), "/nowhere"])
                + os.pathsep + _tools(box))
    assert r.returncode == 0, r.stderr
    assert "name=python" in r.stdout
    assert "redirector" not in box.starts


@needs_bash4
def test_only_redirectors_is_reported_as_no_python(box):
    box.alias("python3")
    box.alias("python")
    r = box.run(os.pathsep.join([str(box.apps), str(box.bin), _tools(box)]))
    assert r.returncode == 1
    assert "no working Python 3 interpreter found" in r.stderr
    assert "not started: python3, python (App Installer's alias" in r.stderr
    assert box.starts == []


@needs_bash4
@pytest.mark.parametrize("ostype", ["msys", "cygwin"])
def test_redirector_behind_a_broken_python_is_not_started(box, ostype):
    # Pass 4 collects every further python3 on PATH by its full path.
    box.alias("python3")
    box.broken(box.bin / "python3")
    box.broken(box.bin / "python")
    r = box.run(os.pathsep.join([str(box.bin), str(box.apps), _tools(box)]), ostype=ostype)
    assert r.returncode == 1
    assert box.starts == []


@needs_bash4
def test_link_outside_windowsapps_is_not_looked_at(box):
    # Only aliases are told by their link; any other python3 is asked.
    box.alias("python3")
    (box.apps / "python3").rename(box.late / "python3")
    box.python(box.bin / "python")
    r = box.run(box.path(box.late))
    assert r.returncode == 0 and "name=python" in r.stdout
    assert "redirector" in box.starts


@needs_bash4
def test_readlink_on_path_is_not_relied_on(box):
    box.alias("python3")
    box.python(box.bin / "python")
    box.broken(box.bin / "readlink")
    r = box.run(box.path(box.apps))
    assert r.returncode == 0 and "redirector" not in box.starts



@needs_bash4
def test_packaged_python_alias_is_still_used(box):
    # An alias of a packaged Python leads to that Python, not to the redirector.
    pkg = box.pkg.parent / "PythonSoftwareFoundation.Python.3.12_3.12.2800.0_x64__qbz5n2kfra8p0"
    pkg.mkdir()
    box.python(pkg / "python3.12.exe")
    (box.apps / "python3").symlink_to(pkg / "python3.12.exe")
    box.broken(box.bin / "python")
    r = box.run(box.path(box.apps))
    assert r.returncode == 0, r.stderr
    assert "stdin=payload" in r.stdout
    assert "python3.12.exe" in box.starts


@needs_bash4
def test_unreadable_link_is_probed_as_before(box):
    # Not a link at all (or readlink missing): the name is started and fails.
    box.write(box.apps / "python3", f"#!{BASH}\necho redirector >> '{box.log}'\nexit 49\n")
    box.python(box.bin / "python")
    r = box.run(box.path(box.apps))
    assert r.returncode == 0 and "name=python" in r.stdout
    assert "redirector" in box.starts


def test_other_systems_do_not_look_at_links(box):
    box.alias("python3")
    box.python(box.bin / "python")
    r = box.run(box.path(box.apps), ostype="linux-gnu")
    assert r.returncode == 0 and "name=python" in r.stdout
    assert "redirector" in box.starts


def test_edit_hook_has_a_time_limit():
    """The edit hook holds the tool call; without a limit of its own a stuck
    one holds it for the host's 600 s default. See #6348."""
    groups = json.loads((HOOKS_DIR / "hooks.json").read_text())["hooks"]["PostToolUse"]
    (edit,) = [g for g in groups if "Edit" in g["matcher"]]
    assert [h.get("timeout") for h in edit["hooks"]] == [60]
    # The background reviews keep the host's limit: they run past a minute.
    for g in groups:
        if g is not edit:
            assert all("timeout" not in h for h in g["hooks"])
