# Integration Testing Patterns

Comprehensive patterns for integration testing including database testing,
API testing, external service mocking, and test environment management.

---

## Database Integration Testing

### Test Database Strategies

| Strategy | Speed | Isolation | Realism | Use Case |
|----------|-------|-----------|---------|----------|
| In-memory (SQLite) | Very Fast | High | Low | Simple queries |
| Docker container | Fast | High | High | Full compatibility |
| Shared test DB | Slow | Low | High | Legacy systems |
| Schema-per-test | Medium | High | High | Parallel tests |

### Docker-Based Testing

**Setup with Testcontainers:**
```javascript
const { PostgreSqlContainer } = require('@testcontainers/postgresql');

describe('Database Integration', () => {
  let container;
  let pool;

  beforeAll(async () => {
    container = await new PostgreSqlContainer()
      .withDatabase('testdb')
      .withUsername('test')
      .withPassword('test')
      .start();

    pool = new Pool({
      connectionString: container.getConnectionUri()
    });

    // Run migrations
    await migrate(pool);
  }, 60000); // 60s timeout for container start

  afterAll(async () => {
    await pool.end();
    await container.stop();
  });

  beforeEach(async () => {
    // Clean between tests
    await pool.query('TRUNCATE users, orders CASCADE');
  });

  it('should insert and retrieve user', async () => {
    const result = await pool.query(
      'INSERT INTO users (email, name) VALUES ($1, $2) RETURNING *',
      ['test@example.com', 'Test User']
    );

    const user = result.rows[0];
    expect(user.email).toBe('test@example.com');
    expect(user.id).toBeDefined();
  });
});
```

### Transaction-Based Isolation

**Rollback After Each Test:**
```javascript
describe('Repository Tests', () => {
  let client;

  beforeEach(async () => {
    client = await pool.connect();
    await client.query('BEGIN');
  });

  afterEach(async () => {
    await client.query('ROLLBACK');
    client.release();
  });

  it('should not persist changes between tests', async () => {
    await client.query(
      'INSERT INTO users (email) VALUES ($1)',
      ['test@example.com']
    );

    const result = await client.query('SELECT * FROM users');
    expect(result.rows).toHaveLength(1);
    // After ROLLBACK, this insert is undone
  });
});
```

### Testing Database Constraints

```javascript
describe('Database Constraints', () => {
  it('should enforce unique email constraint', async () => {
    await pool.query(
      'INSERT INTO users (email, name) VALUES ($1, $2)',
      ['unique@example.com', 'First']
    );

    await expect(
      pool.query(
        'INSERT INTO users (email, name) VALUES ($1, $2)',
        ['unique@example.com', 'Second']
      )
    ).rejects.toThrow(/duplicate key.*users_email_key/);
  });

  it('should enforce foreign key constraint', async () => {
    await expect(
      pool.query(
        'INSERT INTO orders (user_id, total) VALUES ($1, $2)',
        ['non-existent-user-id', 100]
      )
    ).rejects.toThrow(/foreign key constraint.*orders_user_id_fkey/);
  });

  it('should cascade delete order items', async () => {
    // Setup
    const { rows: [user] } = await pool.query(
      'INSERT INTO users (email) VALUES ($1) RETURNING id',
      ['test@example.com']
    );
    const { rows: [order] } = await pool.query(
      'INSERT INTO orders (user_id, total) VALUES ($1, $2) RETURNING id',
      [user.id, 100]
    );
    await pool.query(
      'INSERT INTO order_items (order_id, product_id, quantity) VALUES ($1, $2, $3)',
      [order.id, 'prod_1', 2]
    );

    // Delete order
    await pool.query('DELETE FROM orders WHERE id = $1', [order.id]);

    // Verify cascade
    const { rows: items } = await pool.query(
      'SELECT * FROM order_items WHERE order_id = $1',
      [order.id]
    );
    expect(items).toHaveLength(0);
  });
});
```

---

## API Integration Testing

### HTTP Contract Testing

```javascript
const request = require('supertest');

describe('Users API Contract', () => {
  describe('GET /api/users/:id', () => {
    it('should return user with correct schema', async () => {
      // Setup: create user
      const createResponse = await request(app)
        .post('/api/users')
        .send({ email: 'test@example.com', name: 'Test' });

      const userId = createResponse.body.id;

      // Test: get user
      const response = await request(app)
        .get(`/api/users/${userId}`)
        .expect('Content-Type', /json/)
        .expect(200);

      // Verify schema
      expect(response.body).toEqual({
        id: expect.any(String),
        email: 'test@example.com',
        name: 'Test',
        createdAt: expect.stringMatching(/^\d{4}-\d{2}-\d{2}T/),
        updatedAt: expect.stringMatching(/^\d{4}-\d{2}-\d{2}T/)
      });
    });

    it('should return 404 for non-existent user', async () => {
      const response = await request(app)
        .get('/api/users/non-existent-id')
        .expect(404);

      expect(response.body).toEqual({
        error: {
          code: 'NOT_FOUND',
          message: expect.any(String)
        }
      });
    });
  });

  describe('POST /api/users', () => {
    it('should validate required fields', async () => {
      const response = await request(app)
        .post('/api/users')
        .send({})
        .expect(400);

      expect(response.body.error.code).toBe('VALIDATION_ERROR');
      expect(response.body.error.details).toEqual(
        expect.arrayContaining([
          expect.objectContaining({ field: 'email' }),
          expect.objectContaining({ field: 'name' })
        ])
      );
    });
  });
});
```

### Authentication Testing

```javascript
describe('Authentication', () => {
  let authToken;

  beforeAll(async () => {
    // Create test user
    await request(app)
      .post('/api/users')
      .send({
        email: 'auth-test@example.com',
        name: 'Auth Test',
        password: 'testpassword123'
      });

    // Get auth token
    const loginResponse = await request(app)
      .post('/api/auth/login')
      .send({
        email: 'auth-test@example.com',
        password: 'testpassword123'
      });

    authToken = loginResponse.body.token;
  });

  it('should reject requests without token', async () => {
    await request(app)
      .get('/api/users/me')
      .expect(401);
  });

  it('should reject requests with invalid token', async () => {
    await request(app)
      .get('/api/users/me')
      .set('Authorization', 'Bearer invalid-token')
      .expect(401);
  });

  it('should accept requests with valid token', async () => {
    const response = await request(app)
      .get('/api/users/me')
      .set('Authorization', `Bearer ${authToken}`)
      .expect(200);

    expect(response.body.email).toBe('auth-test@example.com');
  });

  it('should reject expired tokens', async () => {
    // Use a pre-generated expired token
    const expiredToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...';

    await request(app)
      .get('/api/users/me')
      .set('Authorization', `Bearer ${expiredToken}`)
      .expect(401);
  });
});
```

### Rate Limiting Testing

```javascript
describe('Rate Limiting', () => {
  it('should allow requests within limit', async () => {
    // Make requests up to limit
    for (let i = 0; i < 10; i++) {
      await request(app)
        .get('/api/public/health')
        .expect(200);
    }
  });

  it('should reject requests exceeding limit', async () => {
    // Exceed rate limit
    const requests = Array(15).fill(null).map(() =>
      request(app).get('/api/public/health')
    );

    const responses = await Promise.all(requests);
    const tooManyRequests = responses.filter(r => r.status === 429);

    expect(tooManyRequests.length).toBeGreaterThan(0);
  });

  it('should include rate limit headers', async () => {
    const response = await request(app)
      .get('/api/public/health')
      .expect(200);

    expect(response.headers).toHaveProperty('x-ratelimit-limit');
    expect(response.headers).toHaveProperty('x-ratelimit-remaining');
    expect(response.headers).toHaveProperty('x-ratelimit-reset');
  });
});
```

---

## External Service Testing

### Mock Server Approach

**Using MSW (Mock Service Worker):**
```javascript
const { setupServer } = require('msw/node');
const { rest } = require('msw');

const server = setupServer(
  // Mock Stripe API
  rest.post('https://api.stripe.com/v1/charges', (req, res, ctx) => {
    return res(
      ctx.json({
        id: 'ch_test_123',
        amount: 2000,
        currency: 'usd',
        status: 'succeeded'
      })
    );
  }),

  // Mock SendGrid API
  rest.post('https://api.sendgrid.com/v3/mail/send', (req, res, ctx) => {
    return res(ctx.status(202));
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('PaymentService', () => {
  it('should process payment through Stripe', async () => {
    const result = await paymentService.charge({
      amount: 2000,
      currency: 'usd',
      source: 'tok_visa'
    });

    expect(result).toEqual({
      id: 'ch_test_123',
      status: 'succeeded'
    });
  });

  it('should handle Stripe errors', async () => {
    server.use(
      rest.post('https://api.stripe.com/v1/charges', (req, res, ctx) => {
        return res(
          ctx.status(402),
          ctx.json({
            error: {
              type: 'card_error',
              code: 'card_declined',
              message: 'Your card was declined.'
            }
          })
        );
      })
    );

    await expect(
      paymentService.charge({ amount: 2000, source: 'tok_declined' })
    ).rejects.toThrow('Card was declined');
  });
});
```

### Contract Testing with Pact

```javascript
const { Pact } = require('@pact-foundation/pact');

describe('PaymentService Pact', () => {
  const provider = new Pact({
    consumer: 'OrderService',
    provider: 'PaymentService',
    port: 1234
  });

  beforeAll(() => provider.setup());
  afterAll(() => provider.finalize());
  afterEach(() => provider.verify());

  it('should create a charge', async () => {
    // Define expected interaction
    await provider.addInteraction({
      state: 'a valid card token exists',
      uponReceiving: 'a request to create a charge',
      withRequest: {
        method: 'POST',
        path: '/charges',
        headers: { 'Content-Type': 'application/json' },
        body: {
          amount: 2000,
          currency: 'usd',
          source: 'tok_visa'
        }
      },
      willRespondWith: {
        status: 201,
        headers: { 'Content-Type': 'application/json' },
        body: {
          id: like('ch_123'),
          amount: 2000,
          currency: 'usd',
          status: 'succeeded'
        }
      }
    });

    // Make actual request to mock provider
    const client = new PaymentClient(`http://localhost:1234`);
    const result = await client.createCharge({
      amount: 2000,
      currency: 'usd',
      source: 'tok_visa'
    });

    expect(result.status).toBe('succeeded');
  });
});
```

---

## Message Queue Testing

### Testing Event Publishing

```javascript
describe('OrderService Events', () => {
  let mockEventBus;

  beforeEach(() => {
    mockEventBus = {
      publish: jest.fn().mockResolvedValue(undefined)
    };
    orderService = new OrderService(orderRepo, mockEventBus);
  });

  it('should publish OrderCreated event', async () => {
    const order = await orderService.createOrder({
      userId: 'user_123',
      items: [{ productId: 'prod_1', quantity: 2 }]
    });

    expect(mockEventBus.publish).toHaveBeenCalledWith('OrderCreated', {
      orderId: order.id,
      userId: 'user_123',
      total: expect.any(Number),
      timestamp: expect.any(Date)
    });
  });

  it('should not publish event if order creation fails', async () => {
    orderRepo.save.mockRejectedValue(new Error('DB error'));

    await expect(
      orderService.createOrder({ userId: 'user_123', items: [] })
    ).rejects.toThrow();

    expect(mockEventBus.publish).not.toHaveBeenCalled();
  });
});
```

### Testing Event Consumption

```javascript
describe('InventoryEventHandler', () => {
  let handler;
  let inventoryRepo;

  beforeEach(() => {
    inventoryRepo = {
      decrementStock: jest.fn().mockResolvedValue(undefined)
    };
    handler = new InventoryEventHandler(inventoryRepo);
  });

  it('should decrement stock on OrderPaid event', async () => {
    const event = {
      type: 'OrderPaid',
      data: {
        orderId: 'order_123',
        items: [
          { productId: 'prod_1', quantity: 2 },
          { productId: 'prod_2', quantity: 1 }
        ]
      }
    };

    await handler.handle(event);

    expect(inventoryRepo.decrementStock).toHaveBeenCalledWith('prod_1', 2);
    expect(inventoryRepo.decrementStock).toHaveBeenCalledWith('prod_2', 1);
  });

  it('should handle idempotency', async () => {
    const event = {
      type: 'OrderPaid',
      data: { orderId: 'order_123', items: [{ productId: 'prod_1', quantity: 1 }] },
      metadata: { eventId: 'evt_123' }
    };

    // First processing
    await handler.handle(event);

    // Second processing (retry/duplicate)
    await handler.handle(event);

    // Should only process once
    expect(inventoryRepo.decrementStock).toHaveBeenCalledTimes(1);
  });
});
```

---

## Test Data Management

### Factory Pattern

```javascript
// factories/userFactory.js
const { faker } = require('@faker-js/faker');

const userFactory = {
  build: (overrides = {}) => ({
    id: faker.string.uuid(),
    email: faker.internet.email(),
    name: faker.person.fullName(),
    createdAt: faker.date.past(),
    ...overrides
  }),

  create: async (overrides = {}) => {
    const user = userFactory.build(overrides);
    return await userRepository.save(user);
  },

  createMany: async (count, overrides = {}) => {
    return Promise.all(
      Array(count).fill(null).map(() => userFactory.create(overrides))
    );
  }
};

// Usage
const user = await userFactory.create({ email: 'specific@example.com' });
const users = await userFactory.createMany(10, { role: 'admin' });
```

### Fixtures

```javascript
// fixtures/orders.js
module.exports = {
  pendingOrder: {
    id: 'order_pending_1',
    userId: 'user_1',
    status: 'pending',
    total: 99.99,
    items: [
      { productId: 'prod_1', quantity: 2, price: 49.99 }
    ]
  },

  paidOrder: {
    id: 'order_paid_1',
    userId: 'user_1',
    status: 'paid',
    total: 199.99,
    paymentId: 'pay_123',
    paidAt: new Date('2024-01-15')
  },

  shippedOrder: {
    id: 'order_shipped_1',
    userId: 'user_1',
    status: 'shipped',
    trackingNumber: '1Z999AA10123456784'
  }
};

// Usage
const { pendingOrder, paidOrder } = require('./fixtures/orders');
await orderRepository.save(pendingOrder);
```

---

## Integration Test Checklist

Before completing integration tests:

- [ ] All API endpoints have contract tests
- [ ] Database constraints are tested
- [ ] External services are mocked
- [ ] Error scenarios are covered
- [ ] Authentication/authorization tested
- [ ] Rate limiting verified
- [ ] Test data properly isolated
- [ ] Tests run in under 30 seconds total
