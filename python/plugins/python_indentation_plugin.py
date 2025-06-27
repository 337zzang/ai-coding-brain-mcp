"""
Python Indentation Plugin - Simple Version
"""

import re
from typing import List, Optional
from core.wisdom_plugin_base import WisdomPlugin, Detection, WisdomPattern


class PythonIndentationPlugin(WisdomPlugin):
    """Python 들여쓰기 문제 감지"""
    
    def __init__(self):
        super().__init__()
        self.name = "Python Indentation Checker"
        self.patterns = self._init_patterns()
        
    @property
    def plugin_name(self) -> str:
        return self.name
        
    @property
    def plugin_version(self) -> str:
        return "1.0.0"
        
    def _init_patterns(self) -> List[WisdomPattern]:
        return [
            WisdomPattern(
                key="manual_indent",
                name="수동 들여쓰기 조작",
                description="수동으로 들여쓰기를 조작하는 패턴 감지",
                severity="high",
                category="syntax",
                fix_hint="AST 도구 사용",
                auto_fixable=False
            )
        ]
        
    def analyze(self, code: str, filename: str = None) -> List[Detection]:
        detections = []
        lines = code.split('\n')
        
        for pattern in self.patterns:
            if pattern.pattern:
                matches = re.finditer(pattern.pattern, code)
                for match in matches:
                    line_num = code[:match.start()].count('\n') + 1
                    detections.append(Detection(
                        plugin_name=self.name,
                        pattern=pattern,
                        line_number=line_num,
                        column_number=0,
                        matched_text=match.group(0),
                        context=lines[line_num-1] if line_num <= len(lines) else "",
                        filename=filename or "unknown"
                    ))
        return detections
        
    def auto_fix(self, code: str, detection: Detection) -> str:
        # 간단한 버전 - 수정 없음
        return code
