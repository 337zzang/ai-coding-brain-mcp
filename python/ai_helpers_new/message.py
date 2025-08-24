"""
Message System for REPL Environment
메시지 전달 시스템 - Task 간 협업을 위한 간소화된 통신 시스템

Version: 1.0.0
Author: Claude Code
Created: 2025-08-24
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from .api_response import ok, err

class MessageFacade:
    """
    REPL 메시지 전달 시스템 Facade
    
    Task 간 협업을 위한 최소화된 메시지 시스템
    - note: 메시지 남기기
    - task: 다음 작업 지시
    """
    
    def __init__(self):
        """메시지 시스템 초기화"""
        self._init_storage()
    
    def _init_storage(self):
        """전역 저장소 초기화"""
        import builtins
        
        # globals() 대신 builtins를 통해 안전하게 접근
        # name mangling 방지를 위해 __ 대신 명확한 이름 사용
        if not hasattr(builtins, 'repl_message_notes'):
            builtins.repl_message_notes = []
        if not hasattr(builtins, 'repl_message_tasks'):
            builtins.repl_message_tasks = []
    
    def note(self, msg: str) -> Dict[str, Any]:
        """
        메시지 남기기
        
        Args:
            msg: 남길 메시지
            
        Returns:
            {'ok': True, 'data': msg} or {'ok': False, 'error': str}
        
        Examples:
            >>> h.message.note("데이터 처리 완료")
            📝 [17:30:00] 데이터 처리 완료
            {'ok': True, 'data': '데이터 처리 완료'}
        """
        try:
            import builtins
            
            # 저장소 확인
            if not hasattr(builtins, 'repl_message_notes'):
                self._init_storage()
            
            # 메시지 저장
            time = datetime.now().strftime('%H:%M:%S')
            note_data = {
                'msg': msg,
                'time': time,
                'timestamp': datetime.now().isoformat()
            }
            
            builtins.repl_message_notes.append(note_data)
            
            # stdout 출력
            print(f"📝 [{time}] {msg}")
            
            return ok(msg)
            
        except Exception as e:
            return err(f"메시지 남기기 실패: {str(e)}")
    
    def task(self, instruction: str) -> Dict[str, Any]:
        """
        다음 작업 지시
        
        Args:
            instruction: 지시 내용
            
        Returns:
            {'ok': True, 'data': instruction} or {'ok': False, 'error': str}
        
        Examples:
            >>> h.message.task("테스트 코드 작성 필요")
            📋 [17:30:00] → 테스트 코드 작성 필요
            {'ok': True, 'data': '테스트 코드 작성 필요'}
        """
        try:
            import builtins
            
            # 저장소 확인
            if not hasattr(builtins, 'repl_message_tasks'):
                self._init_storage()
            
            # 지시사항 저장
            time = datetime.now().strftime('%H:%M:%S')
            task_data = {
                'instruction': instruction,
                'time': time,
                'timestamp': datetime.now().isoformat(),
                'completed': False
            }
            
            builtins.repl_message_tasks.append(task_data)
            
            # stdout 출력
            print(f"📋 [{time}] → {instruction}")
            
            return ok(instruction)
            
        except Exception as e:
            return err(f"작업 지시 실패: {str(e)}")
    
    def get_notes(self, last: int = 10) -> Dict[str, Any]:
        """
        최근 메시지 조회 (프로그래밍 용도)
        
        Args:
            last: 조회할 메시지 개수
            
        Returns:
            {'ok': True, 'data': [...]} or {'ok': False, 'error': str}
        """
        try:
            import builtins
            
            notes = getattr(builtins, 'repl_message_notes', [])
            return ok(notes[-last:] if notes else [])
            
        except Exception as e:
            return err(f"메시지 조회 실패: {str(e)}")
    
    def get_tasks(self, pending_only: bool = True) -> Dict[str, Any]:
        """
        작업 지시사항 조회 (프로그래밍 용도)
        
        Args:
            pending_only: True면 미완료 작업만 조회
            
        Returns:
            {'ok': True, 'data': [...]} or {'ok': False, 'error': str}
        """
        try:
            import builtins
            
            tasks = getattr(builtins, '__repl_tasks', [])
            
            if pending_only:
                tasks = [t for t in tasks if not t.get('completed', False)]
            
            return ok(tasks)
            
        except Exception as e:
            return err(f"작업 조회 실패: {str(e)}")
    
    def clear(self) -> Dict[str, Any]:
        """
        모든 메시지 초기화
        
        Returns:
            {'ok': True, 'data': 'cleared'} or {'ok': False, 'error': str}
        """
        try:
            import builtins
            
            builtins.__repl_notes = []
            builtins.__repl_tasks = []
            
            print("🗑️ 모든 메시지가 초기화되었습니다.")
            
            return ok('cleared')
            
        except Exception as e:
            return err(f"초기화 실패: {str(e)}")
    
    def stats(self) -> Dict[str, Any]:
        """
        메시지 통계 조회
        
        Returns:
            {'ok': True, 'data': {'notes': int, 'tasks': int, 'pending': int}}
        """
        try:
            import builtins
            
            notes = getattr(builtins, 'repl_message_notes', [])
            tasks = getattr(builtins, '__repl_tasks', [])
            pending = [t for t in tasks if not t.get('completed', False)]
            
            stats_data = {
                'notes': len(notes),
                'tasks': len(tasks),
                'pending': len(pending)
            }
            
            print(f"📊 메시지 통계: 메시지 {stats_data['notes']}개, 작업 {stats_data['tasks']}개 (대기 {stats_data['pending']}개)")
            
            return ok(stats_data)
            
        except Exception as e:
            return err(f"통계 조회 실패: {str(e)}")

# 모듈 로드 시 자동 초기화
import builtins
if not hasattr(builtins, '__repl_notes'):
    builtins.__repl_notes = []
if not hasattr(builtins, '__repl_tasks'):
    builtins.__repl_tasks = []

# Facade 인스턴스 생성
message_facade = MessageFacade()