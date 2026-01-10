# Database Operations Pattern

**Use Case**: Read, write, sync, and manage database data in workflows.

---

## Pattern Structure

```
Trigger → [Query/Read] → [Transform] → [Write/Update] → [Verify/Log]
```

**Key Characteristic**: Data persistence and synchronization

---

## Core Components

### 1. Trigger
**Options**:
- **Schedule** - Periodic sync/maintenance (most common)
- **Webhook** - Event-driven writes
- **Manual** - One-time operations

### 2. Database Read Nodes
**Supported databases**:
- Postgres
- MySQL
- MongoDB
- Microsoft SQL
- SQLite
- Redis
- And more via community nodes

### 3. Transform
**Purpose**: Map between different database schemas or formats

**Typical nodes**:
- **Set** - Field mapping
- **Code** - Complex transformations
- **Merge** - Combine data from multiple sources

### 4. Database Write Nodes
**Operations**:
- INSERT - Create new records
- UPDATE - Modify existing records
- UPSERT - Insert or update
- DELETE - Remove records

### 5. Verification
**Purpose**: Confirm operations succeeded

**Methods**:
- Query to verify records
- Count rows affected
- Log results

---

## Common Use Cases

### 1. Data Synchronization
**Flow**: Schedule → Read Source DB → Transform → Write Target DB → Log

**Example** (Postgres to MySQL sync):
```
1. Schedule (every 15 minutes)
2. Postgres (SELECT * FROM users WHERE updated_at > {{$json.last_sync}})
3. IF (check if records exist)
4. Set (map Postgres schema to MySQL schema)
5. MySQL (INSERT or UPDATE users)
6. Postgres (UPDATE sync_log SET last_sync = NOW())
7. Slack (notify: "Synced X users")
```

**Incremental sync query**:
```sql
SELECT *
FROM users
WHERE updated_at > $1
ORDER BY updated_at ASC
LIMIT 1000
```

**Parameters**:
```javascript
{
  "parameters": [
    "={{$node['Get Last Sync'].json.last_sync}}"
  ]
}
```

### 2. ETL (Extract, Transform, Load)
**Flow**: Extract from multiple sources → Transform → Load into warehouse

**Example** (Consolidate data):
```
1. Schedule (daily at 2 AM)
2. [Parallel branches]
   ├─ Postgres (SELECT orders)
   ├─ MySQL (SELECT customers)
   └─ MongoDB (SELECT products)
3. Merge (combine all data)
4. Code (transform to warehouse schema)
5. Postgres (warehouse - INSERT into fact_sales)
6. Email (send summary report)
```

### 3. Data Validation & Cleanup
**Flow**: Schedule → Query → Validate → Update/Delete invalid records

**Example** (Clean orphaned records):
```
1. Schedule (weekly)
2. Postgres (SELECT users WHERE email IS NULL OR email = '')
3. IF (invalid records exist)
4. Postgres (UPDATE users SET status='inactive' WHERE email IS NULL)
5. Postgres (DELETE FROM users WHERE created_at < NOW() - INTERVAL '1 year' AND status='inactive')
6. Slack (alert: "Cleaned X invalid records")
```

### 4. Backup & Archive
**Flow**: Schedule → Query → Export → Store

**Example** (Archive old records):
```
1. Schedule (monthly)
2. Postgres (SELECT * FROM orders WHERE created_at < NOW() - INTERVAL '2 years')
3. Code (convert to JSON)
4. Write File (save to archive.json)
5. Google Drive (upload archive)
6. Postgres (DELETE FROM orders WHERE created_at < NOW() - INTERVAL '2 years')
```

### 5. Real-time Data Updates
**Flow**: Webhook → Parse → Update Database

**Example** (Update user status):
```
1. Webhook (receive status update)
2. Postgres (UPDATE users SET status = {{$json.body.status}} WHERE id = {{$json.body.user_id}})
3. IF (rows affected > 0)
4. Redis (SET user:{{$json.body.user_id}}:status {{$json.body.status}})
5. Webhook Response ({"success": true})
```

---

## Database Node Configuration

### Postgres

#### SELECT Query
```javascript
{
  operation: "executeQuery",
  query: "SELECT id, name, email FROM users WHERE created_at > $1 LIMIT $2",
  parameters: [
    "={{$json.since_date}}",
    "100"
  ]
}
```

#### INSERT
```javascript
{
  operation: "insert",
  table: "users",
  columns: "id, name, email, created_at",
  values: [
    {
      id: "={{$json.id}}",
      name: "={{$json.name}}",
      email: "={{$json.email}}",
      created_at: "={{$now}}"
    }
  ]
}
```

#### UPDATE
```javascript
{
  operation: "update",
  table: "users",
  updateKey: "id",
  columns: "name, email, updated_at",
  values: {
    id: "={{$json.id}}",
    name: "={{$json.name}}",
    email: "={{$json.email}}",
    updated_at: "={{$now}}"
  }
}
```

#### UPSERT (INSERT ... ON CONFLICT)
```javascript
{
  operation: "executeQuery",
  query: `
    INSERT INTO users (id, name, email)
    VALUES ($1, $2, $3)
    ON CONFLICT (id)
    DO UPDATE SET name = $2, email = $3, updated_at = NOW()
  `,
  parameters: [
    "={{$json.id}}",
    "={{$json.name}}",
    "={{$json.email}}"
  ]
}
```

### MySQL

#### SELECT with JOIN
```javascript
{
  operation: "executeQuery",
  query: `
    SELECT u.id, u.name, o.order_id, o.total
    FROM users u
    LEFT JOIN orders o ON u.id = o.user_id
    WHERE u.created_at > ?
  `,
  parameters: [
    "={{$json.since_date}}"
  ]
}
```

#### Bulk INSERT
```javascript
{
  operation: "insert",
  table: "orders",
  columns: "user_id, total, status",
  values: $json.orders  // Array of objects
}
```

### MongoDB

#### Find Documents
```javascript
{
  operation: "find",
  collection: "users",
  query: JSON.stringify({
    created_at: { $gt: new Date($json.since_date) },
    status: "active"
  }),
  limit: 100
}
```

#### Insert Document
```javascript
{
  operation: "insert",
  collection: "users",
  document: JSON.stringify({
    name: $json.name,
    email: $json.email,
    created_at: new Date()
  })
}
```

#### Update Document
```javascript
{
  operation: "update",
  collection: "users",
  query: JSON.stringify({ _id: $json.user_id }),
  update: JSON.stringify({
    $set: {
      status: $json.status,
      updated_at: new Date()
    }
  })
}
```

---

## Batch Processing

### Pattern 1: Split In Batches
**Use when**: Processing large datasets to avoid memory issues

```
Postgres (SELECT 10000 records)
  → Split In Batches (100 items per batch)
  → Transform
  → MySQL (write batch)
  → Loop (until all processed)
```

### Pattern 2: Paginated Queries
**Use when**: Database has millions of records

```
Set (initialize: offset=0, limit=1000)
  → Loop Start
  → Postgres (SELECT * FROM large_table LIMIT {{$json.limit}} OFFSET {{$json.offset}})
  → IF (records returned)
    ├─ Process records
    ├─ Set (increment offset by 1000)
    └─ Loop back
  └─ [No records] → End
```

**Query**:
```sql
SELECT * FROM large_table
ORDER BY id
LIMIT $1 OFFSET $2
```

### Pattern 3: Cursor-Based Pagination
**Better performance for large datasets**:

```
Set (initialize: last_id=0)
  → Loop Start
  → Postgres (SELECT * FROM table WHERE id > {{$json.last_id}} ORDER BY id LIMIT 1000)
  → IF (records returned)
    ├─ Process records
    ├─ Code (get max id from batch)
    └─ Loop back
  └─ [No records] → End
```

**Query**:
```sql
SELECT * FROM table
WHERE id > $1
ORDER BY id ASC
LIMIT 1000
```

---

## Transaction Handling

### Pattern 1: BEGIN/COMMIT/ROLLBACK
**For databases that support transactions**:

```javascript
// Node 1: Begin Transaction
{
  operation: "executeQuery",
  query: "BEGIN"
}

// Node 2-N: Your operations
{
  operation: "executeQuery",
  query: "INSERT INTO ...",
  continueOnFail: true
}

// Node N+1: Commit or Rollback
{
  operation: "executeQuery",
  query: "={{$node['Operation'].json.error ? 'ROLLBACK' : 'COMMIT'}}"
}
```

### Pattern 2: Atomic Operations
**Use database features for atomicity**:

```sql
-- Upsert example (atomic)
INSERT INTO inventory (product_id, quantity)
VALUES ($1, $2)
ON CONFLICT (product_id)
DO UPDATE SET quantity = inventory.quantity + $2
```

### Pattern 3: Error Rollback
**Manual rollback on error**:

```
Try Operations:
  Postgres (INSERT orders)
  MySQL (INSERT order_items)

Error Trigger:
  Postgres (DELETE FROM orders WHERE id = {{$json.order_id}})
  MySQL (DELETE FROM order_items WHERE order_id = {{$json.order_id}})
```

---

## Data Transformation

### Schema Mapping
```javascript
// Code node - map schemas
const sourceData = $input.all();

return sourceData.map(item => ({
  json: {
    // Source → Target mapping
    user_id: item.json.id,
    full_name: `${item.json.first_name} ${item.json.last_name}`,
    email_address: item.json.email,
    registration_date: new Date(item.json.created_at).toISOString(),
    // Computed fields
    is_premium: item.json.plan_type === 'pro',
    // Default values
    status: item.json.status || 'active'
  }
}));
```

### Data Type Conversions
```javascript
// Code node - convert data types
return $input.all().map(item => ({
  json: {
    // String to number
    user_id: parseInt(item.json.user_id),
    // String to date
    created_at: new Date(item.json.created_at),
    // Number to boolean
    is_active: item.json.active === 1,
    // JSON string to object
    metadata: JSON.parse(item.json.metadata || '{}'),
    // Null handling
    email: item.json.email || null
  }
}));
```

### Aggregation
```javascript
// Code node - aggregate data
const items = $input.all();

const summary = items.reduce((acc, item) => {
  const date = item.json.created_at.split('T')[0];
  if (!acc[date]) {
    acc[date] = { count: 0, total: 0 };
  }
  acc[date].count++;
  acc[date].total += item.json.amount;
  return acc;
}, {});

return Object.entries(summary).map(([date, data]) => ({
  json: {
    date,
    count: data.count,
    total: data.total,
    average: data.total / data.count
  }
}));
```

---

## Performance Optimization

### 1. Use Indexes
Ensure database has proper indexes:

```sql
-- Add index for sync queries
CREATE INDEX idx_users_updated_at ON users(updated_at);

-- Add index for lookups
CREATE INDEX idx_orders_user_id ON orders(user_id);
```

### 2. Limit Result Sets
Always use LIMIT:

```sql
-- ✅ Good
SELECT * FROM large_table
WHERE created_at > $1
LIMIT 1000

-- ❌ Bad (unbounded)
SELECT * FROM large_table
WHERE created_at > $1
```

### 3. Use Prepared Statements
Parameterized queries are faster:

```javascript
// ✅ Good - prepared statement
{
  query: "SELECT * FROM users WHERE id = $1",
  parameters: ["={{$json.id}}"]
}

// ❌ Bad - string concatenation
{
  query: "SELECT * FROM users WHERE id = '={{$json.id}}'"
}
```

### 4. Batch Writes
Write multiple records at once:

```javascript
// ✅ Good - batch insert
{
  operation: "insert",
  table: "orders",
  values: $json.items  // Array of 100 items
}

// ❌ Bad - individual inserts in loop
// 100 separate INSERT statements
```

### 5. Connection Pooling
Configure in credentials:

```javascript
{
  host: "db.example.com",
  database: "mydb",
  user: "user",
  password: "pass",
  // Connection pool settings
  min: 2,
  max: 10,
  idleTimeoutMillis: 30000
}
```

---

## Error Handling

### Pattern 1: Check Rows Affected
```
Database Operation (UPDATE users...)
  → IF ({{$json.rowsAffected === 0}})
    └─ Alert: "No rows updated - record not found"
```

### Pattern 2: Constraint Violations
```javascript
// Database operation with continueOnFail: true
{
  operation: "insert",
  continueOnFail: true
}

// Next node: Check for errors
IF ({{$json.error !== undefined}})
  → IF ({{$json.error.includes('duplicate key')}})
    └─ Log: "Record already exists - skipping"
  → ELSE
    └─ Alert: "Database error: {{$json.error}}"
```

### Pattern 3: Rollback on Error
```
Try Operations:
  → Database Write 1
  → Database Write 2
  → Database Write 3

Error Trigger:
  → Rollback Operations
  → Alert Admin
```

---

## Security Best Practices

### 1. Use Parameterized Queries (Prevent SQL Injection)
```javascript
// ✅ SAFE - parameterized
{
  query: "SELECT * FROM users WHERE email = $1",
  parameters: ["={{$json.email}}"]
}

// ❌ DANGEROUS - SQL injection risk
{
  query: "SELECT * FROM users WHERE email = '={{$json.email}}'"
}
```

### 2. Least Privilege Access
**Create dedicated workflow user**:

```sql
-- ✅ Good - limited permissions
CREATE USER n8n_workflow WITH PASSWORD 'secure_password';
GRANT SELECT, INSERT, UPDATE ON orders TO n8n_workflow;
GRANT SELECT ON users TO n8n_workflow;

-- ❌ Bad - too much access
GRANT ALL PRIVILEGES TO n8n_workflow;
```

### 3. Validate Input Data
```javascript
// Code node - validate before write
const email = $json.email;
const name = $json.name;

// Validation
if (!email || !email.includes('@')) {
  throw new Error('Invalid email address');
}

if (!name || name.length < 2) {
  throw new Error('Invalid name');
}

// Sanitization
return [{
  json: {
    email: email.toLowerCase().trim(),
    name: name.trim()
  }
}];
```

### 4. Encrypt Sensitive Data
```javascript
// Code node - encrypt before storage
const crypto = require('crypto');

const algorithm = 'aes-256-cbc';
const key = Buffer.from($credentials.encryptionKey, 'hex');
const iv = crypto.randomBytes(16);

const cipher = crypto.createCipheriv(algorithm, key, iv);
let encrypted = cipher.update($json.sensitive_data, 'utf8', 'hex');
encrypted += cipher.final('hex');

return [{
  json: {
    encrypted_data: encrypted,
    iv: iv.toString('hex')
  }
}];
```

---

## Common Gotchas

### 1. ❌ Wrong: Unbounded queries
```sql
SELECT * FROM large_table  -- Could return millions
```

### ✅ Correct: Use LIMIT
```sql
SELECT * FROM large_table
ORDER BY created_at DESC
LIMIT 1000
```

### 2. ❌ Wrong: String concatenation in queries
```javascript
query: "SELECT * FROM users WHERE id = '{{$json.id}}'"
```

### ✅ Correct: Parameterized queries
```javascript
query: "SELECT * FROM users WHERE id = $1",
parameters: ["={{$json.id}}"]
```

### 3. ❌ Wrong: No transaction for multi-step operations
```
INSERT into orders
INSERT into order_items  // Fails → orphaned order record
```

### ✅ Correct: Use transaction
```
BEGIN
INSERT into orders
INSERT into order_items
COMMIT (or ROLLBACK on error)
```

### 4. ❌ Wrong: Processing all items at once
```
SELECT 1000000 records → Process all → OOM error
```

### ✅ Correct: Batch processing
```
SELECT records → Split In Batches (1000) → Process → Loop
```

---

## Real Template Examples

From n8n template library (456 database templates):

**Data Sync**:
```
Schedule → Postgres (SELECT new records) → Transform → MySQL (INSERT)
```

**ETL Pipeline**:
```
Schedule → [Multiple DB reads] → Merge → Transform → Warehouse (INSERT)
```

**Backup**:
```
Schedule → Postgres (SELECT all) → JSON → Google Drive (upload)
```

Use `search_templates({query: "database"})` to find more!

---

## Checklist for Database Workflows

### Planning
- [ ] Identify source and target databases
- [ ] Understand schema differences
- [ ] Plan transformation logic
- [ ] Consider batch size for large datasets
- [ ] Design error handling strategy

### Implementation
- [ ] Use parameterized queries (never concatenate)
- [ ] Add LIMIT to all SELECT queries
- [ ] Use appropriate operation (INSERT/UPDATE/UPSERT)
- [ ] Configure credentials properly
- [ ] Test with small dataset first

### Performance
- [ ] Add database indexes for queries
- [ ] Use batch operations
- [ ] Implement pagination for large datasets
- [ ] Configure connection pooling
- [ ] Monitor query execution times

### Security
- [ ] Use parameterized queries (SQL injection prevention)
- [ ] Least privilege database user
- [ ] Validate and sanitize input
- [ ] Encrypt sensitive data
- [ ] Never log sensitive data

### Reliability
- [ ] Add transaction handling if needed
- [ ] Check rows affected
- [ ] Handle constraint violations
- [ ] Implement retry logic
- [ ] Add Error Trigger workflow

---

## Summary

**Key Points**:
1. **Always use parameterized queries** (prevent SQL injection)
2. **Batch processing** for large datasets
3. **Transaction handling** for multi-step operations
4. **Limit result sets** to avoid memory issues
5. **Validate input data** before writes

**Pattern**: Trigger → Query → Transform → Write → Verify

**Related**:
- [http_api_integration.md](http_api_integration.md) - Fetching data to store in DB
- [scheduled_tasks.md](scheduled_tasks.md) - Periodic database maintenance
