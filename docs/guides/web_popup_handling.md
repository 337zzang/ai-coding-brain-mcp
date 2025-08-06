# 웹 자동화 팝업 처리 가이드

## 📋 개요
웹 자동화 시 다양한 형태의 팝업, 모달, 다이얼로그를 효과적으로 처리하기 위한 헬퍼 함수들입니다.

## 🔧 주요 함수

### 1. handle_popup() - 범용 팝업 처리
```python
result = h.handle_popup(page, button_text="예", force=True)
if result['ok']:
    print(f"팝업 처리 완료: {result['data']['method']}")
```

**특징:**
- 다양한 선택자 자동 시도 (role="dialog", .modal, .popup 등)
- 실패 시 JavaScript로 직접 클릭
- 표준 응답 형식 반환

### 2. handle_alert() - 브라우저 alert 처리
```python
result = h.handle_alert(page, accept=True, text="입력값")
```

### 3. wait_and_click() - 요소 대기 후 클릭
```python
result = h.wait_and_click(page, "button.confirm", timeout=5000)
```

### 4. 편의 함수들
```python
h.close_popup(page)    # 다양한 닫기 버튼 시도
h.confirm_popup(page)  # 다양한 확인 버튼 시도
h.cancel_popup(page)   # 다양한 취소 버튼 시도
```

## 🎯 사용 예제

### 기본 사용법
```python
from playwright.sync_api import sync_playwright

# 브라우저 시작
playwright = sync_playwright().start()
browser = playwright.chromium.launch(headless=False, args=['--start-maximized'])
page = browser.new_page(no_viewport=True)

# 페이지 이동
page.goto("https://example.com")

# 팝업 처리
result = h.handle_popup(page, "확인")
if result['ok']:
    print(f"✅ 팝업 처리 성공: {result['data']}")
else:
    print(f"❌ 오류: {result['error']}")
```

### 복잡한 시나리오
```python
# 1. 로그인 후 환영 팝업 처리
page.fill("#username", "user")
page.fill("#password", "pass")
page.click("#login-btn")

# 환영 팝업 닫기
h.close_popup(page)

# 2. 작업 확인 팝업
page.click("#delete-btn")
result = h.confirm_popup(page)  # "확인", "예", "OK" 등 자동 시도

# 3. 특정 클래스의 모달 처리
h.handle_modal_by_class(page, "warning-modal", "계속진행")
```

## 🔍 문제 해결

### 팝업이 클릭되지 않을 때
1. **force=True 옵션 사용** (기본값)
   ```python
   h.handle_popup(page, "확인", force=True)
   ```

2. **JavaScript 직접 실행** (자동 폴백)
   - 모든 선택자 실패 시 자동으로 JavaScript로 클릭

3. **특정 선택자 지정**
   ```python
   h.wait_and_click(page, '[data-testid="confirm-button"]')
   ```

### 동적 로딩 팝업
```python
# 팝업이 나타날 때까지 대기 후 클릭
h.wait_and_click(page, "text=확인", timeout=10000)
```

## 📊 반환값 구조
모든 함수는 표준 응답 형식을 반환합니다:

```python
{
    'ok': True,  # 성공 여부
    'data': {
        'clicked': True,
        'method': 'selector',  # 또는 'javascript'
        'selector': '...',     # 사용된 선택자
        'selector_index': 0    # 몇 번째 선택자로 성공했는지
    },
    'error': None  # 오류 메시지 (실패 시)
}
```

## ⚙️ 내부 동작

### 선택자 우선순위
1. `[role="dialog"] button:has-text("...")`
2. `[role="alertdialog"] button:has-text("...")`
3. `.modal button:has-text("...")`
4. `[class*="popup"] button:has-text("...")`
5. `[class*="dialog"] button:has-text("...")`
6. `[class*="overlay"] button:has-text("...")`
7. `div[style*="z-index"] button:has-text("...")`
8. `button:has-text("..."):visible`
9. JavaScript 직접 실행 (폴백)

### 지원되는 닫기/확인/취소 텍스트
- **닫기**: "닫기", "확인", "OK", "Close", "X", "×", "✕"
- **확인**: "확인", "예", "네", "OK", "Yes", "Confirm"
- **취소**: "취소", "아니오", "아니요", "Cancel", "No"

## 🚀 최적화 팁
1. **자주 사용하는 패턴은 편의 함수 활용**
2. **force=True로 대부분의 가려진 요소 처리 가능**
3. **복잡한 팝업은 handle_modal_by_class()로 정확히 타겟팅**
4. **동적 팝업은 wait_and_click()으로 대기 시간 설정**
