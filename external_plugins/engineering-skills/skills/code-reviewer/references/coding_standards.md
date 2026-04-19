# Coding Standards

Language-specific coding standards and conventions for code review.

---

## Table of Contents

- [Universal Principles](#universal-principles)
- [TypeScript Standards](#typescript-standards)
- [JavaScript Standards](#javascript-standards)
- [Python Standards](#python-standards)
- [Go Standards](#go-standards)
- [Swift Standards](#swift-standards)
- [Kotlin Standards](#kotlin-standards)

---

## Universal Principles

These apply across all languages.

### Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| Variables | camelCase (JS/TS), snake_case (Python/Go) | `userName`, `user_name` |
| Constants | SCREAMING_SNAKE_CASE | `MAX_RETRY_COUNT` |
| Functions | camelCase (JS/TS), snake_case (Python) | `getUserById`, `get_user_by_id` |
| Classes | PascalCase | `UserRepository` |
| Interfaces | PascalCase, optionally prefixed | `IUserService` or `UserService` |
| Private members | Prefix with underscore or use access modifiers | `_internalState` |

### Function Design

```
Good functions:
- Do one thing well
- Have descriptive names (verb + noun)
- Take 3 or fewer parameters
- Return early for error cases
- Stay under 50 lines
```

### Error Handling

```
Good error handling:
- Catch specific errors, not generic exceptions
- Log with context (what, where, why)
- Clean up resources in error paths
- Don't swallow errors silently
- Provide actionable error messages
```

---

## TypeScript Standards

### Type Annotations

```typescript
// Avoid 'any' - use unknown for truly unknown types
function processData(data: unknown): ProcessedResult {
  if (isValidData(data)) {
    return transform(data);
  }
  throw new Error('Invalid data format');
}

// Use explicit return types for public APIs
export function calculateTotal(items: CartItem[]): number {
  return items.reduce((sum, item) => sum + item.price, 0);
}

// Use type guards for runtime checks
function isUser(obj: unknown): obj is User {
  return (
    typeof obj === 'object' &&
    obj !== null &&
    'id' in obj &&
    'email' in obj
  );
}
```

### Null Safety

```typescript
// Use optional chaining and nullish coalescing
const userName = user?.profile?.name ?? 'Anonymous';

// Be explicit about nullable types
interface Config {
  timeout: number;
  retries?: number;  // Optional
  fallbackUrl: string | null;  // Explicitly nullable
}

// Use assertion functions for validation
function assertDefined<T>(value: T | null | undefined): asserts value is T {
  if (value === null || value === undefined) {
    throw new Error('Value is not defined');
  }
}
```

### Async/Await

```typescript
// Always handle errors in async functions
async function fetchUser(id: string): Promise<User> {
  try {
    const response = await api.get(`/users/${id}`);
    return response.data;
  } catch (error) {
    logger.error('Failed to fetch user', { id, error });
    throw new UserFetchError(id, error);
  }
}

// Use Promise.all for parallel operations
async function loadDashboard(userId: string): Promise<Dashboard> {
  const [profile, stats, notifications] = await Promise.all([
    fetchProfile(userId),
    fetchStats(userId),
    fetchNotifications(userId)
  ]);
  return { profile, stats, notifications };
}
```

### React/Component Standards

```typescript
// Use explicit prop types
interface ButtonProps {
  label: string;
  onClick: () => void;
  variant?: 'primary' | 'secondary';
  disabled?: boolean;
}

// Prefer functional components with hooks
function Button({ label, onClick, variant = 'primary', disabled = false }: ButtonProps) {
  return (
    <button
      className={`btn btn-${variant}`}
      onClick={onClick}
      disabled={disabled}
    >
      {label}
    </button>
  );
}

// Use custom hooks for reusable logic
function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);

  return debouncedValue;
}
```

---

## JavaScript Standards

### Variable Declarations

```javascript
// Use const by default, let when reassignment needed
const MAX_ITEMS = 100;
let currentCount = 0;

// Never use var
// var is function-scoped and hoisted, leading to bugs
```

### Object and Array Patterns

```javascript
// Use object destructuring
const { name, email, role = 'user' } = user;

// Use spread for immutable updates
const updatedUser = { ...user, lastLogin: new Date() };
const updatedList = [...items, newItem];

// Use array methods over loops
const activeUsers = users.filter(u => u.isActive);
const emails = users.map(u => u.email);
const total = orders.reduce((sum, o) => sum + o.amount, 0);
```

### Module Patterns

```javascript
// Use named exports for utilities
export function formatDate(date) { ... }
export function parseDate(str) { ... }

// Use default export for main component/class
export default class UserService { ... }

// Group related exports
export { formatDate, parseDate, isValidDate } from './dateUtils';
```

---

## Python Standards

### Type Hints (PEP 484)

```python
from typing import Optional, List, Dict, Union

def get_user(user_id: int) -> Optional[User]:
    """Fetch user by ID, returns None if not found."""
    return db.query(User).filter(User.id == user_id).first()

def process_items(items: List[str]) -> Dict[str, int]:
    """Count occurrences of each item."""
    return {item: items.count(item) for item in set(items)}

def send_notification(
    user: User,
    message: str,
    *,
    priority: str = "normal",
    channels: List[str] = None
) -> bool:
    """Send notification to user via specified channels."""
    channels = channels or ["email"]
    # Implementation
```

### Exception Handling

```python
# Catch specific exceptions
try:
    result = api_client.fetch_data(endpoint)
except ConnectionError as e:
    logger.warning(f"Connection failed: {e}")
    return cached_data
except TimeoutError as e:
    logger.error(f"Request timed out: {e}")
    raise ServiceUnavailableError() from e

# Use context managers for resources
with open(filepath, 'r') as f:
    data = json.load(f)

# Custom exceptions should be informative
class ValidationError(Exception):
    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")
```

### Class Design

```python
from dataclasses import dataclass
from abc import ABC, abstractmethod

# Use dataclasses for data containers
@dataclass
class UserDTO:
    id: int
    email: str
    name: str
    is_active: bool = True

# Use ABC for interfaces
class Repository(ABC):
    @abstractmethod
    def find_by_id(self, id: int) -> Optional[Entity]:
        pass

    @abstractmethod
    def save(self, entity: Entity) -> Entity:
        pass

# Use properties for computed attributes
class Order:
    def __init__(self, items: List[OrderItem]):
        self._items = items

    @property
    def total(self) -> Decimal:
        return sum(item.price * item.quantity for item in self._items)
```

---

## Go Standards

### Error Handling

```go
// Always check errors
file, err := os.Open(filename)
if err != nil {
    return fmt.Errorf("failed to open %s: %w", filename, err)
}
defer file.Close()

// Use custom error types for specific cases
type ValidationError struct {
    Field   string
    Message string
}

func (e *ValidationError) Error() string {
    return fmt.Sprintf("%s: %s", e.Field, e.Message)
}

// Wrap errors with context
if err := db.Query(query); err != nil {
    return fmt.Errorf("query failed for user %d: %w", userID, err)
}
```

### Struct Design

```go
// Use unexported fields with exported methods
type UserService struct {
    repo   UserRepository
    cache  Cache
    logger Logger
}

// Constructor functions for initialization
func NewUserService(repo UserRepository, cache Cache, logger Logger) *UserService {
    return &UserService{
        repo:   repo,
        cache:  cache,
        logger: logger,
    }
}

// Keep interfaces small
type Reader interface {
    Read(p []byte) (n int, err error)
}

type Writer interface {
    Write(p []byte) (n int, err error)
}
```

### Concurrency

```go
// Use context for cancellation
func fetchData(ctx context.Context, url string) ([]byte, error) {
    req, err := http.NewRequestWithContext(ctx, "GET", url, nil)
    if err != nil {
        return nil, err
    }
    // ...
}

// Use channels for communication
func worker(jobs <-chan Job, results chan<- Result) {
    for job := range jobs {
        result := process(job)
        results <- result
    }
}

// Use sync.WaitGroup for coordination
var wg sync.WaitGroup
for _, item := range items {
    wg.Add(1)
    go func(i Item) {
        defer wg.Done()
        processItem(i)
    }(item)
}
wg.Wait()
```

---

## Swift Standards

### Optionals

```swift
// Use optional binding
if let user = fetchUser(id: userId) {
    displayProfile(user)
}

// Use guard for early exit
guard let data = response.data else {
    throw NetworkError.noData
}

// Use nil coalescing for defaults
let displayName = user.nickname ?? user.email

// Avoid force unwrapping except in tests
// BAD: let name = user.name!
// GOOD: guard let name = user.name else { return }
```

### Protocol-Oriented Design

```swift
// Define protocols with minimal requirements
protocol Identifiable {
    var id: String { get }
}

protocol Persistable: Identifiable {
    func save() throws
    static func find(by id: String) -> Self?
}

// Use protocol extensions for default implementations
extension Persistable {
    func save() throws {
        try Storage.shared.save(self)
    }
}

// Prefer composition over inheritance
struct User: Identifiable, Codable {
    let id: String
    var name: String
    var email: String
}
```

### Error Handling

```swift
// Define domain-specific errors
enum AuthError: Error {
    case invalidCredentials
    case tokenExpired
    case networkFailure(underlying: Error)
}

// Use Result type for async operations
func authenticate(
    email: String,
    password: String,
    completion: @escaping (Result<User, AuthError>) -> Void
)

// Use throws for synchronous operations
func validate(_ input: String) throws -> ValidatedInput {
    guard !input.isEmpty else {
        throw ValidationError.emptyInput
    }
    return ValidatedInput(value: input)
}
```

---

## Kotlin Standards

### Null Safety

```kotlin
// Use nullable types explicitly
fun findUser(id: Int): User? {
    return userRepository.find(id)
}

// Use safe calls and elvis operator
val name = user?.profile?.name ?: "Unknown"

// Use let for null checks with side effects
user?.let { activeUser ->
    sendWelcomeEmail(activeUser.email)
    logActivity(activeUser.id)
}

// Use require/check for validation
fun processPayment(amount: Double) {
    require(amount > 0) { "Amount must be positive: $amount" }
    // Process
}
```

### Data Classes and Sealed Classes

```kotlin
// Use data classes for DTOs
data class UserDTO(
    val id: Int,
    val email: String,
    val name: String,
    val isActive: Boolean = true
)

// Use sealed classes for state
sealed class Result<out T> {
    data class Success<T>(val data: T) : Result<T>()
    data class Error(val message: String, val cause: Throwable? = null) : Result<Nothing>()
    object Loading : Result<Nothing>()
}

// Pattern matching with when
fun handleResult(result: Result<User>) = when (result) {
    is Result.Success -> showUser(result.data)
    is Result.Error -> showError(result.message)
    Result.Loading -> showLoading()
}
```

### Coroutines

```kotlin
// Use structured concurrency
suspend fun loadDashboard(): Dashboard = coroutineScope {
    val profile = async { fetchProfile() }
    val stats = async { fetchStats() }
    val notifications = async { fetchNotifications() }

    Dashboard(
        profile = profile.await(),
        stats = stats.await(),
        notifications = notifications.await()
    )
}

// Handle cancellation
suspend fun fetchWithRetry(url: String): Response {
    repeat(3) { attempt ->
        try {
            return httpClient.get(url)
        } catch (e: IOException) {
            if (attempt == 2) throw e
            delay(1000L * (attempt + 1))
        }
    }
    throw IllegalStateException("Unreachable")
}
```
