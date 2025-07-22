# Plan 선택 기능 구현 가이드

## 구현 완료: Plan 선택 기능

### 개요
FlowManagerUnified에 "Plan X 선택" 형식의 명령어를 지원하는 기능을 추가했습니다.

### 구현 내용

1. **process_command 메서드 수정**
   - "/" 없이도 Plan 선택 가능
   - 다양한 형식 지원: "6", "Plan 6", "Plan 6 선택", "6번 Plan"

2. **_handle_plan_select 메서드 추가**
   - Plan 번호로 선택
   - 현재 flow의 plans 리스트에서 조회

3. **_analyze_plan_context 메서드 추가**
   - 완료된 Task 분석
   - 미완료 Task 표시
   - 다음 단계 권장사항 제공

### 사용법

```bash
# Flow의 Plan 목록 확인
/flow ai-coding-brain-mcp

# Plan 선택 (다양한 형식 지원)
6
Plan 6
Plan 6 선택
6번 Plan
```

### 테스트 결과
- 모든 형식에서 정상 작동
- Plan의 Task 정보 정확히 분석
- v30.0 사양에 맞는 출력 형식

### 주의사항
- FlowManagerUnified는 plans를 current_flow['plans'] 리스트로 관리
- self.plans (dict)는 비어있음 (레거시 구조)
