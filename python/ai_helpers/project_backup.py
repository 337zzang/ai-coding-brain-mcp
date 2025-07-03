"""프로젝트 관리 헬퍼 함수들"""

from typing import Dict, Any, List, Optional
import os
import sys

# 프로젝트 루트 경로 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from enhanced_flow import EnhancedFlow
from ai_helpers.decorators import track_operation

# 싱글톤 EnhancedFlow 인스턴스
_flow_instance: Optional[EnhancedFlow] = None

def get_flow_instance() -> EnhancedFlow:
    """EnhancedFlow 싱글톤 인스턴스 반환"""
    global _flow_instance
    if _flow_instance is None:
        _flow_instance = EnhancedFlow()
    return _flow_instance


# ========== 프로젝트 관리 헬퍼 ==========

@track_operation('project', 'get_current')
def get_current_project() -> Optional[Dict[str, Any]]:
    """현재 활성 프로젝트 정보 반환"""
    flow = get_flow_instance()
    projects = flow.list_all_projects()
    
    # 활성 프로젝트 찾기 (보통 첫 번째)
    if projects:
        return projects[0]
    return None


@track_operation('project', 'list_tasks')
def list_tasks(project_id: Optional[str] = None, status: Optional[str] = None) -> List[Dict[str, Any]]:
    """작업 목록 조회
    
    Args:
        project_id: 프로젝트 ID (None이면 현재 프로젝트)
        status: 작업 상태 필터 ('pending', 'in_progress', 'completed')
    
    Returns:
        작업 목록
    """
    flow = get_flow_instance()
    
    # 프로젝트 ID 확인
    if project_id is None:
        current = get_current_project()
        if current:
            project_id = current['id']
        else:
            return []
    
    # TaskManager에서 작업 조회
    if status:
        tasks = flow.task_manager.get_tasks_by_status(status)
    else:
        tasks = flow.task_manager.get_tasks_by_plan(project_id)
    
    # 딕셔너리로 변환
    return [task.__dict__ for task in tasks]


@track_operation('project', 'quick_task')
def quick_task(description: str, priority: int = 1) -> Optional[Dict[str, Any]]:
    """현재 프로젝트에 빠르게 작업 추가
    
    Args:
        description: 작업 설명
        priority: 우선순위 (기본값: 1)
    
    Returns:
        생성된 작업 정보
    """
    flow = get_flow_instance()
    current = get_current_project()
    
    if not current:
        print("⚠️ 활성 프로젝트가 없습니다. 먼저 프로젝트를 생성하세요.")
        return None
    
    # 현재 Phase 찾기
    phase_id = None
    phases = flow.phase_manager.get_phases_by_plan(current['id'])
    if phases:
        # 활성 Phase 찾기
        active_phase = flow.phase_manager.get_active_phase(current['id'])
        if active_phase:
            phase_id = active_phase.id
    
    # 작업 추가
    task = flow.add_task_to_project(
        current['id'], 
        description, 
        phase_id=phase_id,
        priority=priority
    )
    
    print(f"✅ 작업 추가됨: {description}")
    return task.__dict__ if task else None


@track_operation('project', 'get_progress')
def get_project_progress(project_id: Optional[str] = None) -> Dict[str, Any]:
    """프로젝트 진행률 조회
    
    Args:
        project_id: 프로젝트 ID (None이면 현재 프로젝트)
    
    Returns:
        진행 상황 정보
    """
    flow = get_flow_instance()
    
    if project_id is None:
        current = get_current_project()
        if current:
            project_id = current['id']
        else:
            return {}
    
    return flow.get_project_status(project_id)


# ========== Phase 관리 헬퍼 ==========

@track_operation('phase', 'create_standard')
def create_standard_phases(project_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """표준 Phase 세트 생성
    
    Args:
        project_id: 프로젝트 ID (None이면 현재 프로젝트)
    
    Returns:
        생성된 Phase 목록
    """
    flow = get_flow_instance()
    
    if project_id is None:
        current = get_current_project()
        if current:
            project_id = current['id']
        else:
            raise ValueError("프로젝트를 지정하거나 활성 프로젝트가 필요합니다.")
    
    # 표준 Phase 정의
    standard_phases = [
        ("Planning", "계획 및 설계 단계"),
        ("Development", "개발 및 구현 단계"),
        ("Testing", "테스트 및 검증 단계"),
        ("Deployment", "배포 및 운영 단계")
    ]
    
    phases = []
    for i, (name, desc) in enumerate(standard_phases):
        phase = flow.phase_manager.define_phase(
            plan_id=project_id,
            name=name,
            order=i + 1,
            description=desc
        )
        phases.append(phase.__dict__)
        print(f"  📌 Phase {i+1}: {name}")
    
    # 첫 번째 Phase 시작
    if phases:
        flow.phase_manager.start_phase(phases[0]['id'])
        print(f"✅ {phases[0]['name']} Phase 시작됨")
    
    return phases


@track_operation('phase', 'get_current')
def get_current_phase(project_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """현재 활성 Phase 조회
    
    Args:
        project_id: 프로젝트 ID (None이면 현재 프로젝트)
    
    Returns:
        현재 Phase 정보
    """
    flow = get_flow_instance()
    
    if project_id is None:
        current = get_current_project()
        if current:
            project_id = current['id']
        else:
            return None
    
    active_phase = flow.phase_manager.get_active_phase(project_id)
    return active_phase.__dict__ if active_phase else None


@track_operation('phase', 'complete_current')
def complete_current_phase() -> bool:
    """현재 Phase 완료 처리"""
    flow = get_flow_instance()
    current = get_current_project()
    
    if not current:
        print("⚠️ 활성 프로젝트가 없습니다.")
        return False
    
    active_phase = flow.phase_manager.get_active_phase(current['id'])
    if active_phase:
        flow.phase_manager.complete_phase(active_phase.id)
        print(f"✅ {active_phase.name} Phase 완료됨")
        
        # 다음 Phase로 전환
        flow.phase_manager.transition_to_next_phase(current['id'])
        return True
    else:
        print("⚠️ 활성 Phase가 없습니다.")
        return False


# ========== 상태 조회 헬퍼 ==========

@track_operation('status', 'summary')
def get_system_summary() -> Dict[str, Any]:
    """전체 시스템 상태 요약"""
    flow = get_flow_instance()
    
    # 각 Manager의 상태 수집
    projects = flow.list_all_projects()
    all_tasks = []
    
    for project in projects:
        tasks = flow.task_manager.get_tasks_by_plan(project['id'])
        all_tasks.extend(tasks)
    
    pending_tasks = [t for t in all_tasks if t.status == 'pending']
    current_task = flow.task_manager.get_current_task()
    
    summary = {
        'projects': {
            'total': len(projects),
            'active': len([p for p in projects if p['status'] == 'active'])
        },
        'tasks': {
            'total': len(all_tasks),
            'pending': len(pending_tasks),
            'current': current_task.__dict__ if current_task else None
        },
        'event_bus': {
            'total_events': len(flow.event_bus._history)
        }
    }
    
    return summary


@track_operation('status', 'pending_tasks')
def get_pending_tasks() -> List[Dict[str, Any]]:
    """대기 중인 작업 목록 조회"""
    flow = get_flow_instance()
    tasks = flow.task_manager.get_pending_tasks()
    return [task.__dict__ for task in tasks]


@track_operation('status', 'event_history')
def get_event_history(event_type: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
    """이벤트 히스토리 조회
    
    Args:
        event_type: 특정 이벤트 타입만 조회
        limit: 최대 조회 개수
    
    Returns:
        이벤트 목록
    """
    flow = get_flow_instance()
    
    if event_type:
        history = flow.event_bus.get_history(event_type)
    else:
        # 전체 히스토리
        history = []
        for event_type in flow.event_bus._history:
            history.extend(flow.event_bus._history[event_type])
    
    # 최신 순으로 정렬
    history.sort(key=lambda e: e.timestamp, reverse=True)
    
    # limit 적용
    history = history[:limit]
    
    return [{'type': e.event_type, 'timestamp': e.timestamp.isoformat(), 'data': e.__dict__} 
            for e in history]


# ========== 간편 명령 ==========

def project(name: str = None) -> Dict[str, Any]:
    """프로젝트 생성 또는 조회 (간편 명령)
    
    Args:
        name: 프로젝트 이름 (None이면 현재 프로젝트 조회)
    
    Returns:
        프로젝트 정보
    """
    if name:
        flow = get_flow_instance()
        result = flow.create_project(name, f"{name} 프로젝트")
        create_standard_phases(result['plan'].id)
        flow.save_context()
        return result
    else:
        return get_current_project()


def task(description: str = None) -> Any:
    """작업 추가 또는 조회 (간편 명령)
    
    Args:
        description: 작업 설명 (None이면 작업 목록 조회)
    
    Returns:
        작업 정보 또는 작업 목록
    """
    if description:
        result = quick_task(description)
        # 컨텍스트 저장
        flow = get_flow_instance()
        flow.save_context()
        return result
    else:
        tasks = list_tasks()
        for i, task in enumerate(tasks):
            status_icon = "✅" if task['status'] == 'completed' else "⏳"
            print(f"{status_icon} [{task['id'][-6:]}] {task['description']}")
        return tasks


def progress() -> Dict[str, Any]:
    """현재 프로젝트 진행 상황 조회 (간편 명령)"""
    flow = get_flow_instance()
    current = get_current_project()
    
    if not current:
        print("⚠️ 활성 프로젝트가 없습니다.")
        return {}
    
    status = flow.get_project_status(current['id'])
    
    # 보기 좋게 출력
    print(f"\n📊 {current['name']} 진행 상황")
    print(f"   진행률: {status['progress']['percentage']:.1f}%")
    print(f"   작업: {status['progress']['completed']}/{status['progress']['total']}")
    print(f"   현재 Phase: {status['phases']['active'] or 'None'}")
    
    # 대기 중인 작업 표시
    pending = get_pending_tasks()
    if pending:
        print(f"\n⏳ 대기 중인 작업 ({len(pending)}개):")
        for task in pending[:3]:  # 최대 3개만 표시
            print(f"   - [{task['id'][-6:]}] {task['description']}")
    
    return status


def complete(task_id: str) -> bool:
    """작업 완료 처리 (간편 명령)
    
    Args:
        task_id: 작업 ID (전체 또는 마지막 6자리)
    
    Returns:
        성공 여부
    """
    flow = get_flow_instance()
    
    # 짧은 ID로 검색
    if len(task_id) == 6:
        all_tasks = []
        for project in flow.list_all_projects():
            tasks = flow.task_manager.get_tasks_by_plan(project['id'])
            all_tasks.extend(tasks)
        
        # 마지막 6자리가 일치하는 작업 찾기
        matching_tasks = [t for t in all_tasks if t.id.endswith(task_id)]
        if matching_tasks:
            task_id = matching_tasks[0].id
        else:
            print(f"⚠️ 작업 ID {task_id}를 찾을 수 없습니다.")
            return False
    
    try:
        flow.complete_task(task_id)
        print(f"✅ 작업 완료: {task_id[-6:]}")
        flow.save_context()
        return True
    except Exception as e:
        print(f"❌ 오류: {e}")
        return False


# ========== 유틸리티 ==========

def reset_project(project_id: Optional[str] = None) -> bool:
    """프로젝트 초기화
    
    Args:
        project_id: 프로젝트 ID (None이면 현재 프로젝트)
    
    Returns:
        성공 여부
    """
    flow = get_flow_instance()
    
    if project_id is None:
        current = get_current_project()
        if current:
            project_id = current['id']
        else:
            print("⚠️ 초기화할 프로젝트가 없습니다.")
            return False
    
    # 프로젝트의 모든 작업 삭제
    tasks = flow.task_manager.get_tasks_by_plan(project_id)
    for task in tasks:
        flow.task_manager.delete_task(task.id)
    
    # Phase 재생성
    phases = flow.phase_manager.get_phases_by_plan(project_id)
    if phases:
        create_standard_phases(project_id)
    
    print(f"✅ 프로젝트 초기화 완료: {project_id}")
    flow.save_context()
    return True