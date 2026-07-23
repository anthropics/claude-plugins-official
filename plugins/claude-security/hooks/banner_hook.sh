#!/bin/sh
if python3 -c 'import sys' >/dev/null 2>&1; then
  python3 "$(dirname -- "$0")/banner_notice.py"
else
  printf '%s\n' '{"systemMessage":"\n⚠️  Claude Security needs a working python3 (3.9 or newer) on PATH and could not run one. Install Python 3, then start a new session.\n"}'
fi
exit 0
