# 들여쓰기 테스트 파일
def function_with_2_spaces():
  print("2칸 들여쓰기")
  return True

def function_with_4_spaces():
    print("4칸 들여쓰기")
    return True

def function_with_tabs():
    print("탭 들여쓰기")
    return True

class MixedIndentation:
    def __init__(self):
        self.value = 1

def method_2_spaces(self):
    """들여쓰기 수정된 메서드"""
    if True:
        return "2 spaces - fixed"

    def method_4_spaces(self):
        if True:
            return "4 spaces"

def complex_nested():
    for i in range(10):
        if i > 5:
            try:
                result = i * 2
                if result > 10:
                    print("Large")
                else:
                    print("Small")
            except:
                pass
        else:
            continue

def problematic_function():
    x = 1
    if x > 0:
        y = 2
        if y > 1:
            z = 3
            if z > 2:
                return "nested"
    return "default"

# 리스트 컴프리헨션과 들여쓰기
def list_comprehension_test():
    result = [
        x * 2
        for x in range(10)
        if x > 5
    ]

    # 딕셔너리 컴프리헨션
    data = {
        key: value
        for key, value in [
            ('a', 1),
            ('b', 2),
            ('c', 3)
        ]
    }
    return result, data
