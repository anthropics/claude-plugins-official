---
name: pact-architecture-patterns
description: |
  Architectural design patterns, C4 diagram templates, component design guidelines,
  and anti-patterns for PACT Architect phase.
  Use when: designing system components, creating architecture diagrams,
  defining component boundaries, planning API contracts, selecting design patterns,
  or reviewing architectural decisions.
  Triggers on: architecture design, C4 diagrams, component design, system design,
  microservices, monolith, API design, interface contracts, architect phase.
---

# PACT Architecture Patterns

Design patterns and templates for the Architect phase of PACT. This skill provides
quick references for architectural decisions and links to detailed pattern implementations.

## C4 Model Quick Reference

The C4 model provides four levels of abstraction for system architecture documentation.

### Level 1: System Context

Shows your system as a box surrounded by users and other systems it interacts with.

```
                    +------------------+
                    |   External User  |
                    +--------+---------+
                             |
                             v
+------------------+    +----+----+    +------------------+
| Payment Gateway  |<-->|   Your  |<-->|   Email Service  |
+------------------+    | System  |    +------------------+
                        +---------+
                             ^
                             |
                    +--------+---------+
                    |   Admin User     |
                    +------------------+
```

**What to include:**
- Your system (single box)
- Users/personas
- External systems
- High-level interactions

### Level 2: Container

Shows the high-level technical building blocks (not Docker containers).

```
+----------------------------------------------------------------+
|                         Your System                             |
|  +----------------+     +----------------+     +--------------+ |
|  |   Web App      |     |    API         |     |   Database   | |
|  |   (React)      |---->|    (Node.js)   |---->|   (Postgres) | |
|  +----------------+     +----------------+     +--------------+ |
|                               |                                 |
|                               v                                 |
|                         +----------+                            |
|                         |  Cache   |                            |
|                         | (Redis)  |                            |
|                         +----------+                            |
+----------------------------------------------------------------+
```

**Containers are:**
- Separately deployable/runnable units
- Web applications, APIs, databases, file systems, message queues

### Level 3: Component

Shows the internal structure of a container.

```
+---------------------------------------------------------------+
|                         API Container                          |
|  +-------------+    +-------------+    +-------------------+  |
|  | Controllers |    |  Services   |    |   Repositories    |  |
|  |             |--->|             |--->|                   |  |
|  | UserCtrl    |    | UserService |    | UserRepository    |  |
|  | OrderCtrl   |    | OrderService|    | OrderRepository   |  |
|  +-------------+    +-------------+    +-------------------+  |
|                           |                                    |
|                           v                                    |
|                    +-------------+                             |
|                    |   Clients   |                             |
|                    | PaymentAPI  |                             |
|                    | EmailClient |                             |
|                    +-------------+                             |
+---------------------------------------------------------------+
```

**Components are:**
- Logical groupings of related functionality
- Controllers, services, repositories, clients

For full C4 templates with Mermaid diagrams: See [c4-diagram-templates.md](references/c4-diagram-templates.md)

---

## SOLID Principles Quick Reference

| Principle | Summary | Violation Sign |
|-----------|---------|----------------|
| **S**ingle Responsibility | One reason to change | Class does too many things |
| **O**pen/Closed | Open for extension, closed for modification | Frequent changes to existing code |
| **L**iskov Substitution | Subtypes replaceable for base types | Override breaks expectations |
| **I**nterface Segregation | Many specific interfaces > one general | Unused interface methods |
| **D**ependency Inversion | Depend on abstractions | Direct instantiation of dependencies |

---

## Design Patterns by Context

### API Design Patterns

**Resource Naming:**
```
GET    /users           # List users
GET    /users/123       # Get user
POST   /users           # Create user
PUT    /users/123       # Replace user
PATCH  /users/123       # Update user
DELETE /users/123       # Delete user

# Nested resources
GET    /users/123/orders
POST   /users/123/orders

# Actions (when CRUD doesn't fit)
POST   /orders/123/cancel
POST   /users/123/verify-email
```

**Pagination:**
```javascript
// Cursor-based (recommended for real-time data)
GET /posts?cursor=abc123&limit=20

// Offset-based (simpler, but has issues with real-time data)
GET /posts?page=2&per_page=20
```

**Error Response Format:**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": [
      { "field": "email", "message": "Invalid email format" }
    ],
    "request_id": "req_abc123"
  }
}
```

### Data Access Patterns

**Repository Pattern:**
```javascript
// Interface
interface UserRepository {
  findById(id: string): Promise<User | null>;
  findByEmail(email: string): Promise<User | null>;
  save(user: User): Promise<User>;
  delete(id: string): Promise<void>;
}

// Implementation
class PostgresUserRepository implements UserRepository {
  async findById(id: string) {
    return this.db.user.findUnique({ where: { id } });
  }
  // ...
}
```

**Service Layer Pattern:**
```javascript
class UserService {
  constructor(
    private userRepo: UserRepository,
    private emailService: EmailService
  ) {}

  async registerUser(data: CreateUserDto): Promise<User> {
    // Business logic
    const existingUser = await this.userRepo.findByEmail(data.email);
    if (existingUser) {
      throw new ConflictError('Email already registered');
    }

    const user = await this.userRepo.save({
      ...data,
      passwordHash: await hash(data.password)
    });

    await this.emailService.sendWelcome(user.email);

    return user;
  }
}
```

### Integration Patterns

**Backend-for-Frontend (BFF):**
```
Mobile App  -->  Mobile BFF  -->
                                   Core Services
Web App     -->  Web BFF     -->
```

**Circuit Breaker:**
```javascript
class CircuitBreaker {
  constructor(
    private threshold: number = 5,
    private timeout: number = 30000
  ) {
    this.failures = 0;
    this.state = 'CLOSED';
  }

  async execute<T>(fn: () => Promise<T>): Promise<T> {
    if (this.state === 'OPEN') {
      if (Date.now() - this.lastFailure > this.timeout) {
        this.state = 'HALF_OPEN';
      } else {
        throw new Error('Circuit breaker is OPEN');
      }
    }

    try {
      const result = await fn();
      this.onSuccess();
      return result;
    } catch (error) {
      this.onFailure();
      throw error;
    }
  }

  private onSuccess() {
    this.failures = 0;
    this.state = 'CLOSED';
  }

  private onFailure() {
    this.failures++;
    this.lastFailure = Date.now();
    if (this.failures >= this.threshold) {
      this.state = 'OPEN';
    }
  }
}
```

For detailed patterns: See [design-patterns.md](references/design-patterns.md)

---

## Anti-Patterns to Avoid

| Anti-Pattern | Problem | Solution |
|--------------|---------|----------|
| **God Object** | One class does everything | Split by responsibility |
| **Distributed Monolith** | Microservices with tight coupling | Define proper boundaries |
| **N+1 Queries** | One query per item in list | Eager loading, batching |
| **Premature Optimization** | Optimizing before measuring | Measure, then optimize |
| **Magic Numbers/Strings** | Hardcoded values everywhere | Use constants/config |
| **Leaky Abstraction** | Implementation details exposed | Proper encapsulation |
| **Circular Dependencies** | A depends on B, B depends on A | Introduce abstraction |

For comprehensive anti-patterns: See [anti-patterns.md](references/anti-patterns.md)

---

## Architecture Decision Records (ADR)

Document significant decisions for future reference:

```markdown
# ADR-001: Use PostgreSQL for Primary Database

## Status
Accepted

## Context
We need to select a primary database for our application. Key requirements:
- Complex queries across related data
- Strong consistency guarantees
- Support for JSON data when needed
- Team familiarity

## Decision
We will use PostgreSQL as our primary database.

## Alternatives Considered

### MongoDB
- Pros: Flexible schema, good for rapid iteration
- Cons: Eventual consistency, complex joins difficult

### MySQL
- Pros: Widely used, good performance
- Cons: Less feature-rich than PostgreSQL

## Consequences

### Positive
- Strong ACID guarantees
- Rich query capabilities
- JSON support when needed
- Excellent tooling ecosystem

### Negative
- Stricter schema requirements
- Requires upfront data modeling
- Horizontal scaling more complex

## Notes
Review this decision if we encounter significant scaling challenges
or if data model becomes highly document-oriented.
```

---

## Component Boundary Guidelines

### When to Split Components

Split when you have:
- Different rates of change
- Different scaling requirements
- Different team ownership
- Different security requirements
- Circular dependencies forming

### When to Keep Together

Keep together when:
- Highly cohesive functionality
- Frequently change together
- Performance-critical interactions
- Single team ownership
- Adds unnecessary complexity to split

### Boundary Definition Checklist

- [ ] Clear public interface defined
- [ ] Implementation details hidden
- [ ] Dependencies flow inward (to stable parts)
- [ ] Can be tested in isolation
- [ ] Can be deployed independently
- [ ] Owns its data (if applicable)

---

## Quick Architecture Review Checklist

Before finalizing architecture:

### Structure
- [ ] Clear separation of concerns
- [ ] Cohesive components
- [ ] Loose coupling between components
- [ ] No circular dependencies

### Scalability
- [ ] Identified bottlenecks addressed
- [ ] Stateless services where possible
- [ ] Caching strategy defined
- [ ] Database scaling approach planned

### Security
- [ ] Authentication/authorization designed
- [ ] Sensitive data protection planned
- [ ] Backend proxy pattern for external APIs
- [ ] Input validation at boundaries

### Operations
- [ ] Logging strategy defined
- [ ] Monitoring approach planned
- [ ] Error handling consistent
- [ ] Health check endpoints

### Documentation
- [ ] C4 diagrams created
- [ ] API contracts defined
- [ ] ADRs for key decisions
- [ ] Component responsibilities documented

---

## Detailed References

For comprehensive architectural guidance:

- **C4 Diagram Templates**: [references/c4-diagram-templates.md](references/c4-diagram-templates.md)
  - ASCII and Mermaid templates
  - All four C4 levels
  - Common system patterns

- **Design Patterns**: [references/design-patterns.md](references/design-patterns.md)
  - Detailed pattern implementations
  - When to use each pattern
  - Code examples

- **Anti-Patterns**: [references/anti-patterns.md](references/anti-patterns.md)
  - Common architectural mistakes
  - Detection signs
  - Refactoring strategies
