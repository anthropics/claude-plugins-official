# db-migration-guard

A Claude Code plugin that catches dangerous database migration patterns before they reach production.

## What It Does

- Detects destructive operations (dropping columns/tables, renames, type changes)
- Warns about locking risks on large tables (non-concurrent indexes)
- Suggests zero-downtime migration patterns (add/backfill/swap/drop)
- Flags NOT NULL additions without defaults
- Catches mixed data/schema migrations
- Works across Rails, Django, Laravel, Prisma, and Knex

## Installation

```
/plugin install db-migration-guard@claude-plugin-directory
```

## Usage

### Automatic Protection (Hooks)

The plugin automatically intercepts migration file edits and warns about dangerous patterns. No action needed - it runs whenever you create or edit a migration file.

Disable with the environment variable:

```
DISABLE_MIGRATION_GUARD=1
```

### Slash Command

Run a full safety scan on all pending migrations:

```
/migrate-check
/migrate-check db/migrate
/migrate-check prisma/migrations
```

### Skill (Auto-Activated)

The `migrate-check` skill activates automatically when you discuss migration safety, schema changes, or database operations. It provides contextual guidance inline.

### Agent

The `migration-reviewer` agent performs deep analysis - cross-referencing schema files, checking foreign key dependencies, and estimating table sizes to provide risk-aware recommendations.

## Supported Frameworks

| Framework | Migration Path | Schema File |
|---|---|---|
| Rails | `db/migrate/*.rb` | `db/schema.rb` |
| Django | `app/migrations/*.py` | `models.py` |
| Laravel | `database/migrations/*.php` | - |
| Prisma | `prisma/migrations/*.sql` | `schema.prisma` |
| Knex | `migrations/*.js` | - |

## Risk Levels

- **SAFE** - Adding nullable columns, new tables, concurrent indexes
- **WARNING** - NOT NULL without default, non-concurrent indexes, type changes on small tables
- **DANGEROUS** - Dropping columns/tables, renames, type changes on large tables, removing indexes

## Examples

### Dangerous: Dropping a column

```ruby
# This triggers a DANGEROUS warning
class RemoveEmailFromUsers < ActiveRecord::Migration[7.0]
  def change
    remove_column :users, :email, :string
  end
end
```

Suggested safe alternative:

```ruby
# Step 1: Stop writing (app code change, no migration)
# Step 2: Stop reading (app code change, no migration)
# Step 3: Remove the column
class RemoveEmailFromUsers < ActiveRecord::Migration[7.0]
  def change
    safety_assured { remove_column :users, :email, :string }
  end
end
```

### Warning: Non-concurrent index

```ruby
# This triggers a WARNING
class AddIndexToOrders < ActiveRecord::Migration[7.0]
  def change
    add_index :orders, :customer_id
  end
end
```

Suggested fix:

```ruby
class AddIndexToOrders < ActiveRecord::Migration[7.0]
  disable_ddl_transaction!

  def change
    add_index :orders, :customer_id, algorithm: :concurrently
  end
end
```

## License

MIT
