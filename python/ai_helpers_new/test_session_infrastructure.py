"""
Tests for Session infrastructure
"""
import pytest
from ai_helpers_new.session import Session, get_current_session, clear_current_session, isolated_session
from ai_helpers_new.flow_context import FlowContext, ProjectContext


def test_session_creation():
    """Test session creation"""
    session = Session()
    assert session.session_id is not None
    assert session.project_context is None
    assert session.flow_manager is None


def test_get_current_session():
    """Test current session management"""
    clear_current_session()

    # First call creates session
    session1 = get_current_session()
    assert session1 is not None

    # Second call returns same session
    session2 = get_current_session()
    assert session1 is session2


def test_isolated_session():
    """Test isolated session context manager"""
    main_session = get_current_session()

    with isolated_session() as test_session:
        # Inside context, different session
        assert get_current_session() is test_session
        assert get_current_session() is not main_session

    # Outside context, back to main session
    assert get_current_session() is main_session


def test_flow_context():
    """Test FlowContext"""
    context = FlowContext()
    assert context.current_plan_id is None

    # Select plan
    context.select_plan("test_plan_123")
    assert context.current_plan_id == "test_plan_123"
    assert 'plan_selected_at' in context.metadata

    # Clear
    context.clear()
    assert context.current_plan_id is None
    assert len(context.metadata) == 0


if __name__ == "__main__":
    # Run basic tests
    test_session_creation()
    print("✅ Session creation test passed")

    test_get_current_session()
    print("✅ Current session test passed")

    test_isolated_session()
    print("✅ Isolated session test passed")

    test_flow_context()
    print("✅ FlowContext test passed")

    print("\nAll tests passed!")
