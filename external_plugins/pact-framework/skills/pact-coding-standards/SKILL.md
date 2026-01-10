---
name: pact-coding-standards
description: |
  Clean code principles, error handling patterns, and coding standards for PACT Code phase.
  Use when: implementing features, refactoring code, reviewing code quality,
  establishing coding conventions, or handling errors and exceptions.
  Triggers on: code quality, clean code, refactoring, error handling,
  logging patterns, naming conventions, code review, code phase.
---

# PACT Coding Standards

Clean code principles for the Code phase of PACT. This skill provides
essential coding guidelines and links to detailed patterns for implementation.

## Core Principles

### 1. Single Responsibility Principle

Each function, class, or module should have exactly one reason to change.

```javascript
// BAD: Multiple responsibilities
class UserManager {
  createUser(data) { }
  validateEmail(email) { }
  sendWelcomeEmail(user) { }
  generateReport() { }
  updateUserPreferences(userId, prefs) { }
}

// GOOD: Single responsibility each
class UserService {
  createUser(data) { }
  updateUser(userId, data) { }
}

class EmailValidator {
  validate(email) { }
}

class NotificationService {
  sendWelcomeEmail(user) { }
}

class UserReportGenerator {
  generate(criteria) { }
}
```

### 2. DRY (Don't Repeat Yourself)

Extract duplicated logic into reusable functions.

```javascript
// BAD: Duplicated validation logic
function createUser(data) {
  if (!data.email || !data.email.includes('@')) {
    throw new Error('Invalid email');
  }
  // ...
}

function updateUser(id, data) {
  if (data.email && !data.email.includes('@')) {
    throw new Error('Invalid email');
  }
  // ...
}

// GOOD: Extracted validation
function validateEmail(email) {
  if (!email || !email.includes('@')) {
    throw new ValidationError('Invalid email format');
  }
}

function createUser(data) {
  validateEmail(data.email);
  // ...
}

function updateUser(id, data) {
  if (data.email) {
    validateEmail(data.email);
  }
  // ...
}
```

### 3. KISS (Keep It Simple, Stupid)

Choose the simplest solution that works.

```javascript
// BAD: Over-engineered
class ConfigurationFactoryBuilderManager {
  static getInstance() {
    return new ConfigurationFactoryBuilder()
      .withDefaults()
      .withEnvironment()
      .build()
      .getConfiguration();
  }
}

// GOOD: Simple and direct
const config = {
  port: process.env.PORT || 3000,
  dbUrl: process.env.DATABASE_URL,
  debug: process.env.NODE_ENV !== 'production'
};
```

### 4. Defensive Programming

Validate inputs, handle edge cases, and fail gracefully.

```javascript
function processOrder(order) {
  // Guard clauses
  if (!order) {
    throw new ValidationError('Order is required');
  }

  if (!order.items || order.items.length === 0) {
    throw new ValidationError('Order must have at least one item');
  }

  if (order.total < 0) {
    throw new ValidationError('Order total cannot be negative');
  }

  // Safe property access
  const customerEmail = order.customer?.email ?? 'no-email@placeholder.com';

  // Proceed with valid data
  return {
    id: generateOrderId(),
    items: order.items.map(item => ({
      ...item,
      price: Math.max(0, item.price)  // Ensure non-negative
    })),
    total: order.total,
    customerEmail
  };
}
```

---

## Naming Conventions

### Functions

```javascript
// Use verb + noun pattern
function getUser(id) { }           // Retrieval
function createOrder(data) { }     // Creation
function updateProfile(id, data) { } // Mutation
function deleteComment(id) { }     // Deletion
function validateEmail(email) { }  // Validation
function calculateTotal(items) { } // Calculation
function formatDate(date) { }      // Transformation
function isActive(user) { }        // Boolean check
function hasPermission(user, action) { } // Boolean check
function canEdit(user, resource) { }     // Boolean check
```

### Variables

```javascript
// Descriptive nouns
const userCount = 42;               // Not: n, count, uc
const activeUsers = users.filter(); // Not: arr, filtered
const maxRetryAttempts = 3;         // Not: max, retries

// Boolean variables
const isActive = true;              // is/has/can/should prefix
const hasPermission = false;
const canEdit = user.role === 'admin';
const shouldRetry = attempts < maxRetryAttempts;

// Collections are plural
const users = [];                   // Not: userList, userArray
const orderItems = [];              // Not: items (too generic)

// Maps/objects describe content
const userById = {};                // Not: userMap
const priceByProductId = {};        // Describes key-value relationship
```

### Constants

```javascript
// SCREAMING_SNAKE_CASE for true constants
const MAX_RETRY_ATTEMPTS = 3;
const DEFAULT_PAGE_SIZE = 20;
const API_BASE_URL = 'https://api.example.com';

// Configuration objects
const CONFIG = Object.freeze({
  database: {
    host: process.env.DB_HOST,
    port: parseInt(process.env.DB_PORT, 10)
  }
});
```

### Classes

```javascript
// PascalCase, noun-based
class UserRepository { }     // Not: UsersRepo, UserRepo
class OrderService { }       // Not: OrdersService
class EmailValidator { }     // Not: ValidateEmail
class PaymentGateway { }     // Not: PaymentGatewayService

// Interface names (TypeScript)
interface Cacheable { }      // Adjective for capabilities
interface UserRepository { } // Noun for contracts
```

---

## Error Handling

### Fail Fast, Recover Gracefully

```javascript
async function createUser(data) {
  // Validate early
  if (!data.email) {
    throw new ValidationError('Email is required');
  }

  if (!isValidEmail(data.email)) {
    throw new ValidationError('Invalid email format');
  }

  // Check business rules
  const existing = await userRepo.findByEmail(data.email);
  if (existing) {
    throw new ConflictError('Email already registered');
  }

  // Proceed with operation
  try {
    const user = await userRepo.save(data);
    await emailService.sendWelcome(user.email);
    return user;
  } catch (error) {
    // Handle specific errors
    if (error instanceof DatabaseError) {
      logger.error('Database error creating user', { error, data });
      throw new ServiceError('Unable to create user, please try again');
    }
    throw error; // Re-throw unexpected errors
  }
}
```

### Custom Error Classes

```javascript
// Base application error
class AppError extends Error {
  constructor(message, code, statusCode = 500) {
    super(message);
    this.name = this.constructor.name;
    this.code = code;
    this.statusCode = statusCode;
    Error.captureStackTrace(this, this.constructor);
  }
}

// Specific error types
class ValidationError extends AppError {
  constructor(message, details = []) {
    super(message, 'VALIDATION_ERROR', 400);
    this.details = details;
  }
}

class NotFoundError extends AppError {
  constructor(resource, id) {
    super(`${resource} with id ${id} not found`, 'NOT_FOUND', 404);
    this.resource = resource;
    this.resourceId = id;
  }
}

class ConflictError extends AppError {
  constructor(message) {
    super(message, 'CONFLICT', 409);
  }
}

class UnauthorizedError extends AppError {
  constructor(message = 'Authentication required') {
    super(message, 'UNAUTHORIZED', 401);
  }
}
```

For comprehensive error patterns: See [references/error-handling-patterns.md](references/error-handling-patterns.md)

---

## Logging

### Log Levels

| Level | When to Use | Example |
|-------|-------------|---------|
| **ERROR** | Failures requiring attention | Database connection failed |
| **WARN** | Potentially harmful situations | Rate limit approaching |
| **INFO** | Normal operational events | User created, order placed |
| **DEBUG** | Detailed debugging info | Function parameters, intermediate values |

### Structured Logging

```javascript
const logger = require('./logger');

// BAD: Unstructured logging
console.log('User created: ' + user.id);
console.log('Error: ' + error.message);

// GOOD: Structured logging
logger.info('User created', {
  userId: user.id,
  email: user.email,
  source: 'signup'
});

logger.error('Failed to process payment', {
  orderId: order.id,
  amount: order.total,
  error: error.message,
  errorCode: error.code,
  stack: error.stack
});

// Request logging middleware
app.use((req, res, next) => {
  const requestId = req.headers['x-request-id'] || uuidv4();
  req.requestId = requestId;

  logger.info('Request received', {
    requestId,
    method: req.method,
    path: req.path,
    userAgent: req.headers['user-agent'],
    ip: req.ip
  });

  res.on('finish', () => {
    logger.info('Request completed', {
      requestId,
      statusCode: res.statusCode,
      duration: Date.now() - req.startTime
    });
  });

  next();
});
```

---

## Code Organization

### File Size Guidelines

- **Maximum file size**: 500 lines
- **Maximum function size**: 50 lines
- **Maximum line length**: 100 characters

### Module Structure

```javascript
// 1. Imports (external first, then internal)
const express = require('express');
const { validate } = require('class-validator');

const { UserService } = require('../services/UserService');
const { logger } = require('../utils/logger');

// 2. Constants and configuration
const MAX_PAGE_SIZE = 100;
const DEFAULT_PAGE_SIZE = 20;

// 3. Main exports (class, function, or router)
class UserController {
  constructor(userService) {
    this.userService = userService;
  }

  async getUsers(req, res, next) {
    // Implementation
  }
}

// 4. Helper functions (private to module)
function validatePagination(page, limit) {
  // Implementation
}

// 5. Export statement
module.exports = { UserController };
```

---

## Code Quality Checklist

Before completing CODE phase:

### Structure
- [ ] Functions under 50 lines
- [ ] Files under 500 lines
- [ ] Single responsibility per function/class
- [ ] No deeply nested code (max 3 levels)

### Naming
- [ ] Descriptive variable names
- [ ] Consistent naming conventions
- [ ] No abbreviations (except common ones: id, url, api)
- [ ] Boolean variables have is/has/can prefix

### Error Handling
- [ ] All async operations have error handling
- [ ] Errors include relevant context
- [ ] No silent failures
- [ ] User-facing errors are friendly

### Documentation
- [ ] Complex logic has comments
- [ ] Public APIs have JSDoc/docstrings
- [ ] No commented-out code
- [ ] No TODO comments without tickets

### Quality
- [ ] No magic numbers (use named constants)
- [ ] No duplicate code
- [ ] Consistent code style
- [ ] Logging at appropriate levels

---

## Scripts

### Lint Check Script

A helper script is available at `scripts/lint-check.sh` to run project linters.

```bash
# Make executable
chmod +x ~/.claude/skills/pact-coding-standards/scripts/lint-check.sh

# Run
~/.claude/skills/pact-coding-standards/scripts/lint-check.sh
```

---

## Detailed References

For comprehensive coding guidance:

- **Clean Code Principles**: [references/clean-code-principles.md](references/clean-code-principles.md)
  - SOLID principles in depth
  - Code smells and refactoring
  - Function design guidelines
  - Comment best practices

- **Error Handling Patterns**: [references/error-handling-patterns.md](references/error-handling-patterns.md)
  - Error handling by language
  - Global error handlers
  - Retry strategies
  - Circuit breaker patterns
