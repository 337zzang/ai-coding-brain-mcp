#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Configuration Management - AI Coding Brain MCP
Claude Desktop 설정 관리

작성일: 2025-06-20
"""

import os
import json
from pathlib import Path

# ===========================================
# Claude Desktop 설정 관리
# ===========================================

def get_paths_from_config() -> dict:
    """경로 설정 가져오기 - config.json과 Claude Desktop 설정 병합"""
    import os
    import json
    from pathlib import Path
    
    # 기본값 설정
    paths = {
        'project_path': Path.home() / "Desktop",
        'desktop_path': Path.home() / "Desktop",  # desktop_path 추가
        'memory_root': None,  # 이제 각 프로젝트 내부 memory 폴더 사용
        'workspace_dirs': []
    }
    
    # 1. 프로젝트의 config.json 읽기
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    config_json_path = os.path.join(project_root, "config.json")
    
    if os.path.exists(config_json_path):
        try:
            with open(config_json_path, 'r', encoding='utf-8') as f:
                project_config = json.load(f)
                
            # config.json의 설정 적용
            if 'desktop_path' in project_config:
                paths['desktop_path'] = Path(project_config['desktop_path'])
                paths['project_path'] = Path(project_config['desktop_path'])  # project_path도 동일하게
                
            if 'workspace_dirs' in project_config:
                paths['workspace_dirs'] = project_config['workspace_dirs']
                
        except Exception as e:
            print(f"⚠️ config.json 로드 실패: {e}")
    
    # 2. Claude Desktop 설정 읽기 (기존 로직)
    claude_config_path = os.path.expanduser("~/AppData/Roaming/Claude/claude_desktop_config.json")
    
    if os.path.exists(claude_config_path):
        try:
            with open(claude_config_path, 'r', encoding='utf-8') as f:
                claude_config = json.load(f)
            
            mcp_servers = claude_config.get('mcpServers', {})
            for server_name, server_config in mcp_servers.items():
                if 'ai-coding-brain' in server_name.lower():
                    env = server_config.get('env', {})
                    if 'PROJECT_ROOT' in env:
                        # Claude 설정이 있으면 덮어쓰기
                        paths['project_path'] = Path(env['PROJECT_ROOT'])
                        paths['desktop_path'] = Path(env['PROJECT_ROOT'])
    # if 'MEMORY_BANK_ROOT' in env:  # 중앙 집중식 메모리 제거됨
    # paths['memory_root'] = Path(env['MEMORY_BANK_ROOT'])  # 중앙 집중식 메모리 제거됨
                    break
        except Exception as e:
            print(f"⚠️ Claude Desktop 설정 로드 실패: {e}")
    
    # 경로 확인 로그
    print(f"📁 경로 설정:")
    print(f"   desktop_path: {paths['desktop_path']}")
    print(f"   memory_root: {paths['memory_root']}")
    
    return paths






def get_project_path(project_name: str) -> str:
    """프로젝트 이름으로 경로를 찾습니다."""
    import os
    
    # 현재 디렉토리가 프로젝트인 경우
    current_dir = os.getcwd()
    if os.path.basename(current_dir) == project_name:
        return current_dir
    
    # 데스크톱에서 찾기
    desktop = os.path.expanduser("~/Desktop")
    project_path = os.path.join(desktop, project_name)
    if os.path.exists(project_path):
        return project_path
    
    return None
