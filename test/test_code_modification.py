# -*- coding: utf-8 -*-
"""Enhanced Test Module with Better Documentation"""
# Test Module for Code Modification Functions
import os
import sys
import logging

class TestClass:
    def __init__(self):
        self.name = "Test"
        self.value = 100

def simple_method(self):
    """Improved simple method with documentation"""
    print("Simple method - Enhanced version")
    logging.info("Method called")
    return True

    def complex_method(self, x, y):
        """Complex method with multiple branches"""
        if x > 0:
            if y > 0:
                return x + y
            else:
                return x - y
        else:
            return 0

def another_function(param):
    """Another test function"""
    try:
        value = int(param)
        return value * 2
    except ValueError:
        print("Error: Invalid input")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return -1


if __name__ == "__main__":
    test = TestClass()
    print(test.simple_method())
