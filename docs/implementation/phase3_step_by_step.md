
# 📋 Phase 3 실용적 개선 구현 가이드

## 🎯 구현 목표
기존 API 호환성을 유지하면서 선택적으로 AST 기반 정확성을 제공

## 📝 Step 1: search.py에 선택적 AST 모드 추가

### 1.1 현재 코드 분석
```python
# python/ai_helpers_new/search.py
def find_function(name: str, path: str = ".") -> Dict[str, Any]:
    """Python 파일에서 함수 정의 찾기"""
    # 현재는 정규식 기반 검색만 사용
    pattern = rf'def\s+{re.escape(name)}\s*\('
    # ... 정규식 검색 로직
```

### 1.2 수정할 코드
```python
# python/ai_helpers_new/search.py 상단에 추가
import ast
from typing import Optional, List, Tuple
from functools import lru_cache

# AST 기반 함수 검색 헬퍼
def _find_function_ast(name: str, file_path: str) -> Optional[Tuple[int, str]]:
    """AST를 사용한 정확한 함수 검색"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        tree = ast.parse(content)

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == name:
                # 함수의 시작 라인과 정의 추출
                start_line = node.lineno
                lines = content.split('\n')

                # 함수 전체 내용 추출 (들여쓰기 고려)
                func_lines = []
                indent_level = None

                for i in range(start_line - 1, len(lines)):
                    line = lines[i]
                    if line.strip() == "":
                        continue

                    # 첫 줄의 들여쓰기 레벨 저장
                    if indent_level is None:
                        indent_level = len(line) - len(line.lstrip())

                    # 같은 레벨이거나 더 깊은 들여쓰기면 함수의 일부
                    current_indent = len(line) - len(line.lstrip())
                    if current_indent >= indent_level:
                        func_lines.append(line)
                    else:
                        break

                return (start_line, '\n'.join(func_lines))

    except Exception as e:
        print(f"AST 파싱 오류: {e}")
        return None

# 기존 find_function 수정
def find_function(name: str, path: str = ".", strict: bool = False) -> Dict[str, Any]:
    """Python 파일에서 함수 정의 찾기

    Args:
        name: 함수명
        path: 검색 경로
        strict: True면 AST 사용, False면 정규식 사용 (기본값)

    Returns:
        성공: {
            'ok': True,
            'data': {
                'count': 발견 개수,
                'results': [
                    {
                        'file': 파일 경로,
                        'line': 시작 라인,
                        'definition': 함수 정의
                    }
                ]
            }
        }
    """
    try:
        results = []

        # 파일 목록 가져오기
        py_files = []
        if os.path.isfile(path) and path.endswith('.py'):
            py_files = [path]
        else:
            for root, _, files in os.walk(path):
                for file in files:
                    if file.endswith('.py'):
                        py_files.append(os.path.join(root, file))

        # strict 모드 선택
        if strict:
            # AST 기반 검색
            for file_path in py_files:
                result = _find_function_ast(name, file_path)
                if result:
                    line_num, definition = result
                    results.append({
                        'file': file_path,
                        'line': line_num,
                        'definition': definition
                    })
        else:
            # 기존 정규식 기반 검색 로직
            pattern = rf'def\s+{re.escape(name)}\s*\('

            for file_path in py_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()

                    for i, line in enumerate(lines, 1):
                        if re.search(pattern, line):
                            # 함수 정의 추출 로직 (기존과 동일)
                            func_def = _extract_function_definition(lines, i-1)
                            results.append({
                                'file': file_path,
                                'line': i,
                                'definition': func_def
                            })
                except Exception:
                    continue

        return {
            'ok': True,
            'data': {
                'count': len(results),
                'results': results,
                'method': 'ast' if strict else 'regex'
            }
        }

    except Exception as e:
        return {
            'ok': False,
            'error': str(e)
        }
```

## 📝 Step 2: code.py에 안전한 수정 검증 추가

### 2.1 현재 safe_replace 분석
```python
# python/ai_helpers_new/utils/safe_wrappers.py
def safe_replace(file_path: str, old_code: str, new_code: str, 
                text_mode: bool = False) -> Dict[str, Any]:
    # 현재는 libcst 실패 시 텍스트 모드로 폴백
```

### 2.2 AST 검증 기능 추가
```python
# python/ai_helpers_new/code.py에 추가
def validate_python_syntax(code: str) -> Tuple[bool, Optional[str]]:
    """Python 코드의 구문 유효성 검증

    Returns:
        (valid, error_message)
    """
    try:
        ast.parse(code)
        return (True, None)
    except SyntaxError as e:
        return (False, f"Line {e.lineno}: {e.msg}")
    except Exception as e:
        return (False, str(e))

# safe_replace 수정 (safe_wrappers.py)
def safe_replace(file_path: str, old_code: str, new_code: str, 
                text_mode: bool = False, validate: bool = True) -> Dict[str, Any]:
    """파일에서 코드를 안전하게 교체

    Args:
        file_path: 파일 경로
        old_code: 찾을 코드
        new_code: 교체할 코드
        text_mode: 텍스트 모드 사용 (deprecated)
        validate: 수정 후 구문 검증 여부
    """
    try:
        # 파일 읽기
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 교체할 코드가 있는지 확인
        if old_code not in content:
            return {
                'ok': False,
                'error': 'Code not found',
                'suggestion': 'Check whitespace and indentation'
            }

        # 임시로 교체해서 검증
        new_content = content.replace(old_code, new_code)

        # 구문 검증 (옵션)
        if validate and file_path.endswith('.py'):
            valid, error_msg = validate_python_syntax(new_content)
            if not valid:
                return {
                    'ok': False,
                    'error': f'Syntax error after replacement: {error_msg}',
                    'preview': new_content.split('\n')[int(error_msg.split()[1])-1] if 'Line' in error_msg else None
                }

        # 실제 파일 수정
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        return {
            'ok': True,
            'data': {
                'file': file_path,
                'replacements': content.count(old_code),
                'validated': validate
            }
        }

    except Exception as e:
        return {
            'ok': False,
            'error': str(e)
        }
```

## 📝 Step 3: 경량 캐싱 시스템 구현

### 3.1 AST 캐싱 헬퍼 추가
```python
# python/ai_helpers_new/core/ast_cache.py (새 파일)
import ast
import os
from functools import lru_cache
from typing import Optional, Dict, Any

class ASTCache:
    """경량 AST 캐싱 시스템"""

    def __init__(self, max_size: int = 20):
        self.max_size = max_size
        # LRU 캐시 사용
        self._parse = lru_cache(maxsize=max_size)(self._parse_impl)

    def _get_file_key(self, file_path: str) -> tuple:
        """파일의 고유 키 생성 (경로, 수정시간)"""
        try:
            stat = os.stat(file_path)
            return (file_path, stat.st_mtime)
        except:
            return (file_path, 0)

    def _parse_impl(self, file_key: tuple) -> Optional[ast.AST]:
        """실제 파싱 수행"""
        file_path = file_key[0]
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return ast.parse(content)
        except:
            return None

    def parse(self, file_path: str) -> Optional[ast.AST]:
        """캐시된 AST 반환"""
        key = self._get_file_key(file_path)
        return self._parse(key)

    def clear(self):
        """캐시 초기화"""
        self._parse.cache_clear()

    def info(self) -> Dict[str, Any]:
        """캐시 상태 정보"""
        return {
            'max_size': self.max_size,
            'current_size': self._parse.cache_info().currsize,
            'hits': self._parse.cache_info().hits,
            'misses': self._parse.cache_info().misses,
            'hit_rate': self._parse.cache_info().hits / (self._parse.cache_info().hits + self._parse.cache_info().misses)
            if (self._parse.cache_info().hits + self._parse.cache_info().misses) > 0 else 0
        }

# 전역 캐시 인스턴스
_ast_cache = ASTCache()
```

### 3.2 캐시 사용 예시
```python
# search.py에서 캐시 사용
from .core.ast_cache import _ast_cache

def _find_function_ast_cached(name: str, file_path: str) -> Optional[Tuple[int, str]]:
    """캐시를 활용한 AST 기반 함수 검색"""
    tree = _ast_cache.parse(file_path)
    if not tree:
        return None

    # 이후 로직은 동일...
```

## 📝 Step 4: 테스트 코드 작성

### 4.1 단위 테스트
```python
# test/unit/test_strict_mode.py
import pytest
from ai_helpers_new import find_function, safe_replace

def test_find_function_strict_mode(tmp_path):
    """strict 모드 테스트"""
    # 테스트 파일 생성
    test_file = tmp_path / "test.py"
    test_file.write_text('''
def real_function():
    """실제 함수"""
    pass

# 주석 속의 def fake_function(): pass
string_with_function = "def string_function(): pass"
''')

    # 정규식 모드 (기본값)
    result = find_function("fake_function", str(tmp_path))
    assert result['ok'] is True
    assert result['data']['count'] == 1  # 주석도 찾음

    # AST strict 모드
    result = find_function("fake_function", str(tmp_path), strict=True)
    assert result['ok'] is True
    assert result['data']['count'] == 0  # 실제 함수가 아니므로 못 찾음

    # 실제 함수는 두 모드 모두 찾음
    result1 = find_function("real_function", str(tmp_path))
    result2 = find_function("real_function", str(tmp_path), strict=True)
    assert result1['data']['count'] == 1
    assert result2['data']['count'] == 1

def test_safe_replace_validation(tmp_path):
    """구문 검증 테스트"""
    test_file = tmp_path / "test.py"
    test_file.write_text('''
def calculate(x):
    return x * 2
''')

    # 유효한 수정
    result = safe_replace(
        str(test_file),
        "return x * 2",
        "return x * 3",
        validate=True
    )
    assert result['ok'] is True

    # 구문 오류를 만드는 수정
    result = safe_replace(
        str(test_file),
        "return x * 3",
        "return x * * 4",  # 구문 오류
        validate=True
    )
    assert result['ok'] is False
    assert 'Syntax error' in result['error']
```

## 📝 Step 5: 점진적 마이그레이션

### 5.1 Feature Flag 설정
```python
# python/ai_helpers_new/config.py (새 파일)
class FeatureFlags:
    """기능 플래그 관리"""

    def __init__(self):
        self.flags = {
            'use_ast_search': False,  # 기본값 False
            'validate_replacements': True,  # 기본값 True
            'cache_ast_results': True  # 기본값 True
        }

    def set(self, flag: str, value: bool):
        if flag in self.flags:
            self.flags[flag] = value

    def get(self, flag: str, default: bool = False) -> bool:
        return self.flags.get(flag, default)

# 전역 인스턴스
_features = FeatureFlags()

# 헬퍼 함수
def set_feature(flag: str, value: bool):
    _features.set(flag, value)

def get_feature(flag: str) -> bool:
    return _features.get(flag)
```

### 5.2 __init__.py 업데이트
```python
# python/ai_helpers_new/__init__.py에 추가
from .config import set_feature, get_feature

# 기존 export에 추가
__all__ = [
    # ... 기존 항목들
    'set_feature',
    'get_feature',
]
```

## 🚀 적용 방법

### 1. Git 브랜치 생성
```bash
git checkout -b feature/phase3-practical-improvements
```

### 2. 파일별 수정
1. `search.py` - AST 함수 추가 및 strict 파라미터
2. `code.py` - validate_python_syntax 함수 추가
3. `safe_wrappers.py` - validate 파라미터 추가
4. `core/ast_cache.py` - 새 파일 생성
5. `config.py` - 새 파일 생성
6. `__init__.py` - export 업데이트

### 3. 테스트 실행
```bash
pytest test/unit/test_strict_mode.py -v
```

### 4. 성능 측정
```python
# 성능 비교 스크립트
import time
import ai_helpers_new as h

# 정규식 모드
start = time.time()
result1 = h.find_function("find_function", ".")
time1 = time.time() - start

# AST strict 모드
start = time.time()
result2 = h.find_function("find_function", ".", strict=True)
time2 = time.time() - start

print(f"정규식: {time1:.3f}초, 찾은 개수: {result1['data']['count']}")
print(f"AST: {time2:.3f}초, 찾은 개수: {result2['data']['count']}")
```

## ⚠️ 주의사항

1. **호환성 유지**
   - 모든 새 파라미터는 기본값을 가져야 함
   - 기존 동작을 변경하지 않음

2. **에러 처리**
   - AST 파싱 실패 시 graceful fallback
   - 명확한 에러 메시지

3. **성능 모니터링**
   - 캐시 히트율 추적
   - 메모리 사용량 주시

4. **문서화**
   - 새 파라미터 설명 추가
   - 사용 예시 제공
