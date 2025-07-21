"""
Integration tests for Flow Project v2 Phase 3
Tests complete Context System integration with FlowManager
"""

import unittest
import json
import os
import shutil
import time
from datetime import datetime
import tempfile
from pathlib import Path

# Add parent directory to path
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flow_manager_integrated import FlowManagerWithContext, create_flow_manager


class TestPhase3Integration(unittest.TestCase):
    """Test Phase 3 Context System Integration"""

    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.original_dir = os.getcwd()
        os.chdir(self.test_dir)

    def tearDown(self):
        """Clean up test environment"""
        os.chdir(self.original_dir)
        shutil.rmtree(self.test_dir)

    def test_flow_manager_creation(self):
        """Test FlowManager with Context creation"""
        flow = create_flow_manager()
        self.assertIsInstance(flow, FlowManagerWithContext)

        # Check components are initialized
        self.assertIsNotNone(flow.context_manager)
        self.assertIsNotNone(flow.session_manager)
        self.assertIsNotNone(flow.summarizer)

        flow.close()

    def test_plan_task_workflow(self):
        """Test complete plan and task workflow with context"""
        with create_flow_manager() as flow:
            # Create plan
            plan = flow.create_plan("Test Plan", "Testing context integration")
            self.assertIsNotNone(plan)
            self.assertEqual(plan["title"], "Test Plan")

            # Check context was updated
            context_plans = flow.context_manager.context["plans"]
            self.assertEqual(len(context_plans), 1)
            self.assertEqual(context_plans[0]["title"], "Test Plan")

            # Create tasks
            task1 = flow.create_task(plan["id"], "Task 1", "First task")
            task2 = flow.create_task(plan["id"], "Task 2", "Second task")

            # Check context was updated
            context_tasks = flow.context_manager.context["tasks"]
            self.assertEqual(len(context_tasks), 2)

            # Update task status
            flow.update_task_status(task1["id"], "in_progress")
            flow.update_task_status(task1["id"], "done")

            # Check summary
            summary = flow.context_manager.get_summary()
            self.assertEqual(summary["total_plans"], 1)
            self.assertEqual(summary["total_tasks"], 2)
            self.assertEqual(summary["completed_tasks"], 1)

    def test_summary_generation(self):
        """Test summary generation through FlowManager"""
        with create_flow_manager() as flow:
            # Create test data
            plan1 = flow.create_plan("Phase 3 Testing", "Test context system")
            plan2 = flow.create_plan("Phase 4 Planning", "Plan next phase")

            # Add tasks
            for i in range(3):
                flow.create_task(plan1["id"], f"Test Task {i+1}")

            for i in range(2):
                flow.create_task(plan2["id"], f"Planning Task {i+1}")

            # Update some tasks
            tasks = list(flow.tasks.values())
            flow.update_task_status(tasks[0]["id"], "done")
            flow.update_task_status(tasks[1]["id"], "in_progress")

            # Generate summaries
            brief_summary = flow.get_summary("brief")
            self.assertIn("2 plans", brief_summary)
            self.assertIn("5 tasks", brief_summary)

            detailed_summary = flow.get_summary("detailed")
            self.assertIn("Phase 3 Testing", detailed_summary)
            self.assertIn("Phase 4 Planning", detailed_summary)

            ai_summary = flow.get_summary("ai_optimized")
            self.assertIn("Current State", ai_summary)
            self.assertIn("Recommendations", ai_summary)

    def test_checkpoint_and_restore(self):
        """Test checkpoint creation and session restoration"""
        # Create initial state
        with create_flow_manager() as flow:
            plan = flow.create_plan("Checkpoint Test", "Test checkpoints")
            task = flow.create_task(plan["id"], "Task Before Checkpoint")
            flow.update_task_status(task["id"], "done")

            # Create checkpoint
            checkpoint = flow.save_checkpoint("before_changes")
            self.assertIsNotNone(checkpoint)

            # Make changes after checkpoint
            flow.create_task(plan["id"], "Task After Checkpoint")

            # Verify current state
            self.assertEqual(len(flow.tasks), 2)

        # Create new manager and restore checkpoint
        with create_flow_manager() as flow2:
            # First check current state (should be empty or from auto-save)
            sessions = flow2.list_sessions()

            # Find our checkpoint
            checkpoint_session = None
            for session in sessions:
                if "checkpoint_before_changes" in session["file"]:
                    checkpoint_session = session["file"]
                    break

            self.assertIsNotNone(checkpoint_session)

            # Restore checkpoint
            success = flow2.restore_session(checkpoint_session)
            self.assertTrue(success)

            # Verify restored state
            context = flow2.context_manager.context
            self.assertEqual(len(context["tasks"]), 1)  # Only task before checkpoint

    def test_auto_save_functionality(self):
        """Test auto-save works correctly"""
        with create_flow_manager() as flow:
            # Create some data
            plan = flow.create_plan("Auto-save Test")

            # Wait for auto-save (configured for shorter interval in tests)
            initial_sessions = flow.list_sessions()

            # Make changes and wait
            flow.create_task(plan["id"], "Test Task")
            time.sleep(2)  # Wait for potential auto-save

            # Note: Real auto-save testing would require longer waits
            # This just verifies the mechanism is set up
            self.assertIsNotNone(flow.session_manager._auto_save_thread)
            self.assertTrue(flow.session_manager._auto_save_thread.is_alive())

    def test_history_tracking(self):
        """Test history is properly tracked"""
        with create_flow_manager() as flow:
            # Perform various actions
            plan = flow.create_plan("History Test")
            task1 = flow.create_task(plan["id"], "Task 1")
            task2 = flow.create_task(plan["id"], "Task 2")

            flow.update_task_status(task1["id"], "in_progress")
            flow.update_task_status(task1["id"], "done")
            flow.complete_plan(plan["id"])

            # Check history
            history = flow.context_manager.context["history"]
            self.assertGreater(len(history), 5)  # Should have multiple entries

            # Verify history entries
            actions = [entry["action"] for entry in history]
            self.assertIn("created", actions)
            self.assertIn("status_changed", actions)
            self.assertIn("completed", actions)

            # Check targets
            targets = [entry["target"] for entry in history]
            self.assertIn("plan", targets)
            self.assertIn("task", targets)

    def test_statistics_accuracy(self):
        """Test statistics are calculated correctly"""
        with create_flow_manager() as flow:
            # Create structured test data
            plans = []
            for i in range(3):
                plan = flow.create_plan(f"Plan {i+1}")
                plans.append(plan)

                # Add different numbers of tasks to each plan
                for j in range(i + 2):  # 2, 3, 4 tasks respectively
                    task = flow.create_task(plan["id"], f"Task {i+1}-{j+1}")

                    # Complete some tasks
                    if j == 0:  # First task of each plan
                        flow.update_task_status(task["id"], "done")

            # Get summary statistics
            summary = flow.context_manager.get_summary()

            # Verify counts
            self.assertEqual(summary["total_plans"], 3)
            self.assertEqual(summary["total_tasks"], 9)  # 2+3+4
            self.assertEqual(summary["completed_tasks"], 3)  # First task of each plan
            self.assertAlmostEqual(summary["overall_progress"], 3/9, places=2)

            # Complete one plan
            flow.complete_plan(plans[0]["id"])
            summary = flow.context_manager.get_summary()
            self.assertEqual(summary["completed_plans"], 1)

    def test_error_handling(self):
        """Test error handling in integrated system"""
        with create_flow_manager() as flow:
            # Try to create task for non-existent plan
            task = flow.create_task("invalid_plan_id", "Orphan Task")
            self.assertIsNone(task)

            # Try to update non-existent task
            success = flow.update_task_status("invalid_task_id", "done")
            self.assertFalse(success)

            # Verify context remains consistent
            self.assertEqual(len(flow.context_manager.context["tasks"]), 0)
            self.assertEqual(len(flow.context_manager.context["plans"]), 0)

    def test_performance_with_many_items(self):
        """Test performance with larger dataset"""
        import time

        with create_flow_manager() as flow:
            start_time = time.time()

            # Create 10 plans with 10 tasks each
            for i in range(10):
                plan = flow.create_plan(f"Performance Plan {i+1}")
                for j in range(10):
                    task = flow.create_task(plan["id"], f"Task {i+1}-{j+1}")
                    if j % 3 == 0:
                        flow.update_task_status(task["id"], "done")

            # Generate summary
            summary = flow.get_summary("detailed")

            end_time = time.time()
            duration = end_time - start_time

            # Should complete in reasonable time
            self.assertLess(duration, 5.0)  # 5 seconds max

            # Verify data integrity
            self.assertEqual(len(flow.plans), 10)
            self.assertEqual(len(flow.tasks), 100)
            self.assertIn("100 tasks", summary)


def run_phase3_integration_tests():
    """Run all Phase 3 integration tests"""
    print("🧪 Running Phase 3 Integration Tests...")
    print("="*60)

    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPhase3Integration)

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n" + "="*60)
    if result.wasSuccessful():
        print("✅ All Phase 3 integration tests passed!")
        print(f"   Ran {result.testsRun} tests")
    else:
        print("❌ Some tests failed!")
        print(f"   Failures: {len(result.failures)}")
        print(f"   Errors: {len(result.errors)}")

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_phase3_integration_tests()
    sys.exit(0 if success else 1)
