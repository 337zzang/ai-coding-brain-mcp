"""
REPL 친화적 code_ops 도구 모음 - 리팩토링 버전
빠른 코드 작업을 위한 2글자 약어 함수들

사용법:
  from q_tools import *

  qp("file.py")              # 파일 구조 분석
  qv("file.py", "func_name") # 함수 코드 보기
  qr("file.py", "func", new_code) # 함수 교체
"""

from typing import Optional, Dict, Any, List
import sys
import os
import re

# 상수 정의
DEFAULT_PREVIEW_SIZE = 1000
DEFAULT_LIST_LIMIT = 10
DEFAULT_FILE_LIMIT = 5
DEFAULT_CONTEXT_LINES = 2

# 에러 메시지 상수
ERROR_HELPERS_NOT_FOUND = "❌ helpers를 찾을 수 없습니다"
ERROR_FILE_NOT_FOUND = "❌ 파일을 찾을 수 없습니다"
ERROR_FUNCTION_NOT_FOUND = "❌ 함수를 찾을 수 없습니다"

def get_helpers_safely():
    """helpers 객체를 안전하게 가져오기"""
    try:
        if 'helpers' in sys.modules['__main__'].__dict__:
            return sys.modules['__main__'].__dict__['helpers']
        return None
    except Exception:
        return None

def handle_helpers_error() -> None:
    """헬퍼 에러 처리"""
    print(ERROR_HELPERS_NOT_FOUND)

def format_list_output(items: List[str], title: str, limit: int = DEFAULT_LIST_LIMIT) -> None:
    """목록 출력 표준화"""
    print(f"📋 {title}: {len(items)}개")

    if not items:
        print("  (없음)")
        return

    for i, item in enumerate(items[:limit], 1):
        print(f"  {i}. {item}")

    if len(items) > limit:
        print(f"  ... 외 {len(items) - limit}개")

def safe_file_operation(func, *args, **kwargs):
    """안전한 파일 작업 실행"""
    try:
        return func(*args, **kwargs)
    except FileNotFoundError:
        print(ERROR_FILE_NOT_FOUND)
        return None
    except Exception as e:
        print(f"❌ 파일 작업 중 오류: {e}")
        return None

def get_safe_parse_file():
    """safe_parse_file 함수 안전하게 가져오기"""
    try:
        return sys.modules['__main__'].__dict__.get('safe_parse_file')
    except Exception:
        return None


def qp(file_path: str) -> Optional[Dict[str, Any]]:
    """Quick Parse - 파일을 빠르게 파싱하고 요약 출력"""
    helpers = get_helpers_safely()
    if not helpers:
        handle_helpers_error()
        return None

    try:
        # safe_parse_file 사용
        result = _parse_file_safely(helpers, file_path)
        if result and result.get('success'):
            _format_parse_result(result, file_path)
            return result
        else:
            print(f"❌ 파일 파싱 실패: {file_path}")
            return None
    except Exception as e:
        print(f"❌ 파싱 중 오류: {e}")
        return None

def _parse_file_safely(helpers, file_path: str) -> Optional[Dict[str, Any]]:
    """파일 파싱 안전 실행"""
    if hasattr(helpers, 'safe_parse_file'):
        return helpers.safe_parse_file(file_path)
    else:
        safe_parse_file = get_safe_parse_file()
        if safe_parse_file:
            return safe_parse_file(file_path)
    return None

def _format_parse_result(result: Dict[str, Any], file_path: str) -> None:
    """파싱 결과 포맷팅"""
    print(f"📄 {file_path}")
    print(f"  함수: {len(result.get('functions', []))}개")
    print(f"  클래스: {len(result.get('classes', []))}개")
    print(f"  전체 라인: {result.get('total_lines', 0)}")

    if result.get('functions'):
        print("\n  함수 목록:")
        for func in result['functions'][:DEFAULT_FILE_LIMIT]:
            name = func.get('name', 'Unknown')
            line = func.get('line', 0)
            print(f"    • {name}() - 라인 {line}")

        if len(result['functions']) > DEFAULT_FILE_LIMIT:
            print(f"    ... 외 {len(result['functions']) - DEFAULT_FILE_LIMIT}개")

    if result.get('classes'):
        print("\n  클래스 목록:")
        for cls in result['classes'][:DEFAULT_FILE_LIMIT]:
            name = cls.get('name', 'Unknown')
            line = cls.get('line', 0)
            print(f"    • {name} - 라인 {line}")

def ql(file_path: str) -> Optional[Dict[str, Any]]:
    """Quick List - 함수/클래스 목록만 빠르게 보기"""
    helpers = get_helpers_safely()
    if not helpers:
        handle_helpers_error()
        return None

    try:
        result = _parse_file_safely(helpers, file_path)
        if result and result.get('success'):
            _format_list_only(result, file_path)
            return result
        return None
    except Exception as e:
        print(f"❌ 목록 조회 중 오류: {e}")
        return None

def _format_list_only(result: Dict[str, Any], file_path: str) -> None:
    """목록만 포맷팅"""
    print(f"📋 {file_path} 목록")

    functions = result.get('functions', [])
    classes = result.get('classes', [])

    if functions:
        func_names = [f['name'] for f in functions]
        format_list_output(func_names, "함수")

    if classes:
        class_names = [c['name'] for c in classes]
        format_list_output(class_names, "클래스")

def qv(file_path: str, func_name: str) -> Optional[str]:
    """Quick View - 함수 코드를 빠르게 보기"""
    helpers = get_helpers_safely()
    if not helpers:
        handle_helpers_error()
        return None

    try:
        # get_function_code 시도
        code = _get_function_code_safely(helpers, file_path, func_name)
        if code:
            print(f"\n📄 {file_path} - {func_name}():")
            print("=" * 60)
            print(code)
            print("=" * 60)
            return code
        else:
            print(ERROR_FUNCTION_NOT_FOUND)
            return None
    except Exception as e:
        print(f"❌ 함수 조회 중 오류: {e}")
        return None

def _get_function_code_safely(helpers, file_path: str, func_name: str) -> Optional[str]:
    """함수 코드 안전 추출"""
    # 1. get_function_code 시도
    if hasattr(helpers, 'get_function_code'):
        return helpers.get_function_code(file_path, func_name)

    # 2. safe_parse_file 사용
    result = _parse_file_safely(helpers, file_path)
    if result and result.get('success'):
        for func in result.get('functions', []):
            if func['name'] == func_name:
                content = helpers.read_file(file_path)
                if content:
                    lines = content.split('\n')
                    start = func.get('start', 0)
                    end = func.get('end', len(lines))
                    return '\n'.join(lines[start:end])

    return None


def qr(file_path: str, func_name: str, new_code: str) -> Optional[Dict[str, Any]]:
    """Quick Replace - 함수를 빠르게 교체"""
    helpers = get_helpers_safely()
    if not helpers:
        handle_helpers_error()
        return None

    try:
        old_code = _get_function_code_safely(helpers, file_path, func_name)
        if not old_code:
            print(ERROR_FUNCTION_NOT_FOUND)
            return None

        # 교체 실행
        replace_result = helpers.replace_block(file_path, old_code, new_code)
        if replace_result and replace_result.get('success'):
            print(f"✅ {func_name} 함수 교체 완료!")
            print(f"   변경된 라인: {replace_result.get('lines_changed', 'Unknown')}")
            return replace_result
        else:
            print(f"❌ 함수 교체 실패: {func_name}")
            return None
    except Exception as e:
        print(f"❌ 함수 교체 중 오류: {e}")
        return None

def qi(file_path: str, target: str, new_code: str, position: str = "after") -> Optional[Dict[str, Any]]:
    """Quick Insert - 특정 위치에 코드 삽입"""
    helpers = get_helpers_safely()
    if not helpers:
        handle_helpers_error()
        return None

    try:
        if hasattr(helpers, 'insert_block'):
            result = helpers.insert_block(file_path, target, new_code, position)
            if result and result.get('success'):
                print(f"✅ 코드 삽입 완료!")
                return result
            else:
                print("❌ 코드 삽입 실패")
                return None
        else:
            print("❌ insert_block 함수를 찾을 수 없습니다")
            return None
    except Exception as e:
        print(f"❌ 코드 삽입 중 오류: {e}")
        return None

def qs(directory: str = ".", pattern: str = "", file_pattern: str = "*.py") -> Optional[List[Dict[str, Any]]]:
    """Quick Search - 코드에서 패턴 검색"""
    helpers = get_helpers_safely()
    if not helpers:
        handle_helpers_error()
        return None

    try:
        results = helpers.search_code(directory, pattern, file_pattern)
        if results:
            print(f"🔍 '{pattern}' 검색 결과: {len(results)}개")
            for i, result in enumerate(results[:DEFAULT_LIST_LIMIT], 1):
                file_path = result.get('file', 'Unknown')
                line_num = result.get('line_number', 0)
                line_content = result.get('line', '').strip()
                print(f"  {i}. {file_path}:{line_num} - {line_content}")

            if len(results) > DEFAULT_LIST_LIMIT:
                print(f"  ... 외 {len(results) - DEFAULT_LIST_LIMIT}개")

            return results
        else:
            print("🔍 검색 결과가 없습니다")
            return []
    except Exception as e:
        print(f"❌ 검색 중 오류: {e}")
        return None

def qg() -> Optional[Dict[str, Any]]:
    """Quick Git - Git 상태 확인"""
    helpers = get_helpers_safely()
    if not helpers:
        handle_helpers_error()
        return None

    try:
        status = helpers.git_status()
        if status and status.get('success'):
            _format_git_status(status)
            return status
        else:
            print("❌ Git 상태 확인 실패")
            return None
    except Exception as e:
        print(f"❌ Git 상태 확인 중 오류: {e}")
        return None

def _format_git_status(status: Dict[str, Any]) -> None:
    """Git 상태 포맷팅"""
    print("📊 Git Status:")
    print(f"  수정됨: {len(status.get('modified', []))}개")
    print(f"  새파일: {len(status.get('untracked', []))}개")
    print(f"  스테이지: {len(status.get('staged', []))}개")

    modified = status.get('modified', [])
    untracked = status.get('untracked', [])

    if modified:
        print("수정된 파일:")
        for f in modified[:DEFAULT_FILE_LIMIT]:
            print(f"  M {f}")
        if len(modified) > DEFAULT_FILE_LIMIT:
            print(f"  ... 외 {len(modified) - DEFAULT_FILE_LIMIT}개")

    if untracked:
        print("추적안됨:")
        for f in untracked[:DEFAULT_FILE_LIMIT]:
            print(f"  ? {f}")
        if len(untracked) > DEFAULT_FILE_LIMIT:
            print(f"  ... 외 {len(untracked) - DEFAULT_FILE_LIMIT}개")

def qc(message: str) -> Optional[Dict[str, Any]]:
    """Quick Commit - 빠른 Git 커밋"""
    helpers = get_helpers_safely()
    if not helpers:
        handle_helpers_error()
        return None

    try:
        # 모든 변경사항 추가
        helpers.git_add(".")

        # 커밋
        result = helpers.git_commit(message)
        if result and result.get('success'):
            print(f"✅ 커밋 완료: {message}")
            return result
        else:
            error_msg = result.get('stderr', 'Unknown error') if result else 'Unknown error'
            print(f"❌ 커밋 실패: {error_msg}")
            return None
    except Exception as e:
        print(f"❌ 커밋 중 오류: {e}")
        return None


def qf(file_path: str) -> Optional[str]:
    """Quick File - 파일 내용 빠르게 읽기"""
    helpers = get_helpers_safely()
    if not helpers:
        handle_helpers_error()
        return None

    try:
        content = helpers.read_file(file_path)
        if content:
            lines = content.split('\n')
            print(f"📄 {file_path} ({len(lines)} lines)")
            print("=" * 60)

            # 내용 미리보기
            if len(content) > DEFAULT_PREVIEW_SIZE:
                print(content[:DEFAULT_PREVIEW_SIZE] + "...")
            else:
                print(content)

            print("=" * 60)
            return content
        else:
            print(ERROR_FILE_NOT_FOUND)
            return None
    except Exception as e:
        print(f"❌ 파일 읽기 중 오류: {e}")
        return None

def qw(file_path: str, content: str) -> bool:
    """Quick Write - 파일 빠르게 쓰기"""
    helpers = get_helpers_safely()
    if not helpers:
        handle_helpers_error()
        return False

    try:
        result = helpers.write_file(file_path, content)
        if result:
            lines = content.split('\n')
            print(f"✅ {file_path} 저장 완료 ({len(lines)} lines)")
            return True
        else:
            print(f"❌ 파일 저장 실패: {file_path}")
            return False
    except Exception as e:
        print(f"❌ 파일 저장 중 오류: {e}")
        return False

def qe(file_path: str) -> bool:
    """Quick Exists - 파일 존재 확인"""
    try:
        exists = os.path.exists(file_path)
        if exists:
            print(f"✅ {file_path} 존재함")
            # 파일 정보 추가
            stat = os.stat(file_path)
            print(f"   크기: {stat.st_size} bytes")
            print(f"   수정: {os.path.getmtime(file_path)}")
        else:
            print(f"❌ {file_path} 존재하지 않음")
        return exists
    except Exception as e:
        print(f"❌ 파일 확인 중 오류: {e}")
        return False

def qls(path: str = ".") -> Optional[List[str]]:
    """Quick List - 디렉토리 내용 보기"""
    helpers = get_helpers_safely()
    if not helpers:
        handle_helpers_error()
        return None

    try:
        items = helpers.list_directory(path)
        if items:
            print(f"📁 {path}:")

            dirs = [i for i in items if "[DIR]" in i]
            files = [i for i in items if "[FILE]" in i]

            if dirs:
                print("디렉토리:")
                for d in sorted(dirs)[:DEFAULT_LIST_LIMIT]:
                    print(f"  📁 {d}")
                if len(dirs) > DEFAULT_LIST_LIMIT:
                    print(f"  ... 외 {len(dirs) - DEFAULT_LIST_LIMIT}개")

            if files:
                print("파일:")
                for f in sorted(files)[:DEFAULT_LIST_LIMIT]:
                    print(f"  📄 {f}")
                if len(files) > DEFAULT_LIST_LIMIT:
                    print(f"  ... 외 {len(files) - DEFAULT_LIST_LIMIT}개")

            return items
        else:
            print(f"📁 {path}: (비어있음)")
            return []
    except Exception as e:
        print(f"❌ 디렉토리 조회 중 오류: {e}")
        return None

def qfind(pattern: str, path: str = ".") -> Optional[List[str]]:
    """Quick Find - 파일 찾기"""
    helpers = get_helpers_safely()
    if not helpers:
        handle_helpers_error()
        return None

    try:
        results = helpers.search_files(path, pattern)
        if results:
            format_list_output(results, f"'{pattern}' 검색 결과")
            return results
        else:
            print(f"🔍 '{pattern}' 검색 결과: 없음")
            return []
    except Exception as e:
        print(f"❌ 파일 검색 중 오류: {e}")
        return None

def qproj(project_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Quick Project - 프로젝트 전환 또는 정보"""
    helpers = get_helpers_safely()
    if not helpers:
        handle_helpers_error()
        return None

    try:
        if project_name:
            # 프로젝트 전환
            if hasattr(helpers, 'cmd_flow_with_context'):
                result = helpers.cmd_flow_with_context(project_name)
                if result:
                    print(f"✅ 프로젝트 전환: {project_name}")
                    return result
                else:
                    print(f"❌ 프로젝트 전환 실패: {project_name}")
                    return None
            else:
                print("❌ 프로젝트 전환 기능을 찾을 수 없습니다")
                return None
        else:
            # 현재 프로젝트 정보
            current_dir = os.getcwd()
            print(f"📁 현재 디렉토리: {current_dir}")
            print(f"📁 프로젝트명: {os.path.basename(current_dir)}")
            return {"current_dir": current_dir, "project_name": os.path.basename(current_dir)}
    except Exception as e:
        print(f"❌ 프로젝트 작업 중 오류: {e}")
        return None

def qm(file_path: str, class_name: str, method_name: str) -> Optional[str]:
    """Quick Method - 클래스의 메서드 코드 보기"""
    helpers = get_helpers_safely()
    if not helpers:
        handle_helpers_error()
        return None

    try:
        result = _parse_file_safely(helpers, file_path)
        if result and result.get('success'):
            for cls in result.get('classes', []):
                if cls['name'] == class_name:
                    # 메서드 찾기 (간단한 구현)
                    content = helpers.read_file(file_path)
                    if content:
                        lines = content.split('\n')
                        # 클래스 내에서 메서드 찾기
                        for i, line in enumerate(lines):
                            if f"def {method_name}(" in line:
                                # 메서드 끝 찾기
                                method_lines = [line]
                                for j in range(i + 1, len(lines)):
                                    if lines[j].strip() and not lines[j].startswith('    ') and not lines[j].startswith('\t'):
                                        break
                                    method_lines.append(lines[j])

                                method_code = '\n'.join(method_lines)
                                print(f"\n📄 {file_path} - {class_name}.{method_name}():")
                                print("=" * 60)
                                print(method_code)
                                print("=" * 60)
                                return method_code

                        print(f"❌ 메서드 '{method_name}'를 찾을 수 없습니다")
                        return None

            print(f"❌ 클래스 '{class_name}'를 찾을 수 없습니다")
            return None
        else:
            print(f"❌ 파일 파싱 실패: {file_path}")
            return None
    except Exception as e:
        print(f"❌ 메서드 조회 중 오류: {e}")
        return None


def qd(file_path: str) -> Optional[str]:
    """Quick Diff - 파일의 최근 변경사항 확인"""
    helpers = get_helpers_safely()
    if not helpers:
        handle_helpers_error()
        return None

    try:
        if hasattr(helpers, 'git_diff'):
            diff = helpers.git_diff(file_path)
            if diff and diff.get('success'):
                diff_content = diff.get('stdout', '')
                if diff_content:
                    print(f"📊 {file_path} 변경사항:")
                    print("=" * 60)
                    print(diff_content)
                    print("=" * 60)
                    return diff_content
                else:
                    print(f"ℹ️ {file_path}: 변경사항 없음")
                    return ""
            else:
                print(f"❌ diff 확인 실패: {file_path}")
                return None
        else:
            print("❌ git_diff 기능을 찾을 수 없습니다")
            return None
    except Exception as e:
        print(f"❌ diff 확인 중 오류: {e}")
        return None

def qb(file_path: str, old_text: str, new_text: str) -> Optional[Dict[str, Any]]:
    """Quick Block replace - 부분 텍스트 교체"""
    helpers = get_helpers_safely()
    if not helpers:
        handle_helpers_error()
        return None

    try:
        result = helpers.replace_block(file_path, old_text, new_text)
        if result and result.get('success'):
            print(f"✅ 텍스트 교체 완료: {file_path}")
            print(f"   변경된 라인: {result.get('lines_changed', 'Unknown')}")
            return result
        else:
            print(f"❌ 텍스트 교체 실패: {file_path}")
            return None
    except Exception as e:
        print(f"❌ 텍스트 교체 중 오류: {e}")
        return None

def qpush(message: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Quick Push - Git add, commit, push를 한번에"""
    helpers = get_helpers_safely()
    if not helpers:
        handle_helpers_error()
        return None

    try:
        return _execute_git_push(helpers, message)
    except Exception as e:
        print(f"❌ Git push 중 오류: {e}")
        return None

def _execute_git_push(helpers, message: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Git push 실행"""
    # 1. 변경사항 확인
    status = helpers.git_status()
    if not status or not status.get('success'):
        print("❌ Git 상태 확인 실패")
        return None

    modified_count = len(status.get('modified', []))
    untracked_count = len(status.get('untracked', []))

    if modified_count == 0 and untracked_count == 0:
        print("ℹ️ 변경사항이 없습니다")
        return None

    print(f"📊 변경사항: 수정 {modified_count}개, 새파일 {untracked_count}개")

    # 2. 자동 커밋 메시지 생성
    if not message:
        message = f"auto: {modified_count + untracked_count}개 파일 업데이트"

    # 3. Git 작업 실행
    print("🔄 Git 작업 실행 중...")

    # Add
    helpers.git_add(".")

    # Commit
    commit_result = helpers.git_commit(message)
    if not commit_result or not commit_result.get('success'):
        print(f"❌ 커밋 실패: {commit_result.get('stderr', 'Unknown error') if commit_result else 'Unknown error'}")
        return None

    print(f"✅ 커밋 완료: {message}")

    # Push
    push_result = helpers.git_push()
    if push_result and push_result.get('success'):
        print("✅ Push 완료!")
        return push_result
    else:
        print(f"❌ Push 실패: {push_result.get('stderr', 'Unknown error') if push_result else 'Unknown error'}")
        return None

def qpull() -> Optional[Dict[str, Any]]:
    """Quick Pull - Git pull 실행"""
    helpers = get_helpers_safely()
    if not helpers:
        handle_helpers_error()
        return None

    try:
        print("🔄 Git pull 실행 중...")
        result = helpers.git_pull()
        if result and result.get('success'):
            print("✅ Pull 완료!")
            stdout = result.get('stdout', '')
            if stdout:
                print(f"📋 결과: {stdout}")
            return result
        else:
            error_msg = result.get('stderr', 'Unknown error') if result else 'Unknown error'
            print(f"❌ Pull 실패: {error_msg}")
            return None
    except Exception as e:
        print(f"❌ Pull 중 오류: {e}")
        return None

def qlog(count: int = 5) -> Optional[Dict[str, Any]]:
    """Quick Log - 최근 커밋 로그 보기"""
    helpers = get_helpers_safely()
    if not helpers:
        handle_helpers_error()
        return None

    try:
        if hasattr(helpers, 'git_log'):
            result = helpers.git_log(count)
            if result and result.get('success'):
                log_content = result.get('stdout', '')
                if log_content:
                    print(f"📜 최근 {count}개 커밋 로그:")
                    print("=" * 60)
                    print(log_content)
                    print("=" * 60)
                    return result
                else:
                    print("📜 커밋 로그가 없습니다")
                    return result
            else:
                print("❌ 로그 조회 실패")
                return None
        else:
            print("❌ git_log 기능을 찾을 수 없습니다")
            return None
    except Exception as e:
        print(f"❌ 로그 조회 중 오류: {e}")
        return None

# 모든 함수들의 __all__ 목록
__all__ = [
    'qp', 'ql', 'qv', 'qr', 'qi', 'qs', 'qm', 'qd', 'qf', 'qw', 'qe', 'qg', 'qc', 'qb', 
    'qls', 'qfind', 'qproj', 'qpush', 'qpull', 'qlog'
]

# 사용 가능한 함수들 표시
def show_available_functions():
    """사용 가능한 q_tools 함수들 표시"""
    print("🔧 사용 가능한 q_tools 함수들:")
    print("=" * 60)

    categories = {
        "📄 파일 분석": ["qp", "ql", "qv", "qm"],
        "✏️ 코드 수정": ["qr", "qi", "qb"],
        "🔍 검색": ["qs", "qfind"],
        "📁 파일 시스템": ["qf", "qw", "qe", "qls"],
        "🔧 Git 작업": ["qg", "qc", "qd", "qpush", "qpull", "qlog"],
        "🚀 프로젝트": ["qproj"]
    }

    for category, functions in categories.items():
        print(f"\n{category}:")
        for func in functions:
            print(f"  • {func}()")

    print("\n💡 사용법: from q_tools import *")
    print("💡 도움말: help(함수명) 또는 함수명.__doc__")
