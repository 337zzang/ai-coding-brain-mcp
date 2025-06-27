"""
Hardcoded Path Plugin - Simple Version
"""

import re
from typing import List, Optional
from core.wisdom_plugin_base import WisdomPlugin, Detection, WisdomPattern


class HardcodedPathPlugin(WisdomPlugin):
    """하드코딩된 경로 감지"""
    
    def __init__(self):
        super().__init__()
        self.name = "Hardcoded Path Checker"
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
                id="windows_path",
                type="warning",
                severity="high",
                pattern=r"['\"][A-Za-z]:\\\\[^'\"]+['\"]",
                description="Windows 절대 경로",
                fix_suggestion="os.path.join() 사용"
            )
        ]
        
    def analyze(self, code: str, filename: str = None) -> List[Detection]:
        detections = []
        lines = code.split('\n')
        
        for pattern in self.patterns:
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
