"""
User Command API
================

사용자가 사용할 수 있는 명령어 인터페이스
검증, 권한 체크, 사용자 친화적 메시지 제공
"""

import os
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from ..models import Task, TaskStatus
from ..errors import WorkflowError, ErrorCode
from ..parser import CommandParser, ParsedCommand
from python.ai_helpers.helper_result import HelperResult
from .decorators import (
    require_active_plan, 
    log_command, 
    validate_arguments,
    auto_save,
    rate_limit
)

logger = logging.getLogger(__name__)


class UserCommandAPI:
    """
    사용자 명령어 API
    
    사용자가 실행할 수 있는 모든 명령어를 정의
    각 명령어는 검증과 권한 체크를 거침
    """
    
    def __init__(self, workflow_manager):
        self.manager = workflow_manager
        self.parser = CommandParser()
        
        # 확장 명령어 핸들러 등록
        self._register_extended_commands()
        
    def _register_extended_commands(self):
        """확장 명령어 핸들러 등록"""
        # 기존 핸들러에 추가
        extended_handlers = {
            'auto': self._handle_auto,
            'pause': self._handle_pause,
            'resume': self._handle_resume,
            'skip': self._handle_skip,
            'delete': self._handle_delete,
            'move': self._handle_move,
            'depend': self._handle_depend,
            'export': self._handle_export,
            'import': self._handle_import,
            'template': self._handle_template,
            'report': self._handle_report,
            'stats': self._handle_stats
        }
        
        # manager의 command_handlers에 추가
        if hasattr(self.manager, 'command_handlers'):
            self.manager.command_handlers.update(extended_handlers)
            
    # === 기본 명령어 개선 ===
    
    @log_command("user")
    def execute_command(self, command_str: str) -> HelperResult:
        """사용자 명령어 실행 (개선된 버전)"""
        try:
            # 명령어 파싱
            parsed = self.parser.parse(command_str)
            
            # 사용자 권한 체크 (향후 구현)
            # self._check_user_permission(parsed.command)
            
            # 명령어 핸들러 찾기
            handler = self.manager.command_handlers.get(parsed.command)
            if handler:
                return handler(parsed)
            else:
                raise WorkflowError(
                    ErrorCode.INVALID_COMMAND,
                    f"알 수 없는 명령어: {parsed.command}"
                )
            
        except WorkflowError as e:
            # 사용자 친화적 에러 메시지
            user_message = self._get_user_friendly_error(e)
            return HelperResult(False, error=user_message, data=e.to_dict())
            
        except Exception as e:
            logger.error(f"Command execution error: {e}")
            return HelperResult(
                False, 
                error="명령어 실행 중 오류가 발생했습니다. 명령어를 확인해주세요."
            )
            
    def _get_user_friendly_error(self, error: WorkflowError) -> str:
        """사용자 친화적 에러 메시지 생성"""
        error_messages = {
            ErrorCode.NO_ACTIVE_PLAN: "활성 플랜이 없습니다. /start로 새 플랜을 생성하세요.",
            ErrorCode.TASK_NOT_FOUND: "태스크를 찾을 수 없습니다. /task list로 확인하세요.",
            ErrorCode.INVALID_COMMAND: "올바르지 않은 명령어입니다. /help로 도움말을 확인하세요.",
            ErrorCode.INVALID_ARGUMENT: "명령어 인자가 올바르지 않습니다.",
            ErrorCode.PERMISSION_DENIED: "이 명령어를 실행할 권한이 없습니다.",
            ErrorCode.RATE_LIMIT_EXCEEDED: "너무 많은 요청입니다. 잠시 후 다시 시도해주세요."
        }
        
        return error_messages.get(error.code, error.message)
        
    # === 자동 실행 모드 ===
    
    @log_command("user")
    def _handle_auto(self, parsed: ParsedCommand) -> HelperResult:
        """자동 실행 모드 제어"""
        from ..commands.auto_executor import AutoTaskExecutor
        
        # AutoTaskExecutor 인스턴스 가져오기 또는 생성
        if not hasattr(self.manager, '_auto_executor'):
            self.manager._auto_executor = AutoTaskExecutor(self.manager)
            
        executor = self.manager._auto_executor
        
        if not parsed.title or parsed.title.lower() == 'status':
            # 상태 확인
            status = "활성화" if executor.is_running else "비활성화"
            return HelperResult(True, data={
                'auto_mode': executor.is_running,
                'message': f"자동 실행 모드: {status}"
            })
            
        elif parsed.title.lower() == 'on':
            # 활성화
            executor.start()
            return HelperResult(True, data={
                'auto_mode': True,
                'message': "✅ 자동 실행 모드가 활성화되었습니다"
            })
            
        elif parsed.title.lower() == 'off':
            # 비활성화
            executor.stop()
            return HelperResult(True, data={
                'auto_mode': False,
                'message': "⏹️ 자동 실행 모드가 비활성화되었습니다"
            })
            
        else:
            return HelperResult(False, error="사용법: /auto [on|off|status]")
            
    @log_command("user")
    def _handle_pause(self, parsed: ParsedCommand) -> HelperResult:
        """자동 실행 일시 정지"""
        if hasattr(self.manager, '_auto_executor'):
            self.manager._auto_executor.pause()
            return HelperResult(True, data={
                'message': "⏸️ 자동 실행이 일시 정지되었습니다"
            })
        return HelperResult(False, error="자동 실행 모드가 활성화되지 않았습니다")
        
    @log_command("user")
    def _handle_resume(self, parsed: ParsedCommand) -> HelperResult:
        """자동 실행 재개"""
        if hasattr(self.manager, '_auto_executor'):
            self.manager._auto_executor.resume()
            return HelperResult(True, data={
                'message': "▶️ 자동 실행이 재개되었습니다"
            })
        return HelperResult(False, error="자동 실행 모드가 활성화되지 않았습니다")
        
    @log_command("user")
    @require_active_plan
    def _handle_skip(self, parsed: ParsedCommand) -> HelperResult:
        """현재 태스크 건너뛰기"""
        current = self.manager.get_current_task()
        if not current:
            return HelperResult(False, error="건너뛸 태스크가 없습니다")
            
        # 태스크 취소 처리
        reason = parsed.title or "사용자가 건너뛰기 요청"
        self.manager.cancel_task(current.id, reason)
        
        # 다음 태스크로 이동
        next_task = self.manager.get_current_task()
        
        return HelperResult(True, data={
            'skipped_task': current.title,
            'next_task': next_task.title if next_task else None,
            'message': f"⏭️ '{current.title}' 태스크를 건너뛰었습니다"
        })
        
    # === 태스크 관리 확장 ===
    
    @log_command("user")
    @require_active_plan
    @validate_arguments(task_id=lambda x: x and len(x) > 0)
    def _handle_delete(self, parsed: ParsedCommand) -> HelperResult:
        """태스크 삭제"""
        task_id = parsed.title
        
        # 태스크 찾기
        task = None
        task_index = -1
        for i, t in enumerate(self.manager.state.current_plan.tasks):
            if t.id == task_id or str(i+1) == task_id:
                task = t
                task_index = i
                break
                
        if not task:
            return HelperResult(False, error=f"태스크를 찾을 수 없습니다: {task_id}")
            
        # 삭제
        self.manager.state.current_plan.tasks.pop(task_index)
        
        # current_task_index 조정
        if self.manager.state.current_plan.current_task_index >= task_index:
            self.manager.state.current_plan.current_task_index = max(0, 
                self.manager.state.current_plan.current_task_index - 1)
            
        self.manager._save_data()
        
        return HelperResult(True, data={
            'deleted_task': task.title,
            'message': f"🗑️ '{task.title}' 태스크가 삭제되었습니다"
        })
        
    @log_command("user")
    @require_active_plan
    def _handle_move(self, parsed: ParsedCommand) -> HelperResult:
        """태스크 순서 변경"""
        # 파싱: /move <task_id> <position>
        parts = parsed.title.split()
        if len(parts) != 2:
            return HelperResult(False, error="사용법: /move <태스크번호> <새위치>")
            
        try:
            task_id = parts[0]
            new_pos = int(parts[1]) - 1  # 1-based to 0-based
            
            # 태스크 찾기
            task = None
            old_pos = -1
            for i, t in enumerate(self.manager.state.current_plan.tasks):
                if str(i+1) == task_id or t.id == task_id:
                    task = t
                    old_pos = i
                    break
                    
            if not task:
                return HelperResult(False, error=f"태스크를 찾을 수 없습니다: {task_id}")
                
            # 범위 체크
            if new_pos < 0 or new_pos >= len(self.manager.state.current_plan.tasks):
                return HelperResult(False, error="올바르지 않은 위치입니다")
                
            # 이동
            self.manager.state.current_plan.tasks.pop(old_pos)
            self.manager.state.current_plan.tasks.insert(new_pos, task)
            
            self.manager._save_data()
            
            return HelperResult(True, data={
                'moved_task': task.title,
                'from_position': old_pos + 1,
                'to_position': new_pos + 1,
                'message': f"↕️ '{task.title}'을(를) {new_pos + 1}번 위치로 이동했습니다"
            })
            
        except ValueError:
            return HelperResult(False, error="위치는 숫자여야 합니다")
            
    @log_command("user")
    @require_active_plan
    def _handle_depend(self, parsed: ParsedCommand) -> HelperResult:
        """태스크 의존성 설정"""
        # 파싱: /depend <task_id> <depends_on_id>
        parts = parsed.title.split()
        if len(parts) != 2:
            return HelperResult(False, error="사용법: /depend <태스크번호> <의존태스크번호>")
            
        task_id = parts[0]
        depends_on_id = parts[1]
        
        # 태스크 찾기
        task = None
        depends_on = None
        
        for i, t in enumerate(self.manager.state.current_plan.tasks):
            if str(i+1) == task_id or t.id == task_id:
                task = t
            if str(i+1) == depends_on_id or t.id == depends_on_id:
                depends_on = t
                
        if not task:
            return HelperResult(False, error=f"태스크를 찾을 수 없습니다: {task_id}")
        if not depends_on:
            return HelperResult(False, error=f"의존 태스크를 찾을 수 없습니다: {depends_on_id}")
            
        # 의존성 설정 (outputs에 저장)
        if 'dependencies' not in task.outputs:
            task.outputs['dependencies'] = []
        if depends_on.id not in task.outputs['dependencies']:
            task.outputs['dependencies'].append(depends_on.id)
            
        self.manager._save_data()
        
        return HelperResult(True, data={
            'task': task.title,
            'depends_on': depends_on.title,
            'message': f"🔗 '{task.title}'이(가) '{depends_on.title}'에 의존하도록 설정했습니다"
        })
        
    # === 워크플로우 관리 ===
    
    @log_command("user")
    def _handle_export(self, parsed: ParsedCommand) -> HelperResult:
        """워크플로우 내보내기"""
        import json
        from datetime import datetime
        
        if not self.manager.state.current_plan:
            return HelperResult(False, error="내보낼 플랜이 없습니다")
            
        # 내보낼 데이터 구성
        export_data = {
            'version': '1.0',
            'exported_at': datetime.now().isoformat(),
            'plan': self.manager.state.current_plan.to_dict(),
            'metadata': {
                'project': self.manager.project_name,
                'total_tasks': len(self.manager.state.current_plan.tasks)
            }
        }
        
        # 파일명 생성
        filename = parsed.title or f"workflow_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        if not filename.endswith('.json'):
            filename += '.json'
            
        # 저장
        export_path = f"exports/{filename}"
        os.makedirs("exports", exist_ok=True)
        
        with open(export_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
            
        return HelperResult(True, data={
            'filename': filename,
            'path': export_path,
            'message': f"📤 워크플로우를 내보냈습니다: {filename}"
        })
        
    @log_command("user")
    def _handle_import(self, parsed: ParsedCommand) -> HelperResult:
        """워크플로우 가져오기"""
        # 구현 예정
        return HelperResult(False, error="이 기능은 아직 구현 중입니다")
        
    @log_command("user")
    def _handle_template(self, parsed: ParsedCommand) -> HelperResult:
        """워크플로우 템플릿 관리"""
        # 구현 예정
        return HelperResult(False, error="이 기능은 아직 구현 중입니다")
        
    # === 분석 및 보고 ===
    
    @log_command("user")
    @require_active_plan
    def _handle_report(self, parsed: ParsedCommand) -> HelperResult:
        """진행 상황 리포트"""
        report_type = parsed.title or "progress"
        
        if report_type == "progress":
            return self._generate_progress_report()
        elif report_type == "timeline":
            return self._generate_timeline_report()
        else:
            return HelperResult(False, error="사용법: /report [progress|timeline]")
            
    def _generate_progress_report(self) -> HelperResult:
        """진행 상황 리포트 생성"""
        plan = self.manager.state.current_plan
        total = len(plan.tasks)
        completed = len([t for t in plan.tasks if t.status == TaskStatus.COMPLETED])
        in_progress = len([t for t in plan.tasks if t.status == TaskStatus.IN_PROGRESS])
        
        report = f"""
📊 진행 상황 리포트
==================
플랜: {plan.name}
전체: {total}개 태스크
완료: {completed}개 ({completed/total*100:.1f}%)
진행중: {in_progress}개
대기중: {total - completed - in_progress}개

태스크별 상태:
"""
        for i, task in enumerate(plan.tasks, 1):
            status_icon = {
                TaskStatus.COMPLETED: "✅",
                TaskStatus.IN_PROGRESS: "🔄",
                TaskStatus.CANCELLED: "❌"
            }.get(task.status, "⏳")
            
            report += f"{i}. {status_icon} {task.title}\n"
            
        return HelperResult(True, data={
            'report': report,
            'stats': {
                'total': total,
                'completed': completed,
                'in_progress': in_progress,
                'completion_rate': completed/total if total > 0 else 0
            }
        })
        
    def _generate_timeline_report(self) -> HelperResult:
        """타임라인 리포트 생성"""
        # 구현 예정
        return HelperResult(False, error="타임라인 리포트는 아직 구현 중입니다")
        
    @log_command("user")
    def _handle_stats(self, parsed: ParsedCommand) -> HelperResult:
        """통계 정보"""
        # Internal API 활용
        from .internal_api import InternalWorkflowAPI
        internal_api = InternalWorkflowAPI(self.manager)
        
        if self.manager.state.current_plan:
            stats = internal_api.calculate_plan_statistics(self.manager.state.current_plan)
            
            return HelperResult(True, data={
                'stats': stats,
                'message': f"""
📈 워크플로우 통계
================
전체 태스크: {stats['total_tasks']}개
완료율: {stats['completion_rate']*100:.1f}%
평균 소요시간: {stats['average_duration_seconds']:.0f}초
예상 남은 시간: {stats['estimated_remaining_seconds']:.0f}초
"""
            })
            
        return HelperResult(False, error="통계를 계산할 플랜이 없습니다")


# Export
__all__ = ['UserCommandAPI']
