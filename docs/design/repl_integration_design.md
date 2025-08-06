# JSON REPL Session 통합 설계

## 🎯 목표
json-repl-session.py에 TaskLogger, Subprocess Worker, 실행 히스토리 기능 통합

## 📋 통합 요구사항

### 1. TaskLogger 통합
- **목적**: 모든 REPL 실행을 Flow 시스템의 Task 로그에 자동 기록
- **구현 방법**:
  - execute_code() 시작 시 현재 Plan/Task 확인
  - EnhancedTaskLogger로 실행 내용 기록
  - 성공/실패 여부와 결과 저장

### 2. Subprocess Worker 통합  
- **목적**: Import 오염 방지를 위한 격리 실행
- **구현 방법**:
  - USE_SUBPROCESS_WORKER 환경변수 확인
  - True일 경우 repl_kernel.manager 사용
  - 실패 시 자동 fallback

### 3. 실행 히스토리
- **목적**: 디버깅과 분석을 위한 영구 기록
- **구현 방법**:
  - 각 실행을 JSONL 형식으로 저장
  - 실행 시간, 메모리 사용량 추적
  - 통계 및 패턴 분석 API 제공

## 🔧 구현 단계

### Phase 1: 기본 통합 (최소 변경)
1. execute_code()에 옵션 매개변수 추가
2. 환경변수 기반 조건부 활성화
3. 기존 동작에 영향 없도록 보수적 접근

### Phase 2: Flow 시스템 연동
1. 현재 Plan/Task 자동 감지
2. TaskLogger 자동 생성 및 관리
3. 실행 컨텍스트 메타데이터 추가

### Phase 3: 고급 기능
1. 실행 통계 대시보드
2. 패턴 분석 및 최적화 제안
3. 오류 자동 복구 메커니즘

## ⚠️ 주의사항
- 기존 안정성 유지 최우선
- 성능 오버헤드 최소화
- 점진적 롤아웃 가능하도록 설계
