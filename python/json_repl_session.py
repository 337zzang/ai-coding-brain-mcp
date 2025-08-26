#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
🚀 Enhanced JSON REPL Session with Smart Memory Management
Version: 4.1.0

Features:
- Real-time memory monitoring
- Automatic garbage collection
- Variable limit management  
- Memory usage reporting in stdout
- Non-blocking I/O with timeout
- Safe resource cleanup
"""

import sys
import os
import json
import time
import gc
import io
import traceback
import threading
import atexit
import select
import queue
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime

# Import memory facade
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from memory_facade import MEMORY_MANAGER, execute_code_with_memory_check, get_memory_report

# Import original components
from repl_core import EnhancedREPLSession, ExecutionMode

# Windows UTF-8 configuration
if sys.platform == 'win32':
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass
    os.environ['PYTHONIOENCODING'] = 'utf-8'

class SmartSessionPool:
    """메모리 관리가 강화된 세션 풀 - 백그라운드 작업 지원"""
    
    def __init__(self):
        self.session = None
        self.namespace = {}
        self.lock = threading.RLock()
        
        # 메모리 매니저 연결
        self.memory_manager = MEMORY_MANAGER
        
        # 백그라운드 작업 관리
        self.background_tasks = {}
        self.task_counter = 0
        self.executor = None
        
        # 통계
        self.stats = {
            'total_executions': 0,
            'memory_cleanups': 0,
            'peak_memory_mb': 0,
            'background_tasks': 0
        }
        
        # 리소스 정리 등록
        atexit.register(self.cleanup)
    
    def get_or_create_session(self) -> EnhancedREPLSession:
        """세션 가져오기 또는 생성"""
        with self.lock:
            if self.session is None:
                self.session = EnhancedREPLSession(
                    memory_limit_mb=2000,  # 2GB 메모리 제한
                    enable_streaming=True,
                    enable_caching=True
                )
                self._init_namespace()
            return self.session
    
    def _init_namespace(self):
        """네임스페이스 초기화 - 백그라운드 헬퍼 포함"""
        self.namespace = {
            '__builtins__': __builtins__,
            '__name__': '__main__',
            'sys': sys,
            'os': os,
            'Path': Path,
            'datetime': datetime,
            'gc': gc,
            # 메모리 관리 함수 추가
            'mem_status': self.memory_manager.get_memory_status,
            'mem_clean': self.memory_manager.clean_memory,
            'mem_report': lambda: print(get_memory_report()),
            'set_var': self.memory_manager.set_variable,
            'get_var': self.memory_manager.get_variable,
            # 백그라운드 작업 함수 추가
            'bg_run': self.run_background,
            'bg_status': self.get_background_status,
            'bg_result': self.get_background_result,
            'bg_list': self.list_background_tasks,
        }
    
    def execute_with_memory_management(self, code: str) -> Dict[str, Any]:
        """메모리 관리가 포함된 코드 실행 - MCP 호환 개선"""
        
        # 실행 전 메모리 체크
        before_status = self.memory_manager.get_memory_status()
        
        # 메모리 정보는 stderr로만 출력 (디버그용)
        print(f"\n[MEM] 실행 시작 - {before_status['used_mb']:.1f}MB ({before_status['percent_used']:.1f}%)", file=sys.stderr)
        
        # 메모리 임계값 체크
        if before_status['critical']:
            print(f"[MEM] ⚠️ 메모리 위험! 자동 정리 시작...", file=sys.stderr)
            clean_result = self.memory_manager.clean_memory(force=True)
            print(f"[MEM] ✅ {clean_result['memory_freed_mb']:.1f}MB 해제", file=sys.stderr)
            self.stats['memory_cleanups'] += 1
        
        # 실제 코드 실행 - 모든 환경에서 StringIO 캡처
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        
        try:
            # stdout 캡처를 위한 StringIO 설정
            stdout_buffer = io.StringIO()
            stderr_buffer = io.StringIO()
            
            sys.stdout = stdout_buffer
            sys.stderr = stderr_buffer
            
            # 네임스페이스에서 코드 실행
            exec(code, self.namespace)
            
            # 출력 가져오기
            output = stdout_buffer.getvalue()
            error_output = stderr_buffer.getvalue()
            
            # 실행 후 메모리 상태
            after_status = self.memory_manager.get_memory_status()
            memory_delta = after_status['used_mb'] - before_status['used_mb']
            
            # 통계 업데이트
            self.stats['total_executions'] += 1
            if after_status['used_mb'] > self.stats['peak_memory_mb']:
                self.stats['peak_memory_mb'] = after_status['used_mb']
            
            print(f"[MEM] 실행 완료 - 메모리 변화: {memory_delta:+.1f}MB", file=sys.stderr)
            
            return {
                'status': 'success',
                'stdout': output,
                'stderr': '',
                'memory': {
                    'before_mb': before_status['used_mb'],
                    'after_mb': after_status['used_mb'],
                    'delta_mb': round(memory_delta, 2),
                    'percent': after_status['percent_used'],
                    'variables': after_status['variables_count']
                },
                'stats': self.stats
            }
            
        except Exception as e:
            
            # 에러 시에도 메모리 상태 확인
            error_status = self.memory_manager.get_memory_status()
            
            return {
                'status': 'error',
                'error': str(e),
                'traceback': traceback.format_exc(),
                'memory': {
                    'current_mb': error_status['used_mb'],
                    'percent': error_status['percent_used'],
                    'variables': error_status['variables_count']
                }
            }
        finally:
            # stdout/stderr 복원 보장
            sys.stdout = old_stdout
            sys.stderr = old_stderr
    
    def run_background(self, code: str, task_name: str = None) -> str:
        """백그라운드에서 코드 실행"""
        import concurrent.futures
        
        if self.executor is None:
            self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)
        
        task_id = f"bg_task_{self.task_counter}"
        self.task_counter += 1
        
        # 백그라운드 작업 등록
        future = self.executor.submit(self._execute_background, code)
        self.background_tasks[task_id] = {
            'future': future,
            'name': task_name or task_id,
            'start_time': datetime.now(),
            'code': code[:100] + '...' if len(code) > 100 else code,
            'status': 'running'
        }
        
        self.stats['background_tasks'] += 1
        print(f"[BG] 백그라운드 작업 시작: {task_id}", file=sys.stderr)
        return task_id
    
    def _execute_background(self, code: str) -> Dict[str, Any]:
        """백그라운드 실행 워커"""
        try:
            # 별도 네임스페이스에서 실행
            bg_namespace = dict(self.namespace)
            exec(code, bg_namespace)
            return {'status': 'success', 'namespace': bg_namespace}
        except Exception as e:
            return {'status': 'error', 'error': str(e), 'traceback': traceback.format_exc()}
    
    def get_background_status(self, task_id: str = None) -> Dict[str, Any]:
        """백그라운드 작업 상태 확인"""
        if task_id:
            if task_id in self.background_tasks:
                task = self.background_tasks[task_id]
                if task['future'].done():
                    task['status'] = 'completed'
                return {
                    'task_id': task_id,
                    'name': task['name'],
                    'status': task['status'],
                    'running_time': str(datetime.now() - task['start_time'])
                }
            return {'error': f'Task {task_id} not found'}
        
        # 전체 작업 상태
        return {
            'total': len(self.background_tasks),
            'running': sum(1 for t in self.background_tasks.values() if not t['future'].done()),
            'completed': sum(1 for t in self.background_tasks.values() if t['future'].done())
        }
    
    def get_background_result(self, task_id: str) -> Dict[str, Any]:
        """백그라운드 작업 결과 가져오기"""
        if task_id not in self.background_tasks:
            return {'error': f'Task {task_id} not found'}
        
        task = self.background_tasks[task_id]
        if not task['future'].done():
            return {'status': 'running', 'message': 'Task is still running'}
        
        try:
            result = task['future'].result(timeout=0.1)
            task['status'] = 'completed'
            return result
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    def list_background_tasks(self) -> List[Dict[str, Any]]:
        """백그라운드 작업 목록"""
        tasks = []
        for task_id, task in self.background_tasks.items():
            tasks.append({
                'id': task_id,
                'name': task['name'],
                'status': 'completed' if task['future'].done() else 'running',
                'start_time': task['start_time'].isoformat(),
                'code_preview': task['code']
            })
        return tasks
    
    def cleanup(self):
        """리소스 정리"""
        if self.executor:
            try:
                self.executor.shutdown(wait=False)
                print("[CLEANUP] ThreadPoolExecutor 종료됨", file=sys.stderr)
            except:
                pass
    
    def get_stats_report(self) -> str:
        """통계 리포트 생성"""
        bg_status = self.get_background_status()
        return f"""
📊 세션 통계
- 총 실행: {self.stats['total_executions']}회
- 메모리 정리: {self.stats['memory_cleanups']}회
- 최대 메모리: {self.stats['peak_memory_mb']:.1f}MB
- 백그라운드 작업: {self.stats['background_tasks']}개 (실행중: {bg_status.get('running', 0)})
"""

# 전역 세션 풀
SESSION_POOL = SmartSessionPool()

def execute_code(code: str, agent_id: Optional[str] = None, 
                session_id: Optional[str] = None) -> Dict[str, Any]:
    """메모리 관리가 강화된 코드 실행"""
    
    # 세션 풀에서 실행
    result = SESSION_POOL.execute_with_memory_management(code)
    
    # 주기적으로 통계 출력 (10회마다)
    if SESSION_POOL.stats['total_executions'] % 10 == 0:
        print(SESSION_POOL.get_stats_report(), file=sys.stderr)
        print(get_memory_report(), file=sys.stderr)
    
    return result

def process_json_request(request: Dict[str, Any]) -> Dict[str, Any]:
    """JSON-RPC 요청 처리"""
    try:
        # method 체크
        method = request.get('method', '')
        if method != 'execute':
            return {
                'jsonrpc': '2.0',
                'id': request.get('id', 1),
                'error': {
                    'code': -32601,
                    'message': f'Method not found: {method}'
                }
            }
        
        # 코드 추출
        params = request.get('params', {})
        code = params.get('code', '')
        agent_id = params.get('agent_id')
        session_id = params.get('session_id')
        
        # 코드 실행
        result = execute_code(code, agent_id, session_id)
        
        # 응답 생성
        if result['status'] == 'success':
            return {
                'jsonrpc': '2.0',
                'id': request.get('id', 1),
                'result': {
                    'stdout': result['stdout'],  # Changed to match the updated property name
                    'stderr': result.get('stderr', ''),
                    'memory': result['memory'],
                    'stats': result['stats']
                }
            }
        else:
            return {
                'jsonrpc': '2.0',
                'id': request.get('id', 1),
                'error': {
                    'code': -32603,
                    'message': result['error'],
                    'data': {
                        'traceback': result.get('traceback'),
                        'memory': result['memory']
                    }
                }
            }
    except Exception as e:
        return {
            'jsonrpc': '2.0',
            'id': request.get('id', 1),
            'error': {
                'code': -32603,
                'message': str(e)
            }
        }

def read_stdin_with_timeout(timeout=0.5):
    """타임아웃과 함께 stdin 읽기"""
    if sys.platform == 'win32':
        # Windows에서는 threading 사용
        import queue
        q = queue.Queue()
        
        def read_input():
            try:
                line = sys.stdin.readline()
                if line:
                    q.put(line)
                else:
                    q.put(None)
            except:
                q.put(None)
        
        thread = threading.Thread(target=read_input)
        thread.daemon = True
        thread.start()
        
        try:
            return q.get(timeout=timeout)
        except queue.Empty:
            return ""
    else:
        # Unix/Linux에서는 select 사용
        if select.select([sys.stdin], [], [], timeout)[0]:
            return sys.stdin.readline()
        return ""

def main():
    """메인 실행 루프 - 세션 영속성 보장"""
    DEBUG = os.environ.get('DEBUG', '').lower() == 'true'
    
    print("Enhanced JSON REPL with Memory Management v4.1", file=sys.stderr)
    print(f"Memory Limits: {MEMORY_MANAGER.MAX_VARIABLES} vars, "
          f"{MEMORY_MANAGER.MAX_VAR_SIZE_MB}MB/var", file=sys.stderr)
    print(f"Thresholds: Warning {MEMORY_MANAGER.MEMORY_WARNING_THRESHOLD}%, "
          f"Critical {MEMORY_MANAGER.MEMORY_CRITICAL_THRESHOLD}%", file=sys.stderr)
    print("Ready for requests...", file=sys.stderr)
    
    # Send ready signal to MCP handler
    print("__READY__", flush=True)
    
    # Claude Code 환경 감지
    is_claude_code = os.environ.get('CLAUDE_CODE_ENV') == 'true' or \
                     os.environ.get('MCP_MODE') == 'claude' or \
                     not sys.stdin.isatty()
    
    if is_claude_code:
        print("Claude Code/MCP 환경 감지됨 - 세션 초기화", file=sys.stderr)
        # 세션 풀 초기화
        SESSION_POOL.get_or_create_session()
        print("세션 풀 초기화 완료 - 요청 대기 중", file=sys.stderr)
    
    # 에러 카운터
    error_counter = 0
    max_errors = 5
    idle_counter = 0
    max_idle = 120  # 60초 (0.5초 * 120)
    is_first_request = True  # 첫 요청 플래그
    
    # 메인 루프 - 첫 요청은 블로킹, 이후 타임아웃
    while error_counter < max_errors:
        try:
            # 첫 요청은 블로킹으로 대기 (MCP 핸들러 호환성)
            if is_first_request:
                line = sys.stdin.readline()
                is_first_request = False
                if DEBUG:
                    print("[FIRST] 첫 요청 블로킹 모드로 수신", file=sys.stderr)
            else:
                # 두 번째 요청부터 타임아웃 적용
                line = read_stdin_with_timeout(0.5)
                
                if line is None:  # EOF
                    break
                
                if not line:  # 타임아웃
                    idle_counter += 1
                    if idle_counter > max_idle:
                        print(f"[TIMEOUT] {max_idle*0.5}초 동안 입력 없음 - 종료", file=sys.stderr)
                        break
                    continue
            
            # 입력 받으면 카운터 리셋
            idle_counter = 0
            error_counter = 0
            
            # 디버그 출력 (조건부)
            if DEBUG:
                print(f"[DEBUG] Received request: {line.strip()[:100]}...", file=sys.stderr)
            
            # JSON 파싱
            request = json.loads(line.strip())
            
            # 요청 처리
            response = process_json_request(request)
            
            # 디버그 출력 (조건부)
            if DEBUG:
                print(f"[DEBUG] Sending response", file=sys.stderr)
            
            # 응답 전송
            response_json = json.dumps(response, ensure_ascii=False)
            print(response_json)
            sys.stdout.flush()
            
        except KeyboardInterrupt:
            print("\n[INTERRUPT] 사용자 중단", file=sys.stderr)
            break
        except json.JSONDecodeError as e:
            error_counter += 1
            error_response = {
                'jsonrpc': '2.0',
                'error': {
                    'code': -32700,
                    'message': f'Parse error: {str(e)}'
                }
            }
            print(json.dumps(error_response))
            sys.stdout.flush()
        except Exception as e:
            error_counter += 1
            print(f"[ERROR {error_counter}/{max_errors}] {e}", file=sys.stderr)
            if error_counter >= max_errors:
                print(f"[FATAL] 연속 {max_errors}회 에러 - 종료", file=sys.stderr)
    
    # 정리
    print("\n[EXIT] 세션 종료", file=sys.stderr)
    print(SESSION_POOL.get_stats_report(), file=sys.stderr)
    print(get_memory_report(), file=sys.stderr)
    SESSION_POOL.cleanup()

if __name__ == "__main__":
    main()