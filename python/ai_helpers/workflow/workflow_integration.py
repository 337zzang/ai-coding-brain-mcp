"""
Workflow Integration Module
flow_project와 workflow protocol을 통합하는 핵심 모듈
"""

import json
import os
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path
import uuid

class WorkflowIntegration:
    """flow_project와 workflow protocol 통합 클래스"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent.parent
        self.memory_path = self.project_root / "memory"
        self.workflow_path = self.memory_path / "workflow.json"
        self.events_path = self.memory_path / "workflow_events.json"
        self.context_path = self.memory_path / "context.json"

        # 이벤트 리스너
        self.event_listeners = {
            'project_switched': [],
            'workflow_created': [],
            'task_updated': [],
            'state_changed': []
        }

        self._ensure_paths()

    def _ensure_paths(self):
        """필요한 경로 확인 및 생성"""
        self.memory_path.mkdir(exist_ok=True)

        # 초기 파일 생성
        if not self.workflow_path.exists():
            self._save_workflow_data({"plans": [], "current_plan_id": None})

        if not self.events_path.exists():
            self._save_events([])

    def flow_project(self, project_name: str) -> Dict[str, Any]:
        """
        프로젝트 전환 및 워크플로우 동기화

        Args:
            project_name: 전환할 프로젝트 이름

        Returns:
            통합된 프로젝트 및 워크플로우 상태
        """
        try:
            # 1. 프로젝트 컨텍스트 로드
            project_context = self._load_project_context(project_name)

            # 2. 워크플로우 상태 복구
            workflow_state = self._recover_workflow_state(project_name)

            # 3. 이벤트 발행
            event = self._emit_event('project_switched', {
                'project_name': project_name,
                'timestamp': datetime.now().isoformat(),
                'context': project_context,
                'workflow': workflow_state
            })

            # 4. 상태 동기화
            result = self._sync_state(project_name, project_context, workflow_state)

            # 5. 응답 구성
            return {
                'success': True,
                'project_name': project_name,
                'context': project_context,
                'workflow': workflow_state,
                'event_id': event['id'],
                'message': f'✅ 프로젝트 전환 완료: {project_name}'
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'❌ 프로젝트 전환 실패: {str(e)}'
            }

    def _load_project_context(self, project_name: str) -> Dict[str, Any]:
        """프로젝트 컨텍스트 로드"""
        try:
            # context.json에서 프로젝트 정보 로드
            if self.context_path.exists():
                with open(self.context_path, 'r', encoding='utf-8') as f:
                    context = json.load(f)
                    if context.get('project_name') == project_name:
                        return context

            # 새 프로젝트인 경우 기본 컨텍스트 생성
            return {
                'project_name': project_name,
                'created_at': datetime.now().isoformat(),
                'version': '1.0.0',
                'state': 'active'
            }
        except Exception as e:
            print(f"⚠️ 컨텍스트 로드 오류: {e}")
            return {}

    def _recover_workflow_state(self, project_name: str) -> Dict[str, Any]:
        """워크플로우 상태 복구"""
        workflow_data = self._load_workflow_data()

        # 현재 활성 플랜 찾기
        current_plan_id = workflow_data.get('current_plan_id')
        if current_plan_id:
            for plan in workflow_data.get('plans', []):
                if plan.get('id') == current_plan_id:
                    return {
                        'current_plan': plan,
                        'status': plan.get('status', 'unknown'),
                        'progress': self._calculate_progress(plan)
                    }

        return {
            'current_plan': None,
            'status': 'idle',
            'progress': 0
        }

    def _emit_event(self, event_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """이벤트 발행"""
        event = {
            'id': str(uuid.uuid4()),
            'type': event_type,
            'timestamp': datetime.now().isoformat(),
            'data': data
        }

        # 이벤트 저장
        events = self._load_events()
        events.append(event)
        self._save_events(events[-100:])  # 최근 100개만 유지

        # 리스너 실행
        for listener in self.event_listeners.get(event_type, []):
            try:
                listener(event)
            except Exception as e:
                print(f"⚠️ 이벤트 리스너 오류: {e}")

        return event

    def _sync_state(self, project_name: str, context: Dict, workflow: Dict) -> bool:
        """상태 동기화"""
        try:
            # context.json 업데이트
            context.update({
                'project_name': project_name,
                'last_updated': datetime.now().isoformat()
            })

            with open(self.context_path, 'w', encoding='utf-8') as f:
                json.dump(context, f, indent=2, ensure_ascii=False)

            return True
        except Exception as e:
            print(f"❌ 상태 동기화 실패: {e}")
            return False

    def _calculate_progress(self, plan: Dict) -> float:
        """플랜 진행률 계산"""
        tasks = plan.get('tasks', [])
        if not tasks:
            return 0.0

        completed = sum(1 for task in tasks if task.get('status') == 'completed')
        return (completed / len(tasks)) * 100

    def _load_workflow_data(self) -> Dict:
        """워크플로우 데이터 로드"""
        try:
            with open(self.workflow_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {"plans": [], "current_plan_id": None}

    def _save_workflow_data(self, data: Dict):
        """워크플로우 데이터 저장"""
        with open(self.workflow_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _load_events(self) -> List[Dict]:
        """이벤트 로드"""
        try:
            with open(self.events_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # 리스트가 아닌 경우 빈 리스트 반환
                if isinstance(data, list):
                    return data
                else:
                    return []
        except:
            return []
    def _save_events(self, events: List[Dict]):
        """이벤트 저장"""
        with open(self.events_path, 'w', encoding='utf-8') as f:
            json.dump(events, f, indent=2, ensure_ascii=False)

    # 이벤트 리스너 등록
    def on(self, event_type: str, listener):
        """이벤트 리스너 등록"""
        if event_type in self.event_listeners:
            self.event_listeners[event_type].append(listener)

    # Workflow Protocol 메서드들
    def create_plan(self, name: str, tasks: List[Dict]) -> Dict:
        """워크플로우 플랜 생성"""
        plan = {
            'id': str(uuid.uuid4()),
            'name': name,
            'status': 'draft',
            'created_at': datetime.now().isoformat(),
            'tasks': tasks
        }

        workflow_data = self._load_workflow_data()
        workflow_data['plans'].append(plan)
        workflow_data['current_plan_id'] = plan['id']
        self._save_workflow_data(workflow_data)

        self._emit_event('workflow_created', plan)

        return plan

    def update_task(self, task_id: str, updates: Dict) -> bool:
        """태스크 업데이트"""
        workflow_data = self._load_workflow_data()

        for plan in workflow_data['plans']:
            for task in plan.get('tasks', []):
                if task.get('id') == task_id:
                    task.update(updates)
                    task['updated_at'] = datetime.now().isoformat()

                    self._save_workflow_data(workflow_data)
                    self._emit_event('task_updated', {
                        'task_id': task_id,
                        'updates': updates
                    })
                    return True

        return False


# 통합 인스턴스 생성
workflow_integration = WorkflowIntegration()
