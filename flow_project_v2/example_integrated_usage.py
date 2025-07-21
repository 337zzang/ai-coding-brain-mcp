"""
Example usage of FlowManager with Context integration
"""

from flow_project_v2.flow_manager_integrated import create_flow_manager

def main():
    # Create flow manager (auto-starts context tracking)
    with create_flow_manager() as flow:
        # Create a plan
        plan = flow.create_plan("Phase 3 Implementation", "Implement Context System")
        print(f"Created plan: {plan['id']}")

        # Add tasks
        task1 = flow.create_task(plan['id'], "Design context schema", "Define JSON structure")
        task2 = flow.create_task(plan['id'], "Implement ContextManager", "Core context logic")
        task3 = flow.create_task(plan['id'], "Add auto-save", "5-minute interval saves")

        # Update task status
        flow.update_task_status(task1['id'], "in_progress")
        flow.update_task_status(task1['id'], "done")

        # Get summary
        print("\n" + "="*60)
        print(flow.get_summary("brief"))
        print("="*60)

        # Create checkpoint
        checkpoint = flow.save_checkpoint("phase3_progress")
        print(f"\nCheckpoint saved: {checkpoint}")

        # List sessions
        sessions = flow.list_sessions()
        print(f"\nAvailable sessions: {len(sessions)}")

    # Auto-saves and closes on exit


if __name__ == "__main__":
    main()
