---
description: Scan pending database migrations for safety risks and suggest improvements
argument-hint: [path-to-migrations-dir]
allowed-tools: [Read, Glob, Grep, Bash]
---

# Migration Safety Check

Scan and analyze pending database migrations for dangerous patterns, locking risks, and missing best practices.

## Arguments

The user invoked this command with: $ARGUMENTS

## Instructions

When this command is invoked:

1. **Detect the framework** by checking for these directory patterns:
   - `db/migrate/*.rb` - Rails
   - `*/migrations/0*.py` - Django
   - `database/migrations/*.php` - Laravel
   - `prisma/migrations/*/migration.sql` - Prisma
   - `migrations/*.{js,ts}` - Knex/Sequelize

   If the user provided a path argument, search within that path. Otherwise, search from the project root.

2. **Find pending/recent migration files** using Glob. Sort by filename (most recent first). Read each migration file.

3. **Analyze each migration** for these risk categories:

   **DANGEROUS (must fix before deploy):**
   - Dropping columns or tables without a phased approach
   - Renaming columns (causes downtime during rolling deploys)
   - Changing column types on large tables
   - Removing indexes that active queries depend on

   **WARNING (review carefully):**
   - Adding NOT NULL without a default value
   - Adding indexes without concurrency (PostgreSQL)
   - Mixing data and schema changes in one migration
   - Adding unique constraints to tables that may have duplicates
   - Missing reversibility (no `down` method or rollback)

   **SAFE (no action needed):**
   - Adding nullable columns
   - Creating new tables
   - Adding indexes concurrently
   - Adding columns with defaults

4. **Output a risk report** in this format:

   ```
   ## Migration Safety Report

   ### <filename>
   **Risk Level**: DANGEROUS / WARNING / SAFE
   **Operations detected**:
   - <operation description>

   **Issues**:
   - <issue description>

   **Suggested fix**:
   - <concrete code suggestion>

   ---
   ```

5. **Summarize** with a count of DANGEROUS / WARNING / SAFE migrations at the end.

## Example Usage

```
/migrate-check
/migrate-check db/migrate
/migrate-check prisma/migrations
```
