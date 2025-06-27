"""
하드코딩된 경로 감지 플러그인
절대 경로나 하드코딩된 경로를 감지하고 os.path 사용을 권장
"""

import re
from typing import List
from core.wisdom_plugin_base import WisdomPlugin, WisdomPattern, Detection

class HardcodedPathPlugin(WisdomPlugin):
    """하드코딩된 경로 패턴 감지 플러그인"""
    
    @property
    def plugin_name(self) -> str:
        return "hardcoded_path"
    
    @property
    def plugin_version(self) -> str:
        return "1.0.0"
    
    def _init_patterns(self):
        """하드코딩된 경로 관련 패턴 초기화"""
        self.patterns = [
            WisdomPattern(
                key="windows_absolute_path",
                name="Windows 절대 경로",
                description="하드코딩된 Windows 절대 경로 감지",
                severity="high",
                category="portability",
                fix_hint="os.path.join() 또는 pathlib.Path() 사용",
                auto_fixable=False,
                examples=[
                    {
                        "bad": '"C:\\\\Users\\\\admin\\\\file.txt"',
                        "good": 'Path.home() / "file.txt"'
                    }
                ]
            ),
            WisdomPattern(
                key="unix_absolute_path",
                name="Unix/Linux 절대 경로",
                description="하드코딩된 Unix/Linux 절대 경로 감지",
                severity="high",
                category="portability",
                fix_hint="os.path.join() 또는 pathlib.Path() 사용",
                auto_fixable=False
            ),
            WisdomPattern(
                key="hardcoded_separator",
                name="하드코딩된 경로 구분자",
                description="하드코딩된 경로 구분자 사용 감지",
                severity="medium",
                category="portability",
                fix_hint="os.path.sep 또는 pathlib 사용",
                auto_fixable=True
            )
        ]
        
        # 정규식 패턴 정의
        self.regex_patterns = {
            "windows_absolute_path": r"['\"][A-Za-z]:\\\\[^'\"]+['\"]",
            "unix_absolute_path": r"['\"]/(usr|home|var|etc|opt)/[^'\"]+['\"]",
            "hardcoded_separator": r"['\"][^'\"]*[\\/]{2,}[^'\"]*['\"]"
        }
    
    def analyze(self, code: str, filename: str = None) -> List[Detection]:
        """코드에서 하드코딩된 경로 패턴 감지"""
        detections = []
        lines = code.split('\n')
        
        for pattern in self.patterns:
            regex = self.regex_patterns.get(pattern.key)
            if regex:
                for i, line in enumerate(lines):
                    matches = re.finditer(regex, line)
                    for match in matches:
                        detections.append(Detection(
                            pattern_key=pattern.key,
                            line_number=i + 1,
                            column=match.start(),
                            message=f"{pattern.name}: {pattern.description}",
                            severity=pattern.severity,
                            context=line.strip(),
                            fix_hint=pattern.fix_hint,
                            metadata={
                                "filename": filename or "unknown",
                                "pattern_name": pattern.name,
                                "matched_path": match.group(0)
                            }
                        ))
        
        return detections
    
    def auto_fix(self, code: str, detection: Detection) -> str:
        """하드코딩된 경로 자동 수정"""
        lines = code.split('\n')
        
        if detection.pattern_key == "hardcoded_separator":
            if 0 <= detection.line_number - 1 < len(lines):
                line = lines[detection.line_number - 1]
                # 연속된 슬래시를 os.path.sep으로 변경
                fixed_line = re.sub(r'[\\/]{2,}', '", "', line)
                fixed_line = re.sub(r'"([^"]+)"', lambda m: 'os.path.join(' + 
                                  ', '.join(f'"{p}"' for p in m.group(1).split('", "')) + ')', 
                                  fixed_line)
                lines[detection.line_number - 1] = fixed_line
                
                # import os가 없으면 추가
                has_os_import = any("import os" in line for line in lines)
                if not has_os_import:
                    lines.insert(0, "import os")
        
        return '\n'.join(lines)
    
    def get_statistics(self) -> dict:
        """플러그인 통계 반환"""
        return {
            "patterns_count": len(self.patterns),
            "auto_fixable_count": sum(1 for p in self.patterns if p.auto_fixable),
            "categories": list(set(p.category for p in self.patterns))
        }
