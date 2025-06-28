#!/usr/bin/env python3
"""
개선된 계획(Plan) 관리 명령어
ProjectContext와 dict 모두 지원하는 유연한 구조
"""

import os
import datetime as dt
from pathlib import Path
from typing import Dict, Any, Optional, Union, List

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from core.context_manager import get_context_manager
from core.workflow_manager import get_workflow_manager
from core.error_handler import StandardResponse
from core.models import TaskStatus
from analyzers.project_analyzer import ProjectAnalyzer

# Wisdom 시스템 통합
from project_wisdom import get_wisdom_manager
from wisdom_hooks import get_wisdom_hooks



# 자동 작업 생성 템플릿
AUTO_TASK_TEMPLATES = {
    "분석 및 설계": [
        "현재 코드베이스 분석",
        "개선 필요 영역 식별",
        "아키텍처 설계 문서 작성",
        "API 설계 검토"
    ],
    "구현": [
        "핵심 기능 구현",
        "유닛 테스트 작성",
        "통합 테스트 작성",
        "리팩토링"
    ],
    "테스트 및 배포": [
        "전체 테스트 실행",
        "성능 테스트",
        "문서화 작성",
        "배포 준비"
    ],
    "문서화": [
        "README 작성/업데이트",
        "API 문서 생성",
        "사용자 가이드 작성",
        "변경 로그 업데이트"
    ]
}

def get_plan(context) -> Optional[Union[Dict, Any]]:
    """context에서 plan을 안전하게 가져오기"""
    if hasattr(context, 'plan'):
        return context.plan
    elif isinstance(context, dict):
        return context.get('plan')
    elif hasattr(context, 'metadata') and context.metadata:
        return context.metadata.get('plan')
    return None


def set_plan(context, plan_data: Dict):
    """context에 plan을 안전하게 설정
    
    Returns:
        tuple: (성공여부, 에러메시지)
    """
    # helpers 전역 변수 사용
    helpers = globals().get('helpers', None)
    
    # helpers 검증
    if not helpers:
        try:
            # helpers가 없으면 get_context_manager에서 가져오기 시도
            from core.context_manager import get_context_manager
            cm = get_context_manager()
            if hasattr(cm, 'helpers'):
                helpers = cm.helpers
            else:
                return False, "helpers not available in context_manager"
        except Exception as e:
            return False, f"Failed to get helpers: {str(e)}"
    
    if hasattr(context, 'plan'):
        # Plan 객체로 변환 시도
        try:
            from core.models import Plan, Phase
            phases = {}
            for phase_id, phase_data in plan_data.get('phases', {}).items():
                if isinstance(phase_data, dict):
                    phases[phase_id] = Phase(**phase_data)
            
            plan_obj = Plan(
                name=plan_data['name'],
                description=plan_data['description'],
                phases=phases,
                current_phase=plan_data.get('current_phase'),
                current_task=plan_data.get('current_task')
            )
            context.plan = plan_obj
            
            # 캐시도 업데이트
            if helpers:
                helpers.update_cache('plan', plan_obj)
            
            # context_manager 저장 시도
            try:
                from core.context_manager import get_context_manager
                get_context_manager().save()
                return True, None
            except Exception as e:
                # 저장 실패해도 설정은 성공
                print(f"⚠️ Context 저장 실패: {e}")
                return True, f"Plan set but save failed: {str(e)}"
        except Exception as e:
            # Plan 객체 변환 실패시 metadata에 저장
            import traceback
            error_detail = f"Plan object conversion failed: {str(e)}"
            if not hasattr(context, 'metadata'):
                return False, "Context has no metadata attribute"
            if not context.metadata:
                context.metadata = {}
            context.metadata['plan'] = plan_data
            
            # 캐시도 업데이트
            if helpers:
                helpers.update_cache('plan', plan_data)
            
            # context_manager 저장
            try:
                from core.context_manager import get_context_manager
                get_context_manager().save()
                return True, None
            except Exception as save_e:
                return True, f"Plan set in metadata but save failed: {str(save_e)}"
    elif isinstance(context, dict):
        context['plan'] = plan_data
        
        # 캐시도 업데이트
        if helpers:
            try:
                helpers.update_cache('plan', plan_data)
            except Exception as cache_e:
                print(f"⚠️ Cache update failed: {cache_e}")
        
        # context_manager 저장
        try:
            from core.context_manager import get_context_manager
            get_context_manager().save()
            return True, None
        except Exception as save_e:
            return True, f"Plan set in dict but save failed: {str(save_e)}"
    else:
        return False, f"Unknown context type: {type(context)}"


def plan_to_dict(plan) -> Dict:
    """Plan 객체를 dictionary로 변환"""
    if isinstance(plan, dict):
        return plan
    
    # Plan 객체인 경우
    result = {
        'name': getattr(plan, 'name', ''),
        'description': getattr(plan, 'description', ''),
        'created_at': str(getattr(plan, 'created_at', dt.datetime.now())),
        'updated_at': str(getattr(plan, 'updated_at', dt.datetime.now())),
        'current_phase': getattr(plan, 'current_phase', None),
        'current_task': getattr(plan, 'current_task', None),
        'phases': {}
    }
    
    # phases 변환
    if hasattr(plan, 'phases'):
                    for phase_id, phase in plan.phases.items():
                            phase_tasks = list(phase.tasks.values()) if hasattr(phase.tasks, 'values') else phase.tasks
                            if phase_tasks:
                                completed = len([t for t in phase_tasks if t.status == TaskStatus.COMPLETED])
                                progress = (completed / len(phase_tasks)) * 100
                                icon = "✅" if progress == 100 else ("🔄" if progress > 0 else "⏳")
                                print(f"{icon} {phase.name}: {progress:.0f}% ({completed}/{len(phase_tasks)})")
                                
                                # 🆕 완료된 작업의 content 표시
                                completed_tasks = [t for t in phase_tasks if t.status == TaskStatus.COMPLETED and hasattr(t, 'content') and t.content]
                                if completed_tasks:
                                    print("   📝 완료된 작업 내용:")
                                    for task in completed_tasks[:3]:  # 최대 3개만 표시
                                        content_preview = task.content[:80] + "..." if len(task.content) > 80 else task.content
                                        print(f"      • {task.title}: {content_preview}")
                                    if len(completed_tasks) > 3:
                                        print(f"      ... 외 {len(completed_tasks)-3}개 작업")
                            else:
                                print(f"⏳ {phase.name}: 작업 없음")
                    
            # 분석 정보
            analytics = wm.get_task_analytics()
            if analytics['average_completion_time']:
                print(f"\n📈 평균 작업 완료 시간: {analytics['average_completion_time']}")
                
            return StandardResponse.success(
                data={
                    'plan': plan.dict(),
                    'status': status,
                    'analytics': analytics
                }
            )
            
    except Exception as e:
        from core.error_handler import ErrorType
        return StandardResponse.error(ErrorType.PLAN_ERROR, f"계획 처리 중 오류: {str(e)}")
if __name__ == "__main__":
    # 명령줄 인자 처리
    import sys
    if len(sys.argv) > 1:
        plan_name = sys.argv[1]
        description = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else None
        cmd_plan(plan_name, description)
    else:
        cmd_plan()
