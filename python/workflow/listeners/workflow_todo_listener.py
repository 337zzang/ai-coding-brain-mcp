"""
WorkflowTodoListener - 워크플로우와 Claude Code Todo 연동
"""
import logging
from typing import List, Dict, Any
from datetime import datetime
import json
import os

from .base import BaseEventListener
from ..models import WorkflowEvent, EventType, TaskStatus
from ..events import EventBuilder

logger = logging.getLogger(__name__)


class WorkflowTodoListener(BaseEventListener):
    """워크플로우 태스크와 Claude Code TodoWrite 연동"""
    
    def __init__(self):
        super().__init__()
        self.claude_todo_file = "claude_todos.json"
        self.current_workflow_task = None
        self.pending_approval = {}
        
    def get_subscribed_events(self) -> List[EventType]:
        """구독할 이벤트 타입"""
        return [
            EventType.PLAN_CREATED,
            EventType.TASK_ADDED,
            EventType.TASK_STARTED,
            EventType.TASK_COMPLETED,
            EventType.PLAN_COMPLETED
        ]
    
    def handle_event(self, event: WorkflowEvent) -> None:
        """이벤트 처리"""
        if event.type == EventType.PLAN_CREATED:
            self._on_plan_created(event)
        elif event.type == EventType.TASK_ADDED:
            self._on_task_added(event)
        elif event.type == EventType.TASK_STARTED:
            self._on_task_started(event)
        elif event.type == EventType.TASK_COMPLETED:
            self._on_task_completed(event)
        elif event.type == EventType.PLAN_COMPLETED:
            self._on_plan_completed(event)
            
    def _on_plan_created(self, event: WorkflowEvent):
        """플랜 생성 시 사용자에게 승인 요청"""
        plan_name = event.details.get('plan_name', '')
        plan_id = event.plan_id
        
        # 승인 대기 상태로 저장
        self.pending_approval[plan_id] = {
            'type': 'plan',
            'name': plan_name,
            'created_at': datetime.now().isoformat()
        }
        
        # 사용자에게 알림
        print(f"\n🎯 새로운 플랜이 생성되었습니다: {plan_name}")
        print("📋 태스크를 추가한 후 계획을 검토하고 승인해주세요.")
        
    def _on_task_added(self, event: WorkflowEvent):
        """태스크 추가 시 계획 업데이트"""
        task_title = event.details.get('task_title', '')
        
        # 태스크 목록 업데이트
        if event.plan_id in self.pending_approval:
            if 'tasks' not in self.pending_approval[event.plan_id]:
                self.pending_approval[event.plan_id]['tasks'] = []
            
            self.pending_approval[event.plan_id]['tasks'].append({
                'id': event.task_id,
                'title': task_title,
                'status': 'pending'
            })
            
            print(f"  ➕ 태스크 추가: {task_title}")
            
    def _on_task_started(self, event: WorkflowEvent):
        """태스크 시작 시 사용자 승인 요청"""
        task_title = event.details.get('task_title', '')
        task_id = event.task_id
        plan_id = event.plan_id
        
        # 태스크 계획 생성
        task_plan = self._generate_task_plan(task_title)
        
        # 승인 대기 상태로 저장
        approval_key = f"{plan_id}_{task_id}"
        self.pending_approval[approval_key] = {
            'type': 'task',
            'task_id': task_id,
            'task_title': task_title,
            'plan_id': plan_id,
            'task_plan': task_plan,
            'status': 'pending_approval',
            'created_at': datetime.now().isoformat()
        }
        
        # 사용자에게 승인 요청
        print(f"\n🎯 태스크 시작 요청: {task_title}")
        print(f"\n📋 실행 계획:")
        for i, step in enumerate(task_plan, 1):
            print(f"  {i}. {step['content']} ({step['estimated_time']})")
        
        print(f"\n❓ 이 계획으로 진행하시겠습니까?")
        print(f"   승인: approve_task('{approval_key}')")
        print(f"   수정: modify_task_plan('{approval_key}', new_plan)")
        print(f"   취소: reject_task('{approval_key}')")
        print(f"\n⏳ 사용자 승인을 기다리는 중...")
        
    def _on_task_completed(self, event: WorkflowEvent):
        """태스크 완료 시 다음 태스크 준비"""
        task_title = event.details.get('task_title', '')
        
        print(f"\n✅ 태스크 완료: {task_title}")
        print("🔄 Git 커밋 및 푸시가 자동으로 실행됩니다.")
        
        # 현재 태스크 초기화
        self.current_workflow_task = None
        
    def _on_plan_completed(self, event: WorkflowEvent):
        """플랜 완료 시 최종 보고"""
        plan_name = event.details.get('plan_name', '')
        stats = event.details.get('stats', {})
        
        print(f"\n🎉 플랜 완료: {plan_name}")
        print(f"📊 완료된 태스크: {stats.get('completed_tasks', 0)}개")
        print(f"⏱️ 총 소요 시간: {stats.get('total_duration_seconds', 0):.1f}초")
        
    def _create_claude_todo(self, task_id: str, task_title: str):
        """Claude Code Todo 생성을 위한 정보 저장"""
        todo_info = {
            'workflow_task_id': task_id,
            'workflow_task_title': task_title,
            'subtasks': self._generate_subtasks(task_title),
            'created_at': datetime.now().isoformat()
        }
        
        # JSON 파일로 저장 (Claude Code가 읽을 수 있도록)
        try:
            with open(self.claude_todo_file, 'w', encoding='utf-8') as f:
                json.dump(todo_info, f, ensure_ascii=False, indent=2)
            logger.info(f"Claude Todo 정보 저장: {self.claude_todo_file}")
        except Exception as e:
            logger.error(f"Claude Todo 정보 저장 실패: {e}")
            
    def _generate_subtasks(self, task_title: str) -> List[Dict[str, str]]:
        """태스크 제목을 기반으로 서브태스크 생성"""
        subtasks = []
        
        # 키워드 기반 서브태스크 생성
        if "테스트" in task_title:
            subtasks.extend([
                {"content": "테스트 케이스 설계", "status": "pending"},
                {"content": "단위 테스트 작성", "status": "pending"},
                {"content": "통합 테스트 실행", "status": "pending"}
            ])
        elif "구현" in task_title or "개발" in task_title:
            subtasks.extend([
                {"content": "요구사항 분석", "status": "pending"},
                {"content": "코드 구현", "status": "pending"},
                {"content": "코드 리뷰 및 리팩토링", "status": "pending"}
            ])
        elif "문서" in task_title:
            subtasks.extend([
                {"content": "문서 구조 설계", "status": "pending"},
                {"content": "내용 작성", "status": "pending"},
                {"content": "검토 및 최종화", "status": "pending"}
            ])
        else:
            # 기본 서브태스크
            subtasks.extend([
                {"content": "작업 분석 및 계획", "status": "pending"},
                {"content": "실행", "status": "pending"},
                {"content": "검증 및 완료", "status": "pending"}
            ])
            
        return subtasks
        
    def get_approval_status(self, plan_id: str) -> Dict[str, Any]:
        """플랜 승인 상태 반환"""
        return self.pending_approval.get(plan_id, {})
        
    def _generate_task_plan(self, task_title: str) -> List[Dict[str, str]]:
        """태스크 제목을 기반으로 상세 실행 계획 생성"""
        plan = []
        
        # 키워드 기반 계획 생성
        if "파일 생성" in task_title:
            plan.extend([
                {"content": "파일 구조 및 내용 설계", "estimated_time": "2분"},
                {"content": "코드 작성 및 파일 생성", "estimated_time": "3분"},
                {"content": "생성된 파일 검증", "estimated_time": "1분"}
            ])
        elif "수정" in task_title or "변경" in task_title:
            plan.extend([
                {"content": "기존 코드 분석", "estimated_time": "2분"},
                {"content": "수정 사항 구현", "estimated_time": "5분"},
                {"content": "변경사항 테스트", "estimated_time": "2분"},
                {"content": "변경사항 추적 확인", "estimated_time": "1분"}
            ])
        elif "테스트" in task_title:
            plan.extend([
                {"content": "테스트 케이스 설계", "estimated_time": "3분"},
                {"content": "테스트 코드 작성", "estimated_time": "4분"},
                {"content": "테스트 실행 및 검증", "estimated_time": "2분"}
            ])
        elif "커밋" in task_title or "Git" in task_title:
            plan.extend([
                {"content": "변경사항 확인", "estimated_time": "1분"},
                {"content": "Git 커밋 실행", "estimated_time": "1분"},
                {"content": "푸시 및 결과 확인", "estimated_time": "1분"}
            ])
        else:
            # 기본 계획
            plan.extend([
                {"content": "작업 요구사항 분석", "estimated_time": "2분"},
                {"content": "실행 및 구현", "estimated_time": "5분"},
                {"content": "결과 검증 및 정리", "estimated_time": "2분"}
            ])
            
        return plan

    def approve_task(self, approval_key: str):
        """태스크 승인 및 실행 시작"""
        if approval_key in self.pending_approval:
            approval_info = self.pending_approval[approval_key]
            
            if approval_info['type'] == 'task':
                # 승인 상태 업데이트
                approval_info['status'] = 'approved'
                approval_info['approved_at'] = datetime.now().isoformat()
                
                # 현재 작업 중인 태스크 저장
                self.current_workflow_task = {
                    'id': approval_info['task_id'],
                    'title': approval_info['task_title'],
                    'started_at': datetime.now().isoformat()
                }
                
                # Claude Code Todo 생성
                self._create_claude_todo(approval_info['task_id'], approval_info['task_title'])
                
                print(f"✅ 태스크가 승인되어 실행을 시작합니다: {approval_info['task_title']}")
                print("📝 Claude Code의 TodoWrite로 서브태스크가 생성됩니다.")
                
                return True
        
        print(f"❌ 승인할 태스크를 찾을 수 없습니다: {approval_key}")
        return False
    
    def modify_task_plan(self, approval_key: str, new_plan: List[Dict[str, str]]):
        """태스크 계획 수정"""
        if approval_key in self.pending_approval:
            self.pending_approval[approval_key]['task_plan'] = new_plan
            self.pending_approval[approval_key]['modified_at'] = datetime.now().isoformat()
            
            print(f"✏️ 태스크 계획이 수정되었습니다.")
            print(f"📋 수정된 계획:")
            for i, step in enumerate(new_plan, 1):
                print(f"  {i}. {step['content']} ({step.get('estimated_time', '시간미정')})")
            
            return True
        return False
    
    def reject_task(self, approval_key: str):
        """태스크 거부"""
        if approval_key in self.pending_approval:
            approval_info = self.pending_approval.pop(approval_key)
            print(f"❌ 태스크가 거부되었습니다: {approval_info['task_title']}")
            return True
        return False

    def approve_plan(self, plan_id: str):
        """플랜 승인 처리"""
        if plan_id in self.pending_approval:
            self.pending_approval[plan_id]['approved'] = True
            self.pending_approval[plan_id]['approved_at'] = datetime.now().isoformat()
            print(f"✅ 플랜이 승인되었습니다.")
            return True
        return False