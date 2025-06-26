#!/usr/bin/env python3
"""
Wisdom 시스템 명령어 - 리포트 생성 및 통계 확인
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from project_wisdom import get_wisdom_manager
from wisdom_visualizer import WisdomVisualizer, ProjectWisdomStore
from pathlib import Path


def cmd_wisdom(action: str = "report", project: str = None, format: str = "text"):
    """
    Wisdom 시스템 명령어
    
    Actions:
        report - Wisdom 리포트 생성
        stats - 통계 내보내기
        list - 프로젝트 목록
        switch - 프로젝트 전환
    """
    wisdom = get_wisdom_manager()
    visualizer = WisdomVisualizer(wisdom)
    store = ProjectWisdomStore(Path("memory/wisdom"))
    
    if action == "report":
        # Wisdom 리포트 생성
        report = visualizer.generate_report()
        print(report)
        
        # 파일로도 저장
        report_file = Path(f"wisdom_report_{wisdom.project_name}.md")
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\n📄 리포트 저장: {report_file}")
        
    elif action == "stats":
        # 통계 내보내기
        stats = visualizer.export_stats(format)
        print(stats)
        
        # 파일로 저장
        ext = "json" if format == "json" else "csv"
        stats_file = Path(f"wisdom_stats_{wisdom.project_name}.{ext}")
        with open(stats_file, 'w', encoding='utf-8') as f:
            f.write(stats)
        print(f"\n📊 통계 저장: {stats_file}")
        
    elif action == "list":
        # 프로젝트 목록
        projects = store.list_projects()
        print("🧠 Wisdom 데이터가 있는 프로젝트:")
        for i, proj in enumerate(projects, 1):
            print(f"  {i}. {proj}")
            
    elif action == "switch" and project:
        # 프로젝트 전환
        # 현재 프로젝트 Wisdom 저장
        store.save_project_wisdom(wisdom.project_name, wisdom.wisdom_data)
        
        # 새 프로젝트 Wisdom 로드
        wisdom.project_name = project
        wisdom.wisdom_data = store.get_project_wisdom(project)
        wisdom._save_wisdom()
        
        print(f"✅ 프로젝트 전환: {project}")
        print(f"  - 실수: {len(wisdom.wisdom_data.get('common_mistakes', {}))}개")
        print(f"  - 베스트 프랙티스: {len(wisdom.wisdom_data.get('best_practices', []))}개")
        
    else:
        print("❌ 알 수 없는 명령입니다.")
        print("사용법: cmd_wisdom(action='report|stats|list|switch', project='프로젝트명', format='json|csv')")
    
    return True


# 바로 실행 가능하도록
if __name__ == "__main__":
    if len(sys.argv) > 1:
        action = sys.argv[1]
        project = sys.argv[2] if len(sys.argv) > 2 else None
        format_type = sys.argv[3] if len(sys.argv) > 3 else "text"
        cmd_wisdom(action, project, format_type)
    else:
        cmd_wisdom()
