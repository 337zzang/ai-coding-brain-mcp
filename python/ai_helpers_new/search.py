"""
AI Helpers Search Module
파일과 코드를 검색하기 위한 단순하고 실용적인 함수들
"""
import os
import re
import fnmatch
from pathlib import Path
from typing import Dict, Any, List, Optional
from .util import ok, err

# 정규식 캐시 (성능 최적화)
_regex_cache = {}
_MAX_CACHE_SIZE = 100

def _get_compiled_regex(pattern: str, flags=re.IGNORECASE):
    """컴파일된 정규식을 캐시에서 가져오거나 새로 생성"""
    cache_key = (pattern, flags)

    if cache_key not in _regex_cache:
        # 캐시 크기 제한
        if len(_regex_cache) >= _MAX_CACHE_SIZE:
            # LRU 방식: 가장 오래된 절반 제거
            keys = list(_regex_cache.keys())
            for key in keys[:_MAX_CACHE_SIZE // 2]:
                del _regex_cache[key]

        _regex_cache[cache_key] = re.compile(pattern, flags)

    return _regex_cache[cache_key]




def search_files(pattern: str, path: str = ".", recursive: bool = True, 
                 max_depth: Optional[int] = None) -> Dict[str, Any]:
    """파일명 패턴으로 파일 검색 (최적화 버전)

    Args:
        pattern: 파일명 패턴 (예: "*.py", "test_*.txt", "test")
        path: 검색 시작 경로 (기본값: 현재 디렉토리)
        recursive: 하위 디렉토리도 검색할지 여부 (기본값: True)
        max_depth: 최대 검색 깊이 (None=무제한, recursive=False시 1)

    Returns:
        성공: {'ok': True, 'data': ['path1', 'path2', ...], 'count': 개수}
        실패: {'ok': False, 'error': 에러메시지}
    """
    try:
        from pathlib import Path
        import fnmatch

        # 자동 와일드카드 변환
        if '*' not in pattern and '?' not in pattern:
            pattern = f'*{pattern}*'

        base_path = Path(path).resolve()
        if not base_path.exists():
            return err(f"Path not found: {path}")

        results = []

        # 제외 패턴 (성능 향상)
        exclude_dirs = {'__pycache__', '.git', 'node_modules', '.pytest_cache', 
                       'dist', 'build', '.venv', 'venv', '.idea', '.vscode'}

        if recursive:
            # pathlib의 rglob 사용 - 훨씬 빠름
            for file_path in base_path.rglob(pattern):
                # 제외 디렉토리 체크
                if any(exc in file_path.parts for exc in exclude_dirs):
                    continue

                if file_path.is_file():
                    rel_path = file_path.relative_to(base_path)

                    # max_depth 체크
                    if max_depth and len(rel_path.parts) > max_depth:
                        continue

                    # Windows 경로 정규화
                    results.append(str(rel_path).replace(os.sep, '/'))
        else:
            # 현재 디렉토리만
            for file_path in base_path.glob(pattern):
                if file_path.is_file():
                    results.append(file_path.name)

        return ok(results, count=len(results))

    except Exception as e:
        return err(f"Search failed: {str(e)}")


def search_code(pattern: str, path: str = ".", file_pattern: str = "*", 
                max_results: int = 1000) -> Dict[str, Any]:
    """파일 내용에서 패턴 검색 - 스트리밍 최적화 버전

    Args:
        pattern: 검색할 패턴 (정규식)
        path: 검색 시작 경로
        file_pattern: 대상 파일 패턴 (예: "*.py")
        max_results: 최대 결과 수

    Returns:
        성공: {
            'ok': True, 
            'data': [
                {'file': 'path', 'line': 10, 'text': '매칭된 줄', 'match': '매칭 부분'},
                ...
            ],
            'count': 매칭 수,
            'files_searched': 검색한 파일 수,
            'truncated': 결과가 잘렸는지 여부
        }
        실패: {'ok': False, 'error': 에러메시지}
    """
    try:
        # 정규식 컴파일 (캐시 사용)
        regex = _get_compiled_regex(pattern, re.IGNORECASE)
    except re.error as e:
        return err(f"Invalid regex pattern: {e}")

    # 파일 목록 가져오기
    files_result = search_files(file_pattern, path)
    if not files_result['ok']:
        return files_result

    results = []
    files_searched = 0
    truncated = False

    # 바이너리 파일 확장자
    binary_extensions = {'.pyc', '.pyo', '.exe', '.dll', '.so', '.dylib', 
                        '.jpg', '.jpeg', '.png', '.gif', '.pdf', '.zip'}

    for file_path in files_result['data']:
        if max_results and len(results) >= max_results:
            truncated = True
            break

        full_path = os.path.join(path, file_path)

        # 바이너리 파일 스킵
        if any(full_path.endswith(ext) for ext in binary_extensions):
            continue

        try:
            # 스트리밍 방식으로 파일 읽기
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                files_searched += 1

                for line_num, line in enumerate(f, 1):
                    if max_results and len(results) >= max_results:
                        truncated = True
                        break

                    # 매칭 확인
                    match = regex.search(line)
                    if match:
                        results.append({
                            'file': file_path.replace(os.sep, '/'),
                            'line': line_num,
                            'text': line.rstrip()[:200],  # 최대 200자
                            'match': match.group(0)[:100]  # 최대 100자
                        })

                    # 큰 파일에서 라인 제한
                    if line_num > 10000:  # 10000줄 이상은 스킵
                        break

        except (IOError, OSError) as e:
            # 파일 읽기 실패는 무시하고 계속
            continue
        except UnicodeDecodeError:
            # 인코딩 오류는 무시
            continue

    return ok(results, 
             count=len(results),
             files_searched=files_searched,
             truncated=truncated)


def find_function(name: str, path: str = ".", strict: bool = False) -> Dict[str, Any]:
    """Python 파일에서 함수 정의 찾기

    Args:
        name: 함수명
        path: 검색 경로

    Returns:
        성공: {
            'ok': True,
            'data': [
                {'file': 'path', 'line': 10, 'definition': 'def func(...):'},
                ...
            ],
            'count': 찾은 개수
        }
        실패: {'ok': False, 'error': 에러메시지}
    """
    if strict:
        try:
            # AST 기반 정확한 검색
            result = _find_function_ast(name, path)
            result['mode'] = 'ast'
            return result
        except Exception as e:
            # 자동 폴백
            import logging
            logging.warning(f"AST search failed: {e}, falling back to regex")

    # 기존 정규식 로직
    # 함수 정의 패턴
    pattern = rf'^\s*def\s+{re.escape(name)}\s*\('

    result = search_code(pattern, path, "*.py")
    if not result['ok']:
        return result

    # 결과를 더 읽기 쉽게 변환
    functions = []
    for match in result['data']:
        functions.append({
            'file': match['file'],
            'line': match['line'],
            'definition': match['text'].strip()
        })

    return ok(functions, count=len(functions), function_name=name)




def _find_function_ast(name: str, path: str) -> Dict[str, Any]:
    """AST 기반 정확한 함수 검색 (주석/문자열 제외)"""
    import ast
    results = []

    # Python 파일 찾기
    py_files_result = search_files("*.py", path)
    if not py_files_result['ok']:
        return py_files_result

    py_files = py_files_result['data'][:100]  # 성능을 위해 제한

    for file_name in py_files:
        try:
            # 파일 읽기
            file_path = os.path.join(path, file_name)
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # AST 파싱
            tree = ast.parse(content, filename=file_path)

            # 함수 찾기
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == name:
                    # 함수 정의 추출
                    lines = content.split('\n')
                    start_line = node.lineno - 1

                    # 간단한 함수 끝 찾기
                    end_line = start_line
                    if start_line < len(lines):
                        indent_level = len(lines[start_line]) - len(lines[start_line].lstrip())
                        for i in range(start_line + 1, min(len(lines), start_line + 50)):
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

        except (SyntaxError, UnicodeDecodeError):
            # 파싱 불가능한 파일은 건너뛰기
            continue
        except Exception:
            # 기타 오류도 건너뛰기
            continue

    return {
        'ok': True,
        'data': results,
        'count': len(results),
        'function_name': name,
        'mode': 'regex'
    }

def find_class(name: str, path: str = ".", strict: bool = False) -> Dict[str, Any]:
    """Python 파일에서 클래스 정의 찾기

    Args:
        name: 클래스명
        path: 검색 경로

    Returns:
        성공: {
            'ok': True,
            'data': [
                {'file': 'path', 'line': 10, 'definition': 'class MyClass:'},
                ...
            ],
            'count': 찾은 개수
        }
        실패: {'ok': False, 'error': 에러메시지}
    """
    if strict:
        try:
            # AST 기반 정확한 검색
            result = _find_class_ast(name, path)
            result['mode'] = 'ast'
            return result
        except Exception as e:
            # 자동 폴백
            import logging
            logging.warning(f"AST search failed: {e}, falling back to regex")

    # 기존 정규식 로직
    # 클래스 정의 패턴
    pattern = rf'^\s*class\s+{re.escape(name)}\s*[\(:]'

    result = search_code(pattern, path, "*.py")
    if not result['ok']:
        return result

    # 결과를 더 읽기 쉽게 변환
    classes = []
    for match in result['data']:
        classes.append({
            'file': match['file'],
            'line': match['line'],
            'definition': match['text'].strip()
        })

    return ok(classes, count=len(classes), class_name=name)




def _find_class_ast(name: str, path: str) -> Dict[str, Any]:
    """AST 기반 정확한 클래스 검색 (주석/문자열 제외)"""
    import ast
    results = []

    # Python 파일 찾기
    py_files_result = search_files("*.py", path)
    if not py_files_result['ok']:
        return py_files_result

    py_files = py_files_result['data'][:100]  # 성능을 위해 제한

    for file_name in py_files:
        try:
            # 파일 읽기
            file_path = os.path.join(path, file_name)
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # AST 파싱
            tree = ast.parse(content, filename=file_path)

            # 클래스 찾기
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and node.name == name:
                    # 클래스 정의 추출
                    lines = content.split('\n')
                    start_line = node.lineno - 1

                    # 간단한 클래스 끝 찾기
                    end_line = start_line
                    if start_line < len(lines):
                        indent_level = len(lines[start_line]) - len(lines[start_line].lstrip())
                        for i in range(start_line + 1, min(len(lines), start_line + 100)):
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

        except (SyntaxError, UnicodeDecodeError):
            continue
        except Exception:
            continue

    return {
        'ok': True,
        'data': results,
        'count': len(results),
        'class_name': name,
        'mode': 'regex'
    }

def grep(pattern: str, path: str = ".", context: int = 0) -> Dict[str, Any]:
    """간단한 텍스트 검색 (grep과 유사)

    Args:
        pattern: 검색할 텍스트 (대소문자 구분 없음)
        path: 파일 또는 디렉토리 경로
        context: 전후 컨텍스트 줄 수

    Returns:
        성공: {
            'ok': True,
            'data': [
                {
                    'file': 'path',
                    'line': 10,
                    'text': '매칭된 줄',
                    'before': ['이전 줄들...'],  # context > 0일 때
                    'after': ['다음 줄들...']     # context > 0일 때
                },
                ...
            ],
            'count': 매칭 수
        }
        실패: {'ok': False, 'error': 에러메시지}
    """
    try:
        path_obj = Path(path)
        matches = []

        # 단일 파일인 경우
        if path_obj.is_file():
            result = _grep_file(path_obj, pattern, context)
            if result:
                matches.extend(result)

        # 디렉토리인 경우
        elif path_obj.is_dir():
            # 텍스트 파일만 검색
            text_extensions = {'.txt', '.py', '.js', '.ts', '.md', '.json', '.yml', '.yaml', 
                             '.xml', '.html', '.css', '.sh', '.bat', '.cfg', '.ini'}

            for file_path in path_obj.rglob('*'):
                if file_path.is_file() and file_path.suffix in text_extensions:
                    result = _grep_file(file_path, pattern, context)
                    if result:
                        matches.extend(result)
        else:
            return err(f"Path not found: {path}")

        return ok(matches, count=len(matches), pattern=pattern)

    except Exception as e:
        return err(f"Grep error: {e}")


def _grep_file(file_path: Path, pattern: str, context: int = 0) -> List[Dict[str, Any]]:
    """파일 하나에서 grep 수행 (내부 함수)"""
    matches = []
    pattern_lower = pattern.lower()
    # 정규식 캐시 사용 (옵션)
    import re
    use_regex = False  # 필요시 활성화

    try:
        lines = file_path.read_text(encoding='utf-8', errors='ignore').splitlines()

        for i, line in enumerate(lines):
            if pattern_lower in line.lower():
                match = {
                    'file': str(file_path),
                    'line': i + 1,
                    'text': line
                }

                # 컨텍스트 추가
                if context > 0:
                    start = max(0, i - context)
                    end = min(len(lines), i + context + 1)

                    match['before'] = lines[start:i]
                    match['after'] = lines[i+1:end]

                matches.append(match)

    except:
        # 읽을 수 없는 파일은 무시
        pass

    return matches


def find_in_file(file_path: str, pattern: str) -> Dict[str, Any]:
    """특정 파일에서만 패턴 검색

    Args:
        file_path: 파일 경로
        pattern: 검색 패턴 (정규식)

    Returns:
        성공: {'ok': True, 'data': [{'line': 10, 'text': '...', 'match': '...'}, ...]}
        실패: {'ok': False, 'error': 에러메시지}
    """
    if not Path(file_path).exists():
        return err(f"File not found: {file_path}")

    result = search_code(pattern, os.path.dirname(file_path) or '.', 
                        os.path.basename(file_path))

    if result['ok']:
        # 파일 경로 제거 (이미 알고 있으므로)
        for match in result['data']:
            del match['file']

    return result