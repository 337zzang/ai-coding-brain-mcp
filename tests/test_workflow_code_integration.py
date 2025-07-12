
# test_workflow_code_integration.py
import sys
sys.path.append('.')

from python.helpers_wrapper import execute_code_with_workflow, get_workflow_context

def test_workflow_integration():
    """워크플로우 코드 통합 테스트"""

    print("🧪 워크플로우 코드 통합 테스트 시작")
    print("-" * 40)

    # 1. 현재 워크플로우 컨텍스트 확인
    print("\n1. 현재 워크플로우 컨텍스트 확인:")
    context_result = get_workflow_context()
    if context_result.ok:
        context = context_result.data
        if context:
            print(f"   ✅ 현재 태스크: {context['task_title']}")
            print(f"   플랜: {context['plan_name']}")
        else:
            print("   ⚠️ 진행 중인 태스크가 없습니다")
    else:
        print(f"   ❌ 컨텍스트 조회 실패: {context_result.error}")

    # 2. 간단한 코드 실행 테스트
    print("\n2. 워크플로우 연계 코드 실행:")
    test_code = """
print('테스트 코드 실행 중...')
result = 1 + 1
print(f'계산 결과: {result}')
print('테스트 완료!')
"""

    result = execute_code_with_workflow(test_code, auto_progress=False)
    if result.ok:
        print("   ✅ 코드 실행 성공")
    else:
        print(f"   ❌ 코드 실행 실패: {result.error}")

    # 3. 자동 진행 테스트
    print("\n3. 자동 진행 기능 테스트:")
    completion_code = """
print('작업 수행 중...')
# 실제 작업 시뮬레이션
import time
time.sleep(0.5)
print('작업 완료!')
"""

    result = execute_code_with_workflow(completion_code, auto_progress=True)
    if result.ok:
        print("   ✅ 자동 진행 테스트 완료")

    print("\n🎉 테스트 완료!")

if __name__ == "__main__":
    test_workflow_integration()
