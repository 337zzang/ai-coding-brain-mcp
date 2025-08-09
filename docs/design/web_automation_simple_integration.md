
## 🎯 웹 자동화 단순 통합 설계

### 현재 상황
- **api/** (17KB): BrowserManager 중심, 세션 공유 가능
- **python/api/** (82KB): 헬퍼 함수 중심, 즉시 사용 가능

### 문제점
- 두 개의 다른 접근 방식
- 중복 기능 존재
- 복잡한 import 경로

### ✅ 단순 통합 방안

#### 최종 구조 (5개 파일)
```
python/web_automation/
├── __init__.py           # 공개 API
├── browser.py            # BrowserManager + 세션 관리
├── helpers.py            # 모든 web_* 함수
├── errors.py             # 에러 처리
└── utils.py              # 공통 유틸리티
```

#### 파일별 역할

**1. __init__.py**
- 모든 공개 함수/클래스 export
- 하위 호환성 별칭 제공
```python
from .browser import BrowserManager, WebAutomation
from .helpers import (
    web_start, web_goto, web_click, web_type,
    web_extract, web_screenshot, web_close
)

# 하위 호환성
WebBrowser = WebAutomation  # 별칭
```

**2. browser.py** (핵심)
- BrowserManager 클래스 (api/browser_manager.py에서)
- SessionRegistry 통합
- WebAutomation 래퍼 클래스 (새로 작성)
```python
class WebAutomation:
    '''통합 인터페이스'''
    def __init__(self, session_id=None):
        self.manager = BrowserManager()
        self.browser = None

    def start(self, headless=False):
        # BrowserManager 사용

    def goto(self, url):
        # helpers.web_goto 호출
```

**3. helpers.py**
- python/api/web_automation_helpers.py 전체 이동
- 함수명 그대로 유지
- 내부 구현만 정리

**4. errors.py**
- python/api/web_automation_errors.py 이동
- 새로운 에러 클래스 추가

**5. utils.py**
- 공통 유틸리티 함수
- 로깅, 검증 등

### 장점
- **단순함**: 5개 파일로 명확한 구조
- **호환성**: 기존 코드 그대로 동작
- **확장성**: 새 기능 추가 용이
- **유지보수**: 파일별 역할 명확

### 마이그레이션
```python
# 기존 코드 (변경 불필요)
from python.api.web_automation_helpers import web_start, web_goto
web_start()
web_goto("https://example.com")

# 새 코드 (권장)
from python.web_automation import WebAutomation
web = WebAutomation()
web.start()
web.goto("https://example.com")
```

### 실행 계획
1. python/web_automation/ 폴더 생성
2. 파일 복사 및 수정
3. import 경로 수정
4. 테스트
5. 기존 파일 제거
