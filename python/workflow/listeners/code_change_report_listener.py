"""
CodeChangeReportListener - 코드 변경사항 자동 리포트
"""
import logging
from typing import List, Dict, Any, Set
from datetime import datetime
import json
import os
import difflib
from pathlib import Path

from .base import BaseEventListener
from ..models import WorkflowEvent
from python.events.unified_event_types import EventType
from ..events import EventBuilder

logger = logging.getLogger(__name__)


class CodeChangeReportListener(BaseEventListener):
    """코드 변경사항을 추적하고 자동으로 리포트 생성"""
    
    def __init__(self):
        super().__init__()
        self.change_report_file = "code_change_report.md"
        self.changes_tracking = {}
        self.current_task_changes = []
        self.modified_files = set()
        
    def get_subscribed_events(self) -> List[EventType]:
        """구독할 이벤트 타입"""
        return [
            EventType.TASK_STARTED,
            EventType.CODE_MODIFIED,
            EventType.FILE_CREATED,
            EventType.FILE_DELETED,
            EventType.TASK_COMPLETED
        ]
    
    def handle_event(self, event: WorkflowEvent) -> None:
        """이벤트 처리"""
        if event.type == EventType.TASK_STARTED:
            self._on_task_started(event)
        elif event.type == EventType.CODE_MODIFIED:
            self._on_code_modified(event)
        elif event.type == EventType.FILE_CREATED:
            self._on_file_created(event)
        elif event.type == EventType.FILE_DELETED:
            self._on_file_deleted(event)
        elif event.type == EventType.TASK_COMPLETED:
            self._on_task_completed(event)
            
    def _on_task_started(self, event: WorkflowEvent):
        """태스크 시작 시 변경사항 추적 초기화"""
        task_id = event.task_id
        task_title = event.details.get('task_title', '')
        
        # 새 태스크의 변경사항 추적 시작
        self.changes_tracking[task_id] = {
            'title': task_title,
            'started_at': datetime.now().isoformat(),
            'changes': []
        }
        
        self.current_task_changes = []
        self.modified_files = set()
        
        logger.info(f"코드 변경 추적 시작: {task_title}")
        
    def _on_code_modified(self, event: WorkflowEvent):
        """코드 수정 이벤트 처리"""
        file_path = event.details.get('file_path', '')
        change_type = event.details.get('change_type', 'modified')
        line_changes = event.details.get('line_changes', {})
        summary = event.details.get('summary', '')
        
        change_info = {
            'type': 'modified',
            'file': file_path,
            'timestamp': datetime.now().isoformat(),
            'changes': {
                'added_lines': line_changes.get('added', 0),
                'removed_lines': line_changes.get('removed', 0),
                'modified_lines': line_changes.get('modified', 0)
            },
            'summary': summary
        }
        
        self.current_task_changes.append(change_info)
        self.modified_files.add(file_path)
        
        # 즉시 사용자에게 알림
        self._report_single_change(change_info)
        
    def _on_file_created(self, event: WorkflowEvent):
        """파일 생성 이벤트 처리"""
        file_path = event.details.get('file_path', '')
        file_type = event.details.get('file_type', '')
        
        change_info = {
            'type': 'created',
            'file': file_path,
            'timestamp': datetime.now().isoformat(),
            'file_type': file_type,
            'summary': f"새 {file_type} 파일 생성"
        }
        
        self.current_task_changes.append(change_info)
        self.modified_files.add(file_path)
        
        print(f"\n📄 새 파일 생성: {file_path}")
        
    def _on_file_deleted(self, event: WorkflowEvent):
        """파일 삭제 이벤트 처리"""
        file_path = event.details.get('file_path', '')
        
        change_info = {
            'type': 'deleted',
            'file': file_path,
            'timestamp': datetime.now().isoformat(),
            'summary': "파일 삭제"
        }
        
        self.current_task_changes.append(change_info)
        
        print(f"\n🗑️ 파일 삭제: {file_path}")
        
    def _on_task_completed(self, event: WorkflowEvent):
        """태스크 완료 시 전체 변경사항 리포트 생성"""
        task_id = event.task_id
        task_title = event.details.get('task_title', '')
        
        if task_id in self.changes_tracking:
            self.changes_tracking[task_id]['completed_at'] = datetime.now().isoformat()
            self.changes_tracking[task_id]['changes'] = self.current_task_changes
            
            # 전체 리포트 생성
            report = self._generate_change_report(task_id, task_title)
            
            # 리포트 저장
            self._save_report(report)
            
            # 콘솔에 요약 출력
            self._print_summary(task_id)
            
    def _report_single_change(self, change_info: Dict[str, Any]):
        """단일 변경사항 즉시 리포트"""
        file_path = change_info['file']
        change_type = change_info['type']
        
        if change_type == 'modified':
            changes = change_info['changes']
            total_changes = changes['added_lines'] + changes['removed_lines'] + changes['modified_lines']
            
            print(f"\n✏️ 코드 수정: {file_path}")
            print(f"   📊 변경 내용: +{changes['added_lines']} -{changes['removed_lines']} ~{changes['modified_lines']}")
            if change_info.get('summary'):
                print(f"   💡 요약: {change_info['summary']}")
                
    def _generate_change_report(self, task_id: str, task_title: str) -> str:
        """태스크의 전체 변경사항 리포트 생성"""
        task_data = self.changes_tracking.get(task_id, {})
        changes = task_data.get('changes', [])
        
        report = f"# 코드 변경사항 리포트\n\n"
        report += f"## 태스크: {task_title}\n\n"
        report += f"- 시작 시간: {task_data.get('started_at', '')}\n"
        report += f"- 완료 시간: {task_data.get('completed_at', '')}\n"
        report += f"- 수정된 파일: {len(self.modified_files)}개\n\n"
        
        # 파일별 변경사항 정리
        report += "## 파일별 변경사항\n\n"
        
        # 파일별로 그룹화
        file_changes = {}
        for change in changes:
            file_path = change['file']
            if file_path not in file_changes:
                file_changes[file_path] = []
            file_changes[file_path].append(change)
            
        # 각 파일의 변경사항 출력
        for file_path, changes in file_changes.items():
            report += f"### 📄 {file_path}\n\n"
            
            for change in changes:
                if change['type'] == 'modified':
                    c = change['changes']
                    report += f"- **수정**: +{c['added_lines']} -{c['removed_lines']} ~{c['modified_lines']}\n"
                    if change.get('summary'):
                        report += f"  - {change['summary']}\n"
                elif change['type'] == 'created':
                    report += f"- **생성**: 새 {change.get('file_type', '파일')} 생성\n"
                elif change['type'] == 'deleted':
                    report += f"- **삭제**: 파일 제거\n"
                    
            report += "\n"
            
        # 요약 통계
        report += "## 요약\n\n"
        total_added = sum(c['changes']['added_lines'] for c in changes if c['type'] == 'modified')
        total_removed = sum(c['changes']['removed_lines'] for c in changes if c['type'] == 'modified')
        total_modified = sum(c['changes']['modified_lines'] for c in changes if c['type'] == 'modified')
        
        report += f"- 총 추가된 라인: {total_added}\n"
        report += f"- 총 삭제된 라인: {total_removed}\n"
        report += f"- 총 수정된 라인: {total_modified}\n"
        report += f"- 영향받은 파일: {len(self.modified_files)}개\n"
        
        return report
        
    def _save_report(self, report: str):
        """리포트를 파일로 저장"""
        try:
            # 기존 리포트에 추가
            with open(self.change_report_file, 'a', encoding='utf-8') as f:
                f.write(f"\n{'-' * 80}\n")
                f.write(report)
                f.write(f"\n{'-' * 80}\n")
            logger.info(f"변경사항 리포트 저장: {self.change_report_file}")
        except Exception as e:
            logger.error(f"리포트 저장 실패: {e}")
            
    def _print_summary(self, task_id: str):
        """콘솔에 변경사항 요약 출력"""
        task_data = self.changes_tracking.get(task_id, {})
        changes = task_data.get('changes', [])
        
        print(f"\n📊 코드 변경사항 요약:")
        print(f"  - 수정된 파일: {len(self.modified_files)}개")
        
        total_added = sum(c['changes']['added_lines'] for c in changes if c['type'] == 'modified')
        total_removed = sum(c['changes']['removed_lines'] for c in changes if c['type'] == 'modified')
        
        print(f"  - 추가된 라인: +{total_added}")
        print(f"  - 삭제된 라인: -{total_removed}")
        print(f"  - 자세한 리포트: {self.change_report_file}")
        
    def track_code_change(self, file_path: str, change_type: str, **details):
        """외부에서 코드 변경을 수동으로 추적"""
        change_event = WorkflowEvent(
            type=EventType.CODE_MODIFIED,
            details={
                'file_path': file_path,
                'change_type': change_type,
                **details
            }
        )
        self.handle_event(change_event)