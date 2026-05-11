#!/usr/bin/env bash
# Copyright 2026 Anthropic PBC
# SPDX-License-Identifier: Apache-2.0
# Dry-run every managed-agent cookbook and assert the resolved POST /v1/agents
# bodies are well-formed: valid JSON, depth-1, non-empty system prompts, no
# output_schema. Exits non-zero if any cookbook fails.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
fail=0

# Tool-scope lint: assert orchestrators do not carry MCP toolsets, Write, or
# Slack tools. Orchestrators emit handoff_request instead of calling these directly.
if ! python3 "$ROOT/scripts/lint-tool-scope.py"; then
  echo "  ✗ tool-scope lint" >&2
  fail=1
fi

for d in "$ROOT"/managed-agent-cookbooks/*/; do
  slug=$(basename "$d")
  if ! bash "$ROOT/scripts/deploy-managed-agent.sh" "$slug" --dry-run 2>&1 | tail -n +2 | python3 -c "
import json,sys
b=json.load(sys.stdin)
errs=[]
for i,x in enumerate(b):
    if not x.get('system'): errs.append(f'{x.get(\"name\")}: empty system')
    if i<len(b)-1 and x.get('callable_agents'): errs.append(f'{x.get(\"name\")}: depth>1 (subagent has callable_agents)')
if 'output_schema' in json.dumps(b): errs.append('output_schema leaked into a body')
if errs:
    for e in errs: print(f'      {e}', file=sys.stderr)
    sys.exit(1)
print(f'  ✓ {sys.argv[1]:24s} {len(b)} bodies')
" "$slug"; then
    echo "  ✗ $slug" >&2
    fail=1
  fi
done
exit $fail
