"""sg-python.sh finds Python releases newer than its versioned list.

The versioned names it prefers stop at python3.13. A machine whose `python3`
is below 3.10 (stock macOS: 3.9) and whose only newer interpreter is
python3.14 used to end up on 3.9, which cannot load the agent SDK, so the
commit reviewer was off without a word. See #4907, #5024.

Interpreters are emulated with shell scripts, so these tests need a POSIX
shell.
"""
import sys

import pytest

from test_launcher_process_count import PYTHON, _add, _run, _starts, box  # noqa: F401

pytestmark = pytest.mark.skipif(sys.platform == "win32", reason="POSIX shell wrappers")


def test_newer_release_beats_a_python3_below_3_10(box):
    _add(box, "python3", PYTHON, version="3.9")
    _add(box, "python3.14", PYTHON, version="3.14")
    r = _run(box, "hook.py")
    assert "ran:python3.14" in r.stdout, r.stdout + r.stderr
    assert _starts(box) == ["python3 probe", "python3.14 probe", "python3.14 hook.py"]


def test_newer_release_is_found_when_it_is_the_only_python(box):
    _add(box, "python3.15", PYTHON, version="3.15")
    r = _run(box, "hook.py")
    assert "ran:python3.15" in r.stdout, r.stdout + r.stderr
    assert _starts(box) == ["python3.15 probe", "python3.15 hook.py"]


@pytest.mark.parametrize("working", ["python3.12", "python3", "python"])
def test_an_interpreter_that_already_works_is_kept(box, working):
    _add(box, working, PYTHON, version="3.12")
    _add(box, "python3.14", PYTHON, version="3.14")
    r = _run(box, "hook.py")
    assert f"ran:{working}" in r.stdout, r.stdout + r.stderr
    assert "python3.14 probe" not in _starts(box)


def test_oldest_of_the_newer_releases_is_tried_first(box):
    _add(box, "python3.16", PYTHON, version="3.16")
    _add(box, "python3.14", PYTHON, version="3.14")
    r = _run(box, "hook.py")
    assert "ran:python3.14" in r.stdout, r.stdout + r.stderr


def test_no_python_at_all_still_starts_nothing(box):
    r = _run(box, "hook.py")
    assert r.returncode == 1
    assert "python3.14" in r.stderr
    assert _starts(box) == []
