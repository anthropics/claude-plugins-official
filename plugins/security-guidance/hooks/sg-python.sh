#!/usr/bin/env bash
# Find a working Python 3 interpreter and exec the hook with it.
#
# On Windows + Git Bash, `python3` typically resolves to the Microsoft Store
# stub at C:\Users\<user>\AppData\Local\Microsoft\WindowsApps\python3, which
# exits 49 silently in non-TTY subprocess context (a known Microsoft Store
# stub behavior). This shim
# probes each candidate with `-c ""` and skips any that fails, so the Store
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

probe() {
    # Probe writes "<major>.<minor>" and exits 0 iff resolvable.
    "$@" -c 'import sys; print("%d.%d" % sys.version_info[:2])' 2>/dev/null
}

# Sort version strings; returns 0 iff $1 >= $2.
ver_ge() { [ "$(printf '%s\n%s\n' "$1" "$2" | sort -V | head -1)" = "$2" ]; }

for cmd in "python3.13" "python3.12" "python3.11" "python3.10" "python3.9" "python3.8" "python3.7" "python3" "python" "py -3"; do
    # shellcheck disable=SC2086
    v=$(probe $cmd) || continue
    # Need >=3.7 because review_api.py uses `from __future__ import annotations`
    # (PEP 563, added in 3.7). Bare `python3` is 3.6 on Ubuntu 18.04 LTS.
    if ver_ge "$v" "3.7"; then
        # shellcheck disable=SC2086
        exec $cmd "$@"
    fi
done

echo "security-guidance: no working Python 3 interpreter found." >&2
echo "  tried: python3, python, py -3" >&2
echo "  on Windows, install Python from https://python.org (NOT the Microsoft Store)" >&2
exit 1
