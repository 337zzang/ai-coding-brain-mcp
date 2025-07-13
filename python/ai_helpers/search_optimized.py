"""
최적화된 검색 모듈 - 병렬 처리 및 캐싱 적용
기존 search_unified.py의 성능 최적화 버전
"""
import os
import fnmatch
import ast
import re
from typing import Dict, List, Any, Optional, Union, Literal
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

from .helper_result import HelperResult
from .base_api import BaseAPI, OperationType, ParameterSpec, APIOperation
from .performance_optimizer import (
    with_cache, with_parallel, optimize_io_operations, 
    get_performance_optimizer, PerformanceOptimizer
)

SearchType = Literal['files', 'directories', 'both', 'code', 'symbols']


class OptimizedSearchAPI(BaseAPI):
    """최적화된 검색 API"""
    
    def __init__(self):
        super().__init__("OptimizedSearchAPI")
        self.performance_optimizer = get_performance_optimizer()
        
        # 검색 최적화 설정
        self.max_workers = 8
        self.cache_ttl = 1800  # 30분
        self.batch_size = 50
        
    def _initialize_operations(self):
        """검색 작업들 등록"""
        
        # 파일 검색
        self.register_operation(APIOperation(
            name="search_files",
            operation_type=OperationType.SEARCH,
            parameters=[
                ParameterSpec("path", str, True, None, "Search directory path"),
                ParameterSpec("pattern", str, False, "*", "File name pattern"),
                ParameterSpec("recursive", bool, False, True, "Recursive search"),
                ParameterSpec("include_hidden", bool, False, False, "Include hidden files"),
                ParameterSpec("max_depth", int, False, None, "Maximum search depth")
            ],
            description="Search for files with pattern matching",
            examples=["search_files('/path', '*.py')", "search_files('/path', '*test*', recursive=True)"]
        ))
        
        # 코드 검색
        self.register_operation(APIOperation(
            name="search_code",
            operation_type=OperationType.SEARCH,
            parameters=[
                ParameterSpec("path", str, True, None, "Search directory path"),
                ParameterSpec("pattern", str, True, None, "Code pattern to search"),
                ParameterSpec("file_pattern", str, False, "*.py", "File pattern filter"),
                ParameterSpec("case_sensitive", bool, False, False, "Case sensitive search"),
                ParameterSpec("regex", bool, False, False, "Use regex pattern")
            ],
            description="Search for code patterns in files",
            examples=["search_code('/path', 'def function_name')", "search_code('/path', 'class.*Test', regex=True)"]
        ))
        
        # 심볼 검색
        self.register_operation(APIOperation(
            name="find_symbols",
            operation_type=OperationType.SEARCH,
            parameters=[
                ParameterSpec("path", str, True, None, "Search directory path"),
                ParameterSpec("symbol_name", str, True, None, "Symbol name to find"),
                ParameterSpec("symbol_type", str, False, "all", "Symbol type (function, class, variable, all)"),
                ParameterSpec("file_pattern", str, False, "*.py", "File pattern filter")
            ],
            description="Find symbols (functions, classes, variables) in code",
            examples=["find_symbols('/path', 'MyClass')", "find_symbols('/path', 'test_*', symbol_type='function')"]
        ))
        
        # 디렉토리 스캔
        self.register_operation(APIOperation(
            name="scan_directory",
            operation_type=OperationType.READ,
            parameters=[
                ParameterSpec("path", str, True, None, "Directory path to scan"),
                ParameterSpec("include_stats", bool, False, False, "Include file statistics"),
                ParameterSpec("max_files", int, False, 1000, "Maximum files to process")
            ],
            description="Scan directory structure with optimization",
            examples=["scan_directory('/path')", "scan_directory('/path', include_stats=True)"]
        ))
    
    def _execute_core_operation(self, operation_name: str, params: Dict[str, Any]) -> Any:
        """핵심 검색 작업 실행"""
        if operation_name == "search_files":
            return self._search_files_optimized(**params)
        elif operation_name == "search_code":
            return self._search_code_optimized(**params)
        elif operation_name == "find_symbols":
            return self._find_symbols_optimized(**params)
        elif operation_name == "scan_directory":
            return self._scan_directory_optimized(**params)
        else:
            raise ValueError(f"Unknown operation: {operation_name}")
    
    @with_cache(ttl=1800)  # 30분 캐시
    def _search_files_optimized(self, path: str, pattern: str = "*", 
                               recursive: bool = True, include_hidden: bool = False,
                               max_depth: Optional[int] = None) -> Dict[str, Any]:
        """최적화된 파일 검색"""
        search_path = Path(path)
        if not search_path.exists():
            raise FileNotFoundError(f"Path not found: {path}")
        
        results = []
        total_scanned = 0
        
        def scan_directory_batch(dir_paths: List[Path]) -> List[Dict[str, Any]]:
            """디렉토리 배치 스캔"""
            batch_results = []
            for dir_path in dir_paths:
                try:
                    for item in dir_path.iterdir():
                        if item.is_file():
                            if not include_hidden and item.name.startswith('.'):
                                continue
                            
                            if fnmatch.fnmatch(item.name, pattern):
                                batch_results.append({
                                    'path': str(item),
                                    'name': item.name,
                                    'size': item.stat().st_size,
                                    'modified': item.stat().st_mtime,
                                    'type': 'file'
                                })
                except (PermissionError, OSError):
                    continue
            
            return batch_results
        
        # 병렬 처리를 위한 디렉토리 수집
        directories_to_scan = [search_path]
        
        if recursive:
            for root, dirs, files in os.walk(path):
                if max_depth and root.count(os.sep) - path.count(os.sep) >= max_depth:
                    dirs.clear()
                    continue
                
                directories_to_scan.extend([Path(root) / d for d in dirs])
                total_scanned += len(files)
                
                if total_scanned > 10000:  # 너무 많은 파일 방지
                    break
        
        # 병렬 처리
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 디렉토리를 배치로 나누기
            batch_size = max(1, len(directories_to_scan) // self.max_workers)
            futures = []
            
            for i in range(0, len(directories_to_scan), batch_size):
                batch = directories_to_scan[i:i + batch_size]
                future = executor.submit(scan_directory_batch, batch)
                futures.append(future)
            
            # 결과 수집
            for future in as_completed(futures):
                try:
                    batch_results = future.result()
                    results.extend(batch_results)
                except Exception as e:
                    self.logger.warning(f"Batch processing error: {e}")
        
        return {
            'results': results,
            'total_found': len(results),
            'total_scanned': total_scanned,
            'search_pattern': pattern,
            'search_path': path,
            'recursive': recursive
        }
    
    @with_cache(ttl=900)  # 15분 캐시
    def _search_code_optimized(self, path: str, pattern: str, 
                              file_pattern: str = "*.py", case_sensitive: bool = False,
                              regex: bool = False) -> Dict[str, Any]:
        """최적화된 코드 검색"""
        search_path = Path(path)
        if not search_path.exists():
            raise FileNotFoundError(f"Path not found: {path}")
        
        # 검색할 파일 목록 구성
        files_to_search = []
        for file_path in search_path.rglob(file_pattern):
            if file_path.is_file() and file_path.stat().st_size < 10 * 1024 * 1024:  # 10MB 제한
                files_to_search.append(file_path)
        
        def search_file_batch(file_paths: List[Path]) -> List[Dict[str, Any]]:
            """파일 배치 검색"""
            batch_results = []
            
            for file_path in file_paths:
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    # 패턴 매칭
                    if regex:
                        import re
                        flags = 0 if case_sensitive else re.IGNORECASE
                        matches = list(re.finditer(pattern, content, flags))
                    else:
                        if not case_sensitive:
                            content_lower = content.lower()
                            pattern_lower = pattern.lower()
                            matches = []
                            start = 0
                            while True:
                                pos = content_lower.find(pattern_lower, start)
                                if pos == -1:
                                    break
                                matches.append(type('Match', (), {'start': lambda: pos, 'end': lambda: pos + len(pattern)})())
                                start = pos + 1
                        else:
                            matches = []
                            start = 0
                            while True:
                                pos = content.find(pattern, start)
                                if pos == -1:
                                    break
                                matches.append(type('Match', (), {'start': lambda: pos, 'end': lambda: pos + len(pattern)})())
                                start = pos + 1
                    
                    if matches:
                        lines = content.split('\n')
                        file_matches = []
                        
                        for match in matches:
                            # 라인 번호 찾기
                            line_start = content.rfind('\n', 0, match.start()) + 1
                            line_num = content.count('\n', 0, match.start()) + 1
                            line_end = content.find('\n', match.start())
                            if line_end == -1:
                                line_end = len(content)
                            
                            line_content = content[line_start:line_end]
                            
                            file_matches.append({
                                'line_number': line_num,
                                'line_content': line_content.strip(),
                                'match_start': match.start() - line_start,
                                'match_end': match.end() - line_start
                            })
                        
                        batch_results.append({
                            'file_path': str(file_path),
                            'matches': file_matches,
                            'match_count': len(file_matches)
                        })
                
                except (UnicodeDecodeError, PermissionError, OSError) as e:
                    continue
            
            return batch_results
        
        # 병렬 처리
        results = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            batch_size = max(1, len(files_to_search) // self.max_workers)
            futures = []
            
            for i in range(0, len(files_to_search), batch_size):
                batch = files_to_search[i:i + batch_size]
                future = executor.submit(search_file_batch, batch)
                futures.append(future)
            
            for future in as_completed(futures):
                try:
                    batch_results = future.result()
                    results.extend(batch_results)
                except Exception as e:
                    self.logger.warning(f"Code search batch error: {e}")
        
        total_matches = sum(r['match_count'] for r in results)
        
        return {
            'results': results,
            'total_files_with_matches': len(results),
            'total_matches': total_matches,
            'files_searched': len(files_to_search),
            'search_pattern': pattern,
            'file_pattern': file_pattern,
            'case_sensitive': case_sensitive,
            'regex': regex
        }
    
    @with_cache(ttl=1800)  # 30분 캐시
    def _find_symbols_optimized(self, path: str, symbol_name: str, 
                               symbol_type: str = "all", file_pattern: str = "*.py") -> Dict[str, Any]:
        """최적화된 심볼 검색"""
        search_path = Path(path)
        if not search_path.exists():
            raise FileNotFoundError(f"Path not found: {path}")
        
        # Python 파일만 대상
        python_files = list(search_path.rglob(file_pattern))
        
        def analyze_file_batch(file_paths: List[Path]) -> List[Dict[str, Any]]:
            """파일 배치 분석"""
            batch_results = []
            
            for file_path in file_paths:
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    # AST 파싱
                    tree = ast.parse(content)
                    symbols = []
                    
                    for node in ast.walk(tree):
                        symbol_info = None
                        
                        if isinstance(node, ast.FunctionDef) and (symbol_type in ['all', 'function']):
                            if fnmatch.fnmatch(node.name, symbol_name):
                                symbol_info = {
                                    'name': node.name,
                                    'type': 'function',
                                    'line_number': node.lineno,
                                    'args': [arg.arg for arg in node.args.args] if hasattr(node.args, 'args') else []
                                }
                        
                        elif isinstance(node, ast.ClassDef) and (symbol_type in ['all', 'class']):
                            if fnmatch.fnmatch(node.name, symbol_name):
                                symbol_info = {
                                    'name': node.name,
                                    'type': 'class',
                                    'line_number': node.lineno,
                                    'bases': [ast.unparse(base) if hasattr(ast, 'unparse') else str(base) 
                                            for base in node.bases]
                                }
                        
                        elif isinstance(node, ast.Assign) and (symbol_type in ['all', 'variable']):
                            for target in node.targets:
                                if isinstance(target, ast.Name) and fnmatch.fnmatch(target.id, symbol_name):
                                    symbol_info = {
                                        'name': target.id,
                                        'type': 'variable',
                                        'line_number': node.lineno,
                                        'value': ast.unparse(node.value) if hasattr(ast, 'unparse') else str(node.value)
                                    }
                        
                        if symbol_info:
                            symbols.append(symbol_info)
                    
                    if symbols:
                        batch_results.append({
                            'file_path': str(file_path),
                            'symbols': symbols,
                            'symbol_count': len(symbols)
                        })
                
                except (SyntaxError, UnicodeDecodeError, PermissionError, OSError):
                    continue
            
            return batch_results
        
        # 병렬 처리
        results = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            batch_size = max(1, len(python_files) // self.max_workers)
            futures = []
            
            for i in range(0, len(python_files), batch_size):
                batch = python_files[i:i + batch_size]
                future = executor.submit(analyze_file_batch, batch)
                futures.append(future)
            
            for future in as_completed(futures):
                try:
                    batch_results = future.result()
                    results.extend(batch_results)
                except Exception as e:
                    self.logger.warning(f"Symbol search batch error: {e}")
        
        total_symbols = sum(r['symbol_count'] for r in results)
        
        return {
            'results': results,
            'total_files_with_symbols': len(results),
            'total_symbols_found': total_symbols,
            'files_analyzed': len(python_files),
            'symbol_name': symbol_name,
            'symbol_type': symbol_type,
            'file_pattern': file_pattern
        }
    
    @with_cache(ttl=600)  # 10분 캐시
    def _scan_directory_optimized(self, path: str, include_stats: bool = False, 
                                 max_files: int = 1000) -> Dict[str, Any]:
        """최적화된 디렉토리 스캔"""
        search_path = Path(path)
        if not search_path.exists():
            raise FileNotFoundError(f"Path not found: {path}")
        
        files = []
        directories = []
        stats = {
            'total_size': 0,
            'file_count': 0,
            'directory_count': 0,
            'largest_file': None,
            'newest_file': None
        }
        
        def scan_batch(items: List[Path]) -> Dict[str, Any]:
            """항목 배치 스캔"""
            batch_files = []
            batch_dirs = []
            batch_stats = {
                'total_size': 0,
                'file_count': 0,
                'directory_count': 0,
                'largest_file': None,
                'newest_file': None
            }
            
            for item in items:
                try:
                    if item.is_file():
                        stat_info = item.stat()
                        file_info = {
                            'path': str(item),
                            'name': item.name,
                            'size': stat_info.st_size,
                            'modified': stat_info.st_mtime,
                            'type': 'file'
                        }
                        
                        if include_stats:
                            file_info.update({
                                'extension': item.suffix,
                                'is_hidden': item.name.startswith('.'),
                                'permissions': oct(stat_info.st_mode)[-3:]
                            })
                        
                        batch_files.append(file_info)
                        batch_stats['file_count'] += 1
                        batch_stats['total_size'] += stat_info.st_size
                        
                        # 최대 파일 크기 추적
                        if (batch_stats['largest_file'] is None or 
                            stat_info.st_size > batch_stats['largest_file']['size']):
                            batch_stats['largest_file'] = file_info
                        
                        # 최신 파일 추적
                        if (batch_stats['newest_file'] is None or 
                            stat_info.st_mtime > batch_stats['newest_file']['modified']):
                            batch_stats['newest_file'] = file_info
                    
                    elif item.is_dir():
                        dir_info = {
                            'path': str(item),
                            'name': item.name,
                            'type': 'directory'
                        }
                        
                        if include_stats:
                            try:
                                child_count = len(list(item.iterdir()))
                                dir_info['child_count'] = child_count
                            except PermissionError:
                                dir_info['child_count'] = 0
                        
                        batch_dirs.append(dir_info)
                        batch_stats['directory_count'] += 1
                
                except (PermissionError, OSError):
                    continue
            
            return {
                'files': batch_files,
                'directories': batch_dirs,
                'stats': batch_stats
            }
        
        # 항목 수집
        try:
            items = list(search_path.iterdir())
            if len(items) > max_files:
                items = items[:max_files]
        except PermissionError:
            items = []
        
        # 병렬 처리
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            batch_size = max(1, len(items) // self.max_workers)
            futures = []
            
            for i in range(0, len(items), batch_size):
                batch = items[i:i + batch_size]
                future = executor.submit(scan_batch, batch)
                futures.append(future)
            
            for future in as_completed(futures):
                try:
                    batch_result = future.result()
                    files.extend(batch_result['files'])
                    directories.extend(batch_result['directories'])
                    
                    # 통계 병합
                    batch_stats = batch_result['stats']
                    stats['total_size'] += batch_stats['total_size']
                    stats['file_count'] += batch_stats['file_count']
                    stats['directory_count'] += batch_stats['directory_count']
                    
                    if batch_stats['largest_file']:
                        if (stats['largest_file'] is None or 
                            batch_stats['largest_file']['size'] > stats['largest_file']['size']):
                            stats['largest_file'] = batch_stats['largest_file']
                    
                    if batch_stats['newest_file']:
                        if (stats['newest_file'] is None or 
                            batch_stats['newest_file']['modified'] > stats['newest_file']['modified']):
                            stats['newest_file'] = batch_stats['newest_file']
                
                except Exception as e:
                    self.logger.warning(f"Directory scan batch error: {e}")
        
        result = {
            'files': files,
            'directories': directories,
            'path': path,
            'scanned_items': len(items)
        }
        
        if include_stats:
            result['statistics'] = stats
        
        return result


# 전역 최적화된 검색 API 인스턴스
_optimized_search_api = OptimizedSearchAPI()


# 기존 인터페이스 호환 함수들
def search_files(path: str, pattern: str = "*", recursive: bool = True, 
                include_details: bool = False, max_files: Optional[int] = None) -> HelperResult:
    """최적화된 파일 검색"""
    return _optimized_search_api.execute_operation(
        "search_files", 
        path=path, 
        pattern=pattern, 
        recursive=recursive
    )


def search_code(path: str, pattern: str, file_pattern: str = "*.py", 
               case_sensitive: bool = False) -> HelperResult:
    """최적화된 코드 검색"""
    return _optimized_search_api.execute_operation(
        "search_code",
        path=path,
        pattern=pattern,
        file_pattern=file_pattern,
        case_sensitive=case_sensitive
    )


def find_symbol(path: str, symbol_name: str, symbol_type: str = "all") -> HelperResult:
    """최적화된 심볼 검색"""
    return _optimized_search_api.execute_operation(
        "find_symbols",
        path=path,
        symbol_name=symbol_name,
        symbol_type=symbol_type
    )


def scan_directory(path: str, include_stats: bool = False) -> HelperResult:
    """최적화된 디렉토리 스캔"""
    return _optimized_search_api.execute_operation(
        "scan_directory",
        path=path,
        include_stats=include_stats
    )


def get_search_performance_report() -> Dict[str, Any]:
    """검색 성능 리포트"""
    return _optimized_search_api.get_metrics()


# 별칭 함수들 (하위 호환성)
find_class = find_symbol
find_function = find_symbol
find_import = lambda path, import_name: search_code(path, f"import.*{import_name}")
grep = search_code
search_files_advanced = search_files
search_code_content = search_code