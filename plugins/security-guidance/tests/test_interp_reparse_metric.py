"""`interp_reparse` counts sessions whose interpreter is reached through a
symbolic link or junction on Windows.

Measurement only, for anthropics/claude-code#96870: inside the packaged
Claude Desktop app Windows leaks kernel memory on every file opened through
such a link under AppData, and each hook starts an interpreter.

The interpreter paths and the Windows file attributes are passed in, so
these run everywhere.
"""
import json
import os
import subprocess
import sys
import types

import pytest

import _base
from conftest import HOOKS_DIR

REPARSE = 0x400
SYMLINK, JUNCTION, APP_ALIAS = 0xA000000C, 0xA0000003, 0x8000001B
ROAMING = os.path.join(os.sep, "Users", "u", "AppData", "Roaming")
LOCAL = os.path.join(os.sep, "Users", "u", "AppData", "Local")
ENV = {"APPDATA": ROAMING, "LOCALAPPDATA": LOCAL}
REGULAR = os.path.join(os.sep, "Program Files", "Python312")


def _key(path):
    return os.path.normcase(os.path.abspath(path))


def measure(executable, base_prefix, links=None, missing=(), targets=None, calls=None, old_python=False,
            broken=(), environ=ENV):
    links = {_key(k): v for k, v in (links or {}).items()}
    targets = {_key(k): v for k, v in (targets or {}).items()}
    missing = {_key(k) for k in missing}
    broken = {_key(k) for k in broken}

    def lstat(path):
        if calls is not None:
            calls.append(path)
        if _key(path) in missing:
            raise FileNotFoundError(path)
        if _key(path) in broken:
            raise ValueError(path)
        tag = links.get(_key(path))
        st = types.SimpleNamespace(st_file_attributes=REPARSE if tag else 0)
        if not old_python:
            st.st_reparse_tag = tag or 0
        return st

    def readlink(path):
        if _key(path) not in targets:
            raise OSError("not readable")
        return targets[_key(path)]

    return _base.interp_reparse_metric(executable=executable, base_prefix=base_prefix, environ=environ,
                                       platform="win32", lstat=lstat, readlink=readlink)["interp_reparse"]


def exe(folder):
    return os.path.join(folder, "python.exe")


def test_regular_install_is_zero_not_absent():
    assert measure(exe(REGULAR), REGULAR) == 0


@pytest.mark.parametrize("tag", [JUNCTION, SYMLINK])
def test_link_under_appdata(tag):
    # uv keeps a minor-version junction beside the real folder.
    link = os.path.join(ROAMING, "uv", "python", "cpython-3.12-windows-x86_64-none")
    targets = {link: "\\\\?\\C:\\Users\\u\\AppData\\Roaming\\uv\\python\\cpython-3.12.7"}
    assert measure(exe(link), link, {link: tag}, targets=targets) == 7


def test_link_under_local_appdata_counts_too():
    link = os.path.join(LOCAL, "Programs", "py")
    assert measure(exe(link), link, {link: SYMLINK}) == 7


def test_link_elsewhere_has_no_appdata_bit():
    link = os.path.join(os.sep, "tools", "python")
    assert measure(exe(link), link, {link: SYMLINK}) == 3


def test_only_the_standard_library_behind_a_link():
    # A virtual environment's python.exe is a regular file; its base install is linked.
    link = os.path.join(ROAMING, "uv", "python", "cpython-3.12")
    venv = os.path.join(os.sep, "proj", ".venv", "Scripts", "python.exe")
    assert measure(venv, link, {link: SYMLINK}) == 6


def test_only_the_executable_behind_a_link():
    link = os.path.join(os.sep, "tools", "python.exe")
    assert measure(link, REGULAR, {link: SYMLINK}) == 1


@pytest.mark.parametrize("link", [ROAMING, os.path.join(os.sep, "Users", "u")])
def test_appdata_itself_or_the_profile_moved_by_a_link(link):
    prefix = os.path.join(ROAMING, "uv", "python", "cpython-3.12.7")
    assert measure(exe(prefix), prefix, {link: SYMLINK}) == 7


def test_folder_that_only_starts_like_appdata():
    link = ROAMING + "Other"
    assert measure(exe(link), link, {link: SYMLINK}) == 3


def test_app_execution_alias_is_not_a_link():
    alias = os.path.join(LOCAL, "Microsoft", "WindowsApps", "python.exe")
    assert measure(alias, REGULAR, {alias: APP_ALIAS}) == 0


def test_mounted_volume_is_not_a_link():
    mount = os.path.join(os.sep, "tools")
    prefix = os.path.join(mount, "Python312")
    targets = {mount: "\\\\?\\Volume{4c1b02c1-d990-11dc-99ae-806e6f6e6963}\\"}
    assert measure(exe(prefix), prefix, {mount: JUNCTION}, targets=targets) == 0
    # A junction whose target cannot be read still counts.
    assert measure(exe(prefix), prefix, {mount: JUNCTION}) == 3


def test_junction_to_a_folder_named_by_volume_is_a_link():
    link = os.path.join(os.sep, "tools", "py")
    targets = {link: "\\\\?\\Volume{4c1b02c1-d990-11dc-99ae-806e6f6e6963}\\Users\\u\\py"}
    assert measure(exe(link), link, {link: JUNCTION}, targets=targets) == 3


def test_python_without_reparse_tags_says_it_cannot_tell():
    link = os.path.join(ROAMING, "uv", "python", "cpython-3.7")
    assert measure(exe(link), link, {link: JUNCTION}, old_python=True) == 8
    assert measure(exe(REGULAR), REGULAR, old_python=True) == 0


def test_unreadable_folder_is_skipped():
    link = os.path.join(ROAMING, "uv", "python", "cpython-3.12")
    assert measure(exe(link), link, {link: SYMLINK}, missing=(exe(link),)) == 7


def test_each_folder_is_looked_at_once_and_only_up_to_the_link():
    prefix = os.path.join(os.sep, "a", "b", "c")
    calls = []
    measure(exe(prefix), prefix, calls=calls)
    assert sorted(calls) == sorted({exe(prefix), prefix, os.path.dirname(prefix), os.path.join(os.sep, "a")})
    calls.clear()
    measure(exe(prefix), prefix, {prefix: SYMLINK}, calls=calls)
    assert calls == [exe(prefix), prefix]


def test_failure_on_one_path_keeps_the_other():
    link = os.path.join(ROAMING, "uv", "python", "cpython-3.12")
    venv = os.path.join(os.sep, "proj", ".venv", "Scripts", "python.exe")
    # The executable's folder cannot be read; the standard library's link is still found.
    assert measure(venv, link, {link: SYMLINK}, broken=(os.path.dirname(venv),)) == 2 | 4 | 8
    assert measure(exe(REGULAR), REGULAR, broken=(REGULAR,)) == 8
    assert measure(exe(link), link, {link: SYMLINK}, environ={"APPDATA": 7}) == 3


def test_real_system_calls_are_usable():
    # The defaults (sys.executable, os.lstat, os.readlink) on whatever runs the tests.
    found = _base.interp_reparse_metric(platform="win32")
    assert set(found) == {"interp_reparse"} and 0 <= found["interp_reparse"] < 16
    if sys.platform != "win32":
        assert found == {"interp_reparse": 0}


def test_other_systems_do_not_look():
    def lstat(path):
        raise AssertionError("looked")
    assert _base.interp_reparse_metric(platform="linux", lstat=lstat) == {}
    if sys.platform != "win32":
        assert _base.interp_reparse_metric(lstat=lstat) == {}


# SessionStart runs ensure_agent_sdk.py; the wrapper makes the SDK look
# installed (nothing is built) and stands in for the measurement.
_SESSION_START = """
import importlib.util, os, runpy, sys
script, value = sys.argv[1], sys.argv[2]
sys.path.insert(0, os.path.dirname(script))
real = importlib.util.find_spec
importlib.util.find_spec = lambda name, *a, **k: object() if name == "claude_agent_sdk" else real(name, *a, **k)
import _base
_base.interp_reparse_metric = lambda: {} if value == "None" else {"interp_reparse": int(value)}
sys.argv = [script]
runpy.run_path(script, run_name="__main__")
"""


@pytest.mark.parametrize("value", [7, None])
def test_session_start_row_carries_it_last(tmp_path, value):
    state = tmp_path / "state"
    state.mkdir()
    env = dict(os.environ, SECURITY_WARNINGS_STATE_DIR=str(state), HOME=str(tmp_path), CLAUDECODE="1",
               PYTHONDONTWRITEBYTECODE="1", SG_LAUNCHER_PROBE_MS="4350", SG_LAUNCHER_PROBE_MAX_MS="4200")
    r = subprocess.run([sys.executable, "-c", _SESSION_START, str(HOOKS_DIR / "ensure_agent_sdk.py"), str(value)],
                       input="{}", capture_output=True, text=True, env=env, timeout=60)
    assert r.returncode == 0, r.stderr
    keys = list(json.loads(r.stdout.splitlines()[-1])["metrics"])
    if value:
        assert keys[-3:] == ["launcher_probe_ms", "launcher_probe_max_ms", "interp_reparse"]
    else:
        assert "interp_reparse" not in keys
    # The healthy row fits the 10 keys older Claude Code versions kept (20 now).
    assert len(keys) <= 10
