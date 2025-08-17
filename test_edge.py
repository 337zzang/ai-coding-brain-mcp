# 복잡한 코드 구조
def complex_function():
    """
    복잡한 함수
    """
    if True:
        # 여러 중첩 구조
        for i in range(10):
            if i % 2 == 0:
                print(f"Even: {i}")
            else:
                # 이상한 들여쓰기
                    print(f"Odd: {i}")  # 의도적으로 잘못된 들여쓰기
    return "done"