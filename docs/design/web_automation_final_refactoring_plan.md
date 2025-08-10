
# 웹 자동화 시스템 최종 통합 계획

## 목표
- python/ai_helpers_new/web.py 단일 파일로 통합
- Facade 패턴: h.web.* 형태로 사용
- 중복 제거, 198KB → 30KB 이하로 축소

## 현재 문제점
1. 3개 폴더에 21개 파일 분산 (198KB)
2. BrowserManager가 3곳에 중복
3. 세션 관리가 5개 파일에 분산
4. web_automation_helpers.py 1803 lines (너무 큼)

## 통합 전략

### 1단계: 핵심 기능 추출
- BrowserManager (api/browser_manager.py) - 유지 ✅
- 핵심 헬퍼 함수 10개만 선별 (web_automation_helpers.py에서)
- 에러 클래스 3개만 유지

### 2단계: 단일 파일 통합 (python/ai_helpers_new/web.py)
```python
# 구조
class BrowserManager:
    # api/browser_manager.py에서 가져옴
    pass

class WebSession:
    # 세션 관리 통합 (간소화)
    pass

class WebAutomation:
    # 통합 인터페이스
    def __init__(self):
        self.manager = BrowserManager()

    # 핵심 메서드만
    def start()
    def goto()
    def click()
    def type()
    def extract()
    def screenshot()
    def close()

# 헬퍼 함수 (하위 호환성)
def web_start(): pass
def web_goto(): pass
def web_click(): pass
# ... 10개 정도만

# Facade 네임스페이스
class WebNamespace:
    start = web_start
    goto = web_goto
    # ...
```

### 3단계: 삭제할 파일/폴더
- api/ 폴더 전체 (백업 후 삭제)
- python/api/ 폴더 전체 (백업 후 삭제)
- python/web_automation/ 폴더 전체 (백업 후 삭제)

### 4단계: ai_helpers_new/__init__.py 수정
```python
from . import web
# Facade 추가
self.web = web.WebNamespace()
```

### 최종 구조
```
python/ai_helpers_new/
├── __init__.py      (web 모듈 추가)
├── web.py           (통합된 웹 자동화, 30KB 이하)
├── file.py          (기존)
├── code.py          (기존)
├── search.py        (기존)
├── git.py           (기존)
└── llm.py           (기존)
```

### 사용 예시
```python
import ai_helpers_new as h

# Facade 패턴
h.web.start()
h.web.goto("https://example.com")
h.web.click("button")
data = h.web.extract("div.content")
h.web.close()

# 또는 클래스 사용
web = h.WebAutomation()
web.start()
web.goto("https://example.com")
```

## 예상 결과
- 파일 수: 21개 → 1개
- 크기: 198KB → 30KB 이하
- 복잡도: 대폭 감소
- 사용성: h.web.* facade로 단순화

## 위험 요소
- 일부 고급 기능 손실 가능
- 기존 코드 의존성 확인 필요
