"""
개선된 프로젝트 구조 스캔 함수
중요한 파일만 스캔하여 불필요한 파일(테스트, 백업, 로그 등)을 제외
"""
import os
def scan_important_files(root_path="."):
    """
    중요한 파일만 스캔하는 개선된 함수
    
    제외되는 항목:
    - 테스트 파일 (test_, _test, .test, .spec)
    - 백업 파일 (.bak, .backup, .old, backups/)
    - 임시 파일 (.tmp, .temp, ~)
    - 로그 파일 (.log, logs/)
    - 빌드/캐시 디렉토리 (dist/, node_modules/, __pycache__ 등)
    
    포함되는 항목:
    - 소스 코드 (.py, .ts, .js, .tsx, .jsx)
    - 설정 파일 (.json, .yml, .yaml, .toml, .ini)
    - 중요 문서 (.md)
    """
    import os
    
    # 제외할 디렉토리 패턴
    exclude_dirs = {
        # 빌드/배포
        'node_modules', 'dist', 'build', 'out', '.next',
        # 버전 관리
        '.git', '.svn', '.hg',
        # Python
        '__pycache__', '.pytest_cache', '.mypy_cache', '.tox', 'venv', '.venv',
        # IDE
        '.idea', '.vscode', '.vs',
        # 프로젝트 특정
        'memory\\backups', 'memory\\cache', 'memory\\logs',
        'memory/backups', 'memory/cache', 'memory/logs',
        'backups', 'backup', 'logs', 'log',
        # 테스트
        'tests', 'test', '__tests__', '.tests'
    }
    
    # 제외할 파일 패턴
    exclude_file_patterns = [
        # 테스트 파일
        'test_', '_test.', '.test.', '.spec.',
        # 백업 파일
        '.bak', '.backup', '.old', '.orig', '~',
        # 임시 파일
        '.tmp', '.temp', '.cache',
        # 로그 파일
        '.log',
        # OS 파일
        '.DS_Store', 'Thumbs.db', 'desktop.ini',
        # Python
        '.pyc', '.pyo', '.pyd'
    ]
    
    # 포함할 확장자
    include_extensions = {
        # 소스 코드
        '.py', '.ts', '.js', '.tsx', '.jsx', '.mjs', '.cjs',
        # 설정 파일
        '.json', '.yml', '.yaml', '.toml', '.ini', '.env',
        # 문서 (중요한 것만)
        '.md', '.rst'
    }
    
    # 특별히 포함할 파일명
    special_includes = {'Dockerfile', 'Makefile', 'LICENSE', 'README', '.gitignore', '.eslintrc'}
    
    result = {
        'files': [],
        'directories': [],
        'statistics': {
            'total_files': 0,
            'total_directories': 0,
            'by_extension': {},
            'excluded_files': 0,
            'excluded_dirs': 0
        }
    }
    
    root_path = os.path.abspath(root_path)
    
    for root, dirs, files in os.walk(root_path):
        # 상대 경로 계산
        rel_root = os.path.relpath(root, root_path)
        
        # 제외할 디렉토리 필터링
        original_dirs = len(dirs)
        filtered_dirs = []
        
        for d in dirs:
            # 디렉토리 제외 조건 체크
            should_exclude = False
            
            # 정확한 이름 매칭
            if d in exclude_dirs:
                should_exclude = True
            # 숨김 디렉토리 (단, .github은 포함)
            elif d.startswith('.') and d not in ['.github', '.husky']:
                should_exclude = True
            # 경로에 제외 패턴이 포함된 경우
            else:
                full_path = os.path.join(rel_root, d)
                for exc in exclude_dirs:
                    if exc in full_path.split(os.sep):
                        should_exclude = True
                        break
            
            if not should_exclude:
                filtered_dirs.append(d)
        
        dirs[:] = filtered_dirs
        result['statistics']['excluded_dirs'] += original_dirs - len(dirs)
        
        # 디렉토리 추가
        for d in dirs:
            dir_path = os.path.join(rel_root, d) if rel_root != '.' else d
            result['directories'].append(dir_path.replace('\\', '/'))
        
        # 파일 처리
        for file in files:
            file_lower = file.lower()
            
            # 제외 패턴 체크
            if any(pattern in file_lower for pattern in exclude_file_patterns):
                result['statistics']['excluded_files'] += 1
                continue
            
            # 특별 포함 파일 체크
            file_base = file.split('.')[0]
            if file in special_includes or file_base in special_includes:
                file_path = os.path.join(rel_root, file) if rel_root != '.' else file
                result['files'].append(file_path.replace('\\', '/'))
                continue
            
            # 확장자 체크
            ext = os.path.splitext(file)[1].lower()
            if ext not in include_extensions:
                result['statistics']['excluded_files'] += 1
                continue
            
            # 파일 추가
            file_path = os.path.join(rel_root, file) if rel_root != '.' else file
            result['files'].append(file_path.replace('\\', '/'))
            
            # 통계 업데이트
            if ext:
                result['statistics']['by_extension'][ext] = result['statistics']['by_extension'].get(ext, 0) + 1
    
    result['statistics']['total_files'] = len(result['files'])
    result['statistics']['total_directories'] = len(result['directories'])
    
    return result


# helpers에 추가할 메서드
def cache_important_files(self, root_path=".", force_rescan=False):
    """중요한 파일만 스캔하여 캐시하는 메서드"""
    cache_key = f"important_files_{os.path.abspath(root_path)}"
    
    # 캐시 확인
    if not force_rescan and hasattr(self, '_structure_cache'):
        if cache_key in self._structure_cache:
            return self._structure_cache[cache_key]
    
    # 스캔 실행
    result = scan_important_files(root_path)
    
    # 캐시 저장
    if not hasattr(self, '_structure_cache'):
        self._structure_cache = {}
    self._structure_cache[cache_key] = result
    
    return result
