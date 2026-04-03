# KhakiSketcher — Model Policy & Routing

## Workflow: Think → Design → Build → Verify

```
Task → Think(Analyze) → Design(Spec) → Build(Implement) → Verify(Review)
```

### Step 1. Think — Codex (1M context)
사용자의 요청이 **기술적 복잡도가 높은 작업**인 경우:
1. Sonnet이 컨텍스트 수집 (에러 로그, 스택트레이스, 관련 소스)
2. Sonnet → `codex exec "분석"` → Codex가 분석 + 구현 계획 수립 → `.ksk/artifact/` 파일에 저장
3. Sonnet이 구현 계획 요약(~500자)만 읽고 구현에 사용

### Step 2. Design — Gemini (1M context) — UI 작업인 경우에만
사용자의 요청에 **UI/시각적 변경**이 필요한 경우:
1. Sonnet이 UI/비주얼 컨텍스트 수집 (스크린샷, 참고 이미지)
2. Sonnet → `gemini -p @image "디자인 스펙 생성"`
   - 디자인 토큰 (색상, 타이포그래피, 간격, 라운드)
   - 컴포넌트 패턴
   - UX 분석: 사용자 흐름, 정보 계층, 시각적 가독성
3. 결과물을 `.ksk/artifact/` 파일에 저장
4. Sonnet이 디자인 스펙 요약(~500자)만 읽고 구현에 사용

### Step 3. Build — Sonnet (256K~)
Codex의 구현 계획 + 디자인 스펙 기반으로 구현
- Sonnet이 모든 코드를 직접 작성
- 파일에서 필요한 부분만 Read로 참조

### Step 4. Verify — Codex + Gemini
1. Sonnet → `codex exec "리뷰"` (로직/성능/보안 검증)
   - 결과물을 `.ksk/artifact/` 파일에 저장
2. Sonnet이 판정 결과 요약(~200자)을 읽고 다음 작업:
   - PASS → 완료
   - FAIL → 수정 후 Step 3으로 복귀 (최대 3회)

UI 작업인 경우 추가:
- Sonnet → `gemini -p @result.png "UX/시각 QA"` → Gemini가 시각 + UX 품질 평가 (0-100점)

## Model Roles
| Role | Engine | Output | Notes |
|------|--------|--------|-------|
| **Think** | `codex exec` | 분석 보고서, 구현 계획, 위험 평가 | 컨텍스트 1M, 산출물 컴팩트 → 파일 저장 |
| **Design** | `gemini -p @image` | 디자인 스펙, UX 분석 | 컨텍스트 1M, 산출물 컴팩트 → 파일 저장 |
| **Build** | Sonnet (or GLM) | 코드, 테스트, 커밋 | 256K~, 직접 구현 |
| **Verify** | Codex + Gemini | 검증 판정 | 컴팩트 요약 → 사용자에게 보고 |

## When to Use External Models

- **Think**: 아키텍처, 복잡한 버그, 코드 리뷰, 성능 분석
- **Design**: UI 작업, 화면 변경, mockup 구현, 프론트엔드 개선
- **Verify**: 모든 구현 후 품질 확인

## Routing Guide

| User Intent | Route |
|-------------|-------|
| Plan/계획/설계 | `/ksk:plan` (Codex+Gemini 교차 검증 계획) |
| Debug/crash/error | Simple → fix directly. Complex → `/ksk:complex-debug` |
| Architecture/refactor | `/ksk:architecture` |
| UI/design/mockup | `/ksk:ui-redesign` |
| Visual compare/QA | `/ksk:visual-qa` |
| Code review | `/ksk:code-review` |
| Implement/add | Sonnet directly (디자인 필요 시 Gemini Design 먼저) |
| Test | `/ksk:test` |
| Unsure | `/ksk:run` |

## Agent vs Skill

| | Skill | Agent |
|--|-------|-------|
| 호출 | `/ksk:xxx`로 직접 호출 | Sonnet이 판단하여 sub-agent로 위임 |
| 용도 | 주 워크플로우 | 병렬 분석이 필요할 때 |
| 코드 수정 | Skill 내에서 Sonnet이 수행 | Agent는 읽기 전용, 결과만 반환 |

## Rules
- Sonnet = TEXT-ONLY. 이미지 분석은 반드시 `gemini -p @image.png "prompt"`
- 외부 모델 산출물은 항상 `.ksk/artifact/` 파일에 저장 후 요약만 읽고 구현
- 구현 완료 후 항상 Verify 단계 포함
- Verify FAIL → 수정 후 최대 3회 반복
