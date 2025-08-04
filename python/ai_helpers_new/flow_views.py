"""
Flow Views - 출력 및 포맷팅 함수
분리일: 2025-08-03
원본: simple_flow_commands.py
"""

import os
from typing import Dict, List, Optional, Any
from datetime import datetime

from .domain.models import Plan, Task, TaskStatus
from .ultra_simple_flow_manager import UltraSimpleFlowManager
from .project import get_current_project
from .flow_manager_utils import get_manager
# Response helper
def ok_response(data=None, message=None):
    response = {'ok': True}
    if data is not None: response['data'] = data
    if message: response['message'] = message
    return response


def format_timestamp(timestamp: str) -> str:
    """타임스탬프를 읽기 쉬운 형식으로 변환"""
    try:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M')
    except:
        return timestamp


def show_status(manager: UltraSimpleFlowManager) -> None:
    """현재 상태 표시"""

    print("\n📊 Flow 시스템 상태")
    print("=" * 50)
    print(f"프로젝트: {manager.project_name}")

    plans = manager.list_plans()
    print(f"\nPlan 개수: {len(plans)}개")

    # 최근 Plan 3개 표시
    if plans:
        recent_plans = sorted(plans, key=lambda p: p.created_at, reverse=True)[:3]
        print("\n📌 최근 Plan (최대 3개):")
        for i, plan in enumerate(recent_plans):
            task_count = len(plan.tasks) if hasattr(plan, 'tasks') else 0
            if i == 0:
                print(f"  • {plan.id}: {plan.name} (Task {task_count}개) 🔥 가장 최근")
            else:
                print(f"  • {plan.id}: {plan.name} (Task {task_count}개)")

    if get_current_plan_id():
        plan = manager.get_plan(get_current_plan_id())
        if plan:
            print(f"\n현재 선택된 Plan: {plan.name}")
            print(f"Task 개수: {len(plan.tasks)}개")

            # Task 상태별 개수
            todo = sum(1 for t in plan.tasks.values() if str(t.status).endswith("TODO"))
            in_progress = sum(1 for t in plan.tasks.values() if str(t.status).endswith("IN_PROGRESS"))
            done = sum(1 for t in plan.tasks.values() if str(t.status).endswith("DONE"))

            print(f"  - 할 일: {todo}개")
            print(f"  - 진행중: {in_progress}개")
            print(f"  - 완료: {done}개")
    else:
        print("\n선택된 Plan이 없습니다. /select [plan_id]로 선택하세요.")

def show_plans(manager: UltraSimpleFlowManager) -> None:
    """Plan 목록 표시"""
    plans = manager.list_plans()

    if not plans:
        print("\n📋 Plan이 없습니다. /create [이름]으로 생성하세요.")
        return

    print(f"\n📋 Plan 목록 ({len(plans)}개)")
    print("=" * 60)

    for plan in plans:
        task_count = len(plan.tasks) if hasattr(plan, 'tasks') else 0
        print(f"\n{plan.id}")
        print(f"  이름: {plan.name}")
        print(f"  상태: {plan.status}")
        print(f"  Task: {task_count}개")
        print(f"  생성: {str(plan.created_at)[:19]}")

def display_task_history(plan_id: str, show_all: bool = False):
    """완료된 Task들의 JSONL 전체 내역을 모두 표시"""
    plan_dir = os.path.join(
        get_manager().project_path,
        ".ai-brain", "flow", "plans", plan_id
    )

    if not os.path.exists(plan_dir):
        return

    print("\n📋 기존 Task 작업 내역 (전체):")
    print("="*80)

    jsonl_files = sorted(glob.glob(os.path.join(plan_dir, "*.jsonl")))
    
    for jsonl_file in jsonl_files:
        task_name = os.path.basename(jsonl_file).replace('.jsonl', '')
        events = []

        # JSONL 파일 읽기
        try:
            with open(jsonl_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        try:
                            events.append(json.loads(line.strip()))
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            print(f"\n❌ 파일 읽기 오류 ({task_name}): {e}")
            continue

        # 완료된 Task만 표시 (또는 전체 표시)
        is_completed = any(
            e.get('event_type') == 'COMPLETE' or e.get('type') == 'COMPLETE' 
            for e in events
        )

        if is_completed or show_all:
            print(f"\n\n{'='*80}")
            print(f"📁 Task: {task_name}")
            print(f"📊 총 이벤트: {len(events)}개")
            print("="*80)
            
            # 모든 이벤트를 순서대로 표시
            for i, event in enumerate(events, 1):
                event_type = event.get('event_type') or event.get('type', 'UNKNOWN')
                timestamp = event.get('timestamp', event.get('ts', 'N/A'))
                
                print(f"\n[이벤트 #{i}] {event_type} - {timestamp}")
                print("-"*60)
                
                # 이벤트 타입별 전체 내용 표시
                if event_type == 'TASK_INFO':
                    print(f"  📌 제목: {event.get('title', 'N/A')}")
                    print(f"  ⏰ 예상시간: {event.get('estimate', 'N/A')}")
                    print(f"  🎯 우선순위: {event.get('priority', 'N/A')}")
                    desc = event.get('description', '')
                    if desc:
                        print(f"  📝 설명: {desc}")
                        
                elif event_type == 'DESIGN':
                    design_content = event.get('design', '')
                    if design_content:
                        print("  🏗️ 설계 내용:")
                        for line in design_content.split('\n'):
                            print(f"    {line}")
                            
                elif event_type == 'TODO':
                    todos = event.get('todos', [])
                    print(f"  📋 TODO 목록 ({len(todos)}개):")
                    for j, todo in enumerate(todos, 1):
                        print(f"    {j}. {todo}")
                        
                elif event_type == 'TODO_UPDATE':
                    completed = event.get('completed', [])
                    remaining = event.get('remaining', [])
                    new_todos = event.get('new', [])
                    blocked = event.get('blocked', [])
                    
                    if completed:
                        print(f"  ✅ 완료된 항목 ({len(completed)}개):")
                        for item in completed:
                            print(f"    - {item}")
                    if remaining:
                        print(f"  ⏳ 남은 항목 ({len(remaining)}개):")
                        for item in remaining:
                            print(f"    - {item}")
                    if new_todos:
                        print(f"  🆕 새로 추가된 항목 ({len(new_todos)}개):")
                        for item in new_todos:
                            print(f"    - {item}")
                    if blocked:
                        print(f"  🚫 블로킹된 항목 ({len(blocked)}개):")
                        for item in blocked:
                            print(f"    - {item}")
                            
                elif event_type == 'ANALYZE':
                    target = event.get('target', 'N/A')
                    result = event.get('result', '')
                    print(f"  🔍 분석 대상: {target}")
                    if result:
                        print(f"  📊 분석 결과:")
                        for line in result.split('\n'):
                            print(f"    {line}")
                            
                elif event_type == 'CODE':
                    action = event.get('action', 'N/A')
                    file_path = event.get('file', 'N/A')
                    summary = event.get('summary', '')
                    print(f"  🔧 액션: {action}")
                    print(f"  📄 파일: {file_path}")
                    if summary:
                        print(f"  📝 요약:")
                        for line in summary.split('\n'):
                            print(f"    {line}")
                            
                elif event_type == 'DECISION':
                    decision = event.get('decision', '')
                    rationale = event.get('rationale', '')
                    print(f"  🤔 결정: {decision}")
                    if rationale:
                        print(f"  💭 이유: {rationale}")
                        
                elif event_type == 'BLOCKER':
                    issue = event.get('issue', '')
                    severity = event.get('severity', 'N/A')
                    solution = event.get('solution', '')
                    print(f"  🚨 이슈: {issue}")
                    print(f"  ⚠️ 심각도: {severity}")
                    if solution:
                        print(f"  💡 해결방안: {solution}")
                        
                elif event_type == 'NOTE':
                    content = event.get('content', event.get('note', ''))
                    print(f"  📝 메모: {content}")
                    
                elif event_type == 'CONTEXT':
                    ctx_type = event.get('context_type', 'N/A')
                    ctx_data = event.get('data', '')
                    print(f"  🔗 컨텍스트 타입: {ctx_type}")
                    print(f"  📋 데이터: {ctx_data}")
                    
                elif event_type == 'COMPLETE':
                    summary = event.get('summary', '')
                    print(f"  ✅ 완료 요약:")
                    if summary:
                        for line in summary.split('\n'):
                            print(f"    {line}")
                else:
                    # 알 수 없는 이벤트 타입의 경우 전체 내용 표시
                    print(f"  📦 전체 데이터:")
                    print(json.dumps(event, indent=4, ensure_ascii=False))
            
            print(f"\n{'='*80}")
            print(f"📊 Task '{task_name}' 종료 - 총 {len(events)}개 이벤트")
            print("="*80)

def show_tasks(manager: UltraSimpleFlowManager, plan_id: str) -> None:
    """Task 목록 표시"""
    plan = manager.get_plan(plan_id)
    if not plan:
        return

    if not plan.tasks:
        print(f"\n📝 {plan.name}에 Task가 없습니다.")
        print("  /task add [제목]으로 추가하세요.")
        return

    print(f"\n📝 {plan.name}의 Task 목록")
    print("=" * 60)

    for task in plan.tasks.values():
        status_emoji = {
            "TODO": "⬜",
            "IN_PROGRESS": "🟨", 
            "DONE": "✅"
        }
        status_str = str(task.status).split(".")[-1]
        emoji = status_emoji.get(status_str, "❓")

        print(f"\n{emoji} {task.id}")
        print(f"   {task.title}")
        print(f"   상태: {status_str}")

def _show_project_summary():
    """프로젝트 문서 요약 표시"""
    try:
        # file 모듈의 read 함수 import
        from .file import read as h_read

        readme_exists = False
        file_dir_exists = False

        # readme.md 확인 및 요약
        try:
            readme = h_read('readme.md')
            if readme['ok']:
                readme_exists = True
                lines = readme['data'].split('\n')

                print("\n📄 README.md 요약")
                print("=" * 60)

                # 주요 기능 찾기
                in_features = False
                feature_count = 0
                for line in lines:
                    if '주요 기능' in line and line.startswith('#'):
                        in_features = True
                        continue
                    elif in_features and line.startswith('#'):
                        break
                    elif in_features and line.strip() and feature_count < 3:
                        print(f"  {line.strip()}")
                        feature_count += 1
        except:
            pass

        # file_directory.md 확인 및 구조 표시
        try:
            file_dir = h_read('file_directory.md')
            if file_dir['ok']:
                file_dir_exists = True
                lines = file_dir['data'].split('\n')

                # 통계 정보
                print("\n📁 파일 구조 통계")
                print("=" * 60)

                for line in lines[:20]:
                    if '총 파일 수:' in line:
                        print(f"  {line.strip()}")
                    elif '총 디렉토리 수:' in line:
                        print(f"  {line.strip()}")

                # 디렉토리 트리 표시
                print("\n📂 프로젝트 구조")
                print("=" * 60)

                tree_lines = []
                i = 0

                while i < len(lines):
                    line = lines[i]

                    # 디렉토리 트리 섹션 찾기
                    if '디렉토리 트리' in line:
                        # ``` 코드 블록 시작 찾기
                        for j in range(i+1, min(i+5, len(lines))):
                            if lines[j].strip() == '```':
                                # 코드 블록 내용 수집
                                for k in range(j+1, len(lines)):
                                    if lines[k].strip() == '```':
                                        i = k  # 루프 인덱스 업데이트
                                        break
                                    else:
                                        tree_lines.append(lines[k].rstrip())
                                break
                        break
                    i += 1

                # 트리 출력 (전체)
                for line in tree_lines:
                    print(line)

                # 주요 파일 찾기
                print("\n📌 주요 파일")
                print("-" * 60)

                # 진입점 파일 찾기
                entry_points = ['main.py', 'index.js', 'index.ts', 'app.py', 'server.js', 
                              'server.py', '__main__.py', 'run.py', 'json_repl_session.py']
                config_files = ['config.py', 'settings.py', 'package.json', 'pyproject.toml',
                              'requirements.txt', 'setup.py', 'tsconfig.json']
                important_files = ['README.md', 'readme.md', 'LICENSE', '.gitignore']

                found_files = []

                # file_directory.md에서 파일 찾기
                for line in lines:
                    # 진입점 파일
                    for entry in entry_points:
                        if entry in line and ('│' in line or '├' in line or '└' in line):
                            file_entry = f"  🎯 진입점: {entry}"
                            if file_entry not in found_files:
                                found_files.append(file_entry)

                    # 설정 파일
                    for config in config_files:
                        if config in line and ('│' in line or '├' in line or '└' in line):
                            file_entry = f"  ⚙️ 설정: {config}"
                            if file_entry not in found_files:
                                found_files.append(file_entry)

                    # 중요 파일
                    for imp_file in important_files:
                        if imp_file in line and ('│' in line or '├' in line or '└' in line):
                            file_entry = f"  📋 문서: {imp_file}"
                            if file_entry not in found_files:
                                found_files.append(file_entry)

                # 출력 (모든 찾은 파일)
                for file in found_files:
                    print(file)

            else:
                # file_directory.md가 없을 때 직접 스캔
                _show_direct_structure()

        except Exception as e:
            # 오류 시 직접 스캔
            _show_direct_structure()

        # 문서 존재 여부 표시
        if readme_exists or file_dir_exists:
            print("\n📚 프로젝트 문서:")
            if readme_exists:
                print("  - readme.md ✅")
            if file_dir_exists:
                print("  - file_directory.md ✅")
            print("  💡 팁: /a 명령어로 문서를 업데이트할 수 있습니다.")
        else:
            print("\n💡 팁: /a 명령어로 프로젝트 문서를 생성할 수 있습니다.")

    except Exception as e:
        # 조용히 실패
        pass
def _show_direct_structure():
    """file_directory.md가 없을 때 직접 디렉토리 구조 표시"""
    try:
        from pathlib import Path

        print("\n📂 프로젝트 구조")
        print("=" * 60)

        def show_tree(path, prefix="", is_last=True, level=0, max_level=3):
            """디렉토리 트리를 재귀적으로 표시"""
            if level > max_level:
                return

            # 현재 디렉토리의 항목들
            try:
                items = sorted(os.listdir(path))
                # 숨김 파일과 특정 폴더 제외
                items = [item for item in items 
                        if not item.startswith('.') 
                        and item not in ['node_modules', '__pycache__', 'venv', 'dist', 'build']]

                dirs = [item for item in items if os.path.isdir(os.path.join(path, item))]
                files = [item for item in items if os.path.isfile(os.path.join(path, item))]

                # 디렉토리 먼저, 파일 나중에
                all_items = dirs + files

                for i, item in enumerate(all_items):
                    is_last_item = (i == len(all_items) - 1)
                    item_path = os.path.join(path, item)

                    # 트리 문자 선택
                    if is_last_item:
                        print(prefix + "└── ", end="")
                        new_prefix = prefix + "    "
                    else:
                        print(prefix + "├── ", end="")
                        new_prefix = prefix + "│   "

                    # 아이템 표시
                    if os.path.isdir(item_path):
                        print(f"📂 {item}/")
                        # 재귀적으로 하위 디렉토리 표시
                        show_tree(item_path, new_prefix, is_last_item, level + 1, max_level)
                    else:
                        # 파일 아이콘 선택
                        if item.endswith('.py'):
                            icon = "🐍"
                        elif item.endswith(('.js', '.ts', '.jsx', '.tsx')):
                            icon = "📜"
                        elif item.endswith('.json'):
                            icon = "📋"
                        elif item.endswith('.md'):
                            icon = "📝"
                        else:
                            icon = "📄"
                        print(f"{icon} {item}")

            except PermissionError:
                pass

        # 프로젝트 이름 표시
        current = get_current_project()
        project_name = 'unknown'
        if current and current.get('ok'):
            project_name = current.get('data', {}).get('name', 'unknown')
        print(f"{project_name}/")

        # 트리 표시 (3단계 깊이까지)
        show_tree(".", "", True, 0, 3)

        # 주요 파일 찾기
        print("\n📌 주요 파일")
        print("-" * 60)

        # 루트 디렉토리의 주요 파일들
        entry_points = ['main.py', 'index.js', 'index.ts', 'app.py', 'server.js']
        config_files = ['package.json', 'requirements.txt', 'pyproject.toml']

        for file in entry_points:
            if os.path.exists(file):
                print(f"  🎯 진입점: {file}")

        for file in config_files:
            if os.path.exists(file):
                print(f"  ⚙️ 설정: {file}")

    except Exception as e:
        print(f"  디렉토리 구조를 읽을 수 없습니다: {e}")
def show_help() -> None:
    """도움말 표시"""
    print("""
🚀 극단순 Flow 명령어 시스템
==========================

기본 명령어:
  h.flow()                    # 현재 상태 표시
  h.flow("/list")            # Plan 목록 보기
  h.flow("/create 계획이름")  # 새 Plan 생성
  h.flow("/select plan_id")  # Plan 선택
  h.flow("/delete plan_id")  # Plan 삭제

Task 명령어:
  h.flow("/task")            # 현재 Plan의 Task 목록
  h.flow("/task add 작업명")  # Task 추가
  h.flow("/task done task_id") # Task 완료 처리
  h.flow("/task progress task_id") # Task 진행중 처리

프로젝트:
  h.flow("/project")         # 현재 프로젝트 확인
  h.flow("/project 이름")    # 프로젝트 전환

기타:
  h.flow("/help")            # 이 도움말 표시
  h.flow("/status")          # 상태 표시

팁:
- Plan을 먼저 선택해야 Task를 추가할 수 있습니다.
- 새 Plan을 생성하면 자동으로 선택됩니다.
""")

# 별칭 함수들
def help_flow() -> None:
    """도움말 표시"""
    show_help()

# __all__ export
__all__ = ['flow', 'help_flow', 'get_manager']


