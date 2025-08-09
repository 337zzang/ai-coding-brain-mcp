"""
Code manipulation helper functions with improved replace, insert, and delete operations.
Integrated version combining all file editing capabilities.
"""

import ast
import re
import os
import difflib
from typing import Dict, List, Optional, Any, Union, Tuple

# wrap_output import 문제 해결
try:
    from .wrappers import wrap_output, ensure_response, safe_execution
except (ImportError, NameError):
    # 순환 import 문제 발생 시 더미 데코레이터 사용
    def wrap_output(func):
        """Fallback wrapper when circular import occurs"""
        return func
    def ensure_response(result):
        return result
    def safe_execution(func):
        return func


# safe_execution을 wrap_output으로 별칭 설정


def _normalize_code(block: str) -> str:
    """
    코드 블록을 정규화하여 fuzzy matching 정확도 향상

    1. 공통 들여쓰기 제거 (textwrap.dedent)
    2. 우측 공백 제거 (rstrip)
    3. 연속 공백을 단일 공백으로 (re.sub)
    4. 양끝 빈줄 제거
    5. 탭을 공백으로 변환
    """
    import textwrap
    import re

    # 빈 문자열 처리
    if not block:
        return ""

    # 공통 들여쓰기 제거
    block = textwrap.dedent(block)

    # 각 줄 처리
    normalized_lines = []
    for line in block.splitlines():
        # 우측 공백 제거
        line = line.rstrip()
        # 탭을 공백으로 변환
        line = line.replace('\t', '    ')
        # 연속 공백을 단일 공백으로 (문자열 내부는 제외)
        if not line.strip().startswith(('#', '"', "'")):
            line = re.sub(r'  +', ' ', line)
        normalized_lines.append(line)

    # 양끝 빈줄 제거
    while normalized_lines and not normalized_lines[0]:
        normalized_lines.pop(0)
    while normalized_lines and not normalized_lines[-1]:
        normalized_lines.pop()

    return '\n'.join(normalized_lines)




def _normalize_for_fuzzy(text: str) -> str:
    """Fuzzy matching을 위한 텍스트 정규화 (개선된 버전)

    - 공통 들여쓰기 제거 (textwrap.dedent)
    - 각 줄의 우측 공백 제거
    - 연속 공백을 단일 공백으로
    - 양끝 빈줄 제거
    """
    import textwrap
    import re

    # 빈 문자열 처리
    if not text:
        return ""

    # 1. 공통 들여쓰기 제거
    text = textwrap.dedent(text)

    # 2. 각 줄 처리
    lines = []
    for line in text.splitlines():
        # 우측 공백 제거
        line = line.rstrip()
        # 연속 공백/탭을 단일 공백으로
        line = re.sub(r'[ \t]+', ' ', line)
        lines.append(line)

    # 3. 재조합 및 양끝 정리
    normalized = '\n'.join(lines).strip()

    return normalized

def _get_indent_level(source: str, line_no: int) -> int:
    """정확한 들여쓰기 레벨 계산

    tokenize를 사용하여 주어진 라인의 정확한 들여쓰기 레벨을 계산합니다.

    Args:
        source: 소스 코드 전체
        line_no: 들여쓰기를 확인할 라인 번호 (1-based)

    Returns:
        들여쓰기 공백 수
    """
    import tokenize
    import io

    try:
        # tokenize로 들여쓰기 추적
        indent_stack = []
        tokens = tokenize.generate_tokens(io.StringIO(source).readline)

        for tok in tokens:
            if tok.start[0] > line_no:
                break
            if tok.type == tokenize.INDENT:
                indent_stack.append(tok.end[1])
            elif tok.type == tokenize.DEDENT and indent_stack:
                indent_stack.pop()

        return indent_stack[-1] if indent_stack else 0
    except:
        # 폴백: 이전 줄의 들여쓰기 사용
        lines = source.splitlines()
        if 0 < line_no <= len(lines):
            # line_no는 1-based이므로 -1
            line = lines[line_no - 1]
            return len(line) - len(line.lstrip())
        return 0


def get_common_indent(text: str) -> int:
    """Calculate the common indentation level."""
    lines = text.split('\n')
    non_empty_lines = [line for line in lines if line.strip()]
    if not non_empty_lines:
        return 0

    indents = []
    for line in non_empty_lines:
        if line.strip():
            indent = len(line) - len(line.lstrip())
            indents.append(indent)

    return min(indents) if indents else 0

def adjust_indentation(text: str, target_indent: int, preserve_relative: bool = True) -> str:
    """Adjust indentation of text block."""
    lines = text.split('\n')
    if not lines:
        return text

    # Get current base indentation
    current_indent = get_common_indent(text) if preserve_relative else 0

    # Calculate adjustment
    indent_diff = target_indent - current_indent

    # Apply adjustment
    adjusted_lines = []
    for line in lines:
        if line.strip():  # Non-empty line
            if indent_diff > 0:
                adjusted_lines.append(' ' * indent_diff + line)
            elif indent_diff < 0:
                # Remove indentation carefully
                to_remove = -indent_diff
                if line.startswith(' ' * to_remove):
                    adjusted_lines.append(line[to_remove:])
                else:
                    adjusted_lines.append(line.lstrip())
            else:
                adjusted_lines.append(line)
        else:
            adjusted_lines.append(line)

    return '\n'.join(adjusted_lines)

def find_fuzzy_match(content: str, pattern: str, threshold: float = 0.8) -> Optional[Tuple[int, int, str]]:
    """Find fuzzy match for pattern in content."""
    lines = content.split('\n')
    pattern_lines = pattern.strip().split('\n')

    # Try exact match first
    pattern_str = '\n'.join(pattern_lines)
    if pattern_str in content:
        start = content.index(pattern_str)
        return (start, start + len(pattern_str), pattern_str)

    # Normalize for fuzzy matching
def normalize(text):
    """Safe normalization that preserves code structure"""
    import textwrap
    # Remove common indentation but preserve line structure
    text = textwrap.dedent(text)
    # Remove trailing whitespace from each line
    lines = [line.rstrip() for line in text.split('\n')]
    # Remove empty lines at start and end
    while lines and not lines[0]:
        lines.pop(0)
    while lines and not lines[-1]:
        lines.pop()
    return '\n'.join(lines)

    pattern_normalized = normalize(pattern)

    # Sliding window search
    best_match = None
    best_ratio = threshold

    for i in range(len(lines) - len(pattern_lines) + 1):
        window = lines[i:i + len(pattern_lines)]
        window_text = '\n'.join(window)
        window_normalized = normalize(window_text)

        ratio = difflib.SequenceMatcher(None, pattern_normalized, window_normalized).ratio()

        if ratio > best_ratio:
            best_ratio = ratio
            start = sum(len(line) + 1 for line in lines[:i])
            end = start + len(window_text)
            best_match = (start, end, window_text)

    return best_match


@wrap_output
def parse(filepath: str) -> Dict[str, Any]:
    """Parse a Python file and extract its structure."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        raise ValueError(f"Syntax error in {filepath}: {e}")

    functions = []
    classes = []

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            functions.append({
                'name': node.name,
                'lineno': node.lineno,
                'args': [arg.arg for arg in node.args.args],
                'decorators': [d.id if hasattr(d, 'id') else str(d)
                              for d in node.decorator_list]
            })
        elif isinstance(node, ast.ClassDef):
            classes.append({
                'name': node.name,
                'lineno': node.lineno,
                'bases': [base.id if hasattr(base, 'id') else str(base)
                         for base in node.bases],
                'decorators': [d.id if hasattr(d, 'id') else str(d)
                              for d in node.decorator_list]
            })

    # Return the parsed structure
    return {
        'functions': functions,
        'classes': classes,
        'imports': [],  # TODO: implement import extraction
        'globals': []   # TODO: implement global variable extraction
    }

def get_type_repr(annotation):
    """Get string representation of type annotation."""
    if annotation is None:
        return None

    # Try ast.unparse first (Python 3.9+)
    if hasattr(ast, 'unparse'):
        try:
            return ast.unparse(annotation)
        except Exception:
            pass  # Fall back to manual handling

    # Fallback for Python < 3.9 or if unparse fails
    if isinstance(annotation, ast.Name):
        return annotation.id
    elif isinstance(annotation, ast.Constant):
        return repr(annotation.value)
    elif isinstance(annotation, ast.Attribute):
        value = get_type_repr(annotation.value)
        return f"{value}.{annotation.attr}" if value else annotation.attr
    else:
        # Generic fallback
        try:
            return str(annotation)
        except:
            return None
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
            func_info = {
                'name': node.name,
                'line': node.lineno,
                'args': [],
                'return_type': get_type_repr(node.returns) if node.returns else None,
                'is_async': isinstance(node, ast.AsyncFunctionDef),
                'decorators': [get_type_repr(d) for d in node.decorator_list]
            }

            for arg in node.args.args:
                arg_info = {
                    'name': arg.arg,
                    'type': get_type_repr(arg.annotation) if arg.annotation else None
                }
                func_info['args'].append(arg_info)

            functions.append(func_info)

        elif isinstance(node, ast.ClassDef):
            class_info = {
                'name': node.name,
                'line': node.lineno,
                'bases': [],
                'methods': [],
                'decorators': [get_type_repr(d) for d in node.decorator_list]
            }

            for base in node.bases:
                base_name = get_type_repr(base)
                if base_name:
                    class_info['bases'].append(base_name)

            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    method_info = {
                        'name': item.name,
                        'line': item.lineno,
                        'is_async': isinstance(item, ast.AsyncFunctionDef),
                        'args': [arg.arg for arg in item.args.args]
                    }
                    class_info['methods'].append(method_info)

            classes.append(class_info)

    return {
        'functions': functions,
        'classes': classes,
        'imports': [node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))],
        'file': filepath,
        'lines': len(content.splitlines())
    }


@wrap_output
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
        return {
        'ok': False,
        'error': f"Failed to parse file: {parsed.get('error', 'Unknown error')}"
        }
    if isinstance(parsed, dict) and 'data' in parsed:
        parsed = parsed['data']
    
    # Additional check for None data
    if parsed is None:
        return {
            'ok': False,
            'error': 'Parse returned no data'
        }

    target_line = None
    target_type = None

    # Search in functions
    for func in parsed.get('functions', []):
        if func['name'] == target:
            target_line = func['line']
            target_type = 'function'
            break

    # Search in classes
    if target_line is None:
        for cls in parsed.get('classes', []):
            if cls['name'] == target:
                target_line = cls['line']
                target_type = 'class'
                break

            # Search in methods
            for method in cls.get('methods', []):
                if method['name'] == target or f"{cls['name']}.{method['name']}" == target:
                    target_line = method['line']
                    target_type = 'method'
                    break

    if target_line is None:
        # Try to find as a text pattern
        for i, line in enumerate(lines, 1):
            if target in line:
                target_line = i
                target_type = 'text'
                break

    if target_line is None:
        return f"Target '{target}' not found in {filepath}"

    # Calculate range (fixed 10 lines context)
# context_lines is now a parameter with default value 10
    start_line = max(1, target_line - context_lines)
    end_line = min(len(lines), target_line + context_lines)

    # Build output
    output_lines = []
    for i in range(start_line, end_line + 1):
        line_num = str(i).rjust(4)
        marker = '>>> ' if i == target_line else '    '
        output_lines.append(f"{line_num} {marker}{lines[i-1].rstrip()}")

    header = f"\n=== {filepath} - {target_type}: {target} (line {target_line}) ===\n"
    return header + '\n'.join(output_lines)


@wrap_output
def replace(
    filepath: str, 
    old_code: str, 
    new_code: str,
    fuzzy: bool = True,
    threshold: float = 0.8,
    preview: bool = False
) -> Dict[str, Any]:
    """
    Replace code in a file with improved indentation handling and fuzzy matching.

    Args:
        filepath: Path to the file
        old_code: Code to replace
        new_code: New code
        fuzzy: Enable fuzzy matching if exact match fails
        threshold: Fuzzy matching threshold (0.0 to 1.0)
        preview: If True, show preview without making changes

    Returns:
        Dict with operation status and details
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Normalize line endings
    old_code = old_code.replace('\r\n', '\n').replace('\r', '\n')
    new_code = new_code.replace('\r\n', '\n').replace('\r', '\n')

    # Remove trailing whitespace from old_code for better matching
    old_lines = old_code.split('\n')
    old_lines = [line.rstrip() for line in old_lines]
    old_code_normalized = '\n'.join(old_lines)

    # Find match
    match_found = False
    match_start = -1
    match_end = -1
    matched_text = ""

    # Try exact match first (with normalized old_code)
    if old_code_normalized in content:
        match_start = content.index(old_code_normalized)
        match_end = match_start + len(old_code_normalized)
        matched_text = old_code_normalized
        match_found = True

    # Try fuzzy match if enabled and exact match failed
    if not match_found and fuzzy:
        match_result = find_fuzzy_match(content, old_code, threshold)
        if match_result:
            match_start, match_end, matched_text = match_result
            match_found = True

    if not match_found:
        # Provide helpful error message
        lines = content.split('\n')
        snippet_lines = []
        search_pattern = old_lines[0].strip() if old_lines else ""

        for i, line in enumerate(lines):
            if search_pattern and search_pattern in line:
                start = max(0, i - 2)
                end = min(len(lines), i + 3)
                snippet_lines = lines[start:end]
                break

        error_msg = f"Pattern not found in {filepath}"
        if snippet_lines:
            error_msg += f"\nDid you mean this area?\n"
            error_msg += '\n'.join(snippet_lines)

        raise ValueError(error_msg)

    # Detect indentation of the matched block
    before_match = content[:match_start]
    lines_before = before_match.split('\n')
    if lines_before:
        last_line = lines_before[-1] if match_start > 0 else ""
        target_indent = len(last_line) - len(last_line.lstrip())
    else:
        target_indent = 0

    # If match is not at start of line, use the indentation of the current line
    if match_start > 0 and content[match_start - 1] != '\n':
        # Find the start of the current line
        line_start = content.rfind('\n', 0, match_start) + 1
        line_prefix = content[line_start:match_start]
        target_indent = len(line_prefix)

    # Adjust new code indentation
    adjusted_new_code = adjust_indentation(new_code, target_indent, preserve_relative=True)

    # Perform replacement
    new_content = content[:match_start] + adjusted_new_code + content[match_end:]

    if preview:
        # Show preview
        old_lines = matched_text.split('\n')
        new_lines = adjusted_new_code.split('\n')

        preview_text = "\n=== Preview of changes ===\n"
        preview_text += "--- Old code ---\n"
        for line in old_lines[:5]:
            preview_text += f"- {line}\n"
        if len(old_lines) > 5:
            preview_text += f"  ... ({len(old_lines) - 5} more lines)\n"

        preview_text += "\n+++ New code +++\n"
        for line in new_lines[:5]:
            preview_text += f"+ {line}\n"
        if len(new_lines) > 5:
            preview_text += f"  ... ({len(new_lines) - 5} more lines)\n"

        return {
            'preview': preview_text,
            'will_replace': True,
            'match_type': 'exact' if old_code_normalized in content else 'fuzzy'
        }

    # Verify syntax if it's a Python file
    if filepath.endswith('.py'):
        try:
            ast.parse(new_content)
        except SyntaxError as e:
            error_msg = f"Syntax error after replacement: {e}"
            error_msg += f"\nAt line {e.lineno}: {e.text}" if e.text else ""
            raise ValueError(error_msg)

    # Write the file
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)

    return {
        'status': 'success',
        'file': filepath,
        'matched': matched_text[:100] + '...' if len(matched_text) > 100 else matched_text,
        'match_type': 'exact' if old_code_normalized in content else 'fuzzy',
        'lines_changed': len(old_lines),
        'new_lines': len(adjusted_new_code.split('\n'))
    }


@wrap_output  
def insert(
    filepath: str,
    content: str,
    position: Optional[Union[int, str]] = None,
    after: bool = False,
    before: bool = False,
    auto_indent: bool = True
) -> Dict[str, Any]:
    """
    Insert content into a file at specified position with smart indentation.

    Args:
        filepath: Path to the file
        content: Content to insert
        position: Line number (int) or marker text (str) to find position
        after: Insert after the position (default: False)
        before: Insert before the position (default: True if not after)
        auto_indent: Automatically match indentation (default: True)

    Returns:
        Dict with operation status and details
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Determine insert position
    insert_line = 0

    if position is None:
        # Insert at beginning
        insert_line = 0
    elif isinstance(position, int):
        # Direct line number
        insert_line = max(0, min(position - 1, len(lines)))
        if after:
            insert_line += 1
    elif isinstance(position, str):
        # Find marker text
        found = False
        for i, line in enumerate(lines):
            if position in line:
                insert_line = i
                if after:
                    insert_line += 1
                found = True
                break

        if not found:
            # Try fuzzy match
            from difflib import SequenceMatcher
    
            # Normalize for better fuzzy matching (ignore indentation)
            norm_content = _normalize_for_fuzzy(content)
            norm_position = _normalize_for_fuzzy(position)
            best_ratio = 0
            best_line = 0

            for i, line in enumerate(lines):
                ratio = SequenceMatcher(None, position.strip(), line.strip()).ratio()
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_line = i

            if best_ratio > 0.6:  # Threshold for fuzzy match
                insert_line = best_line
                if after:
                    insert_line += 1
            else:
                raise ValueError(f"Marker text '{position}' not found in file")

    # Auto-detect indentation if enabled
    if auto_indent and insert_line > 0 and insert_line <= len(lines):
        # Use _get_indent_level for accurate indentation calculation
        file_content = '\n'.join(lines)
        indent_level = _get_indent_level(file_content, insert_line)

        # Apply indentation to content
        import textwrap
        indented_content = textwrap.indent(content.rstrip('\n'), ' ' * indent_level)

        # For Python files, verify syntax
        if filepath.endswith('.py'):
            # Test insertion
            test_lines = lines.copy()
            test_lines.insert(insert_line - 1, indented_content)
            test_content = '\n'.join(test_lines)

            try:
                compile(test_content, '<test>', 'exec')
                content = indented_content  # Use indented version if successful
            except SyntaxError as e:
                # Don't try to guess indentation - return clear error
                return {
                    'ok': False,
                    'error': f'Syntax error after insertion at line {insert_line}: {e}',
                    'suggestion': 'Check indentation level and code structure'
                }
        else:
            content = indented_content

    # Ensure content ends with newline if needed
    if not content.endswith('\n') and insert_line < len(lines):
        content += '\n'

    # Insert content
    if insert_line >= len(lines):
        # Append at end
        if lines and not lines[-1].endswith('\n'):
            lines[-1] += '\n'
        lines.append(content)
    else:
        # Insert at position
        lines.insert(insert_line, content)

    # Write back
    new_content = ''.join(lines)

    # Verify syntax for Python files
    if filepath.endswith('.py'):
        try:
            ast.parse(new_content)
        except SyntaxError as e:
            error_msg = f"Syntax error after insertion: {e}"
            error_msg += f"\nAt line {e.lineno}: {e.text}" if e.text else ""
            raise ValueError(error_msg)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)

    return {
        'status': 'success',
        'file': filepath,
        'inserted_at': insert_line + 1,  # Convert to 1-based
        'lines_added': len(content.split('\n')),
        'total_lines': len(new_content.split('\n'))
    }


@wrap_output
def delete(
    filepath: str,
    target: Union[int, str, Tuple[int, int], List[int]],
    mode: str = 'auto',
    preview: bool = False
) -> Dict[str, Any]:
    """
    Delete content from a file with multiple targeting options.

    Args:
        filepath: Path to the file
        target: What to delete - can be:
            - int: Single line number
            - str: Pattern to search and delete
            - Tuple[int, int]: Range of lines (start, end)
            - List[int]: Multiple specific lines
        mode: Deletion mode:
            - 'auto': Auto-detect based on target
            - 'line': Delete single line
            - 'lines': Delete multiple lines
            - 'range': Delete range of lines
            - 'pattern': Delete lines matching pattern
            - 'block': Delete code block (class/function)
            - 'empty': Delete empty lines
        preview: Show preview without deleting

    Returns:
        Dict with operation status and details
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    original_count = len(lines)
    lines_to_delete = set()

    # Auto-detect mode if needed
    if mode == 'auto':
        if isinstance(target, int):
            mode = 'line'
        elif isinstance(target, tuple) and len(target) == 2:
            mode = 'range'
        elif isinstance(target, list):
            mode = 'lines'
        elif isinstance(target, str):
            # Check if it's a code structure
            if any(keyword in target for keyword in ['def ', 'class ', 'async def ']):
                mode = 'block'
            else:
                mode = 'pattern'

    # Process based on mode
    if mode == 'line':
        if isinstance(target, int):
            if 1 <= target <= len(lines):
                lines_to_delete.add(target - 1)  # Convert to 0-based
            else:
                raise ValueError(f"Line {target} out of range (1-{len(lines)})")

    elif mode == 'lines':
        if isinstance(target, list):
            for line_num in target:
                if 1 <= line_num <= len(lines):
                    lines_to_delete.add(line_num - 1)

    elif mode == 'range':
        if isinstance(target, tuple) and len(target) == 2:
            start, end = target
            start = max(1, start)
            end = min(len(lines), end)
            for i in range(start - 1, end):
                lines_to_delete.add(i)

    elif mode == 'pattern':
        if isinstance(target, str):
            pattern = re.compile(target) if '*' not in target else None
            for i, line in enumerate(lines):
                if pattern:
                    if pattern.search(line):
                        lines_to_delete.add(i)
                else:
                    if target in line:
                        lines_to_delete.add(i)

    elif mode == 'block':
        if isinstance(target, str):
            # Find the start of the block
            block_start = -1
            for i, line in enumerate(lines):
                if target in line:
                    block_start = i
                    break

            if block_start >= 0:
                # Determine indentation level
                indent_level = len(lines[block_start]) - len(lines[block_start].lstrip())

                # Find the end of the block
                lines_to_delete.add(block_start)
                for i in range(block_start + 1, len(lines)):
                    line = lines[i]
                    if line.strip():  # Non-empty line
                        line_indent = len(line) - len(line.lstrip())
                        if line_indent <= indent_level:
                            break  # End of block
                    lines_to_delete.add(i)

    elif mode == 'empty':
        for i, line in enumerate(lines):
            if not line.strip():
                lines_to_delete.add(i)

    if not lines_to_delete:
        return {
            'status': 'no_match',
            'message': f"No lines matched the target: {target}"
        }

    if preview:
        preview_lines = []
        for i in sorted(lines_to_delete):
            preview_lines.append(f"Line {i + 1}: {lines[i].rstrip()}")

        return {
            'preview': True,
            'will_delete': len(lines_to_delete),
            'lines': preview_lines[:10],  # Show first 10
            'total_lines': original_count
        }

    # Create new content without deleted lines
    new_lines = [line for i, line in enumerate(lines) if i not in lines_to_delete]
    new_content = ''.join(new_lines)

    # Verify syntax for Python files
    if filepath.endswith('.py') and new_content.strip():
        try:
            ast.parse(new_content)
        except SyntaxError as e:
            error_msg = f"Syntax error after deletion: {e}"
            error_msg += f"\nAt line {e.lineno}: {e.text}" if e.text else ""
            raise ValueError(error_msg)

    # Write back
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)

    return {
        'status': 'success',
        'file': filepath,
        'deleted_lines': len(lines_to_delete),
        'original_lines': original_count,
        'remaining_lines': len(new_lines),
        'mode': mode
    }


@wrap_output
def functions(filepath: str) -> List[Dict[str, Any]]:
    """Get list of functions in a Python file."""
    parsed = parse(filepath)
    if isinstance(parsed, dict) and 'data' in parsed:
        return parsed['data'].get('functions', [])
    return parsed.get('functions', [])

@wrap_output
def classes(filepath: str) -> List[Dict[str, Any]]:
    """Get list of classes in a Python file."""
    parsed = parse(filepath)
    if isinstance(parsed, dict) and 'data' in parsed:
        return parsed['data'].get('classes', [])
    return parsed.get('classes', [])

# Export all functions
__all__ = [
    'parse',
    'view', 
    'replace',
    'insert',
    'delete',
    'functions',
    'classes'
]


# ============================================
# Improved Insert/Delete 함수 (재추가)
# ============================================