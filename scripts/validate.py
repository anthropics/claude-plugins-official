#!/usr/bin/env python3
# Copyright 2026 Anthropic PBC
# SPDX-License-Identifier: Apache-2.0
"""Harness-side schema validation for managed-agent worker output, and for
core/ schema conformance (country configs, MCP/legal-source registries).

Usage:
  validate.py <output.json> <schema.json|schema.yaml>
      Exits 0 on valid, 1 on invalid (message to stderr). Original,
      unchanged behavior — the CMA deploy harness runs this between a
      reader subagent and the orchestrator; schemas live in each subagent
      yaml under `output_schema:`.

  validate.py --batch <glob-pattern> <schema.json|schema.yaml>
      Validates every file matching <glob-pattern> (relative to the repo
      root, e.g. "countries/*/mcp/*.yaml") against the same schema. Prints
      one line per file; exits 1 if any file fails. Added for country
      plugin conformance checks (see scripts/lint-country-plugin.py, which
      validates per-country against several different schemas and does not
      use this batch mode — this mode is for the simpler case of "many
      files, one schema").
"""
import json
import sys
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parent.parent


def _load(path: Path):
    text = path.read_text(encoding="utf-8")
    if path.suffix in (".yaml", ".yml"):
        import yaml
        return yaml.safe_load(text)
    return json.loads(text)


def _validate_one(instance_path: Path, schema: dict) -> list[str]:
    """Return a list of error strings (empty if valid)."""
    instance = _load(instance_path)
    errors: list[str] = []
    validator = jsonschema.Draft202012Validator(schema)
    for err in validator.iter_errors(instance):
        loc = "/".join(str(p) for p in err.absolute_path) or "$"
        errors.append(f"{instance_path}: {err.message} at {loc}")
    return errors


def _run_batch(glob_pattern: str, schema_path: Path) -> int:
    schema = _load(schema_path)
    matches = sorted(ROOT.glob(glob_pattern))
    if not matches:
        print(f"no files matched {glob_pattern!r} — nothing to validate, OK")
        return 0
    total_errors: list[str] = []
    for instance_path in matches:
        errs = _validate_one(instance_path, schema)
        if errs:
            total_errors.extend(errs)
        else:
            print(f"  ✓ {instance_path.relative_to(ROOT)}")
    if total_errors:
        print("batch validation FAILED:", file=sys.stderr)
        for e in total_errors:
            print(f"  {e}", file=sys.stderr)
        return 1
    return 0


def main() -> int:
    if len(sys.argv) == 4 and sys.argv[1] == "--batch":
        return _run_batch(sys.argv[2], Path(sys.argv[3]))

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
