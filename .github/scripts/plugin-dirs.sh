#!/usr/bin/env bash
# Print the folders of the plugins that live in this repository, one per line,
# relative to the repo root.
set -euo pipefail
shopt -s nullglob
cd "$(dirname "${BASH_SOURCE[0]}")/../.."

for dir in plugins/*/ external_plugins/*/; do
  printf '%s\n' "${dir%/}"
done
