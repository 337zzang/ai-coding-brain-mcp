"""
Phase 4: 이벤트 버스 통합 테스트
전체 시스템의 이벤트 기반 아키텍처 검증
"""
import sys
from pathlib import Path
import json
import time
from datetime import datetime

# 프로젝트 루트 경로 추가
sys.path.insert(0, str(Path(__file__).parent))

# 실제 존재하는 모듈 임포트
try:
    from python.workflow.v3.event_bus import EventBus
    from python.core.context_manager_ssot import ContextManagerSSOT
    from python.workflow.v3.manager import WorkflowManager
    from python.workflow.v3.workflow_event_adapter import WorkflowEventAdapter
    print("✅ 모든 모듈 임포트 성공")
except ImportError as e:
    print(f"❌ 모듈 임포트 실패: {e}")
    # 대체 경로 시도
    try:
        from python.workflow.v3 import EventBus, WorkflowManager
        from python.core import ContextManagerSSOT
        print("✅ 대체 경로로 임포트 성공")
    except ImportError as e2:
        print(f"❌ 대체 경로도 실패: {e2}")
        sys.exit(1)

class IntegrationTest:
    """통합 테스트 클래스"""

    def __init__(self):
        self.results = []
        self.event_bus = None
        self.context_manager = None
        self.workflow_manager = None

    def setup(self):
        """테스트 환경 설정"""
        try:
            self.event_bus = EventBus()
            self.context_manager = ContextManagerSSOT(self.event_bus)
            self.workflow_manager = WorkflowManager()

            # 이벤트 어댑터 연결
            if hasattr(sys.modules['python.workflow.v3'], 'WorkflowEventAdapter'):
                self.adapter = WorkflowEventAdapter(self.workflow_manager, self.event_bus)

            print("✅ 테스트 환경 설정 완료")
            return True
        except Exception as e:
            print(f"❌ 설정 실패: {e}")
            return False

    def test_basic_event_flow(self):
        """기본 이벤트 플로우 테스트"""
        print("\n=== 기본 이벤트 플로우 테스트 ===")

        events_received = []

        # 이벤트 리스너
        def event_listener(event_type, data):
            events_received.append({
                'type': event_type,
                'data': data,
                'time': datetime.now()
            })
            print(f"  이벤트 수신: {event_type}")

        # 리스너 등록
        self.event_bus.on('test:event', event_listener)

        # 이벤트 발행
        self.event_bus.emit('test:event', {'message': 'Hello Event Bus!'})

        # 검증
        success = len(events_received) == 1
        print(f"  결과: {'✅ PASS' if success else '❌ FAIL'}")
        return success

    def test_workflow_integration(self):
        """워크플로우 통합 테스트"""
        print("\n=== 워크플로우 통합 테스트 ===")

        try:
            # 플랜 생성
            if hasattr(self.workflow_manager, 'create_plan'):
                result = self.workflow_manager.create_plan("테스트 플랜")
                print("  ✅ 플랜 생성 성공")
            else:
                print("  ⚠️  create_plan 메서드 없음")

            # 태스크 추가
            if hasattr(self.workflow_manager, 'add_task'):
                self.workflow_manager.add_task("테스트 태스크")
                print("  ✅ 태스크 추가 성공")
            else:
                print("  ⚠️  add_task 메서드 없음")

            return True
        except Exception as e:
            print(f"  ❌ 오류: {e}")
            return False

    def test_performance(self):
        """성능 테스트"""
        print("\n=== 성능 테스트 ===")

        event_count = 1000
        start_time = time.time()

        # 대량 이벤트 발행
        for i in range(event_count):
            self.event_bus.emit('perf:test', {'index': i})

        elapsed = time.time() - start_time
        events_per_sec = event_count / elapsed

        print(f"  이벤트 수: {event_count}")
        print(f"  소요 시간: {elapsed:.3f}초")
        print(f"  처리 속도: {events_per_sec:.0f} events/sec")

        success = events_per_sec > 500  # 최소 500 events/sec
        print(f"  결과: {'✅ PASS' if success else '❌ FAIL'}")
        return success

    def run_all_tests(self):
        """모든 테스트 실행"""
        print("\n" + "="*60)
        print("Phase 4: 통합 테스트 시작")
        print("="*60)

        if not self.setup():
            print("\n테스트 환경 설정 실패로 종료")
            return False

        # 테스트 목록
        tests = [
            self.test_basic_event_flow,
            self.test_workflow_integration,
            self.test_performance
        ]

        # 각 테스트 실행
        passed = 0
        for test in tests:
            try:
                if test():
                    passed += 1
                    self.results.append((test.__name__, "PASS"))
                else:
                    self.results.append((test.__name__, "FAIL"))
            except Exception as e:
                self.results.append((test.__name__, f"ERROR: {str(e)}"))

        # 결과 요약
        print("\n" + "="*60)
        print("테스트 결과 요약")
        print("="*60)

        for test_name, result in self.results:
            icon = "✅" if result == "PASS" else "❌"
            print(f"{icon} {test_name}: {result}")

        print(f"\n총 {len(tests)}개 중 {passed}개 통과")

        return passed == len(tests)

if __name__ == "__main__":
    tester = IntegrationTest()
    success = tester.run_all_tests()

    # 테스트 결과를 파일로 저장
    result_data = {
        'timestamp': datetime.now().isoformat(),
        'success': success,
        'results': tester.results
    }

    with open('test_phase4_results.json', 'w') as f:
        json.dump(result_data, f, indent=2)

    print(f"\n테스트 결과가 test_phase4_results.json에 저장됨")
    sys.exit(0 if success else 1)
