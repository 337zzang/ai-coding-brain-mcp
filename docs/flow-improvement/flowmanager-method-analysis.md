# FlowManagerUnified 메서드 분석 보고서

## 1. 개요
FlowManagerUnified 클래스의 Plan/Task 관리 메서드들을 상세 분석하여 현재 시스템의 문제점과 개선 방안을 도출했습니다.

## 2. 클래스 구조 분석

### 2.1 메서드 인벤토리
- **Plan 관련 메서드**: 11개
  - create_plan, update_plan_status, complete_plan
  - _add_plan, _list_plans, _handle_plan_command
  - _complete_plan, _reopen_plan, _show_plan_status
  - _check_plan_auto_complete, _handle_plan_subcommand

- **Task 관련 메서드**: 13개  
  - create_task, update_task_status, update_task_context
  - add_task_action, update_task_status_validated
  - _add_task, _list_tasks, _start_task, _complete_task
  - _skip_task, _handle_task_command, _handle_task_subcommand
  - _validate_task_transition

- **Flow 관련 메서드**: 15개
  - create_flow, delete_flow, switch_flow, list_flows
  - get_current_flow_status, _create_default_flow
  - _create_flow, _delete_flow, _switch_flow, _list_flows
  - _load_flows, _save_flows, _save_current_flow_id
  - _handle_flow_command, _export_flow_data

### 2.2 데이터 구조
```json
{
  "flow": {
    "id": "flow_xxx",
    "name": "project_name",
    "plans": [
      {
        "id": "plan_xxx",
        "name": "plan_name",
        "tasks": [
          {
            "id": "task_xxx",
            "name": "task_name",
            "status": "todo|in_progress|completed",
            "context": {}
          }
        ]
      }
    ]
  }
}
```

## 3. 발견된 문제점

### 3.1 주요 문제
1. **Task 추가 명령어 실패**
   - `/flow task add` 명령어가 실제로 Task를 저장하지 않음
   - create_task 메서드는 정상 작동하나, 명령어 처리 체인에 문제

2. **Plan 삭제 기능 부재**
   - `/flow plan delete` 명령어 미구현
   - delete_plan() 메서드 없음

3. **Task 삭제 기능 부재**
   - delete_task() 메서드 없음
   - Task 삭제 명령어 없음

4. **데이터 일관성 문제**
   - 모든 메서드가 Plan 내부의 tasks를 사용 (일관성은 있음)
   - 하지만 일부 오래된 코드나 주석에 Flow 레벨 tasks 참조 존재

### 3.2 호출 체인 문제
```
/flow task add 명령어 처리 흐름:
1. handle_workflow_command() - "flow" 명령어로 인식
2. _handle_flow_command() - "task" 부분 처리 누락
3. Task가 추가되지 않음

정상적인 흐름 (수정 필요):
1. handle_workflow_command() - "task" 명령어로 인식
2. _handle_task_command() - "add" 액션 처리
3. _add_task() - create_task() 호출
4. 성공적으로 저장
```

## 4. 수정 필요 사항

### 4.1 즉시 수정 필요
1. **handle_workflow_command 수정**
   - `/flow task add` 명령어 파싱 로직 수정
   - task 명령어를 올바르게 라우팅

2. **delete_plan 메서드 구현**
   ```python
   def delete_plan(self, plan_id: str) -> Dict[str, Any]:
       # Plan 삭제 로직
   ```

3. **delete_task 메서드 구현**
   ```python
   def delete_task(self, task_id: str) -> Dict[str, Any]:
       # Task 삭제 로직
   ```

### 4.2 개선 사항
1. **명령어 파서 개선**
   - 더 명확한 명령어 구조
   - 에러 메시지 개선

2. **데이터 검증 강화**
   - Plan/Task ID 유효성 검사
   - 중복 방지 로직

3. **테스트 케이스 추가**
   - 모든 CRUD 작업 테스트
   - 명령어 파싱 테스트

## 5. 결론
FlowManagerUnified 클래스는 전반적으로 잘 설계되어 있으나, 명령어 처리 체인에 버그가 있어 일부 기능이 작동하지 않습니다. 특히 `/flow task add` 명령어 처리와 Plan/Task 삭제 기능이 누락되어 있어 즉시 수정이 필요합니다.
