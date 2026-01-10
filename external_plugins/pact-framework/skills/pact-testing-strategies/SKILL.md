---
name: pact-testing-strategies
description: |
  Testing strategies, test pyramid guidance, and quality assurance patterns for PACT Test phase.
  Use when: designing test suites, implementing unit tests, integration tests, E2E tests,
  performance testing, security testing, or determining test coverage priorities.
  Triggers on: test design, unit testing, integration testing, E2E testing,
  test coverage, test pyramid, mocking, fixtures, performance testing, test phase.
---

# PACT Testing Strategies

Testing guidance for the Test phase of PACT. This skill provides frameworks
for designing comprehensive test suites and links to detailed testing patterns.

## Test Pyramid

The test pyramid guides the distribution of test types for optimal coverage and speed.

```
                    /\
                   /  \      E2E Tests (Few)
                  /    \     - Critical user journeys
                 / E2E  \    - Slow, expensive
                /--------\
               /          \  Integration Tests (Some)
              /Integration \  - API contracts
             /--------------\  - Service interactions
            /                \
           /    Unit Tests    \ Unit Tests (Many)
          /                    \ - Fast, isolated
         /______________________\ - Business logic
```

### Coverage Targets

| Layer | Target | Focus | Speed |
|-------|--------|-------|-------|
| **Unit** | 80%+ line coverage | Business logic, edge cases | <1s per test |
| **Integration** | Key paths covered | API contracts, data flow | <10s per test |
| **E2E** | Critical flows only | User journeys, happy paths | <60s per test |

---

## Unit Testing Patterns

### Arrange-Act-Assert (AAA)

```javascript
describe('OrderService', () => {
  describe('calculateTotal', () => {
    it('should apply discount for orders over $100', () => {
      // Arrange
      const orderService = new OrderService();
      const items = [
        { price: 50, quantity: 2 },
        { price: 20, quantity: 1 }
      ];

      // Act
      const total = orderService.calculateTotal(items);

      // Assert
      expect(total).toBe(108); // $120 - 10% discount
    });
  });
});
```

### Test Behavior, Not Implementation

```javascript
// BAD: Testing implementation details
it('should call repository.save once', () => {
  await userService.createUser(userData);
  expect(userRepository.save).toHaveBeenCalledTimes(1);
});

// GOOD: Testing behavior
it('should create a user with hashed password', async () => {
  const user = await userService.createUser({
    email: 'test@example.com',
    password: 'plaintext'
  });

  expect(user.email).toBe('test@example.com');
  expect(user.password).not.toBe('plaintext');
  expect(await bcrypt.compare('plaintext', user.password)).toBe(true);
});
```

### Mocking External Dependencies

```javascript
// Mock setup
const mockEmailService = {
  send: jest.fn().mockResolvedValue({ id: 'msg_123' })
};

const mockUserRepository = {
  findByEmail: jest.fn(),
  save: jest.fn().mockImplementation(user => ({ ...user, id: 'user_123' }))
};

describe('UserService', () => {
  let userService;

  beforeEach(() => {
    jest.clearAllMocks();
    userService = new UserService(mockUserRepository, mockEmailService);
  });

  it('should send welcome email after creating user', async () => {
    mockUserRepository.findByEmail.mockResolvedValue(null);

    await userService.createUser({ email: 'new@example.com', name: 'New User' });

    expect(mockEmailService.send).toHaveBeenCalledWith({
      to: 'new@example.com',
      template: 'welcome',
      data: expect.objectContaining({ name: 'New User' })
    });
  });
});
```

### Testing Edge Cases

```javascript
describe('validateEmail', () => {
  // Happy path
  it('should accept valid email', () => {
    expect(validateEmail('user@example.com')).toBe(true);
  });

  // Edge cases
  it.each([
    ['email with subdomain', 'user@mail.example.com'],
    ['email with plus sign', 'user+tag@example.com'],
    ['email with numbers', 'user123@example.com'],
  ])('should accept %s', (_, email) => {
    expect(validateEmail(email)).toBe(true);
  });

  // Invalid cases
  it.each([
    ['empty string', ''],
    ['missing @', 'userexample.com'],
    ['missing domain', 'user@'],
    ['spaces', 'user @example.com'],
    ['double @', 'user@@example.com'],
  ])('should reject %s', (_, email) => {
    expect(validateEmail(email)).toBe(false);
  });

  // Boundary cases
  it('should handle very long emails', () => {
    const longEmail = 'a'.repeat(64) + '@' + 'b'.repeat(63) + '.com';
    expect(validateEmail(longEmail)).toBe(true);
  });

  it('should reject emails exceeding max length', () => {
    const tooLongEmail = 'a'.repeat(65) + '@' + 'b'.repeat(64) + '.com';
    expect(validateEmail(tooLongEmail)).toBe(false);
  });
});
```

---

## Integration Testing Patterns

### API Contract Testing

```javascript
describe('POST /api/users', () => {
  let app;
  let db;

  beforeAll(async () => {
    db = await setupTestDatabase();
    app = createApp(db);
  });

  afterAll(async () => {
    await db.close();
  });

  beforeEach(async () => {
    await db.clear();
  });

  it('should create a user and return 201', async () => {
    const response = await request(app)
      .post('/api/users')
      .send({
        email: 'new@example.com',
        name: 'New User',
        password: 'securepassword123'
      })
      .expect(201);

    expect(response.body).toMatchObject({
      id: expect.any(String),
      email: 'new@example.com',
      name: 'New User',
      createdAt: expect.any(String)
    });

    // Verify password not returned
    expect(response.body.password).toBeUndefined();
  });

  it('should return 400 for invalid email', async () => {
    const response = await request(app)
      .post('/api/users')
      .send({
        email: 'invalid-email',
        name: 'Test User',
        password: 'password123'
      })
      .expect(400);

    expect(response.body).toMatchObject({
      error: {
        code: 'VALIDATION_ERROR',
        message: expect.any(String)
      }
    });
  });

  it('should return 409 for duplicate email', async () => {
    // Create first user
    await request(app)
      .post('/api/users')
      .send({ email: 'exists@example.com', name: 'First', password: 'pass123' });

    // Try to create duplicate
    const response = await request(app)
      .post('/api/users')
      .send({ email: 'exists@example.com', name: 'Second', password: 'pass456' })
      .expect(409);

    expect(response.body.error.code).toBe('DUPLICATE_EMAIL');
  });
});
```

### Database Integration Testing

```javascript
describe('UserRepository', () => {
  let db;
  let userRepo;

  beforeAll(async () => {
    // Use test database (Docker or in-memory)
    db = await setupTestDatabase();
    await db.migrate();
    userRepo = new UserRepository(db);
  });

  afterAll(async () => {
    await db.close();
  });

  beforeEach(async () => {
    await db.clear();
  });

  it('should persist and retrieve user', async () => {
    const userData = {
      email: 'test@example.com',
      name: 'Test User',
      passwordHash: 'hashed'
    };

    const created = await userRepo.save(userData);
    const retrieved = await userRepo.findById(created.id);

    expect(retrieved).toMatchObject({
      id: created.id,
      email: 'test@example.com',
      name: 'Test User'
    });
  });

  it('should return null for non-existent user', async () => {
    const user = await userRepo.findById('non-existent-id');
    expect(user).toBeNull();
  });

  it('should enforce unique email constraint', async () => {
    await userRepo.save({ email: 'unique@example.com', name: 'First' });

    await expect(
      userRepo.save({ email: 'unique@example.com', name: 'Second' })
    ).rejects.toThrow('duplicate');
  });
});
```

For detailed integration patterns: See [references/integration-patterns.md](references/integration-patterns.md)

---

## E2E Testing Patterns

### Critical User Journey Testing

```javascript
// Using Playwright
describe('Checkout Flow', () => {
  let page;

  beforeAll(async () => {
    // Set up authenticated user
    await seedTestData();
  });

  beforeEach(async () => {
    page = await browser.newPage();
    await page.goto('/login');
    await loginAsTestUser(page);
  });

  afterEach(async () => {
    await page.close();
  });

  it('should complete purchase successfully', async () => {
    // Add item to cart
    await page.goto('/products/test-product');
    await page.click('[data-testid="add-to-cart"]');

    // Go to cart
    await page.click('[data-testid="cart-icon"]');
    await expect(page.locator('[data-testid="cart-item"]')).toBeVisible();

    // Proceed to checkout
    await page.click('[data-testid="checkout-button"]');

    // Fill shipping info
    await page.fill('[data-testid="address"]', '123 Test St');
    await page.fill('[data-testid="city"]', 'Test City');
    await page.fill('[data-testid="zip"]', '12345');
    await page.click('[data-testid="continue-to-payment"]');

    // Complete payment (test card)
    await page.fill('[data-testid="card-number"]', '4242424242424242');
    await page.fill('[data-testid="expiry"]', '12/28');
    await page.fill('[data-testid="cvc"]', '123');
    await page.click('[data-testid="place-order"]');

    // Verify confirmation
    await expect(page.locator('[data-testid="order-confirmation"]')).toBeVisible();
    await expect(page.locator('[data-testid="order-number"]')).toContainText(/ORD-/);
  });
});
```

---

## Test Organization

### Directory Structure

```
tests/
├── unit/                           # Fast, isolated tests
│   ├── services/
│   │   ├── UserService.test.js
│   │   └── OrderService.test.js
│   ├── utils/
│   │   └── validation.test.js
│   └── models/
│       └── Order.test.js
│
├── integration/                    # API and database tests
│   ├── api/
│   │   ├── users.test.js
│   │   └── orders.test.js
│   └── repositories/
│       └── UserRepository.test.js
│
├── e2e/                           # End-to-end tests
│   ├── checkout.spec.js
│   ├── authentication.spec.js
│   └── user-profile.spec.js
│
├── fixtures/                       # Shared test data
│   ├── users.js
│   └── orders.js
│
├── helpers/                        # Shared test utilities
│   ├── setup.js
│   ├── factories.js
│   └── matchers.js
│
└── mocks/                          # Shared mocks
    ├── emailService.js
    └── paymentGateway.js
```

### Test Naming Convention

```javascript
// Format: should [expected behavior] when [condition]
it('should return 404 when user does not exist', () => {});
it('should apply 10% discount when order total exceeds $100', () => {});
it('should send confirmation email when order is placed', () => {});
it('should throw ValidationError when email is invalid', () => {});
```

---

## Decision Log Integration

Read CODE phase decision logs at `docs/decision-logs/{feature}-{domain}.md` for:

- **Areas of uncertainty**: Where bugs often hide
- **Assumptions made**: Validate them with tests
- **Known limitations**: Test boundaries
- **Trade-offs**: Verify acceptable behavior

---

## Test Quality Checklist

Before completing TEST phase:

### Coverage
- [ ] Unit tests cover business logic (80%+ coverage)
- [ ] Integration tests verify API contracts
- [ ] E2E tests cover critical user journeys
- [ ] Edge cases and error scenarios tested

### Quality
- [ ] Tests are independent (no shared state)
- [ ] Tests have clear names describing behavior
- [ ] No flaky tests (all tests deterministic)
- [ ] Tests run quickly (unit < 1s, integration < 10s)

### Maintenance
- [ ] Tests use factories/fixtures (DRY)
- [ ] Mocks are minimal and focused
- [ ] Test data is realistic
- [ ] CI/CD pipeline runs all tests

### Security
- [ ] Authentication tests verify access control
- [ ] Input validation tests check edge cases
- [ ] Error messages don't leak sensitive info
- [ ] Rate limiting is tested

---

## Detailed References

For comprehensive testing guidance:

- **Test Pyramid**: [references/test-pyramid.md](references/test-pyramid.md)
  - Detailed guidance per test layer
  - When to use each layer
  - Anti-patterns to avoid

- **Integration Patterns**: [references/integration-patterns.md](references/integration-patterns.md)
  - Database testing strategies
  - API testing patterns
  - External service testing

- **Performance Testing**: [references/performance-testing.md](references/performance-testing.md)
  - Load testing approaches
  - Benchmark patterns
  - Performance metrics
