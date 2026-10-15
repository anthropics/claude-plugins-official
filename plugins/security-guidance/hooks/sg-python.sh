#!/usr/bin/env bash
# Find a working Python 3 interpreter and exec the hook with it.
#
# On Windows + Git Bash, `python3` typically resolves to the Microsoft Store
# stub at C:\Users\<user>\AppData\Local\Microsoft\WindowsApps\python3, which
# exits 49 silently in non-TTY subprocess context or, as an App Installer
# redirector, never exits at all. This shim
# probes each candidate with `-c ""` under a time limit and skips any that
# fails or does not answer, so the Store
# stub falls through to the real python.org install (`python` in Git Bash) or
# the `py -3` launcher.
#
# Order:
#   1. python3   — canonical on macOS/Linux; the Store stub fails the probe.
#   2. python    — python.org installs on Windows; some Linux distros (RHEL 7
#                  EOL'd 2024-06) point this at Python 2, but `-c ""` succeeds
#                  on Python 2 too — guard with a version check.
#   3. py -3     — Windows Python launcher.
#
# Args after the shim path are passed straight through to the chosen
# interpreter, so the hooks.json invocation is:
#   bash "${CLAUDE_PLUGIN_ROOT}/hooks/sg-python.sh" \
#        "${CLAUDE_PLUGIN_ROOT}/hooks/security_reminder_hook.py"
set -e

# Force UTF-8 for ALL Python filesystem + IO operations (PEP 540).
# Without this, Windows Python defaults `locale.getpreferredencoding()` to
# cp1252 — which makes `text=True` in subprocess.run / open() / json.load
# crash the internal reader thread on any byte that's undefined in cp1252
# (e.g. the 0x81 byte from ف, present in any path/filename with
# Arabic/Hebrew/CJK characters). See #2056, #2099.
#
# No-op on macOS/Linux (already UTF-8). Must be set BEFORE Python starts —
# changing it from inside the interpreter has no effect.
export PYTHONUTF8=1

# Set to 1 below only when the interpreter had to be found by its real path
# (pass 4); the hook reports it as the `launcher_fallback` metric.
unset SG_LAUNCHER_FALLBACK

# Git Bash / MSYS on Windows hands script paths to this shim in POSIX form
# (`/c/Users/...`). When we exec a Windows `python.exe` (which we do on
# Windows since `python3` is the Microsoft Store stub), python interprets the
# leading `/` as the root of the current drive — e.g. `/c/Users/...` becomes
# `C:\c\Users\...` or `D:\c\Users\...` (whichever drive the shell is on),
# fails with ENOENT, and every Edit/Write/MultiEdit tool use blocks until the
# session restarts. See anthropics/claude-plugins-official#2043.
#
# Fix: convert absolute path args to native Windows form before exec.
# `cygpath` ships with Git Bash; it's absent on macOS/Linux, where the
# `command -v` guard makes this a no-op. `cygpath -w` is idempotent for
# already-Windows paths so the rare mixed-form case is safe.
#
# Under Git Bash every $(...) is a new Windows process, and this shim runs on
# every hook, so drive paths (`/c/Users/...`, where the plugin lives) are
# converted in-shell. Git Bash and MSYS2 (OSTYPE=msys) mount drives at
# /<letter>; anything else (`/tmp`, `/usr`, Cygwin's /cygdrive) needs cygpath
# to resolve. See #6470.
if command -v cygpath >/dev/null 2>&1; then
    sg_drive_mounts=""
    case "${OSTYPE:-}" in msys*) sg_drive_mounts=1 ;; esac
    converted=()
    for a in "$@"; do
        case "$a" in
            /[A-Za-z]/*)
                if [ -n "$sg_drive_mounts" ]; then
                    drive="${a:1:1}"
                    rest="${a:3}"
                    converted+=("${drive^^}:\\${rest//\//\\}")
                else
                    converted+=("$(cygpath -w "$a")")
                fi ;;
            /*) converted+=("$(cygpath -w "$a")") ;;
            *)  converted+=("$a") ;;
        esac
    done
    set -- "${converted[@]}"
fi

# The hook script the chosen interpreter has to run (already in native form).
SG_TARGET=""
case "${1:-}" in
    ""|-*) ;;
    *) SG_TARGET="$1" ;;
esac

# Names whose interpreter runs but cannot see the hook script ("|"-separated).
sg_unreadable=""

# Seconds a candidate gets to answer. A candidate can block instead of
# failing: on Windows the python3 / python3.x entries under
# ...\Microsoft\WindowsApps may be an App Installer redirector that never
# exits when started without a console. Waited for without a limit, one such
# name ahead of a working `python` stalls every hook until the host's hook
# timeout (minutes per Edit). See #6315, #3870.
# SG_PROBE_TIMEOUT=<seconds> changes the limit; 0 waits forever, as before.
sg_probe_secs="${SG_PROBE_TIMEOUT:-5}"
case "$sg_probe_secs" in ""|*[!0-9]*) sg_probe_secs=5 ;; esac
sg_probe_secs=$((10#$sg_probe_secs))
# Commands that did not answer in time; the hook reports how many as the
# `launcher_probe_timeout` metric.
sg_slow=()
unset SG_LAUNCHER_PROBE_TIMEOUTS

# Runs "$@" and leaves the first line it prints in $sg_line. Returns 0 with a
# line, 4 if none came within the limit, 1 otherwise.
#
# The wait is bash's own `read -t` on a process substitution, not `$(...)`
# under an external `timeout`: no extra process (see #6470), and the limit
# holds even when the candidate cannot be killed or leaves a child holding
# the pipe. The candidate gets no stdin, which belongs to the hook.
ask() {
    local rc=0 start=$SECONDS
    sg_line=""
    if [ "$sg_probe_secs" -gt 0 ]; then
        IFS= read -r -t "$sg_probe_secs" sg_line < <(exec "$@" 2>/dev/null </dev/null) || rc=$?
    else
        IFS= read -r sg_line < <(exec "$@" 2>/dev/null </dev/null) || rc=$?
    fi
    sg_line=${sg_line%$'\r'}  # native Windows Python prints CRLF
    [ "$rc" -ne 0 ] || return 0
    sg_line=""
    # read reports a timeout as a status above 128; bash 3.2 (stock macOS)
    # returns 1, so there it is told from a failure by the time it took.
    [ "$rc" -gt 128 ] || { [ "$sg_probe_secs" -gt 0 ] && [ $((SECONDS - start)) -ge "$sg_probe_secs" ]; } || return 1
    # Still running. $! is the process substitution from bash 4.4 on; KILL
    # because the redirectors ignore TERM.
    [ -z "${!:-}" ] || kill -9 "$!" 2>/dev/null || true
    return 4
}

probe() {
    # $1..N: the interpreter command (may be multi-word like `py -3`)
    # Sets $v to "<major>.<minor>" and returns 0 iff it is at least
    # Python 3 AND it can read the hook script; returns 3 if it cannot, 4 if
    # it did not answer in time.
    #
    # The second half matters on Windows: an interpreter started through a
    # packaged launcher alias (Microsoft Store Python, Python Install Manager;
    # the python/python3/py entries under ...\Microsoft\WindowsApps) runs with
    # a different view of %APPDATA% than the process that started it. It
    # answers `-c` fine, then fails on the script with "can't open file ...
    # [Errno 2]" and exit code 2 -- and exit 2 from an asyncRewake hook wakes
    # the model, whose reply runs the Stop hook again: an endless loop that
    # never reviewed anything. See #6251, #5781.
    v=""
    ask "$@" -c 'import os, sys; t = (sys.argv[1:] or [""])[0]; print("unreadable" if t and not (os.path.isfile(t) and os.access(t, os.R_OK)) else f"{sys.version_info[0]}.{sys.version_info[1]}")' "$SG_TARGET" || return $?
    [ "$sg_line" != "unreadable" ] || return 3
    v=$sg_line
}

# Use as `probe ... || { note_failed "<name>"; continue; }`.
note_failed() {
    case $? in
        3) sg_unreadable="$sg_unreadable|$1|" ;;
        4)
            sg_slow+=("$1")
            export SG_LAUNCHER_PROBE_TIMEOUTS=${#sg_slow[@]} ;;
    esac
    return 0
}

# True iff the command's executable is on PATH ($1 of a possibly multi-word
# command like `py -3`). A builtin lookup: a probe costs a process even
# when the interpreter does not exist, so missing names are skipped first.
on_path() {
    command -v "$1" >/dev/null 2>&1
}

# True iff arg is a "M.m" version string >= 3.10. claude_agent_sdk requires
# Python >= 3.10; below that, pip install fails ("No matching distribution")
# and the LLM-powered review (Stop / commit / push) silently no-ops while
# pattern checks (PostToolUse regex) keep working. macOS ships 3.9.6 as the
# default `python3` on current versions, so this guard matters in practice.
# See anthropics/claude-plugins-official#2071.
is_sdk_compatible() {
    case "$1" in
        3.1[0-9]|3.[2-9][0-9]|[4-9].*|[1-9][0-9].*) return 0 ;;
        *) return 1 ;;
    esac
}

# Pass 1 — try minor-versioned binaries in descending order. These are only
# present if the user explicitly installed them (Homebrew / python.org / pyenv),
# so picking one here always upgrades over the system `python3`. Highest
# available wins; the user doesn't have to PATH-prefer it.
for cmd in "python3.13" "python3.12" "python3.11" "python3.10"; do
    on_path "$cmd" || continue
    probe "$cmd" || { note_failed "$cmd"; continue; }
    if is_sdk_compatible "$v"; then
        exec "$cmd" "$@"
    fi
done

# Pass 2 — bare interpreters, but only if SDK-compatible. Covers Linux distros
# that ship 3.10+ as the default `python3`, and Windows where `python` /
# `py -3` resolves to the user's python.org install.
sg_older=""  # first of these that is a readable Python 3 below 3.10
for cmd in "python3" "python" "py -3"; do
    # shellcheck disable=SC2086
    on_path $cmd || continue
    # shellcheck disable=SC2086
    probe $cmd || { note_failed "$cmd"; continue; }
    if is_sdk_compatible "$v"; then
        # shellcheck disable=SC2086
        exec $cmd "$@"
    fi
    # Anything that successfully reported a "M.m" string.
    case "$v" in
        [0-9]*.[0-9]*) [ -n "$sg_older" ] || sg_older="$cmd" ;;
    esac
done

# Pass 3 — fallback to any Python 3, even <3.10. Pattern-based checks
# (PostToolUse regex on Edit/Write) only need 3.6+ and are useful on their
# own; the SDK-dependent paths will detect the version mismatch and degrade
# inside the Python code. Without this fallback, the entire plugin would
# stop working on default macOS, which is a regression vs today.
if [ -n "$sg_older" ]; then
    # shellcheck disable=SC2086
    exec $sg_older "$@"
fi

# Pass 4 — nothing above could run the hook script. If that is because the
# names on PATH resolve to packaged launcher aliases that cannot see the
# plugin directory (see probe), the same interpreter usually works when it is
# started by its real path instead of through the alias. Candidates:
#   - every further python3/python on PATH, by full path (a regular install
#     often sits behind the alias in PATH order; the first match is the one
#     the bare name resolved to above),
#   - the real executable each alias reports as sys.executable.
# The list is built before the loop that execs, and from a here-document: a
# redirect around that loop would become the hook's stdin.
sg_candidates=()
for name in "python3" "python"; do
    first=1
    while IFS= read -r c; do
        if [ -n "$first" ]; then first=""; continue; fi
        [ -n "$c" ] && sg_candidates+=("$c")
    done <<EOF
$(type -ap "$name" 2>/dev/null)
EOF
done
for cmd in "python3" "python" "py -3"; do
    case "$sg_unreadable" in *"|$cmd|"*) ;; *) continue ;; esac
    # shellcheck disable=SC2086
    ask $cmd -c 'import sys; print(sys.executable)' || { note_failed "$cmd"; continue; }
    c=$sg_line
    [ -n "$c" ] || continue
    if command -v cygpath >/dev/null 2>&1; then
        c=$(cygpath -u "$c" 2>/dev/null) || continue
    fi
    sg_candidates+=("$c")
done
export SG_LAUNCHER_FALLBACK=1
sg_fallback=""
sg_tried="|"
for cmd in "${sg_candidates[@]}"; do
    case "$sg_tried" in *"|$cmd|"*) continue ;; esac
    sg_tried="$sg_tried$cmd|"
    probe "$cmd" || { note_failed "$cmd"; continue; }
    if is_sdk_compatible "$v"; then
        exec "$cmd" "$@"
    fi
    case "$v" in
        [0-9]*.[0-9]*) [ -n "$sg_fallback" ] || sg_fallback="$cmd" ;;
    esac
done
if [ -n "$sg_fallback" ]; then
    exec "$sg_fallback" "$@"
fi

# Nothing ran the hook. A command that was skipped for not answering in time
# may be a working interpreter on a slow start (cold disk, scanner, network
# mount), so each gets one longer try before giving up.
sg_metrics=""
if [ ${#sg_slow[@]} -gt 0 ]; then
    sg_timeouts=${#sg_slow[@]}
    sg_first_secs=$sg_probe_secs
    sg_probe_secs=$((sg_probe_secs * 3))
    for cmd in "${sg_slow[@]}"; do
        # shellcheck disable=SC2086
        probe $cmd || continue
        case "$v" in
            [0-9]*.[0-9]*)
                # shellcheck disable=SC2086
                exec $cmd "$@"
                ;;
        esac
    done
    echo "security-guidance: no answer within ${sg_first_secs}s, then ${sg_probe_secs}s, from: ${sg_slow[*]}" >&2
    echo "  on Windows these are usually App execution aliases; turn them off under" >&2
    echo "  Settings > Apps > Advanced app settings > App execution aliases" >&2
    sg_metrics="\"launcher_probe_timeout\": $sg_timeouts"
fi

# Exit 1, never 2: on an asyncRewake hook exit 2 means "the review has
# findings, wake the model", and a launcher failure is not a finding.
# No Python to report metrics, so the launcher prints them itself.
if [ -n "$sg_unreadable" ]; then
    echo "security-guidance: found Python, but it cannot read the hook script (missing, or not visible to Python), so no security checks ran." >&2
    echo "  hook script: $SG_TARGET" >&2
    echo "  on Windows this happens when python, python3 and py are Microsoft Store or Python Install Manager aliases;" >&2
    echo "  install Python from https://python.org and put it ahead of ...\\Microsoft\\WindowsApps in PATH" >&2
    echo "{\"metrics\": {\"launcher_unreadable\": 1${sg_metrics:+, $sg_metrics}}}"
    exit 1
fi
[ -z "$sg_metrics" ] || echo "{\"metrics\": {$sg_metrics}}"
echo "security-guidance: no working Python 3 interpreter found." >&2
echo "  tried: python3.13, python3.12, python3.11, python3.10, python3, python, py -3" >&2
echo "  on Windows, install Python from https://python.org (NOT the Microsoft Store)" >&2
echo "  on macOS, install Python 3.10+ via Homebrew (\`brew install python\`)" >&2
exit 1
