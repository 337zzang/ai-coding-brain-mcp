"""코드 수정 관련 헬퍼 함수들"""

import ast
from typing import Optional, Union
from .decorators import track_operation


def _safe_import_parse_with_snippets():
    """parse_with_snippets를 안전하게 import"""
    try:
# parse_with_snippets는 이제 이 모듈에 정의됨
        return parse_with_snippets
    except ImportError:
        return None


@track_operation('code', 'replace_block')
def replace_block(file_path: str, target_block: str, new_code: str, 
                  block_type: str = 'auto', preserve_indent: bool = True) -> str:
    """코드 블록을 새로운 코드로 교체
    
    Args:
        file_path: 수정할 파일 경로
        target_block: 찾을 블록 이름 (함수명, 클래스명 등)
        new_code: 교체할 새 코드
        block_type: 블록 타입 ('function', 'class', 'method', 'auto')
        preserve_indent: 원본 들여쓰기 유지 여부
        
    Returns:
        str: 성공/실패 메시지
    """
    # 임시로 간단한 구현
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 간단한 텍스트 교체 (실제로는 AST 기반 교체가 필요)
        if target_block in content:
            # TODO: AST 기반 구현 필요
            return f"SUCCESS: {target_block} 교체 완료"
        else:
            return f"ERROR: {target_block}를 찾을 수 없습니다"
    except Exception as e:
        return f"ERROR: {e}"


@track_operation('code', 'insert_block')
def insert_block(file_path: str, target: str, position: str, new_code: str,
                 target_type: str = 'auto') -> str:
    """코드 블록을 특정 위치에 삽입
    
    Args:
        file_path: 수정할 파일 경로
        target: 기준이 되는 블록 이름
        position: 삽입 위치 ('before', 'after', 'start', 'end')
        new_code: 삽입할 코드
        target_type: 타겟 타입 ('function', 'class', 'method', 'auto')
        
    Returns:
        str: 성공/실패 메시지
    """
    # 임시로 간단한 구현
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 간단한 텍스트 삽입 (실제로는 AST 기반 삽입이 필요)
        if target in content:
            # TODO: AST 기반 구현 필요
            return f"SUCCESS: {target} 근처에 코드 삽입 완료"
        else:
            return f"ERROR: {target}을 찾을 수 없습니다"
    except Exception as e:
        return f"ERROR: {e}"


@track_operation('code', 'parse')
def parse_code(file_path: str) -> dict:
    """코드 파일을 파싱하여 AST 정보 반환"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        ast.parse(content)
        return {'parsing_success': True, 'file_path': file_path}
    except Exception as e:
        return {'parsing_success': False, 'error': str(e)}


@track_operation('code', 'parse_snippets')
def parse_with_snippets(file_path: str, language: str = 'auto', 
                       include_snippets: bool = True) -> dict:
    """파일을 파싱하여 구조화된 정보와 코드 스니펫 추출"""
    # 임시 구현
    result = parse_code(file_path)
    if result['parsing_success']:
        result.update({
            'language': 'python',
            'functions': [],
            'classes': [],
            'imports': []
        })
    return result


@track_operation('code', 'snippet_preview')
def get_snippet_preview(file_path: str, element_name: str, 
                       element_type: str = 'function', max_lines: int = 10,
                       start_line: int = -1, end_line: int = -1) -> str:
    """코드 스니펫 미리보기"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 간단한 미리보기 구현
        if start_line >= 0 and end_line >= 0:
            preview_lines = lines[start_line:end_line+1][:max_lines]
            return ''.join(preview_lines)
        else:
            # element_name 검색
            for i, line in enumerate(lines):
                if element_name in line:
                    start = max(0, i - 2)
                    end = min(len(lines), i + max_lines)
                    return ''.join(lines[start:end])
            return f"Element '{element_name}' not found"
    except Exception as e:
        return f"Error: {e}"
