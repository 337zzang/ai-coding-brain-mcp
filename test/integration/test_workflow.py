"""
통합 테스트 - 전체 워크플로우
"""
import pytest
import os
from api.public import initialize_context, save_context, update_cache
from commands.flow import cmd_flow
from commands.plan import cmd_plan
from commands.task import cmd_task

def test_full_workflow(temp_project_dir):
    """전체 워크플로우 테스트"""
    # 1. 프로젝트 초기화
    context = initialize_context(str(temp_project_dir))
    assert context is not None
    
    # 2. 계획 수립
    result = cmd_plan("테스트 계획", "통합 테스트를 위한 계획")
    assert result is not None
    
    # 3. 작업 추가
    cmd_task('add', 'phase-1', '첫 번째 작업')
    cmd_task('add', 'phase-1', '두 번째 작업')
    
    # 4. 작업 목록 확인
    tasks = cmd_task('list')
    assert tasks is not None
    
    # 5. 컨텍스트 저장
    save_result = save_context()
    assert save_result is not None
