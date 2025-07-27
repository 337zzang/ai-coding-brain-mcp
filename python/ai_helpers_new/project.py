"""프로젝트 관련 함수들"""
import os
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from .util import ok, err
# from .workflow_manager import get_workflow_manager  # 레거시
try:
    from python.workflow_wrapper import get_workflow_manager
except ImportError:
    # Fallback if direct import fails
    def get_workflow_manager():
        return None

# 프로젝트 정보 캐시
_current_project_cache = None

def get_current_project() -> Dict[str, Any]:
    """현재 프로젝트 정보 가져오기"""
    global _current_project_cache

    if _current_project_cache:
        return _current_project_cache

    # 프로젝트 루트 찾기
    current_dir = os.getcwd()

    # 프로젝트 타입 감지
    project_info = {
        'name': os.path.basename(current_dir),
        'path': current_dir,
        'type': detect_project_type(current_dir),
        'has_git': os.path.exists(os.path.join(current_dir, '.git'))
    }

    _current_project_cache = project_info
    return project_info

def detect_project_type(path: str) -> str:
    """프로젝트 타입 감지"""
    if os.path.exists(os.path.join(path, 'package.json')):
        return 'node'
    elif os.path.exists(os.path.join(path, 'requirements.txt')) or          os.path.exists(os.path.join(path, 'setup.py')) or          os.path.exists(os.path.join(path, 'pyproject.toml')):
        return 'python'
    elif os.path.exists(os.path.join(path, 'Cargo.toml')):
        return 'rust'
    elif os.path.exists(os.path.join(path, 'go.mod')):
        return 'go'
    else:
        return 'unknown'

def scan_directory(path: str = ".", max_depth: Optional[int] = None) -> List[str]:
    """디렉토리 스캔 (파일 리스트 반환)"""
    result = scan_directory_dict(path, max_depth=max_depth or 5)

    # dict 결과를 파일 리스트로 변환
    files = []

    def extract_files(node, prefix=""):
        if node.get('type') == 'file':
            files.append(prefix)
        elif node.get('type') == 'directory':
            for name, child in node.get('children', {}).items():
                extract_files(child, os.path.join(prefix, name))

    if 'structure' in result:
        for name, node in result['structure'].items():
            if node.get('type') == 'file':
                files.append(name)
            else:
                extract_files(node, name)

    return sorted(files)

def scan_directory_dict(path: str = ".", max_depth: int = 5, 
                       ignore_patterns: Optional[List[str]] = None) -> Dict[str, Any]:
    """디렉토리 구조를 딕셔너리로 스캔"""
    if ignore_patterns is None:
        ignore_patterns = [
            '__pycache__', '.git', 'node_modules',
            '.pytest_cache', '.venv', 'venv',
            '*.pyc', '*.pyo', '.DS_Store'
        ]

    def should_ignore(name: str) -> bool:
        for pattern in ignore_patterns:
            if pattern.startswith('*'):
                if name.endswith(pattern[1:]):
                    return True
            elif name == pattern:
                return True
        return False

    def scan_recursive(dir_path: str, current_depth: int = 0) -> Dict[str, Any]:
        if current_depth >= max_depth:
            return {'type': 'directory', 'children': {}}

        result = {'type': 'directory', 'children': {}}

        try:
            for item in os.listdir(dir_path):
                if should_ignore(item):
                    continue

                item_path = os.path.join(dir_path, item)

                if os.path.isfile(item_path):
                    result['children'][item] = {
                        'type': 'file',
                        'size': os.path.getsize(item_path)
                    }
                elif os.path.isdir(item_path):
                    result['children'][item] = scan_recursive(item_path, current_depth + 1)
        except PermissionError:
            pass

        return result

    root_path = os.path.abspath(path)
    structure = scan_recursive(root_path)

    # 통계 계산
    total_files = 0
    total_dirs = 0

    def count_items(node):
        nonlocal total_files, total_dirs
        if node.get('type') == 'file':
            total_files += 1
        elif node.get('type') == 'directory':
            total_dirs += 1
            if 'children' in node:
                for child in node['children'].values():
                    count_items(child)

    count_items(structure)

    return {
        'root': root_path,
        'structure': structure.get('children', {}),
        'stats': {
            'total_files': total_files,
            'total_dirs': total_dirs
        }
    }


def create_project_structure(
    project_name: str,
    project_type: str = 'python',
    base_path: str = "."
) -> Dict[str, Any]:
    """프로젝트 기본 구조 생성"""
    project_path = Path(base_path) / project_name

    # 디렉토리 생성
    project_path.mkdir(parents=True, exist_ok=True)

    # 프로젝트 타입별 구조 생성
    if project_type == 'python':
        # Python 프로젝트 구조
        (project_path / 'src').mkdir(exist_ok=True)
        (project_path / 'tests').mkdir(exist_ok=True)
        (project_path / 'docs').mkdir(exist_ok=True)

        # 기본 파일들
        (project_path / 'README.md').write_text(f"# {project_name}\n\nProject description here.")
        (project_path / 'requirements.txt').write_text("")
        (project_path / '.gitignore').write_text("__pycache__/\n*.pyc\n.venv/\nvenv/\n.env")

    elif project_type == 'node':
        # Node.js 프로젝트 구조
        (project_path / 'src').mkdir(exist_ok=True)
        (project_path / 'tests').mkdir(exist_ok=True)

        # package.json
        package_json = {
            "name": project_name,
            "version": "1.0.0",
            "description": "",
            "main": "index.js",
            "scripts": {
                "test": "echo \"Error: no test specified\" && exit 1"
            }
        }
        write_json(str(project_path / 'package.json'), package_json)

    return {
        'success': True,
        'project_path': str(project_path),
        'created_files': list(project_path.rglob('*'))
    }

# 사용 가능한 함수 목록
__all__ = [
    'get_current_project', 'scan_directory_dict',
    'create_project_structure',
    'flow_project_with_workflow',
]


# Flow Project 함수 (워크플로우 통합)
def flow_project_with_workflow(project_name: str):
    """프로젝트 전환 시 워크플로우도 자동으로 전환 - 바탕화면에서만 검색"""
    result = {"success": False}

    try:
        from pathlib import Path
        
        # 동적으로 바탕화면 경로 찾기
        desktop_candidates = [
            Path.home() / "Desktop",
            Path.home() / "바탕화면",
            Path.home() / "OneDrive" / "Desktop",
            Path.home() / "OneDrive" / "바탕 화면"
        ]
        
        # 실제 존재하는 바탕화면 경로 찾기
        desktop_path = None
        for candidate in desktop_candidates:
            if candidate.exists() and candidate.is_dir():
                desktop_path = candidate
                break
        
        if not desktop_path:
            result = {
                "success": False,
                "error": "바탕화면 경로를 찾을 수 없습니다"
            }
            print("❌ 바탕화면 경로를 찾을 수 없습니다")
            return result
        
        # 바탕화면에서만 프로젝트 찾기
        project_path = desktop_path / project_name


        if project_path.exists() and project_path.is_dir():
            # 현재 디렉토리 저장
            previous_dir = os.getcwd()
            
            # 프로젝트로 이동
            os.chdir(str(project_path))
            
            # 프로젝트 정보 수집
            import json
            from datetime import datetime
            
            project_info = {
                "name": project_name,
                "path": str(project_path),
                "type": "node" if (project_path / "package.json").exists() else "python",
                "has_git": (project_path / ".git").exists(),
                "switched_at": datetime.now().isoformat()
            }
            
            # 캐시 업데이트 (프로젝트 정보 저장)
            cache_dir = Path.home() / ".ai-coding-brain" / "cache"
            cache_dir.mkdir(parents=True, exist_ok=True)
            cache_file = cache_dir / "current_project.json"
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(project_info, f, ensure_ascii=False, indent=2)
            

            # 글로벌 컨텍스트 저장
            # 글로벌 컨텍스트 저장 (미구현 - TODO: 향후 구현)
            pass

                # 컨텍스트 데이터 준비
            # context_data = {
            # 'project_name': project_name,
            # 'project_info': project_info,
            # 'recent_work': f"프로젝트 전환: {project_name}"
            # }

                # 글로벌 컨텍스트에 저장
            # global_ctx.save_project_context(project_name, context_data)

                # AI 컨텍스트 파일 생성
            # ai_context = global_ctx.create_ai_context_file(project_name)

            # print("📋 글로벌 컨텍스트 저장 완료")
            # except Exception as e:
            # print(f"⚠️ 글로벌 컨텍스트 저장 중 오류: {e}")

            result = {
                "success": True,
                "project": project_info,
                "previous": previous_dir
            }
            print(f"✅ 프로젝트 전환: {project_name}")
            print(f"📍 경로: {project_path}")

            # 워크플로우 전환 시도 (에러 무시)
            try:
                from ..workflow_wrapper import wf
                wf(f"/start {project_name}")
                print(f"✅ 워크플로우도 {project_name}로 전환됨")
            except:
                pass  # 워크플로우 실패해도 프로젝트 전환은 성공

        else:
            result = {
                "success": False,
                "error": f"바탕화면에서 프로젝트를 찾을 수 없음: {project_name}"
            }
            print(f"❌ 바탕화면에서 프로젝트를 찾을 수 없음: {project_name}")
            print(f"   검색 경로: {desktop_path}")

    except Exception as e:
        result = {
            "success": False,
            "error": str(e)
        }
        print(f"❌ 프로젝트 전환 실패: {e}")

    return result

# 별칭
fp = flow_project_with_workflow
flow_project = flow_project_with_workflow
