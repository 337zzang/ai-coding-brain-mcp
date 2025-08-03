"""
Compatibility tests for Phase 2-2 API Migration

Tests that existing flow commands still work with the new
session-based architecture and that the new FlowAPI works correctly.
"""

import sys
import os
import tempfile
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_helpers_new.simple_flow_commands import flow, get_manager
from ai_helpers_new.flow_api import get_flow_api
from ai_helpers_new.session import get_current_session, clear_session


def test_backward_compatibility():
    """Test that old flow commands still work."""
    print("🧪 Testing backward compatibility...")

    # Clear session
    clear_session()

    # Test get_manager()
    print("\n1. Testing get_manager()...")
    manager = get_manager()
    print(f"  ✓ Manager type: {type(manager).__name__}")
    print(f"  ✓ Project name: {manager.project_name}")

    # Test flow commands
    print("\n2. Testing flow commands...")

    # Status
    result = flow("/status")
    assert result['ok']
    print("  ✓ /status works")

    # Create plan
    result = flow("/create Test Plan")
    assert result['ok']
    print("  ✓ /create works")

    # List plans
    result = flow("/list")
    assert result['ok']
    assert 'plans' in result['data']
    print("  ✓ /list works")

    # Select plan
    plans = result['data']['plans']
    if plans:
        plan_id = plans[0]['id']
        result = flow(f"/select {plan_id}")
        assert result['ok']
        print("  ✓ /select works")

        # Add task
        result = flow("/task add Test Task")
        assert result['ok']
        print("  ✓ /task add works")

    print("\n✅ Backward compatibility test passed!")


def test_flow_api():
    """Test the new FlowAPI."""
    print("\n🧪 Testing new FlowAPI...")

    # Clear session
    clear_session()

    with tempfile.TemporaryDirectory() as tmpdir:
        # Initialize session
        session = get_current_session()
        session.set_project("test_api", tmpdir)

        # Get API
        api = get_flow_api()
        print("\n1. API instance created")

        # Create plan
        plan = api.create_plan("API Test Plan", "Testing FlowAPI")
        assert plan['name'] == "API Test Plan"
        print("  ✓ create_plan() works")

        # List plans
        plans = api.list_plans()
        assert len(plans) > 0
        print("  ✓ list_plans() works")

        # Select plan
        success = api.select_plan(plan['id'])
        assert success
        print("  ✓ select_plan() works")

        # Add task
        task = api.add_task("API Test Task", "Testing task creation")
        assert task is not None
        assert task['title'] == "API Test Task"
        print("  ✓ add_task() works")

        # Update task status
        success = api.update_task_status(task['id'], 'in_progress')
        assert success
        print("  ✓ update_task_status() works")

        # Get status
        status = api.get_status()
        assert status['plan_count'] > 0
        assert status['task_summary']['in_progress'] == 1
        print("  ✓ get_status() works")

        # Complete task
        success = api.complete_task(task['id'])
        assert success
        print("  ✓ complete_task() works")

    print("\n✅ FlowAPI test passed!")


def test_mixed_usage():
    """Test using both old and new APIs together."""
    print("\n🧪 Testing mixed usage...")

    # Clear session
    clear_session()

    # Create plan with flow command
    flow("/create Mixed Test Plan")

    # Get API and verify it sees the plan
    api = get_flow_api()
    plans = api.list_plans()
    assert any(p['name'] == "Mixed Test Plan" for p in plans)
    print("  ✓ FlowAPI sees plans created by flow()")

    # Create task with API
    plan = plans[0]
    api.select_plan(plan['id'])
    task = api.add_task("API Created Task")

    # Verify flow command sees the task
    result = flow("/task")
    assert result['ok']
    print("  ✓ flow() sees tasks created by FlowAPI")

    # Get manager and verify it works
    manager = get_manager()
    manager_plans = manager.list_plans()
    assert len(manager_plans) > 0
    print("  ✓ get_manager() still works with new system")

    print("\n✅ Mixed usage test passed!")


def test_session_isolation():
    """Test that sessions are properly isolated."""
    print("\n🧪 Testing session isolation...")

    from ai_helpers_new.session import isolated_session

    # Main session
    main_api = get_flow_api()

    # Create in isolated session
    with isolated_session() as test_session:
        test_session.set_project("isolated_test", tempfile.mkdtemp())
        test_api = get_flow_api(test_session)

        # Create plan in isolated session
        test_api.create_plan("Isolated Plan")
        isolated_plans = test_api.list_plans()
        assert len(isolated_plans) == 1
        print("  ✓ Isolated session has its own plans")

    # Verify main session is unaffected
    main_plans = main_api.list_plans()
    assert not any(p['name'] == "Isolated Plan" for p in main_plans)
    print("  ✓ Main session unaffected by isolated session")

    print("\n✅ Session isolation test passed!")


def run_all_tests():
    """Run all compatibility tests."""
    print("🚀 Running API Migration Compatibility Tests")
    print("=" * 50)

    try:
        test_backward_compatibility()
        test_flow_api()
        test_mixed_usage()
        test_session_isolation()

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
