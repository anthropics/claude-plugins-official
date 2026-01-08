#!/usr/bin/env python3
"""
ClaudeMem Vault Validation Hook
Runs after Write|Edit on Vault files to ensure schema compliance.

Exit codes:
- 0: Valid, allow the write
- 2: Invalid, block the write (stderr becomes error message)
"""

import json
import sys
import os
import re
from pathlib import Path

VAULT_PATH = Path.home() / "Vault"

def parse_frontmatter(content):
    """Extract YAML frontmatter from markdown content."""
    if not content.startswith("---"):
        return None

    parts = content.split("---", 2)
    if len(parts) < 3:
        return None

    frontmatter = {}
    for line in parts[1].strip().split("\n"):
        if ":" in line:
            key, value = line.split(":", 1)
            frontmatter[key.strip()] = value.strip()

    return frontmatter

def validate_manifest(content, frontmatter):
    """Validate _manifest.md structure."""
    errors = []

    if frontmatter.get("type") != "manifest":
        errors.append("Manifest must have type: manifest")

    required_sections = ["Active Context", "Projects", "Recent Sessions"]
    for section in required_sections:
        if f"## {section}" not in content:
            errors.append(f"Missing required section: {section}")

    return errors

def validate_project_index(content, frontmatter, file_path):
    """Validate project _index.md structure."""
    errors = []

    required_fields = ["type", "id", "name", "status", "priority", "created"]
    for field in required_fields:
        if field not in frontmatter:
            errors.append(f"Missing required field: {field}")

    if frontmatter.get("type") != "project":
        errors.append("Project index must have type: project")

    # Check status is valid
    valid_statuses = ["active", "paused", "completed", "archived"]
    if frontmatter.get("status") and frontmatter["status"] not in valid_statuses:
        errors.append(f"Invalid status: {frontmatter['status']}. Must be one of: {valid_statuses}")

    # Check priority is valid
    valid_priorities = ["P0", "P1", "P2"]
    if frontmatter.get("priority") and frontmatter["priority"] not in valid_priorities:
        errors.append(f"Invalid priority: {frontmatter['priority']}. Must be one of: {valid_priorities}")

    # Check folder name matches id
    folder_name = file_path.parent.name
    if frontmatter.get("id") and frontmatter["id"] != folder_name:
        errors.append(f"Project id '{frontmatter['id']}' must match folder name '{folder_name}'")

    return errors

def validate_epic(content, frontmatter):
    """Validate epic file structure."""
    errors = []

    required_fields = ["type", "id", "project", "status", "priority", "created"]
    for field in required_fields:
        if field not in frontmatter:
            errors.append(f"Missing required field: {field}")

    if frontmatter.get("type") != "epic":
        errors.append("Epic must have type: epic")

    # Check for Tasks section
    if "## Tasks" not in content:
        errors.append("Epic must have a ## Tasks section")

    return errors

def validate_session(content, frontmatter):
    """Validate session file structure."""
    errors = []

    required_fields = ["type", "date", "project"]
    for field in required_fields:
        if field not in frontmatter:
            errors.append(f"Missing required field: {field}")

    if frontmatter.get("type") != "session":
        errors.append("Session must have type: session")

    return errors

def check_duplicate_project(file_path):
    """Check if creating a duplicate project folder."""
    errors = []

    if "/Projects/" in str(file_path) and file_path.name == "_index.md":
        project_id = file_path.parent.name
        projects_dir = VAULT_PATH / "Projects"

        # Check for case-insensitive duplicates
        existing = [d.name.lower() for d in projects_dir.iterdir() if d.is_dir()]
        if existing.count(project_id.lower()) > 1:
            errors.append(f"Duplicate project folder detected: {project_id}")

    return errors

def validate_file(file_path, content):
    """Main validation logic."""
    errors = []

    # Parse frontmatter
    frontmatter = parse_frontmatter(content)
    if frontmatter is None:
        return ["File must have YAML frontmatter (---\\n...\\n---)"]

    # Route to appropriate validator
    file_name = file_path.name
    relative_path = str(file_path.relative_to(VAULT_PATH))

    if file_name == "_manifest.md":
        errors.extend(validate_manifest(content, frontmatter))
    elif file_name == "_index.md" and "/Projects/" in str(file_path):
        errors.extend(validate_project_index(content, frontmatter, file_path))
        errors.extend(check_duplicate_project(file_path))
    elif "/Epics/" in str(file_path):
        errors.extend(validate_epic(content, frontmatter))
    elif "/Sessions/" in str(file_path):
        errors.extend(validate_session(content, frontmatter))

    return errors

def main():
    # Read hook input from stdin
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        # No input or invalid JSON - skip validation
        sys.exit(0)

    # Get file path from tool input
    tool_input = input_data.get("tool_input", {})
    file_path_str = tool_input.get("file_path", "")

    if not file_path_str:
        sys.exit(0)

    file_path = Path(file_path_str).expanduser().resolve()

    # Only validate files in Vault
    try:
        file_path.relative_to(VAULT_PATH)
    except ValueError:
        # Not in Vault, skip validation
        sys.exit(0)

    # Skip schema files
    if "/.schemas/" in str(file_path):
        sys.exit(0)

    # Read file content
    if not file_path.exists():
        sys.exit(0)

    try:
        content = file_path.read_text()
    except Exception:
        sys.exit(0)

    # Validate
    errors = validate_file(file_path, content)

    if errors:
        print(f"Vault validation failed for {file_path.name}:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        sys.exit(2)  # Block the write

    sys.exit(0)  # Allow the write

if __name__ == "__main__":
    main()
