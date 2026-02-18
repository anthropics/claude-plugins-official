#!/usr/bin/env python3
"""
Prepare environment for running a skill eval.

Usage:
    prepare_eval.py <skill-path> <eval-id> --output-dir <dir> [--no-skill]

Examples:
    prepare_eval.py skills/public/pdf 0 --output-dir workspace/eval-001/with-skill
    prepare_eval.py skills/public/pdf 0 --output-dir workspace/eval-001/without-skill --no-skill

Options:
    <skill-path>     Path to the skill directory
    <eval-id>        Index of the eval in evals/evals.json (0-based)
    --output-dir     Directory to prepare for the eval run
    --no-skill       If set, do not copy the skill (for baseline comparison)
"""

import json
import os
import shutil
import sys
from pathlib import Path


def is_writable(path: Path) -> bool:
    """Check if a directory is writable."""
    try:
        test_file = path / ".write_test"
        test_file.touch()
        test_file.unlink()
        return True
    except (OSError, PermissionError):
        return False


def load_evals(skill_path: Path) -> list:
    """Load evals from the skill's evals/evals.json file."""
    evals_file = skill_path / "evals" / "evals.json"
    if not evals_file.exists():
        raise FileNotFoundError(f"Evals file not found: {evals_file}")

    with open(evals_file, "r") as f:
        data = json.load(f)

    # Handle both formats: plain list or wrapped in object with "evals" key
    if isinstance(data, dict) and "evals" in data:
        evals = data["evals"]
    elif isinstance(data, list):
        evals = data
    else:
        raise ValueError(
            f"Expected evals.json to contain a list or object with 'evals' key, "
            f"got {type(data).__name__}"
        )

    return evals


def get_eval(evals: list, eval_id: int) -> dict:
    """Get a specific eval by ID (0-based index)."""
    if eval_id < 0 or eval_id >= len(evals):
        raise IndexError(f"Eval ID {eval_id} out of range (0-{len(evals)-1})")
    return evals[eval_id]


def normalize_eval(eval_data: dict) -> dict:
    """
    Normalize eval data to a consistent format.

    Handles both the design doc format (prompt, files, assertions)
    and the gym format (query, files, expected_behavior).
    """
    # Get the prompt (can be "prompt" or "query")
    prompt = eval_data.get("prompt") or eval_data.get("query")
    if not prompt:
        raise ValueError("Eval must have either 'prompt' or 'query' field")

    # Get files (default to empty list)
    files = eval_data.get("files", [])

    # Get assertions - can be "assertions" (list of strings)
    # or "expected_behavior" (list of strings or objects)
    assertions = eval_data.get("assertions")
    if assertions is None:
        expected_behavior = eval_data.get("expected_behavior", [])
        # Convert expected_behavior to string assertions if needed
        assertions = []
        for item in expected_behavior:
            if isinstance(item, str):
                assertions.append(item)
            elif isinstance(item, dict):
                # Convert structured assertion to string description
                assertion_type = item.get("assertion", "unknown")
                # Build a human-readable assertion string
                parts = [f"Assertion type: {assertion_type}"]
                for key, value in item.items():
                    if key != "assertion":
                        parts.append(f"{key}={value}")
                assertions.append(" - ".join(parts))

    return {
        "prompt": prompt,
        "files": files,
        "assertions": assertions
    }


def prepare_eval(skill_path: Path, eval_id: int, output_dir: Path, no_skill: bool = False) -> dict:
    """
    Prepare the environment for running an eval.

    Args:
        skill_path: Path to the skill directory
        eval_id: Index of the eval in evals.json
        output_dir: Directory to prepare for the eval run
        no_skill: If True, do not copy the skill (for baseline comparison)

    Returns:
        Dictionary with eval metadata
    """
    skill_path = Path(skill_path).resolve()
    output_dir = Path(output_dir).resolve()

    # Validate skill path
    if not skill_path.exists():
        raise FileNotFoundError(f"Skill directory not found: {skill_path}")

    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        raise FileNotFoundError(f"SKILL.md not found in {skill_path}")

    # Load and get the specific eval
    evals = load_evals(skill_path)
    eval_data = get_eval(evals, eval_id)
    normalized = normalize_eval(eval_data)

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create inputs directory and stage input files
    inputs_dir = output_dir / "inputs"
    inputs_dir.mkdir(exist_ok=True)

    staged_files = []
    for file_ref in normalized["files"]:
        # Files can be relative to skill's evals/files/ directory
        source = skill_path / "evals" / "files" / file_ref
        if not source.exists():
            # Try relative to evals/ directly
            source = skill_path / "evals" / file_ref
        if not source.exists():
            # Try relative to skill root
            source = skill_path / file_ref

        if source.exists():
            dest = inputs_dir / Path(file_ref).name
            if source.is_file():
                shutil.copy2(source, dest)
            else:
                shutil.copytree(source, dest, dirs_exist_ok=True)
            staged_files.append(str(dest))
            print(f"  Staged: {file_ref} -> {dest}")
        else:
            print(f"  Warning: File not found: {file_ref}")

    # Create outputs directory
    outputs_dir = output_dir / "outputs"
    outputs_dir.mkdir(exist_ok=True)

    # Copy skill if not --no-skill
    skill_copy_path = None
    if not no_skill:
        skill_copy_path = output_dir / "skill"
        if skill_copy_path.exists():
            shutil.rmtree(skill_copy_path)
        shutil.copytree(skill_path, skill_copy_path, dirs_exist_ok=True)
        skill_copy_path = str(skill_copy_path)
        print(f"  Copied skill to: {skill_copy_path}")

    # Build metadata
    metadata = {
        "eval_id": eval_id,
        "prompt": normalized["prompt"],
        "assertions": normalized["assertions"],
        "input_files": staged_files,
        "skill_path": skill_copy_path,
        "output_dir": str(output_dir),
        "inputs_dir": str(inputs_dir),
        "outputs_dir": str(outputs_dir),
        "no_skill": no_skill,
        "original_skill_path": str(skill_path)
    }

    # Write metadata file
    metadata_path = output_dir / "eval_metadata.json"
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"  Wrote: {metadata_path}")

    return metadata


def determine_workspace(skill_path: Path) -> Path:
    """
    Determine the appropriate workspace location.

    If skill directory is writable, use <skill>/workspace/
    Otherwise, use <project-root>/<skill-name>-workspace/
    """
    skill_path = Path(skill_path).resolve()

    if is_writable(skill_path):
        return skill_path / "workspace"

    # Find project root (look for .git or go up to home)
    project_root = skill_path
    while project_root != project_root.parent:
        if (project_root / ".git").exists():
            break
        project_root = project_root.parent

    if project_root == project_root.parent:
        # Fallback to skill's parent directory
        project_root = skill_path.parent

    skill_name = skill_path.name
    return project_root / f"{skill_name}-workspace"


def main():
    # Parse arguments
    args = sys.argv[1:]

    if len(args) < 4 or "--output-dir" not in args:
        print(__doc__)
        sys.exit(1)

    # Find positional arguments and flags
    skill_path = args[0]
    eval_id = int(args[1])
    no_skill = "--no-skill" in args

    # Find --output-dir value
    output_dir_idx = args.index("--output-dir")
    if output_dir_idx + 1 >= len(args):
        print("Error: --output-dir requires a value")
        sys.exit(1)
    output_dir = args[output_dir_idx + 1]

    print(f"Preparing eval {eval_id} for skill: {skill_path}")
    print(f"Output directory: {output_dir}")
    if no_skill:
        print("Mode: without skill (baseline)")
    else:
        print("Mode: with skill")
    print()

    try:
        metadata = prepare_eval(
            skill_path=Path(skill_path),
            eval_id=eval_id,
            output_dir=Path(output_dir),
            no_skill=no_skill
        )

        print()
        print("Eval prepared successfully!")
        print(f"  Prompt: {metadata['prompt'][:60]}..." if len(metadata['prompt']) > 60 else f"  Prompt: {metadata['prompt']}")
        print(f"  Assertions: {len(metadata['assertions'])}")
        print(f"  Input files: {len(metadata['input_files'])}")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
