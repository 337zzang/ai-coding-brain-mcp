
# 🌐 웹 자동화 모듈 구조 개선 계획

## 📋 개요
Phase 1-3 구조 개선 완료 후, python/api 폴더의 웹 자동화 모듈도 동일한 구조 개선 원칙에 맞춰 개선이 필요합니다.

## 🔍 현재 상태 분석

### ✅ 이미 준수하는 사항
- BrowserManager 싱글톤 패턴 구현
- 표준 응답 형식 {'ok': bool, 'data': ...} 사용
- os.chdir 미사용
- Pythonic 함수 기반 API 제공

### ⚠️ 개선 필요 사항
1. **전역 변수 _web_instance 사용** (60회)
   - Phase 2의 전역 상태 제거 원칙과 충돌
2. **ai_helpers_new와 미통합**
   - Phase 3의 API 일관성 원칙과 충돌
3. **독립적인 경로 처리**
   - 프로젝트 경로 시스템 미활용

## 🛠️ 개선 계획

### Task 1: 전역 변수 제거 (2시간)
#### 목표
_web_instance 전역 변수를 완전히 제거하고 BrowserManager 내부로 캡슐화

#### TODO
1. BrowserManager에 browser 속성 추가
2. _get_web_instance() → BrowserManager.get_browser() 변경
3. _set_web_instance() → BrowserManager.set_browser() 변경
4. 모든 web_* 함수에서 직접 BrowserManager 호출
5. 전역 변수 관련 코드 정리

#### 예시
```python
# 기존
def web_start():
    global _web_instance
    _web_instance = REPLBrowserWithRecording()

# 개선
def web_start():
    manager = BrowserManager.get_instance()
    browser = REPLBrowserWithRecording()
    manager.set_browser(browser)
```

### Task 2: ai_helpers_new 통합 (1시간)
#### 목표
웹 자동화 함수들을 h.web_* 형태로 사용 가능하도록 통합

#### TODO
1. python/ai_helpers_new/web.py 생성
2. web_automation_helpers.py의 공개 함수들을 web.py로 import
3. __init__.py에 web 모듈 추가
4. 기존 호환성 유지를 위한 alias 제공

#### 구조
```
ai_helpers_new/
├── __init__.py      # web 모듈 export
├── web.py          # 웹 자동화 공개 API
└── ...

python/api/         # 내부 구현 (그대로 유지)
├── web_automation_manager.py
├── web_automation_helpers.py
└── ...
```

### Task 3: 프로젝트 경로 통합 (30분)
#### 목표
스크린샷 등 파일 저장 시 프로젝트 경로 시스템 활용

#### TODO
1. web_screenshot() 함수 개선
2. 프로젝트별 screenshot 폴더 자동 생성
3. h.resolve_project_path() 활용

## 📊 예상 효과
1. **일관성**: 전체 프로젝트가 동일한 구조 원칙 준수
2. **안정성**: 전역 상태 제거로 예측 가능한 동작
3. **사용성**: h.web_* 형태의 통합된 API
4. **확장성**: 향후 멀티 브라우저 지원 가능

## ⚠️ 주의사항
- 기존 web_* 함수 호환성 유지
- 테스트 코드 작성 필수
- 단계별 마이그레이션

## ✅ 승인 요청
웹 자동화 모듈 구조 개선을 위한 3개 Task를 진행하시겠습니까?
예상 소요시간: 약 3.5시간
