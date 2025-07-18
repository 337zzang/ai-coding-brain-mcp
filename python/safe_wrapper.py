"""
Safe Wrapper - 헬퍼 함수를 안전하게 래핑하는 데코레이터 시스템
중복 방지 버전
"""
import functools
import sys
from typing import Any, Callable, Dict, List, Optional, Union

def safe_return(return_type: str = "auto"):
    """헬퍼 함수의 반환값을 안전하게 처리하는 데코레이터"""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)

                # 반환 타입별 처리
                if return_type == "parse":
                    return _handle_parse_result(result)
                elif return_type == "search":
                    return _handle_search_result(result)
                elif return_type == "git":
                    return _handle_git_result(result)
                elif return_type == "replace":
                    return _handle_replace_result(result)
                elif return_type == "scan":
                    return _handle_scan_result(result)
                else:
                    # auto 모드: 결과를 분석해서 적절히 처리
                    return _auto_handle_result(result)

            except Exception as e:
                return {
                    'success': False,
                    'error': str(e),
                    'error_type': type(e).__name__
                }

        # 안전한 함수임을 표시
        wrapper._is_safe_wrapper = True
        return wrapper
    return decorator

def _handle_parse_result(result):
    """parse_with_snippets 결과 처리"""
    if not isinstance(result, dict) or not result.get('success', False):
        return {
            'success': False,
            'functions': [],
            'classes': [],
            'methods': [],
            'all_snippets': []
        }

    snippets = result.get('snippets', [])
    functions = []
    classes = []
    methods = []

    for s in snippets:
        info = {
            'name': getattr(s, 'name', 'unknown'),
            'type': getattr(s, 'type', 'unknown'),
            'start': getattr(s, 'start_line', 0),
            'end': getattr(s, 'end_line', 0),
            'code': getattr(s, 'content', ''),
            'lines': getattr(s, 'end_line', 0) - getattr(s, 'start_line', 0) + 1
        }

        if info['type'] == 'function':
            functions.append(info)
        elif info['type'] == 'class':
            classes.append(info)
        elif info['type'] == 'method':
            methods.append(info)

    return {
        'success': True,
        'functions': functions,
        'classes': classes,
        'methods': methods,
        'total_lines': result.get('total_lines', 0),
        'snippet_count': len(snippets)
    }

def _handle_search_result(results):
    """search_code, find_function 등의 결과 처리"""
    if not isinstance(results, list):
        return []

    clean_results = []
    for r in results:
        if isinstance(r, dict):
            clean_results.append({
                'file': r.get('file', ''),
                'line': r.get('line_number', 0),
                'text': r.get('line', '').strip(),
                'context': r.get('context', [])
            })

    return clean_results

def _handle_git_result(status):
    """git_status 결과 처리"""
    if not isinstance(status, dict):
        return {
            'success': False,
            'is_clean': True,
            'modified': [],
            'untracked': [],
            'staged': []
        }

    return {
        'success': status.get('success', False),
        'is_clean': status.get('clean', True),
        'modified': status.get('modified', []),
        'untracked': status.get('untracked', []),
        'staged': status.get('staged', [])
    }

def _handle_replace_result(result):
    """replace_block 결과 처리"""
    if not isinstance(result, dict):
        return {'success': False, 'error': 'Invalid return type'}

    return {
        'success': result.get('success', False),
        'file': result.get('filepath', ''),
        'backup': result.get('backup_path', ''),
        'changes': result.get('lines_changed', 0),
        'error': result.get('error', '')
    }

def _handle_scan_result(result):
    """scan_directory_dict 결과 처리"""
    if not isinstance(result, dict):
        return {'files': [], 'dirs': [], 'error': 'Invalid return type'}

    structure = result.get('structure', {})
    files = []
    dirs = []

    for name, info in structure.items():
        if isinstance(info, dict):
            item = {
                'name': name,
                'type': info.get('type', 'unknown'),
                'size': info.get('size', 0),
                'modified': info.get('modified', 0),
                'path': f"{result.get('root', '.')}/{name}"
            }

            if item['type'] == 'file':
                files.append(item)
            elif item['type'] == 'directory':
                dirs.append(item)

    return {
        'files': sorted(files, key=lambda x: x['name']),
        'dirs': sorted(dirs, key=lambda x: x['name']),
        'total_files': len(files),
        'total_dirs': len(dirs),
        'root': result.get('root', '.')
    }

def _auto_handle_result(result):
    """자동으로 결과 타입을 판단해서 처리"""
    if isinstance(result, dict):
        # git_status 스타일
        if 'clean' in result and 'modified' in result:
            return _handle_git_result(result)
        # parse_with_snippets 스타일
        elif 'snippets' in result:
            return _handle_parse_result(result)
        # replace_block 스타일
        elif 'filepath' in result and 'backup_path' in result:
            return _handle_replace_result(result)
        # scan_directory_dict 스타일
        elif 'structure' in result and 'root' in result:
            return _handle_scan_result(result)
        else:
            return result
    elif isinstance(result, list):
        # search 결과 스타일
        if result and isinstance(result[0], dict) and 'line_number' in result[0]:
            return _handle_search_result(result)
        else:
            return result
    else:
        return result

def create_safe_helpers(helpers_obj):
    """헬퍼 객체를 받아서 안전한 버전의 함수들을 생성"""

    # 안전한 래퍼 함수들 정의
    @safe_return("parse")
    def safe_parse_file(filename):
        """파일을 파싱하여 함수, 클래스 등을 추출"""
        return helpers_obj.parse_with_snippets(filename)

    @safe_return("search")
    def safe_search_code(path, pattern, file_pattern="*"):
        """코드에서 패턴 검색"""
        return helpers_obj.search_code(path, pattern, file_pattern)

    @safe_return("search")  
    def safe_find_function(path, name):
        """함수 찾기"""
        return helpers_obj.find_function(path, name)

    @safe_return("search")
    def safe_find_class(path, name):
        """클래스 찾기"""
        return helpers_obj.find_class(path, name)

    @safe_return("git")
    def safe_git_status():
        """Git 상태 확인"""
        return helpers_obj.git_status()

    @safe_return("replace")
    def safe_replace_block(file, old_code, new_code):
        """코드 블록 교체"""
        return helpers_obj.replace_block(file, old_code, new_code)

    @safe_return("scan")
    def safe_scan_directory(path="."):
        """디렉토리 스캔"""
        return helpers_obj.scan_directory_dict(path)

    # 안전한 함수들을 딕셔너리로 반환 (safe_ 접두사 포함)
    return {
        # 파일 작업 - 새로운 이름으로만
        'safe_parse_file': safe_parse_file,
        'safe_search_code': safe_search_code,
        'safe_find_function': safe_find_function,
        'safe_find_class': safe_find_class,
        'safe_replace_block': safe_replace_block,
        'safe_git_status': safe_git_status,
        'safe_scan_directory': safe_scan_directory,
    }

def register_safe_helpers(helpers_obj, globals_dict):
    """안전한 헬퍼들을 전역 네임스페이스에 등록 (중복 방지)"""
    safe_funcs = create_safe_helpers(helpers_obj)

    registered = []
    skipped = []
    replaced = []

    # 우선순위 정의
    priority_functions = {
        'parse_file': 'safe_parse_file',
        'search_code': 'safe_search_code', 
        'find_function': 'safe_find_function',
        'find_class': 'safe_find_class',
        'replace_block': 'safe_replace_block',
        'git_status': 'safe_git_status',
        'scan_directory': 'safe_scan_directory',
    }

    # 기존 함수가 안전한 버전이 아닌 경우만 교체
    for original_name, safe_name in priority_functions.items():
        if safe_name in safe_funcs:
            if original_name in globals_dict:
                # 기존 함수가 안전한 버전인지 확인
                existing_func = globals_dict[original_name]
                if hasattr(existing_func, '_is_safe_wrapper'):
                    skipped.append(original_name)
                else:
                    # 안전한 버전으로 교체
                    globals_dict[original_name] = safe_funcs[safe_name]
                    replaced.append(original_name)
            else:
                # 새로 등록
                globals_dict[original_name] = safe_funcs[safe_name]
                registered.append(original_name)

    # safe_ 버전도 등록 (별칭으로)
    for safe_name, func in safe_funcs.items():
        if safe_name not in globals_dict:
            globals_dict[safe_name] = func
            registered.append(safe_name)

    # 결과 출력
    print("✅ Safe Helper 등록 완료:", file=sys.stderr)
    if registered:
        print(f"  새로 등록: {', '.join(registered)}", file=sys.stderr)
    if replaced:
        print(f"  교체됨: {', '.join(replaced)}", file=sys.stderr)
    if skipped:
        print(f"  건너뜀 (이미 안전): {', '.join(skipped)}", file=sys.stderr)

    return safe_funcs

# 함수가 안전한 버전인지 확인하는 유틸리티
def is_safe_function(func):
    """함수가 안전한 래퍼인지 확인"""
    return hasattr(func, '_is_safe_wrapper') and func._is_safe_wrapper




# HelperResult 임포트 추가
from helper_result import HelperResult, SearchResult, FileResult, ParseResult


def safe_return_v2(return_type: str = "auto"):
    """HelperResult를 활용하는 개선된 safe_return 데코레이터"""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)

                # 반환 타입별 처리
                if return_type == "search":
                    # 검색 결과를 SearchResult로 변환
                    if isinstance(result, list):
                        normalized = _normalize_search_results(result)
                        return SearchResult(results=normalized, success=True)
                    else:
                        return SearchResult(success=False, error="Unexpected search result type")

                elif return_type == "file":
                    # 파일 결과를 FileResult로 변환
                    if isinstance(result, (str, bytes)):
                        path = args[0] if args else None
                        return FileResult(content=result, path=path, success=True)
                    else:
                        return FileResult(success=False, error=str(result))

                elif return_type == "parse":
                    # 파싱 결과를 ParseResult로 변환
                    if isinstance(result, dict):
                        return ParseResult(parsed_data=result, success=True)
                    else:
                        return ParseResult(success=False, error="Unexpected parse result type")

                else:
                    # 일반 결과를 HelperResult로 변환
                    return HelperResult(data=result, success=True)

            except Exception as e:
                # 에러를 적절한 Result 타입으로 변환
                error_msg = str(e)
                error_type = type(e).__name__

                if return_type == "search":
                    return SearchResult(success=False, error=error_msg, error_type=error_type)
                elif return_type == "file":
                    return FileResult(success=False, error=error_msg, error_type=error_type)
                elif return_type == "parse":
                    return ParseResult(success=False, error=error_msg, error_type=error_type)
                else:
                    return HelperResult(success=False, error=error_msg, error_type=error_type)

        return wrapper
    return decorator


def _normalize_search_results(results: List) -> List[Dict]:
    """검색 결과를 표준 형태로 정규화"""
    normalized = []
    for item in results:
        if isinstance(item, dict):
            normalized.append({
                'file': item.get('file', item.get('path', '')),
                'line': item.get('line_number', item.get('line', 0)),
                'text': item.get('content', item.get('text', '')).strip(),
                'context': item.get('context', [])
            })
        elif isinstance(item, str):
            # 단순 파일 경로인 경우
            normalized.append({
                'file': item,
                'line': 0,
                'text': '',
                'context': []
            })
    return normalized


# 개선된 safe helpers 생성
def create_safe_helpers_v2(helpers_obj) -> Dict[str, Callable]:
    """HelperResult를 활용하는 개선된 safe helpers 생성"""

    safe_funcs = {}

    # 검색 함수들
    if hasattr(helpers_obj, 'search_code'):
        @safe_return_v2("search")
        def safe_search_code(pattern, path=".", file_pattern="*.py", **kwargs):
            return helpers_obj.search_code(pattern, path, file_pattern, **kwargs)
        safe_funcs['safe_search_code'] = safe_search_code

    if hasattr(helpers_obj, 'search_files'):
        @safe_return_v2("search") 
        def safe_search_files(path, pattern, **kwargs):
            results = helpers_obj.search_files(path, pattern, **kwargs)
            # 파일 경로 리스트를 검색 결과 형태로 변환
            if isinstance(results, list):
                return [{'file': f} for f in results]
            return results
        safe_funcs['safe_search_files'] = safe_search_files

    # 파일 함수들
    if hasattr(helpers_obj, 'read_file'):
        @safe_return_v2("file")
        def safe_read_file(path, **kwargs):
            return helpers_obj.read_file(path, **kwargs)
        safe_funcs['safe_read_file'] = safe_read_file

    # 파싱 함수들
    if hasattr(helpers_obj, 'parse_file'):
        @safe_return_v2("parse")
        def safe_parse_file(path, **kwargs):
            return helpers_obj.parse_file(path, **kwargs)
        safe_funcs['safe_parse_file'] = safe_parse_file

    return safe_funcs
