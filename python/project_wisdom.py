#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Project Wisdom Manager - AI Coding Brain MCP
프로젝트 작업 중 축적되는 지혜와 교훈을 관리하는 모듈

작성일: 2025-06-22
"""

import os
import json
import re
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
# wisdom_visualizer는 별도 파일에 있음
try:
    from wisdom_visualizer import WisdomVisualizer, ProjectWisdomStore
except ImportError:
    # import 실패 시 기본 스텁 클래스 사용
    class WisdomVisualizer:
        def __init__(self, wisdom_manager):
            self.wisdom_manager = wisdom_manager
        
        def generate_report(self) -> str:
            return self.wisdom_manager.generate_wisdom_report()
        
        def export_stats(self, format: str = "json") -> str:
            if format == "json":
                return json.dumps(self.wisdom_manager.wisdom_data, indent=2, ensure_ascii=False)
            return str(self.wisdom_manager.wisdom_data)
    
    class ProjectWisdomStore:
        def __init__(self, wisdom_dir: Path):
            self.wisdom_dir = wisdom_dir
        
        def get_project_wisdom(self, project_name: str) -> Dict:
            wisdom_file = self.wisdom_dir / f"{project_name}_wisdom.json"
            if wisdom_file.exists():
                try:
                    with open(wisdom_file, 'r', encoding='utf-8') as f:
                        return json.load(f)
                except:
                    pass
            return ProjectWisdomManager._get_default_wisdom_data()
        
        def save_project_wisdom(self, project_name: str, wisdom_data: Dict):
            wisdom_file = self.wisdom_dir / f"{project_name}_wisdom.json"
            with open(wisdom_file, 'w', encoding='utf-8') as f:
                json.dump(wisdom_data, f, indent=2, ensure_ascii=False)

class ProjectWisdomManager:
    """프로젝트 지혜 관리 클래스"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.project_name = self.project_root.name  # 프로젝트 이름 추가
        self.wisdom_file = self.project_root / "project_wisdom.md"
        self.vision_file = self.project_root / "project_vision.md"
        
        # 프로젝트별 wisdom_data 경로 설정
        self.wisdom_data_dir = self.project_root / "memory" / "wisdom_data"
        self.wisdom_dir = self.wisdom_data_dir  # wisdom_dir 추가
        self.wisdom_data_file = self.wisdom_data_dir / "_wisdom.json"
        
        # wisdom_data 디렉토리 생성
        self.wisdom_data_dir.mkdir(parents=True, exist_ok=True)
        
        self.wisdom_data = {
            'error_patterns': {},
            'common_mistakes': {},
            'best_practices': [],
            'git_commits': [],
            'git_rollbacks': [],
            'last_updated': datetime.now().isoformat()
        }
        self.load_wisdom()
    
    @staticmethod
    def _get_default_wisdom_data() -> Dict:
        """기본 Wisdom 데이터 구조 반환"""
        return {
            'error_patterns': {},
            'common_mistakes': {},
            'best_practices': [],
            'git_commits': [],
            'git_rollbacks': [],
            'created': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat()
        }

    
    def load_wisdom(self):
        """기존 wisdom 데이터 로드"""
        # JSON 파일에서 로드 시도
        if self.wisdom_data_file.exists():
            try:
                with open(self.wisdom_data_file, "r", encoding="utf-8") as f:
                    loaded_data = json.load(f)
                    self.wisdom_data.update(loaded_data)
            except Exception as e:
                print(f"Wisdom 데이터 로드 실패: {e}")
        
        # Markdown 파일에서도 로드 (기존 코드 유지)

    def track_error(self, error_type: str, details: str = ""):
        """오류 패턴 추적"""
        if error_type not in self.wisdom_data['error_patterns']:
            self.wisdom_data['error_patterns'][error_type] = {
                'count': 0,
                'first_seen': datetime.now().isoformat(),
                'last_seen': None,
                'examples': []
            }
        
        error = self.wisdom_data['error_patterns'][error_type]
        error['count'] += 1
        error['last_seen'] = datetime.now().isoformat()
        
        if details and details not in error['examples']:
            error['examples'].append(details)
            error['examples'] = error['examples'][-5:]  # 최근 5개만 유지
        
        self.save_wisdom()
    
    def track_mistake(self, mistake_type: str, context: str = ""):
        """실수 패턴 추적"""
        if mistake_type not in self.wisdom_data['common_mistakes']:
            self.wisdom_data['common_mistakes'][mistake_type] = {
                'count': 0,
                'first_seen': datetime.now().isoformat(),
                'contexts': [],
                'last_seen': None
            }
        
        mistake = self.wisdom_data['common_mistakes'][mistake_type]
        mistake['count'] += 1
        mistake['last_seen'] = datetime.now().isoformat()
        
        if context and context not in mistake['contexts']:
            mistake['contexts'].append(context)
            mistake['contexts'] = mistake['contexts'][-3:]
        
        self.save_wisdom()
        
        # 실시간 경고
        self._show_mistake_warning(mistake_type, mistake['count'])
    
    def _show_mistake_warning(self, mistake_type: str, count: int):
        """실수에 대한 경고 메시지 표시"""
        warnings = {
            'console_usage': f"또 console을 사용하셨네요! ({count}번째) TypeScript에서는 logger를 사용하세요.",
            'direct_flow': f"flow_project를 직접 호출하셨네요! ({count}번째) execute_code를 사용하세요.",
            'indentation_error': f"들여쓰기 오류가 감지되었습니다! ({count}번째)",
            'complex_code': f"코드가 너무 복잡합니다! ({count}번째) 리팩토링을 고려하세요."
        }
        
        if mistake_type in warnings:
            print(f"\n⚠️ {warnings[mistake_type]}")
            print(f"💡 올바른 방법: {self._get_correct_way(mistake_type)}")
    
    def _get_correct_way(self, mistake_type: str) -> str:
        """올바른 방법 제시"""
        correct_ways = {
            'console_usage': "import { logger } from '../utils/logger'; logger.info('메시지');",
            'direct_flow': "execute_code: helpers.cmd_flow_with_context('project-name')",
            'indentation_error': "Python은 4칸 들여쓰기를 사용하세요",
            'complex_code': "함수를 더 작은 단위로 분리하세요"
        }
        return correct_ways.get(mistake_type, "문서를 참고하세요")
    
    def _get_error_tip(self, error_type: str) -> str:
        """오류 타입별 해결 팁 제공"""
        error_tips = {
            'SyntaxError': "문법을 확인하세요. 괄호, 따옴표, 콜론이 올바른지 체크하세요.",
            'IndentationError': "들여쓰기를 확인하세요. Python은 일관된 들여쓰기가 필요합니다.",
            'NameError': "변수나 함수명이 정의되었는지 확인하세요.",
            'TypeError': "데이터 타입이 올바른지 확인하세요.",
            'ImportError': "모듈이 설치되었는지, 경로가 올바른지 확인하세요.",
            'AttributeError': "객체에 해당 속성이나 메서드가 있는지 확인하세요.",
            'KeyError': "딕셔너리 키가 존재하는지 확인하세요.",
            'ValueError': "함수에 전달하는 값이 올바른지 확인하세요."
        }
        return error_tips.get(error_type, "오류 메시지를 자세히 읽어보세요.")
    
    def add_best_practice(self, practice: str, category: str = "general"):
        """베스트 프랙티스 추가"""
        best_practice = {
            'practice': practice,
            'category': category,
            'added': datetime.now().isoformat()
        }
        
        # 중복 체크
        for bp in self.wisdom_data['best_practices']:
            if bp['practice'] == practice:
                return
        
        self.wisdom_data['best_practices'].append(best_practice)
        self.save_wisdom()
    
    def save_wisdom(self):
        """wisdom 데이터를 파일로 저장"""
        self.wisdom_data['last_updated'] = datetime.now().isoformat()
        
        # wisdom_data를 프로젝트별 JSON으로 저장
        with open(self.wisdom_data_file, 'w', encoding='utf-8') as f:
            json.dump(self.wisdom_data, f, indent=2, ensure_ascii=False)
        
        # Markdown 파일도 업데이트
        self._update_wisdom_markdown()
    
    def get_statistics(self):
        """Wisdom 시스템 통계 반환"""
        stats = {
            'total_mistakes': sum(data['count'] for data in self.wisdom_data.get('common_mistakes', {}).values()),
            'total_errors': sum(data['count'] for data in self.wisdom_data.get('error_patterns', {}).values()),
            'total_best_practices': len(self.wisdom_data.get('best_practices', [])),
            'mistake_types': len(self.wisdom_data.get('common_mistakes', {})),
            'error_types': len(self.wisdom_data.get('error_patterns', {})),
            'last_updated': self.wisdom_data.get('last_updated', 'Never'),
            'project_name': self.project_name
        }
        return stats
    
    def _update_wisdom_markdown(self):
        """project_wisdom.md 파일 업데이트"""
        content = f"""# 🧠 Project Wisdom - {self.project_root.name}

## 📌 프로젝트 비전
프로젝트 작업 중 축적된 지혜와 교훈을 관리합니다.

## 🐛 자주 발생하는 오류 패턴
"""
        
        # 오류 패턴 추가
        for error_type, data in self.wisdom_data.get('error_patterns', {}).items():
            content += f"\n### {error_type} ({data['count']}회)\n"
            content += f"- 팁: {self._get_error_tip(error_type)}\n"
        
        # 자주 하는 실수들 추가
        content += "\n## ❌ 자주 하는 실수들\n"
        for mistake, data in sorted(self.wisdom_data.get('common_mistakes', {}).items(), 
                                   key=lambda x: x[1]['count'], reverse=True):
            content += f"\n### {mistake} ({data['count']}회)\n"
            content += f"- 올바른 방법: {self._get_correct_way(mistake)}\n"
        
        # 베스트 프랙티스 추가
        content += "\n## ✅ 베스트 프랙티스\n"
        categories = {}
        for bp in self.wisdom_data.get('best_practices', []):
            category = bp.get('category', 'general')
            if category not in categories:
                categories[category] = []
            categories[category].append(bp['practice'])
        
        for category, practices in categories.items():
            content += f"\n### {category}\n"
            for practice in practices:
                content += f"- {practice}\n"
        
        # 파일 저장
        wisdom_md_path = self.project_root / 'project_wisdom.md'
        with open(wisdom_md_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def track_commit(self, commit_hash: str, message: str):
        """Git 커밋 추적"""
        if 'git_commits' not in self.wisdom_data:
            self.wisdom_data['git_commits'] = []
        
        commit_data = {
            'hash': commit_hash,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        
        self.wisdom_data['git_commits'].append(commit_data)
        # 최근 100개만 유지
        self.wisdom_data['git_commits'] = self.wisdom_data['git_commits'][-100:]
        self.save_wisdom()
    
    def track_rollback(self, target: str, reason: str):
        """Git 롤백 추적"""
        if 'git_rollbacks' not in self.wisdom_data:
            self.wisdom_data['git_rollbacks'] = []
        
        rollback_data = {
            'target': target,
            'reason': reason,
            'timestamp': datetime.now().isoformat()
        }
        
        self.wisdom_data['git_rollbacks'].append(rollback_data)
        self.save_wisdom()
    
    def get_current_context(self) -> Dict:
        """현재 작업 컨텍스트 반환"""
        # 캐시된 컨텍스트 파일에서 읽기
        context_file = self.project_root / 'memory' / 'cache' / 'context.json'
        if context_file.exists():
            try:
                with open(context_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        
        # 기본 컨텍스트 반환
        return {
            'project_name': self.project_name,
            'current_task': None,
            'current_phase': 'work'
        }
    
    def get_last_stable_commit(self) -> Optional[str]:
        """마지막 안정적인 커밋 해시 반환"""
        # 롤백이 없었던 마지막 커밋 찾기
        commits = self.wisdom_data.get('git_commits', [])
        rollbacks = self.wisdom_data.get('git_rollbacks', [])
        
        if not commits:
            return None
        
        # 롤백된 커밋들의 타임스탬프 수집
        rollback_times = set()
        for rb in rollbacks:
            rollback_times.add(rb['timestamp'][:19])  # 초 단위까지만
        
        # 롤백되지 않은 최근 커밋 찾기
        for commit in reversed(commits):
            commit_time = commit['timestamp'][:19]
            if commit_time not in rollback_times:
                return commit['hash']
        
        return None
    
    def generate_wisdom_report(self) -> str:
        """Wisdom 데이터를 시각적으로 표현한 리포트 생성"""
        report = []
        report.append("=" * 70)
        report.append("🧠 **Wisdom System Report**")
        report.append("=" * 70)
        report.append(f"\n📅 생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"📍 프로젝트: {self.project_name}")
        
        # 1. 실수 통계
        mistakes = self.wisdom_data.get('common_mistakes', {})
        if mistakes:
            report.append("\n## ❌ 실수 통계")
            report.append("\n```")
            max_count = max(data['count'] for data in mistakes.values()) if mistakes else 1
            
            for mistake, data in sorted(mistakes.items(), key=lambda x: x[1]['count'], reverse=True):
                count = data['count']
                bar_length = int((count / max_count) * 40)
                bar = '█' * bar_length + '░' * (40 - bar_length)
                report.append(f"{mistake:20} {bar} {count:3}회")
            report.append("```")
        
        # 2. 베스트 프랙티스
        practices = self.wisdom_data.get('best_practices', [])
        if practices:
            report.append("\n## ✅ 베스트 프랙티스 (최근 5개)")
            for i, practice in enumerate(practices[-5:], 1):
                report.append(f"{i}. {practice}")
        
        return "\n".join(report)
    
    def get_project_wisdom(self, project_name: str) -> Dict:
        """특정 프로젝트의 Wisdom 데이터 가져오기"""
        # 프로젝트별 Wisdom 파일 경로
        project_wisdom_file = self.wisdom_dir / f"{project_name}_wisdom.json"
        
        if project_wisdom_file.exists():
            try:
                with open(project_wisdom_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return self._get_default_wisdom_data()
        else:
            return self._get_default_wisdom_data()
    
    def save_project_wisdom(self, project_name: str, wisdom_data: Dict):
        """프로젝트별 Wisdom 데이터 저장"""
        project_wisdom_file = self.wisdom_dir / f"{project_name}_wisdom.json"
        
        try:
            with open(project_wisdom_file, 'w', encoding='utf-8') as f:
                json.dump(wisdom_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ 프로젝트 Wisdom 저장 실패: {e}")


    def generate_report(self) -> str:
        """Wisdom 리포트 생성 (시각화 모듈 사용)"""
        visualizer = WisdomVisualizer(self)
        return visualizer.generate_report()
    
    def export_stats(self, format: str = "json") -> str:
        """Wisdom 통계 내보내기"""
        visualizer = WisdomVisualizer(self)
        return visualizer.export_stats(format)
    
    def switch_project(self, project_name: str):
        """프로젝트 전환 및 프로젝트별 Wisdom 로드"""
        # 현재 프로젝트 Wisdom 저장
        if hasattr(self, 'project_store'):
            self.project_store.save_project_wisdom(self.project_name, self.wisdom_data)
        
        # 새 프로젝트로 전환
        self.project_name = project_name
        
        # 프로젝트별 Wisdom 로드
        if not hasattr(self, 'project_store'):
            self.project_store = ProjectWisdomStore(self.wisdom_dir)
        
        self.wisdom_data = self.project_store.get_project_wisdom(project_name)
        print(f"🧠 프로젝트 '{project_name}' Wisdom 로드 완료")


# 싱글톤 인스턴스
_wisdom_manager = None

def get_wisdom_manager(project_root: str = ".") -> ProjectWisdomManager:
    """Wisdom Manager singleton instance"""
    global _wisdom_manager
    if _wisdom_manager is None:
        _wisdom_manager = ProjectWisdomManager(project_root)
    return _wisdom_manager
