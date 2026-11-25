"""sg-python.sh runs its `python -c` probes with PYTHONSAFEPATH=1.

The launcher asks a candidate interpreter for its version and, for a packaged
Windows alias, for its real path. Both questions need the standard library
only. The variable is set for those two calls alone, so the hook's environment
is unchanged.

Interpreters are emulated with shell scripts, so these tests need a POSIX
shell.
"""
import os
import shutil
import subprocess
import sys

import pytest

from conftest import HOOKS_DIR

pytestmark = pytest.mark.skipif(sys.platform == "win32", reason="POSIX shell wrappers")

SHIM = HOOKS_DIR / "sg-python.sh"
BASH = shutil.which("bash") or "/bin/bash"
REAL = os.path.realpath(sys.executable)

# Logs the variable at each start, then behaves like the real interpreter.
LOGGING = """#!{bash}
if [ "${{1:-}}" = "-c" ]; then kind=probe; else kind=hook; fi
echo "{name} $kind [${{PYTHONSAFEPATH-unset}}]" >> '{log}'
exec '{real}' "$@"
"""
# A packaged alias: cannot read the hook script, but says where its interpreter is.
ALIAS = """#!{bash}
echo "alias probe [${{PYTHONSAFEPATH-unset}}]" >> '{log}'
case "$2" in
  "import sys; print(sys.executable)") echo '{own}' ;;
  *) exit 3 ;;
esac
"""


@pytest.fixture
def box(tmp_path):
    (tmp_path / "bin").mkdir()
    (tmp_path / "hook.py").write_text("print('ran')\n")
    return tmp_path


def _write(path, template, box, **kw):
    path.write_text(template.format(bash=BASH, real=REAL, log=box / "log", **kw))
    path.chmod(0o755)


def _run(box, **env):
    r = subprocess.run([BASH, str(SHIM), str(box / "hook.py")], input="", capture_output=True,
                       text=True, timeout=60, env={"PATH": str(box / "bin"), "HOME": "/", **env})
    assert r.returncode == 0 and r.stdout.strip() == "ran", r.stderr
    return (box / "log").read_text().splitlines()


def test_version_probe_has_the_variable_and_the_hook_env_is_unchanged(box):
    _write(box / "bin" / "python3", LOGGING, box, name="python3")
    assert _run(box) == ["python3 probe [1]", "python3 hook [unset]"]


def test_alias_path_probe_has_the_variable(box):
    (box / "own").mkdir()
    _write(box / "own" / "python", LOGGING, box, name="own")
    _write(box / "bin" / "python3", ALIAS, box, own=box / "own" / "python")
    assert _run(box) == ["alias probe [1]", "alias probe [1]", "own probe [1]", "own hook [unset]"]


def test_a_value_from_outside_is_passed_on_unchanged(box):
    _write(box / "bin" / "python3", LOGGING, box, name="python3")
    assert _run(box, PYTHONSAFEPATH="0") == ["python3 probe [1]", "python3 hook [0]"]
