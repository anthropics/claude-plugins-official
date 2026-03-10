#!/usr/bin/env python3
"""
Migration Safety Hook for Claude Code
Checks for dangerous patterns in database migration files and warns before execution.
"""

import json
import os
import sys
from datetime import datetime

# File path patterns that indicate a migration file
MIGRATION_PATH_PATTERNS = [
    # Rails
    lambda p: "db/migrate/" in p and p.endswith(".rb"),
    # Django
    lambda p: "migrations/" in p and p.endswith(".py") and not p.endswith("__init__.py"),
    # Laravel
    lambda p: "database/migrations/" in p and p.endswith(".php"),
    # Prisma
    lambda p: "prisma/migrations/" in p and p.endswith(".sql"),
    # Knex / Sequelize
    lambda p: "migrations/" in p and (p.endswith(".js") or p.endswith(".ts")),
]

# Dangerous patterns to detect in migration content
DANGEROUS_PATTERNS = [
    {
        "name": "drop_column",
        "substrings": [
            "remove_column", "drop_column", "dropColumn",
            "RemoveField", "DROP COLUMN",
        ],
        "level": "DANGEROUS",
        "message": (
            "Dropping a column causes irreversible data loss.\n\n"
            "Safe pattern:\n"
            "1. Stop writing to the column in app code\n"
            "2. Deploy code that no longer reads from it\n"
            "3. Remove the column in a separate migration\n"
            "4. Keep a backup migration to restore if needed"
        ),
    },
    {
        "name": "drop_table",
        "substrings": [
            "drop_table", "dropTable", "DeleteModel",
            "DROP TABLE", "Schema::drop",
        ],
        "level": "DANGEROUS",
        "message": (
            "Dropping a table deletes all data permanently.\n\n"
            "Before dropping:\n"
            "- Confirm no code references this table\n"
            "- Back up the data if needed\n"
            "- Consider renaming instead of dropping as a first step"
        ),
    },
    {
        "name": "rename_column",
        "substrings": [
            "rename_column", "rename_table", "renameColumn",
            "RenameField", "RenameModel", "RENAME COLUMN",
            "ALTER TABLE", "@@map",
        ],
        "level": "DANGEROUS",
        "message": (
            "Renaming causes downtime during rolling deployments - "
            "old code still references the old name.\n\n"
            "Safe pattern:\n"
            "1. Add the new column\n"
            "2. Backfill data from old to new\n"
            "3. Update app code to use new column\n"
            "4. Drop the old column in a later migration"
        ),
    },
    {
        "name": "change_type",
        "substrings": [
            "change_column", "change(", "AlterField",
            "ALTER COLUMN", "TYPE ",
        ],
        "level": "WARNING",
        "message": (
            "Changing a column type may lock the table and fail "
            "if existing data is incompatible.\n\n"
            "- Test with production-like data first\n"
            "- For large tables, use add/backfill/swap/drop instead\n"
            "- Check data compatibility before applying"
        ),
    },
    {
        "name": "not_null_no_default",
        "substrings": ["null: false", "NOT NULL", "nullable(false)", "null=False"],
        "level": "WARNING",
        "message": (
            "Adding NOT NULL to a column may fail on tables with existing rows "
            "if no default value is provided.\n\n"
            "Safe pattern:\n"
            "1. Add the column as nullable\n"
            "2. Backfill existing rows\n"
            "3. Add NOT NULL constraint in a separate migration"
        ),
    },
    {
        "name": "non_concurrent_index",
        "substrings": ["add_index", "AddIndex", "CREATE INDEX"],
        "level": "WARNING",
        "message": (
            "Adding an index without CONCURRENTLY locks the table for writes.\n\n"
            "Use concurrent index creation:\n"
            "- Rails: add_index :table, :col, algorithm: :concurrently "
            "(with disable_ddl_transaction!)\n"
            "- Django: AddIndexConcurrently\n"
            "- SQL: CREATE INDEX CONCURRENTLY"
        ),
    },
    {
        "name": "remove_index",
        "substrings": ["remove_index", "RemoveIndex", "dropIndex", "DROP INDEX"],
        "level": "WARNING",
        "message": (
            "Removing an index may cause severe query performance degradation.\n\n"
            "Before removing:\n"
            "- Verify no queries depend on this index\n"
            "- Check slow query logs or run EXPLAIN\n"
            "- Consider the index's role in foreign key lookups"
        ),
    },
]


def is_migration_file(file_path):
    """Check if the file path looks like a migration file."""
    normalized = file_path.lstrip("/")
    return any(check(normalized) for check in MIGRATION_PATH_PATTERNS)


def check_content(content):
    """Check migration content for dangerous patterns. Returns list of matches."""
    findings = []
    for pattern in DANGEROUS_PATTERNS:
        for substring in pattern["substrings"]:
            if substring in content:
                findings.append(pattern)
                break  # One match per pattern is enough
    return findings


def get_state_file(session_id):
    """Get session-specific state file path."""
    return os.path.expanduser(
        f"~/.claude/migration_guard_state_{session_id}.json"
    )


def load_shown(session_id):
    """Load set of already-shown warning keys."""
    path = get_state_file(session_id)
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                return set(json.load(f))
        except (json.JSONDecodeError, IOError):
            return set()
    return set()


def save_shown(session_id, shown):
    """Persist shown warning keys."""
    path = get_state_file(session_id)
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump(list(shown), f)
    except IOError:
        pass


def extract_content(tool_name, tool_input):
    """Pull the content being written/edited from tool input."""
    if tool_name == "Write":
        return tool_input.get("content", "")
    elif tool_name == "Edit":
        return tool_input.get("new_string", "")
    elif tool_name == "MultiEdit":
        edits = tool_input.get("edits", [])
        return " ".join(e.get("new_string", "") for e in edits)
    return ""


def main():
    if os.environ.get("DISABLE_MIGRATION_GUARD", "0") == "1":
        sys.exit(0)

    try:
        input_data = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        sys.exit(0)

    session_id = input_data.get("session_id", "default")
    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})

    if tool_name not in ("Edit", "Write", "MultiEdit"):
        sys.exit(0)

    file_path = tool_input.get("file_path", "")
    if not file_path or not is_migration_file(file_path):
        sys.exit(0)

    content = extract_content(tool_name, tool_input)
    if not content:
        sys.exit(0)

    findings = check_content(content)
    if not findings:
        sys.exit(0)

    # Deduplicate per session - only warn once per file + pattern
    shown = load_shown(session_id)
    new_findings = []
    for f in findings:
        key = f"{file_path}:{f['name']}"
        if key not in shown:
            shown.add(key)
            new_findings.append(f)

    if not new_findings:
        sys.exit(0)

    save_shown(session_id, shown)

    # Build warning message
    lines = ["Migration Safety Warning"]
    lines.append("=" * 40)
    lines.append(f"File: {file_path}")
    lines.append("")

    for f in new_findings:
        lines.append(f"[{f['level']}] {f['name']}")
        lines.append(f['message'])
        lines.append("")

    print("\n".join(lines), file=sys.stderr)
    sys.exit(2)  # Block and show warning


if __name__ == "__main__":
    main()
