"""
Real-world Scenario Tests
실제 사용 시나리오를 기반으로 한 통합 테스트
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'python'))

from workflow.workflow_manager import WorkflowManager
from workflow.models import Task, TaskStatus
from events.event_integration_adapter import integrate_all
from events.event_bus import get_event_bus
from events.workflow_context_bridge import get_workflow_context_bridge
import time


def test_real_development_workflow():
    """실제 개발 워크플로우 시나리오 테스트"""
    print("\n=== 실제 개발 워크플로우 시나리오 ===")
    print("시나리오: 새 기능 개발 프로세스\n")

    # 시스템 통합
    adapter = integrate_all()
    bus = get_event_bus()
    bridge = get_workflow_context_bridge()

    # 이벤트 로깅
    events_log = []

    def log_event(event):
        events_log.append(f"[{event.type}] {event.data.get('task_title', event.data.get('plan_name', 'N/A'))}")
        print(f"  📢 이벤트: {events_log[-1]}")

    # 모든 이벤트 구독
    from events.event_types import EventTypes
    for attr in dir(EventTypes):
        if not attr.startswith('_'):
            event_type = getattr(EventTypes, attr)
            if isinstance(event_type, str):
                bus.subscribe(event_type, log_event)

    # 1. 새 기능 개발 계획 생성
    print("1️⃣ 새 기능 개발 계획 생성")
    wf_manager = WorkflowManager()
    adapter.integrate_workflow_manager(wf_manager)

    plan = wf_manager.create_plan(
        "사용자 인증 시스템 개발",
        "JWT 기반 인증 시스템 구현"
    )

    # 2. 개발 태스크 추가
    print("\n2️⃣ 개발 태스크 추가")
    tasks = [
        Task(title="요구사항 분석", description="인증 시스템 요구사항 정의"),
        Task(title="DB 스키마 설계", description="사용자 테이블 및 토큰 저장소 설계"),
        Task(title="API 엔드포인트 구현", description="로그인/로그아웃/토큰 갱신 API"),
        Task(title="테스트 작성", description="단위 테스트 및 통합 테스트"),
        Task(title="문서화", description="API 문서 및 사용 가이드 작성")
    ]

    for task in tasks:
        plan.tasks.append(task)
        print(f"  ✓ 태스크 추가: {task.title}")

    wf_manager.save_data()

    # 3. 태스크 순차 실행
    print("\n3️⃣ 태스크 순차 실행")

    for i, task in enumerate(plan.tasks):
        print(f"\n--- 태스크 {i+1}/{len(plan.tasks)}: {task.title} ---")

        # 태스크 시작
        task.status = TaskStatus.IN_PROGRESS
        task.started_at = time.strftime("%Y-%m-%dT%H:%M:%S")

        from events.event_types import create_task_started_event
        start_event = create_task_started_event(task.id, task.title)
        bus.publish(start_event)

        # 파일 작업 시뮬레이션
        if "구현" in task.title or "설계" in task.title:
            from events.event_types import FileEvent, EventTypes

            files = {
                "DB 스키마 설계": ["models/user.py", "models/token.py"],
                "API 엔드포인트 구현": ["api/auth.py", "api/middleware.py"]
            }

            if task.title in files:
                for file_path in files[task.title]:
                    file_event = FileEvent(
                        EventTypes.FILE_CREATED,
                        file_path=file_path,
                        operation="create"
                    )
                    bus.publish(file_event)
                    print(f"  📁 파일 생성: {file_path}")

        # 태스크 완료
        time.sleep(0.1)  # 시뮬레이션을 위한 짧은 대기

        task.status = TaskStatus.COMPLETED
        task.completed_at = time.strftime("%Y-%m-%dT%H:%M:%S")

        from events.event_types import create_task_completed_event
        complete_event = create_task_completed_event(
            task.id, 
            task.title,
            f"{task.title} 성공적으로 완료"
        )
        bus.publish(complete_event)

        # 진행률 확인
        progress = plan.get_progress()
        print(f"  📊 진행률: {progress['percentage']:.1f}%")

    # 4. 최종 결과
    print("\n4️⃣ 최종 결과")
    print(f"✅ 계획 '{plan.name}' 완료!")
    print(f"📊 총 이벤트 발생: {len(events_log)}개")

    # 이벤트 히스토리 요약
    print("\n📜 이벤트 히스토리:")
    for event in events_log[-10:]:  # 최근 10개
        print(f"  {event}")

    return True


def test_concurrent_file_operations():
    """동시 파일 작업 시나리오 테스트"""
    print("\n\n=== 동시 파일 작업 시나리오 ===")
    print("시나리오: 여러 파일을 동시에 작업하는 경우\n")

    bridge = get_workflow_context_bridge()
    bus = get_event_bus()

    # 현재 태스크 설정
    bridge.current_task_id = "batch_processing_task"
    print(f"현재 태스크: batch_processing_task")

    # 여러 파일 동시 작업
    files_to_process = [
        "data/input1.csv",
        "data/input2.csv", 
        "data/input3.csv",
        "results/output.json",
        "logs/process.log"
    ]

    from events.event_types import FileEvent, EventTypes

    print("\n파일 작업 시작:")
    for file_path in files_to_process:
        # 파일 읽기
        read_event = FileEvent(
            EventTypes.FILE_ACCESSED,
            file_path=file_path,
            operation="read"
        )
        bus.publish(read_event)
        print(f"  📖 읽기: {file_path}")

        # 처리 후 쓰기
        if "output" in file_path:
            write_event = FileEvent(
                EventTypes.FILE_MODIFIED,
                file_path=file_path,
                operation="write"
            )
            bus.publish(write_event)
            print(f"  ✏️ 쓰기: {file_path}")

    # 모든 파일 작업이 현재 태스크와 연결되었는지 확인
    print(f"\n✅ 모든 파일 작업이 태스크 '{bridge.current_task_id}'와 연결됨")

    return True


def test_error_recovery_scenario():
    """에러 복구 시나리오 테스트"""
    print("\n\n=== 에러 복구 시나리오 ===")
    print("시나리오: 태스크 실패 및 재시도\n")

    bus = get_event_bus()

    # 실패 카운터
    failure_count = {'count': 0}

    def flaky_handler(event):
        """처음 2번은 실패, 3번째는 성공하는 핸들러"""
        failure_count['count'] += 1
        if failure_count['count'] < 3:
            print(f"  ❌ 핸들러 실패 (시도 {failure_count['count']})")
            raise Exception("임시 오류")
        print(f"  ✅ 핸들러 성공 (시도 {failure_count['count']})")

    # 핸들러 등록
    bus.subscribe("retry.test", flaky_handler)

    # 재시도 로직
    from events.event_bus import Event

    max_retries = 3
    for attempt in range(max_retries):
        try:
            print(f"\n시도 {attempt + 1}/{max_retries}")
            bus.publish(Event(type="retry.test"))
            break
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"  ⏳ 재시도 대기...")
                time.sleep(0.1)
            else:
                print(f"  ❌ 최대 재시도 횟수 초과")

    print("\n✅ 에러 복구 시나리오 완료")

    return True


if __name__ == "__main__":
    print("🎬 실제 시나리오 기반 통합 테스트\n")

    try:
        # 각 시나리오 실행
        test_real_development_workflow()
        test_concurrent_file_operations()
        test_error_recovery_scenario()

        print("\n\n✅ 모든 시나리오 테스트 성공!")

    except Exception as e:
        print(f"\n\n❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
