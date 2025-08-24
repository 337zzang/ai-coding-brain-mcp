#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
🚀 Enhanced JSON REPL Session with Session Isolation
Version: 3.0.0

New Features:
- Session pooling for subagent isolation
- Thread-safe session management
- Automatic session cleanup
- Agent-specific namespaces
- Session metrics and monitoring
"""

import sys
import os
import json
import time
import gc
import io
import traceback
import threading
import uuid
from typing import Dict, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime, timedelta
import hashlib

# Add repl_core to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import enhanced components
from repl_core import EnhancedREPLSession, ExecutionMode
from repl_core.streaming import DataStream

# Windows UTF-8 configuration
if sys.platform == 'win32':
    try:
        # Try reconfigure() for Python 3.7+
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')
        elif hasattr(sys.stdout, 'buffer'):
            # For older Python versions with buffer support
            import codecs
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
            sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    except (AttributeError, TypeError):
        # In REPL or StringIO environment, just set the environment variable
        pass
    os.environ['PYTHONIOENCODING'] = 'utf-8'


class SessionPool:
    """Shared session manager with persistent variables"""
    
    def __init__(self, max_sessions: int = 1, session_timeout: int = 7200):
        self.max_sessions = max_sessions  # 1 shared session
        self.session_timeout = session_timeout  # 2 hours
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.RLock()
        
        # 🔥 공유 변수 스토리지 - REPL 핵심 기능
        self.shared_variables = {}  # 모든 에이전트가 공유
        self.workflow_data = {}     # 워크플로우 데이터
        self.cache_data = {}        # 자주 사용하는 데이터 캐시
        
        # 🔗 Flow 시스템 연동
        self.flow_api = None        # Flow API 인스턴스
        self.current_flow_plan = None  # 현재 활성 플랜
        
        self.metrics = {
            'total_created': 0,
            'total_reused': 0,
            'total_expired': 0,
            'current_active': 0,
            'shared_vars_count': 0
        }
    
    def _generate_session_key(self, agent_id: Optional[str], session_id: Optional[str]) -> str:
        """Always return 'shared' for shared session mode"""
        # 🔥 모든 에이전트가 'shared' 세션 사용
        return "shared"  # 단일 공유 세션!
    
    def _try_reuse_session(self, key: str, current_time: float) -> Optional[Tuple[str, EnhancedREPLSession]]:
        """Try to reuse existing session if valid"""
        if key not in self.sessions:
            return None
            
        session_data = self.sessions[key]
        
        # Check if session expired
        if current_time - session_data['last_accessed'] > self.session_timeout:
            self._cleanup_session(key)
            self.metrics['total_expired'] += 1
            return None
        
        # Reuse existing session
        session_data['last_accessed'] = current_time
        session_data['access_count'] += 1
        self.metrics['total_reused'] += 1
        
        return key, session_data['session']
    
    def _register_new_session(self, key: str, session: EnhancedREPLSession, 
                            agent_id: Optional[str], current_time: float) -> None:
        """Register a new session in the pool"""
        self.sessions[key] = {
            'session': session,
            'agent_id': agent_id,
            'created_at': current_time,
            'last_accessed': current_time,
            'access_count': 1,
            'execution_count': 0
        }
        
        self.metrics['total_created'] += 1
        self.metrics['current_active'] = len(self.sessions)
        
        print(f"[SessionPool] Created new session: {key} for agent: {agent_id or 'anonymous'}", 
              file=sys.stderr)
    
    def get_or_create_session(self, 
                            agent_id: Optional[str] = None,
                            session_id: Optional[str] = None) -> Tuple[str, EnhancedREPLSession]:
        """Get existing or create new isolated session"""
        
        with self.lock:
            # Generate session key
            key = self._generate_session_key(agent_id, session_id)
            current_time = time.time()
            
            # Try to reuse existing session
            existing = self._try_reuse_session(key, current_time)
            if existing:
                return existing
            
            # Check pool capacity
            if len(self.sessions) >= self.max_sessions:
                self._evict_lru_session()
            
            # Create and register new session
            new_session = self._create_new_session(agent_id)
            self._register_new_session(key, new_session, agent_id, current_time)
            
            return key, new_session
    
    def _init_flow_api(self):
        """Initialize Flow API if available"""
        try:
            # Flow API를 네임스페이스에서 가져오기
            if 'h' in globals() or 'ai_helpers_new' in globals():
                import ai_helpers_new as h
                self.flow_api = h.flow_api()
                
                # 현재 활성 플랜 확인 - 여러 방법 시도
                plan_id = self.workflow_data.get('flow_plan_id')
                
                if plan_id:
                    # 방법 1: get_plan 시도
                    try:
                        plan = self.flow_api.get_plan(plan_id)
                        if plan and plan.get('ok'):
                            self.current_flow_plan = plan.get('data')
                            print(f"[Flow] 플랜 연결: {self.current_flow_plan.get('name', plan_id)}", 
                                  file=sys.stderr)
                            return
                    except:
                        pass
                
                # 방법 2: 공유 변수에서 가져오기
                if self.shared_variables.get('current_flow_plan'):
                    self.current_flow_plan = self.shared_variables['current_flow_plan']
                    print(f"[Flow] 공유 변수에서 플랜 로드: {self.current_flow_plan.get('name', 'Unknown')}", 
                          file=sys.stderr)
                    return
                
                # 방법 3: list_plans에서 마지막 플랜 가져오기
                try:
                    plans = self.flow_api.list_plans()
                    if plans and plans.get('ok'):
                        plan_list = plans.get('data', [])
                        if plan_list:
                            self.current_flow_plan = plan_list[-1]
                            self.workflow_data['flow_plan_id'] = self.current_flow_plan.get('id')
                            print(f"[Flow] 마지막 플랜 자동 로드: {self.current_flow_plan.get('name')}", 
                                  file=sys.stderr)
                except:
                    pass
                    
        except Exception as e:
            print(f"[Flow] API 초기화 실패: {e}", file=sys.stderr)
    
    def _update_flow_task(self, agent_id: str, success: bool):
        """Update Flow task status based on execution result"""
        if not self.flow_api or not self.current_flow_plan:
            return
        
        try:
            # 에이전트 ID로 태스크 매핑
            task_mapping = {
                'code-analyzer': '분석',
                'code-optimizer': '최적화',
                'test-runner': '테스트',
                'code-validator': '검증',
                'planning-specialist': '설계'
            }
            
            task_name = task_mapping.get(agent_id, agent_id)
            
            # 태스크 찾기 및 업데이트
            if self.current_flow_plan.get('tasks'):
                for task in self.current_flow_plan['tasks']:
                    if task_name in task.get('name', ''):
                        status = 'completed' if success else 'in_progress'
                        self.flow_api.update_task_status(
                            self.current_flow_plan['id'],
                            task['id'],
                            status
                        )
                        print(f"[Flow] 태스크 '{task_name}' → {status}", file=sys.stderr)
                        break
        except Exception as e:
            print(f"[Flow] 태스크 업데이트 실패: {e}", file=sys.stderr)
    
    def _create_new_session(self, agent_id: Optional[str] = None) -> EnhancedREPLSession:
        """Create a shared session with increased memory and persistent variables"""
        
        config = {
            'memory_limit_mb': 2048,  # 🔥 2GB for better performance
            'cache_dir': '.repl_cache/shared',  # Shared cache
            'enable_streaming': True,
            'enable_caching': True,
            'chunk_size': 50000  # Larger chunks for efficiency
        }
        
        # 모든 에이전트가 같은 높은 메모리 사용
        # 세션 격리 제거 - 공유 세션 사용
        if agent_id:
            print(f"[SharedSession] Agent '{agent_id}' using shared session", file=sys.stderr)
        
        session = EnhancedREPLSession(**config)
        
        # 🔥 공유 변수 접근 함수 추가 - REPL의 핵심!
        session.namespace.update({
            'agent_id': agent_id,
            'session_info': lambda: self.get_session_info(agent_id),
            
            # 공유 변수 관리 - 모든 에이전트 접근 가능
            'shared': self.shared_variables,  # 직접 접근
            'workflow': self.workflow_data,    # 워크플로우 데이터
            'cache': self.cache_data,          # 캐시 데이터
            
            # 헬퍼 함수들
            'set_shared': lambda k, v: self.shared_variables.update({k: v}),
            'get_shared': lambda k, default=None: self.shared_variables.get(k, default),
            'list_shared': lambda: list(self.shared_variables.keys()),
            'clear_shared': lambda: self.shared_variables.clear(),
            
            # 워크플로우 데이터 관리
            'set_workflow': lambda k, v: self.workflow_data.update({k: v}),
            'get_workflow': lambda k, default=None: self.workflow_data.get(k, default),
            
            # 캐시 관리
            'set_cache': lambda k, v: self.cache_data.update({k: v}),
            'get_cache': lambda k, default=None: self.cache_data.get(k, default),
            
            # 변수 지속성 통계
            'var_stats': lambda: {
                'shared_count': len(self.shared_variables),
                'workflow_count': len(self.workflow_data),
                'cache_count': len(self.cache_data),
                'total_vars': len(self.shared_variables) + len(self.workflow_data) + len(self.cache_data)
            }
        })
        
        return session
    
    def _evict_lru_session(self) -> None:
        """Evict least recently used session"""
        
        if not self.sessions:
            return
        
        # Find LRU session
        lru_key = min(self.sessions.keys(), 
                     key=lambda k: self.sessions[k]['last_accessed'])
        
        self._cleanup_session(lru_key)
        print(f"[SessionPool] Evicted LRU session: {lru_key}", file=sys.stderr)
    
    def _cleanup_session(self, key: str):
        """Clean up a session and free resources"""
        
        if key not in self.sessions:
            return
        
        session_data = self.sessions[key]
        session = session_data['session']
        
        # Clear session resources
        try:
            session.clear_session()
            if hasattr(session, 'memory_manager'):
                session.memory_manager.cleanup()
            if hasattr(session, 'cache'):
                session.cache.clear()
        except Exception as e:
            print(f"[SessionPool] Error cleaning up session {key}: {e}", file=sys.stderr)
        
        del self.sessions[key]
        self.metrics['current_active'] = len(self.sessions)
    
    def _clear_agent_cache(self, agent_id: str):
        """Clear cache for specific agent"""
        
        cache_dir = Path(f'.repl_cache/{agent_id or "shared"}')
        if cache_dir.exists():
            import shutil
            shutil.rmtree(cache_dir, ignore_errors=True)
            print(f"[SessionPool] Cleared cache for agent: {agent_id}", file=sys.stderr)
    
    def get_session_info(self, session_key: str) -> Dict[str, Any]:
        """Get information about a specific session"""
        
        with self.lock:
            if session_key not in self.sessions:
                return {'error': 'Session not found'}
            
            session_data = self.sessions[session_key]
            
            return {
                'session_id': session_key,
                'agent_id': session_data['agent_id'],
                'created_at': datetime.fromtimestamp(session_data['created_at']).isoformat(),
                'last_accessed': datetime.fromtimestamp(session_data['last_accessed']).isoformat(),
                'access_count': session_data['access_count'],
                'execution_count': session_data['execution_count'],
                'age_seconds': int(time.time() - session_data['created_at'])
            }
    
    def get_pool_metrics(self) -> Dict[str, Any]:
        """Get pool-wide metrics"""
        
        with self.lock:
            return {
                **self.metrics,
                'sessions': {
                    key: self.get_session_info(key) 
                    for key in self.sessions.keys()
                }
            }
    
    def cleanup_expired_sessions(self) -> None:
        """Clean up all expired sessions"""
        
        with self.lock:
            current_time = time.time()
            expired_keys = [
                key for key, data in self.sessions.items()
                if current_time - data['last_accessed'] > self.session_timeout
            ]
            
            for key in expired_keys:
                self._cleanup_session(key)
                self.metrics['total_expired'] += 1
            
            if expired_keys:
                print(f"[SessionPool] Cleaned up {len(expired_keys)} expired sessions", 
                      file=sys.stderr)
    
    def shutdown(self) -> None:
        """Shutdown pool and cleanup all sessions"""
        
        with self.lock:
            print(f"[SessionPool] Shutting down with {len(self.sessions)} active sessions", 
                  file=sys.stderr)
            
            for key in list(self.sessions.keys()):
                self._cleanup_session(key)
            
            self.sessions.clear()
            self.metrics['current_active'] = 0


# Global session pool instance
SESSION_POOL = SessionPool(max_sessions=10, session_timeout=3600)


def get_enhanced_prompt(session_key: str = "shared") -> str:
    """Get enhanced prompt with context, Flow info and next steps"""
    output = []
    output.append("\n" + "━" * 60)
    
    # 1. Flow 시스템 상태 (최우선 표시) - 공유 변수에서 직접 읽기
    flow_plan = SESSION_POOL.shared_variables.get('current_flow_plan') or SESSION_POOL.current_flow_plan
    if flow_plan:
        plan = flow_plan
        tasks = plan.get('tasks', [])
        completed = sum(1 for t in tasks if t.get('status') == 'completed')
        in_progress = sum(1 for t in tasks if t.get('status') == 'in_progress')
        total = len(tasks)
        
        output.append(f"📋 Flow 플랜: {plan.get('name', 'Unknown')}")
        output.append(f"  진행률: {completed}/{total} 완료 | {in_progress} 진행중")
        
        # 태스크 상태 표시
        if tasks:
            output.append("  태스크:")
            # 슬라이스 대신 enumerate 사용
            for i, task in enumerate(tasks):
                if i >= 5:  # 최대 5개만
                    break
                status_icon = "✅" if task.get('status') == 'completed' else "⏳" if task.get('status') == 'in_progress' else "⬜"
                output.append(f"    {status_icon} {task.get('name', 'Unknown')}")
    
    # 2. 저장된 변수 정보 표시
    if SESSION_POOL.shared_variables:
        output.append("\n💾 저장된 주요 변수:")
        for key in list(SESSION_POOL.shared_variables.keys())[-5:]:  # 최근 5개
            value = SESSION_POOL.shared_variables[key]
            if isinstance(value, dict):
                output.append(f"  • {key}: {list(value.keys())[:3]}...")
            elif isinstance(value, list):
                output.append(f"  • {key}: [{len(value)} items]")
            else:
                value_str = str(value)[:50] + "..." if len(str(value)) > 50 else str(value)
                output.append(f"  • {key}: {value_str}")
    
    # 3. 워크플로우 상태 (Flow 관련 제외)
    if SESSION_POOL.workflow_data:
        non_flow_keys = [k for k in SESSION_POOL.workflow_data.keys() if not k.startswith('flow_')]
        if non_flow_keys:
            output.append("\n🔄 워크플로우 상태:")
            for key in non_flow_keys[-3:]:
                value = SESSION_POOL.workflow_data[key]
                output.append(f"  • {key}: {value}")
    
    # 4. 변수 통계
    total_vars = len(SESSION_POOL.shared_variables)
    total_workflow = len(SESSION_POOL.workflow_data)
    total_cache = len(SESSION_POOL.cache_data)
    if total_vars + total_workflow + total_cache > 0:
        output.append(f"\n📊 데이터 현황: 공유({total_vars}) | 워크플로우({total_workflow}) | 캐시({total_cache})")
    
    # 5. 다음 작업 가이드 (Flow 기반)
    output.append("\n🎯 다음 작업:")
    
    # Flow 태스크 기반 가이드
    if SESSION_POOL.current_flow_plan:
        next_task = None
        for task in SESSION_POOL.current_flow_plan.get('tasks', []):
            if task.get('status') != 'completed':
                next_task = task.get('name', 'Unknown')
                break
        
        if next_task:
            # 태스크명으로 에이전트 매핑
            if '분석' in next_task:
                output.append(f"  → code-analyzer 실행: {next_task}")
            elif '최적화' in next_task:
                output.append(f"  → code-optimizer 실행: {next_task}")
            elif '테스트' in next_task:
                output.append(f"  → test-runner 실행: {next_task}")
            else:
                output.append(f"  → {next_task} 실행")
    else:
        # Flow 없을 때 기존 로직
        if 'analysis' in SESSION_POOL.shared_variables or 'analysis_result' in SESSION_POOL.shared_variables:
            if 'optimization' not in SESSION_POOL.shared_variables and 'optimization_result' not in SESSION_POOL.shared_variables:
                output.append("  → optimizer 실행: get_shared('analysis_result')")
            elif 'test' not in SESSION_POOL.shared_variables and 'test_result' not in SESSION_POOL.shared_variables:
                output.append("  → test 실행: get_shared('optimization_result')")
            else:
                output.append("  → 결과 확인: list_shared()")
        else:
            output.append("  → 데이터 활용: get_shared('key_name')")
            output.append("  → 저장: set_shared('key', value)")
    
    output.append("━" * 60)
    return "\n".join(output)


def _track_execution(session_key: str) -> None:
    """Track execution count for a session"""
    if session_key in SESSION_POOL.sessions:
        SESSION_POOL.sessions[session_key]['execution_count'] += 1


def _build_response_metadata(result: Any, session_key: str, agent_id: Optional[str]) -> Dict[str, Any]:
    """Build response metadata from execution result"""
    session_data = SESSION_POOL.sessions.get(session_key, {})
    
    return {
        'success': result.success,
        'language': 'python',
        'session_mode': 'ISOLATED_JSON_REPL',
        'session_id': session_key,
        'agent_id': agent_id,
        'stdout': result.stdout,
        'stderr': result.stderr,
        'execution_count': session_data.get('execution_count', 0),
        'memory_mb': result.memory_usage_mb,
        'execution_time_ms': result.execution_time_ms,
        'execution_mode': result.execution_mode.value,
        'chunks_processed': result.chunks_processed,
        'cached': result.cached,
        'note': f'Isolated session for agent: {agent_id or "anonymous"}',
        'debug_info': {
            'session_active': True,
            'session_age': int(time.time() - session_data.get('created_at', time.time())),
            'pool_size': len(SESSION_POOL.sessions),
            'pool_metrics': SESSION_POOL.get_pool_metrics()
        },
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    }


def _add_cache_statistics(response: Dict[str, Any], session: Any) -> None:
    """Add cache statistics to response if caching is enabled"""
    if session.enable_caching:
        cache_stats = session.get_cache_stats()
        response['cache_stats'] = {
            'entries': cache_stats.get('entries', 0),
            'hit_rate': cache_stats.get('hit_rate', 0)
        }


def execute_code(code: str, 
                agent_id: Optional[str] = None,
                session_id: Optional[str] = None) -> Dict[str, Any]:
    """Execute code in an isolated session with Flow integration"""
    
    # Initialize Flow API if not done
    if SESSION_POOL.flow_api is None:
        SESSION_POOL._init_flow_api()
    
    # Get or create isolated session
    session_key, session = SESSION_POOL.get_or_create_session(agent_id, session_id)
    
    # Track execution
    _track_execution(session_key)
    
    # Execute with enhanced session
    result = session.execute(code)
    
    # Build response
    response = _build_response_metadata(result, session_key, agent_id)
    
    # Add cache statistics if available
    _add_cache_statistics(response, session)
    
    # Update Flow task if agent_id provided
    if agent_id and SESSION_POOL.flow_api:
        SESSION_POOL._update_flow_task(agent_id, response.get("success", False))
    
    # Add enhanced prompt with context for successful executions
    if response.get("success", False):
        response["stdout"] += get_enhanced_prompt(session_key)
    
    return response


def read_json_input() -> Optional[str]:
    """Read JSON input from stdin"""
    try:
        line = sys.stdin.readline()
        if not line:
            return None
        return line.strip()
    except:
        return None


def write_json_output(response: Dict[str, Any]) -> None:
    """Write JSON output to stdout"""
    json_str = json.dumps(response, ensure_ascii=False)
    sys.stdout.write(json_str + '\n')
    sys.stdout.flush()


def periodic_cleanup() -> None:
    """Periodic cleanup task for expired sessions"""
    import threading
    
    def cleanup_task():
        while True:
            time.sleep(300)  # Every 5 minutes
            SESSION_POOL.cleanup_expired_sessions()
    
    cleanup_thread = threading.Thread(target=cleanup_task, daemon=True)
    cleanup_thread.start()


def print_startup_message() -> None:
    """Print startup message to stderr"""
    print("=" * 60, file=sys.stderr)
    print("Isolated JSON REPL Session v3.0", file=sys.stderr)
    print("Session Pooling for Subagent Isolation", file=sys.stderr)
    print("-" * 60, file=sys.stderr)
    print(f"Max sessions: {SESSION_POOL.max_sessions}", file=sys.stderr)
    print(f"Session timeout: {SESSION_POOL.session_timeout}s", file=sys.stderr)
    print(f"Isolation: Enabled", file=sys.stderr)
    print("=" * 60, file=sys.stderr)


def handle_execute_request(request_id: Optional[str], params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle execute request and return response"""
    code = params.get('code', '')
    agent_id = params.get('agent_id')
    session_id = params.get('session_id')
    
    # Auto-detect agent if not provided
    if not agent_id and 'import ai_helpers_new' in code:
        if 'test' in code.lower():
            agent_id = 'test-runner'
        elif 'analyze' in code.lower() or 'analysis' in code.lower():
            agent_id = 'code-analyzer'
        elif 'optimize' in code.lower():
            agent_id = 'code-optimizer'
    
    # Execute code in isolated session
    result = execute_code(code, agent_id, session_id)
    
    return {
        'jsonrpc': '2.0',
        'id': request_id,
        'result': result
    }


def handle_metrics_request(request_id: Optional[str]) -> Dict[str, Any]:
    """Handle pool metrics request"""
    return {
        'jsonrpc': '2.0',
        'id': request_id,
        'result': SESSION_POOL.get_pool_metrics()
    }


def create_error_response(request_id: Optional[str], code: int, message: str) -> Dict[str, Any]:
    """Create error response in JSON-RPC format"""
    return {
        'jsonrpc': '2.0',
        'id': request_id,
        'error': {
            'code': code,
            'message': message
        }
    }


def main() -> None:
    """Main execution loop with session isolation"""
    # Start periodic cleanup
    periodic_cleanup()
    
    # Print startup message
    print_startup_message()
    
    # Ready signal
    print("__READY__", flush=True)
    
    # Run main loop
    run_main_loop()
    
    # Cleanup
    shutdown_repl()


def process_single_request(code_input: str) -> Optional[Dict[str, Any]]:
    """Process a single JSON-RPC request"""
    try:
        request = json.loads(code_input)
        request_id = request.get('id')
        request_type = request.get('method', '').split('/')[-1]
        
        if request_type == 'execute':
            params = request.get('params', {})
            return handle_execute_request(request_id, params)
        elif request_type == 'get_pool_metrics':
            return handle_metrics_request(request_id)
        else:
            return create_error_response(
                request_id, -32601, 
                f'Method not found: {request_type}'
            )
    
    except json.JSONDecodeError as e:
        return create_error_response(None, -32700, f'Parse error: {str(e)}')
    except Exception as e:
        return create_error_response(None, -32603, f'Internal error: {str(e)}')


def run_main_loop() -> None:
    """Run the main request processing loop"""
    while True:
        try:
            # Read JSON request
            code_input = read_json_input()
            if code_input is None:
                break
            
            # Process request
            response = process_single_request(code_input)
            if response:
                write_json_output(response)
        
        except KeyboardInterrupt:
            break
        except Exception as e:
            # Log unexpected errors but continue
            print(f"Unexpected error in main loop: {e}", file=sys.stderr)
            continue


def shutdown_repl() -> None:
    """Clean shutdown of the REPL"""
    
    print("\nShutting down isolated REPL...", file=sys.stderr)
    SESSION_POOL.shutdown()
    gc.collect()
    print("Goodbye!", file=sys.stderr)


if __name__ == '__main__':
    main()