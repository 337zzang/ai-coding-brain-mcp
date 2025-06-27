"""
Hardcoded Path Plugin
Windows/Unix 절대 경로 감지
"""

import re
from typing import List, Optional
import os
from python.core.wisdom_plugin_base import WisdomPlugin, Detection, WisdomPattern


class HardcodedPathPlugin(WisdomPlugin):
    """하드코딩된 경로 감지 및 수정"""
    
    def __init__(self):
        super().__init__()
        self.name = "Hardcoded Path Checker"
        self.description = "절대 경로 하드코딩 감지"
        self.patterns = self._init_patterns()
        
    def _init_patterns(self) -> List[WisdomPattern]:
        """경로 패턴 정의"""
        return [
            WisdomPattern(
                id="windows_path",
                type="warning",
                severity="high",
                pattern=r"['\"][A-Za-z]:\\\\[^'\"]+['\"]",
                description="Windows 절대 경로",
                fix_suggestion="os.path.join() 또는 pathlib 사용"
            ),
            WisdomPattern(
                id="unix_path",
                type="warning",
                severity="high",
                pattern=r"['\"]/(usr|home|var|etc|opt)/[^'\"]+['\"]",
                description="Unix 절대 경로",
                fix_suggestion="os.path.join() 또는 pathlib 사용"
            ),
            WisdomPattern(
                id="home_path",
                type="warning",
                severity="medium",
                pattern=r"['\"]~/[^'\"]+['\"]",
                description="홈 디렉토리 경로",
                fix_suggestion="os.path.expanduser() 사용"
            )
        ]
        
    def check(self, code: str, filename: str) -> List[Detection]:
        """코드에서 하드코딩된 경로 검사"""
        detections = []
        lines = code.split('\n')
        
        for pattern in self.patterns:
            matches = re.finditer(pattern.pattern, code)
            for match in matches:
                line_num = code[:match.start()].count('\n') + 1
                line_content = lines[line_num-1] if line_num <= len(lines) else ""
                
                # 일부 예외 처리 (예: URL, import 구문)
                if not self._is_valid_path_usage(line_content, match.group(0)):
                    continue
                    
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
        
    def _is_valid_path_usage(self, line: str, matched_text: str) -> bool:
        """유효한 경로 사용인지 확인"""
        # URL인 경우 제외
        if 'http://' in line or 'https://' in line:
            return False
            
        # import/require 구문 제외
        if 'import' in line or 'require' in line:
            return False
            
        # 주석 제외
        if line.strip().startswith('#') or line.strip().startswith('//'):
            return False
            
        return True
        
    def fix(self, code: str, detection: Detection) -> Optional[str]:
        """하드코딩된 경로를 동적 경로로 변환"""
        matched = detection.matched_text.strip('"\'')
        
        if detection.pattern.id == "windows_path":
            # Windows 경로를 os.path.join으로 변환
            parts = matched.replace('\\\\', '/').split('/')
            new_path = f"os.path.join('{parts[0]}', " + ", ".join(f"'{p}'" for p in parts[1:]) + ")"
            
        elif detection.pattern.id == "unix_path":
            # Unix 경로를 os.path.join으로 변환
            parts = matched.split('/')
            new_path = "os.path.join('/', " + ", ".join(f"'{p}'" for p in parts[1:] if p) + ")"
            
        elif detection.pattern.id == "home_path":
            # 홈 경로를 expanduser로 변환
            new_path = f"os.path.expanduser('{matched}')"
            
        else:
            return None
            
        # import 구문 추가 확인
        if "import os" not in code:
            code = "import os\n" + code
            
        # 경로 교체
        return code.replace(detection.matched_text, new_path)
        
    def get_statistics(self) -> dict:
        """통계 정보 반환"""
        path_types = {}
        for d in self.detections:
            path_type = d.pattern.id
            path_types[path_type] = path_types.get(path_type, 0) + 1
            
        return {
            "total_hardcoded_paths": len(self.detections),
            "by_type": path_types,
            "files_with_paths": len(set(d.filename for d in self.detections))
        }
