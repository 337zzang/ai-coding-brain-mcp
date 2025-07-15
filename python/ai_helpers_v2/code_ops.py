"""
코드 수정 기능 - parse_with_snippets, replace_block 등
"""
import ast
import re
from typing import Dict, List, Any, Optional, Tuple
from .core import track_execution
from .file_ops import read_file, write_file

class CodeSnippet:
    """코드 스니펫 정보"""
    def __init__(self, name: str, type: str, start_line: int, end_line: int, content: str):
        self.name = name
        self.type = type  # 'function', 'class', 'method'
        self.start_line = start_line
        self.end_line = end_line
        self.content = content

@track_execution
def parse_with_snippets(filepath: str) -> Dict[str, Any]:
    """파일을 파싱하여 함수/클래스 스니펫 추출"""
    content = read_file(filepath)
    lines = content.split('\n')

    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        return {
            'success': False,
            'error': f'Syntax error: {e}',
            'snippets': []
        }

    snippets = []

    # AST를 순회하며 함수와 클래스 찾기
    for node in ast.walk(tree):
        snippet = None

        if isinstance(node, ast.FunctionDef):
            # 함수 찾기
            start_line = node.lineno - 1
            end_line = node.end_lineno if hasattr(node, 'end_lineno') else find_end_line(lines, start_line)

            snippet = CodeSnippet(
                name=node.name,
                type='function',
                start_line=start_line,
                end_line=end_line,
                content='\n'.join(lines[start_line:end_line])
            )

        elif isinstance(node, ast.ClassDef):
            # 클래스 찾기
            start_line = node.lineno - 1
            end_line = node.end_lineno if hasattr(node, 'end_lineno') else find_end_line(lines, start_line)

            snippet = CodeSnippet(
                name=node.name,
                type='class',
                start_line=start_line,
                end_line=end_line,
                content='\n'.join(lines[start_line:end_line])
            )

            # 클래스 내부의 메서드들도 찾기
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    method_start = item.lineno - 1
                    method_end = item.end_lineno if hasattr(item, 'end_lineno') else find_end_line(lines, method_start)

                    method_snippet = CodeSnippet(
                        name=f"{node.name}.{item.name}",
                        type='method',
                        start_line=method_start,
                        end_line=method_end,
                        content='\n'.join(lines[method_start:method_end])
                    )
                    snippets.append(method_snippet)

        if snippet:
            snippets.append(snippet)

    return {
        'success': True,
        'snippets': snippets,
        'total_lines': len(lines),
        'tree': tree  # AST 트리도 반환
    }

def find_end_line(lines: List[str], start_line: int) -> int:
    """들여쓰기를 기반으로 블록의 끝 라인 찾기"""
    if start_line >= len(lines):
        return start_line

    # 시작 라인의 들여쓰기 레벨 확인
    start_indent = len(lines[start_line]) - len(lines[start_line].lstrip())

    # 다음 라인부터 검사
    for i in range(start_line + 1, len(lines)):
        line = lines[i]

        # 빈 줄은 무시
        if not line.strip():
            continue

        # 현재 라인의 들여쓰기 레벨
        current_indent = len(line) - len(line.lstrip())

        # 들여쓰기가 같거나 적으면 블록 종료
        if current_indent <= start_indent:
            return i

    # 파일 끝까지 도달
    return len(lines)

@track_execution
def replace_block(
    filepath: str, 
    old_code: str, 
    new_code: str,
    backup: bool = True
) -> Dict[str, Any]:
    """코드 블록 교체"""
    try:
        content = read_file(filepath)

        # 정확한 매칭을 위해 공백 정규화
        old_code_normalized = normalize_whitespace(old_code)
        content_normalized = normalize_whitespace(content)

        # 코드 블록 찾기
        if old_code_normalized not in content_normalized:
            # 부분 매칭 시도
            match_info = find_fuzzy_match(content, old_code)
            if not match_info['found']:
                return {
                    'success': False,
                    'error': 'Code block not found',
                    'suggestion': match_info.get('suggestion', '')
                }

            # 퍼지 매칭된 코드로 교체
            old_code = match_info['matched_code']

        # 백업 생성
        if backup:
            backup_path = f"{filepath}.backup"
            write_file(backup_path, content)

        # 코드 교체
        new_content = content.replace(old_code, new_code)

        # 변경사항 확인
        if new_content == content:
            return {
                'success': False,
                'error': 'No changes made'
            }

        # 파일 저장
        write_file(filepath, new_content)

        return {
            'success': True,
            'filepath': filepath,
            'backup_path': backup_path if backup else None,
            'lines_changed': abs(len(new_code.split('\n')) - len(old_code.split('\n')))
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

@track_execution
def insert_block(
    filepath: str,
    code: str,
    after: Optional[str] = None,
    before: Optional[str] = None,
    line_number: Optional[int] = None
) -> Dict[str, Any]:
    """코드 블록 삽입"""
    try:
        content = read_file(filepath)
        lines = content.split('\n')

        # 삽입 위치 결정
        if line_number is not None:
            # 라인 번호로 삽입
            insert_pos = line_number - 1
        elif after:
            # 특정 코드 뒤에 삽입
            insert_pos = find_code_position(lines, after, 'after')
        elif before:
            # 특정 코드 앞에 삽입
            insert_pos = find_code_position(lines, before, 'before')
        else:
            return {
                'success': False,
                'error': 'No insertion point specified'
            }

        if insert_pos < 0:
            return {
                'success': False,
                'error': 'Insertion point not found'
            }

        # 코드 삽입
        code_lines = code.split('\n')
        new_lines = lines[:insert_pos] + code_lines + lines[insert_pos:]

        # 파일 저장
        new_content = '\n'.join(new_lines)
        write_file(filepath, new_content)

        return {
            'success': True,
            'filepath': filepath,
            'inserted_at': insert_pos + 1,
            'lines_added': len(code_lines)
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def normalize_whitespace(code: str) -> str:
    """공백 정규화"""
    # 탭을 공백으로
    code = code.replace('\t', '    ')
    # 연속된 공백을 하나로
    code = re.sub(r' +', ' ', code)
    # 줄 끝 공백 제거
    lines = [line.rstrip() for line in code.split('\n')]
    return '\n'.join(lines)

def find_fuzzy_match(content: str, target: str) -> Dict[str, Any]:
    """퍼지 매칭으로 비슷한 코드 찾기"""
    # 타입 검증 추가
    if not isinstance(content, str):
        raise TypeError(f"content must be a string, not {type(content).__name__}")
    if not isinstance(target, str):
        raise TypeError(f"target must be a string, not {type(target).__name__}")
    
    lines = content.split('\n')
    target_lines = target.strip().split('\n')

    best_match = {
        'found': False,
        'matched_code': '',
        'similarity': 0,
        'suggestion': ''
    }

    # 슬라이딩 윈도우로 검색
    for i in range(len(lines) - len(target_lines) + 1):
        window = lines[i:i + len(target_lines)]
        similarity = calculate_similarity(window, target_lines)

        if similarity > best_match['similarity']:
            best_match['similarity'] = similarity
            best_match['matched_code'] = '\n'.join(window)

            if similarity > 0.8:  # 80% 이상 유사하면 매칭
                best_match['found'] = True
                return best_match

    # 매칭 실패시 제안
    if best_match['similarity'] > 0.5:
        best_match['suggestion'] = f"Similar code found with {best_match['similarity']*100:.1f}% match"

    return best_match

def calculate_similarity(lines1: List[str], lines2: List[str]) -> float:
    """두 코드 블록의 유사도 계산"""
    if len(lines1) != len(lines2):
        return 0.0

    matches = sum(1 for l1, l2 in zip(lines1, lines2) if l1.strip() == l2.strip())
    return matches / len(lines1)

def find_code_position(lines: List[str], target: str, position: str) -> int:
    """코드 위치 찾기"""
    target_lines = target.strip().split('\n')

    for i in range(len(lines) - len(target_lines) + 1):
        if all(lines[i + j].strip() == target_lines[j].strip() 
               for j in range(len(target_lines))):
            if position == 'after':
                return i + len(target_lines)
            else:  # before
                return i

    return -1

# 사용 가능한 함수 목록
__all__ = [
    'parse_with_snippets', 'replace_block', 'insert_block',
    'CodeSnippet'
]
