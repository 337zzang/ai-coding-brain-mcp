"""테스트 모듈"""
import os
import sys
import unused_module

def very_long_function():
    """매우 긴 함수 예시"""
    result = 0
    # 50줄 이상의 긴 함수 시뮬레이션
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
        temp11 = temp10 - 1
        temp12 = temp11 * 2
        temp13 = temp12 / 2
        temp14 = temp13 + 1
        temp15 = temp14 - 1
        temp16 = temp15 * 2
        temp17 = temp16 / 2
        temp18 = temp17 + 1
        temp19 = temp18 - 1
        temp20 = temp19 * 2
        
        if temp20 > 1000:
            break
            
    return result

def too_many_params(a, b, c, d, e, f, g):
    """매개변수가 너무 많은 함수"""
    return a + b + c + d + e + f + g

class TestClass:
    """테스트 클래스"""
    def method1(self):
        pass
