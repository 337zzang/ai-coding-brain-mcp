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
        
        # 🔥 단일 공유 변수 스토리지 - 모든 데이터 통합 관리
        self.shared_variables = {}  # 모든 데이터를 하나로 관리
        
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
        
        # 🔥 단순화된 공유 변수 시스템 - 하나로 통합!
        session.namespace.update({
            'agent_id': agent_id,
            'session_info': lambda: self.get_session_info(agent_id),
            
            # 단일 공유 변수 스토리지
            'shared': self.shared_variables,  # 모든 데이터를 여기에
            
            # 간단한 헬퍼 함수들
            'set_shared': lambda k, v: self.shared_variables.update({k: v}),
            'get_shared': lambda k, default=None: self.shared_variables.get(k, default),
            'list_shared': lambda: list(self.shared_variables.keys()),
            'clear_shared': lambda: self.shared_variables.clear(),
            'del_shared': lambda k: self.shared_variables.pop(k, None),
            
            # 변수 통계
            'var_count': lambda: len(self.shared_variables),
            'var_info': lambda: {
                'total': len(self.shared_variables),
                'keys': list(self.shared_variables.keys())[:10]  # 최대 10개 키만
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
    """AI가 다음 작업을 이어서 수행하도록 개별 변수를 명확하게 전달"""
    
    output = []
    output.append("\n" + "━" * 60)
    output.append("\n📦 개별 변수 전달 시스템")
    output.append("━" * 60)
    
    # 1. 모든 개별 변수를 각각 표시
    if SESSION_POOL.shared_variables:
        output.append("\n🔤 사용 가능한 개별 변수들:\n")
        
        # 각 변수를 개별적으로 상세히 표시
        for key, value in SESSION_POOL.shared_variables.items():
            # Flow 플랜은 특별 처리
            if key == 'current_flow_plan':
                output.append(f"  📋 {key}:")
                output.append(f"     • 타입: Flow Plan")
                output.append(f"     • 용도: 작업 플랜 관리")
                output.append(f"     • 접근: plan = get_shared('{key}')")
                output.append("")
                continue
            
            # 각 변수별 상세 정보
            output.append(f"  📌 {key}:")
            
            # 타입 정보
            if isinstance(value, dict):
                output.append(f"     • 타입: Dictionary ({len(value)} 필드)")
                if len(value) <= 5:
                    output.append(f"     • 키: {list(value.keys())}")
                else:
                    output.append(f"     • 주요 키: {list(value.keys())[:5]} ...")
                    
            elif isinstance(value, list):
                output.append(f"     • 타입: List ({len(value)} 항목)")
                if len(value) > 0:
                    output.append(f"     • 첫 항목 타입: {type(value[0]).__name__}")
                    
            elif isinstance(value, str):
                output.append(f"     • 타입: String")
                if len(value) < 50:
                    output.append(f"     • 값: '{value}'")
                else:
                    output.append(f"     • 길이: {len(value)}자")
                    
            elif isinstance(value, (int, float)):
                output.append(f"     • 타입: {type(value).__name__}")
                output.append(f"     • 값: {value}")
                
            else:
                output.append(f"     • 타입: {type(value).__name__}")
            
            # 변수별 개별 접근 방법
            output.append(f"     • 접근: {key}_data = get_shared('{key}')")
            
            # 용도 추정 (키 이름 기반)
            if 'analysis' in key:
                output.append(f"     • 용도: 분석 결과 데이터")
            elif 'test' in key:
                output.append(f"     • 용도: 테스트 결과 데이터")
            elif 'optimization' in key:
                output.append(f"     • 용도: 최적화 결과 데이터")
            elif 'file' in key or 'content' in key:
                output.append(f"     • 용도: 파일/콘텐츠 데이터")
            elif 'data' in key:
                output.append(f"     • 용도: 일반 데이터 저장")
                
            output.append("")  # 빈 줄로 구분
    
    # 2. 함수와 클래스 추적 (개별 표시)
    output.append("\n🔧 사용 가능한 함수/클래스:\n")
    
    # 네임스페이스에서 함수와 클래스 찾기
    for name, obj in SESSION_POOL.shared_variables.items():
        if callable(obj) and not name.startswith('_'):
            if hasattr(obj, '__call__'):
                # 함수인 경우
                output.append(f"  🎯 {name}():")
                output.append(f"     • 타입: Function")
                if hasattr(obj, '__doc__') and obj.__doc__:
                    doc_first_line = obj.__doc__.strip().split('\n')[0][:50]
                    output.append(f"     • 설명: {doc_first_line}")
                output.append(f"     • 호출: result = {name}()")
                output.append("")
                
        elif isinstance(obj, type):
            # 클래스인 경우
            output.append(f"  🏗️ {name}:")
            output.append(f"     • 타입: Class")
            if hasattr(obj, '__doc__') and obj.__doc__:
                doc_first_line = obj.__doc__.strip().split('\n')[0][:50]
                output.append(f"     • 설명: {doc_first_line}")
            output.append(f"     • 생성: instance = {name}()")
            output.append("")
    
    # 3. 단계별 작업 가이드
    output.append("\n📝 단계별 작업 연속성:")
    
    # 이전 단계에서 생성된 중요한 것들 확인
    important_items = []
    for key in SESSION_POOL.shared_variables.keys():
        if any(keyword in key for keyword in ['result', 'data', 'analysis', 'optimization', 'test', 'output']):
            important_items.append(key)
    
    if important_items:
        output.append(f"\n  이전 단계 산출물 ({len(important_items)}개):")
        for item in important_items[-5:]:  # 최근 5개만
            value = SESSION_POOL.shared_variables[item]
            if isinstance(value, dict):
                output.append(f"    • {item} → Dictionary")
            elif isinstance(value, list):
                output.append(f"    • {item} → List[{len(value)}]")
            elif callable(value):
                output.append(f"    • {item} → Function")
            else:
                output.append(f"    • {item} → {type(value).__name__}")
    
    # 4. Flow 플랜 기반 다음 작업 지시
    flow_plan = SESSION_POOL.shared_variables.get('current_flow_plan')
    if flow_plan:
        tasks = flow_plan.get('tasks', {})
        if isinstance(tasks, dict):
            task_list = list(tasks.values())
        else:
            task_list = tasks if tasks else []
        
        # 다음 태스크 찾기
        next_task = None
        for task in task_list:
            if task.get('status') not in ['completed', 'done']:
                next_task = task
                break
        
        if next_task:
            task_name = next_task.get('title') or next_task.get('name', 'Unknown')
            output.append(f"\n🎯 다음 태스크: '{task_name}'")
            
            # 태스크별 구체적 지침
            if '분석' in task_name:
                output.append("  1. 저장된 데이터를 가져오세요:")
                output.append("     data = get_shared('이전_결과_키')")
                output.append("  2. 분석을 수행하세요")
                output.append("  3. 결과를 저장하세요:")
                output.append("     set_shared('analysis_result', 분석결과)")
                
            elif '최적화' in task_name:
                output.append("  1. 분석 결과를 가져오세요:")
                output.append("     analysis = get_shared('analysis_result')")
                output.append("  2. 최적화를 수행하세요")
                output.append("  3. 결과를 저장하세요:")
                output.append("     set_shared('optimization_result', 최적화결과)")
                
            elif '테스트' in task_name:
                output.append("  1. 이전 결과를 가져오세요:")
                output.append("     data = get_shared('optimization_result')")
                output.append("  2. 테스트를 실행하세요")
                output.append("  3. 결과를 저장하세요:")
                output.append("     set_shared('test_result', 테스트결과)")
                
            else:
                output.append(f"  → {task_name}을(를) 수행하고 결과를 set_shared()로 저장하세요")
    
    else:
        # Flow 플랜이 없을 때 일반 지침
        output.append("\n💡 작업 지침:")
        
        # 저장된 변수 기반 추천
        if 'analysis_result' in SESSION_POOL.shared_variables:
            if 'optimization_result' not in SESSION_POOL.shared_variables:
                output.append("  → 분석이 완료되었으니 최적화를 진행하세요:")
                output.append("    1. analysis = get_shared('analysis_result')")
                output.append("    2. # 최적화 로직 수행")
                output.append("    3. set_shared('optimization_result', 결과)")
        else:
            output.append("  → 초기 데이터를 설정하고 작업을 시작하세요:")
            output.append("    1. # 데이터 준비 또는 파일 읽기")
            output.append("    2. set_shared('data', 준비된_데이터)")
            output.append("    3. # 다음 작업 진행")
    
    # 3. 유용한 명령 안내
    output.append("\n📌 유용한 명령:")
    output.append(f"  • list_shared() - 저장된 모든 변수 키 확인")
    output.append(f"  • var_count() - 현재 {len(SESSION_POOL.shared_variables)}개 변수 저장됨")
    
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
    """Execute code in a shared session with enhanced guidance"""
    
    # Get or create shared session
    session_key, session = SESSION_POOL.get_or_create_session(agent_id, session_id)
    
    # Track execution
    _track_execution(session_key)
    
    # Execute with enhanced session
    result = session.execute(code)
    
    # Build response
    response = _build_response_metadata(result, session_key, agent_id)
    
    # Add cache statistics if available
    _add_cache_statistics(response, session)
    
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