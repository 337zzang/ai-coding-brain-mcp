"""
Message System for REPL Environment - Lightweight Version
메시지 출력 시스템 - 순수 stdout 출력만 제공

Version: 2.0.0 (Simplified)
Author: Claude Code
Created: 2025-08-24
Updated: 2025-08-24
"""

from typing import Dict, Any
from datetime import datetime
from .api_response import ok, err

class MessageFacade:
    """
    경량화된 메시지 출력 시스템
    
    순수 stdout 출력만 제공:
    - note: 상태 메시지 출력
    - task: 작업 지시 출력
    - warn: 경고 메시지 출력
    - error: 에러 메시지 출력
    - success: 성공 메시지 출력
    """
    
    def note(self, msg: str) -> Dict[str, Any]:
        """
        일반 메시지 출력
        
        Args:
            msg: 출력할 메시지
            
        Returns:
            {'ok': True, 'data': msg} or {'ok': False, 'error': str}
        
        Examples:
            >>> h.message.note("데이터 처리 중...")
            📝 [17:30:00] 데이터 처리 중...
        """
        try:
            time = datetime.now().strftime('%H:%M:%S')
            print(f"📝 [{time}] {msg}")
            return ok(msg)
        except Exception as e:
            return err(f"메시지 출력 실패: {str(e)}")
    
    def task(self, instruction: str) -> Dict[str, Any]:
        """
        작업 지시 출력
        
        Args:
            instruction: 지시 내용
            
        Returns:
            {'ok': True, 'data': instruction} or {'ok': False, 'error': str}
        
        Examples:
            >>> h.message.task("다음 단계 진행 필요")
            📋 [17:30:00] → 다음 단계 진행 필요
        """
        try:
            time = datetime.now().strftime('%H:%M:%S')
            print(f"📋 [{time}] → {instruction}")
            return ok(instruction)
        except Exception as e:
            return err(f"작업 지시 출력 실패: {str(e)}")
    
    def warn(self, msg: str) -> Dict[str, Any]:
        """
        경고 메시지 출력
        
        Args:
            msg: 경고 메시지
            
        Returns:
            {'ok': True, 'data': msg} or {'ok': False, 'error': str}
        
        Examples:
            >>> h.message.warn("메모리 사용량 80% 초과")
            ⚠️ [17:30:00] 메모리 사용량 80% 초과
        """
        try:
            time = datetime.now().strftime('%H:%M:%S')
            print(f"⚠️ [{time}] {msg}")
            return ok(msg)
        except Exception as e:
            return err(f"경고 출력 실패: {str(e)}")
    
    def error(self, msg: str) -> Dict[str, Any]:
        """
        에러 메시지 출력
        
        Args:
            msg: 에러 메시지
            
        Returns:
            {'ok': True, 'data': msg} or {'ok': False, 'error': str}
        
        Examples:
            >>> h.message.error("파일을 찾을 수 없음")
            ❌ [17:30:00] 파일을 찾을 수 없음
        """
        try:
            time = datetime.now().strftime('%H:%M:%S')
            print(f"❌ [{time}] {msg}")
            return ok(msg)
        except Exception as e:
            return err(f"에러 출력 실패: {str(e)}")
    
    def success(self, msg: str) -> Dict[str, Any]:
        """
        성공 메시지 출력
        
        Args:
            msg: 성공 메시지
            
        Returns:
            {'ok': True, 'data': msg} or {'ok': False, 'error': str}
        
        Examples:
            >>> h.message.success("모든 테스트 통과!")
            ✅ [17:30:00] 모든 테스트 통과!
        """
        try:
            time = datetime.now().strftime('%H:%M:%S')
            print(f"✅ [{time}] {msg}")
            return ok(msg)
        except Exception as e:
            return err(f"성공 메시지 출력 실패: {str(e)}")
    
    def info(self, msg: str) -> Dict[str, Any]:
        """
        정보 메시지 출력 (아이콘 없는 버전)
        
        Args:
            msg: 정보 메시지
            
        Returns:
            {'ok': True, 'data': msg} or {'ok': False, 'error': str}
        
        Examples:
            >>> h.message.info("현재 진행률: 50%")
            ℹ️ [17:30:00] 현재 진행률: 50%
        """
        try:
            time = datetime.now().strftime('%H:%M:%S')
            print(f"ℹ️ [{time}] {msg}")
            return ok(msg)
        except Exception as e:
            return err(f"정보 출력 실패: {str(e)}")
    
    def debug(self, msg: str) -> Dict[str, Any]:
        """
        디버그 메시지 출력
        
        Args:
            msg: 디버그 메시지
            
        Returns:
            {'ok': True, 'data': msg} or {'ok': False, 'error': str}
        
        Examples:
            >>> h.message.debug("변수 x = 10")
            🔍 [17:30:00] 변수 x = 10
        """
        try:
            time = datetime.now().strftime('%H:%M:%S')
            print(f"🔍 [{time}] {msg}")
            return ok(msg)
        except Exception as e:
            return err(f"디버그 출력 실패: {str(e)}")
    
    def header(self, title: str, width: int = 60) -> Dict[str, Any]:
        """
        섹션 헤더 출력
        
        Args:
            title: 헤더 제목
            width: 구분선 너비 (기본값: 60)
            
        Returns:
            {'ok': True, 'data': title} or {'ok': False, 'error': str}
        
        Examples:
            >>> h.message.header("테스트 시작")
            ============================================================
            🎯 테스트 시작
            ============================================================
        """
        try:
            print("=" * width)
            print(f"🎯 {title}")
            print("=" * width)
            return ok(title)
        except Exception as e:
            return err(f"헤더 출력 실패: {str(e)}")
    
    def divider(self, width: int = 60) -> Dict[str, Any]:
        """
        구분선 출력
        
        Args:
            width: 구분선 너비 (기본값: 60)
            
        Returns:
            {'ok': True, 'data': 'divider'} or {'ok': False, 'error': str}
        
        Examples:
            >>> h.message.divider()
            ------------------------------------------------------------
        """
        try:
            print("-" * width)
            return ok('divider')
        except Exception as e:
            return err(f"구분선 출력 실패: {str(e)}")

# Facade 인스턴스 생성
message_facade = MessageFacade()