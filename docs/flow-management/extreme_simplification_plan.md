# Flow 시스템 극단순화 리팩토링 계획

## 🎯 목표
- Flow 개념 완전 제거
- .ai-brain/flow/에 Plan JSON 파일들만 직접 저장
- 극도로 단순한 구조로 전환

## 📊 현재 상태
- 총 파일 수: 40개 이상의 Flow 관련 파일
- 삭제 대상: 25개 파일
- 수정 대상: 1개 파일 (models.py)
- 유지 대상: 2개 파일 (ultra_simple_*)

## 🚀 실행 단계

### 1단계: 백업 (5분)
```bash
# 전체 백업
cp -r python/ai_helpers_new python/ai_helpers_new.backup.20250724_201716

# Git 커밋
git add .
git commit -m "backup: Flow 시스템 리팩토링 전 백업"
```

### 2단계: 대량 삭제 (10분)

#### 2.1 FlowManager 삭제
```bash
rm python/ai_helpers_new/flow_manager.py
rm python/ai_helpers_new/folder_flow_manager.py
rm python/ai_helpers_new/simple_flow_manager.py
rm python/ai_helpers_new/flow_integration.py
```

#### 2.2 Service 삭제
```bash
rm python/ai_helpers_new/service/flow_service.py
rm python/ai_helpers_new/service/cached_flow_service.py
rm python/ai_helpers_new/service/folder_based_flow_service.py
rm python/ai_helpers_new/service/plan_service.py
rm python/ai_helpers_new/service/task_service.py
```

#### 2.3 Repository 삭제
```bash
rm python/ai_helpers_new/repository/folder_based_repository.py
rm python/ai_helpers_new/repository/simplified_repository.py
rm -rf python/ai_helpers_new/infrastructure
```

#### 2.4 유틸리티 삭제
```bash
rm python/ai_helpers_new/flow_*.py
rm python/ai_helpers_new/plan_auto_complete.py
rm python/ai_helpers_new/migrate_*.py
rm python/ai_helpers_new/workflow_commands.py
```

#### 2.5 Commands 폴더 삭제
```bash
rm -rf python/ai_helpers_new/commands
rm -rf python/ai_helpers_new/presentation
```

### 3단계: 파일 수정 (15분)

#### 3.1 models.py 수정
- Flow 클래스 완전 제거
- Flow 관련 import 제거
- Plan 클래스에서 flow_id 관련 제거

#### 3.2 __init__.py 수정
```python
from .ultra_simple_flow_manager import UltraSimpleFlowManager

# 기본 export
__all__ = ['UltraSimpleFlowManager', 'get_flow_manager']

def get_flow_manager(project_path=None):
    return UltraSimpleFlowManager(project_path)
```

### 4단계: 정리 및 검증 (10분)

#### 4.1 폴더 구조 확인
```
python/ai_helpers_new/
├── ultra_simple_flow_manager.py
├── repository/
│   └── ultra_simple_repository.py
├── domain/
│   └── models.py (수정됨)
├── service/
│   └── lru_cache.py
└── __init__.py (수정됨)
```

#### 4.2 import 테스트
```python
from ai_helpers_new import UltraSimpleFlowManager
manager = UltraSimpleFlowManager()
```

### 5단계: 문서화 (10분)
- README.md 작성
- 마이그레이션 가이드 작성

## ⏱️ 예상 소요 시간: 약 50분

## ⚠️ 주의사항
1. 백업 필수
2. 다른 프로젝트에서 사용 중일 수 있음
3. 테스트 코드도 함께 정리 필요

## 🎯 최종 결과
- 40개 → 5개 파일로 축소
- 극도로 단순한 구조
- Plan 중심의 작업 관리
