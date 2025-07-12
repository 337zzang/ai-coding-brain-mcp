"""
WorkflowEventAdapter 기본 테스트
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock

# 프로젝트 루트 추가
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

def test_import():
    """Import 테스트"""
    try:
        from python.workflow.v3.workflow_event_adapter import WorkflowEventAdapter
        from python.workflow.v3.events import WorkflowEvent, EventType
        assert True
    except ImportError as e:
        pytest.fail(f"Import 실패: {e}")

def test_adapter_creation():
    """어댑터 생성 테스트"""
    from python.workflow.v3.workflow_event_adapter import WorkflowEventAdapter

    # Mock WorkflowManager
    mock_manager = Mock()

    # 어댑터 생성
    adapter = WorkflowEventAdapter(mock_manager)
    assert adapter is not None
    assert adapter.workflow_manager == mock_manager

def test_event_bus_exists():
    """EventBus 존재 확인"""
    from python.workflow.v3.workflow_event_adapter import WorkflowEventAdapter

    mock_manager = Mock()
    adapter = WorkflowEventAdapter(mock_manager)

    assert hasattr(adapter, 'event_bus')
    assert adapter.event_bus is not None

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
