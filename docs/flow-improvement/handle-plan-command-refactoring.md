# _handle_plan_command 리팩토링 보고서

## 수행한 작업

### 1. 중복 메서드 통합
- _handle_plan_subcommand와 _handle_plan_command 두 개의 메서드가 존재
- _handle_plan_subcommand 제거하고 _handle_plan_command로 통일
- handle_workflow_command의 라우팅 수정

### 2. 코드 구조 개선
- 메서드 docstring 업데이트
- 각 명령어 처리 부분에 주석 추가
- 에러 메시지 형식 통일

### 3. 버그 수정
- delete 명령어 처리 시 args → plan_args 변경
- 에러 메시지 수정

## 남은 이슈

### 명령어 파싱 문제
현재 `/flow plan delete <plan_id>` 명령어 처리 시:
- handle_workflow_command에서 cmd='plan', args='delete <plan_id>'로 파싱
- _handle_plan_command에서 subcmd='delete', plan_args='<plan_id>'로 재파싱 필요
- 하지만 현재는 전체 args를 plan_id로 사용하려고 함

### 해결 방안
1. _handle_plan_command의 delete 처리 부분에서 plan_args 파싱 수정
2. 또는 handle_workflow_command 레벨에서 더 정확한 파싱

## 개선 효과
- 코드 중복 제거로 유지보수성 향상
- 명령어 처리 로직 일원화
- 더 명확한 코드 구조
