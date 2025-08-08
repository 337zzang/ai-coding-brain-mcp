
# 웹 자동화 세션 유지 테스트

## 1️⃣ 첫 번째 execute_code 블록 - 세션 시작
```python
import ai_helpers_new as h

# 세션 연결
result = h.web_connect("https://www.google.com")
if result['ok']:
    web_session_active = result['session_active']
    print(f"✅ 세션 시작: {result['data']}")
    print(f"   세션 활성: {web_session_active}")
else:
    print(f"❌ 오류: {result['error']}")
```

## 2️⃣ 두 번째 execute_code 블록 - 세션 재사용
```python
# 세션 상태 확인
if web_session_active:
    result = h.web_check_session()
    if result['ok']:
        session_info = result['data']
        print(f"✅ 세션 활성: {session_info['active']}")
        print(f"   현재 URL: {session_info['url']}")
        print(f"   페이지 제목: {session_info['title']}")

# 검색 수행
if web_session_active:
    h.web_type("input[name='q']", "Python web automation")
    h.web_click("button[type='submit']")
    print("✅ 검색 수행 완료")
```

## 3️⃣ 세 번째 execute_code 블록 - 추가 작업
```python
# 세션이 여전히 활성인지 확인
if web_session_active:
    # 스크린샷 캡처
    h.web_screenshot("search_results.png")

    # 데이터 추출
    results = h.web_extract("h3")
    print(f"✅ 검색 결과 {len(results)} 개 찾음")
```

## 4️⃣ 마지막 블록 - 세션 종료
```python
if web_session_active:
    # 세션 종료
    result = h.web_disconnect(save_recording=True)
    if result['ok']:
        print(f"✅ {result['data']}")
        web_session_active = False
```
