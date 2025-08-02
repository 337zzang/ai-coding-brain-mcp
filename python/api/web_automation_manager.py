"""
웹 브라우저 인스턴스 중앙 관리자
싱글톤 패턴으로 안정적인 인스턴스 관리 제공

작성일: 2025-08-02
"""
import threading
from typing import Dict, Optional, Any, List
from datetime import datetime


class BrowserManager:
    """
    브라우저 인스턴스를 중앙에서 관리하는 싱글톤 클래스

    특징:
    - 스레드 안전성 보장
    - 프로젝트별 인스턴스 격리
    - 생명주기 관리
    - 디버깅 정보 제공
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        with self._lock:
            if not self._initialized:
                self._browser_instances: Dict[str, Any] = {}
                self._instance_metadata: Dict[str, Dict[str, Any]] = {}
                self._initialized = True

    def set_instance(self, instance: Any, project_name: str = "default") -> None:
        """브라우저 인스턴스 등록"""
        with self._lock:
            self._browser_instances[project_name] = instance
            self._instance_metadata[project_name] = {
                "created_at": datetime.now(),
                "type": type(instance).__name__,
                "active": True
            }

    def get_instance(self, project_name: str = "default") -> Optional[Any]:
        """브라우저 인스턴스 조회"""
        with self._lock:
            instance = self._browser_instances.get(project_name)
            if instance and self._instance_metadata.get(project_name, {}).get("active", False):
                return instance
            return None

    def remove_instance(self, project_name: str = "default") -> bool:
        """브라우저 인스턴스 제거"""
        with self._lock:
            if project_name in self._browser_instances:
                # 메타데이터 업데이트
                if project_name in self._instance_metadata:
                    self._instance_metadata[project_name]["active"] = False
                    self._instance_metadata[project_name]["closed_at"] = datetime.now()

                # 인스턴스 제거
                del self._browser_instances[project_name]
                return True
            return False

    def list_instances(self) -> List[Dict[str, Any]]:
        """활성 인스턴스 목록 조회"""
        with self._lock:
            instances = []
            for project, metadata in self._instance_metadata.items():
                if metadata.get("active", False):
                    instances.append({
                        "project": project,
                        "type": metadata.get("type"),
                        "created_at": metadata.get("created_at"),
                        "instance": project in self._browser_instances
                    })
            return instances

    def clear_all(self) -> int:
        """모든 인스턴스 정리 (테스트/종료 시 사용)"""
        with self._lock:
            count = len(self._browser_instances)
            self._browser_instances.clear()
            for project in self._instance_metadata:
                self._instance_metadata[project]["active"] = False
                self._instance_metadata[project]["closed_at"] = datetime.now()
            return count

    def get_stats(self) -> Dict[str, Any]:
        """관리 통계 조회"""
        with self._lock:
            return {
                "active_instances": len([m for m in self._instance_metadata.values() if m.get("active")]),
                "total_created": len(self._instance_metadata),
                "projects": list(self._browser_instances.keys())
            }


# 전역 매니저 인스턴스 (import 시 자동 생성)
browser_manager = BrowserManager()
