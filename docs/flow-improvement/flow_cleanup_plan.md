# Flow 시스템 정리 계획

## 🎯 목표
- 5단계 → 3단계로 호출 체인 단순화
- 중복 파일 제거 (16개 → 6개)
- 명확한 아키텍처 구조

## 📋 정리 순서

### Phase 1: 백업 및 테스트 준비 (안전장치)
```bash
# 1. 전체 백업
tar -czf flow_backup_$(date +%Y%m%d).tar.gz python/ai_helpers_new/

# 2. 현재 상태 테스트
/flow ai-coding-brain-mcp
/plan add "테스트 플랜"
/task add "테스트 태스크"
```

### Phase 2: 중복 파일 제거
삭제할 파일들:
1. `flow_command_integration.py` - flow_command_router.py로 대체됨
2. `flow_command_integration_updated.py` - flow_command_router.py로 대체됨  
3. `flow_manager_unified.py` - 단순 래퍼, 불필요
4. `unified_flow_manager.py` - 사용 안 함
5. `service/flow_service.py` - cached_flow_service.py와 중복
6. `flow_system_adapter.py` - 사용 안 함
7. `presentation/flow_commands.py` - 사용 안 함

### Phase 3: LegacyFlowAdapter 제거
1. workflow_wrapper.py 수정:
```python
# 기존
flow_manager = FlowManager(context_enabled=True)
adapter = LegacyFlowAdapter(flow_manager)
_manager = FlowCommandRouter(adapter)

# 변경
flow_manager = FlowManager(context_enabled=True)
_manager = FlowCommandRouter(flow_manager)
```

2. FlowCommandRouter 수정:
- `self.manager` 타입을 LegacyFlowAdapter → FlowManager로 변경
- 메서드 호출 조정

### Phase 4: 구조 정리

#### 최종 파일 구조
```
workflow_wrapper.py          # 진입점 (wf 함수)
flow_command_router.py       # 명령어 라우팅
flow_manager.py             # 비즈니스 로직
service/
  cached_flow_service.py    # 캐싱 + 서비스
infrastructure/
  flow_repository.py        # JSON 저장소
domain/
  models.py                 # Flow, Plan, Task 모델
```

#### 최종 호출 체인
```
wf() → FlowCommandRouter → FlowManager → CachedFlowService
```

### Phase 5: 테스트 및 검증
1. 모든 명령어 테스트:
   - `/flow`, `/flows`
   - `/plan add`, `/plans`
   - `/task add`, `/tasks`
   - `/status`

2. 데이터 무결성 확인:
   - .ai-brain/flows.json 정상 동작
   - 기존 Flow/Plan/Task 유지

3. Context 시스템 연동 확인

## ⚠️ 주의사항

1. **import 수정 필요**
   - `from .flow_manager_unified import FlowManagerUnified` 사용하는 곳 찾기
   - `__init__.py`의 export 목록 수정

2. **하위 호환성**
   - 외부에서 FlowManagerUnified를 직접 import하는 경우 대비
   - 임시로 alias 유지 후 점진적 제거

3. **Git 관리**
   - 각 Phase별로 커밋
   - 문제 발생 시 롤백 가능하도록

## 📊 예상 결과

### Before
- 파일 수: 16개
- 코드 라인: ~4,000줄
- 호출 체인: 5단계
- 중복 코드: 70%

### After  
- 파일 수: 6개 (-62%)
- 코드 라인: ~2,000줄 (-50%)
- 호출 체인: 3단계 (-40%)
- 중복 코드: 최소화

## 🚀 실행 명령어

```bash
# Phase 1: 백업
python -c "import shutil; shutil.copytree('python/ai_helpers_new', 'backup/flow_backup_20250723')"

# Phase 2: 중복 파일 제거
rm python/ai_helpers_new/flow_command_integration.py
rm python/ai_helpers_new/flow_command_integration_updated.py
# ... (나머지 파일들)

# Phase 3-4: 코드 수정
# (수동으로 진행)

# Phase 5: 테스트
python -m pytest tests/test_flow_system.py
```