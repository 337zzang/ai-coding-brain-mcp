# 웹 자동화 시스템 리팩토링 상세 설계
*작성일: 2025-08-09*

## 📊 현황 분석

### 1. 현재 구조 (2개 구현 공존)

#### api/ 폴더 (새로운 구현)
- **아키텍처**: Client-Server 모델
- **핵심 파일**: browser_manager.py (254 lines)
- **특징**: 
  - 프로세스 간 브라우저 공유
  - 세션 영속화
  - 중앙 집중식 관리
- **총 크기**: 약 17KB

#### python/api/ 폴더 (기존 구현)  
- **아키텍처**: 헬퍼 함수 기반
- **핵심 파일**: web_automation_helpers.py (1803 lines)
- **특징**:
  - Playwright 직접 조작
  - 다양한 유틸리티 함수
  - 즉시 실행 가능
- **총 크기**: 약 82KB

### 2. 문제점
- 중복 기능 존재
- import 경로 충돌 가능성
- 두 가지 사용 패턴 혼재
- 유지보수 복잡도 증가

## 🎯 리팩토링 목표

1. **단일 진입점**: 하나의 통합된 API
2. **기능 통합**: 두 구현의 장점 결합
3. **하위 호환성**: 기존 사용 패턴 유지
4. **모듈화**: 명확한 책임 분리
5. **확장성**: 향후 기능 추가 용이

## 🏗️ 통합 아키텍처 설계

### 폴더 구조
```
python/
├── web_automation/              # 통합 웹 자동화 패키지
│   ├── __init__.py              # 공개 API
│   ├── core/                    # 핵심 기능
│   │   ├── browser_manager.py   # 브라우저 관리 (api/에서 이동)
│   │   ├── session_manager.py   # 세션 관리 (api/에서 이동)
│   │   └── playwright_wrapper.py # Playwright 래퍼
│   ├── helpers/                 # 헬퍼 함수
│   │   ├── navigation.py        # 페이지 탐색
│   │   ├── interaction.py       # 요소 상호작용
│   │   ├── extraction.py        # 데이터 추출
│   │   └── javascript.py        # JS 실행
│   ├── utils/                   # 유틸리티
│   │   ├── errors.py            # 에러 처리
│   │   ├── logging.py           # 로깅
│   │   └── validators.py        # 검증
│   └── legacy/                  # 하위 호환성
│       └── compat.py            # 기존 함수 래퍼
```

### 계층 구조
```
┌─────────────────────────────────┐
│      Public API (__init__.py)    │  <- 사용자 진입점
├─────────────────────────────────┤
│         Legacy Compat Layer      │  <- 하위 호환성
├─────────────────────────────────┤
│         Helper Functions         │  <- 고수준 기능
├─────────────────────────────────┤
│      Core Browser Manager        │  <- 핵심 관리
├─────────────────────────────────┤
│      Playwright Wrapper          │  <- 저수준 조작
└─────────────────────────────────┘
```

## 📋 모듈별 통합 방안

### 1. 유지할 파일 (이동 및 개선)
- `api/browser_manager.py` → `python/web_automation/core/browser_manager.py`
- `api/session_registry.py` → `python/web_automation/core/session_manager.py`
- `api/activity_logger.py` → `python/web_automation/utils/logging.py`

### 2. 분할할 파일
**python/api/web_automation_helpers.py** (1803 lines) 분할:
- 탐색 함수 → `helpers/navigation.py`
- 상호작용 함수 → `helpers/interaction.py`  
- JS 실행 → `helpers/javascript.py`
- 데이터 추출 → `helpers/extraction.py`

### 3. 병합할 파일
- `python/api/web_automation_errors.py` + 새로운 에러 → `utils/errors.py`
- `python/api/web_automation_extraction.py` → `helpers/extraction.py`에 병합

### 4. 삭제할 파일
- `api/fix_bugs.py` (임시 유틸리티)
- `api/test_browser_manager.py` (테스트는 test/ 폴더로)
- `python/api/example_javascript_execution.py` (예제는 docs/로)

## 🔧 구체적인 리팩토링 단계

### Phase 1: 준비 (Day 1)
1. 백업 생성
2. 새 폴더 구조 생성
3. 테스트 환경 구축

### Phase 2: 코어 이동 (Day 2)
1. browser_manager.py 이동 및 개선
2. session_manager.py 분리
3. 단위 테스트 작성

### Phase 3: 헬퍼 분할 (Day 3-4)
1. web_automation_helpers.py 분석
2. 기능별 모듈 분할
3. import 경로 수정
4. 통합 테스트

### Phase 4: 통합 API (Day 5)
1. __init__.py 작성
2. 공개 API 정의
3. 문서화

### Phase 5: 하위 호환성 (Day 6)
1. legacy/compat.py 작성
2. 기존 사용 패턴 테스트
3. 마이그레이션 가이드 작성

### Phase 6: 정리 (Day 7)
1. 구 파일 삭제
2. 최종 테스트
3. 문서 업데이트

## 🔌 통합 API 설계

### 단일 진입점
```python
from python.web_automation import WebAutomation

# 방법 1: 컨텍스트 매니저 (권장)
with WebAutomation() as web:
    web.goto("https://example.com")
    data = web.extract("table")

# 방법 2: 직접 사용 (하위 호환)
from python.web_automation import web_start, web_goto, web_extract
web_start()
web_goto("https://example.com")
data = web_extract("table")

# 방법 3: 세션 공유 (새 기능)
from python.web_automation import BrowserSession
session = BrowserSession.get_or_create("user_123")
browser = session.connect()
```

### 주요 메서드
```python
class WebAutomation:
    # 브라우저 제어
    def start(self, headless=False, session_id=None)
    def stop(self)
    def goto(self, url)

    # 상호작용
    def click(self, selector)
    def type(self, selector, text)
    def select(self, selector, value)

    # 데이터 추출
    def extract(self, selector, format='text')
    def extract_table(self, selector)
    def screenshot(self, path=None)

    # JavaScript
    def execute_js(self, script)
    def wait_for(self, condition)

    # 세션 관리
    def save_session(self)
    def load_session(self, session_id)
```

## 📊 예상 결과

### 개선 효과
- **코드 중복 제거**: 약 30% 코드 감소
- **유지보수성**: 모듈별 책임 명확화
- **성능**: 세션 재사용으로 50% 속도 향상
- **확장성**: 새 기능 추가 용이

### 위험 요소
- 기존 코드 의존성 파악 필요
- 테스트 커버리지 확보 필수
- 마이그레이션 기간 중 혼란 가능

## 📝 다음 단계

1. **승인 요청**: 이 설계로 진행할지 결정
2. **백업 생성**: 현재 상태 완전 백업
3. **Phase 1 시작**: 폴더 구조 생성

## 🎯 핵심 결정 사항

1. **python/web_automation/** 폴더로 통합 (api/ 폴더 제거)
2. **BrowserManager 유지** (세션 공유 기능 중요)
3. **헬퍼 함수 분할** (유지보수성 향상)
4. **하위 호환성 레이어** 제공 (기존 코드 보호)
