"""
Python 들여쓰기 문제 감지 플러그인
수동 들여쓰기 조작 패턴을 감지하고 AST 기반 도구 사용을 권장
"""

import re
from typing import List
from core.wisdom_plugin_base import WisdomPlugin, WisdomPattern, Detection

class PythonIndentationPlugin(WisdomPlugin):
    """Python 들여쓰기 관련 문제 감지 플러그인"""
    
    @property
    def plugin_name(self) -> str:
        return "python_indentation"
    
    @property
    def plugin_version(self) -> str:
        return "1.0.0"
    
    def _init_patterns(self):
        """들여쓰기 관련 패턴 초기화"""
        self.patterns = [
            WisdomPattern(
                key="manual_indent",
                name="수동 들여쓰기 조작",
                description="수동으로 들여쓰기를 조작하는 패턴 감지",
                severity="high",
                category="syntax",
                fix_hint="helpers.replace_block() 또는 helpers.insert_block() 사용",
                auto_fixable=False,
                examples=[
                    {
                        "bad": "lines[i] = '    ' + lines[i]",
                        "good": "helpers.replace_block('file.py', 'function_name', new_code)"
                    }
                ]
            ),
            WisdomPattern(
                key="string_concat_indent",
                name="문자열 연결로 들여쓰기",
                description="문자열 연결로 들여쓰기를 추가하는 패턴",
                severity="medium",
                category="syntax",
                fix_hint="AST 기반 도구를 사용하여 구조적으로 코드 수정",
                auto_fixable=False
            )
        ]
        
        # 정규식 패턴 정의
        self.regex_patterns = {
            "manual_indent": r"lines\[\d+\]\s*=\s*[\'\"]\s+[\'\"]\s*\+\s*lines\[\d+\]",
            "string_concat_indent": r"[\'\"][ \t]+[\'\"]\s*\+\s*"
        }
    
    def analyze(self, code: str, filename: str = None) -> List[Detection]:
        """코드에서 들여쓰기 문제 패턴 감지"""
        detections = []
        lines = code.split('\n')
        
        for pattern in self.patterns:
            regex = self.regex_patterns.get(pattern.key)
            if regex:
                for i, line in enumerate(lines):
                    if re.search(regex, line):
                        detections.append(Detection(
                            pattern_key=pattern.key,
                            line_number=i + 1,
                            column=0,
                            message=f"{pattern.name}: {pattern.description}",
                            severity=pattern.severity,
                            context=line.strip(),
                            fix_hint=pattern.fix_hint,
                            metadata={
                                "filename": filename or "unknown",
                                "pattern_name": pattern.name
                            }
                        ))
        
        return detections
    
    def auto_fix(self, code: str, detection: Detection) -> str:
        """들여쓰기 문제 자동 수정 (현재는 수정 없음)"""
        # 들여쓰기 문제는 컨텍스트에 따라 다르므로 자동 수정하지 않음
        return code
    
    def get_statistics(self) -> dict:
        """플러그인 통계 반환"""
        return {
            "patterns_count": len(self.patterns),
            "auto_fixable_count": sum(1 for p in self.patterns if p.auto_fixable),
            "categories": list(set(p.category for p in self.patterns))
        }
