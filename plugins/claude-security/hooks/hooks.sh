#!/bin/sh
# Usage: hooks.sh banner|metrics -- runs hooks.py when python3 is 3.9 or newer.
have=$(python3 -c 'import sys; sys.stdout.write("%d.%d.%d" % sys.version_info[:3]); sys.exit(3 * (sys.version_info < (3, 9)))' 2>/dev/null)
case "$?:$1" in
  0:metrics) python3 "$(dirname -- "$0")/hooks.py" metrics 2>/dev/null ;;
  0:banner) python3 "$(dirname -- "$0")/hooks.py" banner ;;
  3:banner) printf '{"systemMessage": "\\n\\u26a0\\ufe0f  Claude Security needs python3 3.9 or newer, but this python3 is %s. Scanning and fixing will fail until a newer python3 is first on PATH.\\n"}' "$have" ;;
  *:banner) printf '%s\n' '{"systemMessage":"\n⚠️  Claude Security needs a working python3 (3.9 or newer) on PATH and could not run one. Install Python 3, then start a new session.\n"}' ;;
esac
exit 0
