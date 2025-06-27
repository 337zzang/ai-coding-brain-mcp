"""
Wisdom Integration
execute_code와 Wisdom System 통합
"""

import os
import json
from typing import Dict, Any, Optional, Tuple
from .wisdom_factory import WisdomFactory
from .wisdom_plugin_base import PluginManager
from .wisdom_auto_fixer import WisdomAutoFixer
from plugins import PythonIndentationPlugin, ConsoleUsagePlugin, HardcodedPathPlugin


class WisdomIntegration:
    """Wisdom System 통합 인터페이스"""
    
    def __init__(self):
        self.factory = WisdomFactory()
        self.plugin_manager = PluginManager()
        self.auto_fixer = None
        self._setup_default_plugins()
        
    def _setup_default_plugins(self):
        """기본 플러그인 등록"""
        self.plugin_manager.register(PythonIndentationPlugin())
        self.plugin_manager.register(ConsoleUsagePlugin())
        self.plugin_manager.register(HardcodedPathPlugin())
        
        # AutoFixer 초기화
        self.auto_fixer = WisdomAutoFixer(self.plugin_manager)
        
    def pre_execute_check(self, code: str, language: str = "python") -> Tuple[bool, str, Dict]:
        """
        execute_code 실행 전 검사
        
        Returns:
            (should_proceed, modified_code, analysis_result)
        """
        # 파일 확장자 결정
        ext_map = {
            "python": ".py",
            "javascript": ".js",
            "typescript": ".ts"
        }
        filename = f"temp_code{ext_map.get(language, '.txt')}"
        
        # 코드 분석
        result = self.auto_fixer.analyze_and_fix(
            code, 
            filename, 
            auto_apply=False  # 자동 적용 안함
        )
        
        # 분석 결과
        detections = self.plugin_manager.check_all(code, filename)
        
        if not detections:
            return True, code, {"status": "clean", "issues": []}
            
        # 심각한 문제가 있는지 확인
        critical_issues = [d for d in detections if (d.pattern.severity if d.pattern else d.severity) in ["critical", "high"]]
        
        if critical_issues:
            print("\n⚠️ Wisdom System이 심각한 문제를 감지했습니다:")
            for issue in critical_issues:
                print(f"  - {(issue.pattern.description if issue.pattern else issue.message)} (line {issue.line_number})")
                
            # 자동 수정 제안
            print("\n🔧 자동 수정을 적용하시겠습니까? (권장)")
            
            # 여기서는 자동으로 수정 적용 (실제로는 사용자 확인 필요)
            fix_result = self.auto_fixer.analyze_and_fix(
                code, 
                filename, 
                auto_apply=True
            )
            
            if fix_result.fixed_code:
                print(f"✅ {len(fix_result.applied_fixes)}개 문제 자동 수정됨")
                return True, fix_result.fixed_code, self._create_analysis_report(detections, fix_result)
                
        # 경미한 문제만 있는 경우
        warnings = [d for d in detections if (d.pattern.severity if d.pattern else d.severity) in ["medium", "low"]]
        if warnings:
            print(f"\n💡 {len(warnings)}개의 경미한 문제가 감지되었습니다.")
            
        return True, code, self._create_analysis_report(detections, None)
        
    def _create_analysis_report(self, detections, fix_result=None):
        """분석 리포트 생성"""
        report = {
            "status": "issues_found",
            "total_issues": len(detections),
            "by_severity": {},
            "by_type": {},
            "fixes_applied": 0
        }
        
        # 심각도별 분류
        for d in detections:
            severity = d.pattern.severity if d.pattern else d.severity
            report["by_severity"][severity] = report["by_severity"].get(severity, 0) + 1
            
            pattern_id = d.pattern.key if d.pattern else d.pattern_key
            report["by_type"][pattern_id] = report["by_type"].get(pattern_id, 0) + 1
            
        # 수정 정보
        if fix_result and fix_result.applied_fixes:
            report["fixes_applied"] = len(fix_result.applied_fixes)
            report["status"] = "auto_fixed"
            
        return report
        
    def analyze_file(self, filepath: str) -> Dict:
        """파일 분석"""
        if not os.path.exists(filepath):
            return {"error": "File not found"}
            
        with open(filepath, 'r', encoding='utf-8') as f:
            code = f.read()
            
        result = self.auto_fixer.analyze_and_fix(
            code,
            filepath,
            auto_apply=False
        )
        
        detections = self.plugin_manager.check_all(code, filepath)
        return self._create_analysis_report(detections, result)
        
    def get_project_wisdom(self) -> Dict:
        """현재 프로젝트의 Wisdom 데이터"""
        wisdom_manager = self.factory.get_wisdom_manager()
        
        return {
            "project": wisdom_manager.project_name,
            "common_mistakes": wisdom_manager.wisdom_data.get("common_mistakes", {}),
            "error_patterns": wisdom_manager.wisdom_data.get("error_patterns", {}),
            "best_practices": wisdom_manager.wisdom_data.get("best_practices", []),
            "plugin_stats": self.plugin_manager.get_all_statistics()
        }
        
    def generate_wisdom_report(self, output_file: str = None) -> str:
        """Wisdom 리포트 생성"""
        data = self.get_project_wisdom()
        
        report = f"""# 🧠 Wisdom System Report
        
## 📊 프로젝트: {data['project']}

### 자주 하는 실수 TOP 5
"""
        
        # 실수 정렬
        mistakes = sorted(
            data['common_mistakes'].items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:5]
        
        for i, (mistake, count) in enumerate(mistakes, 1):
            report += f"{i}. **{mistake}**: {count}회\n"
            
        report += "\n### 플러그인 통계\n"
        for plugin_name, stats in data['plugin_stats'].items():
            report += f"\n**{plugin_name}**:\n"
            for key, value in stats.items():
                report += f"  - {key}: {value}\n"
                
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report)
                
        return report


# 전역 인스턴스 생성
wisdom_integration = WisdomIntegration()
