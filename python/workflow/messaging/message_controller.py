"""
Integrated Message Controller for Workflow
=========================================
메시지 출력과 필요한 처리를 한곳에서 수행
"""

from typing import Dict, Any, Optional
import json
import time
import os
from datetime import datetime
from contextlib import contextmanager


class Logger:
    """간단한 로거"""
    def __init__(self, log_dir: str = None):
        if log_dir is None:
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            log_dir = os.path.join(project_root, 'memory', 'logs', 'workflow')

        self.log_dir = log_dir
        os.makedirs(self.log_dir, exist_ok=True)

    def log(self, msg_type: str, entity_id: str, data: Dict):
        """로그 기록"""
        today = datetime.now().strftime('%Y%m%d')
        log_file = os.path.join(self.log_dir, f'workflow_{today}.log')

        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'type': msg_type,
            'entity_id': entity_id,
            'data': data
        }

        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')


class ErrorHandler:
    """간단한 에러 핸들러"""
    def __init__(self):
        self.error_count = 0
        self.errors = []

    def handle(self, entity_id: str, error_data: Dict):
        """에러 처리"""
        self.error_count += 1
        self.errors.append({
            'entity_id': entity_id,
            'error': error_data,
            'timestamp': time.time()
        })

        # 에러 통계 출력
        print(f"st:error_stats:system:{json.dumps({'total_errors': self.error_count})}")


class GitService:
    """Git 자동화 서비스"""
    def __init__(self, auto_commit: bool = False):
        self.auto_commit = auto_commit

    def check_auto_commit(self, entity_id: str):
        """자동 커밋 체크"""
        if not self.auto_commit:
            return

        # Git 상태 체크 (helpers 사용)
        try:
            git_status = helpers.git_status()
            modified_count = len(git_status.get('modified', []))

            if modified_count > 0:
                print(f"st:git_check:git:{json.dumps({'modified': modified_count})}")
                # 여기서 실제 auto commit을 수행할 수 있음
        except:
            pass


class MessageController:
    """통합 메시지 컨트롤러"""

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.suppressed = False

        # 서비스 초기화 (설정에 따라)
        self.logger = Logger() if self.config.get('logging', True) else None
        self.error_handler = ErrorHandler() if self.config.get('error_handling', True) else None
        self.git_service = GitService(self.config.get('auto_commit', False))

    def emit(self, msg_type: str, entity_id: str, data: Dict[str, Any]):
        """메시지 출력 및 처리"""
        if self.suppressed:
            return

        # 1. 항상 stdout으로 출력 (AI가 볼 수 있도록)
        print(f"st:{msg_type}:{entity_id}:{json.dumps(data)}")

        # 2. 로깅 (설정되어 있으면)
        if self.logger:
            self.logger.log(msg_type, entity_id, data)

        # 3. 타입별 추가 처리
        if msg_type == 'error_occurred' and self.error_handler:
            self.error_handler.handle(entity_id, data)

        elif msg_type in ['task_completed', 'plan_completed'] and self.git_service:
            self.git_service.check_auto_commit(entity_id)

    def emit_transition(self, entity_id: str, old_state: str, new_state: str, 
                       context: Optional[Dict] = None):
        """상태 전이 메시지"""
        self.emit(
            msg_type='state_changed',
            entity_id=entity_id,
            data={
                'from': old_state,
                'to': new_state,
                'context': context or {},
                'timestamp': time.time()
            }
        )

    def emit_error(self, entity_id: str, error_type: str, message: str):
        """에러 메시지"""
        self.emit(
            msg_type='error_occurred',
            entity_id=entity_id,
            data={
                'error_type': error_type,
                'message': message,
                'timestamp': time.time()
            }
        )

    def emit_summary(self, entity_id: str, status: str, stats: Dict):
        """작업 완료 요약"""
        self.emit(
            msg_type='task_summary',
            entity_id=entity_id,
            data={
                'status': status,
                'stats': stats,
                'timestamp': time.time()
            }
        )

    @contextmanager
    def suppress(self):
        """메시지 발행 일시 중단"""
        old_state = self.suppressed
        self.suppressed = True
        try:
            yield
        finally:
            self.suppressed = old_state


# 전역 인스턴스 (기본 설정)
message_controller = MessageController({
    'logging': True,
    'error_handling': True,
    'auto_commit': False  # 기본값은 False
})
