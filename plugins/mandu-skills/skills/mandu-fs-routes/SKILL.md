---
name: mandu-fs-routes
description: |
  파일 시스템 라우팅 규칙. layout에 html/head/body 금지.
  app/ 폴더, page.tsx, route.ts, layout.tsx, [id] 작업 시 자동 호출.
---

# Mandu FS Routes

파일 시스템 기반 라우팅. `app/` 폴더의 파일 구조가 URL이 됩니다.

## File Naming Conventions

| File | Purpose | Export |
|------|---------|--------|
| `page.tsx` | Page component | `default` function component |
| `route.ts` | API handler | `default` Mandu.filling() chain |
| `layout.tsx` | Shared layout | `default` function with `children` prop |
| `loading.tsx` | Loading UI | `default` function component |
| `error.tsx` | Error UI | `default` function component |

## URL Mapping

| File Path | URL |
|-----------|-----|
| `app/page.tsx` | `/` |
| `app/about/page.tsx` | `/about` |
| `app/blog/[slug]/page.tsx` | `/blog/:slug` |
| `app/users/[id]/page.tsx` | `/users/:id` |
| `app/docs/[...path]/page.tsx` | `/docs/*` (catch-all) |
| `app/(auth)/login/page.tsx` | `/login` (grouped) |
| `app/api/users/route.ts` | `/api/users` |
| `app/api/users/[id]/route.ts` | `/api/users/:id` |

## Layout Rules (CRITICAL)

Layout MUST NOT include `<html>`, `<head>`, or `<body>` tags.
Mandu SSR generates these automatically.

```tsx
// app/layout.tsx - CORRECT
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-background font-sans antialiased">
      {children}
    </div>
  );
}
```

```tsx
// app/layout.tsx - WRONG (causes double-wrapping)
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html>          // <-- DO NOT include
      <head />      // <-- DO NOT include
      <body>        // <-- DO NOT include
        {children}
      </body>
    </html>
  );
}
```

Nested layouts wrap child pages:
```
app/layout.tsx              -> wraps ALL pages
app/dashboard/layout.tsx    -> wraps /dashboard/* pages
```

## Page Components

```tsx
// app/dashboard/page.tsx
export default function DashboardPage() {
  return (
    <main>
      <h1>Dashboard</h1>
    </main>
  );
}
```

Pages are server-rendered by default. No `"use client"` needed unless using Islands.

## API Routes

```typescript
// app/api/users/route.ts
import { Mandu } from "@mandujs/core";

export default Mandu.filling()
  .get((ctx) => ctx.ok({ users: [] }))
  .post(async (ctx) => {
    const body = await ctx.body<{ name: string }>();
    return ctx.created({ user: body });
  });
```

API routes use `.ts` extension (NOT `.tsx`).

## Dynamic Routes

```tsx
// app/users/[id]/page.tsx
export default function UserPage({ params }: { params: { id: string } }) {
  return <h1>User {params.id}</h1>;
}

// app/docs/[...path]/page.tsx
export default function DocsPage({ params }: { params: { path: string[] } }) {
  return <h1>Doc: {params.path.join("/")}</h1>;
}
```

## Route Groups

Parenthesized folders create logical groups without affecting the URL:

```
app/(marketing)/about/page.tsx   -> /about
app/(marketing)/pricing/page.tsx -> /pricing
app/(app)/dashboard/page.tsx     -> /dashboard
```

## Common Mistakes

- Adding `<html>/<head>/<body>` in layout.tsx (SSR does this)
- Using `route.tsx` instead of `route.ts` for API handlers
- Forgetting to export default from page/layout files
- Mixing page.tsx and route.ts in the same directory
