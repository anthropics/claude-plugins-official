# Clean Code Principles

Comprehensive guide to writing clean, maintainable, and readable code.
Based on industry best practices and proven software engineering principles.

---

## SOLID Principles in Depth

### Single Responsibility Principle (SRP)

**Definition**: A class should have only one reason to change.

**Before (Violation):**
```javascript
class User {
  constructor(name, email) {
    this.name = name;
    this.email = email;
  }

  // User data management
  save() {
    db.query('INSERT INTO users...');
  }

  // Email validation - different responsibility
  validateEmail() {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(this.email);
  }

  // Report generation - completely different responsibility
  generateReport() {
    return `User Report: ${this.name}, ${this.email}`;
  }

  // Sending emails - yet another responsibility
  sendWelcomeEmail() {
    emailService.send(this.email, 'Welcome!');
  }
}
```

**After (Correct):**
```javascript
class User {
  constructor(name, email) {
    this.name = name;
    this.email = email;
  }
}

class UserRepository {
  save(user) {
    db.query('INSERT INTO users...', [user.name, user.email]);
  }

  findById(id) {
    return db.query('SELECT * FROM users WHERE id = $1', [id]);
  }
}

class EmailValidator {
  static isValid(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  }
}

class UserReportGenerator {
  generate(user) {
    return `User Report: ${user.name}, ${user.email}`;
  }
}

class UserNotificationService {
  sendWelcome(user) {
    emailService.send(user.email, 'Welcome!');
  }
}
```

---

### Open/Closed Principle (OCP)

**Definition**: Software entities should be open for extension but closed for modification.

**Before (Violation):**
```javascript
class PaymentProcessor {
  process(payment) {
    if (payment.type === 'credit_card') {
      // Credit card processing
      return this.processCreditCard(payment);
    } else if (payment.type === 'paypal') {
      // PayPal processing
      return this.processPayPal(payment);
    } else if (payment.type === 'crypto') {
      // Every new payment type requires modifying this class
      return this.processCrypto(payment);
    }
  }
}
```

**After (Correct):**
```javascript
// Payment processor interface
class PaymentProcessor {
  process(payment) {
    throw new Error('Must implement process method');
  }
}

// Concrete implementations
class CreditCardProcessor extends PaymentProcessor {
  process(payment) {
    // Credit card specific logic
  }
}

class PayPalProcessor extends PaymentProcessor {
  process(payment) {
    // PayPal specific logic
  }
}

class CryptoProcessor extends PaymentProcessor {
  process(payment) {
    // Crypto specific logic
  }
}

// Factory to create the right processor
class PaymentProcessorFactory {
  static create(type) {
    const processors = {
      credit_card: CreditCardProcessor,
      paypal: PayPalProcessor,
      crypto: CryptoProcessor
    };

    const ProcessorClass = processors[type];
    if (!ProcessorClass) {
      throw new Error(`Unknown payment type: ${type}`);
    }

    return new ProcessorClass();
  }
}

// Usage - adding new payment types doesn't modify existing code
const processor = PaymentProcessorFactory.create(payment.type);
processor.process(payment);
```

---

### Liskov Substitution Principle (LSP)

**Definition**: Objects of a superclass should be replaceable with objects of its subclasses without breaking the application.

**Before (Violation):**
```javascript
class Bird {
  fly() {
    return 'Flying...';
  }
}

class Penguin extends Bird {
  fly() {
    throw new Error('Penguins cannot fly!'); // Violates LSP
  }
}

function makeBirdFly(bird) {
  return bird.fly(); // Breaks with Penguin
}
```

**After (Correct):**
```javascript
class Bird {
  move() {
    throw new Error('Must implement move method');
  }
}

class FlyingBird extends Bird {
  move() {
    return this.fly();
  }

  fly() {
    return 'Flying...';
  }
}

class SwimmingBird extends Bird {
  move() {
    return this.swim();
  }

  swim() {
    return 'Swimming...';
  }
}

class Sparrow extends FlyingBird { }

class Penguin extends SwimmingBird { }

function makeBirdMove(bird) {
  return bird.move(); // Works with any Bird
}
```

---

### Interface Segregation Principle (ISP)

**Definition**: Clients should not be forced to depend on interfaces they don't use.

**Before (Violation):**
```javascript
class Worker {
  work() { }
  eat() { }
  sleep() { }
  attendMeeting() { }
  submitReport() { }
}

class Robot extends Worker {
  work() {
    return 'Working...';
  }

  eat() {
    throw new Error('Robots do not eat'); // Forced to implement
  }

  sleep() {
    throw new Error('Robots do not sleep'); // Forced to implement
  }

  // ... more methods it doesn't need
}
```

**After (Correct):**
```javascript
// Smaller, focused interfaces
class Workable {
  work() { throw new Error('Implement work'); }
}

class Eatable {
  eat() { throw new Error('Implement eat'); }
}

class Sleepable {
  sleep() { throw new Error('Implement sleep'); }
}

// Human implements all
class Human {
  work() { return 'Human working...'; }
  eat() { return 'Human eating...'; }
  sleep() { return 'Human sleeping...'; }
}

// Robot only implements what it needs
class Robot {
  work() { return 'Robot working...'; }
}
```

---

### Dependency Inversion Principle (DIP)

**Definition**: High-level modules should not depend on low-level modules. Both should depend on abstractions.

**Before (Violation):**
```javascript
class MySQLDatabase {
  query(sql) {
    // MySQL specific implementation
  }
}

class UserService {
  constructor() {
    // Direct dependency on concrete implementation
    this.database = new MySQLDatabase();
  }

  getUser(id) {
    return this.database.query(`SELECT * FROM users WHERE id = ${id}`);
  }
}
```

**After (Correct):**
```javascript
// Abstract database interface
class Database {
  query(sql, params) {
    throw new Error('Implement query method');
  }
}

// Concrete implementations
class MySQLDatabase extends Database {
  query(sql, params) {
    // MySQL specific implementation
  }
}

class PostgresDatabase extends Database {
  query(sql, params) {
    // Postgres specific implementation
  }
}

// UserService depends on abstraction
class UserService {
  constructor(database) {
    this.database = database; // Injected dependency
  }

  getUser(id) {
    return this.database.query('SELECT * FROM users WHERE id = $1', [id]);
  }
}

// Usage - easy to swap implementations
const database = new PostgresDatabase();
const userService = new UserService(database);
```

---

## Code Smells and Refactoring

### Long Method

**Smell**: Method does too much, hard to understand.

**Refactoring**: Extract Method

```javascript
// Before
function processOrder(order) {
  // Validate order
  if (!order.items) throw new Error('No items');
  if (order.items.length === 0) throw new Error('Empty order');
  for (const item of order.items) {
    if (item.quantity <= 0) throw new Error('Invalid quantity');
    if (item.price < 0) throw new Error('Invalid price');
  }

  // Calculate totals
  let subtotal = 0;
  for (const item of order.items) {
    subtotal += item.price * item.quantity;
  }
  const tax = subtotal * 0.1;
  const shipping = subtotal > 100 ? 0 : 10;
  const total = subtotal + tax + shipping;

  // Create invoice
  const invoice = {
    orderId: order.id,
    items: order.items,
    subtotal,
    tax,
    shipping,
    total,
    date: new Date()
  };

  // Save to database
  db.orders.update(order.id, { status: 'processed' });
  db.invoices.create(invoice);

  // Send notifications
  emailService.send(order.customerEmail, 'Order processed');
  smsService.send(order.customerPhone, 'Order processed');

  return invoice;
}

// After
function processOrder(order) {
  validateOrder(order);
  const totals = calculateTotals(order);
  const invoice = createInvoice(order, totals);
  saveOrder(order, invoice);
  notifyCustomer(order);
  return invoice;
}

function validateOrder(order) {
  if (!order.items || order.items.length === 0) {
    throw new ValidationError('Order must have items');
  }
  order.items.forEach(validateOrderItem);
}

function validateOrderItem(item) {
  if (item.quantity <= 0) throw new ValidationError('Invalid quantity');
  if (item.price < 0) throw new ValidationError('Invalid price');
}

function calculateTotals(order) {
  const subtotal = order.items.reduce(
    (sum, item) => sum + item.price * item.quantity, 0
  );
  return {
    subtotal,
    tax: subtotal * 0.1,
    shipping: subtotal > 100 ? 0 : 10,
    total: subtotal + subtotal * 0.1 + (subtotal > 100 ? 0 : 10)
  };
}

function createInvoice(order, totals) {
  return {
    orderId: order.id,
    items: order.items,
    ...totals,
    date: new Date()
  };
}
```

---

### Magic Numbers/Strings

**Smell**: Unexplained numeric or string literals in code.

```javascript
// Before
if (user.age >= 18) { }
if (order.total > 100) { }
if (retries < 3) { }
if (status === 'ACTV') { }

// After
const MINIMUM_AGE = 18;
const FREE_SHIPPING_THRESHOLD = 100;
const MAX_RETRY_ATTEMPTS = 3;

const OrderStatus = {
  ACTIVE: 'ACTIVE',
  PENDING: 'PENDING',
  CANCELLED: 'CANCELLED'
};

if (user.age >= MINIMUM_AGE) { }
if (order.total > FREE_SHIPPING_THRESHOLD) { }
if (retries < MAX_RETRY_ATTEMPTS) { }
if (status === OrderStatus.ACTIVE) { }
```

---

### Deep Nesting

**Smell**: Too many levels of indentation make code hard to follow.

```javascript
// Before - pyramid of doom
function processUser(user) {
  if (user) {
    if (user.isActive) {
      if (user.hasPermission('edit')) {
        if (user.subscription) {
          if (user.subscription.isValid()) {
            // Finally do something
            return doSomething(user);
          } else {
            throw new Error('Invalid subscription');
          }
        } else {
          throw new Error('No subscription');
        }
      } else {
        throw new Error('No permission');
      }
    } else {
      throw new Error('User not active');
    }
  } else {
    throw new Error('No user');
  }
}

// After - guard clauses
function processUser(user) {
  if (!user) {
    throw new Error('No user');
  }

  if (!user.isActive) {
    throw new Error('User not active');
  }

  if (!user.hasPermission('edit')) {
    throw new Error('No permission');
  }

  if (!user.subscription) {
    throw new Error('No subscription');
  }

  if (!user.subscription.isValid()) {
    throw new Error('Invalid subscription');
  }

  return doSomething(user);
}
```

---

## Function Design Guidelines

### Pure Functions

Functions without side effects are easier to test and reason about.

```javascript
// Impure - modifies external state
let total = 0;
function addToTotal(amount) {
  total += amount; // Side effect
  return total;
}

// Pure - no side effects
function add(a, b) {
  return a + b;
}

function calculateTotal(items) {
  return items.reduce((sum, item) => sum + item.price, 0);
}
```

### Command-Query Separation

Functions should either do something (command) or return something (query), not both.

```javascript
// Bad - does both
function getAndIncrementCounter() {
  const value = counter;
  counter++;
  return value;
}

// Good - separated
function getCounter() {
  return counter;
}

function incrementCounter() {
  counter++;
}
```

### Argument Guidelines

```javascript
// Ideal: 0-2 arguments
function greet(name) { }
function add(a, b) { }

// Acceptable: 3 arguments
function createUser(name, email, role) { }

// Better for 3+ arguments: use object
function createUser({ name, email, role, department, manager }) { }

// Never: flag arguments
function processOrder(order, isExpress) { } // Bad

// Better: separate functions or enum
function processStandardOrder(order) { }
function processExpressOrder(order) { }

// Or
const ShippingType = { STANDARD: 'standard', EXPRESS: 'express' };
function processOrder(order, shippingType) { }
```

---

## Comment Best Practices

### Good Comments

```javascript
// Explain WHY, not WHAT
// Using binary search because list is always sorted and can be very large
const index = binarySearch(sortedItems, target);

// Clarify complex regular expressions
// Matches: user@example.com, user.name+tag@sub.example.co.uk
const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

// Document assumptions and constraints
// Assumes prices are in cents to avoid floating-point issues
function formatPrice(priceInCents) {
  return `$${(priceInCents / 100).toFixed(2)}`;
}

// Warn about consequences
// WARNING: This clears all user data. Cannot be undone.
async function resetUserAccount(userId) { }

// TODO with ticket reference
// TODO(JIRA-123): Implement retry logic when rate limited
```

### Bad Comments

```javascript
// Redundant - code already says this
// Increment counter by 1
counter++;

// Commented-out code - delete it
// function oldImplementation() { ... }

// Outdated - worse than no comment
// Returns user name
function getFullUserDetails() { } // Actually returns full details now

// Noise
// Constructor
constructor() { }
```
