# 🚀 Flow 시스템 극단순화 상세 리팩토링 계획

## 📊 현재 상태 분석
- **총 파일 수**: 58개 Python 파일
- **총 폴더 수**: 16개 (pycache 제외 시 8개)
- **삭제 대상**: 3개 폴더 + 19개 파일
- **수정 대상**: 2개 파일
- **유지 대상**: 19개 파일

## 🎯 목표 구조
```
python/ai_helpers_new/
├── ultra_simple_flow_manager.py  # 메인 매니저
├── repository/
│   └── ultra_simple_repository.py  # 단순 저장소
├── domain/
│   └── models.py  # Plan, Task만 유지
├── service/
│   └── lru_cache.py  # 캐시 유틸리티
├── decorators/
│   ├── __init__.py
│   └── auto_record.py  # Context 자동 기록
└── [기타 헬퍼 파일들]
```

## 📝 실행 단계별 상세 계획

### 1️⃣ 백업 단계 (5분)
```bash
# 전체 백업
cp -r python/ai_helpers_new python/ai_helpers_new.backup.20250724_202345

# Git 커밋
git add .
git commit -m "backup: Flow 시스템 극단순화 전 백업"
```

### 2️⃣ 폴더 삭제 (2분)
- commands/ (5개 파일)
- presentation/ (6개 파일)  
- infrastructure/ (3개 파일)

### 3️⃣ Flow 관련 파일 삭제 (3분)
- flow_batch.py
- flow_context_wrapper.py
- flow_integration.py
- flow_manager.py
- flow_search.py
- folder_flow_manager.py
- simple_flow_manager.py
- workflow_commands.py
- migrate_flows.py
- migrate_to_folder_flow.py
- plan_auto_complete.py

### 4️⃣ Service 파일 삭제 (2분)
- service/cached_flow_service.py
- service/flow_service.py
- service/folder_based_flow_service.py
- service/plan_service.py
- service/task_service.py

### 5️⃣ Repository 파일 삭제 (2분)
- repository/folder_based_repository.py
- repository/simplified_repository.py
- repository/json_repository.py

### 6️⃣ __init__.py 수정 (5분)
Flow 관련 import 제거, ultra_simple만 export

### 7️⃣ models.py 수정 (5분)
Flow 클래스 제거, flow_id 필드 제거

## 📊 예상 결과
- **코드 감소**: 58개 → 20개 파일 (65% 감소)
- **폴더 구조**: 16개 → 4개 폴더 (75% 감소)
- **복잡도**: Flow/Plan/Task 3계층 → Plan/Task 2계층
