"""
워크플로우 헬퍼 함수들
프로젝트 문서 자동 생성 및 기타 유틸리티
"""

import os
import json
import textwrap
from pathlib import Path
from datetime import datetime

# AI Helpers v2의 file_ops 사용
import sys
sys.path.append(str(Path(__file__).parent))
from ai_helpers_v2.file_ops import write_file as safe_write, read_file as safe_read

_HEADER = "# 📁 프로젝트 파일·디렉터리 구조\n\n"
_FOOTER = "\n\n*(자동 생성: /a 명령)*"

def _scan_tree(root: Path, exclude_dirs: set = None) -> str:
    """
    root 이하 구조를 들여쓰기 트리로 Markdown 문자열 반환
    """
    if exclude_dirs is None:
        exclude_dirs = {'.git', '__pycache__', 'node_modules', '.venv', 'venv', 'env'}
    
    lines = []
    
    def _walk_directory(path: Path, prefix: str = "", is_last: bool = True):
        """재귀적으로 디렉토리 구조 생성"""
        items = []
        try:
            for item in sorted(path.iterdir()):
                if item.name in exclude_dirs:
                    continue
                if item.name.startswith('.') and item.name not in {'.gitignore', '.env'}:
                    continue
                items.append(item)
        except PermissionError:
            return
        
        for i, item in enumerate(items):
            is_last_item = i == len(items) - 1
            
            # 트리 문자 결정
            if is_last_item:
                connector = "└── "
                extension = "    "
            else:
                connector = "├── "
                extension = "│   "
            
            # 아이템 출력
            if item.is_dir():
                lines.append(f"{prefix}{connector}{item.name}/")
                _walk_directory(item, prefix + extension, is_last_item)
            else:
                lines.append(f"{prefix}{connector}{item.name}")
    
    # 루트부터 시작
    lines.append(f"{root.name}/")
    _walk_directory(root, "")
    
    return "\n".join(lines)

def generate_docs_for_project(root: Path):
    """file_directory.md · README.md 생성 메인 함수."""
    root = Path(root).resolve()
    
    # ─ file_directory.md ─
    print(f"📝 {root} 디렉토리 구조 스캔 중...")
    
    # 생성 시간 추가
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    header_with_time = f"{_HEADER}생성일시: {timestamp}\n\n```\n"
    
    dir_tree = _scan_tree(root)
    dir_md = header_with_time + dir_tree + "\n```" + _FOOTER
    
    file_dir_path = root / "file_directory.md"
    safe_write(str(file_dir_path), dir_md)
    print(f"✅ {file_dir_path} 생성 완료")

    # ─ README.md (없는 경우만) ─
    readme_path = root / "README.md"
    if not readme_path.exists():
        project_name = root.name
        tmpl = textwrap.dedent(f"""
            # {project_name}
            
            이 README는 `/a` 명령으로 자동 생성되었습니다.
            
            ## 프로젝트 구조
            
            프로젝트의 전체 파일 구조는 **[file_directory.md](./file_directory.md)** 를 참조하세요.
            
            ## 시작하기
            
            ```bash
            # 프로젝트 설정
            npm install  # 또는 pip install -r requirements.txt
            ```
            
            ## 주요 디렉토리
            
            - `src/` - 소스 코드
            - `docs/` - 문서
            - `tests/` - 테스트 코드
            - `memory/` - 프로젝트 상태 및 히스토리
            
            ---
            
            생성일시: {timestamp}
        """).strip()
        safe_write(str(readme_path), tmpl)
        print(f"✅ {readme_path} 생성 완료")
    else:
        print(f"ℹ️ {readme_path}는 이미 존재합니다 (건너뜀)")

    # ─ project_context.json 생성 ─
    memory_dir = root / "memory"
    memory_dir.mkdir(exist_ok=True)
    context_path = memory_dir / "project_context.json"

    print(f"📊 프로젝트 분석 중...")

    # 프로젝트 타입 감지
    project_type = "unknown"
    tech_stack = []

    # 파일 확장자 기반 분석
    file_extensions = {}
    source_files = 0
    test_files = 0
    total_files = 0

    for item in root.rglob('*'):
        if item.is_file() and not any(part.startswith('.') for part in item.parts):
            total_files += 1
            ext = item.suffix.lower()
            if ext:
                file_extensions[ext] = file_extensions.get(ext, 0) + 1

            # 소스 파일 카운트
            if ext in ['.py', '.js', '.ts', '.java', '.cpp', '.cs', '.go', '.rs']:
                source_files += 1

            # 테스트 파일 카운트
            if 'test' in item.name.lower() or 'spec' in item.name.lower():
                test_files += 1

    # 주요 파일로 프로젝트 타입 결정
    if (root / "package.json").exists():
        project_type = "javascript"
        tech_stack.append("Node.js")
        if (root / "tsconfig.json").exists():
            project_type = "typescript"
            tech_stack.append("TypeScript")
    elif (root / "requirements.txt").exists() or (root / "setup.py").exists():
        project_type = "python"
        tech_stack.append("Python")
    elif (root / "pom.xml").exists():
        project_type = "java"
        tech_stack.append("Java")
        tech_stack.append("Maven")
    elif (root / "Cargo.toml").exists():
        project_type = "rust"
        tech_stack.append("Rust")

    # 프레임워크 감지
    if (root / "package.json").exists():
        try:
            import json
            with open(root / "package.json", 'r', encoding='utf-8') as f:
                pkg = json.load(f)
                deps = list(pkg.get('dependencies', {}).keys()) + list(pkg.get('devDependencies', {}).keys())
                if 'react' in deps:
                    tech_stack.append("React")
                if 'vue' in deps:
                    tech_stack.append("Vue")
                if 'express' in deps:
                    tech_stack.append("Express")
        except:
            pass

    # 디렉토리 목록
    directories = [d.name for d in root.iterdir() if d.is_dir() and not d.name.startswith('.')]

    # 컨텍스트 데이터 생성
    context_data = {
        "analyzed_at": timestamp,
        "project_type": project_type,
        "tech_stack": tech_stack,
        "structure": {
            "total_files": total_files,
            "source_files": source_files,
            "test_files": test_files,
            "directories": directories[:20]  # 최대 20개
        },
        "file_extensions": dict(sorted(file_extensions.items(), key=lambda x: x[1], reverse=True)[:10])  # 상위 10개
    }

    # JSON 저장
    import json
    with open(context_path, 'w', encoding='utf-8') as f:
        json.dump(context_data, f, indent=2, ensure_ascii=False)

    print(f"✅ {context_path} 생성 완료")
    print(f"  - 프로젝트 타입: {project_type}")
    print(f"  - 기술 스택: {', '.join(tech_stack) if tech_stack else 'N/A'}")
    print(f"  - 파일 수: {total_files}개")

    for item in root.rglob("*"):
        if item.is_file() and not any(skip in str(item) for skip in ['.git', '__pycache__', 'node_modules']):
            total_files += 1
            if 'test' in str(item).lower():
                test_files += 1
            elif item.suffix in ['.py', '.js', '.ts', '.java']:
                source_files += 1
        elif item.is_dir() and item.parent == root:
            directories.append(item.name)

    # 컨텍스트 생성
    context = {
        "analyzed_at": timestamp,
        "project_type": project_type,
        "tech_stack": tech_stack,
        "structure": {
            "total_files": total_files,
            "source_files": source_files,
            "test_files": test_files,
            "directories": sorted(directories)
        },
        "build_tools": []
    }

    # 빌드 도구 감지
    if (root / "package.json").exists():
        context["build_tools"].append("npm")
    if (root / "requirements.txt").exists():
        context["build_tools"].append("pip")
    if (root / "pom.xml").exists():
        context["build_tools"].append("maven")

    # JSON 저장
    import json
    safe_write(str(context_path), json.dumps(context, indent=2, ensure_ascii=False))
    print(f"✅ {context_path} 생성 완료")

def update_file_directory(root: Path = None):
    """file_directory.md만 업데이트 (README는 건드리지 않음)"""
    if root is None:
        root = Path.cwd()
    root = Path(root).resolve()
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    header_with_time = f"{_HEADER}생성일시: {timestamp}\n\n```\n"
    
    dir_tree = _scan_tree(root)
    dir_md = header_with_time + dir_tree + "\n```" + _FOOTER
    
    file_dir_path = root / "file_directory.md"
    safe_write(str(file_dir_path), dir_md)
    
    return f"✅ {file_dir_path} 업데이트 완료"

# 추가 유틸리티 함수들
def parse_file_directory_md(md_content: str) -> dict:
    """
    file_directory.md 내용을 파싱하여 구조화된 딕셔너리로 반환
    """
    lines = md_content.split('\n')
    tree = {"directories": {}, "files": []}
    current_path = []
    
    for line in lines:
        if '```' in line:
            continue
        if not any(marker in line for marker in ['├──', '└──', '│']):
            continue
            
        # 들여쓰기 레벨 계산
        indent_level = 0
        for char in line:
            if char in ['│', ' ', '├', '└', '─']:
                indent_level += 1
            else:
                break
        
        # 실제 레벨은 4로 나눔 (각 레벨은 4칸)
        level = indent_level // 4
        
        # 파일/디렉토리 이름 추출
        name = line.strip()
        for marker in ['├── ', '└── ', '│   ']:
            name = name.replace(marker, '')
        
        if name.endswith('/'):
            # 디렉토리
            dir_name = name.rstrip('/')
            current_path = current_path[:level] + [dir_name]
            path_str = '/'.join(current_path)
            tree["directories"][path_str] = []
        else:
            # 파일
            if level > 0:
                parent_path = '/'.join(current_path[:level])
                if parent_path in tree["directories"]:
                    tree["directories"][parent_path].append(name)
            else:
                tree["files"].append(name)
    
    return tree
