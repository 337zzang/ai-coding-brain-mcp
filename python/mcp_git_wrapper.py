#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MCP Git Wrapper - AI Coding Brain MCP
MCP 환경에서 Git 명령어 실행을 위한 래퍼
"""

import os
import sys
import json

# 현재 디렉토리의 python 폴더를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Windows Git 경로 설정
if sys.platform == 'win32':
    git_paths = [
        r"C:\Program Files\Git\cmd",
        r"C:\Program Files\Git\bin",
        r"C:\Program Files (x86)\Git\cmd",
        r"C:\Program Files (x86)\Git\bin"
    ]
    for git_path in git_paths:
        if os.path.exists(git_path) and git_path not in os.environ.get('PATH', ''):
            os.environ['PATH'] = git_path + ';' + os.environ.get('PATH', '')

from git_version_manager import GitVersionManager

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"success": False, "message": "Command required."}))
        return

    command = sys.argv[1]
    project_root = os.getcwd()
    
    # 프로젝트 루트가 ai-coding-brain-mcp가 아니면 변경
    if not project_root.endswith('ai-coding-brain-mcp'):
        # 상위 디렉토리들을 검색하여 프로젝트 루트 찾기
        for _ in range(5):  # 최대 5단계까지 상위로
            if os.path.exists(os.path.join(project_root, '.ai-brain.config.json')):
                break
            parent = os.path.dirname(project_root)
            if parent == project_root:  # 루트 디렉토리 도달
                break
            project_root = parent
    
    git_manager = GitVersionManager(project_root)
    
    try:
        if command == "status":
            result = git_manager.git_status()
            if result:
                # 디버깅 정보 추가
                debug_info = f"\n[DEBUG] Branch: {result.get('branch')}"
                debug_info += f"\n[DEBUG] Working dir: {project_root}"
                debug_info += f"\n[DEBUG] Modified: {result.get('modified', [])}"
                debug_info += f"\n[DEBUG] Staged: {result.get('staged', [])}"
                debug_info += f"\n[DEBUG] Untracked: {result.get('untracked', [])}"
                
                message = f"Current branch: {result.get('branch', 'unknown')}\n"
                message += f"Modified files: {len(result.get('modified', []))} files\n"
                message += f"Staged files: {len(result.get('staged', []))} files\n"
                message += f"Untracked files: {len(result.get('untracked', []))} files\n"
                message += f"Clean status: {'Yes' if result.get('clean') else 'No'}"
                # message += debug_info  # 디버깅 시 주석 해제
                
                output = {
                    "success": True,
                    "message": message,
                    "data": result
                }
            else:
                output = {
                    "success": False,
                    "message": "Git status could not be retrieved."
                }
                
        elif command == "commit":
            message = sys.argv[2] if len(sys.argv) > 2 else None
            auto_add = sys.argv[3].lower() != 'false' if len(sys.argv) > 3 else True
            
            result = git_manager.git_commit_smart(message, auto_add)
            output = {
                "success": result['success'],
                "message": result['message'],
                "data": result
            }
            
        elif command == "push":
            remote = sys.argv[2] if len(sys.argv) > 2 else "origin"
            branch = sys.argv[3] if len(sys.argv) > 3 else None
            
            result = git_manager.git_push(remote, branch)
            output = {
                "success": result['success'],
                "message": result['message'],
                "data": result
            }
            
        else:
            output = {
                "success": False,
                "message": f"알 수 없는 명령어: {command}"
            }
            
    except Exception as e:
        output = {
            "success": False,
            "message": f"오류 발생: {str(e)}"
        }
    
    print(json.dumps(output, ensure_ascii=False))

if __name__ == "__main__":
    main()
