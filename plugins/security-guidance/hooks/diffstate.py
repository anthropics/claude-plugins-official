"""
Git-derived diff/review-state helpers for the security-guidance plugin.

Extracted from security_reminder_hook.py for readability. Re-exported
there so callers keep resolving bare names through the hook module's
globals — tests that ``monkeypatch.setattr(hook, "<fn>", …)`` continue
to work without retargeting.
"""
import hashlib
import os
import subprocess
import sys
import time

from _base import debug_log, portable_output, _PV
from gitutil import (
    GIT_CMD,
    _git_dir, _git_toplevel, _git_status_porcelain,
    _git_rev_parse_head, _is_ancestor, _git_name_only, _temp_index,
    _secret_rename_origins, index_entry_count,
)
from session_state import with_locked_state
from extensibility import _same_dir


# =====================================================================
# TTL constants
# =====================================================================

# stop_hook_fire_count expires after this many seconds.
# The asyncRewake loop (vuln→exit(2)→fix→Stop again) is ~30-60s/cycle, so 120s
# comfortably contains MAX_STOP_HOOK_FIRINGS while letting the next user turn
# proceed unblocked. Replaces the UPS-reset that raced against background Stop.
STOP_LOOP_STATE_TTL_SEC = 120

# previous_findings expires independently. Dedup is content-based ((filePath,
# vulnerableCode) — see _record_fire), so a longer TTL suppresses exact-repeat
# re-flags across turns without masking regressions that change the code. v2's
# git-derived review set can re-surface the same uncommitted file across turns;
# 120s could let warnings pile up over a long session.
PREVIOUS_FINDINGS_TTL_SEC = int(os.environ.get("PREVIOUS_FINDINGS_TTL_SEC", "3600"))


# =====================================================================
# Git baseline + stop-state management
# =====================================================================

def save_baseline_sha(session_id, sha):
    """Save the git baseline SHA to state."""
    def _save(state):
        state["baseline_sha"] = sha
    with_locked_state(session_id, _save)


def load_baseline_sha(session_id):
    """Load the git baseline SHA from state."""
    def _load(state):
        return state.get("baseline_sha")
    return with_locked_state(session_id, _load)


def record_touched_path(session_id, file_path):
    """Append a file path to the touched_paths list (deduped, capped at 200).

    Stop is the consumer and clears under the same lock it reads with; UPS
    no longer wipes. The cap is a defensive bound for sessions where Stop
    never fires (disabled mid-session, abort) — git diff naturally filters
    stale paths so over-retention is harmless, just wasteful.
    """
    def _record(state):
        paths = state.setdefault("touched_paths", [])
        if file_path not in paths:
            paths.append(file_path)
            if len(paths) > 200:
                del paths[:len(paths) - 200]
    with_locked_state(session_id, _record)


def consume_stop_state(session_id, clear=True):
    """Atomically snapshot all state the Stop hook needs and clear touched_paths.

    The Stop hook is asyncRewake — it runs in the background after Claude's
    turn ends. The user can submit a new prompt before this hook finishes its
    initial state read. Telemetry showed a meaningful share of would-be reviews lost when
    the next turn's UPS wiped touched_paths before Stop read it.

    Single locked read-then-clear closes that window: PostToolUse appends
    after this clear go into the next snapshot; UPS overwrites of baseline_sha
    after this snapshot are invisible to this Stop fire.
    """
    import time as _time
    now = _time.time()

    def _snap(state):
        fire_ts = state.get("stop_hook_fire_count_ts", 0)
        expired = (now - fire_ts) > STOP_LOOP_STATE_TTL_SEC
        findings_ts = state.get("previous_findings_ts", fire_ts)
        findings_expired = (now - findings_ts) > PREVIOUS_FINDINGS_TTL_SEC
        snap = {
            "touched_paths": list(state.get("touched_paths", [])),
            "baseline_sha": state.get("baseline_sha"),
            "head_at_capture": state.get("head_at_capture"),
            # Where and when the prompt hook captured it; see baseline_origin.
            "baseline_root": state.get("baseline_root"),
            "prompt_at": state.get("prompt_at"),
            "baseline_kept": state.get("baseline_kept") or 0,
            "untracked_at_baseline": (
                dict(state["untracked_at_baseline"])
                if isinstance(state.get("untracked_at_baseline"), dict) else {}
            ),
            "fire_count": 0 if expired else state.get("stop_hook_fire_count", 0),
            "fire_count_expired": expired and state.get("stop_hook_fire_count", 0) > 0,
            "previous_findings": [] if findings_expired else list(state.get("previous_findings", [])),
            "reviewed_diff_hash": state.get("reviewed_diff_hash"),
            # State lost or overwritten since the last Stop (session_state).
            "state_resets": state.get("state_resets", 0),
            "state_overwrites": state.get("state_overwrites", 0),
            "baseline_fail": state.get("baseline_fail") or 0,
        }
        # touched_paths is cleared per Stop, but one baseline can be
        # reviewed by several Stops (rewakes). turn_touched keeps every path
        # recorded since the baseline; only telemetry reads it.
        turn = list(dict.fromkeys(
            [p for p in state.get("turn_touched", []) if isinstance(p, str)]
            + snap["touched_paths"]))[-200:]
        snap["turn_touched"] = turn
        if clear:
            state["turn_touched"] = turn
            state["touched_paths"] = []
            state.pop("reviewed_diff_hash", None)
            state.pop("state_resets", None)
            state.pop("state_overwrites", None)
        return snap

    return with_locked_state(session_id, _snap) or {
        "touched_paths": [], "baseline_sha": None, "head_at_capture": None,
        "untracked_at_baseline": {}, "baseline_root": None, "prompt_at": None,
        "baseline_kept": 0,
        "fire_count": 0, "fire_count_expired": False, "previous_findings": [],
        "reviewed_diff_hash": None, "state_resets": 0, "state_overwrites": 0,
        "baseline_fail": 0, "turn_touched": [],
    }


# Path names compare without case where the filesystem usually does.
_FOLD_CASE = os.name == "nt" or sys.platform == "darwin"


def _rel_in_repo(real_root, path):
    """`path` relative to the repo root (a real path), or None when it lies
    outside the repo."""
    real = os.path.realpath(path)
    try:
        rel = os.path.relpath(real, real_root)
    except ValueError:  # another drive
        return None
    if rel == os.pardir or rel.startswith(os.pardir + os.sep):
        return None
    return rel.casefold() if _FOLD_CASE else rel


def touched_scope(repo_root, cwd, touched_paths):
    """Where the paths the session's edit tools wrote since the baseline lie:
    (scope, repo-relative paths inside the repo). scope: 0 none recorded,
    1 all inside the reviewed repo, 2 some outside, 3 all outside. Relative
    paths are read against `cwd`. The list holds the newest 200 paths, so
    this is approximate past that. Telemetry only."""
    root = os.path.realpath(repo_root)
    inside, outside = set(), 0
    for p in touched_paths:
        rel = _rel_in_repo(root, os.path.join(cwd or root, p))
        if rel is None:
            outside += 1
        else:
            inside.add(rel)
    if not touched_paths:
        return 0, inside
    if not outside:
        return 1, inside
    return (2 if inside else 3), inside


def review_scope_code(repo_root, scope, inside, files, base_fail):
    """One number, for telemetry only, saying how a Stop review relates to
    what the session's edit tools wrote since the baseline:

        base_fail * 100000 + scope * 10000 + min(untouched, 9999)

    scope and inside: from touched_scope. untouched: how many of `files`
    (repo-root-relative or absolute) no edit tool wrote. base_fail: 0 the
    review diffed against a real turn-start snapshot, 1 and 2 see
    last_baseline_fail, 3 there was no usable snapshot. Packed into one key
    and sent even when 0, so a row without it was cut by the metrics key cap
    or had no repo."""
    root = os.path.realpath(repo_root)
    untouched = sum(1 for f in files
                    if _rel_in_repo(root, os.path.join(root, f)) not in inside)
    return int(base_fail or 0) * 100000 + scope * 10000 + min(untouched, 9999)


def record_reviewed_diff(session_id, diff_hash):
    def _save(state):
        state["reviewed_diff_hash"] = diff_hash
    with_locked_state(session_id, _save)


def restore_unreviewed_stop_state(session_id, paths, baseline_sha):
    """Put consumed touched_paths back so the next Stop reviews them.

    consume_stop_state cleared touched_paths on disk; if Stop then exits
    early for a transient reason (CCR API unreachable, Haiku HTTP error)
    the next UPS would see an empty list, fall through the preservation
    guard, and re-baseline past the unreviewed edits. Restoring keeps the
    guard armed. Prepend+dedupe so any concurrent next-turn PostToolUse
    appends survive.
    """
    if not paths:
        return

    def _restore(state):
        existing = state.get("touched_paths", [])
        merged = list(dict.fromkeys(list(paths) + list(existing)))
        if len(merged) > 200:
            merged = merged[:200]
        state["touched_paths"] = merged
        if baseline_sha and not state.get("baseline_sha"):
            state["baseline_sha"] = baseline_sha
    with_locked_state(session_id, _restore)


# state["baseline_kept"]: why a prompt left an earlier turn's baseline in
# place. Only telemetry reads it.
KEPT_NO_CAPTURE = 1   # it could not capture one (not a repo, or git failed)
KEPT_UNREVIEWED = 2   # the previous turn's edits were never reviewed

# baseline_origin() values that mean "captured in another checkout".
FOREIGN_ORIGINS = (1, 2, 3)


def baseline_origin(repo_root, baseline_sha, baseline_root):
    """Where the session's baseline was captured, relative to the checkout a
    Stop review is about to read (`repo_root`):

        0  that checkout (or the origin was not recorded)
        1  another worktree of the same repository
        2  another repository
        3  another folder, which is gone or cannot be read as a checkout
        4  there is no baseline

    `baseline_root` is the repo root the prompt hook stored beside the SHA."""
    if not baseline_sha:
        return 4
    if not baseline_root or not isinstance(baseline_root, str):
        return 0
    if _same_dir(baseline_root, repo_root):
        return 0
    if not os.path.isdir(baseline_root):
        return 3
    here, there = _git_dir(repo_root), _git_dir(baseline_root)
    if not here or not there:
        return 3
    return 1 if _same_dir(here, there) else 2


def baseline_origin_metric(origin, kept):
    """The `bl_origin` number on Stop rows: baseline_origin, plus 10 or 20
    (KEPT_*) when the baseline is an earlier turn's."""
    if origin == 4 or kept not in (KEPT_NO_CAPTURE, KEPT_UNREVIEWED):
        return origin
    return origin + 10 * kept


def get_baseline_file_content(session_id, file_path, cwd):
    """Get the content of a file at the baseline SHA. Returns None if unavailable.

    Decode the file content as UTF-8 with errors="replace" rather than using
    text=True: source files in user repos can be latin-1 / cp1252 / shift-jis
    / etc., and on Windows text=True would decode via locale.getpreferredencoding()
    in strict mode and raise UnicodeDecodeError in the subprocess reader
    thread — leaving result.stdout=None and propagating AttributeError when
    the caller tries to use it. Same class as the existing migrations at
    security_reminder_hook.py:540 (reflog subjects) and :1115 (commit
    diffs); this helper was missed in that pass. See
    anthropics/claude-plugins-official#2056."""
    baseline_sha = load_baseline_sha(session_id)
    if not baseline_sha:
        return None
    try:
        abs_path = os.path.abspath(file_path)
        cwd_abs = os.path.abspath(cwd) if cwd else os.getcwd()
        attempts = [(abs_path, cwd_abs, cwd)]
        # The tool's path and the session directory can name the same place
        # through different symlinks (/tmp and /var on macOS). The relative
        # path between the two spellings then leaves the repo and git finds
        # nothing, so the lookup is tried again with both resolved.
        real_path, real_cwd = os.path.realpath(abs_path), os.path.realpath(cwd_abs)
        if (real_path, real_cwd) != (abs_path, cwd_abs):
            attempts.append((real_path, real_cwd, real_cwd))
        for path, start, git_cwd in attempts:
            try:
                rel_path = os.path.relpath(path, start)
            except ValueError:
                continue
            # `<rev>:<path>` is read from the repo root unless the path starts
            # with `./`, and takes forward slashes only. Without both, the
            # lookup fails for a session started below the repo root, and on
            # Windows for any file that is not directly in the session
            # directory.
            rel_path = rel_path.replace(os.sep, "/")
            result = subprocess.run(
                [*GIT_CMD, "show", f"{baseline_sha}:./{rel_path}"],
                cwd=git_cwd, capture_output=True, timeout=5
            )
            if result.returncode == 0:
                return (result.stdout or b"").decode("utf-8", errors="replace")
        return None
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError, ValueError):
        return None


# How the last capture_git_baseline call got its SHA: 0 a real snapshot,
# 1 `stash create` failed and HEAD was returned, 2 no index copy and HEAD was
# returned. With 1 or 2 the next Stop review cannot tell the turn's changes
# from uncommitted work that was already there. Stored with baseline_sha.
# Telemetry only.
last_baseline_fail = 0
# Entries in the index the last capture copied, None if unknown. Telemetry only.
last_index_entries = None


def capture_git_baseline(cwd):
    """
    Capture a git ref representing the current working tree state.
    Uses `git stash create` which creates a commit object for the current state
    (HEAD + uncommitted changes) without modifying the stash list or working tree.
    Falls back to HEAD if the working tree is clean.
    Returns the SHA string, or None if not in a git repo or if the repo has no commits.

    `stash create` runs on a throwaway copy of the index (GIT_INDEX_FILE), so
    its `index.lock` and `index.stash.<pid>` files land next to the copy, not
    in `.git`: it cannot collide with a concurrent git command, and a timeout
    kill cannot leave a lock that blocks the user's next one.
    GIT_OPTIONAL_LOCKS does not cover stash. Copying the real index without a
    lock is safe: git replaces it by atomic rename.

    NOTE: `git stash create` does NOT capture untracked files. UPS pairs this
    SHA with a `_list_untracked()` snapshot stored as `untracked_at_baseline`,
    and `compute_v2_review_set` subtracts that set so pre-existing untracked
    files are not reviewed as Claude-authored. UPS takes no snapshot while the
    Stop review, its only reader, is switched off.
    """
    # stdout is a SHA so text=True is safe on stdout, but a non-ASCII
    # filename in `git stash create`'s STDERR warning (e.g. a worktree
    # with `Ávila_report.txt` triggers a quotePath/locale warning) would
    # trip the stderr reader thread on Windows cp1252. Decode both streams
    # leniently for symmetry with _list_untracked. See #2056.
    global last_baseline_fail, last_index_entries
    last_baseline_fail = 0
    last_index_entries = None
    try:
        # Check if HEAD exists (i.e., repo has at least one commit)
        head_check = subprocess.run(
            [*GIT_CMD, "rev-parse", "HEAD"],
            cwd=cwd, capture_output=True, timeout=5
        )
        if head_check.returncode != 0:
            # No commits yet — skip review rather than creating commits in the user's repo
            debug_log("No commits in repo, skipping baseline capture")
            return None

        sha = ""
        # untracked_paths=[]: a plain copy of the index, no `add -N` pass.
        with _temp_index(cwd, untracked_paths=[]) as env:
            # env is None when no usable index copy could be made: fall
            # back to HEAD.
            if env is not None:
                last_index_entries = index_entry_count(env["GIT_INDEX_FILE"])
                result = subprocess.run(
                    [*GIT_CMD, "stash", "create"],
                    cwd=cwd, capture_output=True, timeout=15, env=env
                )
                sha = (result.stdout or b"").decode("utf-8", errors="replace").strip()
                if not sha and result.returncode != 0:
                    last_baseline_fail = 1
            else:
                last_baseline_fail = 2
        if sha:
            return sha

        # Working tree is clean — stash create returns empty. Use HEAD.
        result = subprocess.run(
            [*GIT_CMD, "rev-parse", "HEAD"],
            cwd=cwd, capture_output=True, timeout=5
        )
        sha = (result.stdout or b"").decode("utf-8", errors="replace").strip()
        return sha if sha else None
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError, ValueError) as e:
        debug_log(f"Failed to capture git baseline: {e}")
        return None


# ─── push-sweep reviewed-commit tracking ────────────────────────────────────
#
# Repo-local (not session-local) record of which commits the commit-review
# hook has already reviewed, so the push-sweep can advance its diff base past
# the contiguous reviewed prefix and skip entirely when everything pushed was
# already covered. Lives under `.git/` (same precedent as CC's
# `.git/claude-trailers`) so it survives across sessions and is per-clone.
#
# Format: one line per reviewed sha, append-only:
#   <40-hex-sha>\t<unix-ts>\t<pv>\t<vulns_found>
#
# The trailing columns are observability only — load reads just the sha set.
# GC keeps the last _REVIEWED_SHAS_CAP entries; the file is small (~64 bytes
# per line) so even at the cap it's ~32KB.


# =====================================================================
# Reviewed-SHA log (commit/push dedup)
# =====================================================================

# ─── push-sweep reviewed-commit tracking ────────────────────────────────────
#
# Repo-local (not session-local) record of which commits the commit-review
# hook has already reviewed, so the push-sweep can advance its diff base past
# the contiguous reviewed prefix and skip entirely when everything pushed was
# already covered. Lives under `.git/` (same precedent as CC's
# `.git/claude-trailers`) so it survives across sessions and is per-clone.
#
# Format: one line per reviewed sha, append-only:
#   <40-hex-sha>\t<unix-ts>\t<pv>\t<vulns_found>
#
# The trailing columns are observability only — load reads just the sha set.
# GC keeps the last _REVIEWED_SHAS_CAP entries; the file is small (~64 bytes
# per line) so even at the cap it's ~32KB.

_REVIEWED_SHAS_BASENAME = "sg-reviewed-shas"
_REVIEWED_SHAS_CAP = 500

def _is_full_sha(sha):
    return len(sha) == 40 and all(c in "0123456789abcdef" for c in sha)


def _reviewed_shas_path(repo_root):
    gd = _git_dir(repo_root)
    return os.path.join(gd, _REVIEWED_SHAS_BASENAME) if gd else None


def _load_reviewed_shas(repo_root, _gd=None):
    """Set of full 40-hex shas previously reviewed in this clone."""
    p = (os.path.join(_gd, _REVIEWED_SHAS_BASENAME) if _gd
         else _reviewed_shas_path(repo_root))
    if not p or not os.path.exists(p):
        return set()
    out = set()
    try:
        with open(p, "r") as f:
            for line in f:
                sha = line.split("\t", 1)[0].strip()
                if _is_full_sha(sha):
                    out.add(sha)
    except OSError:
        pass
    return out


def _append_reviewed_shas(repo_root, shas, vulns_found=0):
    """Record that `shas` were reviewed. Best-effort; never raises.

    Uses fcntl.flock for the read-gc-write; appends are O_APPEND-atomic but
    GC needs the lock so concurrent CC sessions in the same clone don't race
    each other's truncation.
    """
    p = _reviewed_shas_path(repo_root)
    if not p or not shas:
        return
    import time as _time
    ts = int(_time.time())
    pv = _PV or 0
    lines = [f"{s}\t{ts}\t{pv}\t{int(vulns_found)}\n" for s in shas]
    try:
        import fcntl
        with open(p, "a+") as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            try:
                f.seek(0)
                existing = f.read().splitlines(keepends=True)
                # Dedup by sha (first column) — keep newest, then cap.
                seen = set()
                merged = []
                for ln in (existing + lines)[::-1]:
                    sha = ln.split("\t", 1)[0].strip()
                    if sha and sha not in seen:
                        seen.add(sha)
                        merged.append(ln if ln.endswith("\n") else ln + "\n")
                merged = merged[:_REVIEWED_SHAS_CAP][::-1]
                f.seek(0)
                f.truncate()
                f.writelines(merged)
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    except (OSError, ImportError):
        # fcntl unavailable (Windows) or write failed — degrade to plain
        # append; cap enforcement happens on the next locked write.
        try:
            with open(p, "a") as f:
                f.writelines(lines)
        except OSError:
            pass


# ─── repeated-diff count ────────────────────────────────────────────────────
#
# Count only. A change that comes back under a new commit (undo and re-commit,
# rebase before the first push) is unknown to the reviewed-shas record and is
# reviewed again. These helpers say how often that happens, by remembering a
# hash of each reviewed hunk next to the reviewed-shas file. Nothing here
# decides whether a review runs, and nothing here waits on another process
# for more than a moment.

_SEEN_DIFFS_BASENAME = "sg-reviewed-diffs"
_SEEN_DIFFS_TTL_S = 7 * 24 * 3600
# Past this size the record is cut back to its newest half.
_SEEN_DIFFS_TRIM_BYTES = 1024 * 1024
_SEEN_DIFFS_MAX_KEYS = 500
_SEEN_DIFFS_LOCK_TRIES = 10

# `diff_seen` values, weakest first. A review reports the weakest of its
# hunks: 3 means every hunk already had a finished review in this clone.
DIFF_SEEN_ERROR = -1      # the record could not be read or written
DIFF_SEEN_NO = 0          # some hunk was never reviewed
DIFF_SEEN_UNFINISHED = 1  # a review of it started and has no verdict (yet)
DIFF_SEEN_OTHER_TREE = 2  # finished, on different repo contents
DIFF_SEEN_SAME_TREE = 3   # finished, on the same tree


def _hunk_keys(diff_files):
    """One hash per hunk: the path plus the hunk's lines, context included.

    The `@@` line is left out, so a hunk keeps its key when a rebase only
    moves it; the same edit next to different code gets a different key.
    """
    keys = {}
    for path, content in diff_files:
        hunks, cur = [], []
        for ln in content.split("\n"):
            if ln.startswith("@@"):
                hunks.append(cur)
                cur = []
            else:
                cur.append(ln)
        hunks.append(cur)
        for body in hunks:
            # A file's last hunk ends with the diff's trailing blank line.
            while body and not body[-1]:
                body.pop()
            if not body:
                continue
            h = hashlib.sha256(path.encode("utf-8", "replace"))
            h.update(b"\0")
            h.update("\n".join(body).encode("utf-8", "replace"))
            keys[h.hexdigest()[:16]] = None
    keys = list(keys)
    if len(keys) > _SEEN_DIFFS_MAX_KEYS:
        # Keep the record small: the hunks past the cap share one key, so
        # they only match the same set of hunks again.
        rest = hashlib.sha256(" ".join(keys[_SEEN_DIFFS_MAX_KEYS - 1:]).encode("ascii"))
        keys = keys[:_SEEN_DIFFS_MAX_KEYS - 1] + [rest.hexdigest()[:16]]
    return keys


def _seen_lock(fd):
    """True: locked. False: another process kept it. None: no flock here."""
    for _ in range(_SEEN_DIFFS_LOCK_TRIES):
        try:
            if _flock_nb(fd, exclusive=True):
                return True
        except (ImportError, OSError):
            return None
        time.sleep(0.05)
    return False


def _append_diff_row(f, locked, token, done):
    """Append one record for the review to `f`, the record opened "a+b"."""
    _, keys, tree = token
    row = f"{int(time.time())}\t{tree}\t{int(done)}\t{' '.join(keys)}\n".encode("ascii")
    size = f.seek(0, os.SEEK_END)
    if size:
        f.seek(size - 1)
        if f.read(1) != b"\n":
            row = b"\n" + row  # a torn last record must not swallow this one
    # Cutting the record back rewrites it: not while another process holds
    # the lock. Without flock at all, bounded beats exact.
    if locked is not False and size + len(row) > _SEEN_DIFFS_TRIM_BYTES:
        f.seek(0)
        keep, room = [], _SEEN_DIFFS_TRIM_BYTES // 2
        for ln in reversed(f.read().splitlines(keepends=True)):
            room -= len(ln)
            if room < 0:
                break
            keep.append(ln)
        f.seek(0)
        f.truncate()
        row = b"".join(reversed(keep)) + row
    f.write(row)
    f.flush()


def _diff_review_started(repo_root, diff_files, tip="HEAD"):
    """Note that a review of `diff_files`, a diff ending at `tip`, is starting.

    Returns (token, metrics). `metrics` is {"diff_seen": <DIFF_SEEN_* code>}:
    whether this clone already reviewed every hunk of this diff. `token` goes
    to `_diff_review_done` once the review has a verdict. Never raises.
    """
    if portable_output() or not diff_files:
        # No metrics leave the hook in portable mode, so nothing to count.
        return None, {}
    try:
        gd = _git_dir(repo_root)
        keys = _hunk_keys(diff_files)
        if not gd or not keys:
            raise ValueError("no git dir" if not gd else "no hunks")
        token = (os.path.join(gd, _SEEN_DIFFS_BASENAME), keys,
                 "".join(_full_shas(repo_root, [tip + "^{tree}"])[:1]))
        tree = token[2]
        now = time.time()
        best = dict.fromkeys(keys, DIFF_SEEN_NO)
        # Read and note under one lock, so two reviews of one diff that start
        # together cannot both miss each other.
        with open(token[0], "a+b") as f:
            locked = _seen_lock(f.fileno())
            if locked is False:
                raise OSError("record is locked")
            f.seek(0)
            for ln in f.read().decode("ascii", "replace").splitlines():
                row = ln.split("\t")
                if len(row) != 4 or not row[0].isdigit() or len(row[0]) > 12:
                    continue
                if now - int(row[0]) > _SEEN_DIFFS_TTL_S:
                    continue
                if row[2] != "1":
                    seen = DIFF_SEEN_UNFINISHED
                elif tree and row[1] == tree:
                    seen = DIFF_SEEN_SAME_TREE
                else:
                    seen = DIFF_SEEN_OTHER_TREE
                for k in row[3].split(" "):
                    if best.get(k, seen) < seen:
                        best[k] = seen
            _append_diff_row(f, locked, token, done=False)
        return token, {"diff_seen": min(best.values())}
    except Exception as e:
        debug_log(f"Repeated-diff count: not counted ({type(e).__name__}: {e})")
        return None, {"diff_seen": DIFF_SEEN_ERROR}


def _diff_review_done(token):
    """Note that the review `token` came from got a verdict. Never raises."""
    if not token:
        return
    try:
        with open(token[0], "a+b") as f:
            _append_diff_row(f, _seen_lock(f.fileno()), token, done=True)
    except Exception as e:
        debug_log(f"Repeated-diff count: verdict not noted ({type(e).__name__}: {e})")


# ─── in-flight review markers ───────────────────────────────────────────────
#
# A commit or push review records its shas only once it has a verdict, which
# is minutes after it starts. A review that starts in between (the push right
# after a commit, the next commit's reflog scan) would send the same commits
# through a second full review. So a review first takes an exclusive flock on
# `sg-inflight-<sha>`, next to the reviewed-shas file, and holds it until its
# process ends; other reviews leave a locked commit to it. The kernel drops
# the lock however the holder dies, so a killed review blocks nobody. Native
# Windows Python has no flock; there the same lock is taken with LockFileEx.
# Where files cannot be locked (some network filesystems) there are no
# markers and nothing changes.

_INFLIGHT_PREFIX = "sg-inflight-"
# A marker file nobody holds (a killed review's) is removed once this old.
_INFLIGHT_GC_AGE_S = 3600
_inflight_held = {}
# Windows refuses to delete a file that is open, so a marker is closed first
# there. Elsewhere it is deleted while still locked, so nobody can lock a
# file that is about to go.
_UNLINK_BEFORE_CLOSE = os.name != "nt"


def _full_shas(repo_root, shas):
    """Resolve abbreviated commit refs to full 40-hex shas; drops unresolved."""
    out = []
    for s in shas:
        try:
            r = subprocess.run(
                [*GIT_CMD, "rev-parse", "--verify", "-q", s],
                cwd=repo_root, capture_output=True, timeout=5,
            )
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            continue
        if r.returncode == 0:
            out.append(r.stdout.decode("utf-8", errors="replace").strip())
    return out


_win_lock_file_ex = None


def _win_lock_nb(fd, exclusive):
    """`_flock_nb` for native Windows Python, with LockFileEx.

    Shared and exclusive as with flock, never waits, and Windows drops the
    lock when the handle is closed or the holder's process ends. Windows
    locks stop other processes reading the locked bytes, so the byte locked
    is one far past the end of the (empty) marker: copying a repository while
    a review runs still reads the marker.
    """
    global _win_lock_file_ex
    import errno
    try:
        import ctypes
        import msvcrt
        if _win_lock_file_ex is None:
            from ctypes import wintypes

            class _Overlapped(ctypes.Structure):
                _fields_ = [("Internal", ctypes.c_void_p), ("InternalHigh", ctypes.c_void_p),
                            ("Offset", wintypes.DWORD), ("OffsetHigh", wintypes.DWORD),
                            ("hEvent", wintypes.HANDLE)]

            fn = ctypes.WinDLL("kernel32", use_last_error=True).LockFileEx
            fn.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.DWORD, wintypes.DWORD,
                           wintypes.DWORD, ctypes.POINTER(_Overlapped)]
            fn.restype = wintypes.BOOL
            _win_lock_file_ex = (fn, _Overlapped)
    except (ImportError, AttributeError, OSError) as e:
        raise OSError(errno.ENOLCK, f"no file locking in this Python ({e})")
    fn, _Overlapped = _win_lock_file_ex
    fail_immediately, exclusive_lock = 0x1, 0x2
    where = _Overlapped(Offset=0, OffsetHigh=0x7FFFFFFF)
    if fn(msvcrt.get_osfhandle(fd), fail_immediately | (exclusive_lock if exclusive else 0),
          0, 1, 0, ctypes.byref(where)):
        return True
    err = ctypes.get_last_error()
    if err == 33:  # ERROR_LOCK_VIOLATION: another handle holds it
        return False
    raise OSError(errno.ENOLCK, f"LockFileEx failed (WinError {err})")


def _flock_nb(fd, exclusive):
    """True when the lock was taken, False when another process holds it.
    Raises OSError when the file cannot be locked at all."""
    import errno
    if os.name == "nt":
        return _win_lock_nb(fd, exclusive)
    try:
        import fcntl
    except ImportError as e:
        raise OSError(errno.ENOLCK, f"no file locking in this Python ({e})")
    try:
        fcntl.flock(fd, (fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH) | fcntl.LOCK_NB)
        return True
    except OSError as e:
        if e.errno in (errno.EWOULDBLOCK, errno.EAGAIN):
            return False
        raise


def _again_if_refused(op, *args):
    """`op(*args)`, tried a few times where another process having the file
    open for a moment refuses it (Windows). Raises the last OSError."""
    import time as _time
    tries = 1 if _UNLINK_BEFORE_CLOSE else 3
    for attempt in range(tries):
        try:
            return op(*args)
        except PermissionError:
            if attempt == tries - 1:
                raise
            _time.sleep(0.01)


def _drop_marker(p, fd, unlink=True):
    """Close a marker this process has open and, with `unlink`, delete it, in
    the order this platform needs. Never raises. A delete that stays refused
    leaves an unlocked file, which is swept once old."""
    steps = [(_again_if_refused, os.unlink, p)] if unlink else []
    steps.insert(len(steps) if _UNLINK_BEFORE_CLOSE else 0, (os.close, fd))
    for step, *args in steps:
        try:
            step(*args)
        except OSError:
            pass


def _release_inflight():
    for p, fd in list(_inflight_held.items()):
        _drop_marker(p, fd)
    _inflight_held.clear()


def _sweep_inflight(gd):
    """Remove old marker files no review holds."""
    import time as _time
    cutoff = _time.time() - _INFLIGHT_GC_AGE_S
    for name in os.listdir(gd):
        p = os.path.join(gd, name)
        if not name.startswith(_INFLIGHT_PREFIX) or p in _inflight_held:
            continue
        try:
            if os.path.getmtime(p) > cutoff:
                continue
            fd = os.open(p, os.O_RDWR)
        except OSError:
            continue
        try:
            unheld = _flock_nb(fd, exclusive=True)
        except OSError:
            unheld = False
        _drop_marker(p, fd, unlink=unheld)


def _mark_inflight(repo_root, shas):
    """Claim `shas` (full 40-hex) for the review this process is about to
    run, until the process ends. Best-effort; never raises. A commit another
    live review holds stays with that review."""
    try:
        gd = _git_dir(repo_root)
        if not gd:
            return
        _sweep_inflight(gd)
        for sha in shas:
            p = os.path.join(gd, _INFLIGHT_PREFIX + sha)
            if not _is_full_sha(sha) or p in _inflight_held:
                continue
            try:
                fd = _again_if_refused(os.open, p, os.O_RDWR | os.O_CREAT, 0o600)
            except OSError:
                # One marker that cannot be opened does not cost the others
                # their claim.
                continue
            try:
                held = _flock_nb(fd, exclusive=True)
            except OSError:
                # Cannot lock here at all: leave no file that reads as held.
                _drop_marker(p, fd)
                return
            if held and _UNLINK_BEFORE_CLOSE:
                # The inode check: a holder unlinks its marker when it ends,
                # and a lock on that unlinked file would claim nothing. Not
                # where an open file cannot be unlinked in the first place.
                try:
                    held = os.fstat(fd).st_ino == os.stat(p).st_ino
                except OSError:
                    held = False
            if not held:
                os.close(fd)
                continue
            if not _inflight_held:
                import atexit
                atexit.register(_release_inflight)
            _inflight_held[p] = fd
            os.utime(p)
    except Exception:
        pass


def _load_inflight_shas(repo_root, shas, _gd=None):
    """Which of `shas` another live review in this clone holds right now."""
    out = set()
    gd = _gd or _git_dir(repo_root)
    if not gd:
        return out
    for sha in shas:
        p = os.path.join(gd, _INFLIGHT_PREFIX + sha)
        if not _is_full_sha(sha) or p in _inflight_held:
            continue
        try:
            fd = os.open(p, os.O_RDONLY)
        except OSError:
            continue
        try:
            # Shared, so two reviews asking at once do not look like a
            # holder to each other.
            if not _flock_nb(fd, exclusive=False):
                out.add(sha)
        except OSError:
            pass
        os.close(fd)
    return out


def _reviewed_after_inflight(repo_root, push_range, max_wait_s, poll_s=1.0):
    """The reviewed-sha set for a push of `push_range` (oldest first), read
    once no other review is still running on the commit the push review
    would start from, or after `max_wait_s`. Returns (reviewed, waited_s)."""
    import time as _time
    gd = _git_dir(repo_root)
    start = _time.monotonic()
    waited = False
    reviewed = _load_reviewed_shas(repo_root, _gd=gd)
    while gd:
        # Only the first unreviewed commit matters: if nobody is reviewing
        # it, the push review covers everything from there on anyway.
        first = next((s for s in push_range if s not in reviewed), None)
        if first is None:
            break
        # In-flight before reviewed: a review that ends between the two
        # reads then shows up as reviewed rather than as neither.
        busy = _load_inflight_shas(repo_root, [first], _gd=gd)
        reviewed = _load_reviewed_shas(repo_root, _gd=gd)
        if first in reviewed:
            continue
        if not busy or _time.monotonic() - start >= max_wait_s:
            break
        waited = True
        _time.sleep(poll_s)
    return reviewed, (_time.monotonic() - start) if waited else 0.0


# =====================================================================
# v2 review-set computation (Stop hook)
# =====================================================================

UNTRACKED_BASELINE_CAP = 2000
# Set in a snapshot that hit the cap, to the time the listing started. NUL
# cannot occur in a path, so the key never collides with a file.
UNTRACKED_CAPPED_AT_KEY = "\0capped_at_ns"
# Coarse filesystem timestamps (1 s on ext3, 2 s on FAT) can stamp a file
# created just after the snapshot as slightly older than it.
_CAPPED_BASELINE_SLACK_NS = 2_000_000_000


def _list_untracked(cwd):
    """Repo-root-relative untracked (and not-ignored) path → mtime_ns, or {}
    on error. Used at UPS to snapshot the pre-turn untracked set so the Stop
    hook can exclude unchanged pre-existing untracked files from review.
    mtime is captured so an in-place edit during the turn is still reviewed.

    Uses ls-files (not status) for the UPS path: the index diff isn't needed,
    and ls-files --others only walks the worktree against .gitignore.

    Decodes stdout/stderr as UTF-8 with errors="replace" instead of using
    text=True. With core.quotePath=false git emits raw UTF-8 bytes for
    non-ASCII filenames; text=True decodes via locale.getpreferredencoding()
    in strict mode — on Windows that's cp1252 with several undefined bytes
    (0x81/0x8D/0x8F/0x90/0x9D), all of which appear in UTF-8 encodings of
    common accented capitals (Á Í Ï Ð Ý) and most CJK/emoji codepoints.
    A non-ASCII filename in the worktree crashed the subprocess reader
    thread, left r.stdout=None, and propagated AttributeError out of the
    helper — silently losing the baseline snapshot every UserPromptSubmit.
    See anthropics/claude-plugins-official#2056. The sibling helpers in
    gitutil.py already follow the lenient pattern; this function and
    capture_git_baseline / _git_name_only / _git_status_porcelain were
    the holdouts."""
    try:
        repo = _git_toplevel(cwd) or cwd
        started_ns = time.time_ns()
        # core.quotePath=false comes from GIT_CMD globally (see gitutil.py).
        r = subprocess.run(
            [*GIT_CMD, "ls-files", "--others", "--exclude-standard", "-z"],
            cwd=repo, capture_output=True, timeout=15,
        )
        if r.returncode != 0:
            stderr_str = (r.stderr or b"").decode("utf-8", errors="replace")
            debug_log(f"_list_untracked rc={r.returncode}: {stderr_str[:200]}")
            return {}
        stdout = (r.stdout or b"").decode("utf-8", errors="replace")
        out = {}
        for p in stdout.split("\0"):
            if not p:
                continue
            try:
                out[p] = os.stat(os.path.join(repo, p)).st_mtime_ns
            except OSError:
                out[p] = 0
            if len(out) >= UNTRACKED_BASELINE_CAP:
                debug_log(f"_list_untracked: capped at {UNTRACKED_BASELINE_CAP}")
                # The files past the cap are not recorded one by one. Record
                # when the snapshot was taken so the Stop hook can still tell
                # them from files created or edited during the turn.
                out[UNTRACKED_CAPPED_AT_KEY] = started_ns
                break
        return out
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError, ValueError) as e:
        # ValueError guards against any future strict-decode regression
        # so the helper degrades to {} instead of crashing the hook.
        debug_log(f"_list_untracked error: {e}")
        return {}

def compute_v2_review_set(cwd, baseline_sha, head_at_capture, untracked_at_baseline=None,
                          since_ns=None):
    """v2 diff strategy: derive the review set from git state alone.

    review_set = (files dirty vs current HEAD, plus files committed this turn
    when HEAD advanced linearly) ∩ (files whose content differs from the
    pre-turn stash baseline). The first term is immune to checkout/pull
    ballooning; the second filters out the user's untouched pre-turn WIP.
    Falls back to dirty_now alone when no baseline is available.

    untracked_at_baseline: {repo-root-relative path: mtime_ns} captured at
    UPS. `git stash create` doesn't include untracked files, so without this
    snapshot a pre-existing untracked file looks "new since baseline" forever.
    A file is excluded only if it was untracked at baseline AND its mtime is
    unchanged — an in-place edit during the turn is still reviewed.

    since_ns: for a checkout the prompt hook took no baseline or snapshot of
    (the turn moved into it), the time the turn began. A dirty or untracked
    file last written before then was already that way and is left out.

    Known limitation: a Bash-only turn that's interrupted before Stop fires
    leaves touched_paths empty, so the next UPS re-baselines past those edits.
    v1 never reviews Bash-only turns at all, so v2 is no worse there.

    Returns (absolute paths sorted, diff_base, repo_root, metrics).
    diff_base is "HEAD" unless HEAD advanced linearly this turn (commits),
    in which case it's head_at_capture so committed files produce a diff.
    repo_root is the git toplevel — `git diff --name-only` outputs paths
    relative to it (not to cwd), so the caller's get_git_diff must run
    from there too or pathspecs won't match.

    Also returns the untracked subset of review_set so get_git_diff can do
    a targeted `add -N -- <files>` instead of a whole-tree scan.
    """
    repo = _git_toplevel(cwd) or cwd
    if not isinstance(untracked_at_baseline, dict):
        untracked_at_baseline = {}

    tracked_dirty, untracked = _git_status_porcelain(repo)
    if tracked_dirty is None:
        return [], "HEAD", repo, [], {"dirty_now_count": -1, "changed_since_count": -1, "review_set_count": 0}

    capped_at_ns = untracked_at_baseline.get(UNTRACKED_CAPPED_AT_KEY)

    def _unchanged_since_baseline(p):
        base_mtime = untracked_at_baseline.get(p)
        try:
            st = os.stat(os.path.join(repo, p))
        except OSError:
            return False
        if base_mtime is not None:
            return st.st_mtime_ns == base_mtime
        if not capped_at_ns:
            return False
        # The snapshot stopped at the cap, so this file may simply be one it
        # never reached. Without this, every pre-existing file past the cap
        # looks new on every turn and the same files are reviewed again and
        # again. A file created or edited during the turn has a later mtime
        # or ctime than the snapshot; anything older was already there.
        return max(st.st_mtime_ns, st.st_ctime_ns) < capped_at_ns - _CAPPED_BASELINE_SLACK_NS

    preexisting_unchanged = {p for p in untracked if _unchanged_since_baseline(p)}
    if since_ns:
        def _written_before_turn(p):
            try:
                st = os.stat(os.path.join(repo, p))
            except OSError:
                return False
            return max(st.st_mtime_ns, st.st_ctime_ns) < since_ns - _CAPPED_BASELINE_SLACK_NS

        preexisting_unchanged |= {p for p in untracked if _written_before_turn(p)}
        tracked_dirty = {p for p in tracked_dirty if not _written_before_turn(p)}
    new_untracked = untracked - preexisting_unchanged
    dirty_now = tracked_dirty | new_untracked

    diff_base = "HEAD"
    current_head = _git_rev_parse_head(repo)
    if (head_at_capture and current_head and head_at_capture != current_head
            and _is_ancestor(repo, head_at_capture, current_head)):
        dirty_now |= _git_name_only(repo, f"{head_at_capture}..HEAD") or set()
        diff_base = head_at_capture

    # changed_since: tracked files vs the stash baseline (no `add -N` — the
    # stash never contained untracked files anyway), then union with
    # currently-untracked. The previous `include_untracked=True` arm cost a
    # full `git add -N .` (slow in large repos) per call to surface
    # untracked files in the diff output — but `git diff <stash>` already
    # lists them as "only in worktree" without that, and we have the explicit
    # set from status regardless.
    if baseline_sha:
        changed_since = _git_name_only(repo, baseline_sha)
        if changed_since is not None:
            changed_since |= new_untracked
    else:
        changed_since = None
    # changed_since is None on missing baseline OR on git error (e.g. the
    # dangling stash SHA was pruned). Either way, don't intersect with ∅ —
    # that would silently zero the review set. Fall back to dirty_now.
    review_set = (dirty_now & changed_since) if changed_since is not None else dirty_now
    # Kept beside its new name so that the content diff pairs the two.
    secret_origins = {
        old for new, old in _secret_rename_origins.items() if new in review_set}
    review_set = review_set | secret_origins

    review_paths = [os.path.join(repo, p) for p in sorted(review_set)]
    untracked_in_review = sorted(new_untracked & review_set)
    metrics = {
        "dirty_now_count": len(dirty_now),
        "changed_since_count": len(changed_since) if changed_since is not None else -1,
        "review_set_count": len(review_set),
    }
    # Only emit when nonzero to stay under the 10-key telemetry cap.
    if preexisting_unchanged:
        metrics["preexisting_untracked_excluded"] = len(preexisting_unchanged)
    if secret_origins:
        metrics["secret_renamed"] = len(secret_origins)
    return review_paths, diff_base, repo, untracked_in_review, metrics
