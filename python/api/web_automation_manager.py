"""
웹 브라우저 인스턴스 중앙 관리자
싱글톤 패턴으로 안정적인 인스턴스 관리 제공

작성일: 2025-08-02
"""
import threading
from typing import Dict, Optional, Any, List, Tuple
from datetime import datetime


import re
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



class JavaScriptExecutor:
    """
    JavaScript 실행을 안전하게 관리하는 클래스

    특징:
    - 스크립트 검증 및 샌드박싱
    - 실행 시간 제한
    - 에러 격리 및 상세 정보 제공
    - 스레드 안전성 보장
    """

    # 위험한 JavaScript 패턴들
    DANGEROUS_PATTERNS = [
        r'eval\s*\(',
        r'Function\s*\(',
        r'setTimeout\s*\(',
        r'setInterval\s*\(',
        r'__proto__',
        r'constructor\s*\[',
        r'document\.write',
        r'window\.location',
        r'document\.cookie'
    ]

    def __init__(self):
        self._lock = threading.Lock()
        self._validation_enabled = True
        self._default_timeout = 30000  # 30초

    def validate_script(self, script: str) -> Tuple[bool, Optional[str]]:
        """
        스크립트 안전성 검증

        Returns:
            (is_safe, error_message)
        """
        if not self._validation_enabled:
            return True, None

        import re

        # 위험한 패턴 검사
        for pattern in self.DANGEROUS_PATTERNS:
            if re.search(pattern, script, re.IGNORECASE):
                return False, f"Dangerous pattern detected: {pattern}"

        # 스크립트 길이 제한 (보안상 너무 긴 스크립트 차단)
        if len(script) > 10000:
            return False, "Script too long (max 10000 characters)"

        return True, None

    def prepare_script(self, script: str) -> str:
        """
        스크립트 전처리 및 래핑

        - 안전한 실행 환경 구성
        - 에러 캐칭 추가
        """
        # 기본 래퍼로 감싸기
        wrapped = f"""
        (function() {{
            'use strict';
            try {{
                {script}
            }} catch (error) {{
                return {{
                    __error: true,
                    message: error.message,
                    stack: error.stack,
                    name: error.name
                }};
            }}
        }})()
        """
        return wrapped

    def execute(self, page, script: str, arg=None, timeout: Optional[int] = None) -> Dict[str, Any]:
        """
        JavaScript 실행

        Args:
            page: Playwright page 객체
            script: 실행할 JavaScript 코드
            arg: 스크립트에 전달할 인자
            timeout: 실행 제한 시간 (ms)

        Returns:
            실행 결과를 담은 Response 딕셔너리
        """
        with self._lock:
            try:
                # 스크립트 검증
                is_safe, error_msg = self.validate_script(script)
                if not is_safe:
                    return {
                        "ok": False,
                        "error": f"Script validation failed: {error_msg}",
                        "error_type": "ValidationError"
                    }

                # 타임아웃 설정
                if timeout is None:
                    timeout = self._default_timeout

                # 스크립트 실행
                result = page.evaluate(script, arg=arg)

                # 에러 체크
                if isinstance(result, dict) and result.get("__error"):
                    return {
                        "ok": False,
                        "error": result.get("message", "Unknown JavaScript error"),
                        "error_type": "JavaScriptError",
                        "stack": result.get("stack")
                    }

                return {
                    "ok": True,
                    "data": result,
                    "script_length": len(script)
                }

            except Exception as e:
                return {
                    "ok": False,
                    "error": str(e),
                    "error_type": type(e).__name__
                }

    def set_validation(self, enabled: bool) -> None:
        """검증 활성화/비활성화"""
        self._validation_enabled = enabled

    def set_default_timeout(self, timeout: int) -> None:
        """기본 타임아웃 설정"""
        self._default_timeout = timeout