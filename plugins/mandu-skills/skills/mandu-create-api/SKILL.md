---
name: mandu-create-api
description: |
  REST API 생성. CRUD/인증/업로드 엔드포인트. 'API', 'endpoint', 'CRUD' 시 자동 호출
---

# Mandu Create API

REST API 엔드포인트를 생성하는 워크플로우.
Route + Contract + Slot + Test 파이프라인으로 완전한 API를 스캐폴딩합니다.

## Workflow: Route -> Contract -> Slot -> Test

### Step 1: Route 생성

```typescript
// app/api/posts/route.ts
import { Mandu } from "@mandujs/core";

export default Mandu.filling()
  .get((ctx) => ctx.ok({ posts: [] }))
  .post(async (ctx) => {
    const body = await ctx.body<CreatePostInput>();
    return ctx.created({ post: body });
  });
```

### Step 2: Contract 정의

```typescript
// src/shared/contracts/post.contract.ts
import { z } from "zod";

export const CreatePostInput = z.object({
  title: z.string().min(1).max(200),
  content: z.string().min(1),
  tags: z.array(z.string()).optional(),
});

export const PostResponse = z.object({
  id: z.string(),
  title: z.string(),
  content: z.string(),
  createdAt: z.string().datetime(),
});

export type CreatePostInput = z.infer<typeof CreatePostInput>;
export type PostResponse = z.infer<typeof PostResponse>;
```

### Step 3: Slot (서버 데이터 로더)

```typescript
// spec/slots/posts.slot.ts
import { Mandu } from "@mandujs/core";
import { CreatePostInput } from "@/shared/contracts/post.contract";

export default Mandu.filling()
  .guard(async (ctx) => {
    const token = ctx.headers.get("authorization");
    if (!token) return ctx.error(401, "Unauthorized");
    ctx.set("userId", await verifyToken(token));
  })
  .post(async (ctx) => {
    const body = await ctx.body<CreatePostInput>();
    const validated = CreatePostInput.parse(body);
    const post = await db.posts.create({ ...validated, userId: ctx.get("userId") });
    return ctx.created({ post });
  });
```

### Step 4: Test 작성

```typescript
// tests/api/posts.test.ts
import { describe, test, expect } from "bun:test";

describe("POST /api/posts", () => {
  test("creates a post with valid input", async () => {
    const res = await fetch("http://localhost:3333/api/posts", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: "Bearer test-token",
      },
      body: JSON.stringify({ title: "Test", content: "Hello" }),
    });
    expect(res.status).toBe(201);
    const data = await res.json();
    expect(data.post.title).toBe("Test");
  });

  test("returns 401 without auth", async () => {
    const res = await fetch("http://localhost:3333/api/posts", {
      method: "POST",
      body: JSON.stringify({ title: "Test", content: "Hello" }),
    });
    expect(res.status).toBe(401);
  });
});
```

## CRUD Pattern

```
app/api/{resource}/route.ts          GET (list), POST (create)
app/api/{resource}/[id]/route.ts     GET (read), PATCH (update), DELETE (remove)
src/shared/contracts/{resource}.contract.ts
spec/slots/{resource}.slot.ts
tests/api/{resource}.test.ts
```

## MCP Tools

| Tool | Purpose |
|------|---------|
| `mandu_add_route` | Create route file at correct path |
| `mandu_create_contract` | Generate Zod contract schema |
| `mandu_negotiate` | Analyze API requirements |
| `mandu_generate` | Full scaffold generation |

## Auth Patterns

```typescript
// Bearer token guard
.guard(async (ctx) => {
  const token = ctx.headers.get("authorization")?.replace("Bearer ", "");
  if (!token) return ctx.error(401, "Missing token");
  ctx.set("user", await verifyToken(token));
})

// API key guard
.guard((ctx) => {
  const key = ctx.headers.get("x-api-key");
  if (key !== process.env.API_KEY) return ctx.error(403, "Invalid API key");
})
```

## Key Rules

1. 모든 API route는 `Mandu.filling()` 체인으로 export
2. 반드시 Contract를 먼저 정의하고 validation에 사용
3. `.guard()`로 인증/인가 처리 (인라인 체크 금지)
4. 에러는 `ctx.error(status, message)` 사용
5. `ctx.body()`는 반드시 await
