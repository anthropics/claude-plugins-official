#!/usr/bin/env bash
# Hold the Security Lead's turn while the scan workflow runs: wait, then tell the
# caller to run this again unless the workflow's result has arrived.
# Usage: keep-waiting.sh [SECONDS]   (1 to 110, default 30; exits 2 on a bad value)
# The wait stays under the Bash tool's two-minute default timeout, past which a
# command is moved to the background and no longer holds the turn.
seconds=${1:-30}
case $seconds in '' | *[!0-9]*) seconds=0 ;; esac
if [ "$seconds" -lt 1 ] || [ "$seconds" -gt 110 ]; then
  echo "usage: keep-waiting.sh [SECONDS between 1 and 110]" >&2
  exit 2
fi
sleep "$seconds"
echo "Waited ${seconds}s. If the scan workflow's result has not arrived, run this same command again now; do not reply to the user or end your turn until it arrives."
