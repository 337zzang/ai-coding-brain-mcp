#!/usr/bin/env python3
"""
계획(Plan) 관리 명령어
프로젝트의 Phase 기반 작업 계획을 수립하고 관리
"""

import os
import json
import datetime as dt
from pathlib import Path
from typing import Dict, Any, Optional

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.context_manager import get_context_manager
from core.config import get_paths_from_config
from core.models import Plan, Phase, Task  # Plan, Phase, Task 모델 import

def cmd_plan(plan_name: Optional[str] = None, description: Optional[str] = None) -> None:
    """새로운 계획 수립 또는 현재 계획 조회"""
    
    # helpers 전역 변수 사용
    helpers = globals().get('helpers', None)
    
    # 인자가 없으면 현재 계획 표시
    if not plan_name:
        # ProjectContext와 dict 모두 지원
        context = get_context_manager().context
        if hasattr(context, 'plan'):  # ProjectContext인 경우
            plan = context.plan
        else:  # dict인 경우
            plan = context.get('plan')
        
        if not plan:
            print("❌ 수립된 계획이 없습니다. 'plan <계획명>'으로 새 계획을 생성하세요.")
            return
            
        # Plan 객체와 dict 모두 지원
        if hasattr(plan, 'name'):  # Plan 객체
            print(f"\n📋 현재 계획: {plan.name}")
            print(f"   설명: {plan.description}")
            print(f"   생성: {plan.created_at}")
            print(f"   현재 Phase: {plan.current_phase}")
        else:  # dict
            print(f"\n📋 현재 계획: {plan.get('name', 'Unknown')}")
            print(f"   설명: {plan.get('description', 'N/A')}")
            print(f"   생성: {plan.get('created_at', 'N/A')}")
            print(f"   현재 Phase: {plan.get('current_phase', 'N/A')}")
        return
    
    # 새 계획 생성
    print(f"\n🎯 새로운 계획 '{plan_name}' 수립 중...")
    
    timestamp = dt.datetime.now().isoformat()
    
    # Plan 객체 대신 dictionary 사용 (호환성을 위해)
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
            'tasks': []
        }
    
    new_plan_dict['current_phase'] = 'phase-1'
    
    # ProjectContext와 dict 모두 지원
    context = get_context_manager().context
    
    try:
        if hasattr(context, 'plan'):  # ProjectContext인 경우
            # Plan 객체로 변환 시도
            try:
                from core.models import Plan, Phase
                # Phase 객체들 생성
                phases = {}
                for phase_id, phase_data in new_plan_dict['phases'].items():
                    phases[phase_id] = Phase(**phase_data)
                
                # Plan 객체 생성
                plan_obj = Plan(
                    name=new_plan_dict['name'],
                    description=new_plan_dict['description'],
                    created_at=new_plan_dict['created_at'],
                    updated_at=new_plan_dict['updated_at'],
                    phases=phases,
                    current_phase=new_plan_dict['current_phase'],
                    current_task=new_plan_dict['current_task']
                )
                context.plan = plan_obj
            except:
                # Plan 객체 생성 실패시 metadata에 저장
                if not context.metadata:
                    context.metadata = {}
                context.metadata['plan'] = new_plan_dict
            
            # plan_history 업데이트
            if hasattr(context, 'plan_history'):
                context.plan_history.append({
                    'name': plan_name,
                    'created_at': timestamp,
                    'id': f"plan-{len(context.plan_history) + 1}"
                })
        else:  # dict인 경우
            context['plan'] = new_plan_dict
            if 'plan_history' not in context:
                context['plan_history'] = []
            context['plan_history'].append({
                'name': plan_name,
                'created_at': timestamp,
                'id': f"plan-{len(context['plan_history']) + 1}"
            })
    except Exception as e:
        print(f"❌ 계획 저장 중 오류 발생: {e}")
        return
    
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

if __name__ == "__main__":
    # 명령줄 인자 처리
    import sys
    if len(sys.argv) > 1:
        plan_name = sys.argv[1]
        description = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else None
        cmd_plan(plan_name, description)
    else:
        cmd_plan()
