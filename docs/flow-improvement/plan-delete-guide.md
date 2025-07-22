# Plan 삭제 기능 사용 가이드

## 새로운 기능: Plan 삭제

### 명령어
```bash
/flow plan delete <plan_id>
```

### 기능 설명
- 지정된 Plan과 해당 Plan에 속한 모든 Task를 삭제합니다.
- 삭제 전 Context Manager에 백업이 저장됩니다.
- 완료된 Task가 있어도 삭제됩니다.

### 사용 예시
```bash
# Plan ID로 삭제
/flow plan delete plan_1753159856882495100_e08c5d

# 결과
{
  'ok': True,
  'data': {
    'plan_id': 'plan_1753159856882495100_e08c5d',
    'plan_name': 'Example Plan',
    'deleted_tasks': 5,
    'message': "Plan 'Example Plan' 및 5개의 Task가 삭제되었습니다."
  }
}
```

### 에러 처리
- 존재하지 않는 Plan ID를 입력하면 "Plan not found" 에러가 반환됩니다.
- Flow가 활성화되지 않은 경우 "No active flow" 에러가 반환됩니다.

### 안전 기능
1. **백업**: 삭제되는 Plan의 전체 내용이 Context Manager에 저장됩니다.
2. **이력 기록**: 삭제 작업이 history에 기록됩니다.
3. **Task 개수 표시**: 삭제되는 Task 개수를 미리 확인할 수 있습니다.
