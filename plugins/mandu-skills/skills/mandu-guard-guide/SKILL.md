---
name: mandu-guard-guide
description: |
  Guard 아키텍처 가이드. 위반 수정/프리셋 선택/레이어 규칙. guard violation 시 자동 호출
---

# Mandu Guard Guide

Mandu Guard 아키텍처 강제 시스템의 상세 가이드.
6개 프리셋, 위반 유형별 수정 방법, 레이어 규칙을 다룹니다.

## 6 Presets

### mandu (default)
FSD + Clean Architecture 하이브리드. 프론트엔드와 백엔드 모두 커버.
```typescript
// mandu.config.ts
export default { guard: { preset: "mandu" } };
```

### fsd (Feature-Sliced Design)
프론트엔드 전용. 7계층 레이어 구조.
```
app > pages > widgets > features > entities > shared
```

### clean (Clean Architecture)
백엔드 전용. 의존성 역전 원칙.
```
api > application > domain > infra > core > shared
```

### hexagonal (Ports & Adapters)
포트와 어댑터 패턴. domain이 중심, adapters가 외부 의존성 처리.
```
adapters > ports > application > domain
```

### atomic (Atomic Design)
UI 컴포넌트 전용. atoms -> molecules -> organisms -> templates -> pages.

### cqrs (Command Query Responsibility Segregation)
명령과 조회를 분리. command, query, event, dto 전용 구조.

## Violation Types and Fixes

### LAYER_VIOLATION (error)
상위 레이어가 하위 레이어를 import하는 것만 허용.

```typescript
// BAD: shared가 features를 import (하위 -> 상위)
// src/shared/utils/helper.ts
import { useAuth } from "@/features/auth"; // VIOLATION

// FIX: 의존 방향 반전, 또는 shared에 인터페이스 정의
// src/shared/types/auth.ts
export interface AuthContext { userId: string; }
```

### FORBIDDEN_IMPORT (error)
클라이언트 코드에서 서버 전용 모듈 import 금지.

```typescript
// BAD: island에서 fs import
// app/editor.island.tsx
import fs from "fs"; // VIOLATION

// FIX: 서버 로직은 slot으로 분리
// spec/slots/editor.slot.ts
import fs from "fs"; // OK (server-only)
```

### WRONG_SLOT_LOCATION (warning)
Slot 파일이 잘못된 위치에 있음.

```
BAD:  src/server/slots/user.slot.ts
FIX:  spec/slots/user.slot.ts
```

### GENERATED_DIRECT_EDIT (error)
자동 생성된 파일을 직접 수정하면 안 됨.

```
BAD:  .mandu/generated/server/routes.ts 직접 편집
FIX:  소스 파일을 수정하고 regenerate
```

### CONTRACT_MISSING (warning)
API route에 대응하는 contract가 없음.

```
Missing: src/shared/contracts/user.contract.ts
For:     app/api/users/route.ts
FIX:     contract 파일 생성
```

### SLOT_NAMING (warning)
Slot 파일명이 규칙에 맞지 않음.

```
BAD:  spec/slots/userData.ts
FIX:  spec/slots/user-data.slot.ts
```

## CLI Commands

```bash
# 전체 아키텍처 검사
bunx mandu guard arch

# 특정 프리셋으로 검사
bunx mandu guard arch --preset fsd

# CI 모드 (위반 시 exit 1)
bunx mandu guard arch --ci

# Watch 모드
bunx mandu guard arch --watch

# 단일 파일 검사
bunx mandu guard check-file src/client/features/auth.ts
```

## Configuration

```typescript
// mandu.config.ts
export default {
  guard: {
    preset: "mandu",
    rules: {
      LAYER_VIOLATION: "error",     // "error" | "warning" | "off"
      FORBIDDEN_IMPORT: "error",
      WRONG_SLOT_LOCATION: "warning",
      CONTRACT_MISSING: "off",
      GENERATED_DIRECT_EDIT: "error",
      SLOT_NAMING: "warning",
    }
  }
};
```

## MCP Tools

| Tool | Purpose |
|------|---------|
| `mandu_guard` | Run architecture check |
| `mandu_guard_heal` | Auto-fix violations |
| `mandu_negotiate` | Analyze with preset awareness |
