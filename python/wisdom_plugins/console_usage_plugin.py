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
                auto_fixable=True,
                examples=[
                    {"bad": "console.log('message')", 
                     "good": "logger.info('message')"}
                ]
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
                key="console_warn",
                name="console.warn 사용",
                description="console.warn 대신 logger.warning 사용 권장",
                severity="medium",
                category="style",
                fix_hint="logger.warning()로 변경",
                auto_fixable=True
            ),
            WisdomPattern(
                key="console_debug",
                name="console.debug 사용",
                description="console.debug 대신 logger.debug 사용 권장",
                severity="low",
                category="style",
                fix_hint="logger.debug()로 변경",
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
        
        # 파일 확장자에 따라 다른 패턴 적용
        is_python = filename and filename.endswith('.py')
        is_js_ts = filename and (filename.endswith('.js') or filename.endswith('.ts'))
        
        for i, line in enumerate(lines):
            # JavaScript/TypeScript console 패턴
            if not is_python:  # JS/TS 또는 확장자 불명
                # console.log
                if match := re.search(r'console\.log\s*\(', line):
                    detections.append(Detection(
                        pattern_key="console_log",
                        line_number=i + 1,
                        column=match.start(),
                        message="console.log 사용 감지: logger.info 사용 권장",
                        severity="medium",
                        context=line.strip(),
                        auto_fix=line.replace('console.log', 'logger.info')
                    ))
                
                # console.error
                if match := re.search(r'console\.error\s*\(', line):
                    detections.append(Detection(
                        pattern_key="console_error",
                        line_number=i + 1,
                        column=match.start(),
                        message="console.error 사용 감지: logger.error 사용 권장",
                        severity="medium",
                        context=line.strip(),
                        auto_fix=line.replace('console.error', 'logger.error')
                    ))
                
                # console.warn
                if match := re.search(r'console\.warn\s*\(', line):
                    detections.append(Detection(
                        pattern_key="console_warn",
                        line_number=i + 1,
                        column=match.start(),
                        message="console.warn 사용 감지: logger.warning 사용 권장",
                        severity="medium",
                        context=line.strip(),
                        auto_fix=line.replace('console.warn', 'logger.warning')
                    ))
                
                # console.debug
                if match := re.search(r'console\.debug\s*\(', line):
                    detections.append(Detection(
                        pattern_key="console_debug",
                        line_number=i + 1,
                        column=match.start(),
                        message="console.debug 사용 감지: logger.debug 사용 권장",
                        severity="low",
                        context=line.strip(),
                        auto_fix=line.replace('console.debug', 'logger.debug')
                    ))
            
            # Python print() 패턴
            if is_python:
                # print() 함수 사용 (주석과 문자열 내부 제외)
                # 간단한 휴리스틱: 줄의 시작이나 공백 후 print(
                if match := re.search(r'(?:^|\s)print\s*\(', line):
                    # 주석인지 확인
                    if not line.strip().startswith('#'):
                        detections.append(Detection(
                            pattern_key="print_usage",
                            line_number=i + 1,
                            column=match.start(),
                            message="print() 사용 감지: logger 사용 권장",
                            severity="low",
                            context=line.strip(),
                            fix_hint="logging 모듈을 import하고 logger.info() 사용",
                            auto_fix=self._convert_print_to_logger(line)
                        ))
        
        return detections
    
    def _convert_print_to_logger(self, line: str) -> str:
        """print()를 logger.info()로 변환"""
        # 간단한 변환 (복잡한 경우는 수동 처리 필요)
        # print("text") -> logger.info("text")
        # print(f"text {var}") -> logger.info(f"text {var}")
        return re.sub(r'(?:^|\s)print\s*\(', 'logger.info(', line)
    
    def auto_fix(self, code: str, detection: Detection) -> str:
        """console/print 사용 자동 수정"""
        if detection.auto_fix:
            lines = code.split('\n')
            if 0 < detection.line_number <= len(lines):
                lines[detection.line_number - 1] = detection.auto_fix
                
                # logger import 추가 필요 여부 확인
                fixed_code = '\n'.join(lines)
                
                # Python 파일이고 logger를 사용하는 경우
                if detection.pattern_key == "print_usage" and "logger." in detection.auto_fix:
                    # logging import가 없으면 추가
                    if "import logging" not in fixed_code and "from logging import" not in fixed_code:
                        # 파일 상단에 import 추가
                        import_line = "import logging\nlogger = logging.getLogger(__name__)\n\n"
                        fixed_code = import_line + fixed_code
                
                # JS/TS 파일이고 logger를 사용하는 경우
                elif "logger." in detection.auto_fix:
                    # logger import가 없으면 추가 (프로젝트에 따라 다를 수 있음)
                    if "import.*logger" not in fixed_code.lower():
                        # 일반적인 logger import 패턴
                        import_line = "import { logger } from './utils/logger';\n\n"
                        fixed_code = import_line + fixed_code
                
                return fixed_code
        
        return code
