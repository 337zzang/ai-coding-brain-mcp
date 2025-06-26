#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
프로젝트 상태 브리핑 모듈
프로젝트의 현재 상태를 종합적으로 요약하여 제공

작성일: 2025-06-24
"""

import os
import json
from datetime import datetime, timedelta
from collections import Counter
from pathlib import Path
from typing import Dict, Any, List, Optional

def get_project_status_briefing(context: Any, wisdom: Any = None) -> Dict[str, Any]:
    """프로젝트의 현재 상태를 요약하여 딕셔너리로 반환합니다."""
    
    briefing = {
        "📌 현재 작업 (Current Task)": [],
        "📋 다음 작업 목록 (Next Tasks)": [],
        "🧠 최근 실수 패턴 (Recent Mistakes)": [],
        "📂 프로젝트 구조 (Structure)": "",
        "📈 작업 진행률 (Progress)": [],
        "🕐 최근 활동 (Recent Activity)": []
    }
    
    # 1. 현재 작업 가져오기
    current_task = context.get('current_task', None)
    if current_task:
        if isinstance(current_task, dict):
            task_desc = current_task.get('description', '설명 없음')
            task_id = current_task.get('id', 'N/A')
            briefing["📌 현재 작업 (Current Task)"].append(f"**(진행중)** [{task_id}] {task_desc}")
        else:
            briefing["📌 현재 작업 (Current Task)"].append(f"**(진행중)** {current_task}")
    else:
        briefing["📌 현재 작업 (Current Task)"].append("진행 중인 작업이 없습니다. '/plan'으로 계획을 수립하세요.")

    # 2. 다음 작업 목록 가져오기
    task_list = context.get('task_list', [])
    pending_tasks = [task for task in task_list if not task.get('done', False)][:3]
    
    if pending_tasks:
        for task in pending_tasks:
            task_desc = task.get('description', '설명 없음')
            task_id = task.get('id', 'N/A')
            briefing["📋 다음 작업 목록 (Next Tasks)"].append(f"[{task_id}] {task_desc}")
    else:
        briefing["📋 다음 작업 목록 (Next Tasks)"].append("대기 중인 작업이 없습니다.")
        
    # 3. Wisdom 시스템에서 정보 가져오기
    if wisdom and hasattr(wisdom, 'wisdom_data'):
        mistakes = wisdom.wisdom_data.get('common_mistakes', {})
        # 최근 실수들 (count가 높은 순으로 정렬)
        sorted_mistakes = sorted(mistakes.items(), key=lambda x: x[1].get('count', 0), reverse=True)[:2]
        
        for mistake_type, data in sorted_mistakes:
            count = data.get('count', 0)
            if count > 0:
                briefing["🧠 최근 실수 패턴 (Recent Mistakes)"].append(
                    f"{mistake_type}: {count}회 발생"
                )
                
        if not briefing["🧠 최근 실수 패턴 (Recent Mistakes)"]:
            briefing["🧠 최근 실수 패턴 (Recent Mistakes)"].append("추적된 실수가 없습니다. 훌륭합니다!")
    else:
        briefing["🧠 최근 실수 패턴 (Recent Mistakes)"].append("Wisdom 시스템이 비활성화되어 있습니다.")
    
    # 4. 프로젝트 구조 정보
    analyzed_files = context.get('analyzed_files', {})
    file_count = len(analyzed_files)
    
    # 파일 확장자별 통계
    extensions = Counter()
    for filepath in analyzed_files.keys():
        ext = Path(filepath).suffix.lower()
        if ext:
            extensions[ext] += 1
    
    structure_info = f"총 {file_count}개 파일 분석됨"
    if extensions:
        top_exts = extensions.most_common(3)
        ext_str = ", ".join([f"{ext}: {count}개" for ext, count in top_exts])
        structure_info += f" ({ext_str})"
    
    briefing["📂 프로젝트 구조 (Structure)"] = structure_info
    
    # 5. 작업 진행률
    if task_list:
        total_tasks = len(task_list)
        done_tasks = len([t for t in task_list if t.get('done', False)])
        progress_pct = (done_tasks / total_tasks * 100) if total_tasks > 0 else 0
        briefing["📈 작업 진행률 (Progress)"].append(
            f"전체 {total_tasks}개 중 {done_tasks}개 완료 ({progress_pct:.1f}%)"
        )
    
    # 6. 최근 활동
    file_history = context.get('file_access_history', [])
    if file_history:
        # 최근 3개 파일
        recent_files = file_history[-3:]
        for file_info in reversed(recent_files):
            if isinstance(file_info, dict):
                filepath = file_info.get('file', 'Unknown')
                action = file_info.get('action', 'accessed')
                briefing["🕐 최근 활동 (Recent Activity)"].append(f"{Path(filepath).name} - {action}")
            else:
                briefing["🕐 최근 활동 (Recent Activity)"].append(str(file_info))
    
    return briefing


def generate_project_context_summary(context):
    """기존 함수와의 호환성을 위한 래퍼 함수"""
    briefing = get_project_status_briefing(context)
    
    summary_lines = []
    summary_lines.append("\n📊 프로젝트 작업 컨텍스트 요약")
    summary_lines.append("=" * 60)
    
    for category, items in briefing.items():
        summary_lines.append(f"\n{category}:")
        if isinstance(items, list):
            for item in items:
                summary_lines.append(f"  • {item}")
        else:
            summary_lines.append(f"  {items}")
    
    return "\n".join(summary_lines)
