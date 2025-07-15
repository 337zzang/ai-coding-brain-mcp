"""
Safe Wrapper - 헬퍼 함수를 안전하게 래핑하는 데코레이터 시스템
"""
import functools
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
    def parse_file(filename):
        """파일을 파싱하여 함수, 클래스 등을 추출"""
        return helpers_obj.parse_with_snippets(filename)

    @safe_return("search")
    def search_code(path, pattern, file_pattern="*"):
        """코드에서 패턴 검색"""
        return helpers_obj.search_code(path, pattern, file_pattern)

    @safe_return("search")  
    def find_function(path, name):
        """함수 찾기"""
        return helpers_obj.find_function(path, name)

    @safe_return("search")
    def find_class(path, name):
        """클래스 찾기"""
        return helpers_obj.find_class(path, name)

    @safe_return("git")
    def git_status():
        """Git 상태 확인"""
        return helpers_obj.git_status()

    @safe_return("replace")
    def replace_block(file, old_code, new_code):
        """코드 블록 교체"""
        return helpers_obj.replace_block(file, old_code, new_code)

    @safe_return("scan")
    def scan_directory(path="."):
        """디렉토리 스캔"""
        return helpers_obj.scan_directory_dict(path)

    # 기타 안전한 래퍼들
    def read_file(path):
        """파일 읽기 (원본 그대로)"""
        return helpers_obj.read_file(path)

    def write_file(path, content):
        """파일 쓰기 (원본 그대로)"""
        return helpers_obj.write_file(path, content)

    def create_file(path, content):
        """파일 생성 (원본 그대로)"""
        return helpers_obj.create_file(path, content)

    # workflow는 원본 그대로
    def workflow(command):
        """워크플로우 명령"""
        return helpers_obj.execute_workflow_command(command)

    # git 명령들
    def git_add(path):
        """Git add"""
        return helpers_obj.git_add(path)

    def git_commit(message):
        """Git commit"""
        return helpers_obj.git_commit(message)

    def git_push():
        """Git push"""
        return helpers_obj.git_push()

    # 모든 안전한 함수들을 딕셔너리로 반환
    return {
        # 파일 작업
        'parse_file': parse_file,
        'read_file': read_file,
        'write_file': write_file,
        'create_file': create_file,

        # 검색
        'search_code': search_code,
        'find_function': find_function,
        'find_class': find_class,

        # 코드 수정
        'replace_block': replace_block,

        # Git
        'git_status': git_status,
        'git_add': git_add,
        'git_commit': git_commit,
        'git_push': git_push,

        # 디렉토리
        'scan_directory': scan_directory,

        # 워크플로우
        'workflow': workflow,
        'wf': workflow,  # 단축 버전
    }

def register_safe_helpers(helpers_obj, globals_dict):
    """안전한 헬퍼들을 전역 네임스페이스에 등록"""
    safe_funcs = create_safe_helpers(helpers_obj)

    # 전역 네임스페이스에 등록
    for name, func in safe_funcs.items():
        globals_dict[name] = func

    # 사용 가능한 함수 목록 출력
    print("✅ 안전한 헬퍼 함수 등록 완료:", file=sys.stderr)
    for name in sorted(safe_funcs.keys()):
        if not name.startswith('_'):
            print(f"  - {name}()", file=sys.stderr)

    return safe_funcs
