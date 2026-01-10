# Design Patterns Reference

Comprehensive reference for architectural and design patterns commonly used in
software development. Each pattern includes context, implementation, and guidance
on when to use or avoid it.

---

## Creational Patterns

### Factory Pattern

**When to Use**: Object creation logic is complex or needs to be centralized.

```javascript
// Factory for creating different payment processors
class PaymentProcessorFactory {
  static create(type) {
    switch (type) {
      case 'stripe':
        return new StripeProcessor(process.env.STRIPE_KEY);
      case 'paypal':
        return new PayPalProcessor(process.env.PAYPAL_KEY);
      case 'braintree':
        return new BraintreeProcessor(process.env.BRAINTREE_KEY);
      default:
        throw new Error(`Unknown payment processor: ${type}`);
    }
  }
}

// Usage
const processor = PaymentProcessorFactory.create('stripe');
await processor.charge(amount, customer);
```

### Builder Pattern

**When to Use**: Object has many optional parameters or complex construction.

```javascript
class QueryBuilder {
  constructor(table) {
    this.table = table;
    this.conditions = [];
    this.orderFields = [];
    this.limitValue = null;
  }

  where(field, operator, value) {
    this.conditions.push({ field, operator, value });
    return this; // Enable chaining
  }

  orderBy(field, direction = 'ASC') {
    this.orderFields.push({ field, direction });
    return this;
  }

  limit(value) {
    this.limitValue = value;
    return this;
  }

  build() {
    let query = `SELECT * FROM ${this.table}`;

    if (this.conditions.length > 0) {
      const whereClause = this.conditions
        .map(c => `${c.field} ${c.operator} $${this.conditions.indexOf(c) + 1}`)
        .join(' AND ');
      query += ` WHERE ${whereClause}`;
    }

    if (this.orderFields.length > 0) {
      const orderClause = this.orderFields
        .map(o => `${o.field} ${o.direction}`)
        .join(', ');
      query += ` ORDER BY ${orderClause}`;
    }

    if (this.limitValue) {
      query += ` LIMIT ${this.limitValue}`;
    }

    return {
      query,
      params: this.conditions.map(c => c.value)
    };
  }
}

// Usage
const { query, params } = new QueryBuilder('users')
  .where('status', '=', 'active')
  .where('created_at', '>', '2024-01-01')
  .orderBy('created_at', 'DESC')
  .limit(10)
  .build();
```

### Singleton Pattern

**When to Use**: Exactly one instance needed globally (database connections, configuration).

```javascript
class DatabaseConnection {
  static instance = null;

  constructor() {
    if (DatabaseConnection.instance) {
      return DatabaseConnection.instance;
    }

    this.pool = new Pool({
      connectionString: process.env.DATABASE_URL,
      max: 20
    });

    DatabaseConnection.instance = this;
  }

  static getInstance() {
    if (!DatabaseConnection.instance) {
      DatabaseConnection.instance = new DatabaseConnection();
    }
    return DatabaseConnection.instance;
  }

  query(sql, params) {
    return this.pool.query(sql, params);
  }
}

// Usage
const db = DatabaseConnection.getInstance();
const users = await db.query('SELECT * FROM users');
```

**Warning**: Singletons can make testing difficult. Consider dependency injection instead.

---

## Structural Patterns

### Repository Pattern

**When to Use**: Abstract data access layer from business logic.

```typescript
// Repository interface
interface UserRepository {
  findById(id: string): Promise<User | null>;
  findByEmail(email: string): Promise<User | null>;
  findAll(options?: { limit?: number; offset?: number }): Promise<User[]>;
  save(user: User): Promise<User>;
  update(id: string, data: Partial<User>): Promise<User>;
  delete(id: string): Promise<void>;
}

// PostgreSQL implementation
class PostgresUserRepository implements UserRepository {
  constructor(private db: Pool) {}

  async findById(id: string): Promise<User | null> {
    const result = await this.db.query(
      'SELECT * FROM users WHERE id = $1',
      [id]
    );
    return result.rows[0] || null;
  }

  async findByEmail(email: string): Promise<User | null> {
    const result = await this.db.query(
      'SELECT * FROM users WHERE email = $1',
      [email]
    );
    return result.rows[0] || null;
  }

  async save(user: User): Promise<User> {
    const result = await this.db.query(
      `INSERT INTO users (id, email, name, created_at)
       VALUES ($1, $2, $3, NOW())
       RETURNING *`,
      [user.id || uuidv4(), user.email, user.name]
    );
    return result.rows[0];
  }

  async update(id: string, data: Partial<User>): Promise<User> {
    const fields = Object.keys(data);
    const values = Object.values(data);
    const setClause = fields.map((f, i) => `${f} = $${i + 2}`).join(', ');

    const result = await this.db.query(
      `UPDATE users SET ${setClause}, updated_at = NOW()
       WHERE id = $1 RETURNING *`,
      [id, ...values]
    );
    return result.rows[0];
  }

  async delete(id: string): Promise<void> {
    await this.db.query('DELETE FROM users WHERE id = $1', [id]);
  }
}

// In-memory implementation for testing
class InMemoryUserRepository implements UserRepository {
  private users: Map<string, User> = new Map();

  async findById(id: string): Promise<User | null> {
    return this.users.get(id) || null;
  }

  async save(user: User): Promise<User> {
    const id = user.id || uuidv4();
    const savedUser = { ...user, id };
    this.users.set(id, savedUser);
    return savedUser;
  }

  // ... other methods
}
```

### Adapter Pattern

**When to Use**: Make incompatible interfaces work together.

```typescript
// Target interface our code expects
interface PaymentGateway {
  charge(amount: number, currency: string, source: string): Promise<PaymentResult>;
  refund(transactionId: string, amount?: number): Promise<RefundResult>;
}

// Stripe SDK (external interface)
class StripeSDK {
  createPaymentIntent(params: { amount: number; currency: string; payment_method: string }) { }
  refundPaymentIntent(id: string, params: { amount?: number }) { }
}

// Adapter to make Stripe work with our interface
class StripeAdapter implements PaymentGateway {
  constructor(private stripe: StripeSDK) {}

  async charge(amount: number, currency: string, source: string): Promise<PaymentResult> {
    const intent = await this.stripe.createPaymentIntent({
      amount: amount * 100, // Stripe uses cents
      currency: currency.toLowerCase(),
      payment_method: source
    });

    return {
      transactionId: intent.id,
      status: this.mapStatus(intent.status),
      amount: intent.amount / 100
    };
  }

  async refund(transactionId: string, amount?: number): Promise<RefundResult> {
    const refund = await this.stripe.refundPaymentIntent(transactionId, {
      amount: amount ? amount * 100 : undefined
    });

    return {
      refundId: refund.id,
      status: refund.status,
      amount: refund.amount / 100
    };
  }

  private mapStatus(stripeStatus: string): string {
    const statusMap = {
      'succeeded': 'completed',
      'processing': 'pending',
      'requires_action': 'action_required'
    };
    return statusMap[stripeStatus] || 'unknown';
  }
}
```

### Decorator Pattern

**When to Use**: Add behavior to objects dynamically without modifying them.

```typescript
// Base interface
interface DataFetcher {
  fetch(key: string): Promise<any>;
}

// Base implementation
class DatabaseFetcher implements DataFetcher {
  async fetch(key: string): Promise<any> {
    return db.query('SELECT * FROM data WHERE key = $1', [key]);
  }
}

// Caching decorator
class CachedFetcher implements DataFetcher {
  constructor(
    private fetcher: DataFetcher,
    private cache: Cache,
    private ttl: number = 3600
  ) {}

  async fetch(key: string): Promise<any> {
    const cached = await this.cache.get(key);
    if (cached) return cached;

    const data = await this.fetcher.fetch(key);
    await this.cache.set(key, data, this.ttl);
    return data;
  }
}

// Logging decorator
class LoggedFetcher implements DataFetcher {
  constructor(
    private fetcher: DataFetcher,
    private logger: Logger
  ) {}

  async fetch(key: string): Promise<any> {
    const start = Date.now();
    try {
      const data = await this.fetcher.fetch(key);
      this.logger.info('Fetch successful', { key, duration: Date.now() - start });
      return data;
    } catch (error) {
      this.logger.error('Fetch failed', { key, error, duration: Date.now() - start });
      throw error;
    }
  }
}

// Usage - compose decorators
const fetcher = new LoggedFetcher(
  new CachedFetcher(
    new DatabaseFetcher(),
    new RedisCache(),
    3600
  ),
  new Logger()
);
```

---

## Behavioral Patterns

### Strategy Pattern

**When to Use**: Algorithm needs to be selected at runtime.

```typescript
// Strategy interface
interface PricingStrategy {
  calculatePrice(basePrice: number, customer: Customer): number;
}

// Concrete strategies
class RegularPricing implements PricingStrategy {
  calculatePrice(basePrice: number): number {
    return basePrice;
  }
}

class PremiumPricing implements PricingStrategy {
  calculatePrice(basePrice: number): number {
    return basePrice * 0.9; // 10% discount
  }
}

class VIPPricing implements PricingStrategy {
  calculatePrice(basePrice: number): number {
    return basePrice * 0.8; // 20% discount
  }
}

// Context
class PriceCalculator {
  private strategy: PricingStrategy;

  setStrategy(strategy: PricingStrategy) {
    this.strategy = strategy;
  }

  calculateTotal(items: CartItem[], customer: Customer): number {
    return items.reduce((total, item) => {
      return total + this.strategy.calculatePrice(item.price, customer) * item.quantity;
    }, 0);
  }
}

// Usage
const calculator = new PriceCalculator();

switch (customer.tier) {
  case 'premium':
    calculator.setStrategy(new PremiumPricing());
    break;
  case 'vip':
    calculator.setStrategy(new VIPPricing());
    break;
  default:
    calculator.setStrategy(new RegularPricing());
}

const total = calculator.calculateTotal(cart.items, customer);
```

### Observer Pattern

**When to Use**: Objects need to be notified of changes in another object.

```typescript
// Event types
type EventType = 'order.created' | 'order.paid' | 'order.shipped';

// Observer interface
interface Observer {
  update(event: EventType, data: any): Promise<void>;
}

// Subject
class EventEmitter {
  private observers: Map<EventType, Observer[]> = new Map();

  subscribe(event: EventType, observer: Observer) {
    if (!this.observers.has(event)) {
      this.observers.set(event, []);
    }
    this.observers.get(event)!.push(observer);
  }

  unsubscribe(event: EventType, observer: Observer) {
    const observers = this.observers.get(event);
    if (observers) {
      const index = observers.indexOf(observer);
      if (index > -1) observers.splice(index, 1);
    }
  }

  async emit(event: EventType, data: any) {
    const observers = this.observers.get(event) || [];
    await Promise.all(observers.map(o => o.update(event, data)));
  }
}

// Concrete observers
class EmailNotifier implements Observer {
  async update(event: EventType, data: any) {
    if (event === 'order.shipped') {
      await sendEmail(data.customerEmail, 'Your order has shipped!');
    }
  }
}

class InventoryUpdater implements Observer {
  async update(event: EventType, data: any) {
    if (event === 'order.paid') {
      await decrementInventory(data.items);
    }
  }
}

class AnalyticsTracker implements Observer {
  async update(event: EventType, data: any) {
    await trackEvent(event, data);
  }
}

// Usage
const eventEmitter = new EventEmitter();
eventEmitter.subscribe('order.paid', new EmailNotifier());
eventEmitter.subscribe('order.paid', new InventoryUpdater());
eventEmitter.subscribe('order.paid', new AnalyticsTracker());

// When order is paid
await eventEmitter.emit('order.paid', order);
```

### Command Pattern

**When to Use**: Encapsulate requests as objects for queuing, logging, or undo.

```typescript
// Command interface
interface Command {
  execute(): Promise<void>;
  undo(): Promise<void>;
}

// Concrete commands
class CreateUserCommand implements Command {
  private createdUserId: string | null = null;

  constructor(
    private userService: UserService,
    private userData: CreateUserDto
  ) {}

  async execute(): Promise<void> {
    const user = await this.userService.create(this.userData);
    this.createdUserId = user.id;
  }

  async undo(): Promise<void> {
    if (this.createdUserId) {
      await this.userService.delete(this.createdUserId);
    }
  }
}

class UpdateOrderStatusCommand implements Command {
  private previousStatus: string | null = null;

  constructor(
    private orderService: OrderService,
    private orderId: string,
    private newStatus: string
  ) {}

  async execute(): Promise<void> {
    const order = await this.orderService.findById(this.orderId);
    this.previousStatus = order.status;
    await this.orderService.updateStatus(this.orderId, this.newStatus);
  }

  async undo(): Promise<void> {
    if (this.previousStatus) {
      await this.orderService.updateStatus(this.orderId, this.previousStatus);
    }
  }
}

// Command invoker with history
class CommandInvoker {
  private history: Command[] = [];

  async execute(command: Command): Promise<void> {
    await command.execute();
    this.history.push(command);
  }

  async undo(): Promise<void> {
    const command = this.history.pop();
    if (command) {
      await command.undo();
    }
  }

  async undoAll(): Promise<void> {
    while (this.history.length > 0) {
      await this.undo();
    }
  }
}
```

---

## Architectural Patterns

### Service Layer Pattern

**When to Use**: Separate business logic from controllers and data access.

```typescript
// Service layer with clear boundaries
class OrderService {
  constructor(
    private orderRepo: OrderRepository,
    private productRepo: ProductRepository,
    private paymentService: PaymentService,
    private notificationService: NotificationService,
    private eventEmitter: EventEmitter
  ) {}

  async createOrder(userId: string, items: OrderItem[]): Promise<Order> {
    // Validate products exist and have stock
    await this.validateItems(items);

    // Calculate totals
    const totals = await this.calculateTotals(items);

    // Create order
    const order = await this.orderRepo.save({
      userId,
      items,
      subtotal: totals.subtotal,
      tax: totals.tax,
      total: totals.total,
      status: 'pending'
    });

    // Emit event for async processing
    await this.eventEmitter.emit('order.created', order);

    return order;
  }

  async processPayment(orderId: string, paymentMethod: string): Promise<Order> {
    const order = await this.orderRepo.findById(orderId);
    if (!order) throw new NotFoundError('Order not found');
    if (order.status !== 'pending') {
      throw new InvalidStateError('Order cannot be paid');
    }

    // Process payment
    const paymentResult = await this.paymentService.charge(
      order.total,
      paymentMethod
    );

    // Update order
    const updatedOrder = await this.orderRepo.update(orderId, {
      status: 'paid',
      paymentId: paymentResult.transactionId
    });

    // Emit events
    await this.eventEmitter.emit('order.paid', updatedOrder);

    // Send notification
    await this.notificationService.sendOrderConfirmation(updatedOrder);

    return updatedOrder;
  }

  private async validateItems(items: OrderItem[]): Promise<void> {
    for (const item of items) {
      const product = await this.productRepo.findById(item.productId);
      if (!product) {
        throw new ValidationError(`Product not found: ${item.productId}`);
      }
      if (product.stock < item.quantity) {
        throw new ValidationError(`Insufficient stock for: ${product.name}`);
      }
    }
  }

  private async calculateTotals(items: OrderItem[]) {
    let subtotal = 0;
    for (const item of items) {
      const product = await this.productRepo.findById(item.productId);
      subtotal += product.price * item.quantity;
    }
    const tax = subtotal * 0.1; // 10% tax
    return { subtotal, tax, total: subtotal + tax };
  }
}
```

### Unit of Work Pattern

**When to Use**: Track changes to multiple entities and commit as single transaction.

```typescript
class UnitOfWork {
  private operations: Array<() => Promise<void>> = [];
  private rollbackOperations: Array<() => Promise<void>> = [];

  constructor(private db: Database) {}

  registerNew<T>(repo: Repository<T>, entity: T) {
    this.operations.push(() => repo.save(entity));
    this.rollbackOperations.push(() => repo.delete((entity as any).id));
  }

  registerDirty<T>(repo: Repository<T>, id: string, changes: Partial<T>) {
    // Store original for rollback
    this.operations.push(async () => {
      const original = await repo.findById(id);
      this.rollbackOperations.push(() => repo.update(id, original));
      await repo.update(id, changes);
    });
  }

  registerDeleted<T>(repo: Repository<T>, entity: T) {
    this.operations.push(() => repo.delete((entity as any).id));
    this.rollbackOperations.push(() => repo.save(entity));
  }

  async commit(): Promise<void> {
    const client = await this.db.connect();

    try {
      await client.query('BEGIN');

      for (const operation of this.operations) {
        await operation();
      }

      await client.query('COMMIT');
    } catch (error) {
      await client.query('ROLLBACK');

      // Execute rollback operations
      for (const rollback of this.rollbackOperations.reverse()) {
        try {
          await rollback();
        } catch (rollbackError) {
          console.error('Rollback failed:', rollbackError);
        }
      }

      throw error;
    } finally {
      client.release();
    }
  }
}
```

---

## Pattern Selection Guide

| Scenario | Recommended Pattern |
|----------|-------------------|
| Complex object creation | Factory, Builder |
| Need exactly one instance | Singleton (prefer DI) |
| Wrap external library | Adapter |
| Add behavior dynamically | Decorator |
| Algorithm varies | Strategy |
| React to state changes | Observer |
| Encapsulate operations | Command |
| Abstract data access | Repository |
| Separate business logic | Service Layer |
| Transactional changes | Unit of Work |
