"""
WisdomFactory - 중앙 집중식 Wisdom 인스턴스 관리
AI Coding Brain MCP 환경에서 프로젝트별 Wisdom Manager를 싱글톤으로 관리
"""

import os
from typing import Dict, Optional
from pathlib import Path
from ..project_wisdom import ProjectWisdomManager

class WisdomFactory:
    """MCP 환경에서 공유되는 Wisdom 인스턴스 관리"""
    
    _instances: Dict[str, ProjectWisdomManager] = {}
    _current_project: Optional[str] = None
    
    @classmethod
    def get_manager(cls, project_id: str = None) -> ProjectWisdomManager:
        """프로젝트별 Wisdom Manager 반환 (싱글톤)
        
        Args:
            project_id: 프로젝트 ID (None이면 현재 프로젝트 자동 감지)
            
        Returns:
            ProjectWisdomManager: 해당 프로젝트의 Wisdom Manager 인스턴스
        """
        # 프로젝트 ID가 없으면 현재 프로젝트 자동 감지
        if project_id is None:
            project_id = cls._detect_current_project()
            
        # 캐시된 인스턴스 반환
        if project_id in cls._instances:
            return cls._instances[project_id]
            
        # 새 인스턴스 생성 및 캐싱
        manager = ProjectWisdomManager(project_id)
        cls._instances[project_id] = manager
        cls._current_project = project_id
        
        return manager
    
    @classmethod
    def _detect_current_project(cls) -> str:
        """현재 프로젝트 자동 감지"""
        # 1. 환경 변수에서 확인
        if os.environ.get('PROJECT_ID'):
            return os.environ['PROJECT_ID']
            
        # 2. 현재 작업 디렉토리에서 프로젝트 이름 추출
        cwd = Path.cwd()
        
        # .ai-brain.config.json 파일 확인
        config_path = cwd / '.ai-brain.config.json'
        if config_path.exists():
            import json
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    if 'project_name' in config:
                        return config['project_name']
            except:
                pass
                
        # 3. 디렉토리 이름을 프로젝트 ID로 사용
        return cwd.name
    
    @classmethod
    def clear_cache(cls, project_id: str = None):
        """캐시된 인스턴스 제거
        
        Args:
            project_id: 제거할 프로젝트 ID (None이면 모든 캐시 제거)
        """
        if project_id:
            cls._instances.pop(project_id, None)
        else:
            cls._instances.clear()
            
    @classmethod
    def get_current_project(cls) -> Optional[str]:
        """현재 활성 프로젝트 ID 반환"""
        return cls._current_project
    
    @classmethod
    def list_projects(cls) -> list:
        """캐시된 프로젝트 목록 반환"""
        return list(cls._instances.keys())


# 글로벌 접근을 위한 헬퍼 함수
def get_wisdom_manager(project_id: str = None) -> ProjectWisdomManager:
    """WisdomFactory를 통해 Wisdom Manager 인스턴스 반환
    
    이 함수는 어디서든 import해서 사용할 수 있는 진입점입니다.
    """
    return WisdomFactory.get_manager(project_id)
