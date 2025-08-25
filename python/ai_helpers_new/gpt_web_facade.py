"""
GPT Web Search Facade
백그라운드 처리와 캐싱을 지원하는 GPT 웹 검색 Facade

Version: 1.0.0
Author: Claude Code
Created: 2025-08-25

GPT-4o-search-preview를 활용한 실시간 웹 검색 시스템
"""

import os  # os를 파일 상단으로 이동
import json
import hashlib
from typing import Dict, Any, Optional, List, Union, Tuple
from datetime import datetime, timedelta
import threading
import time
import logging

logger = logging.getLogger(__name__)

from .openai_client import OpenAIWebSearchClient
from .api_response import ok, err
from .message import message_facade

class GPTWebSearchFacade:
    """
    GPT 웹 검색 Facade
    
    핵심 기능:
    - 실시간 웹 검색
    - 결과 캐싱
    - 병렬 검색
    - 백그라운드 처리
    - 검색 체이닝
    """
    
    def __init__(self):
        """Facade 초기화"""
        self.client = OpenAIWebSearchClient()
        self.cache = {}  # 검색 결과 캐시
        self.active_searches = {}  # 진행 중인 검색
        self.search_history = []  # 검색 히스토리
        self.cache_ttl = int(os.getenv('WEB_SEARCH_CACHE_TTL', '3600'))  # 기본 1시간
        self.max_parallel = int(os.getenv('WEB_SEARCH_MAX_PARALLEL', '5'))
        self.message = message_facade
        self._lock = threading.Lock()
        
        # 백그라운드 작업 추적
        self.background_tasks = {}
        self.task_counter = 0
        
        logger.info("GPT Web Search Facade initialized")
    
    def web_search(self, query: str, wait: bool = False,
                   use_cache: bool = True, cache_ttl: Optional[int] = None) -> Dict[str, Any]:
        """
        웹 검색 실행 (동기/비동기)
        
        Args:
            query: 검색 질의
            wait: 결과 대기 여부
            use_cache: 캐시 사용 여부
            cache_ttl: 캐시 유효 시간 (초)
            
        Returns:
            task_id 또는 검색 결과
            
        Examples:
            >>> h.ai.web_search("latest Python features", wait=True)
            >>> h.ai.web_search("React best practices")  # 비동기
        """
        # 캐시 확인
        if use_cache:
            cached = self._get_from_cache(query)
            if cached:
                self.message.info(f"Using cached result for: {query[:50]}")
                return ok(cached)
        
        # 백그라운드 작업 시작
        task_id = self._generate_task_id()
        
        def search_task():
            """백그라운드 검색 작업"""
            try:
                self.message.task(f"Web search started: {query[:50]}")
                
                # OpenAI 클라이언트로 검색
                result = self.client.search(query)
                
                if result['ok']:
                    # 캐시 저장
                    if use_cache:
                        self._save_to_cache(query, result['data'], cache_ttl or self.cache_ttl)
                    
                    # 히스토리 추가
                    self._add_to_history(query, result['data'])
                    
                    # 결과 저장
                    with self._lock:
                        self.background_tasks[task_id] = {
                            'status': 'completed',
                            'result': result['data'],
                            'query': query,
                            'timestamp': datetime.now().isoformat()
                        }
                    
                    self.message.task(f"Web search completed: {query[:50]}", level="SUCCESS")
                else:
                    with self._lock:
                        self.background_tasks[task_id] = {
                            'status': 'failed',
                            'error': result['error'],
                            'query': query,
                            'timestamp': datetime.now().isoformat()
                        }
                    
                    self.message.task(f"Web search failed: {result['error']}", level="ERROR")
                    
            except Exception as e:
                with self._lock:
                    self.background_tasks[task_id] = {
                        'status': 'failed',
                        'error': str(e),
                        'query': query,
                        'timestamp': datetime.now().isoformat()
                    }
                logger.error(f"Web search error: {str(e)}")
        
        # 백그라운드 스레드 시작
        thread = threading.Thread(target=search_task, daemon=True)
        thread.start()
        
        # 작업 등록
        with self._lock:
            self.background_tasks[task_id] = {
                'status': 'processing',
                'query': query,
                'thread': thread,
                'start_time': datetime.now().isoformat()
            }
            self.active_searches[task_id] = query
        
        if wait:
            # 동기적 대기
            return self.wait_for_search(task_id)
        else:
            # task_id 반환
            return ok({'task_id': task_id, 'query': query[:100]})
    
    def web_search_many(self, queries: List[str], use_cache: bool = True) -> Dict[str, Any]:
        """
        여러 검색을 병렬로 실행
        
        Args:
            queries: 검색 질의 리스트
            use_cache: 캐시 사용 여부
            
        Returns:
            모든 task_id 목록
            
        Examples:
            >>> h.ai.web_search_many([
            ...     "Python async programming",
            ...     "JavaScript promises",
            ...     "Go goroutines"
            ... ])
        """
        if len(queries) > self.max_parallel:
            self.message.info(f"Limiting parallel searches to {self.max_parallel}")
            queries = queries[:self.max_parallel]
        
        task_ids = []
        
        for query in queries:
            result = self.web_search(query, wait=False, use_cache=use_cache)
            if result['ok']:
                task_ids.append(result['data']['task_id'])
        
        self.message.share(f"Parallel web searches: {len(task_ids)}", task_ids)
        
        return ok({
            'task_ids': task_ids,
            'count': len(task_ids),
            'queries': [q[:50] for q in queries]
        })
    
    def web_search_chain(self, steps: List[Union[str, Tuple[str, str]]]) -> Dict[str, Any]:
        """
        연속 검색 체인 (이전 결과를 다음 검색에 활용)
        
        Args:
            steps: 검색 단계 리스트
                  - str: 단순 검색
                  - tuple: (검색어, 컨텍스트 처리 방법)
                  
        Returns:
            체인 실행 결과
            
        Examples:
            >>> h.ai.web_search_chain([
            ...     "latest AI trends",
            ...     ("analyze above", "use_previous"),
            ...     ("practical applications", "combine_all")
            ... ])
        """
        results = []
        context = ""
        
        for i, step in enumerate(steps):
            if isinstance(step, tuple):
                query, method = step
                
                if method == "use_previous" and results:
                    # 이전 결과를 컨텍스트로 사용
                    context = results[-1].get('content', '')[:1000]
                    full_query = f"Based on: {context}\n\nNow search for: {query}"
                elif method == "combine_all" and results:
                    # 모든 이전 결과 결합
                    context = "\n".join([r.get('content', '')[:500] for r in results])
                    full_query = f"Considering all previous information:\n{context}\n\nNow search for: {query}"
                else:
                    full_query = query
            else:
                full_query = step
            
            # 검색 실행
            self.message.task(f"Chain step {i+1}/{len(steps)}: {full_query[:50]}")
            
            result = self.web_search(full_query, wait=True, use_cache=False)
            if result['ok']:
                results.append(result['data'])
            else:
                return err(f"Chain failed at step {i+1}: {result['error']}")
        
        self.message.task(f"Search chain completed: {len(results)} steps", level="SUCCESS")
        
        return ok({
            'results': results,
            'steps': len(steps),
            'final_result': results[-1] if results else None
        })
    
    def wait_for_search(self, task_id: str, timeout: float = 90.0) -> Dict[str, Any]:
        """
        검색 결과 대기
        
        Args:
            task_id: 작업 ID
            timeout: 최대 대기 시간 (기본 90초로 증가)
            
        Returns:
            검색 결과
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            with self._lock:
                if task_id in self.background_tasks:
                    task = self.background_tasks[task_id]
                    
                    if task['status'] == 'completed':
                        # 정리
                        del self.active_searches[task_id]
                        return ok(task['result'])
                    elif task['status'] == 'failed':
                        # 정리
                        if task_id in self.active_searches:
                            del self.active_searches[task_id]
                        return err(task['error'])
            
            time.sleep(0.1)
        
        return err(f"Search timeout after {timeout} seconds")
    
    def gather_web_results(self, task_ids: Optional[List[str]] = None,
                          timeout: float = 120.0) -> Dict[str, Any]:
        """
        여러 검색 결과 수집
        
        Args:
            task_ids: 수집할 task_id 리스트 (None이면 모든 활성 검색)
            timeout: 최대 대기 시간
            
        Returns:
            모든 검색 결과
        """
        if task_ids is None:
            with self._lock:
                task_ids = list(self.active_searches.keys())
        
        if not task_ids:
            return err("No active searches to gather")
        
        results = []
        errors = []
        
        for task_id in task_ids:
            result = self.wait_for_search(task_id, timeout / len(task_ids))
            if result['ok']:
                results.append(result['data'])
            else:
                errors.append({
                    'task_id': task_id,
                    'error': result['error']
                })
        
        self.message.task(f"Gathered {len(results)} results, {len(errors)} errors", 
                         level="SUCCESS" if not errors else "WARNING")
        
        return ok({
            'results': results,
            'errors': errors,
            'success_count': len(results),
            'error_count': len(errors)
        })
    
    # ========== 캐싱 시스템 ==========
    
    def _generate_cache_key(self, query: str) -> str:
        """캐시 키 생성"""
        return hashlib.md5(query.encode()).hexdigest()
    
    def _get_from_cache(self, query: str) -> Optional[Dict[str, Any]]:
        """캐시에서 결과 조회"""
        cache_key = self._generate_cache_key(query)
        
        if cache_key in self.cache:
            entry = self.cache[cache_key]
            
            # TTL 확인
            if datetime.now() < entry['expires_at']:
                logger.info(f"Cache hit for query: {query[:50]}")
                return entry['data']
            else:
                # 만료된 캐시 제거
                del self.cache[cache_key]
                logger.info(f"Cache expired for query: {query[:50]}")
        
        return None
    
    def _save_to_cache(self, query: str, data: Dict[str, Any], ttl: int):
        """캐시에 결과 저장"""
        cache_key = self._generate_cache_key(query)
        
        self.cache[cache_key] = {
            'data': data,
            'query': query[:100],
            'created_at': datetime.now(),
            'expires_at': datetime.now() + timedelta(seconds=ttl),
            'ttl': ttl
        }
        
        logger.info(f"Cached result for query: {query[:50]}, TTL: {ttl}s")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """캐시 통계 반환"""
        total_entries = len(self.cache)
        valid_entries = 0
        expired_entries = 0
        
        now = datetime.now()
        for entry in self.cache.values():
            if now < entry['expires_at']:
                valid_entries += 1
            else:
                expired_entries += 1
        
        return {
            'total_entries': total_entries,
            'valid_entries': valid_entries,
            'expired_entries': expired_entries,
            'cache_size_bytes': sum(len(str(v)) for v in self.cache.values())
        }
    
    def clear_cache(self):
        """캐시 초기화"""
        self.cache.clear()
        logger.info("Web search cache cleared")
    
    # ========== 히스토리 관리 ==========
    
    def _add_to_history(self, query: str, result: Dict[str, Any]):
        """검색 히스토리 추가"""
        self.search_history.append({
            'query': query[:100],
            'timestamp': datetime.now().isoformat(),
            'tokens_used': result.get('usage', {}).get('total_tokens', 0),
            'response_time': result.get('response_time', 0)
        })
        
        # 최대 100개 유지
        if len(self.search_history) > 100:
            self.search_history = self.search_history[-100:]
    
    def get_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """검색 히스토리 조회"""
        return self.search_history[-limit:]
    
    # ========== 유틸리티 ==========
    
    def _generate_task_id(self) -> str:
        """고유 task_id 생성"""
        with self._lock:
            self.task_counter += 1
            return f"web_search_{self.task_counter}_{int(time.time() * 1000)}"
    
    def get_status(self) -> Dict[str, Any]:
        """전체 상태 반환"""
        with self._lock:
            active_count = len(self.active_searches)
            completed_count = sum(1 for t in self.background_tasks.values() 
                                if t.get('status') == 'completed')
            failed_count = sum(1 for t in self.background_tasks.values() 
                             if t.get('status') == 'failed')
        
        return ok({
            'client_available': self.client.enabled if hasattr(self.client, 'enabled') else False,
            'active_searches': active_count,
            'completed_searches': completed_count,
            'failed_searches': failed_count,
            'cache_stats': self.get_cache_stats(),
            'client_stats': self.client.stats if hasattr(self.client, 'stats') else None
        })