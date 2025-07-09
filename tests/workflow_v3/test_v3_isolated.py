"""
워크플로우 V3 격리 테스트
v2 의존성 없이 순수 v3 테스트
"""
import sys
from pathlib import Path

# 프로젝트 루트 추가
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from python.workflow.v3.manager import WorkflowManager
from python.workflow.v3.parser import CommandParser
from python.workflow.v3.storage import FileStorage


def test_v3_isolated():
    """v3 격리 테스트"""
    print("=== V3 격리 테스트 시작 ===\n")
    
    # V3 전용 저장소
    storage_path = Path("memory/workflow_v3")
    storage = FileStorage(str(storage_path))
    manager = WorkflowManager(storage=storage)
    parser = CommandParser()
    
    def execute(cmd):
        """명령 실행 헬퍼"""
        parsed = parser.parse(cmd)
        return manager.execute(parsed)
    
    # 1. 초기 상태
    print("1. 초기 상태 확인")
    result = execute("/status")
    print(f"   상태: {result.get('status', 'unknown')}")
    print(f"   플랜: {result.get('plan_name', 'None')}\n")
    
    # 2. 새 플랜 생성
    print("2. 새 플랜 생성")
    result = execute("/start V3 격리 테스트 플랜 | 순수 V3 테스트")
    if result['success']:
        print(f"   ✅ 플랜 생성: {result['plan']['name']}")
        print(f"   ID: {result['plan']['id']}\n")
    
    # 3. 태스크 추가
    print("3. 태스크 추가")
    tasks = ["첫 번째 태스크", "두 번째 태스크", "세 번째 태스크"]
    for task in tasks:
        result = execute(f"/task {task}")
        if result['success']:
            print(f"   ✅ {task}")
    
    # 4. 상태 재확인
    print("\n4. 상태 재확인")
    result = execute("/status")
    print(f"   총 태스크: {result.get('total_tasks', 0)}")
    print(f"   완료된 태스크: {result.get('completed_tasks', 0)}")
    print(f"   진행률: {result.get('progress_percent', 0)}%")
    
    # 5. 태스크 진행
    print("\n5. 태스크 진행")
    # 첫 번째 태스크 포커스
    result = execute("/focus 1")
    if result['success']:
        print(f"   ✅ 포커스: {result['task']['title']}")
    
    # 태스크 완료
    result = execute("/next 첫 번째 완료!")
    if result['success']:
        print(f"   ✅ 완료: {result.get('completed_task', {}).get('title', 'N/A')}")
        if result.get('next_task'):
            print(f"   → 다음: {result['next_task']['title']}")
    
    # 6. 히스토리 확인
    print("\n6. 이벤트 히스토리")
    result = execute("/status history")
    if result['success']:
        events = result.get('history', [])
        print(f"   총 이벤트: {len(events)}")
        for event in events[-5:]:  # 최근 5개
            print(f"   - {event['type']}: {event.get('details', {}).get('title', event.get('details', {}).get('name', 'N/A'))}")
    
    # 7. 빌드 테스트
    print("\n7. 문서 빌드")
    result = execute("/build")
    if result['success']:
        print("   ✅ 빌드 성공")
        print(f"   내용 길이: {len(result.get('content', ''))} 문자")
    
    print("\n=== V3 격리 테스트 완료 ===")


if __name__ == '__main__':
    test_v3_isolated()
