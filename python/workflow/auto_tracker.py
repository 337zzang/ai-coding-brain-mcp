"""
WorkflowV2 자동 추적 시스템
파일 생성, Git 커밋, 코드 변경 등을 자동으로 추적
"""
import os
import json
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Set
import subprocess

from .helper import get_manager, track_file_artifact, track_commit_artifact
from .schema import ArtifactType

class AutoTracker:
    """작업 중 생성된 산출물 자동 추적"""

    def __init__(self):
        self.manager = get_manager()
        self.tracking_enabled = True
        self.tracked_files: Set[str] = set()
        self.last_commit_hash = self._get_last_commit_hash()

    def _get_last_commit_hash(self) -> str:
        """마지막 커밋 해시 가져오기"""
        try:
            result = subprocess.run(['git', 'rev-parse', 'HEAD'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        return ""

    def _get_current_task_id(self) -> int:
        """현재 진행 중인 태스크 ID"""
        return self.manager.workflow.focus_task_id

    def track_file_creation(self, file_path: str):
        """파일 생성 추적"""
        if not self.tracking_enabled:
            return

        task_id = self._get_current_task_id()
        if not task_id:
            return

        # 이미 추적된 파일인지 확인
        if file_path in self.tracked_files:
            return

        self.tracked_files.add(file_path)

        # 파일 타입 판단
        ext = os.path.splitext(file_path)[1].lower()
        file_type = "document" if ext in ['.md', '.txt', '.rst'] else "file"

        # 산출물 추가
        self.manager.add_artifact(
            task_id, 
            file_type,
            path=file_path,
            description=f"Created {os.path.basename(file_path)}"
        )

        print(f"  📎 자동 추적: {file_path}")

    def track_file_modification(self, file_path: str):
        """파일 수정 추적"""
        if not self.tracking_enabled:
            return

        task_id = self._get_current_task_id()
        if not task_id:
            return

        # 주요 수정만 추적 (너무 많은 추적 방지)
        task = self.manager.get_task(task_id)
        if task and not any(a.path == file_path for a in task.artifacts):
            self.manager.add_artifact(
                task_id,
                "file",
                path=file_path,
                description=f"Modified {os.path.basename(file_path)}"
            )

    def track_git_commit(self):
        """Git 커밋 추적"""
        if not self.tracking_enabled:
            return

        task_id = self._get_current_task_id()
        if not task_id:
            return

        # 새 커밋 확인
        current_hash = self._get_last_commit_hash()
        if current_hash and current_hash != self.last_commit_hash:
            # 커밋 메시지 가져오기
            try:
                result = subprocess.run(['git', 'log', '-1', '--pretty=%B'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    commit_message = result.stdout.strip()

                    self.manager.add_artifact(
                        task_id,
                        "commit",
                        description=f"{current_hash[:7]}: {commit_message}"
                    )

                    print(f"  📎 커밋 추적: {current_hash[:7]}")
                    self.last_commit_hash = current_hash
            except:
                pass

    def track_code_execution(self, code: str, success: bool):
        """코드 실행 추적 (중요한 것만)"""
        if not self.tracking_enabled:
            return

        task_id = self._get_current_task_id()
        if not task_id:
            return

        # 중요한 작업만 추적 (파일 생성, 주요 함수 실행 등)
        important_keywords = ['create_file', 'write_file', 'git_commit', 
                            'workflow', 'deploy', 'test', 'build']

        if any(keyword in code.lower() for keyword in important_keywords):
            # 코드 스니펫 저장 (처음 100자만)
            snippet = code[:100] + "..." if len(code) > 100 else code
            snippet = snippet.replace('\n', ' ')

            self.manager.add_artifact(
                task_id,
                "code",
                content=snippet,
                description=f"{'✅' if success else '❌'} Code execution"
            )

    def generate_task_summary(self, task_id: int) -> str:
        """태스크 완료 시 자동 요약 생성"""
        task = self.manager.get_task(task_id)
        if not task:
            return ""

        summary_parts = []

        # 산출물 요약
        file_count = len([a for a in task.artifacts if a.type == ArtifactType.FILE])
        commit_count = len([a for a in task.artifacts if a.type == ArtifactType.COMMIT])
        doc_count = len([a for a in task.artifacts if a.type == ArtifactType.DOCUMENT])

        if file_count:
            summary_parts.append(f"{file_count}개 파일 생성/수정")
        if commit_count:
            summary_parts.append(f"{commit_count}개 커밋")
        if doc_count:
            summary_parts.append(f"{doc_count}개 문서 작성")

        # 주요 파일 목록
        important_files = []
        for artifact in task.artifacts:
            if artifact.path and artifact.type in [ArtifactType.FILE, ArtifactType.DOCUMENT]:
                important_files.append(os.path.basename(artifact.path))

        if important_files:
            summary_parts.append(f"주요 파일: {', '.join(important_files[:3])}")

        return ". ".join(summary_parts) if summary_parts else "작업 완료"

# 전역 트래커 인스턴스
_tracker = None

def get_tracker() -> AutoTracker:
    """트래커 인스턴스 가져오기"""
    global _tracker
    if _tracker is None:
        _tracker = AutoTracker()
    return _tracker

# helpers 통합을 위한 래퍼 함수들
def auto_track_file_creation(file_path: str):
    """파일 생성 자동 추적 (helpers.create_file 후크용)"""
    get_tracker().track_file_creation(file_path)

def auto_track_git_commit():
    """Git 커밋 자동 추적 (helpers.git_commit 후크용)"""
    get_tracker().track_git_commit()

def auto_complete_task(task_id: int):
    """태스크 자동 완료 처리"""
    tracker = get_tracker()
    manager = get_manager()

    # 자동 요약 생성
    summary = tracker.generate_task_summary(task_id)

    # 태스크 완료
    task = manager.complete_task(task_id, summary)
    if task:
        print(f"\n✅ 태스크 자동 완료: {task.name}")
        print(f"📝 요약: {summary}")
        if task.duration_minutes:
            print(f"⏱️ 소요시간: {task.duration_minutes}분")
