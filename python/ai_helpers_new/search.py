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
from .wrappers import wrap_output


def search_files(pattern: str, path: str = ".", recursive: bool = True, max_depth: Optional[int] = None) -> Dict[str, Any]:
    """파일명 패턴으로 파일 검색

    Args:
        pattern: 파일명 패턴 (예: "*.py", "test_*.txt", "test")
        path: 검색 시작 경로 (기본값: 현재 디렉토리)
        recursive: 하위 디렉토리도 검색할지 여부 (기본값: True)
        max_depth: 최대 검색 깊이 (None=무제한, recursive=False시 1)

    Returns:
        성공: {'ok': True, 'data': ['path1', 'path2', ...], 'count': 개수}
        실패: {'ok': False, 'error': 에러메시지}

    Examples:
        h.search_files("*.py")  # 모든 .py 파일
        h.search_files("test")  # 'test'가 포함된 모든 파일
        h.search_files("test*", "src/", max_depth=2)  # src/ 아래 2단계까지
    """
    try:
        found_files = []
        search_path = Path(path)

        if not search_path.exists():
            return err(f"Path not found: {path}")

        # 패턴에 와일드카드가 없으면 양쪽에 추가
        if '*' not in pattern and '?' not in pattern:
            pattern = f"*{pattern}*"

        # recursive=False인 경우 max_depth를 1로 설정
        if not recursive and max_depth is None:
            max_depth = 1

        # 현재 깊이 추적을 위한 헬퍼 함수
        def search_with_depth(current_path, current_depth=0):
            # max_depth 체크
            if max_depth is not None and current_depth >= max_depth:
                return

            try:
                for item in current_path.iterdir():
                    if item.is_file() and fnmatch.fnmatch(item.name, pattern):
                        rel_path = os.path.relpath(item, path)
                        found_files.append(rel_path)
                    elif item.is_dir() and not item.name.startswith('.'):
                        if recursive and (max_depth is None or current_depth < max_depth - 1):
                            search_with_depth(item, current_depth + 1)
            except PermissionError:
                pass  # 권한 없는 디렉토리 무시

        # 검색 시작
        search_with_depth(search_path)

        return ok(sorted(found_files), count=len(found_files), pattern=pattern)

    except Exception as e:
        return err(f"Search files error: {e}")


def search_code(pattern: str, path: str = ".", file_pattern: str = "*", max_results: int = 100) -> Dict[str, Any]:
    """파일 내용에서 패턴 검색 (정규식 지원)

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
        # 정규식 컴파일
        try:
            regex = re.compile(pattern, re.IGNORECASE)
        except re.error as e:
            return err(f"Invalid regex pattern: {e}")

        matches = []
        files_searched = 0

        # 파일 목록 가져오기
        files_result = search_files(file_pattern, path, recursive=True)
        if not files_result['ok']:
            return files_result

        for file_path in files_result['data']:
            # 파일 열기 전 체크 - 불필요한 I/O 방지
            if len(matches) >= max_results:
                break
                
            full_path = os.path.join(path, file_path)

            # 바이너리 파일 스킵
            if full_path.endswith(('.pyc', '.pyo', '.so', '.dll', '.exe')):
                continue

            try:
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    files_searched += 1
                    
                    for line_num, line in enumerate(f, 1):
                        match = regex.search(line)
                        if match:
                            matches.append({
                                'file': file_path,
                                'line': line_num,
                                'text': line.rstrip(),
                                'match': match.group(0)
                            })
                            
                            # 정확한 수에 도달하면 즉시 반환
                            if len(matches) == max_results:
                                return ok(
                                    matches,
                                    count=len(matches),
                                    files_searched=files_searched,
                                    truncated=True
                                )
            except:
                # 읽을 수 없는 파일은 스킵
                continue

        return ok(
            matches,
            count=len(matches),
            files_searched=files_searched,
            truncated=len(matches) >= max_results
        )

    except Exception as e:
        return err(f"Search failed: {str(e)}")


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

    for file_path in py_files:
        try:
            # 파일 읽기
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

    for file_path in py_files:
        try:
            # 파일 읽기
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

    result = h.search_code(pattern, os.path.dirname(file_path) or '.', 
                        os.path.basename(file_path))

    if result['ok']:
        # 파일 경로 제거 (이미 알고 있으므로)
        for match in result['data']:
            del match['file']

    return result

# ============= 새로 추가된 함수들 =============


def get_statistics(path: str = ".") -> Dict[str, Any]:
    """코드베이스 통계를 수집합니다.

    Args:
        path: 분석할 경로

    Returns:
        통계 정보 딕셔너리
    """
    from pathlib import Path
    import ast

    stats = {
        "total_files": 0,
        "python_files": 0,
        "total_lines": 0,
        "code_lines": 0,
        "comment_lines": 0,
        "blank_lines": 0,
        "functions": 0,
        "classes": 0,
        "imports": 0
    }

    # Python 파일 검색
    py_files = search_files("*.py", path)
    if not py_files.get("ok"):
        return py_files

    stats["python_files"] = len(py_files["data"])

    for file_path in py_files["data"]:
        try:
            # 파일 읽기
            source = Path(file_path).read_text(encoding="utf-8")
            lines = source.splitlines()

            stats["total_lines"] += len(lines)

            # 라인 유형 분석
            for line in lines:
                stripped = line.strip()
                if not stripped:
                    stats["blank_lines"] += 1
                elif stripped.startswith("#"):
                    stats["comment_lines"] += 1
                else:
                    stats["code_lines"] += 1

            # AST 분석
            try:
                tree = ast.parse(source)
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        stats["functions"] += 1
                    elif isinstance(node, ast.ClassDef):
                        stats["classes"] += 1
                    elif isinstance(node, (ast.Import, ast.ImportFrom)):
                        stats["imports"] += 1
            except SyntaxError:
                pass

        except Exception:
            pass

    # 전체 파일 수 (Python 외)
    all_files = search_files("*", path)
    if all_files.get("ok"):
        stats["total_files"] = len(all_files["data"])

    return {"ok": True, "data": stats}


# 전역 캐시 레지스트리
_CACHE_REGISTRY = []

def _register_cache(func):
    """캐시 함수를 레지스트리에 등록"""
    if hasattr(func, 'cache_info'):
        _CACHE_REGISTRY.append(func)
    return func


def get_cache_info() -> Dict[str, Any]:
    """캐시 정보를 반환합니다.

    Returns:
        캐시 통계 정보
    """
    cache_info = {}

    for func in _CACHE_REGISTRY:
        if hasattr(func, 'cache_info'):
            info = func.cache_info()
            cache_info[func.__name__] = {
                "hits": info.hits,
                "misses": info.misses,
                "maxsize": info.maxsize,
                "currsize": info.currsize,
                "hit_rate": info.hits / (info.hits + info.misses) if (info.hits + info.misses) > 0 else 0
            }

    total_hits = sum(v["hits"] for v in cache_info.values())
    total_misses = sum(v["misses"] for v in cache_info.values())

    return {
        "ok": True,
        "data": {
            "functions": cache_info,
            "total_hits": total_hits,
            "total_misses": total_misses,
            "total_hit_rate": total_hits / (total_hits + total_misses) if (total_hits + total_misses) > 0 else 0
        }
    }


def clear_cache() -> Dict[str, Any]:
    """모든 캐시를 초기화합니다.

    Returns:
        초기화 결과
    """
    cleared = []

    for func in _CACHE_REGISTRY:
        if hasattr(func, 'cache_clear'):
            func.cache_clear()
            cleared.append(func.__name__)

    return {
        "ok": True,
        "data": {
            "cleared_functions": cleared,
            "count": len(cleared)
        }
    }


# Export할 public 함수들
__all__ = [
    'search_files',
    'search_files',
    'search_code',
    'find_function',
    'find_class',
    'grep',
    'find_in_file',
    'search_imports',
    'get_statistics',
    'get_cache_info',
    'clear_cache'
]


@wrap_output
def search_imports(module_name: str, path: str = ".", recursive: bool = True):
    """
    주어진 모듈명이 import되는 모든 위치를 AST로 찾아냅니다.

    Args:
        module_name: 검색할 모듈명
        path: 검색 시작 경로
        recursive: 하위 디렉토리 포함 여부

    Returns:
        {'ok': True, 'data': [{'file': str, 'line': int, 'code': str}, ...]}
    """
    import ast
    from pathlib import Path

    if not module_name:
        raise ValueError('module_name must be non-empty')

    results = []
    search_path = Path(path).resolve()

    # Python 파일 찾기
    if recursive:
        py_files = search_path.rglob("*.py")
    else:
        py_files = search_path.glob("*.py")

    for py_file in py_files:
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                source = f.read()
                lines = source.splitlines()

            # AST 파싱
            try:
                tree = ast.parse(source, filename=str(py_file))
            except SyntaxError:
                continue  # 구문 오류가 있는 파일은 건너뛰기

            # AST 노드 순회
            for node in ast.walk(tree):
                found = False
                line_no = 0

                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name == module_name or alias.name.startswith(f"{module_name}."):
                            found = True
                            line_no = node.lineno
                            break

                elif isinstance(node, ast.ImportFrom):
                    if node.module and (node.module == module_name or 
                                       node.module.startswith(f"{module_name}.")):
                        found = True
                        line_no = node.lineno

                if found and line_no > 0:
                    # 해당 라인의 코드 가져오기
                    code_line = lines[line_no - 1] if line_no <= len(lines) else ""

                    # 상대 경로로 변환
                    try:
                        relative_path = py_file.relative_to(Path.cwd())
                    except:
                        relative_path = py_file

                    results.append({
                        'file': str(relative_path),
                        'line': line_no,
                        'code': code_line.strip()
                    })

        except Exception as e:
            continue  # 파일 읽기 오류는 무시

    return results


@wrap_output
def get_statistics(path: str = ".", include_tests: bool = False):
    """
    코드베이스 통계를 수집합니다.

    Args:
        path: 분석할 경로
        include_tests: 테스트 파일 포함 여부

    Returns:
        {'ok': True, 'data': {stats...}}
    """
    from pathlib import Path
    import ast

    stats = {
        'total_files': 0,
        'python_files': 0,
        'total_lines': 0,
        'code_lines': 0,
        'comment_lines': 0,
        'blank_lines': 0,
        'functions': 0,
        'classes': 0,
        'imports': 0,
        'files_with_errors': 0,
        'largest_file': None,
        'most_complex_file': None,
        'by_extension': {}
    }

    search_path = Path(path).resolve()
    largest_lines = 0
    most_functions = 0

    for py_file in search_path.rglob("*"):
        if py_file.is_file():
            # 파일 확장자별 카운트
            ext = py_file.suffix
            stats['by_extension'][ext] = stats['by_extension'].get(ext, 0) + 1
            stats['total_files'] += 1

            if ext == '.py':
                # 테스트 파일 제외 옵션
                if not include_tests and ('test' in py_file.name.lower() or 
                                         'test' in str(py_file.parent).lower()):
                    continue

                stats['python_files'] += 1

                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        lines = f.readlines()

                    file_lines = len(lines)
                    stats['total_lines'] += file_lines

                    # 가장 큰 파일 추적
                    if file_lines > largest_lines:
                        largest_lines = file_lines
                        stats['largest_file'] = {
                            'path': str(py_file.relative_to(search_path)),
                            'lines': file_lines
                        }

                    # 라인 타입 분석
                    for line in lines:
                        stripped = line.strip()
                        if not stripped:
                            stats['blank_lines'] += 1
                        elif stripped.startswith('#'):
                            stats['comment_lines'] += 1
                        else:
                            stats['code_lines'] += 1

                    # AST 분석
                    try:
                        source = ''.join(lines)
                        tree = ast.parse(source)

                        file_functions = 0
                        file_classes = 0
                        file_imports = 0

                        for node in ast.walk(tree):
                            if isinstance(node, ast.FunctionDef):
                                stats['functions'] += 1
                                file_functions += 1
                            elif isinstance(node, ast.ClassDef):
                                stats['classes'] += 1
                                file_classes += 1
                            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                                stats['imports'] += 1
                                file_imports += 1

                        # 가장 복잡한 파일 추적
                        complexity = file_functions + file_classes
                        if complexity > most_functions:
                            most_functions = complexity
                            stats['most_complex_file'] = {
                                'path': str(py_file.relative_to(search_path)),
                                'functions': file_functions,
                                'classes': file_classes
                            }

                    except SyntaxError:
                        stats['files_with_errors'] += 1

                except Exception:
                    pass  # 파일 읽기 오류 무시

    # 비율 계산
    if stats['total_lines'] > 0:
        stats['code_ratio'] = round(stats['code_lines'] / stats['total_lines'] * 100, 2)
        stats['comment_ratio'] = round(stats['comment_lines'] / stats['total_lines'] * 100, 2)

    return stats

