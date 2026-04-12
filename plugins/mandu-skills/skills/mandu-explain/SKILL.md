---
name: mandu-explain
description: |
  Mandu 개념 설명. Island/Filling/Guard/Contract/Slot/SSR/ISR 등 '뭐야'/'어떻게' 시 자동 호출
---

# Mandu Explain

Mandu 프레임워크의 핵심 개념 18가지를 설명하는 레퍼런스.

## Core Concepts

### 1. Island Architecture
페이지의 대부분은 정적 HTML로 서버 렌더링하고, 인터랙티브한 부분만 JavaScript를 로드하는 패턴.
```
[Static HTML] [Static HTML] [Island: JS] [Static HTML]
```
장점: 초기 로딩 속도, 작은 번들 크기, SEO 친화적.

### 2. Filling (Mandu.filling())
API 핸들러를 체이닝으로 작성하는 API. Express의 미들웨어와 유사하지만 타입 안전.
```typescript
Mandu.filling().guard(authCheck).get(handler).post(handler)
```

### 3. Guard
아키텍처 규칙을 코드 레벨에서 강제하는 시스템. import 방향, 파일 위치, 금지된 의존성을 검사.
```bash
bunx mandu guard arch  # 전체 프로젝트 검사
```

### 4. Contract
Zod 스키마 기반 API 계약. 클라이언트-서버 간 타입을 공유하고 런타임 validation을 수행.
```typescript
// src/shared/contracts/user.contract.ts
export const CreateUser = z.object({ name: z.string(), email: z.string().email() });
```

### 5. Slot
서버에서 렌더링 전에 실행되는 데이터 로더. `spec/slots/*.slot.ts`에 위치.
```typescript
// spec/slots/dashboard.slot.ts - page 렌더링 전에 데이터를 fetch
export default Mandu.filling().get(async (ctx) => ctx.ok({ stats: await getStats() }));
```

### 6. SSR (Server-Side Rendering)
모든 페이지를 서버에서 HTML로 렌더링. `app/layout.tsx`에서 `<html>/<head>/<body>` 태그 불필요 (자동 생성).

### 7. Streaming SSR
서버에서 HTML을 청크 단위로 스트리밍. 첫 바이트 시간(TTFB)을 단축.

### 8. Hydration
서버 렌더링된 HTML에 JavaScript 인터랙티비티를 부착하는 과정.
Priority: `immediate` > `visible` > `idle` > `interaction`

### 9. FS Routes
파일 시스템 기반 라우팅. `app/` 폴더 구조가 URL이 됨.
- `app/page.tsx` -> `/`
- `app/users/[id]/page.tsx` -> `/users/:id`

### 10. Layout
페이지를 감싸는 공통 UI 래퍼. `<html>/<head>/<body>` 사용 금지.
```tsx
export default function Layout({ children }) {
  return <div className="min-h-screen">{children}</div>;
}
```

### 11. Route Groups
`(name)` 괄호로 감싼 폴더는 URL에 영향 없이 라우트를 그룹화.
```
app/(auth)/login/page.tsx -> /login
app/(auth)/signup/page.tsx -> /signup
```

### 12. MCP (Model Context Protocol)
AI 에이전트가 프레임워크 도구를 직접 호출하는 인터페이스.
`@mandujs/mcp`가 50+ 도구를 제공: negotiate, generate, guard, brain 등.

### 13. ATE (Automated Test Engine)
API 엔드포인트의 테스트를 자동 생성하는 엔진.

### 14. Brain
코드 분석 및 진단 시스템. 프로젝트 구조, 의존성, 성능 이슈를 분석.

### 15. Presets
Guard가 사용하는 아키텍처 템플릿: `mandu`, `fsd`, `clean`, `hexagonal`, `atomic`, `cqrs`

### 16. Lockfile (.mandu/lockfile.json)
프로젝트 설정의 무결성을 보장하는 해시 기반 잠금 파일.

### 17. useServerData
Island에서 서버 Slot이 주입한 데이터를 읽는 클라이언트 훅.
```typescript
const data = useServerData<UserData>("user-profile");
```

### 18. useIslandEvent
Island 간 통신을 위한 이벤트 시스템.
```typescript
const { emit, on } = useIslandEvent();
emit("cart:updated", { count: 5 });
```

## Architecture Layers

```
app/           UI (pages, layouts, islands)
src/client/    Client-side code
src/server/    Server-side business logic
src/shared/    Shared types, contracts, utils
spec/          Slots, tests
```

## Key Import Rules

| From | Import |
|------|--------|
| Island files | `@mandujs/core/client` |
| Server files | `@mandujs/core` |
| Shared code | `@/shared/*` |
