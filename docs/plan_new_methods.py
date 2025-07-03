"""계획된 새로운 메서드들의 예제 구현"""
from typing import Optional, List
from datetime import datetime


class Task:
    """작업 클래스 예제"""
    def __init__(self, task_id: str):
        self.id = task_id
        self.status = "pending"
        self.dependencies = []
        self.created_at = datetime.now()
        self.updated_at = None
        self.started_at = None
        self.completed_at = None
        self.completed = False
        self.priority = "MEDIUM"
    
    def get_priority_value(self) -> int:
        """우선순위를 숫자로 변환"""
        priority_map = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
        return priority_map.get(self.priority, 2)


class Phase:
    """작업 단계 클래스"""
    def __init__(self):
        self.tasks = []


class PlanManager:
    """계획 관리자 클래스 - 새로운 메서드들 포함"""
    
    def __init__(self):
        self.phases = {}
    
    def get_task_by_id(self, task_id: str) -> Optional[Task]:
        """ID로 작업 찾기"""
        for phase in self.phases.values():
            for task in phase.tasks:
                if task.id == task_id:
                    return task
        return None
    
    def get_next_task(self) -> Optional[Task]:
        """우선순위와 의존성을 고려하여 다음 실행할 작업 반환
        
        Returns:
            Optional[Task]: 다음 실행할 작업, 없으면 None
        """
        ready_tasks = self.get_ready_tasks()
        
        if not ready_tasks:
            return None
        
        # 우선순위로 정렬 (HIGH > MEDIUM > LOW)
        ready_tasks.sort(key=lambda t: t.get_priority_value(), reverse=True)
        
        # 동일 우선순위인 경우 생성 시간 순
        ready_tasks.sort(key=lambda t: (t.get_priority_value(), t.created_at), 
                        reverse=True)
        
        return ready_tasks[0]    
    def get_ready_tasks(self) -> List[Task]:
        """실행 가능한 모든 작업 목록 반환
        
        Returns:
            List[Task]: 실행 가능한 작업들
        """
        ready_tasks = []
        
        for phase in self.phases.values():
            for task in phase.tasks:
                # pending 상태이고 의존성이 충족된 작업
                if task.status == "pending" and self._check_task_dependencies(task):
                    ready_tasks.append(task)
                # 이미 ready 상태인 작업
                elif task.status == "ready":
                    ready_tasks.append(task)
        
        return ready_tasks
    
    def get_blocked_tasks(self) -> List[Task]:
        """의존성으로 인해 차단된 작업 목록 반환
        
        Returns:
            List[Task]: 차단된 작업들
        """
        blocked_tasks = []
        
        for phase in self.phases.values():
            for task in phase.tasks:
                # pending 상태이지만 의존성이 충족되지 않은 작업
                if task.status == "pending" and not self._check_task_dependencies(task):
                    blocked_tasks.append(task)
                # 명시적으로 blocked 상태인 작업
                elif task.status == "blocked":
                    blocked_tasks.append(task)
        
        return blocked_tasks    
    def reorder_by_priority(self) -> None:
        """모든 Phase의 작업을 우선순위로 재정렬"""
        for phase in self.phases.values():
            # Phase 내 작업들을 우선순위로 정렬
            phase.tasks.sort(key=lambda t: t.get_priority_value(), reverse=True)
    
    def update_task_status(self, task_id: str, status: str) -> bool:
        """작업 상태 업데이트
        
        Args:
            task_id: 작업 ID
            status: 새로운 상태
            
        Returns:
            bool: 성공 여부
        """
        task = self.get_task_by_id(task_id)
        if task:
            old_status = task.status
            task.status = status
            task.updated_at = datetime.now()
            
            # 상태 전환에 따른 추가 처리
            if status == "in_progress" and old_status != "in_progress":
                task.started_at = datetime.now()
            elif status == "completed" and old_status != "completed":
                task.completed_at = datetime.now()
                task.completed = True
            
            return True
        return False
    
    def _check_task_dependencies(self, task: Task) -> bool:
        """작업의 의존성 충족 여부 확인 (내부 헬퍼)
        
        Args:
            task: 확인할 작업
            
        Returns:
            bool: 의존성이 모두 충족되면 True
        """
        if not task.dependencies:
            return True
        
        for dep_id in task.dependencies:
            dep_task = self.get_task_by_id(dep_id)
            if not dep_task or dep_task.status != "completed":
                return False
        
        return True
