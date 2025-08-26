#!/usr/bin/env python
"""
Hook 테스트용 파일
Stop Hook이 이 변경사항을 감지하고 git-smart-manager를 호출해야 함
"""

def test_function():
    print("Testing Git Hook system")
    print("Created: 2025-08-26 15:21")
    return True

if __name__ == "__main__":
    test_function()