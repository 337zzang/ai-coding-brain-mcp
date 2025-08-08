# Execute_code 문제점 정리 및 해결 가이드 - 최종 요약

## 🎯 핵심 발견사항

### 1. Task Number 문제 (새로 발견)
- **문제**: 기존 Task들의 `number` 필드가 모두 `None`
- **원인**: 이전 버전에서 생성된 Task들은 number가 할당되지 않음
- **영향**: `get_task_by_number()` 메서드 사용 불가
- **해결**: 새로 생성되는 Task만 번호 할당됨

### 2. API 메서드 존재 여부
- ✅ **실제 존재**: 23개 메서드 확인 완료
- ❌ **존재하지 않음**: `show_status()`, `show_plans()` 등
- ⚠️ **체이닝 메서드**: `select_plan()`, `set_context()`, `clear_context()`

### 3. 데이터 구조 불일치
- **Task**: `title` 사용 (`name` 아님)
- **Git Status**: `files`, `count`, `branch`, `clean` 필드만 존재
- **표준 응답**: `{"ok": bool, "data": Any, "error": str}`

## 📋 빠른 참조 가이드

### FlowAPI 올바른 사용법
```python
# 초기화
api = h.get_flow_api()

# 일반 메서드 (표준 응답 확인)
result = api.create_plan("플랜명")
if result['ok']:
    plan = result['data']

# 체이닝 메서드 (반환값 무시)
api.select_plan(plan_id)  # FlowAPI 객체 반환
api.set_context('key', 'value')  # 체이닝 가능
```

### Task 작업 패턴
```python
# Task 생성
result = api.create_task(plan_id, "제목")
if result['ok']:
    task = result['data']
    print(task['title'])  # ✅ 올바름
    # print(task['name'])  # ❌ KeyError

# Task 상태 변경 (대소문자 무관)
api.update_task_status(plan_id, task_id, "DONE")  # ✅
api.update_task_status(plan_id, task_id, "done")  # ✅
api.update_task_status(plan_id, task_id, "completed")  # ✅ 별칭
```

### Git 상태 확인
```python
git = h.git_status()
if git['ok']:
    data = git['data']
    files = data['files']  # ✅ 변경 파일 목록
    # modified = data['modified']  # ❌ 없는 필드
```

## 🔴 주의사항

1. **Task Number**: 기존 Task는 number가 None일 수 있음
2. **체이닝 메서드**: 표준 응답 형식이 아님
3. **Git 파일 분류**: 'modified', 'added' 등 구분 없이 'files' 하나로 통합
4. **flow() 명령**: 초기화 필요 (또는 FlowAPI 직접 사용)

## ✅ 검증 완료
- 모든 문제 패턴 실제 코드로 확인
- 해결책 테스트 완료
- 문서와 실제 구현 일치 확인

## 📂 생성된 문서
1. `docs/troubleshooting/execute_code_issues.md` - 문제점 정리
2. `docs/guides/execute_code_troubleshooting_guide.md` - 해결 가이드
3. `docs/analysis/execute_code_error_statistics.md` - 통계 분석
4. `docs/analysis/execute_code_detailed_analysis.md` - 상세 분석 (이 문서)
