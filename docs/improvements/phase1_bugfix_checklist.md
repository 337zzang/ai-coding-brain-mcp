
## 🔧 치명적 버그 수정 체크리스트

### 1. `.h.append` / `.h.replace` 오타 수정
```python
# ❌ 잘못된 코드
self.actions.h.append(action)  # AttributeError!

# ✅ 수정된 코드
self.actions.append(action)
```

### 2. JavaScript 스타일 boolean 수정
```python
# ❌ 잘못된 코드
is_visible = true
has_error = false

# ✅ 수정된 코드  
is_visible = True
has_error = False
```

### 3. 중복 함수 정의 제거
- `close_instance()` 함수 중복 제거
- `web_extract()` 함수 중복 제거
- 하나의 정의만 남기고 나머지 삭제

### 4. 안전한 JavaScript 코드 생성
```python
# ❌ 위험한 코드
js_code = f"var data = {str(python_dict)};"  # 인젝션 위험!

# ✅ 안전한 코드
page.evaluate("(data) => { /* use data */ }", python_dict)
```

### 수정 스크립트
```python
def fix_critical_bugs(filepath):
    content = h.file.read(filepath)['data']

    # .h.append 오타 수정
    content = content.replace('.h.append(', '.append(')
    content = content.replace('.h.replace(', '.replace(')

    # JavaScript boolean 수정
    import re
    content = re.sub(r'=\s*true', '= True', content)
    content = re.sub(r'=\s*false', '= False', content)

    h.file.write(filepath, content)
    print(f"✅ {filepath} 수정 완료")
```
