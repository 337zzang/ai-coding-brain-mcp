"""
Stdout Protocol 사용 예시
"""

from ai_helpers.protocols import get_protocol, get_tracker

# 프로토콜 가져오기
protocol = get_protocol()
tracker = get_tracker()

# 사용 예시
@tracker.track
def example_function():
    # 섹션 시작
    section_id = protocol.section("example_task")

    # 데이터 출력
    protocol.data("status", "started")

    # 진행 상황
    for i in range(5):
        protocol.progress(i+1, 5, "processing")

    # 체크포인트
    protocol.checkpoint("example_done", {"result": "success"})

    # 섹션 종료
    protocol.end_section()

    # 다음 작업 지시
    protocol.next_action("continue", {"next_batch": 10})

if __name__ == "__main__":
    example_function()
