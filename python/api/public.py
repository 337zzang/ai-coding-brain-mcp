#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Public API - AI Coding Brain MCP
외부에서 사용 가능한 공개 API

작성일: 2025-06-20
"""

from typing import Dict, Any, Optional
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.context_manager import get_context_manager

# ===========================================
# Public API
# ===========================================

def initialize_context(project_path: str, project_name: str = None, memory_root: str = None,
                      existing_context: Dict[str, Any] = None) -> Dict[str, Any]:
    """프로젝트 컨텍스트 초기화"""
    return get_context_manager().initialize(project_path, project_name, memory_root, existing_context)

def save_context() -> bool:
    """컨텍스트 저장"""
    return get_context_manager().save()

def update_cache(key: str, value: Any):
    """캐시 업데이트 (cache 키 없이 직접 접근)"""
    get_context_manager().update_cache(key, value)

def get_value(key: str, default: Any = None) -> Any:
    """값 조회 (cache 키 없이 직접 접근)"""
    return get_context_manager().get_value(key, default)

def track_file_access(file_path: str, operation: str = 'read'):
    """파일 접근 추적"""
    get_context_manager().track_file_access(file_path, operation)

def track_function_edit(file_path: str, function_name: str, class_name: Optional[str] = None):
    """함수 수정 추적"""
    get_context_manager().track_function_edit(file_path, function_name, class_name)

def get_work_tracking_summary() -> str:
    """작업 추적 요약"""
    return get_context_manager().get_work_tracking_summary()

def start_task_tracking(task_id: str):
    """Task 작업 추적 시작"""
    get_context_manager().start_task_tracking(task_id)

def track_task_operation(operation_type: str, details: dict = None):
    """현재 Task의 작업 추적"""
    get_context_manager().track_task_operation(operation_type, details)

def get_current_context() -> Optional[Dict[str, Any]]:
    """현재 context 반환 (auto_tracking_wrapper용)"""
    manager = get_context_manager()
    if manager and manager.context:
        # Pydantic 모델을 dict로 변환하여 반환
        return manager.context.dict()
    return None


# ===========================================
