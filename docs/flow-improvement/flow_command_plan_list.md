# /flow 명령어 Plan 리스트 자동 표시 개선

## 개요
`/flow [프로젝트명]` 명령어 실행 시 자동으로 모든 Plan 리스트를 표시하도록 개선했습니다.

## 변경 전
- 프로젝트 전환 후 최신 Plan 하나만 표시
- 전체 Plan 목록을 보려면 추가 명령어 필요

## 변경 후
- 프로젝트 전환 시 모든 Plan 리스트 자동 표시
- 각 Plan의 상태를 직관적인 아이콘으로 표시
- Plan 선택 방법 안내 메시지 추가

## 구현 내용

### 1. Plan 리스트 표시 개선
```python
# 모든 Plan을 순회하며 표시
for i, plan in enumerate(self.current_flow['plans']):
    # Task 집계
    tasks = plan.get('tasks', [])
    total_tasks = len(tasks)
    completed_tasks = sum(1 for t in tasks if t.get('status') in ['completed', 'reviewing'])

    # 완료 상태 아이콘 결정
    if plan.get('completed', False):
        status_icon = "✅"  # Plan 완료됨
    elif total_tasks == 0:
        status_icon = "📋"  # Task가 없음
    elif completed_tasks == total_tasks and total_tasks > 0:
        status_icon = "🔄"  # 모든 Task 완료했지만 Plan은 미완료
    elif completed_tasks > 0:
        status_icon = "⏳"  # 진행중
    else:
        status_icon = "📝"  # 시작 전
```

### 2. 상태 아이콘 의미
- 📝 : 시작 전 (Task가 있지만 완료된 것이 없음)
- ⏳ : 진행중 (일부 Task가 완료됨)
- 🔄 : 모든 Task 완료 (Plan 완료 처리 필요)
- ✅ : Plan 완료됨
- 📋 : Task가 없음

### 3. 표시 정보
- Plan 번호 및 이름
- Plan ID
- Task 수 (전체/완료)
- 진행률 (퍼센트)
- Plan 설명

### 4. 사용자 안내
명령어 실행 후 하단에 Plan 선택 방법 안내:
```
💡 Plan을 선택하려면 번호를 입력하거나 'Plan 2 선택' 형식으로 입력해주세요.
   예: '2' 또는 'Plan 2 선택' 또는 '2번 Plan'
```

## 수정 파일
- `python/ai_helpers_new/flow_manager_unified.py`
  - `_switch_to_project()` 메서드의 Plan 표시 부분

## 효과
- 사용자가 한 번의 명령으로 프로젝트의 전체 상황 파악 가능
- Plan 진행 상황을 직관적으로 확인
- 다음 작업할 Plan을 쉽게 선택 가능

## 테스트
```bash
wf("/flow ai-coding-brain-mcp")
# 결과: 모든 Plan 리스트와 진행률이 표시됨
```

## 작성일
2025-07-22
