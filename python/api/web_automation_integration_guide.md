# WebAutomation API Manager 통합 가이드

## 1. API 등록
`available_apis` 딕셔너리에 다음 항목 추가:
```python
'browser': 'python.api.web_automation.WebAutomation',
```

## 2. 헬퍼 주입
`_inject_helpers` 메서드에 다음 코드 블록 추가:
```python
elif api_name == 'browser':
    # 웹 자동화 관련 메서드들을 helpers에 주입
    if hasattr(api_instance, 'go_to_page'):
        helpers.go_to_page = api_instance.go_to_page
    if hasattr(api_instance, 'click_element'):
        helpers.click_element = api_instance.click_element
    if hasattr(api_instance, 'input_text'):
        helpers.input_text = api_instance.input_text
    if hasattr(api_instance, 'extract_text'):
        helpers.extract_text = api_instance.extract_text
    if hasattr(api_instance, 'scroll_page'):
        helpers.scroll_page = api_instance.scroll_page
    if hasattr(api_instance, 'handle_login'):
        helpers.handle_login = api_instance.handle_login
    if hasattr(api_instance, 'close_browser'):
        helpers.close_browser = api_instance.close
    if hasattr(api_instance, 'get_browser_status'):
        helpers.get_browser_status = api_instance.get_status
```

## 3. 사용 예시
```python
# API 활성화
api_manager.toggle_api('browser', True)

# 사용
helpers.go_to_page("https://example.com")
helpers.input_text("input[name='username']", "user")
helpers.click_element("button.login")
text = helpers.extract_text("div.content")
```

## 4. 주의사항
- WebAutomation 인스턴스는 브라우저 리소스를 관리하므로 적절한 종료가 필요
- API Manager의 기존 패턴을 따라 일관성 유지
- 에러 처리는 WebAutomation 클래스 내부에서 처리
