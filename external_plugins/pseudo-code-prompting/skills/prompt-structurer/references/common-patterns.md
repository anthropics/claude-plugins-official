# Common Transformation Patterns

## Authentication Features
- "Add OAuth" → `implement_authentication(type="oauth", ...)`
- "Add 2FA" → `implement_authentication(type="two_factor", ...)`
- "Add API keys" → `implement_authentication(type="api_key", ...)`

## Database Operations
- "Optimize query" → `optimize_query(target="...", metrics=["latency"])`
- "Add index" → `create_index(table="...", columns=[...])`
- "Add caching" → `implement_cache(targets=["..."], ttl="...")`

## API Endpoints
- "Add endpoint" → `create_endpoint(path="...", method="...", auth=...)`
- "Add rate limiting" → `implement_rate_limit(endpoints=["..."], limit=...)`

## Performance
- "Speed up X" → `optimize_performance(target="...", priority="speed")`
- "Reduce memory" → `optimize_performance(target="...", priority="memory")`
