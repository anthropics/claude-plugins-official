# Architectural Anti-Patterns

Common architectural mistakes to avoid, with detection signs, consequences,
and refactoring strategies. Recognizing these patterns early prevents costly
technical debt.

---

## Structural Anti-Patterns

### God Object / God Class

**Description**: A single class that knows too much and does too much, centralizing
a large amount of functionality.

**Detection Signs**:
- Class has 1000+ lines of code
- Class has 20+ methods
- Class is imported by most other classes
- Changes to this class affect many features
- Difficult to write unit tests

**Example of the Problem**:
```javascript
// BAD: God class doing everything
class ApplicationManager {
  // User management
  createUser(data) { }
  deleteUser(id) { }
  authenticateUser(email, password) { }
  resetPassword(email) { }

  // Order management
  createOrder(userId, items) { }
  processPayment(orderId) { }
  shipOrder(orderId) { }
  refundOrder(orderId) { }

  // Notification
  sendEmail(to, subject, body) { }
  sendSMS(to, message) { }
  sendPushNotification(userId, message) { }

  // Reporting
  generateSalesReport() { }
  generateUserReport() { }

  // ... 50 more methods
}
```

**Refactored Solution**:
```javascript
// GOOD: Split by responsibility
class UserService {
  createUser(data) { }
  deleteUser(id) { }
}

class AuthService {
  authenticate(email, password) { }
  resetPassword(email) { }
}

class OrderService {
  createOrder(userId, items) { }
  processPayment(orderId) { }
}

class NotificationService {
  sendEmail(to, subject, body) { }
  sendSMS(to, message) { }
}

class ReportingService {
  generateSalesReport() { }
  generateUserReport() { }
}
```

---

### Distributed Monolith

**Description**: A system that looks like microservices but has tight coupling
between services, requiring coordinated deployments and lacking independent scalability.

**Detection Signs**:
- Services share a database
- Changes require multiple service deployments
- Synchronous calls between many services
- Shared code libraries with business logic
- Cannot deploy services independently

**Example of the Problem**:
```
+-----------+    +------------+    +-----------+
|  Service  |--->|  Service   |--->|  Service  |
|     A     |    |     B      |    |     C     |
+-----------+    +------------+    +-----------+
      |               |                  |
      v               v                  v
      +-------- Shared Database ---------+
```

**Refactored Solution**:
```
+------------+    +------------+    +------------+
|  Service   |    |  Service   |    |  Service   |
|     A      |    |     B      |    |     C      |
+-----+------+    +-----+------+    +-----+------+
      |                 |                 |
      v                 v                 v
  +-------+        +-------+        +-------+
  | DB A  |        | DB B  |        | DB C  |
  +-------+        +-------+        +-------+

      +------- Event Bus (async) -------+
```

**Key Fixes**:
- Each service owns its data
- Asynchronous communication via events
- API contracts for synchronous calls
- No shared business logic libraries

---

### Big Ball of Mud

**Description**: A system with no discernible architecture, where any component
can call any other component, and the codebase has grown organically without structure.

**Detection Signs**:
- No clear module boundaries
- Circular dependencies everywhere
- Cannot explain the architecture
- New developers take months to be productive
- Fear of making changes

**Refactoring Strategy**:
1. Map existing dependencies
2. Identify natural clusters
3. Define clear interfaces
4. Gradually extract modules
5. Enforce boundaries with linting rules

```javascript
// eslint.config.js - Enforce boundaries
module.exports = {
  rules: {
    'import/no-restricted-paths': ['error', {
      zones: [
        { target: './src/orders', from: './src/users/internal' },
        { target: './src/users', from: './src/orders/internal' }
      ]
    }]
  }
};
```

---

## Data Anti-Patterns

### N+1 Query Problem

**Description**: Loading a list of items, then executing an additional query
for each item to fetch related data.

**Detection Signs**:
- Slow page loads with lists
- Database shows many similar queries
- Performance degrades with list size
- Queries inside loops

**Example of the Problem**:
```javascript
// BAD: N+1 queries
async function getOrdersWithProducts() {
  const orders = await db.query('SELECT * FROM orders'); // 1 query

  for (const order of orders) {
    // N additional queries!
    order.products = await db.query(
      'SELECT * FROM order_items WHERE order_id = $1',
      [order.id]
    );
  }

  return orders;
}
```

**Refactored Solutions**:

```javascript
// GOOD: JOIN in single query
async function getOrdersWithProducts() {
  return db.query(`
    SELECT o.*, oi.product_id, oi.quantity, p.name, p.price
    FROM orders o
    LEFT JOIN order_items oi ON oi.order_id = o.id
    LEFT JOIN products p ON p.id = oi.product_id
  `);
}

// GOOD: Batch loading (DataLoader pattern)
const orderItemsLoader = new DataLoader(async (orderIds) => {
  const items = await db.query(
    'SELECT * FROM order_items WHERE order_id = ANY($1)',
    [orderIds]
  );
  return orderIds.map(id => items.filter(i => i.order_id === id));
});

// GOOD: ORM eager loading
const orders = await Order.findAll({
  include: [{ model: OrderItem, include: [Product] }]
});
```

---

### Database as Integration Point

**Description**: Using the database as the interface between applications,
with multiple applications reading from and writing to shared tables.

**Detection Signs**:
- Multiple apps have direct database access
- Schema changes break multiple apps
- No clear data ownership
- Database becomes bottleneck
- Data consistency issues

**Example of the Problem**:
```
+--------+    +--------+    +--------+
| App A  |    | App B  |    | App C  |
+---+----+    +---+----+    +---+----+
    |             |             |
    +------+------+------+------+
           |
    +------+------+
    |  Shared DB  |
    +-------------+
```

**Refactored Solution**:
```
+--------+    +--------+    +--------+
| App A  |    | App B  |    | App C  |
+---+----+    +---+----+    +---+----+
    |             |             |
    |     +-------+-------+     |
    +---->|   API Layer   |<----+
          +-------+-------+
                  |
          +-------+-------+
          |   Database    |
          +---------------+
```

---

### Anemic Domain Model

**Description**: Domain objects that contain only data (getters/setters) with
all logic in separate service classes.

**Detection Signs**:
- Entities are just data containers
- All behavior in services
- "Service layer does everything"
- Entities have only getters/setters

**Example of the Problem**:
```javascript
// BAD: Anemic domain model
class Order {
  id;
  items = [];
  status;
  total;
}

class OrderService {
  addItem(order, product, quantity) {
    order.items.push({ product, quantity });
    this.recalculateTotal(order);
  }

  recalculateTotal(order) {
    order.total = order.items.reduce(
      (sum, item) => sum + item.product.price * item.quantity,
      0
    );
  }

  canBeCancelled(order) {
    return order.status === 'pending';
  }

  cancel(order) {
    if (!this.canBeCancelled(order)) {
      throw new Error('Cannot cancel');
    }
    order.status = 'cancelled';
  }
}
```

**Refactored Solution**:
```javascript
// GOOD: Rich domain model
class Order {
  #items = [];
  #status = 'pending';

  get total() {
    return this.#items.reduce(
      (sum, item) => sum + item.subtotal,
      0
    );
  }

  addItem(product, quantity) {
    if (this.#status !== 'pending') {
      throw new Error('Cannot modify non-pending order');
    }
    this.#items.push(new OrderItem(product, quantity));
  }

  cancel() {
    if (!this.canBeCancelled()) {
      throw new Error('Cannot cancel order in current state');
    }
    this.#status = 'cancelled';
  }

  canBeCancelled() {
    return this.#status === 'pending';
  }
}

class OrderItem {
  constructor(product, quantity) {
    this.product = product;
    this.quantity = quantity;
  }

  get subtotal() {
    return this.product.price * this.quantity;
  }
}
```

---

## Integration Anti-Patterns

### Chatty Interface

**Description**: A service interface that requires many calls to complete a
single logical operation.

**Detection Signs**:
- Many sequential API calls needed
- High network latency
- Lot of small HTTP requests
- Performance issues with remote calls

**Example of the Problem**:
```javascript
// BAD: Many calls for one operation
async function displayUserDashboard(userId) {
  const user = await api.get(`/users/${userId}`);
  const preferences = await api.get(`/users/${userId}/preferences`);
  const orders = await api.get(`/users/${userId}/orders`);
  const notifications = await api.get(`/users/${userId}/notifications`);
  const recommendations = await api.get(`/users/${userId}/recommendations`);
  // 5 round trips!
}
```

**Refactored Solution**:
```javascript
// GOOD: Aggregate endpoint
async function displayUserDashboard(userId) {
  const dashboard = await api.get(`/users/${userId}/dashboard`);
  // 1 round trip!
  // Server aggregates: user, preferences, orders, notifications
}

// GOOD: GraphQL for flexible queries
const dashboard = await graphql(`
  query UserDashboard($userId: ID!) {
    user(id: $userId) {
      name
      preferences { theme language }
      orders(limit: 5) { id total status }
      notifications(unread: true) { id message }
    }
  }
`, { userId });
```

---

### Leaky Abstraction

**Description**: An abstraction that exposes implementation details it should hide,
forcing consumers to understand the underlying implementation.

**Detection Signs**:
- Consumers need implementation knowledge
- Changes to internals break consumers
- Abstraction doesn't fully encapsulate
- Exception types from underlying layers

**Example of the Problem**:
```javascript
// BAD: Leaky abstraction
class UserRepository {
  async findById(id) {
    // Leaks SQL implementation
    return this.db.query(`SELECT * FROM users WHERE id = ${id}`);
  }

  // Leaks PostgreSQL-specific error
  async save(user) {
    try {
      await this.db.query('INSERT INTO users...');
    } catch (error) {
      if (error.code === '23505') { // PostgreSQL-specific
        throw error; // Leaked!
      }
    }
  }
}
```

**Refactored Solution**:
```javascript
// GOOD: Proper abstraction
class UserRepository {
  async findById(id) {
    const result = await this.db.query(
      'SELECT * FROM users WHERE id = $1',
      [id]
    );
    return result.rows[0] ? this.toUser(result.rows[0]) : null;
  }

  async save(user) {
    try {
      await this.db.query(
        'INSERT INTO users (id, email) VALUES ($1, $2)',
        [user.id, user.email]
      );
    } catch (error) {
      // Translate to domain exception
      if (this.isDuplicateError(error)) {
        throw new DuplicateUserError(user.email);
      }
      throw new RepositoryError('Failed to save user', error);
    }
  }

  private isDuplicateError(error) {
    // Hide database-specific check
    return error.code === '23505' || error.code === 'ER_DUP_ENTRY';
  }

  private toUser(row) {
    return new User(row.id, row.email, row.name);
  }
}
```

---

## Process Anti-Patterns

### Lava Flow

**Description**: Dead code and forgotten experiments that remain in the codebase
because no one knows if they're needed.

**Detection Signs**:
- Commented-out code blocks
- Unused functions and classes
- "Don't delete this" comments
- Code with no tests or documentation
- Nobody knows what code does

**Refactoring Strategy**:
```bash
# Find unused exports
npx ts-prune

# Find dead code
npx knip

# Check code coverage to find untested code
npm run test:coverage
```

**Prevention**:
- Delete commented code (git has history)
- Add expiration dates to experiments
- Regular dead code audits
- Remove TODOs older than 6 months

---

### Golden Hammer

**Description**: Using a familiar technology or pattern for every problem,
regardless of its suitability.

**Detection Signs**:
- Same solution for every problem
- "We always use X"
- Ignored alternatives
- Forced fit of solution to problem

**Examples**:
- Using microservices for a simple CRUD app
- Using MongoDB for highly relational data
- Using GraphQL when REST would be simpler
- Applying every design pattern

**Prevention**:
- Evaluate alternatives for each problem
- Consider simplest solution first
- Match tool to problem, not vice versa

---

## Anti-Pattern Detection Checklist

Use this checklist during architecture reviews:

### Code Structure
- [ ] No class over 500 lines
- [ ] No function over 50 lines
- [ ] No module with 20+ imports
- [ ] No circular dependencies
- [ ] Clear module boundaries

### Data Access
- [ ] No queries in loops
- [ ] Single source of truth for data
- [ ] Clear data ownership
- [ ] No raw SQL strings (use parameterized)

### Integration
- [ ] No chatty interfaces (batch operations)
- [ ] Abstractions don't leak
- [ ] Error handling at boundaries
- [ ] Timeouts on all external calls

### Process
- [ ] No dead code (use static analysis)
- [ ] No commented-out code
- [ ] Technology choices documented with rationale
- [ ] Regular dependency updates
