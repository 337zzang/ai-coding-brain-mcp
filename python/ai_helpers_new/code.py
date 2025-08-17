"""Code analysis and modification helpers for ai-coding-brain-mcp project."""

import os
import ast
import re
import textwrap
from typing import Dict, Any, List, Optional, Union
from .wrappers import wrap_output
from .util import safe_read_file, safe_write_file

# === AST 기반 코드 분석 ===

def parse(filepath: str) -> Dict[str, Any]:
    """Parse Python file and extract structure using AST.
    
    Args:
        filepath: Path to Python file
        
    Returns:
        dict: {
            'functions': List of function info,
            'classes': List of class info,
            'imports': List of imports,
            'constants': List of constants
        }
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    
    if not filepath.endswith('.py'):
        return {
            'functions': [],
            'classes': [],
            'imports': [],
            'constants': []
        }
    
    content = safe_read_file(filepath)
    if content is None:
        raise IOError(f"Failed to read file: {filepath}")
    
    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        return {
            'error': f"Syntax error: {e}",
            'functions': [],
            'classes': [],
            'imports': [],
            'constants': []
        }
    
    functions = []
    classes = []
    imports = []
    constants = []
    
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            # Skip methods (functions inside classes)
            parent = None
            for parent_node in ast.walk(tree):
                if isinstance(parent_node, ast.ClassDef):
                    if node in ast.walk(parent_node):
                        parent = parent_node
                        break
            
            if parent is None:
                func_info = {
                    'name': node.name,
                    'lineno': node.lineno,
                    'args': [arg.arg for arg in node.args.args],
                    'decorators': [d.id if isinstance(d, ast.Name) else str(d) 
                                   for d in node.decorator_list],
                    'docstring': ast.get_docstring(node)
                }
                functions.append(func_info)
        
        elif isinstance(node, ast.ClassDef):
            methods = []
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    method_info = {
                        'name': item.name,
                        'lineno': item.lineno,
                        'args': [arg.arg for arg in item.args.args],
                        'decorators': [d.id if isinstance(d, ast.Name) else str(d) 
                                       for d in item.decorator_list],
                        'docstring': ast.get_docstring(item)
                    }
                    methods.append(method_info)
            
            class_info = {
                'name': node.name,
                'lineno': node.lineno,
                'bases': [base.id if isinstance(base, ast.Name) else str(base) 
                          for base in node.bases],
                'methods': methods,
                'docstring': ast.get_docstring(node)
            }
            classes.append(class_info)
        
        elif isinstance(node, ast.Import):
            for alias in node.names:
                imports.append({
                    'module': alias.name,
                    'alias': alias.asname,
                    'lineno': node.lineno
                })
        
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                imports.append({
                    'module': f"{node.module}.{alias.name}" if node.module else alias.name,
                    'from': node.module,
                    'name': alias.name,
                    'alias': alias.asname,
                    'lineno': node.lineno
                })
        
        elif isinstance(node, ast.Assign):
            # Simple constant detection
            if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                if node.targets[0].id.isupper():
                    constants.append({
                        'name': node.targets[0].id,
                        'lineno': node.lineno
                    })
    
    return {
        'functions': functions,
        'classes': classes,
        'imports': imports,
        'constants': constants
    }

def functions(filepath: str) -> List[Dict[str, Any]]:
    """Get list of functions in a Python file.
    
    Args:
        filepath: Path to Python file
        
    Returns:
        List of function information dictionaries
    """
    parsed = parse(filepath)
    if parsed.get('ok'):
        return parsed['data'].get('functions', [])
    return parsed.get('data', {}).get('functions', [])

def classes(filepath: str) -> List[Dict[str, Any]]:
    """Get list of classes in a Python file.
    
    Args:
        filepath: Path to Python file
        
    Returns:
        List of class information dictionaries
    """
    parsed = parse(filepath)
    if parsed.get('ok'):
        return parsed['data'].get('classes', [])
    return parsed.get('data', {}).get('classes', [])

# === 코드 수정 함수 ===

@wrap_output
def replace(
    filepath: str,
    old_code: str,
    new_code: str,
    fuzzy: bool = False,
    threshold: float = 0.8,
    preview: bool = False,
    auto_indent: bool = True
) -> Union[bool, Dict[str, Any]]:
    """Replace code in file with IndentationManager for perfect indentation.

    이 함수는 IndentationManager를 사용하여 들여쓰기 문제를 완벽하게 해결합니다.

    Args:
        filepath: Path to file
        old_code: Code to replace
        new_code: Replacement code
        fuzzy: Enable fuzzy matching for whitespace differences
        threshold: Similarity threshold for fuzzy matching (0-1)
        preview: If True, show preview without making changes
        auto_indent: Use IndentationManager for smart indentation

    Returns:
        bool or dict: Success status or preview information
    """
    try:
        # 1순위 Critical: 입력 검증 - 빈 문자열 체크
        if not old_code or not old_code.strip():
            return {"ok": False, "error": "교체할 코드가 비어있습니다"}
        if not new_code or not new_code.strip():
            return {"ok": False, "error": "새 코드가 비어있습니다"}
        
        # 2순위 Critical: 구문 검증 - new_code가 올바른 Python 구문인지 확인
        # new_code 전처리: 들여쓰기 제거하여 compile 검사 통과
        import textwrap
        normalized_new_code = textwrap.dedent(new_code).strip()
        
        try:
            compile(normalized_new_code, '<string>', 'exec')
        except SyntaxError as e:
            return {"ok": False, "error": f"구문 오류: {e}"}
        
        # 파일 존재 확인
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")

        # 파일 읽기
        content = safe_read_file(filepath)
        if content is None:
            raise IOError(f"Failed to read file: {filepath}")

        # IndentationManager 사용 (auto_indent가 True일 때)
        if auto_indent:
            try:
                from .indent_utils import IndentationManager
                manager = IndentationManager()

                # 스마트 교체 수행
                result_content, success = manager.smart_replace(
                    content, 
                    old_code, 
                    new_code
                )

                if not success:
                    # IndentationManager가 실패하면 기존 방식으로 폴백
                    print("⚠️ IndentationManager failed, falling back to legacy method")
                    # ⚠️ 중요: 검증은 이미 함수 시작부에서 완료되었으므로 바로 레거시 호출
                    # 기존 fuzzy matching 로직으로 폴백
                    if fuzzy:
                        return _legacy_fuzzy_replace(content, old_code, new_code, threshold, preview)
                    elif old_code in content:
                        result_content = content.replace(old_code, new_code)
                    else:
                        return {"ok": False, "error": "교체할 코드를 찾을 수 없습니다"}

                # 미리보기 모드
                if preview:
                    return {
                        'preview': result_content,
                        'changes': _generate_diff(content, result_content),
                        'success': True
                    }

                # 실제 파일 쓰기
                success = safe_write_file(filepath, result_content)
                return success

            except ImportError:
                print("⚠️ IndentationManager not found, using legacy method")
                # IndentationManager가 없으면 기존 방식 사용
                pass

        # auto_indent가 False이거나 IndentationManager를 사용할 수 없는 경우
        # 기존 로직 수행 (검증은 이미 완료됨)
        if fuzzy:
            return _legacy_fuzzy_replace(content, old_code, new_code, threshold, preview)
        else:
            # 단순 문자열 교체
            if old_code in content:
                result_content = content.replace(old_code, new_code)

                if preview:
                    return {
                        'preview': result_content,
                        'changes': _generate_diff(content, result_content),
                        'success': True
                    }

                success = safe_write_file(filepath, result_content)
                return success
            else:
                return False

    except Exception as e:
        print(f"❌ Replace error: {str(e)}")
        return False

def _legacy_fuzzy_replace(content, old_code, new_code, threshold=0.8, preview=False):
    """
    개선된 레거시 fuzzy replace 함수
    - 들여쓰기 중복 적용 제거
    - 파일 스타일 감지 및 적용
    - textwrap.dedent 정규화 추가
    """
    import textwrap
    from difflib import SequenceMatcher

    # 1. new_code 정규화 (핵심 개선!)
    new_code = textwrap.dedent(new_code).strip()
    old_code = textwrap.dedent(old_code).strip()

    lines = content.splitlines()

    # 2. 파일 스타일 감지 (탭/공백, 들여쓰기 크기)
    def detect_file_indent_style(content_lines, max_check=500):
        """파일의 지배적 들여쓰기 스타일 감지"""
        tab_count = 0
        space_indents = []

        for line in content_lines[:max_check]:
            if line.strip():  # 빈 줄 제외
                leading = line[:len(line) - len(line.lstrip())]
                if '\t' in leading:
                    tab_count += leading.count('\t')
                elif leading:
                    space_indents.append(len(leading))

        # 탭 우선 판정
        if tab_count > len(space_indents) * 0.3:  # 탭이 30% 이상
            return '\t', 1

        # 공백 기반 - 들여쓰기 크기 추정
        if space_indents:
            # 가장 작은 들여쓰기 단위 찾기
            indent_size = 4  # 기본값
            for size in [2, 3, 4, 8]:
                if any(indent % size == 0 for indent in space_indents if indent > 0):
                    indent_size = size
                    break
            return ' ', indent_size

        return ' ', 4  # 기본값

    indent_char, indent_size = detect_file_indent_style(lines)

    # 3. 기존 fuzzy 매칭 로직 (변경 없음)
    old_lines = old_code.splitlines()
    new_lines = new_code.splitlines()

    best_score = 0
    best_start = -1
    best_end = -1

    for start in range(len(lines) - len(old_lines) + 1):
        for end in range(start + len(old_lines), min(start + len(old_lines) + 3, len(lines) + 1)):
            candidate_lines = lines[start:end]

            # 공백 무시하고 비교
            candidate_text = '\n'.join(line.strip() for line in candidate_lines)
            old_text = '\n'.join(line.strip() for line in old_lines)

            score = SequenceMatcher(None, candidate_text, old_text).ratio()

            if score > best_score:
                best_score = score
                best_start = start
                best_end = end

    if best_score < threshold:
        return content  # 매칭 실패

    # 4. 개선된 들여쓰기 적용 로직 (핵심 수정!)
    if lines[best_start].strip():
        # 기준 들여쓰기 감지 (파일 원본 스타일 유지)
        base_line = lines[best_start]
        base_indent_str = base_line[:len(base_line) - len(base_line.lstrip())]
    else:
        base_indent_str = ''

    # new_code의 최소 들여쓰기 계산 (정규화를 위해)
    new_code_min_indent = float('inf')
    for line in new_lines:
        if line.strip():
            current_indent = len(line) - len(line.lstrip())
            new_code_min_indent = min(new_code_min_indent, current_indent)

    if new_code_min_indent == float('inf'):
        new_code_min_indent = 0

    # 5. 새 코드 재들여쓰기 (중복 방지!)
    indented_new_lines = []
    for line in new_lines:
        if line.strip():
            # 상대 들여쓰기 계산
            original_indent = len(line) - len(line.lstrip())
            relative_indent = original_indent - new_code_min_indent

            # 들여쓰기 레벨 계산
            indent_levels = relative_indent // indent_size
            remainder_spaces = relative_indent % indent_size

            # 최종 들여쓰기 생성 (파일 스타일 적용)
            final_indent = base_indent_str + (indent_char * indent_size * indent_levels) + (' ' * remainder_spaces)
            indented_new_lines.append(final_indent + line.lstrip())
        else:
            indented_new_lines.append('')  # 빈 줄 유지

    # 6. 내용 교체
    result_lines = lines[:best_start] + indented_new_lines + lines[best_end:]
    
    # Preview 처리
    if preview:
        return {
            'ok': True,
            'preview': '\n'.join(result_lines),
            'changes': f'교체 완료: {best_score:.2f} 유사도',
            'success': True
        }
    
    return '\n'.join(result_lines)

def _generate_diff(old_content, new_content):
    """Generate a simple diff between old and new content"""
    old_lines = old_content.split('\n')
    new_lines = new_content.split('\n')

    changes = []
    for i, (old, new) in enumerate(zip(old_lines, new_lines)):
        if old != new:
            changes.append(f"Line {i+1}: {old[:50]}... -> {new[:50]}...")

    return changes[:10]  # Return first 10 changes

@wrap_output
def insert(
    filepath: str,
    content: str,
    position: Union[int, str] = None,
    after: bool = False,
    auto_indent: bool = True,
    smart_mode: bool = True
) -> Union[bool, Dict[str, Any]]:
    """Insert content at specified position with O3-level smart algorithms.
    
    O3 개선사항:
    1. @wrap_output 데코레이터 적용 - 표준 에러 처리
    2. IndentationManager.smart_insert 사용 - 오프셋 보존
    3. 앵커 기반 위치 탐색 - 95%+ 정확도
    4. 블록 구조 인식 - 자동 들여쓰기 조정
    
    Args:
        filepath: Path to file
        content: Content to insert
        position: Line number (int) or marker text (str), None for end of file
        after: If True, insert after the position
        auto_indent: Automatically match indentation
        smart_mode: Use IndentationManager for smart insertion
        
    Returns:
        bool or dict: Success status or detailed result
    """
    try:
        # 입력 검증 (O3 개선: 주석만 있는 경우도 체크)
        if not content or not content.strip():
            return {"ok": False, "error": "삽입할 내용이 비어있습니다"}
        
        # 주석만 있는지 체크
        lines = content.split('\n')
        non_comment_lines = [
            ln for ln in lines 
            if ln.strip() and not ln.lstrip().startswith('#')
        ]
        
        if not non_comment_lines:
            return {"ok": False, "error": "실제 코드가 없습니다 (주석만 있음)"}
        
        # 파일 존재 확인
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")
        
        # 파일 읽기
        file_content = safe_read_file(filepath)
        if file_content is None:
            raise IOError(f"Failed to read file: {filepath}")
        
        # smart_mode가 활성화되고 Python 파일인 경우
        if smart_mode and filepath.endswith('.py') and auto_indent:
            try:
                from .indent_utils import IndentationManager
                manager = IndentationManager()
                
                # position이 None인 경우 파일 끝에 추가
                if position is None:
                    position = len(file_content.split('\n'))
                
                # 스마트 삽입 수행
                result_content, success = manager.smart_insert(
                    file_content,
                    content,
                    position,
                    after
                )
                
                if success:
                    # 파일 쓰기
                    if safe_write_file(filepath, result_content):
                        return {
                            "ok": True,
                            "message": "Smart insert successful",
                            "mode": "smart",
                            "position": position
                        }
                    else:
                        return {"ok": False, "error": "Failed to write file"}
                else:
                    # smart_insert 실패 시 레거시 모드로 폴백
                    print("⚠️ Smart insert failed, falling back to legacy mode")
                    
            except ImportError:
                print("⚠️ IndentationManager not available, using legacy mode")
        
        # 레거시 모드 또는 폴백
        lines = file_content.split('\n')
        
        # position이 None인 경우 파일 끝
        if position is None:
            insert_line = len(lines)
        elif isinstance(position, int):
            insert_line = position - 1 if not after else position
            insert_line = max(0, min(insert_line, len(lines)))
        elif isinstance(position, str):
            # 마커 텍스트 찾기
            insert_line = None
            best_match = None
            best_score = 0
            
            for i, line in enumerate(lines):
                if position in line:
                    # 정확한 매칭
                    insert_line = i if not after else i + 1
                    break
                
                # 부분 매칭 점수 계산
                if position.lower() in line.lower():
                    score = len(position) / len(line) if line else 0
                    if score > best_score:
                        best_match = i
                        best_score = score
            
            if insert_line is None and best_match is not None:
                # 최선의 부분 매칭 사용
                insert_line = best_match if not after else best_match + 1
            elif insert_line is None:
                return {"ok": False, "error": f"Marker '{position}' not found in {filepath}"}
        else:
            return {"ok": False, "error": "Position must be int, str, or None"}
        
        # 자동 들여쓰기 (레거시 모드)
        if auto_indent and insert_line > 0 and insert_line <= len(lines):
            # 참조 라인 선택
            ref_line = lines[insert_line - 1] if insert_line > 0 else ""
            base_indent = len(ref_line) - len(ref_line.lstrip())
            
            # 블록 시작 감지
            if ref_line.strip().endswith(':'):
                # 블록 시작 후 - 한 단계 더 들여쓰기
                base_indent += 4
            
            # 들여쓰기 적용
            content_lines = content.split('\n')
            adjusted_lines = []
            
            for j, line in enumerate(content_lines):
                if line.strip():
                    if j == 0:
                        # 첫 줄은 기본 들여쓰기
                        adjusted_lines.append(' ' * base_indent + line.lstrip())
                    else:
                        # 나머지 줄은 상대적 들여쓰기 보존
                        orig_indent = len(line) - len(line.lstrip())
                        adjusted_lines.append(' ' * base_indent + ' ' * orig_indent + line.lstrip())
                else:
                    adjusted_lines.append('')
            
            content = '\n'.join(adjusted_lines)
        
        # 삽입 수행
        if insert_line >= len(lines):
            lines.append(content)
        else:
            # content가 여러 줄인 경우 각 줄을 별도로 삽입
            content_lines = content.split('\n')
            for i, line in enumerate(content_lines):
                lines.insert(insert_line + i, line)
        
        new_content = '\n'.join(lines)
        
        # 파일 쓰기
        if safe_write_file(filepath, new_content):
            return {
                "ok": True,
                "message": "Insert successful",
                "mode": "legacy",
                "position": insert_line
            }
        else:
            return {"ok": False, "error": f"Failed to write file: {filepath}"}
            
    except Exception as e:
        return {"ok": False, "error": str(e), "error_type": type(e).__name__}

def delete(
    filepath: str,
    target: Union[str, int],
    mode: str = 'line',
    preview: bool = False
) -> Union[bool, Dict[str, Any]]:
    """Delete content from file.
    
    Args:
        filepath: Path to file
        target: Content to delete (str) or line number (int)
        mode: 'line' for single line, 'block' for code block
        preview: If True, show what would be deleted
        
    Returns:
        bool or dict: Success status or preview information
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    
    content = safe_read_file(filepath)
    if content is None:
        raise IOError(f"Failed to read file: {filepath}")
    
    lines = content.split('\n')
    
    if mode == 'line':
        if isinstance(target, int):
            # Delete by line number
            if 1 <= target <= len(lines):
                if preview:
                    return {
                        'line': target,
                        'content': lines[target - 1]
                    }
                del lines[target - 1]
            else:
                raise ValueError(f"Line {target} out of range")
        else:
            # Delete lines containing target
            indices_to_delete = []
            for i, line in enumerate(lines):
                if target in line:
                    indices_to_delete.append(i)
            
            if preview:
                return {
                    'lines': [(i + 1, lines[i]) for i in indices_to_delete]
                }
            
            for i in reversed(indices_to_delete):
                del lines[i]
    
    elif mode == 'block':
        # Delete entire block (function, class, etc.)
        if isinstance(target, str):
            parsed = parse(filepath)
            if not parsed.get('ok'):
                raise ValueError("Failed to parse file")
            
            data = parsed['data']
            
            # Find target in functions or classes
            target_line = None
            block_end = None
            
            for func in data.get('functions', []):
                if func['name'] == target:
                    target_line = func.get('lineno')
                    # Find end of function
                    block_end = _find_block_end(lines, target_line - 1)
                    break
            
            if target_line is None:
                for cls in data.get('classes', []):
                    if cls['name'] == target:
                        target_line = cls.get('lineno')
                        block_end = _find_block_end(lines, target_line - 1)
                        break
            
            if target_line and block_end:
                if preview:
                    return {
                        'block': target,
                        'start': target_line,
                        'end': block_end + 1,
                        'content': '\n'.join(lines[target_line - 1:block_end + 1])
                    }
                
                # Delete the block
                del lines[target_line - 1:block_end + 1]
            else:
                raise ValueError(f"Block '{target}' not found")
    
    new_content = '\n'.join(lines)
    
    if safe_write_file(filepath, new_content):
        return True
    raise IOError(f"Failed to write file: {filepath}")

def _find_block_end(lines: List[str], start_idx: int) -> int:
    """Find the end of a code block starting at start_idx."""
    if start_idx >= len(lines):
        return start_idx
    
    # Get indentation of start line
    start_line = lines[start_idx]
    start_indent = len(start_line) - len(start_line.lstrip())
    
    # Find where this block ends
    for i in range(start_idx + 1, len(lines)):
        line = lines[i]
        
        # Skip empty lines
        if not line.strip():
            continue
        
        # Check indentation
        current_indent = len(line) - len(line.lstrip())
        
        # If we're back to the same or less indentation, block has ended
        if current_indent <= start_indent:
            return i - 1
    
    # Block continues to end of file
    return len(lines) - 1

def view(filepath: str, target: Optional[str] = None, context_lines: int = 10) -> Union[str, Dict[str, Any]]:
    """View code content with optional target focus."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    if target is None:
        return ''.join(lines)

    # Parse file to find target
    parsed = parse(filepath)
    if not parsed.get('ok'):
        return parsed  # Return error
    
    parsed = parsed.get('data', {})
    target_line = None
    target_type = None
    
    # Search in functions
    for func in parsed.get('functions', []):
        if func['name'] == target:
            target_line = func.get('lineno', 0)
            target_type = 'function'
            break
    
    # Search in classes
    if target_line is None:
        for cls in parsed.get('classes', []):
            if cls['name'] == target:
                target_line = cls.get('lineno', 0)
                target_type = 'class'
                break
            
            # Search in methods
            for method in cls.get('methods', []):
                if method['name'] == target or f"{cls['name']}.{method['name']}" == target:
                    target_line = method.get('lineno', 0)
                    target_type = 'method'
                    break

    if target_line is None:
        # Try to find as a text pattern
        for i, line in enumerate(lines, 1):
            if target in line:
                target_line = i
                target_type = 'text'
                break
    
    if target_line:
        start = max(0, target_line - context_lines - 1)
        end = min(len(lines), target_line + context_lines)
        
        result = {
            'found': True,
            'type': target_type,
            'line_number': target_line,
            'content': ''.join(lines[start:end]),
            'start_line': start + 1,
            'end_line': end
        }
        return result
    
    return {
        'found': False,
        'message': f"Target '{target}' not found in {filepath}"
    }

# 추가 헬퍼 함수들

def log_code_change(filepath: str, action: str, description: str = "") -> None:
    """Log code changes for tracking."""
    import datetime
    log_entry = f"[{datetime.datetime.now().isoformat()}] {action}: {filepath}"
    if description:
        log_entry += f" - {description}"
    # TODO: Implement actual logging mechanism if needed
    print(log_entry)

# Export all functions
__all__ = [
    'parse',
    'functions', 
    'classes',
    'replace',
    'insert',
    'delete',
    'view',
    'log_code_change'
]