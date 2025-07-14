
# 통합 시스템 초기화
import sys
sys.path.append('./python')

from ai_helpers.workflow.workflow_adapter import WorkflowAdapter

# 전역 어댑터 초기화
if 'workflow_adapter' not in globals():
    workflow_adapter = WorkflowAdapter()
    print("✅ 워크플로우 어댑터 초기화 완료")

# 현재 프로젝트로 전환
current_project = 'ai-coding-brain-mcp'
result = workflow_adapter.flow_project(current_project)

if result.get('success'):
    print(f"✅ 프로젝트 '{current_project}'로 전환 완료")

    # 현재 상태 출력
    status = workflow_adapter.get_workflow_status()
    print(f"\n📊 통합 시스템 상태:")
    print(f"  - 워크플로우 ID: {status['workflow'].get('plan_id', 'None')}")
    print(f"  - 완료 작업: {status['workflow'].get('completed_tasks', 0)}")
    print(f"  - 세션 ID: {status['shared_data']['session_id']}")
