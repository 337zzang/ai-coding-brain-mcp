#!/usr/bin/env python3
"""
Wisdom 시스템 시각화 및 리포트 생성 모듈
"""

from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import json


class WisdomVisualizer:
    """Wisdom 데이터 시각화 및 리포트 생성"""
    
    def __init__(self, wisdom_manager):
        self.wisdom_manager = wisdom_manager
    
    def generate_report(self) -> str:
        """Wisdom 데이터를 시각적으로 표현한 리포트 생성"""
        report = []
        report.append("=" * 70)
        report.append("🧠 **Wisdom System Report**")
        report.append("=" * 70)
        report.append(f"\n📅 생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        try:
            project_name = self.wisdom_manager.project_root.name
        except:
            project_name = "Unknown"
        report.append(f"📍 프로젝트: {project_name}")
        
        # 1. 실수 통계
        mistakes = self.wisdom_manager.wisdom_data.get('common_mistakes', {})
        if mistakes:
            report.append("\n## ❌ 실수 통계\n")
            report.append("```")
            max_count = max(data['count'] for data in mistakes.values()) if mistakes else 1
            
            for mistake, data in sorted(mistakes.items(), key=lambda x: x[1]['count'], reverse=True):
                count = data['count']
                bar_length = int((count / max_count) * 40)
                bar = '█' * bar_length + '░' * (40 - bar_length)
                report.append(f"{mistake:20} {bar} {count:3}회")
            report.append("```")
        
        # 2. 오류 패턴
        errors = self.wisdom_manager.wisdom_data.get('error_patterns', {})
        if errors:
            report.append("\n## 🐛 오류 패턴\n")
            report.append("| 오류 유형 | 발생 횟수 | 마지막 발생 |")
            report.append("|-----------|-----------|-------------|")
            
            for error_type, data in sorted(errors.items(), key=lambda x: x[1]['count'], reverse=True):
                last_seen = data.get('last_seen', 'Unknown')
                if isinstance(last_seen, str) and 'T' in last_seen:
                    last_seen = last_seen.split('T')[0]
                report.append(f"| {error_type} | {data['count']}회 | {last_seen} |")
        
        # 3. 베스트 프랙티스
        practices = self.wisdom_manager.wisdom_data.get('best_practices', [])
        if practices:
            report.append("\n## ✅ 베스트 프랙티스 (최근 10개)\n")
            for i, practice in enumerate(practices[-10:], 1):
                report.append(f"{i}. {practice}")
        
        # 4. 성장 지표
        report.append("\n## 📈 성장 지표\n")
        total_mistakes = sum(data['count'] for data in mistakes.values())
        total_practices = len(practices)
        
        report.append(f"- 총 실수 추적: {total_mistakes}회")
        report.append(f"- 베스트 프랙티스: {total_practices}개")
        report.append(f"- 학습률: {total_practices / (total_mistakes + 1) * 100:.1f}%")
        
        # 5. 개선 추세
        if total_mistakes > 0:
            report.append("\n## 📊 개선 추세\n")
            report.append("최근 실수 감소율을 계산하여 개선 추세를 보여줍니다.")
            
        report.append("\n" + "=" * 70)
        
        return "\n".join(report)
    
    def export_stats(self, format: str = "json") -> str:
        """Wisdom 통계를 다양한 형식으로 내보내기"""
        stats = {
            "project": self.wisdom_manager.project_root.name if hasattr(self.wisdom_manager, 'project_root') else 'Unknown',
            "timestamp": datetime.now().isoformat(),
            "mistakes": {
                k: v['count'] 
                for k, v in self.wisdom_manager.wisdom_data.get('common_mistakes', {}).items()
            },
            "errors": {
                k: v['count'] 
                for k, v in self.wisdom_manager.wisdom_data.get('error_patterns', {}).items()
            },
            "best_practices_count": len(self.wisdom_manager.wisdom_data.get('best_practices', [])),
            "total_learnings": sum(
                v['count'] 
                for v in self.wisdom_manager.wisdom_data.get('common_mistakes', {}).values()
            )
        }
        
        if format == "json":
            return json.dumps(stats, indent=2, ensure_ascii=False)
        elif format == "csv":
            lines = ["Category,Type,Count"]
            for mistake, count in stats['mistakes'].items():
                lines.append(f"Mistake,{mistake},{count}")
            for error, count in stats['errors'].items():
                lines.append(f"Error,{error},{count}")
            lines.append(f"BestPractices,Total,{stats['best_practices_count']}")
            return "\n".join(lines)
        else:
            return str(stats)


class ProjectWisdomStore:
    """프로젝트별 Wisdom 데이터 관리"""
    
    def __init__(self, wisdom_dir: Path):
        self.wisdom_dir = wisdom_dir
        self.wisdom_dir.mkdir(exist_ok=True)
    
    def get_project_wisdom(self, project_name: str) -> Dict:
        """특정 프로젝트의 Wisdom 데이터 가져오기"""
        project_file = self.wisdom_dir / f"{project_name}_wisdom.json"
        
        if project_file.exists():
            try:
                with open(project_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ 프로젝트 Wisdom 로드 실패: {e}")
        
        # 기본 구조 반환
        return {
            "common_mistakes": {},
            "error_patterns": {},
            "best_practices": [],
            "project_info": {
                "name": project_name,
                "created": datetime.now().isoformat()
            }
        }
    
    def save_project_wisdom(self, project_name: str, wisdom_data: Dict):
        """프로젝트별 Wisdom 데이터 저장"""
        project_file = self.wisdom_dir / f"{project_name}_wisdom.json"
        
        try:
            with open(project_file, 'w', encoding='utf-8') as f:
                json.dump(wisdom_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"❌ 프로젝트 Wisdom 저장 실패: {e}")
    
    def list_projects(self) -> List[str]:
        """Wisdom 데이터가 있는 프로젝트 목록"""
        projects = []
        for file in self.wisdom_dir.glob("*_wisdom.json"):
            project_name = file.stem.replace("_wisdom", "")
            projects.append(project_name)
        return sorted(projects)
    
    def merge_wisdom_data(self, source_project: str, target_project: str):
        """두 프로젝트의 Wisdom 데이터 병합"""
        source_data = self.get_project_wisdom(source_project)
        target_data = self.get_project_wisdom(target_project)
        
        # 실수 병합
        for mistake, data in source_data.get('common_mistakes', {}).items():
            if mistake in target_data.get('common_mistakes', {}):
                target_data['common_mistakes'][mistake]['count'] += data['count']
            else:
                target_data['common_mistakes'][mistake] = data.copy()
        
        # 베스트 프랙티스 병합 (중복 제거)
        existing_practices = set(target_data.get('best_practices', []))
        for practice in source_data.get('best_practices', []):
            if practice not in existing_practices:
                target_data['best_practices'].append(practice)
        
        self.save_project_wisdom(target_project, target_data)
        return target_data
