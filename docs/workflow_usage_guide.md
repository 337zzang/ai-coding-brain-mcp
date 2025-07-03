# Workflow 사용 가이드

## 수정된 오류
1. `helpers_wrapper.py`의 `workflow` 메서드 시그니처 누락
2. `workflow_commands.py`의 `handle_workflow_command` 함수 시그니처 누락

## 올바른 사용법

```python
import json

# workflow 명령 실행
result = helpers.workflow("/status")

# 중요: result.data는 JSON 문자열이므로 파싱 필요!
if result.ok:
    data = json.loads(result.data)  # ← 필수!
    status = data.get('status', {})
    # 이제 딕셔너리로 사용 가능
```

## 주의사항
- `helpers.workflow()`의 반환값은 `HelperResult` 객체
- `result.data`는 JSON 문자열 형태
- 반드시 `json.loads()`로 파싱 후 사용

## 사용 가능한 워크플로우 명령어
- `/status` - 현재 상태 확인
- `/plan 이름 | 설명` - 새 계획 생성
- `/task 제목 | 설명` - 작업 추가
- `/next` - 다음 작업으로 전환
- `/approve yes|no` - 작업 승인
- `/history` - 히스토리 확인
- `/build` - 프로젝트 컨텍스트 빌드
