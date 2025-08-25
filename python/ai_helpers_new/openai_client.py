"""
OpenAI Web Search Client
GPT-4o-search-preview 모델을 사용한 웹 검색 클라이언트

Version: 1.0.0
Author: Claude Code
Created: 2025-08-25

실시간 웹 검색 기능을 제공하는 OpenAI 클라이언트 래퍼
"""

import os
import json
import time
from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio
import logging

logger = logging.getLogger(__name__)

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI library not installed. Web search features will be unavailable.")

from .api_response import ok, err

class OpenAIWebSearchClient:
    """
    OpenAI GPT-4o-search-preview를 사용한 웹 검색 클라이언트
    
    Features:
    - 실시간 웹 검색
    - 자동 재시도 로직
    - 토큰 사용량 추적
    - 에러 핸들링
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        OpenAI 클라이언트 초기화
        
        Args:
            api_key: OpenAI API 키 (없으면 환경 변수에서 로드)
        """
        if not OPENAI_AVAILABLE:
            self.client = None
            self.enabled = False
            logger.error("OpenAI library not available")
            return
            
        # API 키 설정
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            self.client = None
            self.enabled = False
            logger.warning("No OpenAI API key found. Set OPENAI_API_KEY environment variable.")
            return
            
        try:
            self.client = OpenAI(api_key=self.api_key)
            self.enabled = True
            self.model = os.getenv('GPT_WEB_SEARCH_MODEL', 'gpt-4o-search-preview')
            self.max_retries = int(os.getenv('WEB_SEARCH_MAX_RETRIES', '3'))
            self.timeout = int(os.getenv('WEB_SEARCH_TIMEOUT', '30'))
            
            # 통계 추적
            self.stats = {
                'total_searches': 0,
                'successful_searches': 0,
                'failed_searches': 0,
                'total_tokens': 0,
                'total_cost': 0.0
            }
            
            logger.info(f"OpenAI Web Search Client initialized with model: {self.model}")
            
        except Exception as e:
            self.client = None
            self.enabled = False
            logger.error(f"Failed to initialize OpenAI client: {str(e)}")
    
    def search(self, query: str, system_prompt: Optional[str] = None,
               temperature: float = 0.7, max_tokens: Optional[int] = None) -> Dict[str, Any]:
        """
        웹 검색 실행
        
        Args:
            query: 검색 질의
            system_prompt: 시스템 프롬프트 (선택)
            temperature: 응답 다양성 (0.0 ~ 1.0)
            max_tokens: 최대 토큰 수
            
        Returns:
            검색 결과와 메타데이터
        """
        if not self.enabled:
            return err("OpenAI Web Search is not available. Check API key and library installation.")
        
        start_time = time.time()
        
        # 메시지 구성
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": query})
        
        # 재시도 로직
        last_error = None
        for attempt in range(self.max_retries):
            try:
                # API 호출 (web search 모델은 temperature를 지원하지 않음)
                create_params = {
                    'model': self.model,
                    'messages': messages,
                    'web_search_options': {}  # 웹 검색 활성화
                }
                
                # search 모델이 아닌 경우에만 temperature와 max_tokens 추가
                if 'search' not in self.model.lower():
                    create_params['temperature'] = temperature
                    if max_tokens:
                        create_params['max_tokens'] = max_tokens
                
                completion = self.client.chat.completions.create(**create_params)
                
                # 결과 처리
                response_time = time.time() - start_time
                result = {
                    'content': completion.choices[0].message.content,
                    'model': self.model,
                    'usage': {
                        'prompt_tokens': completion.usage.prompt_tokens if completion.usage else 0,
                        'completion_tokens': completion.usage.completion_tokens if completion.usage else 0,
                        'total_tokens': completion.usage.total_tokens if completion.usage else 0
                    },
                    'response_time': response_time,
                    'timestamp': datetime.now().isoformat(),
                    'query': query[:100]  # 쿼리 일부만 저장
                }
                
                # 통계 업데이트
                self.stats['total_searches'] += 1
                self.stats['successful_searches'] += 1
                self.stats['total_tokens'] += result['usage']['total_tokens']
                
                # 비용 계산 (예상치)
                estimated_cost = self._calculate_cost(result['usage'])
                result['estimated_cost'] = estimated_cost
                self.stats['total_cost'] += estimated_cost
                
                logger.info(f"Web search completed in {response_time:.2f}s, tokens: {result['usage']['total_tokens']}")
                
                return ok(result)
                
            except Exception as e:
                last_error = e
                logger.warning(f"Web search attempt {attempt + 1} failed: {str(e)}")
                
                if attempt < self.max_retries - 1:
                    # Exponential backoff
                    wait_time = 2 ** attempt
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
        
        # 모든 재시도 실패
        self.stats['total_searches'] += 1
        self.stats['failed_searches'] += 1
        
        return err(f"Web search failed after {self.max_retries} attempts: {str(last_error)}")
    
    def search_batch(self, queries: List[str], parallel: bool = True) -> Dict[str, Any]:
        """
        여러 검색을 배치로 실행
        
        Args:
            queries: 검색 질의 리스트
            parallel: 병렬 실행 여부
            
        Returns:
            모든 검색 결과
        """
        if not self.enabled:
            return err("OpenAI Web Search is not available")
        
        results = []
        errors = []
        
        if parallel:
            # 병렬 실행 (asyncio 사용)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            async def async_search(query):
                return await asyncio.get_event_loop().run_in_executor(
                    None, self.search, query
                )
            
            async def run_parallel():
                tasks = [async_search(q) for q in queries]
                return await asyncio.gather(*tasks)
            
            try:
                batch_results = loop.run_until_complete(run_parallel())
                for i, result in enumerate(batch_results):
                    if result['ok']:
                        results.append(result['data'])
                    else:
                        errors.append({
                            'index': i,
                            'query': queries[i][:50],
                            'error': result['error']
                        })
            finally:
                loop.close()
        else:
            # 순차 실행
            for i, query in enumerate(queries):
                result = self.search(query)
                if result['ok']:
                    results.append(result['data'])
                else:
                    errors.append({
                        'index': i,
                        'query': query[:50],
                        'error': result['error']
                    })
        
        return ok({
            'results': results,
            'errors': errors,
            'success_count': len(results),
            'error_count': len(errors),
            'total': len(queries)
        })
    
    def search_with_context(self, query: str, context: str,
                           context_instruction: str = "Consider the following context:") -> Dict[str, Any]:
        """
        컨텍스트를 포함한 웹 검색
        
        Args:
            query: 검색 질의
            context: 추가 컨텍스트
            context_instruction: 컨텍스트 설명
            
        Returns:
            컨텍스트를 고려한 검색 결과
        """
        # 컨텍스트를 포함한 쿼리 구성
        full_query = f"{context_instruction}\n\n{context}\n\nNow, search for: {query}"
        
        return self.search(full_query)
    
    def _calculate_cost(self, usage: Dict[str, int]) -> float:
        """
        토큰 사용량으로 예상 비용 계산
        
        Args:
            usage: 토큰 사용량 정보
            
        Returns:
            예상 비용 (USD)
        """
        # GPT-4o pricing (예상치, 실제 가격은 변동 가능)
        input_cost_per_1k = 0.005  # $0.005 per 1K input tokens
        output_cost_per_1k = 0.015  # $0.015 per 1K output tokens
        
        input_cost = (usage.get('prompt_tokens', 0) / 1000) * input_cost_per_1k
        output_cost = (usage.get('completion_tokens', 0) / 1000) * output_cost_per_1k
        
        return round(input_cost + output_cost, 6)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        사용 통계 반환
        
        Returns:
            검색 통계 정보
        """
        if self.stats['total_searches'] > 0:
            success_rate = (self.stats['successful_searches'] / self.stats['total_searches']) * 100
            avg_tokens = self.stats['total_tokens'] / self.stats['successful_searches'] if self.stats['successful_searches'] > 0 else 0
        else:
            success_rate = 0
            avg_tokens = 0
        
        return {
            **self.stats,
            'success_rate': f"{success_rate:.1f}%",
            'average_tokens_per_search': int(avg_tokens),
            'model': self.model if self.enabled else 'N/A',
            'enabled': self.enabled
        }
    
    def reset_stats(self):
        """통계 초기화"""
        self.stats = {
            'total_searches': 0,
            'successful_searches': 0,
            'failed_searches': 0,
            'total_tokens': 0,
            'total_cost': 0.0
        }
        logger.info("OpenAI Web Search statistics reset")
    
    def is_available(self) -> bool:
        """
        웹 검색 기능 사용 가능 여부
        
        Returns:
            사용 가능하면 True
        """
        return self.enabled