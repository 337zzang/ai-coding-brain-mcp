import os
"""
극단순화된 Workflow 명령어 시스템
Flow 개념 없이 Plan과 Task만으로 작업 관리
"""
from typing import Optional, List, Dict, Any
from .ultra_simple_flow_manager import UltraSimpleFlowManager
from .project import get_current_project
from .project import flow_project_with_workflow

# 전역 매니저 인스턴스
_manager: Optional[UltraSimpleFlowManager] = None
_current_plan_id: Optional[str] = None
_current_project_path: Optional[str] = None

def get_manager() -> UltraSimpleFlowManager:
    """현재 프로젝트의 매니저 가져오기 (작업 디렉토리 기반)"""
    global _manager

    # 현재 작업 디렉토리를 프로젝트 경로로 사용
    project_path = os.getcwd()

    # 프로젝트가 변경되었는지 확인
    if not hasattr(get_manager, '_current_project_path'):
        get_manager._current_project_path = None

    # 매니저가 없거나 프로젝트가 변경된 경우 재생성
    if _manager is None or get_manager._current_project_path != project_path:
        _manager = UltraSimpleFlowManager(project_path=project_path, use_enhanced=True)
        get_manager._current_project_path = project_path

        # 프로젝트별 .ai-brain 디렉토리 생성 알림
        project_name = os.path.basename(project_path)
        ai_brain_path = os.path.join(project_path, '.ai-brain', 'flow')
        if not os.path.exists(ai_brain_path):
            print(f"📁 새로운 Flow 저장소 생성: {project_name}/.ai-brain/flow/")
        else:
            print(f"📁 Flow 저장소 사용: {project_name}/.ai-brain/flow/")

    return _manager


def flow(command: str = "") -> None:
    """
    극단순 Flow 명령어 처리

    사용법:
        flow()                    # 현재 상태 표시
        flow("/list")            # Plan 목록
        flow("/create 계획이름")  # 새 Plan 생성
        flow("/select plan_id")  # Plan 선택
        flow("/task add 작업명")  # Task 추가
        flow("/task done task_id") # Task 완료
        flow("/delete plan_id")  # Plan 삭제
        flow("/project 프로젝트명") # 프로젝트 전환
        flow("/help")            # 도움말
    """
    manager = get_manager()
    parts = command.strip().split(maxsplit=2)

    if not parts or not command:
        # 현재 상태 표시
        show_status(manager)
        return

    cmd = parts[0].lower()

    # 명령어 매핑
    commands = {
        "/list": lambda: show_plans(manager),
        "/create": lambda: create_plan(manager, " ".join(parts[1:]) if len(parts) > 1 else None),
        "/select": lambda: select_plan(parts[1] if len(parts) > 1 else None),
        "/task": lambda: handle_task_command(manager, parts[1:] if len(parts) > 1 else []),
        "/delete": lambda: delete_plan(manager, parts[1] if len(parts) > 1 else None),
        "/project": lambda: switch_project(parts[1] if len(parts) > 1 else None),
        "/help": lambda: show_help(),
        "/status": lambda: show_status(manager),
    }

    if cmd in commands:
        commands[cmd]()
    else:
        print(f"❌ 알 수 없는 명령어: {cmd}")
        show_help()

def show_status(manager: UltraSimpleFlowManager) -> None:
    """현재 상태 표시"""
    global _current_plan_id

    print("\n📊 Flow 시스템 상태")
    print("=" * 50)
    print(f"프로젝트: {manager.project_name}")

    plans = manager.list_plans()
    print(f"\nPlan 개수: {len(plans)}개")

    if _current_plan_id:
        plan = manager.get_plan(_current_plan_id)
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

def create_plan(manager: UltraSimpleFlowManager, name: Optional[str]) -> None:
    """새 Plan 생성"""
    if not name:
        print("❌ Plan 이름을 입력하세요: /create [이름]")
        return

    plan = manager.create_plan(name)
    print(f"✅ Plan 생성 완료: {plan.name} ({plan.id})")

    # 자동으로 선택
    global _current_plan_id
    _current_plan_id = plan.id
    print(f"✅ 자동으로 선택됨")

def select_plan(plan_id: Optional[str]) -> None:
    """Plan 선택 - 순번, 부분 매칭, 인덱스 모두 지원"""
    global _current_plan_id

    if not plan_id:
        print("❌ Plan ID를 입력하세요: /select [plan_id]")
        return

    manager = get_manager()

    # 1. 정확한 매칭 시도 (기존 로직)
    plan = manager.get_plan(plan_id)
    if plan:
        _current_plan_id = plan_id
        print(f"✅ Plan 선택됨: {plan.name}")
        return

    # 2. 순번 매칭 (o3 권장 방식)
    if plan_id.isdigit() and len(plan_id) <= 3:
        seq = plan_id.zfill(3)  # 10 → 010
        matches = []

        for plan in manager.list_plans():
            parts = plan.id.split('_')
            if len(parts) >= 3 and parts[2] == seq:
                matches.append(plan)

        if len(matches) == 1:
            _current_plan_id = matches[0].id
            print(f"✅ Plan 선택됨: {matches[0].name}")
            print(f"   (순번 매칭: {plan_id} → {matches[0].id})")
            return
        elif len(matches) > 1:
            # 가장 최근 것 선택 (날짜 역순)
            matches.sort(key=lambda p: p.created_at, reverse=True)
            _current_plan_id = matches[0].id
            print(f"✅ Plan 선택됨: {matches[0].name}")
            print(f"   (순번 {plan_id} 중복 → 가장 최근 선택)")
            if len(matches) > 1:
                print(f"   💡 동일 순번 {len(matches)}개 존재")
            return

    # 3. 부분 매칭 시도
    all_plans = manager.list_plans()
    matches = [p for p in all_plans if plan_id in p.id or plan_id in p.name]

    if len(matches) == 0:
        print(f"❌ Plan을 찾을 수 없습니다: {plan_id}")

        # 유사한 순번 제안
        if plan_id.isdigit():
            similar_seq = []
            target = int(plan_id)
            for p in all_plans:
                parts = p.id.split('_')
                if len(parts) >= 3 and parts[2].isdigit():
                    seq_num = int(parts[2])
                    if abs(seq_num - target) <= 2:  # ±2 범위
                        similar_seq.append((seq_num, p))

            if similar_seq:
                print("\n💡 유사한 순번:")
                for seq, p in sorted(similar_seq, key=lambda x: x[0])[:3]:
                    print(f"  - {seq:03d}: {p.name}")

    elif len(matches) == 1:
        _current_plan_id = matches[0].id
        print(f"✅ Plan 선택됨: {matches[0].name}")
        print(f"   (부분 매칭: {plan_id} → {matches[0].id})")
    else:
        print(f"🔍 여러 Plan이 '{plan_id}'와 일치합니다:")
        for i, p in enumerate(matches[:5], 1):
            parts = p.id.split('_')
            seq = parts[2] if len(parts) >= 3 else "???"
            print(f"  [{seq}] {p.id}")
            print(f"       이름: {p.name}")
        print("\n순번이나 전체 ID를 입력하여 선택하세요.")

def handle_task_command(manager: UltraSimpleFlowManager, args: List[str]) -> None:
    """Task 관련 명령어 처리"""
    global _current_plan_id

    if not _current_plan_id:
        print("❌ 먼저 Plan을 선택하세요: /select [plan_id]")
        return

    if not args:
        # 현재 Plan의 Task 목록 표시
        show_tasks(manager, _current_plan_id)
        return

    subcmd = args[0].lower()

    if subcmd == "add" and len(args) > 1:
        # Task 추가
        title = " ".join(args[1:])
        task = manager.create_task(_current_plan_id, title)
        print(f"✅ Task 추가됨: {task.title} ({task.id})")

    elif subcmd == "done" and len(args) > 1:
        # Task 완료
        task_id = args[1]
        result = manager.update_task_status(_current_plan_id, task_id, "done")
        if result:
            print(f"✅ Task 완료 처리됨: {task_id}")
        else:
            print(f"❌ Task 업데이트 실패: {task_id}")

    elif subcmd == "progress" and len(args) > 1:
        # Task 진행중
        task_id = args[1]
        result = manager.update_task_status(_current_plan_id, task_id, "in_progress")
        if result:
            print(f"✅ Task 진행중 처리됨: {task_id}")
        else:
            print(f"❌ Task 업데이트 실패: {task_id}")

    else:
        print("❌ 올바른 Task 명령어:")
        print("  /task add [제목] - Task 추가")
        print("  /task done [task_id] - Task 완료")
        print("  /task progress [task_id] - Task 진행중")

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

def delete_plan(manager: UltraSimpleFlowManager, plan_id: Optional[str]) -> None:
    """Plan 삭제"""
    global _current_plan_id

    if not plan_id:
        print("❌ Plan ID를 입력하세요: /delete [plan_id]")
        return

    plan = manager.get_plan(plan_id)
    if not plan:
        print(f"❌ Plan을 찾을 수 없습니다: {plan_id}")
        return

    # 확인
    print(f"⚠️  '{plan.name}' Plan을 삭제하시겠습니까?")
    print(f"   Task {len(plan.tasks)}개도 함께 삭제됩니다.")
    response = input("   삭제하려면 'yes'를 입력하세요: ")

    if response.lower() == 'yes':
        result = manager.delete_plan(plan_id)
        if result:
            print(f"✅ Plan 삭제 완료: {plan.name}")
            if _current_plan_id == plan_id:
                _current_plan_id = None
        else:
            print(f"❌ Plan 삭제 실패")

def switch_project(project_name: Optional[str]) -> None:
    """프로젝트 전환 - flow_project_with_workflow 사용"""
    global _manager, _current_plan_id

    if not project_name:
        # 현재 프로젝트 표시
        current = get_current_project()
        current = get_current_project()
        if current:  # dict가 반환되므로 단순 존재 여부만 체크
            print(f"\n현재 프로젝트: {current.get('name', 'Unknown')}")
            print(f"경로: {current.get('path', get_current_project().get('path', '.'))}")
        else:
            print(f"\n현재 프로젝트 확인 실패")
        return

    # 안전한 프로젝트 전환
    try:
        # flow_project_with_workflow 사용 - dict 반환
        result = flow_project_with_workflow(project_name)

        # 전환 성공 확인
        if isinstance(result, dict) and result.get('success'):
            # Flow 매니저 재초기화
            _manager = None
            _current_plan_id = None

            project_info = result.get('project', {})
            print(f"✅ 프로젝트 전환 완료: {project_name}")
            print(f"   경로: {project_info.get('path', '')}")

            # ========== 개선된 부분 ==========
            # 프로젝트 문서 요약 표시
            _show_project_summary()

            # Flow Plan 목록 표시
            print("")  # 빈 줄
            manager = get_manager()
            show_plans(manager)
            # ========== 개선 끝 ==========
        else:
            print(f"❌ 프로젝트 전환 실패: {project_name}")
            if isinstance(result, dict):
                print(f"   오류: {result.get('error', 'Unknown error')}")

    except Exception as e:
        print(f"❌ 프로젝트 전환 중 오류: {e}")



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
        project_name = os.path.basename(get_current_project().get('path', '.'))
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
  flow()                    # 현재 상태 표시
  flow("/list")            # Plan 목록 보기
  flow("/create 계획이름")  # 새 Plan 생성
  flow("/select plan_id")  # Plan 선택
  flow("/delete plan_id")  # Plan 삭제

Task 명령어:
  flow("/task")            # 현재 Plan의 Task 목록
  flow("/task add 작업명")  # Task 추가
  flow("/task done task_id") # Task 완료 처리
  flow("/task progress task_id") # Task 진행중 처리

프로젝트:
  flow("/project")         # 현재 프로젝트 확인
  flow("/project 이름")    # 프로젝트 전환

기타:
  flow("/help")            # 이 도움말 표시
  flow("/status")          # 상태 표시

팁:
- Plan을 먼저 선택해야 Task를 추가할 수 있습니다.
- 새 Plan을 생성하면 자동으로 선택됩니다.
""")

# 별칭 함수들
def wf(command: str = "") -> None:
    """flow()의 짧은 별칭"""
    flow(command)

def help_flow() -> None:
    """도움말 표시"""
    show_help()

# __all__ export
__all__ = ['flow', 'wf', 'help_flow', 'get_manager']
