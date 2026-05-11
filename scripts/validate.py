#!/usr/bin/env python3
"""Harness-side schema validation for managed-agent worker output.

Usage: validate.py <output.json> <schema.json|schema.yaml>
Exits 0 on valid, 1 on invalid (message to stderr).

The CMA API does not enforce structured output today, so the deploy harness
runs this between a reader subagent and the orchestrator. Schemas live in each
subagent yaml under `output_schema:` — the deploy script extracts them.
"""
import json
import sys
from pathlib import Path

import jsonschema


def _load(path: Path):
    text = path.read_text()
    if path.suffix in (".yaml", ".yml"):
        import yaml
        return yaml.safe_load(text)
    return json.loads(text)


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__, file=sys.stderr)
        return 2
    instance = _load(Path(sys.argv[1]))
    schema = _load(Path(sys.argv[2]))
    try:
        jsonschema.validate(instance=instance, schema=schema)
    except jsonschema.ValidationError as e:
        print(f"INVALID: {e.message} at {'/'.join(str(p) for p in e.absolute_path)}", file=sys.stderr)
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
