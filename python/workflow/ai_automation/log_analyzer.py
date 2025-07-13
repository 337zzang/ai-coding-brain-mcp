# python/workflow/ai_automation/log_analyzer.py
"""
자동 로그 분석 및 에러 추적 시스템
"""
import re
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple

class LogAnalyzer:
    """로그 파일을 분석하여 에러를 추적하고 원인을 파악"""

    def __init__(self, project_name: str):
        self.project = project_name
        self.log_path = Path("logs")
        self.error_patterns = {
            "python": {
                "exception": r"(\w+Error|\w+Exception): (.+)",
                "traceback": r"File \"(.+?)\", line (\d+), in (.+)",
                "syntax": r"SyntaxError: (.+)",
                "import": r"ImportError: (.+)",
                "attribute": r"AttributeError: (.+)"
            },
            "general": {
                "error": r"(?i)error: (.+)",
                "failed": r"(?i)failed: (.+)",
                "critical": r"(?i)critical: (.+)"
            }
        }

    def find_recent_errors(self, minutes: int = 5) -> List[Dict]:
        """최근 N분 내의 에러 찾기"""
        errors = []
        cutoff_time = datetime.now().timestamp() - (minutes * 60)

        for log_file in self.log_path.glob("*.log"):
            if log_file.stat().st_mtime > cutoff_time:
                errors.extend(self.parse_log_file(log_file))

        return sorted(errors, key=lambda x: x["timestamp"], reverse=True)

    def parse_log_file(self, log_file: Path) -> List[Dict]:
        """로그 파일에서 에러 추출"""
        errors = []

        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            for i, line in enumerate(lines):
                for category, patterns in self.error_patterns.items():
                    for error_type, pattern in patterns.items():
                        match = re.search(pattern, line)
                        if match:
                            error_info = {
                                "file": str(log_file),
                                "line_number": i + 1,
                                "category": category,
                                "type": error_type,
                                "message": match.group(0),
                                "details": match.groups(),
                                "context": self.get_context(lines, i),
                                "timestamp": self.extract_timestamp(line)
                            }
                            errors.append(error_info)

        except Exception as e:
            print(f"로그 파일 파싱 실패: {e}")

        return errors

    def get_context(self, lines: List[str], error_line: int, context_size: int = 5) -> Dict:
        """에러 전후 컨텍스트 추출"""
        start = max(0, error_line - context_size)
        end = min(len(lines), error_line + context_size + 1)

        return {
            "before": lines[start:error_line],
            "error": lines[error_line],
            "after": lines[error_line + 1:end]
        }

    def extract_timestamp(self, line: str) -> Optional[str]:
        """로그 라인에서 타임스탬프 추출"""
        # 일반적인 타임스탬프 패턴들
        patterns = [
            r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}",
            r"\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}",
            r"\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\]"
        ]

        for pattern in patterns:
            match = re.search(pattern, line)
            if match:
                return match.group(0)

        return datetime.now().isoformat()

    def analyze_error_chain(self, errors: List[Dict]) -> Dict:
        """에러 체인 분석하여 근본 원인 찾기"""
        if not errors:
            return {"root_cause": None, "chain": []}

        # 타임스탬프 기준 정렬 (오래된 것부터)
        sorted_errors = sorted(errors, key=lambda x: x["timestamp"])

        # 첫 번째 에러가 보통 근본 원인
        root_cause = sorted_errors[0]

        # 에러 체인 구성
        chain = []
        for error in sorted_errors:
            chain.append({
                "type": error["type"],
                "message": error["message"],
                "file": error["file"],
                "line": error["line_number"]
            })

        return {
            "root_cause": root_cause,
            "chain": chain,
            "total_errors": len(errors)
        }

    def suggest_fix(self, error: Dict) -> Optional[str]:
        """에러 타입에 따른 수정 제안"""
        suggestions = {
            "import": "모듈이 설치되어 있는지 확인하거나 경로를 점검하세요.",
            "attribute": "객체의 속성/메서드가 존재하는지 확인하세요.",
            "syntax": "문법 오류를 확인하세요. 괄호, 콜론, 들여쓰기 등을 점검하세요.",
            "exception": "예외 처리를 추가하거나 입력값을 검증하세요."
        }

        return suggestions.get(error["type"], "로그의 전체 컨텍스트를 확인하세요.")
