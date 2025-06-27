import ast
import re
import textwrap
from typing import Tuple, Optional

class IndentationPreprocessor:
    """코드 실행 전 들여쓰기 문제를 자동으로 수정하는 전처리기"""
    
    def __init__(self):
        self.indent_unit = None  # 프로젝트의 들여쓰기 단위 (자동 감지)
        
    def detect_indent_style(self, code: str) -> int:
        """코드에서 사용된 들여쓰기 스타일 감지 (2칸, 4칸 등)"""
        lines = code.split('\n')
        indent_counts = {}
        
        for line in lines:
            if line and not line.lstrip() == line:  # 들여쓰기가 있는 줄
                indent_size = len(line) - len(line.lstrip())
                if indent_size > 0:
                    # 가장 작은 단위 찾기
                    for i in range(2, 9):  # 2-8칸 들여쓰기 체크
                        if indent_size % i == 0:
                            indent_counts[i] = indent_counts.get(i, 0) + 1
                            break
        
        # 가장 많이 사용된 들여쓰기 단위 반환
        if indent_counts:
            return max(indent_counts.items(), key=lambda x: x[1])[0]
        return 4  # 기본값
    
    def preprocess(self, code: str) -> Tuple[str, bool]:
        """
        코드 전처리 및 자동 수정
        
        Returns:
            Tuple[str, bool]: (수정된 코드, 수정 여부)
        """
        original_code = code
        modified = False
        
        # 1. 선행 공백 제거
        code = textwrap.dedent(code).strip()
        if code != original_code.strip():
            modified = True
        
        # 2. 탭을 공백으로 변환
        if '\t' in code:
            self.indent_unit = self.detect_indent_style(code)
            code = code.replace('\t', ' ' * self.indent_unit)
            modified = True
        
        # 3. AST 파싱 시도 및 자동 수정
        try:
            ast.parse(code)
            return code, modified
        except IndentationError as e:
            # 자동 수정 시도
            fixed_code = self._fix_indentation_error(code, e)
            if fixed_code != code:
                return fixed_code, True
            raise
        
    def _fix_indentation_error(self, code: str, error: IndentationError) -> str:
        """IndentationError 자동 수정 시도"""
        lines = code.split('\n')
        error_line = error.lineno - 1  # 0-based index
        
        if "expected an indented block" in error.msg:
            # 콜론 뒤에 들여쓰기 필요
            if error_line > 0:
                prev_line = lines[error_line - 1].rstrip()
                if prev_line.endswith(':'):
                    # 다음 줄 들여쓰기 또는 pass 추가
                    if error_line < len(lines) and lines[error_line].strip():
                        # 다음 줄이 있으면 들여쓰기
                        current_indent = len(lines[error_line - 1]) - len(lines[error_line - 1].lstrip())
                        lines[error_line] = ' ' * (current_indent + 4) + lines[error_line].lstrip()
                    else:
                        # pass 문 추가
                        current_indent = len(prev_line) - len(prev_line.lstrip())
                        lines.insert(error_line, ' ' * (current_indent + 4) + 'pass')
        
        elif "unexpected indent" in error.msg:
            # 불필요한 들여쓰기 제거
            if error_line < len(lines):
                # 이전 줄들의 들여쓰기 수준 확인
                expected_indent = 0
                for i in range(error_line - 1, -1, -1):
                    if lines[i].strip():
                        expected_indent = len(lines[i]) - len(lines[i].lstrip())
                        break
                lines[error_line] = ' ' * expected_indent + lines[error_line].lstrip()
        
        elif "unindent does not match" in error.msg:
            # 들여쓰기 수준 조정
            if error_line < len(lines):
                # 상위 블록의 들여쓰기 찾기
                for i in range(error_line - 1, -1, -1):
                    if lines[i].strip() and not lines[i].lstrip().startswith('#'):
                        parent_indent = len(lines[i]) - len(lines[i].lstrip())
                        # 현재 줄이 블록 종료면 부모와 같은 수준
                        # 아니면 부모보다 한 단계 더 들여쓰기
                        if lines[error_line].lstrip().startswith(('return', 'break', 'continue', 'pass')):
                            lines[error_line] = ' ' * parent_indent + lines[error_line].lstrip()
                        else:
                            lines[error_line] = ' ' * (parent_indent + 4) + lines[error_line].lstrip()
                        break
        
        return '\n'.join(lines)
