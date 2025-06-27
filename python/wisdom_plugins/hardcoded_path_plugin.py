"""
Hardcoded Path Plugin - 하드코딩된 경로 감지
절대 경로나 하드코딩된 파일 경로를 감지하고 개선 제안
"""

import re
import os
from typing import List
from ..core.wisdom_plugin_base import WisdomPlugin, Detection, WisdomPattern

class HardcodedPathPlugin(WisdomPlugin):
    """하드코딩된 경로 패턴 감지"""
    
    @property
    def plugin_name(self) -> str:
        return "HardcodedPathPlugin"
    
    @property
    def plugin_version(self) -> str:
        return "1.0.0"
    
    def _init_patterns(self):
        """경로 관련 패턴 정의"""
        self.patterns = [
            WisdomPattern(
                key="absolute_path_windows",
                name="Windows 절대 경로",
                description="하드코딩된 Windows 절대 경로",
                severity="high",
                category="portability",
                fix_hint="os.path.join() 또는 pathlib 사용",
                auto_fixable=False
            ),
            WisdomPattern(
                key="absolute_path_unix",
                name="Unix 절대 경로",
                description="하드코딩된 Unix 절대 경로",
                severity="high",
                category="portability",
                fix_hint="상대 경로나 환경 변수 사용",
                auto_fixable=False
            )
        ]
    
    def analyze(self, code: str, filename: str = None) -> List[Detection]:
        """하드코딩된 경로 패턴 분석"""
        detections = []
        lines = code.split('\n')
        
        for i, line in enumerate(lines):
            # 주석 제외
            if line.strip().startswith('#') or line.strip().startswith('//'):
                continue
            
            # Windows 경로 패턴 (C:\ 등) - 간단한 검사
            if 'C:\\' in line or 'D:\\' in line:
                detections.append(Detection(
                    pattern_key="absolute_path_windows",
                    line_number=i + 1,
                    column=0,
                    message="Windows 절대 경로 감지: 이식성 문제 가능",
                    severity="high",
                    context=line.strip()
                ))
            
            # Unix 경로 패턴
            unix_paths = ['/home/', '/usr/', '/etc/', '/var/', '/opt/']
            for path in unix_paths:
                if path in line:
                    detections.append(Detection(
                        pattern_key="absolute_path_unix",
                        line_number=i + 1,
                        column=0,
                        message="Unix 절대 경로 감지: 이식성 문제 가능",
                        severity="high",
                        context=line.strip()
                    ))
                    break
        
        return detections
    
    def auto_fix(self, code: str, detection: Detection) -> str:
        """하드코딩된 경로 자동 수정"""
        # 복잡한 경로 변환은 수동으로 처리하도록 함
        return code
