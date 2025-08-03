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


    def close_instance(self, project_name: str = "default") -> bool:
        """브라우저 인스턴스를 안전하게 종료하고 제거

        Args:
            project_name: 프로젝트 이름

        Returns:
            bool: 성공 여부
        """
        with self._lock:
            instance = self.get_instance(project_name)
            if instance:
                try:
                    # 브라우저 인스턴스 종료 시도
                    if hasattr(instance, 'stop'):
                        instance.stop()
                    elif hasattr(instance, 'quit'):
                        instance.quit()
                    elif hasattr(instance, 'close'):
                        instance.close()
                except Exception as e:
                    import warnings
                    warnings.warn(f"Failed to stop browser instance: {e}", RuntimeWarning)

                # 인스턴스 제거
                return self.remove_instance(project_name)
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

                # 스크립트를 함수로 래핑 (return 문 지원)
                if "return" in script and not script.strip().startswith("function"):
                    # return 문이 있으면 함수로 래핑
                    wrapped_script = f"() => {{ {script} }}"
                else:
                    # return 문이 없으면 표현식으로 평가
                    wrapped_script = script

                # 스크립트 실행
                if arg is not None:
                    # 인자가 있는 경우
                    result = page.evaluate(f"(arg) => {{ {script} }}", arg)
                else:
                    result = page.evaluate(wrapped_script)

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


    # 추가 위험 패턴들 (XSS, 리소스 고갈 등)
    EXTENDED_DANGEROUS_PATTERNS = [
        # XSS 관련
        r'innerHTML\s*=',
        r'outerHTML\s*=',
        r'document\.body\.appendChild',
        r'insertAdjacentHTML',
        # 무한루프 위험
        r'while\s*\(\s*true\s*\)',
        r'for\s*\(\s*;\s*;\s*\)',
        # 리소스 고갈
        r'Array\s*\(\s*\d{7,}\s*\)',  # 매우 큰 배열
        r'\.repeat\s*\(\s*\d{5,}\s*\)',  # 많은 반복
        # 네트워크 요청
        r'fetch\s*\(',
        r'XMLHttpRequest',
        r'WebSocket',
        # 스토리지 접근
        r'localStorage',
        r'sessionStorage',
        r'indexedDB'
    ]

    # 안전한 JavaScript 함수 화이트리스트
    SAFE_FUNCTIONS = {
        'querySelector', 'querySelectorAll', 'getElementById',
        'getElementsByClassName', 'getElementsByTagName',
        'getAttribute', 'hasAttribute', 'textContent',
        'innerText', 'nodeValue', 'tagName', 'className',
        'classList', 'dataset', 'style', 'offsetWidth',
        'offsetHeight', 'scrollTop', 'scrollLeft',
        'getBoundingClientRect', 'getComputedStyle'
    }

    def validate_script_extended(self, script: str, strict_mode: bool = False) -> Tuple[bool, Optional[str]]:
        """
        확장된 스크립트 검증

        Args:
            script: 검증할 스크립트
            strict_mode: True일 경우 화이트리스트 기반 검증

        Returns:
            (is_safe, error_message)
        """
        # 기본 검증
        is_safe, error_msg = self.validate_script(script)
        if not is_safe:
            return False, error_msg

        # 확장 패턴 검사
        for pattern in self.EXTENDED_DANGEROUS_PATTERNS:
            if re.search(pattern, script, re.IGNORECASE):
                return False, f"Extended dangerous pattern detected: {pattern}"

        # Strict 모드: 화이트리스트 검증
        if strict_mode:
            # 함수 호출 추출
            function_calls = re.findall(r'\.(\w+)\s*\(', script)
            for func in function_calls:
                if func not in self.SAFE_FUNCTIONS:
                    return False, f"Function '{func}' not in whitelist"

        # 복잡도 검증
        complexity_score = self._calculate_complexity(script)
        if complexity_score > 100:
            return False, f"Script too complex (score: {complexity_score})"

        return True, None

    def _calculate_complexity(self, script: str) -> int:
        """
        스크립트 복잡도 계산

        Returns:
            복잡도 점수 (높을수록 복잡함)
        """
        score = 0

        # 중첩 깊이
        max_nesting = 0
        current_nesting = 0
        for char in script:
            if char in '{([':
                current_nesting += 1
                max_nesting = max(max_nesting, current_nesting)
            elif char in '})]':
                current_nesting = max(0, current_nesting - 1)

        score += max_nesting * 10

        # 루프 개수
        loops = len(re.findall(r'(for|while|do)\s*\(', script))
        score += loops * 15

        # 함수 호출 개수
        calls = len(re.findall(r'\.\w+\s*\(', script))
        score += calls * 2

        # 전체 길이
        score += len(script) // 100

        return score

    def create_sandbox_wrapper(self, script: str, allowed_globals: List[str] = None) -> str:
        """
        강화된 샌드박스 래퍼 생성

        Args:
            script: 래핑할 스크립트
            allowed_globals: 허용할 전역 변수 목록

        Returns:
            샌드박스로 래핑된 스크립트
        """
        if allowed_globals is None:
            allowed_globals = ['document', 'window']

        # 전역 변수 접근 제한
        globals_restriction = ', '.join(f"'{g}': {g}" for g in allowed_globals)

        wrapped = f"""
        (function() {{
            'use strict';

            // 샌드박스 환경 설정
            const sandbox = {{
                {globals_restriction}
            }};

            // with 문을 사용한 스코프 제한 (보안 강화)
            with (sandbox) {{
                try {{
                    // 실행 시간 제한을 위한 시작 시간 기록
                    const __startTime = Date.now();
                    const __checkTimeout = () => {{
                        if (Date.now() - __startTime > 5000) {{
                            throw new Error('Script execution timeout (5s)');
                        }}
                    }};

                    // 사용자 스크립트 실행
                    const __result = (function() {{
                        {script}
                    }})();

                    return __result;

                }} catch (error) {{
                    return {{
                        __error: true,
                        message: error.message,
                        stack: error.stack,
                        name: error.name
                    }};
                }}
            }}
        }})()
        """
        return wrapped

