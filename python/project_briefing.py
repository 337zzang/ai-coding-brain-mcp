#!/usr/bin/env python3
"""
프로젝트 브리핑 시스템
flow_project 실행 후 show_project_briefing()으로 호출
"""

import os
from typing import Dict, Any
from datetime import datetime


def print_project_briefing(briefing_data: Dict[str, Any]):
    """ProjectAnalyzer가 제공한 브리핑 데이터를 출력"""
    import sys
    import os
    # Python 경로 설정
    python_path = os.path.dirname(os.path.abspath(__file__))
    if python_path not in sys.path:
        sys.path.insert(0, python_path)
    
    from smart_print import smart_print
    
    print("\n" + "=" * 70)
    print("📊 **프로젝트 상태 브리핑**")
    print("=" * 70)
    
    # 1. 프로젝트 정보
    project_info = briefing_data.get('project_info', {})
    print(f"\n📍 **프로젝트 정보**")
    print(f"  • 이름: {project_info.get('name', 'Unknown')}")
    print(f"  • 경로: {project_info.get('path', 'Unknown')}")
    print(f"  • 언어: {project_info.get('language', 'Unknown')}")
    print(f"  • 전체 파일: {project_info.get('total_files', 0)}개")
    
    # 2. 프로젝트 구조
    structure = briefing_data.get('structure', {})
    if structure:
        print(f"\n📂 **프로젝트 구조**")
        # 구조 요약 출력
        dirs = structure.get('directories', [])
        files_by_type = structure.get('files_by_type', {})
        print(f"  • 디렉토리: {len(dirs)}개")
        for ext, count in list(files_by_type.items())[:5]:
            print(f"  • {ext} 파일: {count}개")
    
    # 3. 최근 수정된 파일
    recent_files = briefing_data.get('recent_files', [])
    if recent_files:
        print(f"\n📝 **최근 수정된 파일** (상위 5개)")
        for file_info in recent_files[:5]:
            print(f"  • {file_info['path']} - {file_info.get('modified', 'Unknown')}")
    
    # 4. 작업 상태
    task_status = briefing_data.get('task_status', {})
    if task_status:
        print(f"\n📋 **작업 상태**")
        print(f"  • 현재 작업: {task_status.get('current_task', '없음')}")
        
        tasks = task_status.get('pending_tasks', [])
        if tasks:
            print(f"\n  📌 대기 중인 작업:")
            for task in tasks[:5]:
                print(f"    - {task}")
        
        progress = task_status.get('progress', 0)
        print(f"\n📊 **전체 진행률**: {progress:.1f}%")
    
    # 5. Wisdom 상태
    wisdom_data = briefing_data.get('wisdom', {})
    if wisdom_data:
        print(f"\n🧠 **프로젝트 지혜**")
        print(f"  • 추적된 실수: {wisdom_data.get('mistakes_count', 0)}종류")
        
        top_mistake = wisdom_data.get('most_frequent_mistake')
        if top_mistake:
            print(f"  • 가장 빈번한 실수: {top_mistake['type']} ({top_mistake['count']}회)")
    
    # 6. 다음 단계 추천
    next_steps = briefing_data.get('next_steps', [])
    if next_steps:
        print(f"\n🎯 **다음 해야 할 일**")
        for i, step in enumerate(next_steps[:3], 1):
            print(f"  {i}. {step}")
    
    print("\n" + "=" * 70)


def show_project_briefing():
    """현재 프로젝트의 완전한 브리핑을 표시"""
    import sys
    
    # 전역 context와 helpers 가져오기
    main_module = sys.modules.get('__main__')
    if not main_module:
        print("❌ 브리핑을 표시할 수 없습니다. execute_code 환경에서 실행하세요.")
        return
    
    context = getattr(main_module, 'context', {})
    helpers = getattr(main_module, 'helpers', None)
    
    if not context or not helpers:
        print("❌ context 또는 helpers를 찾을 수 없습니다.")
        return
    
    print("\n" + "=" * 70)
    print("📊 **프로젝트 현재 상태 브리핑**")
    print("=" * 70)
    
    # 1. 프로젝트 정보
    print(f"\n📍 **프로젝트 정보**")
    print(f"  • 이름: {context.get('project_name', 'Unknown')}")
    print(f"  • 경로: {os.getcwd()}")
    print(f"  • 언어: {context.get('language', 'Unknown')}")
    
    # 프로젝트 통계
    try:
        structure = helpers.scan_directory_dict(".")
        files = structure.get('files', [])
        py_count = len([f for f in files if f.endswith('.py')])
        ts_count = len([f for f in files if f.endswith('.ts')])
        print(f"  • 규모: {len(files)}개 파일 (Python: {py_count}, TypeScript: {ts_count})")
    except:
        pass
    
    # 2. 작업 상태
    print(f"\n📋 **작업 상태**")
    current_task = context.get('current_task')
    print(f"  • 현재 작업: {current_task or '없음'}")
    
    # 3. 최근 활동
    print(f"\n📂 **최근 활동**")
    try:
        work_summary = helpers.get_work_tracking_summary()
        if work_summary and 'file_access' in work_summary:
            file_access = work_summary['file_access']
            recent_files = list(file_access.items())[-5:]
            for file, count in recent_files:
                print(f"  • {file}: {count}회 접근")
    except:
        print("  • 활동 기록 없음")
    
    # 4. Wisdom 상태
    print(f"\n🧠 **Wisdom 상태**")
    try:
        from project_wisdom import get_wisdom_manager
        wisdom = get_wisdom_manager()
        mistakes = wisdom.wisdom_data.get('common_mistakes', {})
        practices = wisdom.wisdom_data.get('best_practices', [])
        
        total_mistakes = sum(m.get('count', 0) for m in mistakes.values())
        print(f"  • 추적된 실수: {total_mistakes}회 ({len(mistakes)}종류)")
        
        # Top 3 실수
        if mistakes:
            sorted_mistakes = sorted(mistakes.items(), 
                                   key=lambda x: x[1].get('count', 0), 
                                   reverse=True)
            print(f"  • 주요 실수:")
            for mistake, data in sorted_mistakes[:3]:
                print(f"    - {mistake}: {data.get('count', 0)}회")
        
        print(f"  • 베스트 프랙티스: {len(practices)}개")
    except:
        print("  • Wisdom 시스템 로드 실패")
    
    # 5. 추천 사항
    print(f"\n💡 **추천 다음 단계**")
    if current_task:
        print(f"  1. 현재 작업 계속: {current_task}")
        print(f"  2. 완료시: task_manage('done', ['task-id'])")
    else:
        print(f"  1. 새 작업 시작: task_manage('add', ['phase', '작업명'])")
        print(f"  2. 계획 수립: plan_project('계획명')")
    
    # Wisdom 기반 추천
    if 'mistakes' in locals() and mistakes:
        top_mistake = list(mistakes.keys())[0]
        if top_mistake == "no_backup":
            print(f"  ⚠️ 파일 수정 전 항상 백업하세요!")
        elif top_mistake == "console_usage":
            print(f"  ⚠️ console 대신 logger 사용하세요!")
    
    print("\n" + "=" * 70 + "\n")


# 전역으로 사용 가능하도록
if __name__ != "__main__":
    import sys
    main_module = sys.modules.get('__main__')
    if main_module:
        main_module.show_project_briefing = show_project_briefing
