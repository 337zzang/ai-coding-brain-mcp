"""
코드 수정 기능 - ez_code 기반으로 단순화
기존 인터페이스를 유지하면서 ez_code를 사용하는 래퍼
"""
from typing import Dict, List, Any, Optional
from .ez_code import ez_parse, ez_replace, ez_view
from .core import track_execution
from .helper_result import ParseResult


class CodeSnippet:
    """코드 스니펫 정보 (레거시 호환)"""
    def __init__(self, name: str, type: str, start_line: int, end_line: int, code: str,
                 start_col: int = 0, end_col: int = 0):
        self.name = name
        self.type = type  # 'function', 'class', 'method'
        self.start_line = start_line
        self.end_line = end_line
        self.start_col = start_col
        self.end_col = end_col
        self.code = code
        self.line_count = end_line - start_line + 1


@track_execution
def parse_with_snippets(filepath: str, max_chars_per_snippet: int = 1500) -> Dict[str, Any]:
    """코드 파일을 파싱하여 스니펫으로 분할 (ez_parse 래퍼)"""
    try:
        # ez_parse 사용
        items = ez_parse(filepath)
        
        # 파일 읽기
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        lines = content.split('\n')
        
        # 스니펫 생성
        snippets = []
        for name, (start, end) in items.items():
            # 타입 결정
            if '.' in name:
                type_ = 'method'
            elif name in items and any(n.startswith(f"{name}.") for n in items):
                type_ = 'class'
            else:
                type_ = 'function'
            
            # 코드 추출
            code_lines = lines[start:end+1]
            code = '\n'.join(code_lines)
            
            # 크기 제한 체크
            if len(code) <= max_chars_per_snippet:
                snippet = CodeSnippet(
                    name=name,
                    type=type_,
                    start_line=start,
                    end_line=end,
                    code=code
                )
                snippets.append(snippet)
        
        # 요약 생성
        summary = {
            'total_functions': len([s for s in snippets if s.type == 'function']),
            'total_classes': len([s for s in snippets if s.type == 'class']),
            'total_methods': len([s for s in snippets if s.type == 'method'])
        }
        
        return {
            'success': True,
            'total_lines': len(lines),
            'snippets': snippets,
            'summary': summary
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


@track_execution
def replace_block(filepath: str, old_code: str, new_code: str,
                 backup: bool = True, ignore_indent: bool = True) -> Dict[str, Any]:
    """코드 블록 교체 (레거시 호환)"""
    try:
        # 먼저 정확한 매칭 시도
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if old_code in content:
            # 정확한 매칭이 되면 직접 교체
            new_content = content.replace(old_code, new_code, 1)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            return {
                'success': True,
                'filepath': filepath,
                'lines_changed': len(old_code.split('\n'))
            }
        
        # 정확한 매칭이 안되면 함수/메서드 단위로 교체 시도
        items = ez_parse(filepath)
        
        # old_code에서 함수/클래스 이름 추출 시도
        old_lines = old_code.strip().split('\n')
        first_line = old_lines[0].strip()
        
        # 함수나 클래스 정의 찾기
        import re
        func_match = re.match(r'^def\s+(\w+)', first_line)
        class_match = re.match(r'^class\s+(\w+)', first_line)
        
        target_name = None
        if func_match:
            target_name = func_match.group(1)
        elif class_match:
            target_name = class_match.group(1)
        
        if target_name:
            # 이름으로 교체 시도
            for name in items:
                if name.endswith(target_name) or name == target_name:
                    result = ez_replace(filepath, name, new_code, backup=backup)
                    if "Replaced" in result:
                        return {
                            'success': True,
                            'filepath': filepath,
                            'lines_changed': len(new_code.split('\n'))
                        }
        
        # 모든 시도가 실패하면
        return {
            'success': False,
            'error': 'No matching code block found',
            'filepath': filepath
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'filepath': filepath
        }


@track_execution
def insert_block(filepath: str, marker: str, code_to_insert: str,
                position: str = "after", create_if_missing: bool = False) -> Dict[str, Any]:
    """코드 블록 삽입 (간단한 구현)"""
    try:
        # 파일 읽기
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        
        # 마커 찾기
        insert_line = -1
        for i, line in enumerate(lines):
            if marker in line:
                if position == "after":
                    insert_line = i + 1
                else:
                    insert_line = i
                break
        
        if insert_line == -1:
            return {
                'success': False,
                'error': f'Marker not found: {marker}'
            }
        
        # 들여쓰기 맞추기
        ref_line = lines[insert_line - 1] if insert_line > 0 else ""
        indent = len(ref_line) - len(ref_line.lstrip())
        
        # 코드 삽입
        insert_lines = code_to_insert.rstrip('\n').split('\n')
        indented_lines = []
        for line in insert_lines:
            if line.strip():
                indented_lines.append(' ' * indent + line)
            else:
                indented_lines.append(line)
        
        # 삽입
        lines[insert_line:insert_line] = indented_lines
        
        # 파일 쓰기
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        return {
            'success': True,
            'filepath': filepath,
            'insert_position': insert_line,
            'lines_inserted': len(indented_lines)
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'filepath': filepath
        }


# 추가 함수들 (호환성)
def normalize_whitespace(code: str) -> str:
    """코드의 공백 정규화"""
    lines = code.split('\n')
    normalized = []
    for line in lines:
        line = line.replace('\t', '    ')
        line = line.rstrip()
        normalized.append(line)
    return '\n'.join(normalized)


# 정밀 수정 함수들은 ez_replace로 대체
def replace_function(filepath: str, func_name: str, new_code: str) -> Dict[str, Any]:
    """함수 교체"""
    result = ez_replace(filepath, func_name, new_code)
    if "Replaced" in result:
        return {'success': True, 'element': func_name}
    return {'success': False, 'error': result}


def replace_method(filepath: str, class_name: str, method_name: str, new_code: str) -> Dict[str, Any]:
    """메서드 교체"""
    full_name = f"{class_name}.{method_name}"
    result = ez_replace(filepath, full_name, new_code)
    if "Replaced" in result:
        return {'success': True, 'element': full_name}
    return {'success': False, 'error': result}


# 나머지 함수들은 단순 스텁으로 처리
def find_code_position(lines: List[str], target: str, position: str) -> int:
    """코드 위치 찾기 (레거시 호환)"""
    return -1


def calculate_similarity(lines1: List[str], lines2: List[str]) -> float:
    """유사도 계산 (레거시 호환)"""
    return 0.0


def find_fuzzy_match(content: str, target: str, threshold: float = 0.8) -> Dict[str, Any]:
    """퍼지 매칭 (레거시 호환)"""
    return {'found': False}


# 기존에 없던 유용한 함수들 추가
@track_execution  
def list_functions(filepath: str) -> List[str]:
    """파일의 모든 함수/메서드 목록"""
    items = ez_parse(filepath)
    return sorted(items.keys())


@track_execution
def get_function_code(filepath: str, func_name: str) -> Optional[str]:
    """특정 함수의 코드 가져오기"""
    result = ez_view(filepath, func_name)
    if "not found" not in result:
        # 헤더 부분 제거
        lines = result.split('\n')
        if lines and lines[0].startswith('📍'):
            return '\n'.join(lines[1:])
    return None
