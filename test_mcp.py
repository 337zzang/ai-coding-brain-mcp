#!/usr/bin/env python3
"""MCP 서버 직접 테스트 스크립트"""

import sys
import os
import subprocess

# Python 경로 설정
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'python'))

def test_mcp_connection():
    """MCP 서버 연결 테스트"""
    print("MCP 서버 테스트 시작...")
    
    # ai_helpers 모듈 임포트 테스트
    try:
        from ai_helpers import helpers
        print("✅ ai_helpers 모듈 로드 성공")
        
        # 프로젝트 목록 확인
        projects = helpers.list_projects()
        print(f"✅ 프로젝트 목록: {projects}")
        
        # 현재 컨텍스트 확인
        context = helpers.get_context()
        print(f"✅ 현재 컨텍스트: {context}")
        
        return True
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return False

if __name__ == "__main__":
    test_mcp_connection()