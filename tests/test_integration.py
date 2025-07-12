"""
워크플로우 통합 테스트 스크립트
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from python.helpers_wrapper import create_helpers

print("🧪 워크플로우 통합 시스템 실제 테스트\n")

# helpers 생성
helpers = create_helpers()

# 1. 현재 워크플로우 상태 확인
print("1️⃣ 현재 워크플로우 상태:")
status = helpers.workflow("/status")
if status.ok:
    data = status.get_data({})
    print(f"  플랜: {data.get('plan_name', 'None')}")
    print(f"  진행률: {data.get('progress_percent', 0)}%")
    current_task = data.get('current_task')
    if current_task:
        print(f"  현재 태스크: {current_task.get('title', 'Unknown')}")

# 2. 테스트 태스크 실행
print("\n2️⃣ 태스크 진행 테스트:")

# 현재 태스크 시작
if current_task and current_task.get('status') == 'todo':
    print(f"  태스크 '{current_task['title']}' 시작...")
    focus_result = helpers.workflow("/focus")
    if focus_result.ok:
        print("  ✅ 태스크 시작됨")

# 3. 파일 생성 확인 (리스너 작동 확인)
print("\n3️⃣ 리스너 작동 확인:")

# task_context.json 확인
if os.path.exists("memory/task_context.json"):
    print("  ✅ task_context.json 파일 존재")
    import json
    with open("memory/task_context.json", 'r', encoding='utf-8') as f:
        context_data = json.load(f)
    print(f"  - 저장된 태스크 수: {len(context_data.get('tasks', {}))}")
else:
    print("  ❌ task_context.json 파일 없음")

# error_log.json 확인
if os.path.exists("memory/error_log.json"):
    print("  ✅ error_log.json 파일 존재")
else:
    print("  ℹ️ error_log.json 파일 없음 (오류 없음)")

# docs 디렉토리 확인
if os.path.exists("docs/tasks"):
    print("  ✅ docs/tasks 디렉토리 존재")
    task_docs = os.listdir("docs/tasks")
    if task_docs:
        print(f"  - 생성된 문서: {len(task_docs)}개")
else:
    print("  ❌ docs/tasks 디렉토리 없음")

# 4. 이벤트 로그 확인
print("\n4️⃣ 이벤트 발행 확인:")
workflow_data = helpers.read_json("memory/workflow.json").get_data({})
if workflow_data.get('events'):
    events = workflow_data['events'][-5:]  # 최근 5개
    print(f"  최근 이벤트 {len(events)}개:")
    for event in events:
        print(f"    - {event.get('type', 'unknown')} at {event.get('timestamp', 'unknown')[:19]}")
else:
    print("  ❌ 이벤트 로그 없음")

print("\n✅ 통합 테스트 완료!")
print("\n💡 다음 명령어로 태스크를 진행해보세요:")
print("  helpers.workflow('/next 작업 완료 메모')")
