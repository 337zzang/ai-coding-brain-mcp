#!/usr/bin/env python3
"""
계획(Plan) 관리 명령어 - 안정화된 버전
모든 로직은 WorkflowManager로 위임하는 단순 래퍼
"""

import os
import sys
from typing import Optional
from pathlib import Path

# 프로젝트 경로 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.workflow_manager import get_workflow_manager
from core.error_handler import StandardResponse, ErrorType
from core.models import TaskStatus


def cmd_plan(name: Optional[str] = None, description: Optional[str] = None, 
             phase_count: int = 3, reset: bool = False, 
             content: Optional[str] = None) -> StandardResponse:
    """프로젝트 계획 수립 또는 조회 - WorkflowManager로 위임하는 단순 래퍼
    
    Args:
        name: 계획 이름 (없으면 현재 계획 표시)
        description: 계획 설명
        phase_count: Phase 개수 (기본 3개) - WorkflowManager에서 처리
        reset: True일 경우 계획 초기화
        content: 계획의 상세 내용 (프로젝트 목표, 전략 등)
        
    Returns:
        StandardResponse: 표준 응답
    """
    try:
        wm = get_workflow_manager()
        
        # reset 옵션 처리
        if reset:
            return wm.reset_plan()
        
        # 새 계획 생성
        if name:
            # 기존 계획이 있는 경우 자동 저장 후 초기화
            if wm.context.plan:
                existing_tasks = len(wm.context.get_all_tasks())
                if existing_tasks > 0:
                    print(f"⚠️ 기존 계획 '{wm.context.plan.name}'에 {existing_tasks}개의 작업이 있습니다.")
                    wm.save_context()  # 기존 계획 저장
                    print(f"✅ 기존 계획이 저장되었습니다.")
                    wm.reset_plan()  # 초기화
            
            # WorkflowManager로 계획 생성 위임
            return wm.create_plan(
                name=name,
                description=description or f"{name} 계획",
                content=content
            )
        
        # 현재 계획 조회
        else:
            if not wm.context.plan:
                return StandardResponse.error(
                    ErrorType.PLAN_ERROR, 
                    "설정된 계획이 없습니다. 'plan "계획명"'으로 생성하세요."
                )
            
            # 현재 계획 정보 표시
            plan = wm.context.plan
            status = wm.get_workflow_status()
            
            print(f"📋 현재 계획: {plan.name}")
            print(f"진행률: {status['progress']:.1f}% ({status['completed_tasks']}/{status['total_tasks']})")
            
            if hasattr(plan, 'content') and plan.content:
                print(f"\n📝 계획 내용:")
                print(f"   {plan.content}")
            
            # Phase별 진행 상황
            print("\n📊 Phase별 진행 상황:")
            for phase_id, phase in plan.phases.items():
                tasks = list(phase.tasks.values())
                if tasks:
                    completed = len([t for t in tasks if t.status == TaskStatus.COMPLETED])
                    progress = (completed / len(tasks)) * 100
                    icon = "✅" if progress == 100 else ("🔄" if progress > 0 else "⏳")
                    print(f"{icon} {phase.name}: {progress:.0f}% ({completed}/{len(tasks)})")
                else:
                    print(f"⏳ {phase.name}: 작업 없음")
            
            return StandardResponse.success({
                'plan': plan,
                'status': status
            })
    
    except Exception as e:
        return StandardResponse.error(
            ErrorType.PLAN_ERROR, 
            f"계획 처리 중 오류: {str(e)}"
        )


# 명령줄 인터페이스
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="프로젝트 계획 관리")
    parser.add_argument('name', nargs='?', help='계획 이름')
    parser.add_argument('-d', '--description', help='계획 설명')
    parser.add_argument('-c', '--content', help='계획 상세 내용')
    parser.add_argument('-r', '--reset', action='store_true', help='계획 초기화')
    
    args = parser.parse_args()
    
    result = cmd_plan(
        name=args.name,
        description=args.description,
        content=args.content,
        reset=args.reset
    )
    
    if not result.success:
        print(f"❌ 오류: {result.error}")
        sys.exit(1)
