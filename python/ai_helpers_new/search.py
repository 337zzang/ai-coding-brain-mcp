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


def search_files(pattern: str, path: str = ".", recursive: bool = True) -> Dict[str, Any]:
    """파일명 패턴으로 파일 검색

    Args:
        pattern: 파일명 패턴 (예: "*.py", "test_*.txt", "test")
        path: 검색 시작 경로 (기본값: 현재 디렉토리)
        recursive: 하위 디렉토리도 검색할지 여부 (기본값: True)

    Returns:
        성공: {'ok': True, 'data': ['path1', 'path2', ...], 'count': 개수}
        실패: {'ok': False, 'error': 에러메시지}

    Examples:
        search_files("*.py")  # 모든 .py 파일
        search_files("test")  # 'test'가 포함된 모든 파일
        search_files("test*", "src/")  # src/ 아래 test로 시작하는 파일
    """
    try:
        found_files = []
        search_path = Path(path)

        if not search_path.exists():
            return err(f"Path not found: {path}")

        # 패턴에 와일드카드가 없으면 양쪽에 추가
        if '*' not in pattern and '?' not in pattern:
            pattern = f"*{pattern}*"

        if recursive:
            # 재귀적으로 검색
            for root, dirs, files in os.walk(search_path):
                # 숨김 디렉토리 제외
                dirs[:] = [d for d in dirs if not d.startswith('.')]

                for file in files:
                    if fnmatch.fnmatch(file, pattern):
                        full_path = os.path.join(root, file)
                        found_files.append(os.path.relpath(full_path, path))
        else:
            # 현재 디렉토리만
            for file in search_path.iterdir():
                if file.is_file() and fnmatch.fnmatch(file.name, pattern):
                    found_files.append(file.name)

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


def find_function(name: str, path: str = ".") -> Dict[str, Any]:
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


def find_class(name: str, path: str = ".") -> Dict[str, Any]:
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

    result = search_code(pattern, os.path.dirname(file_path) or '.', 
                        os.path.basename(file_path))

    if result['ok']:
        # 파일 경로 제거 (이미 알고 있으므로)
        for match in result['data']:
            del match['file']

    return result