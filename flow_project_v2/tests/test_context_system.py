"""
Unit tests for Flow Project v2 Context System
Tests ContextManager, SessionManager, and ContextSummarizer
"""

import unittest
import json
import os
import shutil
import time
from datetime import datetime, timedelta
from pathlib import Path
import tempfile

# Add parent directory to path for imports
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from context import ContextManager, SessionManager, ContextSummarizer


class TestContextManager(unittest.TestCase):
    """Test ContextManager functionality"""

    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.context_manager = ContextManager(self.test_dir)

    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_dir)

    def test_context_creation(self):
        """Test context creation"""
        context = self.context_manager.context

        self.assertIsInstance(context, dict)
        self.assertIn("session", context)
        self.assertIn("plans", context)
        self.assertIn("tasks", context)
        self.assertIn("history", context)
        self.assertIn("summary", context)
        self.assertIn("metadata", context)

        # Check session fields
        self.assertIsNotNone(context["session"]["session_id"])
        self.assertEqual(context["session"]["status"], "active")

    def test_save_and_load(self):
        """Test saving and loading context"""
        # Add some data
        self.context_manager.add_history_entry("test", "unit", "test_1", {"data": "test"})

        # Save
        success = self.context_manager.save()
        self.assertTrue(success)

        # Check file exists
        context_file = Path(self.test_dir) / "current_context.json"
        self.assertTrue(context_file.exists())

        # Create new manager and check data persists
        new_manager = ContextManager(self.test_dir)
        self.assertEqual(len(new_manager.context["history"]), 1)
        self.assertEqual(new_manager.context["history"][0]["action"], "test")

    def test_plan_context_update(self):
        """Test plan context updates"""
        plan_data = {
            "title": "Test Plan",
            "status": "active",
            "tasks": ["task1", "task2"]
        }

        self.context_manager.update_plan_context("plan_1", plan_data)

        # Check plan was added
        self.assertEqual(len(self.context_manager.context["plans"]), 1)
        plan_entry = self.context_manager.context["plans"][0]
        self.assertEqual(plan_entry["plan_id"], "plan_1")
        self.assertEqual(plan_entry["title"], "Test Plan")
        self.assertEqual(plan_entry["task_count"], 2)

        # Check history
        self.assertEqual(len(self.context_manager.context["history"]), 1)

    def test_task_context_update(self):
        """Test task context updates"""
        task_data = {
            "plan_id": "plan_1",
            "title": "Test Task",
            "status": "todo"
        }

        self.context_manager.update_task_context("task_1", task_data)

        # Update to in_progress
        task_data["status"] = "in_progress"
        self.context_manager.update_task_context("task_1", task_data)

        # Check task was updated
        task_entry = self.context_manager.context["tasks"][0]
        self.assertEqual(task_entry["status"], "in_progress")
        self.assertIsNotNone(task_entry["started_at"])

        # Update to done
        task_data["status"] = "done"
        self.context_manager.update_task_context("task_1", task_data)

        # Check completion
        task_entry = self.context_manager.context["tasks"][0]
        self.assertEqual(task_entry["status"], "done")
        self.assertIsNotNone(task_entry["completed_at"])
        self.assertIsNotNone(task_entry["duration"])

    def test_summary_generation(self):
        """Test summary generation"""
        # Add some data
        self.context_manager.update_plan_context("plan_1", {
            "title": "Test Plan",
            "status": "active",
            "tasks": ["task1"]
        })

        self.context_manager.update_task_context("task_1", {
            "plan_id": "plan_1",
            "title": "Test Task",
            "status": "done"
        })

        summary = self.context_manager.get_summary()

        self.assertEqual(summary["total_plans"], 1)
        self.assertEqual(summary["total_tasks"], 1)
        self.assertEqual(summary["completed_tasks"], 1)
        self.assertEqual(summary["overall_progress"], 1.0)
        self.assertIn("Completed 1 tasks", summary["key_achievements"])


class TestSessionManager(unittest.TestCase):
    """Test SessionManager functionality"""

    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.context_manager = ContextManager(self.test_dir)
        self.session_manager = SessionManager(self.context_manager, auto_save_interval=1)

    def tearDown(self):
        """Clean up test environment"""
        self.session_manager.stop_auto_save()
        shutil.rmtree(self.test_dir)

    def test_manual_save(self):
        """Test manual session save"""
        # Add some data
        self.context_manager.add_history_entry("test", "unit", "test_1", {})

        # Save session
        saved_path = self.session_manager.save_session("manual")
        self.assertIsNotNone(saved_path)
        self.assertTrue(os.path.exists(saved_path))

        # Check it's in the sessions directory
        self.assertIn("sessions", saved_path)
        self.assertIn("manual", saved_path)

    def test_auto_save(self):
        """Test auto-save functionality"""
        # Start auto-save with 1 second interval
        self.session_manager.start_auto_save()

        # Wait for auto-save
        time.sleep(2)

        # Check for auto-save files
        sessions = self.session_manager.list_sessions()
        auto_saves = [s for s in sessions if s["type"] == "auto"]
        self.assertGreater(len(auto_saves), 0)

    def test_session_restore(self):
        """Test session restoration"""
        # Add data and save
        self.context_manager.add_history_entry("test", "unit", "test_1", {"data": "original"})
        saved_path = self.session_manager.save_session("manual")

        # Modify context
        self.context_manager.context["history"] = []
        self.context_manager.add_history_entry("test", "unit", "test_2", {"data": "modified"})

        # Restore
        success = self.session_manager.restore_session(saved_path)
        self.assertTrue(success)

        # Check original data is restored
        self.assertEqual(len(self.context_manager.context["history"]), 1)
        self.assertEqual(self.context_manager.context["history"][0]["target_id"], "test_1")

    def test_checkpoint_creation(self):
        """Test checkpoint creation"""
        checkpoint = self.session_manager.create_checkpoint("test_checkpoint")
        self.assertIsNotNone(checkpoint)
        self.assertIn("checkpoint_test_checkpoint", checkpoint)
        self.assertTrue(os.path.exists(checkpoint))

    def test_session_listing(self):
        """Test session listing"""
        # Create multiple sessions
        self.session_manager.save_session("manual")
        time.sleep(0.1)
        self.session_manager.save_session("auto")
        time.sleep(0.1)
        self.session_manager.create_checkpoint("test")

        # List sessions
        sessions = self.session_manager.list_sessions()
        self.assertGreaterEqual(len(sessions), 3)

        # Check session info
        for session in sessions:
            self.assertIn("file", session)
            self.assertIn("type", session)
            self.assertIn("size", session)


class TestContextSummarizer(unittest.TestCase):
    """Test ContextSummarizer functionality"""

    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.context_manager = ContextManager(self.test_dir)
        self.summarizer = ContextSummarizer(self.context_manager)

        # Add test data
        self._add_test_data()

    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_dir)

    def _add_test_data(self):
        """Add test data to context"""
        # Add plans
        for i in range(3):
            self.context_manager.update_plan_context(f"plan_{i}", {
                "title": f"Test Plan {i}",
                "status": "active" if i < 2 else "completed",
                "tasks": [f"task_{i}_0", f"task_{i}_1"]
            })

        # Add tasks
        task_count = 0
        for i in range(3):
            for j in range(2):
                status = ["done", "in_progress", "todo"][task_count % 3]
                self.context_manager.update_task_context(f"task_{i}_{j}", {
                    "plan_id": f"plan_{i}",
                    "title": f"Task {i}-{j}",
                    "status": status
                })
                task_count += 1

    def test_brief_summary(self):
        """Test brief summary generation"""
        summary = self.summarizer.generate_summary("brief")

        self.assertIsInstance(summary, str)
        self.assertIn("Flow Project v2 session active", summary)
        self.assertIn("3 plans", summary)
        self.assertIn("6 tasks", summary)
        self.assertLess(len(summary), 500)  # Should be brief

    def test_detailed_summary(self):
        """Test detailed summary generation"""
        summary = self.summarizer.generate_summary("detailed")

        self.assertIsInstance(summary, str)
        self.assertIn("## 📊 Flow Project v2 - Detailed Summary", summary)
        self.assertIn("### 📈 Progress Overview", summary)
        self.assertIn("### 🎯 Active Plans", summary)
        self.assertGreater(len(summary), 500)  # Should be detailed

    def test_ai_optimized_summary(self):
        """Test AI-optimized summary generation"""
        summary = self.summarizer.generate_summary("ai_optimized")

        self.assertIsInstance(summary, str)
        self.assertIn("## AI-Optimized Context Summary", summary)
        self.assertIn("### Current State", summary)
        self.assertIn("### Recent Actions", summary)
        self.assertIn("### AI Recommendations", summary)

    def test_statistics_calculation(self):
        """Test statistics calculation"""
        stats = self.summarizer._calculate_statistics()

        self.assertIn("Average tasks per plan", stats)
        self.assertIn("Current velocity", stats)
        self.assertIn("Most active hour", stats)

    def test_recommendations_generation(self):
        """Test recommendations generation"""
        recommendations = self.summarizer._generate_recommendations()

        self.assertIsInstance(recommendations, list)
        self.assertLessEqual(len(recommendations), 3)

        # Should have at least one recommendation with tasks
        self.assertGreater(len(recommendations), 0)


class TestIntegration(unittest.TestCase):
    """Test integration between components"""

    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_dir)

    def test_full_workflow(self):
        """Test complete workflow with all components"""
        # Create managers
        context_mgr = ContextManager(self.test_dir)
        session_mgr = SessionManager(context_mgr)
        summarizer = ContextSummarizer(context_mgr)

        # Start auto-save
        session_mgr.start_auto_save()

        # Create plan and tasks
        context_mgr.update_plan_context("plan_1", {
            "title": "Integration Test Plan",
            "status": "active",
            "tasks": []
        })

        # Add tasks
        for i in range(3):
            context_mgr.update_task_context(f"task_{i}", {
                "plan_id": "plan_1",
                "title": f"Integration Task {i}",
                "status": "todo"
            })

        # Update task statuses
        context_mgr.update_task_context("task_0", {"status": "done"})
        context_mgr.update_task_context("task_1", {"status": "in_progress"})

        # Create checkpoint
        checkpoint = session_mgr.create_checkpoint("integration_test")
        self.assertIsNotNone(checkpoint)

        # Generate summaries
        brief = summarizer.generate_summary("brief")
        detailed = summarizer.generate_summary("detailed")
        ai_summary = summarizer.generate_summary("ai_optimized")

        # Verify summaries contain expected content
        for summary in [brief, detailed, ai_summary]:
            self.assertIn("1", summary)  # 1 plan
            self.assertIn("3", summary)  # 3 tasks

        # Stop auto-save
        session_mgr.stop_auto_save()

        # Final save
        final_save = session_mgr.save_session("final")
        self.assertIsNotNone(final_save)


if __name__ == "__main__":
    unittest.main(verbosity=2)
