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
    """Thread-safe session pool manager"""
    
    def __init__(self, max_sessions: int = 10, session_timeout: int = 3600):
        self.max_sessions = max_sessions
        self.session_timeout = session_timeout  # seconds
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.RLock()
        self.metrics = {
            'total_created': 0,
            'total_reused': 0,
            'total_expired': 0,
            'current_active': 0
        }
    
    def get_or_create_session(self, 
                            agent_id: Optional[str] = None,
                            session_id: Optional[str] = None) -> Tuple[str, EnhancedREPLSession]:
        """Get existing or create new isolated session"""
        
        with self.lock:
            # Generate session key
            if session_id:
                key = session_id
            elif agent_id:
                # Agent-specific persistent session
                key = f"agent_{agent_id}"
            else:
                # Anonymous session
                key = f"anon_{uuid.uuid4().hex[:8]}"
            
            current_time = time.time()
            
            # Check if session exists and is valid
            if key in self.sessions:
                session_data = self.sessions[key]
                
                # Check if session expired
                if current_time - session_data['last_accessed'] > self.session_timeout:
                    # Clean up expired session
                    self._cleanup_session(key)
                    self.metrics['total_expired'] += 1
                else:
                    # Reuse existing session
                    session_data['last_accessed'] = current_time
                    session_data['access_count'] += 1
                    self.metrics['total_reused'] += 1
                    
                    return key, session_data['session']
            
            # Check pool capacity
            if len(self.sessions) >= self.max_sessions:
                # Remove least recently used session
                self._evict_lru_session()
            
            # Create new session
            new_session = self._create_new_session(agent_id)
            
            self.sessions[key] = {
                'session': new_session,
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
            
            return key, new_session
    
    def _create_new_session(self, agent_id: Optional[str] = None) -> EnhancedREPLSession:
        """Create a new isolated session with agent-specific configuration"""
        
        config = {
            'memory_limit_mb': 500,  # Lower limit per session
            'cache_dir': f'.repl_cache/{agent_id or "shared"}',
            'enable_streaming': True,
            'enable_caching': True,
            'chunk_size': 10000
        }
        
        # Agent-specific configurations
        if agent_id:
            if 'analyzer' in agent_id.lower():
                config['memory_limit_mb'] = 1000  # More memory for analysis
            elif 'test' in agent_id.lower():
                config['memory_limit_mb'] = 750  # Medium memory for tests
            elif 'optimizer' in agent_id.lower():
                config['memory_limit_mb'] = 1500  # High memory for optimization
        
        session = EnhancedREPLSession(**config)
        
        # Add agent-specific helpers
        session.namespace.update({
            'agent_id': agent_id,
            'session_info': lambda: self.get_session_info(agent_id),
            'clear_agent_cache': lambda: self._clear_agent_cache(agent_id)
        })
        
        return session
    
    def _evict_lru_session(self):
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
    
    def cleanup_expired_sessions(self):
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
    
    def shutdown(self):
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


def get_think_prompt():
    """Get Think tool prompt for successful executions"""
    return """

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🤔 코드 실행 완료 - Think 도구로 분석 권장
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Think 도구를 사용하여 다음을 수행하세요:
• 실행 결과의 정확성 및 완전성 검증
• 코드 패턴과 잠재적 개선점 분석
• 다음 단계 작업 계획 수립
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""


def execute_code(code: str, 
                agent_id: Optional[str] = None,
                session_id: Optional[str] = None) -> Dict[str, Any]:
    """Execute code in an isolated session"""
    
    # Get or create isolated session
    session_key, session = SESSION_POOL.get_or_create_session(agent_id, session_id)
    
    # Track execution
    if session_key in SESSION_POOL.sessions:
        SESSION_POOL.sessions[session_key]['execution_count'] += 1
    
    # Execute with enhanced session
    result = session.execute(code)
    
    # Convert to JSON-compatible format
    response = {
        'success': result.success,
        'language': 'python',
        'session_mode': 'ISOLATED_JSON_REPL',
        'session_id': session_key,  # Return session ID for client reuse
        'agent_id': agent_id,
        'stdout': result.stdout,
        'stderr': result.stderr,
        'execution_count': SESSION_POOL.sessions[session_key]['execution_count'],
        'memory_mb': result.memory_usage_mb,
        'execution_time_ms': result.execution_time_ms,
        'execution_mode': result.execution_mode.value,
        'chunks_processed': result.chunks_processed,
        'cached': result.cached,
        'note': f'Isolated session for agent: {agent_id or "anonymous"}',
        'debug_info': {
            'session_active': True,
            'session_age': int(time.time() - SESSION_POOL.sessions[session_key]['created_at']),
            'pool_size': len(SESSION_POOL.sessions),
            'pool_metrics': SESSION_POOL.get_pool_metrics()
        },
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    }
    
    # Add cache statistics if available
    if session.enable_caching:
        cache_stats = session.get_cache_stats()
        response['cache_stats'] = {
            'entries': cache_stats.get('entries', 0),
            'hit_rate': cache_stats.get('hit_rate', 0)
        }
    
    # Add Think prompt for successful executions
    if response.get("success", False) and response.get("stdout", ""):
        response["stdout"] += get_think_prompt()
    
    return response


def read_json_input():
    """Read JSON input from stdin"""
    try:
        line = sys.stdin.readline()
        if not line:
            return None
        return line.strip()
    except:
        return None


def write_json_output(response):
    """Write JSON output to stdout"""
    json_str = json.dumps(response, ensure_ascii=False)
    sys.stdout.write(json_str + '\n')
    sys.stdout.flush()


def periodic_cleanup():
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


def main():
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