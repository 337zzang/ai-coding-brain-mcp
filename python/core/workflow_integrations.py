"""
WorkflowManager 확장 - ProjectAnalyzer/Wisdom 통합
"""
import os
from typing import Dict, List
from datetime import datetime
from core.models import Task, Phase, Plan, TaskStatus


class WorkflowIntegrations:
    """ProjectAnalyzer와 Wisdom 시스템 통합 기능"""
    
    def __init__(self, workflow_manager):
        self.workflow_manager = workflow_manager
        self.context = workflow_manager.context
    
    def analyze_and_generate_tasks(self, project_path: str = ".") -> Dict[str, List[Task]]:
        """ProjectAnalyzer를 사용하여 자동으로 Task 생성"""
        from analyzers.project_analyzer import ProjectAnalyzer
        from python.project_wisdom import get_wisdom_manager
        
        analyzer = ProjectAnalyzer(project_path)
        wisdom = get_wisdom_manager()
        
        # 프로젝트 분석
        print("🔍 프로젝트 분석 중...")
        # 프로젝트 분석 및 업데이트
        analyzer.analyze_and_update()
        
        # 분석 결과 가져오기
        manifest = analyzer.get_manifest()
        briefing = analyzer.get_briefing_data()
        
        # 결과를 통합 형식으로 변환
        analysis_result = {
            "total_files": briefing.get("total_files", 0),
            "file_types": briefing.get("file_types", {}),
            "average_complexity": briefing.get("average_complexity", 0),
            "complex_files": [],
            "largest_files": []
        }
        
        # 복잡도가 높은 파일 찾기
        if manifest and "files" in manifest:
            files_with_complexity = []
            for file_path, file_info in manifest["files"].items():
                if file_info.get("complexity", 0) > 10:  # 복잡도 10 이상
                    files_with_complexity.append({
                        "file": file_path,
                        "complexity": file_info.get("complexity", 0),
                        "functions": file_info.get("functions", [])
                    })
            
            # 복잡도 순으로 정렬
            files_with_complexity.sort(key=lambda x: x["complexity"], reverse=True)
            analysis_result["complex_files"] = files_with_complexity
            
            # 큰 파일 찾기
            files_with_size = []
            for file_path, file_info in manifest["files"].items():
                size = file_info.get("size", 0)
                if size > 5000:  # 5KB 이상
                    files_with_size.append({
                        "file": file_path,
                        "size": size
                    })
            
            files_with_size.sort(key=lambda x: x["size"], reverse=True)
            analysis_result["largest_files"] = files_with_size
        
        # 분석 결과를 Plan에 저장
        if hasattr(self.context, 'plan') and self.context.plan and hasattr(self.context.plan, 'project_insights'):
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
        try:
            common_mistakes = wisdom.get_common_mistakes()
            if isinstance(common_mistakes, dict):
                mistakes_list = list(common_mistakes.items())
            else:
                # get_common_mistakes가 리스트를 반환하는 경우
                mistakes_list = common_mistakes[:3] if common_mistakes else []
        except:
            mistakes_list = []
        
        for idx, item in enumerate(mistakes_list[:3]):
            if isinstance(item, tuple) and len(item) == 2:
                mistake_type, count = item
            else:
                continue
            task = Task(
                id=f"auto-wisdom-{idx+1}",
                title=f"예방: {mistake_type} 패턴 개선",
                description=f"{count}회 발생한 실수 패턴 예방",
                priority="high" if count > 5 else "medium",
                auto_generated=True,
                wisdom_hints=[f"{mistake_type} 방지: 주의 깊은 검토 필요"],
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
        from core.models import Plan
        plan = Plan(name=name, description=description)
        self.workflow_manager.context.plan = plan
        
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
                "best_practices_count": len(wisdom.wisdom_data.get("best_practices", []))
            }
            
            # 진행률 초기화
            plan.update_progress()
            
            print(f"✅ 스마트 Plan 생성 완료!")
            print(f"   - 자동 생성 Task: {len(generated_tasks['analysis']) + len(generated_tasks['wisdom'])}개")
        
        return plan
