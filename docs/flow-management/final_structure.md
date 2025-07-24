# 🎯 극단순화 후 최종 파일 구조

## 📁 최종 구조 (20개 파일)
```
python/ai_helpers_new/
├── __init__.py                    # ✏️ 수정: ultra_simple만 export
├── ultra_simple_flow_manager.py   # ✅ 유지: 메인 매니저
├── domain/
│   ├── __init__.py               # ✅ 유지
│   └── models.py                 # ✏️ 수정: Flow 제거, Plan/Task만
├── repository/
│   ├── __init__.py               # ✅ 유지
│   └── ultra_simple_repository.py # ✅ 유지: .ai-brain/flow/에 직접 저장
├── service/
│   ├── __init__.py               # ✅ 유지
│   └── lru_cache.py              # ✅ 유지: 캐시 유틸리티
├── decorators/
│   ├── __init__.py               # ✅ 유지
│   └── auto_record.py            # ✅ 유지: Context 자동 기록
├── file.py                       # ✅ 유지: 파일 헬퍼
├── code.py                       # ✅ 유지: 코드 헬퍼
├── search.py                     # ✅ 유지: 검색 헬퍼
├── git.py                        # ✅ 유지: Git 헬퍼
├── llm.py                        # ✅ 유지: LLM 헬퍼
├── util.py                       # ✅ 유지: 유틸리티
├── project.py                    # ✅ 유지: 프로젝트 관리
├── wrappers.py                   # ✅ 유지: 래퍼 함수
├── helpers_integration.py        # ✅ 유지
├── context_integration.py        # ✅ 유지
├── context_reporter.py           # ✅ 유지
├── doc_context_helper.py         # ✅ 유지
├── backup_utils.py               # ✅ 유지
├── error_messages.py             # ✅ 유지
└── exceptions.py                 # ✅ 유지
```

## 🗑️ 삭제된 구조 (38개 파일 + 3개 폴더)
```
❌ commands/ (폴더 전체)
❌ presentation/ (폴더 전체)
❌ infrastructure/ (폴더 전체)
❌ flow_*.py (8개 파일)
❌ migrate_*.py (2개 파일)
❌ workflow_commands.py
❌ plan_auto_complete.py
❌ service/*_service.py (5개 파일)
❌ repository/[기타].py (3개 파일)
```

## 💾 데이터 구조
```
프로젝트/
└── .ai-brain/
    └── flow/              # Flow 폴더만 있고
        ├── plan_001.json  # Plan 파일들이 직접 저장됨
        ├── plan_002.json
        └── plan_003.json
```
