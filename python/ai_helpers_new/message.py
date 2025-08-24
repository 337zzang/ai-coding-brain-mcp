"""
Message System for REPL-Claude Communication
REPL과 Claude Code 간 통신 시스템

Version: 4.0.0 (Simplified & Practical)
Author: Claude Code
Created: 2025-08-24
Updated: 2025-08-24

핵심 메시지 (2종):
- task: 작업 흐름 추적 [TASK]
- share: 영속적 자원 공유 [SHARE]

용도:
- REPL 내부 상태를 stdout으로 Claude에게 전달
- 재사용 가능한 함수/변수/상태 알림
- Think 도구를 위한 컨텍스트 제공
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from .api_response import ok, err

class MessageFacade:
    """
    REPL-Claude 통신 시스템 (심플 버전)
    
    핵심 기능:
    - task(): 작업 흐름 추적 (시작/전환/완료)
    - share(): 영속적 자원 공유 (함수/변수/상태)
    
    사용 원칙:
    - "Claude가 나중에 이걸 쓸까?" → YES면 share()
    - "작업 흐름이 바뀌나?" → YES면 task()
    """
    
    def task(self, msg: str, level: str = "INFO") -> Dict[str, Any]:
        """
        작업 흐름 추적 메시지
        
        Args:
            msg: 작업 내용 (예: "분석 완료 → 최적화 시작")
            level: 중요도 (INFO/SUCCESS/WARNING/ERROR)
            
        Returns:
            {'ok': True, 'data': {'msg': msg, 'level': level, 'time': time}}
        
        Examples:
            >>> h.message.task("분석 시작")
            >>> h.message.task("분석 완료 → 최적화 시작")
            >>> h.message.task("최적화 완료", "SUCCESS")
            >>> h.message.task("메모리 부족", "ERROR")
        """
        try:
            time = datetime.now().strftime('%H:%M:%S')
            
            # 레벨별 이모지
            icons = {
                "INFO": "📋",
                "SUCCESS": "✅", 
                "WARNING": "⚠️",
                "ERROR": "❌"
            }
            icon = icons.get(level.upper(), "📋")
            
            # 화살표 패턴 감지 (작업 전환)
            if "→" in msg or "->" in msg:
                icon = "🔄"  # 전환 표시
            
            print(f"{icon} [{time}] [TASK] {msg}")
            
            return ok({
                'msg': msg,
                'level': level,
                'time': time
            })
        except Exception as e:
            return err(f"작업 추적 실패: {str(e)}")
    
    def share(self, msg: str) -> Dict[str, Any]:
        """
        변수공유 메시지
        
        Args:
            msg: 공유 내용 (예: "analyzer | files=142,bugs=3")
            
        Returns:
            {'ok': True, 'data': msg} or {'ok': False, 'error': str}
        
        Examples:
            >>> h.message.share("analyzer | files=142,bugs=3")
            📦 [17:30:00] [SHARE] analyzer | files=142,bugs=3
        """
        try:
            time = datetime.now().strftime('%H:%M:%S')
            print(f"📦 [{time}] [SHARE] {msg}")
            return ok(msg)
        except Exception as e:
            return err(f"변수공유 실패: {str(e)}")
    
    def call(self, msg: str) -> Dict[str, Any]:
        """
        에이전트호출 메시지
        
        Args:
            msg: 호출 내용 (예: "analyzer -> test-runner | 테스트 필요")
            
        Returns:
            {'ok': True, 'data': msg} or {'ok': False, 'error': str}
        
        Examples:
            >>> h.message.call("analyzer -> test-runner | 테스트 필요")
            🔔 [17:30:00] [CALL] analyzer -> test-runner | 테스트 필요
        """
        try:
            time = datetime.now().strftime('%H:%M:%S')
            print(f"🔔 [{time}] [CALL] {msg}")
            return ok(msg)
        except Exception as e:
            return err(f"에이전트호출 실패: {str(e)}")
    
    def stop(self, msg: str) -> Dict[str, Any]:
        """
        중단요청 메시지
        
        Args:
            msg: 중단 내용 (예: "o3 | 메모리 부족")
            
        Returns:
            {'ok': True, 'data': msg} or {'ok': False, 'error': str}
        
        Examples:
            >>> h.message.stop("o3 | 메모리 부족")
            🛑 [17:30:00] [STOP] o3 | 메모리 부족
        """
        try:
            time = datetime.now().strftime('%H:%M:%S')
            print(f"🛑 [{time}] [STOP] {msg}")
            return ok(msg)
        except Exception as e:
            return err(f"중단요청 실패: {str(e)}")

# Facade 인스턴스 생성
message_facade = MessageFacade()