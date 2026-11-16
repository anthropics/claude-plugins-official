"""sg-python.sh starts Python once per hook on Windows.

The first hook finds the interpreter behind the name on PATH, with the links
in its path resolved, and remembers it for a day; later hooks start that file
and nothing else. Only where it is certain which file that is. See
anthropics/claude-code#96870 (opens through links under AppData) and
test_launcher_alias_own_path.py (packaged aliases, the entry itself).

Interpreters are shell wrappers here and the launcher's Windows branch is
switched on with OSTYPE; the tests at the end run on Windows itself.
"""
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest

from conftest import HOOKS_DIR

SHIM = HOOKS_DIR / "sg-python.sh"
BASH = shutil.which("bash") or "/bin/bash"
REAL = os.path.realpath(sys.executable)
VERSION = f"{sys.version_info[0]}.{sys.version_info[1]}"
WINDOWS = sys.platform == "win32"
posix_only = pytest.mark.skipif(WINDOWS, reason="POSIX shell wrappers")
windows_only = pytest.mark.skipif(not WINDOWS, reason="real Windows paths")


def bash_major(bash):
    try:
        r = subprocess.run([bash, "-c", "echo ${BASH_VERSINFO[0]}"], capture_output=True, text=True, timeout=30)
        return int(r.stdout.strip() or 0)
    except (OSError, ValueError, subprocess.SubprocessError):
        return 0


HOOK = (
    "import os, sys\n"
    "print('direct=' + os.environ.get('SG_LAUNCHER_DIRECT', ''))\n"
    "print('exe=' + (os.environ.get('SG_STANDIN') or sys.executable))\n"
    "print('stdin=' + sys.stdin.read())\n"
)

# An interpreter that says it is {says} (nothing for a virtual environment's),
# as Windows Python does: version, sys.executable, CRLF.
PYTHON = """#!{bash}
[ "${{0##*/}}" = "py" ] && [ "${{1:-}}" = "-3" ] && shift
if [ "${{1:-}}" = "-c" ]; then
  echo "probe $0" >> '{log}'
  [ {rc} -eq 0 ] || exit {rc}
  printf '{version}\\r\\n'; [ -z '{says}' ] || printf '{says}\\r\\n'; exit 0
fi
echo "run $0" >> '{log}'
SG_STANDIN="$0" exec '{real}' "$@"
"""


class Box:
    def __init__(self, root):
        self.root = root.resolve()
        self.state = self.root / "state"
        self.log = self.root / "log"
        self.hooks = self.root / "plugin" / "hooks"
        self.bin = self.root / "bin"
        self.uvbin = self.root / ".local" / "bin"  # where uv puts its starters
        for d in (self.state, self.hooks, self.bin, self.uvbin):
            d.mkdir(parents=True)
        self.script = self.hooks / "hook.py"
        self.script.write_text(HOOK)
        self.memo = self.state / "launcher-python"

    def python(self, path, says=None, version=VERSION, rc=0):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(PYTHON.format(bash=BASH, log=self.log, real=REAL, version=version, rc=rc,
                                      says=path if says is None else says))
        path.chmod(0o755)
        return path

    def install(self, folder="Python312", **kw):
        """A regular install: `python` and `python.exe` are one file, as Git
        Bash finds both names for it."""
        exe = self.python(self.root / folder / "python.exe", **kw)
        os.link(exe, exe.with_name("python"))
        return exe

    def starter(self, name, says, bin=None, **kw):
        exe = self.python((bin or self.uvbin) / f"{name}.exe", says=says, **kw)
        os.link(exe, exe.with_name(name))

    def uv(self, starter="python3.12", **kw):
        """uv's own Python: a starter on PATH that runs the interpreter through
        the minor version's link."""
        uv = self.root / "AppData" / "Roaming" / "uv" / "python"
        exe = uv / "cpython-3.12.5-windows-x86_64-none" / "python.exe"
        link = uv / "cpython-3.12-windows-x86_64-none"
        exe.parent.mkdir(parents=True)
        link.symlink_to(exe.parent)
        self.python(exe, says=link / "python.exe", version="3.12", **kw)
        self.starter(starter, link / "python.exe", version="3.12")
        return exe, link

    def launch(self, path, script=None, ostype="msys", cwd=None, **env):
        self.log.write_text("")
        env = {"PATH": os.pathsep.join(map(str, path)), "HOME": str(self.root), "OSTYPE": ostype,
               "APPDATA": str(self.root / "AppData" / "Roaming"),
               "SECURITY_WARNINGS_STATE_DIR": str(self.state), **env}
        return subprocess.run([BASH, str(SHIM), str(script or self.script)], input="payload",
                              capture_output=True, text=True, timeout=60, env=env, cwd=cwd or self.root)

    def run(self, *path, **kw):
        r = self.launch(path, **kw)
        assert r.returncode == 0 and r.stderr == "", r.stderr
        out = dict(line.split("=", 1) for line in r.stdout.splitlines())
        assert out["stdin"] == "payload"
        return out["direct"], self.starts()

    def starts(self):
        short = str(self.root) + "/"
        return [line.replace(short, "") for line in self.log.read_text().splitlines()]


@pytest.fixture
def box(tmp_path):
    if bash_major(BASH) < 5:
        pytest.skip("the remembered route needs bash 5")
    return Box(tmp_path)


@posix_only
def test_regular_install_is_checked_once_then_started_once_per_hook(box):
    exe = box.install()
    assert box.run(exe.parent) == ("4", ["probe Python312/python", "run Python312/python.exe"])
    for _ in range(3):
        assert box.run(exe.parent) == ("3", ["run Python312/python.exe"])


@posix_only
def test_uv_python_runs_without_its_link(box):
    exe, _ = box.uv()
    rel = str(exe.relative_to(box.root))
    # The resolved path has not been run yet, so it is checked as well.
    assert box.run(box.uvbin) == ("4", ["probe .local/bin/python3.12", f"probe {rel}", f"run {rel}"])
    for _ in range(3):
        assert box.run(box.uvbin) == ("3", [f"run {rel}"])


@posix_only
def test_linked_folder_on_path_is_resolved(box):
    exe, link = box.uv()
    os.link(exe, exe.with_name("python"))
    rel = str(exe.relative_to(box.root))
    via = str((link / "python").relative_to(box.root))
    assert box.run(link) == ("4", [f"probe {via}", f"probe {rel}", f"run {rel}"])
    assert box.run(link) == ("3", [f"run {rel}"])


@posix_only
def test_uv_folder_from_its_own_variable(box):
    exe, _ = box.uv()
    moved = box.root / "pythons"
    (box.root / "AppData" / "Roaming" / "uv" / "python").rename(moved)
    real = moved / exe.parent.name / "python.exe"
    box.python(real, version="3.12")
    for name in ("python3.12", "python3.12.exe"):
        (box.uvbin / name).unlink()
    box.starter("python3.12", real, version="3.12")
    assert box.run(box.uvbin) == ("", ["probe .local/bin/python3.12", "run .local/bin/python3.12"])
    rel = str(real.relative_to(box.root))
    env = {"UV_PYTHON_INSTALL_DIR": str(moved)}
    box.memo.unlink()
    assert box.run(box.uvbin, **env) == ("4", ["probe .local/bin/python3.12", f"probe {rel}", f"run {rel}"])


@posix_only
@pytest.mark.parametrize("root", ["", "relative/uv", "/"])
def test_uv_folder_that_says_nothing_matches_nothing(box, root):
    elsewhere = box.python(box.root / "tools" / "python.exe")
    box.python(box.bin / "python", says=elsewhere)
    env = {"UV_PYTHON_INSTALL_DIR": root, "APPDATA": ""}
    assert box.run(box.bin, **env) == ("", ["probe bin/python", "run bin/python"])


@posix_only
def test_shim_of_a_version_manager_is_asked_every_time(box):
    """It chooses by folder, so what it ran here says nothing about the next hook."""
    elsewhere = box.python(box.root / "versions" / "3.12" / "python.exe")
    box.python(box.bin / "python", says=elsewhere)
    for _ in range(2):
        assert box.run(box.bin) == ("", ["probe bin/python", "run bin/python"])
    # Remembered as "search", so the next hooks do not work it out again.
    assert box.memo.read_text().splitlines()[3:6:2] == ["", "search"]


@posix_only
def test_py_launcher_is_remembered(box):
    exe = box.install()
    box.python(box.bin / "py", says=exe)
    assert box.run(box.bin) == (
        "4", ["probe bin/py", "probe Python312/python.exe", "run Python312/python.exe"])
    assert box.run(box.bin) == ("3", ["run Python312/python.exe"])


@posix_only
def test_regular_install_behind_an_alias_that_is_no_python(box):
    """Pass 4: App Installer's `python` and `python3` come first on PATH."""
    apps = box.root / "Microsoft" / "WindowsApps"
    for name in ("python3", "python"):
        box.python(apps / name, rc=49)
    exe = box.install()
    (box.hooks / "fallback.py").write_text("import os; print(os.environ.get('SG_LAUNCHER_FALLBACK'))")
    tried = ["probe Microsoft/WindowsApps/python3", "probe Microsoft/WindowsApps/python"]
    assert box.run(apps, exe.parent) == ("4", tried + ["probe Python312/python", "run Python312/python.exe"])
    assert box.run(apps, exe.parent) == ("3", ["run Python312/python.exe"])
    # Still counted as found by the fallback.
    assert box.launch([apps, exe.parent], script=box.hooks / "fallback.py").stdout == "1\n"


@posix_only
def test_virtual_environment_on_path_is_left_alone(box):
    exe = box.install("venv/Scripts", says="")
    for _ in range(2):
        assert box.run(exe.parent) == ("", ["probe venv/Scripts/python", "run venv/Scripts/python"])
    assert not box.memo.exists()


@posix_only
def test_active_environment_neither_reads_nor_writes(box):
    exe = box.install()
    env = {"VIRTUAL_ENV": str(box.root / "venv")}
    plain = ("", ["probe Python312/python", "run Python312/python"])
    assert box.run(exe.parent, **env) == plain and not box.memo.exists()
    box.run(exe.parent)
    assert box.run(exe.parent, **env) == plain


@posix_only
def test_relative_path_entry_is_not_remembered(box):
    exe = box.install("here")
    r = box.run("here")
    assert r == ("", ["probe here/python", "run here/python"]) and exe.exists() and not box.memo.exists()


@posix_only
def test_another_path_searches_again(box):
    """A Python put first on PATH (an activated environment, direnv) is seen at once."""
    exe, first = box.install(), box.install("first")
    box.run(exe.parent)
    assert box.run(first.parent, exe.parent) == ("4", ["probe first/python", "run first/python.exe"])


@posix_only
def test_sessions_with_different_paths_keep_their_own_entry(box):
    dirs = [box.install(f"py{i}").parent for i in range(4)]
    for d in dirs:
        assert box.run(d)[0] == "4"
    for d in dirs + dirs[::-1]:
        assert box.run(d) == ("3", [f"run {d.name}/python.exe"])


@posix_only
def test_at_most_four_entries_newest_first(box):
    dirs = [box.install(f"py{i}").parent for i in range(6)]
    for d in dirs:
        box.run(d)
    lines = box.memo.read_text().splitlines()
    assert [lines[i] for i in range(3, len(lines), 7)] == [str(d / "python.exe") for d in dirs[:1:-1]]
    assert box.run(dirs[0])[0] == "4" and box.run(dirs[5])[0] == "3"


@posix_only
def test_old_entries_are_dropped(box):
    a, b = box.install("a").parent, box.install("b").parent
    box.run(a)
    lines = box.memo.read_text().splitlines()
    lines[1] = str(int(time.time()) - 90000)
    box.memo.write_text("\n".join(lines) + "\n")
    box.run(b)
    assert len(box.memo.read_text().splitlines()) == 7
    assert box.run(a)[0] == "4"


@posix_only
def test_removed_interpreter_is_searched_for(box):
    old, new = box.install("old"), box.install("new")
    path = (old.parent, new.parent)
    box.run(*path)
    shutil.rmtree(old.parent)
    old.parent.mkdir()
    assert box.run(*path) == ("4", ["probe new/python", "run new/python.exe"])
    assert box.run(*path) == ("3", ["run new/python.exe"])


@posix_only
def test_uv_upgrade_that_removes_the_old_release(box):
    exe, link = box.uv()
    box.run(box.uvbin)
    new = box.python(exe.parent.with_name("cpython-3.12.6-windows-x86_64-none") / "python.exe",
                     says=link / "python.exe", version="3.12")
    shutil.rmtree(exe.parent)
    link.unlink()
    link.symlink_to(new.parent)
    rel = str(new.relative_to(box.root))
    assert box.run(box.uvbin) == ("4", ["probe .local/bin/python3.12", f"probe {rel}", f"run {rel}"])


@posix_only
def test_entry_of_the_previous_format_is_replaced(box):
    exe = box.install()
    box.memo.write_text("\n".join(["sg-launcher-python 1", str(int(time.time())), str(exe.parent), str(exe),
                                   str(box.hooks), "end"]) + "\n")
    assert box.run(exe.parent)[0] == "4"
    assert box.memo.read_text().splitlines()[0] == "sg-launcher-python 2"


@posix_only
@pytest.mark.parametrize("code", [1, 2])
def test_failed_hook_is_searched_again_once(box, code):
    exe = box.install()
    box.run(exe.parent)
    failing = box.hooks / "fails.py"
    failing.write_text(f"import sys\nsys.stderr.write('findings')\nsys.exit({code})\n")
    r = box.launch([exe.parent], script=failing)
    assert (r.returncode, r.stderr, box.starts()) == (code, "findings", ["run Python312/python.exe"])
    assert box.run(exe.parent)[0] == "4" and box.run(exe.parent)[0] == "3"


@posix_only
def test_resolved_path_that_does_not_work_is_tried_once_a_day(box):
    exe, _ = box.uv(rc=3)
    rel = str(exe.relative_to(box.root))
    plain = ["probe .local/bin/python3.12", "run .local/bin/python3.12"]
    assert box.run(box.uvbin) == ("", [plain[0], f"probe {rel}", plain[1]])
    for _ in range(3):
        assert box.run(box.uvbin) == ("", plain)


@posix_only
def test_failed_hook_drops_its_own_entry_only(box):
    a, b = box.install("a").parent, box.install("b").parent
    box.run(a)
    box.run(b)
    failing = box.hooks / "fails.py"
    failing.write_text("import sys\nsys.exit(2)\n")
    assert box.launch([a], script=failing).returncode == 2
    assert box.run(b)[0] == "3" and box.run(a)[0] == "4"


@posix_only
def test_entry_written_while_the_hook_ran_survives_its_failure(box):
    a, b = box.install("a").parent, box.install("b").parent
    box.run(b)
    other = box.memo.read_text()
    box.memo.unlink()
    box.run(a)
    failing = box.hooks / "fails.py"
    failing.write_text(f"open({str(box.memo)!r}, 'a').write({other!r})\nraise SystemExit(1)\n")
    assert box.launch([a], script=failing).returncode == 1
    assert box.memo.read_text() == other and box.run(b)[0] == "3"


@posix_only
@pytest.mark.parametrize("rc,version", [(0, "3.8"), (1, VERSION)])
def test_earlier_name_that_was_started_and_not_used(box, rc, version):
    """It may be a shim that has a good Python in another folder."""
    shim = box.bin / "python3"
    box.python(shim, says="", version=version, rc=rc)
    exe = box.install()
    for _ in range(2):
        assert box.run(box.bin, exe.parent) == (
            "", ["probe bin/python3", "probe Python312/python", "run Python312/python"])
    assert not box.memo.exists()


@posix_only
def test_shim_that_chooses_among_uv_pythons_is_not_uvs_starter(box):
    exe, link = box.uv()
    rel = "shims/python3.12"
    box.starter("python3.12", link / "python.exe", bin=box.root / "shims", version="3.12")
    assert box.run(box.root / "shims") == ("", [f"probe {rel}", f"run {rel}"])
    # A script in uv's own folder is not its starter either.
    (box.uvbin / "python3.12.exe").unlink()
    assert box.run(box.uvbin)[0] == ""


@posix_only
@pytest.mark.parametrize("name", ["PY_PYTHON", "PY_PYTHON3"])
def test_py_launcher_told_which_python_to_use(box, name):
    exe = box.install()
    box.python(box.bin / "py", says=exe)
    box.run(box.bin)
    assert box.run(box.bin, **{name: "3.11"}) == ("", ["probe bin/py", "run bin/py"])


@posix_only
def test_conda_environment_is_left_alone(box):
    exe = box.install("envs/proj")
    (exe.parent / "conda-meta").mkdir()
    for _ in range(2):
        assert box.run(exe.parent) == ("", ["probe envs/proj/python", "run envs/proj/python"])


@posix_only
def test_linked_interpreter_file_is_resolved(box):
    exe = box.install()
    link = box.root / "links" / "python.exe"
    link.parent.mkdir()
    link.symlink_to(exe)
    (link.parent / "python").symlink_to(exe)
    box.python(exe, says=link)
    assert box.run(link.parent) == (
        "4", ["probe links/python", "probe Python312/python.exe", "run Python312/python.exe"])
    assert box.run(link.parent) == ("3", ["run Python312/python.exe"])


@posix_only
@pytest.mark.parametrize("break_state", [
    lambda b: shutil.rmtree(b.state),
    lambda b: b.memo.mkdir(),
    pytest.param(lambda b: (b.memo.write_text(""), b.memo.chmod(0o400)),
                 marks=pytest.mark.skipif(hasattr(os, "geteuid") and os.geteuid() == 0, reason="root")),
    pytest.param(lambda b: b.state.chmod(0o500),
                 marks=pytest.mark.skipif(hasattr(os, "geteuid") and os.geteuid() == 0, reason="root")),
])
def test_nothing_extra_where_nothing_can_be_kept(box, break_state):
    """Without a place for the entry every hook would be a first hook."""
    box.uv()
    break_state(box)
    try:
        for _ in range(2):
            assert box.run(box.uvbin) == ("", ["probe .local/bin/python3.12", "run .local/bin/python3.12"])
    finally:
        if box.state.exists():
            box.state.chmod(0o700)


@posix_only
@pytest.mark.parametrize("ostype", ["linux-gnu", "darwin23"])
def test_other_systems_are_left_alone(box, ostype):
    exe = box.install()
    box.run(exe.parent)
    assert box.run(exe.parent, ostype=ostype) == ("", ["probe Python312/python", "run Python312/python"])


@posix_only
def test_older_python_is_not_remembered(box):
    # Below 3.10 Windows Python prints no path (pass 3).
    exe = box.install(version="3.9", says="")
    for _ in range(2):
        assert box.run(exe.parent) == ("", ["probe Python312/python", "run Python312/python"])


def git_bash():
    git = shutil.which("git")
    for up in (1, 2, 3):
        if git and len(Path(git).parents) > up:
            bash = Path(git).parents[up] / "bin" / "bash.exe"
            if bash.is_file() and bash_major(str(bash)) >= 5:
                return str(bash)
    return None


@pytest.fixture
def win(tmp_path):
    bash = git_bash()
    if bash is None:
        pytest.skip("needs Git Bash 5")
    state = tmp_path / "state"
    state.mkdir()
    hook = tmp_path / "hook.py"
    hook.write_text("import os, sys\nsys.stdin.read()\n"
                    "print(os.environ.get('SG_LAUNCHER_DIRECT', '-'), sys.executable, sys.base_prefix, sep='|')\n")

    def run(folder, **extra):
        env = {k: v for k, v in os.environ.items() if k.upper() not in ("VIRTUAL_ENV", "PATH")}
        # Only Git's tools and the folder under test.
        usr = Path(bash).parents[1] / "usr" / "bin"
        env.update(PATH=f"{folder};{usr}", SECURITY_WARNINGS_STATE_DIR=str(state), **extra)
        r = subprocess.run([bash, "--noprofile", "--norc", str(SHIM), str(hook)], input="payload",
                           capture_output=True, text=True, timeout=120, env=env)
        assert r.returncode == 0, r.stderr
        direct, exe, base = r.stdout.strip().split("|")
        return direct, Path(exe), Path(base)

    run.root = tmp_path
    return run


def base_python():
    """The folder of the Python that made this environment, if any."""
    folder = Path(os.path.realpath(sys.base_prefix))
    return folder if (folder / "python.exe").is_file() else None


@windows_only
def test_windows_regular_install(win):
    folder = base_python()
    if folder is None:
        pytest.skip("no python.exe in the base install")
    first, again = win(folder), win(folder)
    assert (first[0], again[0]) == ("4", "3")
    assert os.path.samefile(first[1], folder / "python.exe") and again[1:] == first[1:]


@windows_only
def test_windows_junction_is_resolved(win):
    folder = base_python()
    if folder is None:
        pytest.skip("no python.exe in the base install")
    link = win.root / "linked"
    subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(folder)], check=True, capture_output=True)
    try:
        for expected in ("4", "3", "3"):
            direct, exe, base = win(link)
            assert direct == expected
            # Neither the interpreter nor its library is reached through the link.
            assert "linked" not in str(exe).lower() and "linked" not in str(base).lower()
            assert os.path.samefile(base, folder)
    finally:
        os.rmdir(link)


@windows_only
def test_windows_virtual_environment_is_left_alone(win):
    venv = win.root / "venv"
    subprocess.run([sys.executable, "-m", "venv", "--without-pip", str(venv)], check=True, timeout=300)
    for _ in range(2):
        direct, exe, _ = win(venv / "Scripts")
        assert direct == "-" and os.path.samefile(exe, venv / "Scripts" / "python.exe")
