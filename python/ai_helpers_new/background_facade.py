"""
Background Task Facade for REPL
REPL용 백그라운드 태스크 통합 Facade

Version: 2.0.0
Author: Claude Code
Created: 2025-08-24

REPL 변수 영속성과 병렬 실행을 최대한 활용하는 통합 시스템
"""

from typing import Dict, Any, Optional, Callable, List, Union
import time
import threading
from datetime import datetime
from .background import BackgroundTaskManager
from .message import message_facade
from .api_response import ok, err

class BackgroundFacade:
    """
    REPL 환경 최적화 백그라운드 작업 Facade
    
    핵심 기능:
    - 변수 영속성 활용: REPL 세션 간 변수 유지
    - 병렬 작업 관리: 여러 작업 동시 실행
    - 자동 상태 추적: message 시스템 통합
    - 결과 체이닝: 작업 결과를 다음 작업에 활용
    """
    
    def __init__(self):
        self.manager = BackgroundTaskManager()
        self.message = message_facade
        self.persistent_vars = {}  # REPL 영속 변수 저장소
        self.task_chains = {}  # 작업 체인 관리
        
    # ========== 기본 병렬 실행 ==========
    
    def run(self, func: Callable, *args, **kwargs) -> Dict[str, Any]:
        """
        간단한 백그라운드 실행 (자동 ID 생성)
        
        Examples:
            >>> h.bg.run(lambda x: x**2, 10)
            🚀 백그라운드 시작: auto_abc123
            {'ok': True, 'data': {'task_id': 'auto_abc123'}}
        """
        import uuid
        task_id = f"auto_{uuid.uuid4().hex[:6]}"
        
        self.manager.register_task(task_id, func, *args, **kwargs)
        return self.manager.run_async(task_id)
    
    def run_named(self, name: str, func: Callable, *args, **kwargs) -> Dict[str, Any]:
        """
        이름 지정 백그라운드 실행
        
        Examples:
            >>> h.bg.run_named("analysis", analyze_code, "main.py")
            🚀 백그라운드 시작: analysis
        """
        self.manager.register_task(name, func, *args, **kwargs)
        return self.manager.run_async(name)
    
    # ========== 병렬 맵 연산 ==========
    
    def map(self, func: Callable, items: List[Any]) -> Dict[str, Any]:
        """
        병렬 map 연산 (각 아이템을 별도 스레드에서 처리)
        
        Examples:
            >>> h.bg.map(process_file, ['file1.py', 'file2.py', 'file3.py'])
            >>> h.bg.gather_map()  # 모든 결과 수집
        """
        task_ids = []
        for i, item in enumerate(items):
            task_id = f"map_{i}_{item[:10] if isinstance(item, str) else i}"
            self.manager.register_task(task_id, func, item)
            self.manager.run_async(task_id)
            task_ids.append(task_id)
        
        self.persistent_vars['map_tasks'] = task_ids
        self.message.share(f"Map 작업 시작: {len(items)}개 아이템", task_ids)
        
        return ok({
            'task_ids': task_ids,
            'count': len(items)
        })
    
    def gather_map(self, timeout: float = 30.0) -> Dict[str, Any]:
        """
        map 작업 결과 수집
        
        Returns:
            {'ok': True, 'data': [results...]}
        """
        if 'map_tasks' not in self.persistent_vars:
            return err("활성 map 작업 없음")
        
        task_ids = self.persistent_vars['map_tasks']
        results = []
        
        for task_id in task_ids:
            result = self.manager.wait_for(task_id, timeout/len(task_ids))
            if result['ok']:
                results.append(result['data'])
        
        self.message.task(f"Map 결과 수집 완료: {len(results)}개", level="SUCCESS")
        return ok(results)
    
    # ========== 작업 체이닝 ==========
    
    def chain(self, *tasks) -> Dict[str, Any]:
        """
        작업 체인 생성 (이전 결과를 다음 작업에 전달)
        
        Examples:
            >>> h.bg.chain(
            ...     ("load", load_data, "data.json"),
            ...     ("process", process_data),  # 이전 결과 자동 전달
            ...     ("save", save_results)      # 이전 결과 자동 전달
            ... )
        """
        import uuid
        chain_id = f"chain_{uuid.uuid4().hex[:6]}"
        self.task_chains[chain_id] = {
            'tasks': tasks,
            'current': 0,
            'results': []
        }
        
        self.message.share(f"작업 체인 생성: {len(tasks)}개 단계", chain_id)
        self._run_chain_step(chain_id)
        
        return ok({'chain_id': chain_id, 'steps': len(tasks)})
    
    def _run_chain_step(self, chain_id: str):
        """체인의 다음 단계 실행 (내부용)"""
        chain = self.task_chains[chain_id]
        if chain['current'] >= len(chain['tasks']):
            self.message.task(f"체인 완료: {chain_id}", level="SUCCESS")
            return
        
        task = chain['tasks'][chain['current']]
        if isinstance(task, tuple):
            if len(task) >= 3:
                name, func, *args = task
            else:
                name, func = task
                args = []
        else:
            name = f"step_{chain['current']}"
            func = task
            args = []
        
        # 이전 결과를 첫 번째 인자로 전달
        if chain['results']:
            args = [chain['results'][-1]] + list(args)
        
        task_id = f"{chain_id}_{name}"
        
        def wrapper(*wrapper_args, **wrapper_kwargs):
            result = func(*wrapper_args, **wrapper_kwargs)
            chain['results'].append(result)
            chain['current'] += 1
            self._run_chain_step(chain_id)  # 다음 단계 실행
            return result
        
        self.manager.register_task(task_id, wrapper, *args)
        self.manager.run_async(task_id)
    
    # ========== 영속 변수 관리 ==========
    
    def store(self, name: str, value: Any) -> Dict[str, Any]:
        """
        영속 변수 저장 (REPL 세션 간 유지)
        
        Examples:
            >>> h.bg.store("config", {"mode": "production"})
            >>> h.bg.get("config")  # 나중에 다시 사용
        """
        self.persistent_vars[name] = value
        self.message.share(f"영속 변수: {name}", value)
        return ok({'stored': name})
    
    def get(self, name: str, default: Any = None) -> Any:
        """영속 변수 가져오기"""
        return self.persistent_vars.get(name, default)
    
    def list_vars(self) -> Dict[str, Any]:
        """저장된 영속 변수 목록"""
        return ok({
            'variables': list(self.persistent_vars.keys()),
            'count': len(self.persistent_vars)
        })
    
    # ========== 진행 상황 모니터링 ==========
    
    def status(self, detailed: bool = False) -> Dict[str, Any]:
        """
        전체 백그라운드 상태 확인
        
        Args:
            detailed: 상세 정보 표시 여부
        """
        status = self.manager.get_status()['data']
        active = self.manager.get_active_threads()['data']
        
        if detailed:
            # 상세 정보
            details = {
                'active_threads': active,
                'pending': status.get('pending', []),
                'running': status.get('running', []),
                'completed': status.get('completed', []),
                'failed': status.get('failed', []),
                'persistent_vars': list(self.persistent_vars.keys()),
                'active_chains': list(self.task_chains.keys())
            }
            
            self.message.task(f"""
백그라운드 상태:
  - 활성 스레드: {len(active)}개
  - 대기중: {len(details['pending'])}개
  - 실행중: {len(details['running'])}개
  - 완료: {len(details['completed'])}개
  - 실패: {len(details['failed'])}개
  - 영속 변수: {len(details['persistent_vars'])}개
  - 활성 체인: {len(details['active_chains'])}개
            """.strip())
            
            return ok(details)
        else:
            # 간단 요약
            summary = f"활성: {len(active)}, 완료: {len(status.get('completed', []))}"
            self.message.info("bg_status", summary)
            return ok(summary)
    
    def progress(self) -> Dict[str, Any]:
        """
        실시간 진행률 표시
        """
        status = self.manager.get_status()['data']
        total = sum(len(v) for v in status.values())
        completed = len(status.get('completed', []))
        failed = len(status.get('failed', []))
        done = completed + failed
        
        if total > 0:
            self.message.progress(done, total, "백그라운드 작업")
        
        return ok({
            'total': total,
            'completed': completed,
            'failed': failed,
            'progress': f"{done}/{total}"
        })
    
    # ========== 결과 관리 ==========
    
    def results(self) -> Dict[str, Any]:
        """모든 완료된 작업 결과 가져오기"""
        return self.manager.check_results()
    
    def result(self, task_id: str) -> Dict[str, Any]:
        """특정 작업 결과 가져오기"""
        return self.manager.get_result(task_id)
    
    def wait(self, task_id: str = None, timeout: float = 30.0) -> Dict[str, Any]:
        """
        작업 완료 대기
        
        Args:
            task_id: 특정 작업 ID (None이면 모든 작업)
            timeout: 최대 대기 시간
        """
        if task_id:
            return self.manager.wait_for(task_id, timeout)
        else:
            from .background import wait_for_all
            return wait_for_all(timeout)
    
    # ========== 고급 패턴 ==========
    
    def parallel_batch(self, tasks: List[tuple]) -> Dict[str, Any]:
        """
        여러 작업을 동시에 실행
        
        Args:
            tasks: [(name, func, args, kwargs), ...]
        
        Examples:
            >>> h.bg.parallel_batch([
            ...     ("analyze", analyze_code, ("main.py",), {}),
            ...     ("test", run_tests, (), {"verbose": True}),
            ...     ("lint", run_linter, ("src/",), {})
            ... ])
        """
        task_ids = []
        
        for task in tasks:
            if len(task) == 4:
                name, func, args, kwargs = task
            elif len(task) == 3:
                name, func, args = task
                kwargs = {}
            elif len(task) == 2:
                name, func = task
                args = ()
                kwargs = {}
            else:
                continue
            
            self.manager.register_task(name, func, *args, **kwargs)
            self.manager.run_async(name)
            task_ids.append(name)
        
        self.message.task(f"배치 실행: {len(task_ids)}개 작업 시작")
        return ok({'task_ids': task_ids, 'count': len(task_ids)})
    
    def pipeline(self, data: Any, *processors) -> Dict[str, Any]:
        """
        데이터 파이프라인 (각 단계를 병렬로 처리)
        
        Examples:
            >>> h.bg.pipeline(
            ...     raw_data,
            ...     clean_data,
            ...     transform_data,
            ...     validate_data
            ... )
        """
        import uuid
        pipeline_id = f"pipe_{uuid.uuid4().hex[:6]}"
        
        def run_pipeline():
            result = data
            for i, processor in enumerate(processors):
                self.message.task(f"파이프라인 {pipeline_id}: 단계 {i+1}/{len(processors)}")
                result = processor(result)
            return result
        
        self.manager.register_task(pipeline_id, run_pipeline)
        return self.manager.run_async(pipeline_id)
    
    # ========== 유틸리티 ==========
    
    def cleanup(self) -> Dict[str, Any]:
        """완료된 작업 정리"""
        result = self.manager.clear_completed()
        self.message.task(f"정리 완료: {result['data']['cleared']}개 작업", level="SUCCESS")
        return result
    
    def cancel(self, task_id: str) -> Dict[str, Any]:
        """
        작업 취소 (스레드 강제 종료는 위험하므로 플래그만 설정)
        """
        if task_id in self.manager.tasks:
            self.manager.tasks[task_id]['status'] = 'cancelled'
            self.message.task(f"작업 취소 요청: {task_id}", level="WARNING")
            return ok({'cancelled': task_id})
        return err(f"작업을 찾을 수 없음: {task_id}")

# 싱글톤 인스턴스
background_facade = BackgroundFacade()