"""
AI Helpers - 통합 헬퍼 모듈 v13.0
강화된 에러 처리와 복구 메커니즘 포함
"""
import importlib
import logging
import sys
import os
from typing import Dict, Any, List, Optional

# 로깅 설정
logger = logging.getLogger("ai_helpers")
handler = logging.StreamHandler()
formatter = logging.Formatter('[%(levelname)s] %(name)s: %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# 필수 모듈 정의
REQUIRED_MODULES = ["helper_result", "search", "file", "git", "workflow"]
OPTIONAL_MODULES = ["compile", "build", "code", "context", "project", "utils", "legacy_replacements"]

# 로드 상태 추적
_load_status: Dict[str, Dict[str, Any]] = {}
_failed_modules: List[str] = []

def _try_import_module(module_name: str, required: bool = False) -> Optional[Any]:
    """모듈 import 시도 with 상세 에러 로깅"""
    try:
        mod = importlib.import_module(f".{module_name}", __name__)
        _load_status[module_name] = {"status": "loaded", "module": mod}

        # 모듈의 __all__ 속성에 정의된 것들만 export
        if hasattr(mod, '__all__'):
            for name in mod.__all__:
                if hasattr(mod, name):
                    globals()[name] = getattr(mod, name)
        else:
            # __all__이 없으면 _로 시작하지 않는 모든 것 export
            for name in dir(mod):
                if not name.startswith('_'):
                    attr = getattr(mod, name)
                    globals()[name] = attr

        logger.info(f"✅ {module_name} 모듈 로드 성공")
        return mod

    except ImportError as e:
        _load_status[module_name] = {"status": "failed", "error": str(e)}
        _failed_modules.append(module_name)

        if required:
            logger.error(f"❌ 필수 모듈 {module_name} 로드 실패: {e}")
            raise
        else:
            logger.warning(f"⚠️ 선택적 모듈 {module_name} 로드 실패: {e}")
            return None
    except Exception as e:
        _load_status[module_name] = {"status": "error", "error": str(e)}
        _failed_modules.append(module_name)
        logger.error(f"❌ {module_name} 로드 중 예상치 못한 오류: {e}")
        if required:
            raise
        return None

# 1. 필수 모듈 로드 (실패 시 ImportError 발생)
logger.info("=== AI Helpers 초기화 시작 ===")

for module in REQUIRED_MODULES:
    _try_import_module(module, required=True)

# 2. 선택적 모듈 로드 (실패해도 계속 진행)
for module in OPTIONAL_MODULES:
    _try_import_module(module, required=False)

# 3. 특수 처리가 필요한 모듈들
try:
    # enhanced_flow의 cmd_flow_with_context
    import sys
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    from enhanced_flow import cmd_flow_with_context as _flow_cmd

    # flow_project 함수 래핑
    def flow_project(project_name: str) -> Dict[str, Any]:
        """프로젝트 전환 (안정화된 버전)"""
        try:
            result = _flow_cmd(project_name)
            return HelperResult(ok=True, data=result, error=None)
        except Exception as e:
            logger.error(f"flow_project 실행 실패: {e}")
            return HelperResult(ok=False, data=None, error=str(e))

    globals()['flow_project'] = flow_project
    logger.info("✅ flow_project 함수 등록 완료")

except Exception as e:
    logger.warning(f"⚠️ enhanced_flow 연동 실패: {e}")

# 4. search_wrappers 통합
try:
    from . import search_wrappers as _sw
    if hasattr(_sw, '__all__'):
        for name in _sw.__all__:
            if hasattr(_sw, name):
                globals()[name] = getattr(_sw, name)
        logger.info(f"✅ search_wrappers 통합 완료 ({len(_sw.__all__)}개 함수)")
except Exception as e:
    logger.warning(f"⚠️ search_wrappers 로드 실패: {e}")

# 5. 로드 상태 확인 함수
def get_load_status() -> Dict[str, Any]:
    """모듈 로드 상태 반환"""
    return {
        "loaded": [k for k, v in _load_status.items() if v["status"] == "loaded"],
        "failed": _failed_modules,
        "details": _load_status
    }

def reload_failed_modules() -> Dict[str, bool]:
    """실패한 모듈 재로드 시도"""
    results = {}
    for module in _failed_modules[:]:  # 복사본으로 순회
        try:
            _try_import_module(module, required=False)
            if _load_status[module]["status"] == "loaded":
                _failed_modules.remove(module)
                results[module] = True
            else:
                results[module] = False
        except Exception:
            results[module] = False
    return results

# 6. __all__ 정의 (동적으로 생성)
__all__ = []
for name in dir():
    if not name.startswith('_') and name not in ['importlib', 'logging', 'sys', 'os']:
        __all__.append(name)

# 초기화 완료 로그
logger.info(f"=== AI Helpers 초기화 완료 ===")
logger.info(f"로드된 모듈: {len([m for m in _load_status if _load_status[m]['status'] == 'loaded'])}개")
logger.info(f"실패한 모듈: {len(_failed_modules)}개")
if _failed_modules:
    logger.warning(f"실패 모듈 목록: {', '.join(_failed_modules)}")
