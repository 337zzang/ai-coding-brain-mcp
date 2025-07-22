
# Plan 관리 시스템 문제 분석 보고서

## 🚨 발견된 주요 문제점

### 1. Task 저장 구조 불일치
- **문제**: create_task는 Plan 내부의 tasks 리스트에 저장 (`plan['tasks']`)
- **현상**: 다른 메서드들은 Flow 레벨의 tasks를 찾음 (`flow['tasks']`)
- **결과**: Task가 추가되어도 0개로 표시됨

### 2. 데이터 구조 혼란
```
현재 구조:
flow = {
    'id': 'flow_xxx',
    'name': 'project_name',
    'plans': [
        {
            'id': 'plan_xxx',
            'name': 'plan_name',
            'tasks': [...]  # <- create_task가 여기에 저장
        }
    ],
    # 'tasks': [] <- 이 레벨에는 없음
}
```

### 3. Plan 삭제 기능 부재
- `/flow plan delete` 명령어 미구현
- delete_plan() 메서드 없음

### 4. Task 표시 로직 문제
- Task 개수 계산 시 잘못된 위치에서 검색
- Plan별 Task 집계 로직 오류

## 📋 수정 계획

### 단계 1: 데이터 구조 일관성 확보
- Flow와 Plan의 관계 명확화
- Task 저장 위치 통일

### 단계 2: 누락된 기능 구현
- delete_plan() 메서드 추가
- Plan 삭제 명령어 구현

### 단계 3: Task 표시 로직 수정
- 올바른 위치에서 Task 검색
- Plan별 Task 개수 정확히 표시

### 단계 4: 테스트 및 검증
- 모든 Plan/Task 관리 기능 테스트
- 데이터 무결성 확인
