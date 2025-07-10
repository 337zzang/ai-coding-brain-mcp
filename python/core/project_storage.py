"""
ProjectStorageManager - 프로젝트 메모리 파일 통합 관리
context, workflow, cache 파일들을 일관되게 관리하는 추상화 레이어
"""
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List

from python.path_utils import (
    get_project_root,
    get_memory_dir,
    get_context_path,
    get_workflow_path,
    get_cache_dir,
    get_backup_dir,
    ensure_dir
)
from python.utils.io_helpers import (
    read_json,
    write_json,
    atomic_write,
    safe_read,
    backup_file
)

logger = logging.getLogger(__name__)


class ProjectStorageManager:
    """프로젝트의 모든 스토리지 파일을 관리하는 클래스"""

    def __init__(self, project_name: str):
        self.project_name = project_name
        self.project_root = get_project_root(project_name)
        self.memory_dir = get_memory_dir(project_name)

        # 주요 파일 경로
        self.context_path = get_context_path(project_name)
        self.workflow_path = get_workflow_path(project_name)
        self.cache_dir = get_cache_dir(project_name)
        self.backup_dir = get_backup_dir(project_name)

        # 캐시 파일 정의
        self.cache_files = {
            'file_directory': self.cache_dir / 'file_directory.json',
            'analyzed_files': self.cache_dir / 'analyzed_files.json',
            'ast_cache': self.cache_dir / 'ast_cache.json'
        }

        # 메모리 구조 확인
        self.ensure_memory_structure()

    def ensure_memory_structure(self) -> None:
        """필수 디렉토리 구조 생성"""
        dirs_to_create = [
            self.memory_dir,
            self.cache_dir,
            self.backup_dir,
            self.backup_dir / 'context',
            self.backup_dir / 'workflow'
        ]

        for dir_path in dirs_to_create:
            ensure_dir(dir_path)

        logger.debug(f"Memory structure ensured for {self.project_name}")

    def load_project_state(self) -> Dict[str, Any]:
        """프로젝트의 모든 상태를 로드

        Returns:
            {
                'context': {...},
                'workflow': {...},
                'cache': {
                    'file_directory': [...],
                    'analyzed_files': [...],
                    'ast_cache': {...}
                }
            }
        """
        state = {
            'context': {},
            'workflow': {},
            'cache': {}
        }

        # context.json 로드
        state['context'] = read_json(self.context_path, default={})

        # workflow.json 로드
        state['workflow'] = read_json(self.workflow_path, default={})

        # 캐시 파일들 로드
        for cache_name, cache_path in self.cache_files.items():
            if cache_path.exists():
                state['cache'][cache_name] = read_json(cache_path, default=None)

        logger.info(f"Loaded project state for {self.project_name}")
        return state

    def save_project_state(self, context: Dict[str, Any], 
                          workflow: Dict[str, Any],
                          cache_data: Optional[Dict[str, Any]] = None) -> bool:
        """프로젝트 상태를 원자적으로 저장

        Args:
            context: context.json에 저장할 데이터
            workflow: workflow.json에 저장할 데이터  
            cache_data: 캐시 파일들에 저장할 데이터 (선택적)

        Returns:
            성공 여부
        """
        try:
            # 타임스탬프 추가
            timestamp = datetime.now().isoformat()
            context['last_modified'] = timestamp
            workflow['last_modified'] = timestamp

            # context.json 저장
            if not write_json(self.context_path, context):
                logger.error("Failed to save context.json")
                return False

            # workflow.json 저장
            if not write_json(self.workflow_path, workflow):
                logger.error("Failed to save workflow.json")
                return False

            # 캐시 데이터 저장 (있는 경우)
            if cache_data:
                for cache_name, data in cache_data.items():
                    if cache_name in self.cache_files and data is not None:
                        cache_path = self.cache_files[cache_name]
                        if not write_json(cache_path, data):
                            logger.warning(f"Failed to save cache: {cache_name}")

            logger.info(f"Saved project state for {self.project_name}")
            return True

        except Exception as e:
            logger.error(f"Error saving project state: {e}")
            return False

    def update_cache_file(self, cache_name: str, data: Any) -> bool:
        """특정 캐시 파일 업데이트

        Args:
            cache_name: 캐시 이름 (file_directory, analyzed_files, ast_cache 등)
            data: 저장할 데이터

        Returns:
            성공 여부
        """
        if cache_name not in self.cache_files:
            logger.error(f"Unknown cache: {cache_name}")
            return False

        cache_path = self.cache_files[cache_name]
        cache_data = {
            'data': data,
            'last_updated': datetime.now().isoformat()
        }

        return write_json(cache_path, cache_data)

    def get_cache_data(self, cache_name: str) -> Optional[Any]:
        """특정 캐시 데이터 읽기

        Args:
            cache_name: 캐시 이름

        Returns:
            캐시 데이터 또는 None
        """
        if cache_name not in self.cache_files:
            return None

        cache_path = self.cache_files[cache_name]
        if not cache_path.exists():
            return None

        cache_content = read_json(cache_path, default=None)
        if cache_content and isinstance(cache_content, dict):
            return cache_content.get('data')
        return cache_content

    def create_backup(self, include_cache: bool = False) -> Optional[Path]:
        """현재 상태 백업 생성

        Args:
            include_cache: 캐시 파일도 백업할지 여부

        Returns:
            백업 디렉토리 경로 또는 None
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # context 백업
            if self.context_path.exists():
                backup_path = self.backup_dir / 'context' / f'context_{timestamp}.json'
                ensure_dir(backup_path.parent)
                backup_file(self.context_path, backup_path.parent)

            # workflow 백업
            if self.workflow_path.exists():
                backup_path = self.backup_dir / 'workflow' / f'workflow_{timestamp}.json'
                ensure_dir(backup_path.parent)
                backup_file(self.workflow_path, backup_path.parent)

            # 캐시 백업 (선택적)
            if include_cache:
                cache_backup_dir = self.backup_dir / f'cache_{timestamp}'
                ensure_dir(cache_backup_dir)
                for cache_name, cache_path in self.cache_files.items():
                    if cache_path.exists():
                        backup_file(cache_path, cache_backup_dir)

            logger.info(f"Created backup for {self.project_name}")
            return self.backup_dir

        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return None

    def get_file_paths(self) -> Dict[str, Path]:
        """모든 관리 파일 경로 반환"""
        paths = {
            'context': self.context_path,
            'workflow': self.workflow_path,
            'memory_dir': self.memory_dir,
            'cache_dir': self.cache_dir,
            'backup_dir': self.backup_dir
        }

        # 캐시 파일 경로 추가
        for cache_name, cache_path in self.cache_files.items():
            paths[f'cache_{cache_name}'] = cache_path

        return paths

    def get_storage_info(self) -> Dict[str, Any]:
        """스토리지 상태 정보 반환"""
        info = {
            'project_name': self.project_name,
            'project_root': str(self.project_root),
            'files': {}
        }

        # 각 파일의 존재 여부와 크기
        for name, path in self.get_file_paths().items():
            if path.is_file() and path.exists():
                info['files'][name] = {
                    'exists': True,
                    'size': path.stat().st_size,
                    'modified': datetime.fromtimestamp(path.stat().st_mtime).isoformat()
                }
            else:
                info['files'][name] = {'exists': False}

        return info

    def clear_cache(self, cache_name: Optional[str] = None) -> bool:
        """캐시 삭제

        Args:
            cache_name: 특정 캐시만 삭제 (None이면 모든 캐시)

        Returns:
            성공 여부
        """
        try:
            if cache_name:
                if cache_name in self.cache_files:
                    cache_path = self.cache_files[cache_name]
                    if cache_path.exists():
                        cache_path.unlink()
                    logger.info(f"Cleared cache: {cache_name}")
            else:
                # 모든 캐시 삭제
                for name, path in self.cache_files.items():
                    if path.exists():
                        path.unlink()
                logger.info("Cleared all caches")

            return True

        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            return False
