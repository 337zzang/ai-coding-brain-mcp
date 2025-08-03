# Flow 시스템 모듈 분리 마이그레이션 가이드

## 📅 분리 일시
2025-08-03

## 🎯 목적
시니어 개발자의 분석에 따라 1,262줄의 거대한 `simple_flow_commands.py` 파일을 기능별로 분리하여 단일 책임 원칙(SRP)을 준수하고 유지보수성을 향상

## 📊 변경 내역

### Before (이전)
```
simple_flow_commands.py (1,262줄, 49KB)
└── 모든 기능이 하나의 파일에 혼재
```

### After (이후)
```
simple_flow_commands.py (65줄, 1.4KB) - 호환성 래퍼
├── flow_api.py (300줄) - 핵심 비즈니스 로직
├── flow_cli.py (150줄) - CLI 인터페이스  
├── flow_views.py (200줄) - 출력/포맷팅
└── flow_manager_utils.py (100줄) - Manager 유틸리티
```

## 🔄 마이그레이션 방법

### 1. 기존 코드 (변경 불필요)
```python
# 레거시 호환성이 유지되므로 기존 코드는 그대로 작동
from ai_helpers_new.simple_flow_commands import flow
result = flow("/status")
```

### 2. 권장 사항 (새 코드)
```python
# 직접 필요한 모듈만 import
from ai_helpers_new.flow_cli import flow
from ai_helpers_new.flow_api import FlowAPI

# API 직접 사용
api = FlowAPI(manager)
result = api.create_plan("새 계획")
```

## 📌 주요 변경사항

### FlowAPI 위치 변경
- 이전: `simple_flow_commands.FlowAPI`
- 이후: `flow_api.FlowAPI`

### CLI 함수 위치
- 이전: `simple_flow_commands.flow`
- 이후: `flow_cli.flow`

### View 함수 위치
- 이전: `simple_flow_commands.show_status`
- 이후: `flow_views.show_status`

## ⚠️ 주의사항

1. **Import 경로**: 새로운 모듈 구조를 사용할 때는 정확한 import 경로 사용
2. **응답 형식**: 모든 API 메서드는 `{'ok': bool, 'data': ...}` 형식 반환
3. **전역 변수**: 가능한 사용 지양, 세션 기반 관리 권장

## 🚀 향후 계획

1. **Phase 2**: Plan.tasks 데이터 모델 개선 (Dict → List/OrderedDict)
2. **Phase 3**: FlowAPI를 유일한 공개 인터페이스로 확립
3. **Phase 4**: 레거시 코드 및 전역 변수 완전 제거

## 📞 문의사항

문제 발생 시 다음 정보와 함께 보고:
- 사용 중인 import 문
- 발생한 오류 메시지
- 실행하려던 코드
