"""Which Claude Code the Agent SDK is told to start on Windows."""
import os
import subprocess
import sys
import types

import pytest

from conftest import HOOKS_DIR

import _base
import llm

VAR = "NoDefaultCurrentDirectoryInExePath"
windows_only = pytest.mark.skipif(os.name != "nt", reason="needs Windows path rules")


def put(folder, name="claude.exe"):
    folder.mkdir(parents=True, exist_ok=True)
    (folder / name).write_text("")
    return str(folder / name)


def set_path(monkeypatch, *entries):
    monkeypatch.setenv("PATH", os.pathsep.join(str(e) for e in entries))


@pytest.fixture
def win(monkeypatch, tmp_path):
    """llm as on Windows: an empty home and PATH, no CLI named in the
    environment, and a working directory that has a claude.exe of its own."""
    ns = types.SimpleNamespace(home=tmp_path / "home", repo=tmp_path / "repo", tools=tmp_path / "tools")
    for d in (ns.home, ns.repo, ns.tools):
        d.mkdir()
    put(ns.repo)
    monkeypatch.setattr(llm, "_WINDOWS", True)
    monkeypatch.setattr(llm, "_gateway_cli", None)
    monkeypatch.setattr(_base, "DEBUG_LOG_FILE", str(tmp_path / "log.txt"))
    monkeypatch.setenv("HOME", str(ns.home))
    monkeypatch.setenv("USERPROFILE", str(ns.home))  # "~" on Windows
    for var in ("SG_AGENTIC_CLI_PATH", "CLAUDE_CODE_EXECPATH", "CLAUDE_PROJECT_DIR"):
        monkeypatch.delenv(var, raising=False)
    set_path(monkeypatch)
    monkeypatch.chdir(ns.repo)
    return ns


class TestUsersOwnCli:
    def test_native_installers_folder_comes_first(self, win, monkeypatch):
        put(win.tools)
        set_path(monkeypatch, win.tools)
        native = put(win.home / ".local" / "bin")
        assert llm._windows_user_cli() == native

    @pytest.mark.parametrize("spelling", [
        pytest.param("{}", id="plain"),
        pytest.param('"{}"', id="quoted"),
        pytest.param("{}" + os.sep, id="trailing-separator"),
    ])
    def test_found_on_path(self, win, monkeypatch, spelling):
        put(win.tools)
        set_path(monkeypatch, win.tools / "empty", spelling.format(win.tools))
        assert os.path.samefile(llm._windows_user_cli(), win.tools / "claude.exe")

    def test_batch_file_is_not_used(self, win, monkeypatch):
        put(win.tools, "claude.cmd")
        set_path(monkeypatch, win.tools)
        assert llm._windows_user_cli() is None

    @pytest.mark.parametrize("entry", [
        pytest.param("", id="empty"),
        pytest.param(".", id="dot"),
        pytest.param("{repo}", id="full-path"),
        pytest.param("{repo}" + os.sep, id="trailing-separator"),
        pytest.param(os.path.join("..", "repo"), id="relative"),
    ])
    def test_working_directory_is_not_searched(self, win, monkeypatch, entry):
        set_path(monkeypatch, entry.format(repo=win.repo))
        assert llm._windows_user_cli() is None

    def test_search_continues_past_the_working_directory(self, win, monkeypatch):
        exe = put(win.tools)
        set_path(monkeypatch, ".", win.repo, win.tools)
        assert llm._windows_user_cli() == exe

    def test_relative_entry_is_skipped(self, win, monkeypatch):
        put(win.tools)
        set_path(monkeypatch, os.path.join("..", "tools"))
        assert llm._windows_user_cli() is None

    @pytest.mark.parametrize("home", ["~", "", "home"])
    def test_home_that_is_not_a_full_path_is_skipped(self, win, monkeypatch, home):
        put(win.repo / home / ".local" / "bin")
        monkeypatch.setattr(llm.os.path, "expanduser", lambda p: home)
        assert llm._windows_user_cli() is None

    def test_project_root_is_not_searched_from_a_subfolder(self, win, monkeypatch):
        (win.repo / "sub").mkdir()
        monkeypatch.chdir(win.repo / "sub")
        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(win.repo).replace(os.sep, "/"))
        set_path(monkeypatch, win.repo)
        assert llm._windows_user_cli() is None

    def test_link_to_the_working_directory_is_not_searched(self, win, monkeypatch, tmp_path):
        try:
            if os.name == "nt":
                import _winapi
                _winapi.CreateJunction(str(win.repo), str(tmp_path / "link"))
            else:
                os.symlink(win.repo, tmp_path / "link", target_is_directory=True)
        except OSError:
            pytest.skip("cannot make a link here")
        set_path(monkeypatch, tmp_path / "link")
        assert llm._windows_user_cli() is None

    @pytest.mark.parametrize("project", [False, True])
    def test_folder_inside_the_project_is_not_searched(self, win, monkeypatch, project):
        put(win.repo / ".venv" / "Scripts")
        if project:
            (win.repo / "sub").mkdir()
            monkeypatch.chdir(win.repo / "sub")
            monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(win.repo))
        set_path(monkeypatch, win.repo / ".venv" / "Scripts")
        assert llm._windows_user_cli() is None

    def test_folder_that_only_shares_a_prefix_is_found(self, win, monkeypatch, tmp_path):
        exe = put(tmp_path / "repo-tools")
        set_path(monkeypatch, tmp_path / "repo-tools")
        assert llm._windows_user_cli() == exe

    def test_session_above_the_home_folder_still_finds_the_native_install(self, win, monkeypatch):
        native = put(win.home / ".local" / "bin")
        monkeypatch.chdir(win.home.parent)
        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(win.home.parent))
        assert llm._windows_user_cli() == native

    def test_tools_under_the_home_folder_are_found(self, win, monkeypatch):
        exe = put(win.home / "AppData" / "tool")
        monkeypatch.chdir(win.home)
        set_path(monkeypatch, win.home / "AppData" / "tool")
        assert llm._windows_user_cli() == exe

    @windows_only
    def test_entries_without_a_drive_or_a_root_are_skipped(self, win, monkeypatch):
        put(win.tools)
        drive, rest = os.path.splitdrive(str(win.tools))
        set_path(monkeypatch, rest, rest.replace("\\", "/"), drive + os.path.relpath(str(win.tools)))
        assert llm._windows_user_cli() is None

    @windows_only
    def test_other_spellings_of_the_working_directory_are_skipped(self, win, monkeypatch):
        import ctypes
        short = ctypes.create_unicode_buffer(1024)
        ctypes.windll.kernel32.GetShortPathNameW(str(win.repo), short, 1024)
        repo = str(win.repo)
        set_path(monkeypatch, repo.upper(), repo.replace("\\", "/"), "\\\\?\\" + repo, short.value or repo)
        assert llm._windows_user_cli() is None


class TestFixedPaths:
    @pytest.fixture
    def installed_as_on_linux(self, win, monkeypatch):
        monkeypatch.setattr(llm.os.path, "isfile", lambda p: p.endswith("/bin/claude"))

    def test_not_used_on_windows(self, installed_as_on_linux):
        assert llm._user_cli_path() is None

    def test_used_elsewhere(self, installed_as_on_linux, monkeypatch):
        monkeypatch.setattr(llm, "_WINDOWS", False)
        assert llm._user_cli_path().endswith("/.local/bin/claude")


@pytest.fixture
def sdk(monkeypatch, tmp_path):
    """Stand-in for claude_agent_sdk, installed in tmp_path, that records the
    options of each spawn in .spawned."""
    class ResultMessage:
        subtype, usage, total_cost_usd = "success", {}, 0.0
        structured_output = {"findings": []}

    async def query(prompt, options):
        yield ResultMessage()

    mod = types.ModuleType("claude_agent_sdk")
    mod.spawned = []
    mod.ClaudeAgentOptions = lambda **kwargs: mod.spawned.append(kwargs)
    mod.AssistantMessage = type("AssistantMessage", (), {})
    mod.ResultMessage, mod.query = ResultMessage, query
    mod.__file__ = str(tmp_path / "site" / "claude_agent_sdk" / "__init__.py")
    mod.bundled = str(tmp_path / "site" / "claude_agent_sdk" / "_bundled" / "claude.exe")
    monkeypatch.setitem(sys.modules, "claude_agent_sdk", mod)
    monkeypatch.setenv("SECURITY_REVIEW_MODEL", "opus")
    return mod


def bundle(tmp_path):
    return put(tmp_path / "site" / "claude_agent_sdk" / "_bundled")


REVIEWS = [
    pytest.param(lambda: llm.agentic_review(os.getcwd(), [("a.py", "+x = 1\n")], ["a.py"]), id="agentic"),
    pytest.param(lambda: llm._call_claude_via_sdk("review this", {"type": "object"}), id="cloud-provider"),
]


@pytest.mark.parametrize("review", REVIEWS)
class TestWhatTheSdkIsTold:
    @staticmethod
    def told(sdk):
        assert sdk.spawned
        return {o["cli_path"] for o in sdk.spawned}

    def test_bundled_cli_before_the_users(self, win, sdk, tmp_path, review):
        put(win.home / ".local" / "bin")
        bundle(tmp_path)
        review()
        assert self.told(sdk) == {sdk.bundled}

    def test_users_cli_when_nothing_is_bundled(self, win, sdk, monkeypatch, review):
        tolerant = []
        monkeypatch.setattr(llm, "_tolerate_unknown_sdk_messages", lambda: tolerant.append(1))
        set_path(monkeypatch, ".", win.tools)
        cli = put(win.tools)
        review()
        assert self.told(sdk) == {cli} and tolerant

    def test_full_path_is_named_when_no_cli_exists(self, win, sdk, review):
        review()
        assert self.told(sdk) == {sdk.bundled}

    def test_named_cli_is_used_as_named(self, win, sdk, tmp_path, monkeypatch, review):
        bundle(tmp_path)
        monkeypatch.setenv("SG_AGENTIC_CLI_PATH", "X:\\my\\claude.exe")
        review()
        assert self.told(sdk) == {"X:\\my\\claude.exe"}

    def test_empty_name_is_no_name(self, win, sdk, tmp_path, monkeypatch, review):
        put(win.home / ".local" / "bin")
        bundle(tmp_path)
        monkeypatch.setenv("SG_AGENTIC_CLI_PATH", "")
        review()
        assert self.told(sdk) == {sdk.bundled}

    def test_sdk_chooses_off_windows(self, win, sdk, tmp_path, monkeypatch, review):
        monkeypatch.setattr(llm, "_WINDOWS", False)
        monkeypatch.setattr(llm, "_user_cli_path", lambda: None)
        bundle(tmp_path)
        review()
        assert self.told(sdk) == {None}


def test_empty_name_is_no_name_off_windows(monkeypatch):
    monkeypatch.setattr(llm, "_WINDOWS", False)
    assert llm._cli_for_sdk("") is None


def test_sdk_module_without_a_file_still_gets_a_full_path(win, sdk):
    del sdk.__file__
    assert os.path.isabs(llm._cli_for_sdk(None))


class TestSearchOrderVariable:
    @staticmethod
    def after_import(os_name, **env):
        code = (f"import os; os.name = {os_name!r}; import _base; "
                f"print(os.environ.get({VAR!r}))")
        base = {k: v for k, v in os.environ.items() if k.upper() != VAR.upper()}
        return subprocess.run([sys.executable, "-c", code], cwd=HOOKS_DIR, env={**base, **env},
                              capture_output=True, text=True, check=True).stdout.strip()

    def test_set_on_windows_when_absent(self):
        assert self.after_import("nt") == "1"

    def test_existing_value_is_kept(self):
        assert self.after_import("nt", **{VAR: "0"}) == "0"

    @pytest.mark.skipif(os.name == "nt", reason="checks that the variable is not set off Windows")
    def test_not_set_elsewhere(self):
        assert self.after_import(os.name) == "None"
