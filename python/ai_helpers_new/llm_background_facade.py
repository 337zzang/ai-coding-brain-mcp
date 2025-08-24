"""
LLM + Background 통합 Facade
AI 작업과 병렬 처리를 결합한 강력한 워크플로우

Version: 1.0.0
Author: Claude Code
Created: 2025-08-24

LLM 작업을 백그라운드 시스템과 통합하여 극대화된 AI 워크플로우 제공
"""

from typing import Dict, Any, Optional, List, Callable, Union
import time
from datetime import datetime
from .background_facade import BackgroundFacade
from .message import message_facade
from .api_response import ok, err
from .llm import (
    ask_o3_async, 
    check_o3_status, 
    get_o3_result,
    ask_o3_practical,
    O3ContextBuilder
)

class LLMBackgroundFacade(BackgroundFacade):
    """
    LLM과 백그라운드 처리를 통합한 강력한 AI Facade
    
    핵심 기능:
    - 병렬 LLM 질의: 여러 질문을 동시에 처리
    - 컨텍스트 체이닝: 이전 답변을 다음 질문에 활용
    - 결과 캐싱: LLM 응답을 영속 변수로 저장
    - AI 파이프라인: 여러 단계의 AI 처리 자동화
    """
    
    def __init__(self):
        super().__init__()
        self.llm_cache = {}  # LLM 결과 캐시
        self.active_llm_tasks = {}  # 활성 LLM 작업 추적
    
    # ========== LLM 병렬 처리 ==========
    
    def ask(self, question: str, context: Optional[str] = None, 
            reasoning: str = "auto", wait: bool = False) -> Dict[str, Any]:
        """
        LLM에 질문 (비동기 또는 동기)
        
        Args:
            question: 질문 내용
            context: 추가 컨텍스트
            reasoning: 추론 강도 (low/medium/high/auto) - auto는 자동 결정
            wait: True면 결과 대기, False면 즉시 반환
        
        Examples:
            >>> h.ai.ask("코드 분석해줘", context=code, wait=True)
            >>> h.ai.ask("버그 찾아줘")  # 자동으로 적절한 레벨 선택
            >>> h.ai.ask("보안 취약점 분석", reasoning="high")  # 명시적 high
        """
        # reasoning이 auto면 자동 결정
        if reasoning == "auto":
            from .llm import determine_reasoning_effort
            reasoning = determine_reasoning_effort(question, context)
        # 비동기 시작
        result = ask_o3_async(question, context, reasoning)
        if not result['ok']:
            return result
        
        task_id = result['data']
        self.active_llm_tasks[task_id] = {
            'question': question[:100],
            'start_time': datetime.now()
        }
        
        self.message.task(f"LLM 작업 시작: {task_id}")
        
        if wait:
            # 동기적 대기
            return self.wait_llm(task_id)
        else:
            # task_id만 반환
            return ok({'task_id': task_id})
    
    def ask_many(self, questions: List[Union[str, tuple]]) -> Dict[str, Any]:
        """
        여러 질문을 병렬로 처리
        
        Args:
            questions: 질문 리스트 또는 (질문, 컨텍스트) 튜플 리스트
        
        Examples:
            >>> h.ai.ask_many([
            ...     "코드 최적화 방법",
            ...     ("버그 수정", error_context),
            ...     ("테스트 작성", code_context)
            ... ])
            >>> h.ai.gather_llm()  # 모든 결과 수집
        """
        task_ids = []
        
        for i, q in enumerate(questions):
            if isinstance(q, tuple):
                question = q[0]
                context = q[1] if len(q) > 1 else None
                reasoning = q[2] if len(q) > 2 else "medium"
            else:
                question = q
                context = None
                reasoning = "medium"
            
            result = ask_o3_async(question, context, reasoning)
            if result['ok']:
                task_id = result['data']
                task_ids.append(task_id)
                self.active_llm_tasks[task_id] = {
                    'question': question[:50],
                    'index': i
                }
        
        self.persistent_vars['llm_batch_tasks'] = task_ids
        self.message.share(f"LLM 배치: {len(task_ids)}개 질문", task_ids)
        
        return ok({
            'task_ids': task_ids,
            'count': len(task_ids)
        })
    
    def gather_llm(self, timeout: float = 60.0) -> Dict[str, Any]:
        """
        모든 LLM 작업 결과 수집
        
        Returns:
            {'ok': True, 'data': [results...]}
        """
        if 'llm_batch_tasks' not in self.persistent_vars:
            return err("활성 LLM 배치 없음")
        
        task_ids = self.persistent_vars['llm_batch_tasks']
        results = []
        
        for task_id in task_ids:
            result = self.wait_llm(task_id, timeout/len(task_ids))
            if result['ok']:
                results.append(result['data'])
        
        self.message.task(f"LLM 결과 수집 완료: {len(results)}개", level="SUCCESS")
        return ok(results)
    
    # ========== LLM 체이닝 ==========
    
    def llm_chain(self, *steps) -> Dict[str, Any]:
        """
        LLM 작업 체인 (이전 답변을 다음 질문의 컨텍스트로 사용)
        
        Args:
            steps: (name, question) 또는 (name, question_func) 튜플들
        
        Examples:
            >>> h.ai.llm_chain(
            ...     ("analyze", "이 코드의 문제점을 찾아줘"),
            ...     ("fix", lambda prev: f"이 문제를 수정해줘: {prev}"),
            ...     ("test", lambda prev: f"수정된 코드에 대한 테스트 작성: {prev}")
            ... )
        """
        import uuid
        chain_id = f"llm_chain_{uuid.uuid4().hex[:6]}"
        
        def run_chain():
            context = None
            results = []
            
            for i, step in enumerate(steps):
                if len(step) >= 2:
                    name, question = step[:2]
                else:
                    name = f"step_{i}"
                    question = step[0]
                
                # 함수인 경우 이전 결과로 질문 생성
                if callable(question):
                    if results:
                        question = question(results[-1])
                    else:
                        question = question(None)
                
                self.message.task(f"LLM 체인 {chain_id}: {name}")
                
                # LLM 호출 (동기적)
                if context:
                    result = ask_o3_practical(question, context)
                else:
                    result = ask_o3_practical(question)
                
                if result['ok']:
                    answer = result['data'].get('answer', '')
                    results.append(answer)
                    context = answer  # 다음 단계의 컨텍스트로 사용
                else:
                    break
            
            return results
        
        # 백그라운드로 실행
        self.manager.register_task(chain_id, run_chain)
        self.manager.run_async(chain_id)
        
        return ok({'chain_id': chain_id, 'steps': len(steps)})
    
    # ========== 실용적 헬퍼 ==========
    
    def analyze_code(self, file_path: str, question: Optional[str] = None) -> Dict[str, Any]:
        """
        코드 파일 분석 (백그라운드)
        
        Examples:
            >>> h.ai.analyze_code("main.py", "성능 최적화 방법")
            >>> h.ai.analyze_code("module.py")  # 일반 분석
        """
        # 파일 읽기
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
        except Exception as e:
            return err(f"파일 읽기 실패: {e}")
        
        if not question:
            question = f"""이 코드를 분석해주세요:
1. 주요 기능과 목적
2. 잠재적 문제점
3. 개선 제안"""
        
        context = f"=== {file_path} ===\n{code[:2000]}"  # 처음 2000자만
        
        # 분석 작업은 기본적으로 auto(자동 판단)
        return self.ask(question, context, reasoning="auto")
    
    def fix_error(self, error_msg: str, file_path: Optional[str] = None, 
                  line_num: Optional[int] = None) -> Dict[str, Any]:
        """
        에러 수정 제안 (실용적)
        
        Examples:
            >>> h.ai.fix_error("TypeError: 'NoneType' object is not iterable", 
            ...                "utils.py", 42)
        """
        builder = O3ContextBuilder()
        
        if file_path:
            builder.add_file(file_path, max_lines=50)
        
        builder.add_error(error_msg, file_path, line_num or 0)
        
        question = "이 에러를 수정하는 간단한 코드를 제공해주세요."
        
        # 백그라운드로 실행
        def fix_task():
            return builder.ask(question, practical=True)
        
        import uuid
        task_id = f"fix_{uuid.uuid4().hex[:6]}"
        self.manager.register_task(task_id, fix_task)
        self.manager.run_async(task_id)
        
        return ok({'task_id': task_id})
    
    # ========== AI 파이프라인 ==========
    
    def ai_pipeline(self, data: Any, *processors) -> Dict[str, Any]:
        """
        AI 처리 파이프라인
        
        Args:
            data: 초기 데이터
            processors: (name, prompt_template) 튜플들
        
        Examples:
            >>> h.ai.ai_pipeline(
            ...     raw_text,
            ...     ("clean", "다음 텍스트를 정리: {data}"),
            ...     ("analyze", "다음을 분석: {data}"),
            ...     ("summarize", "다음을 요약: {data}")
            ... )
        """
        import uuid
        pipeline_id = f"ai_pipe_{uuid.uuid4().hex[:6]}"
        
        def run_pipeline():
            current_data = data
            results = []
            
            for name, prompt_template in processors:
                prompt = prompt_template.format(data=current_data)
                
                self.message.task(f"AI 파이프라인 {pipeline_id}: {name}")
                
                # LLM 호출
                result = ask_o3_practical(prompt)
                if result['ok']:
                    current_data = result['data'].get('answer', '')
                    results.append({name: current_data})
                else:
                    break
            
            return results
        
        self.manager.register_task(pipeline_id, run_pipeline)
        self.manager.run_async(pipeline_id)
        
        return ok({'pipeline_id': pipeline_id, 'stages': len(processors)})
    
    # ========== 결과 관리 ==========
    
    def wait_llm(self, task_id: str, timeout: float = 60.0) -> Dict[str, Any]:
        """
        LLM 작업 완료 대기
        
        Args:
            task_id: LLM 작업 ID
            timeout: 최대 대기 시간
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            status_result = check_o3_status(task_id)
            if not status_result['ok']:
                return status_result
            
            status = status_result['data']['status']
            
            if status == 'completed':
                result = get_o3_result(task_id)
                if result['ok']:
                    # 캐시에 저장
                    self.llm_cache[task_id] = result['data']
                    self.message.task(f"LLM 완료: {task_id}", level="SUCCESS")
                return result
            elif status == 'error':
                return err(f"LLM 작업 실패: {task_id}")
            
            time.sleep(2)
        
        return err(f"LLM 응답 시간 초과: {task_id}")
    
    def get_llm_cache(self, task_id: Optional[str] = None) -> Any:
        """
        캐시된 LLM 결과 가져오기
        
        Args:
            task_id: 특정 작업 ID (None이면 전체)
        """
        if task_id:
            return self.llm_cache.get(task_id)
        return self.llm_cache
    
    def save_llm_results(self, filename: Optional[str] = None) -> Dict[str, Any]:
        """
        모든 LLM 결과를 파일로 저장
        
        Args:
            filename: 저장할 파일명 (기본: llm/results_timestamp.json)
        """
        if not self.llm_cache:
            return err("저장할 LLM 결과 없음")
        
        import json
        import os
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"llm/results_{timestamp}.json"
        
        # 디렉토리 생성
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.llm_cache, f, indent=2, ensure_ascii=False, default=str)
            
            self.message.task(f"LLM 결과 저장: {filename}", level="SUCCESS")
            return ok({'file': filename, 'count': len(self.llm_cache)})
        except Exception as e:
            return err(f"저장 실패: {e}")
    
    # ========== 상태 모니터링 ==========
    
    def llm_status(self) -> Dict[str, Any]:
        """
        모든 LLM 작업 상태 확인
        """
        active = []
        completed = []
        
        for task_id, info in self.active_llm_tasks.items():
            status_result = check_o3_status(task_id)
            if status_result['ok']:
                status = status_result['data']['status']
                if status == 'completed':
                    completed.append(task_id)
                else:
                    active.append({
                        'id': task_id,
                        'status': status,
                        'question': info['question']
                    })
        
        self.message.info("llm_status", f"활성: {len(active)}, 완료: {len(completed)}")
        
        return ok({
            'active': active,
            'completed': completed,
            'cached': list(self.llm_cache.keys())
        })

# 싱글톤 인스턴스
llm_background_facade = LLMBackgroundFacade()