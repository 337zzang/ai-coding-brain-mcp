# 웹 자동화 시스템 분석 보고서

## 🎯 시스템 개요
AI Coding Brain MCP의 웹 자동화 시스템은 헬퍼 함수를 통해 세션 내에서 브라우저를 자동화하고, 
진행사항을 자동으로 기록/스크래핑하는 통합 시스템입니다.

## 🏗️ 핵심 아키텍처

### 1. 계층 구조
```
사용자 (h.web_* 함수들)
    ↓
web_automation_helpers.py (헬퍼 함수 인터페이스)
    ↓
BrowserManager (싱글톤 인스턴스 관리)
    ↓
REPLBrowserWithRecording (브라우저 + 레코딩)
    ├── REPLBrowser (핵심 브라우저 제어)
    ├── ActionRecorder (액션 기록)
    ├── SmartWaitManager (스마트 대기)
    └── AdvancedExtractionManager (데이터 추출)
```

### 2. 핵심 모듈 역할

#### 📄 web_automation_helpers.py
- **역할**: 사용자가 직접 사용하는 헬퍼 함수들
- **주요 함수**: 19개
  - `web_start()`: 브라우저 시작
  - `web_goto()`: 페이지 이동
  - `web_click()`: 요소 클릭
  - `web_type()`: 텍스트 입력
  - `web_extract()`: 데이터 추출
  - `web_screenshot()`: 스크린샷
  - `web_generate_script()`: 스크립트 생성
  - `web_record_*()`: 레코딩 관련

#### 📄 web_automation_manager.py
- **BrowserManager**: 전역 브라우저 인스턴스 관리
  - 싱글톤 패턴
  - 프로젝트별 격리
  - 스레드 안전성
- **JavaScriptExecutor**: 안전한 JS 실행

#### 📄 web_automation_repl.py
- **REPLBrowser**: 핵심 브라우저 제어 클래스
  - Playwright 기반
  - 명령 큐 방식
  - 별도 스레드에서 실행

#### 📄 web_automation_integrated.py
- **REPLBrowserWithRecording**: 통합 클래스
  - REPLBrowser + ActionRecorder
  - 자동 액션 기록
  - 스크립트 생성 기능

#### 📄 web_automation_extraction.py
- **AdvancedExtractionManager**: 고급 데이터 추출
  - CSS/XPath 선택자
  - 테이블 추출
  - 폼 데이터 추출
  - 배치 추출

#### 📄 web_automation_recorder.py
- **ActionRecorder**: 모든 액션 자동 기록
  - 액션 타입별 기록
  - 시간 정보 포함
  - 스크립트 생성 지원

## 🔄 작동 흐름

### 1. 브라우저 시작
```python
h.web_start(headless=False, project_name="my_scraper")
```
- BrowserManager가 인스턴스 관리
- REPLBrowserWithRecording 생성
- 자동으로 레코딩 시작

### 2. 웹 자동화 수행
```python
h.web_goto("https://example.com")
h.web_click("button.submit")
h.web_type("input#search", "검색어")
data = h.web_extract("div.results")
```
- 모든 액션이 자동으로 기록됨
- 에러 처리 및 재시도 로직 포함
- 스마트 대기 기능 자동 적용

### 3. 데이터 추출 및 스크래핑
```python
# 단일 요소 추출
title = h.web_extract("h1")

# 테이블 추출
table_data = h.web_extract_table("table#data")

# 배치 추출
items = h.web_extract_batch("div.item", {
    "title": "h3",
    "price": ".price",
    "description": "p"
})

# 폼 데이터 추출
form_data = h.web_extract_form("form#signup")
```

### 4. 진행사항 확인 및 스크립트 생성
```python
# 레코딩 상태 확인
status = h.web_record_status()

# 기록된 액션 가져오기
actions = h.web_get_data()

# 재사용 가능한 스크립트 생성
h.web_generate_script("my_scraper.py")
```

## 🚀 사용 예제

### 예제 1: 검색 결과 스크래핑
```python
# 1. 브라우저 시작
h.web_start(project_name="search_scraper")

# 2. 검색 수행
h.web_goto("https://duckduckgo.com")
h.web_type("input[name='q']", "Python web scraping")
h.web_click("button[type='submit']")
h.web_wait(2)  # 결과 로딩 대기

# 3. 검색 결과 추출
results = h.web_extract_batch(".result", {
    "title": ".result__title",
    "url": ".result__url",
    "snippet": ".result__snippet"
})

# 4. 결과 확인
print(f"검색 결과 {len(results)}개 수집")
for i, result in enumerate(results[:5], 1):
    print(f"{i}. {result['title']}")

# 5. 스크립트 생성
h.web_generate_script("search_scraper.py")

# 6. 브라우저 종료
h.web_stop()
```

### 예제 2: 실시간 모니터링
```python
import time

# 1. 모니터링 시작
h.web_start(project_name="price_monitor")

urls = [
    "https://example.com/product1",
    "https://example.com/product2"
]

# 2. 주기적 모니터링
for _ in range(5):  # 5번 반복
    for url in urls:
        h.web_goto(url)

        # 가격 추출
        price = h.web_extract(".price")
        stock = h.web_extract(".stock-status")

        print(f"[{time.strftime('%H:%M:%S')}] {url}")
        print(f"  가격: {price}")
        print(f"  재고: {stock}")

        # 스크린샷 (변화 기록)
        h.web_screenshot(f"monitor_{time.time()}.png")

    time.sleep(60)  # 1분 대기

# 3. 수집된 데이터 확인
all_actions = h.web_get_data()
print(f"\n총 {len(all_actions)} 개의 액션 기록됨")
```

### 예제 3: 폼 자동 작성 및 제출
```python
# 1. 브라우저 시작
h.web_start(project_name="form_automation")

# 2. 폼 페이지로 이동
h.web_goto("https://example.com/signup")

# 3. 폼 작성
h.web_type("input[name='username']", "testuser123")
h.web_type("input[name='email']", "test@example.com")
h.web_type("input[name='password']", "SecurePass123!")
h.web_click("input[type='checkbox']")  # 약관 동의

# 4. 제출 전 폼 데이터 확인
form_data = h.web_extract_form("form#signup")
print("제출할 데이터:", form_data)

# 5. 제출
h.web_click("button[type='submit']")

# 6. 결과 확인
success_msg = h.web_extract(".success-message")
print("결과:", success_msg)
```

## 📊 진행사항 자동 스크래핑

### 레코딩 데이터 구조
```python
{
    "timestamp": "2025-08-02T10:30:45",
    "action": "click",
    "selector": "button.submit",
    "value": None,
    "url": "https://example.com",
    "success": True
}
```

### 실시간 진행상황 모니터링
```python
# 레코딩 상태 실시간 확인
while True:
    status = h.web_record_status()
    print(f"기록된 액션: {status['action_count']}개")
    print(f"현재 URL: {status['current_url']}")
    print(f"실행 시간: {status['duration']}초")

    if status['is_recording']:
        time.sleep(1)
    else:
        break
```

## 🛡️ 주요 특징

1. **자동 레코딩**: 모든 액션이 자동으로 기록
2. **스크립트 생성**: 기록된 액션을 재사용 가능한 스크립트로 변환
3. **에러 처리**: 자동 재시도 및 에러 복구
4. **스마트 대기**: 동적 콘텐츠 로딩 자동 감지
5. **프로젝트 격리**: 프로젝트별 독립된 브라우저 세션
6. **스레드 안전성**: 동시 실행 가능

## 🔧 고급 기능

### JavaScript 실행
```python
# 페이지에서 JS 실행
result = h.web_evaluate("document.title")
data = h.web_evaluate("Array.from(document.querySelectorAll('a')).map(a => a.href)")
```

### 멀티 셀렉터
```python
# 여러 셀렉터 중 첫 번째 매칭 사용
h.web_click(["button.submit", "input[type='submit']", "a.submit-link"])
```

### 조건부 대기
```python
# 특정 요소가 나타날 때까지 대기
h.web_wait_for_function("document.querySelector('.results').children.length > 0")
```

## 📝 결론
이 시스템은 헬퍼 함수를 통해 간단하게 브라우저를 제어하면서, 
모든 진행사항을 자동으로 기록하고 재사용 가능한 스크립트로 변환할 수 있는 
완성된 웹 자동화 솔루션입니다.
