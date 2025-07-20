#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""JSON REPL 검증 스크립트"""

import sys
import ast

def check_syntax(filepath):
    """Python 파일의 문법을 검사합니다."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # AST 파싱으로 문법 검사
        ast.parse(content)
        print(f"✅ {filepath} 문법 검사 통과!")
        return True
    except SyntaxError as e:
        print(f"❌ 문법 오류 발견!")
        print(f"  파일: {e.filename}")
        print(f"  줄 번호: {e.lineno}")
        print(f"  오류: {e.msg}")
        print(f"  문제 코드: {e.text}")
        return False
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return False

if __name__ == "__main__":
    filepath = r"C:\Users\Administrator\Desktop\ai-coding-brain-mcp\python\json_repl_session.py"
    check_syntax(filepath)
