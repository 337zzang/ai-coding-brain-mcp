"""
Commands 모듈 테스트
"""
import pytest
from commands.flow import cmd_flow
from commands.task import cmd_task
from commands.plan import cmd_plan
from commands.next import cmd_next

def test_cmd_flow_without_project():
    """프로젝트 없이 flow 명령 실행"""
    result = cmd_flow(None)
    assert result is not None
    # 프로젝트 목록이 표시되어야 함

def test_cmd_task_list():
    """task list 명령 테스트"""
    result = cmd_task('list')
    assert result is not None

def test_cmd_plan_view():
    """plan 조회 테스트"""
    result = cmd_plan()
    assert result is not None

def test_cmd_next_no_tasks():
    """작업이 없을 때 next 명령"""
    result = cmd_next()
    # 작업이 없다는 메시지가 나와야 함
    assert result is not None
