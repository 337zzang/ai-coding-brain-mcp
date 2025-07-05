"""
중앙화된 에러 보고 시스템
v30.2 - 투명하고 즉각적인 에러 보고
"""
import json
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union
from dataclasses import dataclass, asdict

@dataclass
class ErrorReport:
    """에러 보고 데이터 구조"""
    timestamp: str
    location: str  # 파일:라인 또는 단계
    error_type: str
    message: str
    cause: Optional[str] = None
    attempted_solutions: Optional[list] = None
    next_steps: Optional[list] = None
    traceback: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

class ErrorReporter:
    """중앙화된 에러 리포터"""
    
    def __init__(self):
        self.error_log = []
        self.max_log_size = 100
        self.report_format = """
⚠️ 오류 발생!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📍 위치: {location}
💥 오류: {error_type} - {message}
🔍 원인: {cause}

🔄 시도한 해결책:
{attempted_solutions}

💡 다음 단계:
{next_steps}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        """
    
    def report(self, 
               error: Union[Exception, str],
               location: Optional[str] = None,
               cause: Optional[str] = None,               attempted_solutions: Optional[list] = None,
               next_steps: Optional[list] = None) -> ErrorReport:
        """에러 보고 및 출력
        
        Args:
            error: 예외 객체 또는 에러 메시지
            location: 에러 발생 위치
            cause: 추정 원인
            attempted_solutions: 시도한 해결책 목록
            next_steps: 다음 단계 제안
            
        Returns:
            ErrorReport: 생성된 에러 보고
        """
        # 에러 정보 추출
        if isinstance(error, Exception):
            error_type = type(error).__name__
            message = str(error)
            if not location:
                # 스택 트레이스에서 위치 추출
                tb = traceback.extract_tb(error.__traceback__)
                if tb:
                    last_frame = tb[-1]
                    location = f"{last_frame.filename}:{last_frame.lineno}"
        else:
            error_type = "Error"
            message = str(error)
            
        if not location:
            location = "Unknown"
            
        # 에러 보고 생성
        report = ErrorReport(
            timestamp=datetime.now().isoformat(),
            location=location,
            error_type=error_type,
            message=message,
            cause=cause,
            attempted_solutions=attempted_solutions or [],
            next_steps=next_steps or []
        )
        
        # 콘솔 출력
        self._print_report(report)
        
        # 로그 저장
        self._save_to_log(report)
        
        return report
    
    def _print_report(self, report: ErrorReport) -> None:
        """에러 보고를 콘솔에 출력"""
        print(self.report_template.format(
            location=report.location,
            error_type=report.error_type,
            message=report.message,
            cause=report.cause or "분석 중",
            attempted_solutions=self._format_list(report.attempted_solutions),
            next_steps=self._format_list(report.next_steps)
        ))
        
    def _format_list(self, items: Optional[list]) -> str:
        """리스트를 포맷팅"""
        if not items:
            return "- 없음"
        return "\n".join(f"{i+1}. {item}" for i, item in enumerate(items))
        
    def _save_to_log(self, report: ErrorReport) -> None:
        """에러 로그 저장"""
        try:
            log_file = self.log_dir / f"error_{datetime.now().strftime('%Y%m%d')}.json"
            
            # 기존 로그 읽기
            if log_file.exists():
                with open(log_file, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
            else:
                logs = []
                
            # 새 로그 추가
            logs.append(asdict(report))
            
            # 저장
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(logs, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            # 로그 저장 실패는 조용히 무시
            pass


# 전역 에러 리포터 인스턴스
error_reporter = ErrorReporter()
