"""
Task 분석 및 컨텍스트 관리를 위한 헬퍼 함수들

Task 간 연속성을 유지하고 이전 작업 컨텍스트를 쉽게 확인할 수 있도록
TaskLogger의 JSONL 로그를 분석하고 구조화하는 기능을 제공합니다.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from .ultra_simple_flow_manager import UltraSimpleFlowManager
from .git import git_log, git_status


def get_task_log(plan_id: str, task_id: str) -> Dict[str, Any]:
    """
    특정 Task의 로그를 읽어서 구조화된 형태로 반환

    Args:
        plan_id: Plan ID
        task_id: Task ID

    Returns:
        Response with data:
            - events: 전체 이벤트 리스트
            - summary: 이벤트 타입별 요약
            - completion_message: 완료 메시지
            - created_files: 생성된 파일 목록
            - decisions: 주요 의사결정 목록
    """
    try:
        # TaskLogger 경로 패턴
        base_path = Path(f".ai-brain/flow/plans/{plan_id}")
        if not base_path.exists():
            return {'ok': False, 'error': f'Plan 디렉토리를 찾을 수 없습니다: {plan_id}'}

        # Task에 해당하는 JSONL 파일 찾기
        jsonl_file = None
        for file in base_path.glob("*.jsonl"):
            # 파일명에 task_id가 포함되어 있는지 확인
            if task_id in file.name:
                jsonl_file = file
                break

        if not jsonl_file:
            # 더 정확한 매칭을 위해 Task 정보 조회
            manager = UltraSimpleFlowManager()
            plan = manager.get_plan(plan_id)
            if plan and hasattr(plan, 'tasks'):
                # Task 번호와 이름으로 파일 찾기
                for i, (tid, task) in enumerate(plan.tasks.items(), 1):
                    if tid == task_id:
                        # 파일명 패턴: {번호}.{task_name}.jsonl
                        task_name = task.title.replace(' ', '_').replace(':', '')
                        pattern = f"{i}.*.jsonl"
                        for file in base_path.glob(pattern):
                            jsonl_file = file
                            break
                        break

        if not jsonl_file or not jsonl_file.exists():
            return {'ok': False, 'error': f'Task 로그 파일을 찾을 수 없습니다: {task_id}'}

        # JSONL 파일 읽기
        events = []
        with open(jsonl_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        event = json.loads(line)
                        events.append(event)
                    except json.JSONDecodeError:
                        continue

        # 이벤트 요약 생성
        summary = {
            'total_events': len(events),
            'event_types': {},
            'code_changes': [],
            'decisions': [],
            'blockers': [],
            'notes': []
        }

        completion_message = ""
        created_files = []

        for event in events:
            event_type = event.get('type', 'UNKNOWN')

            # 이벤트 타입별 카운트
            summary['event_types'][event_type] = summary['event_types'].get(event_type, 0) + 1

            # 중요 이벤트 추출
            if event_type == 'CODE':
                summary['code_changes'].append({
                    'action': event.get('action'),
                    'target': event.get('target'),
                    'summary': event.get('summary'),
                    'timestamp': event.get('timestamp')
                })
                # 파일 생성 추적
                if event.get('action') == 'create':
                    created_files.append(event.get('target'))

            elif event_type == 'DECISION':
                summary['decisions'].append({
                    'title': event.get('title'),
                    'choice': event.get('choice'),
                    'timestamp': event.get('timestamp')
                })

            elif event_type == 'BLOCKER':
                summary['blockers'].append({
                    'issue': event.get('issue'),
                    'severity': event.get('severity'),
                    'solution': event.get('solution'),
                    'timestamp': event.get('timestamp')
                })

            elif event_type == 'NOTE':
                summary['notes'].append({
                    'message': event.get('message'),
                    'timestamp': event.get('timestamp')
                })

            elif event_type == 'COMPLETE':
                completion_message = event.get('message', '')

        return {
            'ok': True,
            'data': {
                'plan_id': plan_id,
                'task_id': task_id,
                'log_file': str(jsonl_file),
                'events': events,
                'summary': summary,
                'completion_message': completion_message,
                'created_files': created_files
            }
        }

    except Exception as e:
        return {'ok': False, 'error': f'로그 분석 중 오류 발생: {str(e)}'}


def get_previous_task_context(plan_id: str, current_task_id: str) -> Dict[str, Any]:
    """
    현재 Task의 직전 완료된 Task 컨텍스트를 반환

    Args:
        plan_id: Plan ID
        current_task_id: 현재 Task ID

    Returns:
        Response with data:
            - previous_task: 이전 Task 정보
            - log_summary: 이전 Task 로그 요약
            - git_changes: Git 변경사항
            - unfinished_items: 미완료 항목
    """
    try:
        manager = UltraSimpleFlowManager()
        plan = manager.get_plan(plan_id)

        if not plan or not hasattr(plan, 'tasks'):
            return {'ok': False, 'error': f'Plan을 찾을 수 없습니다: {plan_id}'}

        # Task 목록에서 현재 Task 위치 찾기
        task_list = list(plan.tasks.items())
        current_index = -1

        for i, (task_id, task) in enumerate(task_list):
            if task_id == current_task_id:
                current_index = i
                break

        if current_index == -1:
            return {'ok': False, 'error': f'Task를 찾을 수 없습니다: {current_task_id}'}

        # 이전 완료된 Task 찾기
        previous_task = None
        previous_task_id = None

        for i in range(current_index - 1, -1, -1):
            task_id, task = task_list[i]
            if task.status == 'done':
                previous_task = task
                previous_task_id = task_id
                break

        if not previous_task:
            return {
                'ok': True,
                'data': {
                    'previous_task': None,
                    'log_summary': None,
                    'git_changes': None,
                    'unfinished_items': [],
                    'message': '이전 완료된 Task가 없습니다 (첫 번째 Task)'
                }
            }

        # 이전 Task 로그 분석
        log_result = get_task_log(plan_id, previous_task_id)
        if not log_result['ok']:
            return {'ok': False, 'error': f'이전 Task 로그 분석 실패: {log_result["error"]}'}

        log_summary = log_result['data']

        # Git 변경사항 확인 (이전 Task 완료 시점 이후)
        git_changes = {
            'commits': [],
            'modified_files': [],
            'created_files': log_summary['created_files']
        }

        # 최근 커밋 확인
        git_log_result = git_log(limit=10)
        if git_log_result['ok']:
            # 이전 Task 완료 시간과 비교
            if previous_task.completed_at:
                completed_time = datetime.fromisoformat(previous_task.completed_at.replace('Z', '+00:00'))
                for commit in git_log_result['data']:
                    # 커밋 시간 파싱 (간단한 비교를 위해)
                    if 'date' in commit:
                        git_changes['commits'].append(commit)

        # 현재 변경된 파일
        git_status_result = git_status()
        if git_status_result['ok']:
            git_changes['modified_files'] = git_status_result['data']['files']

        # 미완료 항목 추출 (BLOCKER가 있었는지 확인)
        unfinished_items = []
        if log_summary['summary']['blockers']:
            for blocker in log_summary['summary']['blockers']:
                if blocker['severity'] in ['high', 'critical']:
                    unfinished_items.append({
                        'type': 'blocker',
                        'description': blocker['issue'],
                        'solution': blocker['solution']
                    })

        return {
            'ok': True,
            'data': {
                'previous_task': {
                    'id': previous_task_id,
                    'title': previous_task.title,
                    'status': previous_task.status,
                    'completed_at': previous_task.completed_at
                },
                'log_summary': {
                    'completion_message': log_summary['completion_message'],
                    'total_events': log_summary['summary']['total_events'],
                    'code_changes': len(log_summary['summary']['code_changes']),
                    'decisions': log_summary['summary']['decisions'],
                    'notes': log_summary['summary']['notes']
                },
                'git_changes': git_changes,
                'unfinished_items': unfinished_items
            }
        }

    except Exception as e:
        return {'ok': False, 'error': f'컨텍스트 분석 중 오류 발생: {str(e)}'}
