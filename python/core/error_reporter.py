"""
중앙화된 에러 보고 시스템
v30.2 - 투명하고 즉각적인 에러 보고
"""
import json
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union
from dataclasses import dataclass, asdict

@dataclass
class ErrorReport:
    """에러 보고 데이터 구조"""
    timestamp: str
    location: str  # 파일:라인 또는 단계
    error_type: str
    message: str
    cause: Optional[str] = None
    attempted_solutions: Optional[list] = None
    next_steps: Optional[list] = None
    traceback: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

class ErrorReporter:
    """중앙화된 에러 리포터"""
    
    def __init__(self):
        self.error_log = []
        self.max_log_size = 100
        self.report_format = """
⚠️ 오류 발생!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📍 위치: {location}
💥 오류: {error_type} - {message}
🔍 원인: {cause}

🔄 시도한 해결책:
{attempted_solutions}

💡 다음 단계:
{next_steps}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        """
    
    def report(self, 
               error: Union[Exception, str],
               location: Optional[str] = None,
               cause: Optional[str] = None,