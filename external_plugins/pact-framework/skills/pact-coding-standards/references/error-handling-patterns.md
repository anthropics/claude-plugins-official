# Error Handling Patterns

Comprehensive guide to error handling patterns across different languages,
frameworks, and application layers.

---

## Error Handling Philosophy

### Fail Fast, Recover Gracefully

1. **Validate early** - Check inputs at system boundaries
2. **Fail immediately** - Don't propagate invalid state
3. **Provide context** - Include enough information to debug
4. **Recover gracefully** - Give users actionable feedback

---

## JavaScript/TypeScript Patterns

### Custom Error Hierarchy

```typescript
// Base application error
export class AppError extends Error {
  public readonly code: string;
  public readonly statusCode: number;
  public readonly isOperational: boolean;

  constructor(
    message: string,
    code: string,
    statusCode: number = 500,
    isOperational: boolean = true
  ) {
    super(message);
    this.name = this.constructor.name;
    this.code = code;
    this.statusCode = statusCode;
    this.isOperational = isOperational;
    Error.captureStackTrace(this, this.constructor);
  }
}

// Client errors (4xx)
export class ValidationError extends AppError {
  public readonly details: ValidationDetail[];

  constructor(message: string, details: ValidationDetail[] = []) {
    super(message, 'VALIDATION_ERROR', 400);
    this.details = details;
  }
}

export class NotFoundError extends AppError {
  public readonly resource: string;
  public readonly resourceId: string;

  constructor(resource: string, id: string) {
    super(`${resource} not found: ${id}`, 'NOT_FOUND', 404);
    this.resource = resource;
    this.resourceId = id;
  }
}

export class UnauthorizedError extends AppError {
  constructor(message: string = 'Authentication required') {
    super(message, 'UNAUTHORIZED', 401);
  }
}

export class ForbiddenError extends AppError {
  constructor(message: string = 'Access denied') {
    super(message, 'FORBIDDEN', 403);
  }
}

export class ConflictError extends AppError {
  constructor(message: string) {
    super(message, 'CONFLICT', 409);
  }
}

// Server errors (5xx)
export class InternalError extends AppError {
  constructor(message: string = 'Internal server error') {
    super(message, 'INTERNAL_ERROR', 500, false);
  }
}

export class ServiceUnavailableError extends AppError {
  constructor(service: string) {
    super(`Service unavailable: ${service}`, 'SERVICE_UNAVAILABLE', 503);
  }
}
```

### Global Error Handler (Express)

```typescript
import { Request, Response, NextFunction } from 'express';
import { AppError } from './errors';
import { logger } from './logger';

export function globalErrorHandler(
  error: Error,
  req: Request,
  res: Response,
  next: NextFunction
) {
  // Generate request ID for tracking
  const requestId = req.headers['x-request-id'] || generateRequestId();

  // Log the error
  if (error instanceof AppError) {
    if (error.isOperational) {
      logger.warn('Operational error', {
        requestId,
        error: error.message,
        code: error.code,
        stack: error.stack
      });
    } else {
      logger.error('Non-operational error', {
        requestId,
        error: error.message,
        stack: error.stack
      });
    }
  } else {
    // Unexpected error
    logger.error('Unexpected error', {
      requestId,
      error: error.message,
      stack: error.stack,
      path: req.path,
      method: req.method
    });
  }

  // Determine response
  if (error instanceof AppError) {
    return res.status(error.statusCode).json({
      error: {
        code: error.code,
        message: error.message,
        ...(error instanceof ValidationError && { details: error.details }),
        requestId
      }
    });
  }

  // Unknown error - don't leak details in production
  const message = process.env.NODE_ENV === 'production'
    ? 'An unexpected error occurred'
    : error.message;

  return res.status(500).json({
    error: {
      code: 'INTERNAL_ERROR',
      message,
      requestId
    }
  });
}

// Async error wrapper
export function asyncHandler(fn: Function) {
  return (req: Request, res: Response, next: NextFunction) => {
    Promise.resolve(fn(req, res, next)).catch(next);
  };
}

// Usage
app.get('/users/:id', asyncHandler(async (req, res) => {
  const user = await userService.getById(req.params.id);
  if (!user) {
    throw new NotFoundError('User', req.params.id);
  }
  res.json(user);
}));
```

### Error Handling in Async Operations

```typescript
// Using Result type pattern
type Result<T, E = Error> =
  | { success: true; data: T }
  | { success: false; error: E };

async function fetchUser(id: string): Promise<Result<User>> {
  try {
    const user = await userRepository.findById(id);
    if (!user) {
      return {
        success: false,
        error: new NotFoundError('User', id)
      };
    }
    return { success: true, data: user };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error : new Error(String(error))
    };
  }
}

// Usage
const result = await fetchUser(userId);
if (!result.success) {
  // Handle error
  logger.error('Failed to fetch user', { error: result.error });
  return;
}
// Use result.data safely
console.log(result.data.name);
```

---

## Python Patterns

### Custom Exception Hierarchy

```python
class AppError(Exception):
    """Base application error"""
    def __init__(self, message: str, code: str, status_code: int = 500):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code

    def to_dict(self):
        return {
            'error': {
                'code': self.code,
                'message': self.message
            }
        }


class ValidationError(AppError):
    def __init__(self, message: str, details: list = None):
        super().__init__(message, 'VALIDATION_ERROR', 400)
        self.details = details or []

    def to_dict(self):
        result = super().to_dict()
        if self.details:
            result['error']['details'] = self.details
        return result


class NotFoundError(AppError):
    def __init__(self, resource: str, resource_id: str):
        super().__init__(
            f'{resource} not found: {resource_id}',
            'NOT_FOUND',
            404
        )
        self.resource = resource
        self.resource_id = resource_id


class UnauthorizedError(AppError):
    def __init__(self, message: str = 'Authentication required'):
        super().__init__(message, 'UNAUTHORIZED', 401)
```

### Flask Error Handler

```python
from flask import Flask, jsonify
import logging

app = Flask(__name__)
logger = logging.getLogger(__name__)


@app.errorhandler(AppError)
def handle_app_error(error):
    logger.warning(f'Application error: {error.message}', extra={
        'code': error.code,
        'status_code': error.status_code
    })
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@app.errorhandler(Exception)
def handle_unexpected_error(error):
    logger.exception('Unexpected error occurred')
    response = jsonify({
        'error': {
            'code': 'INTERNAL_ERROR',
            'message': 'An unexpected error occurred'
        }
    })
    response.status_code = 500
    return response
```

### Context Manager for Error Handling

```python
from contextlib import contextmanager

@contextmanager
def error_boundary(operation_name: str, reraise: bool = True):
    """Context manager for consistent error handling"""
    try:
        yield
    except AppError:
        # Re-raise application errors as-is
        raise
    except Exception as e:
        logger.exception(f'Error during {operation_name}')
        if reraise:
            raise InternalError(f'Failed to {operation_name}') from e


# Usage
with error_boundary('fetch user data'):
    user = await user_repository.find_by_id(user_id)
    if not user:
        raise NotFoundError('User', user_id)
```

---

## Retry Strategies

### Exponential Backoff

```typescript
interface RetryOptions {
  maxAttempts: number;
  baseDelayMs: number;
  maxDelayMs: number;
  retryableErrors?: string[];
}

async function withRetry<T>(
  operation: () => Promise<T>,
  options: RetryOptions
): Promise<T> {
  const {
    maxAttempts,
    baseDelayMs,
    maxDelayMs,
    retryableErrors = []
  } = options;

  let lastError: Error;

  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      return await operation();
    } catch (error) {
      lastError = error as Error;

      // Check if error is retryable
      if (retryableErrors.length > 0) {
        const isRetryable = retryableErrors.some(code =>
          error instanceof AppError && error.code === code
        );
        if (!isRetryable) {
          throw error;
        }
      }

      // Don't retry on last attempt
      if (attempt === maxAttempts) {
        break;
      }

      // Calculate delay with jitter
      const delay = Math.min(
        baseDelayMs * Math.pow(2, attempt - 1) + Math.random() * 100,
        maxDelayMs
      );

      logger.warn(`Retry attempt ${attempt}/${maxAttempts}`, {
        error: lastError.message,
        nextRetryIn: delay
      });

      await sleep(delay);
    }
  }

  throw lastError;
}

// Usage
const result = await withRetry(
  () => externalApi.fetchData(id),
  {
    maxAttempts: 3,
    baseDelayMs: 1000,
    maxDelayMs: 10000,
    retryableErrors: ['RATE_LIMITED', 'SERVICE_UNAVAILABLE']
  }
);
```

### Circuit Breaker Pattern

```typescript
enum CircuitState {
  CLOSED = 'CLOSED',     // Normal operation
  OPEN = 'OPEN',         // Failing, reject requests
  HALF_OPEN = 'HALF_OPEN' // Testing recovery
}

class CircuitBreaker {
  private state: CircuitState = CircuitState.CLOSED;
  private failures: number = 0;
  private lastFailureTime: number = 0;
  private successCount: number = 0;

  constructor(
    private readonly options: {
      failureThreshold: number;
      resetTimeoutMs: number;
      halfOpenSuccessThreshold: number;
    }
  ) {}

  async execute<T>(operation: () => Promise<T>): Promise<T> {
    if (this.state === CircuitState.OPEN) {
      if (Date.now() - this.lastFailureTime > this.options.resetTimeoutMs) {
        this.state = CircuitState.HALF_OPEN;
        this.successCount = 0;
      } else {
        throw new ServiceUnavailableError('Circuit breaker is open');
      }
    }

    try {
      const result = await operation();
      this.onSuccess();
      return result;
    } catch (error) {
      this.onFailure();
      throw error;
    }
  }

  private onSuccess(): void {
    if (this.state === CircuitState.HALF_OPEN) {
      this.successCount++;
      if (this.successCount >= this.options.halfOpenSuccessThreshold) {
        this.state = CircuitState.CLOSED;
        this.failures = 0;
      }
    } else {
      this.failures = 0;
    }
  }

  private onFailure(): void {
    this.failures++;
    this.lastFailureTime = Date.now();

    if (this.failures >= this.options.failureThreshold) {
      this.state = CircuitState.OPEN;
    }
  }
}

// Usage
const paymentCircuit = new CircuitBreaker({
  failureThreshold: 5,
  resetTimeoutMs: 30000,
  halfOpenSuccessThreshold: 3
});

try {
  const result = await paymentCircuit.execute(() =>
    paymentGateway.processPayment(payment)
  );
} catch (error) {
  if (error instanceof ServiceUnavailableError) {
    // Handle circuit open - maybe use fallback
  }
}
```

---

## Error Logging Best Practices

### Structured Error Logging

```typescript
interface ErrorLogContext {
  requestId?: string;
  userId?: string;
  operation?: string;
  input?: unknown;
  duration?: number;
}

function logError(error: Error, context: ErrorLogContext = {}): void {
  const logEntry = {
    timestamp: new Date().toISOString(),
    level: 'error',
    message: error.message,
    errorName: error.name,
    stack: error.stack,
    ...context
  };

  // Add AppError specific fields
  if (error instanceof AppError) {
    Object.assign(logEntry, {
      errorCode: error.code,
      statusCode: error.statusCode,
      isOperational: error.isOperational
    });
  }

  // Remove sensitive data
  if (logEntry.input) {
    logEntry.input = sanitizeForLogging(logEntry.input);
  }

  console.error(JSON.stringify(logEntry));
}

function sanitizeForLogging(data: unknown): unknown {
  if (typeof data !== 'object' || data === null) {
    return data;
  }

  const sensitiveKeys = ['password', 'token', 'secret', 'apiKey', 'creditCard'];
  const sanitized = { ...data };

  for (const key of Object.keys(sanitized)) {
    if (sensitiveKeys.some(sk => key.toLowerCase().includes(sk))) {
      sanitized[key] = '[REDACTED]';
    }
  }

  return sanitized;
}
```

---

## Error Response Standards

### REST API Error Format

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": [
      {
        "field": "email",
        "message": "Invalid email format",
        "code": "INVALID_FORMAT"
      },
      {
        "field": "age",
        "message": "Must be at least 18",
        "code": "MIN_VALUE"
      }
    ],
    "requestId": "req_abc123def456"
  }
}
```

### HTTP Status Code Guidelines

| Status | Code | When to Use |
|--------|------|-------------|
| 400 | Bad Request | Invalid input, validation errors |
| 401 | Unauthorized | Missing or invalid authentication |
| 403 | Forbidden | Authenticated but not authorized |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Duplicate resource, state conflict |
| 422 | Unprocessable | Valid syntax but semantic error |
| 429 | Too Many Requests | Rate limited |
| 500 | Internal Error | Server error (hide details in prod) |
| 502 | Bad Gateway | Upstream service error |
| 503 | Service Unavailable | Temporary overload or maintenance |

---

## Error Handling Checklist

Before completing implementation:

- [ ] All async operations have try/catch
- [ ] Custom error classes for domain errors
- [ ] Global error handler catches unhandled errors
- [ ] Errors include sufficient context for debugging
- [ ] Sensitive data is not exposed in errors
- [ ] User-facing errors are friendly and actionable
- [ ] Errors are logged with structured format
- [ ] Retry logic for transient failures
- [ ] Circuit breaker for external dependencies
- [ ] Request IDs for error tracking
