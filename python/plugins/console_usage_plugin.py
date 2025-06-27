"""
Console Usage Plugin
console.log/error 사용을 logger로 변환
"""

import re
from typing import List, Optional
from core.wisdom_plugin_base import WisdomPlugin, Detection, WisdomPattern


class ConsoleUsagePlugin(WisdomPlugin):
    """Console 사용 감지 및 Logger로 변환"""
    
    def __init__(self):
        super().__init__()
        self.name = "Console Usage Checker"
        self.description = "console.log/error를 logger로 변환"
        self.patterns = self._init_patterns()
        
    def _init_patterns(self) -> List[WisdomPattern]:
        """Console 사용 패턴 정의"""
        return [
            WisdomPattern(
                id="console_log",
                type="warning",
                severity="medium",
                pattern=r"console\.log\s*\(",
                description="console.log 사용",
                fix_suggestion="logger.info() 사용"
            ),
            WisdomPattern(
                id="console_error",
                type="warning",
                severity="medium",
                pattern=r"console\.error\s*\(",
                description="console.error 사용",
                fix_suggestion="logger.error() 사용"
            ),
            WisdomPattern(
                id="console_warn",
                type="warning",
                severity="medium",
                pattern=r"console\.warn\s*\(",
                description="console.warn 사용",
                fix_suggestion="logger.warning() 사용"
            ),
            WisdomPattern(
                id="console_debug",
                type="warning",
                severity="low",
                pattern=r"console\.debug\s*\(",
                description="console.debug 사용",
                fix_suggestion="logger.debug() 사용"
            )
        ]
        
    def check(self, code: str, filename: str) -> List[Detection]:
        """코드에서 console 사용 검사"""
        # TypeScript/JavaScript 파일만 검사
        if not filename.endswith(('.ts', '.js', '.tsx', '.jsx')):
            return []
            
        detections = []
        lines = code.split('\n')
        
        for pattern in self.patterns:
            matches = re.finditer(pattern.pattern, code)
            for match in matches:
                line_num = code[:match.start()].count('\n') + 1
                line_content = lines[line_num-1] if line_num <= len(lines) else ""
                
                # 주석이나 문자열 내부가 아닌지 확인
                if not self._is_in_comment_or_string(line_content, match.start()):
                    detections.append(Detection(
                        plugin_name=self.name,
                        pattern=pattern,
                        line_number=line_num,
                        column_number=match.start() - code.rfind('\n', 0, match.start()),
                        matched_text=match.group(0),
                        context=line_content.strip(),
                        filename=filename
                    ))
                    
        return detections
        
    def _is_in_comment_or_string(self, line: str, position: int) -> bool:
        """주석이나 문자열 내부인지 확인"""
        # 간단한 휴리스틱 - 실제로는 더 정교한 파싱 필요
        before = line[:position]
        
        # 주석 확인
        if '//' in before:
            return True
            
        # 문자열 확인 (간단한 버전)
        single_quotes = before.count("'") % 2 == 1
        double_quotes = before.count('"') % 2 == 1
        
        return single_quotes or double_quotes
        
    def fix(self, code: str, detection: Detection) -> Optional[str]:
        """Console 사용을 Logger로 자동 변환"""
        replacements = {
            "console_log": ("console.log", "logger.info"),
            "console_error": ("console.error", "logger.error"),
            "console_warn": ("console.warn", "logger.warning"),
            "console_debug": ("console.debug", "logger.debug")
        }
        
        if detection.pattern.id in replacements:
            old, new = replacements[detection.pattern.id]
            # Logger import 확인
            if "import" not in code or "logger" not in code:
                # Logger import 추가
                import_line = "import { logger } from '../utils/logger';\n"
                code = import_line + code
            
            # Console을 Logger로 변경
            return code.replace(old, new)
            
        return None
        
    def get_statistics(self) -> dict:
        """통계 정보 반환"""
        return {
            "total_console_usage": sum(self.detection_count.values()),
            "by_type": dict(self.detection_count),
            "files_affected": len(set(d.filename for d in self.detections))
        }
