# JSON REPL Session 통합 구현 계획

## 🎯 구현 목표
O3 분석을 기반으로 json-repl-session.py에 3가지 기능 통합

## 📋 구현 순서

### Phase 1: 기본 준비 (환경변수 및 import)
1. 필요한 모듈 import 추가
   - `from ai_helpers_new.task_logger import EnhancedTaskLogger`
   - `from repl_kernel.manager import WorkerManager`

2. 환경변수 처리 로직 추가
   ```python
   USE_SUBPROCESS_WORKER = os.getenv('USE_SUBPROCESS_WORKER', '0') == '1'
   FLOW_PLAN_ID = os.getenv('FLOW_PLAN_ID', 'local')
   FLOW_TASK_ID = os.getenv('FLOW_TASK_ID', 'adhoc')
   ```

### Phase 2: TaskLogger 초기화
1. 모듈 레벨에서 TaskLogger 인스턴스 생성
2. Flow 시스템과 자동 연동되도록 설정

### Phase 3: execute_code() 함수 수정
1. 실행 전 스냅샷 (변수, imports)
2. 조건부 실행 경로 (local vs worker)
3. 실행 후 diff 계산
4. TaskLogger로 기록
5. debug_info에 추가 정보 포함

### Phase 4: 테스트 및 검증
1. 기본 동작 테스트 (worker 비활성화)
2. Worker 모드 테스트
3. TaskLogger 기록 확인
4. 오류 복구 테스트

## ⚠️ 주의사항
- 기존 API 호환성 유지
- 성능 영향 최소화
- 점진적 롤아웃 가능하도록 설계
