"""
Auto Think Integration
execute_code 실행 후 자동으로 분석하고 Think 권장사항 생성
"""

import json
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

class AutoThink:
    """자동 Think 권장 시스템"""
    
    def __init__(self):
        self.last_execution = None
        self.flow_dir = Path("C:/Users/82106/Desktop/ai-coding-brain-mcp/.ai-brain/flow")
        self.flow_dir.mkdir(parents=True, exist_ok=True)
        
    def after_execute(self, code: str, result: Any) -> str:
        """execute_code 실행 후 자동 호출"""
        
        # 실행 정보 저장
        self.last_execution = {
            'timestamp': datetime.now().isoformat(),
            'code': code,
            'result': str(result),
            'code_lines': len(code.split('\n'))
        }
        
        # 분석 수행
        analysis = self._analyze(code, str(result))
        
        # 가이드 생성
        guide = self._generate_guide(analysis)
        
        # Flow에 기록
        self._save_to_flow(analysis)
        
        return guide
    
    def _analyze(self, code: str, output: str) -> Dict[str, Any]:
        """코드와 출력 분석"""
        
        # 오류 검사
        error_keywords = ['error', 'exception', 'traceback', 'failed', '❌']
        has_errors = any(kw.lower() in output.lower() for kw in error_keywords)
        
        # 오류 유형 파악
        error_type = None
        if has_errors:
            if 'AttributeError' in output:
                error_type = 'attribute'
            elif 'NameError' in output:
                error_type = 'name'
            elif 'SyntaxError' in output:
                error_type = 'syntax'
            elif 'FileNotFoundError' in output:
                error_type = 'file_not_found'
            else:
                error_type = 'unknown'
        
        # 코드 패턴 분석
        patterns = {
            'uses_helpers': 'ai_helpers' in code or 'h.' in code,
            'uses_flow': 'flow' in code.lower(),
            'is_test': 'test' in code.lower() or 'assert' in code,
            'is_complex': len(code.split('\n')) > 20
        }
        
        return {
            'has_errors': has_errors,
            'error_type': error_type,
            'patterns': patterns,
            'code_lines': len(code.split('\n')),
            'output_size': len(output)
        }
    
    def _generate_guide(self, analysis: Dict[str, Any]) -> str:
        """분석 기반 가이드 생성"""
        
        lines = []
        lines.append("\n" + "="*60)
        lines.append("🤖 자동 분석 결과 (Auto Think)")
        lines.append("="*60)
        
        if analysis['has_errors']:
            lines.append("\n❌ **오류 감지됨**")
            lines.append(f"오류 유형: {analysis['error_type']}")
            lines.append("\n**권장 액션:**")
            lines.append("다음 명령어를 실행하세요:")
            lines.append("```")
            lines.append("Think 도구를 사용해서 오류를 분석하고 해결 방법을 찾아주세요.")
            
            # 오류별 특별 지침
            if analysis['error_type'] == 'attribute':
                lines.append("특히 올바른 메서드명과 API 사용법에 집중해주세요.")
            elif analysis['error_type'] == 'name':
                lines.append("import 문과 변수 정의를 확인해주세요.")
            elif analysis['error_type'] == 'file_not_found':
                lines.append("파일 경로와 존재 여부를 확인해주세요.")
                
            lines.append("```")
            
        elif analysis['patterns']['is_complex']:
            lines.append("\n📊 **복잡한 코드 실행됨**")
            lines.append(f"코드 라인: {analysis['code_lines']}줄")
            lines.append("\n**권장 액션:**")
            lines.append("```")
            lines.append("Think 도구로 실행 결과를 검증하고 최적화 기회를 찾아주세요.")
            lines.append("```")
            
        elif analysis['patterns']['uses_flow']:
            lines.append("\n📋 **Flow 관련 코드**")
            lines.append("\n**권장 액션:**")
            lines.append("Flow 시스템 상태를 확인하고 다음 태스크를 진행하세요.")
            
        else:
            lines.append("\n✅ **정상 실행 완료**")
            lines.append(f"코드: {analysis['code_lines']}줄 | 출력: {analysis['output_size']}자")
            lines.append("\n다음 작업을 계속 진행하세요.")
        
        lines.append("\n" + "="*60)
        return "\n".join(lines)
    
    def _save_to_flow(self, analysis: Dict[str, Any]):
        """Flow 시스템에 저장"""
        
        try:
            log_file = self.flow_dir / "auto_think_log.json"
            
            # 기존 로그 읽기
            logs = []
            if log_file.exists():
                with open(log_file, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
            
            # 새 로그 추가
            logs.append({
                'timestamp': datetime.now().isoformat(),
                'analysis': analysis
            })
            
            # 최대 50개 유지
            if len(logs) > 50:
                logs = logs[-50:]
            
            # 저장
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(logs, f, ensure_ascii=False, indent=2)
                
        except Exception:
            pass  # 로그 실패는 무시

# 전역 인스턴스
_auto_think = AutoThink()

def analyze_last(code: str, result: Any) -> str:
    """마지막 실행 분석 (간편 함수)"""
    return _auto_think.after_execute(code, result)

def get_think_prompt() -> str:
    """Think 도구용 프롬프트 반환"""
    if not _auto_think.last_execution:
        return "실행된 코드가 없습니다."
    
    code = _auto_think.last_execution['code']
    result = _auto_think.last_execution['result']
    
    if 'error' in result.lower():
        return (
            "Think 도구를 사용하여 다음을 분석해주세요:\n"
            f"1. 오류 원인: {result[:100]}...\n"
            "2. 해결 방법\n"
            "3. 예방 방안"
        )
    else:
        return (
            "Think 도구를 사용하여 다음을 검토해주세요:\n"
            "1. 실행 결과 검증\n"
            "2. 코드 품질 평가\n"
            "3. 개선 제안"
        )