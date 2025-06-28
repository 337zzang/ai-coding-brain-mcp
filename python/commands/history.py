"""
작업 히스토리 관리 명령어

프로젝트의 모든 완료된 작업 내용을 시간순으로 정리하여 표시합니다.
Phase별로 그룹화하여 프로젝트 전체 히스토리를 제공합니다.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from python.core.workflow_manager import get_workflow_manager
from python.core.models import TaskStatus
from python.core.error_handler import StandardResponse, ErrorType


def cmd_history(phase_id: Optional[str] = None, format: str = "timeline") -> StandardResponse:
    """프로젝트 작업 히스토리 표시
    
    Args:
        phase_id: 특정 Phase의 히스토리만 보기 (선택사항)
        format: 표시 형식 ('timeline', 'phase', 'summary')
        
    Returns:
        StandardResponse: 표준 응답
    """
    wm = get_workflow_manager()
    
    try:
        plan = wm.plan
        if not plan:
            print("❌ 현재 설정된 계획이 없습니다.")
            return StandardResponse(
                success=False,
                error="계획이 설정되지 않음"
            )
        
        print(f"\n📚 프로젝트 히스토리: {plan.name}")
        print("=" * 60)
        
        # 모든 완료된 작업 수집
        completed_tasks = []
        for phase_id_iter, phase in plan.phases.items():
            if phase_id and phase_id != phase_id_iter:
                continue
                
            phase_tasks = list(phase.tasks.values()) if hasattr(phase.tasks, 'values') else phase.tasks
            for task in phase_tasks:
                if task.status == TaskStatus.COMPLETED and hasattr(task, 'content') and task.content:
                    completed_tasks.append({
                        'task': task,
                        'phase': phase,
                        'phase_id': phase_id_iter
                    })
        
        if not completed_tasks:
            print("\n아직 완료된 작업이 없습니다.")
            return StandardResponse(success=True, data={'count': 0})
        
        # 정렬 (완료 시간 기준)
        completed_tasks.sort(key=lambda x: x['task'].completed_at or datetime.min)
        
        if format == "timeline":
            # 시간순 표시
            print(f"\n🕐 시간순 작업 히스토리 (총 {len(completed_tasks)}개)")
            print("-" * 60)
            
            for item in completed_tasks:
                task = item['task']
                phase = item['phase']
                
                # 날짜 표시
                if task.completed_at:
                    date_str = task.completed_at.strftime("%Y-%m-%d %H:%M")
                else:
                    date_str = "날짜 없음"
                
                print(f"\n📅 {date_str}")
                print(f"   Phase: {phase.name}")
                print(f"   작업: {task.title}")
                print(f"   내용: {task.content}")
                
        elif format == "phase":
            # Phase별 그룹화
            print(f"\n📊 Phase별 작업 히스토리")
            print("-" * 60)
            
            # Phase별로 그룹화
            phase_groups = {}
            for item in completed_tasks:
                phase_name = item['phase'].name
                if phase_name not in phase_groups:
                    phase_groups[phase_name] = []
                phase_groups[phase_name].append(item)
            
            for phase_name, items in phase_groups.items():
                print(f"\n🎯 {phase_name} (완료: {len(items)}개)")
                for item in items:
                    task = item['task']
                    print(f"\n   ✅ {task.title}")
                    print(f"      수행 내용: {task.content}")
                    if task.completed_at:
                        print(f"      완료 시간: {task.completed_at.strftime('%Y-%m-%d %H:%M')}")
        
        else:  # summary
            # 요약 형식
            print(f"\n📈 프로젝트 진행 요약")
            print("-" * 60)
            print(f"총 완료 작업: {len(completed_tasks)}개")
            
            # Phase별 완료율
            for phase_id_iter, phase in plan.phases.items():
                phase_tasks = list(phase.tasks.values()) if hasattr(phase.tasks, 'values') else phase.tasks
                if phase_tasks:
                    completed = len([t for t in phase_tasks if t.status == TaskStatus.COMPLETED])
                    total = len(phase_tasks)
                    progress = (completed / total) * 100
                    print(f"\n{phase.name}: {progress:.0f}% ({completed}/{total})")
                    
                    # 이 Phase의 완료 작업들
                    phase_completed = [item for item in completed_tasks if item['phase_id'] == phase_id_iter]
                    if phase_completed:
                        print("   주요 성과:")
                        for item in phase_completed[:3]:  # 최대 3개
                            content_preview = item['task'].content[:50] + "..." if len(item['task'].content) > 50 else item['task'].content
                            print(f"   - {content_preview}")
        
        # 통계 정보
        print(f"\n📊 통계:")
        print(f"   총 완료 작업: {len(completed_tasks)}개")
        
        # 평균 작업 시간 계산 (completed_at이 있는 경우만)
        tasks_with_time = [t for t in completed_tasks if t['task'].completed_at and t['task'].started_at]
        if tasks_with_time:
            total_time = sum((t['task'].completed_at - t['task'].started_at).total_seconds() for t in tasks_with_time)
            avg_time_hours = total_time / len(tasks_with_time) / 3600
            print(f"   평균 작업 시간: {avg_time_hours:.1f}시간")
        
        return StandardResponse.success(
            data={
                'total_completed': len(completed_tasks),
                'tasks': [item['task'].dict() for item in completed_tasks]
            }
        )
        
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        return StandardResponse.error(
            ErrorType.GENERAL_ERROR,
            error=str(e)
        )


# MCP 도구로 사용할 수 있도록 export
__all__ = ['cmd_history']
