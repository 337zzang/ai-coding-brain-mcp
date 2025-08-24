"""
Message System for Task Orchestration
태스크 오케스트레이션 메시지 시스템

Version: 3.0.0 (Simplified Orchestration)
Author: Claude Code
Created: 2025-08-24
Updated: 2025-08-24

4가지 핵심 메시지:
- task: 업무지시 [TASK]
- share: 변수공유 [SHARE]
- call: 에이전트호출 [CALL]
- stop: 중단요청 [STOP]
"""

from typing import Dict, Any
from datetime import datetime
from .api_response import ok, err

class MessageFacade:
    """
    오케스트레이션 메시지 시스템 (4종)
    
    모든 메서드는 메시지 문자열 하나만 받음
    형식: "[TYPE] agent | content"
    """
    
    def task(self, msg: str) -> Dict[str, Any]:
        """
        업무지시 메시지
        
        Args:
            msg: 업무지시 내용 (예: "analyzer | 코드 분석 시작")
            
        Returns:
            {'ok': True, 'data': msg} or {'ok': False, 'error': str}
        
        Examples:
            >>> h.message.task("analyzer | 코드 분석 시작")
            📋 [17:30:00] [TASK] analyzer | 코드 분석 시작
        """
        try:
            time = datetime.now().strftime('%H:%M:%S')
            print(f"📋 [{time}] [TASK] {msg}")
            return ok(msg)
        except Exception as e:
            return err(f"업무지시 실패: {str(e)}")
    
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