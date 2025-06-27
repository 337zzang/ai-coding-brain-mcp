"""
Python Indentation Plugin
수동 들여쓰기 조작 및 탭 문자 감지
"""

import re
from typing import List, Optional, Tuple
from python.core.wisdom_plugin_base import WisdomPlugin, Detection, WisdomPattern


class PythonIndentationPlugin(WisdomPlugin):
    """Python 들여쓰기 문제 감지 및 수정"""
    
    def __init__(self):
        super().__init__()
        self.name = "Python Indentation Checker"
        self.description = "수동 들여쓰기 조작 및 탭 문자 감지"
        self.patterns = self._init_patterns()
        
    def _init_patterns(self) -> List[WisdomPattern]:
        """들여쓰기 관련 패턴 정의"""
        return [
            WisdomPattern(
                id="manual_indent",
                type="error",
                severity="high",
                pattern=r"lines\[\d+\]\s*=\s*['\"]\\s+['\"]\\s*\+\\s*lines\[\d+\]",
                description="수동 들여쓰기 조작 감지",
                fix_suggestion="AST 기반 도구(replace_block) 사용"
            ),
            WisdomPattern(
                id="tab_character",
                type="error", 
                severity="medium",
                pattern=r"\t",
                description="탭 문자 사용",
                fix_suggestion="공백 4개로 변경"
            ),
            WisdomPattern(
                id="mixed_indent",
                type="error",
                severity="high",
                pattern=None,  # check 메서드에서 처리
                description="탭과 공백 혼용",
                fix_suggestion="일관된 들여쓰기 사용 (공백 4개)"
            )
        ]
        
    def analyze(self, code: str, filename: str) -> List[Detection]:
        """코드에서 들여쓰기 문제 검사"""
        detections = []
        lines = code.split('\n')
        
        # 기본 패턴 검사
        for pattern in self.patterns:
            if pattern.pattern:
                matches = re.finditer(pattern.pattern, code)
                for match in matches:
                    line_num = code[:match.start()].count('\n') + 1
                    detections.append(Detection(
                        plugin_name=self.name,
                        pattern=pattern,
                        line_number=line_num,
                        column_number=match.start() - code.rfind('\n', 0, match.start()),
                        matched_text=match.group(0),
                        context=lines[line_num-1] if line_num <= len(lines) else "",
                        filename=filename
                    ))
        
        # 탭과 공백 혼용 검사
        has_tab = False
        has_space = False
        for i, line in enumerate(lines):
            if line.startswith('\t'):
                has_tab = True
            elif line.startswith(' '):
                has_space = True
                
        if has_tab and has_space:
            detections.append(Detection(
                plugin_name=self.name,
                pattern=self.patterns[2],  # mixed_indent
                line_number=0,
                column_number=0,
                matched_text="Mixed indentation",
                context="File uses both tabs and spaces",
                filename=filename
            ))
            
        return detections
        
    def auto_fix(self, code: str, detection: Detection) -> Optional[str]:
        """들여쓰기 문제 자동 수정"""
        if detection.pattern.id == "tab_character":
            # 탭을 공백 4개로 변경
            return code.replace('\t', '    ')
        elif detection.pattern.id == "manual_indent":
            # 수동 들여쓰기는 AST 도구 사용 권장
            return None
        elif detection.pattern.id == "mixed_indent":
            # 모든 탭을 공백으로 통일
            return code.replace('\t', '    ')
        return None
        
    def get_statistics(self) -> dict:
        """통계 정보 반환"""
        return {
            "total_detections": sum(self.detection_count.values()),
            "by_type": dict(self.detection_count),
            "most_common": max(self.detection_count.items(), key=lambda x: x[1])[0] if self.detection_count else None
        }
