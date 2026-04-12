---
name: mandu-create-feature
description: |
  Mandu 피처 생성. 페이지/API/Island 스캐폴딩. '만들어줘', 'create', 'add page' 시 자동 호출
---

# Mandu Create Feature

Mandu 프로젝트에 새 피처를 생성하는 5단계 워크플로우.
MCP 도구 파이프라인을 통해 페이지, API, Island을 자동 스캐폴딩합니다.

## 5-Phase Workflow

### Phase 1: Negotiate (요구사항 분석)

MCP 도구 `mandu_negotiate`를 호출하여 피처 요구사항을 분석합니다.

```
mandu_negotiate({ description: "사용자 프로필 페이지와 편집 기능" })
```

결과: 필요한 라우트, 컴포넌트, API 엔드포인트 목록이 반환됩니다.

### Phase 2: Add Routes (라우트 생성)

분석 결과를 바탕으로 `mandu_add_route`로 라우트를 생성합니다.

```
mandu_add_route({ path: "/users/[id]", type: "page" })
mandu_add_route({ path: "/api/users/[id]", type: "api" })
```

파일 생성 규칙:
- Page: `app/users/[id]/page.tsx`
- API: `app/api/users/[id]/route.ts`
- Layout: `app/users/layout.tsx`

### Phase 3: Create Contracts (타입 계약)

`mandu_create_contract`로 API 계약을 정의합니다.

```
mandu_create_contract({
  name: "user",
  methods: ["get", "patch"],
  fields: { name: "string", email: "string", avatar: "string?" }
})
```

생성 위치: `src/shared/contracts/user.contract.ts`

### Phase 4: Generate Scaffold (코드 생성)

`mandu_generate`로 전체 스캐폴드를 생성합니다.

```
mandu_generate({ spec: negotiateResult })
```

생성되는 파일:
- `.mandu/generated/server/` - 서버 코드
- `.mandu/generated/web/` - 클라이언트 코드
- `spec/slots/*.slot.ts` - 서버 데이터 로더
- `app/**/*.island.tsx` - Island 컴포넌트

### Phase 5: Guard Heal (아키텍처 검증)

`mandu_guard_heal`로 생성된 코드의 아키텍처 규칙 준수를 검증합니다.

```
mandu_guard_heal({ autofix: true })
```

위반 사항이 있으면 자동 수정을 시도합니다.

## Quick Recipes

### 새 페이지 추가
```
negotiate → add_route(page) → generate
```

### 새 API + 페이지
```
negotiate → add_route(page) → add_route(api) → create_contract → generate → guard_heal
```

### Island 추가
```
negotiate → add_route(page) → generate → island 파일에 "use client" 확인
```

## Key Rules

1. 항상 `mandu_negotiate`부터 시작 (분석 없이 직접 생성하지 않기)
2. API 엔드포인트에는 반드시 contract 생성
3. 생성 후 `mandu_guard_heal`로 검증
4. Layout에 `<html>/<head>/<body>` 태그 사용 금지
5. Island 파일은 `@mandujs/core/client`에서 import
