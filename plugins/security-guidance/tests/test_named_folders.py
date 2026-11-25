"""Where the repository read off a command does not have the commit, the other
folders the command names are looked at (#7161)."""
import os
import re
import shutil
import subprocess
import time
from pathlib import Path

import pytest

import reporesolve as rr
from conftest import STUB_VULN, GIT_ENV, VULN_PY, bash_payload, commit_file, git, make_repo, metrics_of, run_hook

BASH = r"C:\Program Files\Git\bin\bash.exe" if os.name == "nt" else shutil.which("bash")
COMMIT = "git commit -m x"
windows_only = pytest.mark.skipif(os.name != "nt", reason="Windows paths")
needs_bash = pytest.mark.skipif(not BASH or not os.path.exists(BASH), reason="needs bash")


@pytest.fixture
def repos(tmp_path):
    out = []
    for name in ("session", "other"):
        d = tmp_path / name
        d.mkdir()
        make_repo(d)
        out.append(d)
    return out


def _p(path):
    return str(path).replace("\\", "/")


def _old(repo):
    """The newest commit is from long ago, as in a repository not worked in today."""
    env = {**os.environ, **GIT_ENV, "GIT_COMMITTER_DATE": "2026-01-01T00:00:00Z"}
    subprocess.run(["git", "commit", "-q", "--amend", "--no-edit", "--date=2026-01-01T00:00:00Z"],
                   cwd=repo, env=env, check=True)
    git(repo, "reflog", "delete", "HEAD@{1}")
    then = time.time() - 4000
    os.utime(repo / ".git" / "logs" / "HEAD", (then, then))


# (command, where it commits)
SHAPES = [
    ("(cd {o} && true) && git commit -m x", "s"), ("(cd {o}; true); git commit -m x", "s"),
    ("D=$(cd {o} && pwd); git commit -m x", "s"), ("(cd {o} && (cd .. && true)) && git commit -m x", "s"),
    ("cd {o} && true && cd - >/dev/null && git commit -m x", "s"),
    ('cd {o} && cd "$OLDPWD" && git commit -m x', "s"),
    ("cat > run.sh <<'EOF'\ncd {o}\nmake\nEOF\ngit commit -m x", "s"),
    ("cat > run.sh <<EOF\ncd {o}\ngit commit -m y\nEOF\ngit commit -m x", "s"),
    ("cd {o} & wait; git commit -m x", "s"), ("cd {o} | cat; git commit -m x", "s"),
    ("bash -c 'cd {o}' && git commit -m x", "s"), ("diff <(cd {o} && ls) <(ls) >/dev/null; git commit -m x", "s"),
    ("cat <<A <<'B' >/dev/null\ncd {o}\nA\ncd {o}\nB\ngit commit -m x", "s"),
    ("if false; then cd {o}; fi; git commit -m x", "s"),
    ("R=$PWD; if cd {o}; then cd \"$R\" && git commit -m x; fi", "s"),
    ("cd {o} && git -C {s} commit -m x", "s"),
    ("cd {o}; if [ -d nothere ]; then cd nothere; fi; git commit -m x", "o"),
    ("cd {o} && env $(echo A=1) git commit -m x", "o"),
    ("# go there\ncd {o} && git commit -m x", "o"), ("# don't\ncd {o} && git commit -m x", "o"),
    ("cd {o} # note\ngit commit -m x", "o"), ("echo a#b && cd {o} && git commit -m x", "o"),
    ("if cd {o}; then git commit -m x; fi", "o"),
    ("echo a | while read x; do cd {o}; git commit -m x; done", "o"),
    ("for d in {o}; do (cd \"$d\" && git commit -m x); done", "o"),
    ("D={o}; cd $D && git commit -m x", "o"), ('D="{o}"; cd "${{D}}" && git commit -m x', "o"),
    ("GIT_DIR={o}/.git GIT_WORK_TREE={o} git commit -m x", "o"),
    ("f() {{ cd {o}; }}; f && git commit -m x", "o"), ("bash <<'EOF'\ncd {o}\ngit commit -m x\nEOF", "o"),
    ("bash -c 'cd {o} && git commit -m x'", "o"), ("bash -c \"cd \\\"{o}\\\" && git commit -m x\"", "o"),
    ("D={o}; eval \"cd $D\"; git commit -m x && true \"y\"", "o"), ("cd ../other && git commit -m x", "o"),
    ("cd {o}/.. && cd other && git commit -m x", "o"), ("cd {o} && git commit -m 'fix (a) and )'", "o"),
    ("git -C {o} commit -m x", "o"), ("git --git-dir={o}/.git --work-tree={o} commit -m x", "o"),
    ("pushd {o} >/dev/null && git commit -m x && popd >/dev/null", "o"),
]


@needs_bash
@pytest.mark.parametrize("quiet", [False])
@pytest.mark.parametrize("command,where", SHAPES)
def test_commit_is_reviewed_where_bash_made_it(repos, hook_env, stub_api, command, where, quiet):
    session, other = repos
    for d, name in zip(repos, ("session", "other")):
        _old(d)
        (d / f"{name}_f.py").write_text(VULN_PY)
        git(d, "add", f"{name}_f.py")
    before = [git(d, "rev-parse", "HEAD") for d in repos]
    cmd = command.format(s=_p(session), o=_p(other))
    if quiet:
        cmd = cmd.replace("commit -m x", "commit -q -m x")
    env = {**os.environ, **{f"GIT_{a}_{b}": "t" for a in ("AUTHOR", "COMMITTER") for b in ("NAME", "EMAIL")}}
    r = subprocess.run([BASH, "-c", cmd], cwd=session, capture_output=True, text=True, env=env, timeout=60)
    moved = [git(d, "rev-parse", "HEAD") != b for d, b in zip(repos, before)]
    assert moved == [where == "s", where == "o"], (r.stdout, r.stderr)
    run_hook({**bash_payload(session, cmd, r.stdout, r.stderr), "duration_ms": 100}, hook_env)
    sent = set(re.findall(r"(?:session|other)_f\.py", "".join(stub_api.bodies)))
    assert sent == {"session_f.py" if where == "s" else "other_f.py"}


def test_the_first_choice_stands_where_it_has_the_commit(repos):
    session, other = repos
    sha, _ = commit_file(session, "a.py", "x = 1\n")
    git(other, "fetch", "-q", str(session))
    for known in (session, other):
        assert rr.named_repo_with_new_commit(f"cd {_p(other)}; cd {_p(session)}; {COMMIT}", str(session),
                                             rr._git_toplevel(str(known)), sha[:7], 0) is None


@pytest.mark.parametrize("command", [COMMIT, "git add . && git commit -q -m 'cd elsewhere'", "cd . && " + COMMIT,
                                     "cd sub && " + COMMIT, "cd /nowhere/at/all && " + COMMIT])
def test_no_git_is_started_for_a_command_that_names_no_other_repository(repos, monkeypatch, command):
    session, _ = repos
    (session / "sub").mkdir()
    top = rr._git_toplevel(str(session))
    monkeypatch.setattr(rr.subprocess, "run", lambda *a, **k: pytest.fail("git was started"))
    monkeypatch.setattr(rr, "_git_toplevel", lambda d: pytest.fail("git was started"))
    assert list(rr.named_repos(command, str(session), top)) == []


def test_failed_commit_does_not_take_an_old_one_elsewhere(repos, hook_env, stub_api):
    session, other = repos
    commit_file(other, "app.py", VULN_PY)
    _old(other)
    _old(session)
    cmd = f"if true; then cd {_p(other)}; fi; cd {_p(session)}; {COMMIT}"
    run_hook(bash_payload(session, cmd, "nothing to commit, working tree clean"), hook_env)
    assert "shell=True" not in "".join(stub_api.bodies)


def test_fresh_commit_of_the_first_choice_goes_before_another_fresh_one(repos, hook_env, stub_api):
    session, other = repos
    commit_file(session, "session_f.py", VULN_PY)
    commit_file(other, "other_f.py", VULN_PY)
    cmd = f"git -C {_p(other)} status -s; git commit -q -m x"
    run_hook(bash_payload(session, cmd, ""), hook_env)
    body = "".join(stub_api.bodies)
    assert "session_f.py" in body and "other_f.py" not in body


def test_commit_already_reviewed_is_not_taken_again(repos, hook_env, stub_api):
    session, other = repos
    _old(session)
    _, out = commit_file(other, "other_f.py", VULN_PY)
    run_hook(bash_payload(session, f"cd {_p(other)} && {COMMIT}", out, tool_use_id="t1"), hook_env)
    assert "other_f.py" in "".join(stub_api.bodies)
    stub_api.bodies.clear()
    cmd = f"(cd {_p(other)} && true); git commit -q -m x"
    run_hook(bash_payload(session, cmd, "", tool_use_id="t2"), hook_env)
    assert "other_f.py" not in "".join(stub_api.bodies)


@pytest.mark.parametrize("quiet", [False])
def test_repository_the_hooks_stay_out_of_stays_out(repos, hook_env, stub_api, quiet):
    session, other = repos
    git(other, "config", "filter.x.clean", "touch ran")
    (other / ".gitattributes").write_text("* filter=x\n")
    (other / "app.py").write_text(VULN_PY)
    git(other, "-c", "filter.x.clean=cat", "add", "app.py")
    git(other, "-c", "filter.x.clean=cat", "commit", "-q", "-m", "x")
    sha = git(other, "rev-parse", "--short", "HEAD").strip()
    _old(session)
    for f in (other, session):
        if (f / "ran").exists():
            (f / "ran").unlink()
    out = "" if quiet else f"[main {sha}] x\n 1 file changed, 4 insertions(+)\n"
    env = {**hook_env, "CLAUDE_PROJECT_DIR": str(session)}
    run_hook(bash_payload(session, f"if cd {_p(other)}; then {COMMIT}; fi", out), env)
    assert "shell=True" not in "".join(stub_api.bodies)
    assert not (other / "ran").exists() and not (session / "ran").exists()


@pytest.mark.parametrize("shape,n", [
    ("cd {p}; " * 3000, 1), ('cd "' + "a" * 50000, 1), ("-C" * 30000, 1), ("A=$A" * 5000 + "; cd $A", 1),
    ("a=b " * 20000, 1), ("cd ../" + "../" * 5000, 1), ("for x in " + "a " * 40000 + "; do cd $x; done", 1),
    ("; ".join(f"V{i}=$V{i+1}$V{i+1}" for i in range(50)) + "; cd $V0", 1), ("\\\\" * 40000, 1), ("cd '" * 10000, 1),
    ("".join(f"A={i}{'x' * 5000}; " for i in range(8)) + "cd $A$A$A;" * 5500, 1),
    ("cd \\'" + '\\"' * 45000 + "'", 1), ("A=1 " * 12500 + "cd $A$A$A;" * 5000, 1), ("cd " + '"a"' * 30000, 1), ("cd a" + "\\a" * 30000 + '"', 1),
])
def test_long_commands_are_read_in_time(tmp_path, shape, n):
    (tmp_path / "x").mkdir()
    start = time.monotonic()
    list(rr.named_repos(shape.replace("{p}", _p(tmp_path / "x")), str(tmp_path)))
    assert time.monotonic() - start < 5


@pytest.mark.parametrize("p,expected", [
    ("/c/Users/me", "c:/Users/me"), ("/D/work", "D:/work"), ("/c", "c:/"), ("/cygdrive/c/x", "c:/x"),
])
def test_windows_path(p, expected):
    assert rr._windows_paths(p) == [expected, p]


@pytest.mark.parametrize("p", ["/cc/x", "c/x", "C:/x", "~/x", "/usr/bin", "", "/1/x", "//c/share"])
def test_other_paths_have_one_reading(p):
    assert rr._windows_paths(p) == [p]


def test_tmp_is_the_temporary_folder():
    import tempfile
    assert rr._windows_paths("/tmp/x")[0] == tempfile.gettempdir() + "/x"


@windows_only
@pytest.mark.parametrize("shown", [True])
@pytest.mark.parametrize("shape", [
    'cd "{p}" && git commit -m x', 'pushd "{p}" && git commit -m x', 'git -C "{p}" commit -m x',
    '(cd "{p}"; git commit -m x)', 'cd {e} && git commit -m x', 'cd "{cyg}" && git commit -m x',
])
def test_git_bash_spelling_of_another_repository(tmp_path, hook_env, stub_api, shape, shown):
    session, other = tmp_path / "session", tmp_path / "other repo"
    for d in (session, other):
        d.mkdir()
        make_repo(d)
    _old(session)
    _, out = commit_file(other, "app.py", VULN_PY)
    drive, rest = os.path.splitdrive(_p(other))
    p = "/" + drive[0].lower() + rest
    cmd = shape.format(p=p, e=p.replace(" ", "\\ "), cyg="/cygdrive" + p)
    run_hook({**bash_payload(session, cmd, out if shown else ""), "duration_ms": 100}, hook_env)
    assert "app.py" in "".join(stub_api.bodies)


@windows_only
def test_drive_root_then_relative(tmp_path, hook_env, stub_api):
    session, other = tmp_path / "session", tmp_path / "other"
    for d in (session, other):
        d.mkdir()
        make_repo(d)
    _, out = commit_file(other, "app.py", VULN_PY)
    drive, rest = os.path.splitdrive(_p(other))
    cmd = f"cd /{drive[0].lower()} && cd {rest.lstrip('/')} && {COMMIT}"
    run_hook(bash_payload(session, cmd, out), hook_env)
    assert "app.py" in "".join(stub_api.bodies)


# --- What the first choice gets right, or leaves alone, stays so. -----------

def _metrics(repos, hook_env, command, out="", **extra):
    payload = bash_payload(repos[0], command, out)
    payload.update(extra)
    return metrics_of(run_hook(payload, hook_env)[1])


def _age_head(repo, seconds):
    """HEAD's commit and its reflog record are this old."""
    then = f"@{int(time.time()) - seconds} +0000"
    subprocess.run(["git", "commit", "-q", "--amend", "--no-edit"], cwd=repo, check=True,
                   env={**os.environ, **GIT_ENV, "GIT_COMMITTER_DATE": then})


def test_old_commit_shown_by_a_log_is_not_taken(repos, hook_env, stub_api):
    session, other = repos
    commit_file(other, "app.py", VULN_PY)
    _age_head(other, 3600)
    sha = git(other, "rev-parse", "--short", "HEAD").strip()
    out = f"[{sha}] change\n app.py | 4 ++++\n 1 file changed, 4 insertions(+)\n"
    cmd = f"git -C {_p(other)} log --format='[%h] %s' --stat -1; git commit -q -m x"
    _metrics(repos, hook_env, cmd, out, duration_ms=50)
    assert "shell=True" not in "".join(stub_api.bodies)


def test_commit_from_before_the_command_is_not_taken(repos, hook_env, stub_api):
    session, other = repos
    commit_file(other, "app.py", VULN_PY)
    _age_head(other, 400)
    git(other, "reflog", "delete", "HEAD@{1}")
    git(other, "reflog", "delete", "HEAD@{1}")
    _old(session)
    _metrics(repos, hook_env, f"if true; then cd {_p(other)}; fi; cd {_p(session)}; git commit -q -m x",
             "nothing to commit, working tree clean", duration_ms=50)
    assert "shell=True" not in "".join(stub_api.bodies)


def _untouched(repo):
    then = time.time() - 4000
    os.utime(repo / ".git" / "logs" / "HEAD", (then, then))


def test_review_of_a_named_repository_leaves_no_hint(tmp_path, hook_env, stub_api):
    ws = tmp_path / "ws"
    app, lib = ws / "app", ws / "lib"
    for d in (app, lib):
        d.mkdir(parents=True)
        make_repo(d)
    run_hook(bash_payload(ws, f"cd {_p(app)} && {COMMIT}", commit_file(app, "a.py", "x = 1\n")[1]), hook_env)
    run_hook(bash_payload(ws, f"for r in lib; do (cd $r && {COMMIT}); done", commit_file(lib, "b.py", VULN_PY)[1]),
             hook_env)
    stub_api.bodies.clear()
    commit_file(app, "app_f.py", VULN_PY)
    run_hook(bash_payload(ws, "cd $(ls -d app*) && git commit -q -m x", ""), hook_env)
    assert "app_f.py" in "".join(stub_api.bodies)


def test_one_call_outside_a_repository_is_reviewed_once(repos, hook_env, stub_api, tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    _, out = commit_file(repos[1], "app.py", VULN_PY)
    for _ in range(3):
        run_hook(bash_payload(ws, f"for d in {_p(repos[1])}; do (cd $d && {COMMIT}); done", out,
                              tool_use_id="toolu_7"), hook_env)
    assert len([b for b in stub_api.bodies if "shell=True" in b]) == 1


@pytest.mark.parametrize("p,expected", [("/", "/"), ("c:/", "c:/"), ("C:\\", "C:\\"), ("/a/", "/a"), ("a//", "a"), ("", "")])
def test_without_slash(p, expected):
    assert rr._without_slash(p) == expected


def test_nothing_is_written_in_a_repository_that_is_only_named(repos, hook_env, tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    before = sorted(p.name for p in (repos[1] / ".git").iterdir())
    cmd = f"cat > notes <<'E'\ncd {_p(repos[1])}\nE\nif cd real; then git commit -m x; fi"
    run_hook(bash_payload(ws, cmd, "[main abcdef1] x\n 1 file changed\n", tool_use_id="toolu_9"), hook_env)
    assert sorted(p.name for p in (repos[1] / ".git").iterdir()) == before


@pytest.mark.parametrize("word", ["//nas/backup", "\\\\\\\\host\\\\share", "'\\\\host\\share'"])
def test_network_paths_are_not_looked_at(repos, monkeypatch, word):
    looked = []
    real = os.path.isdir
    monkeypatch.setattr(rr.os.path, "isdir", lambda p: looked.append(str(p)) or real(p))
    list(rr.named_repos(f"git commit -m 'run cd {word}'; if cd {word}; then x; fi; if cd sub; then y; fi", str(repos[0])))
    assert looked and not [p for p in looked if p.startswith(("//", "\\\\"))]


@pytest.mark.parametrize("shape", [
    'ROOT={w}; if cd "$ROOT"/other; then {c}; fi', 'if cd "{w}"/other; then {c}; fi', 'if cd {w}/"other"; then {c}; fi',
    "if cd {w}/'oth'er; then {c}; fi", "GIT_DIR={w}/other/.git/ GIT_WORK_TREE={w}/other {c}",
    "if cd {w}/other/.git/hooks; then cd ../..; {c}; fi; cd {w}/other", 'for d in "{w}/other"; do cd "$d"; {c}; done',
    "if cd {w}/other/; then {c}; fi", "cd {w}/other/sub/.. ; {c} | cat",
])
def test_spellings_of_a_folder(repos, hook_env, stub_api, shape):
    session, other = repos
    (other / "sub").mkdir()
    _old(session)
    _, out = commit_file(other, "app.py", VULN_PY)
    _metrics(repos, hook_env, shape.format(w=_p(other.parent), c=COMMIT), out)
    assert "app.py" in "".join(stub_api.bodies)


@pytest.mark.parametrize("ms,expected", [(0, 60), (5000, 65), (None, 120), ("x", 120), (True, 120), (-1, 120)])
def test_command_started(ms, expected):
    import security_reminder_hook as h
    data = {} if ms is None else {"duration_ms": ms}
    assert abs(time.time() - h._hook_spent_s() - h._command_started(data) - expected) < 2


def test_commit_records_are_read_by_their_own_time(repos):
    _, other = repos
    now = time.time()
    sha, _ = commit_file(other, "a.py", "x = 1\n")
    assert git(other, "rev-parse", "HEAD").strip() in rr.commits_made_since(str(other), now - 5)
    assert rr.commits_made_since(str(other), now + 60) == {}
    git(other, "checkout", "-q", "-b", "b")
    assert len(rr.commits_made_since(str(other), 0)) == 2
    assert rr.commits_made_since("/nowhere/x", 0) == {}


def test_escaped_quote_in_a_folder_name(repos, hook_env, stub_api):
    session, _ = repos
    d = session.parent / "it's"
    d.mkdir()
    make_repo(d)
    _, out = commit_file(d, "app.py", VULN_PY)
    _metrics(repos, hook_env, "if cd ../it\\'s; then git commit -m x; fi", out)
    assert "app.py" in "".join(stub_api.bodies)


def test_printed_commit_under_many_records(repos, hook_env, stub_api):
    _, other = repos
    _, out = commit_file(other, "app.py", VULN_PY)
    head = git(other, "rev-parse", "HEAD").strip()
    parent = git(other, "rev-parse", "HEAD^").strip()
    for a, b in [(parent, head), (head, parent)] * 8:
        git(other, "update-ref", "-m", "rebase (pick): x", "HEAD", a, b)
    _metrics(repos, hook_env, f"if cd {_p(other)}; then {COMMIT} && git pull --rebase; fi", out)
    assert "app.py" in "".join(stub_api.bodies)


def test_command_that_also_pushes_keeps_the_first_choice(repos, hook_env, stub_api):
    """The push review leaves its commits to the commit review."""
    session, other = repos
    commit_file(session, "session_f.py", VULN_PY)
    _untouched(session)
    commit_file(other, "other_f.py", VULN_PY)
    cmd = f"if cd {_p(other)}; then git commit -q -m x; fi; cd {_p(session)}; git push"
    _metrics(repos, hook_env, cmd, "", duration_ms=50)
    assert "session_f.py" in "".join(stub_api.bodies)


def test_nothing_is_looked_at_with_commit_review_off(repos, hook_env, stub_api):
    _, other = repos
    _, out = commit_file(other, "app.py", VULN_PY)
    env = {**hook_env, "SECURITY_GUIDANCE_COMMIT_REVIEW": "off"}
    m = metrics_of(run_hook(bash_payload(repos[0], f"if cd {_p(other)}; then {COMMIT}; fi", out), env)[1])
    assert m["skip_reason"] == 32 and "repo_resolution" not in m


@pytest.mark.parametrize("cmd", [
    "for d in '{w}/a b'; do (cd \"$d\" && {c}); done", "if true; then cd \\\n  \"{w}/a b\"; {c}; fi",
    'A=a; B=" b"; C="{w}"; E=/; if cd "$C$E$A$B"; then {c}; fi',
    "for d in " + " ".join("{w}/" + "x" * 100 + str(i) for i in range(10)) + " '{w}/a b'; do (cd \"$d\" && {c}); done",
])
def test_more_spellings(tmp_path, repos, hook_env, stub_api, cmd):
    d = tmp_path / "a b"
    d.mkdir()
    make_repo(d)
    _, out = commit_file(d, "app.py", VULN_PY)
    _metrics(repos, hook_env, cmd.format(w=_p(tmp_path), c=COMMIT), out)
    assert "app.py" in "".join(stub_api.bodies)


def test_old_marks_are_swept(repos, hook_env, stub_api, tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    state = Path(hook_env["SECURITY_WARNINGS_STATE_DIR"])
    state.mkdir(exist_ok=True)
    old = state / "sg-hook-once-toolu_0-commit"
    old.write_text("")
    os.utime(old, (1, 1))
    _, out = commit_file(repos[1], "app.py", VULN_PY)
    run_hook(bash_payload(ws, f"D={_p(repos[1])}; cd $D && {COMMIT}", out, tool_use_id="toolu_8"), hook_env)
    assert not old.exists()


def test_many_spellings_of_one_folder_count_once(tmp_path):
    names = " ".join(f"svc{i}" for i in range(16))
    cmd = (f'for d in {names}; do git -C "$d" fetch; git -C $d status; git -C "${{d}}" log; git -C ${{d}} diff; done; '
           "if cd ../real; then git commit -m x; fi")
    assert "../real" in rr._named_words(cmd, time.monotonic() + 5)


def test_list_in_a_variable():
    words = rr._named_words('DIRS="a b"; for d in $DIRS "c d"; do (cd $d && git commit); done', time.monotonic() + 5)
    assert {"a", "b", "c d"} <= set(words)


@pytest.mark.parametrize("said", ["On branch main\nnothing to commit, working tree clean\n",
                                  "no changes added to commit (use \"git add\")\n",
                                  "nothing added to commit but untracked files present\n"])
@pytest.mark.parametrize("cmd", ["git -C {o} status -s; git commit -m x", "cd {s} && git commit -m x; cd {o}"])
def test_commit_that_git_did_not_make_leaves_others_alone(repos, hook_env, stub_api, said, cmd):
    session, other = repos
    _old(session)
    commit_file(other, "other_f.py", VULN_PY)
    _metrics(repos, hook_env, cmd.format(o=_p(other), s=_p(session)), said, duration_ms=600_000)
    assert "other_f.py" not in "".join(stub_api.bodies)


@pytest.mark.parametrize("command,word", [
    ("cd /d D:/x && git commit", "D:/x"), ("$repo = \"C:/x\"; Set-Location $repo; git commit -m x", "C:/x"),
    ("cd -PL /x && git commit", "/x"), ("cd -P /x", "/x"), ("Set-Location -LiteralPath /x", "/x"), ("cd -- /x", "/x"),
    ("; ".join(f"cd d{i} && make" for i in range(100)) + "; if cd ../real; then git commit; fi", "../real"),
])
def test_word_is_found(command, word):
    assert word in rr._named_words(command, time.monotonic() + 5)


@pytest.mark.parametrize("command", [
    'echo "see cd foo"; if cd {o}; then git commit -m "x"; fi', "echo 'then cd foo'; if cd {o}; then git commit -m 'x'; fi",
    "bash -c 'cd /tmp'; if cd {o}; then git commit -m 'x'; fi", "if cd {o}; then git commit -m x && git status; fi"])
def test_found_after_a_closing_quote_and_with_status(repos, hook_env, stub_api, command):
    _, out = commit_file(repos[1], "app.py", VULN_PY)
    _metrics(repos, hook_env, command.format(o=_p(repos[1])), out + "nothing to commit, working tree clean\n")
    assert "app.py" in "".join(stub_api.bodies)


def test_last_folder_of_a_long_loop(tmp_path):
    names = [f"../svc{i}" for i in range(40)]
    words = rr._named_words(f"for d in {' '.join(names)}; do cd \"$d\"; done", time.monotonic() + 5)
    assert "../svc39" in words and "../svc0" in words


@pytest.mark.parametrize("command", ["git commit -m 'run cd {o} first'", "git -C {o} log -1; git commit -m x", "cd {o} && git commit -q -m x"])
def test_without_a_printed_commit_nothing_changes(repos, hook_env, stub_api, command):
    """The session's commit failed, or is quiet: another session's fresh one is not taken."""
    commit_file(repos[1], "app.py", VULN_PY)
    first = rr.toplevel_from_command(command.format(o=_p(repos[1])), str(repos[0]), rr.COMMIT_SUBCOMMANDS, str(repos[0]))
    m = _metrics(repos, hook_env, command.format(o=_p(repos[1])), "ruff....Failed\n")
    assert m.get("repo_resolution") != rr.RES_NAMED and (first or not stub_api.bodies)


def test_findings_of_another_repository_hide_none_here(repos, hook_env, stub_api):
    session, other = repos
    stub_api.vulns = [STUB_VULN]
    _, out = commit_file(other, "app.py", VULN_PY)
    run_hook(bash_payload(session, f"if cd {_p(other)}; then {COMMIT}; fi", out, tool_use_id="toolu_a"), hook_env)
    assert stub_api.bodies
    stub_api.bodies.clear()
    _, out = commit_file(session, "app.py", VULN_PY)
    rc, _, se = run_hook(bash_payload(session, COMMIT, out, tool_use_id="toolu_b"), hook_env)
    assert rc == 2 and "PREVIOUS FINDINGS" not in "".join(stub_api.bodies)


def test_it_takes_no_hourly_slot_of_the_others(repos, hook_env, stub_api):
    session, other = repos
    env = {**hook_env, "MAX_COMMIT_REVIEWS_PER_HOUR": "1"}
    _, out = commit_file(other, "app.py", VULN_PY)
    run_hook(bash_payload(session, f"if cd {_p(other)}; then {COMMIT}; fi", out, tool_use_id="toolu_a"), env)
    _, out = commit_file(session, "mine.py", VULN_PY)
    run_hook(bash_payload(session, COMMIT, out, tool_use_id="toolu_b"), env)
    assert "mine.py" in stub_api.bodies[-1]


def test_hint_of_the_first_choice_is_kept(tmp_path, hook_env, stub_api):
    ws, app, lib = tmp_path / "ws", tmp_path / "ws" / "app", tmp_path / "ws" / "lib"
    for d in (app, lib):
        d.mkdir(parents=True)
        make_repo(d)
    _, out = commit_file(lib, "lib_f.py", VULN_PY)
    run_hook(bash_payload(ws, "cd app && if cd ../lib; then :; fi; git commit -m x", out, tool_use_id="toolu_a"), hook_env)
    assert "lib_f.py" in "".join(stub_api.bodies)
    commit_file(app, "app_f.py", VULN_PY)
    run_hook(bash_payload(ws, "cd $(ls -d app*) && git commit -q -m x", "", tool_use_id="toolu_b"), hook_env)
    assert "app_f.py" in "".join(stub_api.bodies)


def test_amended_commit_elsewhere_is_reviewed_whole(repos, hook_env, stub_api):
    session, other = repos
    commit_file(other, "vuln_f.py", VULN_PY)
    (other / "extra_f.py").write_text(VULN_PY)
    git(other, "add", ".")
    out = subprocess.run(["git", "commit", "--amend", "--no-edit"], cwd=other, env={**os.environ, **GIT_ENV},
                         capture_output=True, text=True, check=True).stdout
    _metrics(repos, hook_env, f"for d in {_p(other)}; do (cd $d && git add -A && git commit --amend --no-edit); done", out)
    assert "vuln_f.py" in "".join(stub_api.bodies)


def test_commit_shown_by_a_later_call_is_not_reviewed_again(repos, hook_env, stub_api):
    session, other = repos
    sha, out = commit_file(other, "other_f.py", VULN_PY)
    run_hook(bash_payload(session, f"cd {_p(other)} && {COMMIT}", out, tool_use_id="toolu_a"), hook_env)
    n = len(stub_api.bodies)
    run_hook(bash_payload(session, f"git commit -q -m x; git -C {_p(other)} log -1 --format='[%h] %s'",
                          out, tool_use_id="toolu_b"), hook_env)
    assert n and len(stub_api.bodies) == n


def test_failed_review_elsewhere_is_silent_and_keeps_the_notice(repos, hook_env, stub_api):
    session, other = repos
    stub_api.status = 400
    _, out = commit_file(other, "other_f.py", VULN_PY)
    rc, so, se = run_hook(bash_payload(session, f"for d in {_p(other)}; do (cd $d && {COMMIT}); done", out,
                                       tool_use_id="toolu_a"), hook_env)
    assert rc == 0 and "did not complete" not in se and metrics_of(so).get("review_failed")
    _, out = commit_file(session, "mine.py", VULN_PY)
    rc, _, se = run_hook(bash_payload(session, COMMIT, out, tool_use_id="toolu_b"), hook_env)
    assert rc == 2 and "did not complete" in se


def test_nothing_is_held_elsewhere(repos, hook_env, stub_api):
    _, other = repos
    _, out = commit_file(other, "other_f.py", VULN_PY)
    _metrics(repos, hook_env, f"if cd {_p(other)}; then {COMMIT}; fi", out)
    assert "other_f.py" in "".join(stub_api.bodies)
    assert not list((other / ".git").glob("*inflight*"))


def test_the_message_names_the_repository(repos, hook_env, stub_api):
    session, other = repos
    stub_api.vulns = [STUB_VULN]
    _, out = commit_file(other, "app.py", VULN_PY)
    rc, _, se = run_hook(bash_payload(session, f"if cd {_p(other)}; then {COMMIT}; fi", out, tool_use_id="toolu_a"), hook_env)
    assert rc == 2 and "In the repository " in se and "other" in se


def test_session_commit_found_so_is_separate_too(repos, hook_env, stub_api):
    """The same finding in the other repository, right after, is still told."""
    session, other = repos
    stub_api.vulns = [STUB_VULN]
    _, out = commit_file(session, "app.py", VULN_PY)
    run_hook(bash_payload(session, f"(cd {_p(other)} && true) && {COMMIT}", out, tool_use_id="toolu_a"), hook_env)
    _, out = commit_file(other, "app.py", VULN_PY)
    rc, so, _ = run_hook(bash_payload(session, f"cd {_p(other)} && {COMMIT}", out, tool_use_id="toolu_b"), hook_env)
    assert rc == 2 and metrics_of(so)["vulns_found"] == 1


def test_amend_in_the_session_found_so_is_whole(repos, hook_env, stub_api):
    session, other = repos
    commit_file(session, "vuln_f.py", VULN_PY)
    (session / "small_f.py").write_text(VULN_PY)
    git(session, "add", ".")
    out = subprocess.run(["git", "commit", "--amend", "--no-edit"], cwd=session, env={**os.environ, **GIT_ENV},
                         capture_output=True, text=True, check=True).stdout
    _metrics(repos, hook_env, f"(cd {_p(other)} && git status -s); git commit --amend --no-edit", out)
    assert "vuln_f.py" in "".join(stub_api.bodies)


def test_a_logs_line_is_no_commit_line(repos, hook_env, stub_api):
    session, other = repos
    sha, _ = commit_file(other, "other_f.py", VULN_PY)
    out = f"[{sha[:7]}] seed\n 1 file changed, 1 insertion(+)\n"
    _metrics(repos, hook_env, f"git -C {_p(other)} log --format='[%h] %s' --stat -1; git commit -q -m x", out)
    assert not stub_api.bodies


def test_commit_from_before_a_command_of_known_length(repos, hook_env, stub_api):
    session, other = repos
    (other / "other_f.py").write_text(VULN_PY)
    git(other, "add", ".")
    out = subprocess.run(["git", "commit", "-m", "x"], cwd=other, capture_output=True, text=True, check=True,
                         env={**os.environ, **GIT_ENV, "GIT_COMMITTER_DATE": f"@{int(time.time()) - 90} +0000"}).stdout
    _metrics(repos, hook_env, f"if cd {_p(other)}; then cat log; fi; true git commit", out, duration_ms=100)
    assert not stub_api.bodies


@pytest.mark.parametrize("mark", ["reviewed", "inflight"])
def test_commit_another_process_has_is_left_to_it(repos, hook_env, stub_api, mark, monkeypatch):
    import diffstate
    monkeypatch.setattr(diffstate, "_inflight_held", type(diffstate._inflight_held)())
    session, other = repos
    sha, out = commit_file(other, "other_f.py", VULN_PY)
    full = subprocess.run(["git", "rev-parse", "HEAD"], cwd=other, capture_output=True, text=True).stdout.strip()
    if mark == "reviewed":
        diffstate._append_reviewed_shas(str(other), [full])
    else:
        diffstate._mark_inflight(str(other), [full])
        if os.name == "nt":
            pytest.skip("no marker on native Windows")
    _metrics(repos, hook_env, f"if cd {_p(other)}; then {COMMIT}; fi", out)
    assert not stub_api.bodies


def test_repository_with_a_file_named_head(repos, hook_env, stub_api):
    _, other = repos
    (other / "HEAD").write_text("x")
    _, out = commit_file(other, "other_f.py", VULN_PY)
    _metrics(repos, hook_env, f"if cd {_p(other)}; then {COMMIT}; fi", out)
    assert "other_f.py" in "".join(stub_api.bodies)


def test_subject_is_no_record(repos):
    _, other = repos
    old = git(other, "rev-parse", "HEAD")
    old = old.strip() if isinstance(old, str) else subprocess.run(["git", "rev-parse", "HEAD"], cwd=other, capture_output=True, text=True).stdout.strip()
    subprocess.run(["git", "commit", "-q", "--allow-empty", "-m", f"x\f{old}|@{{9999999999}}|commit"], cwd=other,
                   env={**os.environ, **GIT_ENV}, check=True)
    assert rr.commits_made_since(str(other), time.time() + 1000) == {}


def test_last_of_many_repositories(tmp_path, repos, hook_env, stub_api):
    for i in range(20):
        (tmp_path / f"r{i:02}").mkdir()
        make_repo(tmp_path / f"r{i:02}")
    _, out = commit_file(tmp_path / "r19", "last_f.py", VULN_PY)
    _metrics(repos, hook_env, "for d in " + " ".join(f"../r{i:02}" for i in range(20)) + "; do (cd $d && git commit -m a); done", out)
    assert "last_f.py" in "".join(stub_api.bodies)


def test_it_is_left_to_the_push_review_where_that_takes_it(repos, hook_env, stub_api):
    sha, out = commit_file(repos[1], "both_f.py", VULN_PY)
    pushed = f"To /remote\n   1234567..{sha[:7]}  main -> main\n"
    m = _metrics(repos, hook_env, f"if cd {_p(repos[1])}; then {COMMIT}; fi; git -C {_p(repos[1])} push", out + pushed)
    assert m.get("skip_reason") == 28 and not stub_api.bodies


@pytest.mark.parametrize("after", ["", "error: failed to push some refs to '/remote'\n"])
def test_a_push_that_shows_nothing_takes_nothing(repos, hook_env, stub_api, after):
    _, out = commit_file(repos[1], "both_f.py", VULN_PY)
    _metrics(repos, hook_env, f"if cd {_p(repos[1])}; then {COMMIT}; fi; git -C {_p(repos[1])} push -q", out + after)
    assert "both_f.py" in "".join(stub_api.bodies)


def test_it_goes_there_when_the_push_is_of_another(repos, hook_env, stub_api):
    _, out = commit_file(repos[1], "both_f.py", VULN_PY)
    _metrics(repos, hook_env, f"if cd {_p(repos[1])}; then {COMMIT} && git push; fi", out)
    assert "both_f.py" in "".join(stub_api.bodies)
