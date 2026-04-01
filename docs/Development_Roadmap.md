# QJC-OS 스타일 고도화 개발 계획서

본 계획서는 `AutonomousCompanyMVP`를 캡처 이미지 수준의 전문적인 자율 운영 시스템으로 진화시키기 위한 단계별 가이드입니다.

## Phase 1: 프론트엔드 UI/UX 전면 개편 (The Visualizer)
- **목표**: 분석 보고서에 명시된 다크 테마 및 카드 레이아웃 구현.
- **주요 작업**:
  - `web/monitoring/index.html`을 최신 대시보드 스타일로 교체.
  - Tailwind CSS를 활용한 글래스모피즘 UI 적용.
  - KPI 대시보드(사용자, 세션, 도구 사용량) 위젯 구현.
  - 좌측 사이드바 및 탭 전환 시스템 구축.

## Phase 2: 에이전트 & 파이프라인 아키텍처 고도화 (The Brain)
- **목표**: 기획-실행-검증 분리(GAN 패턴) 및 부서별 에이전트 체계 구축.
- **주요 작업**:
  - `src/agentic/` 내에 `Planner`, `Generator`, `Evaluator` 클래스 고도화.
  - 부서별(Trading, Marketing, Compliance 등) 특화 에이전트 정의 및 연동.
  - `configs/pipelines/`를 통한 업무 시퀀스 정의 엔진 개발.

## Phase 3: 가드레일 및 보안 후크 시스템 (The Shield)
- **목표**: Hooks와 Rules를 통한 물리적 차단 및 안전성 확보.
- **주요 작업**:
  - `src/ops/security_hooks.py` 구현 (파일 접근, 명령어 실행 필터링).
  - `configs/rules/` 시스템 구축 (업무 준수 지침 JSON/MD 관리).
  - AI 편향 교정 가이드 주입 시스템 개발.

## Phase 4: 데이터 분석 및 시각화 엔진 (The Analytics)
- **목표**: 실시간 활동 및 도구 사용량 통계 자동 수집 및 차트화.
- **주요 작업**:
  - `db/schema.sql`에 도구 사용 로그 및 세션 통계 테이블 보강.
  - Chart.js 또는 D3.js를 연동하여 실시간 활동 지표 가시화.
  - 에이전트 오피스 맵(부서별 배치도) 구현.

## Phase 5: 자율 운영 통합 및 안정화 (The Integration)
- **목표**: 모든 시스템의 유기적 결합 및 자가 치유 기능 강화.
- **주요 작업**:
  - 피드백 루프 자동화 (에러 시 Evaluator가 즉시 Generator에게 수정 요청).
  - 최종 500개 시나리오 기반 스트레스 테스트 및 안정성 검증.
