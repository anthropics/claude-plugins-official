#!/usr/bin/env python3
"""
Copy a skill directory with metadata tracking.

Creates a copy of a skill directory and adds a META.yaml file
to track lineage, changes, and performance metrics.
"""

import argparse
import shutil
from datetime import datetime, timezone
from pathlib import Path


def create_meta_yaml(
    dest: Path,
    parent: str | None,
    changes: str | None,
    score: float | None,
    iteration: int | None,
) -> None:
    """Create META.yaml file in the destination directory."""
    created_at = datetime.now(timezone.utc).isoformat()

    # Build YAML content manually to avoid external dependencies
    lines = ["# Skill iteration metadata", ""]

    # Helper to format YAML values
    def yaml_value(val):
        if val is None:
            return "null"
        if isinstance(val, bool):
            return "true" if val else "false"
        if isinstance(val, (int, float)):
            return str(val)
        if isinstance(val, str):
            # Quote strings that might be ambiguous
            if val in ("null", "true", "false") or val.startswith(("'", '"', "[", "{")):
                return f'"{val}"'
            # Quote strings with special characters
            if any(c in val for c in (":", "#", "\n", '"', "'")):
                escaped = val.replace("\\", "\\\\").replace('"', '\\"')
                return f'"{escaped}"'
            return val
        return str(val)

    lines.append(f"parent: {yaml_value(parent)}")
    lines.append(f"changes: {yaml_value(changes)}")
    lines.append(f"score: {yaml_value(score)}")
    lines.append(f"iteration: {yaml_value(iteration)}")
    lines.append(f"created_at: {yaml_value(created_at)}")
    lines.append("")

    meta_path = dest / "META.yaml"
    meta_path.write_text("\n".join(lines))


def copy_skill(
    source: Path,
    dest: Path,
    parent: str | None = None,
    changes: str | None = None,
    score: float | None = None,
    iteration: int | None = None,
) -> None:
    """
    Copy a skill directory and create version directory structure.

    Creates a version directory with:
    - skill/        : The actual skill files (copied from source)
    - runs/         : Created by executor during execution (run-1/, run-2/, run-3/)
    - improvements/ : For improvement suggestions (if not v0)
    - META.yaml     : Version metadata

    The runs/ directory structure is created on-demand by the executor:
    - runs/run-1/transcript.md, outputs/, evaluation.json
    - runs/run-2/...
    - runs/run-3/...

    Args:
        source: Path to the source skill directory (or source/skill/ if copying from another version)
        dest: Path to the destination version directory (e.g., workspace/v1)
        parent: Name/path of the parent skill iteration
        changes: Description of changes from parent
        score: Evaluation score for this iteration
        iteration: Iteration number
    """
    source = Path(source).resolve()
    dest = Path(dest).resolve()

    if not source.exists():
        raise FileNotFoundError(f"Source directory does not exist: {source}")

    if not source.is_dir():
        raise ValueError(f"Source must be a directory: {source}")

    if dest.exists():
        raise FileExistsError(f"Destination already exists: {dest}")

    # Create the version directory structure
    dest.mkdir(parents=True)
    skill_dest = dest / "skill"
    (dest / "runs").mkdir()

    # Create improvements directory for non-baseline versions
    if iteration is not None and iteration > 0:
        (dest / "improvements").mkdir()

    # Copy the skill files to skill/ subdirectory
    shutil.copytree(source, skill_dest)

    # Create metadata file at the version root
    create_meta_yaml(dest, parent, changes, score, iteration)

    print(f"Copied skill from {source} to {skill_dest}")
    print(f"Created version directory structure at {dest}")
    print(f"  - skill/        : Skill files")
    print(f"  - runs/         : For execution runs (run-1/, run-2/, run-3/)")
    if iteration is not None and iteration > 0:
        print(f"  - improvements/ : Improvement suggestions")
    print(f"  - META.yaml     : Version metadata")


def main():
    parser = argparse.ArgumentParser(
        description="Copy a skill directory with metadata tracking and version structure.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create baseline v0 from an existing skill
  python copy_skill.py ./skills/public/pdf ./skill_iterations/v0 --iteration 0

  # Create v1 from v0's skill directory
  python copy_skill.py ./skill_iterations/v0/skill ./skill_iterations/v1 \\
      --parent v0 \\
      --changes "Added error handling for empty cells" \\
      --iteration 1

  # Create v2 with score from evaluation
  python copy_skill.py ./skill_iterations/v1/skill ./skill_iterations/v2 \\
      --parent v1 \\
      --changes "Improved coordinate guidance" \\
      --score 7.5 \\
      --iteration 2

Output structure:
  dest/
  ├── META.yaml        # Version metadata
  ├── skill/           # The actual skill files
  ├── runs/            # Execution runs (created by executor)
  │   ├── run-1/
  │   │   ├── transcript.md
  │   │   ├── outputs/
  │   │   └── evaluation.json
  │   ├── run-2/
  │   └── run-3/
  └── improvements/    # Improvement suggestions (v1+)
        """,
    )

    parser.add_argument("source", type=Path, help="Source skill directory to copy")

    parser.add_argument("dest", type=Path, help="Destination path for the copy")

    parser.add_argument(
        "--parent",
        type=str,
        default=None,
        help="Name or path of the parent skill iteration",
    )

    parser.add_argument(
        "--changes",
        type=str,
        default=None,
        help="Description of changes from the parent version",
    )

    parser.add_argument(
        "--score",
        type=float,
        default=None,
        help="Evaluation score for this iteration (e.g., 7.5)",
    )

    parser.add_argument(
        "--iteration",
        type=int,
        default=None,
        help="Iteration number (e.g., 1, 2, 3)",
    )

    args = parser.parse_args()

    try:
        copy_skill(
            source=args.source,
            dest=args.dest,
            parent=args.parent,
            changes=args.changes,
            score=args.score,
            iteration=args.iteration,
        )
    except (FileNotFoundError, FileExistsError, ValueError) as e:
        parser.error(str(e))


if __name__ == "__main__":
    main()
