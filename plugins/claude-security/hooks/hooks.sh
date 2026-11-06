#!/bin/sh
# Usage: hooks.sh banner | metrics | unanswered | tip push|pr. Runs hooks.py when python3 is 3.9 or newer; metrics also runs when python or py is.
if [ "$1" = tip ]; then
  if [ "$GITHUB_ACTIONS" = true ] || [ "$CI" = true ]; then exit 0; fi
  case "$CLAUDE_SECURITY_SCAN_TIP" in [Oo][Ff][Ff]) exit 0 ;; esac
  unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_COMMON_DIR
fi
floor='sys.exit(3 * (sys.version_info < (3, 9)))'
probe='import sys; sys.stdout.write("%d.%d.%d" % sys.version_info[:3]); '"$floor"
python=python3
failed=
have=$(python3 -c "$probe" 2>/dev/null </dev/null); status=$?
if [ "$1" = metrics ]; then
  [ "$status" -eq 0 ] || { failed=python3; python=; }
  # The fallback runs by the path its probe printed, not by name: py is a launcher and "py hooks.py" may choose a different Python than "py -c" did.
  exe_probe='import sys; sys.stdout.write(sys.executable.replace("\\", "/")); '"$floor"
  for candidate in python py; do
    if found=$("$candidate" -c "$exe_probe" 2>/dev/null </dev/null); then python=${python:-$found}; status=0; else failed="$failed $candidate"; fi
  done
fi
case "$status:$1" in
  0:unanswered) python3 "$(dirname -- "$0")/hooks.py" unanswered 2>/dev/null ;;
  # $failed is unquoted so each failed name is its own argument; each name probed must be in hooks.py's INTERPRETERS.
  0:metrics) "$python" "$(dirname -- "$0")/hooks.py" metrics $failed 2>/dev/null ;;
  0:tip) GIT_TERMINAL_PROMPT=0 GIT_NO_LAZY_FETCH=1 \
    python3 "$(dirname -- "$0")/hooks.py" tip "$2" "$CLAUDE_PLUGIN_DATA" "$CLAUDE_SECURITY_SCAN_TIP" 2>/dev/null ;;
  0:banner) python3 "$(dirname -- "$0")/hooks.py" banner "$CLAUDE_PLUGIN_DATA" ;;
  3:banner) printf '{"systemMessage": "\\n\\u26a0\\ufe0f  Claude Security needs python3 3.9 or newer, but this python3 is %s. Scanning and fixing will fail until a newer python3 is first on PATH.\\n"}' "$have" ;;
  *:banner) printf '%s\n' '{"systemMessage":"\n⚠️  Claude Security needs a working python3 (3.9 or newer) on PATH and could not run one. Install Python 3, then start a new session.\n"}' ;;
esac
exit 0
