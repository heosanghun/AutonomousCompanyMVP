# AutonomousCompanyMVP Complete Manual

## 1. Executive Overview

AutonomousCompanyMVP is a self-operating trading company framework built around:

- Revenue engine: automated trading
- Control engine: risk gates, operational readiness, and auditability
- MLOps/AIOps backbone: data quality pipeline, monitoring, alerts, and fail-closed checks

The system is designed to maximize operational safety first, then scale autonomy.

## 2. Architecture

### 2.1 Core runtime

- `src/system1/*`: fast execution (signal -> action)
- `src/system2/*`: slow planning (policy updates)
- `src/runtime/engine.py`: orchestration layer
- `src/interface/*`: FiLM + PolicyBuffer bridge

### 2.2 Trading execution

- `src/execution/order_router.py`: order creation and lineage fields
- `src/execution/broker.py`: paper/live split with guarded live path
- `src/execution/binance_adapter.py`: signed Binance order path

### 2.3 MLOps/AIOps

- `src/mlops/data_pipeline.py`: ingest/quality/features/registry
- `scripts/run_mlops_data_pipeline.py`: pipeline runner
- `scripts/monitoring_server.py`: browser and API status
- `src/ops/alerts.py`: webhook alert integration
- `src/ops/reconcile.py`: execution artifact reconcile checks

## 3. Safety and Governance Model

### 3.1 Fail-closed production policy

Production profile defaults to `strict`.

- Required for strict readiness:
  - compliance docs
  - readiness bundle
  - live readiness flag
  - human approval artifact (`outputs/human_live_approval.json`)
  - exchange credential verification
  - MLOps pipeline success artifact
  - reconcile success

### 3.2 Profiles

- `FULL_OPS_PROFILE=strict` (default): no operational shortcuts
- `FULL_OPS_PROFILE=lab`: controlled waivers for sandbox experiments only

## 4. Lineage and Audit Fields

Every order/fill now carries operational lineage:

- `model_version`
- `feature_version`
- `policy_version`
- `input_snapshot_hash`
- `decision_id`, `strategy_id`

This improves replayability and post-incident forensics.

## 5. Risk Controls

Risk limits are now loaded from `configs/operational_limits.json` and mapped into runtime guard:

- max daily loss threshold
- max position/leverage cap
- volatility breaker
- external kill-switch support (`external_kill_switch.flag`)

## 6. Operational Commands

### 6.1 Core flow

```bash
python scripts/run_mlops_data_pipeline.py
python -m src.main
python scripts/verify_production_readiness.py
python scripts/verify_full_operational_gate.py
```

### 6.2 Human approval template

```bash
python scripts/create_human_live_approval_template.py
```

Then fill `outputs/human_live_approval.json` with real approval identity before strict live readiness.

### 6.3 Monitoring

```bash
python scripts/monitoring_server.py
```

Open:

- `http://127.0.0.1:8787`
- `http://127.0.0.1:8787/api/status`

## 7. CI and Quality Gates

GitHub Actions workflow (`.github/workflows/ci.yml`) executes:

- syntax checks
- unit tests
- MLOps pipeline smoke
- runtime smoke

## 8. Remaining Work (Real-world external dependencies)

The following still require external real-world execution:

- legal/tax professional sign-off with legal effect
- long-horizon live trading validation with real capital

These are intentionally **not** auto-completed by code in strict profile.

## 9. Design Principle

Autonomy expands gradually; control starts strict.

Production trust is earned through:

- measurable data quality
- reproducible lineage
- fail-closed readiness
- explicit human accountability

---

## [한글 번역] AutonomousCompanyMVP 완전 매뉴얼

## 1. 경영진 개요

AutonomousCompanyMVP는 다음 축을 중심으로 구성된 자율 운영 트레이딩 회사 프레임워크입니다.

- 수익 엔진: 자동매매
- 통제 엔진: 리스크 게이트, 운영 준비도, 감사 가능성
- MLOps/AIOps 백본: 데이터 품질 파이프라인, 모니터링, 알림, fail-closed 점검

이 시스템은 먼저 운영 안전성을 극대화하고, 그 다음 자율성을 점진적으로 확장하도록 설계되었습니다.

## 2. 아키텍처

### 2.1 코어 런타임

- `src/system1/*`: 고속 실행 루프 (신호 -> 액션)
- `src/system2/*`: 저속 계획 루프 (정책 업데이트)
- `src/runtime/engine.py`: 오케스트레이션 계층
- `src/interface/*`: FiLM + PolicyBuffer 브리지

### 2.2 트레이딩 실행

- `src/execution/order_router.py`: 주문 생성 및 계보(lineage) 필드 관리
- `src/execution/broker.py`: paper/live 분리 및 보호된 live 경로
- `src/execution/binance_adapter.py`: Binance 서명 주문 경로

### 2.3 MLOps/AIOps

- `src/mlops/data_pipeline.py`: 수집/품질/피처/레지스트리
- `scripts/run_mlops_data_pipeline.py`: 파이프라인 실행기
- `scripts/monitoring_server.py`: 브라우저 및 API 상태 모니터링
- `src/ops/alerts.py`: 웹훅 알림 연동
- `src/ops/reconcile.py`: 실행 산출물 정합성(reconcile) 점검

## 3. 안전 및 거버넌스 모델

### 3.1 Fail-closed 운영 정책

운영 프로파일 기본값은 `strict`입니다.

- strict 준비도 통과에 필요한 항목:
  - 컴플라이언스 문서
  - readiness 번들
  - live readiness 플래그
  - 사람 승인 산출물 (`outputs/human_live_approval.json`)
  - 거래소 자격증명 검증
  - MLOps 파이프라인 성공 산출물
  - 정합성(reconcile) 성공

### 3.2 프로파일

- `FULL_OPS_PROFILE=strict` (기본값): 운영상 지름길 허용 없음
- `FULL_OPS_PROFILE=lab`: 샌드박스 실험에 한해 통제된 예외 허용

## 4. 계보(Lineage) 및 감사 필드

이제 모든 주문/체결에는 다음 운영 계보 정보가 포함됩니다.

- `model_version`
- `feature_version`
- `policy_version`
- `input_snapshot_hash`
- `decision_id`, `strategy_id`

이를 통해 재현 가능성(replayability)과 사고 후 포렌식 능력이 향상됩니다.

## 5. 리스크 통제

리스크 한도는 `configs/operational_limits.json`에서 로드되어 런타임 가드에 매핑됩니다.

- 일 손실 한도
- 포지션/레버리지 상한
- 변동성 브레이커
- 외부 킬스위치 지원 (`external_kill_switch.flag`)

## 6. 운영 명령

### 6.1 코어 실행 흐름

```bash
python scripts/run_mlops_data_pipeline.py
python -m src.main
python scripts/verify_production_readiness.py
python scripts/verify_full_operational_gate.py
```

### 6.2 사람 승인 템플릿

```bash
python scripts/create_human_live_approval_template.py
```

그 다음 strict live readiness 이전에 `outputs/human_live_approval.json`에 실제 승인자 정보를 입력합니다.

### 6.3 모니터링

```bash
python scripts/monitoring_server.py
```

접속 주소:

- `http://127.0.0.1:8787`
- `http://127.0.0.1:8787/api/status`

## 7. CI 및 품질 게이트

GitHub Actions 워크플로(`.github/workflows/ci.yml`)는 다음을 수행합니다.

- 문법 점검
- 단위 테스트
- MLOps 파이프라인 스모크 테스트
- 런타임 스모크 테스트

## 8. 남은 작업 (현실 세계 외부 의존)

다음 항목은 외부 현실 실행이 여전히 필요합니다.

- 법적 효력이 있는 법무/세무 전문가 승인
- 실제 자본을 투입한 장기 라이브 트레이딩 검증

이 항목들은 strict 프로파일에서 코드로 자동 완료되지 않도록 의도적으로 분리되어 있습니다.

## 9. 설계 원칙

자율성은 점진적으로 확장하고, 통제는 엄격하게 시작합니다.

운영 신뢰는 다음을 통해 확보됩니다.

- 측정 가능한 데이터 품질
- 재현 가능한 계보(lineage)
- fail-closed 준비도
- 명시적인 인간 책임성
