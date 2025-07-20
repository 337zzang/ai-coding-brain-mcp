"""
Flow Project 함수 수정 - 바탕화면 기반 프로젝트 관리 및 워크플로우 연동
Created: 2025-01-19 19:30
Updated: 워크플로우 연동 강화
"""

import os
import json
import shutil
from datetime import datetime
from pathlib import Path

def flow_project_with_workflow(project_name: str, desktop: bool = True) -> dict:
    """프로젝트 전환 및 워크플로우 자동 연동 (바탕화면 기반)"""
    import json
    import os
    import shutil
    from datetime import datetime
    from pathlib import Path

    result = {"success": False}

    try:
        # 바탕화면 또는 projects 디렉토리 경로 결정
        if desktop:
            desktop_paths = [
                Path.home() / "Desktop",
                Path.home() / "바탕화면",
                Path.home() / "OneDrive" / "Desktop",
                Path.home() / "OneDrive" / "바탕 화면"
            ]

            project_path = None
            for desktop_path in desktop_paths:
                if desktop_path.exists():
                    potential_path = desktop_path / project_name
                    if potential_path.exists():
                        project_path = potential_path
                        break

            if not project_path:
                for desktop_path in desktop_paths:
                    if desktop_path.exists():
                        project_path = desktop_path / project_name
                        break
        else:
            projects_dir = Path.home() / "projects"
            projects_dir.mkdir(exist_ok=True)
            project_path = projects_dir / project_name

        if not project_path:
            result["error"] = "적절한 프로젝트 경로를 찾을 수 없습니다"
            return result

        # 현재 워크플로우 백업
        try:
            current_workflow = Path("memory/workflow.json")
            if current_workflow.exists():
                current_memory = Path("memory")
                if current_memory.exists():
                    backup_name = f"workflow_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    backup_path = current_memory / backup_name
                    shutil.copy2(current_workflow, backup_path)
                    print(f"💾 현재 워크플로우 백업: {backup_name}")
        except:
            pass

        # 프로젝트 디렉토리 처리
        is_new = not project_path.exists()
        if is_new:
            print(f"🆕 새 프로젝트 생성: {project_name}")
            project_path.mkdir(parents=True, exist_ok=True)

            # 기본 구조 생성
            for dir_name in ["src", "docs", "tests", "memory", "memory/checkpoints", "memory/backups"]:
                (project_path / dir_name).mkdir(parents=True, exist_ok=True)

            # 초기 워크플로우 생성
            initial_workflow = {
                "project": project_name,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "current_task": None,
                "tasks": [],
                "completed_tasks": [],
                "progress": 0,
                "state": "active",
                "focus": f"Setting up {project_name} project"
            }

            (project_path / "memory" / "workflow.json").write_text(
                json.dumps(initial_workflow, indent=2, ensure_ascii=False),
                encoding='utf-8'
            )
        else:
            print(f"📂 기존 프로젝트로 전환: {project_name}")

        # 작업 디렉토리 변경
        os.chdir(str(project_path))
        print(f"\n📍 작업 디렉토리 변경: {project_path}")

        # 프로젝트 워크플로우 로드 및 활성화
        project_workflow_path = Path("memory/workflow.json")
        if project_workflow_path.exists():
            # 프로젝트 워크플로우 읽기
            with open(project_workflow_path, 'r', encoding='utf-8') as f:
                project_wf = json.load(f)

            # 프로젝트 정보 업데이트
            project_wf['project'] = project_name
            project_wf['project_path'] = str(project_path)
            project_wf['updated_at'] = datetime.now().isoformat()
            project_wf['state'] = 'active'

            # 저장
            with open(project_workflow_path, 'w', encoding='utf-8') as f:
                json.dump(project_wf, f, indent=2, ensure_ascii=False)

            print("✅ 프로젝트 워크플로우 활성화")

        # 프로젝트 정보 캐시
        project_info = {
            "name": project_name,
            "path": str(project_path),
            "type": "node" if (project_path / "package.json").exists() else "python",
            "has_git": (project_path / ".git").exists(),
            "switched_at": datetime.now().isoformat()
        }

        # 캐시 저장
        cache_dir = Path.home() / "AppData/Local/AnthropicClaude/app-0.12.28/memory/.cache"
        cache_dir.mkdir(parents=True, exist_ok=True)

        cache_file = cache_dir / "current_project.json"
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(project_info, f, ensure_ascii=False, indent=2)

        result["success"] = True
        result["project"] = project_info

        print(f"\n✅ 프로젝트 전환 완료: {project_name}")

        # 워크플로우 상태 표시
        if project_workflow_path.exists():
            with open(project_workflow_path, 'r', encoding='utf-8') as f:
                wf_data = json.load(f)

            print(f"\n📋 워크플로우 상태:")
            print(f"  - 프로젝트: {wf_data.get('project', 'N/A')}")
            print(f"  - 작업 수: {len(wf_data.get('tasks', []))}")
            print(f"  - 완료: {len(wf_data.get('completed_tasks', []))}")
            print(f"  - 진행률: {wf_data.get('progress', 0)}%")

            current_task = wf_data.get('current_task')
            if current_task:
                print(f"  - 현재 작업: {current_task}")

        return result

    except Exception as e:
        import traceback
        result["error"] = str(e)
        result["traceback"] = traceback.format_exc()
        print(f"\n❌ flow_project 오류: {e}")
        return result

# 전역 함수로 노출
fp = flow_project_with_workflow

def patch_helpers(helpers):
    """AIHelpersV2 인스턴스에 flow_project 패치"""
    helpers.flow_project = flow_project_with_workflow
    helpers.fp = flow_project_with_workflow
    print("✅ flow_project 패치 적용")
    return helpers
