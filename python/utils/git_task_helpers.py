"""
Git 연계 헬퍼 함수들
작업과 커밋을 연결하는 유틸리티
"""
import subprocess
import os
from typing import Optional, Dict, Any


def get_current_commit_hash(project_path: str = ".") -> Optional[str]:
    """현재 HEAD 커밋 해시 반환"""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=project_path,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None


def create_task_commit(task_title: str, task_id: str, summary: str = "", 
                      project_path: str = ".") -> Dict[str, Any]:
    """작업 완료 커밋 생성 및 정보 반환

    Returns:
        {
            'success': bool,
            'commit_id': str or None,
            'message': str
        }
    """
    # 커밋 메시지 생성 (작업 ID 포함)
    commit_message = f"task({task_id[:8]}): {task_title}"
    if summary:
        commit_message += f" - {summary}"

    try:
        # git add
        subprocess.run(
            ["git", "add", "."],
            cwd=project_path,
            check=True
        )

        # git commit
        result = subprocess.run(
            ["git", "commit", "-m", commit_message],
            cwd=project_path,
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            # 커밋 해시 가져오기
            commit_hash = get_current_commit_hash(project_path)
            return {
                'success': True,
                'commit_id': commit_hash,
                'message': commit_message
            }
        else:
            # 변경사항이 없는 경우
            if "nothing to commit" in result.stdout:
                return {
                    'success': False,
                    'commit_id': None,
                    'message': "변경사항 없음"
                }
            else:
                return {
                    'success': False,
                    'commit_id': None,
                    'message': result.stderr
                }

    except subprocess.CalledProcessError as e:
        return {
            'success': False,
            'commit_id': None,
            'message': str(e)
        }


def get_task_related_files(project_path: str = ".") -> Dict[str, Any]:
    """현재 변경된 파일 목록 조회

    Returns:
        {
            'modified': [],
            'added': [],
            'deleted': [],
            'untracked': []
        }
    """
    try:
        # git status --porcelain
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=project_path,
            capture_output=True,
            text=True,
            check=True
        )

        files = {
            'modified': [],
            'added': [],
            'deleted': [],
            'untracked': []
        }

        for line in result.stdout.strip().split('\n'):
            if not line:
                continue

            status = line[:2]
            filepath = line[3:]

            if status == ' M' or status == 'M ':
                files['modified'].append(filepath)
            elif status == 'A ' or status == 'AM':
                files['added'].append(filepath)
            elif status == 'D ':
                files['deleted'].append(filepath)
            elif status == '??':
                files['untracked'].append(filepath)

        return files

    except subprocess.CalledProcessError:
        return {
            'modified': [],
            'added': [],
            'deleted': [],
            'untracked': []
        }


def push_commits(branch: Optional[str] = None, project_path: str = ".") -> bool:
    """커밋을 원격 저장소에 푸시

    Args:
        branch: 브랜치명. None이면 현재 브랜치

    Returns:
        성공 여부
    """
    try:
        cmd = ["git", "push"]
        if branch:
            cmd.extend(["origin", branch])

        result = subprocess.run(
            cmd,
            cwd=project_path,
            capture_output=True,
            text=True
        )

        return result.returncode == 0

    except subprocess.CalledProcessError:
        return False
