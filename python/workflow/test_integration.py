"""
워크플로우-프로토콜 통합 테스트
"""

def test_integrated_workflow():
    """통합 워크플로우 테스트"""
    print("🧪 워크플로우-프로토콜 통합 테스트")
    print("=" * 60)

    # 1. 워크플로우 생성
    print("\n1️⃣ 워크플로우 생성:")
    result = helpers.workflow("create", name="프로토콜 통합 테스트", description="테스트용 워크플로우")
    if hasattr(result, 'data'):
        print(f"  ✅ 워크플로우 생성: {result.data}")

    # 2. 작업 추가
    print("\n2️⃣ 작업 추가:")
    tasks = [
        "프로토콜 초기화 테스트",
        "데이터 추적 테스트",
        "체크포인트 테스트"
    ]

    for task_title in tasks:
        result = helpers.workflow("add", title=task_title)
        if hasattr(result, 'data'):
            print(f"  ✅ 작업 추가: {task_title}")

    # 3. 작업 실행
    print("\n3️⃣ 작업 실행:")
    for i, task_title in enumerate(tasks):
        # 작업 시작
        helpers.workflow("start")
        print(f"  ▶️ 시작: {task_title}")

        # 프로토콜로 세부 작업 추적
        helpers.data("subtask", f"processing_{i}")
        helpers.progress(i+1, len(tasks), "test_workflow")

        # 작업 완료
        helpers.workflow("complete", notes=f"{task_title} 완료")
        print(f"  ✅ 완료: {task_title}")

    # 4. 최종 상태 확인
    print("\n4️⃣ 최종 상태:")
    status = helpers.workflow("status")
    if hasattr(status, 'data'):
        data = status.data
        print(f"  - 활성: {data.get('active', False)}")
        print(f"  - 완료: {data.get('completed_tasks', 0)}/{data.get('total_tasks', 0)}")
        print(f"  - 프로토콜 연동: {data.get('protocol_enabled', False)}")

    print("\n✅ 통합 테스트 완료!")

# 테스트 실행
if __name__ == "__main__":
    test_integrated_workflow()
