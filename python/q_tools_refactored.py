
# HelperResult 패턴 import
try:
    from ai_helpers_v2.helper_result import SearchResult, FileResult, ParseResult, HelperResult
except ImportError:
    from ai_helpers_v2.helper_result import SearchResult, FileResult, ParseResult, HelperResult

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
            # 개선: 구체적인 에러 메시지
            print(f"❌ 함수를 찾을 수 없습니다: '{func_name}' in {file_path}")

            # 파일이 존재하는지 확인
            import os
            if not os.path.exists(file_path):
                print(f"   파일이 존재하지 않습니다: {file_path}")
            else:
                # 파일의 함수 목록 제시
                parse_result = safe_file_operation(
                    lambda: helpers.safe_parse_file(file_path) if hasattr(helpers, 'safe_parse_file') else None
                )
                if parse_result and 'functions' in parse_result:
                    available_funcs = list(parse_result['functions'].keys())
                    if available_funcs:
                        print(f"\n💡 사용 가능한 함수들:")
                        for f in available_funcs[:10]:
                            print(f"   - {f}")
                        if len(available_funcs) > 10:
                            print(f"   ... 외 {len(available_funcs) - 10}개")
            return None
    except Exception as e:
        print(f"❌ 함수 조회 실패: {e}")
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

def qi(file_path: str, target: str, new_code: str, position: str = "after") -> bool:
    """Quick Insert - 코드 삽입"""
    helpers = get_helpers_safely()
    if not helpers:
        handle_helpers_error()
        return False

    try:
        # 파일 존재 확인
        import os
        if not os.path.exists(file_path):
            print(f"❌ 파일을 찾을 수 없습니다: {file_path}")
            return False

        # 대상 텍스트가 파일에 있는지 확인
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        if target not in content:
            print(f"❌ 코드 삽입 실패: 대상 텍스트를 찾을 수 없습니다")
            print(f"   파일: {file_path}")
            print(f"   찾는 텍스트: '{target[:50]}{'...' if len(target) > 50 else ''}'")

            # 비슷한 텍스트 찾기 시도
            lines = content.split('\n')
            similar_lines = []
            target_lower = target.lower().strip()

            for i, line in enumerate(lines):
                if target_lower in line.lower():
                    similar_lines.append((i + 1, line.strip()))

            if similar_lines:
                print("\n💡 비슷한 라인을 찾았습니다:")
                for line_num, line_text in similar_lines[:5]:
                    print(f"   라인 {line_num}: {line_text[:80]}{'...' if len(line_text) > 80 else ''}")

            return False

        # 삽입 시도
        success = safe_file_operation(
            lambda: helpers.insert_block(file_path, target, new_code, position) 
            if hasattr(helpers, 'insert_block') else None
        )

        if success:
            print(f"✅ 코드 삽입 성공: {file_path}")
            print(f"   위치: {target[:30]}... 다음에 삽입")

            # 삽입된 라인 수 계산
            inserted_lines = len(new_code.split('\n'))
            print(f"   삽입된 라인: {inserted_lines}줄")
            return True
        else:
            print(f"❌ 코드 삽입 실패")
            print(f"   파일: {file_path}")
            print(f"   원인: insert_block 함수 실행 오류")
            print("   💡 파일 권한을 확인하거나 다시 시도해보세요.")
            return False

    except PermissionError:
        print(f"❌ 코드 삽입 실패: 파일 쓰기 권한이 없습니다")
        print(f"   파일: {file_path}")
        return False
    except Exception as e:
        print(f"❌ 코드 삽입 실패: {e}")
        print(f"   파일: {file_path}")
        return False
def qs(pattern: str, path: str = ".", file_pattern: str = "*.py") -> SearchResult:
    """Quick Search - 코드 검색 (HelperResult 패턴 적용)

    Returns:
        SearchResult: 검색 결과 객체 (success, results, error 포함)
    """
    helpers = get_helpers_safely()

    # helpers가 없는 경우 fallback
    if not helpers:
        print("⚠️ helpers를 사용할 수 없어 grep fallback을 시도합니다.")
        try:
            import subprocess
            import os

            # Windows인 경우 findstr 사용
            if os.name == 'nt':
                # Windows findstr 명령
                cmd = ['findstr', '/s', '/n', f'/c:{pattern}', os.path.join(path, file_pattern)]
            else:
                # Unix/Linux grep 명령
                cmd = ['grep', '-n', '-r', f'--include={file_pattern}', pattern, path]

            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')

            if result.returncode == 0 and result.stdout:
                matches = []
                for line in result.stdout.strip().split('\n'):
                    if os.name == 'nt':
                        # Windows findstr 형식: filepath:line:content
                        parts = line.split(':', 2)
                    else:
                        # grep 형식: filepath:line:content
                        parts = line.split(':', 2)

                    if len(parts) >= 3:
                        matches.append({
                            'file': parts[0].strip(),
                            'line': int(parts[1]) if parts[1].isdigit() else 0,
                            'text': parts[2].strip(),
                            'context': []
                        })

                search_result = SearchResult(results=matches, success=True)
                _print_search_results(search_result)
                return search_result
            else:
                print(f"❌ 패턴 '{pattern}'을 찾을 수 없습니다.")
                return SearchResult(success=False, error="No matches found")

        except FileNotFoundError:
            error_msg = "grep/findstr 명령을 찾을 수 없습니다. 기본 검색 도구가 설치되어 있지 않습니다."
            print(f"❌ {error_msg}")
            return SearchResult(success=False, error=error_msg, error_type="FileNotFoundError")
        except Exception as e:
            print(f"❌ Fallback 검색 실패: {e}")
            return SearchResult(success=False, error=str(e), error_type=type(e).__name__)

    # helpers 사용 가능한 경우
    try:
        # search_code 실행
        raw_results = safe_file_operation(
            lambda: helpers.search_code(pattern, path, file_pattern) if hasattr(helpers, 'search_code') else None
        )

        if raw_results:
            # 결과 정규화
            normalized = []
            for item in raw_results:
                if isinstance(item, dict):
                    normalized.append({
                        'file': item.get('file', item.get('path', '')),
                        'line': item.get('line_number', item.get('line', 0)),
                        'text': item.get('content', item.get('line', '')).strip(),
                        'context': item.get('context', [])
                    })

            result = SearchResult(results=normalized, success=True)
            _print_search_results(result)
            return result
        else:
            print(f"❌ 패턴 '{pattern}'을 찾을 수 없습니다.")
            return SearchResult(success=False, error="No matches found")

    except Exception as e:
        error_msg = f"검색 중 오류 발생: {str(e)}"
        print(f"❌ {error_msg}")
        return SearchResult(success=False, error=error_msg, error_type=type(e).__name__)


def _print_search_results(result: SearchResult, limit: int = 20):
    """검색 결과를 보기 좋게 출력하는 헬퍼 함수"""
    if not result.success or not result.results:
        return

    print(f"\n🔍 검색 결과: {result.count}개 매치, {len(result.files())}개 파일")
    print("=" * 60)

    # 파일별로 그룹화하여 출력
    by_file = result.by_file()
    file_count = 0
    total_shown = 0

    for file_path, matches in by_file.items():
        if file_count >= 5:  # 최대 5개 파일만 표시
            remaining_files = len(by_file) - file_count
            remaining_matches = result.count - total_shown
            print(f"\n... 외 {remaining_files}개 파일, {remaining_matches}개 매치")
            break

        print(f"\n📄 {file_path} ({len(matches)}개):")
        for i, match in enumerate(matches[:4]):  # 파일당 최대 4개
            line_num = match.get('line', 0)
            text = match.get('text', '').strip()
            # 긴 텍스트는 잘라서 표시
            if len(text) > 80:
                text = text[:77] + "..."
            print(f"  {line_num:4d}: {text}")
            total_shown += 1

        if len(matches) > 4:
            print(f"       ... 외 {len(matches) - 4}개")

        file_count += 1

    print("=" * 60)

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

def qc(pattern: str) -> SearchResult:
    """Quick Code search - 현재 디렉토리에서 빠른 코드 검색

    qs()의 간단한 래퍼로, 현재 디렉토리에서 Python 파일을 검색합니다.

    Args:
        pattern: 검색할 패턴

    Returns:
        SearchResult: 검색 결과
    """
    return qs(pattern, ".", "*.py")

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

def qfind(path: str = ".", pattern: str = "*.py") -> SearchResult:
    """Quick Find - 파일 검색 (HelperResult 패턴 적용)

    Args:
        path: 검색 시작 경로
        pattern: 파일 패턴 (예: *.py, test_*.py, **/*.js)

    Returns:
        SearchResult: 파일 검색 결과 (파일 경로 목록)
    """
    helpers = get_helpers_safely()

    # Fallback: helpers가 없을 때 glob 사용
    if not helpers or not hasattr(helpers, 'search_files'):
        print("⚠️ helpers를 사용할 수 없어 기본 파일 검색을 수행합니다.")
        try:
            import glob
            import os

            # 경로 정규화
            search_path = os.path.abspath(path)

            # 재귀적 검색 지원
            if '**' in pattern:
                # Python 3.5+ recursive glob
                full_pattern = os.path.join(search_path, pattern)
                files = glob.glob(full_pattern, recursive=True)
            else:
                # 단일 레벨 검색
                full_pattern = os.path.join(search_path, pattern)
                files = glob.glob(full_pattern)

            # 결과를 SearchResult 형태로 변환
            if files:
                # 파일 경로를 검색 결과 형태로 변환
                results = []
                for file_path in files:
                    # 상대 경로로 변환 시도
                    try:
                        rel_path = os.path.relpath(file_path, os.getcwd())
                    except ValueError:
                        rel_path = file_path

                    results.append({
                        'file': rel_path,
                        'line': 0,
                        'text': os.path.basename(file_path),
                        'context': []
                    })

                result = SearchResult(results=results, success=True)
                _print_file_search_results(result)
                return result
            else:
                print(f"❌ '{pattern}' 패턴과 일치하는 파일을 찾을 수 없습니다.")
                return SearchResult(success=False, error=f"No files matching '{pattern}' found in {path}")

        except Exception as e:
            error_msg = f"파일 검색 중 오류: {str(e)}"
            print(f"❌ {error_msg}")
            return SearchResult(success=False, error=error_msg, error_type=type(e).__name__)

    # helpers 사용 가능한 경우
    try:
        # search_files 실행
        files = safe_file_operation(
            lambda: helpers.search_files(path, pattern) if hasattr(helpers, 'search_files') else None
        )

        if files:
            # 파일 목록을 SearchResult 형태로 변환
            results = []
            for file_path in files:
                results.append({
                    'file': file_path,
                    'line': 0,
                    'text': os.path.basename(file_path) if os else file_path.split('/')[-1],
                    'context': []
                })

            result = SearchResult(results=results, success=True)
            _print_file_search_results(result)
            return result
        else:
            print(f"❌ '{pattern}' 패턴과 일치하는 파일을 찾을 수 없습니다.")
            return SearchResult(success=False, error=f"No files matching '{pattern}' found")

    except Exception as e:
        error_msg = f"파일 검색 실패: {str(e)}"
        print(f"❌ {error_msg}")
        return SearchResult(success=False, error=error_msg, error_type=type(e).__name__)


def _print_file_search_results(result: SearchResult, limit: int = 50):
    """파일 검색 결과 출력 헬퍼"""
    if not result.success or not result.results:
        return

    files = result.files()
    print(f"\n🔍 검색 결과: {len(files)}개 파일")
    print("=" * 60)

    # 디렉토리별로 그룹화
    by_dir = {}
    for file_path in files[:limit]:
        dir_path = os.path.dirname(file_path) if os else '/'.join(file_path.split('/')[:-1])
        if not dir_path:
            dir_path = "."

        if dir_path not in by_dir:
            by_dir[dir_path] = []
        by_dir[dir_path].append(os.path.basename(file_path) if os else file_path.split('/')[-1])

    # 디렉토리별로 출력
    for dir_path, filenames in sorted(by_dir.items()):
        print(f"\n📁 {dir_path}/")
        for filename in sorted(filenames)[:10]:
            print(f"  📄 {filename}")
        if len(filenames) > 10:
            print(f"  ... 외 {len(filenames) - 10}개")

    if len(files) > limit:
        print(f"\n... 전체 {len(files)}개 중 {limit}개만 표시")

    print("=" * 60)

def qproj(project_name: Optional[str] = None) -> None:
    """Quick Project - 프로젝트 전환 또는 정보 보기"""

    if project_name:
        # 프로젝트 전환
        helpers = get_helpers_safely()
        if not helpers:
            print("❌ 프로젝트 전환 기능을 사용할 수 없습니다.")
            print("💡 프로젝트 관리 모듈이 로드되었는지 확인하세요.")
            print("   - helpers 객체가 초기화되었는지 확인")
            print("   - 프로젝트 관리 기능이 활성화되었는지 확인")
            return

        try:
            if hasattr(helpers, 'cmd_flow_with_context'):
                result = helpers.cmd_flow_with_context(project_name)
                if result:
                    print(f"✅ 프로젝트 전환 성공: {project_name}")
                else:
                    print(f"❌ 프로젝트 전환 실패: {project_name}")
                    print("💡 프로젝트 이름이 올바른지 확인하세요.")
            else:
                print("❌ 프로젝트 전환 기능(cmd_flow_with_context)을 찾을 수 없습니다.")
                print("💡 대안:")
                print("   1. fp() 함수 사용: fp('프로젝트명')")
                print("   2. 수동 디렉토리 변경: os.chdir('경로')")
        except Exception as e:
            print(f"❌ 프로젝트 전환 중 오류: {e}")
    else:
        # 현재 프로젝트 정보 표시
        import os
        current_dir = os.getcwd()
        project_name = os.path.basename(current_dir)

        print(f"\n📁 현재 프로젝트: {project_name}")
        print(f"📂 경로: {current_dir}")

        # 프로젝트 통계
        try:
            # 파일 개수 계산
            total_files = 0
            total_size = 0
            file_types = {}

            for root, dirs, files in os.walk(current_dir):
                # .git, node_modules 등 제외
                dirs[:] = [d for d in dirs if not d.startswith('.') and d != 'node_modules']

                for file in files:
                    if not file.startswith('.'):
                        total_files += 1
                        file_path = os.path.join(root, file)
                        try:
                            total_size += os.path.getsize(file_path)
                            ext = os.path.splitext(file)[1].lower()
                            if ext:
                                file_types[ext] = file_types.get(ext, 0) + 1
                        except:
                            pass

            print(f"\n📊 프로젝트 통계:")
            print(f"  총 파일 수: {total_files:,}개")
            print(f"  총 크기: {total_size / (1024*1024):.2f} MB")

            if file_types:
                print("\n📋 파일 타입별 분포:")
                sorted_types = sorted(file_types.items(), key=lambda x: x[1], reverse=True)
                for ext, count in sorted_types[:10]:
                    print(f"  {ext}: {count}개")
                if len(sorted_types) > 10:
                    print(f"  ... 외 {len(sorted_types) - 10}개 타입")

            # Git 상태 확인
            if os.path.exists('.git'):
                print("\n🔧 Git 저장소: ✅")
                try:
                    import subprocess
                    # 현재 브랜치
                    branch = subprocess.run(
                        ['git', 'branch', '--show-current'],
                        capture_output=True,
                        text=True
                    ).stdout.strip()
                    if branch:
                        print(f"  현재 브랜치: {branch}")

                    # 변경된 파일 수
                    status = subprocess.run(
                        ['git', 'status', '--porcelain'],
                        capture_output=True,
                        text=True
                    ).stdout.strip()
                    if status:
                        changed_files = len(status.split('\n'))
                        print(f"  변경된 파일: {changed_files}개")
                except:
                    pass
            else:
                print("\n🔧 Git 저장소: ❌")

        except Exception as e:
            print(f"\n⚠️ 프로젝트 통계 수집 중 오류: {e}")

        print("\n💡 프로젝트 전환: qproj('프로젝트명')")
def qm(file_path: str, class_name: str, method_name: str) -> Optional[str]:
    """Quick Method - 클래스 메서드 코드 보기"""
    helpers = get_helpers_safely()
    if not helpers:
        handle_helpers_error()
        return None

    try:
        # 파일 존재 확인
        import os
        if not os.path.exists(file_path):
            print(f"❌ 파일을 찾을 수 없습니다: {file_path}")
            return None

        # 파일 파싱
        parse_result = safe_file_operation(
            lambda: helpers.safe_parse_file(file_path) if hasattr(helpers, 'safe_parse_file') else None
        )

        if not parse_result:
            print(f"❌ 파일 파싱 실패: {file_path}")
            return None

        # 클래스 찾기
        classes = parse_result.get('classes', {})
        if class_name not in classes:
            print(f"❌ 클래스 '{class_name}'를 찾을 수 없습니다")
            if classes:
                print("\n💡 사용 가능한 클래스들:")
                for cls in list(classes.keys())[:10]:
                    print(f"   - {cls}")
            return None

        class_info = classes[class_name]

        # 메서드 정보 확인
        methods = class_info.get('methods', {})
        if method_name not in methods:
            print(f"❌ 메서드 '{method_name}'를 클래스 '{class_name}'에서 찾을 수 없습니다")
            if methods:
                print(f"\n💡 {class_name} 클래스의 메서드들:")
                for method in list(methods.keys())[:10]:
                    print(f"   - {method}")
                if len(methods) > 10:
                    print(f"   ... 외 {len(methods) - 10}개")
            return None

        # 메서드 코드 추출 (개선된 방식)
        method_info = methods[method_name]
        start_line = method_info.get('start', 0)
        end_line = method_info.get('end', 0)

        if start_line and end_line:
            # 라인 번호를 사용한 정확한 추출
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            if 0 < start_line <= len(lines) and 0 < end_line <= len(lines):
                method_code = ''.join(lines[start_line-1:end_line])
                print(f"\n📄 {file_path} - {class_name}.{method_name}():")
                print("=" * 60)
                print(method_code)
                print("=" * 60)
                return method_code

        # Fallback: 문자열 매칭 방식
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 클래스 시작 찾기
        class_pattern = f"class {class_name}"
        class_start = content.find(class_pattern)
        if class_start == -1:
            print(f"❌ 클래스 정의를 찾을 수 없습니다: {class_name}")
            return None

        # 메서드 찾기 (클래스 내부에서)
        method_pattern = f"def {method_name}("
        method_start = content.find(method_pattern, class_start)

        if method_start == -1 or method_start < class_start:
            print(f"❌ 메서드를 찾을 수 없습니다: {class_name}.{method_name}")
            return None

        # 메서드 끝 찾기 (들여쓰기 기반)
        lines = content[method_start:].split('\n')
        method_lines = [lines[0]]  # def 라인

        # 메서드의 들여쓰기 레벨 확인
        base_indent = len(lines[0]) - len(lines[0].lstrip())

        for line in lines[1:]:
            if line.strip():  # 비어있지 않은 라인
                current_indent = len(line) - len(line.lstrip())
                if current_indent <= base_indent:
                    break
            method_lines.append(line)

        method_code = '\n'.join(method_lines).rstrip()
        print(f"\n📄 {file_path} - {class_name}.{method_name}():")
        print("=" * 60)
        print(method_code)
        print("=" * 60)
        return method_code

    except Exception as e:
        print(f"❌ 메서드 조회 실패: {e}")
        return None
def qd(file_path: Optional[str] = None) -> Optional[str]:
    """Quick Diff - Git 변경사항 보기"""
    helpers = get_helpers_safely()

    # Fallback: helpers가 없거나 git_diff가 없을 때 subprocess 사용
    if not helpers or not hasattr(helpers, 'git_diff'):
        print("⚠️ helpers.git_diff를 사용할 수 없어 직접 git diff를 실행합니다.")
        try:
            import subprocess

            # git diff 명령 구성
            cmd = ['git', 'diff']
            if file_path:
                cmd.append(file_path)

            # git diff 실행
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8'
            )

            if result.returncode == 0:
                if result.stdout:
                    print(f"\n🔄 Git 변경사항{' - ' + file_path if file_path else ''}:")
                    print("=" * 60)
                    print(result.stdout)
                    print("=" * 60)
                    return result.stdout
                else:
                    print(f"✅ 변경사항 없음{' - ' + file_path if file_path else ''}")
                    return ""
            else:
                error_msg = result.stderr.strip()
                if "not a git repository" in error_msg:
                    print("❌ Git 저장소가 아닙니다.")
                elif "does not exist" in error_msg:
                    print(f"❌ 파일을 찾을 수 없습니다: {file_path}")
                else:
                    print(f"❌ Git diff 실행 실패: {error_msg}")
                return None

        except FileNotFoundError:
            print("❌ Git이 설치되어 있지 않습니다.")
            return None
        except Exception as e:
            print(f"❌ Git diff 실행 중 오류: {e}")
            return None

    # helpers 사용 가능한 경우
    try:
        diff = safe_file_operation(
            lambda: helpers.git_diff(file_path) if hasattr(helpers, 'git_diff') else None
        )
        if diff:
            print(f"\n🔄 Git 변경사항{' - ' + file_path if file_path else ''}:")
            print("=" * 60)
            print(diff)
            print("=" * 60)
            return diff
        else:
            print(f"✅ 변경사항 없음{' - ' + file_path if file_path else ''}")
            return ""
    except Exception as e:
        print(f"❌ Git diff 조회 실패: {e}")
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

def qlog(n: int = 10) -> Optional[List[str]]:
    """Quick Log - Git 커밋 로그 보기"""
    helpers = get_helpers_safely()

    # Fallback: helpers가 없거나 git_log가 없을 때 subprocess 사용
    if not helpers or not hasattr(helpers, 'git_log'):
        print("⚠️ helpers.git_log를 사용할 수 없어 직접 git log를 실행합니다.")
        try:
            import subprocess

            # git log 실행
            result = subprocess.run(
                ['git', 'log', f'-{n}', '--oneline'],
                capture_output=True,
                text=True,
                encoding='utf-8'
            )

            if result.returncode == 0:
                if result.stdout:
                    logs = result.stdout.strip().split('\n')
                    print(f"\n📜 최근 커밋 {len(logs)}개:")
                    print("=" * 60)
                    for log in logs:
                        print(f"  {log}")
                    print("=" * 60)
                    return logs
                else:
                    print("❌ 커밋 이력이 없습니다.")
                    return []
            else:
                error_msg = result.stderr.strip()
                if "not a git repository" in error_msg:
                    print("❌ Git 저장소가 아닙니다.")
                    print("💡 git init 명령으로 저장소를 초기화하세요.")
                elif "does not have any commits yet" in error_msg:
                    print("❌ 아직 커밋이 없습니다.")
                    print("💡 첫 번째 커밋을 만들어보세요: git commit -m 'Initial commit'")
                else:
                    print(f"❌ Git log 실행 실패: {error_msg}")
                return None

        except FileNotFoundError:
            print("❌ Git이 설치되어 있지 않습니다.")
            print("💡 Git을 설치하려면: https://git-scm.com/downloads")
            return None
        except Exception as e:
            print(f"❌ Git log 실행 중 오류: {e}")
            return None

    # helpers 사용 가능한 경우
    try:
        logs = safe_file_operation(
            lambda: helpers.git_log(n) if hasattr(helpers, 'git_log') else None
        )
        if logs:
            print(f"\n📜 최근 커밋 {len(logs)}개:")
            print("=" * 60)
            for log in logs:
                print(f"  {log}")
            print("=" * 60)
            return logs
        else:
            print("❌ 로그 조회 실패 또는 커밋 이력 없음")
            return []
    except Exception as e:
        print(f"❌ Git log 조회 실패: {e}")
        return None
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


# SearchResult 관련 유틸리티 함수들
def search_and_open(pattern: str, editor: str = "code") -> SearchResult:
    """검색 후 첫 번째 결과를 에디터로 열기"""
    result = qs(pattern)
    if result and result.files():
        first_file = result.files()[0]
        try:
            import subprocess
            subprocess.run([editor, first_file])
            print(f"✅ {editor}로 열었습니다: {first_file}")
        except Exception as e:
            print(f"❌ 파일 열기 실패: {e}")
    return result


def search_in_file(file_path: str, pattern: str) -> SearchResult:
    """특정 파일 내에서만 검색"""
    helpers = get_helpers_safely()

    try:
        # 파일 읽기
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        results = []
        for i, line in enumerate(lines, 1):
            if pattern.lower() in line.lower():
                results.append({
                    'file': file_path,
                    'line': i,
                    'text': line.strip(),
                    'context': []
                })

        if results:
            result = SearchResult(results=results, success=True)
            _print_search_results(result)
            return result
        else:
            print(f"❌ '{pattern}'을 찾을 수 없습니다: {file_path}")
            return SearchResult(success=False, error="Pattern not found in file")

    except Exception as e:
        return SearchResult(success=False, error=str(e), error_type=type(e).__name__)
