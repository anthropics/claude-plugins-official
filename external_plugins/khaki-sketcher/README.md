<h1 align="center">KhakiSketcher</h1>

<p align="center">
  <strong>확실한 개발을 위한 Cross-model 오케스트레이터</strong><br>
  Sonnet이 구현하고, Codex가 검증하고, Gemini가 확인한다.<br>
  <strong>Reliable development through cross-model verification.</strong>
</p>

<p align="center">
  <a href="https://github.com/KhakiSkech/KhakiSketcher/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="MIT License"></a>
  <img src="https://img.shields.io/badge/Claude%20Code-plugin-purple.svg" alt="Claude Code Plugin">
  <img src="https://img.shields.io/badge/context-~800_tokens-green.svg" alt="Low overhead">
  <img src="https://img.shields.io/badge/zero_dependencies-zero_build-brightgreen.svg" alt="Zero deps">
  <img src="https://img.shields.io/badge/skills-8-blue.svg" alt="8 Skills">
</p>

---

## KhakiSketcher가 해결하는 문제

**단일 모델의 근본적 한계.**

Sonnet은 훌륭한 구현 모델이지만, 혼자서는 해결할 수 없는 문제가 있습니다:

| 한계 | 이유 | KhakiSketcher의 해결 |
|------|------|---------------------|
| 복잡한 논리 오류 | 자신의 논리를 스스로 검증하기 어려움 | **Codex**가 독립적으로 분석 (1M context) |
| 시각적 품질 | 텍스트 모델이라 스크린샷을 볼 수 없음 | **Gemini**가 pixel 단위 QA (1M context) |
| 회귀 위험 | 자신이 작성한 코드를 객관적으로 평가하기 어려움 | **Codex**가 PASS/FAIL 판정 |
| 계획의 맹점 | 단일 시각으로는 놓치는 게 생김 | **Codex + Gemini 교차 검증**으로 보완 |

**핵심 철학**: 자동화가 아닙니다. **교차 검증(Cross-validation)** 입니다.

각 모델이 **강한 것만** 하도록 엄격하게 분리합니다:

| 모델 | 역할 | 하는 일 | 하지 않는 일 |
|------|------|---------|-------------|
| **Claude Sonnet** | 구현 + 오케스트레이션 | 모든 코드 작성, 테스트, 커밋 | — |
| **Codex CLI** | Deep reasoning | 분석, 리뷰, 디버깅, 계획 | 코드 수정 절대 불가 |
| **Gemini CLI** | Vision 분석 | 디자인, UX QA, 스크린샷 분석 | 코드 수정 절대 불가 |

---

## 핵심 워크플로우: Think → Design → Build → Verify

```
Task
  ↓
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  Think   │───▶│  Design  │───▶│  Build   │───▶│  Verify  │
│ (Codex)  │    │ (Gemini) │    │ (Sonnet) │    │(C+G 둘 다)│
└──────────┘    └──────────┘    └──────────┘    └──────────┘
  분석+계획       UI 전용          코드 구현        독립 검증
  artifact 저장   artifact 저장                    artifact 저장
```

### Step 1: Think — Codex (1M context)

복잡한 작업인 경우 Codex가 **최고 effort**로 분석합니다:

- 아키텍처 분석 (결합도, 응집도, 의존성)
- 버그 근본원인 분석 (5-Whys 방법론)
- 구현 계획 수립 (단계별, 독립 검증 가능)
- 위험 평가 (회귀 가능성, 영향 범위)

산출물은 `.ksk/artifact/`에 저장, **Sonnet은 요약(~500자)만 읽고 구현**에 사용합니다.

### Step 2: Design — Gemini (1M context) — UI 작업인 경우에만

UI/시각적 변경이 필요한 경우:

- 디자인 토큰 (색상, 타이포그래피, 간격, border-radius)
- 컴포넌트 패턴 (레이아웃, 계층 구조)
- UX 분석 (사용자 흐름, 정보 계층, 시각적 가독성)
- 접근성 (WCAG 2.1 AA, 터치 타겟, 포커스 표시)

코드는 "정확"해도 UX가 이상할 수 있습니다. Gemini가 **코드가 맞는지가 아니라 화면이 맞는지** 검증합니다.

### Step 3: Build — Sonnet

Think 요약 + Design 요약 기반으로 **Sonnet이 모든 코드를 직접 작성**합니다.
Codex와 Gemini는 절대 코드를 수정하지 않습니다.

### Step 4: Verify — Codex + Gemini

**편향 없는 독립 검증.** Verify 프롬프트에는 이전 분석 결과를 포함하지 않습니다:
오직 diff와 소스 코드만 제공하여, 신선한 눈으로 리뷰합니다.

- Codex: 로직, 성능, 보안, 회귀 위험 검증 → **PASS / FAIL 판정**
- Gemini (UI인 경우): 시각 품질, UX, 접근성 → **0-100점 평가**

FAIL → 수정 후 Step 3으로 복귀 (최대 3회 반복).

---

## 컨텍스트 브릿징: Artifact 시스템

모델 간 컨텍스트 윈도우 차이(Codex 1M, Gemini 1M, Sonnet 256K)를 **파일 기반 artifact**로 해결합니다:

```
.ksk/artifact/                    ← 프로젝트별 (글로벌 아님)
  think-20260402-1430.md          ← Codex 분석 결과
  design-20260402-1435.md         ← Gemini 디자인 스펙
  debug-20260402-1440.md          ← Codex RCA 결과
  plan-20260402-1500.md           ← 교차 검증된 최종 계획
  review-20260402-1510.md         ← Codex 리뷰 판정
  visual-qa-20260402-1515.md      ← Gemini 시각 QA 결과
```

**핵심 원칙**: 외부 모델 산출물은 항상 파일에 저장하고, **Sonnet은 요약만 읽습니다.**
이렇게 하면 Codex의 1M 컨텍스트 분석이 Sonnet의 256K 컨텍스트를 압도하지 않습니다.

---

## 실제 사용 시나리오

### 1. 교차 검증 계획 — `/ksk:plan`

```
👤 "인증 시스템 설계해줘"
👤 "Plan the authentication system"

Phase 1: Codex → 아키텍처 분석 (의존성, 보안, 단계별 구현 계획)
Phase 2: Gemini → UX 분석 (사용자 흐름, 접근성, 화면 설계)
Phase 3: 교차 검증
  - Codex가 Gemini의 UX 계획 검토 (기술적 가능성)
  - Gemini가 Codex의 구현 계획 검토 (UX 블라인드스팟)
Phase 4: 통합 계획서 → .ksk/artifact/plan-<ts>.md 저장

→ 한 번에 완성된 계획. 재계획 불필요.
→ 이후 Sonnet이 계획서 기반으로 전체 구현 완료
```

### 2. 복잡한 버그 — `/ksk:complex-debug`

```
👤 "프로덕션에서 간헐적으로 에러 나"

Think: Codex 5-Whys 분석 → 근본원인 도출 → artifact 저장
Build: Sonnet이 근본원인 기반 최소 수정 + 재현 테스트 작성
Verify: Codex 회귀 리뷰 → PASS/FAIL 판정
  FAIL → 수정 후 재검증 (max 3회)
```

### 3. 아키텍처 리팩터링 — `/ksk:architecture`

```
👤 "이 모듈 구조 리팩터해줘"

Think: Codex 결합도/응집도 분석 + 마이그레이션 전략
Build: Sonnet이 의존성 순서대로 단계별 구현 (각 단계 테스트)
Verify: Codex 아키텍처 리뷰 → PASS/FAIL
```

### 4. UI 구현 — `/ksk:ui-redesign`

```
👤 "이 목업대로 페이지 만들어줘"

Design: Gemini → 디자인 토큰 + 컴포넌트 패턴 + UX 분석
Build: Sonnet → 스펙 기반 UI 구현
Verify: Gemini → 85점 이상 시 통과, 미만 시 수정 후 재검증
```

### 5. 코드 리뷰 — `/ksk:code-review`

```
👤 "이 PR 리뷰해줘"

Think: Codex → 로직/보안/성능/컨벤션/회귀 검사
Verdict: PASS / FAIL_MINOR / FAIL_MAJOR / FAIL_CRITICAL
  FAIL_MINOR → Sonnet self-fix 후 재리뷰
  FAIL_MAJOR → 사용자에게 에스컬레이션
  FAIL_CRITICAL → 즉시 중단
```

### 6. 일반 구현 — 외부 모델 불필요

```
👤 "버튼 색깔 바꿔줘"
👤 "로그인 페이지 만들어줘"

→ Sonnet이 직접 구현 → 완료 (Codex/Gemini 개입 없음)
```

---

## Skill 목록 (8개)

| Skill | 역할 | 외부 모델 | 언제 사용? |
|-------|------|-----------|-----------|
| `/ksk:plan` | **교차 검증 계획** | Codex + Gemini | 복잡한 기능 설계, 프로젝트 초기 계획 |
| `/ksk:run` | 범용 진입점 | 상황에 따라 | 뭐 해야 할지 모를 때 |
| `/ksk:complex-debug` | 디버깅 | Codex | 크래시, race condition, 간헐적 버그 |
| `/ksk:architecture` | 아키텍처 | Codex | 리팩터링, 모듈 재구성, 마이그레이션 |
| `/ksk:ui-redesign` | UI 구현 | Gemini | 목업 구현, 디자인 변경 |
| `/ksk:visual-qa` | 시각 QA | Gemini | Before/After 비교, pixel-level 검증 |
| `/ksk:code-review` | 코드 리뷰 | Codex | PR 리뷰, 품질 검증 |
| `/ksk:test` | 테스트 | Codex (복잡한 실패 시) | 테스트 작성, 커버리지 분석 |

모든 Skill은 **에러 핸들링 + Verify 격리**를 포함합니다:
- CLI 실패 시 자동 fallback (Codex ↔ Gemini)
- Verify 프롬프트에 이전 분석 포함 금지 (편향 방지)
- 두 CLI 모두 불가 시 Sonnet이 직접 처리

---

## Agent 목록 (3개)

| Agent | 역할 | 언제 사용? |
|-------|------|-----------|
| `architect` | 아키텍처 분석 (Read-only) | Codex 호출 필요 시 sub-agent로 위임 |
| `debugger` | 근본원인 분석 (Read-only) | 5-Whys 분석 필요 시 |
| `vision-analyst` | 시각 분석 (Read-only) | Gemini 호출 필요 시 |

**Agent vs Skill**: Skill은 `/ksk:xxx`로 직접 호출하는 주 워크플로우. Agent는 Sonnet이 병렬 분석이 필요할 때 sub-agent로 위임하는 선택적 도구.

---

## 자연어 라우팅

한국어/영어 자연어로 요청하면 Sonnet이 의도를 파악하여 적절한 Skill로 라우팅합니다:

| 사용자 요청 | 라우팅 |
|-------------|--------|
| "계획 세워줘" / "설계해줘" / "plan" | `/ksk:plan` |
| "에러나" / "crash" / "bug" | 간단 → 직접 수정 / 복잡 → `/ksk:complex-debug` |
| "리팩터해줘" / "refactor" | `/ksk:architecture` |
| "목업대로" / "UI looks off" | `/ksk:ui-redesign` |
| "비교해봐" / "before/after" | `/ksk:visual-qa` |
| "리뷰해줘" / "review" | `/ksk:code-review` |
| "만들어줘" / "implement" | Sonnet 직접 처리 |
| "테스트" / "test" | `/ksk:test` |
| 판단 안 설 때 | `/ksk:run` (자동 분류) |

---

## 설치

### 사전 요구사항

- [Claude Code](https://claude.ai/code) CLI (필수)
- [Codex CLI](https://github.com/openai/codex) (선택 — reasoning용)
- [Gemini CLI](https://github.com/google-gemini/gemini-cli) (선택 — vision용)

### 플러그인 설치

```bash
claude plugin install https://github.com/KhakiSkech/KhakiSketcher
```

빌드 없음. npm install 없음. 마크다운 + 셸 스크립트만으로 동작합니다.

### 세션 시작 시 자동 감지

KhakiSketcher는 세션 시작 시 설치된 CLI를 자동 감지합니다:

| 설치 상태 | 동작 |
|-----------|------|
| Codex + Gemini 모두 | 전체 기능 (교차 검증 + 시각 QA) |
| Codex만 | reasoning 가능, vision은 text-only fallback |
| Gemini만 | vision 가능, reasoning은 Gemini가 대체 |
| 둘 다 없음 | Sonnet만으로 동작 (외부 검증 없음, 여전히 작동함) |

---

## 아키텍처

```
KhakiSketcher/
  CLAUDE.md                    라우팅 정책 (~800 토큰, 항상 로드)
  .claude-plugin/plugin.json   플러그인 메타데이터 (v0.2.1)
  hooks/hooks.json             2개 훅
  agents/                      3개 Agent 정의 (선택적 sub-agent)
  skills/                      8개 Skill 워크플로우
  scripts/
    session-init.mjs           CLI 감지 + 정책 주입 + artifact 디렉토리 생성
    security-guard.mjs         위험 명령 차단 + 민감 파일 감시
    run.cjs                    훅 실행기 (ESM shim)
```

### 파일 로딩 전략

| 파일 | 로딩 시점 | 컨텍스트 비용 |
|------|-----------|--------------|
| `CLAUDE.md` | 세션 시작 시 항상 | ~800 토큰 |
| `skills/*/SKILL.md` | `/ksk:xxx` 호출 시에만 | 호출 시에만 |
| `agents/*.md` | Agent 위임 시에만 | 위임 시에만 |
| `hooks/*` | 자동 (Claude Code 관리) | 0 (시스템 훅) |
| `.ksk/artifact/*` | 필요 시 Sonnet이 Read | 읽을 때만 |

### 설계 원칙

| 원칙 | 설명 |
|------|------|
| **CLI-native** | Skill이 `codex exec` / `gemini -p`를 Bash로 직접 호출. MCP Layer 없음 |
| **Zero build** | TypeScript 없음, 번들링 없음. 마크다운 + 셸 스크립트만 |
| **Minimal context** | 무조건 로드 ~800 토큰. 나머지는 필요 시에만 |
| **Model-agnostic** | 모델명 하드코딩 없음. CLI가 최신 모델을 자동 사용 |
| **Graceful degradation** | CLI 미설치 / rate limit → 자동 fallback, 크래시 없음 |
| **Verify isolation** | 검증 프롬프트에 이전 분석 포함 금지. 편향 없는 독립 리뷰 |

### 왜 MCP를 사용하지 않는가

v0.1.0에서는 8개 MCP 도구가 `codex exec` / `gemini -p`를 감싸는 래퍼 역할을 했습니다:

| 항목 | v0.1.0 (MCP) | v0.2.1 (CLI-native) |
|------|-------------|---------------------|
| MCP 도구 | 8개 (~625 토큰) | **0개** |
| 무조건 로드 | ~3,045 토큰 | **~800 토큰** |
| 빌드 산출물 | 784KB 번들 + esbuild | **없음** |
| 런타임 의존성 | npm packages | **없음** |
| TypeScript | 필수 | **불필요** |

MCP 도구 8개의 실체는 CLI 호출을 감싼 래퍼였습니다. Skill이 Bash로 직접 호출하면 MCP 전체가 불필요합니다.

---

## About KhakiSketch

[KhakiSketch](https://khakisketch.co.kr/) — 청주의 2인 개발 스튜디오. CS 전공자 두 명이 Next.js, React, TypeScript, Python, FastAPI, PostgreSQL, Flutter, Supabase로 스타트업 MVP, 비즈니스 자동화, 프로덕션 앱을 만듭니다.

KhakiSketcher는 우리의 일상적인 개발 경험에서 탄생했습니다:
- **교차 검증**은 실제 프로덕션 인시던트에서 "Sonnet이 놓친 것을 Codex가 발견"한 경험에서
- **Verify 격리**는 "이전 분석을 알고 있으면 편향된 리뷰"를 관찰한 경험에서
- **Artifact 시스템**은 "Codex의 1M 분석 결과를 Sonnet의 256K에 어떻게 전달할까"를 해결하면서
- **`/ksk:plan`**은 "단일 모델의 계획은 항상 맹점이 있다"는 깨달음에서

---

## License

[MIT](LICENSE)

<p align="center">
  <a href="https://khakisketch.co.kr/">khakisketch.co.kr</a> · <a href="https://github.com/KhakiSkech">GitHub</a>
</p>
