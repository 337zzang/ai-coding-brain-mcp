"""Code analysis and modification helpers for ai-coding-brain-mcp project."""

import os
import ast
import re
from typing import Dict, Any, List, Optional, Union
from .wrappers import wrap_output
from .util import safe_read_file, safe_write_file

# === AST 기반 코드 분석 ===

@wrap_output
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

@wrap_output
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

@wrap_output
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
    preview: bool = False
) -> Union[bool, Dict[str, Any]]:
    """Replace code in file with fuzzy matching support.
    
    Args:
        filepath: Path to file
        old_code: Code to replace
        new_code: Replacement code
        fuzzy: Enable fuzzy matching for whitespace differences
        threshold: Similarity threshold for fuzzy matching (0-1)
        preview: If True, show preview without making changes
        
    Returns:
        bool or dict: Success status or preview information
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    
    content = safe_read_file(filepath)
    if content is None:
        raise IOError(f"Failed to read file: {filepath}")
    
    # Normalize whitespace if fuzzy matching
    if fuzzy:
        # Normalize the old_code pattern
        old_normalized = re.sub(r'\s+', ' ', old_code.strip())
        
        # Find best match in content
        lines = content.split('\n')
        best_match = None
        best_score = 0
        best_start = 0
        best_end = 0
        
        # Sliding window search
        old_lines = old_code.strip().split('\n')
        window_size = len(old_lines)
        
        for i in range(len(lines) - window_size + 1):
            window = '\n'.join(lines[i:i+window_size])
            window_normalized = re.sub(r'\s+', ' ', window.strip())
            
            # Calculate similarity
            from difflib import SequenceMatcher
            score = SequenceMatcher(None, old_normalized, window_normalized).ratio()
            
            if score > best_score and score >= threshold:
                best_score = score
                best_match = window
                best_start = i
                best_end = i + window_size
        
        if best_match:
            if preview:
                return {
                    'found': True,
                    'match': best_match,
                    'score': best_score,
                    'line_start': best_start + 1,
                    'line_end': best_end
                }
            
            # Perform replacement
            lines[best_start:best_end] = new_code.strip().split('\n')
            new_content = '\n'.join(lines)
            
            if safe_write_file(filepath, new_content):
                return True
            raise IOError(f"Failed to write file: {filepath}")
        else:
            if preview:
                return {
                    'found': False,
                    'message': f"No match found with threshold {threshold}"
                }
            raise ValueError(f"Code not found in {filepath} (best score: {best_score:.2f})")
    
    else:
        # Exact matching
        if old_code in content:
            if preview:
                count = content.count(old_code)
                return {
                    'found': True,
                    'occurrences': count
                }
            
            new_content = content.replace(old_code, new_code)
            if safe_write_file(filepath, new_content):
                return True
            raise IOError(f"Failed to write file: {filepath}")
        else:
            if preview:
                return {
                    'found': False,
                    'message': "Exact match not found"
                }
            raise ValueError(f"Code not found in {filepath}")

@wrap_output
def insert(
    filepath: str,
    content: str,
    position: Union[int, str],
    after: bool = False,
    auto_indent: bool = True
) -> bool:
    """Insert content at specified position in file.
    
    Args:
        filepath: Path to file
        content: Content to insert
        position: Line number (int) or marker text (str)
        after: If True, insert after the position
        auto_indent: Automatically match indentation
        
    Returns:
        bool: Success status
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    
    file_content = safe_read_file(filepath)
    if file_content is None:
        raise IOError(f"Failed to read file: {filepath}")
    
    lines = file_content.split('\n')
    
    # Determine insert position
    if isinstance(position, int):
        insert_line = position - 1 if not after else position
    elif isinstance(position, str):
        # Find marker text
        insert_line = None
        for i, line in enumerate(lines):
            if position in line:
                insert_line = i if not after else i + 1
                break
        
        if insert_line is None:
            raise ValueError(f"Marker '{position}' not found in {filepath}")
    else:
        raise TypeError("Position must be int or str")
    
    # Auto-indent if requested
    if auto_indent and insert_line > 0:
        prev_line = lines[insert_line - 1] if insert_line > 0 else ""
        indent = len(prev_line) - len(prev_line.lstrip())
        content_lines = content.split('\n')
        content_lines = [' ' * indent + line if line.strip() else line 
                         for line in content_lines]
        content = '\n'.join(content_lines)
    
    # Insert content
    if insert_line >= len(lines):
        lines.append(content)
    else:
        lines.insert(insert_line, content)
    
    new_content = '\n'.join(lines)
    
    if safe_write_file(filepath, new_content):
        return True
    raise IOError(f"Failed to write file: {filepath}")

@wrap_output
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
