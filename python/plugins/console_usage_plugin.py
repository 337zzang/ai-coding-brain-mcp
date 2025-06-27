"""
Console 사용 감지 플러그인
TypeScript/JavaScript 코드에서 console.log 사용을 감지하고 logger 사용을 권장
"""

import re
from typing import List
from core.wisdom_plugin_base import WisdomPlugin, WisdomPattern, Detection

class ConsoleUsagePlugin(WisdomPlugin):
    """Console 사용 패턴 감지 플러그인"""
    
    @property
    def plugin_name(self) -> str:
        return "console_usage"
    
    @property
    def plugin_version(self) -> str:
        return "1.0.0"
    
    def _init_patterns(self):
        """Console 사용 관련 패턴 초기화"""
        self.patterns = [
            WisdomPattern(
                key="console_log",
                name="console.log 사용",
                description="TypeScript/JavaScript에서 console.log 사용 감지",
                severity="medium",
                category="style",
                fix_hint="import { logger } from '../utils/logger'; logger.info('메시지');",
                auto_fixable=True,
                examples=[
                    {
                        "bad": "console.log('debug message')",
                        "good": "logger.info('debug message')"
                    }
                ]
            ),
            WisdomPattern(
                key="console_error",
                name="console.error 사용",
                description="TypeScript/JavaScript에서 console.error 사용 감지",
                severity="medium",
                category="style",
                fix_hint="import { logger } from '../utils/logger'; logger.error('에러 메시지');",
                auto_fixable=True
            ),
            WisdomPattern(
                key="console_warn",
                name="console.warn 사용",
                description="TypeScript/JavaScript에서 console.warn 사용 감지",
                severity="low",
                category="style",
                fix_hint="import { logger } from '../utils/logger'; logger.warn('경고 메시지');",
                auto_fixable=True
            )
        ]
        
        # 정규식 패턴 정의
        self.regex_patterns = {
            "console_log": r"console\s*\.\s*log\s*\(",
            "console_error": r"console\s*\.\s*error\s*\(",
            "console_warn": r"console\s*\.\s*warn\s*\("
        }
        
        # logger 메서드 매핑
        self.logger_mapping = {
            "console_log": "info",
            "console_error": "error",
            "console_warn": "warn"
        }
    
    def analyze(self, code: str, filename: str = None) -> List[Detection]:
        """코드에서 console 사용 패턴 감지"""
        detections = []
        
        # TypeScript/JavaScript 파일만 검사
        if filename and not (filename.endswith('.ts') or filename.endswith('.js') or 
                           filename.endswith('.tsx') or filename.endswith('.jsx')):
            return detections
        
        lines = code.split('\n')
        
        for pattern in self.patterns:
            regex = self.regex_patterns.get(pattern.key)
            if regex:
                for i, line in enumerate(lines):
                    match = re.search(regex, line)
                    if match:
                        detections.append(Detection(
                            pattern_key=pattern.key,
                            line_number=i + 1,
                            column=match.start(),
                            message=f"{pattern.name}: {pattern.description}",
                            severity=pattern.severity,
                            context=line.strip(),
                            fix_hint=pattern.fix_hint,
                            auto_fix=self._generate_fix(line, pattern.key),
                            metadata={
                                "filename": filename or "unknown",
                                "pattern_name": pattern.name
                            }
                        ))
        
        return detections
    
    def _generate_fix(self, line: str, pattern_key: str) -> str:
        """console 사용을 logger로 변경하는 수정 코드 생성"""
        logger_method = self.logger_mapping.get(pattern_key, "info")
        
        # console.xxx( -> logger.xxx( 로 변경
        regex = self.regex_patterns.get(pattern_key)
        if regex:
            fixed_line = re.sub(
                regex,
                f"logger.{logger_method}(",
                line
            )
            return fixed_line
        
        return line
    
    def auto_fix(self, code: str, detection: Detection) -> str:
        """console 사용을 logger로 자동 변경"""
        lines = code.split('\n')
        
        if 0 <= detection.line_number - 1 < len(lines):
            if detection.auto_fix:
                lines[detection.line_number - 1] = detection.auto_fix
                
                # import 문이 없으면 파일 상단에 추가
                has_logger_import = any("from '../utils/logger'" in line for line in lines)
                if not has_logger_import:
                    # 첫 번째 import 문을 찾아서 그 다음에 추가
                    import_index = 0
                    for i, line in enumerate(lines):
                        if line.strip().startswith('import'):
                            import_index = i + 1
                        elif import_index > 0 and not line.strip().startswith('import'):
                            break
                    
                    lines.insert(import_index, "import { logger } from '../utils/logger';")
        
        return '\n'.join(lines)
    
    def get_statistics(self) -> dict:
        """플러그인 통계 반환"""
        return {
            "patterns_count": len(self.patterns),
            "auto_fixable_count": sum(1 for p in self.patterns if p.auto_fixable),
            "categories": list(set(p.category for p in self.patterns))
        }
