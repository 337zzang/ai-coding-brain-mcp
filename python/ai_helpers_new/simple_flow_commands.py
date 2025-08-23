"""
Simple Flow Commands - Flow 시스템 간편 명령어
Claude Code /flow 명령어와 연동
"""

from typing import Optional, Dict, Any, List
from .flow_api import FlowAPI

# Flow API 인스턴스 (싱글톤)
_flow_api = None

def get_flow_api() -> FlowAPI:
    """Flow API 싱글톤 인스턴스 반환"""
    global _flow_api
    if _flow_api is None:
        _flow_api = FlowAPI()
    return _flow_api

def flow_status() -> Dict[str, Any]:
    """Flow 시스템 현재 상태"""
    api = get_flow_api()
    stats = api.get_stats()
    plans = api.list_plans()

    return {
        'ok': True,
        'stats': stats.get('data', {}),
        'plans': plans.get('data', [])[:5],  # 최근 5개만
        'message': f"총 {stats.get('data', {}).get('total_plans', 0)}개 플랜"
    }

def flow_create(name: str, description: str = "") -> Dict[str, Any]:
    """새 플랜 생성"""
    api = get_flow_api()
    return api.create_plan(name, description)

def flow_add_task(plan_id: str, name: str, description: str = "") -> Dict[str, Any]:
    """플랜에 태스크 추가"""
    api = get_flow_api()
    return api.create_task(plan_id, name, description)

def flow_update_task(plan_id: str, task_id: str, status: str) -> Dict[str, Any]:
    """태스크 상태 업데이트"""
    api = get_flow_api()
    return api.update_task_status(plan_id, task_id, status)

def flow_get_plan(plan_id: str) -> Dict[str, Any]:
    """플랜 상세 정보"""
    api = get_flow_api()
    return api.get_plan(plan_id)

def flow_list_plans() -> Dict[str, Any]:
    """모든 플랜 목록"""
    api = get_flow_api()
    return api.list_plans()

def flow_quick_task(description: str) -> Dict[str, Any]:
    """빠른 태스크 생성 (현재 플랜에)"""
    api = get_flow_api()

    # 현재 플랜 가져오기
    current = api.get_current_plan()
    if not current.get('ok') or not current.get('data'):
        # 없으면 새 플랜 생성
        from datetime import datetime
        plan_name = f"Quick_{datetime.now().strftime('%Y%m%d')}"
        plan = api.create_plan(plan_name, "빠른 태스크를 위한 플랜")
        if plan.get('ok'):
            plan_id = plan['data']['id']
        else:
            return {'ok': False, 'error': '플랜 생성 실패'}
    else:
        plan_id = current['data']['id']

    # 태스크 추가
    return api.create_task(plan_id, description, "")

def help_flow():
    """Flow 시스템 도움말"""
    help_text = """
🧠 Flow 시스템 간편 명령어

Python에서 직접 사용:
    from ai_helpers_new import flow_status, flow_create, flow_add_task

    # 상태 확인
    status = flow_status()

    # 새 플랜 생성
    plan = flow_create("프로젝트명", "설명")

    # 태스크 추가
    task = flow_add_task(plan_id, "태스크명", "설명")

    # 빠른 태스크 (현재 플랜에 자동 추가)
    quick = flow_quick_task("할 일 내용")

Claude Code 슬래시 명령어:
    /flow              - 현재 상태
    /flow create       - 새 플랜 생성
    /flow task         - 태스크 추가
    /flow show         - 플랜 상세
    /flow help         - 도움말

API 직접 사용:
    import ai_helpers_new as h
    api = h.flow_api()
    """
    print(help_text)
    return {'ok': True, 'message': 'Flow 도움말 표시됨'}

# 편의 함수들을 __all__에 export
__all__ = [
    'get_flow_api',
    'flow_status',
    'flow_create',
    'flow_add_task',
    'flow_update_task',
    'flow_get_plan',
    'flow_list_plans',
    'flow_quick_task',
    'help_flow'
]
