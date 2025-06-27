"""
Console Usage Plugin - console 사용 감지 및 logger 변환
console.log/error/warn 등을 logger로 자동 변환
"""

import re
from typing import List
from ..core.wisdom_plugin_base import WisdomPlugin, Detection, WisdomPattern

class ConsoleUsagePlugin(WisdomPlugin):
    """console 사용 패턴 감지 및 logger 변환"""
    
    @property
    def plugin_name(self) -> str:
        return "ConsoleUsagePlugin"
    
    @property
    def plugin_version(self) -> str:
        return "1.0.0"
    
    def _init_patterns(self):
        """console 관련 패턴 정의"""
        self.patterns = [
            WisdomPattern(
                key="console_log",
                name="console.log 사용",
                description="console.log 대신 logger.info 사용 권장",
                severity="medium",
                category="style",
                fix_hint="logger.info()로 변경",
                auto_fixable=True
            ),
            WisdomPattern(
                key="console_error",
                name="console.error 사용",
                description="console.error 대신 logger.error 사용 권장",
                severity="medium",
                category="style",
                fix_hint="logger.error()로 변경",
                auto_fixable=True
            ),
            WisdomPattern(
                key="print_usage",
                name="print() 사용",
                description="Python에서 print() 대신 logger 사용 권장",
                severity="low",
                category="style",
                fix_hint="logger.info()로 변경",
                auto_fixable=True
            )
        ]
    
    def analyze(self, code: str, filename: str = None) -> List[Detection]:
        """console 사용 패턴 분석"""
        detections = []
        lines = code.split('\n')
        
        # 파일 확장자 확인
        is_python = filename and filename.endswith('.py')
        
        for i, line in enumerate(lines):
            # JavaScript/TypeScript console 패턴
            if not is_python:
                if 'console.log' in line:
                    detections.append(Detection(
                        pattern_key="console_log",
                        line_number=i + 1,
                        column=0,
                        message="console.log 사용 감지: logger.info 사용 권장",
                        severity="medium",
                        context=line.strip(),
                        auto_fix=line.replace('console.log', 'logger.info')
                    ))
                
                if 'console.error' in line:
                    detections.append(Detection(
                        pattern_key="console_error",
                        line_number=i + 1,
                        column=0,
                        message="console.error 사용 감지: logger.error 사용 권장",
                        severity="medium",
                        context=line.strip(),
                        auto_fix=line.replace('console.error', 'logger.error')
                    ))
            
            # Python print() 패턴
            if is_python and 'print(' in line and not line.strip().startswith('#'):
                detections.append(Detection(
                    pattern_key="print_usage",
                    line_number=i + 1,
                    column=0,
                    message="print() 사용 감지: logger 사용 권장",
                    severity="low",
                    context=line.strip(),
                    auto_fix=line.replace('print(', 'logger.info(')
                ))
        
        return detections
    
    def auto_fix(self, code: str, detection: Detection) -> str:
        """console/print 사용 자동 수정"""
        if detection.auto_fix:
            lines = code.split('\n')
            if 0 < detection.line_number <= len(lines):
                lines[detection.line_number - 1] = detection.auto_fix
                return '\n'.join(lines)
        return code
