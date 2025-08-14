from typing import Dict, Any, Optional, List
import pprint
import html
from functools import wraps

"""
AI Helpers 표준화 래퍼
기존 함수를 수정하지 않고 표준 API 패턴 제공
"""
from .core.fs import scan_directory as core_scan_directory, ScanOptions
from .util import safe_get_data, get_list_items


# ==================================================
# REPL 최적화를 위한 HelperResult 클래스 (v1.0)
# Added: 2025-08-11
# ==================================================


class HelperResult(dict):
    """
    AI Helper 표준 응답 객체 (REPL 최적화 버전)

    dict를 상속받아 완벽한 하위 호환성을 유지하면서,
    REPL 환경에서 'data' 필드만 깔끔하게 출력되도록 합니다.

    Example:
        >>> result = HelperResult({'ok': True, 'data': ['file1.py', 'file2.py']})
        >>> result  # REPL에서 data만 출력
        ['file1.py', 'file2.py']
        >>> result['ok']  # dict처럼 사용 가능
        True
    """

    def __repr__(self):
        """REPL에서의 표현 (data 필드만 깔끔하게)"""
        return self._formatted_output()

    def __str__(self):
        """문자열 변환 시 표현"""
        return self._formatted_output()

    def _formatted_output(self):
        """포맷팅된 출력 생성 - 개선된 버전"""
        if self.get('ok'):
            data = self.get('data')
            if data is None:
                # 성공했지만 데이터가 없는 경우 (예: write 작업)
                return "✅ Success"

            # 데이터 타입별 최적화된 출력
            try:
                if isinstance(data, list):
                    if len(data) == 0:
                        return "✅ [] (empty)"
                    elif len(data) <= 5:
                        # 5개 이하는 전체 표시
                        return pprint.pformat(data, indent=2, width=120)
                    else:
                        # 많은 항목은 요약 표시
                        preview = data[:3]
                        return f"✅ [{len(data)} items] {pprint.pformat(preview, indent=2, width=80)}..."
                
                elif isinstance(data, dict):
                    if len(data) == 0:
                        return "✅ {} (empty)"
                    elif len(data) <= 3:
                        # 3개 이하 키는 전체 표시
                        return pprint.pformat(data, indent=2, width=120)
                    else:
                        # 많은 키는 요약 표시
                        keys = list(data.keys())[:3]
                        preview = {k: data[k] for k in keys}
                        return f"✅ [{len(data)} keys] {pprint.pformat(preview, indent=2, width=80)}..."
                
                elif isinstance(data, str):
                    if len(data) <= 100:
                        return f"✅ {repr(data)}"
                    else:
                        return f"✅ {repr(data[:100])}... ({len(data)} chars)"
                
                else:
                    # 기타 타입 (bool, int, etc.)
                    return f"✅ {repr(data)}"
                    
            except Exception:
                # pprint 실패 시 기본 처리
                return f"✅ {repr(data)}"
        else:
            # 실패 시 에러 메시지 출력
            error = self.get('error', 'Unknown error')
            error_type = self.get('error_type', '')
            if error_type:
                return f"❌ [{error_type}] {error}"
            return f"❌ {error}"

    def _repr_html_(self):
        """Jupyter 노트북 등에서의 리치 디스플레이 지원"""
        if self.get('ok'):
            data = self.get('data')
            if data is None:
                return "<div style='color: green;'>✅ <b>Success</b> (No data returned)</div>"

            # HTML 형식으로 출력
            formatted = self._formatted_output()
            escaped = html.escape(formatted)
            return f"<pre style='background: #f5f5f5; padding: 10px;'>{escaped}</pre>"
        else:
            error = html.escape(self.get('error', 'Unknown error'))
            return f"<div style='color: red;'>❌ <b>Error:</b> {error}</div>"

    def as_dict(self):
        """일반 dict로 변환 (필요시 사용)"""
        return dict(self)

    def to_json(self):
        """JSON 직렬화를 위한 메서드"""
        import json
        return json.dumps(dict(self), ensure_ascii=False)





# ==================================================
# safe_execution 데코레이터 및 헬퍼 함수들 (v1.0)
# Added: 2025-08-11
# ==================================================

import functools
from typing import Any, Optional

def wrap_output(func):
    """함수 출력을 표준 응답 형식으로 래핑하는 데코레이터
    
    모든 반환값을 {'ok': True/False, 'data': ..., 'error': ...} 형태로 변환합니다.
    """
    import functools
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            # 이미 표준 응답인 경우 그대로 반환
            if isinstance(result, dict) and 'ok' in result:
                return result
            # 아니면 성공 응답으로 래핑
            return {'ok': True, 'data': result}
        except Exception as e:
            return {'ok': False, 'error': str(e), 'data': None}
    return wrapper


def ensure_response(data: Any, error: str = None, **extras) -> HelperResult:
    """모든 데이터를 표준 응답 형식(HelperResult)으로 변환

    Args:
        data: 반환할 데이터
        error: 에러 메시지 (있는 경우)
        **extras: 추가 메타데이터

    Returns:
        HelperResult: 표준 응답 형식 (REPL 최적화)
    """
    if error:
        # 에러 응답을 HelperResult로 생성
        error_info = HelperResult({'ok': False, 'error': error, 'data': None})
        # exception 객체가 전달된 경우 타입 정보 추가
        if 'exception' in extras:
            exc = extras.pop('exception')
            error_info['error_type'] = type(exc).__name__
        error_info.update(extras)
        return error_info

    # 이미 표준 응답이지만 HelperResult가 아닌 경우 변환
    if isinstance(data, dict) and 'ok' in data and not isinstance(data, HelperResult):
        response = HelperResult(data)
        if extras:
            response.update(extras)
        return response

    # 이미 HelperResult인 경우
    if isinstance(data, HelperResult):
        if extras:
            data.update(extras)
        return data

    # Boolean False는 실패로 처리 (개선됨)
    if isinstance(data, bool) and not data:
        error_response = HelperResult({'ok': False, 'error': 'Operation failed', 'data': data})
        error_response.update(extras)
        return error_response

    # 일반 데이터는 성공 응답으로 생성
    response = HelperResult({'ok': True, 'data': data})
    response.update(extras)
    return response
def safe_execution(func):
    """함수 실행을 안전하게 래핑하고 HelperResult를 반환하는 데코레이터

    모든 AI Helper 함수에 적용되는 표준 래퍼입니다.
    예외를 잡아서 HelperResult 형태로 변환합니다.
    """
    if not callable(func):
        return func

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            # ensure_response를 통해 HelperResult로 변환 보장
            return ensure_response(result)
        except Exception as e:
            # 에러 발생 시 HelperResult 반환
            return ensure_response(
                None, 
                str(e), 
                exception=e,
                function=func.__name__,
                args=args,
                kwargs=list(kwargs.keys()) if kwargs else []
            )
    return wrapper
def scan_directory(path: str = '.', 
                  max_depth: Optional[int] = None,
                  output: str = 'list') -> Dict[str, Any]:
    """
    통합 디렉토리 스캔

    Args:
        path: 스캔할 경로
        max_depth: 최대 깊이 (None = 전체)
        output: 'list' | 'dict' | 'tree'

    Returns:
        {'ok': True, 'data': [...], 'count': N, 'path': path}
    """
    try:
        if output == 'list':
            # 기존 방식 - core 사용
            options = ScanOptions(output="flat", max_depth=max_depth)
            result = core_scan_directory(path, options=options)
            if result["ok"]:
                return ensure_response(result["data"], count=len(result["data"]), path=path)
            else:
                return ensure_response(None, error=result.get("error", "Unknown error"), path=path)

        elif output == 'dict':
            # 동적 import로 순환 참조 방지
            from .project import scan_directory_dict as _scan_directory_dict
            # 기존 scan_directory_dict 활용
            data = _scan_directory_dict(path, max_depth or 5)
            return ensure_response(data, path=path)

        else:  # tree 등 추가 형식
            return ensure_response([], count=0, path=path)

    except Exception as e:
        return ensure_response(None, error=str(e), path=path)
def scan_directory_dict(path: str = '.', max_depth: int = 3) -> Dict[str, Any]:
    """DEPRECATED: Use h.scan_directory(path, output='dict') instead

    이 함수는 곧 제거될 예정입니다.
    h.scan_directory(path, max_depth=max_depth, output='dict')를 사용하세요.
    """
    import warnings
    warnings.warn(
        "scan_directory_dict is deprecated. Use h.scan_directory(output='dict')",
        DeprecationWarning,
        stacklevel=2
    )
    return h.scan_directory(path, max_depth=max_depth, output='dict')
def get_current_project() -> Dict[str, Any]:
    """현재 프로젝트 정보 반환 (안전 버전)

    Returns:
        {'ok': bool, 'data': dict} - 프로젝트 정보 또는 에러
    """
    try:
        # 동적 import로 순환 참조 방지
        from .project import get_current_project as _get_current_project
        project = _get_current_project()
        if not project:
            return ensure_response(None, error='No project selected')
        return ensure_response(project)
    except Exception as e:
        return ensure_response(None, error=str(e))
# 하위 호환성을 위한 별칭
safe_scan_directory = scan_directory
safe_scan_directory_dict = scan_directory_dict
safe_get_current_project = get_current_project


# Execute_code 문제 해결을 위한 헬퍼 함수들

def fix_task_numbers(plan_id: str) -> Dict[str, Any]:
    """기존 Task들의 누락된 number 필드 복구

    Args:
        plan_id: 플랜 ID

    Returns:
        표준 응답 형식 {"ok": bool, "data": dict, "error": str}
    """
    try:
        from .flow_api import get_flow_api
        api = get_flow_api()
        tasks_result = api.list_tasks(plan_id)

        if not tasks_result['ok']:
            return {"ok": False, "data": None, "error": tasks_result['error']}

        tasks = tasks_result['data']
        fixed_count = 0

        # number가 None인 Task들 찾아서 수정
        for i, task in enumerate(tasks, 1):
            if task.get('number') is None:
                update_result = api.update_task(plan_id, task['id'], number=i)
                if update_result['ok']:
                    fixed_count += 1

        return {
            "ok": True,
            "data": {
                "total_tasks": len(tasks),
                "fixed_count": fixed_count,
                "message": f"Fixed {fixed_count} tasks with missing numbers"
            },
            "error": None
        }
    except Exception as e:
        return {"ok": False, "data": None, "error": str(e)}


def validate_flow_response(response: Any, method_name: str = "") -> bool:
    """FlowAPI 응답 검증 헬퍼

    Args:
        response: API 응답
        method_name: 메서드 이름 (디버깅용)

    Returns:
        응답이 표준 형식인지 여부
    """
    if isinstance(response, dict) and 'ok' in response:
        return True

    # 체이닝 메서드들은 FlowAPI 객체 반환
    chaining_methods = ['select_plan', 'set_context', 'clear_context']
    if method_name in chaining_methods:
        return hasattr(response, '__class__') and response.__class__.__name__ == 'FlowAPI'

    return False


def get_task_safe(plan_id: str, task_id: str) -> Dict[str, Any]:
    """Task 데이터를 안전하게 가져오기 (title 필드 보장)

    Args:
        plan_id: 플랜 ID
        task_id: Task ID

    Returns:
        표준 응답 형식, data에 정규화된 Task 정보
    """
    try:
        from .flow_api import get_flow_api
        api = get_flow_api()
        result = api.get_task(plan_id, task_id)

        if not result['ok']:
            return result

        task = result['data']

        # title 필드 확인 및 정규화
        if 'title' not in task and 'name' in task:
            task['title'] = task['name']
        elif 'title' not in task:
            task['title'] = f"Task {task.get('id', 'Unknown')}"

        # number 필드 확인
        if task.get('number') is None:
            # ID에서 추출 시도
            try:
                task_id_parts = task['id'].split('_')
                if len(task_id_parts) >= 3:
                    task['number'] = int(task_id_parts[2][:6])
            except:
                task['number'] = None

        return {"ok": True, "data": task, "error": None}
    except Exception as e:
        return {"ok": False, "data": None, "error": str(e)}


def git_status_normalized() -> Dict[str, Any]:
    """정규화된 Git 상태 반환 (modified, added, deleted 필드 추가)

    Returns:
        표준 응답 형식, data에 확장된 Git 정보
    """
    try:
        from .git import git_status
        result = git_status()
        if not result['ok']:
            return result

        data = result['data']
        files = data.get('files', [])

        # 파일 분류
        modified = []
        added = []
        deleted = []

        for file_info in files:
            if isinstance(file_info, str):
                # 문자열 형태의 파일 정보 파싱
                parts = file_info.split()
                if len(parts) >= 2:
                    status = parts[0]
                    filepath = ' '.join(parts[1:])

                    if status == 'M':
                        modified.append(filepath)
                    elif status == 'A' or status == '??':
                        added.append(filepath)
                    elif status == 'D':
                        deleted.append(filepath)

        # 확장된 데이터 구조
        data['modified'] = modified
        data['added'] = added
        data['deleted'] = deleted

        return {"ok": True, "data": data, "error": None}
    except Exception as e:
        return {"ok": False, "data": None, "error": str(e)}


# Excel 세션 상태 확인
def check_excel_session():
    """
    Excel 세션이 활성 상태인지 확인합니다.

    Returns:
        dict: 표준 응답 형식
            - ok: bool - 성공 여부
            - data: dict - 세션 정보 (active, workbook_name)
            - error: str or None
    """
    try:
        from . import excel
        manager = excel.get_excel_manager()

        if manager.excel and manager.workbook:
            return {
                "ok": True,
                "data": {
                    "active": True,
                    "workbook_name": manager.workbook.FullName,
                    "sheet_count": manager.workbook.Sheets.Count,
                    "active_sheet": manager.workbook.ActiveSheet.Name
                },
                "error": None
            }
        else:
            return {
                "ok": True,
                "data": {
                    "active": False,
                    "workbook_name": None,
                    "sheet_count": 0,
                    "active_sheet": None
                },
                "error": None
            }
    except ImportError:
        return {
            "ok": False,
            "data": {"active": False},
            "error": "Excel module not available (Windows only)"
        }
    except Exception as e:
        return {
            "ok": False,
            "data": {"active": False},
            "error": str(e)
        }

# 웹 자동화 세션 상태 확인
def check_web_session():
    """
    웹 자동화 브라우저 세션이 활성 상태인지 확인합니다.

    Returns:
        dict: 표준 응답 형식
            - ok: bool - 성공 여부
            - data: dict - 세션 정보 (active, url, title)
            - error: str or None
    """
    try:
        from . import web_automation_helpers as web

        # web_check_session이 있는지 확인
        if hasattr(web, 'web_check_session'):
            result = web.web_check_session()
            return result
        else:
            # 대체 방법: 브라우저 상태 직접 확인
            if hasattr(web, 'browser') and web.browser is not None:
                try:
                    current_url = web.browser.current_url
                    current_title = web.browser.title
                    return {
                        "ok": True,
                        "data": {
                            "active": True,
                            "url": current_url,
                            "title": current_title
                        },
                        "error": None
                    }
                except:
                    return {
                        "ok": True,
                        "data": {
                            "active": False,
                            "url": None,
                            "title": None
                        },
                        "error": None
                    }
            else:
                return {
                    "ok": True,
                    "data": {
                        "active": False,
                        "url": None,
                        "title": None
                    },
                    "error": None
                }
    except ImportError:
        return {
            "ok": False,
            "data": {"active": False},
            "error": "Web automation module not available"
        }
    except Exception as e:
        return {
            "ok": False,
            "data": {"active": False},
            "error": str(e)
        }

# 모든 세션 상태 한번에 확인
def check_all_sessions():
    """
    Excel과 웹 자동화 세션 상태를 모두 확인합니다.

    Returns:
        dict: 표준 응답 형식
            - ok: bool - 성공 여부
            - data: dict - 각 세션 정보
            - error: str or None
    """
    try:
        excel_status = check_excel_session()
        web_status = check_web_session()

        return {
            "ok": True,
            "data": {
                "excel": excel_status['data'],
                "web": web_status['data']
            },
            "error": None
        }
    except Exception as e:
        return {
            "ok": False,
            "data": None,
            "error": str(e)
        }


# ==================================================
# API 응답 표준화 래퍼 (v2.0)
# Added: 2025-08-14
# ==================================================

def standardize_api_response(func):
    """
    모든 API를 {'ok', 'data', 'error'} 플랫 구조로 통일
    
    중첩된 data 구조를 평탄화하고 일관된 응답 형식을 보장합니다.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            
            # 이미 표준 형식이면 확인 후 반환
            if isinstance(result, dict) and 'ok' in result:
                # 중첩된 data 구조 평탄화
                if 'data' in result and isinstance(result['data'], dict):
                    data = result['data']
                    # list_directory 형식 평탄화
                    if 'items' in data or 'entries' in data:
                        items = data.get('items') or data.get('entries', [])
                        return {'ok': True, 'data': items}
                    # 중첩된 data.data 구조 평탄화
                    if 'data' in data:
                        return {'ok': True, 'data': data['data']}
                return result
                
            # 비표준 형식 변환
            return {'ok': True, 'data': result}
            
        except Exception as e:
            return {'ok': False, 'data': None, 'error': str(e)}
    return wrapper

def safe_api_wrapper(func):
    """
    API 호출을 안전하게 래핑하고 표준 응답 보장
    
    KeyError나 AttributeError를 방지하고 일관된 응답을 제공합니다.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            
            # None 반환 처리
            if result is None:
                return {'ok': False, 'data': None, 'error': 'Function returned None'}
            
            # 표준화
            from .util import normalize_api_response
            return normalize_api_response(result)
            
        except (KeyError, AttributeError) as e:
            return {'ok': False, 'data': None, 'error': f'Data access error: {e}'}
        except Exception as e:
            return {'ok': False, 'data': None, 'error': str(e)}
    return wrapper

def flatten_list_directory_response(result):
    """
    list_directory 응답을 평탄화
    
    중첩된 data.items 구조를 data: [items] 형태로 변환
    """
    if not isinstance(result, dict) or not result.get('ok'):
        return result
        
    data = result.get('data', {})
    if isinstance(data, dict) and ('items' in data or 'entries' in data):
        items = data.get('items') or data.get('entries', [])
        return {
            'ok': True,
            'data': items,
            'metadata': {
                'path': data.get('path'),
                'count': data.get('count', len(items))
            }
        }
    return result