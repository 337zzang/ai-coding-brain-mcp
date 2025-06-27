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
                auto_fixable=False
            ),
            WisdomPattern(
                key="mixed_indentation",
                name="혼합된 들여쓰기",
                description="탭과 공백이 혼재된 들여쓰기",
                severity="critical",
                category="syntax",
                fix_hint="일관된 들여쓰기 (4 spaces) 사용",
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
        
        # 1. 수동 들여쓰기 조작 감지 - 간단한 패턴만
        for i, line in enumerate(lines):
            # lines[i] = '    ' + 패턴
            if "lines[" in line and "] = '" in line and "' +" in line:
                if "    " in line or "  " in line:
                    detections.append(Detection(
                        pattern_key="manual_indentation",
                        line_number=i + 1,
                        column=0,
                        message="수동 들여쓰기 조작 감지: AST 기반 도구 사용 권장",
                        severity="high",
                        context=line.strip()
                    ))
        
        # 2. 탭 문자 감지
        for i, line in enumerate(lines):
            if '\t' in line:
                detections.append(Detection(
                    pattern_key="mixed_indentation",
                    line_number=i + 1,
                    column=0,
                    message="탭 문자 사용 감지: 공백 사용 권장",
                    severity="critical",
                    context=line.strip()
                ))
        
        return detections
    
    def auto_fix(self, code: str, detection: Detection) -> str:
        """들여쓰기 자동 수정"""
        if detection.pattern_key == "mixed_indentation":
            # 탭을 공백으로 변환
            return code.replace('\t', '    ')
        return code
