"""
검색 래퍼 함수들 - 통합 및 개선된 버전
중복 제거 및 기능 강화
"""
from typing import Dict, List, Any, Optional
from .helper_result import HelperResult
from pathlib import Path
import fnmatch
import re

def search_files_advanced(directory: str, pattern: str = "*", 
                         recursive: bool = True, 
                         include_hidden: bool = False,
                         max_results: int = 1000) -> HelperResult:
    """
    고급 파일 검색 - 모든 파일 검색 기능 통합

    Args:
        directory: 검색할 디렉토리
        pattern: 파일 패턴 (glob 형식)
        recursive: 재귀적 검색 여부
        include_hidden: 숨김 파일 포함 여부
        max_results: 최대 결과 수

    Returns:
        HelperResult with list of matched file paths
    """
    try:
        search_path = Path(directory).resolve()
        if not search_path.exists():
            return HelperResult(False, error=f"Directory not found: {directory}")

        results = []
        count = 0

        if recursive:
            for file_path in search_path.rglob(pattern):
                if count >= max_results:
                    break
                if file_path.is_file():
                    if not include_hidden and file_path.name.startswith('.'):
                        continue
                    results.append({
                        'path': str(file_path),
                        'name': file_path.name,
                        'size': file_path.stat().st_size,
                        'modified': file_path.stat().st_mtime
                    })
                    count += 1
        else:
            for file_path in search_path.glob(pattern):
                if count >= max_results:
                    break
                if file_path.is_file():
                    if not include_hidden and file_path.name.startswith('.'):
                        continue
                    results.append({
                        'path': str(file_path),
                        'name': file_path.name,
                        'size': file_path.stat().st_size,
                        'modified': file_path.stat().st_mtime
                    })
                    count += 1

        return HelperResult(True, data={
            'results': results,
            'total': len(results),
            'pattern': pattern,
            'directory': str(search_path)
        })

    except Exception as e:
        return HelperResult(False, error=f"Search failed: {str(e)}")


def search_code_content(path: str, pattern: str, 
                       file_pattern: str = "*.py",
                       regex: bool = False,
                       case_sensitive: bool = True,
                       context_lines: int = 2,
                       max_matches_per_file: int = 100) -> HelperResult:
    """
    코드 내용 검색 - 모든 코드 검색 기능 통합

    Args:
        path: 검색할 경로
        pattern: 검색할 패턴 (문자열 또는 정규식)
        file_pattern: 파일 패턴
        regex: 정규식 사용 여부
        case_sensitive: 대소문자 구분
        context_lines: 컨텍스트 라인 수
        max_matches_per_file: 파일당 최대 매치 수

    Returns:
        HelperResult with search results
    """
    try:
        search_path = Path(path).resolve()
        if not search_path.exists():
            return HelperResult(False, error=f"Path not found: {path}")

        # 정규식 컴파일
        if regex:
            flags = 0 if case_sensitive else re.IGNORECASE
            regex_pattern = re.compile(pattern, flags)

        results = []

        # 파일 검색
        files_to_search = []
        if search_path.is_file():
            files_to_search = [search_path]
        else:
            files_to_search = list(search_path.rglob(file_pattern))

        for file_path in files_to_search:
            if not file_path.is_file():
                continue

            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()

                matches = []
                for i, line in enumerate(lines):
                    if len(matches) >= max_matches_per_file:
                        break

                    # 패턴 매칭
                    found = False
                    if regex:
                        found = bool(regex_pattern.search(line))
                    else:
                        if case_sensitive:
                            found = pattern in line
                        else:
                            found = pattern.lower() in line.lower()

                    if found:
                        # 컨텍스트 라인 추출
                        start = max(0, i - context_lines)
                        end = min(len(lines), i + context_lines + 1)

                        context = []
                        for j in range(start, end):
                            prefix = ">>>" if j == i else "   "
                            context.append(f"{prefix} {j+1:4d} | {lines[j].rstrip()}")

                        matches.append({
                            'line_number': i + 1,
                            'line_content': line.strip(),
                            'context': '\n'.join(context)
                        })

                if matches:
                    results.append({
                        'file_path': str(file_path),
                        'matches': matches,
                        'match_count': len(matches)
                    })

            except Exception:
                # 읽을 수 없는 파일은 건너뛰기
                continue

        return HelperResult(True, data={
            'results': results,
            'total_files': len(results),
            'total_matches': sum(r['match_count'] for r in results),
            'pattern': pattern,
            'file_pattern': file_pattern
        })

    except Exception as e:
        return HelperResult(False, error=f"Code search failed: {str(e)}")


# 특수 목적 검색 함수들
def find_class(path: str, class_name: str, exact_match: bool = True) -> HelperResult:
    """클래스 정의 찾기"""
    pattern = f"^class {class_name}" if exact_match else f"class.*{class_name}"
    return search_code_content(path, pattern, "*.py", regex=True, context_lines=5)


def find_function(path: str, function_name: str, exact_match: bool = True) -> HelperResult:
    """함수 정의 찾기"""
    pattern = f"^def {function_name}" if exact_match else f"def.*{function_name}"
    return search_code_content(path, pattern, "*.py", regex=True, context_lines=5)


# 별칭 (하위 호환성)
search_files = search_files_advanced  # 기존 함수명 호환
search_code = search_code_content     # 기존 함수명 호환
