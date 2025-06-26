"""
🔍 통합 검색 시스템 (Integrated Search System)
============================================

모든 데이터 소스를 한번에 검색하는 통합 검색 엔진
- Context Manager (메모리 캐시)
- Vibe Memory (로컬 .md 파일)
- 프로젝트 캐시 (.json 파일)
- Claude Memory (개발 경험)

작성일: 2025-06-10
"""

import os
import json
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union
from pathlib import Path


class IntegratedSearchEngine:
    """통합 검색 엔진"""
    
    def __init__(self, project_context: dict):
        self.project_context = project_context
        self.project_path = project_context.get('storage', {}).get('base_path', '.')
        self.memory_bank_path = project_context.get('memory_bank', {}).get('project_path', '')
        
        # 검색 결과 캐시 (성능 최적화)
        self._search_cache = {}
        
    def search(self, query: str, search_type: str = 'all', limit: int = 20) -> Dict[str, Any]:
        """
        통합 검색 실행
        
        Args:
            query: 검색어
            search_type: 'all', 'code', 'tasks', 'memory', 'cache'
            limit: 최대 결과 수
            
        Returns:
            통합된 검색 결과
        """
        print(f"\n🔍 통합 검색: '{query}' (타입: {search_type})")
        
        results = {
            'query': query,
            'timestamp': datetime.now().isoformat(),
            'sources': {},
            'total_results': 0
        }
        
        # 1. Context Manager 검색
        if search_type in ['all', 'code', 'cache']:
            context_results = self._search_context_manager(query)
            if context_results:
                results['sources']['context_manager'] = context_results
                results['total_results'] += len(context_results)
        
        # 2. Vibe Memory 검색
        if search_type in ['all', 'tasks', 'memory']:
            vibe_results = self._search_vibe_memory(query)
            if vibe_results:
                results['sources']['vibe_memory'] = vibe_results
                results['total_results'] += sum(len(v) for v in vibe_results.values())
        
        # 3. 프로젝트 캐시 검색
        if search_type in ['all', 'cache']:
            cache_results = self._search_project_cache(query)
            if cache_results:
                results['sources']['project_cache'] = cache_results
                results['total_results'] += len(cache_results)
        
        # 4. Claude Memory 검색
        if search_type in ['all', 'memory']:
            memory_results = self._search_claude_memory(query)
            if memory_results:
                results['sources']['claude_memory'] = memory_results
                results['total_results'] += len(memory_results)
        
        # 결과 정렬 및 제한
        results = self._rank_and_limit_results(results, limit)
        
        return results
    
    def _search_context_manager(self, query: str) -> List[Dict[str, Any]]:
        """Context Manager 캐시에서 검색"""
        results = []
        query_lower = query.lower()
        
        cache = self.project_context.get('cache', {})
        
        # 1. symbol_index 검색
        symbol_index = cache.get('symbol_index', {})
        for symbol, file_path in symbol_index.items():
            if query_lower in symbol.lower():
                results.append({
                    'type': 'symbol',
                    'name': symbol,
                    'file': file_path,
                    'source': 'symbol_index',
                    'relevance': self._calculate_relevance(query_lower, symbol.lower())
                })
        
        # 2. analyzed_files 검색
        analyzed_files = cache.get('analyzed_files', {})
        for file_path, file_data in analyzed_files.items():
            if isinstance(file_data, dict) and 'data' in file_data:
                analysis = file_data['data']
                
                # 함수 검색
                for func in analysis.get('functions', []):
                    if query_lower in func.get('name', '').lower():
                        results.append({
                            'type': 'function',
                            'name': func['name'],
                            'file': file_path,
                            'line': func.get('start_line'),
                            'source': 'analyzed_files',
                            'relevance': self._calculate_relevance(query_lower, func['name'].lower())
                        })
                
                # 클래스 검색
                for cls in analysis.get('classes', []):
                    if query_lower in cls.get('name', '').lower():
                        results.append({
                            'type': 'class',
                            'name': cls['name'],
                            'file': file_path,
                            'line': cls.get('start_line'),
                            'source': 'analyzed_files',
                            'relevance': self._calculate_relevance(query_lower, cls['name'].lower())
                        })
        
        # 3. recent_operations 검색
        recent_ops = cache.get('recent_operations', [])
        for op in recent_ops:
            if query_lower in str(op).lower():
                results.append({
                    'type': 'operation',
                    'operation': op.get('operation'),
                    'target': op.get('target'),
                    'timestamp': op.get('timestamp'),
                    'source': 'recent_operations',
                    'relevance': 0.5
                })
        
        return results
    
    def _search_vibe_memory(self, query: str) -> Dict[str, List[Dict[str, Any]]]:
        """Vibe Memory .md 파일들에서 검색"""
        results = {}
        query_lower = query.lower()
        
        if not self.memory_bank_path or not os.path.exists(self.memory_bank_path):
            return results
        
        md_files = {
            'coding_flow.md': 'tasks',
            'feature_roadmap.md': 'features',
            'project_vision.md': 'vision',
            'decision-log.md': 'decisions',
            'system-patterns.md': 'patterns'
        }
        
        for filename, category in md_files.items():
            filepath = os.path.join(self.memory_bank_path, filename)
            if os.path.exists(filepath):
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # 줄 단위로 검색
                    lines = content.splitlines()
                    matches = []
                    
                    for i, line in enumerate(lines):
                        if query_lower in line.lower():
                            # 컨텍스트 포함 (앞뒤 2줄)
                            start = max(0, i - 2)
                            end = min(len(lines), i + 3)
                            context = '\n'.join(lines[start:end])
                            
                            matches.append({
                                'line': i + 1,
                                'text': line.strip(),
                                'context': context,
                                'file': filename,
                                'relevance': self._calculate_relevance(query_lower, line.lower())
                            })
                    
                    if matches:
                        results[category] = matches
                        
                except Exception as e:
                    print(f"  ⚠️ {filename} 읽기 실패: {e}")
        
        return results
    
    def _search_project_cache(self, query: str) -> List[Dict[str, Any]]:
        """프로젝트 캐시 파일에서 검색"""
        results = []
        query_lower = query.lower()
        
        cache_dir = os.path.join(self.project_path, '.cache')
        if not os.path.exists(cache_dir):
            return results
        
        # 프로젝트 ID 기반 캐시 파일들
        project_id = self.project_context.get('project_id')
        if project_id:
            cache_files = [
                f'cache_{project_id}.json',
                f'index_{project_id}.json',
                f'session_{project_id}.json'
            ]
            
            for cache_file in cache_files:
                filepath = os.path.join(cache_dir, cache_file)
                if os.path.exists(filepath):
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        
                        # JSON 내용 검색
                        matches = self._search_json_recursive(data, query_lower, cache_file)
                        results.extend(matches)
                        
                    except Exception as e:
                        print(f"  ⚠️ {cache_file} 읽기 실패: {e}")
        
        return results
    
    def _search_claude_memory(self, query: str) -> List[Dict[str, Any]]:
        """Claude Memory (개발 경험)에서 검색"""
        results = []
        query_lower = query.lower()
        
        # project_context의 experiences 검색
        experiences = self.project_context.get('experiences', [])
        if hasattr(self.project_context, 'get'):
            experiences.extend(self.project_context.get('coding_experiences', []))
        
        for exp in experiences:
            exp_str = json.dumps(exp, ensure_ascii=False).lower()
            if query_lower in exp_str:
                results.append({
                    'type': 'experience',
                    'task': exp.get('task', 'Unknown'),
                    'category': exp.get('category'),
                    'timestamp': exp.get('timestamp'),
                    'importance': exp.get('importance', 0.5),
                    'data': exp,
                    'relevance': self._calculate_relevance(query_lower, exp_str)
                })
        
        return results
    
    def _search_json_recursive(self, obj: Any, query: str, source: str, path: str = '') -> List[Dict[str, Any]]:
        """JSON 객체를 재귀적으로 검색"""
        results = []
        
        if isinstance(obj, dict):
            for key, value in obj.items():
                new_path = f"{path}.{key}" if path else key
                
                # 키에서 검색
                if query in key.lower():
                    results.append({
                        'type': 'json_key',
                        'path': new_path,
                        'key': key,
                        'value': str(value)[:100],
                        'source': source,
                        'relevance': self._calculate_relevance(query, key.lower())
                    })
                
                # 값에서 재귀 검색
                results.extend(self._search_json_recursive(value, query, source, new_path))
                
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                new_path = f"{path}[{i}]"
                results.extend(self._search_json_recursive(item, query, source, new_path))
                
        elif isinstance(obj, str):
            if query in obj.lower():
                results.append({
                    'type': 'json_value',
                    'path': path,
                    'value': obj[:200],
                    'source': source,
                    'relevance': self._calculate_relevance(query, obj.lower())
                })
        
        return results
    
    def _calculate_relevance(self, query: str, text: str) -> float:
        """검색 관련성 점수 계산 (0~1)"""
        # 정확히 일치
        if query == text:
            return 1.0
        
        # 단어 경계에서 시작
        if text.startswith(query):
            return 0.9
        
        # 단어로 포함
        if f' {query} ' in f' {text} ':
            return 0.8
        
        # 부분 문자열로 포함
        if query in text:
            return 0.6
        
        return 0.5
    
    def _rank_and_limit_results(self, results: Dict[str, Any], limit: int) -> Dict[str, Any]:
        """결과를 관련성 순으로 정렬하고 제한"""
        # 모든 결과를 평면화하여 정렬
        all_results = []
        
        for source, source_results in results.get('sources', {}).items():
            if isinstance(source_results, list):
                for item in source_results:
                    item['_source'] = source
                    all_results.append(item)
            elif isinstance(source_results, dict):
                for category, items in source_results.items():
                    for item in items:
                        item['_source'] = f"{source}.{category}"
                        all_results.append(item)
        
        # 관련성 순으로 정렬
        all_results.sort(key=lambda x: x.get('relevance', 0), reverse=True)
        
        # 상위 N개만 유지
        results['ranked_results'] = all_results[:limit]
        
        return results


# 검색 헬퍼 함수들
def integrated_search(
    query: str, 
    search_type: str = 'all', 
    limit: int = 20,
    project_context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """통합 검색 실행
    
    Args:
        query: 검색어
        search_type: 검색 타입 ('all', 'code', 'tasks', 'memory', 'cache')
        limit: 최대 결과 수
        project_context: 프로젝트 컨텍스트 (선택적)
    
    Returns:
        검색 결과 딕셔너리
    """
    # project_context 가져오기
    if project_context is None:
        # globals에서 project_context 확인
        if 'project_context' in globals():
            project_context = globals()['project_context']
        # 또는 global_project_context라는 이름으로 저장되어 있을 수도 있음
        elif 'global_project_context' in globals():
            project_context = globals()['global_project_context']
        else:
            # project_context를 찾을 수 없는 경우 빈 딕셔너리 반환
            project_context = {}
    
    engine = IntegratedSearchEngine(project_context)
    return engine.search(query, search_type, limit)


def search_by_date(date_range: str, project_context: Optional[dict] = None) -> Dict[str, Any]:
    """
    날짜 기반 검색
    
    Args:
        date_range: 날짜 범위 문자열
            - 'today': 오늘
            - 'yesterday': 어제
            - 'last_week': 지난 주
            - 'last_month': 지난 달
            - 'YYYY-MM-DD': 특정 날짜
            - 'YYYY-MM-DD to YYYY-MM-DD': 날짜 범위
        project_context: 프로젝트 컨텍스트 (선택적)
        
    Returns:
        날짜별 검색 결과
    """
    # project_context 초기화 및 타입 보장
    if project_context is None:
        project_context = globals().get('project_context', {})
    
    # project_context가 여전히 None이거나 falsy면 빈 딕셔너리로 설정
    if not project_context:
        project_context = {}
    
    # 타입 체커를 위한 명시적 확인
    assert isinstance(project_context, dict), "project_context must be a dictionary"
    
    # 이제 project_context는 확실히 dict 타입
    
    # 날짜 범위 파싱
    end_date = datetime.now()
    start_date = end_date
    
    if date_range == 'today':
        start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
    elif date_range == 'yesterday':
        start_date = (end_date - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=1)
    elif date_range == 'last_week':
        start_date = end_date - timedelta(days=7)
    elif date_range == 'last_month':
        start_date = end_date - timedelta(days=30)
    elif ' to ' in date_range:
        # 날짜 범위 파싱
        try:
            start_str, end_str = date_range.split(' to ')
            start_date = datetime.strptime(start_str.strip(), '%Y-%m-%d')
            end_date = datetime.strptime(end_str.strip(), '%Y-%m-%d')
        except ValueError:
            return {'error': f'Invalid date range format: {date_range}'}
    else:
        # 단일 날짜
        try:
            start_date = datetime.strptime(date_range, '%Y-%m-%d')
            end_date = start_date + timedelta(days=1)
        except ValueError:
            return {'error': f'Invalid date format: {date_range}'}
    
    results = {
        'date_range': date_range,
        'start_date': start_date.isoformat(),
        'end_date': end_date.isoformat(),
        'sources': {},
        'total_results': 0
    }
    
    # 1. 작업 히스토리에서 검색
    work_history = project_context.get('cache', {}).get('work_tracking', {}).get('history', [])
    history_results = []
    
    for entry in work_history:
        entry_time = datetime.fromisoformat(entry.get('timestamp', ''))
        if start_date <= entry_time <= end_date:
            history_results.append(entry)
    
    if history_results:
        results['sources']['work_history'] = history_results
        results['total_results'] += len(history_results)
    
    # 2. 최근 작업에서 검색
    recent_ops = project_context.get('cache', {}).get('recent_operations', [])
    recent_results = []
    
    for op in recent_ops:
        op_time = datetime.fromisoformat(op.get('timestamp', ''))
        if start_date <= op_time <= end_date:
            recent_results.append(op)
    
    if recent_results:
        results['sources']['recent_operations'] = recent_results
        results['total_results'] += len(recent_results)
    
    # 3. 파일 수정 시간 기반 검색
    file_results = []
    project_path = project_context.get('path', '.')
    
    for root, dirs, files in os.walk(project_path):
        # 백업 디렉토리 제외
        if 'backup' in root or 'node_modules' in root:
            continue
            
        for file in files:
            if file.endswith(('.py', '.js', '.ts', '.json', '.md')):
                file_path = os.path.join(root, file)
                try:
                    mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                    if start_date <= mtime <= end_date:
                        file_results.append({
                            'file': os.path.relpath(file_path, project_path),
                            'modified': mtime.isoformat(),
                            'size': os.path.getsize(file_path)
                        })
                except:
                    pass
    
    if file_results:
        # 수정 시간 순으로 정렬
        file_results.sort(key=lambda x: x['modified'], reverse=True)
        results['sources']['modified_files'] = file_results
        results['total_results'] += len(file_results)
    
    return results


def search_by_file(file_pattern: str, project_context: Optional[dict] = None) -> Dict[str, Any]:
    """
    파일 패턴 기반 검색
    
    Args:
        file_pattern: 파일 패턴 문자열
            - '*.py': 모든 Python 파일
            - 'test_*.py': test로 시작하는 Python 파일
            - '**/*.js': 모든 하위 디렉토리의 JavaScript 파일
            - 'helpers.py': 특정 파일명
            - 'src/': 특정 디렉토리 내 파일들
        project_context: 프로젝트 컨텍스트 (선택적)
        
    Returns:
        파일 패턴에 매칭되는 검색 결과
    """
    # project_context 초기화 및 타입 보장
    if project_context is None:
        project_context = globals().get('project_context', {})
    
    # project_context가 여전히 None이거나 falsy면 빈 딕셔너리로 설정
    if not project_context:
        project_context = {}
    
    # 타입 체커를 위한 명시적 확인
    assert isinstance(project_context, dict), "project_context must be a dictionary"
    
    # 이제 project_context는 확실히 dict 타입
    
    project_path = project_context.get('path', '.')
    
    results = {
        'file_pattern': file_pattern,
        'timestamp': datetime.now().isoformat(),
        'sources': {},
        'total_results': 0
    }
    
    # 1. 파일 시스템에서 패턴 매칭
    import fnmatch
    file_matches = []
    
    # 디렉토리 패턴인지 확인
    is_dir_pattern = file_pattern.endswith('/') or file_pattern.endswith('\\')
    clean_pattern = file_pattern.rstrip('/\\')
    
    for root, dirs, files in os.walk(project_path):
        # 백업과 node_modules 제외
        if 'backup' in root or 'node_modules' in root or '.git' in root:
            continue
        
        rel_root = os.path.relpath(root, project_path)
        
        # 디렉토리 패턴 매칭
        if is_dir_pattern:
            if fnmatch.fnmatch(rel_root, clean_pattern) or rel_root.startswith(clean_pattern):
                # 해당 디렉토리의 모든 파일 추가
                for file in files:
                    if file.endswith(('.py', '.js', '.ts', '.json', '.md')):
                        file_path = os.path.join(root, file)
                        rel_path = os.path.relpath(file_path, project_path)
                        try:
                            file_info = {
                                'path': rel_path,
                                'name': file,
                                'directory': rel_root,
                                'size': os.path.getsize(file_path),
                                'modified': datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat(),
                                'extension': os.path.splitext(file)[1]
                            }
                            file_matches.append(file_info)
                        except:
                            pass
        else:
            # 파일 패턴 매칭
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, project_path)
                
                # 다양한 패턴 매칭 시도
                if (fnmatch.fnmatch(file, file_pattern) or 
                    fnmatch.fnmatch(rel_path, file_pattern) or
                    fnmatch.fnmatch(rel_path.replace('\\', '/'), file_pattern)):
                    try:
                        file_info = {
                            'path': rel_path,
                            'name': file,
                            'directory': rel_root,
                            'size': os.path.getsize(file_path),
                            'modified': datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat(),
                            'extension': os.path.splitext(file)[1]
                        }
                        file_matches.append(file_info)
                    except:
                        pass
    
    if file_matches:
        # 경로 길이로 정렬 (짧은 경로 우선)
        file_matches.sort(key=lambda x: (len(x['path']), x['path']))
        results['sources']['file_system'] = file_matches
        results['total_results'] += len(file_matches)
    
    # 2. 캐시된 파일 정보에서 검색
    cache = project_context.get('cache', {})
    analyzed_files = cache.get('analyzed_files', {})
    cache_matches = []
    
    for cached_path, file_data in analyzed_files.items():
        rel_path = os.path.relpath(cached_path, project_path) if os.path.isabs(cached_path) else cached_path
        
        if (fnmatch.fnmatch(os.path.basename(cached_path), file_pattern) or
            fnmatch.fnmatch(rel_path, file_pattern) or
            fnmatch.fnmatch(rel_path.replace('\\', '/'), file_pattern)):
            
            cache_info = {
                'path': rel_path,
                'cached_at': file_data.get('timestamp', 'unknown'),
                'has_analysis': 'data' in file_data
            }
            
            if isinstance(file_data, dict) and 'data' in file_data:
                analysis = file_data['data']
                cache_info.update({
                    'functions': len(analysis.get('functions', [])),
                    'classes': len(analysis.get('classes', [])),
                    'lines': analysis.get('total_lines', 0)
                })
            
            cache_matches.append(cache_info)
    
    if cache_matches:
        results['sources']['cache'] = cache_matches
        results['total_results'] += len(cache_matches)
    
    # 3. 작업 추적에서 최근 접근한 파일 검색
    work_tracking = cache.get('work_tracking', {})
    file_access = work_tracking.get('file_access', {})
    access_matches = []
    
    for accessed_file, access_info in file_access.items():
        rel_path = os.path.relpath(accessed_file, project_path) if os.path.isabs(accessed_file) else accessed_file
        
        if (fnmatch.fnmatch(os.path.basename(accessed_file), file_pattern) or
            fnmatch.fnmatch(rel_path, file_pattern) or
            fnmatch.fnmatch(rel_path.replace('\\', '/'), file_pattern)):
            
            access_matches.append({
                'path': rel_path,
                'access_count': access_info.get('count', 0),
                'last_accessed': access_info.get('last_access', 'unknown'),
                'operations': access_info.get('operations', [])
            })
    
    if access_matches:
        # 접근 횟수로 정렬
        access_matches.sort(key=lambda x: x['access_count'], reverse=True)
        results['sources']['recent_access'] = access_matches
        results['total_results'] += len(access_matches)
    
    # 4. 메타 정보 추가
    if results['total_results'] > 0:
        # 확장자별 통계
        extensions = {}
        for source_data in results['sources'].values():
            for item in source_data:
                if 'extension' in item:
                    ext = item['extension']
                    extensions[ext] = extensions.get(ext, 0) + 1
        
        results['statistics'] = {
            'by_extension': extensions,
            'unique_files': len(set(
                item['path'] for source_data in results['sources'].values() 
                for item in source_data if 'path' in item
            ))
        }
    
    return results


# 전역 등록
if __name__ != "__main__":
    print("✅ 통합 검색 시스템 로드됨")
    print("  - integrated_search(query, type='all', limit=20)")
    print("  - 타입: 'all', 'code', 'tasks', 'memory', 'cache'")
    print("  - search_by_date(date_range)")
    print("  - search_by_file(file_pattern)")
