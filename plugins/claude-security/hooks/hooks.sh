#!/bin/sh
# Usage: hooks.sh banner | metrics | unanswered | guard | turn | bound | tip push|pr. Runs hooks.py
# when python3 is 3.9 or newer (guard, turn and bound run it without that check); metrics and guard
# also run when python or py is.
# bash as sh takes shell options from an exported SHELLOPTS. These four would end the script early, keep Python from starting, or keep the guard from writing over its note.
set +aCeu
# Every start of hooks.py has -IS: the hooks import the standard library alone, and a module on the
# user's PYTHONPATH or a .pth file could keep one from starting. Every start but the guard's second
# on a Python has -X utf8: some Pythons start only with it (the guard's comment, below), and the
# usage hook, the tip and bound handle paths that Claude Code names in UTF-8.

if [ "$1" = tip ]; then
  if [ "$GITHUB_ACTIONS" = true ] || [ "$CI" = true ]; then exit 0; fi
  case "$CLAUDE_SECURITY_SCAN_TIP" in [Oo][Ff][Ff]) exit 0 ;; esac
  unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_COMMON_DIR GIT_CONFIG
fi
[ "$1" = guard ] && { input=$(cat); note=${CLAUDE_PLUGIN_DATA:+$CLAUDE_PLUGIN_DATA/guard-did-not-run}
  # Claude Code shows the user a hook's message only at a call of the main conversation. So an
  # unchecked call notes that its session is owed the message, and that session's main conversation
  # shows it at its next call. Each call of the main conversation first looks whether the note
  # exists, because the search for the id in a long input can be slow.
  read_note() { id=${input#*\"session_id\":}; id=${id#*\"}; id=${id%%\"*}; state=; read -r state <"$note"; } 2>/dev/null
  case "$input" in *claude-security:*) ;; *'"agent_id"'*) exit 0 ;;
    *) [ -e "$note" ] && read_note && [ "$state" = "owed $id" ] && echo "told $id" >"$note" && printf '%s\n' '{"systemMessage":"\n\u26a0\ufe0f  The Claude Security plugin checks the shell commands of its agents. In this session at least one command was not checked. The check needs Python 3.9 or newer on PATH as python3, python or py. Run each with --version. If none shows 3.9 or newer, install Python or fix PATH. If one does, update or reinstall the plugin. Then start a new session.\n"}'; exit 0 ;; esac
  here=$(dirname -- "$0")
  # An answer is held until its run has ended: two answers on stdout are no valid JSON, and Claude
  # Code would then let the call run. A failed run's answer counts only if it begins and ends as a
  # refusal does: hooks.py prints that last, so the check was made.
  # Under a locale that is not UTF-8, some Pythons start only with -X utf8, and others only without
  # it. The start with the option comes first: every other hook, and the guard's check, start so.
  # $option is unquoted, so that it gives the first start two arguments and the second start none.
  run() { for option in '-X utf8' ''; do answer=$(printf '%s\n' "$input" | "$1" -IS $option "$here/hooks.py" guard) || case "$answer" in '{"hookSpecificOutput"'*'"permissionDecision": "deny"'*'}}') ;; *) continue ;; esac; printf '%s' "$answer"; exit 0; done; }
  run python3
  # python and py run by the path that their check prints, as for metrics: another program of that name that exits 0 would otherwise pass for the guard, with no note.
  # With -IS alone, this check would drop a user's PYTHONUTF8=1, which some Pythons need.
  for name in python py; do python=$("$name" -IS -X utf8 "$here/python_check.py" --path 2>/dev/null) && run "$python"; done
  [ -z "$note" ] || { read_note; [ "${state#* }" = "$id" ] || echo "owed $id" >"$note"; }
  echo "Claude Security plugin: the check of its agents' calls did not run (python3, python and py are missing or failed), so this call runs unchecked." >&2; exit 0; }
[ "$1" = turn ] && { python3 -IS -X utf8 "$(dirname -- "$0")/hooks.py" turn "${CLAUDE_CONFIG_DIR:-$HOME/.claude}" >/dev/null 2>&1 || printf '%s\n' '{"decision":"block","reason":"Claude Security plugin: /claude-security:threat-model did not start, because it could not set its limit on which files it writes. It needs a working python3, Claude Code 2.1.196 or newer, and a folder that it can write: plugins/data/claude-security-turns, below the Claude Code config folder."}'; exit 0; }
[ "$1" = bound ] && { python3 -IS -X utf8 "$(dirname -- "$0")/hooks.py" bound "${CLAUDE_CONFIG_DIR:-$HOME/.claude}" 2>/dev/null; exit 0; }
# The check is a file beside hooks.py, run by its path as hooks.py is. Below, it starts without -IS, as the helper scripts do; the guard's check, above, has -IS. It imports os and sys alone, so the banner's notice and the usage hook's failed names tell only whether this file passes at a plain start: a helper script can fail where it passes. It also decides whether hooks.py starts below, with -IS: a hook can be skipped though that start would work, or fail though the check passed.
check="$(dirname -- "$0" 2>/dev/null)/python_check.py"
python=python3
failed=
have=$(python3 "$check" 2>/dev/null </dev/null); status=$?
if [ "$1" = metrics ]; then
  [ "$status" -eq 0 ] || { failed=python3; python=; }
  # The fallback runs by the path its check printed, not by name: py is a launcher and may choose a different Python on another call.
  for candidate in python py; do
    if found=$("$candidate" "$check" --path 2>/dev/null </dev/null); then python=${python:-$found}; status=0; else failed="$failed $candidate"; fi
  done
fi
case "$status:$1" in
  0:unanswered) python3 -IS -X utf8 "$(dirname -- "$0")/hooks.py" unanswered 2>/dev/null ;;
  # $failed is unquoted so each failed name is its own argument.
  0:metrics) "$python" -IS -X utf8 "$(dirname -- "$0")/hooks.py" metrics $failed 2>/dev/null ;;
  0:tip) GIT_TERMINAL_PROMPT=0 GIT_NO_LAZY_FETCH=1 \
    python3 -IS -X utf8 "$(dirname -- "$0")/hooks.py" tip "$2" "$CLAUDE_PLUGIN_DATA" "$CLAUDE_SECURITY_SCAN_TIP" 2>/dev/null ;;
  0:banner) python3 -IS -X utf8 "$(dirname -- "$0")/hooks.py" banner "$CLAUDE_PLUGIN_DATA" "$CLAUDE_CODE_ENTRYPOINT" ;;
  3:banner) printf '{"systemMessage": "\\n\\u26a0\\ufe0f  Claude Security needs python3 3.9 or newer, but this python3 is %s. Scanning and fixing will fail until a newer python3 is first on PATH.\\n"}' "$have" ;;
  *:banner) printf '%s\n' '{"systemMessage":"\n⚠️  Claude Security needs a working python3 (3.9 or newer) on PATH and could not run one. Install Python 3, then start a new session.\n"}' ;;
esac
exit 0
