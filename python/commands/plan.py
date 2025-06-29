#!/usr/bin/env python3
"""
개선된 계획(Plan) 관리 명령어
ProjectContext와 dict 모두 지원하는 유연한 구조
"""

from datetime import datetime
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
            if isinstance(phase, dict):
                result['phases'][phase_id] = phase
            else:
                # Phase 객체를 dict로 변환
                result['phases'][phase_id] = {
                    'id': getattr(phase, 'id', phase_id),
                    'name': getattr(phase, 'name', ''),
                    'description': getattr(phase, 'description', ''),
                    'status': getattr(phase, 'status', 'pending'),
                    'tasks': [
                        {
                            'id': getattr(t, 'id', ''),
                            'title': getattr(t, 'title', ''),
                            'description': getattr(t, 'description', ''),
                            'status': getattr(t, 'status', 'pending'),
                            'phase_id': getattr(t, 'phase_id', ''),
                            'completed': getattr(t, 'completed', False)
                        }
                        for t in getattr(phase, 'tasks', [])
                    ]
                }
    
    return result


def get_plan_template(template_name: str = "default") -> Dict[str, Any]:
    """계획 템플릿 로드"""
    template_dir = Path("memory/plan_templates")
    template_file = template_dir / f"{template_name}.json"
    
    if not template_file.exists():
        # 기본 템플릿 반환
        return {
            "phases": [
                {
                    "name": "분석 및 설계",
                    "default_tasks": ["현재 코드 구조 분석", "개선 사항 도출", "구현 계획 수립"]
                },
                {
                    "name": "구현",
                    "default_tasks": ["핵심 기능 구현", "테스트 작성", "코드 리뷰"]
                },
                {
                    "name": "마무리",
                    "default_tasks": ["문서화", "최종 테스트", "배포 준비"]
                }
            ]
        }
    
    with open(template_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def interactive_plan_creation(plan_name: str, description: str) -> Dict[str, Any]:
    """대화형 계획 수립"""
    print("\n🎯 대화형 계획 수립을 시작합니다.")
    print(f"📋 계획명: {plan_name}")
    print(f"📝 설명: {description}\n")
    
    # 템플릿 선택
    template_dir = Path("memory/plan_templates")
    templates = []
    if template_dir.exists():
        templates = [f.stem for f in template_dir.glob("*.json")]
    
    if templates:
        print("📚 사용 가능한 템플릿:")
        for i, tmpl in enumerate(templates, 1):
            print(f"  {i}. {tmpl}")
        print(f"  {len(templates)+1}. 빈 계획으로 시작")
        
        choice = input("\n템플릿을 선택하세요 (번호 또는 Enter로 기본값): ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(templates):
            template = get_plan_template(templates[int(choice)-1])
        elif choice.isdigit() and int(choice) == len(templates)+1:
            template = {"phases": []}
        else:
            template = get_plan_template("default")
    else:
        template = get_plan_template("default")
    
    # Phase별 정보 입력
    phases = []
    
    if template.get("phases"):
        print("\n📊 템플릿의 Phase를 기반으로 계획을 수립합니다.")
        for i, phase_template in enumerate(template["phases"], 1):
            print(f"\n--- Phase {i}: {phase_template['name']} ---")
            
            # Phase 이름 확인/수정
            phase_name = input(f"Phase 이름 [{phase_template['name']}]: ").strip()
            if not phase_name:
                phase_name = phase_template['name']
            
            # Phase 목표 입력
            goal = input("Phase 목표 (Enter로 건너뛰기): ").strip()
            
            # 기본 Task 확인
            tasks = []
            if phase_template.get("default_tasks"):
                print("\n기본 Task:")
                for j, task in enumerate(phase_template["default_tasks"], 1):
                    print(f"  {j}. {task}")
                
                use_default = input("\n기본 Task를 사용하시겠습니까? (y/n) [y]: ").strip().lower()
                if use_default != 'n':
                    tasks = [{"task": t, "status": "pending"} for t in phase_template["default_tasks"]]
            
            # 추가 Task 입력
            print("\n추가 Task 입력 (빈 줄로 종료):")
            while True:
                task = input(f"Task {len(tasks)+1}: ").strip()
                if not task:
                    break
                tasks.append({"task": task, "status": "pending"})
            
            phase = {
                "id": i,
                "name": phase_name,
                "status": "pending",
                "tasks": tasks
            }
            if goal:
                phase["goal"] = goal
            
            phases.append(phase)
    
    # 추가 Phase 입력
    while True:
        add_more = input("\n새로운 Phase를 추가하시겠습니까? (y/n) [n]: ").strip().lower()
        if add_more != 'y':
            break
        
        phase_id = len(phases) + 1
        phase_name = input(f"\nPhase {phase_id} 이름: ").strip()
        if not phase_name:
            print("Phase 이름은 필수입니다.")
            continue
        
        goal = input("Phase 목표 (Enter로 건너뛰기): ").strip()
        
        # Task 입력
        tasks = []

        # 자동 작업 생성 옵션
        auto_suggest = input("\n🤖 이 Phase에 대한 작업을 자동으로 생성할까요? (y/n, 기본값: y): ").strip().lower()
        if auto_suggest != 'n':
            suggested_tasks = auto_generate_tasks(phase_data['name'])
            if suggested_tasks:
                print("\n💡 추천 작업:")
                for idx, task in enumerate(suggested_tasks, 1):
                    print(f"  {idx}. {task}")
                
                use_suggestions = input("\n이 작업들을 사용하시겠습니까? (y/n/select, 기본값: y): ").strip().lower()
                if use_suggestions == 'y' or use_suggestions == '':
                    tasks.extend(suggested_tasks)
                    print(f"✅ {len(suggested_tasks)}개의 작업이 추가되었습니다.")
                elif use_suggestions == 'select':
                    selected = input("사용할 작업 번호를 입력하세요 (쉼표로 구분): ").strip()
                    if selected:
                        indices = [int(x.strip()) - 1 for x in selected.split(',') if x.strip().isdigit()]
                        selected_tasks = [suggested_tasks[i] for i in indices if 0 <= i < len(suggested_tasks)]
                        tasks.extend(selected_tasks)
                        print(f"✅ {len(selected_tasks)}개의 작업이 추가되었습니다.")
        print("\nTask 입력 (빈 줄로 종료):")
        while True:
            task = input(f"Task {len(tasks)+1}: ").strip()
            if not task:
                break
            tasks.append({"task": task, "status": "pending"})
        
        phase = {
            "id": phase_id,
            "name": phase_name,
            "status": "pending",
            "tasks": tasks
        }
        if goal:
            phase["goal"] = goal
        
        phases.append(phase)
    
    # 계획 생성
    plan = {
        "name": plan_name,
        "description": description,
        "created_at": dt.datetime.now().isoformat(),
        "phases": phases,
        "current_phase": 1 if phases else None,
        "current_task": None,
        "status": "active"
    }
    
    return plan




def get_wisdom_suggestions(plan_type: str = None) -> Dict[str, Any]:
    """Wisdom 시스템에서 계획 관련 제안 가져오기"""
    wisdom = get_wisdom_manager()
    suggestions = {
        "common_phases": [],
        "recommended_tasks": [],
        "warnings": []
    }
    
    # 베스트 프랙티스에서 계획 관련 내용 추출
    for practice in wisdom.wisdom_data.get('best_practices', []):
        if 'plan' in practice.lower() or 'phase' in practice.lower():
            suggestions['recommended_tasks'].append(practice)
    
    # 자주 하는 실수 경고
    for mistake_type, data in wisdom.wisdom_data.get('common_mistakes', {}).items():
        if data['count'] > 2:  # 2번 이상 발생한 실수
            suggestions['warnings'].append(f"주의: {mistake_type} ({data['count']}회 발생)")
    
    # 프로젝트 유형별 추천 Phase
    if plan_type:
        if plan_type.lower() in ['feature', '기능']:
            suggestions['common_phases'] = ["분석 및 설계", "구현", "테스트", "문서화"]
        elif plan_type.lower() in ['bugfix', '버그']:
            suggestions['common_phases'] = ["원인 분석", "수정", "테스트", "검증"]
        elif plan_type.lower() in ['refactor', '리팩토링']:
            suggestions['common_phases'] = ["현재 상태 분석", "개선 계획", "단계별 리팩토링", "테스트"]
    
    return suggestions


def auto_generate_tasks(phase_name: str, project_analyzer: ProjectAnalyzer = None) -> List[str]:
    """Phase에 맞는 작업 자동 생성"""
    tasks = []
    
    # 기본 템플릿에서 작업 가져오기
    for template_key in AUTO_TASK_TEMPLATES:
        if phase_name.lower() in template_key.lower():
            tasks.extend(AUTO_TASK_TEMPLATES[template_key])
            break
    
    # 프로젝트 분석 결과 활용
    if project_analyzer:
        # TODO: ProjectAnalyzer 결과 기반 작업 추가
        pass
    
    # Wisdom 기반 추가 작업
    wisdom = get_wisdom_manager()
    hooks = get_wisdom_hooks()
    
    # 최근 오류 패턴 기반 작업 추가
    error_patterns = wisdom.wisdom_data.get('error_patterns', {})
    if error_patterns and "테스트" in phase_name:
        for error_type in error_patterns:
            if error_patterns[error_type]['count'] > 0:
                tasks.append(f"{error_type} 관련 테스트 케이스 추가")
    
    return tasks


def enhance_plan_with_wisdom(plan_data: Dict) -> Dict:
    """계획에 Wisdom 시스템의 인사이트 추가"""
    wisdom = get_wisdom_manager()
    
    # 계획 메타데이터에 Wisdom 정보 추가
    plan_data['wisdom_insights'] = {
        'created_with_wisdom': True,
        'wisdom_version': getattr(wisdom, 'version', '1.0'),
        'tracked_mistakes': len(wisdom.wisdom_data.get('common_mistakes', {})),
        'best_practices_applied': []
    }
    
    # Phase별로 관련 베스트 프랙티스 추가
    for phase_id, phase in plan_data.get('phases', {}).items():
        phase['wisdom_tips'] = []
        
        # Phase 이름과 관련된 베스트 프랙티스 찾기
        for practice in wisdom.wisdom_data.get('best_practices', []):
            if any(keyword in practice.lower() for keyword in phase['name'].lower().split()):
                phase['wisdom_tips'].append(practice)
                plan_data['wisdom_insights']['best_practices_applied'].append(practice)
    
    return plan_data

def cmd_plan(name: Optional[str] = None, description: Optional[str] = None, phase_count: int = 3, reset: bool = False, content: Optional[str] = None) -> StandardResponse:
    """프로젝트 계획 수립 또는 조회
    
    Args:
        name: 계획 이름 (없으면 현재 계획 표시)
        description: 계획 설명
        phase_count: Phase 개수 (기본 3개)
        reset: True일 경우 계획 초기화
        content: 계획의 상세 내용 (프로젝트 목표, 전략 등)
        
    Returns:
        StandardResponse: 표준 응답
    """
    wm = get_workflow_manager()
    
    try:
        # reset 옵션이 True인 경우 계획 초기화
        if reset:
            result = wm.reset_plan()
            if result['success']:
                print(result['data']['message'])
            return result
            
        if name:
            # 기존 계획이 있는지 확인
            if wm.plan and hasattr(wm.plan, 'name'):
                existing_tasks = wm.get_workflow_status()['total_tasks']
                if existing_tasks > 0:
                    print(f"⚠️  기존 계획 '{wm.plan.name}'에 {existing_tasks}개의 작업이 있습니다.")
                    # 비대화형 모드: 자동으로 저장하고 진행
                    # 비대화형 모드: 자동으로 저장하고 진행
                    wm.save()  # save는 None을 반환
                    print(f"✅ 기존 계획 '{wm.plan.name}'이 저장되었습니다.")
                    
                    # 계획 초기화
                    reset_result = wm.reset_plan()
                    if not reset_result['success']:
                        from core.error_handler import ErrorType
                        return StandardResponse.error(ErrorType.PLAN_ERROR, f"계획 초기화 실패: {reset_result.get('message', '')}")
            
            # 새 계획 생성
            result = wm.create_plan(
                name=name,
                description=description if description else f"{name} 계획"
            )
        else:
            return result
            # 현재 계획 표시
            if not wm.plan:
                return StandardResponse.error("설정된 계획이 없습니다. 'plan \"계획명\"'으로 생성하세요.")
                
            plan = wm.plan
            status = wm.get_workflow_status()
            
            print(f"📋 현재 계획: {plan.name}")
            print(f"진행률: {status['progress']:.1f}% ({status['completed_tasks']}/{status['total_tasks']})")
            print(f"\n생성일: {plan.created_at}")
            
            # Plan content 표시
            if hasattr(plan, 'content') and plan.content:
                print(f"\n📝 계획 내용:")
                print(f"   {plan.content}")
            
            # Phase별 진행 상황
            print("\n📊 Phase별 진행 상황:")
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
                    'plan': plan.dict() if hasattr(plan, 'dict') else plan,
                    'status': status,
                    'analytics': analytics
                }
            )
            
    except Exception as e:
    except Exception as e:
        from core.error_handler import ErrorType
        import traceback
        print(f"\n❌ 오류 발생 위치:")
        traceback.print_exc()
        print(f"\n❌ 오류 발생 위치:")
        traceback.print_exc()
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
