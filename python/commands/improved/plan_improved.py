#!/usr/bin/env python3
"""
개선된 계획(Plan) 관리 명령어
ProjectContext와 dict 모두 지원하는 유연한 구조
"""

import os
import json
import datetime as dt
from pathlib import Path
from typing import Dict, Any, Optional, Union

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from core.context_manager import get_context_manager
from core.config import get_paths_from_config


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
    """context에 plan을 안전하게 설정"""
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
            return True
        except:
            # 실패시 metadata에 저장
            if not hasattr(context, 'metadata'):
                return False
            if not context.metadata:
                context.metadata = {}
            context.metadata['plan'] = plan_data
            return True
    elif isinstance(context, dict):
        context['plan'] = plan_data
        return True
    return False


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
            if isinstance(phase, dict):
                result['phases'][phase_id] = phase
            else:
                # Phase 객체를 dict로 변환
                result['phases'][phase_id] = {
                    'id': getattr(phase, 'id', phase_id),
                    'name': getattr(phase, 'name', ''),
                    'description': getattr(phase, 'description', ''),
                    'status': getattr(phase, 'status', 'pending'),
                    'tasks': getattr(phase, 'tasks', [])
                }
    
    return result


def cmd_plan(plan_name: Optional[str] = None, description: Optional[str] = None) -> None:
    """새로운 계획 수립 또는 현재 계획 조회"""
    
    # helpers 전역 변수 사용
    helpers = globals().get('helpers', None)
    context = get_context_manager().context
    
    # 인자가 없으면 현재 계획 표시
    if not plan_name:
        plan = get_plan(context)
        
        if not plan:
            print("❌ 수립된 계획이 없습니다. 'plan <계획명>'으로 새 계획을 생성하세요.")
            return
        
        # dict로 변환하여 일관된 처리
        plan_dict = plan_to_dict(plan)
        
        print(f"\n📋 현재 계획: {plan_dict['name']}")
        print(f"   설명: {plan_dict['description']}")
        print(f"   생성: {plan_dict.get('created_at', 'N/A')}")
        print(f"   현재 Phase: {plan_dict.get('current_phase', 'N/A')}")
        
        # Phase 목록 표시
        if plan_dict.get('phases'):
            print("\n📊 Phase 목록:")
            for phase_id, phase in plan_dict['phases'].items():
                tasks = phase.get('tasks', [])
                completed = sum(1 for t in tasks if t.get('status') == 'completed')
                status = "✅" if phase.get('status') == 'completed' else "🔄" if phase.get('status') == 'in_progress' else "⏳"
                print(f"   {status} {phase['name']} ({completed}/{len(tasks)} 완료)")
        return
    
    # 새 계획 생성
    print(f"\n🎯 새로운 계획 '{plan_name}' 수립 중...")
    
    timestamp = dt.datetime.now().isoformat()
    
    # 계획 데이터를 dictionary로 생성
    new_plan_dict = {
        'name': plan_name,
        'description': description or f"{get_context_manager().project_name} 작업 계획",
        'created_at': timestamp,
        'updated_at': timestamp,
        'phases': {},
        'current_phase': None,
        'current_task': None
    }
    
    # 기본 Phase 3개 생성
    default_phases = [
        ('phase-1', 'Phase 1: 분석 및 설계', '현재 상태 분석과 개선 방향 설계'),
        ('phase-2', 'Phase 2: 핵심 구현', '주요 기능 구현 및 개선'),
        ('phase-3', 'Phase 3: 테스트 및 문서화', '테스트 작성 및 문서 정리')
    ]
    
    for phase_id, phase_name, phase_desc in default_phases:
        new_plan_dict['phases'][phase_id] = {
            'id': phase_id,
            'name': phase_name,
            'description': phase_desc,
            'status': 'pending',
            'tasks': [],
            'created_at': timestamp,
            'updated_at': timestamp
        }
    
    new_plan_dict['current_phase'] = 'phase-1'
    
    # context에 plan 설정
    if set_plan(context, new_plan_dict):
        # plan_history 업데이트
        if hasattr(context, 'plan_history'):
            if not context.plan_history:
                context.plan_history = []
            context.plan_history.append({
                'name': plan_name,
                'created_at': timestamp,
                'id': f"plan-{len(context.plan_history) + 1}"
            })
        elif isinstance(context, dict):
            if 'plan_history' not in context:
                context['plan_history'] = []
            context['plan_history'].append({
                'name': plan_name,
                'created_at': timestamp,
                'id': f"plan-{len(context['plan_history']) + 1}"
            })
        
        # Phase 변경 (metadata 사용)
        if hasattr(context, 'metadata'):
            if not context.metadata:
                context.metadata = {}
            context.metadata['phase'] = 'planning'
        
        get_context_manager().save()
        
        print(f"\n✅ 새 계획 '{plan_name}' 생성 완료!")
        print(f"   설명: {new_plan_dict['description']}")
        print(f"\n   3개의 기본 Phase가 생성되었습니다:")
        for phase_id, phase_name, _ in default_phases:
            print(f"   - {phase_name}")
        
        print(f"\n💡 다음 단계:")
        print(f"   1. 'task add phase-1 \"작업명\"'으로 작업 추가")
        print(f"   2. 'next'로 작업 시작")
        print(f"   3. 'task done'으로 작업 완료")
    else:
        print("❌ 계획 저장 중 오류가 발생했습니다.")


if __name__ == "__main__":
    # 명령줄 인자 처리
    import sys
    if len(sys.argv) > 1:
        plan_name = sys.argv[1]
        description = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else None
        cmd_plan(plan_name, description)
    else:
        cmd_plan()
