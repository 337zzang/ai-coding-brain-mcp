"""
Basic tests for Session infrastructure

Tests the new Session, Context, and Manager classes to ensure
they work correctly before integration.
"""

import sys
import os
from pathlib import Path
import tempfile
import shutil
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_helpers_new.session import (
    Session, get_current_session, set_session, 
    clear_session, isolated_session
)
from ai_helpers_new.flow_context import ProjectContext, FlowContext
from ai_helpers_new.contextual_flow_manager import ContextualFlowManager


def test_session_basics():
    """Test basic session functionality."""
    print("🧪 Testing Session basics...")

    # Create session
    session = Session()
    assert not session.is_initialized
    assert session.project_context is None
    assert session.flow_manager is None

    # Set project
    with tempfile.TemporaryDirectory() as tmpdir:
        project_ctx = session.set_project("test_project", tmpdir)
        assert session.is_initialized
        assert session.project_context is not None
        assert session.flow_manager is not None
        assert session.get_project_name() == "test_project"

        # Clear session
        session.clear()
        assert not session.is_initialized

    print("  ✅ Session basics work correctly")


def test_global_session():
    """Test global session management."""
    print("\n🧪 Testing global session management...")

    # Clear any existing session
    clear_session()

    # Get current session (should create new)
    session1 = get_current_session()
    session2 = get_current_session()
    assert session1 is session2  # Same instance

    # Set different session
    new_session = Session()
    old_session = set_session(new_session)
    assert old_session is session1
    assert get_current_session() is new_session

    # Clear session
    clear_session()
    session3 = get_current_session()
    assert session3 is not new_session  # New instance

    print("  ✅ Global session management works correctly")


def test_isolated_session():
    """Test isolated session for testing."""
    print("\n🧪 Testing isolated session...")

    # Set up a main session
    main_session = get_current_session()
    with tempfile.TemporaryDirectory() as tmpdir:
        main_session.set_project("main_project", tmpdir)

        # Use isolated session
        with isolated_session() as test_session:
            assert test_session is not main_session
            assert get_current_session() is test_session

            # Work in isolated session
            test_session.set_project("test_project", tmpdir)
            assert test_session.get_project_name() == "test_project"

        # Main session restored
        assert get_current_session() is main_session
        assert main_session.get_project_name() == "main_project"

    print("  ✅ Isolated session works correctly")


def test_project_context():
    """Test ProjectContext functionality."""
    print("\n🧪 Testing ProjectContext...")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create project context
        ctx = ProjectContext("test_project", Path(tmpdir))

        # Test path resolution
        resolved = ctx.resolve_path("subdir/file.txt")
        assert resolved.parent.name == "subdir"
        assert resolved.name == "file.txt"

        # Test directory creation
        subdir = ctx.ensure_directory("test_subdir")
        assert subdir.exists()
        assert subdir.is_dir()

        # Test metadata
        ctx.metadata["test_key"] = "test_value"
        ctx.save_metadata()

        # Create new context and load metadata
        ctx2 = ProjectContext("test_project", Path(tmpdir))
        assert ctx2.metadata.get("test_key") == "test_value"

    print("  ✅ ProjectContext works correctly")


def test_flow_context():
    """Test FlowContext functionality."""
    print("\n🧪 Testing FlowContext...")

    # Create flow context
    flow_ctx = FlowContext()
    assert flow_ctx.current_plan_id is None
    assert flow_ctx.current_task_id is None

    # Set plan
    flow_ctx.set_plan("plan_001", {"name": "Test Plan"})
    assert flow_ctx.current_plan_id == "plan_001"
    assert len(flow_ctx.history) == 1
    assert flow_ctx.history[0]["type"] == "plan_selected"

    # Set task
    flow_ctx.set_task("task_001", {"title": "Test Task"})
    assert flow_ctx.current_task_id == "task_001"
    assert len(flow_ctx.history) == 2

    # Clear
    flow_ctx.clear_plan()
    assert flow_ctx.current_plan_id is None
    assert flow_ctx.current_task_id is None

    print("  ✅ FlowContext works correctly")


def test_contextual_flow_manager():
    """Test ContextualFlowManager functionality."""
    print("\n🧪 Testing ContextualFlowManager...")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create project context and manager
        project_ctx = ProjectContext("test_project", Path(tmpdir))
        flow_path = project_ctx.resolve_path(".ai-brain/flow")
        manager = ContextualFlowManager(flow_path, project_ctx)

        # Create plan
        plan = manager.create_plan("Test Plan", "Test description")
        assert plan["name"] == "Test Plan"
        assert plan["status"] == "active"
        assert manager.flow_context.current_plan_id == plan["id"]

        # Add task
        task = manager.add_task("Test Task", "Do something")
        assert task is not None
        assert task["title"] == "Test Task"
        assert task["status"] == "todo"

        # Update task status
        success = manager.update_task_status(task["id"], "in_progress")
        assert success

        # List plans
        plans = manager.list_plans()
        assert len(plans) == 1
        assert plans[0]["id"] == plan["id"]

        # Get current plan
        current = manager.get_current_plan()
        assert current is not None
        assert current["id"] == plan["id"]

    print("  ✅ ContextualFlowManager works correctly")


def test_integration():
    """Test integrated workflow."""
    print("\n🧪 Testing integrated workflow...")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create session and set project
        session = Session()
        session.set_project("integration_test", tmpdir)

        # Work with flow manager
        manager = session.flow_manager
        assert manager is not None

        # Create plan through manager
        plan = manager.create_plan("Integration Plan")
        assert session.flow_context.current_plan_id == plan["id"]

        # Add tasks
        task1 = manager.add_task("Task 1")
        task2 = manager.add_task("Task 2")

        # Verify context state
        state = session.flow_context.get_state()
        assert state["current_plan_id"] == plan["id"]
        assert state["history_length"] > 0

    print("  ✅ Integration works correctly")


def run_all_tests():
    """Run all tests."""
    print("🚀 Running Session Infrastructure Tests")
    print("=" * 50)

    try:
        test_session_basics()
        test_global_session()
        test_isolated_session()
        test_project_context()
        test_flow_context()
        test_contextual_flow_manager()
        test_integration()

        print("\n✅ All tests passed!")
        return True

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
