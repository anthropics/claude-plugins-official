---
name: mandu-debug
description: |
  에러 진단+수정. 빌드실패/하얀화면/Island안됨/API에러/CSS깨짐 시 자동 호출
---

# Mandu Debug

Mandu 프로젝트의 에러를 진단하고 수정하는 8카테고리 트리아지 시스템.
증상 → 수집 → 진단 → 수정 → 검증 순서로 진행합니다.

## Triage: 8 Error Categories

| Category | Symptoms | First Check |
|----------|----------|-------------|
| **Build** | `bun run build` fails, TS errors | `bunx mandu guard arch --ci` |
| **White Screen** | Page loads but blank | Browser console, SSR output |
| **Island** | Component not interactive | `"use client"`, import path |
| **API** | 4xx/5xx from endpoints | Route file, `Mandu.filling()` chain |
| **CSS** | Styles missing/broken | `app/globals.css`, Tailwind config |
| **Guard** | Architecture violations | `bunx mandu guard arch` |
| **HMR** | Changes not reflecting | Dev server restart, port conflict |
| **Hydration** | Mismatch warnings | Server vs client render diff |

## Parallel Collection Phase

문제 발생 시 동시에 수집할 정보:

```bash
# 1. Guard check (아키텍처 위반 여부)
bunx mandu guard arch --ci

# 2. TypeScript check
bunx tsc --noEmit

# 3. Dev server logs
# 이미 실행 중이면 터미널 출력 확인

# 4. Browser console
# 개발자 도구에서 에러 메시지 확인
```

MCP 도구로 수집:
```
mandu_brain_diagnose({ symptoms: "white screen on /dashboard" })
```

## Fix Patterns by Category

### Build Failure
1. `bunx tsc --noEmit` - TypeScript 에러 위치 확인
2. Import 경로 확인 (특히 `@mandujs/core` vs `@mandujs/core/client`)
3. `bun install` - 의존성 누락 확인

### White Screen
1. `app/layout.tsx`에 `<html>/<head>/<body>` 태그가 있는지 확인 -> 있으면 제거
2. `page.tsx`에서 default export 확인
3. SSR 에러: 서버 로그에서 렌더링 에러 확인

### Island Not Working
1. `"use client"` 디렉티브 확인 (파일 최상단)
2. Import: `@mandujs/core/client` (NOT `@mandujs/core`)
3. `.island.tsx` 또는 `.client.tsx` 파일 확장자 확인
4. `island()` API로 감싸져 있는지 확인

### API Error
1. `route.ts` (NOT `route.tsx`) 확인
2. `Mandu.filling()` 체인으로 default export 확인
3. `ctx.body()` await 누락 확인
4. `.guard()` 반환값 확인 (void = 계속, Response = 차단)

### CSS Missing
1. `app/globals.css` 존재 확인
2. Tailwind v4 import 확인: `@import "tailwindcss"`
3. 프로덕션: `cssPath` 옵션이 서버에 전달되는지 확인

### Guard Violation
1. `bunx mandu guard arch` 실행
2. Layer 위반: import 방향 확인 (상위 → 하위만 허용)
3. `mandu.config.ts`의 preset 확인

### HMR Not Working
1. Dev server 재시작: `Ctrl+C` → `bun run dev`
2. 포트 충돌: `lsof -i :3333` 또는 다른 포트 사용
3. `.mandu/` 캐시 삭제: `rm -rf .mandu/generated`

### Hydration Mismatch
1. 서버/클라이언트 렌더링 차이 확인
2. `Date.now()`, `Math.random()` 등 비결정적 값 제거
3. `useHydrated()` 훅으로 클라이언트 전용 코드 분기

## Verification

수정 후 반드시 검증:

```bash
bunx mandu guard arch --ci  # 아키텍처 검증
bunx tsc --noEmit            # 타입 검증
bun run dev                  # 런타임 검증
```

## MCP Tools for Debugging

| Tool | Purpose |
|------|---------|
| `mandu_brain_diagnose` | 증상 기반 자동 진단 |
| `mandu_guard` | 아키텍처 규칙 검사 |
| `mandu_guard_heal` | 위반 자동 수정 |
| `mandu_runtime_check` | 런타임 상태 점검 |
