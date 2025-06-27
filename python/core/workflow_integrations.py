"""
WorkflowManager 확장 - ProjectAnalyzer/Wisdom 통합
"""
from typing import Dict, List
from datetime import datetime
from python.core.models import Task, Phase, Plan, TaskStatus


class WorkflowIntegrations:
    """ProjectAnalyzer와 Wisdom 시스템 통합 기능"""
    
    def __init__(self, workflow_manager):
        self.workflow_manager = workflow_manager
        self.context = workflow_manager.context
    
    def analyze_and_generate_tasks(self, project_path: str = ".") -> Dict[str, List[Task]]:
        """ProjectAnalyzer를 사용하여 자동으로 Task 생성"""
        from python.analyzers.project_analyzer import ProjectAnalyzer
        from python.project_wisdom import get_wisdom_manager
        
        analyzer = ProjectAnalyzer(project_path)
        wisdom = get_wisdom_manager()
        
        # 프로젝트 분석
        print("🔍 프로젝트 분석 중...")
        analysis_result = analyzer.analyze_project(project_path)
        
        # 분석 결과를 Plan에 저장
        if self.context.plan:
            self.context.plan.project_insights = {
                "total_files": analysis_result.get("total_files", 0),
                "file_types": analysis_result.get("file_types", {}),
                "complexity_score": analysis_result.get("average_complexity", 0),
                "largest_files": analysis_result.get("largest_files", []),
                "analysis_timestamp": datetime.now().isoformat()
            }
        
        # Task 자동 생성
        generated_tasks = {
            "analysis": [],
            "wisdom": []
        }
        
        # 1. 복잡도가 높은 파일에 대한 리팩토링 Task
        complex_files = analysis_result.get("complex_files", [])
        for idx, file_info in enumerate(complex_files[:5]):
            task = Task(
                id=f"auto-complexity-{idx+1}",
                title=f"리팩토링: {file_info['file']}",
                description=f"복잡도 {file_info['complexity']:.1f}인 파일 개선",
                priority="high" if file_info['complexity'] > 15 else "medium",
                auto_generated=True,
                wisdom_hints=["복잡한 함수를 작은 단위로 분리", "중복 코드 제거"],
                context_data={
                    "file_path": file_info['file'],
                    "complexity": file_info['complexity']
                }
            )
            generated_tasks["analysis"].append(task)
        
        # 2. Wisdom 기반 예방 Task
        common_mistakes = wisdom.get_common_mistakes()
        for idx, (mistake_type, count) in enumerate(list(common_mistakes.items())[:3]):
            task = Task(
                id=f"auto-wisdom-{idx+1}",
                title=f"예방: {mistake_type} 패턴 개선",
                description=f"{count}회 발생한 실수 패턴 예방",
                priority="high" if count > 5 else "medium",
                auto_generated=True,
                wisdom_hints=wisdom.get_prevention_tips(mistake_type),
                context_data={
                    "mistake_type": mistake_type,
                    "occurrence_count": count
                }
            )
            generated_tasks["wisdom"].append(task)
        
        return generated_tasks
    
    def create_smart_plan(self, name: str, description: str, auto_analyze: bool = True) -> Plan:
        """ProjectAnalyzer와 Wisdom을 활용한 스마트 Plan 생성"""
        # 기본 Plan 생성
        plan = self.workflow_manager.create_plan(name, description)
        
        if auto_analyze:
            # 자동 분석 및 Task 생성
            generated_tasks = self.analyze_and_generate_tasks()
            
            # Phase 1: 자동 생성된 분석 Task
            if generated_tasks["analysis"]:
                phase1 = Phase(
                    id="auto-phase-1",
                    name="자동 분석 기반 개선",
                    description="ProjectAnalyzer가 발견한 개선 사항"
                )
                for task in generated_tasks["analysis"]:
                    phase1.tasks[task.id] = task
                plan.phases["auto-phase-1"] = phase1
                plan.phase_order.append("auto-phase-1")
            
            # Phase 2: Wisdom 기반 예방 Task
            if generated_tasks["wisdom"]:
                phase2 = Phase(
                    id="auto-phase-2",
                    name="Wisdom 기반 예방",
                    description="과거 실수 패턴 예방"
                )
                for task in generated_tasks["wisdom"]:
                    phase2.tasks[task.id] = task
                plan.phases["auto-phase-2"] = phase2
                plan.phase_order.append("auto-phase-2")
            
            # Wisdom 데이터 Plan에 저장
            from python.project_wisdom import get_wisdom_manager
            wisdom = get_wisdom_manager()
            plan.wisdom_data = {
                "applied_at": datetime.now().isoformat(),
                "total_mistakes_tracked": sum(wisdom.wisdom_data.get("common_mistakes", {}).values()),
                "best_practices_count": len(wisdom.get_best_practices())
            }
            
            # 진행률 초기화
            plan.update_progress()
            
            print(f"✅ 스마트 Plan 생성 완료!")
            print(f"   - 자동 생성 Task: {len(generated_tasks['analysis']) + len(generated_tasks['wisdom'])}개")
        
        return plan
