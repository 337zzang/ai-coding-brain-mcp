"""
GitAutoCommitListener - 태스크 완료 시 자동 Git 커밋/푸시
"""
import logging
from typing import List, Dict, Any
from datetime import datetime
import subprocess
import os

from .base import BaseEventListener
from ..models import WorkflowEvent, EventType
from ..events import EventBuilder

logger = logging.getLogger(__name__)


class GitAutoCommitListener(BaseEventListener):
    """태스크 완료 시 자동으로 Git 커밋과 푸시 수행"""
    
    def __init__(self):
        super().__init__()
        self.auto_push = True  # 자동 푸시 활성화
        self.commit_prefix = "✨"  # 커밋 메시지 프리픽스
        self.pending_commits = []
        
    def get_subscribed_events(self) -> List[EventType]:
        """구독할 이벤트 타입"""
        return [
            EventType.TASK_COMPLETED,
            EventType.PLAN_COMPLETED
        ]
    
    def handle_event(self, event: WorkflowEvent) -> None:
        """이벤트 처리"""
        if event.type == EventType.TASK_COMPLETED:
            self._on_task_completed(event)
        elif event.type == EventType.PLAN_COMPLETED:
            self._on_plan_completed(event)
            
    def _on_task_completed(self, event: WorkflowEvent):
        """태스크 완료 시 자동 커밋"""
        task_title = event.details.get('task_title', '')
        task_id = event.task_id
        duration = event.details.get('duration')
        
        print(f"\n🔄 Git 자동 커밋 준비 중...")
        
        # Git 상태 확인
        status = self._git_status()
        if not status['has_changes']:
            print("ℹ️ 커밋할 변경사항이 없습니다.")
            return
            
        # 변경된 파일 목록
        print(f"📝 변경된 파일: {len(status['modified_files'])}개")
        for file in status['modified_files'][:5]:  # 최대 5개만 표시
            print(f"  - {file}")
        if len(status['modified_files']) > 5:
            print(f"  ... 외 {len(status['modified_files']) - 5}개")
            
        # 커밋 메시지 생성
        commit_message = self._generate_commit_message(task_title, status)
        
        # 변경사항 스테이징
        self._git_add_all()
        
        # 커밋 실행
        commit_result = self._git_commit(commit_message)
        if commit_result['success']:
            print(f"✅ 커밋 성공: {commit_result['commit_hash'][:8]}")
            print(f"📝 메시지: {commit_message}")
            
            # 자동 푸시
            if self.auto_push:
                push_result = self._git_push()
                if push_result['success']:
                    print(f"🚀 푸시 성공!")
                else:
                    print(f"⚠️ 푸시 실패: {push_result['error']}")
                    self.pending_commits.append(commit_result['commit_hash'])
        else:
            print(f"❌ 커밋 실패: {commit_result['error']}")
            
    def _on_plan_completed(self, event: WorkflowEvent):
        """플랜 완료 시 최종 커밋"""
        plan_name = event.details.get('plan_name', '')
        stats = event.details.get('stats', {})
        
        # 남은 변경사항이 있다면 최종 커밋
        status = self._git_status()
        if status['has_changes']:
            commit_message = f"🎉 완료: {plan_name} (태스크 {stats.get('completed_tasks', 0)}개 완료)"
            
            self._git_add_all()
            commit_result = self._git_commit(commit_message)
            
            if commit_result['success']:
                print(f"\n🏁 플랜 완료 커밋: {commit_result['commit_hash'][:8]}")
                
        # 미푸시 커밋이 있다면 모두 푸시
        if self.pending_commits:
            print(f"\n📤 미푸시 커밋 {len(self.pending_commits)}개 푸시 중...")
            push_result = self._git_push()
            if push_result['success']:
                print("✅ 모든 커밋 푸시 완료!")
                self.pending_commits = []
                
    def _git_status(self) -> Dict[str, Any]:
        """Git 상태 확인"""
        try:
            # 변경된 파일 확인
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                capture_output=True,
                text=True,
                check=True
            )
            
            lines = result.stdout.strip().split('\n') if result.stdout.strip() else []
            modified_files = []
            added_files = []
            deleted_files = []
            
            for line in lines:
                if line:
                    status_code = line[:2]
                    file_path = line[3:]
                    
                    if 'M' in status_code:
                        modified_files.append(file_path)
                    elif 'A' in status_code or '?' in status_code:
                        added_files.append(file_path)
                    elif 'D' in status_code:
                        deleted_files.append(file_path)
                        
            return {
                'has_changes': len(lines) > 0,
                'modified_files': modified_files,
                'added_files': added_files,
                'deleted_files': deleted_files,
                'total_changes': len(lines)
            }
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Git status 실패: {e}")
            return {'has_changes': False, 'error': str(e)}
            
    def _git_add_all(self):
        """모든 변경사항 스테이징"""
        try:
            subprocess.run(['git', 'add', '-A'], check=True)
            logger.info("Git add 완료")
        except subprocess.CalledProcessError as e:
            logger.error(f"Git add 실패: {e}")
            
    def _git_commit(self, message: str) -> Dict[str, Any]:
        """Git 커밋 실행"""
        try:
            result = subprocess.run(
                ['git', 'commit', '-m', message],
                capture_output=True,
                text=True,
                check=True
            )
            
            # 커밋 해시 추출
            hash_result = subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                capture_output=True,
                text=True,
                check=True
            )
            
            commit_hash = hash_result.stdout.strip()
            
            return {
                'success': True,
                'commit_hash': commit_hash,
                'message': message
            }
            
        except subprocess.CalledProcessError as e:
            return {
                'success': False,
                'error': e.stderr or str(e)
            }
            
    def _git_push(self) -> Dict[str, Any]:
        """Git 푸시 실행"""
        try:
            # 현재 브랜치 확인
            branch_result = subprocess.run(
                ['git', 'branch', '--show-current'],
                capture_output=True,
                text=True,
                check=True
            )
            current_branch = branch_result.stdout.strip()
            
            # 푸시 실행
            result = subprocess.run(
                ['git', 'push', 'origin', current_branch],
                capture_output=True,
                text=True,
                check=True
            )
            
            return {
                'success': True,
                'branch': current_branch
            }
            
        except subprocess.CalledProcessError as e:
            return {
                'success': False,
                'error': e.stderr or str(e)
            }
            
    def _generate_commit_message(self, task_title: str, status: Dict[str, Any]) -> str:
        """커밋 메시지 자동 생성"""
        # 기본 메시지
        message = f"{self.commit_prefix} {task_title}"
        
        # 변경 내용 요약 추가
        changes_summary = []
        if status.get('modified_files'):
            changes_summary.append(f"수정 {len(status['modified_files'])}개")
        if status.get('added_files'):
            changes_summary.append(f"추가 {len(status['added_files'])}개")
        if status.get('deleted_files'):
            changes_summary.append(f"삭제 {len(status['deleted_files'])}개")
            
        if changes_summary:
            message += f" ({', '.join(changes_summary)})"
            
        return message
        
    def enable_auto_push(self, enabled: bool = True):
        """자동 푸시 활성화/비활성화"""
        self.auto_push = enabled
        logger.info(f"자동 푸시: {'활성화' if enabled else '비활성화'}")