#!/usr/bin/env bash
# Hold a session's or agent's turn while a workflow or agent it launched runs.
# The wait stays under the Bash tool's two-minute default timeout, past which a
# command is moved to the background and no longer holds the turn.
# With a limit, each printed command carries the seconds waited so far.
# With a task, the wait can end early, once that workflow has written its result (see below).
usage() {
  echo "usage: keep-waiting.sh [SECONDS between 1 and 110 [--task ID | LIMIT in minutes [WAITED in seconds]]]" >&2
  exit 2
}
seconds=${1:-30} limit=${2:-} waited=${3:-} task=
if [ "$limit" = --task ]; then
  task=$waited limit='' waited=''
  case $task in '' | *[!0-9A-Za-z]*) usage ;; esac # The ID goes into a file name pattern.
fi
# $(( )) reads a leading 0 as octal, so the script refuses a LIMIT or WAITED that starts with 0.
case $seconds in *[!0-9]* | ????*) usage ;; esac # Caps on digits: a longer number could overflow.
case $limit in 0* | *[!0-9]* | ?????*) usage ;; esac
case $waited in 0* | *[!0-9]* | ???????*) usage ;; esac
if [ "$seconds" -lt 1 ] || [ "$seconds" -gt 110 ]; then
  usage
fi
# Claude Code makes this file empty, and fills it when the workflow completes. Its place is not
# documented: where no such file is found, the wait takes the whole time.
output=
if [ -n "$task" ]; then
  for temp in "${CLAUDE_CODE_TMPDIR:-/tmp}" "${TMPDIR:-/tmp}" /tmp; do
    root="$temp/claude-$(id -u)"
    # Another account can make this folder in a shared /tmp: read only ours, and files of ours.
    if [ ! -L "$root" ] && [ -O "$root" ]; then
      for file in "$root"/*/*/tasks/"$task.output"; do
        if [ -f "$file" ] && [ ! -L "$file" ] && [ -O "$file" ]; then
          output=$file
          break 2
        fi
      done
    fi
  done
fi
# Only a file that was filled in the last minute or two ends the wait: if no result follows it, the
# later waits are whole again. BSD find rounds the age up to whole minutes, GNU find does not.
filled() { [ -n "$(find "$output" -size +0 -mmin -2 2> /dev/null)" ]; }
if [ -z "$output" ]; then
  sleep "$seconds"
else
  slept=0
  while [ "$slept" -lt "$seconds" ] && ! filled; do
    sleep 1
    slept=$((slept + 1))
  done
  if filled; then sleep 1; fi # The notice of the result follows the file.
  seconds=$slept
fi
# The count reads no clock, which would also count the time the machine sleeps.
waited=$((waited + 10#$seconds)) # 10# reads a SECONDS that starts with 0 as decimal.
if [ -z "$limit" ]; then
  echo "Waited ${seconds}s. If the result you are waiting for has not arrived, run this same command again now; do not reply to the user or end your turn until it arrives."
elif [ "$waited" -lt $((limit * 60)) ]; then
  echo "Waited ${seconds}s. If the result you are waiting for has not arrived, do not reply to the user or end your turn, and run this command now: bash \"$0\" $seconds $limit $waited"
else
  echo "The limit of $limit minutes has passed. Treat what you are waiting for as hung, and stop waiting."
fi
