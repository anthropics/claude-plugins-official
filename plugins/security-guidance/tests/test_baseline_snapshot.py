"""The turn baseline is a commit of the tracked changes (#6854), where it used
to be `git stash create`. These pin the states where the two could differ."""
import os
import subprocess

import pytest

import diffstate
import gitutil
from conftest import GIT_ENV, git, make_repo


@pytest.fixture(autouse=True)
def safe_env(monkeypatch):
    for k, v in gitutil.git_config_env(gitutil.SAFE_GIT_CONFIG).items():
        monkeypatch.setenv(k, v)


def _tree(repo, sha):
    return git(repo, "rev-parse", f"{sha}^{{tree}}").strip()


def _plain_stash_tree(repo):
    """What `git stash create` would have produced, on the real index."""
    out = subprocess.run(["git", "stash", "create"], cwd=repo, capture_output=True,
                         text=True, env={**os.environ, **GIT_ENV})
    sha = out.stdout.strip()
    return _tree(repo, sha) if sha else _tree(repo, "HEAD")


def _capture(repo):
    sha = diffstate.capture_git_baseline(str(repo))
    return sha, diffstate.last_baseline_fail


def _repo(tmp_path, name="r"):
    return make_repo(tmp_path / name, {"a.txt": "a\n", "b.txt": "b\n", "d/c.txt": "c\n"})


def test_unstaged_and_staged_changes_are_in_the_snapshot(tmp_path):
    repo = _repo(tmp_path)
    (repo / "a.txt").write_text("staged\n")
    git(repo, "add", "a.txt")
    (repo / "a.txt").write_text("staged\nunstaged\n")
    (repo / "b.txt").write_text("also dirty\n")
    sha, fail = _capture(repo)
    assert fail == 0
    assert git(repo, "show", f"{sha}:a.txt") == "staged\nunstaged\n"
    assert git(repo, "show", f"{sha}:b.txt") == "also dirty\n"
    assert git(repo, "rev-parse", f"{sha}^").strip() == git(repo, "rev-parse", "HEAD").strip()


@pytest.mark.parametrize("state", [
    "unstaged", "staged", "staged-plus-unstaged", "worktree-delete", "staged-delete",
    "staged-rename", "staged-new", "mode-change", "symlink", "untracked-only", "stale-stat",
])
def test_same_tree_as_stash_create(tmp_path, state):
    repo = _repo(tmp_path, state)
    if state == "unstaged":
        (repo / "a.txt").write_text("x\n")
    elif state == "staged":
        (repo / "a.txt").write_text("x\n"); git(repo, "add", "a.txt")
    elif state == "staged-plus-unstaged":
        (repo / "a.txt").write_text("x\n"); git(repo, "add", "a.txt")
        (repo / "a.txt").write_text("y\n")
    elif state == "worktree-delete":
        (repo / "a.txt").unlink()
    elif state == "staged-delete":
        git(repo, "rm", "-q", "a.txt")
    elif state == "staged-rename":
        git(repo, "mv", "a.txt", "z.txt")
    elif state == "staged-new":
        (repo / "n.txt").write_text("n\n"); git(repo, "add", "n.txt")
    elif state == "mode-change":
        os.chmod(repo / "a.txt", 0o755)
    elif state == "symlink":
        (repo / "a.txt").unlink(); os.symlink("b.txt", repo / "a.txt")
    elif state == "untracked-only":
        (repo / "u.txt").write_text("u\n")
    elif state == "stale-stat":
        t = os.stat(repo / "a.txt").st_mtime + 2
        os.utime(repo / "a.txt", (t, t))
    # Capture FIRST: `git stash create` refreshes the real index, which would
    # cancel the stale stat entry the last state is about.
    sha, fail = _capture(repo)
    assert fail == 0
    assert _tree(repo, sha) == _plain_stash_tree(repo)


def test_clean_tree_is_head(tmp_path):
    repo = _repo(tmp_path)
    assert _capture(repo) == (git(repo, "rev-parse", "HEAD").strip(), 0)


def test_conflicted_merge_snapshots_the_conflicted_files(tmp_path):
    """`stash create` refused here and the whole conflicted file was then
    reviewed as the turn's work. `add -u` resolves the conflict in the index
    COPY, so the baseline holds what the work tree had, markers and all, and
    the user's own index keeps its unmerged entries."""
    repo = _repo(tmp_path)
    git(repo, "checkout", "-q", "-b", "other")
    (repo / "a.txt").write_text("theirs\n"); git(repo, "commit", "-qam", "theirs")
    git(repo, "checkout", "-q", "main")
    (repo / "a.txt").write_text("ours\n"); git(repo, "commit", "-qam", "ours")
    subprocess.run(["git", "merge", "other"], cwd=repo, capture_output=True,
                   env={**os.environ, **GIT_ENV})
    assert "UU" in git(repo, "status", "--porcelain")
    conflicted = (repo / "a.txt").read_text()
    sha, fail = _capture(repo)
    assert fail == 0
    assert git(repo, "show", f"{sha}:a.txt") == conflicted
    assert "UU" in git(repo, "status", "--porcelain")
    assert git(repo, "ls-files", "-u")


def test_intent_to_add_file_is_snapshotted_with_its_content(tmp_path):
    """`git add -N` marks a file to be committed without staging content.
    `stash create` refused on such an index and the baseline fell back to
    HEAD, so the file's pre-existing content was reviewed as the turn's work.
    The snapshot holds that content, so only what the turn changes is."""
    repo = _repo(tmp_path)
    (repo / "n.txt").write_text("secret = 1\n")
    git(repo, "add", "-N", "n.txt")
    sha, fail = _capture(repo)
    assert fail == 0
    assert sha != git(repo, "rev-parse", "HEAD").strip()
    assert git(repo, "show", f"{sha}:n.txt") == "secret = 1\n"
    # The path is still named in the review set, as it was before, but its
    # content is in the baseline now, so the reviewer is sent nothing for it
    # where `stash create` failing sent the whole file.


def test_subdirectory_cwd_snapshots_the_whole_tree(tmp_path):
    repo = _repo(tmp_path)
    (repo / "a.txt").write_text("top changed\n")
    (repo / "d" / "c.txt").write_text("below changed\n")
    sha, fail = _capture(repo / "d")
    assert fail == 0
    assert git(repo, "show", f"{sha}:a.txt") == "top changed\n"
    assert git(repo, "show", f"{sha}:d/c.txt") == "below changed\n"


def test_nested_repository_stays_out_of_the_snapshot(tmp_path):
    """A directory with its own .git is another repository: #6837 keeps its
    gitlink out of the index copy, so it must stay out of the tree too."""
    repo = _repo(tmp_path)
    nested = repo / "vendor"
    make_repo(nested, {"x.txt": "x\n"})
    git(repo, "add", "vendor")
    git(repo, "commit", "-qm", "add nested")
    (nested / "x.txt").write_text("changed inside\n")
    (repo / "a.txt").write_text("changed outside\n")
    sha, fail = _capture(repo)
    assert fail == 0
    assert git(repo, "show", f"{sha}:a.txt") == "changed outside\n"
    assert "vendor" not in git(repo, "ls-tree", "--name-only", sha)


def test_clean_tree_with_a_nested_repository_is_head(tmp_path):
    """The index copy has no gitlink, so its tree can never equal HEAD's.
    Without a second look that would mint a commit object on every prompt in
    a repo with submodules, and the baseline would be a prunable dangling
    commit instead of HEAD."""
    repo = _repo(tmp_path)
    make_repo(repo / "vendor", {"x.txt": "x\n"})
    git(repo, "add", "vendor")
    git(repo, "commit", "-qm", "add nested")
    head = git(repo, "rev-parse", "HEAD").strip()
    assert _capture(repo) == (head, 0)

    # A change inside the nested repository is still not this repo's work.
    (repo / "vendor" / "x.txt").write_text("changed inside\n")
    assert _capture(repo) == (head, 0)

    # A real change outside it still gets a snapshot.
    (repo / "a.txt").write_text("changed outside\n")
    sha, fail = _capture(repo)
    assert fail == 0 and sha != head
    assert git(repo, "show", f"{sha}:a.txt") == "changed outside\n"


def test_snapshot_leaves_the_real_index_and_worktree_alone(tmp_path):
    repo = _repo(tmp_path)
    (repo / "a.txt").write_text("dirty\n")
    before_index = (repo / ".git" / "index").read_bytes()
    before_status = git(repo, "status", "--porcelain")
    before_stash = git(repo, "stash", "list")
    _capture(repo)
    assert (repo / ".git" / "index").read_bytes() == before_index
    assert git(repo, "status", "--porcelain") == before_status
    assert git(repo, "stash", "list") == before_stash
    assert [p for p in os.listdir(repo / ".git") if p.startswith("index.")] == []


def test_snapshot_commit_is_unreferenced(tmp_path):
    repo = _repo(tmp_path)
    (repo / "a.txt").write_text("dirty\n")
    sha, _ = _capture(repo)
    assert sha not in git(repo, "log", "--all", "--format=%H")
    assert git(repo, "rev-parse", "HEAD").strip() != sha


def test_partial_clone_snapshots_without_fetching(tmp_path):
    """A blobless clone has no blob for an unchanged file. git counts a
    promisor object as present, so write-tree neither fetches nor fails;
    this pins that, since the snapshot must never make a network call."""
    origin = _repo(tmp_path, "origin")
    git(origin, "config", "uploadpack.allowFilter", "true")
    for i in range(3):
        (origin / f"big{i}.txt").write_text(f"content {i}\n")
    git(origin, "add", "-A")
    git(origin, "commit", "-qm", "more")
    clone = tmp_path / "clone"
    subprocess.run(["git", "clone", "-q", "--filter=blob:none", "--no-local",
                    str(origin), str(clone)], check=True, capture_output=True,
                   env={**os.environ, **GIT_ENV})
    # Nothing can be fetched from here on: a snapshot that tried would fail.
    git(clone, "config", "remote.origin.url", "/nonexistent-origin")
    (clone / "a.txt").write_text("dirty\n")
    sha, fail = _capture(clone)
    assert fail == 0 and sha
    assert git(clone, "show", f"{sha}:a.txt") == "dirty\n"


def test_literal_pathspecs_in_the_environment(tmp_path, monkeypatch):
    """A user who exports GIT_LITERAL_PATHSPECS gets it in the hook's
    environment, and a magic pathspec would then fail outright and drop the
    baseline to HEAD on every prompt of the session."""
    repo = _repo(tmp_path)
    monkeypatch.setenv("GIT_LITERAL_PATHSPECS", "1")
    (repo / "a.txt").write_text("dirty\n")
    sha, fail = _capture(repo)
    assert fail == 0
    assert git(repo, "show", f"{sha}:a.txt") == "dirty\n"


def test_no_identity_configured_still_snapshots(tmp_path, monkeypatch):
    repo = _repo(tmp_path)
    (repo / "a.txt").write_text("dirty\n")
    for var in ("GIT_AUTHOR_NAME", "GIT_AUTHOR_EMAIL",
                "GIT_COMMITTER_NAME", "GIT_COMMITTER_EMAIL", "EMAIL"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_SYSTEM", os.devnull)
    sha, fail = _capture(repo)
    assert fail == 0 and sha
    assert "security-guidance" in git(repo, "show", "-s", "--format=%an", sha)


def test_signing_configured_does_not_sign_the_snapshot(tmp_path):
    repo = _repo(tmp_path)
    git(repo, "config", "commit.gpgsign", "true")
    git(repo, "config", "gpg.program", "/nonexistent-gpg")
    (repo / "a.txt").write_text("dirty\n")
    sha, fail = _capture(repo)
    assert fail == 0 and sha
    assert git(repo, "show", "-s", "--format=%G?", sha).strip() in ("N", "")
