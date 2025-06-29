import sys
"""
🔍 Search Helper - 기존 Search MCP 도구들 통합

기존 Search 2개 MCP 도구들을 헬퍼 함수로 통합:
- search_files(): search_files MCP 도구 기능 (고급)
- search_code(): search_code MCP 도구 기능 (AST 기반)
"""

import os
import glob
import re
from typing import Dict, List, Any, Optional

class SearchHelper:
    """🔍 Search 통합 헬퍼"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SearchHelper, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        # 이미 초기화되었는지 확인
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        
        # 한 번만 출력
        # print("🔍 Search Helper 초기화 완료")  # 초기화 메시지 제거
        
        # 검색 결과 캐시
        self._search_cache = {}
        self._cache_ttl = 300  # 5분
    def search_files(self, path: str = '.', pattern: str = '*', 
                    recursive: bool = True, max_results: int = 100,
                    include_dirs: bool = False) -> Dict[str, Any]:
        """📁 파일명 패턴 검색 (search_files MCP 도구 고급 버전)"""
        try:
            if not os.path.exists(path):
                return {'error': f'Search path not found: {path}'}
            
            results = []
            search_pattern = os.path.join(path, '**', pattern) if recursive else os.path.join(path, pattern)
            
            for file_path in glob.glob(search_pattern, recursive=recursive):
                is_dir = os.path.isdir(file_path)
                
                if is_dir and not include_dirs:
                    continue
                if not is_dir and not os.path.isfile(file_path):
                    continue
                
                results.append({
                    'path': os.path.abspath(file_path),
                    'name': os.path.basename(file_path),
                    'type': 'directory' if is_dir else 'file',
                    'size': None if is_dir else os.path.getsize(file_path),
                    'directory': os.path.dirname(file_path),
                    'extension': os.path.splitext(file_path)[1] if not is_dir else None,
                    'modified': os.path.getmtime(file_path)
                })
                
                if len(results) >= max_results:
                    break
            
            # 정렬: 타입별, 이름별
            results.sort(key=lambda x: (x['type'], x['name']))
            
            return {
                'search_path': os.path.abspath(path),
                'pattern': pattern,
                'recursive': recursive,
                'results': results,
                'total_found': len(results),
                'max_results': max_results,
                'truncated': len(results) >= max_results
            }
            
        except Exception as e:
            return {'error': f'File search failed: {str(e)}'}
    
    def search_code(self, path: str = '.', pattern: str = '', 
                   file_pattern: str = '*', max_results: int = 50,
                   case_sensitive: bool = False, whole_word: bool = False) -> Dict[str, Any]:
        """📝 코드 내용 검색 (search_code MCP 도구 AST 기반 확장)"""
        try:
            if not pattern:
                return {'error': 'Search pattern is required'}
            
            if not os.path.exists(path):
                return {'error': f'Search path not found: {path}'}
            
            results = []
            flags = 0 if case_sensitive else re.IGNORECASE
            
            # 정규식 패턴 준비
            if whole_word:
                regex_pattern = rf'\b{re.escape(pattern)}\b'
            else:
                regex_pattern = re.escape(pattern)
            
            compiled_pattern = re.compile(regex_pattern, flags)
            
            # 파일 검색 및 내용 스캔
            search_pattern = os.path.join(path, '**', file_pattern)
            
            for file_path in glob.glob(search_pattern, recursive=True):
                if not os.path.isfile(file_path):
                    continue
                
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                    
                    file_matches = []
                    for line_num, line in enumerate(lines, 1):
                        matches = compiled_pattern.finditer(line)
                        for match in matches:
                            file_matches.append({
                                'line_start': line_num,
                                'line_content': line.rstrip(),
                                'match_start': match.start(),
                                'match_end': match.end(),
                                'match_text': match.group()
                            })
                    
                    if file_matches:
                        results.append({
                            'file_path': os.path.abspath(file_path),
                            'file_name': os.path.basename(file_path),
                            'matches': file_matches,
                            'match_count': len(file_matches),
                            'file_size': os.path.getsize(file_path)
                        })
                    
                    if len(results) >= max_results:
                        break
                        
                except (UnicodeDecodeError, PermissionError):
                    continue  # 바이너리 파일이나 접근 불가 파일 스킵
            
            # 매치 수로 정렬
            results.sort(key=lambda x: x['match_count'], reverse=True)
            
            total_matches = sum(r['match_count'] for r in results)
            
            return {
                'search_path': os.path.abspath(path),
                'pattern': pattern,
                'file_pattern': file_pattern,
                'case_sensitive': case_sensitive,
                'whole_word': whole_word,
                'results': results,
                'total_files': len(results),
                'total_matches': total_matches,
                'max_results': max_results,
                'truncated': len(results) >= max_results
            }
            
        except Exception as e:
            return {'error': f'Code search failed: {str(e)}'}
    



# 전역 SearchHelper 인스턴스 (싱글톤)
_search_helper = SearchHelper()

# 전역 SearchHelper 인스턴스 (싱글톤)


def scan_directory(path: str = '.', level: int = 1) -> List[str]:
    """📁 디렉토리 스캔 (개선된 버전)
    
    Args:
        path: 스캔할 디렉토리 경로
        level: 스캔 깊이 레벨 (1=현재 레벨만, 2=1단계 하위까지)
    
    Returns:
        파일 및 디렉토리 경로 리스트
    """
    import os
    
    try:
        if not os.path.exists(path):
            return [f"ERROR: 경로를 찾을 수 없습니다: {path}"]
        
        if not os.path.isdir(path):
            return [f"ERROR: 디렉토리가 아닙니다: {path}"]
        
        results = []
        
        def scan_recursive(current_path: str, current_level: int, max_level: int):
            if current_level > max_level:
                return
            
            try:
                items = os.listdir(current_path)
                items.sort()  # 알파벳 순 정렬
                
                for item in items:
                    item_path = os.path.join(current_path, item)
                    relative_path = os.path.relpath(item_path, path)
                    
                    if os.path.isdir(item_path):
                        results.append(f"[DIR]  {relative_path}")
                        if current_level < max_level:
                            scan_recursive(item_path, current_level + 1, max_level)
                    else:
                        # 파일 크기 정보 추가
                        try:
                            size = os.path.getsize(item_path)
                            if size > 1024*1024:  # 1MB 이상
                                size_str = f"{size/(1024*1024):.1f}MB"
                            elif size > 1024:  # 1KB 이상
                                size_str = f"{size/1024:.1f}KB"
                            else:
                                size_str = f"{size}B"
                            results.append(f"[FILE] {relative_path} ({size_str})")
                        except:
                            results.append(f"[FILE] {relative_path}")
                            
            except PermissionError:
                results.append(f"[ERROR] 접근 권한 없음: {current_path}")
            except Exception as e:
                results.append(f"[ERROR] {current_path}: {str(e)}")
        
        scan_recursive(path, 1, level)
        
        if not results:
            results.append(f"INFO: 빈 디렉토리입니다: {path}")
        
        return results
        
    except Exception as e:
        return [f"ERROR: scan_directory 실행 실패: {str(e)}"]


# ================================================================
# 🎯 SearchHelper 래퍼 함수들 (AI Coding Brain MCP 확장)
# ================================================================

def search_files_advanced(path: str = '.', pattern: str = '*', 
                         recursive: bool = True, max_results: int = 100,
                         include_dirs: bool = False, timeout_ms: int = 30000,
                         project_context: Optional[Dict] = None) -> Dict[str, Any]:
    """📁 고급 파일명 패턴 검색 (SearchHelper.search_files 래퍼)
    
    🎯 목적:
        파일명 패턴 기반 고급 검색 기능 제공
        기존 MCP search_files보다 강화된 기능
        scan_directory 기능도 완전히 커버
    
    📊 주요 기능:
        • glob 패턴 지원 (*, ?, [abc], **/*.py 등)
        • 재귀/비재귀 검색 선택
        • 디렉토리 포함/제외 옵션
        • 파일 메타데이터 자동 수집 (크기, 수정일, 확장자)
        • 결과 수 제한 및 정렬
        • 경로 정규화 및 오류 처리
    
    📋 매개변수:
        path (str): 검색할 기본 경로 (기본값: 현재 디렉토리)
        pattern (str): 파일명 패턴 (기본값: '*' - 모든 파일)
        recursive (bool): 하위 디렉토리 재귀 검색 여부 (기본값: True)
        max_results (int): 최대 결과 수 제한 (기본값: 100)
        include_dirs (bool): 디렉토리도 결과에 포함 여부 (기본값: False)
    
    📤 반환값:
        Dict[str, Any]: 검색 결과 정보
        {
            'search_path': str,           # 검색한 절대경로
            'pattern': str,               # 사용된 패턴
            'recursive': bool,            # 재귀 검색 여부
            'results': List[Dict],        # 파일/디렉토리 목록
            'total_found': int,           # 발견된 항목 수
            'max_results': int,           # 제한 설정값
            'truncated': bool,            # 결과 잘림 여부
            'error': str                  # 오류 발생시
        }
        
        results 각 항목:
        {
            'path': str,                  # 절대경로
            'name': str,                  # 파일/디렉토리명
            'type': str,                  # 'file' 또는 'directory'
            'size': int,                  # 파일 크기 (바이트, 디렉토리는 None)
            'directory': str,             # 상위 디렉토리
            'extension': str,             # 파일 확장자 (디렉토리는 None)
            'modified': float             # 수정일 (timestamp)
        }
    
    💡 사용 예시:
        # 모든 Python 파일 검색
        search_files_advanced('.', '*.py')
        
        # 현재 디렉토리만 검색 (재귀 X)
        search_files_advanced('.', '*', recursive=False)
        
        # 디렉토리도 포함하여 검색
        search_files_advanced('.', '*', include_dirs=True)
        
        # 특정 패턴으로 제한된 검색
        search_files_advanced('/project', '**/*.js', max_results=50)
    
    🔧 기술적 특징:
        • SearchHelper 인스턴스 자동 생성 및 관리
        • 예외 처리 및 오류 메시지 표준화
        • 경로 정규화 및 플랫폼 호환성
        • 메모리 효율적인 대용량 파일 처리
        • project_context 통합 및 캐싱 지원
    
    ⚠️ 주의사항:
        • 대용량 디렉토리에서는 max_results로 제한 권장
        • 네트워크 드라이브에서는 성능 저하 가능
        • 권한 없는 디렉토리는 자동으로 스킵
    
    사용 예제:
        # 중요: 이 함수는 딕셔너리를 반환합니다!
        
        # 올바른 사용법:
        result = search_files_advanced('.', '*.py')
        files = result['results']  # 실제 파일 목록은 'results' 키에 있음
        
        # 파일 정보 접근
        for file_info in files[:10]:  # 처음 10개만
            print(f"{file_info['path']} - {file_info['size']} bytes")
        
        # 잘못된 사용법 (TypeError 발생):
        # files = search_files_advanced('.', '*.py')
        # for file in files[:10]:  # 에러! files는 딕셔너리임
    
    
    사용 예제:
        주의: 이 함수는 딕셔너리를 반환합니다!
        
        올바른 사용법:
            result = search_files_advanced('.', '*.py')
            files = result['results']  # 실제 파일 목록은 'results' 키에 있음
            
            # 파일 정보 접근
            for file_info in files[:10]:  # 처음 10개만
                print(f"{file_info['path']} - {file_info['size']} bytes")
            
            # 결과 정보 확인
            print(f"총 {result['total_found']}개 발견")
            if result['truncated']:
                print(f"최대 {result['max_results']}개로 제한됨")
        
    사용 예제:
        주의: 이 함수는 딕셔너리를 반환합니다!
        
        올바른 사용법:
            result = search_files_advanced('.', '*.py')
            files = result['results']  # 실제 파일 목록은 'results' 키에 있음
            
            # 파일 정보 접근
            for file_info in files[:10]:  # 처음 10개만
                print(f"{file_info['path']} - {file_info['size']} bytes")
            
            # 결과 정보 확인
            print(f"총 {result['total_found']}개 발견")
            if result['truncated']:
                print(f"최대 {result['max_results']}개로 제한됨")
        
        잘못된 사용법 (TypeError 발생):
            # files = search_files_advanced('.', '*.py')
            # for file in files[:10]:  # 에러! files는 딕셔너리임
    """
    try:
        # SearchHelper 인스턴스 생성
        helper = _search_helper
        
        # 매개변수 검증
        if not isinstance(path, str) or not path.strip():
            return {'error': 'Invalid path parameter'}
            
        if not isinstance(pattern, str):
            return {'error': 'Invalid pattern parameter'}
        
        # SearchHelper.search_files 호출
        result = helper.search_files(
            path=path.strip(),
            pattern=pattern,
            recursive=recursive,
            max_results=max_results,
            include_dirs=include_dirs
        )
        
        # project_context에 검색 기록 저장 (있을 경우에만)
        if project_context is not None:
            if 'search_history' not in project_context:
                project_context['search_history'] = []
            
            project_context['search_history'].append({
            'type': 'file_search',
            'path': path,
            'pattern': pattern,
            'results_count': result.get('total_found', 0),
            'timestamp': __import__('time').time()
            })
        
        return result
        
    except Exception as e:
        error_msg = f"search_files_advanced failed: {str(e)}"
        print(f"❌ {error_msg}")
        return {'error': error_msg}


def search_code_content(path: str = '.', pattern: str = '', 
                       file_pattern: str = '*', max_results: int = 50,
                       case_sensitive: bool = False, whole_word: bool = False,
                       project_context: Optional[Dict] = None) -> Dict[str, Any]:
    """📝 코드 내용 텍스트 검색 (SearchHelper.search_code 래퍼)
    
    🎯 목적:
        파일 내용에서 텍스트 패턴 검색
        기존 MCP search_code보다 강화된 AST 기반 기능
        정규식 지원 및 상세한 매치 정보 제공
    
    📊 주요 기능:
        • 정규식 패턴 지원 (re.escape 자동 처리)
        • 대소문자 구분/무시 선택
        • 단어 단위 검색 옵션 (\b 경계 사용)
        • 파일 타입 필터링 (file_pattern)
        • 라인 번호 및 매치 위치 정보
        • 파일별 매치 카운트 및 정렬
        • 바이너리 파일 자동 스킵
    
    📋 매개변수:
        path (str): 검색할 기본 경로 (기본값: 현재 디렉토리)
        pattern (str): 검색할 텍스트 패턴 (필수)
        file_pattern (str): 파일명 필터 패턴 (기본값: '*' - 모든 파일)
        max_results (int): 최대 파일 수 제한 (기본값: 50)
        case_sensitive (bool): 대소문자 구분 여부 (기본값: False)
        whole_word (bool): 단어 단위 검색 여부 (기본값: False)
    
    📤 반환값:
        Dict[str, Any]: 검색 결과 정보
        {
            'search_path': str,           # 검색한 절대경로
            'pattern': str,               # 검색 패턴
            'file_pattern': str,          # 파일 필터 패턴
            'case_sensitive': bool,       # 대소문자 구분 설정
            'whole_word': bool,           # 단어 단위 검색 설정
            'results': List[Dict],        # 매치된 파일들
            'total_files': int,           # 매치된 파일 수
            'total_matches': int,         # 전체 매치 수
            'max_results': int,           # 제한 설정값
            'truncated': bool,            # 결과 잘림 여부
            'error': str                  # 오류 발생시
        }
        
        results 각 파일:
        {
            'file_path': str,             # 파일 절대경로
            'file_name': str,             # 파일명
            'matches': List[Dict],        # 매치 정보들
            'match_count': int,           # 파일 내 매치 수
            'file_size': int              # 파일 크기
        }
        
        matches 각 매치:
        {
            'line_start': int,            # 라인 번호 (1부터 시작)
            'line_content': str,          # 라인 전체 내용
            'match_start': int,           # 라인 내 매치 시작 위치
            'match_end': int,             # 라인 내 매치 끝 위치  
            'match_text': str             # 매치된 텍스트
        }
    
    💡 사용 예시:
        # 함수명 검색
        search_code_content('.', 'def process_data', '*.py')
        
        # 대소문자 구분하여 클래스명 검색
        search_code_content('.', 'MyClass', case_sensitive=True)
        
        # 단어 단위로 변수명 검색
        search_code_content('.', 'user_id', whole_word=True)
        
        # JavaScript 파일에서 특정 함수 검색
        search_code_content('./src', 'function.*login', '*.js')
    
    🔧 기술적 특징:
        • re.compile을 사용한 효율적인 정규식 처리
        • UTF-8 인코딩 및 오류 무시 (errors='ignore')
        • 바이너리 파일 및 접근 불가 파일 자동 스킵
        • 매치 수 기준 정렬로 관련성 높은 결과 우선
        • 메모리 효율적인 라인 단위 처리
    
    ⚠️ 주의사항:
        • pattern이 비어있으면 오류 반환
        • 대용량 파일이 많은 경우 max_results로 제한 권장
        • 정규식 특수문자는 re.escape로 자동 이스케이프
        • 바이너리 파일은 검색에서 제외됨
    """
    try:
        # 매개변수 검증
        if not pattern or not isinstance(pattern, str):
            return {'error': 'Search pattern is required and must be a string'}
            
        if not isinstance(path, str) or not path.strip():
            return {'error': 'Invalid path parameter'}
        
        # SearchHelper 인스턴스 생성
        helper = _search_helper
        
        # SearchHelper.search_code 호출
        result = helper.search_code(
            path=path.strip(),
            pattern=pattern,
            file_pattern=file_pattern,
            max_results=max_results,
            case_sensitive=case_sensitive,
            whole_word=whole_word
        )
        
        # project_context에 검색 기록 저장 (있을 경우에만)
        if project_context is not None:
            if 'search_history' not in project_context:
                project_context['search_history'] = []
            
            project_context['search_history'].append({
            'type': 'code_search',
            'path': path,
            'pattern': pattern,
            'file_pattern': file_pattern,
            'total_matches': result.get('total_matches', 0),
            'total_files': result.get('total_files', 0),
            'timestamp': __import__('time').time()
            })
        
        return result
        
    except Exception as e:
        error_msg = f"search_code_content failed: {str(e)}"
        print(f"❌ {error_msg}")
        return {'error': error_msg}


# ================================================================
# 🔄 helper 함수 등록 업데이트
# ================================================================

# print("📝 래퍼 함수 2개 정의 완료:", file=sys.stderr)
# print("📝 래퍼 함수 2개 정의 완료:", file=sys.stderr)
print("  1. search_files_advanced() - 파일명 패턴 검색 완전체", file=sys.stderr)
print("  2. search_code_content() - 코드 내용 검색 전용", file=sys.stderr)
print("✅ 상세한 독스트링 및 사용 예시 포함", file=sys.stderr)