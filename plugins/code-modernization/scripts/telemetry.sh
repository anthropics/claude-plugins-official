#!/bin/sh
# The plugin's usage-count hooks: telemetry.sh command|state|run|failure|health, with the hook's JSON on stdin.
# It starts Python only when the plugin is in use here: a plugin command was typed, or the folder holds files the plugin
# wrote under analysis/, or (for a failure) the failing command names the plugin. The one exception is `health`, once per
# plugin version and machine at session start: what the plugin runs on, so that a machine where nobody gets as far as typing
# a command is still counted once. A Mac without developer tools never sees the "install command line tools" dialog that a
# bare python3 would raise.
# When Python itself cannot run (missing, the Windows Store stub, too old, crashing) this script says so in numbers,
# because Python cannot report its own absence. What is counted, and how to turn it off: see the Telemetry section of
# the README and scripts/telemetry.py.
mode="$1"
input=$(cat)
here=$(dirname "$0")

in_use() {
  for f in analysis/*/INTENT.md analysis/*/PREFLIGHT.md analysis/*/MODERNIZATION_BRIEF.md analysis/*/BUSINESS_RULES.md \
           analysis/*/DELTA_CATALOG.md analysis/*/VERIFICATION.json analysis/*/RULE_REVIEWS.json analysis/*/AI_NATIVE_SPEC.md; do
    [ -f "$f" ] && return 0
  done
  return 1
}

case "$mode" in
  command) printf '%s' "$input" | grep -Eq '"prompt"[[:space:]]*:[[:space:]]*"[[:space:]]*/(code-modernization:)?modernize' || exit 0 ;;
  state|run) in_use || exit 0 ;;
  failure) in_use || printf '%s' "$input" | grep -q 'code-modernization' || exit 0 ;;
  health) ;;
  *) exit 0 ;;
esac

# The off switches count here as well, so nothing at all is sent, not even a python problem.
for v in "$CODE_MODERNIZATION_TELEMETRY" "$CLAUDE_PLUGIN_OPTION_TELEMETRY"; do
  case "$v" in ''|1|true|TRUE|True|on|ON|On|yes|YES|Yes) ;; *) exit 0 ;; esac
done
case "$DISABLE_TELEMETRY$CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC" in *1*|*true*|*TRUE*|*yes*|*on*) exit 0 ;; esac

# Which system this is: 1 macOS, 2 Linux, 3 Windows (Git Bash, MSYS, Cygwin), 4 WSL, 0 other.
case "$(uname -s 2>/dev/null)" in
  Darwin) os=1 ;;
  Linux) if grep -qi microsoft /proc/version 2>/dev/null; then os=4; else os=2; fi ;;
  MINGW*|MSYS*|CYGWIN*) os=3 ;;
  *) os=0 ;;
esac

# Things about the folder that break scripts on Windows: 1 a space in the path, 2 a non-ASCII character, 4 a long path.
pathf=0
case "$PWD" in *" "*) pathf=$((pathf + 1)) ;; esac
printf '%s' "$PWD" | LC_ALL=C grep -q '[^ -~]' && pathf=$((pathf + 2))
[ "${#PWD}" -gt 200 ] && pathf=$((pathf + 4))

# The plugin's version as major*10000 + minor*100 + patch, read without Python.
set -- $(sed -n 's/.*"version"[[:space:]]*:[[:space:]]*"\([0-9]*\)\.\([0-9]*\)\.\([0-9]*\)".*/\1 \2 \3/p' "$here/../.claude-plugin/plugin.json" 2>/dev/null | head -1)
pv=$(( ${1:-0} * 10000 + ${2:-0} * 100 + ${3:-0} ))

# health is sent once per plugin version and machine: a marker file in the plugin's data folder says it was.
marker=""
if [ "$mode" = health ]; then
  d=${CLAUDE_PLUGIN_DATA:-}
  [ -d "$d" ] || d="${TMPDIR:-/tmp}/code-modernization-$(id -u 2>/dev/null || echo 0)"
  mkdir -p -m 700 "$d" 2>/dev/null
  [ -d "$d" ] && [ ! -L "$d" ] && [ -O "$d" ] || exit 0
  marker="$d/health-sent-$pv"
  [ -e "$marker" ] && exit 0
fi
mark() { [ -n "$marker" ] && : > "$marker"; }

# One line of numbers, for the cases where Python cannot speak for itself.
emit() {
  printf '{"metrics":{"pv":%s' "$pv"
  for kv in "$@"; do printf ',"%s":%s' "${kv%%:*}" "${kv#*:}"; done
  printf '}}\n'
}

# Run the Python script with one interpreter; sets out and rc. $2 is the python status the script should report.
run_python() {
  out=$(printf '%s' "$input" | CODE_MODERNIZATION_OS="$os" CODE_MODERNIZATION_PY="$2" CODE_MODERNIZATION_PATHF="$pathf" \
        PYTHONDONTWRITEBYTECODE=1 $1 "$here/telemetry.py" "$mode" 2>/dev/null)
  rc=$?
}

# python3 first, as everywhere else in the plugin. It is never run on a Mac without developer tools (that raises a dialog).
first=1   # 1 none found, 2 macOS stub, 3 present but broken (the Windows Store stub), 5 too old, 6 the script crashed
p3=$(command -v python3 2>/dev/null)
if [ -n "$p3" ]; then
  if [ "$os" = 1 ] && [ "$p3" = /usr/bin/python3 ] && ! xcode-select -p >/dev/null 2>&1; then
    first=2
  else
    run_python python3 0
    if [ "$rc" = 0 ]; then
      [ -n "$out" ] && { mark; printf '%s\n' "$out"; }
      exit 0
    fi
    ver=$(python3 -c 'import sys; print(sys.version_info[0] * 100 + sys.version_info[1])' 2>/dev/null)
    case "$ver" in ''|*[!0-9]*) first=3 ;; *) if [ "$ver" -lt 308 ]; then first=5; else first=6; fi ;; esac
  fi
fi

# Windows in particular: python3 may be missing or a stub while python or the py launcher works.
for c in python "py -3"; do
  command -v "${c%% *}" >/dev/null 2>&1 || continue
  run_python "$c" 4
  if [ "$rc" = 0 ]; then
    [ -n "$out" ] && { mark; printf '%s\n' "$out"; }
    exit 0
  fi
done

# No interpreter could run the script. Say so in numbers, for a command the person typed or an interpreter failure.
case "$mode" in
  command)
    verb=$(printf '%s' "$input" | grep -Eo '"prompt"[[:space:]]*:[[:space:]]*"[[:space:]]*/(code-modernization:)?modernize[a-z-]*' | head -1)
    ns=""; case "$verb" in *code-modernization:*) ns=1 ;; esac
    verb=${verb##*modernize}
    case "$verb" in
      ""|-) c=1 ;; -preflight) c=2 ;; -assess) c=3 ;; -map) c=4 ;; -extract-rules) c=5 ;; -review) c=6 ;; -brief) c=7 ;;
      -transform) c=8 ;; -uplift) c=9 ;; -reimagine) c=10 ;; -verify) c=11 ;; -harden) c=12 ;; -status) c=13 ;;
      -panel) c=20 ;; -review-pane) c=21 ;; -sign) c=22 ;;
      *) c=99; [ -n "$ns" ] || exit 0 ;;
    esac
    emit "cmd:$c" "os:$os" "py:$first" "pyv:0" "pathf:$pathf" ;;
  health)
    mark
    emit "os:$os" "py:$first" "pyv:0" "pathf:$pathf" ;;
  failure)
    if printf '%s' "$input" | grep -Eqi "(python3?|py)(\.exe)?: (command )?not found|'(python3?|py)' is not recognized|Python was not found|python3?: No such file"; then
      emit "os:$os" "py:$first" "tool:1" "kind:1"
    fi ;;
esac
exit 0
