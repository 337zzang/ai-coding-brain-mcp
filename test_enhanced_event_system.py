"""
Enhanced Event System Test
미사용 이벤트 타입 활성화 테스트
"""

import asyncio
import time
from python.workflow.v3.event_bus import event_bus
from python.workflow.v3.event_types import EventType
from python.workflow.v3.manager import WorkflowManager
from python.workflow.v3.dispatcher import execute_workflow_command


def setup_event_handlers():
    """이벤트 핸들러 설정"""
    
    def on_task_failed(event):
        print(f"🔴 TASK_FAILED: {event.payload.get('task_title')} - {event.payload.get('error')}")
    
    def on_task_blocked(event):
        print(f"🚧 TASK_BLOCKED: {event.payload.get('task_title')} - {event.payload.get('blocker')}")
    
    def on_task_unblocked(event):
        print(f"✅ TASK_UNBLOCKED: {event.payload.get('task_title')}")
    
    def on_task_cancelled(event):
        print(f"❌ TASK_CANCELLED: {event.payload.get('task_title')} - {event.payload.get('reason', 'No reason')}")
    
    def on_any_event(event):
        print(f"📢 Event: {event.type} at {event.timestamp}")
    
    # 핸들러 등록
    event_bus.subscribe(EventType.TASK_FAILED.value, on_task_failed)
    event_bus.subscribe(EventType.TASK_BLOCKED.value, on_task_blocked)
    event_bus.subscribe(EventType.TASK_UNBLOCKED.value, on_task_unblocked)
    event_bus.subscribe(EventType.TASK_CANCELLED.value, on_task_cancelled)
    
    # 모든 이벤트 타입에 대한 핸들러
    for event_type in EventType:
        event_bus.subscribe(event_type.value, on_any_event)


def test_event_system():
    """이벤트 시스템 테스트"""
    print("=== Enhanced Event System Test ===\n")
    
    # 이벤트 핸들러 설정
    setup_event_handlers()
    
    # 테스트용 프로젝트로 전환
    print("1. 프로젝트 초기화")
    manager = WorkflowManager.get_instance("event_test_project")
    
    # 새 플랜 생성
    print("\n2. 테스트 플랜 생성")
    plan = manager.start_plan("이벤트 테스트 플랜", "미사용 이벤트 활성화 테스트")
    print(f"   ✅ 플랜 생성: {plan.name}")
    
    # 태스크 추가
    print("\n3. 테스트 태스크 추가")
    task1 = manager.add_task("정상 태스크", "정상적으로 완료될 태스크")
    task2 = manager.add_task("실패할 태스크", "오류가 발생할 태스크")
    task3 = manager.add_task("차단될 태스크", "의존성으로 차단될 태스크")
    task4 = manager.add_task("취소될 태스크", "요구사항 변경으로 취소될 태스크")
    
    print(f"   ✅ 태스크 4개 추가 완료")
    
    # 잠시 대기 (이벤트 처리)
    time.sleep(0.5)
    
    # 태스크 상태 변경 테스트
    print("\n4. 태스크 상태 변경 테스트")
    
    # 정상 완료
    print("\n   a) 정상 태스크 완료")
    manager.complete_task(task1.id, "정상적으로 완료됨")
    time.sleep(0.1)
    
    # 실패 처리
    print("\n   b) 태스크 실패 처리")
    manager.fail_task(task2.id, "데이터베이스 연결 오류")
    time.sleep(0.1)
    
    # 차단 처리
    print("\n   c) 태스크 차단")
    manager.block_task(task3.id, "외부 API 응답 대기 중")
    time.sleep(0.1)
    
    # 차단 해제
    print("\n   d) 태스크 차단 해제")
    manager.unblock_task(task3.id)
    time.sleep(0.1)
    
    # 취소 처리
    print("\n   e) 태스크 취소")
    manager.cancel_task(task4.id, "요구사항 변경으로 불필요")
    time.sleep(0.1)
    
    # 통계 출력
    print("\n5. 이벤트 처리 통계")
    stats = event_bus.get_stats()
    print(f"   - 발행된 이벤트: {stats['published']}")
    print(f"   - 처리된 이벤트: {stats['processed']}")
    print(f"   - 실패한 이벤트: {stats['failed']}")
    
    # 핸들러 수 확인
    handlers = event_bus.get_handlers_count()
    print(f"\n6. 등록된 핸들러")
    for event_type, count in handlers.items():
        print(f"   - {event_type}: {count}개")
    
    # 현재 태스크 상태 확인
    print("\n7. 최종 태스크 상태")
    tasks = manager.get_tasks()
    for task in tasks:
        status_icon = {
            'completed': '✅',
            'cancelled': '❌',
            'todo': '⏳',
            'in_progress': '🔄'
        }.get(task['status'], '❓')
        print(f"   {status_icon} {task['title']} - {task['status']}")


if __name__ == "__main__":
    test_event_system()
