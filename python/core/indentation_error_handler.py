
"""
IndentationError 전용 예외 처리 및 피드백 시스템
"""
import ast
import re
from typing import Dict, List, Optional, Tuple

class IndentationErrorHandler:
    """들여쓰기 오류에 대한 상세한 분석과 해결책 제공"""
    
    def __init__(self, wisdom_manager=None):
        self.wisdom_manager = wisdom_manager
        self.common_patterns = {
            "expected an indented block": self._fix_missing_indent,
            "unexpected indent": self._fix_unexpected_indent,
            "unindent does not match": self._fix_unindent_mismatch,
            "inconsistent use of tabs and spaces": self._fix_mixed_indentation
        }
    
    def handle_error(self, code: str, error: IndentationError) -> Dict:
        """
        들여쓰기 오류를 분석하고 해결책 제공
        
        Returns:
            dict: {
                'error_type': str,
                'line': int,
                'column': int,
                'message': str,
                'suggestion': str,
                'auto_fix': Optional[str],
                'context': List[str]
            }
        """
        lines = code.split('\n')
        error_line = error.lineno - 1
        
        result = {
            'error_type': 'IndentationError',
            'line': error.lineno,
            'column': error.offset or 0,
            'message': error.msg,
            'suggestion': '',
            'auto_fix': None,
            'context': self._get_context(lines, error_line)
        }
        
        # 오류 패턴별 처리
        for pattern, fix_func in self.common_patterns.items():
            if pattern in error.msg.lower():
                suggestion, fixed_code = fix_func(lines, error_line)
                result['suggestion'] = suggestion
                result['auto_fix'] = fixed_code
                break
        
        # Wisdom에 기록
        if self.wisdom_manager:
            self.wisdom_manager.track_mistake(
                'indentation_error',
                f"{error.msg} at line {error.lineno}"
            )
        
        return result
    
    def _get_context(self, lines: List[str], error_line: int) -> List[str]:
        """오류 주변 코드 컨텍스트 반환"""
        start = max(0, error_line - 2)
        end = min(len(lines), error_line + 3)
        
        context = []
        for i in range(start, end):
            prefix = ">>> " if i == error_line else "    "
            context.append(f"{i+1:3d} {prefix}{lines[i] if i < len(lines) else ''}")
        
        return context
    
    def _fix_missing_indent(self, lines: List[str], error_line: int) -> Tuple[str, Optional[str]]:
        """expected an indented block 오류 수정"""
        if error_line > 0:
            prev_line = lines[error_line - 1]
            if prev_line.rstrip().endswith(':'):
                indent = len(prev_line) - len(prev_line.lstrip())
                
                # 다음 줄에 내용이 있으면 들여쓰기
                if error_line < len(lines) and lines[error_line].strip():
                    fixed_lines = lines.copy()
                    fixed_lines[error_line] = ' ' * (indent + 4) + lines[error_line].lstrip()
                    
                    suggestion = f"콜론(:) 다음 줄은 들여쓰기가 필요합니다.\n"
                    suggestion += f"수정: '{fixed_lines[error_line]}'"
                    
                    return suggestion, '\n'.join(fixed_lines)
                else:
                    # pass 문 추가
                    fixed_lines = lines.copy()
                    fixed_lines.insert(error_line, ' ' * (indent + 4) + 'pass')
                    
                    suggestion = "빈 블록에는 'pass' 문을 추가하세요."
                    return suggestion, '\n'.join(fixed_lines)
        
        return "콜론(:) 다음에는 들여쓰기된 블록이 필요합니다.", None
    
    def _fix_unexpected_indent(self, lines: List[str], error_line: int) -> Tuple[str, Optional[str]]:
        """unexpected indent 오류 수정"""
        if error_line < len(lines):
            # 이전 줄들의 들여쓰기 수준 확인
            expected_indent = 0
            for i in range(error_line - 1, -1, -1):
                if lines[i].strip() and not lines[i].lstrip().startswith('#'):
                    expected_indent = len(lines[i]) - len(lines[i].lstrip())
                    break
            
            fixed_lines = lines.copy()
            fixed_lines[error_line] = ' ' * expected_indent + lines[error_line].lstrip()
            
            suggestion = f"불필요한 들여쓰기를 제거하세요.\n"
            suggestion += f"예상 들여쓰기: {expected_indent}칸"
            
            return suggestion, '\n'.join(fixed_lines)
        
        return "예상치 못한 들여쓰기입니다.", None
    
    def _fix_unindent_mismatch(self, lines: List[str], error_line: int) -> Tuple[str, Optional[str]]:
        """unindent does not match 오류 수정"""
        if error_line < len(lines):
            # 유효한 들여쓰기 수준 찾기
            valid_indents = set()
            for i in range(error_line):
                if lines[i].strip():
                    indent = len(lines[i]) - len(lines[i].lstrip())
                    valid_indents.add(indent)
            
            current_indent = len(lines[error_line]) - len(lines[error_line].lstrip())
            
            # 가장 가까운 유효한 들여쓰기 찾기
            if valid_indents:
                closest_indent = min(valid_indents, key=lambda x: abs(x - current_indent))
                
                fixed_lines = lines.copy()
                fixed_lines[error_line] = ' ' * closest_indent + lines[error_line].lstrip()
                
                suggestion = f"들여쓰기가 상위 블록과 맞지 않습니다.\n"
                suggestion += f"유효한 들여쓰기: {sorted(valid_indents)}"
                
                return suggestion, '\n'.join(fixed_lines)
        
        return "들여쓰기 수준을 확인하세요.", None
    
    def _fix_mixed_indentation(self, lines: List[str], error_line: int) -> Tuple[str, Optional[str]]:
        """탭과 스페이스 혼용 오류 수정"""
        fixed_lines = []
        for line in lines:
            # 탭을 4칸 공백으로 변환
            fixed_line = line.replace('\t', '    ')
            fixed_lines.append(fixed_line)
        
        suggestion = "탭과 스페이스를 혼용하지 마세요.\n"
        suggestion += "모든 탭을 4칸 공백으로 변환했습니다."
        
        return suggestion, '\n'.join(fixed_lines)
