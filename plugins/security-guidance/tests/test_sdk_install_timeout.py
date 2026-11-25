"""A `pip install` that is killed leaves nothing in the system temp dir.

pip keeps each wheel it downloads in a `pip-unpack-*` folder under the temp
dir and removes it only on a normal exit. The bootstrap kills pip at its
timeout, so on a slow connection every attempt left a download behind, and
attempts repeat while the SDK is missing. See #6979.
"""
import os
import subprocess
import sys
import time

import pytest

import ensure_agent_sdk as boot
from test_sdk_bootstrap_switches import SWITCHES

pytestmark = pytest.mark.skipif(sys.version_info < (3, 10),
                                reason="bootstrap stops before the install")

# Stands in for pip: downloads "a wheel" the way pip does, says where, then
# either hangs (a slow connection) or exits without cleaning up.
_STAND_IN_PIP = """
import sys, tempfile, time
d = tempfile.mkdtemp(prefix="pip-unpack-")
open(d + "/claude_agent_sdk-0.0.0-py3-none-any.whl", "wb").write(b"x" * 4096)
open(sys.argv[2], "a").write(d + "\\n")
if sys.argv[1] == "hang":
    time.sleep(120)
"""


class Install:
    """Empty state dir, no SDK anywhere. `python -m venv` is skipped and
    `pip install` is the stand-in above: in "hang" mode it is killed once it
    has downloaded, as subprocess.run does at the timeout."""

    def __init__(self, tmp_path):
        self.state = tmp_path / "state"
        self.systmp = tmp_path / "systmp"
        self.systmp.mkdir()
        self.mode = "hang"
        self.calls = []
        self._script = tmp_path / "stand_in_pip.py"
        self._script.write_text(_STAND_IN_PIP)
        self._log = tmp_path / "downloads.txt"
        self._real_run = subprocess.run

    def downloads(self):
        """The folders the stand-in downloaded into, one per install."""
        return self._log.read_text().split("\n")[:-1] if self._log.exists() else []

    def run(self, cmd, **kwargs):
        cmd = [str(c) for c in cmd]
        if cmd[1:3] == ["-m", "venv"]:
            return subprocess.CompletedProcess(cmd, 0, b"", b"")
        if cmd[1:4] != ["-m", "pip", "install"]:
            return self._real_run(cmd, **kwargs)
        self.calls.append(cmd)
        stand_in = [sys.executable, str(self._script), self.mode, str(self._log)]
        if self.mode != "hang":
            return self._real_run(stand_in, **kwargs)
        before = len(self.downloads())
        proc = subprocess.Popen(stand_in, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                cwd=kwargs.get("cwd"), env=kwargs.get("env"))
        deadline = time.time() + 60
        while len(self.downloads()) == before and time.time() < deadline:
            time.sleep(0.02)
        proc.kill()
        proc.wait()
        raise subprocess.TimeoutExpired(cmd, kwargs["timeout"])


@pytest.fixture
def install(tmp_path, monkeypatch):
    for name in SWITCHES + ("PYTHONPATH",):
        monkeypatch.delenv(name, raising=False)
    inst = Install(tmp_path)
    monkeypatch.setenv("SECURITY_WARNINGS_STATE_DIR", str(inst.state))
    for name in ("TMPDIR", "TEMP", "TMP"):
        monkeypatch.setenv(name, str(inst.systmp))
    monkeypatch.setattr(boot, "_sdk_on_syspath", lambda: False)
    monkeypatch.setattr(boot, "_near_git_repo", lambda: True)
    monkeypatch.setattr(boot.subprocess, "run", inst.run)
    return inst


def _left_in(folder):
    return sorted(p.name for p in folder.iterdir()) if folder.is_dir() else []


def _downloaded_under(inst, folder):
    return [os.path.realpath(d).startswith(os.path.realpath(folder) + os.sep)
            for d in inst.downloads()]


def test_timed_out_install_leaves_no_download_behind(install):
    assert boot.main() == (boot.BUILD_FAILED, "pip", "subprocess_timeout")
    assert _downloaded_under(install, install.state / "pip-tmp") == [True]
    assert _left_in(install.systmp) == []
    assert _left_in(install.state / "pip-tmp") == []


def test_repeated_timeouts_do_not_add_up(install):
    for _ in range(3):
        boot._build_via_target(install.state)
    assert len(install.downloads()) == 3
    assert _left_in(install.systmp) == []
    assert _left_in(install.state / "pip-tmp") == []


def test_fallback_install_is_covered_too(install):
    assert boot._build_via_target(install.state) == (
        boot.BUILD_FAILED, "pip_target", "subprocess_timeout")
    assert "--target" in install.calls[0]
    assert _downloaded_under(install, install.state / "pip-tmp") == [True]
    assert _left_in(install.systmp) == []
    assert _left_in(install.state / "pip-tmp") == []


def test_finished_install_is_cleaned_up_as_well(install):
    install.mode = "exit"
    assert boot.main()[0] == boot.BUILT
    assert len(install.downloads()) == 1
    assert _left_in(install.systmp) == []
    assert _left_in(install.state / "pip-tmp") == []


def _leave_folder(install, name, age):
    folder = install.state / "pip-tmp" / name
    (folder / "pip-unpack-abc").mkdir(parents=True)
    (folder / "pip-unpack-abc" / "half.whl").write_bytes(b"x" * 4096)
    then = time.time() - age
    os.utime(folder, (then, then))


def test_folder_of_a_killed_bootstrap_is_removed_by_a_later_run(install):
    _leave_folder(install, "tmpkilled", boot._PIP_TEMP_STALE_SEC + 60)
    # An attempt that is still running keeps its folder.
    _leave_folder(install, "tmprunning", 30)
    boot._sweep_pip_temp(install.state)
    assert _left_in(install.state / "pip-tmp") == ["tmprunning"]


def test_sweep_runs_even_when_nothing_is_installed_this_time(install, monkeypatch):
    """Otherwise a folder left just before the SDK got installed stays for good."""
    _leave_folder(install, "tmpkilled", boot._PIP_TEMP_STALE_SEC + 60)
    monkeypatch.setattr(boot, "_target_sdk_importable", lambda state_dir: True)
    assert boot.main()[0] == boot.NOOP_TARGET
    assert install.calls == []
    assert _left_in(install.state / "pip-tmp") == []


@pytest.mark.parametrize("switch", ["SECURITY_GUIDANCE_DISABLE=1", "ENABLE_CODE_SECURITY_REVIEW=0"])
def test_sweep_runs_with_reviews_switched_off(install, monkeypatch, switch):
    _leave_folder(install, "tmpkilled", boot._PIP_TEMP_STALE_SEC + 60)
    monkeypatch.setenv(*switch.split("="))
    assert boot.main()[0] == boot.SKIP_REVIEWS_OFF
    assert _left_in(install.state / "pip-tmp") == []


def test_install_still_runs_when_the_folder_cannot_be_made(install):
    install.mode = "exit"
    install.state.mkdir()
    (install.state / "pip-tmp").write_text("in the way")
    assert boot._build_via_target(install.state)[0] == boot.BUILT_TARGET
    assert _downloaded_under(install, install.systmp) == [True]


def test_pip_timeout_starts_a_cooldown(install):
    assert boot.main()[0] == boot.BUILD_FAILED
    # The next attempts (every SessionStart, and every 5 minutes from the
    # tool hooks) do not download the SDK again.
    outcome = boot.main()
    assert outcome == (boot.SKIP_COOLDOWN, "", "")
    assert len(install.calls) == 1
    assert boot._install_context_metrics(outcome[0], install.state) == {"sdk_timeout_cooldown": 1}


def test_timeout_of_the_fallback_install_starts_it_too(install):
    boot._build_via_target(install.state)
    assert boot._timeout_cooldown_remaining(install.state) > 0


def test_timeout_cooldown_is_shorter_than_the_signal_kill_one(install):
    boot.main()
    assert boot._cooldown_remaining(install.state) == 0
    assert 0 < boot._timeout_cooldown_remaining(install.state) <= 3600
    then = time.time() - boot.PIP_TIMEOUT_COOLDOWN_SEC - 60
    os.utime(install.state / "agent-sdk-venv.timeout", (then, then))
    install.mode = "exit"
    assert boot.main()[0] == boot.BUILT
    assert len(install.calls) == 2


def test_slow_venv_creation_does_not_start_it(install, monkeypatch):
    def run(cmd, **kwargs):
        if [str(c) for c in cmd][1:3] == ["-m", "venv"]:
            raise subprocess.TimeoutExpired(cmd, kwargs["timeout"])
        return install.run(cmd, **kwargs)
    monkeypatch.setattr(boot.subprocess, "run", run)
    assert boot.main() == (boot.BUILD_FAILED, "venv", "subprocess_timeout")
    assert boot._timeout_cooldown_remaining(install.state) == 0


def test_signal_kill_cooldown_is_not_counted_as_a_timeout(install):
    boot._write_cooldown(install.state)
    boot._write_cooldown(install.state, boot._PIP_TIMEOUT_MARKER)
    outcome = boot.main()[0]
    assert outcome == boot.SKIP_COOLDOWN
    assert "sdk_timeout_cooldown" not in boot._install_context_metrics(outcome, install.state)


def test_count_belongs_to_the_run_that_skipped(install):
    boot.main()
    assert boot.main()[0] == boot.SKIP_COOLDOWN
    install.mode = "exit"
    (install.state / "agent-sdk-venv.timeout").unlink()
    outcome = boot.main()[0]
    assert outcome == boot.BUILT
    assert "sdk_timeout_cooldown" not in boot._install_context_metrics(outcome, install.state)


def test_marker_from_the_future_does_not_stretch_the_cooldown(install):
    boot._write_cooldown(install.state, boot._PIP_TIMEOUT_MARKER)
    ahead = time.time() + 6 * 3600
    os.utime(install.state / "agent-sdk-venv.timeout", (ahead, ahead))
    assert boot._timeout_cooldown_remaining(install.state) == boot.PIP_TIMEOUT_COOLDOWN_SEC


def _link(target, path):
    try:
        os.symlink(target, path, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("cannot create links here")


def test_sweep_needs_a_real_temp_folder(install, tmp_path):
    other = tmp_path / "other"
    (other / "old").mkdir(parents=True)
    then = time.time() - boot._PIP_TEMP_STALE_SEC - 60
    os.utime(other / "old", (then, then))
    install.state.mkdir(exist_ok=True)
    _link(other, install.state / "pip-tmp")
    boot._sweep_pip_temp(install.state)
    assert (other / "old").is_dir()
    assert not os.path.lexists(install.state / "pip-tmp")


@pytest.mark.skipif(os.name == "nt", reason="POSIX ownership")
def test_temp_folder_of_another_user_is_not_used(install, monkeypatch):
    root = install.state / "pip-tmp"
    root.mkdir(parents=True)
    (root / "tmpold").mkdir()
    then = time.time() - boot._PIP_TEMP_STALE_SEC - 60
    os.utime(root / "tmpold", (then, then))
    monkeypatch.setattr(boot.os, "getuid", lambda: os.stat(root).st_uid + 1)
    boot._sweep_pip_temp(install.state)
    assert _left_in(root) == ["tmpold"]
    install.mode = "exit"
    assert boot.main()[0] == boot.BUILT
    assert _left_in(root) == ["tmpold"]


@pytest.mark.skipif(os.name == "nt", reason="POSIX modes")
def test_temp_folder_is_private(install):
    install.mode = "exit"
    (install.state / "pip-tmp").mkdir(parents=True, mode=0o775)
    (install.state / "pip-tmp").chmod(0o775)
    assert boot.main()[0] == boot.BUILT
    assert (install.state / "pip-tmp").stat().st_mode & 0o077 == 0
