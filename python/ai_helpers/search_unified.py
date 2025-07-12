"""
통합 검색 모듈 - 모든 검색 기능을 하나로 통합
중복 제거 및 성능 최적화
"""
from typing import Dict, List, Any, Optional, Union, Literal
from pathlib import Path
import fnmatch
import re
import ast
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
from .helper_result import HelperResult

# 검색 타입 정의
SearchType = Literal['files', 'code', 'symbols', 'directories']
SymbolType = Literal['class', 'function', 'method', 'variable', 'import']


class UnifiedSearch:
    """통합 검색 클래스 - 모든 검색 기능을 하나로"""
    
    def __init__(self):
        self.max_workers = min(8, os.cpu_count() or 1)
        
    def search(self, 
               path: str,
               pattern: str = "*",
               search_type: SearchType = 'files',
               symbol_type: Optional[SymbolType] = None,
               file_pattern: str = "*",
               recursive: bool = True,
               case_sensitive: bool = True,
               include_hidden: bool = False,
               context_lines: int = 2,
               max_results: int = 1000,
               regex: bool = False,
               whole_word: bool = False,
               include_details: bool = True) -> HelperResult:
        """
        통합 검색 함수 - 모든 검색을 하나의 인터페이스로
        
        Args:
            path: 검색 경로
            pattern: 검색 패턴
            search_type: 검색 타입 ('files', 'code', 'symbols', 'directories')
            symbol_type: 심볼 타입 (search_type='symbols'일 때 사용)
            file_pattern: 파일 패턴 (기본: "*")
            recursive: 재귀 검색 여부
            case_sensitive: 대소문자 구분
            include_hidden: 숨김 파일 포함
            context_lines: 컨텍스트 라인 수
            max_results: 최대 결과 수
            regex: 정규식 사용 여부
            whole_word: 전체 단어 매칭
            include_details: 상세 정보 포함
            
        Returns:
            HelperResult with search results
        """
        try:
            search_path = Path(path).resolve()
            if not search_path.exists():
                return HelperResult(False, error=f"Path not found: {path}")
            
            # 검색 타입별 처리
            if search_type == 'files':
                return self._search_files(search_path, pattern, recursive, 
                                        include_hidden, max_results, include_details)
            elif search_type == 'code':
                return self._search_code(search_path, pattern, file_pattern,
                                       regex, case_sensitive, whole_word,
                                       context_lines, max_results)
            elif search_type == 'symbols':
                if not symbol_type:
                    return HelperResult(False, error="symbol_type required for symbols search")
                return self._search_symbols(search_path, pattern, symbol_type,
                                          file_pattern, exact_match=not regex,
                                          max_results=max_results)
            elif search_type == 'directories':
                return self._scan_directory(search_path, recursive, include_hidden,
                                          max_depth=10 if recursive else 1)
            else:
                return HelperResult(False, error=f"Unknown search type: {search_type}")
                
        except Exception as e:
            return HelperResult(False, error=f"Search failed: {str(e)}")
    
    def _search_files(self, path: Path, pattern: str, recursive: bool,
                     include_hidden: bool, max_results: int,
                     include_details: bool) -> HelperResult:
        """파일 검색 구현"""
        results = []
        count = 0
        
        # 파일 패턴 처리
        if ',' in pattern:
            patterns = [p.strip() for p in pattern.split(',')]
        else:
            patterns = [pattern]
        
        # 검색 실행
        for file_path in (path.rglob('*') if recursive else path.glob('*')):
            if count >= max_results:
                break
                
            if not file_path.is_file():
                continue
                
            # 숨김 파일 필터
            if not include_hidden and file_path.name.startswith('.'):
                continue
            
            # 패턴 매칭
            matched = any(fnmatch.fnmatch(file_path.name, p) for p in patterns)
            if not matched:
                continue
            
            if include_details:
                stat = file_path.stat()
                results.append({
                    'path': str(file_path),
                    'name': file_path.name,
                    'size': stat.st_size,
                    'modified': stat.st_mtime,
                    'relative_path': str(file_path.relative_to(path))
                })
            else:
                results.append(str(file_path))
            
            count += 1
        
        return HelperResult(True, data={
            'results': results,
            'count': len(results),
            'pattern': pattern,
            'search_path': str(path)
        })
    
    def _search_code(self, path: Path, pattern: str, file_pattern: str,
                    regex: bool, case_sensitive: bool, whole_word: bool,
                    context_lines: int, max_results: int) -> HelperResult:
        """코드 검색 구현"""
        # 패턴 준비
        if whole_word and not regex:
            pattern = r'\b' + re.escape(pattern) + r'\b'
            regex = True
        
        if regex:
            flags = 0 if case_sensitive else re.IGNORECASE
            try:
                regex_pattern = re.compile(pattern, flags)
            except re.error as e:
                return HelperResult(False, error=f"Invalid regex pattern: {e}")
        
        results = []
        total_matches = 0
        
        # 파일 수집
        files_to_search = []
        if path.is_file():
            files_to_search = [path]
        else:
            # 파일 패턴 처리
            if ',' in file_pattern:
                patterns = [p.strip() for p in file_pattern.split(',')]
                for p in patterns:
                    files_to_search.extend(path.rglob(p))
            else:
                files_to_search = list(path.rglob(file_pattern))
        
        # 병렬 검색
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_file = {
                executor.submit(self._search_in_file, file_path, pattern,
                              regex_pattern if regex else None,
                              case_sensitive, context_lines): file_path
                for file_path in files_to_search
                if file_path.is_file()
            }
            
            for future in as_completed(future_to_file):
                if total_matches >= max_results:
                    break
                    
                file_result = future.result()
                if file_result and file_result['matches']:
                    results.append(file_result)
                    total_matches += len(file_result['matches'])
        
        return HelperResult(True, data={
            'results': results,
            'total_files': len(results),
            'total_matches': total_matches,
            'pattern': pattern,
            'file_pattern': file_pattern
        })
    
    def _search_in_file(self, file_path: Path, pattern: str,
                       regex_pattern: Optional[re.Pattern],
                       case_sensitive: bool, context_lines: int) -> Optional[Dict]:
        """단일 파일에서 검색"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            matches = []
            for i, line in enumerate(lines):
                found = False
                
                if regex_pattern:
                    found = bool(regex_pattern.search(line))
                else:
                    if case_sensitive:
                        found = pattern in line
                    else:
                        found = pattern.lower() in line.lower()
                
                if found:
                    # 컨텍스트 추출
                    start = max(0, i - context_lines)
                    end = min(len(lines), i + context_lines + 1)
                    
                    context = []
                    for j in range(start, end):
                        prefix = ">>>" if j == i else "   "
                        context.append(f"{prefix} {j+1:4d} | {lines[j].rstrip()}")
                    
                    matches.append({
                        'line_number': i + 1,
                        'line_content': line.strip(),
                        'context': '\n'.join(context)
                    })
            
            if matches:
                return {
                    'file_path': str(file_path),
                    'matches': matches,
                    'match_count': len(matches)
                }
            
        except Exception:
            pass
        
        return None
    
    def _search_symbols(self, path: Path, pattern: str, symbol_type: SymbolType,
                       file_pattern: str, exact_match: bool,
                       max_results: int) -> HelperResult:
        """심볼 검색 구현 (AST 기반)"""
        results = []
        
        # Python 파일만 검색
        python_files = list(path.rglob("*.py"))
        
        for file_path in python_files:
            if len(results) >= max_results:
                break
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                
                # 심볼 타입별 검색
                for node in ast.walk(tree):
                    if len(results) >= max_results:
                        break
                    
                    symbol_info = self._extract_symbol_info(node, pattern, 
                                                           symbol_type, exact_match)
                    if symbol_info:
                        symbol_info['file_path'] = str(file_path)
                        symbol_info['source'] = ast.get_source_segment(content, node)
                        results.append(symbol_info)
                        
            except Exception:
                continue
        
        return HelperResult(True, data={
            'results': results,
            'count': len(results),
            'symbol_type': symbol_type,
            'pattern': pattern
        })
    
    def _extract_symbol_info(self, node: ast.AST, pattern: str,
                           symbol_type: SymbolType, exact_match: bool) -> Optional[Dict]:
        """AST 노드에서 심볼 정보 추출"""
        if symbol_type == 'class' and isinstance(node, ast.ClassDef):
            if self._match_name(node.name, pattern, exact_match):
                return {
                    'type': 'class',
                    'name': node.name,
                    'line': node.lineno,
                    'docstring': ast.get_docstring(node)
                }
                
        elif symbol_type == 'function' and isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if self._match_name(node.name, pattern, exact_match):
                return {
                    'type': 'function',
                    'name': node.name,
                    'line': node.lineno,
                    'args': [arg.arg for arg in node.args.args],
                    'docstring': ast.get_docstring(node),
                    'async': isinstance(node, ast.AsyncFunctionDef)
                }
                
        elif symbol_type == 'import' and isinstance(node, (ast.Import, ast.ImportFrom)):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if self._match_name(alias.name, pattern, exact_match):
                        return {
                            'type': 'import',
                            'name': alias.name,
                            'line': node.lineno,
                            'alias': alias.asname
                        }
            else:
                module = node.module or ''
                if self._match_name(module, pattern, exact_match):
                    return {
                        'type': 'import_from',
                        'module': module,
                        'line': node.lineno,
                        'names': [alias.name for alias in node.names]
                    }
        
        return None
    
    def _match_name(self, name: str, pattern: str, exact_match: bool) -> bool:
        """이름 매칭"""
        if exact_match:
            return name == pattern
        else:
            return pattern.lower() in name.lower()
    
    def _scan_directory(self, path: Path, recursive: bool,
                       include_hidden: bool, max_depth: int) -> HelperResult:
        """디렉토리 스캔"""
        def scan_recursive(current_path: Path, current_depth: int) -> Dict:
            if current_depth > max_depth:
                return None
                
            result = {
                'name': current_path.name,
                'path': str(current_path),
                'type': 'directory',
                'children': []
            }
            
            try:
                for item in sorted(current_path.iterdir()):
                    # 숨김 파일 필터
                    if not include_hidden and item.name.startswith('.'):
                        continue
                    
                    if item.is_file():
                        result['children'].append({
                            'name': item.name,
                            'path': str(item),
                            'type': 'file',
                            'size': item.stat().st_size
                        })
                    elif item.is_dir() and recursive:
                        sub_dir = scan_recursive(item, current_depth + 1)
                        if sub_dir:
                            result['children'].append(sub_dir)
                            
            except PermissionError:
                pass
            
            return result
        
        tree = scan_recursive(path, 0)
        
        # 플랫 리스트도 생성
        flat_list = []
        
        def flatten(node: Dict, parent_path: str = ""):
            if node['type'] == 'file':
                flat_list.append(node['path'])
            else:
                for child in node.get('children', []):
                    flatten(child, node['path'])
        
        flatten(tree)
        
        return HelperResult(True, data={
            'tree': tree,
            'files': flat_list,
            'total_files': len(flat_list),
            'root_path': str(path)
        })


# 전역 인스턴스
_unified_search = UnifiedSearch()


# 공개 API 함수들 (간단한 인터페이스)
def search_files(path: str, pattern: str = "*", **kwargs) -> HelperResult:
    """파일 검색"""
    return _unified_search.search(path, pattern, search_type='files', **kwargs)


def search_code(path: str, pattern: str, file_pattern: str = "*", **kwargs) -> HelperResult:
    """코드 내용 검색"""
    return _unified_search.search(path, pattern, search_type='code', 
                                 file_pattern=file_pattern, **kwargs)


def find_symbol(path: str, symbol_name: str, symbol_type: SymbolType, **kwargs) -> HelperResult:
    """심볼 검색 (클래스, 함수 등)"""
    return _unified_search.search(path, symbol_name, search_type='symbols',
                                 symbol_type=symbol_type, **kwargs)


def scan_directory(path: str, **kwargs) -> HelperResult:
    """디렉토리 스캔"""
    return _unified_search.search(path, search_type='directories', **kwargs)


# 특화된 검색 함수들 (편의 함수)
def find_class(path: str, class_name: str, exact: bool = True) -> HelperResult:
    """클래스 찾기"""
    return find_symbol(path, class_name, 'class', regex=not exact)


def find_function(path: str, function_name: str, exact: bool = True) -> HelperResult:
    """함수 찾기"""
    return find_symbol(path, function_name, 'function', regex=not exact)


def find_import(path: str, module_name: str, exact: bool = False) -> HelperResult:
    """import 문 찾기"""
    return find_symbol(path, module_name, 'import', regex=not exact)


def grep(path: str, pattern: str, **kwargs) -> HelperResult:
    """grep 스타일 검색"""
    return search_code(path, pattern, regex=True, **kwargs)