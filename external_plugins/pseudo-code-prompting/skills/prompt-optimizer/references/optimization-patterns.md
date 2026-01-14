# Optimization Patterns

## Pattern Library

### Pattern 1: Boolean Flag Consolidation
**When**: Multiple boolean flags that are commonly used together

**Before**:
```
feature(enabled=true, active=true, visible=true, public=true)
```

**After**:
```
feature(state="active")  // implies enabled, visible, public
```

### Pattern 2: Nested Object Flattening
**When**: Single-level nesting with few properties

**Before**:
```
config(database={host:"localhost"}, cache={host:"localhost"})
```

**After**:
```
config(db_host="localhost", cache_host="localhost")
```

### Pattern 3: Array Simplification
**When**: Single-item arrays or obvious defaults

**Before**:
```
setup(languages=["javascript"], frameworks=["react"])
```

**After**:
```
setup(lang="javascript", framework="react")
```

### Pattern 4: Implicit Context
**When**: Parameter values can be inferred from function name

**Before**:
```
create_user_account(entity_type="user", action="create")
```

**After**:
```
create_user_account()  // type and action implicit
```

### Pattern 5: Default Elimination
**When**: Value is the most common default

**Before**:
```
request(method="GET", format="json", timeout=30)
```

**After**:
```
request()  // all are standard defaults
```

### Pattern 6: Enumeration Shortening
**When**: Using verbose enumeration values

**Before**:
```
log(level="information", destination="filesystem")
```

**After**:
```
log(level="info", dest="file")
```

### Pattern 7: Redundant Prefix Removal
**When**: Parameter names repeat function context

**Before**:
```
authenticate_user(user_name="john", user_email="john@example.com")
```

**After**:
```
authenticate_user(name="john", email="john@example.com")
```

### Pattern 8: Unit Suffix Integration
**When**: Units can be integrated into value

**Before**:
```
cache(duration=3600, duration_unit="seconds")
```

**After**:
```
cache(ttl="3600s")
```

## Common Abbreviations

### Infrastructure
- database → db
- configuration → config
- environment → env
- repository → repo
- authentication → auth
- authorization → authz

### Operations
- create → new (when context is clear)
- delete → del
- update → upd
- synchronize → sync
- initialize → init
- execute → exec

### Attributes
- maximum → max
- minimum → min
- average → avg
- count → cnt
- number → num
- information → info
- temporary → temp
- destination → dest
- source → src

### Time Units
- milliseconds → ms
- seconds → s
- minutes → m
- hours → h
- days → d

### Data Types
- boolean → bool
- integer → int
- string → str
- array → arr
- object → obj

## Anti-Patterns to Avoid

### Anti-Pattern 1: Over-Abbreviation
**Bad**: `usr_cfg_db_conn_str`
**Good**: `user_db_connection`

### Anti-Pattern 2: Unclear Context Removal
**Bad**: `process(data)` (what kind of processing?)
**Good**: `validate_input(data)`

### Anti-Pattern 3: Losing Critical Information
**Bad**: `setup(params)`
**Good**: `setup(db_host="...", api_key="...")`

### Anti-Pattern 4: Inconsistent Naming
**Bad**: `create_usr()`, `delete_user()`, `update_u()`
**Good**: `create_user()`, `delete_user()`, `update_user()`

### Anti-Pattern 5: Premature Optimization
**Bad**: Optimizing already clear, short pseudo-code
**Good**: Only optimize when there's clear benefit
