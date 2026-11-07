"""Project rules and guidance keep loading after the session moves to another
folder of the project, and only then."""
import json
import os

import pytest

import extensibility
from conftest import edit_payload, git, make_repo, run_hook

GUIDANCE = extensibility.GUIDANCE_BASENAME


@pytest.fixture
def home(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    monkeypatch.delenv("CLAUDE_CONFIG_DIR", raising=False)
    monkeypatch.setattr(extensibility, "_guidance_block", "")
    monkeypatch.setattr(extensibility, "_user_patterns", [])
    return home


@pytest.fixture
def load(home, monkeypatch):
    def run(cwd, project=None):
        if project is None:
            monkeypatch.delenv("CLAUDE_PROJECT_DIR", raising=False)
        else:
            monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(project))
        extensibility.load_for_session(str(cwd) if cwd else cwd)
        return ([r["ruleName"][5:] for r in extensibility.user_patterns()],
                extensibility.guidance_block())
    return run


def _config(folder, name, local=False):
    config = folder / ".claude"
    config.mkdir(parents=True, exist_ok=True)
    suffix = ".local" if local else ""
    (config / f"security-patterns{suffix}.json").write_text(json.dumps({"patterns": [
        {"rule_name": name, "reminder": "x", "substrings": ["NEEDLE("]}]}))
    (config / f"claude-security-guidance{suffix}.md").write_text(f"text of {name}\n")


@pytest.fixture
def repo(tmp_path):
    r = make_repo(tmp_path / "repo", {"src/lib/a.py": "1\n"})
    _config(r, "project")
    return r


@pytest.mark.parametrize("sub", ["src", "src/lib"])
def test_after_cd(repo, load, sub):
    rules, guidance = load(repo / sub, repo)
    assert rules == ["project"] and "text of project" in guidance


def test_local_files_too(repo, load):
    _config(repo, "local", local=True)
    assert load(repo / "src", repo)[0] == ["project", "local"]


def test_in_the_project_folder_they_load_once(repo, load):
    rules, guidance = load(repo, repo)
    assert rules == ["project"] and guidance.count("text of project") == 1


def test_project_folder_spelled_another_way_loads_once(repo, load):
    assert load(repo, repo / "src" / "..")[0] == ["project"]


def test_folder_moved_to_still_counts_and_comes_after(repo, load):
    _config(repo / "src", "sub")
    rules, guidance = load(repo / "src", repo)
    assert rules == ["project", "sub"]
    assert guidance.index("text of project") < guidance.index("text of sub")


def test_a_subfolder_never_pushes_out_the_projects_own(repo, load, monkeypatch):
    _config(repo / "src", "sub")
    (repo / "src" / ".claude" / GUIDANCE).write_text("x" * 9000)
    monkeypatch.setattr(extensibility, "PATTERN_MAX_RULES", 1)
    rules, guidance = load(repo / "src", repo)
    assert rules == ["project"] and "text of project" in guidance


@pytest.mark.parametrize("project", [None, "", "relative/path"])
def test_without_a_usable_project_folder_as_before(repo, load, project):
    assert load(repo / "src", project) == ([], "")
    assert load(repo, project)[0] == ["project"]


def test_no_cwd_loads_no_project_file(repo, load):
    assert load(None, repo) == ([], "")


def test_another_repository_outside_the_project(repo, load, tmp_path):
    other = make_repo(tmp_path / "other")
    _config(other, "other")
    assert load(other, repo)[0] == ["other"]


def test_folder_outside_the_project_and_any_repository(repo, load, tmp_path):
    (tmp_path / "scratch").mkdir()
    assert load(tmp_path / "scratch", repo) == ([], "")


def test_project_spelled_in_another_case(repo, load, tmp_path):
    """macOS and Windows: the same folder, whatever case it is typed in."""
    other = tmp_path / "REPO"
    if not (other.exists() and os.path.samefile(other, repo)):
        pytest.skip("this file system tells case apart")
    assert load(other / "src", repo)[0] == ["project"]
    assert load(repo / "src", other)[0] == ["project"]


def test_name_that_only_starts_like_the_project(repo, load, tmp_path):
    (tmp_path / "repo-two").mkdir()
    assert load(tmp_path / "repo-two", repo) == ([], "")


def test_sibling_package_of_a_monorepo(tmp_path, load):
    r = make_repo(tmp_path / "mono", {"a/x.py": "1\n", "b/x.py": "1\n"})
    _config(r, "root")
    _config(r / "a", "a")
    # The project is `a`; the root's own files were never this session's.
    assert load(r / "b", r / "a")[0] == ["a"]


def test_project_that_is_no_repository(tmp_path, load):
    ws = tmp_path / "ws"
    _config(ws, "ws")
    repo = make_repo(ws / "app", {"src/x.py": "1\n"})
    assert load(repo / "src", ws)[0] == ["ws"]


def test_nested_repository_inside_the_project(repo, load):
    nested = make_repo(repo / "vendor" / "dep")
    assert load(nested, repo)[0] == ["project"]


class TestWorktree:
    @pytest.fixture
    def tree(self, repo):
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", "rules")
        tree = repo / ".claude" / "worktrees" / "t"
        git(repo, "worktree", "add", "-q", "-b", "side", str(tree))
        _config(tree, "branch")
        return tree

    def test_at_its_top_its_own_files_once(self, repo, tree, load):
        assert load(tree, repo)[0] == ["branch"]

    def test_after_cd_its_own_files_not_the_main_checkouts(self, repo, tree, load):
        assert load(tree / "src", repo)[0] == ["branch"]

    def test_outside_the_project_folder(self, repo, load, tmp_path):
        tree = tmp_path / "elsewhere"
        git(repo, "worktree", "add", "-q", "-b", "side", str(tree))
        _config(tree, "branch")
        assert load(tree / "src", repo)[0] == ["branch"]

    def test_project_below_the_top(self, tmp_path, load):
        r = make_repo(tmp_path / "mono", {"pkg/src/x.py": "1\n"})
        tree = tmp_path / "tree"
        git(r, "worktree", "add", "-q", "-b", "side", str(tree))
        _config(tree / "pkg", "branch")
        assert load(tree / "pkg" / "src", r / "pkg")[0] == ["branch"]

    def test_repositories_with_a_git_folder_elsewhere_are_not_worktrees(self, tmp_path, load):
        (tmp_path / "worktrees").mkdir()
        for name in ("a", "b"):
            (tmp_path / name / "src").mkdir(parents=True)
            git(tmp_path, "init", "-q", "--separate-git-dir",
                str(tmp_path / "worktrees" / f"{name}.git"), str(tmp_path / name))
            _config(tmp_path / name, name)
        assert load(tmp_path / "b" / "src", tmp_path / "a") == ([], "")

    def test_session_started_in_the_worktree(self, repo, tree, load):
        assert load(tree / "src", tree)[0] == ["branch"]


@pytest.mark.parametrize("content", [b"", b"gitdir:", b"nonsense\n", b"gitdir: /no/such\n", b"\xff\xfe"])
def test_odd_git_file_does_not_stop_loading(tmp_path, load, content):
    ws = tmp_path / "ws"
    _config(ws, "ws")
    (ws / "x").mkdir()
    (ws / "x" / ".git").write_bytes(content)
    assert load(ws / "x", ws)[0] == ["ws"]


def test_home_as_the_project_does_not_load_the_user_files_twice(home, load):
    _config(home, "user")
    (home / "work").mkdir()
    rules, guidance = load(home / "work", home)
    assert rules == ["user"] and guidance.count("text of user") == 1


def test_link_in_the_project_folder_is_still_skipped(tmp_path, load):
    r = make_repo(tmp_path / "repo", {"src/x.py": "1\n", "secret": "outside\n"})
    (r / ".claude").mkdir()
    try:
        os.symlink(r / "secret", r / ".claude" / GUIDANCE)
    except (OSError, NotImplementedError) as e:
        pytest.skip(f"cannot make a link here: {e}")
    assert load(r / "src", r)[1] == ""


def test_the_hook_gives_the_reminder_after_cd(workspace, hook_env, tmp_path):
    _, repo = workspace
    _config(repo, "project")
    (repo / "src").mkdir()
    home = tmp_path / "home"
    home.mkdir()
    env = {**hook_env, "CLAUDE_PROJECT_DIR": str(repo), "HOME": str(home), "USERPROFILE": str(home)}
    env.pop("CLAUDE_CONFIG_DIR", None)
    _, out, _ = run_hook(
        edit_payload(repo / "src", repo / "src" / "a.py", "NEEDLE(1)\n"), env)
    assert "additionalContext" in out
