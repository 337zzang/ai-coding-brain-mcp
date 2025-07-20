#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
🚀 JSON REPL Session for AI Coding Brain v6.0
==============================================

이 파일은 AI Coding Brain의 핵심 REPL 세션 관리자입니다.
JSON 기반 통신을 통해 Python 코드를 안전하게 실행하고 결과를 반환합니다.

주요 기능:
- JSON REPL 세션 관리
- 안전한 코드 실행 (샌드박스)
- AI 헬퍼 함수 통합
- 워크플로우 시스템 연동
"""

# ============================================================================
# 🔧 Import 섹션
# ============================================================================

# 안전한 실행 헬퍼 (구문 검사 포함)
try:
    from safe_exec_helpers import enhanced_safe_exec, quick_syntax_check
    SAFE_EXEC_AVAILABLE = True
except ImportError:
    enhanced_safe_exec = None
    quick_syntax_check = None
    SAFE_EXEC_AVAILABLE = False

import sys
import os

# Windows에서 UTF-8 출력 강제 설정
if sys.platform == 'win32':
    import locale
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
    os.environ['PYTHONIOENCODING'] = 'utf-8'

import json
import tempfile
import io
import traceback
import time
import datetime as dt
import platform
import subprocess
import builtins
from pathlib import Path
from typing import Dict, Any, Optional
from contextlib import contextmanager

# 기본 경로 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# JSON 유틸리티 (safe_json_write 포함)
from json_utils import safe_json_write

# Enhanced Safe Execution v2 - f-string 및 정규식 안전성 검사
try:
    from safe_execution_v2 import (
        safe_exec as safe_exec_v2,
        check_regex,
        benchmark_regex_safety
    )
    SAFE_EXEC_V2_AVAILABLE = True
except ImportError:
    SAFE_EXEC_V2_AVAILABLE = False

# AI Helpers v2 통합
try:
    from ai_helpers_v2 import (
        # File operations
        read_file, write_file, create_file, file_exists, append_to_file,
        read_json, write_json,
        # Search operations
        search_code, search_files, grep, find_function, find_class,
        # Code operations
        parse_with_snippets, insert_block, replace_block,
        # Git operations
        git_status, git_add, git_commit, git_branch, git_push, git_pull,
        # Project operations
        get_current_project, scan_directory_dict, create_project_structure,
        # Core operations
        get_metrics, clear_cache, get_execution_history
    )
    AI_HELPERS_V2_LOADED = True
    print("✅ AI Helpers v2 로드 성공")
except ImportError as e:
    print(f"⚠️ AI Helpers v2 로드 실패: {e}")
    AI_HELPERS_V2_LOADED = False

# 실행 설정
CONFIG = {
    'use_safe_exec_v2': True,      # Enhanced Safe Execution v2 사용
    'fstring_check': True,         # f-string 미정의 변수 검사
    'regex_check': True,           # 정규식 안전성 검사
    'redos_protection': True,      # ReDoS 패턴 경고
    'show_warnings': True,         # 경고 메시지 표시
}

# ============================================================================
# 🌟 전역 변수 초기화
# ============================================================================

repl_globals = {}  # REPL 전역 네임스페이스
execution_count = 0  # 실행 카운터
