# Common Antipatterns

Code antipatterns to identify during review, with examples and fixes.

---

## Table of Contents

- [Structural Antipatterns](#structural-antipatterns)
- [Logic Antipatterns](#logic-antipatterns)
- [Security Antipatterns](#security-antipatterns)
- [Performance Antipatterns](#performance-antipatterns)
- [Testing Antipatterns](#testing-antipatterns)
- [Async Antipatterns](#async-antipatterns)

---

## Structural Antipatterns

### God Class

A class that does too much and knows too much.

```typescript
// BAD: God class handling everything
class UserManager {
  createUser(data: UserData) { ... }
  updateUser(id: string, data: UserData) { ... }
  deleteUser(id: string) { ... }
  sendEmail(userId: string, content: string) { ... }
  generateReport(userId: string) { ... }
  validatePassword(password: string) { ... }
  hashPassword(password: string) { ... }
  uploadAvatar(userId: string, file: File) { ... }
  resizeImage(file: File) { ... }
  logActivity(userId: string, action: string) { ... }
  // 50 more methods...
}

// GOOD: Single responsibility classes
class UserRepository {
  create(data: UserData): User { ... }
  update(id: string, data: Partial<UserData>): User { ... }
  delete(id: string): void { ... }
}

class EmailService {
  send(to: string, content: string): void { ... }
}

class PasswordService {
  validate(password: string): ValidationResult { ... }
  hash(password: string): string { ... }
}
```

**Detection:** Class has >20 methods, >500 lines, or handles unrelated concerns.

---

### Long Method

Functions that do too much and are hard to understand.

```python
# BAD: Long method doing everything
def process_order(order_data):
    # Validate order (20 lines)
    if not order_data.get('items'):
        raise ValueError('No items')
    if not order_data.get('customer_id'):
        raise ValueError('No customer')
    # ... more validation

    # Calculate totals (30 lines)
    subtotal = 0
    for item in order_data['items']:
        price = get_product_price(item['product_id'])
        subtotal += price * item['quantity']
    # ... tax calculation, discounts

    # Process payment (40 lines)
    payment_result = payment_gateway.charge(...)
    # ... handle payment errors

    # Create order record (20 lines)
    order = Order.create(...)

    # Send notifications (20 lines)
    send_order_confirmation(...)
    notify_warehouse(...)

    return order

# GOOD: Composed of focused functions
def process_order(order_data):
    validate_order(order_data)
    totals = calculate_order_totals(order_data)
    payment = process_payment(order_data['customer_id'], totals)
    order = create_order_record(order_data, totals, payment)
    send_order_notifications(order)
    return order
```

**Detection:** Function >50 lines or requires scrolling to read.

---

### Deep Nesting

Excessive indentation making code hard to follow.

```javascript
// BAD: Deep nesting
function processData(data) {
  if (data) {
    if (data.items) {
      if (data.items.length > 0) {
        for (const item of data.items) {
          if (item.isValid) {
            if (item.type === 'premium') {
              if (item.price > 100) {
                // Finally do something
                processItem(item);
              }
            }
          }
        }
      }
    }
  }
}

// GOOD: Early returns and guard clauses
function processData(data) {
  if (!data?.items?.length) {
    return;
  }

  const premiumItems = data.items.filter(
    item => item.isValid && item.type === 'premium' && item.price > 100
  );

  premiumItems.forEach(processItem);
}
```

**Detection:** Indentation >4 levels deep.

---

### Magic Numbers and Strings

Hard-coded values without explanation.

```go
// BAD: Magic numbers
func calculateDiscount(total float64, userType int) float64 {
    if userType == 1 {
        return total * 0.15
    } else if userType == 2 {
        return total * 0.25
    }
    return total * 0.05
}

// GOOD: Named constants
const (
    UserTypeRegular  = 1
    UserTypePremium  = 2

    DiscountRegular  = 0.05
    DiscountStandard = 0.15
    DiscountPremium  = 0.25
)

func calculateDiscount(total float64, userType int) float64 {
    switch userType {
    case UserTypePremium:
        return total * DiscountPremium
    case UserTypeRegular:
        return total * DiscountStandard
    default:
        return total * DiscountRegular
    }
}
```

**Detection:** Literal numbers (except 0, 1) or repeated string literals.

---

### Primitive Obsession

Using primitives instead of small objects.

```typescript
// BAD: Primitives everywhere
function createUser(
  name: string,
  email: string,
  phone: string,
  street: string,
  city: string,
  zipCode: string,
  country: string
): User { ... }

// GOOD: Value objects
interface Address {
  street: string;
  city: string;
  zipCode: string;
  country: string;
}

interface ContactInfo {
  email: string;
  phone: string;
}

function createUser(
  name: string,
  contact: ContactInfo,
  address: Address
): User { ... }
```

**Detection:** Functions with >4 parameters of same type, or related primitives always passed together.

---

## Logic Antipatterns

### Boolean Blindness

Passing booleans that make code unreadable at call sites.

```swift
// BAD: What do these booleans mean?
user.configure(true, false, true, false)

// GOOD: Named parameters or option objects
user.configure(
    sendWelcomeEmail: true,
    requireVerification: false,
    enableNotifications: true,
    isAdmin: false
)

// Or use an options struct
struct UserConfiguration {
    var sendWelcomeEmail: Bool = true
    var requireVerification: Bool = false
    var enableNotifications: Bool = true
    var isAdmin: Bool = false
}

user.configure(UserConfiguration())
```

**Detection:** Function calls with multiple boolean literals.

---

### Null Returns for Collections

Returning null instead of empty collections.

```kotlin
// BAD: Returning null
fun findUsersByRole(role: String): List<User>? {
    val users = repository.findByRole(role)
    return if (users.isEmpty()) null else users
}

// Caller must handle null
val users = findUsersByRole("admin")
if (users != null) {
    users.forEach { ... }
}

// GOOD: Return empty collection
fun findUsersByRole(role: String): List<User> {
    return repository.findByRole(role)
}

// Caller can iterate directly
findUsersByRole("admin").forEach { ... }
```

**Detection:** Functions returning nullable collections.

---

### Stringly Typed Code

Using strings where enums or types should be used.

```python
# BAD: String-based logic
def handle_event(event_type: str, data: dict):
    if event_type == "user_created":
        handle_user_created(data)
    elif event_type == "user_updated":
        handle_user_updated(data)
    elif event_type == "user_dleted":  # Typo won't be caught
        handle_user_deleted(data)

# GOOD: Enum-based
from enum import Enum

class EventType(Enum):
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"

def handle_event(event_type: EventType, data: dict):
    handlers = {
        EventType.USER_CREATED: handle_user_created,
        EventType.USER_UPDATED: handle_user_updated,
        EventType.USER_DELETED: handle_user_deleted,
    }
    handlers[event_type](data)
```

**Detection:** String comparisons for type/status/category values.

---

## Security Antipatterns

### SQL Injection

String concatenation in SQL queries.

```javascript
// BAD: String concatenation
const query = `SELECT * FROM users WHERE id = ${userId}`;
db.query(query);

// BAD: String templates still vulnerable
const query = `SELECT * FROM users WHERE name = '${userName}'`;

// GOOD: Parameterized queries
const query = 'SELECT * FROM users WHERE id = $1';
db.query(query, [userId]);

// GOOD: Using ORM safely
User.findOne({ where: { id: userId } });
```

**Detection:** String concatenation or template literals with SQL keywords.

---

### Hardcoded Credentials

Secrets in source code.

```python
# BAD: Hardcoded secrets
API_KEY = "sk-abc123xyz789"
DATABASE_URL = "postgresql://admin:password123@prod-db.internal:5432/app"

# GOOD: Environment variables
import os

API_KEY = os.environ["API_KEY"]
DATABASE_URL = os.environ["DATABASE_URL"]

# GOOD: Secrets manager
from aws_secretsmanager import get_secret

API_KEY = get_secret("api-key")
```

**Detection:** Variables named `password`, `secret`, `key`, `token` with string literals.

---

### Unsafe Deserialization

Deserializing untrusted data without validation.

```python
# BAD: Binary serialization from untrusted source can execute arbitrary code
# Examples: Python's binary serialization, yaml.load without SafeLoader

# GOOD: Use safe alternatives
import json

def load_data(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

# GOOD: Use SafeLoader for YAML
import yaml

with open('config.yaml') as f:
    config = yaml.safe_load(f)
```

**Detection:** Binary deserialization functions, yaml.load without safe loader, dynamic code execution on external data.

---

### Missing Input Validation

Trusting user input without validation.

```typescript
// BAD: No validation
app.post('/user', (req, res) => {
  const user = db.create({
    name: req.body.name,
    email: req.body.email,
    role: req.body.role  // User can set themselves as admin!
  });
  res.json(user);
});

// GOOD: Validate and sanitize
import { z } from 'zod';

const CreateUserSchema = z.object({
  name: z.string().min(1).max(100),
  email: z.string().email(),
  // role is NOT accepted from input
});

app.post('/user', (req, res) => {
  const validated = CreateUserSchema.parse(req.body);
  const user = db.create({
    ...validated,
    role: 'user'  // Default role, not from input
  });
  res.json(user);
});
```

**Detection:** Request body/params used directly without validation schema.

---

## Performance Antipatterns

### N+1 Query Problem

Loading related data one record at a time.

```python
# BAD: N+1 queries
def get_orders_with_items():
    orders = Order.query.all()  # 1 query
    for order in orders:
        items = OrderItem.query.filter_by(order_id=order.id).all()  # N queries
        order.items = items
    return orders

# GOOD: Eager loading
def get_orders_with_items():
    return Order.query.options(
        joinedload(Order.items)
    ).all()  # 1 query with JOIN

# GOOD: Batch loading
def get_orders_with_items():
    orders = Order.query.all()
    order_ids = [o.id for o in orders]
    items = OrderItem.query.filter(
        OrderItem.order_id.in_(order_ids)
    ).all()  # 2 queries total
    # Group items by order_id...
```

**Detection:** Database queries inside loops.

---

### Unbounded Collections

Loading unlimited data into memory.

```go
// BAD: Load all records
func GetAllUsers() ([]User, error) {
    return db.Find(&[]User{})  // Could be millions
}

// GOOD: Pagination
func GetUsers(page, pageSize int) ([]User, error) {
    offset := (page - 1) * pageSize
    return db.Limit(pageSize).Offset(offset).Find(&[]User{})
}

// GOOD: Streaming for large datasets
func ProcessAllUsers(handler func(User) error) error {
    rows, err := db.Model(&User{}).Rows()
    if err != nil {
        return err
    }
    defer rows.Close()

    for rows.Next() {
        var user User
        db.ScanRows(rows, &user)
        if err := handler(user); err != nil {
            return err
        }
    }
    return nil
}
```

**Detection:** `findAll()`, `find({})`, or queries without `LIMIT`.

---

### Synchronous I/O in Hot Paths

Blocking operations in request handlers.

```javascript
// BAD: Sync file read on every request
app.get('/config', (req, res) => {
  const config = fs.readFileSync('./config.json');  // Blocks event loop
  res.json(JSON.parse(config));
});

// GOOD: Load once at startup
const config = JSON.parse(fs.readFileSync('./config.json'));

app.get('/config', (req, res) => {
  res.json(config);
});

// GOOD: Async with caching
let configCache = null;

app.get('/config', async (req, res) => {
  if (!configCache) {
    configCache = JSON.parse(await fs.promises.readFile('./config.json'));
  }
  res.json(configCache);
});
```

**Detection:** `readFileSync`, `execSync`, or blocking calls in request handlers.

---

## Testing Antipatterns

### Test Code Duplication

Repeating setup in every test.

```typescript
// BAD: Duplicate setup
describe('UserService', () => {
  it('should create user', async () => {
    const db = await createTestDatabase();
    const userRepo = new UserRepository(db);
    const emailService = new MockEmailService();
    const service = new UserService(userRepo, emailService);

    const user = await service.create({ name: 'Test' });
    expect(user.name).toBe('Test');
  });

  it('should update user', async () => {
    const db = await createTestDatabase();  // Duplicated
    const userRepo = new UserRepository(db);  // Duplicated
    const emailService = new MockEmailService();  // Duplicated
    const service = new UserService(userRepo, emailService);  // Duplicated

    // ...
  });
});

// GOOD: Shared setup
describe('UserService', () => {
  let service: UserService;
  let db: TestDatabase;

  beforeEach(async () => {
    db = await createTestDatabase();
    const userRepo = new UserRepository(db);
    const emailService = new MockEmailService();
    service = new UserService(userRepo, emailService);
  });

  afterEach(async () => {
    await db.cleanup();
  });

  it('should create user', async () => {
    const user = await service.create({ name: 'Test' });
    expect(user.name).toBe('Test');
  });
});
```

---

### Testing Implementation Instead of Behavior

Tests coupled to internal implementation.

```python
# BAD: Testing implementation details
def test_add_item_to_cart():
    cart = ShoppingCart()
    cart.add_item(Product("Apple", 1.00))

    # Testing internal structure
    assert cart._items[0].name == "Apple"
    assert cart._total == 1.00

# GOOD: Testing behavior
def test_add_item_to_cart():
    cart = ShoppingCart()
    cart.add_item(Product("Apple", 1.00))

    # Testing public behavior
    assert cart.item_count == 1
    assert cart.total == 1.00
    assert cart.contains("Apple")
```

---

## Async Antipatterns

### Floating Promises

Promises without await or catch.

```typescript
// BAD: Floating promise
async function saveUser(user: User) {
  db.save(user);  // Not awaited, errors lost
  logger.info('User saved');  // Logs before save completes
}

// BAD: Fire and forget in loop
for (const item of items) {
  processItem(item);  // All run in parallel, no error handling
}

// GOOD: Await the promise
async function saveUser(user: User) {
  await db.save(user);
  logger.info('User saved');
}

// GOOD: Process with proper handling
await Promise.all(items.map(item => processItem(item)));

// Or sequentially
for (const item of items) {
  await processItem(item);
}
```

**Detection:** Async function calls without `await` or `.then()`.

---

### Callback Hell

Deeply nested callbacks.

```javascript
// BAD: Callback hell
getUser(userId, (err, user) => {
  if (err) return handleError(err);
  getOrders(user.id, (err, orders) => {
    if (err) return handleError(err);
    getProducts(orders[0].productIds, (err, products) => {
      if (err) return handleError(err);
      renderPage(user, orders, products, (err) => {
        if (err) return handleError(err);
        console.log('Done');
      });
    });
  });
});

// GOOD: Async/await
async function loadPage(userId) {
  try {
    const user = await getUser(userId);
    const orders = await getOrders(user.id);
    const products = await getProducts(orders[0].productIds);
    await renderPage(user, orders, products);
    console.log('Done');
  } catch (err) {
    handleError(err);
  }
}
```

**Detection:** >2 levels of callback nesting.

---

### Async in Constructor

Async operations in constructors.

```typescript
// BAD: Async in constructor
class DatabaseConnection {
  constructor(url: string) {
    this.connect(url);  // Fire-and-forget async
  }

  private async connect(url: string) {
    this.client = await createClient(url);
  }
}

// GOOD: Factory method
class DatabaseConnection {
  private constructor(private client: Client) {}

  static async create(url: string): Promise<DatabaseConnection> {
    const client = await createClient(url);
    return new DatabaseConnection(client);
  }
}

// Usage
const db = await DatabaseConnection.create(url);
```

**Detection:** `async` calls or `.then()` in constructor.
