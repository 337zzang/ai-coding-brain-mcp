#!/usr/bin/env python
"""
Workflow v2 Quick Start Script
"""
import sys
import os

# Add python directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'python'))

from workflow.v2 import WorkflowV2Manager, workflow_status, workflow_plan, workflow_task

def main():
    print("🚀 Workflow v2 Quick Start")
    print("="*50)

    # Create manager
    manager = WorkflowV2Manager("quickstart")

    # Check status
    status = manager.get_status()
    print(f"\n📊 Current Status: {status['status']}")

    if status['status'] == 'no_plan':
        # Create a new plan
        plan = manager.create_plan("Quick Start Plan", "Testing v2 system")
        print(f"✅ Created plan: {plan.name}")

        # Add some tasks
        tasks = [
            ("Learn v2 API", "Read the documentation"),
            ("Create first project", "Start using v2"),
            ("Migrate existing workflows", "Move from v1 to v2")
        ]

        for title, desc in tasks:
            task = manager.add_task(title, desc)
            print(f"  ✅ Added task: {title}")

    # Show final status
    final_status = manager.get_status()
    print(f"\n📈 Progress: {final_status['completed_tasks']}/{final_status['total_tasks']} tasks")
    print(f"📊 {final_status['progress_percent']:.1f}% complete")

    print("\n✨ Workflow v2 is ready to use!")

if __name__ == "__main__":
    main()
