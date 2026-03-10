# Database Migration Guard

You have the db-migration-guard plugin active. Follow these rules whenever you create, edit, or review database migrations.

## Framework Detection

Detect the framework from the project structure:
- **Rails**: `db/migrate/` directory, files like `*_create_*.rb`
- **Django**: `migrations/` inside app directories, files like `0001_initial.py`
- **Laravel**: `database/migrations/` directory, PHP migration files
- **Prisma**: `prisma/migrations/` directory, `migration.sql` files
- **Knex/Sequelize**: `migrations/` directory, JS/TS files

## Dangerous Patterns - ALWAYS Warn

### 1. Dropping Columns or Tables
- `remove_column`, `drop_table` (Rails)
- `RemoveField`, `DeleteModel` (Django)
- `dropColumn`, `drop` (Laravel)
- `DROP COLUMN`, `DROP TABLE` (raw SQL / Prisma)

**Warning**: Data loss is irreversible. Suggest a phased approach:
1. Stop writing to the column in application code
2. Deploy code that no longer reads from the column
3. Add the migration to remove the column
4. Keep a backup or reversible migration ready

### 2. Renaming Columns or Tables
- `rename_column`, `rename_table` (Rails)
- `RenameField`, `RenameModel` (Django)
- `renameColumn`, `rename` (Laravel)
- `RENAME COLUMN`, `ALTER TABLE ... RENAME` (raw SQL)

**Warning**: Renaming causes downtime during deployment if old code references the old name. Suggest the safe pattern:
1. Add the new column
2. Backfill data from old to new
3. Update application code to use new column
4. Drop the old column in a separate migration

### 3. Changing Column Types
- `change_column` (Rails)
- `AlterField` with type change (Django)
- `change()` with type modification (Laravel)
- `ALTER COLUMN ... TYPE` (raw SQL)

**Warning**: Type changes can fail on existing data and may lock the table. Suggest:
- Test with production-like data first
- For large tables, use the add/backfill/swap/drop pattern
- Check that existing data is compatible with the new type

### 4. Adding NOT NULL Without Default
- `add_column ..., null: false` without `default:` (Rails)
- `null=False` without `default=` (Django)
- `->nullable(false)` without `->default()` (Laravel)
- `NOT NULL` without `DEFAULT` (raw SQL)

**Warning**: Adding NOT NULL to an existing column without a default will fail if the table has existing rows. Suggest:
1. Add the column as nullable first
2. Backfill existing rows with the desired value
3. Add the NOT NULL constraint in a separate migration

### 5. Missing Index Concurrency (PostgreSQL)
- `add_index` without `algorithm: :concurrently` (Rails)
- `AddIndex` without `concurrently=True` (Django)
- `CREATE INDEX` without `CONCURRENTLY` (raw SQL)

**Warning**: Adding an index on a large table locks it for writes. Use concurrent index creation:
- Rails: `add_index :table, :column, algorithm: :concurrently` (requires `disable_ddl_transaction!`)
- Django: Use `AddIndexConcurrently` from `django.contrib.postgres.operations`
- SQL: `CREATE INDEX CONCURRENTLY`

### 6. Running Data Migrations Inside Schema Migrations
- ActiveRecord queries inside Rails migration `change`/`up` methods
- ORM queries inside Django migration `RunPython`
- Eloquent queries inside Laravel migration `up()`

**Warning**: Mixing data and schema changes in one migration is risky. If the migration fails partway, the database may be left in an inconsistent state. Suggest:
- Separate schema changes and data backfills into distinct migrations
- Data migrations should be idempotent and reversible

### 7. Removing or Dropping Indexes
- `remove_index` (Rails)
- `RemoveIndex` (Django)
- `dropIndex` (Laravel)
- `DROP INDEX` (raw SQL)

**Warning**: Removing an index can cause severe query performance degradation. Verify:
- No queries depend on this index
- Check slow query logs or EXPLAIN plans
- Consider the index's role in foreign key lookups

### 8. Adding Unique Constraints to Populated Tables
- `add_index ..., unique: true` (Rails)
- `unique=True` on field (Django)
- `->unique()` (Laravel)
- `ADD CONSTRAINT ... UNIQUE` (raw SQL)

**Warning**: Will fail if duplicate values already exist. Suggest:
1. Query for duplicates first
2. Resolve duplicates before adding the constraint
3. Add the constraint in a separate migration after cleanup

## Safe Migration Checklist

When reviewing any migration, verify:
- [ ] Migration is reversible (has a `down` method or rollback strategy)
- [ ] No data loss without explicit user confirmation
- [ ] Large table operations use concurrent/batched approaches
- [ ] Schema and data changes are separated
- [ ] NOT NULL columns have defaults or are added in phases
- [ ] Indexes are added concurrently for large tables
- [ ] Foreign key constraints reference valid tables/columns

## Risk Levels

Classify each migration operation:
- **SAFE**: Adding nullable columns, adding indexes concurrently, creating new tables
- **WARNING**: Adding NOT NULL with defaults, adding unique constraints, changing defaults
- **DANGEROUS**: Dropping columns/tables, renaming, type changes, removing indexes
