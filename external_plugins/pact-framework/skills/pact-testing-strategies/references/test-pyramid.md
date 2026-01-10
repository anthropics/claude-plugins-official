# Test Pyramid Deep Dive

Detailed guidance for each layer of the test pyramid, including when to use
each layer, anti-patterns to avoid, and practical implementation strategies.

---

## Test Pyramid Overview

```
                              Slower, More Expensive
                                       ^
                                      /|\
                                     / | \
                                    /  |  \
                                   /   |   \
                    Manual/      /    |    \
                    Exploratory /     |     \  UI / E2E Tests
                               /______|______\  (5-10%)
                              /       |       \
                             /        |        \
                            /         |         \
            Integration    /          |          \  Integration Tests
            Tests         /___________|___________\  (15-25%)
                         /            |            \
                        /             |             \
                       /              |              \
          Unit        /               |               \  Unit Tests
          Tests      /_______________|________________\  (70-80%)
                                      |
                                      v
                              Faster, Cheaper
```

---

## Unit Tests (70-80% of tests)

### What to Test at Unit Level

**Test these things:**
- Pure functions and business logic
- Data transformations
- Validation rules
- State machines
- Edge cases and boundary conditions
- Error handling

**Avoid testing:**
- Framework code (React, Express routing)
- Database queries (use integration tests)
- External API calls (use integration tests)
- Simple getters/setters

### Unit Test Patterns

**Pure Function Testing:**
```javascript
describe('calculateDiscount', () => {
  it.each([
    { total: 50, expectedDiscount: 0 },
    { total: 100, expectedDiscount: 0 },
    { total: 100.01, expectedDiscount: 10.001 },
    { total: 200, expectedDiscount: 20 },
    { total: 500, expectedDiscount: 75 },  // Max 15%
  ])('should calculate $expectedDiscount discount for $total order', ({ total, expectedDiscount }) => {
    expect(calculateDiscount(total)).toBeCloseTo(expectedDiscount, 2);
  });

  it('should throw for negative amounts', () => {
    expect(() => calculateDiscount(-10)).toThrow('Amount must be positive');
  });
});
```

**State Machine Testing:**
```javascript
describe('OrderStateMachine', () => {
  describe('transitions from PENDING', () => {
    it('should allow transition to PAID', () => {
      const order = new Order({ status: 'PENDING' });
      order.transitionTo('PAID');
      expect(order.status).toBe('PAID');
    });

    it('should allow transition to CANCELLED', () => {
      const order = new Order({ status: 'PENDING' });
      order.transitionTo('CANCELLED');
      expect(order.status).toBe('CANCELLED');
    });

    it('should NOT allow transition to SHIPPED', () => {
      const order = new Order({ status: 'PENDING' });
      expect(() => order.transitionTo('SHIPPED'))
        .toThrow('Invalid transition: PENDING -> SHIPPED');
    });
  });

  describe('transitions from PAID', () => {
    it('should allow transition to SHIPPED', () => {
      const order = new Order({ status: 'PAID' });
      order.transitionTo('SHIPPED');
      expect(order.status).toBe('SHIPPED');
    });

    it('should NOT allow transition to PENDING', () => {
      const order = new Order({ status: 'PAID' });
      expect(() => order.transitionTo('PENDING'))
        .toThrow('Invalid transition: PAID -> PENDING');
    });
  });
});
```

**Error Handling Testing:**
```javascript
describe('UserService.createUser', () => {
  it('should throw ValidationError for invalid email', async () => {
    const service = new UserService(mockRepo);

    await expect(
      service.createUser({ email: 'invalid', name: 'Test' })
    ).rejects.toThrow(ValidationError);
  });

  it('should throw ConflictError for duplicate email', async () => {
    mockRepo.findByEmail.mockResolvedValue({ id: 'existing' });
    const service = new UserService(mockRepo);

    await expect(
      service.createUser({ email: 'exists@test.com', name: 'Test' })
    ).rejects.toThrow(ConflictError);
  });

  it('should propagate unexpected errors', async () => {
    mockRepo.save.mockRejectedValue(new Error('Database connection lost'));
    const service = new UserService(mockRepo);

    await expect(
      service.createUser({ email: 'new@test.com', name: 'Test' })
    ).rejects.toThrow('Database connection lost');
  });
});
```

### Unit Test Anti-Patterns

**Testing Implementation Details:**
```javascript
// BAD: Testing internal method calls
it('should call validateEmail', async () => {
  const spy = jest.spyOn(userService, 'validateEmail');
  await userService.createUser(userData);
  expect(spy).toHaveBeenCalled();
});

// GOOD: Testing observable behavior
it('should reject invalid email format', async () => {
  await expect(
    userService.createUser({ email: 'invalid', name: 'Test' })
  ).rejects.toThrow('Invalid email format');
});
```

**Excessive Mocking:**
```javascript
// BAD: Too many mocks make test meaningless
const mockConfig = jest.mock();
const mockValidator = jest.mock();
const mockFormatter = jest.mock();
const mockTransformer = jest.mock();
// At this point, what are we really testing?

// GOOD: Mock only external dependencies
const mockRepository = { save: jest.fn() };
const service = new UserService(mockRepository);
// Test actual service logic
```

---

## Integration Tests (15-25% of tests)

### What to Test at Integration Level

**Test these things:**
- API endpoints (request/response contracts)
- Database operations (CRUD, constraints)
- External service integrations
- Message queue interactions
- Cache behavior
- Authentication/authorization

**Avoid testing:**
- Business logic (use unit tests)
- UI behavior (use E2E tests)
- Third-party library internals

### Integration Test Patterns

**API Contract Testing:**
```javascript
describe('Users API', () => {
  describe('POST /api/users', () => {
    it('should conform to API contract', async () => {
      const response = await request(app)
        .post('/api/users')
        .send(validUserData)
        .expect(201);

      // Verify response structure (contract)
      expect(response.body).toEqual({
        id: expect.any(String),
        email: validUserData.email,
        name: validUserData.name,
        createdAt: expect.stringMatching(/^\d{4}-\d{2}-\d{2}T/),
        updatedAt: expect.stringMatching(/^\d{4}-\d{2}-\d{2}T/)
      });

      // Verify sensitive data excluded
      expect(response.body).not.toHaveProperty('password');
      expect(response.body).not.toHaveProperty('passwordHash');
    });

    it('should return proper error format', async () => {
      const response = await request(app)
        .post('/api/users')
        .send({ email: 'invalid' })
        .expect(400);

      expect(response.body).toEqual({
        error: {
          code: expect.any(String),
          message: expect.any(String),
          details: expect.any(Array)
        }
      });
    });
  });
});
```

**Database Integration Testing:**
```javascript
describe('OrderRepository', () => {
  let db;
  let orderRepo;

  beforeAll(async () => {
    db = await TestDatabase.create();
    await db.migrate();
    orderRepo = new OrderRepository(db);
  });

  afterEach(async () => {
    await db.truncate(['orders', 'order_items']);
  });

  afterAll(async () => {
    await db.destroy();
  });

  describe('transactional operations', () => {
    it('should rollback on partial failure', async () => {
      // Create user for foreign key
      const userId = await db.users.insert({ email: 'test@test.com' });

      // Attempt to create order with invalid item
      await expect(
        orderRepo.createWithItems(userId, [
          { productId: 'valid', quantity: 1 },
          { productId: 'invalid-fk', quantity: 1 }  // FK violation
        ])
      ).rejects.toThrow();

      // Verify no order was created (transaction rolled back)
      const orders = await db.orders.where({ userId });
      expect(orders).toHaveLength(0);
    });
  });
});
```

### Integration Test Environment

**Docker Compose for Test Dependencies:**
```yaml
# docker-compose.test.yml
version: '3.8'
services:
  test-db:
    image: postgres:15
    environment:
      POSTGRES_DB: test_db
      POSTGRES_USER: test
      POSTGRES_PASSWORD: test
    ports:
      - "5433:5432"
    tmpfs:
      - /var/lib/postgresql/data  # In-memory for speed

  test-redis:
    image: redis:7
    ports:
      - "6380:6379"
```

**Test Setup Script:**
```javascript
// tests/setup.js
const { Pool } = require('pg');
const { createClient } = require('redis');

let db, redis;

beforeAll(async () => {
  db = new Pool({ connectionString: process.env.TEST_DATABASE_URL });
  redis = createClient({ url: process.env.TEST_REDIS_URL });
  await redis.connect();

  // Run migrations
  await runMigrations(db);
});

afterAll(async () => {
  await db.end();
  await redis.quit();
});

// Make available to tests
global.testDb = db;
global.testRedis = redis;
```

---

## E2E Tests (5-10% of tests)

### What to Test at E2E Level

**Test these things:**
- Critical user journeys (happy paths)
- Multi-step workflows
- Cross-service integrations
- Real browser behavior
- Mobile-specific flows

**Avoid testing:**
- Every edge case (use unit tests)
- API contracts (use integration tests)
- Performance under load (use load tests)

### E2E Test Patterns

**Page Object Model:**
```javascript
// pages/LoginPage.js
class LoginPage {
  constructor(page) {
    this.page = page;
    this.emailInput = page.locator('[data-testid="email-input"]');
    this.passwordInput = page.locator('[data-testid="password-input"]');
    this.submitButton = page.locator('[data-testid="login-button"]');
    this.errorMessage = page.locator('[data-testid="error-message"]');
  }

  async goto() {
    await this.page.goto('/login');
  }

  async login(email, password) {
    await this.emailInput.fill(email);
    await this.passwordInput.fill(password);
    await this.submitButton.click();
  }

  async expectError(message) {
    await expect(this.errorMessage).toContainText(message);
  }
}

// tests/login.spec.js
describe('Login', () => {
  let loginPage;

  beforeEach(async () => {
    loginPage = new LoginPage(page);
    await loginPage.goto();
  });

  it('should login successfully with valid credentials', async () => {
    await loginPage.login('test@example.com', 'validpassword');
    await expect(page).toHaveURL('/dashboard');
  });

  it('should show error for invalid credentials', async () => {
    await loginPage.login('test@example.com', 'wrongpassword');
    await loginPage.expectError('Invalid email or password');
  });
});
```

**Visual Regression Testing:**
```javascript
it('should match login page snapshot', async () => {
  await page.goto('/login');
  await expect(page).toHaveScreenshot('login-page.png', {
    maxDiffPixels: 100
  });
});
```

### E2E Test Anti-Patterns

**Flaky Tests:**
```javascript
// BAD: Race condition, will be flaky
await page.click('[data-testid="submit"]');
expect(await page.locator('.success').isVisible()).toBe(true);

// GOOD: Wait for expected state
await page.click('[data-testid="submit"]');
await expect(page.locator('.success')).toBeVisible({ timeout: 5000 });
```

**Tight Coupling to Implementation:**
```javascript
// BAD: Coupled to CSS class names
await page.click('.btn-primary.submit-button.large');

// GOOD: Use data-testid for stability
await page.click('[data-testid="submit-order"]');
```

---

## Test Selection Guide

| Scenario | Test Layer | Reason |
|----------|------------|--------|
| Pure function logic | Unit | Fast, isolated |
| Validation rules | Unit | Many cases to cover |
| API request/response | Integration | Verifies contract |
| Database constraints | Integration | Needs real DB |
| User signup flow | E2E | Multi-step journey |
| Error message display | Unit | Component isolation |
| Auth token handling | Integration | Needs real auth |
| Mobile responsiveness | E2E | Needs real browser |

---

## Common Mistakes

### Inverted Pyramid

```
// WRONG: Too many E2E, too few unit tests
E2E Tests: 200        <- Too many! Slow, flaky
Integration: 100
Unit Tests: 50        <- Too few!

// CORRECT: Follow the pyramid
E2E Tests: 20
Integration: 100
Unit Tests: 500
```

**Symptoms of Inverted Pyramid:**
- Test suite takes 30+ minutes
- Frequent flaky test failures
- Hard to identify what broke
- Developers avoid running tests

### Ice Cream Cone (Manual Testing Heavy)

```
// WRONG: Mostly manual testing
Manual Testing: 80%
E2E: 15%
Integration: 4%
Unit: 1%
```

**Fix by:**
- Automating repetitive checks
- Writing unit tests for bug fixes
- Adding integration tests for APIs
- Using E2E only for critical paths
