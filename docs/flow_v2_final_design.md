# Flow Project v2 최종 설계 문서
생성일: 2025-07-21
작성자: Claude + o3 분석

## 🎯 개요
Flow Project v2를 기존 시스템에 통합하는 최종 설계입니다.
o3의 심층 분석을 바탕으로 "어댑터 패턴"을 사용하여 최소한의 변경으로 최대의 효과를 달성합니다.

## 📋 핵심 원칙
1. **Zero Breaking Change**: 기존 코드 영향 없음
2. **어댑터 패턴**: 교체가 아닌 확장
3. **환경변수 제어**: FLOW_V2_ENABLE로 즉시 전환
4. **점진적 마이그레이션**: 단계별 전환 가능

## 🏗️ 구조

### 현재 구조
```
python/
├── workflow_wrapper.py      # wf() 함수 정의
├── ai_helpers_new/
│   ├── __init__.py
│   └── workflow_manager.py  # WorkflowManager 클래스
flow_project_v2/
└── flow_manager_integrated.py  # FlowManagerWithContext (미사용)
```

### 목표 구조
```
python/
├── workflow_wrapper.py      # 수정 없음 (이미 확장 가능)
├── ai_helpers_new/
│   ├── __init__.py
│   ├── workflow_manager.py  # 5줄 추가로 v2 활성화
│   └── flow_v2_adapter.py  # 신규 어댑터 (30-40줄)
```

## 📝 구현 상세

### 1. flow_v2_adapter.py (신규)
```python
import os
from flow_project_v2.flow_manager_integrated import FlowManagerWithContext

class V2WorkflowAdapter:
    def __init__(self):
        self.flow_manager = FlowManagerWithContext()
        self._load_existing_data()

    def wf_command(self, command, verbose=False):
        # /flow 명령어 처리
        if command.startswith('/flow'):
            return self._handle_flow_command(command)

        # 기존 명령어 처리
        return self._handle_legacy_command(command)

    def _handle_flow_command(self, command):
        # Flow v2 명령어 라우팅
        parts = command.split()
        subcommand = parts[1] if len(parts) > 1 else 'help'

        handlers = {
            'list': self.flow_manager.list_flows,
            'create': lambda: self.flow_manager.create_flow(' '.join(parts[2:])),
            'switch': lambda: self.flow_manager.switch_flow(parts[2]),
            'status': self.flow_manager.get_current_flow_status,
        }

        handler = handlers.get(subcommand)
        if handler:
            return {'ok': True, 'data': handler()}
        return {'ok': False, 'error': f'Unknown command: {subcommand}'}

    # 기존 API 호환 메서드들
    def add_task(self, name, description=''):
        return self.flow_manager.create_task(name, description)

    def list_tasks(self):
        return self.flow_manager.list_tasks()

    # ... 나머지 호환 메서드들
```

### 2. workflow_manager.py 수정 (5줄)
파일 끝에 추가:
```python
# Flow v2 활성화
if os.environ.get('FLOW_V2_ENABLE', '1') == '1':
    from .flow_v2_adapter import V2WorkflowAdapter
    WorkflowManager = V2WorkflowAdapter
```

### 3. 환경 설정
```bash
export FLOW_V2_ENABLE=1    # v2 활성화
export CONTEXT_SYSTEM=on   # Context 시스템 활성화
```

## 🧪 테스트 계획

### Phase 1: 기본 호환성 (10분)
- 기존 명령어 동작 확인
- API 메서드 호출 테스트

### Phase 2: Flow 기능 (20분)
- /flow list, create, switch 테스트
- 다중 프로젝트 전환 테스트

### Phase 3: 통합 테스트 (20분)
- Context 시스템과 통합
- 전체 워크플로우 시나리오

## 📊 예상 결과

### 성공 지표
- ✅ 기존 기능 100% 유지
- ✅ Flow 명령어 정상 작동
- ✅ Context 시스템 통합
- ✅ 성능 저하 없음

### 실패 시 대응
- FLOW_V2_ENABLE=0으로 즉시 복구
- 어댑터만 수정하여 문제 해결
- 기존 시스템 영향 없음

## 🚀 구현 일정
- 10:30 - 어댑터 클래스 작성
- 10:45 - WorkflowManager 수정
- 10:50 - 기본 테스트
- 11:00 - Flow 기능 테스트
- 11:20 - 통합 테스트
- 11:30 - 문서화 완료

## 📌 주의사항
1. 반드시 새 브랜치에서 작업
2. 각 단계별로 Git 커밋
3. 테스트 실패 시 즉시 중단
4. 프로덕션 적용 전 충분한 검증

---
이 설계는 o3의 심층 분석과 실제 코드 분석을 바탕으로 작성되었습니다.
