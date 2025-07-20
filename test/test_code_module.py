"""테스트 모듈"""
import os
import sys

def hello(name):
    """인사 함수"""
    return f"Hello, {name}!"

def add(a, b):
    """덧셈 함수"""
    return a + b

class Calculator:
    """계산기 클래스"""

    def __init__(self):
        self.result = 0

    def add(self, x):
        self.result += x
        return self.result

    def subtract(self, x):
        self.result -= x
        return self.result

# 메인 실행
if __name__ == "__main__":
    print(hello("World"))
