# 🔧 파일 수정 헬퍼 실전 사용 가이드

## 🎯 Quick Reference

### 1. 우선순위별 사용법

#### 🥇 최우선: Desktop Commander edit_block
```python
# 가장 안정적, 들여쓰기 문제 없음
from desktop-commander import edit_block

edit_block(
    file_path="path/to/file.py",
    old_string="""    def old_method(self):
        return "old"""",
    new_string="""    def old_method(self):
        # 수정됨
        return "new"""",
    expected_replacements=1  # 기본값
)
```

#### 🥈 차선: h.replace (정확한 매칭)
```python
# 들여쓰기까지 정확히 포함하여 매칭
old_code = '''    def method(self):
        """정확한 들여쓰기 포함"""
        return value'''

new_code = '''    def method(self):
        """수정된 메서드"""
        return new_value'''

h.replace(file_path, old_code, new_code)
```

#### 🥉 특수 케이스: h.safe_replace
```python
# 식별자 교체 시 AST 모드 자동 사용
h.safe_replace("app.py", "old_var", "new_var")
```

## 📋 케이스별 베스트 프랙티스

### Case 1: 함수 시그니처 변경
```python
# ✅ GOOD - Desktop Commander
edit_block(
    file_path="api.py",
    old_string="def get_data(self, endpoint):",
    new_string="def get_data(self, endpoint, timeout=30):"
)

# ⚠️ OK - h.replace (더 많은 컨텍스트 포함)
h.replace(
    "api.py",
    "def get_data(self, endpoint):\n        \"\"\"데이터를 가져옴\"\"\"",
    "def get_data(self, endpoint, timeout=30):\n        \"\"\"데이터를 가져옴\"\"\"",
)
```

### Case 2: 메서드 전체 교체
```python
# ✅ BEST - 전체 메서드를 정확히 복사
old_method = h.view("file.py", "method_name")['data']
new_method = """    def method_name(self):
        # 완전히 새로운 구현
        return new_implementation()"""

edit_block("file.py", old_method, new_method)
```

### Case 3: 블록 내부 수정
```python
# ✅ GOOD - 충분한 컨텍스트 포함
edit_block(
    file_path="processor.py",
    old_string="""        for item in items:
            if item > 0:
                process(item)""",
    new_string="""        for item in items:
            if item > 0:
                # 로깅 추가
                logger.info(f"Processing {item}")
                process(item)"""
)
```

### Case 4: import 문 추가
```python
# ✅ SIMPLE - h.insert 사용
content = h.read("file.py")['data']
lines = content.split('\n')

# 적절한 위치 찾기
insert_line = 0
for i, line in enumerate(lines):
    if line.startswith('import ') or line.startswith('from '):
        insert_line = i + 1
    elif line and not line.startswith('#'):
        break

h.insert("file.py", "import logging", insert_line)
```

## ⚠️ 주의사항

### 1. 들여쓰기 정확성
```python
# ❌ BAD - 들여쓰기 불일치
h.replace("file.py", "def method():", "  def method():")  # 실패!

# ✅ GOOD - 정확한 들여쓰기
h.replace("file.py", "    def method():", "    def method():")
```

### 2. 멀티라인 패턴
```python
# ❌ BAD - 윈도우 줄바꿈 문제
pattern = "line1\r\nline2"  # 실패 가능

# ✅ GOOD - 플랫폼 독립적
pattern = """line1
line2"""  # 또는 content.replace('\r\n', '\n')
```

### 3. 특수문자 이스케이프
```python
# ❌ BAD
h.replace("file.py", "price = $100", "price = $200")  # $ 문제

# ✅ GOOD  
h.replace("file.py", "price = \$100", "price = \$200")
```

## 🛠️ 디버깅 팁

### 1. 교체 실패 시
```python
# 패턴이 정확한지 확인
content = h.read("file.py")['data']
if old_pattern in content:
    print("✅ 패턴 존재")
else:
    print("❌ 패턴 없음")
    # 탭/스페이스, 줄바꿈 확인
    print(repr(old_pattern))
    print(repr(content[start:end]))
```

### 2. 구문 오류 발생 시
```python
# 교체 전 백업 복원
if h.exists("file.py.backup")['data']:
    h.replace("file.py.backup", "", "")  # 복원

# AST 검증
try:
    ast.parse(new_content)
    print("✅ 구문 검증 통과")
except SyntaxError as e:
    print(f"❌ Line {e.lineno}: {e.msg}")
```

### 3. diff 확인
```python
import difflib

old = h.read("file.py.backup")['data']
new = h.read("file.py")['data']

diff = difflib.unified_diff(
    old.splitlines(keepends=True),
    new.splitlines(keepends=True),
    fromfile="backup",
    tofile="current"
)
print(''.join(diff))
```

## 💡 프로 팁

### 1. 안전한 교체 워크플로우
```python
def safe_file_edit(file_path, old, new):
    # 1. 백업
    backup = f"{file_path}.backup"
    shutil.copy2(file_path, backup)

    try:
        # 2. 교체 시도
        if '\n' in old:  # 멀티라인
            result = edit_block(file_path, old, new)
        else:  # 단일라인
            result = h.replace(file_path, old, new)

        # 3. 검증
        content = h.read(file_path)['data']
        ast.parse(content)

        # 4. 백업 삭제
        os.remove(backup)
        return True

    except Exception as e:
        # 5. 복원
        shutil.copy2(backup, file_path)
        print(f"복원됨: {e}")
        return False
```

### 2. 패턴 정확도 향상
```python
def get_exact_pattern(file_path, function_name):
    """함수의 정확한 코드 가져오기"""
    content = h.read(file_path)['data']
    tree = ast.parse(content)

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == function_name:
            start_line = node.lineno - 1
            end_line = node.end_lineno
            lines = content.split('\n')[start_line:end_line]
            return '\n'.join(lines)

    return None
```

### 3. 일괄 교체
```python
def batch_replace(file_patterns, old, new):
    """여러 파일 일괄 교체"""
    results = []

    for pattern in file_patterns:
        files = h.search_files(pattern)['data']
        for file in files:
            try:
                h.replace(file, old, new)
                results.append((file, "✅"))
            except:
                results.append((file, "❌"))

    return results
```

## 📊 성능 비교

| 방법 | 안정성 | 속도 | 들여쓰기 | 추천도 |
|------|--------|------|----------|--------|
| edit_block | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 🥇 |
| h.replace | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | 🥈 |
| h.safe_replace | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | 🥉 |
| 수동 편집 | ⭐⭐⭐⭐⭐ | ⭐ | ⭐⭐⭐⭐⭐ | - |

## 🎯 결론

1. **Desktop Commander의 edit_block을 기본으로 사용**
2. **정확한 패턴 매칭**이 가능하면 h.replace
3. **복잡한 리팩토링**은 CST 도구 활용
4. **항상 백업과 검증** 수행
