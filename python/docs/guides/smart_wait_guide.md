# 스마트 대기 기능 사용 가이드

## 📋 개요

스마트 대기 기능은 웹 자동화 시 불필요한 대기 시간을 최소화하고 안정성을 높이는 지능형 대기 메커니즘입니다.

### 주요 특징
- ✅ **조건 기반 대기**: 특정 조건이 충족되면 즉시 진행
- ✅ **하위 호환성**: 기존 코드 수정 없이 사용 가능
- ✅ **다양한 대기 타입**: 요소, 네트워크, JavaScript 지원
- ✅ **성능 개선**: 평균 30-50% 실행 시간 단축

## 🚀 빠른 시작

### 기존 방식 (유지됨)
```python
# 단순 시간 대기 - 항상 전체 시간 대기
web_wait(5)  # 5초 대기
```

### 스마트 대기 방식
```python
# 요소가 나타나면 즉시 진행 (최대 10초)
web_wait(10, wait_for="element", selector="#submit-btn", condition="clickable")
```

## 📖 상세 사용법

### 1. 요소 대기 (wait_for="element")

특정 요소의 상태를 기다립니다.

#### 지원하는 조건(condition)
- `"present"`: DOM에 요소가 존재
- `"visible"`: 화면에 요소가 보임 (기본값)
- `"clickable"`: 클릭 가능한 상태
- `"hidden"`: 화면에서 숨겨짐

#### 사용 예시
```python
# 로그인 버튼이 클릭 가능할 때까지 대기
web_wait(10, wait_for="element", selector="#login-btn", condition="clickable")

# 로딩 스피너가 사라질 때까지 대기
web_wait(15, wait_for="element", selector=".loading-spinner", condition="hidden")

# 검색 결과가 나타날 때까지 대기
web_wait(5, wait_for="element", selector=".search-results", condition="visible")
```

### 2. 네트워크 대기 (wait_for="network_idle")

모든 네트워크 요청이 완료될 때까지 대기합니다.

```python
# AJAX 요청 완료 대기
web_goto("https://example.com/data")
web_wait(20, wait_for="network_idle")

# 커스텀 idle 시간 설정 (기본 0.5초)
web_wait(30, wait_for="network_idle", idle_time=1.0)
```

### 3. JavaScript 대기 (wait_for="js")

JavaScript 표현식이 특정 값이 될 때까지 대기합니다.

```python
# 페이지 완전 로드 대기
web_wait(10, wait_for="js", script="document.readyState", value="complete")

# 특정 변수 값 대기
web_wait(5, wait_for="js", script="window.appInitialized", value=True)

# 요소 개수 대기
web_wait(15, wait_for="js", 
         script="document.querySelectorAll('.item').length", 
         value=10)
```

## 💡 실전 활용 예시

### 로그인 자동화
```python
# 1. 로그인 페이지 이동
web_goto("https://example.com/login")

# 2. 페이지 로드 완료 대기
web_wait(10, wait_for="js", script="document.readyState", value="complete")

# 3. 로그인 폼 입력
web_type("#username", "user@example.com")
web_type("#password", "password")

# 4. 로그인 버튼 클릭 가능 대기 후 클릭
web_wait(5, wait_for="element", selector="#login-btn", condition="clickable")
web_click("#login-btn")

# 5. 로그인 처리 완료 대기 (네트워크)
web_wait(10, wait_for="network_idle")

# 6. 대시보드 로드 확인
web_wait(10, wait_for="element", selector=".dashboard", condition="visible")
```

### 동적 콘텐츠 처리
```python
# 1. 검색 실행
web_type("#search-input", "검색어")
web_click("#search-btn")

# 2. 로딩 표시가 나타났다가 사라질 때까지 대기
web_wait(1, wait_for="element", selector=".loading", condition="visible")
web_wait(10, wait_for="element", selector=".loading", condition="hidden")

# 3. 검색 결과 확인
web_wait(5, wait_for="js", 
         script="document.querySelectorAll('.result-item').length > 0", 
         value=True)
```

## 🔄 마이그레이션 가이드

### 점진적 마이그레이션
기존 코드를 한 번에 변경할 필요 없이 점진적으로 개선할 수 있습니다.

```python
# 단계 1: 문제가 있는 부분만 우선 개선
# Before
web_wait(10)  # 항상 10초 대기

# After  
web_wait(10, wait_for="element", selector="#content", condition="visible")

# 단계 2: 성능이 중요한 부분 개선
# Before
web_click("#load-more")
web_wait(5)  # 데이터 로드 대기

# After
web_click("#load-more")
web_wait(5, wait_for="network_idle")
```

### WebAutomationIntegrated 클래스 사용
```python
# 통합 클래스에서도 동일하게 사용
with WebAutomationIntegrated() as browser:
    browser.goto("https://example.com")
    browser.wait(10, wait_for="element", selector="#app", condition="visible")
    browser.click("#start-btn")
    browser.wait(20, wait_for="network_idle")
```

## ⚠️ 주의사항

1. **Selector 정확성**: 잘못된 selector는 항상 타임아웃됩니다
2. **적절한 타임아웃**: 너무 짧으면 실패, 너무 길면 비효율적
3. **조건 선택**: 상황에 맞는 적절한 조건 사용
4. **디버그 모드**: `WEB_AUTO_DEBUG=true` 환경변수로 상세 로그 확인

## 📊 성능 비교

| 시나리오 | 기존 방식 | 스마트 대기 | 개선율 |
|---------|----------|------------|--------|
| 버튼 클릭 대기 | 5초 (고정) | 0.5-2초 | 60-90% |
| AJAX 완료 대기 | 10초 (고정) | 1-3초 | 70-90% |
| 페이지 로드 | 3초 + 재시도 | 정확한 감지 | 안정성 향상 |

## 🐛 문제 해결

### 요소를 찾을 수 없음
```python
# 디버그 모드 활성화
os.environ['WEB_AUTO_DEBUG'] = 'true'

# 더 구체적인 selector 사용
web_wait(10, wait_for="element", 
         selector="button[type='submit']#login", 
         condition="clickable")
```

### 네트워크 대기 타임아웃
```python
# 타임아웃 증가 및 idle_time 조정
web_wait(30, wait_for="network_idle", idle_time=1.0)
```

### JavaScript 조건 실패
```python
# 브라우저 콘솔에서 먼저 테스트
# 정확한 표현식 사용
web_wait(10, wait_for="js", 
         script="typeof window.myApp !== 'undefined' && window.myApp.ready", 
         value=True)
```

## 🎯 모범 사례

1. **명확한 조건 사용**: 가능한 구체적인 조건 설정
2. **적절한 타임아웃**: 일반적으로 5-10초, 느린 작업은 20-30초
3. **단계별 대기**: 복잡한 시나리오는 여러 단계로 분리
4. **에러 처리**: 대기 실패 시 적절한 처리

```python
# 모범 예시
result = web_wait(10, wait_for="element", selector="#submit", condition="clickable")
if not result['ok']:
    print(f"대기 실패: {result['error']}")
    # 대체 로직 또는 재시도
```

---

작성일: 2025-08-02
버전: 1.0
