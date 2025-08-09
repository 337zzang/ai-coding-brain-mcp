
# Part 5: 통계 함수 (캐싱 적용, 중복 제거)

@lru_cache(maxsize=32)
@_register_cache
def get_statistics(
    path: str = ".",
    include_tests: bool = False
) -> Dict[str, Any]:
    """
    코드베이스 통계 - 단일 구현, 캐싱 적용
    메모리 효율적인 라인 카운팅
    """
    stats = {
        'total_files': 0,
        'total_lines': 0,
        'py_files': 0,
        'py_lines': 0,
        'test_files': 0,
        'test_lines': 0,
        'file_types': {},
        'largest_files': []
    }

    # 표준 테스트 파일 패턴
    test_patterns = [
        'test_*.py', '*_test.py',
        'tests/', 'test/', '__tests__/'
    ]

    def is_test_file(file_path: str) -> bool:
        """표준 테스트 파일 패턴 매칭"""
        path_str = str(file_path).replace('\\', '/')

        # 디렉토리 기반 확인
        if any(f'/{pattern}' in path_str for pattern in ['tests/', 'test/', '__tests__/']):
            return True

        # 파일명 기반 확인
        filename = os.path.basename(file_path)
        return filename.startswith('test_') or filename.endswith('_test.py')

    file_sizes = []

    for file_path in search_files_generator(path, "*"):
        if is_binary_file(file_path):
            continue

        try:
            # 메모리 효율적인 라인 카운팅
            line_count = 0
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for _ in f:
                    line_count += 1

            # 통계 업데이트
            stats['total_files'] += 1
            stats['total_lines'] += line_count

            # 파일 타입별 통계
            ext = os.path.splitext(file_path)[1].lower()
            if ext not in stats['file_types']:
                stats['file_types'][ext] = {'files': 0, 'lines': 0}
            stats['file_types'][ext]['files'] += 1
            stats['file_types'][ext]['lines'] += line_count

            # Python 파일 통계
            if ext == '.py':
                stats['py_files'] += 1
                stats['py_lines'] += line_count

                # 테스트 파일 통계
                if is_test_file(file_path):
                    stats['test_files'] += 1
                    stats['test_lines'] += line_count

            # 가장 큰 파일 추적
            file_sizes.append((line_count, file_path))

        except (PermissionError, UnicodeDecodeError, IOError) as e:
            logger.debug(f"Cannot process {file_path}: {e}")
            continue

    # 가장 큰 파일 Top 10
    file_sizes.sort(reverse=True)
    stats['largest_files'] = [
        {'file': path, 'lines': lines}
        for lines, path in file_sizes[:10]
    ]

    # 테스트 제외 옵션
    if not include_tests:
        stats['py_files'] -= stats['test_files']
        stats['py_lines'] -= stats['test_lines']

    return {'ok': True, 'data': stats}

def search_imports(module_name: str, path: str = ".") -> Dict[str, Any]:
    """
    특정 모듈의 import 문을 검색
    """
    import_patterns = [
        f"^import {module_name}",
        f"^from {module_name}",
        f"import.*{module_name}",
    ]

    results = []
    for pattern in import_patterns:
        result = search_code(
            pattern=pattern,
            path=path,
            file_pattern="*.py",
            use_regex=True
        )
        if result['ok']:
            results.extend(result['data'])

    # 중복 제거
    unique_results = []
    seen = set()
    for r in results:
        key = (r['file'], r['line'])
        if key not in seen:
            seen.add(key)
            unique_results.append(r)

    return {'ok': True, 'data': unique_results}

# 최종 API 함수들
def search_function(name: str, path: str = ".", strict: bool = False) -> Dict[str, Any]:
    """함수 검색 - AST 기반"""
    results = []

    for file_path in search_files_generator(path, "*.py"):
        try:
            for func_info in _find_function_ast(file_path, name, strict):
                results.append(func_info)
        except Exception as e:
            logger.debug(f"Error processing {file_path}: {e}")
            continue

    return {'ok': True, 'data': results}

def search_class(name: str, path: str = ".", strict: bool = False) -> Dict[str, Any]:
    """클래스 검색 - AST 기반"""
    results = []

    for file_path in search_files_generator(path, "*.py"):
        try:
            for class_info in _find_class_ast(file_path, name, strict):
                results.append(class_info)
        except Exception as e:
            logger.debug(f"Error processing {file_path}: {e}")
            continue

    return {'ok': True, 'data': results}

# 캐시 정보
def get_cache_info() -> Dict[str, Any]:
    """캐시 상태 정보"""
    info = {}
    for cache in _caches:
        if hasattr(cache, 'cache_info'):
            cache_info = cache.cache_info()
            info[cache.__name__] = {
                'hits': cache_info.hits,
                'misses': cache_info.misses,
                'size': cache_info.currsize,
                'maxsize': cache_info.maxsize
            }
    return {'ok': True, 'data': info}

def clear_cache():
    """모든 캐시 클리어"""
    clear_all_caches()
    return {'ok': True, 'data': 'All caches cleared'}
