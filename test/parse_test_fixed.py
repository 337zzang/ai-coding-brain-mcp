"""테스트 모듈"""
import os
import sys

def hello_world():
    """Hello world 함수"""
    return "Hello, World!"

def add(a, b):
    """두 수를 더하는 함수"""
    return a + b

class Calculator:
    """계산기 클래스"""

    def __init__(self):
        self.result = 0

    def add(self, x, y):
        """더하기 메서드"""
        self.result = x + y
        return self.result

class AdvancedCalculator(Calculator):
    """고급 계산기"""

    def multiply(self, x, y):
        return x * y
