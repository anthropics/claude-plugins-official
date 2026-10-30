"""sg-python.sh stops starting a packaged Windows alias on every hook.

When the name that answers is an alias under ...\\Microsoft\\WindowsApps and
its interpreter is a regular file elsewhere, the hook runs with that file and
the path is remembered for a day, so later hooks are one process and none
through the alias. See anthropics/claude-code#98929.

Aliases and interpreters are shell wrappers, so these tests need a POSIX
shell; the launcher's Windows branch is switched on with OSTYPE.
"""
import os
import shutil
import subprocess
import sys
import time

import pytest

from conftest import HOOKS_DIR, metrics_of, run_hook, stop_payload

SHIM = HOOKS_DIR / "sg-python.sh"
BASH = shutil.which("bash") or "/bin/bash"
REAL = os.path.realpath(sys.executable)
VERSION = f"{sys.version_info[0]}.{sys.version_info[1]}"
try:
    BASH_MAJOR = int(subprocess.run([BASH, "-c", "echo ${BASH_VERSINFO[0]}"], capture_output=True,
                                    text=True, timeout=30).stdout.strip() or 0)
except (OSError, ValueError, subprocess.SubprocessError):
    BASH_MAJOR = 0

pytestmark = pytest.mark.skipif(sys.platform == "win32", reason="POSIX shell wrappers")

HOOK = (
    "import os, sys\n"
    "print('direct=' + os.environ.get('SG_LAUNCHER_DIRECT', ''))\n"
    "print('exe=' + os.environ.get('SG_NAME', ''))\n"
    "print('argv=' + ' '.join(sys.argv[1:]))\n"
    "print('stdin=' + sys.stdin.read())\n"
)

# A packaged alias: answers the probe like Windows Python does (version, then
# sys.executable, CRLF), and runs the hook itself when asked to.
ALIAS = """#!{bash}
[ "${{0##*/}}" = "py" ] && [ "${{1:-}}" = "-3" ] && shift
if [ "${{1:-}}" = "-c" ]; then
  echo "${{0##*/}} probe" >> '{log}'; printf '{version}\\r\\n{own}\\r\\n'; exit 0
fi
echo "${{0##*/}} run" >> '{log}'
SG_NAME=alias exec '{real}' "$@"
"""
# The interpreter behind it: the real one, logging its starts.
OWN = """#!{bash}
if [ "${{1:-}}" = "-c" ]; then
  echo "own probe" >> '{log}'
  [ {rc} -eq 0 ] || exit {rc}
else
  echo "own run" >> '{log}'
fi
SG_NAME=own exec '{real}' "$@"
"""


class Box:
    def __init__(self, tmp_path):
        self.root = tmp_path
        self.apps = tmp_path / "AppData" / "Local" / "Microsoft" / "WindowsApps"
        self.own = tmp_path / "AppData" / "Local" / "Python" / "pythoncore-3-64" / "python.exe"
        self.state = tmp_path / "state"
        self.log = tmp_path / "log"
        self.hooks = tmp_path / "plugin" / "hooks"
        for d in (self.apps, self.own.parent, self.state, self.hooks):
            d.mkdir(parents=True)
        self.log.write_text("")
        self.script = self.hooks / "hook.py"
        self.script.write_text(HOOK)
        self.memo = self.state / "launcher-python"

    def write(self, path, template, **kw):
        kw = {"version": VERSION, "own": self.own, "rc": 0, **kw}
        path.write_text(template.format(bash=BASH, log=self.log, real=REAL, **kw))
        path.chmod(0o755)

    def alias(self, name="py", **kw):
        self.write(self.apps / name, ALIAS, **kw)

    def interpreter(self, **kw):
        self.write(self.own, OWN, **kw)

    def launch(self, *args, script=None, ostype="msys", path=None, **extra_env):
        env = {"PATH": path or str(self.apps), "HOME": str(self.root), "OSTYPE": ostype,
               "SECURITY_WARNINGS_STATE_DIR": str(self.state)}
        env.update(extra_env)
        self.log.write_text("")
        return subprocess.run([BASH, str(SHIM), str(script or self.script), *args], input="payload",
                              capture_output=True, text=True, timeout=60, env=env)

    def run(self, *args, **kw):
        r = self.launch(*args, **kw)
        assert r.returncode == 0 and r.stderr == "", r.stderr
        out = dict(line.split("=", 1) for line in r.stdout.splitlines())
        return out, self.starts()

    def starts(self):
        return self.log.read_text().splitlines()


@pytest.fixture
def box(tmp_path):
    if BASH_MAJOR < 5:
        pytest.skip("the remembered route needs bash 5")
    b = Box(tmp_path)
    b.alias()
    b.interpreter()
    return b


def test_first_hook_checks_the_interpreter_and_runs_it(box):
    out, starts = box.run("extra")
    assert starts == ["py probe", "own probe", "own run"]
    assert (out["exe"], out["direct"], out["argv"], out["stdin"]) == ("own", "2", "extra", "payload")
    assert box.memo.read_text().splitlines()[3] == str(box.own)


def test_later_hooks_are_one_process_and_never_the_alias(box):
    box.run()
    for _ in range(3):
        out, starts = box.run("extra")
        assert starts == ["own run"]
        assert (out["exe"], out["direct"], out["argv"], out["stdin"]) == ("own", "1", "extra", "payload")


def test_state_folder_follows_the_config_dir(box):
    (box.root / "cfg" / "security").mkdir(parents=True)
    env = {"SECURITY_WARNINGS_STATE_DIR": "", "CLAUDE_CONFIG_DIR": str(box.root / "cfg")}
    box.run(**env)
    assert (box.root / "cfg" / "security" / "launcher-python").exists()
    assert box.run(**env)[1] == ["own run"]
    (box.root / ".claude" / "security").mkdir(parents=True)
    env["CLAUDE_CONFIG_DIR"] = ""
    box.run(**env)
    assert (box.root / ".claude" / "security" / "launcher-python").exists()
    assert not box.memo.exists()


def test_changed_path_is_searched_again(box):
    box.run()
    other = box.root / "other"
    other.mkdir()
    out, starts = box.run(path=f"{box.apps}{os.pathsep}{other}")
    assert starts == ["py probe", "own probe", "own run"] and out["direct"] == "2"


def test_another_hook_folder_is_checked_again(box):
    box.run()
    moved = box.root / "plugin-next" / "hooks"
    moved.mkdir(parents=True)
    (moved / "hook.py").write_text(HOOK)
    out, starts = box.run(script=moved / "hook.py")
    assert starts == ["py probe", "own probe", "own run"]
    # Same folder, another hook script: still the remembered route.
    (moved / "other.py").write_text(HOOK)
    assert box.run(script=moved / "other.py")[1] == ["own run"]


@pytest.mark.parametrize("shift", [-86400 - 60, 3600])
def test_entry_is_trusted_for_a_day(box, shift):
    box.run()
    lines = box.memo.read_text().splitlines()
    lines[1] = str(int(time.time()) + shift)
    box.memo.write_text("\n".join(lines) + "\n")
    out, starts = box.run()
    assert starts == ["py probe", "own probe", "own run"]
    assert abs(int(box.memo.read_text().splitlines()[1]) - time.time()) < 120


@pytest.mark.parametrize("damage", [
    lambda lines: lines[:4],                                   # cut short while being written
    lambda lines: ["sg-launcher-python 0"] + lines[1:],        # another format
    lambda lines: lines[:1] + ["soon"] + lines[2:],
    lambda lines: lines[:1] + ["9" * 30] + lines[2:],
    lambda lines: lines[:3] + ["/bin/sh"] + lines[4:],         # not an interpreter
    lambda lines: lines[:3] + ["tools/python.exe"] + lines[4:],  # not absolute
    lambda lines: lines[:3] + [lines[4] + "/python.exe"] + lines[4:],  # a folder (made below)
    lambda lines: lines[:5] + ["more"],
    lambda lines: [],
])
def test_damaged_entry_is_ignored_and_replaced(box, damage):
    box.run()
    (box.hooks / "python.exe").mkdir()
    good = box.memo.read_text()
    box.memo.write_text("".join(line + "\n" for line in damage(good.splitlines())))
    out, starts = box.run()
    assert starts == ["py probe", "own probe", "own run"] and out["stdin"] == "payload"
    assert box.memo.read_text().splitlines()[2:] == good.splitlines()[2:]


def test_remembered_alias_path_is_never_started(box):
    box.run()
    lines = box.memo.read_text().splitlines()
    inner = box.apps / "python.exe"
    box.write(inner, OWN)
    lines[3] = str(inner)
    box.memo.write_text("\n".join(lines) + "\n")
    assert box.run()[1] == ["py probe", "own probe", "own run"]


def test_removed_interpreter_falls_back_to_the_alias(box):
    box.run()
    box.own.unlink()
    out, starts = box.run()
    assert starts == ["py probe", "py run"]
    assert (out["exe"], out["direct"], out["stdin"]) == ("alias", "", "payload")


def test_missing_hook_script_is_not_run_from_memory(box):
    box.run()
    box.script.unlink()
    box.launch()
    # The full search ran: the remembered interpreter was not started first.
    assert box.starts()[0] == "py probe"


@pytest.mark.parametrize("code", [1, 2])
def test_failed_hook_on_the_remembered_path_empties_the_entry(box, code):
    box.run()
    failing = box.hooks / "fails.py"
    failing.write_text(f"import sys\nsys.stderr.write('findings')\nsys.exit({code})\n")
    r = box.launch(script=failing)
    # Its exit code and output pass through unchanged, once.
    assert (r.returncode, r.stderr, box.starts()) == (code, "findings", ["own run"])
    assert box.memo.read_text() == ""
    out, starts = box.run()
    assert starts == ["py probe", "own probe", "own run"] and out["direct"] == "2"
    assert box.run()[1] == ["own run"]


def test_virtual_environment_keeps_the_alias(box):
    box.run()
    out, starts = box.run(VIRTUAL_ENV=str(box.root / "venv"))
    assert starts == ["py probe", "py run"] and (out["exe"], out["direct"]) == ("alias", "")


def test_tilde_and_userprofile_resolve_like_the_hooks_do(box):
    profile = box.root / "profile"
    (profile / "st").mkdir(parents=True)
    env = {"SECURITY_WARNINGS_STATE_DIR": "~/st", "USERPROFILE": str(profile)}
    box.run(**env)
    assert (profile / "st" / "launcher-python").exists()
    assert box.run(**env)[1] == ["own run"]
    (profile / ".claude" / "security").mkdir(parents=True)
    env["SECURITY_WARNINGS_STATE_DIR"] = ""
    box.run(**env)
    assert (profile / ".claude" / "security" / "launcher-python").exists()


def test_unwritable_entry_is_silent(box):
    box.memo.mkdir()
    for _ in range(2):
        out, starts = box.run()   # run() asserts an empty stderr
        assert starts == ["py probe", "own probe", "own run"]


def test_windows_form_path_goes_through_cygpath(box):
    # OSTYPE=cygwin has no /<drive> mounts: the answer is converted by cygpath.
    box.write(box.apps / "cygpath", """#!{bash}
echo "cygpath $1" >> '{log}'
[ "$1" = "-u" ] && [ "$2" = 'C:\\Py\\python.exe' ] && {{ echo '{own}'; exit 0; }}
echo "$2"
""")
    box.alias(own="C:\\\\Py\\\\python.exe")
    out, starts = box.run(ostype="cygwin")
    assert [s for s in starts if not s.startswith("cygpath -w")] == [
        "py probe", "cygpath -u", "own probe", "own run"]
    assert (out["exe"], out["direct"]) == ("own", "2")
    assert box.memo.read_text().splitlines()[3] == str(box.own)
    assert [s for s in box.run(ostype="cygwin")[1] if not s.startswith("cygpath -w")] == ["own run"]


@pytest.mark.parametrize("name", ["pypy3.exe", "python"])
def test_interpreter_by_another_name_is_neither_checked_nor_remembered(box, name):
    other = box.own.parent / name
    box.write(other, OWN)
    box.alias(own=other)
    out, starts = box.run()
    assert starts == ["py probe", "py run"] and not box.memo.exists()


def test_interpreter_that_cannot_read_the_script_is_not_used(box):
    box.interpreter(rc=3)
    out, starts = box.run()
    assert starts == ["py probe", "own probe", "py run"]
    assert (out["exe"], out["direct"]) == ("alias", "") and not box.memo.exists()


def test_other_version_behind_the_alias_is_not_used(box):
    box.alias(version="3.10" if VERSION != "3.10" else "3.11")
    out, starts = box.run()
    assert starts == ["py probe", "own probe", "py run"]
    assert (out["exe"], out["direct"]) == ("alias", "") and not box.memo.exists()


def test_interpreter_inside_the_alias_folder_is_left_alone(box):
    # Microsoft Store Python: sys.executable is itself under WindowsApps.
    inner = box.apps / "PythonSoftwareFoundation.Python.3" / "python.exe"
    inner.parent.mkdir()
    box.write(inner, OWN)
    box.alias(own=inner)
    out, starts = box.run()
    assert starts == ["py probe", "py run"] and out["direct"] == "" and not box.memo.exists()


def test_regular_install_is_left_alone(box):
    regular = box.root / "Python312"
    regular.mkdir()
    box.write(regular / "python", ALIAS)
    out, starts = box.run(path=str(regular))
    assert starts == ["python probe", "python run"] and out["direct"] == "" and not box.memo.exists()


@pytest.mark.parametrize("ostype", ["linux-gnu", "darwin23", ""])
def test_other_systems_are_left_alone(box, ostype):
    box.run()
    out, starts = box.run(ostype=ostype)
    assert starts == ["py probe", "py run"] and out["direct"] == ""


def test_missing_state_folder_is_not_created(box):
    gone = box.root / "nowhere"
    out, starts = box.run(SECURITY_WARNINGS_STATE_DIR=str(gone))
    assert starts == ["py probe", "own probe", "own run"] and out["exe"] == "own"
    assert not gone.exists()


def test_versioned_alias_is_remembered_too(box):
    (box.apps / "py").unlink()
    box.alias("python3.12", version="3.12")
    box.write(box.own, ALIAS.replace("SG_NAME=alias", "SG_NAME=own").replace("${{0##*/}}", "own"),
              version="3.12")
    out, starts = box.run()
    assert starts == ["python3.12 probe", "own probe", "own run"] and out["direct"] == "2"
    assert box.run()[1] == ["own run"]


def test_newer_python_answering_with_two_lines_is_still_chosen(box):
    # Pass 2b reads the probe without `ask`.
    (box.apps / "py").unlink()
    box.alias("python3.14", version="3.14")
    out, starts = box.run()
    assert starts == ["python3.14 probe", "python3.14 run"] and out["exe"] == "alias"


@pytest.mark.parametrize("value,expected", [("1", 1), ("2", 2), ("", None), ("3", None), ("yes", None)])
def test_stop_hook_reports_the_direct_route(hook_env, workspace, value, expected):
    _, repo = workspace
    rc, out, err = run_hook(stop_payload(repo), {**hook_env, "SG_LAUNCHER_DIRECT": value})
    m = metrics_of(out)
    assert m is not None, err
    assert m.get("launcher_direct") == expected


def test_direct_route_key_is_the_last_one(hook_env, workspace):
    """Claude Code keeps the first 20 keys, so this one never displaces another."""
    _, repo = workspace
    rc, out, err = run_hook(stop_payload(repo), {**hook_env, "SG_LAUNCHER_DIRECT": "1"})
    assert list(metrics_of(out))[-1] == "launcher_direct"


def test_value_is_read_once(monkeypatch):
    import _base
    monkeypatch.setenv("SG_LAUNCHER_DIRECT", "1")
    assert _base.launcher_direct_metric() == {"launcher_direct": 1}
    assert "SG_LAUNCHER_DIRECT" not in os.environ and _base.launcher_direct_metric() == {}
