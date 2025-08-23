# 📊 execute_code의 Flow 시스템 완벽 가이드

## 🎯 개요

Flow 시스템은 AI Coding Brain MCP의 핵심 워크플로우 관리 시스템으로, `execute_code` 도구와 완전히 통합되어 프로젝트 관리, 작업 추적, 상태 유지를 자동화합니다.

## 🏗️ 시스템 아키텍처

```
execute_code (MCP Tool)
        ↓
Python REPL Session (영속적)
        ↓
ai_helpers_new (Facade Pattern)
        ↓
FlowAPI (비즈니스 로직)
        ↓
UltraSimpleFlowManager (데이터 관리)
        ↓
EnhancedRepository (영속성 계층)
        ↓
.ai-brain/flow/ (파일 시스템)
```

## 📁 파일 시스템 구조

```
.ai-brain/flow/
├── plans/              # Plan JSON 파일들
│   ├── project1.json
│   ├── project2.json
│   └── ...
├── logs/               # Task 실행 로그
│   ├── task_001.log
│   ├── task_002.log
│   └── ...
├── workflow.json       # 현재 워크플로우 상태
└── context.json        # 프로젝트 컨텍스트
```

## 🔧 핵심 API

### 1. FlowAPI 주요 메서드

```python
import ai_helpers_new as h

# Flow API 인스턴스
api = h.flow_api()

# Plan 관리
api.create_plan(name, description)    # 새 프로젝트 계획 생성
api.list_plans()                      # 모든 계획 목록
api.get_plan(plan_id)                 # 특정 계획 정보
api.update_plan(plan_id, **updates)   # 계획 업데이트
api.delete_plan(plan_id)              # 계획 삭제

# Task 관리
api.create_task(plan_id, title)       # 새 작업 생성
api.update_task(task_id, **updates)   # 작업 상태 변경
api.complete_task(task_id)            # 작업 완료
api.list_tasks(plan_id)               # 작업 목록
api.get_task(task_id)                 # 특정 작업 정보

# 통계 및 상태
api.get_stats()                       # 전체 통계
api.get_current_plan()                # 현재 활성 계획
api.get_context()                     # 컨텍스트 조회
api.update_context(key, value)        # 컨텍스트 업데이트
```

### 2. 데이터 모델

#### Plan (프로젝트 계획)
```python
{
    "id": "dashboard_20250823",
    "name": "dashboard_project",
    "tasks": {},
    "metadata": {
        "description": "웹 대시보드 개발",
        "created_at": "2025-08-23T10:00:00",
        "updated_at": "2025-08-23T10:30:00"
    },
    "status": "active"
}
```

#### Task (작업)
```python
{
    "id": "task_uuid",
    "title": "API 개발",
    "status": "todo",  # todo | in_progress | completed
    "number": 1,
    "created_at": "2025-08-23T10:00:00",
    "priority": "normal"
}
```

## 🔄 자동 통합 메커니즘

### execute_code와 Flow 연동

1. **자동 컨텍스트 감지**
   - execute_code 실행 시 현재 프로젝트 자동 확인
   - 활성 Plan/Task 자동 감지

2. **실행 기록 자동화**
   - 모든 코드 실행이 Task 로그에 기록
   - 파일 작업이 자동으로 추적됨

3. **상태 동기화**
   - Task 진행률 자동 업데이트
   - workflow.json에 실시간 반영

4. **영속성 보장**
   - 세션 간 상태 유지
   - 중단된 작업 자동 복원

## 💡 실전 활용 예제

### 예제 1: 새 프로젝트 시작

```python
import ai_helpers_new as h

# Flow API 초기화
api = h.flow_api()

# 1. 새 프로젝트 Plan 생성
result = api.create_plan(
    name="ecommerce_site",
    description="전자상거래 웹사이트 개발"
)
plan_id = result['data']['id']

# 2. Task들 추가
tasks = [
    "요구사항 분석",
    "데이터베이스 설계",
    "백엔드 API 개발",
    "프론트엔드 구현",
    "테스트 및 배포"
]

for task_name in tasks:
    api.create_task(plan_id, task_name)

# 3. 현재 상태 확인
stats = api.get_stats()
print(f"총 Tasks: {stats['data']['total_tasks']}개")
```

### 예제 2: 작업 진행 관리

```python
# 1. 첫 번째 Task 시작
tasks = api.list_tasks(plan_id)['data']
first_task = tasks[0]

# 2. 상태를 'in_progress'로 변경
api.update_task(first_task['id'], status='in_progress')

# 3. 실제 작업 수행 (자동으로 Flow에 기록됨)
h.file.write('requirements.md', '# 프로젝트 요구사항...')

# 4. Task 완료
api.complete_task(first_task['id'])
```

### 예제 3: 프로젝트 전환

```python
# 다른 프로젝트로 전환
h.flow_project("other_project")

# 새 컨텍스트에서 작업
api = h.flow_api()
current = api.get_current_plan()
print(f"현재 프로젝트: {current['data']['name']}")
```

### 예제 4: 컨텍스트 관리

```python
# 프로젝트 상태 저장
api.update_context("environment", "production")
api.update_context("version", "1.0.0")
api.update_context("last_deployment", datetime.now().isoformat())

# 컨텍스트 조회
context = api.get_context()
print(f"환경: {context['data'].get('environment')}")
```

## 🚀 베스트 프랙티스

### 1. 프로젝트 구조화
- 명확한 Plan 이름 사용
- Task를 논리적 단위로 분할
- 우선순위 설정 활용

### 2. 자동화 활용
- execute_code로 모든 작업 수행
- Flow가 자동으로 추적하도록 허용
- 수동 상태 업데이트 최소화

### 3. 컨텍스트 관리
- 중요한 상태는 컨텍스트에 저장
- 세션 간 연속성 확보
- 정기적 백업 활용

### 4. 모니터링
- get_stats()로 정기적 확인
- 완료율 추적
- 병목 지점 식별

## 🎯 Flow 시스템의 이점

### 1. **완전 자동화**
- 수동 프로젝트 관리 불필요
- 모든 작업 자동 추적
- 실시간 상태 업데이트

### 2. **영속성 보장**
- 세션 간 상태 유지
- 중단 후 자동 복원
- 데이터 손실 방지

### 3. **통합 워크플로우**
- execute_code와 완벽 통합
- 단일 인터페이스
- 일관된 작업 경험

### 4. **확장 가능성**
- 플러그인 아키텍처
- 커스텀 워크플로우 지원
- API 확장 가능

## 📌 문제 해결

### Flow 저장소가 없을 때
```python
# .ai-brain/flow 디렉토리 자동 생성
api = h.flow_api()
api.create_plan("initial", "초기 프로젝트")
```

### Plan이 없을 때
```python
# 기본 Plan 생성
plans = api.list_plans()
if not plans['data']:
    api.create_plan("default", "기본 프로젝트")
```

### 컨텍스트 복원
```python
# 이전 세션 컨텍스트 복원
context = api.get_context()
if context['ok']:
    # 컨텍스트 기반 작업 재개
    pass
```

## 🔮 미래 계획

- [ ] 웹 대시보드 UI
- [ ] 실시간 협업 기능
- [ ] AI 기반 작업 추천
- [ ] 자동 리포트 생성
- [ ] GitHub/GitLab 통합

## 📚 참고 자료

- FlowAPI 소스: `python/ai_helpers_new/flow_api.py`
- Manager 구현: `python/ai_helpers_new/ultra_simple_flow_manager.py`
- Repository: `python/ai_helpers_new/repository/`
- 도메인 모델: `python/ai_helpers_new/domain/models.py`

---

*이 문서는 AI Coding Brain MCP v4.2.0 기준으로 작성되었습니다.*
*최종 업데이트: 2025-08-23*