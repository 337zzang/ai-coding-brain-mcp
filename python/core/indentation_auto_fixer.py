
"""
들여쓰기 오류 자동 수정 제안 시스템
"""
from typing import Dict, List, Optional, Tuple
import difflib
import json

class IndentationAutoFixer:
    """들여쓰기 오류를 자동으로 수정하고 사용자에게 제안"""
    
    def __init__(self):
        self.fix_history = []  # 수정 이력 저장
        self.success_rate = {}  # 패턴별 성공률
        
    def suggest_fix(self, original_code: str, error_info: Dict) -> Dict:
        """
        오류 정보를 바탕으로 수정 제안 생성
        
        Returns:
            dict: {
                'has_fix': bool,
                'fixed_code': Optional[str],
                'diff': Optional[str],
                'confidence': float,
                'explanation': str,
                'preview': List[str]
            }
        """
        if not error_info.get('auto_fix'):
            return {
                'has_fix': False,
                'explanation': error_info.get('suggestion', '수정 제안 없음'),
                'confidence': 0.0
            }
        
        fixed_code = error_info['auto_fix']
        
        # 차이점 생성
        diff = self._generate_diff(original_code, fixed_code)
        
        # 미리보기 생성
        preview = self._generate_preview(fixed_code, error_info['line'])
        
        # 신뢰도 계산
        confidence = self._calculate_confidence(error_info['error_type'], error_info['message'])
        
        result = {
            'has_fix': True,
            'fixed_code': fixed_code,
            'diff': diff,
            'confidence': confidence,
            'explanation': error_info['suggestion'],
            'preview': preview,
            'error_line': error_info['line']
        }
        
        # 이력 저장
        self.fix_history.append({
            'error': error_info['message'],
            'line': error_info['line'],
            'confidence': confidence,
            'accepted': None  # 사용자 수락 여부
        })
        
        return result
    
    def _generate_diff(self, original: str, fixed: str) -> str:
        """원본과 수정본의 차이점 생성"""
        original_lines = original.split('\n')
        fixed_lines = fixed.split('\n')
        
        diff = difflib.unified_diff(
            original_lines,
            fixed_lines,
            fromfile='original.py',
            tofile='fixed.py',
            lineterm=''
        )
        
        return '\n'.join(diff)
    
    def _generate_preview(self, code: str, error_line: int, context: int = 3) -> List[str]:
        """수정된 코드의 미리보기 생성"""
        lines = code.split('\n')
        start = max(0, error_line - context - 1)
        end = min(len(lines), error_line + context)
        
        preview = []
        for i in range(start, end):
            if i < len(lines):
                marker = ">>>" if i == error_line - 1 else "   "
                preview.append(f"{i+1:3d} {marker} {lines[i]}")
        
        return preview
    
    def _calculate_confidence(self, error_type: str, message: str) -> float:
        """수정 제안의 신뢰도 계산"""
        # 기본 신뢰도
        base_confidence = 0.7
        
        # 특정 패턴에 대한 신뢰도 조정
        if "expected an indented block" in message:
            base_confidence = 0.95  # 매우 명확한 오류
        elif "unexpected indent" in message:
            base_confidence = 0.85
        elif "unindent does not match" in message:
            base_confidence = 0.75
        elif "inconsistent use of tabs" in message:
            base_confidence = 0.99  # 탭/스페이스 변환은 거의 확실
        
        # 성공률 기반 조정
        pattern_key = error_type + ":" + message.split(':')[0]
        if pattern_key in self.success_rate:
            history_factor = self.success_rate[pattern_key]
            base_confidence = base_confidence * 0.7 + history_factor * 0.3
        
        return round(base_confidence, 2)
    
    def update_success_rate(self, error_type: str, message: str, accepted: bool):
        """사용자의 수락/거부에 따라 성공률 업데이트"""
        pattern_key = error_type + ":" + message.split(':')[0]
        
        if pattern_key not in self.success_rate:
            self.success_rate[pattern_key] = 1.0 if accepted else 0.0
        else:
            # 이동평균으로 업데이트
            old_rate = self.success_rate[pattern_key]
            new_value = 1.0 if accepted else 0.0
            self.success_rate[pattern_key] = old_rate * 0.8 + new_value * 0.2
        
        # 최근 이력 업데이트
        if self.fix_history:
            self.fix_history[-1]['accepted'] = accepted
    
    def get_statistics(self) -> Dict:
        """수정 제안 통계 반환"""
        total = len(self.fix_history)
        accepted = sum(1 for h in self.fix_history if h.get('accepted') is True)
        rejected = sum(1 for h in self.fix_history if h.get('accepted') is False)
        pending = total - accepted - rejected
        
        return {
            'total_suggestions': total,
            'accepted': accepted,
            'rejected': rejected,
            'pending': pending,
            'acceptance_rate': accepted / total if total > 0 else 0,
            'pattern_success_rates': self.success_rate.copy()
        }


class InteractiveFixUI:
    """사용자와 상호작용하는 수정 제안 UI"""
    
    @staticmethod
    def display_suggestion(suggestion: Dict) -> str:
        """수정 제안을 사용자 친화적으로 표시"""
        if not suggestion['has_fix']:
            return f"\n❌ 자동 수정 불가\n💡 제안: {suggestion['explanation']}"
        
        output = []
        output.append("\n" + "="*60)
        output.append("🔧 들여쓰기 오류 자동 수정 제안")
        output.append("="*60)
        
        output.append(f"\n📍 오류 위치: 줄 {suggestion['error_line']}")
        output.append(f"💡 설명: {suggestion['explanation']}")
        output.append(f"🎯 신뢰도: {suggestion['confidence']*100:.0f}%")
        
        output.append("\n📝 수정 미리보기:")
        output.extend(suggestion['preview'])
        
        if suggestion['confidence'] >= 0.9:
            output.append("\n✅ 높은 신뢰도 - 자동 수정을 권장합니다.")
        elif suggestion['confidence'] >= 0.7:
            output.append("\n⚠️ 중간 신뢰도 - 수정 내용을 확인하세요.")
        else:
            output.append("\n❓ 낮은 신뢰도 - 수동 검토가 필요합니다.")
        
        output.append("\n" + "="*60)
        
        return '\n'.join(output)
