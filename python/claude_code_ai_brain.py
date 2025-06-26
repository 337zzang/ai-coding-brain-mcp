#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
🧠 AI Coding Brain - Refactored Version v2.0
==========================================

리팩토링된 모듈 구조:
- core/: Context 관리, 설정
- commands/: 명령어 처리
- api/: Public API
- output/: 출력 처리

작성일: 2025-06-20
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from typing import Dict, Any, Optional

# Core imports
from core.context_manager import get_context_manager, UnifiedContextManager
from core.config import get_paths_from_config

# Command imports
from commands.enhanced_flow import flow_project as cmd_flow
from commands.plan import cmd_plan
from commands.task import cmd_task
from commands.next import cmd_next

# API imports
from api.public import (
    initialize_context, save_context, update_cache, get_value,
    track_file_access, track_function_edit, get_work_tracking_summary,
    start_task_tracking, track_task_operation, get_current_context
)

# Output imports
from output.handlers import ConsoleOutput, OutputHandler

# ===========================================
# 전역 컨텍스트 관리자 (하위 호환성)
# ===========================================
_context_manager = get_context_manager()

# ===========================================
# 명령어 처리 함수
# ===========================================

def process_command(command: str, existing_context: Dict[str, Any] = None) -> Any:
    """명령어 처리"""
    parts = command.strip().split()
    if not parts:
        return None
    
    cmd = parts[0].lower()
    args = parts[1:] if len(parts) > 1 else []
    
    if cmd == '/flow':
        project_name = args[0] if args else None
        return cmd_flow(project_name, existing_context)
    
    elif cmd == '/plan':
        if len(args) == 0:
            return cmd_plan()
        elif len(args) == 1:
            return cmd_plan(args[0])
        else:
            return cmd_plan(args[0], ' '.join(args[1:]))
    
    elif cmd == '/task':
        if not args:
            print("사용법: /task add|edit|done|list [인자...]")
            return None
        return cmd_task(args[0], *args[1:])
    
    elif cmd == '/next':
        return cmd_next()
    
    elif cmd == '/save':
        return save_context()
    
    else:
        print(f"알 수 없는 명령어: {cmd}")
        print("사용 가능한 명령어: /flow, /plan, /task, /next, /save")
        return None

# ===========================================
# 메인 진입점
# ===========================================

if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = ' '.join(sys.argv[1:])
        process_command(command)
    else:
        print("AI Coding Brain v2.0 (Refactored)")
        print("사용법: python claude_code_ai_brain_v2.py [명령어]")
        print("명령어: /flow, /plan, /task, /next, /save")
