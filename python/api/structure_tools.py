"""
structure_tools.py
프로젝트 구조 관련 MCP 도구들
"""

import os
import sys
from datetime import datetime

# python 디렉토리를 sys.path에 추가
python_path = os.path.dirname(os.path.abspath(__file__))
if python_path not in sys.path:
    sys.path.insert(0, python_path)

from file_directory_generator import create_file_directory_md, check_file_directory_freshness

def structure_info(refresh: bool = False) -> dict:
    """프로젝트 구조 정보 제공 및 file_directory.md 업데이트
    
    Args:
        refresh: 구조를 재스캔할지 여부
        
    Returns:
        dict: 구조 정보와 file_directory.md 내용
    """
    # helpers 가져오기
    helpers = globals().get('helpers')
    if not helpers:
        raise RuntimeError("helpers 객체를 찾을 수 없습니다.")
    
    # 구조 캐시 업데이트
    if refresh or not helpers.get_project_structure():
        print("🔄 프로젝트 구조 재스캔 중...")
        helpers.cache_project_structure(force_rescan=True)
    
    # file_directory.md 경로
    file_path = os.path.join(os.getcwd(), "memory", "file_directory.md")
    
    # 파일 신선도 확인 (24시간)
    if not check_file_directory_freshness(file_path, max_age_hours=24):
        print("📄 file_directory.md 업데이트 중...")
        create_file_directory_md(helpers)
    
    # 구조 정보 반환
    structure = helpers.get_project_structure()
    stats = helpers.get_structure_stats()
    
    # 트리 생성
    tree = helpers.get_directory_tree(max_depth=3)
    
    # file_directory.md 읽기
    file_content = ""
    if os.path.exists(file_path):
        file_content = helpers.read_file(file_path)
    
    return {
        "success": True,
        "stats": stats,
        "tree": tree[:1000],  # 처음 1000자만
        "file_directory_content": file_content[:2000],  # 처음 2000자만
        "file_path": file_path,
        "message": "✅ 구조 정보 로드 완료"
    }


def refresh_context() -> dict:
    """모든 캐시 및 컨텍스트 새로고침"""
    
    helpers = globals().get('helpers')
    if not helpers:
        raise RuntimeError("helpers 객체를 찾을 수 없습니다.")
    
    print("🔄 전체 컨텍스트 새로고침 시작...")
    
    # 1. 구조 재스캔
    helpers.cache_project_structure(force_rescan=True)
    
    # 2. AST 분석 재실행 (주요 Python 파일)
    py_files = helpers.search_files_advanced(".", "*.py")
    analyzed_count = 0
    for file_path in py_files[:20]:  # 주요 파일 20개만
        if 'test' not in file_path.lower() and 'vendor' not in file_path:
            try:
                helpers.parse_with_snippets(file_path)
                analyzed_count += 1
            except:
                pass
    
    # 3. file_directory.md 재생성
    file_size, file_path = create_file_directory_md(helpers)
    
    # 4. 컨텍스트 저장
    helpers.save_context()
    
    return {
        "success": True,
        "message": "✅ 컨텍스트 새로고침 완료",
        "updated": {
            "structure": True,
            "ast_analysis": f"{analyzed_count} files",
            "file_directory": f"{file_size:,} bytes"
        }
    }


def quick_context() -> dict:
    """빠른 컨텍스트 정보 제공 (file_directory.md 기반)"""
    
    helpers = globals().get('helpers')
    if not helpers:
        raise RuntimeError("helpers 객체를 찾을 수 없습니다.")
    
    # file_directory.md 경로
    file_path = os.path.join(os.getcwd(), "memory", "file_directory.md")
    
    # 파일이 있으면 바로 읽기
    if os.path.exists(file_path):
        content = helpers.read_file(file_path)
        
        # Overview 섹션 추출
        lines = content.split('\n')
        overview_lines = []
        in_overview = False
        
        for line in lines:
            if "## 📊 Overview" in line:
                in_overview = True
            elif in_overview and line.startswith("##"):
                break
            elif in_overview:
                overview_lines.append(line)
        
        # 트리 섹션 추출 (간략하게)
        tree_lines = []
        in_tree = False
        tree_count = 0
        
        for line in lines:
            if "## 🌳 Directory Tree" in line:
                in_tree = True
            elif in_tree and line.startswith("##"):
                break
            elif in_tree and tree_count < 20:  # 최대 20줄
                tree_lines.append(line)
                tree_count += 1
        
        return {
            "success": True,
            "overview": '\n'.join(overview_lines),
            "tree_preview": '\n'.join(tree_lines),
            "full_content": content[:3000],  # 처음 3000자
            "last_updated": datetime.fromtimestamp(
                os.path.getmtime(file_path)
            ).isoformat(),
            "file_path": file_path
        }
    else:
        # 파일이 없으면 생성
        print("📄 file_directory.md가 없습니다. 생성 중...")
        create_file_directory_md(helpers)
        return quick_context()  # 재귀 호출


# API로 노출할 함수들
__all__ = ['structure_info', 'refresh_context', 'quick_context']
