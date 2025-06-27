"""
import sys
import os
# Python 경로 설정
python_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if python_path not in sys.path:
    sys.path.insert(0, python_path)

Wisdom Auto Fixer - 자동 코드 수정 시스템
코드를 분석하고 자동으로 수정하는 고급 기능 제공
"""

import ast
from typing import Tuple, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime

from core.wisdom_plugin_base import Detection, PluginManager
from .wisdom_factory import get_wisdom_manager

@dataclass
class FixResult:
    """수정 결과 정보"""
    original_code: str
    fixed_code: str
    detections: List[Detection]
    applied_fixes: List[str]
    skipped_fixes: List[str]
    success: bool
    error_message: str = None
    fix_time: datetime = None
    
    def __post_init__(self):
        if self.fix_time is None:
            self