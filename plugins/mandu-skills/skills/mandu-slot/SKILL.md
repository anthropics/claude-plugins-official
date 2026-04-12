---
name: mandu-slot
description: |
  Filling API 레퍼런스. ctx 메서드, 라이프사이클 훅, 미들웨어 체인.
  Mandu.filling(), ctx.ok(), .guard(), slot 파일 작업 시 자동 호출.
---

# Mandu Slot (Filling API)

Slot은 비즈니스 로직을 작성하는 파일입니다. `Mandu.filling()` API를 사용하여
API 핸들러, 인증 가드, 라이프사이클 훅을 구현합니다.

## Filling Chain API

### Basic Route Handler

```typescript
// app/api/users/route.ts
import { Mandu } from "@mandujs/core";

export default Mandu.filling()
  .get((ctx) => ctx.ok({ users: [] }))
  .post(async (ctx) => {
    const body = await ctx.body<{ name: string }>();
    return ctx.created({ user: { id: "1", ...body } });
  })
  .patch(async (ctx) => {
    const body = await ctx.body<{ name: string }>();
    return ctx.ok({ user: { id: ctx.params.id, ...body } });
  })
  .delete((ctx) => ctx.noContent());
```

CRITICAL: Always use `Mandu.filling()` chain as default export. Never export raw functions.

## Context Methods (ctx)

### Response Methods

| Method | Status | Usage |
|--------|--------|-------|
| `ctx.ok(data)` | 200 | Success response |
| `ctx.created(data)` | 201 | Resource created |
| `ctx.noContent()` | 204 | Deleted/no body |
| `ctx.error(status, msg)` | 4xx/5xx | Error response |

### Request Methods

```typescript
const body = await ctx.body<T>();       // Parse JSON body (MUST await)
const { id } = ctx.params;             // URL params (/users/[id])
const { page, limit } = ctx.query;     // Query string (?page=1&limit=10)
const auth = ctx.headers.get("authorization");  // Request header
```

### Store (cross-middleware state)

```typescript
ctx.set("user", authenticatedUser);    // Set value
const user = ctx.get("user");          // Get value
```

## Guard (Authentication/Authorization)

```typescript
export default Mandu.filling()
  .guard(async (ctx) => {
    const token = ctx.headers.get("authorization");
    if (!token) return ctx.error(401, "Unauthorized");
    const user = await verifyToken(token);
    ctx.set("user", user);
    // Return void to continue, return Response to block
  })
  .get((ctx) => ctx.ok({ user: ctx.get("user") }));
```

Multiple guards run in order. First one to return a Response blocks the chain.

## Lifecycle Hooks

```typescript
export default Mandu.filling()
  .onRequest((ctx) => {
    ctx.set("startTime", Date.now());       // Before handler
  })
  .get((ctx) => ctx.ok({ data: "hello" }))
  .afterHandle((ctx, response) => {
    const ms = Date.now() - ctx.get("startTime");
    console.log(`${ctx.method} ${ctx.path} ${ms}ms`);
    return response;                        // After handler
  });
```

## Slot File Locations

| File | Location | Purpose |
|------|----------|---------|
| API route | `app/api/{name}/route.ts` | HTTP endpoint handler |
| Data loader | `spec/slots/{name}.slot.ts` | Server-side data fetch (before render) |
| Client logic | `spec/slots/{name}.client.ts` | Client-side island logic |

Slot files (`.slot.ts`) run on the server before page rendering.
Data they return is available to Islands via `useServerData()`.

## Middleware Pattern

```typescript
// Reusable middleware
const withAuth = (ctx) => {
  const token = ctx.headers.get("authorization");
  if (!token) return ctx.error(401, "Unauthorized");
  ctx.set("user", decodeToken(token));
};

const withRateLimit = (ctx) => {
  // rate limit logic
};

// Compose
export default Mandu.filling()
  .guard(withRateLimit)
  .guard(withAuth)
  .get((ctx) => ctx.ok({ user: ctx.get("user") }));
```

## Common Mistakes

- Exporting raw handler functions instead of `Mandu.filling()` chain
- Placing slot files outside `spec/slots/` directory
- Forgetting to `await ctx.body()`
- Using inline auth checks instead of `.guard()`
- Not returning `void` from guard when request should continue
