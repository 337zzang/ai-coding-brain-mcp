
# view 함수 사용 가이드

## ❌ 문제가 있었던 코드
```python
# TypeError 발생 코드
view_result = h.view(file_path, function_name)
content = view_result['data']['content']  # ❌ data는 문자열!
```

## ✅ 올바른 사용법
```python
# 방법 1: 직접 처리
view_result = h.view(file_path, function_name)
if view_result['ok']:
    code_content = view_result['data']  # data가 이미 코드 문자열
    line_start = view_result.get('line_start')
    line_end = view_result.get('line_end')

# 방법 2: 안전한 처리
view_result = h.view(file_path, function_name)
if isinstance(view_result, dict) and view_result.get('ok'):
    code_content = view_result.get('data', '')
else:
    # 에러 처리
    error = view_result.get('error') if isinstance(view_result, dict) else 'Invalid response'
```

## 📌 반환값 구조
성공 시:
- `ok`: True
- `data`: 코드 내용 (문자열)
- `line_start`: 시작 라인 번호
- `line_end`: 끝 라인 번호
- `type`: 'function' 또는 'class'

실패 시:
- `ok`: False
- `error`: 에러 메시지
