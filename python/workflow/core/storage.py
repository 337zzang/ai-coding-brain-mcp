"""
Simple Workflow Storage
======================
워크플로우와 태스크 데이터를 저장
"""

import json
import os
from typing import Dict, Any, Optional, List
from datetime import datetime


class WorkflowStorage:
    """간단한 파일 기반 스토리지"""

    def __init__(self, project_name: str):
        self.project_name = project_name

        # 저장 경로: memory/projects/{project_name}/workflow_data/
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        self.storage_dir = os.path.join(
            project_root, 'memory', 'projects', project_name, 'workflow_data'
        )
        os.makedirs(self.storage_dir, exist_ok=True)

    def save_workflow(self, workflow_id: str, data: Dict[str, Any]):
        """워크플로우 저장"""
        file_path = os.path.join(self.storage_dir, f'workflow_{workflow_id}.json')
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_workflow(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """워크플로우 로드"""
        file_path = os.path.join(self.storage_dir, f'workflow_{workflow_id}.json')
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None

    def save_task(self, task_id: str, data: Dict[str, Any]):
        """태스크 저장"""
        file_path = os.path.join(self.storage_dir, f'task_{task_id}.json')
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """태스크 로드"""
        file_path = os.path.join(self.storage_dir, f'task_{task_id}.json')
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None

    def list_workflows(self) -> List[str]:
        """모든 워크플로우 ID 목록"""
        workflows = []
        for filename in os.listdir(self.storage_dir):
            if filename.startswith('workflow_') and filename.endswith('.json'):
                workflow_id = filename[9:-5]  # workflow_ 제거, .json 제거
                workflows.append(workflow_id)
        return workflows

    def list_tasks(self) -> List[str]:
        """모든 태스크 ID 목록"""
        tasks = []
        for filename in os.listdir(self.storage_dir):
            if filename.startswith('task_') and filename.endswith('.json'):
                task_id = filename[5:-5]  # task_ 제거, .json 제거
                tasks.append(task_id)
        return tasks

    def delete_workflow(self, workflow_id: str):
        """워크플로우 삭제"""
        file_path = os.path.join(self.storage_dir, f'workflow_{workflow_id}.json')
        if os.path.exists(file_path):
            os.remove(file_path)

    def delete_task(self, task_id: str):
        """태스크 삭제"""
        file_path = os.path.join(self.storage_dir, f'task_{task_id}.json')
        if os.path.exists(file_path):
            os.remove(file_path)

    def backup(self) -> str:
        """백업 생성"""
        backup_dir = os.path.join(self.storage_dir, 'backups')
        os.makedirs(backup_dir, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = os.path.join(backup_dir, f'backup_{timestamp}')
        os.makedirs(backup_path, exist_ok=True)

        # 모든 파일 복사
        import shutil
        for filename in os.listdir(self.storage_dir):
            if filename.endswith('.json'):
                src = os.path.join(self.storage_dir, filename)
                dst = os.path.join(backup_path, filename)
                shutil.copy2(src, dst)

        return backup_path
