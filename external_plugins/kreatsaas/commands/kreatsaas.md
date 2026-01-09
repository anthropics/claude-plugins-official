---
name: kreatsaas
description: SaaS 빌더 가이드 - 디자인부터 배포까지 단계별 안내
arguments:
  - name: phase
    description: 실행할 단계 (design, architecture, develop, deploy)
    required: false
---

# KreatSaaS - SaaS 빌더 가이드

초보자도 독창적이고 프로덕션 수준의 SaaS를 만들 수 있도록 안내합니다.

## 실행 방법

사용자가 `/kreatsaas`를 실행하면:

1. **언어 선택**: 첫 실행 시 한글/영어 선택
2. **Discovery**: SaaS 아이디어와 타겟 사용자 파악
3. **Design**: saas-designer 에이전트로 디자인 방향 결정
4. **Architecture**: saas-architect 에이전트로 기술 설계
5. **Development**: saas-developer 에이전트로 코드 생성
6. **Deployment**: saas-deployer 에이전트로 배포 가이드

## 단계별 실행

특정 단계만 실행하려면:
- `/kreatsaas design` - 디자인 단계만
- `/kreatsaas architecture` - 아키텍처 단계만
- `/kreatsaas develop` - 개발 단계만
- `/kreatsaas deploy` - 배포 단계만

## 가이드 스킬

초보자를 위한 가이드:
- `/kreatsaas beginner` - SaaS 개념 설명 (SaaS란?, 프론트엔드/백엔드/API 등)
- `/kreatsaas setup` - 설치 가이드 (Node.js, VS Code, Git, 계정 생성)
- `/kreatsaas enhance` - 수정/고도화 가이드 (기능 추가, 성능 개선, 스케일링)

## LLM 관리 커맨드

- `/update-llm` - LLM 모델/가격 최신 업데이트
- `/upgrade-models scan` - 소스 코드에서 구버전 모델 스캔
- `/upgrade-models auto` - 모든 모델 자동 업그레이드
- `/upgrade-models select` - 하나씩 선택하며 업그레이드

## 버전 및 기능 관리

- `/version show` - 현재 버전 표시
- `/version history` - 변경 이력 보기
- `/version bump <type>` - 버전 업데이트 (major/minor/patch)
- `/request-feature add` - 새 기능 요청
- `/request-feature list` - 요청된 기능 목록
- `/request-feature implement` - 기능 구현

## 워크플로우

### Phase 1: Discovery (발견)

사용자에게 다음을 질문:
- 어떤 SaaS를 만들고 싶은가요?
- 타겟 사용자는 누구인가요?
- 핵심 기능은 무엇인가요?
- 비즈니스 모델은? (구독, 프리미엄, 광고 등)

### Phase 2: Design Thinking (디자인 사고)

saas-designer 에이전트 실행:
- 10가지 미적 방향 중 선택
- Purpose, Tone, Constraints, Differentiation 정의

### Phase 3: UI/UX Design (UI/UX 디자인)

saas-designer 에이전트 계속:
- 컬러 팔레트 결정
- 타이포그래피 선택
- 레이아웃 설계
- 주요 화면 와이어프레임

### Phase 4: Architecture (아키텍처)

saas-architect 에이전트 실행:
- 기술 스택 선택 (프론트엔드, 백엔드, DB)
- DB 스키마 설계
- API 엔드포인트 설계
- 3가지 구현 방식 제안

사용자 선택 옵션:
- 결제 시스템: Stripe / 토스페이먼츠 / 포트원 / Paddle / 없음
- 서버리스: Vercel Edge / Cloudflare Workers / AWS Lambda / Firebase
- 데이터베이스: Supabase / PlanetScale / Turso / MongoDB / Cloudflare D1 / IndexedDB / SQLite
- 이미지 스토리지: Cloudflare R2 / Supabase Storage / Cloudinary / AWS S3 / ImageKit / Uploadthing
- LLM 텍스트: OpenAI GPT-4o / Claude Sonnet / Gemini 2.5 / Groq / DeepSeek / Together AI / Mistral / Perplexity
- AI 이미지: DALL-E 3 / Nano Banana Pro / Stable Diffusion 3.5 / Flux
- AI 영상: Veo 3.1 / Sora / Runway Gen-3 / Kling
- AI 음성: Whisper / Deepgram / ElevenLabs / OpenAI TTS / Vapi

### Phase 5: Development (개발)

saas-developer 에이전트 실행:
- 프로젝트 초기화
- 컴포넌트별 코드 생성
- 단계별 설명과 함께 진행

### Phase 6: Quality Review (품질 검토)

코드 품질 검증:
- 린트 및 타입 체크
- 보안 취약점 검사
- 성능 최적화 제안

### Phase 7: Deployment (배포)

saas-deployer 에이전트 실행:
- 배포 플랫폼 선택 (Vercel, Railway, AWS 등)
- 환경 변수 설정
- CI/CD 파이프라인 구성
- 도메인 연결 가이드

### Phase 8: Enhancement (고도화) - 선택

enhancement-guide 스킬 활용:
- 코드 수정 방법
- 새 기능 추가 방법
- 디자인 변경 (색상, 레이아웃, 다크모드, 애니메이션)
- 성능 개선 (이미지 최적화, 코드 분할, 캐싱)
- 확장 (스케일링) - Redis, CDN, 백그라운드 작업
- 보안 강화 - Rate Limiting, 입력 검증
- 유지보수 - 의존성 업데이트, 모니터링, 백업
