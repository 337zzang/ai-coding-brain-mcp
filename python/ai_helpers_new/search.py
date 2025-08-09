#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
search.py - AI Helpers Search Module (개선된 버전)
생성일: 2025-08-09

주요 개선사항:
- 치명적 버그 4개 수정 (중복 정의, 외부 의존, AST mode, 소스 추출)
- 성능 개선 5개 적용 (제너레이터, 스트리밍, 캐싱 등)
- 코드 품질 개선 4개 (예외 처리, 테스트 패턴, 통합, 옵션)

v2.0.0 - Complete rewrite with bug fixes and performance improvements
"""


# search.py 개선 버전 - Part 1: 유틸리티 함수들
import os
import re
import ast
import sys
from pathlib import Path
from typing import Dict, Any, List, Generator, Optional
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)

# 바이너리 파일 감지용 상수
NULL_BYTE = b'\x00'

def is_binary_file(file_path: str, sample_size: int = 8192) -> bool:
    """널 바이트로 바이너리 파일 감지"""
    try:
        with open(file_path, 'rb') as f:
            chunk = f.read(sample_size)
            return NULL_BYTE in chunk
    except (FileNotFoundError, PermissionError, IOError):
        return True  # 읽기 실패시 바이너리로 간주

# 캐시 관리
_caches = []

def _register_cache(func):
    """캐시된 함수 등록"""
    if hasattr(func, 'cache_clear'):
        _caches.append(func)
    return func

def clear_all_caches():
    """모든 등록된 캐시 클리어"""
    for cache in _caches:
        if hasattr(cache, 'cache_clear'):
            cache.cache_clear()
def search_files_generator(
    path: str, 
    pattern: str = "*",
    max_depth: Optional[int] = None,
    exclude_patterns: Optional[set] = None
) -> Generator[str, None, None]:
    """
    파일을 발견하는 즉시 yield하는 제너레이터
    메모리 효율적이고 조기 종료 가능
    """
    exclude_patterns = exclude_patterns or {'.git', '__pycache__', 'node_modules'}
    base_path = Path(path).resolve()

    def should_exclude(file_path: Path) -> bool:
        for part in file_path.parts:
            if any(pattern in part for pattern in exclude_patterns):
                return True
        return False

    def walk_with_depth(current_path: Path, current_depth: int = 0):
        if max_depth is not None and current_depth > max_depth:
            return

        try:
            for item in current_path.iterdir():
                if should_exclude(item):
                    continue

                if item.is_file():
                    if pattern == "*" or item.match(pattern):
                        yield str(item)
                elif item.is_dir():
                    yield from walk_with_depth(item, current_depth + 1)
        except (PermissionError, OSError) as e:
            logger.debug(f"Cannot access {current_path}: {e}")

    yield from walk_with_depth(base_path)
@lru_cache(maxsize=256)
@_register_cache
def _load_ast_cached(file_path: str) -> tuple:
    """파일을 읽어 AST와 소스 텍스트를 캐싱"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        tree = ast.parse(source, file_path)
        return tree, source
    except (SyntaxError, UnicodeDecodeError) as e:
        logger.debug(f"Cannot parse {file_path}: {e}")
        return None, None

def _find_function_ast(
    file_path: str, 
    name: str,
    strict: bool = False
) -> Generator[Dict[str, Any], None, None]:
    """
    AST를 사용한 함수 검색
    Python 3.8+에서는 ast.get_source_segment 사용
    """
    tree, source = _load_ast_cached(file_path)
    if tree is None:
        return

    pattern = re.compile(name if strict else f".*{name}.*", re.IGNORECASE)

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and pattern.search(node.name):
            # Python 3.8+ - 정확한 소스 추출
            if sys.version_info >= (3, 8):
                definition = ast.get_source_segment(source, node)
            else:
                # Python 3.7 이하 - 라인 기반 추출
                start_line = node.lineno - 1
                end_line = start_line + 50  # 합리적인 기본값
                lines = source.split('\n')
                definition = '\n'.join(lines[start_line:end_line])

            # 데코레이터 정보 추가
            decorators = [d.id if hasattr(d, 'id') else str(d) 
                         for d in node.decorator_list]

            yield {
                'file': file_path,
                'name': node.name,
                'line': node.lineno,
                'definition': definition,
                'decorators': decorators,
                'mode': 'ast',  # 수정됨: 'regex' -> 'ast'
                'type': 'function'
            }

def _find_class_ast(
    file_path: str,
    name: str,
    strict: bool = False  
) -> Generator[Dict[str, Any], None, None]:
    """
    AST를 사용한 클래스 검색
    상속 정보 포함
    """
    tree, source = _load_ast_cached(file_path)
    if tree is None:
        return

    pattern = re.compile(name if strict else f".*{name}.*", re.IGNORECASE)

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and pattern.search(node.name):
            # Python 3.8+ - 정확한 소스 추출
            if sys.version_info >= (3, 8):
                definition = ast.get_source_segment(source, node)
            else:
                # Python 3.7 이하
                start_line = node.lineno - 1
                end_line = start_line + 100
                lines = source.split('\n')
                definition = '\n'.join(lines[start_line:end_line])

            # 상속 정보 추출
            bases = []
            for base in node.bases:
                if hasattr(base, 'id'):
                    bases.append(base.id)
                elif hasattr(base, 'attr'):
                    bases.append(f"{base.value.id if hasattr(base.value, 'id') else '?'}.{base.attr}")

            yield {
                'file': file_path,
                'name': node.name,
                'line': node.lineno,
                'definition': definition,
                'bases': bases,
                'mode': 'ast',  # 수정됨: 'regex' -> 'ast'
                'type': 'class'
            }
def search_code(
    pattern: str,
    path: str = ".",
    file_pattern: str = "*.py",
    max_results: int = 100,
    context_lines: int = 0,
    context: Optional[int] = None,
    use_regex: bool = True,
    case_sensitive: bool = False
) -> Dict[str, Any]:
    """
    개선된 코드 검색 - 제너레이터 기반으로 조기 종료 지원
    grep 기능 통합 (context_lines, context, case_sensitive 옵션)

    Args:
        pattern: 검색할 패턴
        path: 검색 경로
        file_pattern: 파일 패턴
        max_results: 최대 결과 수
        context_lines: 컨텍스트 라인 수 (이전/이후)
        context: context_lines의 별칭 (호환성을 위해 추가)
        use_regex: 정규식 사용 여부
        case_sensitive: 대소문자 구분
"""
    # context가 주어지면 context_lines 대신 사용
    if context is not None:
        context_lines = context

    results = []

    # 패턴 컴파일
    if use_regex:
        flags = 0 if case_sensitive else re.IGNORECASE
        try:
            regex = re.compile(pattern, flags)
        except re.error as e:
            return {'ok': False, 'error': f"Invalid regex: {e}"}
    else:
        # 리터럴 검색
        search_pattern = pattern if case_sensitive else pattern.lower()

    # 제너레이터 기반 파일 탐색
    for file_path in search_files_generator(path, file_pattern):
        if is_binary_file(file_path):
            continue

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = []
                for line_num, line in enumerate(f, 1):
                    lines.append(line.rstrip())

                    # 매치 확인
                    matched = False
                    if use_regex:
                        matched = regex.search(line)
                    else:
                        test_line = line if case_sensitive else line.lower()
                        matched = search_pattern in test_line

                    if matched:
                        # 컨텍스트 수집
                        start = max(0, line_num - context_lines - 1)
                        end = min(len(lines), line_num + context_lines)

                        results.append({
                            'file': file_path,
                            'line': line_num,
                            'match': line.rstrip(),
                            'context': lines[start:end] if context_lines > 0 else None
                        })

                        # 조기 종료
                        if len(results) >= max_results:
                            return {'ok': True, 'data': results}

        except (PermissionError, UnicodeDecodeError, IOError) as e:
            logger.debug(f"Cannot read {file_path}: {e}")
            continue

    return {'ok': True, 'data': results}

def find_in_file(
    file_path: str,
    pattern: str,
    context_lines: int = 2
) -> Dict[str, Any]:
    """
    단일 파일 내 검색 (수정됨: h.search_code 대신 search_code 호출)
    """
    # 파일이 존재하는지 확인
    if not os.path.isfile(file_path):
        return {'ok': False, 'error': f"File not found: {file_path}"}

    # search_code를 직접 호출 (h.search_code 대신)
    result = search_code(
        pattern,
        os.path.dirname(file_path) or '.',
        os.path.basename(file_path),
        context_lines=context_lines
    )

    return result

def grep(
    pattern: str,
    path: str = ".",
    context: int = 2,
    file_pattern: str = "*.py",
    use_regex: bool = False
) -> Dict[str, Any]:
    """
    grep 스타일 검색 - search_code로 리다이렉트
    """
    return search_code(
        pattern=pattern,
        path=path,
        file_pattern=file_pattern,
        context_lines=context,
        use_regex=use_regex,
        case_sensitive=False
    )
@lru_cache(maxsize=32)
@_register_cache
def get_statistics(
    path: str = ".",
    include_tests: bool = False
) -> Dict[str, Any]:
    """
    코드베이스 통계 - 단일 구현, 캐싱 적용
    메모리 효율적인 라인 카운팅
    """
    stats = {
        'total_files': 0,
        'total_lines': 0,
        'py_files': 0,
        'py_lines': 0,
        'test_files': 0,
        'test_lines': 0,
        'file_types': {},
        'largest_files': []
    }

    # 표준 테스트 파일 패턴
    test_patterns = [
        'test_*.py', '*_test.py',
        'tests/', 'test/', '__tests__/'
    ]

    def is_test_file(file_path: str) -> bool:
        """표준 테스트 파일 패턴 매칭"""
        path_str = str(file_path).replace('\\', '/')

        # 디렉토리 기반 확인
        if any(f'/{pattern}' in path_str for pattern in ['tests/', 'test/', '__tests__/']):
            return True

        # 파일명 기반 확인
        filename = os.path.basename(file_path)
        return filename.startswith('test_') or filename.endswith('_test.py')

    file_sizes = []

    for file_path in search_files_generator(path, "*"):
        if is_binary_file(file_path):
            continue

        try:
            # 메모리 효율적인 라인 카운팅
            line_count = 0
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for _ in f:
                    line_count += 1

            # 통계 업데이트
            stats['total_files'] += 1
            stats['total_lines'] += line_count

            # 파일 타입별 통계
            ext = os.path.splitext(file_path)[1].lower()
            if ext not in stats['file_types']:
                stats['file_types'][ext] = {'files': 0, 'lines': 0}
            stats['file_types'][ext]['files'] += 1
            stats['file_types'][ext]['lines'] += line_count

            # Python 파일 통계
            if ext == '.py':
                stats['py_files'] += 1
                stats['py_lines'] += line_count

                # 테스트 파일 통계
                if is_test_file(file_path):
                    stats['test_files'] += 1
                    stats['test_lines'] += line_count

            # 가장 큰 파일 추적
            file_sizes.append((line_count, file_path))

        except (PermissionError, UnicodeDecodeError, IOError) as e:
            logger.debug(f"Cannot process {file_path}: {e}")
            continue

    # 가장 큰 파일 Top 10
    file_sizes.sort(reverse=True)
    stats['largest_files'] = [
        {'file': path, 'lines': lines}
        for lines, path in file_sizes[:10]
    ]

    # 테스트 제외 옵션
    if not include_tests:
        stats['py_files'] -= stats['test_files']
        stats['py_lines'] -= stats['test_lines']

    return {'ok': True, 'data': stats}

def search_imports(module_name: str, path: str = ".") -> Dict[str, Any]:
    """
    특정 모듈의 import 문을 검색
    """
    import_patterns = [
        f"^import {module_name}",
        f"^from {module_name}",
        f"import.*{module_name}",
    ]

    results = []
    for pattern in import_patterns:
        result = search_code(
            pattern=pattern,
            path=path,
            file_pattern="*.py",
            use_regex=True
        )
        if result['ok']:
            results.extend(result['data'])

    # 중복 제거
    unique_results = []
    seen = set()
    for r in results:
        key = (r['file'], r['line'])
        if key not in seen:
            seen.add(key)
            unique_results.append(r)

    return {'ok': True, 'data': unique_results}

# 최종 API 함수들
def search_function(name: str, path: str = ".", strict: bool = False) -> Dict[str, Any]:
    """함수 검색 - AST 기반"""
    results = []

    for file_path in search_files_generator(path, "*.py"):
        try:
            for func_info in _find_function_ast(file_path, name, strict):
                results.append(func_info)
        except Exception as e:
            logger.debug(f"Error processing {file_path}: {e}")
            continue

    return {'ok': True, 'data': results}

def search_class(name: str, path: str = ".", strict: bool = False) -> Dict[str, Any]:
    """클래스 검색 - AST 기반"""
    results = []

    for file_path in search_files_generator(path, "*.py"):
        try:
            for class_info in _find_class_ast(file_path, name, strict):
                results.append(class_info)
        except Exception as e:
            logger.debug(f"Error processing {file_path}: {e}")
            continue

    return {'ok': True, 'data': results}

# 캐시 정보
def get_cache_info() -> Dict[str, Any]:
    """캐시 상태 정보"""
    info = {}
    for cache in _caches:
        if hasattr(cache, 'cache_info'):
            cache_info = cache.cache_info()
            info[cache.__name__] = {
                'hits': cache_info.hits,
                'misses': cache_info.misses,
                'size': cache_info.currsize,
                'maxsize': cache_info.maxsize
            }
    return {'ok': True, 'data': info}

def clear_cache():
    """모든 캐시 클리어"""
    clear_all_caches()
    return {'ok': True, 'data': 'All caches cleared'}


# ============================================
# Namespace Style Wrapper (Facade Pattern)
# ============================================

class SearchNamespace:
    """검색 함수들을 위한 네임스페이스 (Facade 패턴)"""

    @staticmethod
    def files(pattern="*", path=".", max_depth=None, exclude_patterns=None):
        """파일 검색 (리스트 반환)"""
        try:
            result = list(search_files_generator(path, pattern, max_depth, exclude_patterns))
            # wrap_output 형식으로 반환
            return {'ok': True, 'data': result}
        except Exception as e:
            return {'ok': False, 'error': str(e), 'data': []}

    @staticmethod
    def code(pattern, path=".", file_pattern="*.py", **kwargs):
        """코드 내용 검색 - context와 context_lines 모두 지원"""
        # search_code 함수가 이제 context를 직접 처리하므로 그대로 전달
        return search_code(pattern, path, file_pattern, **kwargs)

    @staticmethod
    def function(name, path=".", strict=False):
        """함수 검색 (AST 기반)"""
        return search_function(name, path, strict)

    @staticmethod
    def class_(name, path=".", strict=False):
        """클래스 검색 (AST 기반)"""
        return search_class(name, path, strict)

    @staticmethod
    def imports(module_name, path="."):
        """import 문 검색"""
        return search_imports(module_name, path)

    @staticmethod
    def statistics(path=".", include_tests=False):
        """코드베이스 통계"""
        return get_statistics(path, include_tests)

    @staticmethod
    def grep(pattern, path=".", context=2, **kwargs):
        """grep 스타일 검색"""
        return grep(pattern, path, context, **kwargs)

# 네임스페이스 인스턴스 생성
search = SearchNamespace()

# ============================================
# Legacy Compatibility Aliases (하위 호환성)
# ============================================

# 기존 함수명 별칭 (기존 코드 호환성 유지)
search_files = lambda path=".", pattern="*", **kwargs: search.files(pattern, path, **kwargs)
find_function = lambda name, path=".", **kwargs: search.function(name, path, **kwargs)
find_class = lambda name, path=".", **kwargs: search.class_(name, path, **kwargs)

# 표준 래퍼 적용 함수들 export
__all__ = [
    # Core functions
    'search_files_generator',
    'search_code',
    'search_function', 
    'search_class',
    'search_imports',
    'get_statistics',
    'grep',
    'find_in_file',

    # Utilities
    'is_binary_file',
    'clear_cache',
    'get_cache_info',

    # Namespace
    'search',
    'SearchNamespace',

    # Legacy aliases
    'search_files',
    'find_function',
    'find_class',
]