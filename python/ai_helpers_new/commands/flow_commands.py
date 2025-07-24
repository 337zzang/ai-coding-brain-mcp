"""
Flow 관련 명령어
"""
from typing import List, Dict, Any
from .router import command


@command('flow', 'f', description='Flow 생성/선택/목록')
def flow_command(manager, args: List[str]) -> Dict[str, Any]:
    """Flow 명령어 처리"""
    if not args:
        # Flow 목록
        flows = manager.list_flows()
        if not flows:
            return {'ok': True, 'message': 'Flow가 없습니다'}

        lines = ["Flow 목록:", "-" * 40]
        for i, flow in enumerate(flows, 1):
            status = f"{flow['plans']} plans, {flow['tasks']} tasks"
            lines.append(f"{i}. {flow['name']} ({status})")

        return {'ok': True, 'message': '\n'.join(lines)}

    # Flow 이름으로 선택 또는 생성
    flow_name = args[0]

    # 기존 Flow 찾기
    flows = manager.list_flows()
    for flow in flows:
        if flow['name'] == flow_name or flow['id'] == flow_name:
            success = manager.select_flow(flow['id'])
            if success:
                # v30.0: Flow 선택 시 Plan 목록 표시
                try:
                    # Plan 목록 가져오기
                    plans = manager.get_plans()
                    
                    lines = [f"Flow 선택: {flow_name}"]
                    lines.append("")
                    lines.append(f"📋 Plan 목록 ({len(plans)}개):")
                    lines.append("-" * 40)
                    
                    for i, plan in enumerate(plans, 1):
                        plan_id = plan.get('id')
                        plan_name = plan.get('name', 'Unnamed Plan')
                        plan_status = plan.get('status', 'pending')
                        
                        # Task 목록 가져오기
                        try:
                            tasks = manager.get_tasks(plan_id)
                            completed_tasks = [t for t in tasks if t.get('status') in ['completed', 'done']]
                            in_progress_tasks = [t for t in tasks if t.get('status') in ['in_progress', 'doing']]
                            
                            # 상태 아이콘 결정
                            if plan_status == 'completed':
                                status_icon = "✅"
                            elif in_progress_tasks:
                                status_icon = "⏳"
                            elif len(completed_tasks) == len(tasks) and tasks:
                                status_icon = "🔄"  # 모든 Task 완료했지만 Plan은 미완료
                            else:
                                status_icon = "📌"
                            
                            lines.append(f"\n{i}. {status_icon} Plan: {plan_name}")
                            lines.append(f"   ID: {plan_id}")
                            lines.append(f"   상태: {plan_status}")
                            lines.append(f"   Tasks: {len(completed_tasks)}/{len(tasks)} 완료")
                            
                            # Task 상태 요약
                            if tasks:
                                todo_tasks = len([t for t in tasks if t.get('status') in ['todo', 'pending']])
                                if in_progress_tasks:
                                    lines.append(f"   - 진행 중: {len(in_progress_tasks)}개")
                                if todo_tasks > 0:
                                    lines.append(f"   - 대기 중: {todo_tasks}개")
                        
                        except Exception as e:
                            lines.append(f"   ⚠️ Task 정보 로드 실패: {str(e)}")
                    
                    lines.append("")
                    lines.append("💡 Plan을 선택하려면 Plan 번호나 이름을 입력하세요.")
                    lines.append("예: '1번 Plan 선택' 또는 'Plan 1'")
                    
                    return {'ok': True, 'message': '\n'.join(lines)}
                    
                except Exception as e:
                    # 오류 발생 시 기본 메시지
                    return {'ok': True, 'message': f"Flow 선택: {flow_name}\n⚠️ Plan 목록 표시 중 오류: {str(e)}"}

    # 없으면 생성
    flow_id = manager.create_flow(flow_name)
    return {'ok': True, 'message': f"Flow 생성: {flow_name}", 'flow_id': flow_id}


@command('flows', 'list', description='전체 Flow 목록')
def list_flows(manager, args: List[str]) -> Dict[str, Any]:
    """Flow 목록 표시"""
    flows = manager.list_flows()

    if not flows:
        return {'ok': True, 'message': 'Flow가 없습니다'}

    lines = ["전체 Flow 목록:", "=" * 60]
    for flow in flows:
        lines.append(f"📁 {flow['name']}")
        lines.append(f"   ID: {flow['id']}")
        lines.append(f"   Plans: {flow['plans']}, Tasks: {flow['tasks']}")
        lines.append(f"   생성: {flow['created'][:19]}")
        lines.append("")

    return {'ok': True, 'message': '\n'.join(lines)}


@command('delete-flow', description='Flow 삭제')
def delete_flow(manager, args: List[str]) -> Dict[str, Any]:
    """Flow 삭제"""
    if not args:
        return {'ok': False, 'error': 'Flow ID가 필요합니다'}

    flow_id = args[0]
    success = manager.delete_flow(flow_id)

    if success:
        return {'ok': True, 'message': f"Flow 삭제됨: {flow_id}"}
    else:
        return {'ok': False, 'error': f"Flow 삭제 실패: {flow_id}"}


@command('status', 's', description='현재 상태')
def status_command(manager, args: List[str]) -> Dict[str, Any]:
    """현재 상태 표시"""
    current = manager.get_current_flow()

    if not current:
        return {'ok': True, 'message': 'Flow가 선택되지 않았습니다'}

    summary = manager.get_flow_summary()

    lines = [
        f"📁 현재 Flow: {current.name}",
        f"   ID: {current.id}",
        "-" * 40,
        f"📋 Plans: {summary['plans']['total']} (완료: {summary['plans']['completed']})",
        f"✅ Tasks: {summary['tasks']['total']}",
        f"   - TODO: {summary['tasks']['todo']}",
        f"   - DOING: {summary['tasks']['doing']}",  
        f"   - DONE: {summary['tasks']['done']}"
    ]

    return {'ok': True, 'message': '\n'.join(lines)}


@command('stats', description='전체 통계')
def stats_command(manager, args: List[str]) -> Dict[str, Any]:
    """전체 통계"""
    stats = manager.get_stats()

    lines = [
        "📊 전체 통계",
        "=" * 40,
        f"Flows: {stats['flows']['total']} (활성: {stats['flows']['active']})",
        f"Plans: {stats['plans']['total']}",
        f"Tasks: {stats['tasks']['total']}",
        f"  - TODO: {stats['tasks']['todo']}",
        f"  - DOING: {stats['tasks']['doing']}",
        f"  - DONE: {stats['tasks']['done']}",
        "",
        "💾 저장소 정보",
        f"파일: {stats['repository']['data_path']}",
        f"크기: {stats['repository']['size']:,} bytes",
        f"백업: {stats['repository']['backup_count']}개"
    ]

    return {'ok': True, 'message': '\n'.join(lines)}
