
# 🛠️ Phase 3 실용적 개선 - 구체적 변경 방법

## 📝 변경할 파일 목록
1. `python/ai_helpers_new/search.py` - find_function에 strict 모드 추가
2. `python/ai_helpers_new/utils/safe_wrappers.py` - safe_replace에 validate 추가
3. `python/ai_helpers_new/core/ast_helper.py` (새 파일) - AST 헬퍼 함수들

## 🔧 Step-by-Step 변경 가이드

### Step 1: Git 브랜치 생성 및 백업
```python
# 현재 상태 저장
h.git_stash("Phase 3 작업 전 백업")

# 새 브랜치 생성
h.git_checkout_b("feature/phase3-practical")
```

### Step 2: search.py 수정

#### 2-1. AST 헬퍼 함수 추가 (파일 상단)
```python
# python/ai_helpers_new/search.py 
# 라인 10 근처, import 구문 다음에 추가

def _find_function_with_ast(name: str, file_path: str) -> Optional[Dict[str, Any]]:
    """AST를 사용한 정확한 함수 검색"""
    try:
        import ast

        # 파일 읽기
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # AST 파싱
        tree = ast.parse(content)

        # 함수 찾기
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == name:
                # 함수 시작 라인
                start_line = node.lineno

                # 함수 끝 라인 찾기 (다음 같은 레벨 노드까지)
                lines = content.split('\n')
                func_lines = []

                # 첫 줄의 들여쓰기 확인
                first_line = lines[start_line - 1]
                base_indent = len(first_line) - len(first_line.lstrip())

                # 함수 전체 추출
                for i in range(start_line - 1, len(lines)):
                    line = lines[i]
                    if i > start_line - 1:  # 첫 줄 이후
                        if line.strip() and (len(line) - len(line.lstrip())) <= base_indent:
                            break  # 같거나 낮은 들여쓰기면 함수 끝
                    func_lines.append(line)

                return {
                    'file': file_path,
                    'line': start_line,
                    'definition': '\n'.join(func_lines)
                }

        return None

    except Exception as e:
        # AST 파싱 실패 시 None 반환
        print(f"AST parsing failed for {file_path}: {e}")
        return None
```

#### 2-2. find_function 수정 (Line 157 근처)
```python
# 기존 함수 시그니처 변경
def find_function(name: str, path: str = ".", strict: bool = False) -> Dict[str, Any]:
    """Python 파일에서 함수 정의 찾기

    Args:
        name: 함수명
        path: 검색 경로 
        strict: True면 AST 사용 (정확하지만 느림), False면 정규식 사용 (빠르지만 부정확)
    """
    try:
        results = []

        # 파일 목록 수집 (기존 코드와 동일)
        if os.path.isfile(path) and path.endswith('.py'):
            files = [path]
        elif os.path.isdir(path):
            files = []
            for root, _, filenames in os.walk(path):
                for filename in filenames:
                    if filename.endswith('.py'):
                        files.append(os.path.join(root, filename))
        else:
            return {'ok': False, 'error': 'Invalid path'}

        # Strict 모드 분기
        if strict:
            # AST 기반 검색
            for file_path in files:
                result = _find_function_with_ast(name, file_path)
                if result:
                    results.append(result)
        else:
            # 기존 정규식 검색 로직 (변경 없음)
            pattern = rf'def\s+{re.escape(name)}\s*\('

            for file_path in files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()

                    for i, line in enumerate(lines, 1):
                        if re.search(pattern, line):
                            # 기존 함수 정의 추출 로직...
                            # (변경 없음)
                except:
                    continue

        return {
            'ok': True,
            'data': {
                'count': len(results),
                'results': results,
                'search_method': 'ast' if strict else 'regex'
            }
        }
    except Exception as e:
        return {'ok': False, 'error': str(e)}
```

### Step 3: safe_wrappers.py 수정

#### 3-1. safe_replace에 validate 파라미터 추가
```python
# python/ai_helpers_new/utils/safe_wrappers.py
# safe_replace 함수 찾아서 수정

def safe_replace(file_path: str, old_code: str, new_code: str, 
                text_mode: bool = False, validate: bool = False) -> Dict[str, Any]:
    """안전하게 코드 교체 (validate 옵션 추가)"""
    try:
        # 파일 읽기
        response = h.read(file_path)
        if not response['ok']:
            return response

        content = response['data']

        # 코드가 존재하는지 확인
        if old_code not in content:
            return {
                'ok': False,
                'error': 'Code not found in file'
            }

        # 임시로 교체
        new_content = content.replace(old_code, new_code)

        # 검증 옵션 (새로 추가)
        if validate and file_path.endswith('.py'):
            try:
                import ast
                ast.parse(new_content)
            except SyntaxError as e:
                return {
                    'ok': False,
                    'error': f'Syntax error after replacement: Line {e.lineno}: {e.msg}',
                    'preview': {
                        'line': e.lineno,
                        'text': new_content.split('\n')[e.lineno-1] if e.lineno > 0 else ''
                    }
                }

        # 실제 파일 쓰기
        write_response = h.write(file_path, new_content)
        if write_response['ok']:
            write_response['data']['validated'] = validate

        return write_response

    except Exception as e:
        return {'ok': False, 'error': str(e)}
```

### Step 4: 간단한 캐싱 추가 (선택사항)

#### 4-1. 새 파일 생성: core/ast_helper.py
```python
# python/ai_helpers_new/core/ast_helper.py
import ast
import os
from functools import lru_cache
from typing import Optional

# 간단한 LRU 캐시 (파일 20개까지)
@lru_cache(maxsize=20)
def _cached_parse(file_path: str, mtime: float) -> Optional[ast.AST]:
    """파일을 AST로 파싱 (캐시됨)"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return ast.parse(content)
    except:
        return None

def parse_file_cached(file_path: str) -> Optional[ast.AST]:
    """캐시를 활용한 AST 파싱"""
    try:
        mtime = os.path.getmtime(file_path)
        return _cached_parse(file_path, mtime)
    except:
        return None

def clear_ast_cache():
    """캐시 초기화"""
    _cached_parse.cache_clear()
```

### Step 5: 테스트

#### 5-1. 변경사항 테스트 스크립트
```python
# test_phase3_changes.py
import ai_helpers_new as h

# 테스트 1: strict 모드 테스트
print("=== Test 1: strict mode ===")

# 테스트 파일 생성
test_code = '''
def real_function():
    """This is a real function"""
    return 42

# Comment: def fake_function(): pass

class MyClass:
    def method(self):
        # Another comment with def another_fake(): pass
        pass
'''

h.write("test_strict_mode.py", test_code)

# 일반 모드 (정규식)
print("\n일반 모드:")
result = h.find_function("fake_function", ".")
print(f"찾은 개수: {result['data']['count']}")

# Strict 모드 (AST)
print("\nStrict 모드:")
result = h.find_function("fake_function", ".", strict=True)
print(f"찾은 개수: {result['data']['count']}")

# 테스트 2: validate 모드 테스트
print("\n=== Test 2: validate mode ===")

# 유효한 수정
result = h.safe_replace(
    "test_strict_mode.py",
    "return 42",
    "return 84",
    validate=True
)
print(f"유효한 수정: {result['ok']}")

# 구문 오류를 만드는 수정
result = h.safe_replace(
    "test_strict_mode.py", 
    "return 84",
    "return 84 +++ 1",  # 구문 오류
    validate=True
)
print(f"구문 오류 수정: {result['ok']}")
if not result['ok']:
    print(f"오류: {result['error']}")
```

### Step 6: 커밋

```python
# 변경사항 확인
h.git_status()

# 스테이징
h.git_add(["python/ai_helpers_new/search.py", 
           "python/ai_helpers_new/utils/safe_wrappers.py"])

# 커밋
h.git_commit("feat: Add strict mode to find_function and validate to safe_replace")
```

## ⚠️ 주의사항

1. **import 위치**: ast는 함수 내부에서 import (전역 의존성 최소화)
2. **기본값**: strict=False, validate=False (기존 동작 유지)
3. **에러 처리**: AST 실패 시 정규식으로 자동 폴백 가능
4. **성능**: strict 모드는 느리므로 필요할 때만 사용

## 📊 예상 결과

- 주석이나 문자열 내의 함수 정의를 실제 함수로 착각하지 않음
- 코드 수정 후 구문 오류 사전 방지
- 기존 API 완벽 호환
- 점진적 도입 가능
