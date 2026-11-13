"""A file renamed from a name the commit and push reviews leave out to one
they read is reviewed whole; every other rename is reviewed as before."""
import json
import os
import sys

import pytest

from conftest import (
    GIT_ENV, bash_payload, commit_file, git, make_repo, metrics_of, run_hook,
)

import gitutil
import security_reminder_hook as hook
from diffstate import _load_reviewed_shas

BODY = "import os\n" + "".join(f"value_{i} = {i}\n" for i in range(30)) + "os.system(input())\n"
MARK = "os.system(input())"
SECRET = "".join(f"KEY_{i}=SECRET_VALUE_{i}\n" for i in range(30))


@pytest.fixture(autouse=True)
def git_env(monkeypatch):
    for k, v in GIT_ENV.items():
        monkeypatch.setenv(k, v)


def _sent(stub_api):
    return "\n".join(json.dumps(b) for b, c in zip(stub_api.bodies, stub_api.calls)
                     if c.endswith("/v1/messages"))


def _move(repo, old, new):
    (repo / new).parent.mkdir(parents=True, exist_ok=True)
    git(repo, "mv", old, new)


def _commit(repo, env, command="git commit -m change", args=("-m", "change")):
    git(repo, "add", "-A")
    out = git(repo, "commit", *args)
    return metrics_of(run_hook(bash_payload(repo, command, stdout=out), env)[1])


def _push_repo(tmp_path, files):
    repo = make_repo(tmp_path / "repo", files)
    remote = tmp_path / "remote.git"
    git(tmp_path, "init", "-q", "--bare", str(remote))
    git(repo, "remote", "add", "origin", str(remote))
    git(repo, "push", "-q", "-u", "origin", "main")
    return repo, remote


def _push(repo, remote, env):
    old = git(repo, "rev-parse", "--short", "@{u}").strip()
    git(repo, "push", "-q")
    new = git(repo, "rev-parse", "--short", "HEAD").strip()
    out = f"To {remote}\n   {old}..{new}  main -> main\n"
    return metrics_of(run_hook(bash_payload(repo, "git push", out), env)[1])


@pytest.mark.parametrize("old,new", [
    ("notes.txt", "payload.py"),
    ("docs/setup.md", "bin/setup.sh"),
    ("docs/image.txt", "Dockerfile"),
    ("notes.txt", "a b/pay load.py"),
    ("notes.txt", "café.py"),
])
def test_commit_review_reads_the_renamed_file(tmp_path, hook_env, stub_api, old, new):
    repo = make_repo(tmp_path / "repo", {old: BODY, "app.py": "x = 1\n"})
    _move(repo, old, new)
    m = _commit(repo, hook_env)
    assert m.get("skip_reason") is None and m["files_reviewed"] == 1, m
    assert m["renamed_in"] == 1
    assert MARK in _sent(stub_api)


def test_push_review_reads_the_renamed_file(tmp_path, hook_env, stub_api):
    repo, remote = _push_repo(tmp_path, {"notes.txt": BODY})
    _move(repo, "notes.txt", "payload.py")
    git(repo, "commit", "-qm", "rename")
    m = _push(repo, remote, hook_env)
    assert m.get("skip_reason") is None and m["files_reviewed"] == 1, m
    assert MARK in _sent(stub_api)


def test_edit_in_the_rename_shows_the_whole_file_once(tmp_path, hook_env, stub_api):
    repo = make_repo(tmp_path / "repo", {"notes.txt": BODY})
    _move(repo, "notes.txt", "payload.py")
    text = (repo / "payload.py").read_text().replace("value_29 = 29", "value_29 = EDITED")
    (repo / "payload.py").write_text(text)
    m = _commit(repo, hook_env)
    assert m["renamed_in"] == 1 and m["files_reviewed"] == 1, m
    # Added, not context: the reviewer is told to leave context lines alone.
    assert "+" + MARK in _sent(stub_api) and "+value_29 = EDITED" in _sent(stub_api)
    assert "\\n " + MARK not in _sent(stub_api)
    # What the edit removed is still there to see.
    assert "-value_29 = 29" in _sent(stub_api)


def test_edit_hunk_stays_where_the_whole_file_does_not_fit(tmp_path, monkeypatch):
    repo = make_repo(tmp_path / "repo", {"notes.txt": BODY, "app.py": "x = 1\n"})
    _move(repo, "notes.txt", "payload.py")
    git(repo, "commit", "-qm", "c")
    renamed = [("payload.py", ("show", "--format=", "HEAD"), "HEAD")]
    edits = [("payload.py", "@@ -1 +1 @@\n-x\n+y"), ("app.py", "@@ -1 +1 @@\n-x\n+y")]
    files, failed = hook._with_renamed_in(str(repo), edits, renamed, 30)
    assert [n for n, _ in files] == ["payload.py", "app.py"] and not failed
    assert MARK in files[0][1] and files[1] == edits[1]
    for name, limit in (("DIFF_TOTAL_BYTES", 300), ("DIFF_PER_FILE_BYTES", 300)):
        with monkeypatch.context() as m:
            m.setattr(hook, name, limit)
            assert hook._with_renamed_in(str(repo), edits, renamed, 30)[0] == edits
    monkeypatch.setattr(hook, "RENAMED_IN_BYTES", 300)
    for before in (edits, edits[1:]):
        assert hook._with_renamed_in(str(repo), before, renamed, 30)[0] == before


def test_merge_hunks_are_left_alone(tmp_path):
    repo = make_repo(tmp_path / "repo", {"notes.txt": BODY})
    _move(repo, "notes.txt", "payload.py")
    git(repo, "commit", "-qm", "c")
    files = [("payload.py", "@@@ -1,1 -1,1 +1,1 @@@\n- x\n -y\n++z")]
    renamed = [("payload.py", ("show", "--format=", "HEAD"), "HEAD")]
    assert hook._with_renamed_in(str(repo), files, renamed, 30) == (files, False)


def test_rename_added_by_an_amend(tmp_path, hook_env, stub_api):
    repo = make_repo(tmp_path / "repo", {"notes.txt": BODY, "app.py": "x = 1\n"})
    commit_file(repo, "app.py", "x = 2\n")
    _move(repo, "notes.txt", "payload.py")
    m = _commit(repo, hook_env, "git commit --amend --no-edit", ("--amend", "--no-edit"))
    assert m.get("amend_delta_review") is True and m["files_reviewed"] == 1, m
    assert MARK in _sent(stub_api)


@pytest.mark.parametrize("old,new", [
    ("a.py", "pkg/b.py"), ("a.py", "notes.txt"), ("notes.txt", "other.txt"),
    ("a.py", "vendor/a.py"), ("vendor/a.py", "a.py"), ("server.pem", "server"),
    ("prod.env", "prod.sh"), (".htpasswd", "htpasswd"), ("dump.csv", "dump.sql"),
    ("credentials.txt", "credentials.sh"), ("deploy_rsa.txt", "deploy.sh"),
    ("passwords.md", "list.py"), ("notes.txt", "notes"), ("data.txt", "data.json"), ("notes.txt", "vendor/a.py"),
])
def test_other_renames_are_not_sent(tmp_path, hook_env, stub_api, old, new):
    repo = make_repo(tmp_path / "repo", {old: BODY, "app.py": "x = 1\n"})
    _move(repo, old, new)
    m = _commit(repo, hook_env)
    assert m["skip_reason"] == 30 and "renamed_in" not in m
    assert _sent(stub_api) == ""


def test_rename_away_from_a_secret_shaped_name_stays_out(tmp_path, hook_env, stub_api):
    repo = make_repo(tmp_path / "repo", {"deploy_rsa": SECRET})
    _move(repo, "deploy_rsa", "settings.py")
    assert _commit(repo, hook_env)["skip_reason"] == 30
    assert _sent(stub_api) == ""


@pytest.mark.parametrize("secret_goes", ["deleted", "renamed"])
def test_not_sent_whole_when_a_secret_shaped_file_goes_too(
        tmp_path, hook_env, stub_api, secret_goes):
    # Same content under both names: git may pair either with the new file.
    repo = make_repo(tmp_path / "repo", {
        ".env": SECRET, "notes.txt": SECRET, "app.py": "x = 1\n"})
    _move(repo, "notes.txt", "settings.py")
    if secret_goes == "deleted":
        git(repo, "rm", "-q", ".env")
    else:
        _move(repo, ".env", "old_env.txt")
    (repo / "app.py").write_text("x = input()\n")
    m = _commit(repo, hook_env)
    assert m["files_reviewed"] == 1 and "renamed_in" not in m, m
    assert "SECRET_VALUE" not in _sent(stub_api)


@pytest.mark.parametrize("amend", [False, True])
def test_secret_shaped_file_renamed_in_two_steps_stays_out(tmp_path, hook_env, stub_api, amend):
    repo = make_repo(tmp_path / "repo", {".env": SECRET})
    _move(repo, ".env", "settings.txt")
    git(repo, "commit", "-qm", "one")
    _move(repo, "settings.txt", "settings.py")
    extra = ["--amend", "--no-edit"] if amend else ["-m", "two"]
    m = _commit(repo, hook_env, "git commit " + " ".join(extra), extra)
    assert "SECRET_VALUE" not in _sent(stub_api) and "renamed_in" not in m, m
    assert m["skip_reason"] == (35 if amend and m.get("amend_delta_review") else 30), m


def test_secret_shaped_file_renamed_after_edits_stays_out(tmp_path, hook_env, stub_api):
    repo = make_repo(tmp_path / "repo", {"deploy_rsa": SECRET})
    _move(repo, "deploy_rsa", "a.txt")
    with open(repo / "a.txt", "a") as f:
        f.write("MORE=1\n")
    git(repo, "commit", "-qam", "one")
    commit_file(repo, "other.py", "x = 1\n")
    _move(repo, "a.txt", "settings.py")
    m = _commit(repo, hook_env)
    assert "SECRET_VALUE" not in _sent(stub_api), m


@pytest.mark.parametrize("how", [
    "added lately", "in a merge", "in a merge, combined diffs", "on a side branch"])
def test_secret_shaped_origin_is_followed(tmp_path, hook_env, stub_api, how):
    repo = make_repo(tmp_path / "repo", {"app.py": "x = 1\n"})
    if how.endswith("combined diffs"):
        git(repo, "config", "log.diffMerges", "combined")
    if how == "on a side branch":
        commit_file(repo, "app.py", "x = 2\n")
        git(repo, "switch", "-qc", "side", "HEAD~1")
    commit_file(repo, ".env", SECRET)
    if how.startswith("in a merge"):
        git(repo, "switch", "-qc", "side")
        commit_file(repo, "side.py", "y = 1\n")
        git(repo, "switch", "-q", "main")
        git(repo, "merge", "-q", "--no-ff", "--no-commit", "side")
    _move(repo, ".env", "settings.txt")
    git(repo, "commit", "-qm", "one")
    if how == "on a side branch":
        git(repo, "switch", "-q", "main")
        git(repo, "merge", "-q", "--no-ff", "--no-edit", "side")
    for i in range(5):
        commit_file(repo, f"m{i}.py", "z = 1\n")
    _move(repo, "settings.txt", "settings.py")
    m = _commit(repo, hook_env)
    assert m["skip_reason"] == 30 and "SECRET_VALUE" not in _sent(stub_api), m


def test_unknown_origin_stays_out(tmp_path):
    repo = make_repo(tmp_path / "repo", {"notes.txt": BODY})
    _move(repo, "notes.txt", "payload.py")
    git(repo, "commit", "-qm", "c")
    show = ("show", "--format=", "HEAD")
    assert hook._with_renamed_in(str(repo), [], [("payload.py", show, "nope")], 30) == ([], True)
    assert hook._with_renamed_in(str(repo), [], [("payload.py", show, "HEAD")], 30)[0]
    assert gitutil.came_from_secret(str(repo), "HEAD", ["payload.py"], 10) == set()
    assert gitutil.came_from_secret(str(repo), "nope", ["payload.py"], 10) is None


def _two_quiet_commits(repo, env, second):
    _move(repo, "notes.txt", "payload.py")
    git(repo, "commit", "-qm", "one")
    second()
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "two")
    command = "git commit -qm one && git commit -qam two"
    return metrics_of(run_hook(bash_payload(repo, command), env)[1])


def test_file_is_shown_as_the_last_of_the_commits_left_it(tmp_path, hook_env, stub_api):
    repo = make_repo(tmp_path / "repo", {"notes.txt": BODY})
    m = _two_quiet_commits(repo, hook_env, lambda: (repo / "payload.py").write_text(
        BODY.replace(MARK, "print('fixed')")))
    assert m["reflog_shas_n"] > 1 and m["files_reviewed"] == 1 and m["renamed_in"] == 1, m
    assert "+value_5 = 5" in _sent(stub_api) and "+print('fixed')" in _sent(stub_api)
    assert "+" + MARK not in _sent(stub_api)


def _many(n):
    return {f"d/m{i:03}.txt": f"import os\nvalue = {i}\nkey_{i} = 'k{i}'\nname_{i} = {i}\n"
            for i in range(n)}


@pytest.mark.parametrize("edits,renames,renamed_in", [
    (28, 20, 2), (30, 5, None), (3, 12, hook.MAX_RENAMED_IN), (0, 40, hook.MAX_RENAMED_IN)])
def test_renamed_files_take_only_free_places(
        tmp_path, hook_env, stub_api, edits, renames, renamed_in):
    edited = {f"e{i:02}.py": "x = 1\n" for i in range(edits)}
    repo = make_repo(tmp_path / "repo", {**edited, **_many(renames)})
    for name in edited:
        (repo / name).write_text("x = 2\n")
    for name in _many(renames):
        _move(repo, name, name[:-4] + ".py")
    m = _commit(repo, hook_env)
    assert m["files_reviewed"] == edits + (renamed_in or 0), m
    assert m.get("renamed_in") == renamed_in and "diff_files_dropped" not in m
    assert all(n in _sent(stub_api) for n in edited)


def test_renames_do_not_count_towards_the_skip_for_huge_diffs(tmp_path, monkeypatch):
    many = [(f"e{i}.py", "@@ -1 +1 @@\n-x\n+y") for i in range(31)]
    monkeypatch.setattr(hook, "git_diff_unpaired", None)
    assert hook._with_renamed_in("/r", many, [("n.py", ("show", "x"), "x")], 30) == (many, False)


def test_a_directory_replaced_by_the_file_adds_one_file(tmp_path, hook_env, stub_api):
    under = {f"makefile/auth_handler{i:02}.py": f"import os\nx = {i}\n" for i in range(20)}
    edits = {f"e{i:02}.py": "x = 1\n" for i in range(9)}
    repo = make_repo(tmp_path / "repo", {"notes.txt": BODY, **under, **edits})
    git(repo, "rm", "-rq", "makefile")
    _move(repo, "notes.txt", "makefile")
    for name in edits:
        (repo / name).write_text("x = 2\n")
    m = _commit(repo, hook_env)
    assert m["renamed_in"] == 1 and m["files_reviewed"] == 30, m
    assert "diff_files_dropped" not in m


def test_push_with_an_unreadable_file_leaves_the_commits_unrecorded(tmp_path, hook_env, stub_api):
    repo, remote = _push_repo(tmp_path, {"notes.txt": BODY})
    blob = git(repo, "rev-parse", "HEAD:notes.txt").strip()
    _move(repo, "notes.txt", "payload.py")
    git(repo, "commit", "-qm", "rename")
    git(repo, "push", "-q")
    # git shows a rename of unchanged content without reading that content.
    obj = repo / ".git" / "objects" / blob[:2] / blob[2:]
    os.chmod(obj, 0o644)
    obj.unlink()
    out = f"To {remote}\n   {git(repo, 'rev-parse', '--short', 'HEAD~1').strip()}.."\
          f"{git(repo, 'rev-parse', '--short', 'HEAD').strip()}  main -> main\n"
    m = metrics_of(run_hook(bash_payload(repo, "git push", out), hook_env)[1])
    assert m["skip_reason"] == 45, m
    assert not _load_reviewed_shas(str(repo))
    assert _sent(stub_api) == ""


@pytest.mark.skipif(sys.platform in ("win32", "darwin"), reason="file names are Unicode there")
def test_push_of_a_name_that_is_not_utf8_is_not_recorded(tmp_path, hook_env, stub_api):
    repo, remote = _push_repo(tmp_path, {"notes.txt": BODY})
    os.rename(repo / "notes.txt", os.fsencode(repo) + b"/caf\xe9.py")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "rename")
    assert _push(repo, remote, hook_env)["skip_reason"] == 45
    assert not _load_reviewed_shas(str(repo))


@pytest.mark.parametrize("name", ["GIT_ICASE_PATHSPECS", "GIT_GLOB_PATHSPECS",
                                  "GIT_NOGLOB_PATHSPECS", "GIT_LITERAL_PATHSPECS"])
def test_pathspec_setting_in_the_environment(tmp_path, hook_env, stub_api, name):
    repo = make_repo(tmp_path / "repo", {"notes.txt": BODY})
    _move(repo, "notes.txt", "payload.py")
    m = _commit(repo, {**hook_env, name: "1"})
    assert m.get("renamed_in") == 1, m


def test_new_name_is_a_file_name_not_a_pattern(tmp_path):
    repo = make_repo(tmp_path / "repo", {"notes.txt": BODY, "a.py": "x = 1\n"})
    _move(repo, "notes.txt", "[ab].py")
    (repo / "a.py").write_text("x = 2\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "c")
    files = gitutil.git_diff_unpaired(
        str(repo), ("show", "--format=", "HEAD"), ["[ab].py"], 10)
    assert list(files) == ["[ab].py"]


def test_names_in_a_rename_with_an_edit_come_from_the_rename_lines():
    hunk = ["--- a/x", "+++ b/y", "@@ -1 +1 @@", "-a", "+b"]
    text = (_section("a/cfg b/.env b/cfg b/app.py", "rename from cfg b/.env",
                     "rename to cfg b/app.py", *hunk)
            + _section("a/a b/x.py b/a b/y.py", "rename from a b/x.py", "rename to a b/y.py", *hunk))
    assert [n for n, _ in gitutil.parse_diff_into_files(text)] == ["a b/y.py"]
    assert gitutil.extract_file_paths_from_diff(text) == ["a b/y.py"]


def test_name_with_the_header_separator_in_it(tmp_path, hook_env, stub_api):
    repo = make_repo(tmp_path / "repo", {"notes.txt": BODY, "cfg b/app.py": "x = 1\n"})
    _move(repo, "notes.txt", "pkg b/tool.py")
    (repo / "cfg b/app.py").write_text("x = input()\n")
    m = _commit(repo, hook_env)
    assert m["files_reviewed"] == 2 and m["renamed_in"] == 1, m
    assert "pkg b/tool.py" in _sent(stub_api) and "cfg b/app.py" in _sent(stub_api)
    assert "tool.py b/pkg" not in _sent(stub_api) and "app.py b/cfg" not in _sent(stub_api)


def _section(header, *lines):
    return "\n".join([f"diff --git {header}", *lines]) + "\n"


@pytest.mark.parametrize("header,old,new,expect", [
    ("a/n.txt b/n.py", "n.txt", "n.py", ["n.py"]),
    ('"a/we\\"ird.txt" "b/we\\"ird.py"', '"we\\"ird.txt"', '"we\\"ird.py"', ['we"ird.py']),
    ("a/x b/y.txt b/x b/y.py", "x b/y.txt", "x b/y.py", ["x b/y.py"]),
    ("a/x.py b/y.py b/x.py b/z.py", "x.py b/y.py", "x.py b/z.py", []),
    ("a/.env b/n.py", ".env", "n.py", []),
    ("a/n.txt b/deploy_rsa", "n.txt", "deploy_rsa", []),
])
@pytest.mark.parametrize("verb", ["rename", "copy"])
def test_names_come_from_the_rename_lines(verb, header, old, new, expect):
    text = _section(header, "similarity index 100%", f"{verb} from {old}", f"{verb} to {new}")
    assert gitutil.renamed_into_review(text) == expect


def test_lines_of_content_are_not_rename_lines():
    text = _section("a/a.py b/a.py", "--- a/a.py", "+++ b/a.py", "@@ -1 +1,3 @@",
                    " rename from n.txt", "rename from n.txt", "rename to n.py")
    assert gitutil.renamed_into_review(text) == []


@pytest.mark.parametrize("gone", [".env", "cfg b/.env", "deploy_rsa"])
def test_nothing_is_listed_when_a_secret_shaped_file_goes_too(gone):
    text = (_section(f"a/{gone} b/{gone}", "deleted file mode 100644", "@@ -1 +0,0 @@", "-x")
            + _section("a/n.txt b/n.py", "similarity index 100%", "rename from n.txt", "rename to n.py"))
    assert gitutil.renamed_into_review(text) == []
