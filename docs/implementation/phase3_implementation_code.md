
# 📄 Phase 3 구현 코드 예시

## 1️⃣ search.py 전체 수정 내용

```python
# python/ai_helpers_new/search.py

import ast
import os
from typing import Dict, Any, List, Optional
from .wrappers import safe_wrapper
from .file import read

# 기존 import와 함수들은 그대로 유지...

@safe_wrapper
def find_function(name: str, path: str = ".", strict: bool = False) -> Dict[str, Any]:
    """Python 파일에서 함수 정의 찾기

    Args:
        name: 함수명
        path: 검색 경로
        strict: True시 AST 기반 정확한 검색 (기본값: False)

    Returns:
        성공: {
            'ok': True,
            'data': [{'file': str, 'line': int, 'definition': str}, ...],
            'count': int,
            'function_name': str,
            'mode': 'ast' | 'regex'
        }
    """
    if strict:
        try:
            result = _find_function_ast(name, path)
            result['data']['mode'] = 'ast'
            return result
        except Exception as e:
            # 로깅만 하고 아래 정규식으로 진행
            import logging
            logging.warning(f"AST search failed: {e}, falling back to regex")

    # 기존 정규식 로직 (변경 없음)
    result = _find_function_regex(name, path)
    result['data']['mode'] = 'regex'
    return result


def _find_function_ast(name: str, path: str) -> Dict[str, Any]:
    """AST 기반 정확한 함수 검색"""
    results = []

    # Python 파일 찾기
    from .search import search_files
    py_files_result = search_files("*.py", path)
    if not py_files_result['ok']:
        return py_files_result

    py_files = py_files_result['data'][:100]  # 성능 제한

    for file_path in py_files:
        try:
            # 파일 읽기
            content_result = read(file_path)
            if not content_result['ok']:
                continue

            content = content_result['data']

            # AST 파싱
            tree = ast.parse(content, filename=file_path)

            # 함수 찾기
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == name:
                    # 함수 정의 추출
                    lines = content.split('\n')
                    start_line = node.lineno - 1

                    # 함수 끝 찾기 (간단한 휴리스틱)
                    end_line = start_line
                    indent_level = len(lines[start_line]) - len(lines[start_line].lstrip())

                    for i in range(start_line + 1, len(lines)):
                        line = lines[i]
                        if line.strip() and len(line) - len(line.lstrip()) <= indent_level:
                            break
                        end_line = i

                    definition = '\n'.join(lines[start_line:end_line + 1])

                    results.append({
                        'file': file_path,
                        'line': node.lineno,
                        'definition': definition
                    })

        except SyntaxError:
            # 구문 오류가 있는 파일은 건너뛰기
            continue
        except Exception:
            # 기타 오류도 건너뛰기
            continue

    return {
        'ok': True,
        'data': results,
        'count': len(results),
        'function_name': name
    }


def _find_function_regex(name: str, path: str) -> Dict[str, Any]:
    """기존 정규식 기반 함수 검색 (현재 코드 그대로)"""
    # 현재 구현을 그대로 사용
    # ... 기존 코드 ...
```

## 2️⃣ safe_wrappers.py 수정 내용

```python
# python/ai_helpers_new/utils/safe_wrappers.py

import ast
import warnings
from typing import Dict, Any

def safe_replace(file_path: str, old_code: str, new_code: str, 
                text_mode: bool = False, validate: bool = False) -> Dict[str, Any]:
    """안전한 코드 교체 with 선택적 구문 검증

    Args:
        file_path: 파일 경로
        old_code: 교체할 코드
        new_code: 새 코드
        text_mode: True시 단순 텍스트 교체 (기본값: False)
        validate: True시 수정 후 구문 검증 (기본값: False)

    Returns:
        성공: {'ok': True, 'data': {'lines_changed': int, 'validated': bool}}
        실패: {'ok': False, 'error': str, ...}
    """
    try:
        # 파일 읽기
        from ..file import read
        read_result = read(file_path)
        if not read_result['ok']:
            return read_result

        content = read_result['data']

        # 교체 수행
        if text_mode:
            # 단순 텍스트 교체
            if old_code not in content:
                return {
                    'ok': False,
                    'error': 'Old code not found in file'
                }
            new_content = content.replace(old_code, new_code)
        else:
            # AST 기반 교체 (기존 로직)
            from ..code import safe_replace as ast_replace
            replace_result = ast_replace(file_path, old_code, new_code)
            if not replace_result['ok']:
                return replace_result
            return replace_result  # 이미 파일 저장됨

        # 새 기능: 구문 검증
        if validate:
            try:
                ast.parse(new_content)
            except SyntaxError as e:
                return {
                    'ok': False,
                    'error': f'구문 오류 발생: {str(e)}',
                    'error_type': 'SyntaxError',
                    'line': e.lineno,
                    'offset': e.offset,
                    'text': e.text
                }

        # 파일 저장
        from ..file import write
        write_result = write(file_path, new_content)
        if not write_result['ok']:
            return write_result

        return {
            'ok': True,
            'data': {
                'lines_changed': old_code.count('\n') + 1,
                'validated': validate,
                'mode': 'text' if text_mode else 'ast'
            }
        }

    except Exception as e:
        return {
            'ok': False,
            'error': str(e),
            'error_type': type(e).__name__
        }
```

## 3️⃣ 테스트 코드

```python
# test/unit/test_phase3_improvements.py

import pytest
import tempfile
import os

def test_find_function_strict_mode():
    """strict 모드에서 주석 내 함수명 무시 테스트"""
    # 테스트 파일 생성
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write('''
# This comment mentions process_data but it's not a function
def real_function():
    """Docstring mentions process_data"""
    print("process_data is just a string here")

def process_data(x):
    return x * 2
''')
        temp_file = f.name

    try:
        import ai_helpers_new as h

        # strict=False (정규식): 주석/문자열도 포함될 수 있음
        result = h.find_function("process_data", os.path.dirname(temp_file), strict=False)
        assert result['ok']

        # strict=True (AST): 실제 함수만 찾음
        result = h.find_function("process_data", os.path.dirname(temp_file), strict=True)
        assert result['ok']
        assert len(result['data']) == 1
        assert result['data'][0]['line'] == 7  # 실제 함수 라인

    finally:
        os.unlink(temp_file)


def test_safe_replace_validate():
    """validate 모드에서 구문 오류 방지 테스트"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write('''
def old_function():
    return 42
''')
        temp_file = f.name

    try:
        import ai_helpers_new as h

        # 유효한 수정
        result = h.safe_replace(
            temp_file,
            "return 42",
            "return 43",
            validate=True
        )
        assert result['ok']
        assert result['data']['validated'] is True

        # 무효한 수정 (구문 오류)
        result = h.safe_replace(
            temp_file,
            "def old_function():",
            "def new_function(:",  # 구문 오류!
            validate=True
        )
        assert not result['ok']
        assert 'SyntaxError' in result['error_type']

    finally:
        os.unlink(temp_file)
```

## 4️⃣ 사용 가이드

```python
# 실제 사용 예시

import ai_helpers_new as h

# 1. 정확한 함수 찾기 (주석/문자열 제외)
results = h.find_function("authenticate", strict=True)
if results['ok']:
    print(f"Found {results['count']} exact matches")
    for match in results['data']:
        print(f"  {match['file']}:{match['line']}")

# 2. 안전한 코드 수정 (구문 검증 포함)
result = h.safe_replace(
    "auth.py",
    "def login(user, pass):",
    "def login(user, password):",  # 'pass'는 예약어!
    validate=True
)
if not result['ok']:
    print(f"수정 실패: {result['error']}")

# 3. 빠른 검색 (기존 방식)
results = h.find_function("helper", strict=False)  # 또는 strict 생략

# 4. 빠른 수정 (기존 방식)
h.safe_replace("util.py", "old", "new")  # validate 생략
```
