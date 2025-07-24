"""
auto_record decorator 테스트
"""
import os
import time
from ai_helpers_new.decorators import auto_record
from ai_helpers_new.context_integration import ContextIntegration

class TestFlowManager:
    """테스트용 FlowManager"""

    def __init__(self):
        self._context = ContextIntegration()
        self._context_enabled = True
        self._current_flow_id = "test_flow_001"

    @auto_record(capture_params=True, capture_result=True)
    def create_something(self, name: str, value: int = 42):
        """테스트 메서드 - 성공 케이스"""
        time.sleep(0.01)  # 10ms 대기
        return {"ok": True, "id": f"{name}_{value}"}

    @auto_record(log_start=True)
    def delete_something(self, item_id: str):
        """테스트 메서드 - 실패 케이스"""
        if "invalid" in item_id:
            raise ValueError(f"Invalid ID: {item_id}")
        return {"ok": True}

    @auto_record(capture_result=False)
    def process_large_data(self, data_size: int):
        """결과 캡처하지 않는 케이스"""
        # 큰 데이터 시뮬레이션
        result = list(range(data_size))
        return result

# 테스트 실행
if __name__ == "__main__":
    print("=== auto_record decorator 테스트 ===\n")

    # Context 시스템 활성화
    os.environ['CONTEXT_SYSTEM'] = 'on'

    manager = TestFlowManager()

    # 1. 정상 실행 테스트
    print("1. 정상 실행 테스트:")
    result = manager.create_something("test_item", value=100)
    print(f"   결과: {result}")

    # 2. 예외 발생 테스트
    print("\n2. 예외 발생 테스트:")
    try:
        manager.delete_something("invalid_id_123")
    except ValueError as e:
        print(f"   예외 캐치: {e}")

    # 3. 큰 결과 테스트
    print("\n3. 큰 결과 처리 테스트:")
    large_result = manager.process_large_data(1000)
    print(f"   결과 길이: {len(large_result)}")

    # 4. Context OFF 테스트
    print("\n4. Context OFF 테스트:")
    os.environ['CONTEXT_OFF'] = '1'
    result = manager.create_something("no_context", 999)
    print(f"   결과: {result}")
    os.environ.pop('CONTEXT_OFF', None)

    # Context 기록 확인 (약간의 지연 필요)
    import time
    time.sleep(0.5)  # executor가 작업 완료하도록 대기

    print("\n✅ 테스트 완료")
