"""
Wisdom Auto Fixer
플러그인에서 감지된 문제를 자동으로 수정
"""

import ast
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from .wisdom_plugin_base import Detection, PluginManager


@dataclass
class FixResult:
    """수정 결과"""
    success: bool
    original_code: str
    fixed_code: Optional[str]
    applied_fixes: List[Detection]
    error_message: Optional[str] = None
    

class WisdomAutoFixer:
    """자동 수정 시스템"""
    
    def __init__(self, plugin_manager: PluginManager):
        self.plugin_manager = plugin_manager
        self.fix_history: List[FixResult] = []
        
    def analyze_and_fix(self, code: str, filename: str, 
                       auto_apply: bool = False) -> FixResult:
        """코드 분석 및 수정"""
        # 1. 모든 플러그인으로 문제 감지
        all_detections = self.plugin_manager.check_all(code, filename)
        
        if not all_detections:
            return FixResult(
                success=True,
                original_code=code,
                fixed_code=code,
                applied_fixes=[]
            )
            
        # 2. 심각도별로 정렬
        sorted_detections = sorted(
            all_detections, 
            key=lambda d: self._get_severity_score(d.pattern.severity if d.pattern else d.severity),
            reverse=True
        )
        
        # 3. 수정 적용
        fixed_code = code
        applied_fixes = []
        
        for detection in sorted_detections:
            # plugin_name 대신 pattern에서 플러그인 찾기
            plugin = None
            for p in self.plugin_manager.plugins.values():
                if any(pattern.key == detection.pattern_key for pattern in p.patterns):
                    plugin = p
                    break
            if not plugin:
                continue
                
            # 수정 시도
            try:
                suggested_fix = plugin.fix(fixed_code, detection)
                if suggested_fix and self._validate_fix(suggested_fix, filename):
                    if auto_apply:
                        fixed_code = suggested_fix
                        applied_fixes.append(detection)
                    else:
                        # 수정 제안만 표시
                        self._show_fix_suggestion(detection, suggested_fix)
                        
            except Exception as e:
                print(f"❌ 수정 중 오류: {e}")
                
        # 4. 결과 생성
        result = FixResult(
            success=True,
            original_code=code,
            fixed_code=fixed_code if applied_fixes else None,
            applied_fixes=applied_fixes
        )
        
        self.fix_history.append(result)
        return result
        
    def _get_severity_score(self, severity: str) -> int:
        """심각도를 점수로 변환"""
        scores = {
            "critical": 100,
            "high": 75,
            "medium": 50,
            "low": 25
        }
        return scores.get(severity, 0)
        
    def _validate_fix(self, fixed_code: str, filename: str) -> bool:
        """수정된 코드 검증"""
        # Python 파일인 경우 AST 파싱으로 검증
        if filename.endswith('.py'):
            try:
                ast.parse(fixed_code)
                return True
            except SyntaxError:
                return False
                
        # TypeScript/JavaScript는 기본 검증만
        # TODO: 더 정교한 검증 추가
        return True
        
    def _show_fix_suggestion(self, detection: Detection, suggested_fix: str):
        """수정 제안 표시"""
        print(f"\n🔧 수정 제안: {detection.pattern.description if detection.pattern else detection.message}")
        print(f"📍 위치: {detection.filename}:{detection.line_number}")
        print(f"❌ 문제: {detection.matched_text}")
        print(f"✅ 제안: {detection.pattern.fix_hint if detection.pattern and hasattr(detection.pattern, 'fix_hint') else detection.fix_hint}")
        
    def apply_selected_fixes(self, code: str, filename: str, 
                           fix_indices: List[int]) -> FixResult:
        """선택된 수정사항만 적용"""
        detections = self.plugin_manager.check_all(code, filename)
        
        fixed_code = code
        applied_fixes = []
        
        for idx in fix_indices:
            if 0 <= idx < len(detections):
                detection = detections[idx]
                # plugin_name 대신 pattern에서 플러그인 찾기
            plugin = None
            for p in self.plugin_manager.plugins.values():
                if any(pattern.key == detection.pattern_key for pattern in p.patterns):
                    plugin = p
                    break
                
                if plugin:
                    suggested_fix = plugin.fix(fixed_code, detection)
                    if suggested_fix and self._validate_fix(suggested_fix, filename):
                        fixed_code = suggested_fix
                        applied_fixes.append(detection)
                        
        return FixResult(
            success=True,
            original_code=code,
            fixed_code=fixed_code if applied_fixes else None,
            applied_fixes=applied_fixes
        )
        
    def get_fix_report(self) -> Dict:
        """수정 이력 리포트"""
        total_fixes = sum(len(r.applied_fixes) for r in self.fix_history)
        fix_types = {}
        
        for result in self.fix_history:
            for fix in result.applied_fixes:
                fix_type = fix.pattern.key if fix.pattern else fix.pattern_key
                fix_types[fix_type] = fix_types.get(fix_type, 0) + 1
                
        return {
            "total_sessions": len(self.fix_history),
            "total_fixes_applied": total_fixes,
            "fix_types": fix_types,
            "success_rate": sum(1 for r in self.fix_history if r.success) / len(self.fix_history) if self.fix_history else 0
        }
