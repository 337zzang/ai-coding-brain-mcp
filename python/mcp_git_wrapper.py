#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MCP Git Wrapper - Git 명령을 위한 래퍼 스크립트
"""
import sys
import json
import os

# 프로젝트 python 디렉토리를 sys.path에 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
python_dir = os.path.join(project_root, 'python')
if python_dir not in sys.path:
    sys.path.insert(0, python_dir)

from git_version_manager import GitVersionManager

def main():
    if len(sys.argv) < 2:
        print(json.dumps({
            "success": False,
            "message": "No command provided"
        }))
        return
    
    command = sys.argv[1]
    git_manager = GitVersionManager()
    
    try:
        if command == "status":
            result = git_manager.git_status()
            print(json.dumps(result, ensure_ascii=False))
            
        elif command == "commit":
            message = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] else ""
            auto_add = sys.argv[3].lower() == 'true' if len(sys.argv) > 3 else True
            result = git_manager.git_commit_smart(message, auto_add)
            print(json.dumps(result, ensure_ascii=False))
            
        elif command == "branch-smart":
            branch_name = sys.argv[2] if len(sys.argv) > 2 else None
            base_branch = None
            
            # --base 옵션 파싱
            if "--base" in sys.argv:
                base_idx = sys.argv.index("--base")
                if base_idx + 1 < len(sys.argv):
                    base_branch = sys.argv[base_idx + 1]
            
            result = git_manager.git_branch_smart(branch_name, base_branch)
            print(json.dumps(result, ensure_ascii=False))
            
        else:
            print(json.dumps({
                "success": False,
                "message": f"Unknown command: {command}"
            }))
            
    except Exception as e:
        print(json.dumps({
            "success": False,
            "message": str(e)
        }, ensure_ascii=False))

if __name__ == "__main__":
    main()
