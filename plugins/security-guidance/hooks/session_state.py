"""
Per-session state-file plumbing for the security-guidance plugin.

Holds the JSON state file location, fcntl-locked read-modify-write helper,
and old-file GC. Side-effect-free at import time (no env-var reads beyond
``CLAUDE_CODE_REMOTE_SESSION_ID`` inside the helpers).

The ``atomic_check_*`` helpers that build on ``with_locked_state`` deliberately
remain in ``security_reminder_hook.py`` so that tests which monkeypatch
``hook.with_locked_state`` and then call a handler still see the patched
binding via the handler → ``atomic_check_*`` → bare-name lookup chain.
"""
try:
    import fcntl
except ImportError:
    fcntl = None
import json
import os
import re
import tempfile
from datetime import datetime

from _base import debug_log, make_state_dir, state_dir as _state_dir


def _state_key(session_id):
    # In CCR each user turn is a new CC process with a fresh session_id; the
    # remote session ID is stable across those restarts. Prefer it so the
    # pending-warnings sweep and any unprocessed touched_paths survive.
    key = os.environ.get("CLAUDE_CODE_REMOTE_SESSION_ID") or session_id
    # The key becomes a filename component under the state dir. CC session ids
    # are UUIDs (sanitization is a no-op for them), but nothing in the hook
    # protocol guarantees that, so strip path separators and anything else
    # that could escape the state dir, and bound the length.
    return re.sub(r"[^A-Za-z0-9._-]", "_", str(key))[:128]


def get_state_file(session_id):
    """Get session-specific state file path."""
    state_dir = _state_dir()
    return os.path.join(state_dir, f"security_warnings_state_{_state_key(session_id)}.json")


def get_lock_file(session_id):
    """Get session-specific lock file path."""
    state_dir = _state_dir()
    return os.path.join(state_dir, f"security_warnings_state_{_state_key(session_id)}.lock")


def get_commit_log_file(session_id):
    """Where diffstate notes the commits a session's hooks saw and counted."""
    state_dir = _state_dir()
    return os.path.join(state_dir, f"security_warnings_state_{_state_key(session_id)}.commits")


def commit_log_files(newer_than):
    """Those files of all sessions, written to since `newer_than` (epoch
    seconds, with some slack for coarse file times)."""
    state_dir = _state_dir()
    out = []
    try:
        for name in os.listdir(state_dir):
            if name.startswith("security_warnings_state_") and name.endswith(".commits"):
                path = os.path.join(state_dir, name)
                try:
                    if os.path.getmtime(path) >= newer_than - 5:
                        out.append(path)
                except OSError:
                    pass
    except OSError:
        pass
    return out


def cleanup_old_state_files():
    """Remove state files, lock files and leftover temporary files older than 30 days."""
    try:
        state_dir = _state_dir()
        if not os.path.exists(state_dir):
            return

        current_time = datetime.now().timestamp()
        thirty_days_ago = current_time - (30 * 24 * 60 * 60)

        for filename in os.listdir(state_dir):
            if filename.startswith("security_warnings_state_") and (
                filename.endswith((".json", ".lock", ".tmp", ".commits"))
            ):
                file_path = os.path.join(state_dir, filename)
                try:
                    file_mtime = os.path.getmtime(file_path)
                    if file_mtime < thirty_days_ago:
                        os.remove(file_path)
                except (OSError, IOError):
                    pass

        # Sweep legacy lock files left at ~/.claude/ root by versions
        # <1.1.66, where get_lock_file() didn't honor state_dir. Same
        # 30-day mtime gate as above so we don't race an older
        # concurrent peer that may still hold an active lock.
        legacy_dir = os.path.expanduser("~/.claude")
        for filename in os.listdir(legacy_dir):
            if filename.startswith("security_warnings_state_") and filename.endswith(".lock"):
                file_path = os.path.join(legacy_dir, filename)
                try:
                    if os.path.getmtime(file_path) < thirty_days_ago:
                        os.remove(file_path)
                except (OSError, IOError):
                    pass
    except Exception:
        pass


def load_state(session_id):
    """Load the full state dict from file."""
    state_file = get_state_file(session_id)
    try:
        with open(state_file, "r") as f:
            data = json.load(f)
            if isinstance(data, list):
                return {"shown_warnings": data}
            if isinstance(data, dict):
                data.setdefault("shown_warnings", [])
                return data
    except FileNotFoundError:
        return {"shown_warnings": []}
    except (ValueError, IOError, KeyError, TypeError):
        # ValueError: not JSON, or bytes that do not decode.
        pass
    # The file is there but cannot be used, so everything the session had
    # recorded is gone. Leave a mark for the Stop hook to report: a flag, not
    # a count, since an earlier mark is lost with the rest.
    debug_log(f"State file {state_file} is unreadable, starting from an empty state")
    return {"shown_warnings": [], "state_resets": 1}


# Windows still writes the state file in place: a rename there is refused
# while another process has the file open and can make a concurrent open fail,
# and hooks run without a state lock on Windows (see with_locked_state).
_RENAME_INTO_PLACE = os.name != "nt"


def _write_then_rename(state_file, state):
    """Write `state` to a temporary file and rename it over `state_file`.
    Returns False, with nothing changed, when this directory does not allow
    it; any other failure raises OSError and leaves the state file as it was."""
    tmp = None
    try:
        fd, tmp = tempfile.mkstemp(
            dir=os.path.dirname(state_file),
            prefix=os.path.basename(state_file) + ".", suffix=".tmp")
        with os.fdopen(fd, "w") as f:
            json.dump(state, f)
        os.replace(tmp, state_file)
        return True
    except BaseException as e:
        if tmp:
            try:
                os.unlink(tmp)
            except OSError:
                pass
        if isinstance(e, PermissionError):
            return False
        raise


def _write_in_place(state_file, state):
    """The fallback (Windows, or a folder that refuses the rename) writes the
    state file itself. As with the rename, a link there is replaced, not
    followed, and a new file is the user's only, as the temporary file is."""
    if os.path.islink(state_file):
        os.unlink(state_file)
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(state_file, flags, 0o600)
    with os.fdopen(fd, "w") as f:
        json.dump(state, f)


def save_state(session_id, state):
    """Save the full state dict to file.

    The new contents go to a temporary file that is then renamed over the
    state file, so a hook killed part-way through a save (a timeout, an
    interrupt) leaves the previous state. Written in place it left a truncated
    file, which load_state reads as an empty state: the turn baseline, touched
    paths and shown warnings were lost.
    """
    state_file = get_state_file(session_id)
    try:
        state_dir = os.path.dirname(state_file)
        if state_dir:
            make_state_dir(state_dir)

        if _RENAME_INTO_PLACE and _write_then_rename(state_file, state):
            return
        _write_in_place(state_file, state)
    except (IOError, OSError) as e:
        debug_log(f"Failed to save state file {state_file}: {e}")


def _raw_state(state_file):
    try:
        with open(state_file, "rb") as f:
            return f.read()
    except OSError:
        return None


def with_locked_state(session_id, callback):
    """
    Execute callback with exclusive access to the state file.
    The callback receives the state dict and can modify it in place.
    State is saved after the callback returns.
    Returns the callback's return value.
    """
    lock_file = get_lock_file(session_id)
    state_dir = os.path.dirname(lock_file)

    try:
        make_state_dir(state_dir)
    except OSError:
        pass

    if fcntl is None:
        # No file locking available (Windows) — run without locking
        state_file = get_state_file(session_id)
        before = _raw_state(state_file)
        state = load_state(session_id)
        result = callback(state)
        if _raw_state(state_file) != before:
            # Another hook changed the state after it was read here, and this
            # save is about to drop that change. Count how often it happens;
            # the Stop hook reports the count.
            state["state_overwrites"] = state.get("state_overwrites", 0) + 1
        save_state(session_id, state)
        return result

    lock_fd = None
    try:
        lock_fd = os.open(lock_file, os.O_RDWR | os.O_CREAT)
        fcntl.flock(lock_fd, fcntl.LOCK_EX)

        state = load_state(session_id)
        result = callback(state)
        save_state(session_id, state)
        return result

    except (OSError, IOError) as e:
        debug_log(f"Lock/state operation failed: {e}")
        return None

    finally:
        if lock_fd is not None:
            try:
                fcntl.flock(lock_fd, fcntl.LOCK_UN)
                os.close(lock_fd)
            except (OSError, IOError):
                pass

