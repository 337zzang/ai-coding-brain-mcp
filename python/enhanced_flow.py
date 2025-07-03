from workflow_manager import WorkflowManager
"""
Enhanced Flow - 통합 버전
기존 시스템과 호환되도록 수정된 v2
"""
import os
import sys
import json
import logging
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 전역 변수
context = {}
last_loaded_context = None

def cmd_flow_with_context(project_name: str) -> Dict[str, Any]:
    """프로젝트로 전환하고 전체 컨텍스트를 로드
    
    기존 인터페이스 유지하면서 개선된 구조 적용
    """
    global context, last_loaded_context
    
    try:
        # 0. 안전 점검 수행
        print("=" * 60)
        print(f"🚀 프로젝트 전환: {project_name}")
        print("=" * 60)
        
        safety_check = _safe_project_check(project_name)
        
        # 오류가 있으면 중단
        if safety_check.get("errors"):
            print("\n❌ 안전 점검 실패:")
            for error in safety_check["errors"]:
                print(f"   - {error}")
            return {
                "success": False,
                "error": "안전 점검 실패",
                "details": safety_check
            }
        
        # 경고 표시
        if safety_check.get("warnings"):
            print("\n⚠️  경고 사항:")
            for warning in safety_check["warnings"]:
                print(f"   - {warning}")
            
            # Git 수정사항이 있으면 확인
            git_info = safety_check["checks"].get("git", {})
            if git_info.get("ok") and git_info.get("modified"):
                print("\n💡 수정된 파일을 백업하시겠습니까? (권장)")
                print("   나중에 'git stash' 또는 'git commit'으로 백업 가능합니다.")
        
        print("\n✅ 안전 점검 완료! 프로젝트 전환을 계속합니다...\n")
        

        # 1. 프로젝트 경로 확인/생성
        project_path = _get_project_path(project_name)
        
        # 2. 이전 컨텍스트 백업
        if context and context.get('project_name') != project_name:
            _backup_context()
        
        # 3. 디렉토리 전환
        os.chdir(project_path)
        logger.info(f"✅ 작업 디렉토리 변경: {project_path}")
        
        # 4. sys.path 업데이트
        if str(project_path) not in sys.path:
            sys.path.insert(0, str(project_path))
        
        # 5. 컨텍스트 로드
        context = _load_context(project_name)
        context['project_name'] = project_name
        context['project_path'] = str(project_path)
        context['last_updated'] = datetime.now().isoformat()
        
        # 6. 컨텍스트 저장
        _save_context(context)
        
        # 7. 워크플로우 로드 및 표시
        workflow_status = _load_and_show_workflow()
        
        # 8. 프로젝트 구조 업데이트
        _update_file_directory()
        
        # 9. 결과 출력
        _print_project_briefing(project_name, workflow_status)
        
        last_loaded_context = project_name
        
        return {
            'success': True,
            'project_name': project_name,
            'context': context,
            'workflow_status': workflow_status
        }
        
    except Exception as e:
        logger.error(f"프로젝트 전환 실패: {e}")
        return {
            'success': False,
            'error': str(e)
        }



# ==================== 안전 점검 함수들 ====================

def _safe_git_status(repo_path: str = ".") -> Dict[str, Any]:
    """Git 상태를 안전하게 확인하는 함수"""
    try:
        from git import Repo, InvalidGitRepositoryError
        repo = Repo(repo_path, search_parent_directories=True)
        branch = repo.active_branch.name
        modified = [item.a_path for item in repo.index.diff(None)]
        untracked = repo.untracked_files
        return {
            "ok": True,
            "branch": branch,
            "modified": modified,
            "untracked": untracked
        }
    except Exception as e:
        # GitPython 실패 → CLI fallback
        try:
            out = subprocess.check_output(
                ["git", "-C", repo_path, "status", "-sb"],
                text=True, 
                stderr=subprocess.STDOUT
            )
            return {"ok": True, "raw": out}
        except Exception as cli_e:
            return {"ok": False, "error": f"{type(cli_e).__name__}: {cli_e}"}


def _safe_load_json(path: Path) -> Dict[str, Any]:
    """JSON 파일을 안전하게 로드하는 함수"""
    try:
        # helpers.read_file 존재 확인
        if 'helpers' in globals():
            helpers = globals()['helpers']
            if hasattr(helpers, 'read_file'):
                data = helpers.read_file(str(path))
                if isinstance(data, str):
                    data = json.loads(data)
                elif isinstance(data, bytes):
                    data = json.loads(data.decode())
                elif isinstance(data, dict):
                    pass  # 이미 파싱되어 있음
                else:
                    raise TypeError("Unknown data type from read_file")
                return {"ok": True, "data": data}
        
        # 표준 open 사용
        with open(path, encoding="utf-8") as f:
            return {"ok": True, "data": json.load(f)}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _print_directory_tree(path: Path, depth: int = 1, max_depth: int = 2):
    """디렉터리 트리를 출력하는 함수"""
    if depth > max_depth:
        return
    
    try:
        items = list(path.iterdir())
        # 파일과 디렉터리 분리
        dirs = [p for p in items if p.is_dir() and not p.name.startswith('.')]
        files = [p for p in items if p.is_file() and not p.name.startswith('.')]
        
        # 정렬
        dirs.sort()
        files.sort()
        
        # 출력 (최대 10개씩)
        for p in (dirs[:5] + files[:5]):
            indent = "│   " * (depth - 1)
            prefix = "└── " if p.is_file() else "📂 "
            print(f"{indent}{prefix}{p.name}")
            
            if p.is_dir() and depth < max_depth:
                _print_directory_tree(p, depth + 1, max_depth)
                
        if len(dirs) > 5 or len(files) > 5:
            indent = "│   " * (depth - 1)
            print(f"{indent}... ({len(dirs)} 디렉터리, {len(files)} 파일)")
            
    except PermissionError:
        pass


def _safe_project_check(project_name: str) -> Dict[str, Any]:
    """프로젝트 상태를 안전하게 점검하는 함수"""
    result = {
        "project_name": project_name,
        "checks": {},
        "warnings": [],
        "errors": []
    }
    
    # 1. 현재 작업 디렉터리 확인
    cwd = Path.cwd()
    result["checks"]["cwd"] = {
        "path": str(cwd),
        "exists": cwd.exists(),
        "is_dir": cwd.is_dir()
    }
    
    print(f"🔍 현재 작업 디렉터리: {cwd}")
    
    # 2. 프로젝트 구조 간단히 확인
    print("\n📂 프로젝트 구조 (최상위 2레벨):")
    _print_directory_tree(cwd, 1, 2)
    
    # 3. Git 상태 점검
    print("\n🔍 Git 상태 점검 중...")
    git_info = _safe_git_status()
    result["checks"]["git"] = git_info
    
    if git_info.get("ok"):
        if "branch" in git_info:
            print(f"✅ Git 브랜치: {git_info['branch']}")
            print(f"   수정된 파일: {len(git_info.get('modified', []))}")
            print(f"   추적되지 않은 파일: {len(git_info.get('untracked', []))}")
            
            # 수정된 파일이 있으면 경고
            if git_info.get('modified'):
                result["warnings"].append("수정된 파일이 있습니다. 백업을 권장합니다.")
                print("\n⚠️  수정된 파일 목록:")
                for f in git_info['modified'][:5]:
                    print(f"   - {f}")
                if len(git_info['modified']) > 5:
                    print(f"   ... 외 {len(git_info['modified']) - 5}개")
        else:
            print("✅ Git 상태 확인 (raw output)")
    else:
        result["errors"].append(f"Git 상태 확인 실패: {git_info.get('error')}")
        print(f"❌ Git 상태 확인 실패: {git_info.get('error')}")
    
    # 4. workflow.json 점검
    print("\n🔍 워크플로우 상태 점검 중...")
    wf_path = Path("memory/workflow.json")
    
    if wf_path.exists():
        wf_data = _safe_load_json(wf_path)
        result["checks"]["workflow"] = wf_data
        
        if wf_data.get("ok"):
            data = wf_data["data"]
            plan_id = data.get("current_plan_id")
            plans = {p["id"]: p for p in data.get("plans", [])}
            current = plans.get(plan_id)
            
            if current:
                tasks = current.get("tasks", [])
                done = sum(1 for t in tasks if t.get("status") == "completed")
                print(f"✅ 활성 플랜: {current['name']} ({done}/{len(tasks)} 완료)")
            else:
                print("⚠️  활성 플랜이 없습니다.")
        else:
            result["warnings"].append(f"workflow.json 로드 실패: {wf_data.get('error')}")
            print(f"⚠️  workflow.json 로드 실패: {wf_data.get('error')}")
    else:
        print("⚠️  workflow.json 파일이 없습니다.")
        result["warnings"].append("workflow.json 파일이 없습니다.")
    
    # 5. helpers 모듈 상태 확인
    print("\n🔍 helpers 모듈 상태 확인 중...")
    helpers_ok = False
    
    try:
        if 'helpers' in globals():
            helpers = globals()['helpers']
            # 주요 메서드 확인
            required_methods = ['read_file', 'create_file', 'git_status']
            missing = [m for m in required_methods if not hasattr(helpers, m)]
            
            if not missing:
                print("✅ helpers 모듈 정상")
                helpers_ok = True
            else:
                result["warnings"].append(f"helpers 메서드 누락: {missing}")
                print(f"⚠️  helpers 메서드 누락: {missing}")
        else:
            result["warnings"].append("helpers 모듈을 찾을 수 없습니다.")
            print("⚠️  helpers 모듈을 찾을 수 없습니다.")
    except Exception as e:
        result["errors"].append(f"helpers 확인 중 오류: {e}")
        print(f"❌ helpers 확인 중 오류: {e}")
    
    result["checks"]["helpers_ok"] = helpers_ok
    
    return result

# ===========================================================

def _get_project_path(project_name: str) -> Path:
    """프로젝트 경로 가져오기 - OS 독립적 Desktop 경로 사용
    
    우선순위:
    1. FLOW_PROJECT_ROOT 환경변수
    2. AI_PROJECTS_DIR 환경변수  
    3. 사용자 Desktop 폴더 (OS 독립적)
    """
    # 환경변수 확인
    base_path = os.environ.get('FLOW_PROJECT_ROOT')
    if not base_path:
        base_path = os.environ.get('AI_PROJECTS_DIR')
    
    # 환경변수가 없으면 Desktop 사용
    if not base_path:
        # OS 독립적인 Desktop 경로 찾기
        desktop_path = Path.home() / "Desktop"
        
        # Desktop 폴더가 없는 경우 (일부 Linux 환경)
        if not desktop_path.exists():
            # XDG_DESKTOP_DIR 환경변수 확인 (Linux)
            xdg_desktop = os.environ.get('XDG_DESKTOP_DIR')
            if xdg_desktop and Path(xdg_desktop).exists():
                desktop_path = Path(xdg_desktop)
            else:
                # 대체 경로들 시도
                alt_paths = [
                    Path.home() / "바탕화면",  # 한글 Windows
                    Path.home() / "桌面",      # 중국어
                    Path.home() / "デスクトップ"  # 일본어
                ]
                for alt in alt_paths:
                    if alt.exists():
                        desktop_path = alt
                        break
                else:
                    # 모두 실패하면 홈 디렉토리 사용
                    desktop_path = Path.home() / "Projects"
                    desktop_path.mkdir(exist_ok=True)
        
        base_path = str(desktop_path)
    
    project_path = Path(base_path) / project_name
    
    # 프로젝트 디렉토리가 없으면 생성
    is_new_project = not project_path.exists()
    if is_new_project:
        project_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"✅ 새 프로젝트 '{project_name}' 생성: {project_path}")
    else:
        logger.info(f"📂 기존 프로젝트 '{project_name}' 로드: {project_path}")
    
    # 필수 서브디렉토리 확인 및 생성 (기존 프로젝트에서도 체크)
    essential_dirs = ['memory', 'test', 'docs']
    created_dirs = []
    
    for subdir in essential_dirs:
        subdir_path = project_path / subdir
        if not subdir_path.exists():
            subdir_path.mkdir(exist_ok=True)
            created_dirs.append(subdir)
    
    if created_dirs:
        logger.info(f"📁 필수 디렉토리 생성: {', '.join(created_dirs)}")
    
    # README.md 확인 및 생성 (기존 프로젝트에서도 체크)
    readme_path = project_path / "README.md"
    if not readme_path.exists():
        readme_content = f"""# {project_name}

프로젝트 생성일: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 설명
{project_name} 프로젝트입니다.

## 구조
- `memory/` - 프로젝트 메모리 및 컨텍스트
- `test/` - 테스트 파일
- `docs/` - 문서
"""
        readme_path.write_text(readme_content, encoding='utf-8')
        logger.info(f"📄 README.md 생성됨")
    
    return project_path
def _backup_context():
    """현재 컨텍스트 백업"""
    if not context:
        return
        
    project_name = context.get('project_name', 'unknown')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = f"memory/context_backup_{project_name}_{timestamp}.json"
    
    try:
        os.makedirs('memory', exist_ok=True)
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(context, f, indent=2, ensure_ascii=False)
        logger.info(f"💾 이전 프로젝트 컨텍스트 백업: {backup_file}")
    except Exception as e:
        logger.warning(f"컨텍스트 백업 실패: {e}")

def _load_context(project_name: str) -> Dict[str, Any]:
    """컨텍스트 로드"""
    context_file = Path('memory') / 'context.json'
    
    if context_file.exists():
        try:
            with open(context_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"컨텍스트 로드 실패: {e}")
    
    # 기본 컨텍스트
    return {
        'project_name': project_name,
        'created_at': datetime.now().isoformat(),
        'description': f'{project_name} 프로젝트',
        'version': '1.0.0'
    }

def _save_context(ctx: Dict[str, Any]):
    """컨텍스트 저장"""
    context_file = Path('memory') / 'context.json'
    
    try:
        os.makedirs('memory', exist_ok=True)
        with open(context_file, 'w', encoding='utf-8') as f:
            json.dump(ctx, f, indent=2, ensure_ascii=False)
        logger.info("✅ 컨텍스트 저장 완료")
    except Exception as e:
        logger.error(f"컨텍스트 저장 실패: {e}")

def _load_and_show_workflow() -> Dict[str, Any]:
    """워크플로우 로드 및 상태 반환"""
    workflow_file = Path('memory') / 'workflow.json'
    
    if not workflow_file.exists():
        return {'status': 'no_workflow', 'message': '워크플로우 없음'}
    
    try:
        with open(workflow_file, 'r', encoding='utf-8') as f:
            workflow_data = json.load(f)
        
        # 현재 계획 찾기
        current_plan_id = workflow_data.get('current_plan_id')
        if not current_plan_id:
            return {'status': 'no_plan', 'message': '활성 계획 없음'}
        
        current_plan = None
        for plan in workflow_data.get('plans', []):
            if plan.get('id') == current_plan_id:
                current_plan = plan
                break
        
        if not current_plan:
            return {'status': 'no_plan', 'message': '계획을 찾을 수 없음'}
        
        # 상태 계산
        tasks = current_plan.get('tasks', [])
        completed = sum(1 for t in tasks if t.get('status') == 'completed')
        
        # 현재 작업 찾기
        current_task = None
        for task in tasks:
            if task.get('status') in ['pending', 'in_progress']:
                current_task = task
                break
        
        return {
            'status': 'active',
            'plan_name': current_plan.get('name'),
            'description': current_plan.get('description'),
            'total_tasks': len(tasks),
            'completed_tasks': completed,
            'progress_percent': (completed / len(tasks) * 100) if tasks else 0,
            'current_task': current_task
        }
        
    except Exception as e:
        logger.error(f"워크플로우 로드 실패: {e}")
        return {'status': 'error', 'message': str(e)}

def _update_file_directory():
    """파일 디렉토리 업데이트"""
    try:
        from helpers import scan_directory_dict, create_file
        
        # 디렉토리 스캔
        file_data = scan_directory_dict('.')
        
        # file_directory.md 생성
        content = f"# File Directory\n\n"
        content += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        # 파일 목록
        content += "## Files\n"
        for file in sorted(file_data.get('files', [])):
            content += f"- {file}\n"
        
        # 디렉토리 목록
        content += "\n## Directories\n"
        for dir in sorted(file_data.get('directories', [])):
            content += f"- {dir}/\n"
        
        create_file('file_directory.md', content)
        logger.info("✅ file_directory.md 업데이트 완료")
        
    except Exception as e:
        logger.warning(f"파일 디렉토리 업데이트 실패: {e}")

def _print_project_briefing(project_name: str, workflow_status: Dict[str, Any]):
    """프로젝트 브리핑 출력"""
    print("\n" + "=" * 50)
    print(f"🚀 프로젝트 전환: {project_name}")
    print("=" * 50)
    print(f"✅ 작업 디렉토리: {os.getcwd()}")
    
    # Git 상태 확인
    try:
        # global_helpers 사용 (enhanced_flow.py의 전역 변수)
        if 'global_helpers' in globals():
            git_result = global_helpers.git_status()
            if git_result.ok:
                git_data = git_result.data
                modified_count = len(git_data.get('modified', []))
                print(f"\n🌿 Git 브랜치: {git_data.get('branch', 'N/A')}")
                print(f"📝 변경된 파일: {modified_count}개")
                
                if git_data.get('modified'):
                    print("\n변경된 파일:")
                    for file in git_data['modified'][:5]:  # 최대 5개
                        print(f"  - {file}")
                    if modified_count > 5:
                        print(f"  ... 외 {modified_count - 5}개")
    except Exception as e:
        # Git 상태 실패 시 조용히 넘어감
        pass
    
    # 워크플로우 상태
    print("\n" + "=" * 50)
    if workflow_status.get('status') == 'active':
        print(f"📋 워크플로우: {workflow_status.get('plan_name')}")
        print(f"📊 진행률: {workflow_status.get('completed_tasks')}/{workflow_status.get('total_tasks')} 완료 ({workflow_status.get('progress_percent', 0):.0f}%)")
        
        if workflow_status.get('current_task'):
            task = workflow_status['current_task']
            print(f"▶️  현재 작업: {task.get('title')}")
            print("💡 /next로 다음 작업 진행")
    else:
        print("📋 워크플로우: 활성 계획 없음")
        print("💡 /plan 명령으로 새 계획 생성")
    
    print("=" * 50)
    print("✅ 프로젝트 전환 완료!")
    print("=" * 50)

def show_workflow_status_improved() -> Dict[str, Any]:
    """개선된 워크플로우 상태 표시"""
    workflow_status = _load_and_show_workflow()
    
    print("\n" + "━" * 50)
    if workflow_status.get('status') == 'active':
        print(f"📋 워크플로우: {workflow_status.get('plan_name')}")
        print(f"📊 진행률: {workflow_status.get('completed_tasks')}/{workflow_status.get('total_tasks')} 완료")
        print("━" * 50)
        
        if workflow_status.get('current_task'):
            task = workflow_status['current_task']
            print(f"▶️  현재 작업: {task.get('title')}")
            print(f"   상태: {task.get('status', 'pending')}")
            print(f"   설명: {task.get('description', 'N/A')}")
            print("\n💡 /next 명령으로 다음 작업 진행")
    else:
        print("📋 현재 활성 계획이 없습니다.")
        print("💡 /plan 명령으로 새 계획을 생성하세요.")
    print("━" * 50)
    
    return workflow_status

# 헬퍼 바인딩용 함수
def flow_project(project_name: str):
    """helpers.flow_project() 래퍼"""
    return cmd_flow_with_context(project_name)

# helpers 바인딩 함수
def bind_to_helpers(helpers_obj):
    """helpers 객체에 함수 바인딩"""
    helpers_obj.flow_project = flow_project
    helpers_obj.cmd_flow_with_context = cmd_flow_with_context
    helpers_obj.show_workflow_status = show_workflow_status_improved
    logger.info("Enhanced Flow 함수들이 helpers에 바인딩되었습니다")

# 모듈 로드 시 자동 실행
if __name__ != "__main__":
    # helpers가 있으면 자동 바인딩
    try:
        import sys
        if 'helpers' in sys.modules:
            helpers_module = sys.modules['helpers']
            # AIHelpers 또는 HelpersWrapper 모두 지원
            if hasattr(helpers_module, 'AIHelpers') or hasattr(helpers_module, 'helpers'):
                try:
                    # 전역 helpers 객체가 있는지 확인
                    import builtins
                    if hasattr(builtins, 'helpers'):
                        bind_to_helpers(builtins.helpers)
                        logger.info("helpers 객체에 enhanced_flow 함수 바인딩 완료")
                except Exception as e:
                    logger.warning(f"helpers 바인딩 실패: {e}")
    except:
        pass
