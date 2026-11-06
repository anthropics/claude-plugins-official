"""NotebookEdit cell sources go through the same pattern checks as file edits."""
import json
import subprocess
import sys

import pytest

import extensibility
import security_reminder_hook as hook

from conftest import HOOKS_DIR, metrics_of, run_hook

CELL = (
    "import pickle, os\n"
    "data = pickle.loads(open('model.pkl', 'rb').read())\n"
    "os.system(f'convert {user_input}')\n"
)
CELL_RULES = ["os_system_injection", "pickle_deserialization"]


@pytest.fixture
def env(hook_env, tmp_path):
    # Keep the developer's own security-patterns files out of the counts.
    home = tmp_path / "home"
    home.mkdir()
    hook_env.update(HOME=str(home), USERPROFILE=str(home))
    hook_env.pop("CLAUDE_CONFIG_DIR", None)
    return hook_env


def notebook_payload(cwd, notebook, new_source=CELL, tool_response=None, **tool_input):
    return {
        "session_id": "s1",
        "hook_event_name": "PostToolUse",
        "tool_name": "NotebookEdit",
        "tool_input": {"notebook_path": str(notebook), "new_source": new_source, **tool_input},
        "tool_response": tool_response if tool_response is not None else {},
        "cwd": str(cwd),
    }


def warning_of(stdout):
    for line in stdout.splitlines():
        if line.strip().startswith("{"):
            out = json.loads(line).get("hookSpecificOutput")
            if out:
                return out["additionalContext"]
    return ""


@pytest.mark.parametrize("tool_input", [
    {"cell_id": "c1"},
    {"cell_id": "c1", "edit_mode": "replace", "cell_type": "code"},
    {"cell_id": "c1", "edit_mode": "insert", "cell_type": "code"},
    {"edit_mode": "insert", "cell_type": "code"},
    {"cell_id": "c1", "cell_type": "markdown"},
])
def test_cell_source_is_checked(tmp_path, env, tool_input):
    rc, out, _ = run_hook(
        notebook_payload(tmp_path, tmp_path / "analysis.ipynb", **tool_input), env)
    assert rc == 0
    warning = warning_of(out)
    assert "pickle" in warning
    assert "os.system" in warning
    assert metrics_of(out)["pattern_hits"] == 2


def test_same_cell_matches_a_python_file_edit(tmp_path, env):
    _, nb_out, _ = run_hook(
        notebook_payload(tmp_path, tmp_path / "analysis.ipynb", cell_id="c1"), env)
    py = notebook_payload(tmp_path, tmp_path / "analysis.py")
    py.update(tool_name="Edit", tool_input={
        "file_path": str(tmp_path / "analysis.py"), "old_string": "", "new_string": CELL})
    _, py_out, _ = run_hook(py, env)
    assert metrics_of(nb_out)["rule_mask"] == metrics_of(py_out)["rule_mask"]


@pytest.mark.parametrize("tool_input, tool_response", [
    ({"cell_id": "c1", "edit_mode": "delete"}, {}),
    ({"cell_id": "c1", "edit_mode": "delete", "cell_type": "code"}, {"error": ""}),
    ({"cell_id": "c1"}, {"error": "File has been modified since read"}),
    ({"cell_id": "c1"}, {"new_source": CELL, "error": "Edit rejected"}),
])
def test_deleted_cell_and_failed_edit_are_not_checked(tmp_path, env, tool_input, tool_response):
    rc, out, _ = run_hook(
        notebook_payload(tmp_path, tmp_path / "analysis.ipynb",
                         tool_response=tool_response, **tool_input), env)
    assert rc == 0
    assert metrics_of(out) is None
    assert warning_of(out) == ""


def test_successful_edit_with_an_empty_error_is_checked(tmp_path, env):
    # What Claude Code sends for an edit that worked.
    _, out, _ = run_hook(
        notebook_payload(tmp_path, tmp_path / "analysis.ipynb", cell_id="c1",
                         tool_response={"error": "", "cell_type": "code", "old_source": CELL}),
        env)
    assert metrics_of(out)["pattern_hits"] == 2


@pytest.mark.parametrize("tool_input, tool_response", [
    ({"cell_id": "c1", "new_source": None}, {}),
    ({"cell_id": "c1", "new_source": ["import pickle"]}, {}),
    ({"cell_id": None}, {}),
    ({"cell_id": "c1"}, "Updated cell c1"),
    ({"cell_id": "c1"}, None),
])
def test_unexpected_shapes_do_not_break_the_hook(tmp_path, env, tool_input, tool_response):
    payload = notebook_payload(tmp_path, tmp_path / "analysis.ipynb", **tool_input)
    payload["tool_response"] = tool_response
    rc, _, err = run_hook(payload, env)
    assert rc == 0
    assert "Traceback" not in err


def test_clean_cell_is_quiet(tmp_path, env):
    rc, out, _ = run_hook(
        notebook_payload(tmp_path, tmp_path / "analysis.ipynb",
                         new_source="import json\ndata = json.load(open('m.json'))\n",
                         cell_id="c1"), env)
    assert rc == 0
    assert metrics_of(out) is None


def saved_notebook(code, bom=""):
    # NotebookEdit saves a cell's source as one string; Jupyter saves a list of lines.
    return bom + json.dumps({
        "cells": [
            {"cell_type": "markdown", "id": "m", "metadata": {}, "source": "# Notes\n"},
            {"cell_type": "code", "id": "c", "metadata": {}, "source": code, "outputs": []},
        ],
        "metadata": {}, "nbformat": 4, "nbformat_minor": 5,
    }, indent=1)


@pytest.fixture
def rules(monkeypatch):
    monkeypatch.setattr(extensibility, "_user_patterns", [])
    return lambda path, content: sorted(r for r, _ in hook.check_patterns(str(path), content))


@pytest.mark.parametrize("bom", ["", "﻿"])
def test_saved_notebook_is_checked_by_its_cells_as_written(rules, bom):
    saved = saved_notebook(CELL, bom)
    assert "\\nos.system(" in saved
    assert rules("analysis.ipynb", saved) == CELL_RULES
    assert rules("analysis.ipynb", saved_notebook(CELL.splitlines(True), bom)) == CELL_RULES
    assert rules("analysis.ipynb", saved_notebook("x = 1\n", bom)) == []


def test_saved_notebook_outputs_are_not_checked(rules):
    saved = json.loads(saved_notebook("x = 1\n"))
    saved["cells"][1]["outputs"] = [{"output_type": "stream", "name": "stdout", "text": [CELL]}]
    assert rules("analysis.ipynb", json.dumps(saved)) == []
    saved["cells"][0]["source"] = CELL.splitlines(True)
    assert rules("analysis.ipynb", json.dumps(saved)) == CELL_RULES


@pytest.mark.parametrize("content", [
    "{not json", "{}", '{"cells": 5}', '{"cells": [5]}', '{"cells": [{"source": 5}]}', "[]",
])
def test_content_that_is_not_a_saved_notebook_is_checked_as_is(rules, content):
    assert rules("analysis.ipynb", content) == []
    assert rules("analysis.ipynb", content + "\nimport os\nos.system(cmd)\n") == ["os_system_injection"]


def test_other_files_are_not_read_as_notebooks(rules):
    assert rules("analysis.py", saved_notebook("import os\nos.system(cmd)\n")) == []


SWEEP = (
    "import sys, json; sys.path.insert(0, sys.argv[1]);"
    "import security_reminder_hook as h;"
    "print(json.dumps(h.sweep_pending_warnings('s1')[:2]))"
)


def sweep(env):
    r = subprocess.run([sys.executable, "-c", SWEEP, str(HOOKS_DIR)],
                       capture_output=True, text=True, env=env)
    return json.loads(r.stdout.strip().splitlines()[-1])


def test_notebook_warning_is_tallied_from_the_saved_cells(tmp_path, env):
    nb = tmp_path / "analysis.ipynb"
    nb.write_text(saved_notebook(CELL))
    run_hook(notebook_payload(tmp_path, nb, cell_id="c"), env)
    assert sweep(env) == [0, 2]

    run_hook(notebook_payload(tmp_path, nb, cell_id="c"), env)
    nb.write_text(saved_notebook("x = 1\n"))
    assert sweep(env) == [2, 0]
