# 웹 자동화 시스템 에러 처리 개선 가이드

## 📋 개요

웹 자동화 시스템의 에러 처리가 개선되어 더 나은 디버깅과 안정성을 제공합니다.
기존 API와 100% 호환되므로 코드 변경 없이 사용할 수 있습니다.

## 🚀 주요 개선사항

### 1. 구조화된 에러 처리
- 모든 함수에 `safe_execute` 래퍼 적용
- 예외 발생 시 안전한 에러 응답 반환
- Stack trace 보존 (디버그 모드)

### 2. 로깅 시스템
- JSON 형식의 구조화된 로그
- 로그 파일: `api/logs/web_automation_YYYYMMDD.log`
- 에러, 경고, 정보 레벨별 로깅

### 3. 디버그 모드
- 환경변수 또는 런타임 제어 가능
- 상세한 에러 정보 제공
- 개발 환경에서 문제 해결 용이

## 💻 사용 방법

### 기본 사용 (변경 없음)
```python
from api import web_automation_helpers as web

# 기존과 동일하게 사용
web.web_start()
result = web.web_goto("https://example.com")
if not result['ok']:
    print(f"에러: {result['error']}")
```

### 디버그 모드 활성화

#### 방법 1: 환경변수
```bash
# Windows
set WEB_AUTO_DEBUG=true

# Linux/Mac
export WEB_AUTO_DEBUG=true
```

#### 방법 2: 런타임 제어
```python
from api import web_automation_errors as errors

# 디버그 모드 켜기
errors.enable_debug_mode()

# 에러 발생 시 상세 정보
result = web.web_click("button")
if not result['ok']:
    print(f"에러: {result['error']}")
    if '_debug' in result:
        debug = result['_debug']
        print(f"타입: {debug['error_type']}")
        print(f"스택: {debug['stack_trace']}")

# 디버그 모드 끄기
errors.disable_debug_mode()
```

## 📊 응답 형식

### 성공 응답 (변경 없음)
```json
{
    "ok": true,
    "data": "결과값"
}
```

### 에러 응답 (기본)
```json
{
    "ok": false,
    "error": "에러 메시지"
}
```

### 에러 응답 (디버그 모드)
```json
{
    "ok": false,
    "error": "에러 메시지",
    "_debug": {
        "error_type": "ValueError",
        "stack_trace": "...",
        "context": {
            "function": "web_click",
            "args": ["button"],
            "execution_time": 0.123
        },
        "timestamp": "2025-08-02T12:00:00"
    }
}
```

## 🔍 로그 파일 분석

로그 파일은 JSON Lines 형식으로 저장됩니다:

```json
{"timestamp": "2025-08-02T12:00:00", "level": "ERROR", "function": "web_click", "message": "..."}
{"timestamp": "2025-08-02T12:00:01", "level": "INFO", "function": "web_goto", "message": "..."}
```

분석 도구로 쉽게 필터링 가능:
```python
import json

# 에러만 필터링
with open('logs/web_automation_20250802.log', 'r') as f:
    for line in f:
        log = json.loads(line)
        if log['level'] == 'ERROR':
            print(log)
```

## ⚡ 성능 영향

- 디버그 모드 OFF: 성능 영향 최소 (<1ms)
- 디버그 모드 ON: 약간의 오버헤드 (Stack trace 수집)
- 로깅: 비동기 처리로 영향 최소화

## 🔄 마이그레이션 가이드

### 신규 프로젝트
- 변경 없이 사용 가능
- 필요시 디버그 모드 활용

### 기존 프로젝트
1. 코드 변경 불필요
2. 에러 처리 개선 자동 적용
3. 디버그가 필요한 경우만 모드 활성화

## 🛠️ 문제 해결

### 로그 파일을 찾을 수 없음
- 위치 확인: `api/logs/` 폴더
- 권한 확인: 쓰기 권한 필요

### 디버그 정보가 나타나지 않음
- 환경변수 확인: `echo %WEB_AUTO_DEBUG%`
- 런타임 상태 확인: `errors.get_debug_status()`

### 성능 저하
- 프로덕션에서는 디버그 모드 OFF
- 로그 레벨 조정 고려

## 📚 참고 자료

- 소스 코드: `web_automation_errors.py`
- 테스트 코드: `test_error_handling.py`
- 로그 위치: `api/logs/`
