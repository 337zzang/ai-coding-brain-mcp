"""
개선된 Insert 함수 - Replace 기반으로 모든 장점 상속
"""

def insert_v2(path: str, marker: Union[str, int], code: str, 
              after: bool = True, indent_auto: bool = True) -> Dict[str, Any]:
    """개선된 insert - 들여쓰기 자동 처리

    Args:
        path: 파일 경로
        marker: 삽입 위치 (문자열 패턴 또는 라인 번호)
        code: 삽입할 코드
        after: True면 마커 뒤에, False면 앞에 삽입
        indent_auto: True면 들여쓰기 자동 감지/적용

    Returns:
        {'ok': True, 'data': {'line': 삽입된 라인}}

    Examples:
        # Import 추가
        insert_v2("app.py", "import os", "import sys")

        # 함수에 데코레이터 추가
        insert_v2("app.py", "def api():", "@login_required", after=False)

        # 라인 번호로 삽입
        insert_v2("app.py", 10, "# 주석 추가")
    """
    from improved_replace import replace_improved
    from pathlib import Path

    # 파일 읽기
    content = Path(path).read_text(encoding='utf-8')
    lines = content.split('\n')

    # 1. 라인 번호인 경우
    if isinstance(marker, int):
        line_num = marker
        if 0 <= line_num <= len(lines):
            # 들여쓰기 자동 감지
            if indent_auto and line_num > 0:
                prev_line = lines[line_num - 1] if line_num > 0 else ""
                indent = len(prev_line) - len(prev_line.lstrip())
                indented_code = ' ' * indent + code.lstrip()
            else:
                indented_code = code

            if after and line_num < len(lines):
                lines.insert(line_num + 1, indented_code)
            else:
                lines.insert(line_num, indented_code)

            new_content = '\n'.join(lines)
            Path(path).write_text(new_content, encoding='utf-8')
            return {'ok': True, 'data': {'line': line_num, 'inserted': indented_code}}
        else:
            return {'ok': False, 'error': f"Line {line_num} out of range (0-{len(lines)})"}

    # 2. 문자열 패턴인 경우 - replace_improved 활용
    if after:
        # 마커 뒤에 삽입
        replacement = f"{marker}\n{code}"
    else:
        # 마커 앞에 삽입
        replacement = f"{code}\n{marker}"

    # replace_improved의 모든 장점 활용
    result = replace_improved(path, marker, replacement, fuzzy=True)

    if result['ok']:
        # 삽입된 라인 찾기
        new_content = Path(path).read_text(encoding='utf-8')
        new_lines = new_content.split('\n')
        for i, line in enumerate(new_lines):
            if code in line:
                result['data']['line'] = i + 1
                break

    return result


def delete_lines(path: str, start: Union[str, int], end: Optional[Union[str, int]] = None) -> Dict[str, Any]:
    """라인 또는 블록 삭제 함수

    Args:
        path: 파일 경로
        start: 시작 라인 (번호 또는 패턴)
        end: 끝 라인 (None이면 한 줄만 삭제)

    Returns:
        {'ok': True, 'data': {'deleted': 삭제된 라인 수}}

    Examples:
        # 한 줄 삭제
        delete_lines("app.py", 10)

        # 범위 삭제
        delete_lines("app.py", 10, 20)

        # 패턴으로 삭제
        delete_lines("app.py", "# TODO", "# END TODO")

        # 함수 전체 삭제
        delete_lines("app.py", "def old_function():", "    return")
    """
    from pathlib import Path

    content = Path(path).read_text(encoding='utf-8')
    lines = content.split('\n')

    # 시작 라인 찾기
    if isinstance(start, int):
        start_idx = start - 1  # 0-based index
    else:
        start_idx = None
        for i, line in enumerate(lines):
            if start in line:
                start_idx = i
                break
        if start_idx is None:
            return {'ok': False, 'error': f"Pattern '{start}' not found"}

    # 끝 라인 찾기
    if end is None:
        end_idx = start_idx
    elif isinstance(end, int):
        end_idx = end - 1
    else:
        end_idx = None
        for i in range(start_idx + 1, len(lines)):
            if end in lines[i]:
                end_idx = i
                break
        if end_idx is None:
            end_idx = start_idx  # 끝을 못 찾으면 한 줄만 삭제

    # 범위 검증
    if start_idx < 0 or end_idx >= len(lines) or start_idx > end_idx:
        return {'ok': False, 'error': f"Invalid range: {start_idx+1} to {end_idx+1}"}

    # 삭제
    deleted_count = end_idx - start_idx + 1
    deleted_lines = lines[start_idx:end_idx + 1]

    # 백업
    backup_path = f"{path}.backup"
    Path(backup_path).write_text(content, encoding='utf-8')

    # 새 내용 생성
    new_lines = lines[:start_idx] + lines[end_idx + 1:]
    new_content = '\n'.join(new_lines)

    # 저장
    Path(path).write_text(new_content, encoding='utf-8')

    return {
        'ok': True,
        'data': {
            'deleted': deleted_count,
            'deleted_lines': deleted_lines,
            'backup': backup_path
        }
    }
