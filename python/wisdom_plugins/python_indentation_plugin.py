"""
Python Indentation Plugin - 파이썬 들여쓰기 규칙 검사
수동 들여쓰기 조작 감지 및 자동 수정
"""

import re
import ast
from typing import List
from ..core.wisdom_plugin_base import WisdomPlugin, Detection, WisdomPattern

class PythonIndentationPlugin(WisdomPlugin):
    """파이썬 들여쓰기 관련 패턴 감지 및 수정"""
    
    @property
    def plugin_name(self) -> str:
        return "PythonIndentationPlugin"
    
    @property
    def plugin_version(self) -> str:
        return "1.0.0"
    
    def _init_patterns(self):
        """들여쓰기 관련 패턴 정의"""
        self.patterns = [
            WisdomPattern(
                key="manual_indentation",
                name="수동 들여쓰기 조작",
                description="코드 문자열에 직접 공백을 추가하는 패턴",
                severity="high",
                category="syntax",
                fix_hint="AST 기반 도구(replace_block, insert_block)를 사용하세요",
                auto_fixable=False,
                examples=[
                    {"bad": "lines[i] = '    ' + lines[i]", 
                     "good": "helpers.replace_block('file.py', 'function_name', new_code)"}
                ]
            ),
            WisdomPattern(
                key="mixed_indentation",
                name="혼합된 들여쓰기",
                description="탭과 공백이 혼재된 들여쓰기",
                severity="critical",
                category="syntax",
                fix_hint="일관된 들여쓰기 (4 spaces) 사용",
                auto_fixable=True
            ),
            WisdomPattern(
                key="incorrect_indentation_level",
                name="잘못된 들여쓰기 레벨",
                description="예상과 다른 들여쓰기 레벨",
                severity="critical",
                category="syntax",
                fix_hint="올바른 들여쓰기 레벨로 수정",
                auto_fixable=True
            )
        ]
    
    def analyze(self, code: str, filename: str = None) -> List[Detection]:
        """들여쓰기 패턴 분석"""
        detections = []
        
        # 파이썬 파일이 아니면 스킵
        if filename and not filename.endswith('.py'):
            return detections
        
        lines = code.split('\n')
        
        # 1. 수동 들여쓰기 조작 감지
        manual_patterns = [
            r"lines\[.*?\]\s*=\s*['"]\s+['"]\s*\+",  # lines[i] = '  ' + 
            r"\+\s*['"]\s{2,}['"]",  # + '    '
            r"['"]\s{2,}['"]\s*\+",  # '    ' +
            r"\.replace\(['"][^'"]*['"],\s*['"]\s+",  # .replace('x', '  ')
        ]
        
        for i, line in enumerate(lines):
            for pattern in manual_patterns:
                if re.search(pattern, line):
                    detections.append(Detection(
                        pattern_key="manual_indentation",
                        line_number=i + 1,
                        column=0,
                        message="수동 들여쓰기 조작 감지: AST 기반 도구 사용 권장",
                        severity="high",
                        context=line.strip(),
                        fix_hint="helpers.replace_block() 또는 desktop-commander:edit_block 사용"
                    ))
        
        # 2. 혼합된 들여쓰기 감지
        has_tabs = False
        has_spaces = False
        
        for i, line in enumerate(lines):
            if line.strip():  # 빈 줄 제외
                leading = line[:len(line) - len(line.lstrip())]
                if '\t' in leading:
                    has_tabs = True
                if ' ' in leading:
                    has_spaces = True
                    
                # 같은 줄에 탭과 공백이 섞여있는 경우
                if '\t' in leading and ' ' in leading:
                    detections.append(Detection(
                        pattern_key="mixed_indentation",
                        line_number=i + 1,
                        column=0,
                        message="탭과 공백이 혼재된 들여쓰기",
                        severity="critical",
                        context=line[:50] + "..." if len(line) > 50 else line,
                        auto_fix=leading.replace('\t', '    ')  # 탭을 4칸 공백으로
                    ))
        
        # 3. AST를 사용한 구문 분석 (들여쓰기 오류 감지)
        try:
            ast.parse(code)
        except IndentationError as e:
            detections.append(Detection(
                pattern_key="incorrect_indentation_level",
                line_number=e.lineno or 1,
                column=e.offset or 0,
                message=f"들여쓰기 오류: {str(e)}",
                severity="critical",
                context=lines[e.lineno - 1] if e.lineno and e.lineno <= len(lines) else "",
                fix_hint="올바른 들여쓰기 레벨로 수정 필요"
            ))
        except SyntaxError as e:
            # 들여쓰기와 관련된 구문 오류만 처리
            if "indent" in str(e).lower():
                detections.append(Detection(
                    pattern_key="incorrect_indentation_level",
                    line_number=e.lineno or 1,
                    column=e.offset or 0,
                    message=f"들여쓰기 관련 구문 오류: {str(e)}",
                    severity="critical",
                    context=lines[e.lineno - 1] if e.lineno and e.lineno <= len(lines) else ""
                ))
        
        return detections
    
    def auto_fix(self, code: str, detection: Detection) -> str:
        """들여쓰기 자동 수정"""
        if detection.pattern_key == "manual_indentation":
            # 수동 들여쓰기는 자동 수정 불가 (AST 도구 사용 필요)
            return code
            
        elif detection.pattern_key == "mixed_indentation":
            # 탭을 공백으로 변환
            lines = code.split('\n')
            if 0 < detection.line_number <= len(lines):
                line = lines[detection.line_number - 1]
                # 탭을 4칸 공백으로 변환
                fixed_line = line.replace('\t', '    ')
                lines[detection.line_number - 1] = fixed_line
                return '\n'.join(lines)
                
        elif detection.pattern_key == "incorrect_indentation_level":
            # 복잡한 들여쓰기 수정은 AST 재구성이 필요
            # 여기서는 기본적인 수정만 시도
            try:
                # autopep8이나 black 같은 도구를 사용하는 것이 이상적
                # 현재는 간단한 수정만
                return code
            except:
                return code
                
        return code
