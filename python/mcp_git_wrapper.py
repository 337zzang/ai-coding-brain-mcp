#!/usr/bin/env python3
"""
MCP Git Wrapper - Git 명령어를 Python으로 래핑
AI Coding Brain MCP 프로젝트
"""

import sys
import json
import subprocess
import os
from datetime import datetime
from git_version_manager import GitVersionManager

def main():
    """메인 진입점"""
    if len(sys.argv) < 2:
        print(json.dumps({"success": False, "message": "명령어가 지정되지 않았습니다"}))
        sys.exit(1)
    
    command = sys.argv[1]
    gvm = GitVersionManager()
    
    try:
        if command == "status":
            result = gvm.git_status()
            print(json.dumps(result, ensure_ascii=False))
            
        elif command == "branch-smart":
            branch_name = sys.argv[2] if len(sys.argv) > 2 else None
            base_branch = "master"  # 기본값
            
            # --base 옵션 파싱
            if "--base" in sys.argv:
                base_idx = sys.argv.index("--base")
                if base_idx + 1 < len(sys.argv):
                    base_branch = sys.argv[base_idx + 1]
            
            result = gvm.git_branch_smart(branch_name, base_branch)
            print(json.dumps(result, ensure_ascii=False))
            
        elif command == "commit-smart":
            message = sys.argv[2] if len(sys.argv) > 2 else None
            auto_add = "--auto-add" in sys.argv
            
            result = gvm.git_commit_smart(message, auto_add)
            print(json.dumps(result, ensure_ascii=False))
            
        elif command == "rollback-smart":
            target = sys.argv[2] if len(sys.argv) > 2 else None
            safe_mode = "--safe" in sys.argv or True  # 기본값 True
            
            result = gvm.git_rollback_smart(target, safe_mode)
            print(json.dumps(result, ensure_ascii=False))
            
        elif command == "push":
            remote = sys.argv[2] if len(sys.argv) > 2 else "origin"
            branch = sys.argv[3] if len(sys.argv) > 3 else None
            
            result = gvm.git_push(remote, branch)
            print(json.dumps(result, ensure_ascii=False))
            
        else:
            print(json.dumps({
                "success": False, 
                "message": f"알 수 없는 명령어: {command}"
            }))
            sys.exit(1)
            
    except Exception as e:
        print(json.dumps({
            "success": False,
            "message": f"오류 발생: {str(e)}"
        }, ensure_ascii=False))
        sys.exit(1)

if __name__ == "__main__":
    main()
