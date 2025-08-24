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
    
    def task(self, msg: str, *, level: str = "INFO") -> Dict[str, Any]:
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
    
    def share(self, msg: str, obj: Optional[Any] = None) -> Dict[str, Any]:
        """
        영속적 자원 공유 메시지
        
        Args:
            msg: 공유 내용 (예: "함수: analyze() - 코드 분석")
            obj: 선택적 객체 (자동 타입 감지)
            
        Returns:
            {'ok': True, 'data': {'msg': msg, 'type': type, 'time': time}}
        
        Examples:
            >>> h.message.share("함수: analyze() - 코드 분석")
            >>> h.message.share("변수: config", {"mode": "production"})
            >>> h.message.share("클래스: Manager - save(), load()")
        """
        try:
            time = datetime.now().strftime('%H:%M:%S')
            
            # 자동 타입 감지 및 아이콘 선택
            if obj is not None:
                obj_type = type(obj).__name__
                if callable(obj):
                    icon = "🔧"  # 함수
                elif isinstance(obj, type):
                    icon = "🏗️"  # 클래스
                elif isinstance(obj, dict):
                    icon = "📂"  # 딕셔너리
                elif isinstance(obj, (list, tuple)):
                    icon = "📚"  # 리스트/튜플
                else:
                    icon = "📦"  # 기타
                    
                # 값 포맷팅 (너무 길면 요약)
                if isinstance(obj, (dict, list)) and len(str(obj)) > 50:
                    value_str = f" ({obj_type}, {len(obj)} items)"
                else:
                    value_str = f" = {obj}"
                    
                msg = f"{msg}{value_str}"
            else:
                # msg에서 패턴 감지
                if "함수:" in msg or "function:" in msg.lower():
                    icon = "🔧"
                elif "클래스:" in msg or "class:" in msg.lower():
                    icon = "🏗️"
                elif "변수:" in msg or "variable:" in msg.lower():
                    icon = "📂"
                else:
                    icon = "📦"
            
            print(f"{icon} [{time}] [SHARE] {msg}")
            
            return ok({
                'msg': msg,
                'type': type(obj).__name__ if obj else 'str',
                'time': time
            })
        except Exception as e:
            return err(f"자원 공유 실패: {str(e)}")
    
    # 유틸리티 메서드 추가
    def info(self, name: str, value: Any = None) -> Dict[str, Any]:
        """
        간편한 정보 공유 (share의 단축 버전)
        
        Examples:
            >>> h.message.info("current_step", "analyzing")
            >>> h.message.info("files_processed", 42)
        """
        if value is not None:
            return self.share(f"{name}: {value}", value)
        return self.share(name)
    
    def progress(self, current: int, total: int, desc: str = "") -> Dict[str, Any]:
        """
        진행률 표시 (task의 특수 버전)
        
        Examples:
            >>> h.message.progress(50, 100, "파일 처리")
            🔄 [22:45:00] [TASK] 진행률: 50/100 (50%) - 파일 처리
        """
        percent = (current / total * 100) if total > 0 else 0
        msg = f"진행률: {current}/{total} ({percent:.0f}%)"
        if desc:
            msg += f" - {desc}"
        return self.task(msg, "INFO")

# Facade 인스턴스 생성
message_facade = MessageFacade()