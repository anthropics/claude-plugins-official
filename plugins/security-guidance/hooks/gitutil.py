"""
Leaf git/subprocess helpers and diff parsing for the security-guidance plugin.

Everything here is a thin wrapper over ``git``/``subprocess`` plus pure
diff-text parsing and source-file classification. None of these functions
reference any name that the test suite monkeypatches on
``security_reminder_hook`` and then calls *through* another function in this
module — that property is what makes them safe to live in their own module
while still being re-exported (so tests that patch ``hook._git_toplevel`` and
then call a handler in ``security_reminder_hook`` continue to see the patched
binding).

Functions that DO compose patched leaves (``compute_v2_review_set``,
``_list_untracked``, ``_append_reviewed_shas``) deliberately remain in
``security_reminder_hook.py`` for that reason.
"""
import contextlib
import errno
import os
import re
import subprocess
import sys
import tempfile
import threading
import time

from _base import debug_log


GIT_CMD = [
    "git",
    "-c", "core.fsmonitor=false",
    "-c", "core.hooksPath=/dev/null",
    # core.quotePath=false: emit raw UTF-8 in path-emitting commands instead
    # of C-quoting non-ASCII bytes (default `"\\303\\201vila/..."` vs
    # `Ávila/...`). Downstream parsers — both ours (parse_diff_into_files,
    # extract_file_paths_from_diff) and Python stdlib (os.path.isabs,
    # os.path.join) — expect raw paths and silently drop / mishandle the
    # quoted form. Adding the flag globally to GIT_CMD covers every
    # subprocess.run site that uses the splat — diff feeders, rev-parse
    # path queries (--show-toplevel, --git-dir, --git-common-dir),
    # reflog %gs subjects, ls-files, status, etc. — without per-site
    # flag duplication. See #2082, #2099.
    "-c", "core.quotePath=false",
    # A work-tree `git diff` that meets stat-stale entries (mtime changed,
    # content same) rewrites the index under index.lock, GIT_OPTIONAL_LOCKS or
    # not. Off, every diff here only reads the index, so none needs a copy.
    "-c", "diff.autoRefreshIndex=false",
    # The diff parsers read `diff --git a/<old> b/<new>` headers. A user's
    # diff.mnemonicPrefix (c/ w/ i/), diff.noprefix or diff.srcPrefix /
    # diff.dstPrefix changes that shape, and every file would be dropped.
    "-c", "diff.mnemonicPrefix=false",
    "-c", "diff.noprefix=false",
    "-c", "diff.srcPrefix=a/",
    "-c", "diff.dstPrefix=b/",
    # A directory with its own `.git` inside the work tree (a submodule, a
    # vendored checkout, an unpacked archive) is another repository with its
    # own config. To report it as modified, or to show its changes inline
    # (diff.submodule=diff), git starts a second git inside it, which reads
    # that config and runs the commands it names. Such a directory is left
    # out of the review set, and so is a commit that moves one. See also
    # _drop_gitlinks for the commands that take no such setting.
    "-c", "diff.ignoreSubmodules=all",
    "-c", "diff.submodule=short",
]

# diff.ignoreSubmodules is a default that the repository's own settings for
# one submodule (.gitmodules, submodule.<name>.ignore) override. The option
# cannot be overridden. Pass it to every `git status` and work-tree `git diff`.
IGNORE_SUBMODULES = "--ignore-submodules=all"

SAFE_GIT_CONFIG = (
    ("core.fsmonitor", "false"),
    ("core.hooksPath", "/dev/null"),
    ("diff.ignoreSubmodules", "all"),
    ("diff.submodule", "short"),
)

# The hook's git runs in the background beside the session's own git. Without
# this, `git status` holds .git/index.lock while it writes back a refreshed
# index: a concurrent `git add` fails, and a timeout kill leaves the lock.
SAFE_GIT_ENV = {
    "GIT_OPTIONAL_LOCKS": "0",
}


def git_config_env(pairs, base=None):
    base = os.environ if base is None else base
    try:
        n = max(0, int(base.get("GIT_CONFIG_COUNT") or 0))
    except (TypeError, ValueError):
        n = 0
    env = {}
    for i, (k, v) in enumerate(pairs, start=n):
        env[f"GIT_CONFIG_KEY_{i}"] = k
        env[f"GIT_CONFIG_VALUE_{i}"] = v
    env["GIT_CONFIG_COUNT"] = str(n + len(pairs))
    return env


def apply_safe_git_env():
    os.environ.update(git_config_env(SAFE_GIT_CONFIG))
    os.environ.update(SAFE_GIT_ENV)


def _git_rev_parse_head(cwd):
    """Return the current HEAD SHA, or None if not a git repo / no commits."""
    try:
        # See #2099: text=True on Windows cp1252 crashes the reader thread on
        # any UTF-8 byte undefined in cp1252 (e.g. via a git error message
        # referencing a non-ASCII filename in stderr). stdout is a SHA so it
        # IS safe; stderr is not. capture_output=True with bytes-by-default
        # never decodes, so the reader thread can't crash.
        result = subprocess.run(
            [*GIT_CMD, "rev-parse", "HEAD"],
            cwd=cwd, capture_output=True, timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.decode("utf-8", errors="replace").strip()
        return None
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return None




def _find_git_index(cwd):
    """
    Find the real index file for a git repo. Handles worktrees where .git
    is a file pointing to the main repo's gitdir.
    Returns the absolute path to the index file, or None.
    """
    try:
        # See #2099: stdout here is a PATH which can contain non-ASCII bytes
        # (e.g. C:\אבטחה\repo\.git). text=True decodes via cp1252 strict on
        # Windows → crashes the reader thread → returns stdout=None →
        # caller does .strip() on None → AttributeError. Decode manually.
        result = subprocess.run(
            [*GIT_CMD, "rev-parse", "--git-dir"],
            cwd=cwd, capture_output=True, timeout=5
        )
        if result.returncode != 0:
            return None
        git_dir = result.stdout.decode("utf-8", errors="replace").strip()
        if not os.path.isabs(git_dir):
            git_dir = os.path.join(cwd, git_dir)
        index_path = os.path.join(git_dir, "index")
        return index_path if os.path.isfile(index_path) else None
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return None


def _find_git_index_and_top(cwd):
    """_find_git_index plus the work tree's top directory, from one git
    call. (None, None) when either is missing: no index file, a bare
    repository, or a `cwd` inside the git directory."""
    try:
        result = subprocess.run(
            [*GIT_CMD, "rev-parse", "--git-dir", "--show-toplevel"],
            cwd=cwd, capture_output=True, timeout=5
        )
        if result.returncode != 0:
            return None, None
        # Paths as bytes from git: decode by hand (see _find_git_index).
        out = result.stdout.decode("utf-8", errors="replace")
        parts = out[:-1].split("\n") if out.endswith("\n") else []
        if len(parts) != 2 or not all(parts):
            # A newline in one of the paths: ask for them one at a time.
            index_path, top = _find_git_index(cwd), _git_toplevel(cwd)
            return (index_path, top) if index_path and top else (None, None)
        git_dir, top = parts
        if not os.path.isabs(git_dir):
            git_dir = os.path.join(cwd, git_dir)
        index_path = os.path.join(git_dir, "index")
        if not os.path.isfile(index_path):
            return None, None
        return index_path, top
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return None, None


def _diff_pathspec(cwd, paths):
    """Convert absolute touched-paths to repo-relative pathspec args for
    git diff. Paths outside cwd (e.g. ~/.claude/…) are dropped. Returns the
    list to splice after `--`, or [] for an unrestricted diff. realpath both
    sides so the macOS /var ↔ /private/var symlink doesn't make in-repo
    paths look external."""
    if not paths:
        return []
    cwd_abs = os.path.realpath(cwd)
    rel = []
    for p in paths:
        try:
            r = os.path.relpath(os.path.realpath(p), cwd_abs)
        except ValueError:
            continue
        if r.startswith(".."):
            continue
        rel.append(r)
    return ["--"] + rel if rel else []


# Bytes of file paths per git call once a path list has proved too long for
# one command. Windows caps a whole command line at 32,767 characters;
# elsewhere the limit is about 1 MB (macOS) or 2 MB (Linux), environment
# included.
_MAX_PATH_ARGS_BYTES = (
    20000 if sys.platform in ("win32", "cygwin", "msys") else 500000)
# More commands than this and the path list is not worth diffing: each one
# matches its paths against the whole index, and a set that large is thrown
# away as pathological after the diff anyway.
_MAX_PATH_BATCHES = 4


def _arg_cost(path):
    # The exec limit also counts a terminator and a pointer per argument.
    return len(os.fsencode(path)) + 9


def _path_args_budget(env=None):
    """_MAX_PATH_ARGS_BYTES, or less where this system's own limit is lower
    (a small stack limit, a BSD, a very large environment). Half of what the
    system leaves after the environment, so the rest of the command fits."""
    try:
        arg_max = os.sysconf("SC_ARG_MAX")
    except (AttributeError, ValueError, OSError):
        return _MAX_PATH_ARGS_BYTES
    env_bytes = sum(len(k) + len(v) + 2 for k, v in (env or os.environ).items())
    return min(_MAX_PATH_ARGS_BYTES, max(4096, (arg_max - env_bytes) // 2))


def _path_batches(paths, budget=None):
    if budget is None:
        budget = _MAX_PATH_ARGS_BYTES
    batch, size = [], 0
    for p in paths:
        n = _arg_cost(p)
        if batch and size + n > budget:
            yield batch
            batch, size = [], 0
        batch.append(p)
        size += n
    if batch:
        yield batch


# Why a path list too long for one command left the last get_git_diff call
# without a diff, for the Stop review's skip reason: "gave_up" (still too
# long once cut down) or "none_reviewable".
_path_list_too_long = set()


def _too_many_args(e):
    """The OS refused to start the command because its arguments are too
    long. Windows reports ERROR_FILENAME_EXCED_RANGE, which Python turns into
    a FileNotFoundError."""
    return e.errno == errno.E2BIG or getattr(e, "winerror", None) == 206


def _run_captured(cmd, timeout, **kwargs):
    return subprocess.run(cmd, capture_output=True, timeout=timeout, **kwargs)


def _run_git_on_review_paths(args, paths, timeout, run=_run_captured, **kwargs):
    """Run `git <args> -- <paths>` for the Stop review; return the results.
    `run(cmd, timeout, **kwargs)` starts each command (_run_diff_bounded for
    the diff, so its output is never held whole).

    One command with every path whenever the OS takes it. When the OS refuses
    the argument list as too long, only reviewable source paths are kept (the
    review drops the rest from the diff anyway) and they go out in as few
    commands as they need, all within `timeout` seconds together. If even
    those need more than _MAX_PATH_BATCHES commands, the refusal is raised
    again.

    Secret-shaped paths that are gone from the work tree go into every one
    of those commands: `git diff` must still pair a rename away from such a
    name, or the secret's content would show as a new source file. A new file
    that only resembles the secret may be paired with it too and left out of
    the review. Any other rename is paired only when both of its paths are
    reviewable source and in the same command; otherwise it shows as a delete
    or an add.
    """
    cmd = [*GIT_CMD, *args, "--"]
    paths = list(paths)
    deadline = time.monotonic() + timeout
    try:
        return [run(cmd + paths, timeout, **kwargs)]
    except OSError as e:
        if not _too_many_args(e):
            raise
        too_long = e
    budget = _path_args_budget(kwargs.get("env"))
    batches = list(_path_batches(
        [p for p in paths if _is_reviewable_source(p)], budget))
    root = kwargs.get("cwd") or os.getcwd()
    secret = [p for p in paths if _is_secret_shaped(p)
              and not os.path.lexists(os.path.join(root, p))]
    debug_log(f"git {args[0]}: {len(paths)} paths do not fit one command; "
              f"{len(batches)} command(s) for the reviewable ones")
    # The secret-shaped paths ride along with every batch, so they get a
    # small share of a command of their own.
    if (len(batches) > _MAX_PATH_BATCHES
            or sum(map(_arg_cost, secret)) > budget // 4):
        raise too_long
    cmd += secret
    results = []
    for batch in batches:
        left = deadline - time.monotonic()
        if left <= 0:
            raise subprocess.TimeoutExpired(cmd, timeout)
        results.append(run(cmd + batch, left, **kwargs))
    return results


_TEMP_INDEX_PREFIX = "security_hook_idx_"
# A copy is named <prefix>pid<hook pid>_<8 random chars>, so a later run can
# tell that the hook which made it is gone. Names from earlier releases have
# only the 8 random characters and never match.
_OWNER_PID = re.compile(re.escape(_TEMP_INDEX_PREFIX) + r"pid(\d+)_[^.]{8}(?:\.|$)")
# A live copy is in use for under a minute (a couple of bounded git calls), so
# anything this old belongs to a run that was killed.
_TEMP_INDEX_STALE_S = 1800
# Unlinking index-sized files is slow; a large backlog drains over several
# calls instead of stalling one hook past its timeout.
_SWEEP_BUDGET_S = 2


def _owner_is_gone(name):
    """True when `name` records the pid of the hook that made it and no such
    process exists. A reused pid reads as alive: the file then waits for the
    age limit. Never probes on Windows, where os.kill would end the process."""
    if not hasattr(os, "getuid"):
        return False
    m = _OWNER_PID.match(name)
    if not m:
        return False
    try:
        os.kill(int(m.group(1)), 0)
    except ProcessLookupError:
        return True
    except (OSError, OverflowError, ValueError):
        return False
    return False


def _sweep_stale_indexes(dirpath, uid):
    """Delete index copies in `dirpath` that a killed run left behind. Only
    regular files owned by `uid` (None: no ownership check) are touched.

    A copy goes as soon as the hook that made it is gone: a killed hook can
    leave one per run, and index-sized files fill a disk long before the age
    limit. The age limit covers names without a pid and reused pids.

    Age is the newer of mtime and ctime: a copy keeps .git/index's mtime,
    which may be days old, so mtime alone would delete a file that another
    running hook is still using."""
    import stat
    import time
    cutoff = time.time() - _TEMP_INDEX_STALE_S
    deadline = time.monotonic() + _SWEEP_BUDGET_S
    try:
        names = os.listdir(dirpath)
    except OSError:
        return
    for name in names:
        if not name.startswith(_TEMP_INDEX_PREFIX):
            continue
        p = os.path.join(dirpath, name)
        try:
            st = os.lstat(p)
            if not stat.S_ISREG(st.st_mode):
                continue
            if uid is not None and st.st_uid != uid:
                continue
            if max(st.st_mtime, st.st_ctime) < cutoff or _owner_is_gone(name):
                os.unlink(p)
                if time.monotonic() > deadline:
                    return
        except OSError:
            pass


def _sweep_stale_stash_indexes(real_index):
    """Delete `<index>.stash.<pid>` files a killed `git stash create` left
    next to the real index. Releases before 2.0.10 ran it there, so a clone
    can hold hundreds, each the size of the index, and nothing else removes
    them. Only our own regular files past the age limit go: git keeps one for
    seconds. `index.lock` is never touched; a live git may hold it."""
    import stat
    import time
    uid = os.getuid() if hasattr(os, "getuid") else None
    cutoff = time.time() - _TEMP_INDEX_STALE_S
    deadline = time.monotonic() + _SWEEP_BUDGET_S
    dirpath = os.path.dirname(real_index)
    stale = re.compile(re.escape(os.path.basename(real_index)) + r"\.stash\.\d+$")
    try:
        names = os.listdir(dirpath)
    except OSError:
        return
    for name in names:
        if not stale.match(name):
            continue
        p = os.path.join(dirpath, name)
        try:
            st = os.lstat(p)
            if not stat.S_ISREG(st.st_mode):
                continue
            if uid is not None and st.st_uid != uid:
                continue
            if max(st.st_mtime, st.st_ctime) < cutoff:
                os.unlink(p)
                if time.monotonic() > deadline:
                    return
        except OSError:
            pass


# Index copies this process has made and not yet removed.
_live_copies = set()

# A hook working on a copy needs up to three times the index's size for a
# moment (the copy, and git's rewrite and stash index next to it). With many
# agents in one clone that alone can fill a disk, so only so many hooks per
# user work on a copy at once; the others wait, then go without.
_MAX_LIVE_COPIES = 8
_SLOT_WAIT_S = 5


def _copy_slots(tmpdir, index_bytes):
    """How many hooks may work on a copy at once: what fits into a quarter of
    the free space at three times the index each, from 1 to
    _MAX_LIVE_COPIES."""
    import shutil
    try:
        free = shutil.disk_usage(tmpdir).free
    except OSError:
        return 1
    return max(1, min(_MAX_LIVE_COPIES, free // (12 * max(index_bytes, 1))))


@contextlib.contextmanager
def _copy_slot(tmpdir, index_bytes=0):
    """Hold one of the copy slots; yields False when none came free in
    _SLOT_WAIT_S. A slot is an flock, so the kernel frees it when its holder
    dies, however it dies. No cap without flock or a private dir."""
    import time
    try:
        import fcntl
    except ImportError:
        fcntl = None
    if fcntl is None or tmpdir is None:
        yield True
        return
    deadline = time.monotonic() + _SLOT_WAIT_S
    held = None
    while held is None:
        for i in range(_copy_slots(tmpdir, index_bytes)):
            try:
                fd = os.open(os.path.join(tmpdir, f"slot{i}.lock"),
                             os.O_RDWR | os.O_CREAT, 0o600)
            except OSError:
                continue
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                held = fd
                break
            except OSError:
                os.close(fd)
        if held is None:
            if time.monotonic() >= deadline:
                break
            time.sleep(0.1)
    try:
        yield held is not None
    finally:
        if held is not None:
            os.close(held)


def _remove_copy(tmp_index):
    """Remove an index copy and the files git wrote next to it."""
    import glob
    for p in glob.glob(glob.escape(tmp_index) + "*"):
        try:
            os.unlink(p)
        except OSError:
            pass


def remove_copies_on_termination():
    """Remove this process's index copies when it is told to terminate.
    Python's default SIGTERM action ends the process without running
    `finally`, which left an index-sized file behind each time."""
    import signal

    def _on_term(signum, _frame):
        for tmp_index in list(_live_copies):
            _remove_copy(tmp_index)
        os._exit(128 + signum)

    try:
        signal.signal(signal.SIGTERM, _on_term)
    except (ValueError, OSError, AttributeError):
        pass  # not the main thread, or no SIGTERM here


def _hook_tmpdir():
    """Private per-user directory for throwaway index copies, or None to use
    the bare temp dir.

    An index copy can be hundreds of MB and a killed hook cannot clean up, so
    copies live in one 0700 directory and anything stale is swept on entry,
    here and in the bare temp dir. The name is predictable and the temp dir
    may be shared, so anything that is not a real directory we own is
    refused. Windows has no uid and its temp dir is already per-user."""
    import stat
    import tempfile
    base = tempfile.gettempdir()
    uid = os.getuid() if hasattr(os, "getuid") else None
    _sweep_stale_indexes(base, uid)
    if uid is None:
        return None
    d = os.path.join(base, f"claude-security-guidance-{uid}")
    try:
        os.mkdir(d, 0o700)
    except FileExistsError:
        pass
    except OSError:
        return None
    try:
        st = os.lstat(d)
    except OSError:
        return None
    if not stat.S_ISDIR(st.st_mode) or st.st_uid != uid:
        return None
    try:
        os.chmod(d, 0o700)
    except OSError:
        pass
    _sweep_stale_indexes(d, uid)
    return d


@contextlib.contextmanager
def _temp_index(cwd, untracked_paths=None):
    """Yield an env dict pointing GIT_INDEX_FILE at a throwaway copy of the
    repo's index with `git add --intent-to-add` applied, so untracked files
    show up in subsequent `git diff` calls without touching the user's real
    index. The copy has no gitlink entry for a nested repository (see
    _drop_gitlinks). Yields None if no index can be found (bare repo / not a
    repo), no copy slot came free, or those entries could not be removed.
    Callers then go on without the copy: the diff reads the real index, and
    the baseline falls back to HEAD. Always cleans up the temp file.

    Perf: when `untracked_paths` is given, only those paths are added (O(n)
    in untracked count). The default `add -N .` stats every file in the
    worktree — slow in large repos vs fast targeted scan. v2 callers
    already know the untracked set from `git status --porcelain`, so they
    pass it; v1 keeps the whole-tree scan since it has no prior list.

    Cleanup removes `<tmp_index>*`, not just the copy: git writes
    `<index>.lock` and `<index>.stash.<pid>` next to the index it is given and
    cannot remove them itself when a subprocess timeout kills it."""
    real_index, top = _find_git_index_and_top(cwd)
    if not real_index:
        yield None
        return

    _sweep_stale_stash_indexes(real_index)
    tmpdir = _hook_tmpdir()
    try:
        index_bytes = os.path.getsize(real_index)
    except OSError:
        index_bytes = 0
    with _copy_slot(tmpdir, index_bytes) as got_slot:
        if not got_slot:
            debug_log("no index copy slot came free; going without a copy")
            yield None
            return
        with _copied_index(cwd, top, real_index, tmpdir, untracked_paths) as env:
            yield env


@contextlib.contextmanager
def _copied_index(cwd, top, real_index, tmpdir, untracked_paths):
    import shutil
    import tempfile

    tmp_fd, tmp_index = tempfile.mkstemp(
        prefix=f"{_TEMP_INDEX_PREFIX}pid{os.getpid()}_", dir=tmpdir)
    os.close(tmp_fd)
    _live_copies.add(tmp_index)
    try:
        # A hard link where the filesystem allows it: no bytes are copied, and
        # git never writes an index in place (it renames a new file over it),
        # so the real index cannot change through the link. Either way the
        # copy must keep .git/index's mtime (copy2, not copyfile): git
        # re-reads any file whose mtime is not older than the index file's,
        # and with a fresh mtime it would miss a same-size edit made in the
        # same second as the last index write.
        try:
            os.unlink(tmp_index)
            os.link(real_index, tmp_index)
        except (OSError, NotImplementedError, AttributeError):
            shutil.copy2(real_index, tmp_index)
        env = {**os.environ, "GIT_INDEX_FILE": tmp_index}
        # Before `git add` runs, since add reads the gitlinks its paths cover.
        if not _drop_gitlinks(top, env, tmp_index):
            debug_log("could not remove gitlinks from the index copy; going on "
                      "without the copy")
            yield None
            return
        if untracked_paths is None:
            add_args = ["."]
        elif untracked_paths:
            # `git add -N -- a b nonexistent` is atomic — one missing path
            # makes it exit 128 and add NOTHING, so a file removed between
            # `git status` and here would silently drop ALL untracked files
            # from the diff. --ignore-missing only works with --dry-run, so
            # filter to surviving paths (lexists so dangling symlinks count).
            # A nested repository (`dir/`) would be added as a submodule
            # entry; see diff.ignoreSubmodules in GIT_CMD.
            surviving = [p for p in untracked_paths
                         if not p.endswith("/")
                         and os.path.lexists(os.path.join(cwd, p))]
            add_args = surviving or None
        else:
            add_args = None
        if add_args:
            # No stdout used here (only returncode matters), but text=True
            # still spawns reader threads that decode stderr — git error
            # messages can reference non-ASCII filenames and crash on
            # cp1252. See #2099. Drop text=True so bytes stay raw.
            _run_git_on_review_paths(
                ["add", "--intent-to-add"], add_args, timeout=10, cwd=cwd,
                # The paths are file names, not patterns, for this git add
                # only: an untracked file named `:(glob)**` must add only
                # itself.
                env={**env, "GIT_LITERAL_PATHSPECS": "1"})
            # A whole-tree add puts a nested repository back.
            if untracked_paths is None and not _drop_gitlinks(top, env, tmp_index):
                yield None
                return
        yield env
    finally:
        _remove_copy(tmp_index)
        _live_copies.discard(tmp_index)


# An index entry stores its mode as four bytes; this is a gitlink's.
_GITLINK_MODE = b"\x00\x00\xe0\x00"
# Signature of the index extension that says most entries are in a second,
# shared file (core.splitIndex).
_SPLIT_INDEX_EXT = b"link"


def _may_have_gitlinks(index_path):
    """False only when the index file at `index_path` cannot hold a gitlink
    entry: neither a gitlink's mode bytes nor the split-index signature occur
    anywhere in it. Either can occur by chance (in an object id, a file
    size, a path), so True means "list the entries and see". Most
    repositories have no gitlink, and for them this saves a git process on
    every index copy."""
    keep = max(len(_GITLINK_MODE), len(_SPLIT_INDEX_EXT)) - 1
    try:
        with open(index_path, "rb") as f:
            tail = b""
            while True:
                chunk = f.read(1 << 20)
                if not chunk:
                    return False
                data = tail + chunk
                if _GITLINK_MODE in data or _SPLIT_INDEX_EXT in data:
                    return True
                tail = data[-keep:]
    except OSError:
        return True


_GITLINK_LIST_TIMEOUT = 10
# `git ls-files --sparse` (git 2.35) lists a sparse index as it is stored;
# without it git first expands the index to every path in the repository.
# Set to False once this git has refused the option.
_ls_files_sparse = True


def _gitlink_paths(top, env):
    """Paths (bytes, relative to `top`) of the gitlink entries, at any depth,
    in the index `env` names. None if they could not be listed. The listing
    is read as it comes, so a large index costs time but not memory."""
    global _ls_files_sparse
    cmd = [*GIT_CMD, "ls-files", "-s", "-z"] + (["--sparse"] if _ls_files_sparse else [])
    p = subprocess.Popen(cmd, cwd=top, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, env=env)
    killer = threading.Timer(_GITLINK_LIST_TIMEOUT, p.kill)
    killer.daemon = True
    found = set()
    tail = b""
    try:
        killer.start()
        while True:
            chunk = p.stdout.read1(65536)
            if not chunk:
                break
            data = tail + chunk
            end = data.rfind(b"\0") + 1
            # "<mode> <object> <stage>\t<path>", NUL-terminated. Most chunks
            # have no gitlink and are not split up.
            if b"160000 " in data:
                for rec in data[:end].split(b"\0"):
                    if rec.startswith(b"160000 "):
                        found.add(rec.split(b"\t", 1)[1])
            tail = data[end:]
        rc = p.wait()
    finally:
        killer.cancel()
        if p.poll() is None:
            p.kill()
            p.wait()
        p.stdout.close()
    if rc == 129 and _ls_files_sparse:
        # Usage error: a git without --sparse.
        _ls_files_sparse = False
        return _gitlink_paths(top, env)
    if rc != 0:
        debug_log(f"git ls-files on the index copy failed (rc={rc})")
        return None
    return found


def _drop_gitlinks(top, env, tmp_index):
    """Remove the gitlink (mode 160000) entry of every nested repository from
    the index copy that `env` names, never from the real index, before
    anything else runs on the copy. A gitlink marks a directory that is, or
    can be, another repository (see diff.ignoreSubmodules in GIT_CMD):
    `git stash create` takes no flag like IGNORE_SUBMODULES, and `git add`
    reads the gitlinks its paths cover. An entry whose directory has no
    `.git` stays: git starts nothing there, and without the entry an older
    `git stash create` fails on the empty directory. `top` is the work
    tree's top directory. Returns True on success, False on any failure; the
    copy must not be used then."""
    try:
        if not _may_have_gitlinks(tmp_index):
            return True
        gitlinks = _gitlink_paths(top, env)
        if gitlinks is None:
            return False
        top_b = os.fsencode(top)
        nested = sorted(p for p in gitlinks
                        if os.path.lexists(os.path.join(top_b, p, b".git")))
        if not nested:
            return True
        mtime_ns = os.stat(tmp_index).st_mtime_ns
        # git writes a new file and renames it over the copy, so a copy that
        # is a hard link to the real index leaves the real one as it was.
        rm = subprocess.run(
            [*GIT_CMD, "update-index", "--force-remove", "-z", "--stdin"],
            cwd=top, input=b"".join(p + b"\0" for p in nested),
            capture_output=True, timeout=10, env=env)
        if rm.returncode != 0:
            debug_log(f"git update-index on the index copy failed (rc={rm.returncode}): "
                      f"{rm.stderr[:200].decode('utf-8', errors='replace')}")
            return False
        # Keep the mtime the copy came with; see _copied_index.
        os.utime(tmp_index, ns=(mtime_ns, mtime_ns))
        debug_log(f"gitlink entries (nested repositories) removed from the "
                  f"index copy: {len(nested)}; their contents are not reviewed")
        return True
    except (subprocess.TimeoutExpired, OSError, RuntimeError, ValueError) as e:
        # RuntimeError: the timer thread could not start.
        debug_log(f"removing gitlinks from the index copy failed: {e}")
        return False


def _git_toplevel(cwd):
    """Absolute repo root for `cwd`, or None if not in a work tree."""
    try:
        # See #2099: stdout is a PATH — `C:\אבטחה\repo` returned as UTF-8
        # bytes by git. text=True would decode via cp1252 strict on Windows
        # → reader-thread crash. Decode manually with errors="replace".
        r = subprocess.run(
            [*GIT_CMD, "rev-parse", "--show-toplevel"],
            cwd=cwd, capture_output=True, timeout=5,
        )
        if r.returncode != 0:
            return None
        path = r.stdout.decode("utf-8", errors="replace").strip()
        return path if path else None
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return None


def _git_toplevel_and_head(cwd):
    """(repo root, HEAD SHA) for `cwd` from one git call, or (None, None)
    when git cannot give both (not a work tree, no commits)."""
    try:
        r = subprocess.run(
            [*GIT_CMD, "rev-parse", "--show-toplevel", "HEAD"],
            cwd=cwd, capture_output=True, timeout=5,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return None, None
    if r.returncode != 0:
        return None, None
    # See #2099: the first line is a PATH, so decode the bytes manually.
    top, _, head = r.stdout.decode("utf-8", errors="replace").strip().rpartition("\n")
    return (top.strip() or None), (head.strip() or None)


def _git_head_at(cwd, epoch):
    """The SHA this checkout's HEAD pointed at just before `epoch` (seconds),
    read from its own reflog. A checkout created after `epoch` answers with
    the commit it was created at. None when git cannot say (no reflog)."""
    try:
        # Reflog times are whole seconds: ask for the second before, so a
        # commit made in the same second as `epoch` counts as after it.
        r = subprocess.run(
            [*GIT_CMD, "rev-parse", "--verify", "-q", f"HEAD@{{@{int(epoch) - 1}}}"],
            cwd=cwd, capture_output=True, timeout=5,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError,
            TypeError, ValueError, OverflowError):
        return None
    sha = r.stdout.decode("utf-8", errors="replace").strip()
    return sha if r.returncode == 0 and sha else None


def _git_dir(repo_root):
    """Absolute shared `.git` directory for repo_root.

    Uses `rev-parse --git-common-dir` so linked worktrees resolve to the
    SHARED gitdir, not the per-worktree `.git/worktrees/<name>/`. That way
    push-sweep's reviewed-shas record (and the bash-hook-once sentinel)
    is per-clone — a commit reviewed in one worktree counts as reviewed
    if a different worktree later pushes it. Returns None on failure so
    callers can degrade (push-sweep state is best-effort).
    """
    try:
        # See #2099: stdout is a PATH (shared gitdir), may be non-ASCII.
        # Decode bytes manually to avoid cp1252 reader-thread crash.
        r = subprocess.run(
            [*GIT_CMD, "rev-parse", "--git-common-dir"],
            cwd=repo_root, capture_output=True, timeout=5,
        )
        if r.returncode != 0:
            return None
        d = r.stdout.decode("utf-8", errors="replace").strip()
        return d if os.path.isabs(d) else os.path.join(repo_root, d)
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return None


def _git_rev_list_range(repo_root, base, head="HEAD"):
    """Shas in `base..head`, oldest→newest. Empty list on error."""
    try:
        # See #2099: stdout is ASCII SHAs, but stderr can carry git error
        # messages referencing non-ASCII filenames — keep bytes raw.
        r = subprocess.run(
            [*GIT_CMD, "rev-list", "--reverse", f"{base}..{head}"],
            cwd=repo_root, capture_output=True, timeout=10,
        )
        if r.returncode != 0:
            return []
        return [s for s in r.stdout.decode("utf-8", errors="replace").strip().split("\n") if s]
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return []


def _git_diff_range(repo_root, base, head="HEAD"):
    """`git diff -p base head` as text on success, None on error.

    Distinguishing failure from success-with-empty-diff matters: the push-sweep
    caller marks the tail reviewed when the diff is empty (nothing to review),
    but on failure (timeout, non-zero exit, missing git) it must NOT mark
    them reviewed — otherwise unreviewed commits get permanently silenced.
    """
    try:
        # GIT_CMD globally passes core.quotePath=false (see definition) so
        # non-ASCII paths in `diff --git a/... b/...` headers come through as
        # raw UTF-8, not C-quoted. Required by the downstream
        # parse_diff_into_files / extract_file_paths_from_diff regex.
        r = subprocess.run(
            [*GIT_CMD, "diff", "-p", "--no-color", "--no-ext-diff", "--no-textconv", base, head],
            cwd=repo_root, capture_output=True, timeout=30,
        )
        if r.returncode != 0:
            return None
        return r.stdout.decode("utf-8", errors="replace")
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return None


def _detect_main_branch(repo_root):
    for ref in ("origin/HEAD", "origin/main", "origin/master", "main", "master"):
        try:
            # See #2099: stdout is a SHA but stderr can carry non-ASCII git
            # warnings — keep bytes raw to avoid cp1252 reader-thread crash.
            r = subprocess.run(
                [*GIT_CMD, "rev-parse", "--verify", "-q", ref],
                cwd=repo_root, capture_output=True, timeout=5,
            )
            if r.returncode == 0 and r.stdout.strip():
                return ref
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass
    return None


def _git_reflog_recent_commits(repo_root, max_age_s=120, max_n=5):
    """Return (fresh_commit_shas, stale_count) from the HEAD reflog.

    Scans the last `max_n` reflog entries and returns the SHAs whose action is
    `commit*` AND whose commit timestamp is within `max_age_s` of now,
    newest-first. `stale_count` is the number of commit-action entries that
    were too old (so the caller can distinguish "no commit happened" from
    "commit happened earlier than the window").

    Used by commit-review when stdout-based `[branch sha]` detection fails
    (output piped/redirected/-q, or a chained command after `git commit`
    pushed the success line off — `git commit && git push` makes HEAD@{0}
    `update by push`, not `commit:`). The HEAD@{0}-only check
    keeps the not-yet-visible-HEAD skip rare; analysis showed the
    residual is dominated by these chained-command and noop-guard cases.

    Safety vs. blindly reading HEAD:
      - cross-repo (`cd ../other && git commit`): repo_root's own reflog has
        no fresh commit, so this returns ([], 0).
      - commit actually failed (pre-commit reject, nothing-staged): reflog's
        recent entries are the prior checkout/commit/reset → ([], 0) or only
        stale entries.
      - HEAD raced ahead (a second commit landed before this async hook ran):
        both commits appear in the scan and both get reviewed — correct.
      - prior Bash call's commit within the window: would be returned here,
        but the call site deduplicates against `.git/sg-reviewed-shas` so a
        SHA is reviewed at most once. This is also the non-overlap invariant
        with push-sweep.
    """
    if not repo_root:
        return [], 0
    try:
        # %gs (the reflog subject) is `commit: <commit-msg first line>` and can
        # contain `|`; put it LAST so split("|", 2) leaves it intact. %H is
        # hex and %ct is integer, so the first two fields are delimiter-safe.
        #
        # Bytes + decode utf-8/replace: %gs embeds commit-message subjects
        # which git stores as raw bytes — commits can be authored in
        # latin-1 / cp1252 / shift-jis etc., and text=True would raise
        # UnicodeDecodeError in the subprocess reader thread on Windows
        # cp1252 (subprocess.run returns r.stdout=None, then
        # r.stdout.splitlines() AttributeErrors). Mirrors the existing
        # migration at security_reminder_hook.py:540 — same pattern was
        # missed here. See anthropics/claude-plugins-official#2056.
        r = subprocess.run(
            [*GIT_CMD, "log", "-g", "-n", str(max_n),
             "--format=%H|%ct|%gs", "HEAD"],
            cwd=repo_root, capture_output=True, timeout=5,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError, ValueError):
        return [], 0
    if r.returncode != 0:
        return [], 0
    stdout = (r.stdout or b"").decode("utf-8", errors="replace")
    import time as _time
    now = int(_time.time())
    fresh, stale = [], 0
    for idx, line in enumerate(stdout.splitlines()):
        parts = line.split("|", 2)
        if len(parts) != 3:
            continue
        sha, ct, subject = parts
        # `commit: msg`, `commit (amend): msg`, `commit (initial): msg`,
        # `commit (merge): msg` — all create a reviewable commit object.
        if not subject.startswith("commit"):
            continue
        try:
            age = now - int(ct)
        except ValueError:
            continue
        # HEAD@{0} (idx==0) is exempt from the age gate. The gate exists to
        # bound the WIDENED HEAD@{1..max_n-1} scan from picking up commits
        # made by *prior* Bash calls; HEAD@{0} is by definition the most
        # recent reflog entry and was previously accepted unconditionally
        # (_git_reflog_head_if_just_committed previously had no age check).
        # Applying max_age_s to idx==0 made the not-yet-visible-HEAD skip
        # noticeably more frequent on chained
        # `git commit && <slow command>` where %ct is >120s old by the
        # time the async PostToolUse hook fires.
        if idx == 0 or age <= max_age_s:
            fresh.append(sha)
        else:
            stale += 1
    return fresh, stale


# New name -> secret-shaped old name, for the renames and copies git reported
# during this hook run. The Stop review limits its diff to a list of paths:
# with only the new name in it, git shows the secret's content as a new file,
# and the diff parsers cannot tell it came from a name they leave out.
_secret_rename_origins = {}


def _note_rename(old_path, new_path):
    if _is_secret_shaped(old_path):
        _secret_rename_origins[new_path] = old_path


def _git_name_only(cwd, base, include_untracked=False):
    """Return the set of repo-root-relative paths that differ from `base`,
    or None if git failed (unresolvable ref, not a repo, timeout). Callers
    must distinguish None (error → don't trust as a filter) from set()
    (genuinely nothing changed). `-c core.quotePath=false -z` keeps non-ASCII
    and space-containing paths intact.

    Against the work tree the set can also hold a file whose stat changed and
    whose content did not: the diff does not refresh the index. Callers
    intersect with `git status`, which compares content."""
    # Decode stdout/stderr as UTF-8 with errors="replace" instead of using
    # text=True. core.quotePath=false makes git emit raw UTF-8 for non-ASCII
    # paths, and text=True on Windows decodes via cp1252 strict — a non-ASCII
    # changed path would crash the subprocess reader thread, leave
    # result.stdout=None, and propagate AttributeError out of the helper.
    # Same fix shape as diffstate._list_untracked. See #2056.
    def _run(env):
        # core.quotePath=false comes from GIT_CMD globally (see definition).
        result = subprocess.run(
            [*GIT_CMD, "diff", IGNORE_SUBMODULES, "--name-status", "-z", base],
            cwd=cwd, capture_output=True, timeout=30,
            env=env,
        )
        if result.returncode != 0:
            stderr_str = (result.stderr or b"").decode("utf-8", errors="replace")
            debug_log(f"_git_name_only({base!r}) rc={result.returncode}: {stderr_str[:200]}")
            return None
        stdout = (result.stdout or b"").decode("utf-8", errors="replace")
        # Fields are `status\0path\0`, or `R<score>\0old\0new\0` for a rename
        # or copy, which is listed by its new name only.
        fields = stdout.split("\0")
        names = set()
        i = 0
        while i + 1 < len(fields):
            if fields[i][:1] in ("R", "C") and i + 2 < len(fields):
                _note_rename(fields[i + 1], fields[i + 2])
                i += 1
            names.add(fields[i + 1])
            i += 2
        return names

    try:
        # The diff only reads the index (diff.autoRefreshIndex is off in
        # GIT_CMD); a copy is for `add -N` alone.
        if not include_untracked:
            return _run(None)
        with _temp_index(cwd) as env:
            return _run(env)
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError, ValueError) as e:
        debug_log(f"_git_name_only({base!r}) error: {e}")
        return None


def _git_status_porcelain(cwd):
    """One `git status --porcelain=v1 -z` → (tracked_dirty, untracked) sets of
    repo-root-relative paths, or (None, None) on error. Replaces the
    `_temp_index + git diff HEAD --name-only` pair for the v2 dirty_now
    computation: faster in large repos, and yields the
    untracked set separately so the later get_git_diff can do a targeted
    `add -N -- <files>` instead of a whole-tree `add -N .`.

    -uall: list individual files inside untracked directories (default
    collapses to `dir/`). Required so the untracked set subtracts cleanly
    against the UPS-time `_list_untracked` snapshot, which uses ls-files and
    therefore always lists individual files."""
    # Lenient decode: same UTF-8 + errors="replace" pattern as the
    # sibling helpers — a non-ASCII path in the worktree would otherwise
    # crash the cp1252 reader thread on Windows. See #2056.
    try:
        # core.quotePath=false comes from GIT_CMD globally (see definition).
        r = subprocess.run(
            [*GIT_CMD, "status", IGNORE_SUBMODULES, "--porcelain=v1", "-uall", "-z"],
            cwd=cwd, capture_output=True, timeout=30,
        )
        if r.returncode != 0:
            stderr_str = (r.stderr or b"").decode("utf-8", errors="replace")
            debug_log(f"_git_status_porcelain rc={r.returncode}: {stderr_str[:200]}")
            return None, None
        tracked, untracked = set(), set()
        stdout = (r.stdout or b"").decode("utf-8", errors="replace")
        entries = stdout.split("\0")
        i = 0
        while i < len(entries):
            e = entries[i]
            if not e:
                i += 1
                continue
            xy, path = e[:2], e[3:]
            if xy == "??":
                # With -uall only a nested repository is listed as `dir/`.
                # It is not a file to review; see diff.ignoreSubmodules.
                if not path.endswith("/"):
                    untracked.add(path)
            else:
                tracked.add(path)
                # Rename/copy entries are XY old\0new\0 — second NUL field is
                # the origin path; consume it so it isn't misparsed as a new
                # 2-char-status entry.
                if "R" in xy or "C" in xy:
                    i += 1
                    if i < len(entries):
                        _note_rename(entries[i], path)
            i += 1
        return tracked, untracked
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError, ValueError) as e:
        # ValueError guards against any future strict-decode regression
        # so the helper degrades to (None, None) instead of crashing.
        debug_log(f"_git_status_porcelain error: {e}")
        return None, None



def _is_ancestor(cwd, maybe_ancestor, descendant):
    """True if `maybe_ancestor` is reachable from `descendant` (i.e. HEAD
    moved forward via commit/merge, not sideways via checkout)."""
    try:
        # See #2099: only returncode matters, but text=True spawns reader
        # threads that decode stderr — git error messages can carry non-ASCII
        # filenames. Drop text=True to keep bytes raw, avoid cp1252 crash.
        result = subprocess.run(
            [*GIT_CMD, "merge-base", "--is-ancestor", maybe_ancestor, descendant],
            cwd=cwd, capture_output=True, timeout=5,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return False


_DEFAULT_FILE_DIFF_BYTES = 4 * 1024 * 1024
_LATE_FILE_DIFF_BYTES = 256 * 1024
_LAST_FILE_DIFF_BYTES = 96 * 1024


def _file_diff_cap():
    """SG_MAX_FILE_DIFF_BYTES, or the default when it is unset, not a number
    or not positive. Never below what a late file keeps, which is well above
    what the review prompt takes of one file."""
    try:
        n = int(os.environ.get("SG_MAX_FILE_DIFF_BYTES", ""))
    except ValueError:
        return _DEFAULT_FILE_DIFF_BYTES
    if n <= 0:
        return _DEFAULT_FILE_DIFF_BYTES
    return max(n, _LATE_FILE_DIFF_BYTES)


# How much of one file's diff the Stop review keeps while it reads git's
# output: this much from the start of the file's section, and as much again
# of the added lines after that. The review prompt takes far less of a file
# (DIFF_PER_FILE_BYTES); the rest is for filter_preexisting_from_diff, which
# needs the removed and the added side of a rewritten file.
MAX_FILE_DIFF_BYTES = _file_diff_cap()
# Past this much kept in total, a further file keeps _LATE_FILE_DIFF_BYTES
# the same two ways; past four times as much, _LAST_FILE_DIFF_BYTES from its
# start, which is still more than the review prompt takes of one file.
MAX_KEPT_DIFF_BYTES = 4 * MAX_FILE_DIFF_BYTES
_SECTION_MARK = b"\ndiff --git "
_MAX_HEADER_BYTES = 64 * 1024
_CUT_MARK = b"\\ [cut by security-guidance: the rest of this file's diff was not read]\n"

# What the last get_git_diff read, for the Stop hook's metrics: bytes of git
# output, reviewable files whose diff was cut and the bytes cut from them,
# and diffs that hit the timeout during this hook run.
_diff_read = {"bytes": 0, "cut_files": 0, "cut_bytes": 0, "timeouts": 0}


class _DiffKeeper:
    """Takes `git diff` output as it arrives and keeps only what the review
    can use: the header line of every file, and a bounded part of each file
    parse_diff_into_files would keep. A turn that wrote large data files no
    longer puts their whole diff in memory."""

    def __init__(self):
        self.parts = []
        self.kept = 0
        self.seen = 0
        self.cut_files = 0
        self.cut_bytes = 0
        # Unhandled input. Starts as a newline that is not git's, so a header
        # at the very start of the output is found like any other.
        self._pending = b"\n"
        self._at_start = True
        self._reviewable = True
        self._room = self._added_room = MAX_FILE_DIFF_BYTES
        self._cut = False
        self._ends_nl = True
        # Past the cut: whether the next byte starts a line, and whether the
        # line being read is an added one.
        self._bol = True
        self._in_added = False

    def feed(self, data):
        buf = self._pending + data
        pos = 0
        while True:
            i = buf.find(_SECTION_MARK, pos)
            if i < 0:
                # Hold back a tail that could be the start of a header.
                end = max(pos, len(buf) - len(_SECTION_MARK) + 1)
                self._keep(buf, pos, end)
                self._pending = buf[end:]
                return
            j = buf.find(b"\n", i + 1)
            if j < 0 and len(buf) - i <= _MAX_HEADER_BYTES:
                # The header line is not complete yet.
                self._keep(buf, pos, i)
                self._pending = buf[i:]
                return
            self._keep(buf, pos, i + 1)
            if j >= 0:
                self._begin(buf[i + 1:j])
            pos = i + 1

    def _begin(self, header):
        """A new file's section starts with this `diff --git ` line."""
        self._end_section()
        text = header[len(_SECTION_MARK) - 1:].decode("utf-8", errors="replace")
        paths = _parse_diff_header(text)
        # A section the parser drops, or whose header it cannot read and only
        # counts, keeps its header line.
        self._reviewable = bool(paths) and _section_is_reviewable(
            paths[1] or paths[0], paths[0])
        if not self._reviewable:
            self._room, self._added_room = len(header) + 1, 0
        elif self.kept > 4 * MAX_KEPT_DIFF_BYTES:
            self._room, self._added_room = max(len(header) + 1, _LAST_FILE_DIFF_BYTES), 0
        elif self.kept > MAX_KEPT_DIFF_BYTES:
            self._room = self._added_room = max(len(header) + 1, _LATE_FILE_DIFF_BYTES)
        else:
            self._room = self._added_room = MAX_FILE_DIFF_BYTES
        self._cut = False

    def _end_section(self):
        if not self._ends_nl:
            # Cut inside a line: end it, so what follows starts a line.
            self._append(b"\n")
        if self._cut:
            self._append(_CUT_MARK)

    def _append(self, piece):
        self.parts.append(piece)
        self.kept += len(piece)
        self._ends_nl = piece.endswith(b"\n")

    def _keep(self, buf, start, end):
        if self._at_start and end > start:
            self._at_start = False
            start += 1
        n = end - start
        if n <= 0:
            return
        self.seen += n
        take = min(n, self._room)
        if take:
            self._append(buf[start:start + take])
            self._room -= take
        if take == n or not self._reviewable:
            return
        if not self._cut:
            self._cut = True
            self.cut_files += 1
            self._bol = self._ends_nl
            self._in_added = False
        self.cut_bytes += n - take - self._keep_added(buf, start + take, end)

    def _keep_added(self, buf, pos, end):
        """Past a file's cut, keep its added lines only, up to as much again.
        A rewritten file lists every removed line before the first added one,
        and the review is about the added ones. Returns the bytes kept."""
        kept = 0
        run = -1  # where a run of added lines not yet appended starts
        while pos < end and self._added_room > 0:
            if self._bol:
                self._bol = False
                self._in_added = buf.startswith(b"+", pos)
                if self._in_added and run < 0 and not self._ends_nl:
                    self._append(b"\n")
            if not self._in_added:
                if run >= 0:
                    self._append(buf[run:pos])
                    run = -1
                nxt = buf.find(b"\n+", pos, end)
                if nxt < 0:
                    self._bol = buf.endswith(b"\n", pos, end)
                    break
                pos = nxt + 1
                self._bol = True
                continue
            nl = buf.find(b"\n", pos, end)
            stop = end if nl < 0 else nl + 1
            take = min(stop - pos, self._added_room)
            if run < 0:
                run = pos
            self._added_room -= take
            kept += take
            self._bol = nl >= 0
            if pos + take < stop:
                self._append(buf[run:pos + take])
                run = -1
            pos = stop
        if run >= 0:
            self._append(buf[run:pos])
        return kept

    def result(self):
        self._keep(self._pending, 0, len(self._pending))
        self._pending = b""
        self._end_section()
        self._cut = False
        return b"".join(self.parts)


def _run_diff_bounded(cmd, timeout, **kwargs):
    """subprocess.run(cmd, capture_output=True, timeout=timeout) for a
    `git diff`, except that stdout goes through _DiffKeeper instead of being
    held whole."""
    keeper = _DiffKeeper()
    deadline = time.monotonic() + timeout
    try:
        err = tempfile.TemporaryFile()
    except OSError:
        err = None
    try:
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                             stderr=err if err is not None else subprocess.DEVNULL,
                             **kwargs)
        failed = []
        given_up = []

        def _read():
            try:
                while not given_up:
                    chunk = p.stdout.read1(65536)
                    if not chunk or given_up:
                        break
                    keeper.feed(chunk)
            except BaseException as e:
                failed.append(e)

        # Read on a thread, so the timeout holds even while something git
        # started still has the pipe open after git itself is gone.
        reader = threading.Thread(target=_read, daemon=True)
        timed_out = False
        try:
            try:
                reader.start()
            except RuntimeError as e:
                failed.append(e)
            else:
                reader.join(timeout)
                timed_out = reader.is_alive()
            if timed_out or failed:
                p.kill()
            try:
                returncode = p.wait(max(deadline - time.monotonic(), 0.1))
            except subprocess.TimeoutExpired:
                timed_out = True
        finally:
            if timed_out or failed or p.returncode is None:
                # The reader may be left waiting on a pipe something else
                # holds: it keeps nothing more, and the pipe stays its.
                given_up.append(True)
                p.kill()
                p.wait()
                if reader.ident is not None:
                    reader.join(1)
            if not reader.is_alive():
                p.stdout.close()
        _diff_read["bytes"] += keeper.seen
        if timed_out:
            _diff_read["timeouts"] += 1
            raise subprocess.TimeoutExpired(cmd, timeout)
        if failed:
            raise OSError(f"reading the diff failed: {failed[0]!r}")
        stdout = keeper.result()
        _diff_read["cut_files"] += keeper.cut_files
        _diff_read["cut_bytes"] += keeper.cut_bytes
        stderr = b""
        if err is not None:
            err.seek(0)
            stderr = err.read(4096)
        return subprocess.CompletedProcess(cmd, returncode, stdout, stderr)
    finally:
        if err is not None:
            err.close()


def get_git_diff(cwd, baseline_sha, full_context=False, paths=None, untracked_paths=None):
    """
    Get the git diff between the baseline SHA and the current working tree,
    including untracked (new) files.

    Uses a temporary copy of the git index (GIT_INDEX_FILE) so the user's
    real index is never modified. The temp index gets intent-to-add entries
    for untracked files, making them visible in the diff output. Cleanup
    is just deleting the temp file in a finally block.

    If `paths` is given, the diff is restricted to those paths (relative to
    cwd; absolute paths are converted, paths outside cwd are dropped).
    A path list too long for one command is cut down to reviewable source
    files: see _run_git_on_review_paths.
    `untracked_paths` (repo-root-relative) is forwarded to _temp_index so it
    can add only those files instead of scanning the whole worktree.
    The output is read through _DiffKeeper: files the review would drop come
    back as their header line only, and a file's diff past
    MAX_FILE_DIFF_BYTES is cut down to its added lines.
    """
    _path_list_too_long.clear()
    pathspec = _diff_pathspec(cwd, paths)
    if paths and not pathspec:
        # Caller restricted to specific paths but none are inside this repo
        # (e.g. only ~/.claude/... edits). Returning "" flows to skip(6); an
        # empty pathspec would mean an UNRESTRICTED diff — the bug this whole
        # change exists to fix.
        return ""

    # core.quotePath=false comes from GIT_CMD globally (see definition).
    args = ["diff", IGNORE_SUBMODULES, "--no-color", "--no-ext-diff", "--no-textconv", baseline_sha] + (["--unified=99999"] if full_context else [])
    _diff_read.update(bytes=0, cut_files=0, cut_bytes=0)

    def _run(env):
        if pathspec:
            results = _run_git_on_review_paths(args, pathspec[1:], timeout=30, run=_run_diff_bounded, cwd=cwd, env=env)
        else:
            results = [_run_diff_bounded([*GIT_CMD, *args], 30, cwd=cwd, env=env)]
        if not results:
            _path_list_too_long.add("none_reviewable")
        for result in results:
            if result.returncode != 0:
                debug_log(f"git diff failed: {result.stderr[:200].decode('utf-8', errors='replace')}")
                return None
        # Decode with errors='replace' so binary diffs don't crash
        return b"".join(r.stdout for r in results).decode("utf-8", errors="replace")

    try:
        if untracked_paths is not None and not untracked_paths:
            # Nothing to `add -N`, and the diff only reads the index.
            return _run(None)
        with _temp_index(cwd, untracked_paths) as env:
            # env is None when there is no index (bare repo / not a repo)
            # or no copy slot — diff still runs, just without
            # untracked-file support.
            return _run(env)
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
        debug_log(f"git diff error: {e}")
        if isinstance(e, OSError) and _too_many_args(e):
            _path_list_too_long.add("gave_up")
        return None


# Source file extensions worth reviewing for security
SOURCE_CODE_EXTENSIONS = {
    '.py', '.js', '.ts', '.jsx', '.tsx', '.go', '.java', '.rb', '.php',
    '.rs', '.c', '.cpp', '.h', '.hpp', '.cs', '.swift', '.kt', '.scala',
    '.html', '.htm', '.ejs', '.yaml', '.yml', '.properties',
    '.mjs', '.cjs', '.mts', '.cts', '.vue', '.svelte',
    '.sh', '.bash', '.zsh', '.fish', '.ksh', '.ps1', '.sql',
    '.gradle', '.groovy',
    '.tf', '.hcl', '.tfvars',
    '.json', '.toml', '.ipynb',
}

# Reviewable files identified by basename rather than extension (lowercased).
# These are by-convention extensionless but contain executable recipes/DSL
# with shell/exec surface (Make recipes, Jenkinsfile Groovy, Rakefile Ruby).
SOURCE_CODE_BASENAMES = {
    'dockerfile', 'makefile', 'gnumakefile', 'jenkinsfile', 'vagrantfile',
    'rakefile', 'gemfile', 'procfile', 'brewfile', 'justfile',
}

# Extensionless basenames that are NOT source — plain-text metadata. Anything
# extensionless not in this set is treated as source (likely a shebang script
# under bin/ or scripts/). Analysis of skipped reviews found
# extensionless executables (bin/deploy, scripts/run-canary) were the largest
# remaining false-negative class — they carry shell-injection surface but
# `splitext` gives '' so they were filtered out. _cap_files_for_prompt bounds
# the byte cost downstream, and the reviewer ignores prose, so opting
# extensionless IN with this small deny-list is the better default than
# opting OUT.
NON_SOURCE_EXTENSIONLESS_BASENAMES = {
    'license', 'licence', 'copying', 'notice', 'patents', 'authors',
    'contributors', 'maintainers', 'changelog', 'changes', 'news',
    'readme', 'todo', 'install', 'version', 'codeowners',
    'owners', 'copyright',
}

# Directory components and file suffixes that are never worth reviewing even
# when the extension is in SOURCE_CODE_EXTENSIONS — vendored deps, build
# output, generated code, minified bundles, lockfiles, protobuf stubs.
# Matched as path *components* (so `node_modules/` matches anywhere in the
# path, not just as a prefix) and as case-sensitive suffixes (the ecosystems
# that emit `.min.js` / `_pb2.py` / `.pb.go` are case-consistent).
SKIP_PATH_PATTERNS = (
    'node_modules/', 'dist/', 'build/', '.next/', 'vendor/',
    '__generated__/', '__pycache__/', '.venv/', 'target/',
)
SKIP_FILE_SUFFIXES = (
    '.min.js', '.min.css', '.d.ts', '.d.mts', '.d.cts',
    '.lock', '_pb2.py', '.pb.go',
)

# Files that hold secrets by naming convention are never sent for review. The
# review covers everything dirty in the work tree, including files the user
# changed and Claude never opened, so a key file or an encrypted dotfile source
# would otherwise leave the machine in the review request. The list is kept to
# names that are secret stores by convention; ordinary source such as
# `private_api.py` or `id_generator.py` stays reviewable.
_SSH_PRIVATE_KEY_BASENAMES = frozenset((
    'id_rsa', 'id_dsa', 'id_ecdsa', 'id_ecdsa_sk', 'id_ed25519',
    'id_ed25519_sk', 'id_xmss',
))
_PRIVATE_KEY_NAME_SUFFIXES = ('_rsa', '_dsa', '_ecdsa', '_ed25519')
# `.credentials.json` and `.claude.json` are Claude Code's own files: sign-in
# tokens, a saved API key, MCP server secrets. Claude Code rewrites them as it
# runs, so they show up as changed when its config directory is a git repo.
_CREDENTIAL_BASENAMES = frozenset((
    'credentials', '.netrc', '.pgpass', '.npmrc', '.pypirc',
    '.git-credentials', '.dockercfg', '.credentials.json', '.claude.json',
))
# chezmoi encodes a target file's attributes as stacked name prefixes
# (`private_dot_netrc`, `encrypted_private_token`); `dot_` stands for a
# leading dot.
_CHEZMOI_ATTR_PREFIXES = (
    'after_', 'before_', 'create_', 'empty_', 'encrypted_', 'exact_',
    'executable_', 'external_', 'literal_', 'modify_', 'once_', 'onchange_',
    'private_', 'readonly_', 'remove_', 'run_', 'symlink_',
)
# An `encrypted_` source keeps its target's name, so `encrypted_store.py` could
# be either ciphertext or code about encryption. Treat it as ciphertext only
# when it has no extension or a data-file one.
_ENCRYPTED_DATA_EXTENSIONS = frozenset((
    '', '.json', '.yaml', '.yml', '.toml', '.properties', '.tfvars',
))


# Paths skipped as secret-shaped during this hook run. The Stop hook reports
# the count (never the names) so the skip can be watched in telemetry.
_secret_shaped_skipped = set()


def _skip_secret_shaped(file_path):
    if not _is_secret_shaped(file_path):
        return False
    _secret_shaped_skipped.add(file_path)
    return True


def _is_secret_shaped(file_path):
    base = os.path.basename(file_path.replace("\\", "/")).lower()
    target = base
    encrypted = False
    stripped = True
    while stripped:
        stripped = False
        for prefix in _CHEZMOI_ATTR_PREFIXES:
            if target.startswith(prefix) and len(target) > len(prefix):
                target = target[len(prefix):]
                encrypted = encrypted or prefix == 'encrypted_'
                stripped = True
                break
    if target.startswith('dot_'):
        target = '.' + target[4:]
    ext = os.path.splitext(target)[1]
    if encrypted and ext in _ENCRYPTED_DATA_EXTENSIONS:
        return True
    for name in {base, target}:
        if name.startswith('.env'):
            return True
        if name in _SSH_PRIVATE_KEY_BASENAMES or name in _CREDENTIAL_BASENAMES:
            return True
        if '.' not in name and name.endswith(_PRIVATE_KEY_NAME_SUFFIXES):
            return True
    return False


# Data files whose name says they hold secrets (`secrets.yml`,
# `client_secret.json`). They are reviewed like any other data file; the Stop
# hook only counts how many are in its review set (never the names), to show
# how common they are.
_SECRET_NAMED_STEMS = frozenset((
    'secret', 'secrets', 'credential', 'credentials',
    'client_secret', 'client_secrets', 'client-secret', 'client-secrets',
    'service-account', 'service_account', 'serviceaccount',
    'service-account-key', 'service_account_key', 'serviceaccountkey',
))
_SECRET_NAMED_DATA_EXTENSIONS = frozenset((
    '.json', '.yaml', '.yml', '.toml', '.properties', '.tfvars',
))
# `secrets.example.yml` is a placeholder and `secrets.enc.yaml` is ciphertext.
_NOT_SECRET_NAME_PARTS = frozenset((
    'example', 'sample', 'template', 'tmpl', 'dist', 'schema',
    'enc', 'encrypted', 'sops',
))


def _is_secret_named(file_path):
    base = os.path.basename(file_path.replace("\\", "/")).lower()
    parts = base.lstrip('.').split('.')
    if len(parts) < 2 or '.' + parts[-1] not in _SECRET_NAMED_DATA_EXTENSIONS:
        return False
    if _NOT_SECRET_NAME_PARTS.intersection(parts[1:-1]):
        return False
    stem = parts[0]
    # Google's OAuth download is `client_secret_<client id>.json`.
    return stem in _SECRET_NAMED_STEMS or stem.startswith('client_secret_')


def count_secret_named(diff_files):
    return sum(1 for file_path, _ in diff_files if _is_secret_named(file_path))


# Path tokens that bump a file's review priority when a commit exceeds
# MAX_DIFF_FILES and we have to pick a subset. These are exactly the surfaces
# single-shot and agentic reviews disagree on most (auth, routing, IPC,
# subprocess, deserialization). Matched as lowercase substrings against the
# path; not regex — keep it cheap.
_SECURITY_RISK_PATH_TOKENS = (
    "auth", "login", "session", "token", "secret", "credential", "perm",
    "acl", "rbac", "iam", "policy",
    "route", "handler", "controller", "endpoint", "api/", "/api", "gateway",
    "middleware", "view",
    "exec", "subprocess", "shell", "spawn", "command",
    "client", "request", "fetch", "http", "url",
    "serialize", "pickle", "yaml", "parse", "deser",
    # Short tokens that would substring-match unrelated names (`format`,
    # `transform`, `sandbox`, `platform`) are intentionally omitted —
    # `sql`/`query` already cover the DB surface.
    "sql", "query",
)
# Suffixes that pass _is_reviewable_source but are almost always low-signal
# in large scaffolds — generated clients, migrations, test fixtures, config
# shims. These go to the BACK of the priority sort, not dropped outright.
_LOW_PRIORITY_SUFFIXES = (
    ".gen.ts", ".gen.tsx", ".generated.ts", "_gen.py",
    ".test.ts", ".test.tsx", ".test.py", ".spec.ts", ".spec.js",
    ".config.js", ".config.ts", ".config.mjs", ".config.cjs",
)
_LOW_PRIORITY_PATH_TOKENS = (
    "/migrations/", "/alembic/versions/", "/__tests__/", "/fixtures/",
)


def _prioritize_diff_files(diff_files, cap):
    """When `diff_files` exceeds `cap`, return the top-`cap` by security
    relevance plus the count dropped. Otherwise return (diff_files, 0).

    Score = (risk_tokens_in_path, not_low_priority, added_lines). The
    added-lines proxy is `content.count('\\n+')` which counts diff additions
    cheaply without re-parsing hunks. This is a heuristic, not a guarantee —
    the goal is to review the likely-dangerous subset of an over-cap diff
    instead of reviewing nothing. Diffs that exceed the cap are typically
    large multi-file scaffolds, and the cross-file source→sink vulnerabilities
    in them concentrate in a handful of api/client/route files.
    """
    if len(diff_files) <= cap:
        return diff_files, 0

    def _score(item):
        fp, content = item
        low = fp.lower()
        # Prepend "/" so leading-slash patterns in _LOW_PRIORITY_PATH_TOKENS
        # match top-level dirs (git diff paths are repo-root-relative, e.g.
        # `migrations/001.py` not `/migrations/001.py`). Same trick as
        # _is_reviewable_source.
        low_slashed = "/" + low
        risk = sum(1 for t in _SECURITY_RISK_PATH_TOKENS if t in low)
        low_prio = (
            fp.endswith(_LOW_PRIORITY_SUFFIXES)
            or any(t in low_slashed for t in _LOW_PRIORITY_PATH_TOKENS)
        )
        # added_lines: count('\n+') over-counts by including '+++' header and
        # any literal '+' at line start in context, but it's a consistent
        # ordinal across files in the same diff which is all we need.
        added = content.count("\n+")
        return (risk, not low_prio, added)

    ranked = sorted(diff_files, key=_score, reverse=True)
    return ranked[:cap], len(diff_files) - cap


def _is_reviewable_source(file_path):
    # Normalize for component matching: a path like `.next/x.js` or
    # `pkg/node_modules/y.ts` should both be excluded; matching against
    # `'/' + path` lets each pattern be checked as `'/' + p in '/' + path`
    # without false-positiving on `rebuild/` matching `build/`.
    norm = "/" + file_path.replace("\\", "/")
    if any(("/" + p) in norm for p in SKIP_PATH_PATTERNS):
        return False
    if _skip_secret_shaped(file_path):
        return False
    if file_path.endswith(SKIP_FILE_SUFFIXES):
        return False
    ext = os.path.splitext(file_path)[1].lower()
    if ext in SOURCE_CODE_EXTENSIONS:
        return True
    base = os.path.basename(file_path).lower()
    # Accept dot-suffixed variants too: `Dockerfile.dev`, `Makefile.am`,
    # `Jenkinsfile.release`. splitext gives ext='.dev'/'.am' for these so they
    # miss both the extension check and the exact-basename check otherwise.
    if base in SOURCE_CODE_BASENAMES \
            or base.split(".", 1)[0] in SOURCE_CODE_BASENAMES:
        return True
    # Extensionless files default to reviewable unless they're known
    # plain-text metadata or dotfiles. Covers shebang scripts under bin/ or
    # scripts/ (`deploy`, `run-canary`, `entrypoint`) which carry
    # shell-injection surface but were previously filtered out — the largest
    # remaining false-negative class for extensionless files. Dotfiles (`.gitignore`,
    # `.nvmrc`, `.env`) are config, not code; `.bashrc`-style runnables are
    # rare in repos and not worth the noise. The deny-list is prefix-aware on
    # `-`/`_` so dual-license / i18n variants (`LICENSE-MIT`, `README-CN`)
    # don't fall through as source.
    if ext == "" and not base.startswith("."):
        if any(base == x or base.startswith(x + "-") or base.startswith(x + "_")
               for x in NON_SOURCE_EXTENSIONLESS_BASENAMES):
            return False
        return True
    return False


# A file's section starts at a `diff --git ` line. Inside a section every line
# of file content carries a `+`, `-` or space prefix, so only a real header can
# start a line with it; source text that merely contains the words cannot.
_DIFF_SECTION_RE = re.compile(r'^diff --git ', re.MULTILINE)
_UNQUOTED_HEADER_RE = re.compile(r'^a/(.+?) b/(.+)$')
_C_ESCAPES = {
    'a': b'\a', 'b': b'\b', 'f': b'\f', 'n': b'\n', 'r': b'\r', 't': b'\t',
    'v': b'\v', '\\': b'\\', '"': b'"',
}


def _read_quoted_path(text, start):
    """Decode the C-quoted path whose opening quote is at text[start].
    Returns (path, index after the closing quote), or None if unterminated."""
    out = bytearray()
    i = start + 1
    while i < len(text):
        c = text[i]
        if c == '"':
            return out.decode("utf-8", errors="replace"), i + 1
        if c == '\\' and i + 1 < len(text):
            n = text[i + 1]
            if n in _C_ESCAPES:
                out += _C_ESCAPES[n]
                i += 2
                continue
            octal = re.match(r'[0-7]{1,3}', text[i + 1:i + 4])
            if octal:
                out.append(int(octal.group(0), 8) & 0xFF)
                i += 1 + len(octal.group(0))
                continue
        out += c.encode("utf-8")
        i += 1
    return None


def _parse_diff_header(header):
    """(old_path, new_path) from the text after `diff --git `, or None.

    core.quotePath=false keeps non-ASCII names raw, but git still C-quotes a
    name that contains a double quote, a backslash or a control character:
    `"a/we\\"ird.py" "b/we\\"ird.py"`. Either side can be quoted on its own.
    """
    old = new = None
    if header.startswith('"'):
        first = _read_quoted_path(header, 0)
        if not first:
            return None
        old, end = first
        rest = header[end:].lstrip(' ')
        if rest.startswith('"'):
            second = _read_quoted_path(rest, 0)
            new = second[0] if second else None
        else:
            new = rest
    elif header.endswith('"') and ' "b/' in header:
        split_at = header.index(' "b/')
        old = header[:split_at]
        second = _read_quoted_path(header, split_at + 1)
        new = second[0] if second else None
    else:
        m = _UNQUOTED_HEADER_RE.match(header)
        return (m.group(1), m.group(2)) if m else None
    if not old or not new or not old.startswith('a/') or not new.startswith('b/'):
        return None
    return old[2:], new[2:]


# Section headers that could not be parsed during this hook run; that file is
# left out of the review. The Stop hook reports the count so a header shape
# this parser misses shows up in telemetry instead of passing silently.
_unparsed_diff_headers = set()


def _section_is_reviewable(file_path, old_path):
    """Whether a diff section is sent for review: a source file, and not one
    renamed away from a secret-shaped name, which still carries the secret's
    content."""
    return _is_reviewable_source(file_path) and not _skip_secret_shaped(old_path)


def _iter_diff_sections(diff_output):
    """Yield (new_path, old_path, lines after the header line) per file section."""
    for section in _DIFF_SECTION_RE.split(diff_output)[1:]:
        lines = section.split('\n')
        paths = _parse_diff_header(lines[0])
        if paths:
            yield paths[1] or paths[0], paths[0], lines[1:]
        else:
            _unparsed_diff_headers.add(lines[0])


def extract_file_paths_from_diff(diff_output):
    """
    Extract file paths from unified diff output (without content).
    Only includes files with source code extensions.
    """
    if not diff_output or not diff_output.strip():
        return []

    return [
        file_path for file_path, old_path, _ in _iter_diff_sections(diff_output)
        if _section_is_reviewable(file_path, old_path)
    ]


def parse_diff_into_files(diff_output):
    """
    Parse unified diff output into a list of (file_path, diff_content) tuples.
    Only includes files with source code extensions.
    """
    if not diff_output or not diff_output.strip():
        return []

    files = []
    for file_path, old_path, lines in _iter_diff_sections(diff_output):
        # Filter to source code files only. A rename away from a secret-shaped
        # name still carries the secret's content, so the old name counts too.
        if not _section_is_reviewable(file_path, old_path):
            continue

        # Extract the diff content (from first @@ onwards)
        diff_lines = []
        in_hunks = False
        for line in lines:
            if line.startswith('@@'):
                in_hunks = True
            if in_hunks:
                diff_lines.append(line)

        if diff_lines:
            files.append((file_path, '\n'.join(diff_lines)))

    return files


def filter_preexisting_from_diff(diff_files, cwd, baseline_sha):
    """
    Filter out pre-existing content from diff files.
    When a file is fully rewritten (Write tool replaces entire content),
    git shows all lines as removed (-) then re-added (+). This function
    detects such rewrites and strips lines from the + section that also
    appeared in the - section, so the LLM reviewer only sees truly new code.
    """
    if not baseline_sha:
        return diff_files

    filtered = []
    for file_path, diff_content in diff_files:
        lines = diff_content.split('\n')

        # Collect removed and added lines (stripping the +/- prefix)
        removed_lines = set()
        added_lines = []
        for line in lines:
            if line.startswith('-') and not line.startswith('---'):
                removed_lines.add(line[1:].strip())
            elif line.startswith('+') and not line.startswith('+++'):
                added_lines.append(line[1:].strip())

        if not removed_lines:
            # New file, no pre-existing content to filter
            filtered.append((file_path, diff_content))
            continue

        # Check what fraction of added lines were pre-existing
        preexisting_count = sum(1 for l in added_lines if l in removed_lines)
        if preexisting_count == 0:
            filtered.append((file_path, diff_content))
            continue

        added_lines_set = set(added_lines)

        # Rebuild diff with pre-existing lines converted to context (space prefix).
        # Known imprecision: .strip() matches across indentation (so reindented
        # code is treated as unchanged) and the set lets one removal mask N
        # additions of the same stripped text. Accepted trade-off — this filter
        # exists for the full-file Write rewrite case where exact-match would
        # miss everything; the diff-review prompt's previous-findings recheck
        # is the backstop.
        new_lines = []
        for line in lines:
            if line.startswith('+') and not line.startswith('+++'):
                content = line[1:].strip()
                if content in removed_lines:
                    # Convert to context line (pre-existing, not new)
                    new_lines.append(' ' + line[1:])
                else:
                    new_lines.append(line)
            elif line.startswith('-') and not line.startswith('---'):
                content = line[1:].strip()
                if content in added_lines_set:
                    # Skip removed lines that were re-added (they become context)
                    continue
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)

        filtered.append((file_path, '\n'.join(new_lines)))

    return filtered

