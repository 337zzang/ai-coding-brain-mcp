"""
FlowManagerUnified 통합 테스트
"""
import os
import sys
from pathlib import Path

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from python.workflow_wrapper import wf

def print_result(name, result):
    """테스트 결과 출력"""
    status = "✅" if result.get('ok') else "❌"
    print(f"{status} {name}")
    if result.get('ok'):
        data = result.get('data')
        if isinstance(data, str):
            print(f"   → {data[:100]}..." if len(data) > 100 else f"   → {data}")
        elif isinstance(data, dict):
            print(f"   → {data}")
        elif isinstance(data, list):
            print(f"   → {len(data)} items")
    else:
        print(f"   ❌ {result.get('error')}")
    print()

def main():
    print("="*60)
    print("🧪 FlowManagerUnified 통합 테스트")
    print("="*60)

    # 1. 기본 명령어 테스트
    print("\n### 1. 기본 명령어 테스트")
    print_result("help", wf("/help"))
    print_result("status", wf("/status"))

    # 2. Flow 관리 테스트
    print("\n### 2. Flow 관리 테스트")
    print_result("flow create Test Project", wf("/flow create Test Project"))
    print_result("flow list", wf("/flow list"))
    print_result("flow status", wf("/flow"))

    # 3. Plan 관리 테스트
    print("\n### 3. Plan 관리 테스트")
    print_result("plan add Development", wf("/plan add Development"))
    print_result("plan add Testing", wf("/plan add Testing"))
    print_result("plan list", wf("/plan list"))

    # 4. Task 관리 테스트
    print("\n### 4. Task 관리 테스트")
    print_result("task add 코드 작성", wf("/task add 코드 작성"))
    print_result("task add 테스트 작성", wf("/task add 테스트 작성"))
    print_result("task add 문서화", wf("/task add 문서화"))
    print_result("list", wf("/list"))

    # 5. Task 상태 변경 테스트
    print("\n### 5. Task 상태 변경 테스트")
    # 태스크 목록에서 첫 번째 태스크 ID 가져오기
    tasks = wf("/list")
    if tasks['ok'] and isinstance(tasks['data'], list) and len(tasks['data']) > 0:
        first_task_id = tasks['data'][0]['id']
        print_result(f"start {first_task_id}", wf(f"/start {first_task_id}"))
        print_result(f"done {first_task_id}", wf(f"/done {first_task_id}"))

    # 6. Context 시스템 테스트 (활성화된 경우)
    print("\n### 6. Context 시스템 테스트")
    os.environ['CONTEXT_SYSTEM'] = 'on'
    print_result("context", wf("/context"))
    print_result("session save test", wf("/session save test"))
    print_result("stats", wf("/stats"))

    # 7. 전체 리포트
    print("\n### 7. 전체 리포트")
    print_result("report", wf("/report"))

    # 8. Flow 전환 테스트
    print("\n### 8. Flow 전환 테스트")
    print_result("flow create Another Project", wf("/flow create Another Project"))
    flows = wf("/flow list")
    if flows['ok'] and flows['data']:
        # 첫 번째 flow로 전환
        print("현재 flow 목록:")
        print(flows['data'])

    print("\n" + "="*60)
    print("✅ 통합 테스트 완료!")
    print("="*60)

if __name__ == "__main__":
    main()
