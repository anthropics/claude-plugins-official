"""Custom rule globs can be relative to the project, and `**/` can match no folder."""
import json
import sys

import pytest

import extensibility
from conftest import git, make_repo

import security_reminder_hook as hook

CASES = [
    # glob, file inside the project, applies
    ("src/*.ts", "src/a.ts", True),
    ("src/**", "src/lib/a.ts", True),
    ("src/**/*.ts", "src/a.ts", True),
    ("src/**/*.ts", "src/lib/a.ts", True),
    ("**/src/**/*.ts", "src/a.ts", True),
    ("./src/**", "src/a.ts", True),
    ("/src/**", "src/a.ts", True),
    ("*.py", "x/y.py", True),
    ("src/**", "lib/a.ts", False),
    ("src/*.ts", "other/src.ts", False),
    ("**/vendor/**", "src/a.ts", False),
]


@pytest.fixture(autouse=True)
def _module_state(monkeypatch):
    monkeypatch.setattr(extensibility, "_user_patterns", [])
    monkeypatch.setattr(extensibility, "_match_roots", ())
    monkeypatch.setattr(extensibility, "_rels_cache", {})


def _commit(project):
    git(project, "add", "-A")
    git(project, "commit", "-q", "-m", "rules")


def _rule(tmp_path, monkeypatch, include=None, exclude=None):
    project = make_repo(tmp_path / "p", {"README": "x\n"})
    (project / ".claude").mkdir()
    entry = {"rule_name": "r", "substrings": ["NEEDLE("], "reminder": "x"}
    if include:
        entry["paths"] = include
    if exclude:
        entry["exclude_paths"] = exclude
    (project / ".claude" / "security-patterns.json").write_text(json.dumps({"patterns": [entry]}))
    _commit(project)
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(project))
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("USERPROFILE", str(tmp_path / "home"))
    monkeypatch.delenv("CLAUDE_CONFIG_DIR", raising=False)
    return project


def _hits(project, rel, cwd=None):
    extensibility.load_for_session(str(cwd or project))
    return [r for r, _ in hook.check_patterns(str(project / rel), "NEEDLE(1)\n")]


@pytest.mark.parametrize("glob,rel,applies", CASES)
def test_paths_inside_the_project(glob, rel, applies, tmp_path, monkeypatch):
    project = _rule(tmp_path, monkeypatch, include=[glob])
    assert bool(_hits(project, rel)) is applies


@pytest.mark.parametrize("glob,rel,applies", CASES)
def test_excludes_read_the_same_way(glob, rel, applies, tmp_path, monkeypatch):
    project = _rule(tmp_path, monkeypatch, exclude=[glob])
    assert bool(_hits(project, rel)) is not applies


def test_a_glob_that_matched_before_still_matches(tmp_path, monkeypatch):
    project = _rule(tmp_path, monkeypatch, include=["**/src/**"])
    assert _hits(project, "src/lib/a.ts")


def test_an_absolute_glob(tmp_path, monkeypatch):
    project = _rule(tmp_path, monkeypatch)
    rules = project / ".claude" / "security-patterns.json"
    entry = json.loads(rules.read_text())
    entry["patterns"][0]["paths"] = [project.as_posix() + "/src/**"]
    rules.write_text(json.dumps(entry))
    _commit(project)
    assert _hits(project, "src/a.ts")
    assert not _hits(project, "lib/a.ts")


def test_the_session_moved_to_a_subfolder(tmp_path, monkeypatch):
    project = _rule(tmp_path, monkeypatch, include=["src/**"])
    (project / "src").mkdir()
    assert _hits(project, "src/a.ts", cwd=project / "src")


def test_a_file_outside_the_project(tmp_path, monkeypatch):
    project = _rule(tmp_path, monkeypatch, include=["src/**"])
    outside = tmp_path / "elsewhere"
    outside.mkdir()
    extensibility.load_for_session(str(project))
    assert not [r for r, _ in hook.check_patterns(str(outside / "a.ts"), "NEEDLE(1)\n")]


def test_each_load_starts_from_its_own_folders(tmp_path, monkeypatch):
    project = _rule(tmp_path, monkeypatch, include=["src/**"])
    extensibility.load_for_session(str(project))
    assert extensibility._rule_covers(str(project / "src/a.ts").lstrip("/"), ("src/**",), ())
    monkeypatch.delenv("CLAUDE_PROJECT_DIR")
    extensibility.load_for_session(str(tmp_path))
    assert not extensibility._rule_covers(str(project / "src/a.ts").lstrip("/"), ("src/**",), ())


def test_the_folder_the_session_is_in_does_not_decide(tmp_path, monkeypatch):
    project = _rule(tmp_path, monkeypatch, include=["lib/**"])
    (project / "src").mkdir()
    assert not _hits(project, "src/lib/a.ts")
    assert not _hits(project, "src/lib/a.ts", cwd=project / "src")


def test_a_glob_with_no_folder_is_about_the_file_name(tmp_path, monkeypatch):
    project = _rule(tmp_path, monkeypatch, exclude=["test*"])
    assert _hits(project, "tests/x/a.py")
    assert not _hits(project, "x/test_a.py")


def test_a_subfolder_of_a_linked_worktree(tmp_path, monkeypatch):
    project = _rule(tmp_path, monkeypatch, include=["src/**"])
    tree = tmp_path / "tree"
    git(project, "worktree", "add", "-q", "-b", "side", str(tree))
    (tree / "pkg").mkdir()
    assert _hits(tree, "src/a.ts", cwd=tree / "pkg")


@pytest.mark.skipif(sys.platform == "win32", reason="needs symlink privilege")
def test_a_linked_folder_by_the_name_in_the_project(tmp_path, monkeypatch):
    project = _rule(tmp_path, monkeypatch, exclude=["vendor/**"])
    other = tmp_path / "other"
    other.mkdir()
    (project / "vendor").symlink_to(other, target_is_directory=True)
    assert not _hits(project, "vendor/a.ts")
