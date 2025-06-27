"""테스트용 Python 파일"""
import os
import sys
from pathlib import Path
from .utils import helper_function
import unused_module

class TestClass:
    """테스트 클래스"""
    
    def __init__(self):
        self.value = 0
        
    def simple_method(self):
        """간단한 메서드"""
        return self.value
        
    def long_method(self):
        """긴 메서드 예시"""
        # 50줄 이상의 긴 함수 시뮬레이션
        result = 0
        for i in range(100):
            if i % 2 == 0:
                result += i
            else:
                result -= i
                
            if i > 50:
                if i % 3 == 0:
                    result *= 2
                elif i % 5 == 0:
                    result //= 2
                    
            # 더 많은 코드...
            temp = result * 2
            temp2 = temp + 1
            temp3 = temp2 - 1
            temp4 = temp3 * 2
            temp5 = temp4 / 2
            temp6 = temp5 + 1
            temp7 = temp6 - 1
            temp8 = temp7 * 2
            temp9 = temp8 / 2
            temp10 = temp9 + 1
            
            if temp10 > 100:
                break
                
        return result

def standalone_function(param1, param2, param3, param4, param5, param6):
    """매개변수가 많은 함수"""
    return param1 + param2

async def async_function():
    """비동기 함수"""
    return await some_async_call()
    
# 미사용 변수
unused_var = "This is not used"
