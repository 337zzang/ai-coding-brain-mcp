#!/usr/bin/env python3
"""
개선된 계획(Plan) 관리 명령어
ProjectContext와 dict 모두 지원하는 유연한 구조
"""

import os
import json
import datetime as dt
from pathlib import Path
from typing import Dict, Any, Optional, Union, List

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from core.context_manager import get_context_manager
from core.config import get_paths_from_config
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
                phases=phases,,
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

def cmd_plan(plan_name: Optional[str] = None, description: Optional[str] = None, interactive: bool = False) -> None:
    """새로운 계획 수립 또는 현재 계획 조회
    
    Args:
        plan_name: 계획 이름
        description: 계획 설명
        interactive: 대화형 모드 활성화 (--interactive)
    """
    
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
    if interactive:
        # 대화형 모드
        if not description:
            description = input("계획 설명을 입력하세요: ").strip()
            if not description:
                description = f"{plan_name} 프로젝트 계획"
        
        plan = interactive_plan_creation(plan_name, description)
        
        # 사용자 승인
        print("\n📊 생성된 계획 요약:")
        print(f"  • 계획명: {plan['name']}")
        print(f"  • 설명: {plan['description']}")
        print(f"  • Phase 수: {len(plan['phases'])}")
        total_tasks = sum(len(phase.get('tasks', [])) for phase in plan['phases'])
        print(f"  • 전체 Task 수: {total_tasks}")
        
        print("\n📋 Phase 상세:")
        for phase in plan['phases']:
            print(f"\n  Phase {phase['id']}: {phase['name']}")
            if phase.get('goal'):
                print(f"    목표: {phase['goal']}")
            print(f"    Tasks: {len(phase.get('tasks', []))}개")
            for task in phase.get('tasks', [])[:3]:  # 처음 3개만 표시
                print(f"      - {task['task']}")
            if len(phase.get('tasks', [])) > 3:
                print(f"      ... 외 {len(phase['tasks']) - 3}개")
        
        confirm = input("\n이 계획을 저장하시겠습니까? (y/n) [y]: ").strip().lower()
        if confirm == 'n':
            print("❌ 계획 수립이 취소되었습니다.")
            return
            
    else:
        # 기존 자동 모드
        print(f"\n🎯 새로운 계획 '{plan_name}' 수립 중...")
    
    # ProjectAnalyzer를 활용한 프로젝트 분석
    print("🔍 프로젝트 구조 분석 중...")
    project_path = get_context_manager().project_path
    analyzer = ProjectAnalyzer(project_path)
    
    try:
        # 프로젝트 분석 수행
        analyzer.analyze_and_update()
        briefing = analyzer.get_briefing_data()
        
        print(f"  ✅ 분석 완료: {briefing.get('total_files', 0)}개 파일")
        languages = briefing.get('languages', {})
        if languages:
            print(f"  📊 주요 언어: {', '.join(list(languages.keys())[:3])}")
        
        # 프로젝트 특성에 따른 추천 작업 생성
        recommendations = []
        
        # TypeScript/JavaScript 프로젝트
        if any(lang in languages for lang in ['.ts', '.js', '.tsx', '.jsx']):
            recommendations.append({
                'phase': 'phase-1',
                'task': 'TypeScript 타입 안전성 개선',
                'priority': 'high'
            })
            recommendations.append({
                'phase': 'phase-2',
                'task': '테스트 커버리지 향상',
                'priority': 'medium'
            })
        
        # Python 프로젝트
        if '.py' in languages:
            recommendations.append({
                'phase': 'phase-1',
                'task': 'Python 코드 품질 분석 (flake8, mypy)',
                'priority': 'high'
            })
            recommendations.append({
                'phase': 'phase-2',
                'task': 'docstring 및 타입 힌트 추가',
                'priority': 'medium'
            })
        
        # 문서화 필요성
        if briefing.get('readme_exists'):
            recommendations.append({
                'phase': 'phase-3',
                'task': 'README.md 업데이트',
                'priority': 'low'
            })
        else:
            recommendations.append({
                'phase': 'phase-3',
                'task': 'README.md 작성',
                'priority': 'high'
            })
        
    except Exception as e:
        print(f"  ⚠️ 프로젝트 분석 실패: {e}")
        recommendations = []
    
    timestamp = dt.datetime.now().isoformat()
    
    # 계획 데이터를 dictionary로 생성
    new_plan_dict = {
        'name': plan_name,
        'description': description or f"{get_context_manager().project_name} 작업 계획",
        'created_at': timestamp,
        'updated_at': timestamp,
        'phases': {},
        'current_phase': None,
        'current_task': None,
        'analysis_summary': briefing if 'briefing' in locals() else None
    }
    
    # 기본 Phase 3개 생성 (프로젝트 분석 결과 반영)
    default_phases = [ [
        ('phase-1', 'Phase 1: 분석 및 설계', '현재 상태 분석과 개선 방향 설계', [
            '현재 코드 구조 분석',
            '개선 사항 도출',
            '구현 계획 수립'
        ]),
        ('phase-2', 'Phase 2: 핵심 구현', '주요 기능 구현 및 개선', [
            '핵심 기능 구현',
            '단위 테스트 작성',
            '코드 리뷰 및 리팩토링'
        ]),
        ('phase-3', 'Phase 3: 테스트 및 문서화', '테스트 작성 및 문서 정리', [
            '통합 테스트 작성',
            'API 문서화',
            'README 및 가이드 업데이트'
        ])
    ]
    
    for phase_id, phase_name, phase_desc, default_tasks in default_phases:
        # 기본 tasks 생성
        tasks = []
        for i, task_name in enumerate(default_tasks, 1):
            task_id = f"{phase_id}-task-{i}"
            tasks.append({
                'id': task_id,
                'title': task_name,
                'status': 'pending',
                'created_at': timestamp,
                'phase_id': phase_id
            })
        
        new_plan_dict['phases'][phase_id] = {
            'id': phase_id,
            'name': phase_name,
            'description': phase_desc,
            'status': 'pending',
            'tasks': tasks,
            'created_at': timestamp,
            'updated_at': timestamp
        }
    
    new_plan_dict['current_phase'] = 'phase-1'
    
    # 프로젝트 분석 기반 추천 작업을 Phase에 추가
    if recommendations:
        print("\n📋 프로젝트 분석 기반 추천 작업:")
        task_counter = 1
        for rec in recommendations:
            phase_id = rec['phase']
            if phase_id in new_plan_dict['phases']:
                task_id = f"{phase_id}-task-{task_counter}"
                task = {
                    'id': task_id,
                    'title': rec['task'],
                    'description': f"[{rec['priority'].upper()}] {rec['task']}",
                    'status': 'pending',
                    'priority': rec['priority'],
                    'created_at': timestamp,
                    'updated_at': timestamp
                }
                new_plan_dict['phases'][phase_id]['tasks'].append(task)
                print(f"   ➕ {phase_id}: {rec['task']} (우선순위: {rec['priority']})")
                task_counter += 1
    
    # context에 plan 설정
    if set_plan(context, new_plan_dict):
        # 기존 작업 큐 정리 (새 계획 생성 시)
        if hasattr(context, 'tasks'):
            # 완료된 작업은 보존, next 큐만 초기화
            old_next_count = len(context.tasks.get('next', []))
            if old_next_count > 0:
                print(f"  🧹 기존 대기 작업 {old_next_count}개 정리")
            context.tasks['next'] = []
        elif isinstance(context, dict) and 'tasks' in context:
            old_next_count = len(context['tasks'].get('next', []))
            if old_next_count > 0:
                print(f"  🧹 기존 대기 작업 {old_next_count}개 정리")
            context['tasks']['next'] = []
        
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
        for phase_id, phase_name, _, _ in default_phases:
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
