# 웹 자동화 레코딩 기능

Playwright 액션을 자동으로 파이썬 스크립트로 변환하는 기능입니다.

## 주요 기능

1. **액션 레코딩**: 모든 웹 자동화 액션을 자동으로 기록
2. **스크립트 생성**: 기록된 액션을 실행 가능한 파이썬 스크립트로 변환
3. **민감 정보 보호**: 비밀번호 등의 민감한 정보는 자동으로 마스킹
4. **로그 파일**: 모든 액션의 상세 정보를 JSON 형식으로 저장

## 사용법

### 1. 레코딩 시작

```python
from python.ai_helpers import web_automation_record_start

# 레코딩 시작 (브라우저 표시)
web = web_automation_record_start(headless=False, project_name="my_project")
```

### 2. 웹 자동화 작업 수행

```python
# 페이지 이동
web.go_to_page("https://example.com")

# 요소 클릭
web.click_element("button.submit", by="css")

# 텍스트 입력
web.input_text("input[name='email']", "user@example.com", by="css")

# 텍스트 추출
web.extract_text("h1", by="css")

# 스크롤
web.scroll_page(action="down")
```

### 3. 스크립트 생성

```python
from python.ai_helpers import web_automation_record_stop

# 레코딩 중지 및 스크립트 생성
result = web_automation_record_stop("my_script.py")
print(f"생성된 스크립트: {result['script_path']}")
```

## 생성된 스크립트 예시

```python
#!/usr/bin/env python3
"""
자동 생성된 웹 자동화 스크립트
생성 시간: 2025-07-13 15:30:00
프로젝트: my_project
총 액션 수: 5
"""

import time
from python.api.web_automation import WebAutomation


def main():
    """메인 실행 함수"""
    # WebAutomation 인스턴스 생성
    with WebAutomation(headless=False) as web:
        try:
            # 액션 1: navigate
            print("🌐 페이지 이동: https://example.com")
            result = web.go_to_page("https://example.com")
            if not result["success"]:
                raise Exception(f"페이지 이동 실패: {result['message']}")
            time.sleep(2)  # 페이지 로드 대기

            # 액션 2: click
            print("🖱️ 클릭: button.submit")
            result = web.click_element("button.submit", by="css")
            if not result["success"]:
                raise Exception(f"클릭 실패: {result['message']}")
            time.sleep(1)

            # ... 더 많은 액션들 ...

        except Exception as e:
            print(f"❌ 오류 발생: {e}")
            return False

        print("✅ 모든 작업 완료!")
        return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
```

## 고급 기능

### 레코딩 상태 확인

```python
from python.ai_helpers import web_automation_record_status

status = web_automation_record_status()
print(f"레코딩 중: {status['recording']}")
print(f"총 액션 수: {status['total_actions']}")
print(f"경과 시간: {status['duration']}초")
```

### 데모 실행

```python
from python.ai_helpers import web_record_demo

# 구글 검색 데모 실행
web_record_demo()
```

## 주의사항

1. **민감 정보**: 비밀번호 필드는 자동으로 마스킹되지만, 추가 보안이 필요한 경우 수동으로 편집하세요.
2. **대기 시간**: 생성된 스크립트는 적절한 대기 시간을 포함하지만, 필요에 따라 조정하세요.
3. **에러 처리**: 생성된 스크립트는 기본적인 에러 처리를 포함합니다.
4. **브라우저 종료**: `with` 문을 사용하여 자동으로 브라우저가 종료됩니다.

## 파일 구조

```
generated_scripts/
├── web_auto_20250713_153000.py    # 생성된 스크립트
└── web_auto_20250713_153000.json  # 액션 로그
```
