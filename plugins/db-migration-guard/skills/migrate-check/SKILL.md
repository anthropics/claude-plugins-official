---
name: migrate-check
description: This skill should be used when the user creates or edits a database migration, mentions "migration safety", "schema change", "database migration", "add column", "drop column", "rename table", "migration review", or discusses database schema changes. Provides automatic safety analysis of migration files.
version: 1.0.0
---

# Migration Safety Check Skill

This skill automatically activates when database migration files are being created or modified, providing real-time safety guidance.

## When This Skill Applies

This skill activates when:
- The user creates a new migration file
- The user edits an existing migration
- The user asks about migration safety or best practices
- Schema change operations are being planned
- The user mentions dropping, renaming, or altering database columns/tables

## Safety Rules

### Always Apply These Checks

When a migration file is created or edited, automatically check for:

1. **Destructive operations**: `DROP`, `remove_column`, `drop_table`, `RemoveField`, `DeleteModel`
   - Warn the user about data loss
   - Suggest the phased removal pattern (stop writing, stop reading, then remove)

2. **Rename operations**: `rename_column`, `rename_table`, `RenameField`
   - Warn about deployment downtime
   - Suggest add/backfill/swap/drop pattern

3. **Type changes**: `change_column`, `AlterField`, `ALTER COLUMN TYPE`
   - Warn about data compatibility and table locks
   - Suggest testing with production-like data

4. **NOT NULL without defaults**: `null: false` / `NOT NULL` without `default:`
   - Warn this will fail on populated tables
   - Suggest adding nullable first, then backfilling

5. **Non-concurrent indexes** (PostgreSQL): `add_index` without `algorithm: :concurrently`
   - Warn about table write locks
   - Provide the concurrent alternative with `disable_ddl_transaction!`

6. **Mixed data and schema changes**
   - Warn about partial failure risks
   - Suggest splitting into separate migrations

### Framework-Specific Guidance

**Rails**:
- Recommend `strong_migrations` gem for automated checks
- Use `safety_assured` blocks only when risk is understood
- Ensure `disable_ddl_transaction!` is used with concurrent operations

**Django**:
- Use `AddIndexConcurrently` from `django.contrib.postgres.operations`
- Separate `RunPython` data migrations from schema operations
- Use `SeparateDatabaseAndState` for complex changes

**Laravel**:
- Use `doctrine/dbal` for column modifications
- Test migrations with `--pretend` flag first
- Use `Schema::hasColumn` guards for safety

**Prisma**:
- Check `prisma migrate diff` output before applying
- Use `@default` for new required fields
- Be cautious with `@map` and `@@map` renames

## Response Format

When this skill activates, prepend the migration analysis before any other response:

```
**Migration Safety Analysis**
Risk Level: SAFE / WARNING / DANGEROUS

[List of issues found, if any]
[Suggested fixes, if any]
```
