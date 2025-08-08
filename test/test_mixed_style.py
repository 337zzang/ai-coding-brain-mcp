# 혼합 들여쓰기 스타일
def two_space_function():
  """2칸 들여쓰기 함수"""
  result = []
  for i in range(10):
    if i % 2 == 0:
      result.append(i)
  return result

def four_space_function():
    """4칸 들여쓰기 함수"""
    result = []
    for i in range(10):
        if i % 2 == 0:
            result.append(i)
    return result

def tab_function():
    """탭 들여쓰기 함수"""
    result = []
    for i in range(10):
        if i % 2 == 0:
            result.append(i)
    return result

class MixedClass:
    def __init__(self):
        self.value = 0

    def method_four_spaces(self):
        """4칸 메서드"""
        return self.value * 2

  def method_two_spaces(self):
    """2칸 메서드"""
    return self.value * 3
