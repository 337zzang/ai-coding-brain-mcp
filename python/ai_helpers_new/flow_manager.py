"""
Flow Project v2 - FlowManager
Plan-Task 계층 구조를 지원하는 워크플로우 관리자
"""
import os
import json
from typing import Dict, List, Optional
from datetime import datetime

from .models import Plan, Task
from .workflow_manager import WorkflowManager
from .context_manager import ContextManager



# 워크플로우 디렉토리
WORKFLOW_DIR = ".ai-brain"

class FlowManager:
    """Plan-Task 계층 구조를 지원하는 워크플로우 관리자"""

    def __init__(self, workflow_dir: str = WORKFLOW_DIR):
        self.workflow_dir = workflow_dir
        self.wm = WorkflowManager()  # 기존 기능 재사용
        self.version = "2.0"
        self.plans: Dict[str, Plan] = {}
        self.metadata: Dict = {}

        # 디렉토리 구조 확인
        self._ensure_directories()

        # 데이터 로드
        self._load_data()
        
        # Context Manager 초기화
        self.context_manager = ContextManager(self)

    def _ensure_directories(self):
        """필요한 디렉토리 생성"""
        dirs = ['.ai-brain', '.ai-brain/backups']
        for dir_name in dirs:
            os.makedirs(dir_name, exist_ok=True)

    def _get_file_path(self, filename: str) -> str:
        """파일 경로 생성"""
        return os.path.join(self.workflow_dir, filename)

    def _load_data(self):
        """데이터 로드 (v1/v2 자동 감지)"""
        workflow_path = self._get_file_path('workflow.json')

        if not os.path.exists(workflow_path):
            self._create_default_structure()
            return

        try:
            with open(workflow_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            version = data.get('version', '1.0')

            if version.startswith('1.'):
                # v1 데이터 마이그레이션
                self._migrate_v1_to_v2(data)
            else:
                # v2 데이터 로드
                self._load_v2_data(data)

        except Exception as e:
            print(f"데이터 로드 오류: {e}")
            self._create_default_structure()

    def _create_default_structure(self):
        """기본 구조 생성"""
        self.metadata = {
            'version': self.version,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        self._save_data()

    def _migrate_v1_to_v2(self, v1_data: Dict):
        """v1 데이터를 v2로 마이그레이션"""
        print("🔄 v1 → v2 마이그레이션 시작...")

        # 백업 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self._get_file_path(f'backups/v1_pre_migration_{timestamp}.json')
        os.makedirs(os.path.dirname(backup_path), exist_ok=True)

        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(v1_data, f, indent=2)
        print(f"✅ v1 백업 생성: {backup_path}")

        # 기본 Plan 생성
        default_plan = Plan(
            id="plan_migrated",
            title="Migrated Tasks",
            objective="Tasks migrated from v1 workflow",
            status="active"
        )

        # v1 태스크 변환
        for v1_task in v1_data.get('tasks', []):
            task = Task(
                id=v1_task.get('id', f"task_{datetime.now().timestamp()}"),
                title=v1_task.get('name', v1_task.get('title', 'Untitled')),
                description=v1_task.get('description', ''),
                status=v1_task.get('status', 'todo'),
                plan_id=default_plan.id,
                created_at=v1_task.get('created_at', datetime.now().isoformat()),
                updated_at=v1_task.get('updated_at', datetime.now().isoformat())
            )

            # 완료 시간 처리
            if v1_task.get('status') == 'completed' and v1_task.get('completed_at'):
                task.completed_at = v1_task['completed_at']

            default_plan.tasks.append(task)

        # 진행률 계산
        default_plan.update_progress()

        # 저장
        self.plans[default_plan.id] = default_plan
        self.metadata = {
            'version': self.version,
            'created_at': v1_data.get('created_at', datetime.now().isoformat()),
            'updated_at': datetime.now().isoformat(),
            'migrated_from': 'v1',
            'migration_date': datetime.now().isoformat()
        }

        self._save_data()
        print(f"✅ 마이그레이션 완료: {len(default_plan.tasks)}개 태스크")

    def _load_v2_data(self, data: Dict):
        """v2 데이터 로드"""
        self.metadata = data.get('metadata', {})

        # Plans 로드
        for plan_id, plan_data in data.get('plans', {}).items():
            try:
                plan = Plan.from_dict(plan_data)
                self.plans[plan_id] = plan
            except Exception as e:
                print(f"Plan 로드 오류 ({plan_id}): {e}")

    def _save_data(self):
        """데이터 저장"""
        data = {
            'version': self.version,
            'metadata': self.metadata,
            'plans': {pid: plan.to_dict() for pid, plan in self.plans.items()}
        }

        workflow_path = self._get_file_path('workflow.json')

        try:
            with open(workflow_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"저장 오류: {e}")

    # Plan 관리 메서드
    def create_plan(self, title: str, objective: str = "", **kwargs) -> Plan:
        """새 Plan 생성"""
        plan = Plan(
            title=title,
            objective=objective,
            priority=kwargs.get('priority', 0),
            tags=kwargs.get('tags', [])
        )

        self.plans[plan.id] = plan
        self._save_data()

        print(f"✅ Plan 생성: {plan.title} ({plan.id})")
        return plan

    def get_plan(self, plan_id: str) -> Optional[Plan]:
        """Plan 조회"""
        return self.plans.get(plan_id)

    def update_plan(self, plan_id: str, **updates) -> Optional[Plan]:
        """Plan 업데이트"""
        if plan_id not in self.plans:
            return None

        plan = self.plans[plan_id]

        # 허용된 필드만 업데이트
        allowed_fields = ['title', 'objective', 'status', 'priority', 'tags']
        for field, value in updates.items():
            if field in allowed_fields and hasattr(plan, field):
                setattr(plan, field, value)

        plan.updated_at = datetime.now().isoformat()
        self._save_data()

        return plan

    def get_active_plan(self) -> Optional[Plan]:
        """현재 활성 Plan 반환"""
        active_plans = [p for p in self.plans.values() if p.status == 'active']

        if not active_plans:
            return None

        # 가장 최근 업데이트된 것 반환
        return max(active_plans, key=lambda p: p.updated_at)

    # Task 관리 메서드
    def create_task(self, title: str, plan_id: str = None, **kwargs) -> Task:
        """Task 생성"""
        # Plan 결정
        if not plan_id:
            active_plan = self.get_active_plan()
            if not active_plan:
                # 기본 Plan 생성
                active_plan = self.create_plan("Default Plan", "Auto-created plan")
            plan_id = active_plan.id

        if plan_id not in self.plans:
            raise ValueError(f"Plan '{plan_id}' not found")

        # Task 생성
        task = Task(
            title=title,
            description=kwargs.get('description', ''),
            plan_id=plan_id,
            dependencies=kwargs.get('dependencies', []),
            tags=kwargs.get('tags', []),
            assigned_to=kwargs.get('assigned_to')
        )

        # Plan에 추가
        plan = self.plans[plan_id]
        plan.add_task(task)

        self._save_data()

        print(f"✅ Task 생성: {task.title} ({task.id})")
        return task

    def update_task(self, task_id: str, **updates) -> Optional[Task]:
        """Task 업데이트"""
        # 모든 Plan에서 Task 찾기
        for plan in self.plans.values():
            task = plan.get_task(task_id)
            if task:
                task.update(**updates)
                plan.update_progress()
                self._save_data()
                return task

        return None

    def find_task(self, task_id: str) -> Optional[Task]:
        """Task 찾기"""
        for plan in self.plans.values():
            task = plan.get_task(task_id)
            if task:
                return task
        return None

    # 기존 WorkflowManager 호환성
    def wf_command(self, command: str) -> Dict:
        """통합 명령어 처리 (하위 호환성)"""
        command = command.strip()

        # 기존 명령어는 WorkflowManager로 위임
        if command.startswith('/task') or command == '/status' or command == '/list':
            # 동기화: WorkflowManager의 태스크를 FlowManager로 가져오기
            self._sync_from_workflow_manager()
            return self.wm.wf_command(command)

        # /flow 명령어는 여기서 처리
        if command.startswith('/flow') or command == '/flow':
            return self._handle_flow_command(command)

        return {'ok': False, 'error': '알 수 없는 명령어'}

    def _sync_from_workflow_manager(self):
        """WorkflowManager와 동기화"""
        # 구현 예정 (필요시)
        pass

    def _handle_flow_command(self, command: str) -> Dict:
        """flow 명령어 처리"""
        if command == '/flow':
            # 현재 상태 표시
            return self._show_flow_status()

        # 추가 명령어는 Phase 4에서 구현
        # /flow context 명령어
        if command.startswith('/flow context'):
            return self._handle_context_command(command)

        return {'ok': False, 'error': 'Phase 4에서 구현 예정'}

    def _show_flow_status(self) -> Dict:
        """Flow 상태 표시"""


    def _handle_context_command(self, command: str) -> Dict:
        """context 명령어 처리"""
        parts = command.split()

        if len(parts) == 2 or parts[2] == 'save':
            # 컨텍스트 저장
            result = self.save_context()
            if result['ok']:
                return {'ok': True, 'data': '✅ 컨텍스트 저장 완료', 'type': 'context_command'}
            else:
                return result

        elif parts[2] == 'load' or parts[2] == 'summary':
            # 세션 요약
            summary = self.load_context_summary()
            return {'ok': True, 'data': summary, 'type': 'context_summary'}

        elif len(parts) > 3 and parts[2] == 'decision':
            # 결정사항 추가
            decision = ' '.join(parts[3:])
            self.context_manager.add_decision(decision)
            return {'ok': True, 'data': f'✅ 결정사항 추가: {decision}', 'type': 'context_command'}

        return {'ok': False, 'error': '알 수 없는 context 명령어'}
        active_plan = self.get_active_plan()

        if not active_plan:
            status = "활성 Plan이 없습니다. /flow plan add 명령으로 생성하세요."
        else:
            total_tasks = len(active_plan.tasks)
            completed = sum(1 for t in active_plan.tasks if t.status == 'completed')

            status = f"""📊 Flow Project v2 상태
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 활성 Plan: {active_plan.title}
   목표: {active_plan.objective}
   진행률: {active_plan.progress}% ({completed}/{total_tasks})

💡 다음 명령어: /flow help (Phase 4에서 구현)"""

        return {'ok': True, 'data': status, 'type': 'flow_status'}


    def save_context(self) -> Dict:
        """컨텍스트 저장 (공개 메서드)"""
        return self.context_manager.save_context()

    def load_context_summary(self) -> str:
        """세션 요약 로드"""
        return self.context_manager.generate_session_summary()



    # === Phase 2 추가 메서드 ===

    def delete_plan(self, plan_id: str, cascade: bool = False) -> Dict:
        """Plan 삭제"""
        if plan_id not in self.plans:
            return {'ok': False, 'error': 'Plan not found'}

        plan = self.plans[plan_id]

        if plan.tasks and not cascade:
            return {'ok': False, 'error': f'Plan has {len(plan.tasks)} tasks. Use cascade=True to delete all.'}

        # 백업 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_data = {'deleted_plan': plan.to_dict(), 'timestamp': timestamp}

        # 삭제
        del self.plans[plan_id]
        self._save_data()

        return {'ok': True, 'data': f'Plan {plan.title} deleted'}

    def archive_plan(self, plan_id: str) -> Optional[Plan]:
        """Plan 아카이브 (소프트 삭제)"""
        return self.update_plan(plan_id, status='archived')

    def find_plans(self, **criteria) -> List[Plan]:
        """조건에 맞는 Plan 검색"""
        results = []

        for plan in self.plans.values():
            match = True

            # 상태 필터
            if 'status' in criteria and plan.status != criteria['status']:
                match = False

            # 태그 필터
            if 'tags' in criteria:
                required_tags = set(criteria['tags'])
                if not required_tags.issubset(set(plan.tags)):
                    match = False

            # 텍스트 검색
            if 'search' in criteria:
                search_text = criteria['search'].lower()
                if search_text not in plan.title.lower() and search_text not in plan.objective.lower():
                    match = False

            # 우선순위 필터
            if 'priority' in criteria and plan.priority != criteria['priority']:
                match = False

            if match:
                results.append(plan)

        # 정렬
        sort_by = criteria.get('sort_by', 'updated_at')
        reverse = criteria.get('reverse', True)

        if sort_by == 'progress':
            results.sort(key=lambda p: p.progress, reverse=reverse)
        elif sort_by == 'priority':
            results.sort(key=lambda p: p.priority, reverse=reverse)
        else:
            results.sort(key=lambda p: getattr(p, sort_by, ''), reverse=reverse)

        return results

    def get_plan_statistics(self, plan_id: str) -> Dict:
        """Plan의 상세 통계"""
        if plan_id not in self.plans:
            return {'ok': False, 'error': 'Plan not found'}

        plan = self.plans[plan_id]
        tasks = plan.tasks

        stats = {
            'total_tasks': len(tasks),
            'completed_tasks': sum(1 for t in tasks if t.status == 'completed'),
            'in_progress_tasks': sum(1 for t in tasks if t.status == 'in_progress'),
            'todo_tasks': sum(1 for t in tasks if t.status == 'todo'),
            'progress': plan.progress,
            'created_at': plan.created_at,
            'updated_at': plan.updated_at,
            'has_dependencies': any(t.dependencies for t in tasks),
            'health_score': self._calculate_health_score(plan)
        }

        return {'ok': True, 'data': stats}

    def _calculate_health_score(self, plan: Plan) -> int:
        """Plan의 건강도 점수 (0-100)"""
        score = 100

        # 정체된 태스크 체크 (3일 이상 in_progress)
        from datetime import datetime, timedelta
        now = datetime.now()

        for task in plan.tasks:
            if task.status == 'in_progress':
                updated = datetime.fromisoformat(task.updated_at.replace('Z', '+00:00').replace('+00:00', ''))
                if (now - updated).days > 3:
                    score -= 10

        # 진행률 대비 시간 경과
        created = datetime.fromisoformat(plan.created_at.replace('Z', '+00:00').replace('+00:00', ''))
        days_passed = (now - created).days

        if days_passed > 7 and plan.progress < 50:
            score -= 20

        return max(0, score)

    def move_task(self, task_id: str, to_plan_id: str) -> Dict:
        """Task를 다른 Plan으로 이동"""
        if to_plan_id not in self.plans:
            return {'ok': False, 'error': 'Target plan not found'}

        # 현재 위치 찾기
        from_plan = None
        task = None

        for plan in self.plans.values():
            found_task = plan.get_task(task_id)
            if found_task:
                from_plan = plan
                task = found_task
                break

        if not task:
            return {'ok': False, 'error': 'Task not found'}

        if from_plan.id == to_plan_id:
            return {'ok': False, 'error': 'Task already in target plan'}

        # 이동
        from_plan.remove_task(task_id)
        task.plan_id = to_plan_id

        to_plan = self.plans[to_plan_id]
        to_plan.add_task(task)

        self._save_data()

        return {'ok': True, 'data': f'Task moved from {from_plan.title} to {to_plan.title}'}

    def add_task_dependency(self, task_id: str, depends_on: str) -> Dict:
        """Task 간 의존성 추가"""
        task = self.find_task(task_id)
        dependency = self.find_task(depends_on)

        if not task or not dependency:
            return {'ok': False, 'error': 'Task not found'}

        if task.plan_id != dependency.plan_id:
            return {'ok': False, 'error': 'Dependencies must be in the same plan'}

        # 순환 의존성 체크
        if self._would_create_cycle(task_id, depends_on):
            return {'ok': False, 'error': 'Would create circular dependency'}

        if depends_on not in task.dependencies:
            task.dependencies.append(depends_on)
            task.updated_at = datetime.now().isoformat()
            self._save_data()

        return {'ok': True, 'data': f'Dependency added: {task.title} depends on {dependency.title}'}

    def _would_create_cycle(self, task_id: str, new_dependency: str) -> bool:
        """순환 의존성 검사"""
        visited = set()

        def has_path(from_id: str, to_id: str) -> bool:
            if from_id == to_id:
                return True
            if from_id in visited:
                return False

            visited.add(from_id)
            task = self.find_task(from_id)

            if task:
                for dep in task.dependencies:
                    if has_path(dep, to_id):
                        return True

            return False

        return has_path(new_dependency, task_id)

    def get_task_order(self, plan_id: str) -> List[Task]:
        """의존성을 고려한 Task 실행 순서 (위상 정렬)"""
        if plan_id not in self.plans:
            return []

        plan = self.plans[plan_id]
        tasks = {t.id: t for t in plan.tasks}

        # 진입 차수 계산
        in_degree = {t.id: 0 for t in plan.tasks}

        for task in plan.tasks:
            for dep in task.dependencies:
                if dep in tasks:  # 같은 plan 내의 의존성만
                    in_degree[task.id] += 1

        # 위상 정렬
        queue = [t_id for t_id, degree in in_degree.items() if degree == 0]
        result = []

        while queue:
            task_id = queue.pop(0)
            result.append(tasks[task_id])

            # 이 태스크에 의존하는 태스크들 찾기
            for t in plan.tasks:
                if task_id in t.dependencies:
                    in_degree[t.id] -= 1
                    if in_degree[t.id] == 0:
                        queue.append(t.id)

        return result

# FlowManager 싱글톤
_flow_manager_instance = None

def get_flow_manager() -> FlowManager:
    """FlowManager 싱글톤 인스턴스"""
    global _flow_manager_instance
    if _flow_manager_instance is None:
        _flow_manager_instance = FlowManager()
    return _flow_manager_instance

def flow(command: str) -> Dict:
    """Flow 명령어 헬퍼"""
    fm = get_flow_manager()
    return fm.wf_command(command)
