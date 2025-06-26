"""
file_directory_generator.py
프로젝트 구조와 함수/클래스 정보를 포함한 file_directory.md를 memory 폴더에 생성
"""

import os
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

def create_file_directory_md(helpers=None, context=None) -> tuple[int, str]:
    """프로젝트 구조와 함수/클래스 정보를 포함한 file_directory.md를 memory 폴더에 생성
    
    Returns:
        tuple: (파일 크기, 파일 경로)
    """
    # helpers와 context 가져오기
    if helpers is None:
        helpers = globals().get('helpers')
        if not helpers:
            raise RuntimeError("helpers 객체를 찾을 수 없습니다.")
    
    if context is None:
        context = helpers.get_context()
    
    structure = helpers.get_project_structure()
    if not structure:
        # 구조가 없으면 스캔
        structure = helpers.cache_project_structure()
    
    analyzed_files = context.analyzed_files if hasattr(context, 'analyzed_files') else {}
    
    content = []
    content.append("# 📁 Project Structure - ai-coding-brain-mcp\n")
    content.append(f"*Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")
    
    # 통계 정보
    stats = helpers.get_structure_stats()
    if stats:
        content.append("## 📊 Overview\n")
        content.append(f"- Total Files: {stats.get('total_files', 0)}")
        content.append(f"- Total Directories: {stats.get('total_dirs', 0)}")
        content.append(f"- Analyzed Python Files: {len(analyzed_files)}")
        
        # 파일 타입 분포
        file_types = stats.get('file_types', {})
        if file_types:
            content.append("\n### File Types Distribution:")
            for ext, count in sorted(file_types.items(), key=lambda x: x[1], reverse=True)[:10]:
                content.append(f"- `{ext}`: {count} files")
        content.append("")
    
    # 주요 디렉토리 구조
    content.append("## 🌳 Directory Tree\n")
    content.append("```")
    tree = helpers.get_directory_tree(max_depth=3)
    if tree:
        content.append(tree)
    else:
        content.append("(Directory tree not available)")
    content.append("```\n")
    
    # Python 파일들의 함수/클래스 정보
    if analyzed_files:
        content.append("## 🐍 Python Modules\n")
        
        # 주요 Python 파일들만 선택 (test 제외)
        py_files = [f for f in analyzed_files.keys() if f.endswith('.py') and 'test' not in f.lower()]
        
        # 카테고리별로 분류
        core_files = [f for f in py_files if 'python/' in f and '/vendor/' not in f]
        command_files = [f for f in py_files if 'python/commands/' in f]
        other_files = [f for f in py_files if f not in core_files and f not in command_files]
        
        # Core Python 모듈
        if core_files:
            content.append("### Core Python Modules\n")
            for file_path in sorted(core_files)[:20]:  # 최대 20개
                _add_python_file_info(content, file_path, analyzed_files[file_path])
        
        # Command 모듈
        if command_files:
            content.append("### Command Modules\n")
            for file_path in sorted(command_files)[:10]:
                _add_python_file_info(content, file_path, analyzed_files[file_path])
    
    # TypeScript 파일들 정보
    _add_typescript_info(content, structure)
    
    # 명령어 정보 추가
    content.append("## 🔧 Quick Commands\n")
    content.append("### Structure Analysis:")
    content.append("```python")
    content.append("# Get cached structure")
    content.append("structure = helpers.get_project_structure()")
    content.append("")
    content.append("# Force rescan")
    content.append("helpers.cache_project_structure(force_rescan=True)")
    content.append("")
    content.append("# Get directory tree")
    content.append("tree = helpers.get_directory_tree(max_depth=4)")
    content.append("")
    content.append("# Search in structure")
    content.append("results = helpers.search_in_structure('pattern')")
    content.append("```")
    
    # 파일로 저장 - memory 폴더에 저장
    file_content = '\n'.join(content)
    
    # memory 폴더 경로
    memory_path = os.path.join(os.getcwd(), "memory")
    if not os.path.exists(memory_path):
        os.makedirs(memory_path)
    
    # memory/file_directory.md에 저장
    file_path = os.path.join(memory_path, "file_directory.md")
    helpers.create_file(file_path, file_content)
    
    return len(file_content), file_path


def _add_python_file_info(content: list, file_path: str, file_info: dict):
    """Python 파일 정보를 content에 추가"""
    # 파일명 (상대 경로로 표시)
    rel_path = file_path.replace('\\', '/').replace('python/', '')
    content.append(f"#### 📄 `{file_path}`\n")
    
    # 클래스 정보
    if 'classes' in file_info and file_info['classes']:
        content.append("**Classes:**")
        for class_name, class_info in list(file_info['classes'].items())[:5]:
            methods = class_info.get('methods', [])
            content.append(f"- `{class_name}` ({len(methods)} methods)")
            if methods[:3]:
                for method in methods[:3]:
                    content.append(f"  - `{method}()`")
                if len(methods) > 3:
                    content.append(f"  - ... +{len(methods)-3} more")
    
    # 함수 정보
    if 'functions' in file_info and file_info['functions']:
        content.append("\n**Functions:**")
        funcs = list(file_info['functions'].keys())[:5]
        for func_name in funcs:
            content.append(f"- `{func_name}()`")
        if len(file_info['functions']) > 5:
            content.append(f"- ... +{len(file_info['functions'])-5} more")
    
    content.append("")


def _add_typescript_info(content: list, structure: dict):
    """TypeScript 파일 정보를 content에 추가"""
    if structure and 'structure' in structure:
        all_files = []
        
        def collect_files(node, path=""):
            if isinstance(node, dict):
                for name, child in node.items():
                    if isinstance(child, dict):
                        collect_files(child, f"{path}/{name}" if path else name)
                    elif name.endswith('.ts'):
                        all_files.append(f"{path}/{name}" if path else name)
        
        collect_files(structure['structure'])
        
        ts_files = [f for f in all_files if f.endswith('.ts')]
        if ts_files:
            content.append("## 📘 TypeScript Modules\n")
            content.append(f"Total: {len(ts_files)} files\n")
            
            # 주요 TypeScript 파일들
            important_ts = sorted([f for f in ts_files if any(key in f for key in ['index.ts', 'main.ts', 'server.ts', 'tool-definitions.ts'])])
            if important_ts:
                content.append("### Key TypeScript Files:")
                for ts_file in important_ts[:15]:
                    content.append(f"- `{ts_file}`")
                if len(ts_files) > 15:
                    content.append(f"- ... +{len(ts_files)-15} more files")
                content.append("")


def check_file_directory_freshness(file_path: str, max_age_hours: int = 24) -> bool:
    """file_directory.md의 신선도 확인
    
    Args:
        file_path: 파일 경로
        max_age_hours: 최대 허용 시간 (기본 24시간)
        
    Returns:
        bool: True면 파일이 신선함, False면 업데이트 필요
    """
    if not os.path.exists(file_path):
        return False
    
    mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
    age = datetime.now() - mtime
    
    return age.total_seconds() < (max_age_hours * 3600)
