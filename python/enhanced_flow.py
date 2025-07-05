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

# path_utils에서 필요한 함수들 import
from utils.path_utils import write_gitignore, is_git_available


# 로깅 설정 - stderr로 출력하여 JSON 응답 오염 방지
logging.basicConfig(
    level=logging.INFO,
    stream=sys.stderr,
    format='%(message)s'
)
logger = logging.getLogger(__name__)

# MCP JSON 응답 오염 방지를 위해 print를 logger.info로 리디렉션
import builtins
_original_print = builtins.print
def safe_print(*args, **kwargs):
    """print를 logger.info로 리디렉션"""
    message = ' '.join(str(arg) for arg in args)
    logger.info(message)
# 리디렉션 임시 비활성화 - print 출력 문제 해결을 위해
# builtins.print = safe_print

# helpers 자동 주입 - 모듈 로드 시점에 확인
if not hasattr(builtins, 'helpers'):
    try:
        from helpers_wrapper import HelpersWrapper
        from ai_helpers import AIHelpers
        builtins.helpers = HelpersWrapper(AIHelpers())
        logger.info("Enhanced Flow에서 helpers 자동 주입 완료")
    except Exception as e:
        logger.warning(f"helpers 자동 주입 실패: {e}")

# 전역 변수
context = {}
last_loaded_context = None

# ==================== 새 프로젝트 생성 함수 ====================
def _create_new_project(proj_root: Path, *, init_git: bool = True):
    """새 프로젝트 구조 생성"""
    # 필수 디렉토리 생성
    (proj_root / "memory").mkdir(parents=True, exist_ok=True)
    for sub in ("test", "docs", "src"):
        (proj_root / sub).mkdir(exist_ok=True)

    # 기본 파일 생성
    readme_content = f"""# {proj_root.name}

프로젝트 초기화 완료 - {datetime.now().strftime('%Y-%m-%d %H:%M')}

## 프로젝트 구조
```
{proj_root.name}/
├── memory/         # 프로젝트 메모리 (컨텍스트, 워크플로우)
├── src/            # 소스 코드
├── test/           # 테스트 코드
├── docs/           # 문서
└── README.md       # 프로젝트 설명
```

## 시작하기
```bash
# 프로젝트로 이동
flow_project("{proj_root.name}")

# 작업 계획 수립
/plan 초기설정 | 프로젝트 기본 구조 설정
```
"""
    (proj_root / "README.md").write_text(readme_content, encoding="utf-8")

    # 문서 파일
    (proj_root / "docs" / "overview.md").write_text(
        f"# {proj_root.name} 개요\n\n## 프로젝트 설명\n\n*여기에 프로젝트 설명을 작성하세요*",
        encoding="utf-8"
    )

    # 테스트 파일
    (proj_root / "test" / "__init__.py").touch()
    (proj_root / "test" / "test_smoke.py").write_text(
        "\"\"\"기본 smoke 테스트\"\"\"\n\ndef test_smoke():\n    \"\"\"프로젝트가 정상적으로 설정되었는지 확인\"\"\"\n    assert True\n",
        encoding="utf-8"
    )

    # Git 초기화
    if init_git and is_git_available():
        try:
            subprocess.run(["git", "init"], cwd=proj_root, capture_output=True)
            write_gitignore(proj_root)
            subprocess.run(["git", "add", "."], cwd=proj_root, capture_output=True)
            subprocess.run(
                ["git", "commit", "-m", f"feat: {proj_root.name} 프로젝트 초기화"],
                cwd=proj_root,
                capture_output=True
            )
            print(f"[OK] Git 저장소 초기화 완료")
        except Exception as e:
            print(f"[WARN]  Git 초기화 실패 (수동으로 진행 가능): {e}")
    else:
        if not init_git:
            print("[INFO]  Git 초기화 건너뜀 (--no-git 옵션)")
        else:
            print("[WARN]  Git이 설치되지 않음 (나중에 수동으로 초기화 가능)")

    # 초기 컨텍스트 생성
    initial_context = {
        "project_name": proj_root.name,
        "project_path": str(proj_root),
        "created_at": datetime.now().isoformat(),
        "last_updated": datetime.now().isoformat(),
        "type": "new_project",
        "status": "initialized"
    }

    # memory 디렉토리에 저장
    context_path = proj_root / "memory" / "context.json"
    context_path.write_text(
        json.dumps(initial_context, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    print(f"\n[OK] 새 프로젝트 '{proj_root.name}' 생성 완료!")
    print(f"   경로: {proj_root}")
    print(f"   구조: README.md, src/, test/, docs/, memory/")
    if init_git and is_git_available():
        print(f"   Git: 초기 커밋 완료")

def _create_new_project(proj_root: Path, *, init_git: bool = True) -> Dict[str, Any]:
    """새 프로젝트 구조 생성 및 초기화

    Args:
        proj_root: 프로젝트 루트 경로
        init_git: Git 초기화 여부

    Returns:
        생성 결과 정보
    """
    try:
        # 1. 디렉터리 구조 생성
        proj_root.mkdir(parents=True, exist_ok=True)

        # 표준 디렉터리들
        dirs_to_create = ['src', 'test', 'docs', 'memory']
        for dir_name in dirs_to_create:
            (proj_root / dir_name).mkdir(exist_ok=True)

        # 2. 기본 파일들 생성
        # README.md
        readme_content = f"""# {proj_root.name}

## 🚀 프로젝트 개요
{proj_root.name} 프로젝트입니다.

## 📁 디렉터리 구조
```
{proj_root.name}/
├── README.md          # 프로젝트 문서
├── src/              # 소스 코드
├── test/             # 테스트 코드
├── docs/             # 문서
└── memory/           # 프로젝트 메모리/컨텍스트
```

## 🛠️ 시작하기
프로젝트가 초기화되었습니다. 이제 개발을 시작하세요!

생성일: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        (proj_root / "README.md").write_text(readme_content, encoding="utf-8")

        # docs/overview.md
        docs_content = f"""# {proj_root.name} 프로젝트 문서

## 프로젝트 설명
이 문서는 {proj_root.name} 프로젝트의 기술 문서입니다.

## 주요 기능
- [ ] 기능 1
- [ ] 기능 2
- [ ] 기능 3

## 아키텍처
프로젝트 아키텍처 설명을 여기에 작성하세요.
"""
        (proj_root / "docs" / "overview.md").write_text(docs_content, encoding="utf-8")

        # test/__init__.py
        (proj_root / "test" / "__init__.py").touch()

        # test/test_smoke.py - 기본 테스트
        test_content = '''"""Smoke test for project initialization"""

def test_smoke():
    """프로젝트가 정상적으로 초기화되었는지 확인"""
    assert True, "Basic smoke test passed"

def test_project_structure():
    """프로젝트 구조 확인"""
    import os
    assert os.path.exists("README.md")
    assert os.path.exists("src")
    assert os.path.exists("test")
    assert os.path.exists("docs")
'''
        (proj_root / "test" / "test_smoke.py").write_text(test_content, encoding="utf-8")

        # src/__init__.py
        (proj_root / "src" / "__init__.py").touch()

        # 3. Git 초기화
        git_initialized = False
        if init_git and is_git_available():
            try:
                # Git 초기화
                subprocess.run(["git", "init"], cwd=proj_root, check=True, capture_output=True)

                # .gitignore 생성
                write_gitignore(proj_root)

                # 첫 커밋
                subprocess.run(["git", "add", "."], cwd=proj_root, check=True, capture_output=True)
                subprocess.run(
                    ["git", "commit", "-m", "feat: initial project skeleton"],
                    cwd=proj_root,
                    check=True,
                    capture_output=True
                )
                git_initialized = True

            except subprocess.CalledProcessError as e:
                logger.warning(f"Git 초기화 실패: {e}")
                git_initialized = False

        # 4. 결과 반환
        return {
            "success": True,
            "project_name": proj_root.name,
            "path": str(proj_root),
            "git_initialized": git_initialized,
            "created_dirs": dirs_to_create,
            "created_files": ["README.md", "docs/overview.md", "test/__init__.py", "test/test_smoke.py", "src/__init__.py"]
        }

    except Exception as e:
        logger.error(f"프로젝트 생성 실패: {e}")
        return {
            "success": False,
            "error": str(e)
        }

def cmd_flow_with_context(project_name: str) -> Dict[str, Any]:
    """프로젝트로 전환하고 전체 컨텍스트를 로드

    기존 인터페이스 유지하면서 개선된 구조 적용
    """
    global context, last_loaded_context

    try:
        # 0. 안전 점검 수행
        logger.info("=" * 60)
        logger.info(f"[START] 프로젝트 전환: {project_name}")
        logger.info("=" * 60)

        safety_check = _safe_project_check(project_name)
        if safety_check is None:
            raise RuntimeError("_safe_project_check() returned None")

        # 오류가 있으면 중단
        if safety_check.get("errors"):
            print("\n[ERROR] 안전 점검 실패:")
            for error in safety_check["errors"]:
                print(f"   - {error}")
            return {
                "success": False,
                "error": "안전 점검 실패",
                "details": safety_check
            }

        # 경고 표시
        if safety_check.get("warnings"):
            print("\n[WARN]  경고 사항:")
            for warning in safety_check["warnings"]:
                print(f"   - {warning}")

            # Git 수정사항이 있으면 확인
            git_info = safety_check["checks"].get("git", {})
            if git_info.get("ok") and git_info.get("modified"):
                print("\n[TIP] 수정된 파일을 백업하시겠습니까? (권장)")
                print("   나중에 'git stash' 또는 'git commit'으로 백업 가능합니다.")

        print("\n[OK] 안전 점검 완료! 프로젝트 전환을 계속합니다...\n")


        # 1. 프로젝트 경로 확인/생성
        project_path = _get_project_path(project_name)

        # 1-1. 새 프로젝트인 경우 생성
        is_new_project = not project_path.exists()
        if is_new_project:
            logger.info(f"[NEW] 새 프로젝트 생성: {project_name}")

            # Git 초기화 옵션 (환경변수 또는 기본값)
            init_git = os.environ.get('FLOW_INIT_GIT', 'true').lower() != 'false'

            # 프로젝트 생성
            creation_result = _create_new_project(project_path, init_git=init_git)

            if not creation_result.get('success'):
                error_msg = creation_result.get('error', '알 수 없는 오류')
                logger.error(f"프로젝트 생성 실패: {error_msg}")
                return {
                    'status': 'error',
                    'error': f'프로젝트 생성 실패: {error_msg}'
                }

            # 생성 결과 출력
            print(f"\n✅ 새 프로젝트 '{project_name}' 생성 완료!")
            print(f"   📍 경로: {project_path}")
            print(f"   📁 생성된 디렉터리: {', '.join(creation_result['created_dirs'])}")
            print(f"   📄 생성된 파일: {len(creation_result['created_files'])}개")
            if creation_result.get('git_initialized'):
                print(f"   🔀 Git: 초기화 완료 (첫 커밋 생성)")
            print()

        # 2. 이전 컨텍스트와 다른 프로젝트인 경우 로그만 남김
        if context and context.get('project_name') != project_name:
            logger.info(f"프로젝트 전환: {context.get('project_name')} -> {project_name}")
            # context_backup 로직 제거됨 - 더 이상 필요하지 않음

        # 3. 디렉토리 전환
        os.chdir(project_path)
        logger.info(f"[OK] 작업 디렉토리 변경: {project_path}")

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

        # 8. Git 상태 확인 및 context에 추가
        git_info = _safe_git_status(os.getcwd())
        if git_info.get("ok"):
            context['git'] = {
                'branch': git_info.get('branch', 'unknown'),
                'modified': git_info.get('modified', []),
                'untracked': git_info.get('untracked', []),
                'untracked_count': git_info.get('untracked_count', 0)
            }

        # 9. 프로젝트 구조 업데이트
        _update_file_directory()

        # 10. 결과 출력
        if workflow_status is None:
            workflow_status = {}
        _print_project_briefing(project_name, workflow_status, context)

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
        # untracked = repo.untracked_files  # 성능 문제로 주석 처리
        untracked_count = len(repo.untracked_files) if len(repo.untracked_files) < 1000 else "1000+"  # 성능 최적화
        return {
            "ok": True,
            "branch": branch,
            "modified": modified,
            "untracked_count": untracked_count  # 파일 목록 대신 개수만 반환
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
            prefix = "└── " if p.is_file() else "[DIR] "
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

    print(f"[SEARCH] 현재 작업 디렉터리: {cwd}")

    # 2. 프로젝트 구조 간단히 확인
    print("\n[DIR] 프로젝트 구조 (최상위 2레벨):")
    _print_directory_tree(cwd, 1, 2)

    # 3. Git 상태 점검
    print("\n[SEARCH] Git 상태 점검 중...")
    git_info = _safe_git_status()
    result["checks"]["git"] = git_info

    if git_info.get("ok"):
        if "branch" in git_info:
            print(f"[OK] Git 브랜치: {git_info['branch']}")
            print(f"   수정된 파일: {len(git_info.get('modified', []))}")
            print(f"   추적되지 않은 파일: {git_info.get('untracked_count', 0)}")

            # 수정된 파일이 있으면 경고
            if git_info.get('modified'):
                result["warnings"].append("수정된 파일이 있습니다. 백업을 권장합니다.")
                print("\n[WARN]  수정된 파일 목록:")
                for f in git_info['modified'][:5]:
                    print(f"   - {f}")
                if len(git_info['modified']) > 5:
                    print(f"   ... 외 {len(git_info['modified']) - 5}개")
        else:
            print("[OK] Git 상태 확인 (raw output)")
    else:
        result["errors"].append(f"Git 상태 확인 실패: {git_info.get('error')}")
        print(f"[ERROR] Git 상태 확인 실패: {git_info.get('error')}")

    # 4. workflow.json 점검
    print("\n[SEARCH] 워크플로우 상태 점검 중...")
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
                print(f"[OK] 활성 플랜: {current['name']} ({done}/{len(tasks)} 완료)")
            else:
                print("[WARN]  활성 플랜이 없습니다.")
        else:
            result["warnings"].append(f"workflow.json 로드 실패: {wf_data.get('error')}")
            print(f"[WARN]  workflow.json 로드 실패: {wf_data.get('error')}")
    else:
        print("[WARN]  workflow.json 파일이 없습니다.")
        result["warnings"].append("workflow.json 파일이 없습니다.")

    # 5. helpers 모듈 상태 확인
    print("\n[SEARCH] helpers 모듈 상태 확인 중...")
    helpers_ok = False

    try:
        # helpers를 여러 위치에서 확인
        helpers = None
        if hasattr(builtins, 'helpers'):
            helpers = builtins.helpers
        elif 'helpers' in globals():
            helpers = globals()['helpers']
        elif 'helpers' in locals():
            helpers = locals()['helpers']

        if helpers:
            # 주요 메서드 확인
            required_methods = ['read_file', 'create_file', 'git_status']
            missing = [m for m in required_methods if not hasattr(helpers, m)]

            if not missing:
                print("[OK] helpers 모듈 정상")
                helpers_ok = True
            else:
                result["warnings"].append(f"helpers 메서드 누락: {missing}")
                print(f"[WARN]  helpers 메서드 누락: {missing}")
        else:
            result["warnings"].append("helpers 모듈을 찾을 수 없습니다.")
            print("[WARN]  helpers 모듈을 찾을 수 없습니다.")
    except Exception as e:
        result["errors"].append(f"helpers 확인 중 오류: {e}")
        print(f"[ERROR] helpers 확인 중 오류: {e}")

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
        logger.info(f"[OK] 새 프로젝트 '{project_name}' 생성: {project_path}")
        # 새 프로젝트 초기화
        _create_new_project(project_path, init_git=True)
    else:
        logger.info(f"[DIR] 기존 프로젝트 '{project_name}' 로드: {project_path}")

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
        logger.info(f"[FILE] README.md 생성됨")

    return project_path
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
        logger.info("[OK] 컨텍스트 저장 완료")
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
    """파일 디렉토리 업데이트 - helpers 의존성 제거"""
    try:
        import os
        import glob
        from pathlib import Path

        # 현재 디렉토리 정보 수집
        current_dir = Path('.')
        files = []
        directories = []

        # 파일과 디렉토리 수집 (최대 깊이 3)
        for item in current_dir.rglob('*'):
            if len(item.parts) > 4:  # 깊이 제한
                continue
            if item.is_file():
                files.append(str(item))
            elif item.is_dir():
                directories.append(str(item))

        # file_directory.md 생성
        content = f"# File Directory\n\n"
        content += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        # 파일 목록
        content += "## Files\n"
        for file in sorted(files)[:100]:  # 최대 100개 파일
            content += f"- {file}\n"
        if len(files) > 100:
            content += f"... and {len(files) - 100} more files\n"

        # 디렉토리 목록
        content += "\n## Directories\n"
        for dir in sorted(directories)[:50]:  # 최대 50개 디렉토리
            content += f"- {dir}/\n"
        if len(directories) > 50:
            content += f"... and {len(directories) - 50} more directories\n"

        # 파일 쓰기
        with open('file_directory.md', 'w', encoding='utf-8') as f:
            f.write(content)

        logger.info("[OK] file_directory.md 업데이트 완료")

    except Exception as e:
        logger.warning(f"파일 디렉토리 업데이트 실패: {e}")

def _print_project_briefing(project_name: str, workflow_status: Dict[str, Any], context: Dict[str, Any]):
    """프로젝트 브리핑 출력 - 개선된 버전"""
    print("\n" + "=" * 50)
    print(f"[START] 프로젝트 전환: {project_name}")
    print("=" * 50)
    print(f"[OK] 작업 디렉토리: {os.getcwd()}")

    # Git 상태 확인
    try:
        # _safe_git_status 함수 직접 호출
        git_info = _safe_git_status(os.getcwd())
        if git_info.get("ok"):
            # Git 정보를 context에 저장
            context['git'] = {
                'branch': git_info.get('branch', 'unknown'),
                'modified': git_info.get('modified', []),
                'untracked': git_info.get('untracked', []),
                'untracked_count': git_info.get('untracked_count', 0)
            }

            print(f"\n[GIT] Git 브랜치: {git_info.get('branch', 'N/A')}")
            modified_count = len(git_info.get('modified', []))
            print(f"[EDIT] 변경된 파일: {modified_count}개")

            if git_info.get('modified'):
                print("\n변경된 파일:")
                for file in git_info['modified'][:5]:  # 최대 5개
                    print(f"  - {file}")
                if modified_count > 5:
                    print(f"  ... 외 {modified_count - 5}개")
    except Exception as e:
        # Git 상태 실패 시 조용히 넘어감
        pass

    # 워크플로우 상태
    print("\n" + "=" * 50)
    if workflow_status and workflow_status.get('status') == 'active':
        print(f"[LIST] 워크플로우: {workflow_status.get('plan_name') if workflow_status else 'None'}")
        print(f"[STAT] 진행률: {workflow_status.get('completed_tasks') if workflow_status else 0}/{workflow_status.get('total_tasks') if workflow_status else 0} 완료 ({workflow_status.get('progress_percent', 0):.0f}%)")

        if workflow_status and workflow_status.get('current_task'):
            task = workflow_status['current_task']
            print(f"▶️  현재 작업: {task.get('title')}")
            print("[TIP] /next로 다음 작업 진행")
    else:
        print("[LIST] 워크플로우: 활성 계획 없음")
        print("[TIP] /plan 명령으로 새 계획 생성")

    print("=" * 50)
    print("[OK] 프로젝트 전환 완료!")
    print("=" * 50)

def show_workflow_status_improved() -> Dict[str, Any]:
    """개선된 워크플로우 상태 표시"""
    workflow_status = _load_and_show_workflow()

    print("\n" + "━" * 50)
    if workflow_status and workflow_status.get('status') == 'active':
        print(f"[LIST] 워크플로우: {workflow_status.get('plan_name') if workflow_status else 'None'}")
        print(f"[STAT] 진행률: {workflow_status.get('completed_tasks') if workflow_status else 0}/{workflow_status.get('total_tasks') if workflow_status else 0} 완료")
        print("━" * 50)

        if workflow_status and workflow_status.get('current_task'):
            task = workflow_status['current_task']
            print(f"▶️  현재 작업: {task.get('title')}")
            print(f"   상태: {task.get('status', 'pending')}")
            print(f"   설명: {task.get('description', 'N/A')}")
            print("\n[TIP] /next 명령으로 다음 작업 진행")
    else:
        print("[LIST] 현재 활성 계획이 없습니다.")
        print("[TIP] /plan 명령으로 새 계획을 생성하세요.")
    print("━" * 50)

    # workflow_status가 None인 경우 기본값 반환
    return workflow_status or {'status': 'no_workflow', 'message': '워크플로우 없음'}

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
