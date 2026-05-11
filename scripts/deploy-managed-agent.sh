#!/usr/bin/env bash
# Copyright 2026 Anthropic PBC
# SPDX-License-Identifier: Apache-2.0
# Deploy a managed-agent template to POST /v1/agents.
#
# Resolves manifest conveniences before posting:
#   system: {file: ...}                  -> inlined string
#   skills: [{path: ...}]                -> uploaded, referenced by skill_id
#   callable_agents: [{manifest: ...}]   -> created first, referenced by agent id
#
# Reader subagents with an `output_schema` block get a thin validation wrapper
# so their JSON is schema-checked before the orchestrator consumes it.
#
# Usage: scripts/deploy-managed-agent.sh <slug>
#   e.g. scripts/deploy-managed-agent.sh reg-monitor

set -euo pipefail

ROLE="${1:?usage: deploy-managed-agent.sh <slug> [--dry-run]}"
DRY_RUN=0; [[ "${2:-}" == "--dry-run" ]] && DRY_RUN=1
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DIR="$ROOT/managed-agent-cookbooks/$ROLE"
API="${ANTHROPIC_API_BASE:-https://api.anthropic.com}"
[[ $DRY_RUN -eq 1 ]] || : "${ANTHROPIC_API_KEY:?ANTHROPIC_API_KEY must be set}"

[[ -f "$DIR/agent.yaml" ]] || { echo "no manifest at $DIR/agent.yaml" >&2; exit 1; }

# Validate SKILL_TITLE_PREFIX against the same allowlist the YAML env-var
# substitution uses. This string flows into `curl -F display_title=...`;
# without validation, a hostile prefix could inject extra multipart fields
# or smuggle newlines.
if [[ -n "${SKILL_TITLE_PREFIX:-}" ]]; then
  if ! [[ "$SKILL_TITLE_PREFIX" =~ ^[A-Za-z0-9._/:@\ -]+$ ]]; then
    echo "refusing SKILL_TITLE_PREFIX: value contains characters outside [A-Za-z0-9._/:@ -]" >&2
    exit 1
  fi
fi

req() {
  curl -sS -H "x-api-key: $ANTHROPIC_API_KEY" \
           -H "anthropic-version: 2023-06-01" \
           -H "anthropic-beta: managed-agents-2026-04-01" \
           -H "content-type: application/json" "$@"
}

# jq + python(pyyaml) do the manifest→payload transform
command -v jq >/dev/null || { echo "requires jq" >&2; exit 1; }
python3 -c 'import yaml' 2>/dev/null || { echo "requires python3 + pyyaml" >&2; exit 1; }
yaml2json() {
  python3 -c '
import sys,os,re,yaml,json
SAFE = re.compile(r"^[A-Za-z0-9._/:@-]*$")
def sub(m):
    name = m.group(1)
    v = os.environ.get(name)
    if v is None:
        return m.group(0)
    if not SAFE.fullmatch(v):
        sys.exit(f"refusing ${{{name}}}: value contains characters outside [A-Za-z0-9._/:@-]")
    return v
t = open(sys.argv[1]).read()
t = re.sub(r"\$\{([A-Z0-9_]+)\}", sub, t)
json.dump(yaml.safe_load(t), sys.stdout)
' "$1"
}

SKILL_CACHE_FILE="$(mktemp -t skillcache)"
trap 'rm -f "$SKILL_CACHE_FILE"' EXIT
upload_skill() {
  local path="$1" key cached
  key="$(basename "$path")"
  cached=$(grep -m1 "^${key}=" "$SKILL_CACHE_FILE" 2>/dev/null | cut -d= -f2-)
  if [[ -n "$cached" ]]; then printf '%s' "$cached"; return; fi
  if [[ $DRY_RUN -eq 1 ]]; then
    cached=$(printf '{"type":"custom","skill_id":"DRYRUN_%s","version":"latest"}' "$key")
    echo "${key}=${cached}" >>"$SKILL_CACHE_FILE"
    printf '%s' "$cached"; return
  fi
  local resp id zip
  zip="$(mktemp -t skill).zip"
  (cd "$(dirname "$path")" && zip -qr "$zip" "$(basename "$path")")
  # /v1/skills uses its own beta header and multipart, not the managed-agents JSON path
  resp=$(curl -sS "$API/v1/skills" \
    -H "x-api-key: $ANTHROPIC_API_KEY" \
    -H "anthropic-version: 2023-06-01" \
    -H "anthropic-beta: skills-2025-10-02" \
    -F "display_title=${SKILL_TITLE_PREFIX:-}$(basename "$path")" \
    -F "files[]=@$zip")
  rm -f "$zip"
  id=$(jq -r '.id // empty' <<<"$resp")
  if [[ -z "$id" ]]; then
    echo "POST /v1/skills failed for $path:" >&2
    echo "$resp" | jq . >&2 2>/dev/null || echo "$resp" >&2
    exit 1
  fi
  cached=$(printf '{"type":"custom","skill_id":"%s","version":"latest"}' "$id")
  echo "${key}=${cached}" >>"$SKILL_CACHE_FILE"
  printf '%s' "$cached"
}

resolve_manifest() {
  local file="$1" base
  base="$(cd "$(dirname "$file")" && pwd)"
  local json
  json=$(yaml2json "$file")
  # Expand any {from_plugin: <dir>} into one {path: ...} per skills/* under that dir.
  local fp
  fp=$(jq -r '.skills[]? | select(.from_plugin) | .from_plugin' <<<"$json" | head -1)
  if [[ -n "$fp" ]]; then
    local plugdir expanded="[]"
    plugdir="$(cd "$base/$fp" && pwd)"
    for sk in "$plugdir"/skills/*/; do
      [[ -d "$sk" ]] || continue
      expanded=$(jq --arg p "${sk%/}" '. + [{__upload:$p}]' <<<"$expanded")
    done
    json=$(jq --argjson e "$expanded" \
      '.skills = ((.skills // [] | map(select(.from_plugin | not))) + $e)' <<<"$json")
  fi
  jq --arg base "$base" '
    .skills = ((.skills // []) | map(
      if .path then {__upload: ($base + "/" + .path)}
      elif .__upload then .
      else . end))
  ' <<<"$json"
}

inline_system() {
  local json="$1" base="$2" sysfile text append body
  if jq -e '.system | type == "object"' >/dev/null <<<"$json"; then
    sysfile=$(jq -r '.system.file // empty' <<<"$json")
    text=$(jq -r '.system.text // empty' <<<"$json")
    append=$(jq -r '.system.append // empty' <<<"$json")
    body="$text"
    if [[ -n "$sysfile" ]]; then
      [[ -f "$base/$sysfile" ]] || { echo "system.file not found: $base/$sysfile" >&2; exit 1; }
      body="$(cat "$base/$sysfile")"
    fi
    [[ -n "$append" ]] && body="${body}"$'\n\n'"${append}"
    jq --arg s "$body" '.system=$s' <<<"$json"
  else
    printf '%s' "$json"
  fi
}

create_agent() {
  local file="$1" base json sub_ids skills_json
  base="$(cd "$(dirname "$file")" && pwd)"
  json=$(resolve_manifest "$file")
  json=$(inline_system "$json" "$base")

  skills_json="[]"
  while IFS= read -r p; do
    [[ -z "$p" ]] && continue
    [[ -d "$p" ]] || { echo "skill path not found: $p" >&2; exit 1; }
    skills_json=$(jq ". + [$(upload_skill "$p")]" <<<"$skills_json")
  done < <(jq -r '.skills[]? | select(.__upload) | .__upload' <<<"$json")
  json=$(jq --argjson s "$skills_json" '.skills=$s' <<<"$json")

  sub_ids="[]"
  while IFS= read -r m; do
    [[ -z "$m" ]] && continue
    local out sid sver
    out=$(create_agent "$base/$m")
    sid=${out%% *}; sver=${out##* }
    sub_ids=$(jq --arg i "$sid" --argjson v "$sver" '. + [{type:"agent", id:$i, version:$v}]' <<<"$sub_ids")
  done < <(jq -r '.callable_agents[]?.manifest // empty' <<<"$json")
  json=$(jq --argjson c "$sub_ids" '.callable_agents=$c | del(.output_schema)' <<<"$json")
  [[ -n "${DEPLOY_DEBUG:-}" ]] && jq -c '{name, callable_agents}' <<<"$json" >&2

  if [[ $DRY_RUN -eq 1 ]]; then
    echo "$json" >>"$DRY_OUT"
    jq -r '"DRYRUN_" + .name + " 1"' <<<"$json"; return
  fi
  local resp id ver
  resp=$(req -X POST "$API/v1/agents" -d "$json")
  id=$(jq -r '.id // empty' <<<"$resp")
  ver=$(jq -r '.version // 1' <<<"$resp")
  if [[ -z "$id" ]]; then
    echo "POST /v1/agents failed for $(jq -r .name <<<"$json"):" >&2
    echo "$resp" | jq . >&2 2>/dev/null || echo "$resp" >&2
    exit 1
  fi
  echo "$id $ver"
}

if [[ $DRY_RUN -eq 1 ]]; then
  DRY_OUT="$(mktemp)"
  create_agent "$DIR/agent.yaml" >/dev/null
  echo "# --dry-run: resolved POST /v1/agents bodies (subagents first, orchestrator last)"
  jq -s '.' "$DRY_OUT"
  rm -f "$DRY_OUT"
  exit 0
fi

OUT=$(create_agent "$DIR/agent.yaml")
AGENT_ID=${OUT%% *}
echo "deployed: $ROLE"
echo "agent id: $AGENT_ID"
echo "console:  https://console.anthropic.com/agents/$AGENT_ID"
