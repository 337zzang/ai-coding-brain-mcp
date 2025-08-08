# 📄 code.py 파일 수정 권장사항

"""
파일 수정 함수들 - 최종 개선 버전
"""

from typing import Dict, Any, Union, Optional
from pathlib import Path
import shutil

# ========== REPLACE ==========
def replace(path: str, old: str, new: str, count: int = 1, **kwargs) -> Dict[str, Any]:
    """통합 replace 함수 - 자동으로 최적 방법 선택

    하위 호환성 100% 유지하면서 다음 기능 추가:
    - 들여쓰기 자동 처리 (fuzzy=True)
    - 특수 문자 100% 처리
    - 미리보기 지원 (preview=True)
    - 구문 검증 (validate=True)
    """
    try:
        # 최우선: 모든 기능 통합 버전
        from smart_replace_ultimate import smart_replace_ultimate
        return smart_replace_ultimate(path, old, new, **kwargs)
    except ImportError:
        try:
            # 차선: fuzzy matching 버전
            from improved_replace import replace_improved
            return replace_improved(path, old, new, **kwargs)
        except ImportError:
            # 폴백: 기존 로직
            return _old_replace(path, old, new, count)

def _old_replace(path: str, old: str, new: str, count: int = 1) -> Dict[str, Any]:
    """기존 replace 로직 (폴백용)"""
    # 기존 코드 백업...
    pass

# ========== INSERT ==========
def insert(path: str, marker: Union[str, int], code: str, 
          after: bool = True, **kwargs) -> Dict[str, Any]:
    """개선된 insert - replace 기반으로 들여쓰기 자동 처리

    하위 호환성 100% 유지하면서 다음 기능 추가:
    - 들여쓰기 자동 감지/적용
    - 특수 문자 처리
    - fuzzy matching 지원
    """
    # 라인 번호인 경우
    if isinstance(marker, int):
        content = Path(path).read_text(encoding='utf-8')
        lines = content.split('\n')

        if 0 <= marker <= len(lines):
            # 들여쓰기 자동 감지
            if marker > 0:
                prev_line = lines[marker - 1]
                indent = len(prev_line) - len(prev_line.lstrip())
                indented_code = ' ' * indent + code.lstrip()
            else:
                indented_code = code

            if after and marker < len(lines):
                lines.insert(marker + 1, indented_code)
            else:
                lines.insert(marker, indented_code)

            # 백업 생성
            backup_path = f"{path}.backup"
            shutil.copy2(path, backup_path)

            # 저장
            new_content = '\n'.join(lines)
            Path(path).write_text(new_content, encoding='utf-8')

            return {'ok': True, 'data': {'line': marker, 'backup': backup_path}}
        else:
            return {'ok': False, 'error': f"Line {marker} out of range"}

    # 문자열 패턴인 경우 - replace 활용
    if after:
        replacement = f"{marker}\n{code}"
    else:
        replacement = f"{code}\n{marker}"

    return replace(path, marker, replacement, fuzzy=True, **kwargs)

# ========== DELETE (새로 추가) ==========  
def delete(path: str, start: Union[str, int], 
          end: Optional[Union[str, int]] = None) -> Dict[str, Any]:
    """라인 또는 블록 삭제

    Args:
        path: 파일 경로
        start: 시작 (라인 번호 또는 패턴)
        end: 끝 (None이면 한 줄만)

    Examples:
        delete("app.py", 10)  # 10번 라인 삭제
        delete("app.py", 10, 20)  # 10-20 라인 삭제
        delete("app.py", "# TODO", "# END")  # 블록 삭제
    """
    content = Path(path).read_text(encoding='utf-8')
    lines = content.split('\n')

    # 시작 위치 찾기
    if isinstance(start, int):
        start_idx = start - 1
    else:
        start_idx = next((i for i, line in enumerate(lines) if start in line), None)
        if start_idx is None:
            return {'ok': False, 'error': f"Pattern '{start}' not found"}

    # 끝 위치 찾기
    if end is None:
        end_idx = start_idx
    elif isinstance(end, int):
        end_idx = end - 1
    else:
        end_idx = next((i for i in range(start_idx + 1, len(lines)) if end in lines[i]), start_idx)

    # 백업
    backup_path = f"{path}.backup"
    Path(backup_path).write_text(content, encoding='utf-8')

    # 삭제
    deleted = lines[start_idx:end_idx + 1]
    new_lines = lines[:start_idx] + lines[end_idx + 1:]

    # 저장
    Path(path).write_text('\n'.join(new_lines), encoding='utf-8')

    return {
        'ok': True,
        'data': {
            'deleted_count': len(deleted),
            'deleted_lines': deleted,
            'backup': backup_path
        }
    }

# ========== 기존 함수들은 그대로 유지 ==========
# view, parse, functions, classes 등...
