"""
enhanced_file_directory_generator.py
프로젝트 구조와 함수/클래스 정보를 포함한 file_directory.md를 memory 폴더에 생성
기존 파일이 있으면 업데이트만 수행
"""

import os
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
import difflib
import hashlib

def create_or_update_file_directory_md(helpers=None, context=None) -> tuple[int, str, bool]:
    """프로젝트 구조와 함수/클래스 정보를 포함한 file_directory.md를 생성 또는 업데이트
    
    Returns:
        tuple: (파일 크기, 파일 경로, 업데이트 여부)
    """
    # helpers와 context 가져오기
    if helpers is None:
        helpers = globals().get('helpers')
        if not helpers:
            raise RuntimeError("helpers 객체를 찾을 수 없습니다.")
    
    if context is None:
        context = helpers.get_context()
    
    # memory 폴더 경로
    memory_path = os.path.join(os.getcwd(), "memory")
    if not os.path.exists(memory_path):
        os.makedirs(memory_path)
    
    file_path = os.path.join(memory_path, "file_directory.md")
    
    # 기존 파일 내용 로드
    existing_content = ""
    existing_module_info = {}
    if os.path.exists(file_path):
        existing_content = helpers.read_file(file_path)
        existing_module_info = parse_existing_content(existing_content)
    
    # 새로운 내용 생성
    new_content = generate_file_directory_content(helpers, context, existing_module_info)
    
    # 변경사항 확인
    is_updated = existing_content != new_content
    
    if is_updated:
        # 파일 저장
        helpers.create_file(file_path, new_content)
        
        # 변경 사항 요약
        if existing_content:
            print("📝 file_directory.md 업데이트 완료:")
            summarize_changes(existing_content, new_content)
    else:
        print("✅ file_directory.md는 이미 최신 상태입니다.")
    
    return len(new_content), file_path, is_updated


def parse_existing_content(content: str) -> Dict[str, Any]:
    """기존 file_directory.md 내용을 파싱하여 모듈 정보 추출"""
    module_info = {}
    lines = content.split('\n')
    current_module = None
    current_section = None
    buffer = []
    
    for line in lines:
        # 모듈 헤더 감지
        if line.startswith("#### 📄 `") and line.endswith("`"):
            # 이전 모듈 정보 저장
            if current_module and buffer:
                module_info[current_module] = '\n'.join(buffer).strip()
            
            # 새 모듈 시작
            current_module = line[9:-1]  # "#### 📄 `"와 "`" 제거
            buffer = []
            current_section = None
        
        # 섹션 헤더 감지
        elif line.startswith("**") and line.endswith(":**"):
            current_section = line
            buffer.append(line)
        
        # 내용 수집
        elif current_module and line.strip():
            buffer.append(line)
    
    # 마지막 모듈 저장
    if current_module and buffer:
        module_info[current_module] = '\n'.join(buffer).strip()
    
    return module_info


def generate_file_directory_content(helpers, context, existing_info: Dict[str, Any]) -> str:
    """새로운 file_directory.md 내용 생성"""
    structure = helpers.get_project_structure()
    if not structure:
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
    
    # Python 파일들의 함수/클래스 정보 (개선된 버전)
    if analyzed_files:
        content.append("## 🐍 Python Modules\n")
        
        # 주요 Python 파일들만 선택
        py_files = [f for f in analyzed_files.keys() if f.endswith('.py') and 'test' not in f.lower()]
        
        # 카테고리별로 분류
        categories = {
            "Core Modules": [f for f in py_files if 'python/' in f and '/vendor/' not in f and '/commands/' not in f],
            "Command Modules": [f for f in py_files if 'python/commands/' in f],
            "API Modules": [f for f in py_files if 'python/api/' in f],
            "Vendor Modules": [f for f in py_files if '/vendor/' in f]
        }
        
        for category, files in categories.items():
            if files:
                content.append(f"### {category}\n")
                for file_path in sorted(files)[:30]:  # 카테고리별 최대 30개
                    # 모듈 정보 생성
                    module_content = generate_module_info(file_path, analyzed_files.get(file_path, {}))
                    
                    # 기존 정보와 비교
                    if file_path in existing_info:
                        # 변경사항이 있는 경우에만 업데이트
                        if module_content != existing_info[file_path]:
                            content.append(f"#### 📄 `{file_path}` *(updated)*\n")
                        else:
                            content.append(f"#### 📄 `{file_path}`\n")
                    else:
                        content.append(f"#### 📄 `{file_path}` *(new)*\n")
                    
                    content.append(module_content)
                    content.append("")
    
    # TypeScript 파일들 정보
    content.extend(generate_typescript_section(structure))
    
    # Quick Commands 섹션
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
    
    return '\n'.join(content)


def generate_module_info(file_path: str, file_info: dict) -> str:
    """모듈의 상세 정보 생성 (가독성 개선 버전)"""
    lines = []
    
    # 모듈 요약 정보 추가
    module_summary = get_module_summary(file_path)
    if module_summary:
        lines.append(f"_{module_summary}_")
        lines.append("")  # 빈 줄 추가
    
    has_content = False
    
    # 클래스 정보
    if 'classes' in file_info and file_info['classes']:
        has_content = True
        lines.append("**Classes:**")
        classes = file_info['classes']
        
        class_count = 0
        if isinstance(classes, list):
            for class_item in classes[:3]:  # 최대 3개
                if isinstance(class_item, dict):
                    class_name = class_item.get('name', 'unknown')
                    if class_name.startswith('_') and not class_name.startswith('__'):
                        continue  # private 클래스 스킵
                    
                    methods = class_item.get('methods', [])
                    docstring = class_item.get('docstring', '')
                    
                    class_desc = f"- `{class_name}`"
                    if methods:
                        class_desc += f" ({len(methods)} methods)"
                    if docstring:
                        first_line = docstring.split('\n')[0].strip()
                        if first_line and len(first_line) > 10:
                            class_desc += f" - {first_line[:50]}"
                            if len(first_line) > 50:
                                class_desc += "..."
                    lines.append(class_desc)
                    class_count += 1
        
        if isinstance(classes, list) and len(classes) > class_count:
            lines.append(f"  ... +{len(classes) - class_count} more classes")
    
    # 함수 정보
    if 'functions' in file_info and file_info['functions']:
        has_content = True
        if lines and lines[-1] != "":
            lines.append("")
        lines.append("**Functions:**")
        
        functions = file_info['functions']
        func_list = []
        
        if isinstance(functions, list):
            for func_item in functions:
                if isinstance(func_item, dict):
                    func_name = func_item.get('name', 'unknown')
                    # private 함수 제외
                    if not func_name.startswith('_') or func_name.startswith('__') and func_name.endswith('__'):
                        func_list.append((func_name, func_item.get('docstring', '')))
        
        # 중요한 함수 우선 표시
        important_funcs = [f for f in func_list if not f[0].startswith('_')][:5]
        for func_name, docstring in important_funcs:
            func_desc = f"- `{func_name}()`"
            if docstring:
                first_line = docstring.split('\n')[0].strip()
                if first_line and len(first_line) > 10:
                    func_desc += f" - {first_line[:40]}"
                    if len(first_line) > 40:
                        func_desc += "..."
            lines.append(func_desc)
        
        remaining = len(func_list) - len(important_funcs)
        if remaining > 0:
            lines.append(f"  ... +{remaining} more functions")
    
    # imports 정보 (__init__.py 파일용)
    if not has_content and '__init__.py' in file_path:
        if 'imports' in file_info and file_info['imports']:
            has_content = True
            lines.append("**Exports/Imports:**")
            imports = file_info['imports']
            
            if isinstance(imports, list):
                # from . import 형태 우선
                local_imports = [imp for imp in imports[:5] if isinstance(imp, dict) and imp.get('module', '').startswith('.')]
                for imp in local_imports:
                    module = imp.get('module', '')
                    names = imp.get('names', [])
                    if names:
                        lines.append(f"- from {module} import {', '.join(names[:3])}")
    
    # 빈 모듈 처리
    if not has_content:
        if '__init__.py' in file_path:
            lines.append("*(Package initializer - no exports)*")
        else:
            lines.append("*(Empty module)*")
    
    return '
'.join(lines)  # 실제 줄바꿈 사용


def get_module_summary(file_path: str) -> str:
    """모듈의 요약 정보 생성"""
    # 파일 경로에서 모듈 타입 추론
    if '/commands/' in file_path:
        if 'enhanced_flow' in file_path:
            return "Enhanced project flow management with context handling"
        elif 'next' in file_path:
            return "Task progression and workflow management"
        elif 'plan' in file_path:
            return "Project planning and phase management"
        elif 'task' in file_path:
            return "Task creation and management"
        elif 'wisdom' in file_path:
            return "Project wisdom and best practices tracking"
    
    elif '/api/' in file_path:
        if 'public' in file_path:
            return "Public API exports for MCP tools"
        elif 'structure_tools' in file_path:
            return "Project structure analysis and file directory management"
    
    elif 'ai_helpers' in file_path:
        return "Core helper functions for file operations, AST parsing, and context management"
    
    elif 'ast_parser' in file_path:
        return "AST parsing utilities for Python code analysis"
    
    elif 'wisdom' in file_path:
        return "Wisdom system for tracking mistakes and best practices"
    
    elif 'context_manager' in file_path:
        return "Project context management and persistence"
    
    elif 'models' in file_path:
        return "Pydantic models for project data structures"
    
    return ""


def generate_typescript_section(structure: dict) -> List[str]:
    """TypeScript 섹션 생성"""
    lines = []
    
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
            lines.append("## 📘 TypeScript Modules\n")
            lines.append(f"Total: {len(ts_files)} files\n")
            
            # 주요 TypeScript 파일들
            important_ts = sorted([f for f in ts_files if any(key in f for key in ['index.ts', 'main.ts', 'server.ts', 'tool-definitions.ts'])])
            if important_ts:
                lines.append("### Key TypeScript Files:")
                for ts_file in important_ts[:15]:
                    # 파일 설명 추가
                    if 'tool-definitions' in ts_file:
                        lines.append(f"- `{ts_file}` - MCP tool definitions and handlers")
                    elif 'index' in ts_file:
                        lines.append(f"- `{ts_file}` - Module entry point")
                    elif 'server' in ts_file:
                        lines.append(f"- `{ts_file}` - Server implementation")
                    else:
                        lines.append(f"- `{ts_file}`")
                
                if len(ts_files) > 15:
                    lines.append(f"- ... +{len(ts_files)-15} more files")
                lines.append("")
    
    return lines


def summarize_changes(old_content: str, new_content: str):
    """변경사항 요약 출력"""
    old_lines = old_content.split('\n')
    new_lines = new_content.split('\n')
    
    # 간단한 통계
    print(f"  - 이전 크기: {len(old_content):,} bytes")
    print(f"  - 새 크기: {len(new_content):,} bytes")
    print(f"  - 변경: {abs(len(new_content) - len(old_content)):,} bytes")
    
    # 새로 추가된 모듈 찾기
    new_modules = []
    updated_modules = []
    
    for line in new_lines:
        if line.startswith("#### 📄 `") and "*(new)*" in line:
            module = line.split('`')[1]
            new_modules.append(module)
        elif line.startswith("#### 📄 `") and "*(updated)*" in line:
            module = line.split('`')[1]
            updated_modules.append(module)
    
    if new_modules:
        print(f"  - 새 모듈: {len(new_modules)}개")
        for module in new_modules[:5]:
            print(f"    + {module}")
        if len(new_modules) > 5:
            print(f"    ... +{len(new_modules)-5} more")
    
    if updated_modules:
        print(f"  - 업데이트된 모듈: {len(updated_modules)}개")
        for module in updated_modules[:5]:
            print(f"    ~ {module}")
        if len(updated_modules) > 5:
            print(f"    ... +{len(updated_modules)-5} more")
