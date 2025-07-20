#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Missing helper functions implementation
"""

import os
import json
from pathlib import Path


def get_current_project():
    """현재 프로젝트 정보 반환"""
    # 현재 디렉토리 이름을 프로젝트명으로 사용
    current_dir = os.getcwd()
    project_name = os.path.basename(current_dir)

    # 프로젝트 메타데이터 파일 확인
    project_info = {
        'name': project_name,
        'path': current_dir,
        'type': 'unknown',
        'has_git': False
    }

    # package.json 확인 (Node.js 프로젝트)
    if os.path.exists('package.json'):
        project_info['type'] = 'node'
        try:
            with open('package.json', 'r', encoding='utf-8') as f:
                pkg = json.load(f)
                project_info['version'] = pkg.get('version', 'unknown')
                project_info['description'] = pkg.get('description', '')
        except:
            pass

    # pyproject.toml 확인 (Python 프로젝트)
    elif os.path.exists('pyproject.toml'):
        project_info['type'] = 'python'

    # requirements.txt 확인 (Python 프로젝트)
    elif os.path.exists('requirements.txt'):
        project_info['type'] = 'python'

    # Git 확인
    if os.path.exists('.git'):
        project_info['has_git'] = True

    return project_info


def get_execution_history():
    """실행 히스토리 반환"""
    # 임시로 빈 리스트 반환
    # 향후 실제 실행 기록을 추적하도록 개선
    return []


def fp(project_name):
    """flow_project의 별칭"""
    # flow_project가 구현되어 있다면 그것을 호출
    # 아니면 간단한 메시지 반환
    return f"Switching to project: {project_name}"


def flow_project(project_name):
    """프로젝트 전환"""
    # 임시 구현
    return f"Switched to project: {project_name}"


def scan_directory(path="."):
    """디렉토리 스캔"""
    import os
    result = []

    try:
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            if os.path.isdir(item_path):
                result.append(f"[DIR] {item}")
            else:
                result.append(f"[FILE] {item}")
    except Exception as e:
        return f"Error scanning directory: {e}"

    return result


def workflow(command=None):
    """워크플로우 명령 처리"""
    if command is None:
        return "Workflow status: No active workflow"

    # 임시 구현
    return f"Workflow command: {command}"


# 테스트를 위한 메인 블록
if __name__ == "__main__":
    print("Testing missing helpers...")
    print(f"Current project: {get_current_project()}")
    print(f"Execution history: {get_execution_history()}")
