# 🚀 AI Coding Brain MCP - Flow System

## 개요
AI Coding Brain MCP의 Flow 시스템은 프로젝트, 플랜, 태스크를 체계적으로 관리하는 
프로덕션 레벨의 워크플로우 관리 시스템입니다.

## ✨ 주요 기능

### 1. 플랜 관리
- 프로젝트별 플랜 생성 및 관리
- 플랜 상태 추적 (pending, active, completed)
- 플랜별 메타데이터 저장

### 2. 태스크 관리
- 플랜 내 태스크 생성/수정/삭제
- 태스크 상태 관리 (todo, in_progress, done)
- TaskLogger를 통한 자동 추적

### 3. 데이터 영속성
- JSON 기반 파일 저장
- Repository 패턴 구현
- 자동 백업 및 복구

## 📂 시스템 구조

```
python/ai_helpers_new/
├── flow_api.py              # 외부 인터페이스
├── ultra_simple_flow_manager.py  # 핵심 관리 엔진
├── flow_context.py          # 컨텍스트 관리
├── task_logger.py           # 태스크 로깅
├── repository/              # 데이터 저장
│   ├── ultra_simple_repository.py
│   └── enhanced_ultra_simple_repository.py
├── domain/                  # 도메인 모델
│   └── models.py           # Plan, Task, Phase
├── service/                 # 서비스 계층
│   └── lru_cache.py       # 캐싱
└── decorators/             # 데코레이터
    └── auto_record.py      # 자동 기록
```

## 🔧 사용법

### 기본 사용 예제

```python
import ai_helpers_new as h

# Flow API 초기화
api = h.flow_api()

# 플랜 생성
plan = api.create_plan(
    name="My Project",
    description="프로젝트 설명"
)

# 태스크 추가
task = api.create_task(
    plan_id=plan['data']['id'],
    name="첫 번째 태스크",
    description="태스크 설명"
)

# 태스크 상태 업데이트
api.update_task_status(
    plan_id=plan['data']['id'],
    task_id=task['data']['id'],
    status='in_progress'
)

# 플랜 조회
plan_detail = api.get_plan(plan['data']['id'])
```

## 📊 API 레퍼런스

### FlowAPI 클래스 메서드

| 메서드 | 설명 | 매개변수 |
|--------|------|----------|
| `create_plan(name, description)` | 새 플랜 생성 | name: str, description: str |
| `get_plan(plan_id)` | 플랜 조회 | plan_id: str |
| `list_plans()` | 모든 플랜 목록 | - |
| `create_task(plan_id, name, description)` | 태스크 생성 | plan_id: str, name: str, description: str |
| `update_task_status(plan_id, task_id, status)` | 태스크 상태 변경 | plan_id: str, task_id: str, status: str |
| `get_task(plan_id, task_id)` | 태스크 조회 | plan_id: str, task_id: str |

## 🎯 성능 지표

- 플랜 생성: < 50ms
- 태스크 생성: < 30ms  
- 상태 업데이트: < 20ms
- 대량 처리: 50 태스크/초

## 🔍 디버깅

TaskLogger가 자동으로 모든 작업을 기록합니다:
- 로그 위치: `.ai-brain/flow/logs/`
- 로그 레벨: INFO, DEBUG, ERROR

## 📈 모니터링

시스템 통계 확인:
```python
stats = api.get_stats()
# {'total_plans': 18, 'active_plans': 2, 'completed_plans': 5}
```

## 🚀 최적화 팁

1. **LRU 캐시 활용**: 자주 조회하는 플랜은 자동 캐싱
2. **배치 처리**: 대량 태스크는 batch 모드 사용
3. **비동기 처리**: async 메서드 활용 (준비 중)

## 📝 버전 히스토리

- v2.0.0 (2025-08-23): 프로덕션 레벨 완성
  - 완전한 태스크 관리 시스템
  - TaskLogger 통합
  - Repository 패턴 구현

- v1.0.0: 초기 버전

## 🤝 기여하기

이슈 및 PR은 GitHub에서 환영합니다.

## 📄 라이선스

MIT License

---
Created with ❤️ by AI Coding Brain Team
