"""
워크플로우 테스트 파일
이 파일은 워크플로우-Claude Code 통합 테스트를 위해 생성되었습니다.
"""

def hello_workflow():
    """워크플로우 테스트 함수"""
    print("안녕하세요! 워크플로우 테스트입니다.")
    return "워크플로우 테스트 성공"

def calculate_sum(a, b):
    """간단한 계산 함수"""
    return a + b

if __name__ == "__main__":
    hello_workflow()
    result = calculate_sum(5, 3)
    print(f"계산 결과: {result}")
