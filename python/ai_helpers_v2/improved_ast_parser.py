"""
개선된 AST 파서 - 중첩 구조와 고급 기능 지원
"""
import ast
from typing import Dict, Tuple, List, Optional, Any
import os


class ImprovedASTParser(ast.NodeVisitor):
    """개선된 AST 파서 - 중첩 구조 완벽 지원"""
    
    def __init__(self, lines: List[str]):
        self.lines = lines
        self.items = {}
        self.context_stack = []  # 부모 컨텍스트 스택
        
    def visit_ClassDef(self, node: ast.ClassDef):
        self._process_node(node)
        
    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._process_node(node)
        
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self._process_node(node)
        
    def _process_node(self, node):
        # 전체 이름 생성 (부모 포함)
        full_name = self._get_full_name(node.name)
        
        # 시작/끝 위치 계산
        start_line = self._get_start_line_with_decorators(node)
        end_line = self._get_end_line(node)
        
        self.items[full_name] = (start_line, end_line)
        
        # 컨텍스트 스택에 추가하고 자식 노드 방문
        self.context_stack.append(node.name)
        self.generic_visit(node)
        self.context_stack.pop()
        
    def _get_full_name(self, name: str) -> str:
        """부모 컨텍스트를 포함한 전체 이름 생성"""
        if self.context_stack:
            return ".".join(self.context_stack + [name])
        return name
        
    def _get_start_line_with_decorators(self, node) -> int:
        """데코레이터를 포함한 실제 시작 라인"""
        if hasattr(node, 'decorator_list') and node.decorator_list:
            # 첫 번째 데코레이터의 라인 번호
            return node.decorator_list[0].lineno - 1
        return node.lineno - 1
        
    def _get_end_line(self, node) -> int:
        """노드의 끝 라인 계산"""
        # Python 3.8+에서는 end_lineno 사용 가능
        if hasattr(node, 'end_lineno') and node.end_lineno:
            return node.end_lineno - 1
        
        # 이전 버전은 들여쓰기 기반 계산
        return self._find_end_by_indent(node.lineno - 1)
        
    def _find_end_by_indent(self, start_line: int) -> int:
        """들여쓰기 기반 블록 끝 찾기"""
        if start_line >= len(self.lines):
            return start_line
            
        start_indent = len(self.lines[start_line]) - len(self.lines[start_line].lstrip())
        
        for i in range(start_line + 1, len(self.lines)):
            line = self.lines[i]
            if not line.strip() or line.strip().startswith('#'):
                continue
                
            current_indent = len(line) - len(line.lstrip())
            if current_indent <= start_indent:
                return i - 1
                
        return len(self.lines) - 1


def ez_parse_advanced(filepath: str, 
                     include_nested_functions: bool = False,
                     include_docstrings: bool = False) -> Dict[str, Dict[str, Any]]:
    """개선된 ez_parse - 중첩 구조와 추가 정보 지원"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        tree = ast.parse(content)
        lines = content.split('\n')
        
        parser = ImprovedASTParser(lines)
        parser.visit(tree)
        
        # 기본 결과
        result = {}
        for name, (start, end) in parser.items.items():
            # 중첩 함수 필터링
            if not include_nested_functions:
                # 함수 내부 함수는 제외
                parts = name.split('.')
                if len(parts) > 1 and not any(p[0].isupper() for p in parts[:-1]):
                    continue
                    
            result[name] = {
                'start': start,
                'end': end,
                'lines': end - start + 1,
                'type': _get_node_type(name)
            }
            
            # docstring 추가
            if include_docstrings:
                docstring = _extract_docstring(lines, start, end)
                if docstring:
                    result[name]['docstring'] = docstring
        
        return result
        
    except SyntaxError as e:
        print(f"⚠️ 구문 오류: {filepath} - {e}")
        return {}
    except Exception as e:
        print(f"❌ 파싱 오류: {filepath} - {e}")
        return {}


def _get_node_type(name: str) -> str:
    """이름으로부터 노드 타입 추론"""
    parts = name.split('.')
    
    # 마지막 부분이 대문자로 시작하면 클래스
    if parts[-1][0].isupper():
        return 'class'
    
    # 클래스 내부 메서드
    if len(parts) > 1 and parts[-2][0].isupper():
        return 'method'
    
    # 나머지는 함수
    return 'function'


def _extract_docstring(lines: List[str], start: int, end: int) -> Optional[str]:
    """함수/클래스의 docstring 추출"""
    # 첫 번째 비어있지 않은 줄 찾기
    for i in range(start, min(end + 1, len(lines))):
        line = lines[i].strip()
        if line and not line.startswith(('def ', 'class ', '@')):
            # docstring 시작 확인 (삼중 따옴표)
            if line.startswith('"""') or line.startswith("'''"):
                docstring_lines = []
                quote = line[:3]
                
                # 한 줄 docstring
                if line.endswith(quote) and len(line) > 6:
                    return line[3:-3].strip()
                
                # 여러 줄 docstring
                docstring_lines.append(line[3:])
                for j in range(i + 1, min(end + 1, len(lines))):
                    if lines[j].strip().endswith(quote):
                        docstring_lines.append(lines[j].strip()[:-3])
                        return '\n'.join(docstring_lines).strip()
                    docstring_lines.append(lines[j])
            break
    
    return None


# 캐시 기능 추가
_parse_cache = {}

def ez_parse_cached(filepath: str, **kwargs) -> Dict[str, Any]:
    """캐싱을 지원하는 파서"""
    # 파일 수정 시간 확인
    try:
        mtime = os.path.getmtime(filepath)
        cache_key = f"{filepath}:{mtime}:{kwargs}"
        
        if cache_key in _parse_cache:
            return _parse_cache[cache_key]
        
        result = ez_parse_advanced(filepath, **kwargs)
        _parse_cache[cache_key] = result
        return result
        
    except Exception:
        return ez_parse_advanced(filepath, **kwargs)
